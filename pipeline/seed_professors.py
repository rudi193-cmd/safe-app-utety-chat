"""
UTETY Professor Knowledge Seeder
==================================
Reads Willow's knowledge graph and writes per-professor context files to
data/professors/{name}_context.md

These files are loaded by ChatSession at init so each professor speaks from
their actual shared history rather than relying solely on generic semantic search.

Run:
  python pipeline/seed_professors.py
  python pipeline/seed_professors.py --dry-run
  python pipeline/seed_professors.py --professor Gerald

Confidence weighting (same model as NASA Archive):
  Sean-direct atom (entity[2] tagged) -> HIGH
  1-hop atom (shares entity with Sean atom) -> MEDIUM
  Other -> LOW
"""

import sqlite3
import sys
from datetime import datetime
from pathlib import Path

WILLOW_DB = Path(__file__).parent.parent.parent / "Willow" / "artifacts" / "Sweet-Pea-Rudi19" / "willow_knowledge.db"
OUT_DIR   = Path(__file__).parent.parent / "data" / "professors"
DRY_RUN   = "--dry-run" in sys.argv
FILTER    = next((a for a in sys.argv[1:] if not a.startswith("--")), None)

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
    "Binder":      773,   #  2 atoms (The Binder entity)
    # Hanz, Jeles, Willow — no Willow DB entities yet
}

MAX_ATOMS   = 15   # cap per professor (highest-confidence first)
MAX_CHARS   = 400  # max chars per atom (summary + snippet combined)


def connect():
    conn = sqlite3.connect(str(WILLOW_DB))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=10000")
    return conn


def get_sean_sets(conn):
    """Return (sean_atom_ids, hop1_ids) sets for confidence weighting."""
    sean_ids = set(
        r[0] for r in conn.execute(
            "SELECT knowledge_id FROM knowledge_entities WHERE entity_id = ?",
            (SEAN_ENTITY_ID,)
        ).fetchall()
    )
    adjacent = set(
        r[0] for r in conn.execute("""
            SELECT DISTINCT ke2.entity_id
            FROM knowledge_entities ke1
            JOIN knowledge_entities ke2 ON ke1.knowledge_id = ke2.knowledge_id
            WHERE ke1.entity_id = ? AND ke2.entity_id != ?
        """, (SEAN_ENTITY_ID, SEAN_ENTITY_ID)).fetchall()
    )
    hop1 = set()
    if adjacent:
        ph = ",".join("?" * len(adjacent))
        hop1 = set(
            r[0] for r in conn.execute(
                f"SELECT DISTINCT knowledge_id FROM knowledge_entities WHERE entity_id IN ({ph})",
                list(adjacent)
            ).fetchall()
        ) - sean_ids
    return sean_ids, hop1


def seed_professor(conn, name: str, entity_id: int, sean_ids: set, hop1_ids: set) -> int:
    """Write data/professors/{name}_context.md. Returns atom count written."""
    rows = conn.execute("""
        SELECT k.id, k.title, k.summary, k.content_snippet, k.category, k.created_at
        FROM knowledge k
        JOIN knowledge_entities ke ON k.id = ke.knowledge_id
        WHERE ke.entity_id = ?
          AND k.category NOT IN ('merged')
        ORDER BY k.id
    """, (entity_id,)).fetchall()

    if not rows:
        print(f"  {name}: 0 atoms — skipping")
        return 0

    # Sort by confidence tier: high first, then medium, then low
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
        title   = (atom["title"] or "").strip()
        summary = (atom["summary"] or "").strip()
        snippet = (atom["content_snippet"] or "").strip()

        conf = "high" if atom_id in sean_ids else ("medium" if atom_id in hop1_ids else "low")
        text = " ".join(filter(None, [summary, snippet]))[:MAX_CHARS]

        lines.append(f"## {title}" if title else f"## atom[{atom_id}]")
        lines.append(f"*confidence: {conf}*")
        if text:
            lines.append(text)
        lines.append("")

    out_path = OUT_DIR / f"{name.lower()}_context.md"

    if DRY_RUN:
        print(f"  [DRY RUN] {name}: {len(sorted_rows)}/{len(rows)} atoms -> {out_path.name}")
    else:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  {name}: {len(sorted_rows)}/{len(rows)} atoms -> {out_path.name}")

    return len(sorted_rows)


def main():
    if not WILLOW_DB.exists():
        print(f"ERROR: Willow DB not found at {WILLOW_DB}")
        sys.exit(1)

    print(f"=== UTETY Professor Knowledge Seeder ===")
    print(f"Willow DB: {WILLOW_DB}")
    print(f"Output:    {OUT_DIR}")
    if DRY_RUN:
        print("[DRY RUN MODE]")
    print()

    conn     = connect()
    sean_ids, hop1_ids = get_sean_sets(conn)

    targets = PROFESSOR_ENTITIES
    if FILTER:
        targets = {k: v for k, v in PROFESSOR_ENTITIES.items() if k.lower() == FILTER.lower()}
        if not targets:
            print(f"Unknown professor: {FILTER}")
            sys.exit(1)

    total = 0
    for name, entity_id in targets.items():
        total += seed_professor(conn, name, entity_id, sean_ids, hop1_ids)

    conn.close()
    print(f"\nDone: {total} atom entries written across {len(targets)} professors")


if __name__ == "__main__":
    main()
