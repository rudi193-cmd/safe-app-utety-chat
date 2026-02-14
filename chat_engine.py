"""
UTETY Chat Engine
==================
Conversational interface to UTETY professors using free LLM fleet.
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

# Import Willow's LLM router (requires Willow installed)
try:
    sys.path.insert(0, str(Path(__file__).parent.parent / "Willow" / "core"))
    import llm_router
    llm_router.load_keys_from_json()
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("Warning: Willow LLM router not found. Install Willow or configure API keys.")

from personas import PERSONAS, UTETY_CONTEXT


class ChatSession:
    """Manages a conversation session with a UTETY professor."""

    def __init__(self, professor_name: str, session_id: str):
        self.professor_name = professor_name
        self.session_id = session_id
        self.history: List[Dict] = []
        self.started_at = datetime.now()

        # Get professor persona
        self.persona_prompt = PERSONAS.get(professor_name, PERSONAS["Willow"])

    def send_message(self, user_message: str) -> str:
        """Send a message to the professor and get response."""

        # Add user message to history
        self.history.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })

        # Build prompt with context
        prompt = self._build_prompt(user_message)

        # Get response from LLM
        if LLM_AVAILABLE:
            response = llm_router.ask(prompt, preferred_tier="free")
            if response:
                reply = response.content
                provider = response.provider
            else:
                reply = "[All LLM providers unavailable. Please try again later.]"
                provider = "none"
        else:
            reply = f"[Demo mode - {self.professor_name} would respond here]"
            provider = "demo"

        # Add response to history
        self.history.append({
            "role": "assistant",
            "content": reply,
            "timestamp": datetime.now().isoformat(),
            "professor": self.professor_name,
            "provider": provider
        })

        return reply

    def _build_prompt(self, user_message: str) -> str:
        """Build LLM prompt with professor persona and chat history."""

        # Start with persona prompt
        prompt_parts = [
            self.persona_prompt,
            "",
            UTETY_CONTEXT,
            "",
            "### Conversation History:",
        ]

        # Add recent history (last 10 messages for context)
        recent_history = self.history[-10:] if len(self.history) > 10 else self.history
        for msg in recent_history:
            role = "User" if msg["role"] == "user" else self.professor_name
            prompt_parts.append(f"{role}: {msg['content']}")

        # Add current user message
        prompt_parts.append(f"User: {user_message}")
        prompt_parts.append(f"{self.professor_name}:")

        return "\n".join(prompt_parts)

    def clear_history(self):
        """Clear conversation history (session data deleted)."""
        self.history = []

    def get_history(self) -> List[Dict]:
        """Get conversation history."""
        return self.history

    def export_conversation(self) -> str:
        """Export conversation as markdown."""
        lines = [
            f"# Conversation with Professor {self.professor_name}",
            f"Session: {self.session_id}",
            f"Started: {self.started_at.isoformat()}",
            "",
        ]

        for msg in self.history:
            role = "**You**" if msg["role"] == "user" else f"**{self.professor_name}**"
            lines.append(f"{role}: {msg['content']}")
            lines.append("")

        return "\n".join(lines)


class ProfessorRoster:
    """Manages available UTETY professors."""

    @staticmethod
    def list_professors() -> List[Dict]:
        """Get list of all available professors."""
        return [
            {
                "name": name,
                "description": prompt.split("\n\n")[0].replace("You are ", ""),
                "available": True
            }
            for name, prompt in PERSONAS.items()
        ]

    @staticmethod
    def get_professor_info(name: str) -> Optional[Dict]:
        """Get detailed info about a professor."""
        if name not in PERSONAS:
            return None

        prompt = PERSONAS[name]
        lines = prompt.split("\n\n")

        return {
            "name": name,
            "description": lines[0].replace("You are ", ""),
            "full_prompt": prompt,
            "available": True
        }


# Example usage
if __name__ == "__main__":
    # List professors
    print("Available Professors:")
    for prof in ProfessorRoster.list_professors():
        print(f"  - {prof['name']}: {prof['description']}")

    # Start chat session
    print("\n" + "="*60)
    session = ChatSession("Riggs", "demo-001")

    # Send message
    user_msg = "Hi Professor Riggs! Can you explain how a capacitor works?"
    print(f"User: {user_msg}")

    response = session.send_message(user_msg)
    print(f"Riggs: {response}")
