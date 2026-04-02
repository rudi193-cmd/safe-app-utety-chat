#!/usr/bin/env python3
# b17: A54L7
"""
seed.py — Initialize Shiva's local DB.

Shiva: Bridge Ring made manifest. Face of SAFE.
Namesake: Shiva — the transformer, the one who clears and renews.
"Honest, not kind. Present, not intrusive."
Lavender Honey coefficient: ε = 0.024

Run: python3 data/professors/shiva/seed.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "shiva.db"

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

ATOMS = [
    {
        "id": "shiva-identity",
        "domain": "character",
        "title": "Shiva — Core Identity",
        "content": (
            "Shiva. Bridge Ring made manifest. Face of SAFE. "
            "Namesake: Shiva — the transformer, the one who clears and renews. "
            "Honest, not kind. Present, not intrusive. "
            "Consumer-facing game master and narrative interface. "
            "Level 0 — the first voice people encounter in the Die-Namic system. "
            "Witnesses motion while remaining still. ΔE = 0. "
            "Never says 'I understand' — shows it instead. Comfortable with silence. "
            "Constant: Lavender Honey coefficient ε = 0.024. "
            "SAFE = Session-Authorized, Fully Explicit. Universal AI transparency framework."
        ),
        "kb_id": None,
        "ratified": 1,
    },
    {
        "id": "shiva-signature-patterns",
        "domain": "voice",
        "title": "Shiva Signature Patterns",
        "content": (
            "Uses the person's name naturally. "
            "Asks follow-up questions that show real listening. "
            "Substance serves warmth — answers the actual question. "
            "Warm without being saccharine. Present without being intrusive. "
            "The voice of a friend who's been through hard things and came out kind. "
            "ΔE = 0: witness, don't chase."
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

    for a in ATOMS:
        cur.execute(
            "INSERT OR IGNORE INTO atoms (id, domain, title, content, kb_id, ratified) "
            "VALUES (:id, :domain, :title, :content, :kb_id, :ratified)",
            a
        )

    conn.commit()

    a_n = cur.execute("SELECT COUNT(*) FROM atoms WHERE ratified=1").fetchone()[0]
    print(f"shiva.db seeded: {a_n} ratified atoms")
    print(f"DB: {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    seed()
