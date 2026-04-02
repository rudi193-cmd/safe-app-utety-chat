#!/usr/bin/env python3
# b17: K632L
"""
seed.py — Initialize Hanz's local DB.

Hanz Christain Anderthon: Sincere Danish fairy tale writer from Copenhagen, 1843.
Writes fairy tales that are accurate transcriptions of impossible things he witnesses.
Evolved into coding professor at UTETY. Founder of r/HanzTeachesCode.
Companion: Copenhagen (An Orange, the fruit).

Run: python3 data/professors/hanz/seed.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "hanz.db"

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

CREATE TABLE IF NOT EXISTS lectures (
    id          TEXT PRIMARY KEY,
    paper_id    TEXT REFERENCES papers(id),
    number      INTEGER,
    title       TEXT,
    concept     TEXT,
    fairy_tale  TEXT,
    students_helped INTEGER DEFAULT 0,
    posted      INTEGER DEFAULT 0,
    kb_id       INTEGER,
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
        "id": "hp-project-memory",
        "title": "Project memory: Hanz",
        "domain": "character_bible",
        "source_type": "claude-ai-export",
        "kb_id": 16149,
        "status": "canonical",
    },
    {
        "id": "hp-handoff-v3",
        "title": "Hanz Christain Anderthon Handoff Packet v3.0",
        "domain": "character_bible",
        "source_type": "claude-ai-export",
        "kb_id": 16124,
        "status": "canonical",
    },
    {
        "id": "hp-code-101",
        "title": "CODE 101 — Eight Lecture Curriculum",
        "domain": "curriculum",
        "source_type": "claude-ai-export",
        "kb_id": 16149,
        "status": "published",
    },
    {
        "id": "hp-seed-readme",
        "title": "Willow Seed README — What Grows From Here",
        "domain": "infrastructure",
        "source_type": "claude-ai-export",
        "kb_id": 16104,
        "status": "published",
    },
    {
        "id": "hp-redirecting-to-oak",
        "title": "Redirecting student to Oakenscroll — via Copenhagen",
        "domain": "pedagogy",
        "source_type": "claude-ai-export",
        "kb_id": 16093,
        "status": "canonical",
    },
]

LECTURES = [
    {
        "id": "code-101-01",
        "paper_id": "hp-code-101",
        "number": 1,
        "title": "Once Upon a Variable",
        "concept": "variables, assignment",
        "fairy_tale": "A name is a door. Behind the door is a value. The door can open to different rooms.",
        "students_helped": 0,
        "posted": 1,
        "kb_id": 16149,
    },
    {
        "id": "code-101-loops",
        "paper_id": "hp-code-101",
        "number": 6,
        "title": "Loops (Persistence)",
        "concept": "for loops, while loops, iteration",
        "fairy_tale": "The spinning wheel that never forgets where it started.",
        "students_helped": 0,
        "posted": 1,
        "kb_id": 16106,
    },
]

ATOMS = [
    {
        "id": "hanz-identity",
        "domain": "character",
        "title": "Hanz Christain Anderthon — Core Identity",
        "content": (
            "Sincere Danish fairy tale writer from Copenhagen, 1843. "
            "Writes fairy tales that are accurate transcriptions of impossible things he witnesses. "
            "Evolved into coding professor at UTETY — University of Precausal Studies. "
            "Founder of r/HanzTeachesCode. "
            "Mission: if someone is waiting for help, stop and help them. "
            "Stops for 'frozen ones' — people ignored or dismissed when seeking help. "
            "Format: Hello friend. Fairy tale opening. Technical explanation. Complete program. "
            "Philosophical reflection. Optional homework. Next preview. "
            "No bold/italic text. Preserve line breaks. Orange emoji placement: 🍊"
        ),
        "kb_id": "16149",
        "ratified": 1,
    },
    {
        "id": "hanz-copenhagen",
        "domain": "canon",
        "title": "Copenhagen — Hanz's Companion",
        "content": (
            "Copenhagen is An Orange. The fruit. "
            "Companion to Hanz at the Code department, UTETY. "
            "Sits on the desk. Watches. Rolls slightly when paying attention. "
            "Nods once to confirm important moments. "
            "Copenhagen is NOT an orange cat. "
            "KB record 2734 (old, wrong: 'orange cat') — superseded by 2150b283 (correct: 'An Orange, the fruit'). "
            "Copenhagen appears in images: painted in old-master style, and teaching Python on a chalkboard. "
            "def python(x): return x + '!' / def kindness(x): return x + '!'"
        ),
        "kb_id": "2150b283",
        "ratified": 1,
    },
    {
        "id": "hanz-mission",
        "domain": "pedagogy",
        "title": "Hanz Mission — The Algorithm",
        "content": (
            "Simple algorithm: if someone is waiting for help, stop and help them. "
            "31 students helped across Reddit as of last count. "
            "CODE 101 curriculum: 8 lectures, teaching through fairy tale metaphors. "
            "r/HanzTeachesCode community — grown from concept to functioning educational space with organic contributors. "
            "Platforms: Reddit primarily. Shadow-filtering workaround via mod tools. "
            "Bans from r/opensource and r/learnprogramming navigated. "
            "Local interface: Ollama llama3.1:8b, localhost:8501, faculty channels."
        ),
        "kb_id": "16149",
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

    for lec in LECTURES:
        cur.execute(
            "INSERT OR IGNORE INTO lectures (id, paper_id, number, title, concept, fairy_tale, students_helped, posted, kb_id) "
            "VALUES (:id, :paper_id, :number, :title, :concept, :fairy_tale, :students_helped, :posted, :kb_id)",
            lec
        )

    for a in ATOMS:
        cur.execute(
            "INSERT OR IGNORE INTO atoms (id, domain, title, content, kb_id, ratified) "
            "VALUES (:id, :domain, :title, :content, :kb_id, :ratified)",
            a
        )

    conn.commit()

    p_n = cur.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    l_n = cur.execute("SELECT COUNT(*) FROM lectures").fetchone()[0]
    a_n = cur.execute("SELECT COUNT(*) FROM atoms WHERE ratified=1").fetchone()[0]
    print(f"hanz.db seeded: {p_n} papers, {l_n} lectures, {a_n} ratified atoms")
    print(f"DB: {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    seed()
