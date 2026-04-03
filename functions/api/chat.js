/**
 * UTETY Chat — Cloudflare Pages Function
 * POST /api/chat
 * Body: { message, persona, history }
 * Returns: { response }
 *
 * Flow:
 *   1. Receive compiled persona string + message + history from client
 *   2. Send to Gemini 2.5 Flash (primary) / Groq Llama 3.3 (fallback)
 *   3. Return professor response
 *
 * Secrets (set in Pages dashboard): GEMINI_API_KEY, GROQ_API_KEY
 */

const CORS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

const RATE_LIMIT = 20;
const WINDOW_MS = 60 * 60 * 1000;
const ipMap = new Map();

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

export async function onRequestOptions() {
  return new Response(null, { status: 204, headers: CORS });
}

export async function onRequestPost({ request, env }) {
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
  if (!rateCheck(ip)) {
    return new Response(JSON.stringify({ error: 'rate_limited' }), {
      status: 429, headers: { ...CORS, 'Content-Type': 'application/json' },
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
  if (!message) {
    return new Response(JSON.stringify({ error: 'missing message' }), {
      status: 400, headers: { ...CORS, 'Content-Type': 'application/json' },
    });
  }

  const systemPrompt = persona || 'You are a professor at UTETY. Be helpful, thoughtful, and true to your character.';

  const apiKey = env.GEMINI_API_KEY;
  if (!apiKey) {
    return new Response(JSON.stringify({ error: 'server_misconfigured' }), {
      status: 500, headers: { ...CORS, 'Content-Type': 'application/json' },
    });
  }

  const contents = [
    ...history.map(m => ({
      role: m.role === 'assistant' ? 'model' : 'user',
      parts: [{ text: m.content }],
    })),
    { role: 'user', parts: [{ text: message }] },
  ];

  const geminiReq = {
    system_instruction: { parts: [{ text: systemPrompt }] },
    contents,
    generationConfig: { maxOutputTokens: 2048, temperature: 0.8 },
  };

  const geminiResp = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(geminiReq) }
  );

  // Groq fallback on rate limit
  if (geminiResp.status === 429 && env.GROQ_API_KEY) {
    const groqMessages = [
      { role: 'system', content: systemPrompt },
      ...history.map(m => ({ role: m.role === 'assistant' ? 'assistant' : 'user', content: m.content })),
      { role: 'user', content: message },
    ];
    const groqResp = await fetch('https://api.groq.com/openai/v1/chat/completions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${env.GROQ_API_KEY}` },
      body: JSON.stringify({ model: 'llama-3.3-70b-versatile', messages: groqMessages, max_tokens: 2048, temperature: 0.8 }),
    });
    if (groqResp.ok) {
      const groqData = await groqResp.json();
      const text = groqData?.choices?.[0]?.message?.content || '';
      return new Response(JSON.stringify({ response: text }), {
        status: 200, headers: { ...CORS, 'Content-Type': 'application/json' },
      });
    }
  }

  if (!geminiResp.ok) {
    const err = await geminiResp.text();
    return new Response(JSON.stringify({ error: 'llm_error', detail: err }), {
      status: geminiResp.status === 429 ? 429 : 502,
      headers: { ...CORS, 'Content-Type': 'application/json' },
    });
  }

  const data = await geminiResp.json();
  const text = data?.candidates?.[0]?.content?.parts?.[0]?.text || '';
  return new Response(JSON.stringify({ response: text }), {
    status: 200, headers: { ...CORS, 'Content-Type': 'application/json' },
  });
}
