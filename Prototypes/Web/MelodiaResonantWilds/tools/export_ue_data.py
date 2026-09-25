"""Export Melodia UE data into the Resonant Wilds web game.

Reads the same files the UE project reads and writes one ES module:
    Prototypes/Web/MelodiaResonantWilds/js/generated/ue_data.js

Sources (never edited here):
    Plugins/MelodiaCore/Rules/melodia_rules.json            rhythm windows, grade multipliers,
                                                             SP economy, Crescendo, Encore, toughness,
                                                             element wheel, modifier registry
    Content/Melodia/DataStuctures/DT_MelodySlime_Skills.json skill charts (element, SP, power, MIDI notes)
    Content/Melodia/DataStuctures/DT_MelodySlime_Enemies.json enemy roster (hp, toughness, dmg, speed, bpm)
    Content/Melodia/DataStuctures/DT_Artifacts.json          artifact powers (-> Opus item arias)
    Content/Melodia/DataStuctures/DT_Blessings.json          blessings (-> run boons)
    Content/Melodia/DataStuctures/DT_Burdens.json            burdens (-> rift curses)
    Content/Melodia/DataStuctures/DT_MelodiaTokens.json      element shards (-> crafting currency)
    Docs/WorldGen/GAEA_SETUP_*.json                          biome identity + terrain recipe

Run from the repository root:
    python Prototypes/Web/MelodiaResonantWilds/tools/export_ue_data.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
GAME = Path(__file__).resolve().parents[1]
DT = ROOT / "Content" / "Melodia" / "DataStuctures"
OUT = GAME / "js" / "generated" / "ue_data.js"


def _rows(name: str) -> dict:
    data = json.loads((DT / name).read_text(encoding="utf-8-sig"))
    return data.get("Rows", data)


def _rules() -> dict:
    rules = json.loads((ROOT / "Plugins" / "MelodiaCore" / "Rules" / "melodia_rules.json").read_text(encoding="utf-8-sig"))
    return {
        "version": rules["_meta"]["version"],
        "rhythm": rules["rhythm"],
        "turn_economy": rules["turn_economy"],
        "crescendo": {"max": rules["songcraft"]["crescendo_max"], "gain": rules["songcraft"]["crescendo_gain"]},
        "ultimate": rules["ultimate"],
        "toughness": rules["toughness"],
        "defense": rules["defense"],
        "elements": {k: v for k, v in rules["elements"].items() if not k.startswith("_")},
        "modifiers": rules["modifiers"]["registry"],
    }


def _skills() -> list[dict]:
    out = []
    for key, row in _rows("DT_MelodySlime_Skills.json").items():
        out.append({
            "id": key,
            "name": row["display_name"].replace("_", " "),
            "element": row["element"],
            "instrument": row["instrument"],
            "tier": int(row["mechanic_level"]),
            "sp": int(row["sp_cost"]),
            "power": round(float(row["power_scalar"]), 3),
            "pitches": [int(p) for p in row["note_pitches"]],
            "durations": [round(float(d), 3) for d in row["note_durations"]],
        })
    return out


def _enemies() -> list[dict]:
    out = []
    for key, row in _rows("DT_MelodySlime_Enemies.json").items():
        out.append({
            "id": key,
            "name": row["display_name"],
            "hp": float(row["max_hp"]),
            "toughness": float(row["max_toughness"]),
            "damage": float(row["base_damage"]),
            "speed": int(row["speed"]),
            "element": row["element"],
            "bpm": float(row["bpm"]),
        })
    return out


def _simple(name: str, keys: list[str]) -> list[dict]:
    return [{k: row.get(k) for k in keys} for row in _rows(name).values()]


def _biomes() -> list[dict]:
    out = []
    for path in sorted((ROOT / "Docs" / "WorldGen").glob("GAEA_SETUP_*.json")):
        d = json.loads(path.read_text(encoding="utf-8-sig"))
        recipe = d.get("recipe", {})
        out.append({
            "id": d["setup_id"],
            "name": d["display_name"],
            "seed": d.get("world_seed", 3900),
            "movement": d["musical_binding"]["movement_id"],
            "midi_preset": d["musical_binding"]["midi_preset"],
            "dressing": d["musical_binding"]["dressing_style"],
            "intent": d["musical_binding"]["design_intent"],
            "graph_chain": recipe.get("graph_chain", []),
            "height_range_m": recipe.get("height_range_m"),
            "terrace_strength": recipe.get("terrace_strength"),
            "flow_strength": recipe.get("flow_strength"),
            "waterline_m": recipe.get("waterline_m"),
            "source_file": path.relative_to(ROOT).as_posix(),
        })
    return out


def main() -> None:
    payload = {
        "rules": _rules(),
        "skills": _skills(),
        "enemies": _enemies(),
        "artifacts": _simple("DT_Artifacts.json", ["artifact_id", "display_name", "description", "modifier_id", "cost_golden_tokens"]),
        "blessings": [b for b in _simple("DT_Blessings.json", ["blessing_id", "display_name", "description", "token_cost", "effect_type", "effect_value", "effect_str"])
                      if not b["blessing_id"].startswith("RoomMod_")],
        "burdens": _simple("DT_Burdens.json", ["burden_id", "display_name", "description", "rule_type", "magnitude", "duration_or_scope"]),
        "tokens": _simple("DT_MelodiaTokens.json", ["TokenID", "DisplayName", "Description", "Element", "Value", "Rarity"]),
        "biomes": _biomes(),
    }
    header = (
        "// GENERATED by tools/export_ue_data.py from the UE project's rules JSON, data tables and\n"
        "// Gaea world-gen setups. Do not edit by hand: edit the UE source and re-run the exporter.\n"
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(header + "export const UE = " + json.dumps(payload, indent=1) + ";\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(payload['skills'])} skills, {len(payload['enemies'])} enemies, "
          f"{len(payload['biomes'])} biomes, rules v{payload['rules']['version']}")


if __name__ == "__main__":
    main()
