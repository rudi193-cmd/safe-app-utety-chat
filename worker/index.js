/**
 * UTETY Chat — Cloudflare Worker
 * API proxy for Gemini. Holds the key server-side.
 * Rate limit: 20 req/IP/hour (in-memory, resets on restart)
 */

const RATE_LIMIT = 20;
const WINDOW_MS = 60 * 60 * 1000; // 1 hour
const ipMap = new Map(); // { ip: { count, resetAt } }

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};
const COUNTER_KEY = 'utety:visits';
const COUNTER_SEED = 1095; // founding year

function rateCheck(ip) {
  const now = Date.now();
  const entry = ipMap.get(ip);
  if (!entry || now > entry.resetAt) {
    ipMap.set(ip, { count: 1, resetAt: now + WINDOW_MS });
    return true;
  }
  if (entry.count >= RATE_LIMIT) return false;
  entry.count++;
  return true;
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: CORS });
    }

    const url = new URL(request.url);

    // ── Visit counter ──
    if (url.pathname === '/counter' && request.method === 'GET') {
      let count = COUNTER_SEED;
      if (env.UTETY_COUNTER) {
        const stored = await env.UTETY_COUNTER.get(COUNTER_KEY);
        count = stored ? parseInt(stored) + 1 : COUNTER_SEED + 1;
        await env.UTETY_COUNTER.put(COUNTER_KEY, String(count));
      }
      return new Response(JSON.stringify({ count }), {
        status: 200,
        headers: { ...CORS, 'Content-Type': 'application/json' },
      });
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405, headers: CORS });
    }

    const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
    if (!rateCheck(ip)) {
      return new Response(JSON.stringify({ error: 'rate_limited' }), {
        status: 429,
        headers: { ...CORS, 'Content-Type': 'application/json' },
      });
    }

    let body;
    try {
      body = await request.json();
    } catch {
      return new Response(JSON.stringify({ error: 'invalid_json' }), {
        status: 400, headers: { ...CORS, 'Content-Type': 'application/json' },
      });
    }

    const { message, persona, history = [] } = body;
    if (!message || !persona) {
      return new Response(JSON.stringify({ error: 'missing fields' }), {
        status: 400, headers: { ...CORS, 'Content-Type': 'application/json' },
      });
    }

    const apiKey = env.GEMINI_API_KEY;
    if (!apiKey) {
      return new Response(JSON.stringify({ error: 'server_misconfigured' }), {
        status: 500, headers: { ...CORS, 'Content-Type': 'application/json' },
      });
    }

    // Build Gemini request
    const contents = [
      ...history.map(m => ({ role: m.role === 'assistant' ? 'model' : 'user', parts: [{ text: m.content }] })),
      { role: 'user', parts: [{ text: message }] },
    ];

    const geminiReq = {
      system_instruction: { parts: [{ text: persona }] },
      contents,
      generationConfig: { maxOutputTokens: 1024, temperature: 0.8 },
    };

    const resp = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`,
      { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(geminiReq) }
    );

    if (!resp.ok) {
      const err = await resp.text();
      // Pass 429 through so the client can show the "add your own key" modal
      const status = resp.status === 429 ? 429 : 502;
      return new Response(JSON.stringify({ error: 'gemini_error', detail: err }), {
        status, headers: { ...CORS, 'Content-Type': 'application/json' },
      });
    }

    const data = await resp.json();
    const text = data?.candidates?.[0]?.content?.parts?.[0]?.text || '';

    return new Response(JSON.stringify({ response: text }), {
      status: 200,
      headers: { ...CORS, 'Content-Type': 'application/json' },
    });
  },
};
