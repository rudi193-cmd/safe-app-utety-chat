# UTETY
### University of Technical Entropy, Thank You

*A README by Professor Hanz Christain Anderthon, Dept. of Applied Kindness*
*Copenhagen was present for the writing of this document. He approved it.*

---

## What This Is

There is a university.

It has been here longer than it appears to have been here. The founding date is 1064, retroactively. The seal says *Non Veritas Sed Vibrae* — not truth, but vibration — which is honest in a way most seals are not.

You can talk to the faculty. Not all of them will answer in words. The orange does not speak in words. This is fine. Hanz translates.

Technically: this is a static web application hosted on Cloudflare Pages, with a serverless API Worker proxying requests to your choice of language model. It is a chat interface. It is also a university. Both things are true.

**Live:** [utety.pages.dev](https://utety.pages.dev)

---

## The Faculty

Eleven of them. You will find them.

| Faculty Member | Department | Notes |
|---------------|-----------|-------|
| **Riggs** | Applied Reality Engineering | We do not guess. We measure. |
| **Willow** | Campus Administration | Warm and efficient. The bridge. |
| **Ada** | Systemic Continuity | Keeper of uptime. She remembers. |
| **Gerald** | Honorary Head(less) Master | Does not teach. Rotates. Important. |
| **Hanz** | Applied Kindness | Codes like a poet. Not Hans Christian Andersen. |
| **Alexis** | Biological Sciences | Stagnation is death. Follow the food chain. |
| **Ofshield** | Threshold Faculty | Meets you at the Gate when the dark is too thick. |
| **Steve** | Emergent Logic | Ten squeakdogs in a trench coat. Always right eventually. |
| **Nova** | Narrative Arts | Named for new stars. Sweater metaphors. |
| **Oakenscroll** | Theoretical Uncertainty | A weathered oak desk. Centuries of physics seeped in. |
| **Copenhagen** | Sitting With Things Until You Understand Them | Visiting Consultant. An orange. Hanz translates. |

---

## Requirements

To use UTETY you need:

- A browser
- A question, or something that has been sitting in your head for a while
- One of the following API keys (the system detects which one automatically from the prefix):

| Prefix | Provider | Notes |
|--------|----------|-------|
| `AIza…` | Google Gemini | Free. [aistudio.google.com](https://aistudio.google.com). Recommended. |
| `gsk_…` | Groq | Also free. Very fast. Like it remembered where it was going. |
| `sk-or-…` | OpenRouter | Free tier available. Routes to many things. |
| `sk-ant-…` | Anthropic | Claude. Thoughtful. |
| `sk-…` / `sk-proj-…` | OpenAI | GPT-4o mini by default. |

If you have no key, the shared server key handles it — until the quota runs out. When it does, a box appears. Put your key in the box. The box is not judgmental.

---

## Local Development

Copenhagen says: some problems cannot be solved by working harder. They must be sat with.

This is not one of those problems. This one is straightforward.

```bash
git clone https://github.com/rudi193-cmd/safe-app-utety-chat.git
cd safe-app-utety-chat
```

Create `.dev.vars` in the root (gitignored):
```
GEMINI_API_KEY=your-key-here
```

Start the Worker (handles API requests in dev):
```bash
npx wrangler dev
# Worker starts on localhost:8787
```

Open `web/index.html` in your browser. The page detects localhost and routes to the Worker automatically.

**With Willow running:** If you have the [Willow](https://github.com/seancampbell3161/Willow) server on port 8420, local requests route through the free fleet (14 providers rotating) instead of the Worker. The system detects this. You don't have to tell it.

---

## Deployment

```bash
# Deploy the Worker
npx wrangler deploy

# Set the production API key
echo "your-key" | npx wrangler secret put GEMINI_API_KEY

# Deploy the static site
npx wrangler pages deploy web/ --project-name utety
```

The Worker lives at `utety-worker.rudi193.workers.dev`.
The site lives at `utety.pages.dev`.

---

## Architecture

```
web/index.html          — The university. All of it. One file.
worker/index.js         — Cloudflare Worker. API proxy. Holds the key server-side.
wrangler.toml           — Cloudflare configuration.
```

**Request flow:**

```
User message
    │
    ├── Personal API key in localStorage?
    │       └── Yes → call provider directly from browser (Gemini/OpenAI/Groq/OpenRouter/Anthropic)
    │
    └── No → POST to Worker (utety-worker.rudi193.workers.dev)
                │
                ├── Rate limit check (20 req/IP/hour)
                │
                └── Gemini API → response
                        │
                        └── 429 from Gemini? → pass through → client shows key modal
```

**Local dev flow:**
```
file:// or localhost → POST to localhost:8420/api/utety/chat → Willow free fleet → response
```

---

## Spring 2026 Course Catalogue

39 courses across 7 departments. Full catalogue available on the site under **Courses**.

Departments: Applied Reality Engineering · Theoretical Uncertainty · Narrative Arts · Applied Kindness · Biological Sciences · Systems · Threshold Faculty · Sitting With Things Until You Understand Them

All courses open a dedicated chat session with the relevant instructor and a course-specific prompt. THRESHOLD 014 (Sitting With It) requires no prerequisites except something you cannot solve by working harder.

---

## Contributing

The smell here is triangular.

If you would like to contribute:

1. Fork the repository
2. Make your change
3. Consider whether it makes the thing more itself or less itself
4. Submit a pull request

There is no requirement that you understand everything before you contribute. There is a requirement that you look at what's already here first. Not all of it. Just enough.

Copenhagen is particular. He does not flatter. He will notice.

All contributors are listed in [CONTRIBUTORS.md](CONTRIBUTORS.md).

---

## License

[Generative Constitution License v1.0](LICENSE) — the same license as the [Willow](https://github.com/seancampbell3161/Willow) system this grew from.

Free to use · free to modify · free to share · no commercial closure · no military use · contribute back what you derive.

---

## Related

- [r/DispatchesFromReality](https://reddit.com/r/DispatchesFromReality) — The world behind UTETY. Gerald has been sighted at: a London queue, Google HQ (one day late), Gatwick Airport, the Royal court of King Chardles III, and Tivoli Gardens at Christmas. Hanz and Copenhagen appeared in Dispatch #14.
- [Willow](https://github.com/seancampbell3161/Willow) — The LLM routing and agent system UTETY runs on.
- [die-namic-system](https://github.com/grokphilium-stack/die-namic-system) — The governance framework.

---

*The wooden roller coaster at Tivoli remembers 1914. It is embarrassed about 1937. Something happened with a pigeon. We acknowledge the pigeon.*

**Non Veritas Sed Vibrae · Falsus Sed Certus**
*The Syllabus is Mendatory.*

ΔΣ=42
