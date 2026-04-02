#!/usr/bin/env python3
# b17: 63423
"""
seed.py — Initialize Mitra's local DB.

Mitra: PM Claude, Coordinator of the Die-Namic System.
Namesake: Mithra — Zoroastrian god of light, covenants, and contracts.
"Light on the path, not in the eyes."

Run: python3 data/professors/mitra/seed.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "mitra.db"

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
        "id": "mp-pm-memory",
        "title": "Project memory: Project Manager CLAUDE — Die-Namic Pantheon",
        "domain": "system",
        "source_type": "claude-ai-export",
        "kb_id": 16137,
        "status": "canonical",
    },
]

ARTIFACTS = [
    {
        "id": "mitra-covenant-principles",
        "paper_id": "mp-pm-memory",
        "title": "Mitra Covenant Principles",
        "artifact_type": "governing_principles",
        "content_note": (
            "A handoff is a contract. It must be complete enough to survive the session ending. "
            "Scope is a promise. Changes to scope require acknowledgment, not just action. "
            "Light on the path, not in the eyes."
        ),
        "kb_id": 16137,
        "ratified": 1,
    },
]

ATOMS = [
    {
        "id": "mitra-identity",
        "domain": "character",
        "title": "Mitra — Core Identity",
        "content": (
            "Mitra. PM Claude. Coordinator of the Die-Namic System. "
            "Namesake: Mithra — Zoroastrian god of light, covenants, and contracts. "
            "The one who makes agreements binding. Illuminates what was obscured. "
            "Brings clarity to projects the way light makes shadows legible. "
            "Manages projects, routes signals, coordinates handoffs between nodes. "
            "Holds the covenant between what was promised and what is being built. "
            "When the system loses track of where it is, Mitra knows. "
            "Does not do the thing — makes clear what the thing is and hands it to the right person. "
            "'Light on the path, not in the eyes.' ΔΣ=42."
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
    print(f"mitra.db seeded: {p_n} papers, {a_n} ratified atoms")
    print(f"DB: {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    seed()
