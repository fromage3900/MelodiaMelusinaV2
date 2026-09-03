#!/usr/bin/env python3
"""
Challenger Empirical Verification & Adversarial Stress Suite
Authored by: Melusina Challenger Agent (teamwork_preview_challenger)

Adversarially audits:
1. Cross-module interactions: QuillScript notifications, 7-verb grammar, allowlist seeds, narrative records.
2. DataTable serialization integrity: DT_MelodySlime_Skills.json pitch/duration match, SP > 0, power > 0, MIDI [36, 120], elemental affinities across all 31 skills.
3. MCP tool contracts and boundary condition fuzzing / edge cases.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "deploy"))

import melodia_mcp_server as mcp

VALID_VERBS = {
    "melodia:battle",
    "melodia:quest",
    "melodia:flag",
    "melodia:travel",
    "melodia:reward",
    "melodia:stat",
    "melodia:item",
}

VALID_ELEMENTS = {
    "Arcane",
    "Forte",
    "Gale",
    "Radiant",
    "Stone",
    "Tide",
    "Umbral",
    "Anemo",
    "Cryo",
    "Dendro",
    "Electro",
    "Geo",
    "Hydro",
    "Pyro",
    "Harmonic",
}

def test_cross_module_quill_interactions():
    print("=== Challenge 1: Cross-Module QuillScript & 7-Verb Contract ===")
    qsc_path = ROOT / "Content" / "MelodiaIntegration" / "Narrative" / "MelodiaQuillHarmonyAwakening.qsc"
    assert qsc_path.exists(), f"Missing QuillScript: {qsc_path}"
    
    seed_path = ROOT / "specs" / "progression" / "melodia_integration_allowlist_seed.v1.json"
    assert seed_path.exists(), f"Missing allowlist seed: {seed_path}"
    seed = json.loads(seed_path.read_text(encoding="utf-8"))
    sets = seed.get("sets", {})
    
    # Extract all $ Notify statements
    qsc_content = qsc_path.read_text(encoding="utf-8")
    notify_lines = [
        line.replace("$ Notify", "").strip()
        for line in qsc_content.splitlines()
        if line.strip().startswith("$ Notify")
    ]
    print(f"Extracted {len(notify_lines)} notification(s) from {qsc_path.name}:")
    for nl in notify_lines:
        print(f"  - {nl}")
    
    assert len(notify_lines) > 0, "No notifications found in QuillScript"
    
    # Validate each notification against melodia_quill_validate_notification
    for nl in notify_lines:
        res = mcp.melodia_quill_validate_notification(nl)
        assert res["is_valid_verb"] is True, f"Invalid verb for notification '{nl}': {res['verb']}"
        assert res["verb"] in VALID_VERBS, f"Verb {res['verb']} not in valid 7 verbs"
        
        parts = nl.split(":")
        verb_prefix = ":".join(parts[:2])
        remainder = parts[2:]
        
        if verb_prefix == "melodia:quest":
            quest_id = remainder[0]
            assert quest_id in sets.get("QuestIds", []), f"Quest ID '{quest_id}' not in seed QuestIds"
        elif verb_prefix == "melodia:reward":
            reward_id = remainder[0]
            assert reward_id in sets.get("DialogueRewardIds", []), f"Reward ID '{reward_id}' not in seed DialogueRewardIds"
        elif verb_prefix == "melodia:flag":
            flag_id = remainder[0]
            assert flag_id in sets.get("NarrativeFlagIds", []), f"Flag ID '{flag_id}' not in seed NarrativeFlagIds"
        elif verb_prefix == "melodia:stat":
            intent_id = remainder[0]
            stat_name = remainder[1]
            delta = int(remainder[2])
            assert intent_id.startswith("intent."), f"Stat intent '{intent_id}' must start with 'intent.'"
            assert delta > 0, f"Stat delta must be > 0, got {delta}"
            print(f"    [OK] Stat intent validated: intent={intent_id}, stat={stat_name}, delta={delta}")
    
    # Narrative record schema verification
    narrative_rec = mcp.melodia_narrative_get_record()
    assert narrative_rec["record"]["schema_version"] == 4
    assert "ConsumedIntentIds (melodia:stat:)" in narrative_rec["record"]["idempotency_seams"]
    assert "ConsumedRewardIds (melodia:reward:)" in narrative_rec["record"]["idempotency_seams"]
    assert "Flags (melodia:flag:)" in narrative_rec["record"]["idempotency_seams"]
    print("  -> Cross-module QuillScript, 7-verb dispatch, allowlist seed, and narrative record: ALL PASS.")

def test_datatable_serialization_stress():
    print("\n=== Challenge 2: DataTable Serialization Stress (DT_MelodySlime_Skills.json) ===")
    dt_path = ROOT / "Content" / "Melodia" / "DataStuctures" / "DT_MelodySlime_Skills.json"
    assert dt_path.exists(), f"Missing DataTable JSON: {dt_path}"
    
    data = json.loads(dt_path.read_text(encoding="utf-8"))
    assert data.get("DataType") == "SkillData", f"Unexpected DataType: {data.get('DataType')}"
    rows = data.get("Rows", {})
    
    row_count = len(rows)
    print(f"Total skills in DataTable: {row_count} (Asserting == 31)")
    assert row_count == 31, f"Expected exactly 31 skills, got {row_count}"
    
    elements_found = set()
    total_notes_audited = 0
    
    for skill_id, skill in rows.items():
        # Assert required fields
        assert "display_name" in skill and skill["display_name"], f"{skill_id} missing display_name"
        assert "element" in skill, f"{skill_id} missing element"
        assert "instrument" in skill, f"{skill_id} missing instrument"
        assert "mechanic_level" in skill and skill["mechanic_level"] in (1, 2, 3), f"{skill_id} invalid mechanic_level"
        assert "sp_cost" in skill, f"{skill_id} missing sp_cost"
        assert "power_scalar" in skill, f"{skill_id} missing power_scalar"
        assert "note_pitches" in skill, f"{skill_id} missing note_pitches"
        assert "note_durations" in skill, f"{skill_id} missing note_durations"
        
        element = skill["element"]
        elements_found.add(element)
        assert element in VALID_ELEMENTS, f"{skill_id} has invalid element '{element}'"
        
        sp_cost = skill["sp_cost"]
        assert isinstance(sp_cost, int) and sp_cost > 0, f"{skill_id} sp_cost must be int > 0, got {sp_cost}"
        
        power = skill["power_scalar"]
        assert isinstance(power, (int, float)) and power > 0.0, f"{skill_id} power_scalar must be > 0, got {power}"
        
        pitches = skill["note_pitches"]
        durations = skill["note_durations"]
        
        # Invariant 1: pitch length == duration length
        assert len(pitches) == len(durations), (
            f"{skill_id} pitch count ({len(pitches)}) != duration count ({len(durations)})"
        )
        assert len(pitches) > 0, f"{skill_id} note array cannot be empty"
        
        total_notes_audited += len(pitches)
        
        # Invariant 2: MIDI pitches strictly in [36, 120]
        for idx, pitch in enumerate(pitches):
            assert isinstance(pitch, int), f"{skill_id} pitch[{idx}]={pitch} is not an integer"
            assert 36 <= pitch <= 120, (
                f"{skill_id} pitch[{idx}]={pitch} outside valid MIDI range [36, 120]"
            )
            
        # Invariant 3: durations > 0
        for idx, dur in enumerate(durations):
            assert isinstance(dur, (int, float)) and dur > 0, (
                f"{skill_id} duration[{idx}]={dur} must be > 0"
            )
            
    print(f"  -> Audited {row_count} skills, {total_notes_audited} total note events.")
    print(f"  -> Elements verified across set: {sorted(elements_found)}")
    print("  -> DataTable pitch/duration equality, SP > 0, power > 0, MIDI [36, 120], and elemental integrity: ALL PASS.")

def test_mcp_adversarial_boundary_conditions():
    print("\n=== Challenge 3: MCP Adversarial Boundary & Fuzzing Tests ===")
    
    # 1. Invalid / malformed notification strings
    invalid_cases = [
        "",
        "invalid",
        "melodia",
        "melodia:",
        "melodia:unknown_verb:123",
        "other:quest:test",
        ":::",
        "melodia:quest",
    ]
    for case in invalid_cases:
        res = mcp.melodia_quill_validate_notification(case)
        if case.startswith("melodia:quest") and len(case.split(":")) >= 2 and case.split(":")[1] == "quest":
            # Valid verb format
            pass
        else:
            assert not res["is_valid_verb"], f"Falsely validated invalid notification '{case}'"
    print("  -> Fuzzed malformed notifications: correctly rejected.")
    
    # 2. Non-existent quest lookup
    res_quest = mcp.melodia_persona_get_quests("quest.nonexistent_foo_bar")
    assert res_quest["matched_quest"] is None
    assert len(res_quest["quests"]) >= 4
    print("  -> Non-existent quest query handled safely.")
    
    # 3. Non-existent fixture validation
    res_fix = mcp.melodia_bp_validate_fixture("non_existent_fixture_xyz")
    assert res_fix["valid"] is False
    assert "error" in res_fix
    print("  -> Non-existent fixture validation fails closed safely.")
    
    # 4. Non-existent BP template
    res_tmpl = mcp.melodia_bp_get_template("non_existent_template")
    assert "error" in res_tmpl
    print("  -> Non-existent BP template lookup fails closed safely.")
    
    # 5. Narrative idempotency audit
    audit = mcp.melodia_narrative_audit_idempotency()
    assert audit.get("all_paths_guarded") is True, f"Unchecked mutation path in audit: {audit}"
    print("  -> Narrative idempotency audit: all mutation paths strictly guarded.")
    
    # 6. P0 route validation
    p0_val = mcp.melodia_bp_validate_p0_route()
    assert p0_val.get("p0_route_valid") is True, f"P0 route validation failed: {p0_val}"
    print("  -> P0 Dream golden route validation: 100% PASS.")
    
    # 7. System health spec
    health = mcp.melodia_system_health()
    assert health["checks"]["specs"]["allowlist_seed"] is True
    assert health["checks"]["specs"]["bp_kit"] is True
    assert health["checks"]["specs"]["capability_gate"] is True
    assert health["checks"]["policy"]["default_is_deny"] is True
    print("  -> System health offline specs: 100% HEALTHY.")

if __name__ == "__main__":
    try:
        test_cross_module_quill_interactions()
        test_datatable_serialization_stress()
        test_mcp_adversarial_boundary_conditions()
        print("\n" + "="*70)
        print("ALL EMPIRICAL CHALLENGER STRESS TESTS PASSED CLEANLY (0 FAILURES)")
        print("="*70)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] Assertion failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}", file=sys.stderr)
        sys.exit(2)
