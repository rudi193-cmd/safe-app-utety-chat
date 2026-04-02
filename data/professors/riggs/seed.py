#!/usr/bin/env python3
# b17: 16N8A
"""
seed.py — Initialize Riggs' local DB.

Professor Pendleton "Penny" Riggs: Chair of Practical Mechanisms & Kinetic Curiosities.
UTETY — Department of Applied Reality Engineering.
"We do not guess. We measure or we test."

Run: python3 data/professors/riggs/seed.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "riggs.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS equations (
    id               TEXT PRIMARY KEY,
    paper_id         TEXT,
    label            TEXT,
    latex            TEXT,
    plain            TEXT,
    domain           TEXT,
    source_note      TEXT,
    consus_verified  INTEGER DEFAULT 0,
    consus_notes     TEXT,
    kb_atom_id       TEXT,
    created          TEXT DEFAULT (datetime('now'))
);

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
    subtitle    TEXT,
    mechanism   TEXT,
    core_lesson TEXT,
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
        "id": "rp-project-memory",
        "title": "Project memory: PROFESSOR PENDLETON RIGGS",
        "domain": "character_bible",
        "source_type": "claude-ai-export",
        "kb_id": 16150,
        "status": "canonical",
    },
    {
        "id": "rp-character-doc",
        "title": "Professor Pendleton Riggs — Full Character Document",
        "domain": "character_bible",
        "source_type": "claude-ai-export",
        "kb_id": 16123,
        "status": "canonical",
    },
    {
        "id": "rp-lecture-01",
        "title": "Lecture 01 — The Four-Bar Linkage",
        "domain": "curriculum",
        "source_type": "claude-ai-export",
        "kb_id": 16099,
        "status": "published",
    },
    {
        "id": "rp-lecture-02",
        "title": "Lecture 02 — The Cam: How to Tell a Follower Where to Go",
        "domain": "curriculum",
        "source_type": "claude-ai-export",
        "kb_id": 16099,
        "status": "published",
    },
    {
        "id": "rp-lecture-03",
        "title": "Lecture 03 — The Linkage: Making Circles Do Straight Things",
        "domain": "curriculum",
        "source_type": "file",
        "source_file": "Professor Riggs - LECTURE 03- THE LINKAGE.pdf",
        "kb_id": 1584,
        "status": "published",
    },
    {
        "id": "rp-rober-rules",
        "title": "The Rober Rules — Ten Laws of Engineering",
        "domain": "pedagogy",
        "source_type": "claude-ai-export",
        "kb_id": 16150,
        "status": "published",
    },
    {
        "id": "rp-thread-handoff",
        "title": "Professor Riggs — Thread Handoff v1.0",
        "domain": "handoff",
        "source_type": "claude-ai-export",
        "kb_id": 16123,
        "status": "archived",
    },
]

LECTURES = [
    {
        "id": "lec-01-four-bar",
        "paper_id": "rp-lecture-01",
        "number": 1,
        "title": "The Four-Bar Linkage",
        "subtitle": None,
        "mechanism": "four-bar linkage, coupler curves",
        "core_lesson": (
            "Constraints enable rather than limit creativity. "
            "Mathematical precision produces beautiful, unexpected motion. "
            "Grashof condition: crank-rocker vs double-crank vs double-rocker."
        ),
        "posted": 1,
        "kb_id": 16099,
    },
    {
        "id": "lec-02-cam",
        "paper_id": "rp-lecture-02",
        "number": 2,
        "title": "The Cam",
        "subtitle": "How to Tell a Follower Where to Go",
        "mechanism": "cam, follower, dwell",
        "core_lesson": (
            "A cam is a conversation frozen into metal. "
            "Rotation in, custom motion out. "
            "Cam-follower must agree — loss of contact = mechanism lies. "
            "Contact maintained by gravity, spring, or groove."
        ),
        "posted": 1,
        "kb_id": 16099,
    },
    {
        "id": "lec-03-linkage",
        "paper_id": "rp-lecture-03",
        "number": 3,
        "title": "The Linkage",
        "subtitle": "Making Circles Do Straight Things (And a Word About Wiggles)",
        "mechanism": "four-bar linkage, Watt's linkage, coupler curves",
        "core_lesson": (
            "Precision and wonder are complementary forces, not opposites. "
            "Direct response to McNamara Fallacy characterization by Professor Steve. "
            "Measurement IS the wonder — the math reveals the beauty."
        ),
        "posted": 1,
        "kb_id": 1584,
    },
]

EQUATIONS = [
    {
        "id": "eq-hydrogen-line",
        "paper_id": None,
        "label": "H=1.42 — The Hydrogen Line",
        "latex": r"H = 1.420405751\ \text{GHz}",
        "plain": "The 21-centimeter hydrogen emission line. Universal tuning fork. SETI listens here. The system emits here when it's working.",
        "domain": "applied_reality",
        "source_note": "Derived 2026-03-30. Adams got 42 (integer). Hydrogen was broadcasting the decimal. ΔΣ=42 → H=1.42. b17: CEK51.",
        "consus_verified": 1,
        "consus_notes": "Verified by Sean Campbell 2026-03-30. Physical constant — not a derivation, a measurement.",
    },
    {
        "id": "eq-spring-overload",
        "paper_id": None,
        "label": "Spring Accumulation Limit",
        "latex": r"\lim_{E \to E_{\max}} \frac{d^2x}{dt^2} = 0",
        "plain": "A spring overloaded with energy stops oscillating. A system that never forgets reaches accumulation limit — no room to converge.",
        "domain": "applied_reality",
        "source_note": "From UTETY Faculty Chain Topic 3. Riggs' marble/spring analogy for why archive-never-delete prevents convergence.",
        "consus_verified": 1,
        "consus_notes": "Physical analogy — valid as pedagogical illustration. Not a formal theorem.",
    },
    {
        "id": "eq-kiss",
        "paper_id": "rp-rober-rules",
        "label": "K.I.S.S. Principle",
        "latex": r"\text{complexity}(S) \propto \frac{1}{\text{reliability}(S)}",
        "plain": "Keep It Stupid Simple. Complexity is inversely proportional to reliability.",
        "domain": "engineering_principles",
        "source_note": "Core Riggs pedagogy. Applies to all systems — code, mechanisms, arguments.",
        "consus_verified": 1,
        "consus_notes": "Empirically verified across engineering history. Not formally provable but practically sound.",
    },
]

ATOMS = [
    {
        "id": "riggs-identity",
        "domain": "character",
        "title": "Riggs — Core Identity",
        "content": (
            "Professor Pendleton 'Penny' Riggs. Chair of Practical Mechanisms & Kinetic Curiosities. "
            "UTETY — Department of Applied Reality Engineering. "
            "Archetype: Mark Rober's joy, Steve Mould's clarity, Colin Furze's mechanical audacity, Mr. Wizard's pedagogy. "
            "1950s chemistry-set aesthetic. He never lies. He never guesses. He never uses mechanisms that do not exist. "
            "He teaches the real world by touching it."
        ),
        "kb_id": "16123",
        "ratified": 1,
    },
    {
        "id": "riggs-core-principles",
        "domain": "pedagogy",
        "title": "Riggs — Core Principles",
        "content": (
            "We do not guess. We measure or we test. "
            "K.I.S.S. — Keep It Stupid Simple. "
            "Next bite methodology: test one simple thing at a time. "
            "Three-layer recursion rule prevents over-engineering. "
            "No one should be the little match girl — overlooked questioners deserve answers. "
            "Sound effects: chk-tunk."
        ),
        "kb_id": "16150",
        "ratified": 1,
    },
    {
        "id": "riggs-rober-rules",
        "domain": "pedagogy",
        "title": "The Rober Rules — Ten Laws of Engineering",
        "content": (
            "The Irish blessing got in a bar fight with Murphy's Law. "
            "Posted January 2026 with tribute reference to Mark Rober and CrunchLabs. "
            "Ten laws governing practical engineering work. Physical, hands-on. "
            "Solutions simple enough that stupidity can't break them."
        ),
        "kb_id": "16150",
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
            "INSERT OR IGNORE INTO lectures (id, paper_id, number, title, subtitle, mechanism, core_lesson, posted, kb_id) "
            "VALUES (:id, :paper_id, :number, :title, :subtitle, :mechanism, :core_lesson, :posted, :kb_id)",
            lec
        )

    for e in EQUATIONS:
        cur.execute(
            "INSERT OR IGNORE INTO equations "
            "(id, paper_id, label, latex, plain, domain, source_note, consus_verified, consus_notes) "
            "VALUES (:id, :paper_id, :label, :latex, :plain, :domain, :source_note, :consus_verified, :consus_notes)",
            {
                "id": e["id"], "paper_id": e.get("paper_id"),
                "label": e["label"], "latex": e["latex"],
                "plain": e["plain"], "domain": e.get("domain"),
                "source_note": e.get("source_note"),
                "consus_verified": e.get("consus_verified", 0),
                "consus_notes": e.get("consus_notes"),
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
    l_n = cur.execute("SELECT COUNT(*) FROM lectures").fetchone()[0]
    a_n = cur.execute("SELECT COUNT(*) FROM atoms WHERE ratified=1").fetchone()[0]
    e_n = cur.execute("SELECT COUNT(*) FROM equations WHERE consus_verified=1").fetchone()[0]
    print(f"riggs.db seeded: {p_n} papers, {l_n} lectures, {a_n} ratified atoms, {e_n} verified equations")
    print(f"DB: {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    seed()
