# UTETY Chat -- Full Code Audit Report

**Date:** 2026-04-08
**Scope:** All source files in `rudi193-cmd/safe-app-utety-chat`
**Branch:** `claude/code-audit-jNhgM`

---

## Executive Summary

The UTETY Chat application is a multi-professor conversational interface built on Cloudflare Pages/Workers with a Python backend that integrates with a "Willow" knowledge graph via PostgreSQL. The audit identified **6 Critical**, **7 High**, **8 Medium**, and **7 Low** severity findings across security, correctness, and code quality categories.

**Top priorities requiring immediate attention:**
1. SQL injection via unparameterized schema names (`core/db.py`, `chat_db.py`)
2. Hardcoded database credentials in source code (`pipeline/seed_professors.py`)
3. XSS risk from unsanitized markdown rendering (`web/chat.html`)
4. Wildcard CORS policy on API endpoints (`functions/api/chat.js`, `worker/index.js`)
5. Path traversal risk in conversation save (`safe_integration.py`)
6. Hardcoded filesystem path (`chat_db.py`)

---

## CRITICAL Severity

### C1. SQL Injection via f-string Schema Names

**Files:** `core/db.py:143,160,176` | `chat_db.py:69,107,108`
**Category:** Security -- SQL Injection

Schema names are interpolated into SQL using f-strings rather than the `psycopg2.sql` module:

```python
# core/db.py:143
cur.execute(f"SET search_path = {safe}, public")

# chat_db.py:107
cur.execute(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA}")
```

While `_safe_schema_name()` performs regex sanitization (`[^a-z0-9] -> _`), this is a defense-in-depth violation. If the sanitizer is ever bypassed or a new call site skips it, full SQL injection is possible. PostgreSQL identifiers cannot be passed as `%s` parameters, but `psycopg2.sql.Identifier` exists precisely for this purpose.

**Fix:** Replace all f-string SQL with `psycopg2.sql`:
```python
from psycopg2 import sql
cur.execute(sql.SQL("SET search_path = {}, public").format(sql.Identifier(safe)))
```

---

### C2. Hardcoded Database Credentials in Source

**File:** `pipeline/seed_professors.py:17`
**Category:** Security -- Credential Exposure

```
WILLOW_DB_URL   postgresql://willow:willow@172.26.176.1:5437/willow  (required)
```

The example connection string exposes:
- Username/password: `willow:willow`
- Internal IP: `172.26.176.1`
- Port: `5437`
- Database name: `willow`

This is committed to a public repository. Even as a comment, secret scanners will flag it and attackers can use it directly if the host is reachable.

**Fix:** Replace with a placeholder: `postgresql://<user>:<pass>@<host>:<port>/<db>`. Remove the internal IP address entirely.

---

### C3. Hardcoded Absolute Filesystem Path

**File:** `chat_db.py:18`
**Category:** Bug / Security -- Path Disclosure

```python
sys.path.insert(0, "/home/sean-campbell/willow-1.5/core")
```

This hardcoded path:
- Breaks the application on any machine except the developer's
- Exposes a real username (`sean-campbell`) and internal project structure
- Modifies `sys.path` globally, risking module shadowing

**Fix:** Use a relative import, an environment variable (`WILLOW_CORE_PATH`), or package the dependency properly.

---

### C4. XSS via Unsanitized Markdown Rendering

**File:** `web/chat.html` (multiple locations where `marked.parse()` is used with `innerHTML`)
**Category:** Security -- Cross-Site Scripting

LLM responses are rendered via `marked.parse()` directly into `innerHTML` without sanitization:
```javascript
div.innerHTML = marked.parse(content);
```

If an LLM returns content containing malicious HTML/JavaScript (via prompt injection or model compromise), it executes in the user's browser. There is no Content Security Policy to mitigate this.

**Fix:**
1. Add DOMPurify: `div.innerHTML = DOMPurify.sanitize(marked.parse(content))`
2. Add CSP headers: `Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.jsdelivr.net`

---

### C5. Wildcard CORS (`Access-Control-Allow-Origin: *`)

**Files:** `functions/api/chat.js:16` | `worker/index.js:12`
**Category:** Security -- CORS Misconfiguration

```javascript
const CORS = {
  'Access-Control-Allow-Origin': '*',
  ...
};
```

The wildcard origin allows any website to make cross-origin requests to the chat API. An attacker's site could make API calls on behalf of any visitor, consuming rate limits and potentially exfiltrating responses.

**Fix:** Restrict to known origins:
```javascript
'Access-Control-Allow-Origin': 'https://utety.pages.dev'
```

---

### C6. Path Traversal in Conversation Save

**File:** `safe_integration.py:222-228`
**Category:** Security -- Path Traversal

```python
filename = f"{professor_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
filepath = save_dir / filename
filepath.write_text(conversation_md, encoding="utf-8")
```

`professor_name` comes from the URL path (`server.py:160-174`) and is used directly in a filename. A crafted professor name like `../../etc/cron.d/evil` could write outside the intended directory.

**Fix:** Sanitize `professor_name` to alphanumeric characters only:
```python
import re
safe_name = re.sub(r'[^a-zA-Z0-9_-]', '', professor_name)
```

---

## HIGH Severity

### H1. CDN Scripts Without Subresource Integrity (SRI)

**Files:** `web/chat.html`, `web/research.html`, `web/dispatches.html`
**Category:** Security -- Supply Chain

```html
<script src="https://cdn.jsdelivr.net/npm/marked@12/marked.min.js"></script>
```

No `integrity` attribute. If jsdelivr is compromised, arbitrary JavaScript runs in users' browsers. The version is also unpinned (`@12` instead of a specific patch).

**Fix:** Pin exact version and add SRI hash:
```html
<script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"
        integrity="sha384-..." crossorigin="anonymous"></script>
```

---

### H2. In-Memory Rate Limiter Resets on Restart

**Files:** `functions/api/chat.js:23-24` | `worker/index.js:9`
**Category:** Security -- Rate Limiting Bypass

```javascript
const ipMap = new Map();
```

Rate limit state lives in Worker memory. Every deployment, restart, or cold start resets all counters. Cloudflare Workers can also run multiple isolates, so the Map is not shared across instances.

**Fix:** Use Cloudflare KV or Durable Objects for persistent, shared rate limiting.

---

### H3. In-Memory Session Storage (No Persistence, Unbounded Growth)

**File:** `server.py:19-21`
**Category:** Bug / Security -- Denial of Service

```python
sessions: Dict[str, SAFESession] = {}
chat_sessions: Dict[str, Dict[str, ChatSession]] = {}
```

Sessions are stored in Python dicts with no eviction, no TTL, and no size limit. Each session accumulates conversation history in memory. Over time, this leads to unbounded memory growth and eventual OOM. Sessions are also lost on server restart.

**Fix:**
- Add TTL-based eviction (e.g., 1 hour timeout)
- Cap maximum concurrent sessions
- For production, use Redis or database-backed sessions

---

### H4. No Authentication or Authorization on Server API

**File:** `server.py` (all endpoints)
**Category:** Security -- Missing Authentication

The FastAPI server has no authentication middleware. All endpoints are publicly accessible:
- `POST /api/chat/{session_id}/{professor_name}` -- anyone can chat
- `POST /api/session/{session_id}/end` -- anyone can terminate another user's session
- `GET /api/professors/{name}` -- returns full system prompts including persona internals

The `get_professor_info()` method (`chat_engine.py:193`) returns the full LLM system prompt, which should be treated as confidential.

**Fix:**
- Add authentication middleware (JWT, API key, or session cookie)
- Remove `full_prompt` from public professor info endpoint
- Validate session ownership before allowing mutations

---

### H5. Hardcoded Default Username Across Multiple Files

**Files:** `core/db.py:21` | `pipeline/seed_professors.py:14,18,69`
**Category:** Security -- Credential Exposure

```python
WILLOW_USERNAME = os.getenv("WILLOW_USERNAME", "Sweet-Pea-Rudi19")
```

This username is a PostgreSQL schema name and is used as a default fallback. It appears in multiple files and is committed to the public repo.

**Fix:** Require `WILLOW_USERNAME` as a mandatory env var with no default. Raise an error if unset.

---

### H6. Error Messages Leak Internal Details

**Files:** `safe_integration.py:66-67` | `functions/api/chat.js:116` | `worker/index.js:129`
**Category:** Security -- Information Disclosure

```python
"error": f"Willow not reachable at {_WILLOW_URL}. ..."
```

```javascript
const err = await geminiResp.text();
return new Response(JSON.stringify({ error: 'llm_error', detail: err }), ...);
```

Error responses include internal URLs, raw upstream error messages, and infrastructure details. These help attackers map the internal architecture.

**Fix:** Return generic error messages to clients. Log details server-side only.

---

### H7. Unsafe `lib/auth.ts` References Non-Existent Supabase Module

**File:** `lib/auth.ts:7`
**Category:** Bug -- Dead Code / Broken Import

```typescript
import { supabase } from './supabase';
```

This file imports from `./supabase` which does not exist in the `lib/` directory. The file appears to be leftover from an earlier auth strategy. If ever imported, it will throw at module load time.

**Fix:** Either remove the file or add the corresponding `supabase.ts` module with proper configuration (keeping credentials out of source).

---

## MEDIUM Severity

### M1. No CSRF Protection

**Files:** `web/login.html`, `web/signup.html`, `server.py`
**Category:** Security -- Cross-Site Request Forgery

No CSRF tokens are generated or validated. Combined with the wildcard CORS policy, this allows cross-site attacks against authenticated endpoints.

**Fix:** Implement CSRF tokens or use `SameSite=Strict` cookies for session management.

---

### M2. Predictable Guest Token Format

**File:** `web/chat.html`
**Category:** Security -- Weak Authentication

```javascript
sessionStorage.setItem('willow_token', 'guest-trial-' + Date.now());
```

Guest tokens are trivially guessable (prefix + timestamp). There is no server-side validation of these tokens.

**Fix:** Generate cryptographically random tokens server-side. Validate on every API call.

---

### M3. `_resolve_host()` Reads `/etc/resolv.conf` as Network Config

**File:** `chat_db.py:33-44`
**Category:** Bug -- Fragile Assumption

```python
def _resolve_host() -> str:
    with open("/etc/resolv.conf") as f:
        for line in f:
            if line.strip().startswith("nameserver"):
                host = line.strip().split()[1]
                break
    return host
```

This function uses the DNS nameserver as the database host -- a WSL-specific hack. On any other Linux system, this connects to the DNS resolver (e.g., `127.0.0.53` on systemd-resolved), not the database.

**Fix:** Remove this function. Require explicit `WILLOW_DB_URL` in all environments.

---

### M4. Duplicate Code Between Worker and Pages Function

**Files:** `functions/api/chat.js` and `worker/index.js`
**Category:** Quality -- Code Duplication

These two files contain nearly identical logic: same rate limiter, same Gemini/Groq request building, same CORS headers, same error handling. Changes to one must be manually replicated to the other.

**Fix:** Extract shared logic into a common module imported by both.

---

### M5. `safe_integration.py` Uses Undefined Variables

**File:** `safe_integration.py:268,269,276,289`
**Category:** Bug -- NameError at Runtime

```python
resp = _r.get(f"{WILLOW_URL}/api/apps", ...)  # WILLOW_URL is not defined
return next((a["consented"] for a in apps if a["app_id"] == APP_ID), False)  # APP_ID is not defined
```

The functions `get_consent_status()`, `request_consent_url()`, and `check_inbox()` reference `WILLOW_URL` and `APP_ID` -- but the module defines `_WILLOW_URL` and `_APP_ID` (with underscores). These functions will raise `NameError` when called.

**Fix:** Replace `WILLOW_URL` with `_WILLOW_URL` and `APP_ID` with `_APP_ID`.

---

### M6. No Input Length Validation on Chat Messages

**Files:** `server.py:110`, `functions/api/chat.js:58-63`, `worker/index.js:74-79`
**Category:** Security -- Input Validation

The `Message` model and request parsing accept arbitrarily long content strings. A user could send megabytes of text, consuming LLM tokens and backend memory.

**Fix:** Add max length validation:
```python
class Message(BaseModel):
    content: str = Field(..., max_length=4000)
```

---

### M7. Conversation History Sent to Client Unfiltered

**File:** `server.py:130-134`
**Category:** Security -- Information Disclosure

```python
return {
    "professor": professor_name,
    "response": response,
    "history": chat.get_history()
}
```

The full history (including internal metadata like `provider` and `timestamp`) is returned on every message. History objects may contain sensitive system information.

**Fix:** Filter history to only include `role` and `content` fields before returning to the client.

---

### M8. No Security Headers Configured

**Files:** `wrangler.toml`, all HTML files
**Category:** Security -- Missing Headers

No `Content-Security-Policy`, `Strict-Transport-Security`, `X-Content-Type-Options`, `X-Frame-Options`, or `Referrer-Policy` headers are set.

**Fix:** Add a `_headers` file for Cloudflare Pages or configure headers in the Worker:
```
Content-Security-Policy: default-src 'self'; script-src 'self' https://cdn.jsdelivr.net
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

---

## LOW Severity

### L1. Exposed Infrastructure URLs in README

**File:** `README.md`
**Category:** Information Disclosure

The README documents specific Worker URLs (`utety-worker.rudi193.workers.dev`), Cloudflare account identifiers, and architecture details that facilitate reconnaissance.

**Fix:** Use generic references in public documentation. Move deployment-specific URLs to a private wiki.

---

### L2. `personas.py` Contains ~37KB of Inline Prompt Data

**File:** `personas.py`
**Category:** Quality -- Maintainability

The entire professor persona corpus is defined as Python string literals. This makes version control diffs noisy and editing error-prone.

The persona compiler (`persona_compiler.py`) and JSON files exist but `personas.py` is still the primary source for most professors. Some professors have both, creating ambiguity about the source of truth.

**Fix:** Complete the migration to JSON persona files. Load all personas via `persona_compiler.load_all_personas()`.

---

### L3. Sprite Data Inlined in HTML (~900 lines)

**File:** `web/chat.html`
**Category:** Quality -- Performance / Maintainability

Pixel art sprite data is embedded as JavaScript arrays directly in the HTML, adding ~80KB to every page load. This cannot be cached independently.

**Fix:** Move to `web/static/sprites.json` and load asynchronously.

---

### L4. Missing `.gitignore` Patterns

**File:** `.gitignore`
**Category:** Configuration

Missing patterns for:
- `*.key`, `*.pem` (private keys)
- `node_modules/` (npm dependencies)
- `.dev.vars` is covered by `.dev.*` pattern via `.env.*`, but should be explicit

---

### L5. `server.py` Listens on `0.0.0.0`

**File:** `server.py:206`
**Category:** Security -- Network Exposure

```python
uvicorn.run(app, host="0.0.0.0", port=8421)
```

Binds to all interfaces by default, exposing the unauthenticated API to the local network.

**Fix:** Default to `127.0.0.1` for development. Use environment variable for production binding.

---

### L6. No Graceful Pool Shutdown

**Files:** `chat_db.py`, `core/db.py`
**Category:** Quality -- Resource Management

Connection pools are created but never closed. On application shutdown, connections may leak.

**Fix:** Add `atexit` handler or application lifecycle hook to close the pool.

---

### L7. PII in Context Data Files

**File:** `data/professors/jane_context.md` (and potentially others)
**Category:** Privacy -- Data Exposure

Context files contain partial real usernames (e.g., Reddit usernames from OCR'd screenshots).

**Fix:** Sanitize or redact all PII from context data files before committing.

---

## Summary

| Severity | Count | Key Areas |
|----------|-------|-----------|
| CRITICAL | 6 | SQL injection, credential exposure, XSS, CORS, path traversal, hardcoded path |
| HIGH | 7 | Missing auth, SRI, rate limiting, session management, info disclosure |
| MEDIUM | 8 | CSRF, weak tokens, code duplication, input validation, undefined vars |
| LOW | 7 | Info disclosure, maintainability, performance, privacy |

## Recommended Priority Order

### Immediate (before any public deployment)
1. **C1** -- Fix SQL injection (use `psycopg2.sql`)
2. **C2** -- Remove hardcoded credentials from source
3. **C3** -- Remove hardcoded filesystem path
4. **C4** -- Add DOMPurify for markdown sanitization
5. **C5** -- Restrict CORS to known origins
6. **C6** -- Sanitize filenames in conversation save
7. **H4** -- Add authentication to server API
8. **M5** -- Fix `NameError` bugs in `safe_integration.py`

### Short-term (next sprint)
9. **H1** -- Add SRI to CDN scripts
10. **H5** -- Remove hardcoded default username
11. **H6** -- Sanitize error messages
12. **M1** -- Add CSRF protection
13. **M6** -- Add input length validation
14. **M8** -- Add security headers

### Medium-term (next quarter)
15. **H2** -- Move rate limiting to Cloudflare KV/Durable Objects
16. **H3** -- Add session eviction and persistence
17. **M3** -- Remove WSL-specific host resolution hack
18. **M4** -- Deduplicate Worker/Function code
19. **L2** -- Complete persona JSON migration
20. **L3** -- Externalize sprite data
