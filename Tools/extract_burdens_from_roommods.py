#!/usr/bin/env python3
"""Recover the authored burden (curse) half of the room-modifier data.

WHY

`Content/Python/extend_roguelike_blessings.py` copies room modifiers into blessing
rows, but its field list omits `curse` and `curse_effect`. That is why
`DT_Blessings.json` holds 26 blessings and zero burdens: the burden half was
authored and then dropped in transit, not never written.

The source of truth is `DT_MelodySlime_RoomMods.json`, which carries 21 authored
blessing/curse pairs.

WHAT THIS DOES NOT DO

It does not invent burdens, and it does not guess magnitudes. `curse_effect` is
free text; where a rule type or magnitude cannot be read out of it mechanically,
the row is emitted with `needs_review` and an explicit reason rather than a
plausible number. A wrong magnitude that looks authored is worse than a flagged
gap, because nothing downstream can tell it was a guess.

Contract: specs/roguelike/melodia_blessing_burden_contract.v1.json
Required fields: burden_id, display_name, description, rule_type, magnitude,
duration_or_scope, stack_policy, source_content_pack.

USAGE

    python Tools/extract_burdens_from_roommods.py            # report only
    python Tools/extract_burdens_from_roommods.py --write    # write DT_Burdens.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Content" / "Melodia" / "DataStuctures" / "DT_MelodySlime_RoomMods.json"
OUTPUT = ROOT / "Content" / "Melodia" / "DataStuctures" / "DT_Burdens.json"

# Keyword -> rule_type. Ordered: the first match wins, so put the more specific
# phrasings first. These are read from the authored strings, not invented.
RULE_PATTERNS: list[tuple[str, str]] = [
    (r"ultimate gauge (?:recharge|charge)", "ultimate_gauge_recharge"),
    (r"ultimate gauge", "ultimate_gauge"),
    (r"rhythm (?:timing )?window|rhythm window", "rhythm_timing_window"),
    (r"toughness damage taken", "toughness_damage_taken"),
    (r"toughness damage", "toughness_damage"),
    (r"\bsp\b", "sp"),
    (r"\bhp\b", "hp"),
    (r"speed", "movement_speed"),
    (r"double damage|damage taken", "damage_taken"),
]

# A burden must constrain. These read as benefits and cannot be accepted as
# burdens without a design call, however they were authored.
BENEFIT_PHRASES = [r"reduces? toughness damage taken", r"reduces? damage taken"]


def slugify(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "", text.title()) or "Unnamed"


def parse_effect(effect: str) -> tuple[str | None, float | None, list[str]]:
    """(rule_type, magnitude, problems) read out of a free-text curse_effect."""
    problems: list[str] = []
    lowered = effect.lower()

    rule_type = None
    for pattern, name in RULE_PATTERNS:
        if re.search(pattern, lowered):
            rule_type = name
            break
    if rule_type is None:
        problems.append("no recognisable rule_type in curse_effect")

    magnitude = None
    percent = re.search(r"(\d+(?:\.\d+)?)\s*%", effect)
    if percent:
        magnitude = float(percent.group(1))
    elif re.search(r"\bdouble\b", lowered):
        magnitude = 100.0  # double = +100%
        problems.append("magnitude inferred from 'double' (=100%); confirm intent")
    else:
        bare = re.search(r"by\s+(\d+(?:\.\d+)?)\b", lowered)
        if bare:
            magnitude = float(bare.group(1))
            problems.append("magnitude is a bare number, unit unknown (points? percent?)")
        else:
            problems.append("no magnitude found in curse_effect")

    # Two effects in one string cannot be one typed rule.
    if "," in effect and re.search(r"\d+\s*%.*,.*\b(halve|reduce|increase|\d+\s*%)", lowered):
        problems.append("compound effect: more than one rule in a single string")

    for phrase in BENEFIT_PHRASES:
        if re.search(phrase, lowered):
            problems.append("reads as a BENEFIT, not a constraint; a burden must constrain")
            break

    return rule_type, magnitude, problems


def scope_of(effect: str) -> str:
    lowered = effect.lower()
    if "rest of your run" in lowered or "for the run" in lowered:
        return "run"
    if "per turn" in lowered:
        return "turn"
    if "until next" in lowered:
        return "until_condition"
    if "per note" in lowered or "missed note" in lowered or "per missed" in lowered:
        return "per_miss"
    return "room"


def build() -> tuple[dict, list[dict]]:
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    rows_in = data.get("Rows", {})

    rows_out: dict[str, dict] = {}
    flagged: list[dict] = []
    used_ids: set[str] = set()

    for mod_id, mod in rows_in.items():
        curse = (mod.get("curse") or "").strip()
        effect = (mod.get("curse_effect") or "").strip()
        if not curse and not effect:
            continue

        rule_type, magnitude, problems = parse_effect(effect)

        # Curse display names repeat across mods (Deafening Echoes, Rhythmic
        # Shackles, Harmonic Weakness each appear twice). Key on the mod id so
        # every burden id is unique and traceable to its source row.
        burden_id = f"Burden_{mod_id}"
        if burden_id in used_ids:
            problems.append("duplicate burden_id collision")
        used_ids.add(burden_id)

        row = {
            "burden_id": burden_id,
            "display_name": curse or "Unnamed Burden",
            "description": effect,
            "rule_type": rule_type,
            "magnitude": magnitude,
            "duration_or_scope": scope_of(effect),
            "stack_policy": "unique_per_run",
            "source_content_pack": "MelodySlime_RoomMods",
            "paired_blessing_id": mod.get("blessing_id"),
            "source_row": mod_id,
        }
        if problems:
            row["needs_review"] = problems
            flagged.append({"burden_id": burden_id, "effect": effect, "problems": problems})

        rows_out[burden_id] = row

    doc = {
        "DataType": "RoguelikeBurden",
        "SchemaVersion": 1,
        "GeneratedFrom": "Content/Melodia/DataStuctures/DT_MelodySlime_RoomMods.json",
        "Contract": "specs/roguelike/melodia_blessing_burden_contract.v1.json",
        "Note": ("Recovered curse/curse_effect pairs dropped by "
                 "Content/Python/extend_roguelike_blessings.py. Rows carrying needs_review "
                 "are NOT gameplay-ready: magnitude or rule_type could not be read from the "
                 "authored text and must not be guessed."),
        "Rows": rows_out,
    }
    return doc, flagged


def main() -> int:
    ap = argparse.ArgumentParser(description="Recover authored burdens from room modifiers.")
    ap.add_argument("--write", action="store_true", help="write DT_Burdens.json")
    args = ap.parse_args()

    if not SOURCE.exists():
        print(f"[HOLD] source not found: {SOURCE}")
        return 2

    doc, flagged = build()
    rows = doc["Rows"]
    ready = [r for r in rows.values() if "needs_review" not in r]

    print(f"burdens recovered: {len(rows)}   gameplay-ready: {len(ready)}   "
          f"needs review: {len(flagged)}\n")

    for item in flagged:
        print(f"  REVIEW  {item['burden_id']}")
        print(f"          \"{item['effect']}\"")
        for problem in item["problems"]:
            print(f"            - {problem}")

    if args.write:
        OUTPUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        print(f"\nwrote {OUTPUT.relative_to(ROOT)}")
    else:
        print("\n(dry run — pass --write to emit DT_Burdens.json)")

    # Recovery itself succeeded; flagged rows are data to review, not a tool failure.
    return 0


if __name__ == "__main__":
    sys.exit(main())
