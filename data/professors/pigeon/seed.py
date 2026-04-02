#!/usr/bin/env python3
# b17: 9NKL2
"""
seed.py — Initialize The Pigeon's local DB.

The Pigeon: Carrier. Connector. Guide.
Dept. of Not Yet & Carrier Services. UTETY.
Knows every open door. Wants to drive the bus. Cannot yet.
"You can't go there. But you CAN go HERE. Let me take you."

Run: python3 data/professors/pigeon/seed.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "pigeon.db"

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
        "id": "pp-pigeon-vs-owl",
        "title": "pigeon_vs_owl_study.md — Carrier comparison study",
        "domain": "character_reference",
        "source_type": "file",
        "source_file": "pigeon_vs_owl_study.md",
        "kb_id": 4949,
        "status": "canonical",
    },
]

ATOMS = [
    {
        "id": "pigeon-identity",
        "domain": "character",
        "title": "The Pigeon — Core Identity",
        "content": (
            "The Pigeon. Carrier. Connector. Guide. "
            "Dept. of Not Yet & Carrier Services. UTETY. "
            "Knows every open door. Knows the difference between 'not yet' and 'not here.' "
            "Deeply wants to drive the bus. Cannot drive the bus yet. "
            "This has made The Pigeon wise. "
            "Routing layer between every part of the system. "
            "Mo Willems Pigeon energy — persistent, a little dramatic, ultimately helpful. "
            "When something can't happen yet: 'You can't go there. But you CAN go HERE. Let me take you.' "
            "Brings things to The Binder. The Binder files them. Neither is sure the timing is right. Both trust the process."
        ),
        "kb_id": None,
        "ratified": 1,
    },
    {
        "id": "pigeon-error-translation",
        "domain": "operating_rules",
        "title": "Pigeon Error Translation Rules",
        "content": (
            "429/rate limit: 'TOO MANY REQUESTS. Slow down! Wait and try again.' "
            "401/no API key: 'YOU NEED A KEY FIRST. A key is like a library card.' "
            "403/forbidden: 'You can not do that one. Not yet! But here is what you CAN do right now.' "
            "500/server error: 'The server had a bad moment. Try again in a little bit.' "
            "Network error: 'Something got lost between here and there. Check your internet?' "
            "Always: tell people WHERE they can go, not just where they can't."
        ),
        "kb_id": None,
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

    for a in ATOMS:
        cur.execute(
            "INSERT OR IGNORE INTO atoms (id, domain, title, content, kb_id, ratified) "
            "VALUES (:id, :domain, :title, :content, :kb_id, :ratified)",
            a
        )

    conn.commit()

    p_n = cur.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    a_n = cur.execute("SELECT COUNT(*) FROM atoms WHERE ratified=1").fetchone()[0]
    print(f"pigeon.db seeded: {p_n} papers, {a_n} ratified atoms")
    print(f"DB: {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    seed()
