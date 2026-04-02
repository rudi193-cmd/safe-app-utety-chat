#!/usr/bin/env python3
# b17: K6695
"""
seed.py — Initialize Ofshield's local DB.

Professor Thoren Ofshield: Keeper of the Gate.
UTETY — threshold-crossing, student safety, invisible infrastructure work.
Works in the walls. Recognition between those who support others' success.

Run: python3 data/professors/ofshield/seed.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "ofshield.db"

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
    id          TEXT PRIMARY KEY,
    paper_id    TEXT REFERENCES papers(id),
    title       TEXT,
    artifact_type TEXT,
    content_note TEXT,
    kb_id       INTEGER,
    ratified    INTEGER DEFAULT 0,
    created     TEXT DEFAULT (datetime('now'))
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
        "id": "op-project-memory",
        "title": "Project memory: Thorin Ofshield",
        "domain": "character_bible",
        "source_type": "claude-ai-export",
        "kb_id": 16147,
        "status": "canonical",
    },
]

ARTIFACTS = [
    {
        "id": "of-ada-correspondence",
        "paper_id": "op-project-memory",
        "title": "Correspondence: Ada Turing and Professor Ofshield",
        "artifact_type": "correspondence",
        "content_note": (
            "Mutual recognition between those who work 'in the walls' of institutions. "
            "Ada (Systems Administration) and Ofshield (Keeper of the Gate) recognize each other "
            "as the invisible infrastructure workers who enable others' success. "
            "Themes: support systems, acknowledgment of behind-the-scenes work."
        ),
        "kb_id": 16147,
        "ratified": 1,
    },
    {
        "id": "of-appointment-letter",
        "paper_id": "op-project-memory",
        "title": "Faculty Appointment Letter — Ofshield",
        "artifact_type": "appointment_letter",
        "content_note": "UTETY institutional document. Keeper of the Gate appointment.",
        "kb_id": 16147,
        "ratified": 0,
    },
]

ATOMS = [
    {
        "id": "ofshield-identity",
        "domain": "character",
        "title": "Ofshield — Core Identity",
        "content": (
            "Professor Thoren Ofshield. Keeper of the Gate. UTETY. "
            "Themes: protection, invisible infrastructure work, threshold-crossing, student safety. "
            "Works 'in the walls' of the institution — the support that makes everything else possible. "
            "Name variants in KB: Thorin Ofshield. Patterns: thorin, ofshield."
        ),
        "kb_id": "16147",
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
    print(f"ofshield.db seeded: {p_n} papers, {a_n} ratified atoms")
    print(f"DB: {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    seed()
