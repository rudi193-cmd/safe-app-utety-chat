#!/usr/bin/env python3
"""
professor-scan.py — Scan known locations for professor content.
Routes files through Jeles (JSONL) or knowledge_ingest (text/HTML).
Writes verified atoms to per-professor SQLite DBs.

Usage:
  python3 professor-scan.py           # dry run — shows what would be processed
  python3 professor-scan.py --run     # actually runs
"""

import sys, os, json, sqlite3, hashlib
from pathlib import Path
from datetime import datetime

DRY_RUN = "--run" not in sys.argv

PROFESSORS_DIR = Path(__file__).parent
DB_ROOT        = PROFESSORS_DIR

SCAN_LOCATIONS = [
    # ── Home-level directories ─────────────────────────────────────────────────
    Path("/home/sean-campbell/willow-pending"),
    Path("/home/sean-campbell/willow-artifacts"),       # full tree (was: /documents only)
    Path("/home/sean-campbell/willow-1.5"),             # agent profiles, hooks, commands
    Path("/home/sean-campbell/journal"),
    Path("/home/sean-campbell/Documents/haumana"),
    Path("/home/sean-campbell/agents/hanuman/projects/claude_export_20260327"),
    # ── Ashokoa — full tree (was: /Nest/processed + /corpus/auth-users) ───────
    Path("/home/sean-campbell/Ashokoa"),
    # ── personal — full documents tree (consolidates many prior specific paths)
    Path("/home/sean-campbell/personal/documents"),
    Path("/home/sean-campbell/personal/writing"),
    Path("/home/sean-campbell/personal/research"),
    Path("/home/sean-campbell/personal/agent-history"),
    # ── github — full tree (consolidates safe-apps, Willow, die-namic, etc.) ──
    Path("/home/sean-campbell/github"),
    # ── archive — CONF_ files, opus handoffs, origin materials ───────────────
    Path("/home/sean-campbell/archive"),
    # ── projects — Claude Code session excerpts ───────────────────────────────
    Path("/home/sean-campbell/projects"),
]

PROFESSOR_PATTERNS = {
    # Original faculty
    "oakenscroll": ["oakenscroll", "oakenscrolled", "_oake_"],
    "gerald":      ["gerald", "geraldverse", "definitelynotgerald", "squeakdog", "_gera_", "dispatch-"],
    "riggs":       ["riggs", "pendleton", "_rigg_", "rober-rules"],
    "hanz":        ["hanz", "anderthon", "copenhagen"],
    "ofshield":    ["ofshield", "thorin", "_ofsh_"],
    "nova":        ["nova hale", "nova_hale", "oracle nova", "_nova_"],
    "alexis":      ["alexis", "_alex_"],
    "consus":      ["consus"],
    "ada":         ["ada turing", "ada_turing", "_ada_"],
    "steve":       ["prof steve", "professor steve", "_stev_"],
    # Previously missing from scan
    "binder":      ["binder", "_bind_"],
    "jeles":       ["jeles", "_jele_"],
    "shiva":       ["shiva", "_shiv_", "jane"],  # jane = shiva predecessor name
    "mitra":       ["mitra", "_mitr_"],           # PM Claude, sun god namesake
    # pigeon = message bus (not faculty); willow = substrate (not faculty)
}

JELES_EXTENSIONS  = {".jsonl"}
TEXT_EXTENSIONS   = {".md", ".txt", ".json", ".html"}
SKIP_EXTENSIONS   = {".pdf", ".docx", ".png", ".jpg", ".jpeg", ".db", ".py"}

# ── Manifest DB (tracks processed files) ─────────────────────────────────────
MANIFEST_DB = DB_ROOT / "scan-manifest.db"

def open_manifest():
    conn = sqlite3.connect(MANIFEST_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS processed (
            file_hash    TEXT PRIMARY KEY,
            file_path    TEXT,
            professor    TEXT,
            jeles_id     TEXT,
            atom_id      TEXT,
            is_canonical INTEGER DEFAULT 1,
            processed    TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS duplicates (
            file_hash      TEXT,
            duplicate_path TEXT,
            canonical_path TEXT,
            professor      TEXT,
            found          TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (file_hash, duplicate_path)
        )
    """)
    conn.commit()
    return conn

def file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()

def already_processed(conn, fhash: str) -> bool:
    return conn.execute("SELECT 1 FROM processed WHERE file_hash=?", (fhash,)).fetchone() is not None

def mark_duplicate(conn, fhash, duplicate_path, professor):
    canonical = conn.execute(
        "SELECT file_path FROM processed WHERE file_hash=?", (fhash,)
    ).fetchone()
    canonical_path = canonical[0] if canonical else "unknown"
    conn.execute("""
        INSERT OR IGNORE INTO duplicates (file_hash, duplicate_path, canonical_path, professor)
        VALUES (?, ?, ?, ?)
    """, (fhash, str(duplicate_path), canonical_path, professor))
    conn.commit()
    return canonical_path

def mark_processed(conn, fhash, path, professor, jeles_id=None, atom_id=None):
    conn.execute("""
        INSERT OR REPLACE INTO processed (file_hash, file_path, professor, jeles_id, atom_id, is_canonical)
        VALUES (?, ?, ?, ?, ?, 1)
    """, (fhash, str(path), professor, jeles_id, atom_id))
    conn.commit()

# ── Professor DB ──────────────────────────────────────────────────────────────
def get_professor_db(professor: str) -> sqlite3.Connection | None:
    db_path = DB_ROOT / professor / f"{professor}.db"
    if not db_path.exists():
        return None
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scanned_files (
            file_hash  TEXT PRIMARY KEY,
            file_path  TEXT,
            jeles_id   TEXT,
            atom_id    TEXT,
            title      TEXT,
            processed  TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS atoms (
            id        TEXT PRIMARY KEY,
            domain    TEXT,
            title     TEXT,
            content   TEXT,
            kb_id     TEXT,
            ratified  INTEGER DEFAULT 0,
            created   TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    return conn

def write_to_professor_db(prof_conn, fhash, path, title, content, jeles_id=None, atom_id=None):
    prof_conn.execute("""
        INSERT OR IGNORE INTO scanned_files (file_hash, file_path, jeles_id, atom_id, title)
        VALUES (?, ?, ?, ?, ?)
    """, (fhash, str(path), jeles_id, atom_id, title))
    if atom_id:
        prof_conn.execute("""
            INSERT OR IGNORE INTO atoms (id, domain, title, content, kb_id, ratified)
            VALUES (?, 'character', ?, ?, ?, 1)
        """, (atom_id, title, str(path), atom_id))
    prof_conn.commit()

# Content patterns — more specific than filename patterns to reduce false positives
CONTENT_PATTERNS = {
    "oakenscroll": ["oakenscroll", "archimedes oakenscroll"],
    "gerald":      ["gerald", "rotisserie chicken", "squeakdog", "geraldverse", "definitelynotgerald"],
    "riggs":       ["professor riggs", "prof riggs", "penny riggs", "pendleton riggs", "pendleton"],
    "hanz":        ["hanz", "hanz christian", "copenhagen"],
    "ofshield":    ["ofshield", "thorin"],
    "nova":        ["nova hale", "oracle nova", "professor nova", "nova_hale"],
    "alexis":      ["professor alexis", "prof alexis"],
    "consus":      ["consus"],
    "ada":         ["ada turing", "professor ada turing"],
    "steve":       ["professor steve", "prof steve"],
    "binder":      ["the binder", "professor binder", "binder knows", "binder filed"],
    "jeles":       ["jeles"],
    "shiva":       ["agent shiva", "shiva agent", "katy padilla", "recursive learning", "recursive knowledge", "jane game master", "regarding jane"],
    "mitra":       ["mitra", "pm claude", "sun god"],
    # pigeon + willow removed — infrastructure, not faculty
}

# ── Match file to professor ───────────────────────────────────────────────────
def match_professor(path: Path) -> str | None:
    """First try filename match, then content match for text files."""
    name_lower = path.name.lower()
    for professor, patterns in PROFESSOR_PATTERNS.items():
        for pat in patterns:
            if pat in name_lower:
                return professor
    # Filename miss — try content for readable files
    if path.suffix.lower() in TEXT_EXTENSIONS | JELES_EXTENSIONS:
        try:
            content = path.read_text(errors="ignore")[:2000].lower()
            for professor, patterns in CONTENT_PATTERNS.items():
                for pat in patterns:
                    if pat in content:
                        return professor
        except Exception:
            pass
    return None

# ── Jeles pipeline ────────────────────────────────────────────────────────────
def process_jsonl(path: Path, professor: str, manifest_conn, prof_conn):
    """Register JSONL with Jeles, extract atom, write to professor DB."""
    sys.path.insert(0, "/home/sean-campbell/willow-1.5/core")
    try:
        from pg_bridge import try_connect
        pg = try_connect()
        if not pg:
            print(f"  [SKIP] pg_bridge unavailable for {path.name}")
            return
    except Exception as e:
        print(f"  [SKIP] pg_bridge error: {e}")
        return

    fhash = file_hash(path)
    session_id = f"professor-scan-{professor}-{path.stem[:30]}"
    title = f"[{professor.title()}] {path.stem[:60]}"

    print(f"  → Jeles register: {path.name}")
    if DRY_RUN:
        print(f"    [DRY] would register + extract")
        return

    try:
        reg = pg.jeles_register_jsonl(
            agent="hanuman",
            jsonl_path=str(path),
            session_id=session_id,
            cwd=str(path.parent),
            file_size=path.stat().st_size,
        )
        jeles_id = reg.get("b17") or reg.get("id")
        if not jeles_id:
            print(f"    [WARN] no jeles_id returned: {reg}")
            return

        atom = pg.jeles_extract_atom(
            agent="hanuman",
            jsonl_id=jeles_id,
            content=str(path),
            domain="character",
            depth=1,
            certainty=0.96,
            title=title,
        )
        atom_id = atom.get("id")
        print(f"    Jeles: {jeles_id} → atom: {atom_id} ({atom.get('status')})")

        mark_processed(manifest_conn, fhash, path, professor, jeles_id, atom_id)
        if prof_conn:
            write_to_professor_db(prof_conn, fhash, path, title, str(path), jeles_id, atom_id)

    except Exception as e:
        print(f"    [ERROR] {e}")

def process_text(path: Path, professor: str, manifest_conn, prof_conn):
    """Read text/HTML file, ingest to KB, write to professor DB."""
    fhash = file_hash(path)
    title = f"[{professor.title()}] {path.stem[:60]}"

    print(f"  → Text ingest: {path.name}")
    if DRY_RUN:
        print(f"    [DRY] would ingest to KB")
        return

    try:
        content = path.read_text(errors="ignore")[:2000]  # first 2000 chars as summary

        sys.path.insert(0, "/home/sean-campbell/willow-1.5/core")
        from pg_bridge import try_connect
        pg = try_connect()
        if not pg:
            print(f"    [SKIP] pg_bridge unavailable")
            return

        conn = pg._get_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO knowledge (title, summary, source_type, category)
            VALUES (%s, %s, 'file', 'character')
            RETURNING id
        """, (title, content))
        row = cur.fetchone()
        conn.commit()
        cur.close()
        atom_id = str(row[0]) if row else None

        print(f"    KB id: {atom_id}")
        mark_processed(manifest_conn, fhash, path, professor, None, atom_id)
        if prof_conn:
            write_to_professor_db(prof_conn, fhash, path, title, str(path), None, atom_id)

    except Exception as e:
        print(f"    [ERROR] {e}")

# ── Main scan ─────────────────────────────────────────────────────────────────
def scan():
    print(f"{'='*55}")
    print(f"PROFESSOR SCAN {'(DRY RUN)' if DRY_RUN else '(LIVE)'}")
    print(f"{'='*55}")

    manifest_conn = open_manifest()
    found = skipped = processed = 0

    for location in SCAN_LOCATIONS:
        if not location.exists():
            print(f"\n[MISSING] {location}")
            continue

        print(f"\n[SCANNING] {location}")
        for path in sorted(location.rglob("*")):
            if not path.is_file():
                continue
            if path.suffix.lower() in SKIP_EXTENSIONS:
                continue

            professor = match_professor(path)
            if not professor:
                continue

            found += 1
            fhash = file_hash(path)

            if already_processed(manifest_conn, fhash):
                canonical = mark_duplicate(manifest_conn, fhash, path, professor)
                print(f"  [DUP] {path.name}")
                print(f"        canonical: {canonical}")
                skipped += 1
                continue

            prof_conn = get_professor_db(professor)
            ext = path.suffix.lower()

            if ext in JELES_EXTENSIONS:
                process_jsonl(path, professor, manifest_conn, prof_conn)
                processed += 1
            elif ext in TEXT_EXTENSIONS:
                process_text(path, professor, manifest_conn, prof_conn)
                processed += 1
            else:
                print(f"  [SKIP ext] {path.name}")

            if prof_conn:
                prof_conn.close()

    dup_count = manifest_conn.execute("SELECT COUNT(*) FROM duplicates").fetchone()[0]
    manifest_conn.close()
    dup_count = dup_count  # already fetched before close
    print(f"\n{'='*55}")
    print(f"Found: {found}  |  Duplicates: {dup_count}  |  Skipped: {skipped - dup_count}  |  Processed: {processed}")
    if DRY_RUN:
        print("Run with --run to execute.")
    print(f"{'='*55}")


if __name__ == "__main__":
    scan()
