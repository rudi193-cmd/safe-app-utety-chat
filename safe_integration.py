"""
SAFE Framework Integration for UTETY Chat
==========================================
Session hooks, consent management, and Pigeon bus helpers.

Pigeon drop point: POST /api/pigeon/drop
Topics: ask, query, contribute, connect, status
"""

import json
import os as _os
import uuid
import requests as _requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone

# ── Pigeon Bus Helpers ────────────────────────────────────────────────────────

_WILLOW_URL = _os.environ.get("WILLOW_URL", "http://localhost:8420")
_PIGEON_URL = f"{_WILLOW_URL}/api/pigeon/drop"
_APP_ID = "safe-app-utety-chat"
_session_id = str(uuid.uuid4())
_APP_DATA = Path("/media/willow/Apps/utety-chat")


def ask(prompt: str, persona: Optional[str] = None, tier: str = "free") -> str:
    """Ask Willow a question via the Pigeon bus. Returns the LLM response string."""
    result = _drop("ask", {"prompt": prompt, "persona": persona, "tier": tier})
    if result.get("ok"):
        return result.get("result", "")
    return f"[Error: {result.get('error', 'unknown')}]"


def ask_raw(prompt: str, tier: str = "free") -> dict:
    """Ask Willow and return full result dict (includes provider info)."""
    return _drop("ask", {"prompt": prompt, "tier": tier})


def query(q: str, limit: int = 5) -> list:
    """Query Willow's knowledge graph via the Pigeon bus. Returns atom list."""
    result = _drop("query", {"q": q, "limit": limit})
    if result.get("ok"):
        return result.get("result", [])
    return []


def contribute(content: str, category: str = "note", metadata: Optional[dict] = None) -> dict:
    """Stage a contribution to the Willow intake queue (filesystem, portless)."""
    try:
        intake_dir = _APP_DATA / "intake"
        intake_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        fname = intake_dir / f"{ts}_{uuid.uuid4().hex[:8]}.json"
        fname.write_text(json.dumps({
            "source_app": _APP_ID,
            "type": category,
            "content": content,
            "metadata": metadata or {},
            "contributed_at": datetime.now(timezone.utc).isoformat(),
        }, indent=2))
        return {"ok": True, "staged": str(fname)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def status() -> dict:
    """Check if Willow bus is reachable."""
    return _drop("status", {})


def _drop(topic: str, payload: dict) -> dict:
    """Internal: drop a message onto the Pigeon bus."""
    try:
        r = _requests.post(_PIGEON_URL, json={
            "topic": topic,
            "app_id": _APP_ID,
            "session_id": _session_id,
            "payload": payload,
        }, timeout=30)
        return r.json() if r.ok else {"ok": False, "error": r.text}
    except _requests.ConnectionError:
        return {
            "ok": False,
            "guest_mode": True,
            "error": f"Willow not reachable at {_WILLOW_URL}. "
                     "Set WILLOW_URL env var or run Willow locally."
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


class SAFESession:
    """Manages SAFE session lifecycle for UTETY Chat."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.started_at = datetime.now()
        self.consents = {}
        self.active = True
        self.chat_sessions = {}  # professor_name -> ChatSession

    def on_session_start(self) -> Dict:
        """
        Called when user opens UTETY Chat.
        Returns authorization requests for data streams.
        """
        return {
            "session_id": self.session_id,
            "authorization_requests": [
                {
                    "stream_id": "chat_history",
                    "purpose": "Maintain conversation context during this session",
                    "retention": "session",
                    "required": True,
                    "prompt": "May I remember our conversation while the app is open?"
                },
                {
                    "stream_id": "saved_conversations",
                    "purpose": "Save conversations you explicitly choose to keep",
                    "retention": "permanent",
                    "required": False,
                    "prompt": "May I save conversations when you click 'Save'?"
                },
                {
                    "stream_id": "persona_preferences",
                    "purpose": "Remember which professors you talk to most",
                    "retention": "permanent",
                    "required": False,
                    "prompt": "May I remember your professor preferences?"
                }
            ]
        }

    def on_consent_granted(self, stream_id: str, granted: bool) -> Dict:
        """Called when user grants/denies consent."""
        self.consents[stream_id] = {
            "granted": granted,
            "timestamp": datetime.now().isoformat()
        }

        # chat_history is required for app to function
        if stream_id == "chat_history" and not granted:
            return {
                "status": "consent_required",
                "message": "Chat requires temporary memory to maintain conversation context."
            }

        # saved_conversations is optional
        if stream_id == "saved_conversations" and not granted:
            return {
                "status": "limited_mode",
                "message": "Conversations will not be saved. They'll disappear when you close the app."
            }

        # persona_preferences is optional
        if stream_id == "persona_preferences" and not granted:
            return {
                "status": "limited_mode",
                "message": "Professor preferences won't be saved."
            }

        return {"status": "ok"}

    def can_access_stream(self, stream_id: str) -> bool:
        """Check if app has consent to access a stream."""
        return self.consents.get(stream_id, {}).get("granted", False)

    def on_session_end(self) -> Dict:
        """
        Called when user closes the app.
        Deletes all session data unless explicitly saved.
        """
        self.active = False
        actions = []

        # Delete chat history (session retention)
        if self.can_access_stream("chat_history"):
            num_chats = len(self.chat_sessions)
            actions.append({
                "action": "delete",
                "stream": "chat_history",
                "items_deleted": num_chats,
                "reason": "session_ended"
            })

        # Keep saved conversations (if consented)
        if self.can_access_stream("saved_conversations"):
            actions.append({
                "action": "retain",
                "stream": "saved_conversations",
                "reason": "permanent_consent"
            })

        # Keep preferences (if consented)
        if self.can_access_stream("persona_preferences"):
            actions.append({
                "action": "retain",
                "stream": "persona_preferences",
                "reason": "permanent_consent"
            })

        return {
            "session_id": self.session_id,
            "ended_at": datetime.now().isoformat(),
            "duration_seconds": (datetime.now() - self.started_at).total_seconds(),
            "cleanup_actions": actions
        }

    def on_revoke(self, stream_id: str) -> Dict:
        """User revokes consent mid-session."""
        if stream_id in self.consents:
            self.consents[stream_id]["granted"] = False
            self.consents[stream_id]["revoked_at"] = datetime.now().isoformat()

        # If chat_history revoked, clear all conversations
        if stream_id == "chat_history":
            self.chat_sessions = {}
            return {
                "status": "revoked",
                "stream": stream_id,
                "action": "all_conversations_deleted"
            }

        return {
            "status": "revoked",
            "stream": stream_id,
            "action": "data_deleted"
        }

    def save_conversation(self, professor_name: str, conversation_md: str) -> Dict:
        """
        Save a conversation permanently (requires consent).
        """
        if not self.can_access_stream("saved_conversations"):
            return {
                "error": "No consent to save conversations",
                "status": "denied"
            }

        # Save to disk
        save_dir = _APP_DATA / "saved_conversations"
        save_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{professor_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        filepath = save_dir / filename

        filepath.write_text(conversation_md, encoding="utf-8")

        return {
            "status": "saved",
            "filename": filename,
            "path": str(filepath)
        }


# Example usage
if __name__ == "__main__":
    session = SAFESession("session-001")

    # 1. Session starts
    auth = session.on_session_start()
    print("Authorization requests:", json.dumps(auth, indent=2))

    # 2. User grants consent
    session.on_consent_granted("chat_history", granted=True)
    session.on_consent_granted("saved_conversations", granted=True)
    session.on_consent_granted("persona_preferences", granted=False)

    # 3. Check access
    print("\nCan chat:", session.can_access_stream("chat_history"))
    print("Can save:", session.can_access_stream("saved_conversations"))
    print("Can track prefs:", session.can_access_stream("persona_preferences"))

    # 4. Session ends
    cleanup = session.on_session_end()
    print("\nCleanup:", json.dumps(cleanup, indent=2))


# ── Willow Consent Helpers ────────────────────────────────────────────────────

def get_consent_status(token=None):
    """Check if this app has consent to contribute to the user's Willow."""
    try:
        import requests as _r
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        resp = _r.get(f"{_WILLOW_URL}/api/apps", headers=headers, timeout=10)
        apps = resp.json().get("apps", [])
        return next((a["consented"] for a in apps if a["app_id"] == _APP_ID), False)
    except Exception:
        return False


def request_consent_url():
    """Return the Willow URL where the user can grant consent to this app."""
    return f"{_WILLOW_URL}/apps?highlight={_APP_ID}"



def send(to_app, subject, body, thread_id=None):
    """Send a message to another app's Pigeon inbox."""
    return _drop("send", {"to": to_app, "subject": subject, "body": body, "thread_id": thread_id})


def check_inbox(unread_only=True):
    """Fetch this app's Pigeon inbox from Willow."""
    try:
        import requests as _r
        r = _r.get(
            f"{_WILLOW_URL}/api/pigeon/inbox",
            params={"app_id": _APP_ID, "unread_only": str(unread_only).lower()},
            timeout=10
        )
        return r.json().get("messages", []) if r.ok else []
    except Exception:
        return []

