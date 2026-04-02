"""
UTETY Professor Knowledge Seeder
==================================
Reads Willow's knowledge graph (PostgreSQL) and writes per-professor context
files to data/professors/{name}_context.md

These files are loaded by ChatSession at init so each professor speaks from
their actual shared history rather than relying solely on generic semantic search.

Run:
  python pipeline/seed_professors.py
  python pipeline/seed_professors.py --dry-run
  python pipeline/seed_professors.py --professor Gerald
  python pipeline/seed_professors.py --username Sweet-Pea-Rudi19

Environment variables:
  WILLOW_DB_URL   postgresql://willow:willow@172.26.176.1:5437/willow  (required)
  WILLOW_USERNAME Willow username whose knowledge schema to read        (default: Sweet-Pea-Rudi19)

Confidence weighting (same model as NASA Archive):
  Sean-direct atom (entity[2] tagged) -> HIGH
  1-hop atom (shares entity with Sean atom) -> MEDIUM
  Other -> LOW
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve output directory relative to this file, not an absolute path
# ---------------------------------------------------------------------------
OUT_DIR = Path(__file__).parent.parent / "data" / "professors"

SEAN_ENTITY_ID = 2

# Professor -> Willow entity ID mapping
# (from: SELECT id, name FROM entities WHERE name LIKE '%<name>%')
PROFESSOR_ENTITIES = {
    "Oakenscroll": 536,   # 36 atoms
    "Gerald":      325,   # 21 atoms
    "Jane":       1001,   # 21 atoms
    "Steve":       228,   #  8 atoms
    "Alexis":      320,   #  7 atoms
    "Consus":      343,   #  5 atoms
    "Ada":         259,   #  4 atoms
    "Riggs":       518,   #  1 atom
    "Nova":        363,   #  1 atom
    "Mitra":      3859,   #  1 atom
    "Kart":        109,   # 11 atoms
    "Pigeon":      770,   #  2 atoms
    "Binder":      773,   #  2 atoms (The Binder entity; canonical=430 — check atom count before switching)
    "Hanz":       1588,   # canonical (aliases: 941, 200, 2583 all point here)
    "Jeles":      2789,   # "Jeles" entity
    "Shiva":      2786,   # "Shiva" entity
    "Willow":        9,   # "Willow" entity
}

MAX_ATOMS = 15   # cap per professor (highest-confidence first)
MAX_CHARS = 400  # max chars per atom (summary + snippet combined)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed professor context files from Willow knowledge DB")
    parser.add_argument("--dry-run",    action="store_true",  help="Print what would be written without writing")
    parser.add_argument("--professor",  metavar="NAME",       help="Only seed this professor (case-insensitive)")
    parser.add_argument(
        "--username",
        metavar="USERNAME",
        default=os.getenv("WILLOW_USERNAME", "Sweet-Pea-Rudi19"),
        help="Willow username to read knowledge from (default: WILLOW_USERNAME env or Sweet-Pea-Rudi19)",
    )
    return parser.parse_args()


def connect(username: str):
    """Return a Postgres connection scoped to the given Willow user's schema."""
    # Import here so the module can be imported without WILLOW_DB_URL set
    # (e.g. during unit tests that mock the connection).
    # Ensure core.db resolves to this app's core/, not the caller's CWD.
    _app_root = str(Path(__file__).parent.parent)
    if _app_root not in sys.path:
        sys.path.insert(0, _app_root)
    from core.db import get_willow_connection
    return get_willow_connection(username)


def get_sean_sets(conn):
    """Return (sean_atom_ids, hop1_ids) sets for confidence weighting."""
    cur = conn.cursor()

    cur.execute(
        "SELECT knowledge_id FROM knowledge_entities WHERE entity_id = %s",
        (SEAN_ENTITY_ID,),
    )
    sean_ids = {r["knowledge_id"] for r in cur.fetchall()}

    cur.execute(
        """
        SELECT DISTINCT ke2.entity_id
        FROM knowledge_entities ke1
        JOIN knowledge_entities ke2 ON ke1.knowledge_id = ke2.knowledge_id
        WHERE ke1.entity_id = %s AND ke2.entity_id != %s
        """,
        (SEAN_ENTITY_ID, SEAN_ENTITY_ID),
    )
    adjacent = {r["entity_id"] for r in cur.fetchall()}

    hop1 = set()
    if adjacent:
        ph = ",".join(["%s"] * len(adjacent))
        cur.execute(
            f"SELECT DISTINCT knowledge_id FROM knowledge_entities WHERE entity_id IN ({ph})",
            list(adjacent),
        )
        hop1 = {r["knowledge_id"] for r in cur.fetchall()} - sean_ids

    return sean_ids, hop1


def seed_professor(
    conn,
    name: str,
    entity_id: int,
    sean_ids: set,
    hop1_ids: set,
    dry_run: bool,
) -> int:
    """Write data/professors/{name}_context.md. Returns atom count written."""
    cur = conn.cursor()
    # knowledge_entities is currently unpopulated — use FTS by professor name.
    # entity_id is kept as a parameter for future use when associations exist.
    try:
        ts_term = name.replace(" ", " & ")
        cur.execute(
            """
            SELECT k.id, k.title, k.summary, k.category, k.created_at
            FROM knowledge k
            WHERE search_vector @@ to_tsquery('english', %s)
              AND k.category NOT IN ('merged')
            ORDER BY ts_rank(search_vector, to_tsquery('english', %s)) DESC
            LIMIT 50
            """,
            (ts_term, ts_term),
        )
        rows = cur.fetchall()
    except Exception:
        rows = []

    if not rows:
        print(f"  {name}: 0 atoms -- skipping")
        return 0

    def tier(atom_id):
        if atom_id in sean_ids:  return 0
        if atom_id in hop1_ids:  return 1
        return 2

    sorted_rows = sorted(rows, key=lambda r: tier(r["id"]))[:MAX_ATOMS]

    lines = [
        f"# Willow Memory: {name}",
        f"*{len(rows)} atoms total | Top {len(sorted_rows)} shown | Seeded {datetime.now().strftime('%Y-%m-%d')}*",
        "",
    ]

    for atom in sorted_rows:
        atom_id = atom["id"]
        title   = (atom["title"]   or "").strip()
        summary = (atom["summary"] or "").strip()
        snippet = ""

        conf = "high" if atom_id in sean_ids else ("medium" if atom_id in hop1_ids else "low")
        text = " ".join(filter(None, [summary, snippet]))[:MAX_CHARS]

        lines.append(f"## {title}" if title else f"## atom[{atom_id}]")
        lines.append(f"*confidence: {conf}*")
        if text:
            lines.append(text)
        lines.append("")

    out_path = OUT_DIR / f"{name.lower()}_context.md"

    if dry_run:
        print(f"  [DRY RUN] {name}: {len(sorted_rows)}/{len(rows)} atoms -> {out_path.name}")
    else:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  {name}: {len(sorted_rows)}/{len(rows)} atoms -> {out_path.name}")

    return len(sorted_rows)


def main():
    args = parse_args()

    print("=== UTETY Professor Knowledge Seeder ===")
    print(f"Willow username: {args.username}")
    print(f"Output:          {OUT_DIR}")
    if args.dry_run:
        print("[DRY RUN MODE]")
    print()

    conn = connect(args.username)
    sean_ids, hop1_ids = get_sean_sets(conn)

    targets = PROFESSOR_ENTITIES
    if args.professor:
        targets = {k: v for k, v in PROFESSOR_ENTITIES.items()
                   if k.lower() == args.professor.lower()}
        if not targets:
            print(f"Unknown professor: {args.professor}")
            sys.exit(1)

    total = 0
    for name, entity_id in targets.items():
        total += seed_professor(conn, name, entity_id, sean_ids, hop1_ids, args.dry_run)

    conn.close()
    print(f"\nDone: {total} atom entries written across {len(targets)} professors")


if __name__ == "__main__":
    main()
