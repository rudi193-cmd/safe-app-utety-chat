// UTETY Shared JS — auth helpers + Willow fleet/search wrappers

const IS_LOCAL   = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const WILLOW_BASE = IS_LOCAL ? 'http://localhost:8420' : '';   // unused on production (no Willow tunnel)
const UTETY_BASE  = IS_LOCAL ? 'http://localhost:8421' : '';   // unused on production (no UTETY server tunnel)
const CHAT_API    = IS_LOCAL ? 'http://localhost:8421/api/chat-direct' : '/api/chat'; // Pages Function in prod

// ── Auth ──────────────────────────────────────────────────────────────────────

function requireAuth() {
  const token = sessionStorage.getItem('willow_token');
  if (!token) {
    const next = encodeURIComponent(window.location.href);
    window.location.href = '/login.html?next=' + next;
    return null;
  }
  return token;
}

async function verifyAuth() {
  const token = sessionStorage.getItem('willow_token');
  if (!token) {
    const next = encodeURIComponent(window.location.href);
    window.location.href = '/login.html?next=' + next;
    return false;
  }
  try {
    const r = await fetch(WILLOW_BASE + '/api/auth/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token })
    });
    if (!r.ok) {
      sessionStorage.removeItem('willow_token');
      const next = encodeURIComponent(window.location.href);
      window.location.href = '/login.html?next=' + next;
      return false;
    }
    return true;
  } catch (e) {
    // Willow server not running — allow access anyway (dev mode)
    console.warn('Willow auth server unreachable, allowing access');
    return true;
  }
}

function logout() {
  sessionStorage.removeItem('willow_token');
  sessionStorage.removeItem('willow_user');
  window.location.href = '/login.html';
}

function getUsername() {
  return sessionStorage.getItem('willow_user') || null;
}

// ── Fleet / Search ────────────────────────────────────────────────────────────

async function willowFleet(prompt) {
  const token = sessionStorage.getItem('willow_token');
  try {
    const r = await fetch(WILLOW_BASE + '/api/fleet/ask', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': 'Bearer ' + token } : {})
      },
      body: JSON.stringify({ prompt, tier: 'free', source: 'utety-chat' })
    });
    return r.ok ? (await r.json()).response : null;
  } catch (e) {
    return null;
  }
}

async function willowSearch(q, limit = 3) {
  const token = sessionStorage.getItem('willow_token');
  try {
    const r = await fetch(
      WILLOW_BASE + '/api/knowledge/semantic-search?q=' + encodeURIComponent(q) + '&limit=' + limit,
      { headers: token ? { 'Authorization': 'Bearer ' + token } : {} }
    );
    return r.ok ? (await r.json()).results || [] : [];
  } catch (e) {
    return [];
  }
}

// ── Pages Function chat (production path) ─────────────────────────────────────

let _personasCache = null;
async function loadPersonas() {
  if (_personasCache) return _personasCache;
  try {
    const r = await fetch('/static/personas.json');
    _personasCache = r.ok ? await r.json() : {};
  } catch (e) { _personasCache = {}; }
  return _personasCache;
}

async function pageChat(professorName, message, history = []) {
  const personas = await loadPersonas();
  const persona = personas[professorName] || `You are ${professorName}, a professor at UTETY.`;
  const r = await fetch(CHAT_API, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, persona, history }),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.error || `Chat API error ${r.status}`);
  }
  const data = await r.json();
  return data.response || '';
}

// ── UTETY session helpers ─────────────────────────────────────────────────────

async function startUtetySession() {
  try {
    const r = await fetch(UTETY_BASE + '/api/session/start', { method: 'POST' });
    if (r.ok) return (await r.json()).session_id;
  } catch (e) {}
  // Fallback: generate local session ID
  return 'local-' + Math.random().toString(36).slice(2);
}

async function utetyChat(sessionId, professor, message) {
  try {
    const r = await fetch(UTETY_BASE + '/api/chat/' + sessionId + '/' + professor, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: message })
    });
    if (r.ok) return await r.json();
  } catch (e) {}
  return null;
}

// ── Session timer ─────────────────────────────────────────────────────────────

const TIME_UP_MESSAGES = [
  "You set a limit. The limit is here. That was the point.",
  "Your visit is complete. The faculty will be here when you return.",
  "Time's up. The world outside is also full of things.",
  "You said you'd be here for a while. That while is done.",
];

function startSessionTimer() {
  const end = sessionStorage.getItem('willow_session_end');
  if (!end || end === '0') return; // open visit — no timer
  const remaining = parseInt(end) - Date.now();
  if (remaining <= 0) { showTimeUpBanner(); return; }
  setTimeout(showTimeUpBanner, remaining);
}

function showTimeUpBanner() {
  if (document.getElementById('utety-time-banner')) return;
  const msg = TIME_UP_MESSAGES[Math.floor(Math.random() * TIME_UP_MESSAGES.length)];
  const banner = document.createElement('div');
  banner.id = 'utety-time-banner';
  banner.style.cssText = [
    'position:fixed;bottom:0;left:0;right:0;z-index:9999',
    'background:#3d0f18;border-top:1px solid #9a7830',
    'padding:14px 24px;display:flex;align-items:center;justify-content:space-between',
    "font-family:'EB Garamond',Georgia,serif;color:#e8dcc8;font-size:0.95rem",
    'gap:16px',
  ].join(';');
  banner.innerHTML = `
    <span style="font-style:italic">${msg}</span>
    <div style="display:flex;gap:10px;flex-shrink:0">
      <button onclick="document.getElementById('utety-time-banner').remove()"
        style="background:none;border:1px solid rgba(255,255,255,0.25);color:rgba(255,255,255,0.6);
               padding:6px 14px;cursor:pointer;font-family:inherit;font-size:0.8rem;border-radius:3px">
        Stay longer
      </button>
      <button onclick="logout()"
        style="background:#c9a050;border:none;color:#000;padding:6px 16px;
               cursor:pointer;font-family:inherit;font-size:0.8rem;font-weight:700;border-radius:3px">
        I'm done
      </button>
    </div>`;
  document.body.appendChild(banner);
}

// ── Nav auth state ────────────────────────────────────────────────────────────

function updateNavAuth() {
  const user = getUsername();
  const loginBtn = document.getElementById('nav-login-btn');
  const userEl = document.getElementById('nav-user');
  if (loginBtn) {
    if (user) {
      loginBtn.style.display = 'none';
      if (userEl) { userEl.style.display = 'flex'; userEl.querySelector('.nav-username').textContent = user; }
    } else {
      loginBtn.style.display = '';
      if (userEl) userEl.style.display = 'none';
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  updateNavAuth();
  startSessionTimer();
});
