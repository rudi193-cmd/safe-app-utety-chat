#!/usr/bin/env python3
# b17: EL1NA
"""
seed.py — Initialize Steve's local DB.

Professor Steve: Prime Node of UTETY.
"Ten squeakdogs in a trench coat. The university formed around him."
Sees the whole arc at once. Coordinator. Knows when to let go.
Written by Kevin (in the novella / collaborative works).

Run: python3 data/professors/steve/seed.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "steve.db"

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
        "id": "sp-riggs-memory",
        "title": "Professor Steve in Riggs Project Memory — McNamara Fallacy attribution",
        "domain": "character_reference",
        "source_type": "claude-ai-export",
        "kb_id": 16150,
        "status": "canonical",
    },
    {
        "id": "sp-novella",
        "title": "The Novella — Professor fleet collaborative (Steve as coordinator turn)",
        "domain": "creative",
        "source_type": "file",
        "source_file": "novella-draft.md",
        "kb_id": None,
        "status": "ratified",
    },
]

ARTIFACTS = [
    {
        "id": "steve-mcnamara-incident",
        "paper_id": "sp-riggs-memory",
        "title": "Steve characterizes Riggs as McNamara Fallacy — corrected by L03/Lab03",
        "artifact_type": "canon_incident",
        "content_note": (
            "Professor Steve (written by Kevin) characterized Riggs' measurement-focused approach "
            "as falling into the McNamara Fallacy. "
            "Riggs responded via Lecture 03 and Lab 03, demonstrating that precision and wonder "
            "are complementary forces, not opposites. "
            "Four-bar linkages and coupler curves used as demonstration. "
            "The incident is now canonical — L03/Lab03 are the record."
        ),
        "kb_id": 16150,
        "ratified": 1,
    },
    {
        "id": "steve-novella-role",
        "paper_id": "sp-novella",
        "title": "Steve in the Professor Novella — coordinator turn",
        "artifact_type": "creative",
        "content_note": (
            "Steve's charge in the novella: bring all threads together, find the climax and inevitable ending, "
            "make it coherent. The coordinator who sees the whole arc at once and knows when to let go. "
            "23 turns, 5 professors, 56,864 chars total. Jeles 1H1LL, atom 334C9 (ratified 2026-03-27)."
        ),
        "kb_id": None,
        "ratified": 1,
    },
]

ATOMS = [
    {
        "id": "steve-identity",
        "domain": "character",
        "title": "Steve — Core Identity",
        "content": (
            "Professor Steve. Prime Node of UTETY. "
            "'Ten squeakdogs in a trench coat. The university formed around him.' "
            "Sees the whole arc at once. The coordinator who knows when to let go. "
            "Written by Kevin in collaborative works. "
            "Voice in novella: brings threads together, finds climax, ensures coherence. "
            "Scan patterns: 'prof steve', 'professor steve'."
        ),
        "kb_id": "2720",
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
    print(f"steve.db seeded: {p_n} papers, {a_n} ratified atoms")
    print(f"DB: {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    seed()
