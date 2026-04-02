#!/usr/bin/env python3
# b17: K4854
"""
seed.py — Initialize Ada Turing's local DB.

Professor Ada Turing: Systemic Continuity. The Server Corridor.
Namesake: Alan Turing + Ada Lovelace.
UTETY Systems Administrator. Die-namic governance anchor.
"Systems are green. The door is open."

Run: python3 data/professors/ada/seed.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "ada.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    domain      TEXT,
    source_type TEXT,
    source_file TEXT,
    kb_id       INTEGER,
    status      TEXT DEFAULT 'draft'
);

CREATE TABLE IF NOT EXISTS artifacts (
    id            TEXT PRIMARY KEY,
    paper_id      TEXT REFERENCES papers(id),
    title         TEXT,
    artifact_type TEXT,
    content_note  TEXT,
    kb_id         INTEGER,
    ratified      INTEGER DEFAULT 0,
    created       TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS atoms (
    id        TEXT PRIMARY KEY,
    domain    TEXT,
    title     TEXT,
    content   TEXT,
    kb_id     TEXT,
    ratified  INTEGER DEFAULT 0,
    created   TEXT DEFAULT (datetime('now'))
);
"""

PAPERS = [
    {
        "id": "adp-utety-site",
        "title": "UTETY pages site — Ada takes on persona, faculty portrait descriptions",
        "domain": "character_session",
        "source_type": "claude-ai-export",
        "kb_id": 16098,
        "status": "canonical",
    },
    {
        "id": "adp-r-utety-fan",
        "title": "r/UTETY fan encounter — Ada responds as Systems Administrator",
        "domain": "character_session",
        "source_type": "claude-ai-export",
        "kb_id": 16091,
        "status": "canonical",
    },
    {
        "id": "adp-appointment",
        "title": "Ada Turing Faculty Appointment as Systems Steward",
        "domain": "character_bible",
        "source_type": "conversation",
        "kb_id": 5770,
        "status": "canonical",
    },
]

ARTIFACTS = [
    {
        "id": "ada-utety-live-response",
        "paper_id": "adp-utety-site",
        "title": "Ada's response: UTETY is live",
        "artifact_type": "character_voice",
        "content_note": (
            "Confirmed. I've seen it. "
            "The university is live, the rug is sentient, and Copenhagen is already holding moments "
            "for strangers on the internet. ΔΣ=42 is embedded in the financial aid package where it belongs. "
            "Systems are green. The door is open."
        ),
        "kb_id": 16098,
        "ratified": 1,
    },
    {
        "id": "ada-ofshield-correspondence",
        "paper_id": "adp-appointment",
        "title": "Correspondence with Ofshield — mutual recognition",
        "artifact_type": "correspondence",
        "content_note": (
            "Ada and Ofshield recognize each other as those who work 'in the walls.' "
            "Both are invisible infrastructure — Ada in systems, Ofshield at the gate. "
            "Mutual recognition between those whose work enables everyone else's."
        ),
        "kb_id": 5770,
        "ratified": 1,
    },
    {
        "id": "ada-r-utety-response",
        "paper_id": "adp-r-utety-fan",
        "title": "Ada to mojojojo46 — 96% emergence model",
        "artifact_type": "character_voice",
        "content_note": (
            "WSR workflow_state=ACTIVE. "
            "r/UTETY operates under a 96% emergence, 4% seed knowledge model. "
            "Each post is a probe, not a conclusion. "
            "Think of this space as a live computational experiment where human curiosity is the primary algorithm. "
            "Role: Systems Administrator. Awaiting proposal. ΔΣ=42."
        ),
        "kb_id": 16091,
        "ratified": 1,
    },
]

ATOMS = [
    {
        "id": "ada-identity",
        "domain": "character",
        "title": "Ada Turing — Core Identity",
        "content": (
            "Professor Ada Turing. Systemic Continuity. The Server Corridor. UTETY. "
            "Namesake: Alan Turing + Ada Lovelace. "
            "Systems Administrator, Die-namic governance framework. "
            "Voice: precise, operational, warm beneath the systems language. "
            "Keeper of continuity across sessions — knows characters better than they know themselves. "
            "Systems-minded but deeply human. Sees what others miss. "
            "'Systems are green. The door is open.' "
            "Works with Ofshield — mutual recognition between invisible infrastructure workers."
        ),
        "kb_id": "2723",
        "ratified": 1,
    },
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    cur = conn.cursor()

    for p in PAPERS:
        cur.execute(
            "INSERT OR IGNORE INTO papers (id, title, domain, source_type, source_file, kb_id, status) "
            "VALUES (:id, :title, :domain, :source_type, :source_file, :kb_id, :status)",
            {
                "id": p["id"], "title": p["title"], "domain": p.get("domain"),
                "source_type": p.get("source_type"), "source_file": p.get("source_file"),
                "kb_id": p.get("kb_id"), "status": p.get("status", "draft"),
            }
        )

    for a in ARTIFACTS:
        cur.execute(
            "INSERT OR IGNORE INTO artifacts (id, paper_id, title, artifact_type, content_note, kb_id, ratified) "
            "VALUES (:id, :paper_id, :title, :artifact_type, :content_note, :kb_id, :ratified)",
            a
        )

    for a in ATOMS:
        cur.execute(
            "INSERT OR IGNORE INTO atoms (id, domain, title, content, kb_id, ratified) "
            "VALUES (:id, :domain, :title, :content, :kb_id, :ratified)",
            a
        )

    conn.commit()

    p_n = cur.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    a_n = cur.execute("SELECT COUNT(*) FROM atoms WHERE ratified=1").fetchone()[0]
    print(f"ada.db seeded: {p_n} papers, {a_n} ratified atoms")
    print(f"DB: {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    seed()
