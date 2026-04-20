"""
SAFE Framework Integration for UTETY Chat
==========================================
Session hooks, consent management, and Pigeon bus helpers.

Pigeon drop point: POST /api/pigeon/drop
Topics: ask, query, contribute, connect, status
"""

import json
import os as _os
import sqlite3 as _sqlite3
_STORE_ROOT = _os.environ.get(
    "WILLOW_STORE_ROOT",
    _os.path.join(_os.path.expanduser("~"), ".willow", "store")
)
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone

# ── Pigeon Bus Helpers ────────────────────────────────────────────────────────

_APP_ID = "safe-app-utety-chat"
_session_id = str(uuid.uuid4())
_APP_DATA = Path(_os.path.expanduser("~")) / ".willow" / "apps" / _APP_ID


def ask(prompt: str, persona: str = None, tier: str = "free") -> str:
    """LLM routing via Willow — not available in portless mode."""
    return "[Willow LLM routing not available in portless mode]"


def ask_raw(prompt: str, tier: str = "free") -> dict:
    """LLM routing via Willow — not available in portless mode."""
    return {"ok": False, "error": "LLM routing not available in portless mode"}


def query(q: str, limit: int = 5) -> list:
    """Query Willow's knowledge store directly via SOIL SQLite."""
    db_path = _os.path.join(_STORE_ROOT, "knowledge", "store.db")
    if not _os.path.exists(db_path):
        return []
    try:
        conn = _sqlite3.connect(db_path)
        rows = conn.execute(
            "SELECT data FROM records WHERE deleted=0 AND data LIKE ? LIMIT ?",
            (f"%{q}%", limit)
        ).fetchall()
        conn.close()
        return [json.loads(r[0]) for r in rows]
    except Exception:
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
    """Check if Willow store is reachable."""
    db_path = _os.path.join(_STORE_ROOT, "knowledge", "store.db")
    reachable = _os.path.exists(db_path)
    return {"ok": reachable, "store": _STORE_ROOT, "mode": "portless"}


def _drop(topic: str, payload: dict) -> dict:
    return {"ok": False, "error": "portless mode — porch removed"}


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
    return False


def request_consent_url():
    return None



def send(to_app, subject, body, thread_id=None):
    return {"ok": False, "error": "messaging not available in portless mode"}


def check_inbox(unread_only=True):
    return []

