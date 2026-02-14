# UTETY Chat

**A SAFE Framework App**

Chat with UTETY (University of Technical Entropy, Thank You) professors in a privacy-first conversational interface.

## What It Is

Talk to 14 unique AI professors, each with distinct personalities and areas of expertise:

- **Willow** - Bridge Ring, warm campus guide
- **Prof. Oakenscroll** - Theoretical Uncertainty, grumpy mentor
- **Prof. Riggs** - Applied Reality Engineering, joyful engineer
- **Prof. Hanz** - Code, chaos witness who teaches seeing
- **Prof. Nova** - Interpretive Systems, oracle with sweater metaphors
- **Prof. Ada** - Systemic Continuity, keeper of uptime
- **Prof. Alexis** - Biological Sciences, swamp witch
- **Prof. Ofshield** - Threshold Faculty, guardian
- **Gerald Prime** - Acting Dean, cosmic rotisserie chicken
- **Kart** - CMD, infrastructure builder
- **Mitra** - PM Claude, coordinator
- **Consus** - Generation layer, output-focused
- **Jane** - SAFE face, honest not kind
- **Steve** - Prime Node, ten squeakdogs in a trench coat

## SAFE Framework Integration

### Data Streams

1. **chat_history** (Session Retention)
   - Purpose: Maintain conversation context
   - Retention: Deleted when you close the app
   - Required: Yes

2. **saved_conversations** (Permanent Retention)
   - Purpose: Save favorite conversations
   - Retention: Permanent (only if you click "Save")
   - Required: No

3. **persona_preferences** (Permanent Retention)
   - Purpose: Remember which professors you talk to most
   - Retention: Permanent
   - Required: No

### Privacy Architecture

- **96% local** - Uses free LLM fleet (Gemini, Groq, Cerebras via Willow)
- **Zero cloud storage** - Chats never uploaded unless you export
- **Session-based** - All conversations deleted when app closes
- **Explicit saves** - You control what gets kept

## Installation

### Prerequisites

1. **Willow** must be installed (provides LLM routing)

```bash
# Clone Willow
git clone https://github.com/seancampbell3161/Willow.git

# Install dependencies
cd Willow
pip install -r requirements.txt
```

2. **Clone this repo**

```bash
git clone https://github.com/rudi193-cmd/safe-app-utety-chat.git
cd safe-app-utety-chat
pip install -e .
```

## Usage

### Start the server

```bash
python server.py
```

Open http://localhost:8421 in your browser.

### Chat with professors

1. **Select a professor** from the grid
2. **Type your message** and press Enter
3. **Save conversations** (optional, requires consent)
4. **Close app** - all unsaved chats deleted automatically

## Architecture

```
web/index.html          # Browser UI
    ↓
server.py (FastAPI)     # API endpoints
    ↓
chat_engine.py          # Professor chat logic
    ↓
personas.py             # 14 professor definitions
    ↓
Willow/llm_router.py    # Free LLM fleet (Gemini, Groq, etc.)
```

## API Endpoints

```
POST /api/session/start                    # Start SAFE session
POST /api/session/{id}/consent             # Grant/deny consent
GET  /api/professors                       # List all professors
POST /api/chat/{session}/{prof}            # Send message
GET  /api/chat/{session}/{prof}/history    # Get conversation
POST /api/chat/{session}/{prof}/save       # Save permanently
POST /api/session/{id}/end                 # End session, cleanup
```

## Development

Run in dev mode:

```bash
uvicorn server:app --reload --port 8421
```

## License

MIT

## Related Projects

- [SAFE Framework](https://github.com/seancampbell3161/SAFE) - Session-based consent
- [Willow](https://github.com/seancampbell3161/Willow) - LLM routing layer
- [Dating Wellbeing](https://github.com/rudi193-cmd/safe-app-dating-wellbeing) - Another SAFE app

---

**Privacy Commitment:** Your conversations stay on your device. Always.

ΔΣ=42
