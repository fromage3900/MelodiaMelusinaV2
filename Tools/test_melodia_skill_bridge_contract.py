#!/usr/bin/env python3
"""Offline assertions for the Melodia skill-definition bridge design gate."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "specs" / "skills" / "melodia_skill_definition_bridge.v1.json"
SKILL = ROOT / "specs" / "skills" / "melodia_skill_execution.v1.json"


def load(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    assert isinstance(value, dict), path
    return value


def main() -> int:
    bridge = load(BRIDGE)
    skill = load(SKILL)
    architecture = bridge["recommended_architecture"]
    assert architecture["canonical_definition_authority"] == "UMelodiaSongSkillDefinition_in_MelodiaCore"
    assert architecture["migration_source_definition"] == "UMelodiaRhythmSkillDefinition_in_BS_GodFile"
    assert architecture["canonical_command_authority"] == "UMelodiaBattleSession"
    assert architecture["resource_authority"] == "UMelodiaCombatStateComponent_for_battle_skill_points"

    mapping = bridge["field_mapping_policy"]
    direct = mapping["direct_identity"]
    direct_names = [item["canonical"] for item in direct]
    assert len(direct_names) == len(set(direct_names))
    assert {"SkillId", "DisplayName", "Description", "TargetMode", "TargetCount", "SkillPointCost"}.issubset(direct_names)
    assert all(item.get("rule") for item in direct)

    separate = mapping["separate_semantics_no_enum_coercion"]
    separate_names = {item["canonical"] for item in separate}
    assert {"EffectType", "Element", "Niche", "CooldownPolicy", "ManaCost"}.issubset(separate_names)
    assert all(item.get("rule") for item in separate)
    assert "never_derive" in next(item["rule"] for item in separate if item["canonical"] == "EffectType")
    assert "separate_explicit" in next(item["rule"] for item in separate if item["canonical"] == "ManaCost")

    chart = mapping["chart_precedence"]
    assert chart["preferred"] == "ChartNotes"
    assert "LaneIndex" in chart["lane_rule"]
    assert "modulo" in " ".join(chart["forbidden_derivations"])

    invariants = bridge["offline_validation_invariants"]
    assert len(invariants) >= 7
    assert bridge["request_protocol"]["request_id"]
    assert bridge["request_protocol"]["cancel"]
    assert skill["bridge_contract"] == "specs/skills/melodia_skill_definition_bridge.v1.json"
    assert skill["current_native_surface"]["bridge_required_before_bp"] is True
    assert bridge["status"] == "design_gate_before_native_refactor"
    print("validated skill bridge contract: explicit mappings, chart precedence, cost separation, and replay rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
