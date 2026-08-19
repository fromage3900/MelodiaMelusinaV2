#!/usr/bin/env python3
"""Regression checks for the offline Melodia BP materialization preflight."""

from __future__ import annotations

from melodia_bp_materialization_preflight import build_report


def main() -> int:
    report = build_report()
    assert report["kind"] == "melodia_blueprint_materialization_preflight"
    assert report["offline_only"] is True
    assert report["no_assets_created"] is True
    assert report["live_readonly"]["status"] == "not_contacted"
    assert report["summary"]["templates"] == 7
    assert report["summary"]["blocked"] == 1, report["templates"]
    assert len(report["live_plan"]) == 7
    assert [item["template"] for item in report["live_plan"]] == [
        "skill",
        "traversal_gate",
        "enemy",
        "encounter",
        "portal",
        "world_challenge",
        "state_anchor",
    ]
    for item in report["templates"]:
        assert item["checks"]["artifact_model_declared"], item["id"]
        assert item["checks"]["blockers_declared"], item["id"]
        assert item["offline_preflight"] in {
            "ready_for_live_materialization",
            "materialized_requires_live_readback",
            "blocked",
        }
        assert item["live_proof_still_required"]
        assert item["checks"]["adapter_contract_valid_when_declared"], item["id"]
    assert {item["id"] for item in report["templates"] if item["offline_preflight"] == "blocked"} == {
        "skill",
    }
    for item in report["templates"]:
        assert item["checks"]["planned_asset_absent_or_requires_live_readback"] == (
            not item["asset_on_disk"]
        ), item["id"]
    by_id = {item["id"]: item for item in report["templates"]}
    assert by_id["world_challenge"]["adapter_contract"] == "specs/progression/melodia_world_challenge_adapter.v1.json"
    assert by_id["state_anchor"]["adapter_contract"] == "specs/progression/melodia_state_anchor_adapter.v1.json"
    assert by_id["world_challenge"]["native_parent"] == "/Script/Engine.Actor"
    assert by_id["state_anchor"]["native_parent"] == "/Script/Engine.Actor"
    assert "DA_MelodiaIntegrationConfig.WorldChallengeIds entry" in by_id["world_challenge"]["declared_blockers"]
    assert "DA_MelodiaIntegrationConfig.StateAnchorIds entry" in by_id["state_anchor"]["declared_blockers"]
    assert by_id["world_challenge"]["required_config_allowlist"]["WorldChallengeIds"] == [
        "challenge.first_resonance_echo"
    ]
    assert by_id["world_challenge"]["required_config_allowlist_source"] == (
        "specs/progression/melodia_integration_allowlist_seed.v1.json"
    )
    assert by_id["state_anchor"]["required_config_allowlist"]["StateAnchorIds"] == [
        "anchor.first_dream.progress"
    ]
    assert by_id["state_anchor"]["required_config_allowlist_source"] == (
        "specs/progression/melodia_integration_allowlist_seed.v1.json"
    )
    print(
        f"validated materialization preflight: {report['summary']['templates']} templates, "
        "no assets created by the preflight, existing assets require live proof"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
