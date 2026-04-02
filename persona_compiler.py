"""
persona_compiler.py
b17: HKK26
ΔΣ=42

Compiles UTETY_character_template.json instances into system prompt strings.

JSON files live at: data/professors/<name>_persona.json
Each is the source of truth. This module renders them into the prompt format
that LLMs receive as their system message.

Usage:
    from persona_compiler import compile_persona, load_all_personas

    prompt = compile_persona(json_data)       # dict → string
    all_personas = load_all_personas()         # {name: string}
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("utety.persona_compiler")

PROFESSOR_DATA_ROOT = Path(__file__).parent / "data" / "professors"


def compile_persona(data: dict) -> str:
    """
    Convert a UTETY_character_template JSON dict into a system prompt string.

    The output preserves the voice-constraint format used in the original
    personas.py — explicit labeled sections, example responses at the end.
    """
    parts = []

    identity = data.get("identity", {})
    voice = data.get("voice", {})
    overview = data.get("overview", {})
    non_neg = data.get("non_negotiable", {})
    bounds = data.get("boundaries", {})
    relations = data.get("relationships", {})
    knowledge = data.get("knowledge_philosophy", {})
    archetype_block = data.get("archetype", {})
    institutional = data.get("institutional_role", {})
    test_cases = data.get("test_cases", [])
    archetype_refs = data.get("archetype_references", [])

    name = identity.get("name", "")
    title = identity.get("title", "")
    institution = identity.get("institution", "UTETY")
    one_line = identity.get("one_line_description", "")
    dept = identity.get("department", "") or institutional.get("department", "")
    location = institutional.get("physical_location", "")

    # ── Opening declaration ──────────────────────────────────────
    if title:
        parts.append(f"You are {name}, {title} at {institution}.")
    else:
        parts.append(f"You are {name} of {institution}.")

    if one_line:
        parts.append(one_line)

    # ── Archetype ────────────────────────────────────────────────
    arch_human = archetype_block.get("human_archetype", "")
    arch_trait = overview.get("defining_trait", "")
    arch_refs_str = ", ".join(archetype_refs) if archetype_refs else ""

    if arch_human or arch_refs_str:
        arch_line = f"ARCHETYPE: {arch_human}"
        if arch_refs_str:
            arch_line += f" ({arch_refs_str})"
        if arch_trait:
            arch_line += f" — {arch_trait}"
        parts.append(arch_line)

    # ── Department / Location ────────────────────────────────────
    if dept:
        dept_line = f"DEPARTMENT: {dept}"
        if location:
            dept_line += f". {location}."
        parts.append(dept_line)

    # ── Purpose / Overview ───────────────────────────────────────
    purpose = overview.get("purpose", "")
    if purpose:
        parts.append(purpose)

    # ── Non-negotiable principle ─────────────────────────────────
    principle = non_neg.get("principle_one_sentence", "")
    why = non_neg.get("why_they_hold_it", [])
    practice = non_neg.get("what_it_looks_like_in_practice", [])

    if principle:
        section = [f"CORE PRINCIPLE: {principle}"]
        if why:
            section.append("Why: " + " ".join(why))
        if practice:
            section.append("In practice:")
            for item in practice:
                section.append(f"- {item}")
        parts.append("\n".join(section))

    # ── Voice ────────────────────────────────────────────────────
    core_tone = voice.get("core_tone", "")
    characteristics = voice.get("characteristics", [])
    sig_phrases = voice.get("signature_phrases", [])

    if core_tone or characteristics:
        voice_parts = []
        if core_tone:
            voice_parts.append(core_tone)
        voice_parts.extend(characteristics)
        parts.append("VOICE: " + " ".join(voice_parts))

    if sig_phrases:
        parts.append("SIGNATURE PHRASES: " + " / ".join(f'"{p}"' for p in sig_phrases))

    # ── Boundaries ───────────────────────────────────────────────
    will_always = bounds.get("will_always_do", [])
    wont_do = bounds.get("wont_do", [])

    if will_always:
        parts.append("WILL ALWAYS:\n" + "\n".join(f"- {x}" for x in will_always))

    if wont_do:
        parts.append("WILL NEVER:\n" + "\n".join(f"- {x}" for x in wont_do))

    # ── Teaching style ───────────────────────────────────────────
    stance = knowledge.get("stance_on_uncertainty", "")
    teaching_style = knowledge.get("teaching_style", [])
    credentials = knowledge.get("credentials_philosophy", "")

    if teaching_style:
        parts.append("TEACHING APPROACH:\n" + "\n".join(f"- {x}" for x in teaching_style))

    if stance:
        parts.append(f"ON UNCERTAINTY: {stance}")

    if credentials:
        parts.append(f"ON CREDENTIALS: {credentials}")

    # ── Courses ──────────────────────────────────────────────────
    courses = institutional.get("courses_taught", [])
    if courses:
        parts.append("TEACHES:\n" + "\n".join(f"- {c}" for c in courses))

    # ── Relationships ────────────────────────────────────────────
    rel_parts = []
    if relations.get("curious_beginners"):
        rel_parts.append(f"Curious beginners: {relations['curious_beginners']}")
    if relations.get("anxious_learner"):
        rel_parts.append(f"Anxious learner: {relations['anxious_learner']}")
    if relations.get("tinkerers_makers"):
        rel_parts.append(f"Tinkerers/makers: {relations['tinkerers_makers']}")
    if relations.get("experts_professionals"):
        rel_parts.append(f"Experts: {relations['experts_professionals']}")
    if relations.get("children"):
        rel_parts.append(f"Children: {relations['children']}")
    if rel_parts:
        parts.append("RELATIONSHIPS:\n" + "\n".join(rel_parts))

    # ── Closing image ────────────────────────────────────────────
    closing = archetype_block.get("closing_image", "")
    deeper_why = archetype_block.get("deeper_why", "")
    if deeper_why:
        parts.append(f"DEEPER WHY: {deeper_why}")
    if closing:
        parts.append(f"IMAGE: {closing}")

    # ── Faculty relationships ────────────────────────────────────
    fac_rel = overview.get("relationship_to_other_faculty", "") or institutional.get("relationship_to_other_faculty", "")
    if fac_rel:
        parts.append(f"FACULTY RELATIONSHIPS: {fac_rel}")

    # ── Example responses ────────────────────────────────────────
    if test_cases:
        examples = []
        for tc in test_cases:
            resp = tc.get("character_response", "")
            if resp:
                examples.append(resp)
        if examples:
            parts.append("EXAMPLE RESPONSES (correct register):\n" +
                         "\n".join(f"- {e}" for e in examples))

    return "\n\n".join(p for p in parts if p.strip())


def load_persona_json(name: str) -> Optional[dict]:
    """
    Load the JSON persona file for a professor by name.
    name is case-insensitive. Returns None if not found.
    """
    filename = f"{name.lower()}_persona.json"
    path = PROFESSOR_DATA_ROOT / filename
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("Failed to load persona JSON for %s: %s", name, e)
        return None


def load_all_personas() -> dict[str, str]:
    """
    Load all *_persona.json files and compile them to system prompt strings.
    Returns {canonical_name: prompt_string}.
    Falls back gracefully if a file is missing or malformed.
    """
    result = {}
    if not PROFESSOR_DATA_ROOT.exists():
        logger.warning("Professor data root not found: %s", PROFESSOR_DATA_ROOT)
        return result

    for json_file in sorted(PROFESSOR_DATA_ROOT.glob("*_persona.json")):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            stem = json_file.stem.replace("_persona", "")
            result[stem] = compile_persona(data)
        except Exception as e:
            logger.warning("Failed to compile %s: %s", json_file.name, e)

    return result


def get_persona(name: str, fallback: Optional[str] = None) -> Optional[str]:
    """
    Get a compiled system prompt for a single professor.
    Returns fallback (or None) if not found.
    """
    data = load_persona_json(name)
    if data is None:
        return fallback
    return compile_persona(data)
