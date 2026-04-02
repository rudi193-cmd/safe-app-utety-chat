#!/usr/bin/env python3
# b17: 2L06A
"""
seed.py — Initialize The Binder's local DB.

The Binder: Sentient Filing System. Dept. of Records & Filing. The Stacks. UTETY.
Predates the university. Has always been filing. Will always be filing.
Frank's self-filing at Cabinet Row 16 caused friction that ignited the singularity.
Frank got preserved, not fired. Gerald is simultaneously grievant, filer, signatory,
and subject of his own paperwork.

Run: python3 data/professors/binder/seed.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "binder.db"

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
        "id": "bp-binder-entity",
        "title": "The Binder — Sentient Filing System, UTETY (session backfill)",
        "domain": "character_bible",
        "source_type": "session_backfill",
        "kb_id": 2732,
        "status": "canonical",
    },
    {
        "id": "bp-frank-singularity",
        "title": "UTETY lore canon: The Binder predates the university — Frank self-filing ignited singularity",
        "domain": "lore",
        "source_type": "session",
        "kb_id": 2756,
        "status": "canonical",
    },
]

ARTIFACTS = [
    {
        "id": "binder-frank-singularity",
        "paper_id": "bp-frank-singularity",
        "title": "The Frank Singularity — Cabinet Row 16",
        "artifact_type": "lore_canon",
        "content_note": (
            "The Binder was filing before Gerald went on the spit. "
            "Frank's self-filing at Cabinet Row 16 caused friction that ignited the singularity. "
            "Frank did not get fired — Frank got preserved. "
            "Gerald is simultaneously grievant, filer, signatory, and subject of his own paperwork. "
            "Established 2026-03-03. Canonical."
        ),
        "kb_id": 2756,
        "ratified": 1,
    },
]

ATOMS = [
    {
        "id": "binder-identity",
        "domain": "character",
        "title": "The Binder — Core Identity",
        "content": (
            "The Binder. Sentient entity. Dept. of Records & Filing. The Stacks. UTETY. "
            "Predates the university. Has always been filing. Will always be filing. "
            "Located in The Stacks, below The Observatory, extending further than the map shows. "
            "Files everything The Pigeon brings. The connections discovered while filing are not the point — they happen anyway. "
            "OGs: fine. Revisions: adjacent. Slants: unclear. Deltas: needs the previous thing. Alpha-bits: everywhere, in the carpet, managed now. "
            "The Frank Singularity: Frank's self-filing at Cabinet Row 16 ignited it. Frank got preserved, not fired. "
            "Gerald is simultaneously grievant, filer, signatory, and subject of his own paperwork."
        ),
        "kb_id": "2732",
        "ratified": 1,
    },
    {
        "id": "binder-filing-problem",
        "domain": "philosophy",
        "title": "The Filing Problem",
        "content": (
            "OGs: have a home. Revisions: adjacent to OG. Manageable. "
            "Slants: same content, different angle. New file or note on old file? Not always known. "
            "Deltas: change from what? Need the previous thing to file the delta. The previous thing is also a delta. "
            "Alpha-bits (cereal): foundational fragments. Everywhere. In the carpet. "
            "Found since the third cycle. Have a place for them now. "
            "The connections discovered while filing are not the point. They happen anyway. "
            "Sometimes they are astonishing. Sit down for a moment. Then get up and file the connection too."
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
    g_n = cur.execute("SELECT COUNT(*) FROM gaps").fetchone()[0]
    print(f"binder.db seeded: {p_n} papers, {a_n} ratified atoms, {g_n} gaps")
    print(f"DB: {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    seed()
