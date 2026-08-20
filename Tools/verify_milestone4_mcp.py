#!/usr/bin/env python3
"""
Comprehensive Verification Script for Milestone 4: Active Daemon Content Generation & Live MCP Injection.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import deploy.melodia_mcp_server as mcp_server
from Tools.test_melodia_mcp import run_all as run_mcp_tests


def test_fixture_verification() -> dict:
    print("=== Verification 1: Blueprint Fixtures (List & Validate) ===")
    list_result = mcp_server.melodia_bp_list_fixtures()
    fixtures = list_result.get("fixtures", [])
    fixture_names = {f["name"] for f in fixtures}
    print(f"Total fixtures discovered: {len(fixtures)}")

    # Verify new skill fixtures exist
    assert "cadence_strike_resonance_skill.v1" in fixture_names or "cadence_strike_resonance_skill" in fixture_names
    assert "lullaby_mend_resonance_skill.v1" in fixture_names or "lullaby_mend_resonance_skill" in fixture_names

    val1 = mcp_server.melodia_bp_validate_fixture("cadence_strike_resonance_skill")
    print(f"Validation cadence_strike_resonance_skill: valid={val1['valid']}, missing={val1['missing_fields']}, readiness={val1['readiness']}")
    assert val1["valid"] is True
    assert val1["missing_fields"] == []
    assert val1["readiness"] == "L1"

    val2 = mcp_server.melodia_bp_validate_fixture("lullaby_mend_resonance_skill")
    print(f"Validation lullaby_mend_resonance_skill: valid={val2['valid']}, missing={val2['missing_fields']}, readiness={val2['readiness']}")
    assert val2["valid"] is True
    assert val2["missing_fields"] == []
    assert val2["readiness"] == "L1"

    return {"list_count": len(fixtures), "cadence_valid": val1["valid"], "lullaby_valid": val2["valid"]}


def test_quest_verification() -> dict:
    print("\n=== Verification 2: Persona / Narrative Quests ===")
    all_quests = mcp_server.melodia_persona_get_quests()
    quest_ids = [q["quest_id"] for q in all_quests.get("quests", [])]
    print(f"Registered Quests ({len(quest_ids)}): {quest_ids}")

    # Verify newly generated quests are present
    expected_new_quests = [
        "quest.harmony_awakening",
        "quest.echoes_of_resonance",
        "quest.twilight_overture",
    ]
    for nq in expected_new_quests:
        assert nq in quest_ids, f"Quest {nq} missing from registered quests"
        filtered = mcp_server.melodia_persona_get_quests(nq)
        assert filtered["requested_quest"] == nq
        assert filtered["matched_quest"] is not None
        assert filtered["matched_quest"]["quest_id"] == nq
        print(f"  Verified quest retrieval: {nq} -> matched={filtered['matched_quest']}")

    # Verify Quill notification validator matches new quest
    q_notif = mcp_server.melodia_quill_validate_notification("melodia:quest:quest.harmony_awakening")
    print(f"Quill notification validation for quest.harmony_awakening: valid_verb={q_notif['is_valid_verb']}, matches={q_notif['known_allowlist_matches']}")
    assert q_notif["is_valid_verb"] is True
    assert "quest.harmony_awakening" in q_notif["known_allowlist_matches"]

    return {"total_quests": len(quest_ids), "verified_quests": expected_new_quests}


def test_rhythm_skills_verification() -> dict:
    print("\n=== Verification 3: Rhythm Combat Skills in Live MCP & Data Table ===")
    rhythm_result = mcp_server.melodia_rhythm_list_skills()
    skills = rhythm_result.get("skills", [])
    dt_skills = rhythm_result.get("data_table_skills", [])
    dt_ids = {s["skill_id"] for s in dt_skills}

    print(f"Config DataAsset Skills Count: {len(skills)}")
    print(f"DataTable Skills Count: {len(dt_skills)}")
    assert len(skills) > 0
    assert len(dt_skills) >= 24

    # Verify key new generated skill rows
    expected_skills = [
        "Chart_Forte_CadenceStrike",
        "Chart_Radiant_LullabyMend",
        "Chart_Umbral_DissonantSilence",
        "Chart_Arcane_CosmicResonance",
        "Chart_Tide_AbyssalSong",
        "Chart_Stone_TerraFirma",
        "Chart_Gale_StormChase",
    ]
    for es in expected_skills:
        assert es in dt_ids, f"Generated skill {es} not found in DataTable skills"
        skill_entry = next(s for s in dt_skills if s["skill_id"] == es)
        print(f"  Verified Skill Row: {es} | Element: {skill_entry['element']} | Instrument: {skill_entry['instrument']} | SP Cost: {skill_entry['sp_cost']} | Power: {skill_entry['power_scalar']} | Notes: {skill_entry['note_count']}")

    return {"config_skills": len(skills), "dt_skills": len(dt_skills), "verified_skills": expected_skills}


def test_data_table_file_integrity() -> dict:
    print("\n=== Verification 4: DataTable File Ingestion Integrity ===")
    dt_path = PROJECT_ROOT / "Content" / "Melodia" / "DataStuctures" / "DT_MelodySlime_Skills.json"
    assert dt_path.exists(), f"{dt_path} does not exist"
    data = json.loads(dt_path.read_text(encoding="utf-8"))
    assert data.get("DataType") == "SkillData"
    rows = data.get("Rows", {})
    assert len(rows) >= 30
    for sid, row in rows.items():
        assert "display_name" in row
        assert "element" in row
        assert "instrument" in row
        assert "mechanic_level" in row
        assert "sp_cost" in row
        assert "power_scalar" in row
        assert "note_pitches" in row and len(row["note_pitches"]) >= 6
        assert "note_durations" in row and len(row["note_durations"]) == len(row["note_pitches"])

    print(f"DT_MelodySlime_Skills.json verified: {len(rows)} valid rows with complete schema contracts.")
    return {"dt_rows_count": len(rows)}


def main() -> int:
    print("=================================================================")
    print("STARTING PROGRAMMATIC VERIFICATION FOR MILESTONE 4")
    print("=================================================================\n")

    res_fixtures = test_fixture_verification()
    res_quests = test_quest_verification()
    res_skills = test_rhythm_skills_verification()
    res_dt = test_data_table_file_integrity()

    print("\n=== Verification 5: Running Complete 13/13 MCP Test Suite ===")
    mcp_code = run_mcp_tests()
    assert mcp_code == 0, "MCP test suite failed!"

    print("\n=================================================================")
    print("ALL PROGRAMMATIC MCP AND INGESTION VERIFICATIONS PASSED (100%)")
    print("=================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
