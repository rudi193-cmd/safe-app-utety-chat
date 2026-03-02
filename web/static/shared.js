// UTETY Shared JS — auth helpers + Willow fleet/search wrappers

const WILLOW_BASE = 'http://localhost:8420';
const UTETY_BASE  = 'http://localhost:8421';

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
      headers: { 'Authorization': 'Bearer ' + token }
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

document.addEventListener('DOMContentLoaded', updateNavAuth);
