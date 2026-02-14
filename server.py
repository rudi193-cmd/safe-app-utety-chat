"""
UTETY Chat API Server
======================
FastAPI server connecting web UI to chat engine.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict
import uuid

from chat_engine import ChatSession, ProfessorRoster
from safe_integration import SAFESession

app = FastAPI(title="UTETY Chat API")

# Active sessions (in-memory for demo - use DB for production)
sessions: Dict[str, SAFESession] = {}
chat_sessions: Dict[str, Dict[str, ChatSession]] = {}  # session_id -> {prof_name -> ChatSession}


class Message(BaseModel):
    content: str


class ConsentRequest(BaseModel):
    stream_id: str
    granted: bool


@app.get("/")
async def root():
    """Serve web UI."""
    return FileResponse("web/index.html")


@app.post("/api/session/start")
async def start_session():
    """Start new SAFE session."""
    session_id = str(uuid.uuid4())
    safe_session = SAFESession(session_id)
    sessions[session_id] = safe_session
    chat_sessions[session_id] = {}

    return safe_session.on_session_start()


@app.post("/api/session/{session_id}/consent")
async def grant_consent(session_id: str, request: ConsentRequest):
    """Grant or deny consent for a data stream."""
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")

    session = sessions[session_id]
    return session.on_consent_granted(request.stream_id, request.granted)


@app.get("/api/professors")
async def list_professors():
    """Get list of available professors."""
    return ProfessorRoster.list_professors()


@app.get("/api/professors/{name}")
async def get_professor(name: str):
    """Get professor details."""
    info = ProfessorRoster.get_professor_info(name)
    if not info:
        raise HTTPException(404, "Professor not found")
    return info


@app.post("/api/chat/{session_id}/{professor_name}")
async def send_message(session_id: str, professor_name: str, message: Message):
    """Send message to professor and get response."""
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")

    safe_session = sessions[session_id]

    # Check consent
    if not safe_session.can_access_stream("chat_history"):
        raise HTTPException(403, "No consent to chat")

    # Get or create chat session for this professor
    if professor_name not in chat_sessions[session_id]:
        chat_sessions[session_id][professor_name] = ChatSession(professor_name, session_id)

    chat = chat_sessions[session_id][professor_name]

    # Send message and get response
    response = chat.send_message(message.content)

    return {
        "professor": professor_name,
        "response": response,
        "history": chat.get_history()
    }


@app.get("/api/chat/{session_id}/{professor_name}/history")
async def get_history(session_id: str, professor_name: str):
    """Get conversation history."""
    if session_id not in chat_sessions:
        return {"history": []}

    if professor_name not in chat_sessions[session_id]:
        return {"history": []}

    chat = chat_sessions[session_id][professor_name]
    return {"history": chat.get_history()}


@app.post("/api/chat/{session_id}/{professor_name}/clear")
async def clear_history(session_id: str, professor_name: str):
    """Clear conversation history."""
    if session_id in chat_sessions and professor_name in chat_sessions[session_id]:
        chat = chat_sessions[session_id][professor_name]
        chat.clear_history()

    return {"status": "cleared"}


@app.post("/api/chat/{session_id}/{professor_name}/save")
async def save_conversation(session_id: str, professor_name: str):
    """Save conversation permanently (requires consent)."""
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")

    safe_session = sessions[session_id]

    if session_id not in chat_sessions or professor_name not in chat_sessions[session_id]:
        raise HTTPException(404, "No conversation found")

    chat = chat_sessions[session_id][professor_name]
    markdown = chat.export_conversation()

    return safe_session.save_conversation(professor_name, markdown)


@app.post("/api/session/{session_id}/end")
async def end_session(session_id: str):
    """End session and cleanup."""
    if session_id not in sessions:
        raise HTTPException(404, "Session not found")

    session = sessions[session_id]
    cleanup = session.on_session_end()

    # Delete session data
    if session_id in sessions:
        del sessions[session_id]
    if session_id in chat_sessions:
        del chat_sessions[session_id]

    return cleanup


# Mount static files
app.mount("/static", StaticFiles(directory="web"), name="static")


if __name__ == "__main__":
    import uvicorn
    print("Starting UTETY Chat server...")
    print("Open http://localhost:8421 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8421)
