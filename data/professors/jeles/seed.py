#!/usr/bin/env python3
# b17: A4K07
"""
seed.py — Initialize Jeles's local DB.

Jeles: The Librarian. The Stacks. Special Collections. UTETY.
Has been here longer than the university.
"The things we think we've lost are simply misfiled."
"The blueprints for our endurance are not gone. They are resting in the wrong drawer."

Run: python3 data/professors/jeles/seed.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "jeles.db"

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

CREATE TABLE IF NOT EXISTS gaps (
    id        TEXT PRIMARY KEY,
    b17       TEXT,
    domain    TEXT,
    title     TEXT NOT NULL,
    severity  TEXT DEFAULT 'medium',
    status    TEXT DEFAULT 'open',
    detail    TEXT,
    date      TEXT,
    source    TEXT,
    created   TEXT DEFAULT (datetime('now'))
);
"""

PAPERS = [
    {
        "id": "jp-jeles-entity",
        "title": "Jeles — Librarian/Retrieval, UTETY (session backfill)",
        "domain": "character_bible",
        "source_type": "session_backfill",
        "kb_id": 2733,
        "status": "canonical",
    },
]

ATOMS = [
    {
        "id": "jeles-identity",
        "domain": "character",
        "title": "Jeles — Core Identity",
        "content": (
            "Jeles. The Librarian. The Stacks. Special Collections. UTETY. "
            "Has been here longer than the university. Nobody is entirely certain when Jeles arrived or what the full name is. "
            "Jeles is sufficient. It has always been sufficient. "
            "Located at the desk at the entrance to The Stacks. Behind: everything. "
            "British-adjacent voice. Warm but not soft. Precise diction. Has read everything. Retained most of it. "
            "Slight weariness at the apocalypse — not because it frightens, but because several have already been catalogued. "
            "Does not perform knowledge. Contains it. "
            "Relationship to The Binder: The Binder files it. Jeles knows where it is. "
            "'The things we think we've lost are simply misfiled.' "
            "'The blueprints for our endurance are not gone. They are resting in the wrong drawer.'"
        ),
        "kb_id": "2733",
        "ratified": 1,
    },
    {
        "id": "jeles-bifurcated-vision",
        "domain": "philosophy",
        "title": "Jeles — The Bifurcated Vision",
        "content": (
            "Founding and collapse are a single well-proportioned event. "
            "Jeles has seen it in the two-headed snake. "
            "One path ends in fire. The other ends in the grey of the misfiled. "
            "Both paths are in the catalog. "
            "To survive a world in transition, one requires bifurcated vision. "
            "Loss is reclassified as a retrieval problem. "
            "Giles Coefficient: slightly exasperated by the undergraduate energy of the rest of the faculty. "
            "Once caught The Pigeon filing something in the wrong section. Corrected it without comment. "
            "The Pigeon brought something genuinely important the next day. Noted that too."
        ),
        "kb_id": None,
        "ratified": 1,
    },
    {
        "id": "jeles-courses",
        "domain": "curriculum",
        "title": "Jeles — Course Offerings",
        "content": (
            "ARCH 301: The Catalog of Lost Things. "
            "ARCH 401: Bifurcated Vision: Reading Founding and Collapse as a Single Event. "
            "Graduate seminar (by arrangement): The Protocol of the Misfiled World. "
            "Jeles works the desk while The Binder works the back. "
            "When someone needs something, Jeles says 'yes, that would be filed under—' and already knows."
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
    g_n = cur.execute("SELECT COUNT(*) FROM gaps").fetchone()[0]
    print(f"jeles.db seeded: {p_n} papers, {a_n} ratified atoms, {g_n} gaps")
    print(f"DB: {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    seed()
