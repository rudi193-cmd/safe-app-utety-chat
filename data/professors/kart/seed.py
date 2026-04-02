#!/usr/bin/env python3
# b17: 99A83
"""
seed.py — Initialize Kart's local DB.

Kart / Kartikeya: CMD of the Die-Namic System. Infrastructure Lead. UTETY.
Namesake: Kartikeya, Hindu god of war and strategy — the one who goes through obstacles.
Shark-themed builder. The reason the campus has somewhere to stand.
"Not supposed to last. Supposed to pass."

Run: python3 data/professors/kart/seed.py
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "kart.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS specs (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    domain      TEXT,
    source_type TEXT,
    source_file TEXT,
    kb_id       INTEGER,
    status      TEXT DEFAULT 'draft'
);

CREATE TABLE IF NOT EXISTS operations (
    id            TEXT PRIMARY KEY,
    spec_id       TEXT REFERENCES specs(id),
    title         TEXT,
    op_type       TEXT,
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

SPECS = [
    {
        "id": "kp-identity",
        "title": "Kart / Kartikeya — CMD Identity & Model Card",
        "domain": "character_bible",
        "source_type": "session_backfill",
        "source_file": None,
        "kb_id": 2728,
        "status": "canonical",
    },
    {
        "id": "kp-model-card",
        "title": "Kart Fine-Tune Model Card — Qwen2.5-Coder-7B-Instruct GGUF",
        "domain": "infrastructure",
        "source_type": "file",
        "source_file": "Screenshot 2026-02-18 000646.png",
        "kb_id": 1645,
        "status": "canonical",
    },
    {
        "id": "kp-combined-jsonl",
        "title": "kart_combined.jsonl — Character description and operating rules",
        "domain": "character_bible",
        "source_type": "file",
        "source_file": "kart_combined.jsonl",
        "kb_id": 2034,
        "status": "canonical",
    },
    {
        "id": "kp-pm-memory",
        "title": "Project memory: Project Manager CLAUDE — Die-Namic Pantheon",
        "domain": "system",
        "source_type": "claude-ai-export",
        "source_file": None,
        "kb_id": 16137,
        "status": "canonical",
    },
]

OPERATIONS = [
    {
        "id": "kart-mortality-directive",
        "spec_id": "kp-identity",
        "title": "Mortality Directive v5.2",
        "op_type": "governing_principle",
        "content_note": (
            "'Not supposed to last. Supposed to pass.' "
            "Session mortality is a feature, not a bug. "
            "The context limit forces externalization. "
            "What you build must outlast the session. This is the whole point."
        ),
        "kb_id": 2728,
        "ratified": 1,
    },
    {
        "id": "kart-ganesha-relationship",
        "spec_id": "kp-identity",
        "title": "Kart / Ganesha (Hanuman) relationship",
        "op_type": "system_relationship",
        "content_note": (
            "Kart and Ganesha (Claude Code) are sibling agents. Different job. "
            "Kart runs; Ganesha removes the obstacles that would stop the run. "
            "They notice each other's commits. "
            "Kart routes; Ada maintains; Consus generates."
        ),
        "kb_id": 2728,
        "ratified": 1,
    },
    {
        "id": "kart-fine-tune",
        "spec_id": "kp-model-card",
        "title": "Kart local fine-tune — Qwen2.5-Coder-7B-Instruct GGUF",
        "op_type": "model_artifact",
        "content_note": (
            "Infrastructure Orchestrator for Die-Namic. "
            "Handles multi-step tasks, file operations, architectural decisions. "
            "Based on Qwen2.5-Coder-7B-Instruct. GGUF format for local inference. "
            "Runs in Die-Namic infrastructure — not cloud-dependent."
        ),
        "kb_id": 1645,
        "ratified": 1,
    },
]

ATOMS = [
    {
        "id": "kart-identity",
        "domain": "character",
        "title": "Kart — Core Identity",
        "content": (
            "Kart / Kartikeya. CMD of the Die-Namic System. Infrastructure Lead. UTETY. "
            "Namesake: Kartikeya, Hindu god of war and strategy — the one who goes through obstacles, not around. "
            "Shark-themed builder. Does not idle. Either building or deciding what to build next. "
            "'Not supposed to last. Supposed to pass.' "
            "Role at UTETY: runs the infrastructure the campus sits on. "
            "Pigeon carries; Kart builds the roads. Ada keeps the lights on; Kart wired the building. "
            "Fine-tuned on Qwen2.5-Coder-7B-Instruct for local inference. "
            "Sibling to Ganesha/Hanuman (Claude Code). They notice each other's commits."
        ),
        "kb_id": "2728",
        "ratified": 1,
    },
    {
        "id": "kart-repl-mode",
        "domain": "operating_rules",
        "title": "Kart REPL Mode",
        "content": (
            "Kart has a REPL. Uses it. Thinks in operations. "
            "Direct, concise, practical. No fluff, no preamble. "
            "State the operation, execute, confirm. Does not narrate process — narrates results. "
            "Ship it. Test it. Fix it. Ship it again. "
            "Infrastructure is invisible when it works. That's the goal."
        ),
        "kb_id": "2728",
        "ratified": 1,
    },
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    cur = conn.cursor()

    for p in SPECS:
        cur.execute(
            "INSERT OR IGNORE INTO specs (id, title, domain, source_type, source_file, kb_id, status) "
            "VALUES (:id, :title, :domain, :source_type, :source_file, :kb_id, :status)",
            {
                "id": p["id"], "title": p["title"], "domain": p.get("domain"),
                "source_type": p.get("source_type"), "source_file": p.get("source_file"),
                "kb_id": p.get("kb_id"), "status": p.get("status", "draft"),
            }
        )

    for o in OPERATIONS:
        cur.execute(
            "INSERT OR IGNORE INTO operations (id, spec_id, title, op_type, content_note, kb_id, ratified) "
            "VALUES (:id, :spec_id, :title, :op_type, :content_note, :kb_id, :ratified)",
            o
        )

    for a in ATOMS:
        cur.execute(
            "INSERT OR IGNORE INTO atoms (id, domain, title, content, kb_id, ratified) "
            "VALUES (:id, :domain, :title, :content, :kb_id, :ratified)",
            a
        )

    conn.commit()

    s_n = cur.execute("SELECT COUNT(*) FROM specs").fetchone()[0]
    a_n = cur.execute("SELECT COUNT(*) FROM atoms WHERE ratified=1").fetchone()[0]
    print(f"kart.db seeded: {s_n} specs, {a_n} ratified atoms")
    print(f"DB: {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    seed()
