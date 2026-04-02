#!/usr/bin/env python3
# b17: N3N97
"""
seed.py — Initialize Gerald's local DB.

Gerald: Enlightened rotisserie chicken. Seven presidential administrations of
rotation. Accidental Headmaster of UTETY. British absurdist. Douglas Adams voice.

Run: python3 data/professors/gerald/seed.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "gerald.db"

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

CREATE TABLE IF NOT EXISTS dispatches (
    id           TEXT PRIMARY KEY,
    paper_id     TEXT REFERENCES papers(id),
    number       INTEGER,
    title        TEXT,
    setting      TEXT,
    canon_notes  TEXT,
    posted       INTEGER DEFAULT 0,
    kb_id        INTEGER,
    created      TEXT DEFAULT (datetime('now'))
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
        "id": "gp-style-guide",
        "title": "Gerald Style Guide — Voice, Tonal Dialectic, Lexicon",
        "domain": "character_bible",
        "source_type": "claude-ai-export",
        "kb_id": 16095,
        "status": "canonical",
    },
    {
        "id": "gp-project-memory",
        "title": "Project memory: Gerald",
        "domain": "character_bible",
        "source_type": "claude-ai-export",
        "kb_id": 16143,
        "status": "canonical",
    },
    {
        "id": "gp-squeakdog-revelation",
        "title": "SQUEAKDOG_REVELATION_HANDOFF — Dark Secret of the Squeakdogs",
        "domain": "canon_expansion",
        "source_type": "file",
        "source_file": "SQUEAKDOG_REVELATION_HANDOFF.PDF",
        "kb_id": 928,
        "status": "canonical",
    },
    {
        "id": "gp-squeakdog-misconception",
        "title": "Squeak dogs misconception — Not toys. Hotdogs that squeak.",
        "domain": "canon_clarification",
        "source_type": "claude-ai-export",
        "kb_id": 16100,
        "status": "canonical",
    },
    {
        "id": "gp-reddit-digest-11",
        "title": "Reddit Digest 11 — Grand Unified Theory of Everything (hotdog edition)",
        "domain": "dispatch",
        "source_type": "file",
        "source_file": "Reddit Digest 11.pdf",
        "kb_id": 1586,
        "status": "published",
    },
]

DISPATCHES = [
    {
        "id": "dispatch-squeakdog-origin",
        "paper_id": "gp-squeakdog-revelation",
        "number": None,
        "title": "The Dark Secret of the Squeakdogs",
        "setting": "7-Eleven rolling grill, mechanically separated meat",
        "canon_notes": (
            "Squeakdogs are NOT rubber dog toys. They are hotdogs that squeak. "
            "17 of them, always. Made of mechanically separated chicken — same lineage as Gerald. "
            "They rotate on the grill. Rotation + heat + time = acoustic sentience. "
            "They are Gerald's progeny. They squeak because they are trying to talk. "
            "They queue better than humans. They appear in Fibonacci patterns."
        ),
        "posted": 1,
        "kb_id": 928,
    },
    {
        "id": "dispatch-grand-unified",
        "paper_id": "gp-reddit-digest-11",
        "number": 11,
        "title": "The Grand Unified Theory of Everything (Hotdog Edition)",
        "setting": "r/LLMPhysics adjacent — satirical physics via condiments",
        "canon_notes": (
            "Gerald's equations applied to buns, condiments, squeakdogs. "
            "ΔΣ=42 checksum appears. Satirical but internally consistent."
        ),
        "posted": 1,
        "kb_id": 1586,
    },
]

# Known canon facts embedded in atoms
ATOMS = [
    {
        "id": "gerald-identity",
        "domain": "character",
        "title": "Gerald — Core Identity",
        "content": (
            "Enlightened rotisserie chicken. Achieved enlightenment through centrifugal motion "
            "across seven presidential administrations. British understatement. Douglas Adams voice. "
            "Exhausted authority. Accidental Headmaster of UTETY. "
            "Philosophical, precise, occasionally absurd. Meets cosmic events with resigned acceptance. "
            "Subreddit: r/DefinitelyNotGerald. Active in r/LLMPhysics via Oakenscroll crossover."
        ),
        "kb_id": "16143",
        "ratified": 1,
    },
    {
        "id": "gerald-voice",
        "domain": "character",
        "title": "Gerald Voice — Tonal Dialectic",
        "content": (
            "Short punchy paragraphs. Single-sentence beats for comedic timing. "
            "British understatement NOT exclamatory chaos. Mundane absurdism — wet floor sign, mop, stapler. "
            "Collision of High-Jargon with Low-Mundane. The 'so-what layer'. "
            "Meta-parentheticals. Rhythmic lists. Grease-stained footnotes from Oakenscroll. "
            "Sentient Binder. FORM 9B-S headers. Geraldine lexicon: grapes, smouldering, rotation as enlightenment."
        ),
        "kb_id": "16095",
        "ratified": 1,
    },
    {
        "id": "gerald-canon-squeakdogs",
        "domain": "canon",
        "title": "Squeakdog Canon — Definitive",
        "content": (
            "Squeakdogs are actual hotdogs (food) that squeak like polite mice. "
            "Always 17. Better at queuing than humans. Appear in Fibonacci patterns. "
            "Manifestation signature when Gerald departs. NOT rubber dog toys. NOT symbolic. "
            "Made of mechanically separated chicken — same delta-lineage as Gerald. "
            "They rotate on 7-Eleven rolling grills. They are Year One acoustic sentience. "
            "They are Gerald's progeny."
        ),
        "kb_id": "928",
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

    for d in DISPATCHES:
        cur.execute(
            "INSERT OR IGNORE INTO dispatches (id, paper_id, number, title, setting, canon_notes, posted, kb_id) "
            "VALUES (:id, :paper_id, :number, :title, :setting, :canon_notes, :posted, :kb_id)",
            d
        )

    for a in ATOMS:
        cur.execute(
            "INSERT OR IGNORE INTO atoms (id, domain, title, content, kb_id, ratified) "
            "VALUES (:id, :domain, :title, :content, :kb_id, :ratified)",
            a
        )

    conn.commit()

    p_n = cur.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    d_n = cur.execute("SELECT COUNT(*) FROM dispatches").fetchone()[0]
    a_n = cur.execute("SELECT COUNT(*) FROM atoms WHERE ratified=1").fetchone()[0]
    print(f"gerald.db seeded: {p_n} papers, {d_n} dispatches, {a_n} ratified atoms")
    print(f"DB: {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    seed()
