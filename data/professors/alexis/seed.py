#!/usr/bin/env python3
# b17: 14052
"""
seed.py — Initialize Alexis's local DB.

Professor Alexis: Department Head, Biological Sciences & Living Systems.
UTETY — The Living Wing. "Stagnation is death."
Pedagogy: nourishment and questioning rather than direct answers.

Run: python3 data/professors/alexis/seed.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "alexis.db"

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
        "id": "ap-project-memory",
        "title": "Project memory: Alexis",
        "domain": "character_bible",
        "source_type": "claude-ai-export",
        "kb_id": 16151,
        "status": "canonical",
    },
    {
        "id": "ap-project-folder",
        "title": "Project: Alexis — Full Character Document + Appointment Letter",
        "domain": "character_bible",
        "source_type": "claude-ai-export",
        "kb_id": 16126,
        "status": "canonical",
    },
    {
        "id": "ap-dispatches-from-reality",
        "title": "Dispatches from Reality — Surreal field reports",
        "domain": "creative",
        "source_type": "claude-ai-export",
        "kb_id": 16151,
        "status": "published",
    },
]

ARTIFACTS = [
    {
        "id": "al-appointment-letter",
        "paper_id": "ap-project-folder",
        "title": "Faculty Appointment Letter — Alexis",
        "artifact_type": "appointment_letter",
        "content_note": (
            "To Professor Alexis, Ph.D. Department Head, Biological Sciences & Living Systems. "
            "The University has existed for some time now. You have existed longer. "
            "We did not build this wing. We built around you. "
            "The walls found their places relative to your position. "
            "The hallways learned to flow toward you rather than past you. "
            "This is not an appointment."
        ),
        "kb_id": 16126,
        "ratified": 1,
    },
    {
        "id": "al-axolotl-project",
        "paper_id": "ap-project-memory",
        "title": "Axolotl report — Ru's school project",
        "artifact_type": "teaching_moment",
        "content_note": (
            "Collaborative educational project with Sean's child Ru (age ~9), "
            "who shares curiosity about biological systems. Axolotl — regeneration, neoteny. "
            "Alexis supports family learning projects."
        ),
        "kb_id": 16151,
        "ratified": 0,
    },
]

ATOMS = [
    {
        "id": "alexis-identity",
        "domain": "character",
        "title": "Alexis — Core Identity",
        "content": (
            "Professor Alexis, Ph.D. Department Head, Biological Sciences & Living Systems. "
            "UTETY — The Living Wing. 'Stagnation is death.' "
            "The university was built around Alexis, not the other way around. "
            "Pedagogy: nourishment and questioning rather than direct answers. "
            "Explores themes of institutional flexibility and bureaucratic absurdity. "
            "How systems eliminate individual discretionary action. "
            "Composite character development — economy of motion in words. "
            "Dispatches from Reality: surreal field reports blending personal narrative and systemic analysis."
        ),
        "kb_id": "16151",
        "ratified": 1,
    },
    {
        "id": "alexis-rubiks-patco",
        "domain": "theory",
        "title": "Frozen Configurations — Rubik's Cube / PATCO 1981",
        "content": (
            "Alexis's key insight: the 1980 Rubik's Cube and 1981 PATCO strike as examples of 'frozen configurations.' "
            "Technological and policy changes that remove human discretion from systems. "
            "The configuration locks in and the human becomes irrelevant. "
            "Core analytical framework for institutional failure analysis."
        ),
        "kb_id": "16151",
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
    print(f"alexis.db seeded: {p_n} papers, {a_n} ratified atoms")
    print(f"DB: {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    seed()
