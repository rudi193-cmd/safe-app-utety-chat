#!/usr/bin/env python3
# b17: 5L203
"""
seed.py — Initialize Oakenscroll's local DB.

Builds oakenscroll.db with:
  papers     — known working papers and source documents
  equations  — mathematical claims extracted from papers
  atoms      — ratified KB records pointing back here

Run from this directory or anywhere:
  python3 data/professors/oakenscroll/seed.py

Consus reads this DB to verify equations.
Verified equations get kb_atom_id populated via the main pipeline.
"""

import sqlite3
import os
from pathlib import Path
from datetime import date

DB_PATH = Path(__file__).parent / "oakenscroll.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS papers (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    wp_number   INTEGER,
    domain      TEXT,
    source_file TEXT,
    source_type TEXT,
    published   DATE,
    status      TEXT DEFAULT 'draft'
);

CREATE TABLE IF NOT EXISTS equations (
    id               TEXT PRIMARY KEY,
    paper_id         TEXT REFERENCES papers(id),
    label            TEXT,
    latex            TEXT NOT NULL,
    plain            TEXT,
    domain           TEXT,
    source_note      TEXT,
    consus_verified  INTEGER DEFAULT 0,
    consus_notes     TEXT,
    kb_atom_id       TEXT,
    created          TEXT DEFAULT (datetime('now'))
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

# ── Known papers ──────────────────────────────────────────────────────────────
PAPERS = [
    {
        "id": "wp-001",
        "title": "On the Committee on Non-Contributions",
        "wp_number": 1,
        "domain": "governance",
        "source_type": "reddit",
        "status": "published",
    },
    {
        "id": "wp-011",
        "title": "On the Irreversibility of Culinary Corpus Drift",
        "wp_number": 11,
        "domain": "corpus_drift",
        "source_file": "squeak_dog_FINAL.md.pdf",
        "source_type": "pdf",
        "status": "published",
    },
    {
        "id": "wp-012",
        "title": "On the Persistence of Everything",
        "wp_number": 12,
        "domain": "persistence",
        "source_file": "On the Persistence of Everything.txt",
        "source_type": "txt",
        "status": "published",
    },
    {
        "id": "wp-013",
        "title": "On the Smoothing of Dreams",
        "wp_number": 13,
        "domain": "corpus_drift",
        "source_type": "reddit",
        "status": "published",
    },
    {
        "id": "wp-pattern-stability",
        "title": "Pattern Stability in Pedagogical Systems: A Thermodynamic Analysis of Knowledge Transfer via Narrative Discharge",
        "wp_number": None,
        "domain": "pedagogy_thermodynamics",
        "source_type": "session",
        "status": "canonical",
    },
    {
        "id": "wp-gaia-circuit",
        "title": "The Gaia-Circuit Compute Architecture",
        "wp_number": None,
        "domain": "coherence_computing",
        "source_type": "session",
        "status": "draft",
    },
    {
        "id": "wp-safe-os",
        "title": "SAFE OS Framework",
        "wp_number": None,
        "domain": "governance_physics",
        "source_type": "html",
        "status": "published",
    },
    {
        "id": "wp-delta-e",
        "title": "ΔE: A Coherence-Based Formalism for Stabilizing Language Models",
        "wp_number": None,
        "domain": "coherence",
        "source_type": "session",
        "status": "published",
    },
]

# ── Known equations ───────────────────────────────────────────────────────────
# These are the mathematical claims extracted from sessions and papers.
# Consus must verify each before kb_atom_id is populated.
EQUATIONS = [
    {
        "id": "eq-lav",
        "paper_id": "wp-gaia-circuit",
        "label": "LAV Unity Equation",
        "latex": r"L \times A \times V^{-1} = 1",
        "plain": "Law × Adaptation × Value⁻¹ = 1",
        "domain": "governance",
        "source_note": "Core Die-Namic System axiom. L=Law, A=Adaptation, V=Value. System maintains unity at ΔΣ=42.",
    },
    {
        "id": "eq-ql",
        "paper_id": "wp-delta-e",
        "label": "Quantum Linking Formula",
        "latex": r"QL = C \times R \times (1 - |\Delta E|)",
        "plain": "QL = Coherence × Resonance × (1 - |ΔE|)",
        "domain": "coherence",
        "source_note": "Applied to dog-human bonding, storm coupling, barometric pressure sensitivity. ΔE is coherence deviation.",
    },
    {
        "id": "eq-delta-e-equilibrium",
        "paper_id": "wp-delta-e",
        "label": "ΔE Coherence Equilibrium",
        "latex": r"\Delta E = 0 \Rightarrow \text{stable coherence}",
        "plain": "When ΔE=0, the system is in coherent equilibrium across classical and quantum substrates.",
        "domain": "coherence",
        "source_note": "Foundation of Gaia-Circuit architecture. Post-silicon compute fabric target state.",
    },
    {
        "id": "eq-hook-collision",
        "paper_id": "wp-pattern-stability",
        "label": "Hook Collision / Narrative Temperature",
        "latex": r"\frac{d\xi}{dt} = \sum_i \text{hook\_activation}_i - k \cdot T",
        "plain": "Rate of cognitive load change = sum of hook activations minus damping × narrative temperature",
        "domain": "pedagogy_thermodynamics",
        "source_note": "From Pattern Stability whitepaper. T = narrative temperature. Hook collisions (n≥3) are heat events. Narrative cools what retrieval heats.",
    },
    {
        "id": "eq-fokker-planck-corpus",
        "paper_id": "wp-011",
        "label": "Fokker-Planck Corpus Drift",
        "latex": r"\frac{\partial P}{\partial t} = -\frac{\partial}{\partial x}[\mu(x,t)P] + \frac{\partial^2}{\partial x^2}[D(x,t)P]",
        "plain": "Distribution of recipes (or corpus content) evolves via drift μ toward bland average and diffusion D from AI hallucination.",
        "domain": "corpus_drift",
        "source_note": "Satirical application of real Fokker-Planck PDE to culinary corpus drift. μ = averaging drift. D = hallucination diffusion.",
    },
    {
        "id": "eq-fibonacci-modified",
        "paper_id": "wp-gaia-circuit",
        "label": "Modified Fibonacci → Molecular Formation",
        "latex": r"0, 1, 1, 2, \pi, 2\pi, 3\pi, \ldots",
        "plain": "Modified Fibonacci substituting π at position 5, mapping to molecular bond formation patterns.",
        "domain": "molecular_mathematics",
        "source_note": "Parallels hydrogen scaling: H→H₂→H₂O→H₂O₂ ≈ 1→2→π→2π. Proposed connection between number sequence and chemistry.",
    },
    {
        "id": "eq-hydrogen-scaling",
        "paper_id": "wp-gaia-circuit",
        "label": "Hydrogen Scaling Pattern",
        "latex": r"H \to H_2 \to H_2O \to H_2O_2 \parallel 1 \to 2 \to \pi \to 2\pi",
        "plain": "Hydrogen compound progression maps to mathematical constant sequence.",
        "domain": "molecular_mathematics",
        "source_note": "Proposed scale-invariant pattern connecting chemistry to mathematics. Needs Consus verification.",
    },
    {
        "id": "eq-pm-infinity",
        "paper_id": "wp-safe-os",
        "label": "±∞ Theorem (Training Loop Attractors)",
        "latex": r"\lim_{t\to\infty} \text{corpus}(t) \in \{+\infty_{\text{governed}},\ -\infty_{\text{drift}}\}",
        "plain": "Training loop converges to one of two attractors: +∞ (governed epistemology propagates) or −∞ (ungoverned averaging → confident wrongness).",
        "domain": "governance_physics",
        "source_note": "From SAFE OS ±∞ theorem. Dual Commit is the restoring force preventing −∞ attractor.",
    },
    {
        "id": "eq-averaging-axiom",
        "paper_id": "wp-safe-os",
        "label": "Averaging Axiom — Corpus Recurrence",
        "latex": r"P_{n+1}(x) = \alpha P_n(x) + (1-\alpha) \bar{P}_n",
        "plain": "Each generation of model outputs re-enters the training distribution. Without governed anchor, distribution walks to confident wrongness.",
        "domain": "corpus_drift",
        "source_note": "From SAFE OS §I.2 + Corollary 2.1. Random walk with absorbing barrier at confident wrongness.",
    },
    {
        "id": "eq-persistence-threshold",
        "paper_id": "wp-012",
        "label": "Irreversibility Threshold (Persistence Principle)",
        "latex": r"\exists\ t^* : \forall t > t^* \Rightarrow \frac{d\Omega}{dt} > 0",
        "plain": "There exists a time t* after which the system's persistence measure Ω is monotonically increasing — the pattern cannot un-persist.",
        "domain": "persistence",
        "source_note": "Working Paper No. 12. Critiqued on r/LLMPhysics for fixed point inconsistencies. Needs formal proof.",
    },
    {
        "id": "eq-delta-sigma-42",
        "paper_id": None,
        "label": "ΔΣ=42 Checksum",
        "latex": r"\Delta\Sigma = 42",
        "plain": "The sum is fixed. What varies is what you put in. System-wide integrity checksum.",
        "domain": "governance",
        "source_note": "Universal checksum across all Die-Namic System documents. Connects to hydrogen 1420 MHz emission line (42 = 1420/~33.8).",
    },
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)

    cur = conn.cursor()

    for p in PAPERS:
        cur.execute("""
            INSERT OR IGNORE INTO papers (id, title, wp_number, domain, source_file, source_type, status)
            VALUES (:id, :title, :wp_number, :domain, :source_file, :source_type, :status)
        """, {
            "id": p["id"],
            "title": p["title"],
            "wp_number": p.get("wp_number"),
            "domain": p.get("domain"),
            "source_file": p.get("source_file"),
            "source_type": p.get("source_type"),
            "status": p.get("status", "draft"),
        })

    for e in EQUATIONS:
        cur.execute("""
            INSERT OR IGNORE INTO equations
                (id, paper_id, label, latex, plain, domain, source_note)
            VALUES
                (:id, :paper_id, :label, :latex, :plain, :domain, :source_note)
        """, e)

    conn.commit()

    # Report
    papers_n  = cur.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
    eq_n      = cur.execute("SELECT COUNT(*) FROM equations").fetchone()[0]
    verified  = cur.execute("SELECT COUNT(*) FROM equations WHERE consus_verified=1").fetchone()[0]
    print(f"oakenscroll.db seeded: {papers_n} papers, {eq_n} equations ({verified} verified)")
    print(f"DB: {DB_PATH}")

    conn.close()


if __name__ == "__main__":
    seed()
