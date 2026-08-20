"""Validate contract-only Melodia gameplay fixture specifications.

This is intentionally an offline gate. It does not claim that a Blueprint or DataAsset
exists, compiles, reaches a map, or passes PIE.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "specs" / "blueprints" / "melodia_content_package.v1.json"
RELEASE_MANIFEST_PATH = ROOT / "specs" / "content" / "melodia_content_release_manifest.v1.json"
ALLOWLIST_SEED_PATH = ROOT / "specs" / "progression" / "melodia_integration_allowlist_seed.v1.json"
FIXTURE_DIR = ROOT / "specs" / "blueprints" / "fixtures"

FORBIDDEN_TEXT = (
    "direct OpenLevel calls",
    "direct save-file mutation",
    "new GameMode authority",
    "duplicated traversal state machine",
)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise AssertionError(f"expected object: {path}")
    return value


def main() -> int:
    contract = load_json(CONTRACT_PATH)
    release_manifest = load_json(RELEASE_MANIFEST_PATH)
    allowlist_seed = load_json(ALLOWLIST_SEED_PATH)
    assert release_manifest["kind"] == "melodia_content_release_manifest_contract"
    assert release_manifest["contract_id"] == "melodia_content_release_manifest"
    assert "PackageRefs" in release_manifest["required_manifest_fields"]
    assert release_manifest["schedule_rules"]["clock"] == "UTC"
    assert release_manifest["schedule_rules"]["blueprints_must_not_own_schedule_state"] is True
    assert release_manifest["cleanup_policy"]["rules"]
    assert "direct save-file mutation" in release_manifest["authority_rules"]["forbidden"]
    assert allowlist_seed["kind"] == "melodia_integration_allowlist_seed"
    assert allowlist_seed["target_asset"] == "/Game/MelodiaIntegration/Config/DA_MelodiaIntegrationConfig"
    assert allowlist_seed["merge_policy"]["never_remove_existing_ids"] is True
    capability_gate_path = ROOT / contract["capability_gate_contract"]
    capability_gate = load_json(capability_gate_path)
    assert capability_gate["kind"] == "melodia_capability_gate_contract"
    assert capability_gate["status"] == "offline_contract_ready_live_registry_evidence_pending"
    assert capability_gate["authority"]["canonical_lookup"] == (
        "UMelodiaTraversalCapabilityRegistry -> registered read-only provider"
    )
    assert capability_gate["evaluation_result"]["no_mutation_on_block"] is True
    assert "missing_provider" in capability_gate["evaluation_result"]["block_reason"]
    assert "blocked_context" in capability_gate["evaluation_result"]["block_reason"]
    assert "on_load_complete" in capability_gate["re_evaluation_triggers"]
    assert set(capability_gate["content_kind_routes"]) == {
        "skill",
        "enemy",
        "encounter",
        "portal",
        "traversal",
        "world_challenge",
        "state_anchor",
    }
    assert "grant capability locally" in capability_gate["blueprint_invariants"]["forbidden"]
    world_challenge_adapter_path = ROOT / contract["world_challenge_adapter_contract"]
    world_challenge_adapter = load_json(world_challenge_adapter_path)
    assert world_challenge_adapter["status"] == "native_adapter_source_wired_closed_editor_build_pending"
    assert world_challenge_adapter["required_native_surface"]["read_completion"].startswith(
        "BlueprintPure IsWorldChallengeCompleted"
    )
    assert world_challenge_adapter["required_native_surface"]["commit"].startswith("BlueprintCallable CommitWorldChallenge")
    assert world_challenge_adapter["transient_attempt_surface"]["native_adapter_required"] is False
    assert world_challenge_adapter["transient_attempt_surface"]["persistence_rule"] == (
        "never write attempt progress to FMelodiaNarrativeRecord"
    )
    assert world_challenge_adapter["commit_transaction"]["rollback_rule"].startswith("if any preflight check fails")
    assert "unknown_challenge" in world_challenge_adapter["required_native_surface"]["failure_reason"]
    assert "WorldChallengeIds" in " ".join(world_challenge_adapter["commit_transaction"]["preflight"])
    assert "BP verifies an allowed shared capability-gate result" in world_challenge_adapter["commit_transaction"]["preflight"][0]
    assert world_challenge_adapter["gate_boundary"]["native_obligation"].startswith("validate canonical IDs")
    assert "call SetNarrativeFlag and GrantDialogueReward as separate unsynchronized completion steps" in world_challenge_adapter["blueprint_invariants"]["forbidden"]
    state_anchor_adapter_path = ROOT / contract["state_anchor_adapter_contract"]
    state_anchor_adapter = load_json(state_anchor_adapter_path)
    assert state_anchor_adapter["status"] == "native_adapter_source_wired_closed_editor_build_pending"
    assert state_anchor_adapter["required_native_surface"]["read"].startswith(
        "BlueprintPure IsStateAnchorApplied"
    )
    assert state_anchor_adapter["required_native_surface"]["apply"].startswith("BlueprintCallable ApplyStateAnchor")
    assert "unknown_anchor" in state_anchor_adapter["required_native_surface"]["failure_reason"]
    assert "StateAnchorIds" in " ".join(state_anchor_adapter["apply_transaction"]["preflight"])
    assert "BP verifies an allowed shared capability-gate result" in state_anchor_adapter["apply_transaction"]["preflight"][0]
    assert state_anchor_adapter["gate_boundary"]["native_obligation"].startswith("validate canonical IDs")
    assert state_anchor_adapter["apply_transaction"]["rollback_rule"].startswith("if any operation is invalid")
    assert "AMelodiaOpeningStateAnchor remains opening-specific" in state_anchor_adapter["authority"]["opening_boundary"]
    narrative_header = ROOT / "Source" / "BS_GodFile" / "MelodiaIntegration" / "MelodiaNarrativeSubsystem.h"
    narrative_cpp = ROOT / "Source" / "BS_GodFile" / "MelodiaIntegration" / "MelodiaNarrativeSubsystem.cpp"
    narrative_header_text = narrative_header.read_text(encoding="utf-8")
    narrative_cpp_text = narrative_cpp.read_text(encoding="utf-8")
    assert "IsWorldChallengeCompleted" in narrative_header_text and "IsWorldChallengeCompleted" in narrative_cpp_text
    assert "CommitWorldChallenge" in narrative_header_text and "CommitWorldChallenge" in narrative_cpp_text
    assert "IsStateAnchorApplied" in narrative_header_text and "IsStateAnchorApplied" in narrative_cpp_text
    assert "ApplyStateAnchor" in narrative_header_text and "ApplyStateAnchor" in narrative_cpp_text
    assert "All validation is complete before the first canonical field is changed" in narrative_cpp_text
    assert "The complete operation list has been validated before this transaction" in narrative_cpp_text
    traversal_contract_path = ROOT / contract["traversal_authority_contract"]
    traversal_contract = load_json(traversal_contract_path)
    assert traversal_contract["status"] == "native_request_api_build_passed_live_evidence_pending"
    assert traversal_contract["current_native_surface"]["public_capability_request_api"] == "compiled_and_uht_reflected_live_editor_verification_pending"
    assert traversal_contract["current_native_surface"]["source_supported_modes"] == ["Grounded", "Glide"]
    capability_seam = traversal_contract["current_native_surface"]["capability_query_seam"]
    assert capability_seam["status"] == "source_wired_closed_editor_build_pending"
    assert capability_seam["canonical_query_provider"] == "UMelodiaWardrobeSubsystem"
    assert "BS_GodFile must not depend on MelodiaWardrobe" in capability_seam["module_dependency_rule"]
    assert "missing_provider" in capability_seam["fail_closed_reasons"]
    provider_header = ROOT / "Source" / "BS_GodFile" / "MelodiaIntegration" / "MelodiaTraversalCapabilityProvider.h"
    provider_cpp = ROOT / "Source" / "BS_GodFile" / "MelodiaIntegration" / "MelodiaTraversalCapabilityProvider.cpp"
    traversal_cpp = ROOT / "Source" / "BS_GodFile" / "MelodiaIntegration" / "MelodiaTraversalComponent.cpp"
    wardrobe_cpp = ROOT / "Plugins" / "MelodiaWardrobe" / "Source" / "MelodiaWardrobe" / "Private" / "MelodiaWardrobeSubsystem.cpp"
    assert provider_header.exists() and provider_cpp.exists()
    assert "UMelodiaTraversalCapabilityRegistry" in provider_cpp.read_text(encoding="utf-8")
    assert "RequestTraversalMode(EMelodiaTraversalMode::Glide)" in traversal_cpp.read_text(encoding="utf-8")
    assert "RegisterProvider(this, *this)" in wardrobe_cpp.read_text(encoding="utf-8")
    skill_contract_path = ROOT / contract["skill_execution_contract"]
    skill_contract = load_json(skill_contract_path)
    bridge_contract_path = ROOT / skill_contract["bridge_contract"]
    bridge_contract = load_json(bridge_contract_path)
    assert bridge_contract["status"] == "design_gate_before_native_refactor"
    assert bridge_contract["recommended_architecture"]["canonical_command_authority"] == "UMelodiaBattleSession"
    assert bridge_contract["recommended_architecture"]["resource_authority"] == "UMelodiaCombatStateComponent_for_battle_skill_points"
    assert bridge_contract["forbidden_until_complete"]
    assert skill_contract["status"] == "native_surface_verified_definition_bridge_required"
    assert skill_contract["current_native_surface"]["cooldown_authority"] is False
    assert skill_contract["current_native_surface"]["bridge_required_before_bp"] is True
    assert skill_contract["current_native_surface"]["bridge_gap"]["decision"].startswith("no_guessed_adapter")
    t3d_probe = load_json(ROOT / "specs" / "t3d" / "live_probe_print.json")
    assert t3d_probe["nodes"] == [{"id": "Probe", "class": "K2Node_CallFunction", "semantic_label": "temporary_print_probe"}]
    assert t3d_probe["expected_postconditions"]["required_nodes"] == ["Probe"]
    assert t3d_probe["expected_postconditions"]["compile_error_count"] == 0
    assert t3d_probe["expected_postconditions"]["reexport_after_save"] is True
    fixture_paths = sorted(FIXTURE_DIR.glob("*.v1.json"))
    assert fixture_paths, f"no fixture specs found in {FIXTURE_DIR}"

    required_fields = {
        field
        for group in contract["package_fields"].values()
        for field in group
    }
    forbidden_contract_text = " ".join(contract["authority_rules"]["forbidden"])

    for path in fixture_paths:
        fixture = load_json(path)
        package = fixture.get("package", {})
        assert fixture.get("kind") == "melodia_content_fixture", path
        assert fixture.get("status") == "contract_spec_only", path
        assert fixture.get("readiness_level") == "L1", path
        assert required_fields.issubset(package), (
            f"{path.name}: missing package fields "
            f"{sorted(required_fields - set(package))}"
        )
        assert package.get("CapabilityGateContract") == "specs/capability/melodia_capability_gate.v1.json"

        blueprint = fixture.get("blueprint", {})
        assert blueprint.get("planned_asset"), path
        assert blueprint.get("parent_template"), path
        assert blueprint.get("runtime_authority"), path

        route = fixture.get("deterministic_fixture", {})
        assert route.get("fixture_map"), path
        assert route.get("entry_route"), path
        assert route.get("reset_route"), path
        assert fixture.get("failure_routes"), path
        assert fixture.get("evidence_required"), path

        serialized = json.dumps(fixture, sort_keys=True)
        for marker in FORBIDDEN_TEXT:
            assert marker not in serialized, f"{path.name}: forbidden marker {marker!r}"
        assert "OpenLevel" not in serialized
        assert "save-file" not in serialized

        content_kind = package.get("ContentKind")
        if content_kind == "world_challenge":
            definition = fixture.get("definition_contract", {})
            assert definition.get("challenge_id")
            assert definition.get("completion_flag_id")
            assert definition.get("reward_id")
            assert definition.get("completion_state_is_canonical") is True
            assert definition.get("reward_requires_committed_completion") is True
            assert definition.get("adapter_must_not_write_save_object_directly") is True
            assert definition["challenge_id"] in allowlist_seed["sets"]["WorldChallengeIds"]
            assert definition["completion_flag_id"] in allowlist_seed["sets"]["NarrativeFlagIds"]
            assert definition["reward_id"] in allowlist_seed["sets"]["DialogueRewardIds"]
        elif content_kind == "state_anchor":
            definition = fixture.get("definition_contract", {})
            assert definition.get("stable_anchor_id")
            assert definition.get("persistence_key")
            assert definition.get("apply_once_is_guarded_by_canonical_consumed_intent") is True
            assert definition.get("presentation_may_replay_without_reapplying_state") is True
            assert definition.get("adapter_must_not_write_save_object_directly") is True
            assert definition["stable_anchor_id"] in allowlist_seed["sets"]["StateAnchorIds"]
            for operation in definition["apply_operations"]:
                if operation["operation"] == "SetNarrativeFlag":
                    assert operation["flag_id"] in allowlist_seed["sets"]["NarrativeFlagIds"]
                elif operation["operation"] == "SetQuestActive":
                    assert operation["quest_id"] in allowlist_seed["sets"]["QuestIds"]
        elif content_kind == "enemy":
            definition = fixture.get("definition_contract", {})
            assert definition.get("enemy_id")
            assert definition.get("stock_session_owns_execution") is True
            assert definition.get("reward_requires_observed_defeat") is True
            assert definition.get("adapter_must_not_write_save_object_directly") is True
        elif content_kind == "encounter":
            definition = fixture.get("definition_contract", {})
            assert definition.get("encounter_id")
            assert definition.get("battle_request_authority")
            assert definition.get("abort_authority")
            assert definition.get("lock_is_runtime_only_until_result") is True
            assert definition.get("adapter_must_not_write_save_object_directly") is True
        elif content_kind == "portal":
            definition = fixture.get("definition_contract", {})
            assert definition.get("portal_id")
            assert definition.get("travel_request_authority") == "UMelodiaTravelSubsystem"
            assert definition.get("save_before_travel_required") is True
            assert definition.get("direct_open_level_forbidden") is True

    print(f"validated {len(fixture_paths)} Melodia fixture specs against {CONTRACT_PATH.name}")
    print(f"validated release manifest contract: {RELEASE_MANIFEST_PATH.name}")
    print(f"validated allowlist seed: {ALLOWLIST_SEED_PATH.name}")
    print(f"validated capability gate contract: {capability_gate_path.name}")
    print(f"validated world-challenge adapter contract: {world_challenge_adapter_path.name}")
    print(f"validated state-anchor adapter contract: {state_anchor_adapter_path.name}")
    print(f"validated traversal authority contract: {traversal_contract_path.name}")
    print(f"validated skill execution contract: {skill_contract_path.name}")
    print(f"authority forbidden-list entries checked: {len(contract['authority_rules']['forbidden'])}")
    assert forbidden_contract_text
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
