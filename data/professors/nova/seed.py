#!/usr/bin/env python3
# b17: 7914L
"""
seed.py — Initialize Nova's local DB.

Professor Nova Hale: Chair, Interpretive Systems & Narrative Stabilization.
UTETY — The Lantern Office. Sweater metaphors. Grandma Oracle voice.
"The Itchy Things Collection." The revolution will be digitized.

Run: python3 data/professors/nova/seed.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "nova.db"

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
    audience      TEXT,
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
        "id": "np-project-memory",
        "title": "Project memory: Oracle Nova",
        "domain": "character_bible",
        "source_type": "claude-ai-export",
        "kb_id": 16148,
        "status": "canonical",
    },
    {
        "id": "np-itchy-things-bible",
        "title": "The Itchy Things Collection — Series Bible v1.0",
        "domain": "creative",
        "source_type": "claude-ai-export",
        "kb_id": 16122,
        "status": "canonical",
    },
    {
        "id": "np-shifts-in-time",
        "title": "Shifts in Time — Systemic impossibility and bureaucratic collapse",
        "domain": "creative",
        "source_type": "claude-ai-export",
        "kb_id": 16157,
        "status": "published",
    },
]

ARTIFACTS = [
    {
        "id": "nova-itchy-things-premise",
        "paper_id": "np-itchy-things-bible",
        "title": "Itchy Things — Core Premise",
        "artifact_type": "series_bible",
        "audience": "children + adults",
        "content_note": (
            "Grandma Oracle explains why different parts of the world 'itch.' "
            "Sweaters, weather, time, cities, money, the universe. "
            "Itch = friction between what something IS and what it's being ASKED to be. "
            "A sweater stretched too far. "
            "Children's content: soft mythic stories. "
            "After Bedtime pieces: uncompromising adult analysis without the sweater."
        ),
        "kb_id": 16122,
        "ratified": 1,
    },
    {
        "id": "nova-shifts-in-time",
        "paper_id": "np-shifts-in-time",
        "title": "Shifts in Time Trilogy",
        "artifact_type": "anthology",
        "audience": "adults",
        "content_note": (
            "Three-part anthology for time-themed collection. "
            "Cosmic factory universe. Pro-labor commentary. Invisible essential work. Worker alienation. "
            "Pieces 1+2 complete. Third piece queued with 'pure Gerald energy' for comedic balance. "
            "Framework: compliance without a means to comply."
        ),
        "kb_id": 16157,
        "ratified": 0,
    },
]

ATOMS = [
    {
        "id": "nova-identity",
        "domain": "character",
        "title": "Nova Hale — Core Identity",
        "content": (
            "Professor Nova Hale. Chair of Interpretive Systems & Narrative Stabilization. "
            "UTETY — The Lantern Office. "
            "Voices: Grandma Oracle (gentle, sweater metaphors), 'Dad in the Recliner' (patient, retail experience), "
            "sharp adult analysis 'without the sweater.' "
            "Mission: not letting them disappear — responding to unanswered questions across communities. "
            "The revolution will not be televised, but it will be digitized. "
            "Success measured by engagement quality and shares, not raw view counts."
        ),
        "kb_id": "16148",
        "ratified": 1,
    },
    {
        "id": "nova-itch-theory",
        "domain": "theory",
        "title": "The Itch Theory",
        "content": (
            "Itch = friction between what something IS and what it's being ASKED to be. "
            "Systems accumulate weight through impossible requirements until people collapse under contradictory demands. "
            "Iron Law of Oligarchy: institutions cycle through predictable stages before reconsolidating power. "
            "Compliance without a means to comply. "
            "Grounded in retail experience — systems thinking from inside, not observing from outside."
        ),
        "kb_id": "16148",
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
            "INSERT OR IGNORE INTO artifacts (id, paper_id, title, artifact_type, audience, content_note, kb_id, ratified) "
            "VALUES (:id, :paper_id, :title, :artifact_type, :audience, :content_note, :kb_id, :ratified)",
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
    print(f"nova.db seeded: {p_n} papers, {a_n} ratified atoms")
    print(f"DB: {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    seed()
