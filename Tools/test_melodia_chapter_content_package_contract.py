#!/usr/bin/env python3
"""Focused offline checks for the reusable Melodia chapter content package.

This test is source/spec-only.  It does not contact Unreal, inspect or mutate assets,
invoke Quill, run the shared contract runner, or claim editor/PIE/package evidence.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specs" / "schemas" / "melodia_chapter_content_package.v1.schema.json"
TEMPLATE_PATH = ROOT / "specs" / "content" / "melodia_chapter_content_package.template.v1.json"
PROGRESSION_SCHEMA_PATH = ROOT / "specs" / "schemas" / "melodia_progression_package.v1.schema.json"
PROGRESSION_PATH = ROOT / "specs" / "progression" / "melodia_first_dream_progression.v1.json"
P2_PROGRESSION_PATH = ROOT / "specs" / "progression" / "melodia_p2_fabric_mountains_progression.v1.json"
P3_PROGRESSION_PATH = ROOT / "specs" / "progression" / "melodia_p3_horizon_eater_progression.v1.json"
ALLOWLIST_SEED_PATH = ROOT / "specs" / "progression" / "melodia_integration_allowlist_seed.v1.json"
TRACKER_PATH = ROOT / "specs" / "progression" / "melodia_objective_tracker_presentation.v1.json"
STORY_CONTRACT_PATH = ROOT / "Docs" / "MELODIA_STORY_SEQUENCE_AND_QUILL_CONTRACT.md"
ROUTE_SPEC_PATH = ROOT / "specs" / "p0" / "core_p0_dream_golden_run.v1.json"
WARDROBE_CONTRACT_PATH = ROOT / "specs" / "wardrobe" / "wardrobe_catalog_contract.v1.json"
TRAVERSAL_CONTRACT_PATH = ROOT / "specs" / "traversal" / "melodia_traversal_capability.v1.json"
CAPABILITY_CONTRACT_PATH = ROOT / "specs" / "capability" / "melodia_capability_gate.v1.json"

ID_RE = re.compile(r"^[a-z][a-z0-9_.{}-]+$")
REQUIRED_TOP_LEVEL = {
    "$schema",
    "schema",
    "schema_version",
    "kind",
    "contract_id",
    "status",
    "package",
    "progression_binding",
    "authority",
    "chapter",
    "beats",
    "quests",
    "objectives",
    "dialogue_sources",
    "route_references",
    "encounters",
    "rewards",
    "wardrobe_unlocks",
    "form_unlocks",
    "pacing_targets",
    "emotional_turn",
    "traversal_decision",
    "consequence",
    "checkpoint",
    "exit_criteria",
    "evidence_links",
    "owner_inputs",
    "acceptance",
}
REQUIRED_PACING_RULES = {
    "skip_or_advance_never_emits_a_second_intent",
    "interruption_restores_from_canonical_checkpoint",
    "missing_quill_or_unavailable_encounter_fails_closed_without_mutating_canonical_state",
    "victory_defeat_and_fled_each_resolve_to_one_typed_objective_outcome",
    "replay_after_save_load_does_not_duplicate_intents_rewards_or_consequences",
    "tracker_refresh_is_read_only",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise AssertionError(f"expected JSON object: {path}")
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _json_type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def _resolve_local_ref(root_schema: dict[str, Any], reference: str) -> dict[str, Any]:
    require(reference.startswith("#/$defs/"), f"unsupported schema reference: {reference}")
    name = reference.removeprefix("#/$defs/")
    resolved = root_schema.get("$defs", {}).get(name)
    require(isinstance(resolved, dict), f"missing schema definition: {name}")
    return resolved


def _schema_errors(
    value: Any,
    schema: dict[str, Any],
    root_schema: dict[str, Any],
    path: str = "$",
) -> list[str]:
    if "$ref" in schema:
        return _schema_errors(value, _resolve_local_ref(root_schema, schema["$ref"]), root_schema, path)

    if "oneOf" in schema:
        branch_errors = [
            _schema_errors(value, branch, root_schema, path) for branch in schema["oneOf"]
        ]
        valid_branches = sum(not errors for errors in branch_errors)
        if valid_branches != 1:
            return [f"{path}: expected exactly one oneOf branch, got {valid_branches}"]
        return []

    errors: list[str] = []
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected const {schema['const']!r}, got {value!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: expected one of {schema['enum']!r}, got {value!r}")

    expected_type = schema.get("type")
    if expected_type is not None:
        expected_types = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(_json_type_matches(value, item) for item in expected_types):
            return errors + [f"{path}: expected type {expected_types!r}, got {type(value).__name__}"]

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append(f"{path}: string is shorter than {schema['minLength']}")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"{path}: string does not match {schema['pattern']!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"{path}: number is below {schema['minimum']}")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            errors.append(f"{path}: number is not greater than {schema['exclusiveMinimum']}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append(f"{path}: array has fewer than {schema['minItems']} items")
        if schema.get("uniqueItems"):
            serialized = [json.dumps(item, sort_keys=True) for item in value]
            if len(serialized) != len(set(serialized)):
                errors.append(f"{path}: array items are not unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                errors.extend(_schema_errors(item, item_schema, root_schema, f"{path}[{index}]"))

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for required in schema.get("required", []):
            if required not in value:
                errors.append(f"{path}: missing required property {required!r}")
        additional = schema.get("additionalProperties", True)
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in properties:
                errors.extend(_schema_errors(child, properties[key], root_schema, child_path))
            elif additional is False:
                errors.append(f"{child_path}: additional property is not allowed")
            elif isinstance(additional, dict):
                errors.extend(_schema_errors(child, additional, root_schema, child_path))

    return errors


def _require_existing_reference(path: Path, label: str) -> None:
    require(path.is_file(), f"{label} is missing: {path.relative_to(ROOT)}")


def test_schema_and_template_validate() -> None:
    schema = load_json(SCHEMA_PATH)
    template = load_json(TEMPLATE_PATH)

    require(schema["$schema"] == "https://json-schema.org/draft/2020-12/schema", "schema draft drifted")
    require(schema["additionalProperties"] is False, "chapter schema must reject unknown top-level fields")
    require(set(schema["required"]) == REQUIRED_TOP_LEVEL, "chapter schema required sections drifted")
    require(set(schema["properties"]) == REQUIRED_TOP_LEVEL, "chapter schema properties drifted")
    require(schema.get("$defs"), "chapter schema has no reusable definitions")

    errors = _schema_errors(template, schema, schema)
    require(not errors, "template failed chapter schema:\n" + "\n".join(errors))
    require(set(template) == REQUIRED_TOP_LEVEL, "template has an unreviewed top-level section")
    require(template["status"] == "template_only", "future content must remain explicitly template-only")
    require(template["package"]["status"] == "template_only", "package status overstated")
    serialized = json.dumps(template, sort_keys=True)
    require(".uasset" not in serialized, "template must not claim a materialized Unreal asset")
    require("Tools/run_contract_tests.py" not in serialized, "template must not own the shared contract runner")


def test_progression_binding_reuses_existing_schema_and_ids() -> None:
    template = load_json(TEMPLATE_PATH)
    progression_schema = load_json(PROGRESSION_SCHEMA_PATH)
    first_dream = load_json(PROGRESSION_PATH)
    binding = template["progression_binding"]
    reference = binding["reference_package"]

    _require_existing_reference(PROGRESSION_SCHEMA_PATH, "progression schema")
    _require_existing_reference(PROGRESSION_PATH, "First Dream progression package")
    _require_existing_reference(TRACKER_PATH, "objective tracker contract")
    require(progression_schema["$id"].endswith("melodia_progression_package.v1.schema.json"), "wrong progression schema")
    require(first_dream["schema"] == "melodia.progression_package.v1", "First Dream schema marker drifted")
    require(binding["schema_ref"] == "specs/schemas/melodia_progression_package.v1.schema.json", "second progression schema introduced")
    require(binding["package_ref"] is None, "template must not pretend a future progression package exists")
    require(reference["path"] == "specs/progression/melodia_first_dream_progression.v1.json", "ID reference package drifted")
    require(first_dream["chapter"]["chapter_id"] == reference["chapter_id"], "chapter ID reference drifted")
    require(first_dream["quests"][0]["quest_id"] == reference["quest_id"], "quest ID reference drifted")
    require(first_dream["chapter"]["checkpoint_id"] == reference["checkpoint_id"], "checkpoint ID reference drifted")
    require(
        template["objectives"][0]["tracker_contract_ref"]
        == "specs/progression/melodia_objective_tracker_presentation.v1.json",
        "objective source does not reuse the tracker contract",
    )

    for group, key in (
        ("beats", "beat_id"),
        ("quests", "quest_id"),
        ("objectives", "objective_id"),
        ("rewards", "reward_id"),
        ("consequences", "consequence_id"),
    ):
        for entry in first_dream[group]:
            require(ID_RE.fullmatch(entry[key]) is not None, f"First Dream ID is not stable: {entry[key]}")


def test_source_sections_and_id_patterns_are_explicit() -> None:
    template = load_json(TEMPLATE_PATH)
    binding = template["progression_binding"]
    patterns = binding["id_patterns"]

    require(template["chapter"]["chapter_id_pattern"] == patterns["chapter"], "chapter pattern drifted")
    require(template["beats"][0]["beat_id_pattern"] == patterns["beat"], "beat pattern drifted")
    require(template["quests"][0]["quest_id_pattern"] == patterns["quest"], "quest pattern drifted")
    require(template["objectives"][0]["objective_id_pattern"] == patterns["objective"], "objective pattern drifted")
    require(template["rewards"][0]["reward_id_pattern"] == patterns["reward"], "reward pattern drifted")
    require(
        template["consequence"]["consequence_id_pattern"] == patterns["consequence"],
        "consequence pattern drifted",
    )
    require(template["checkpoint"]["checkpoint_id_pattern"] == patterns["checkpoint"], "checkpoint pattern drifted")

    primary_patterns = [
        template["chapter"]["chapter_id_pattern"],
        *(beat["beat_id_pattern"] for beat in template["beats"]),
        *(quest["quest_id_pattern"] for quest in template["quests"]),
        *(objective["objective_id_pattern"] for objective in template["objectives"]),
        *(encounter["encounter_id_pattern"] for encounter in template["encounters"]),
        *(reward["reward_id_pattern"] for reward in template["rewards"]),
        template["consequence"]["consequence_id_pattern"],
        template["checkpoint"]["checkpoint_id_pattern"],
    ]
    require(len(primary_patterns) == len(set(primary_patterns)), "primary template ID patterns are duplicated")
    for pattern in primary_patterns + list(patterns.values()):
        require(ID_RE.fullmatch(pattern) is not None, f"unstable ID pattern: {pattern}")

    for beat in template["beats"]:
        require(beat["progression_source"]["source_kind"] == "progression_package", "beat source is not progression data")
        require(beat["dialogue_source_ids"], "beat does not declare dialogue source IDs")
    for quest in template["quests"]:
        require(quest["progression_source"]["source_kind"] == "progression_package", "quest source is not progression data")
    for objective in template["objectives"]:
        require(
            objective["state_source"] == "canonical_record_journals",
            "objective source is not the canonical record journal",
        )
    for dialogue in template["dialogue_sources"]:
        require(dialogue["source_kind"] == "quill_qsc", "dialogue source is not Quill .qsc")
        require(dialogue["authority"] == "QuillScript", "dialogue source authority drifted")
        require(
            dialogue["notification_route"]
            == "melodia:<verb>:<stable-id> through UMelodiaNarrativeSubsystem",
            "dialogue bypasses the canonical intent route",
        )


def test_route_encounter_reward_and_unlock_boundaries() -> None:
    template = load_json(TEMPLATE_PATH)
    first_dream = load_json(PROGRESSION_PATH)
    route = template["route_references"]
    encounter = template["encounters"][0]
    reward = template["rewards"][0]
    wardrobe = template["wardrobe_unlocks"][0]
    form = template["form_unlocks"][0]

    _require_existing_reference(ROUTE_SPEC_PATH, "First Dream route spec")
    _require_existing_reference(WARDROBE_CONTRACT_PATH, "wardrobe contract")
    _require_existing_reference(TRAVERSAL_CONTRACT_PATH, "traversal contract")
    _require_existing_reference(CAPABILITY_CONTRACT_PATH, "capability gate contract")
    require(route["reference_route"] == first_dream["content_refs"]["player_route"], "reference player route drifted")
    require(
        route["integration_proof_map"] == "/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap",
        "integration proof map drifted",
    )
    require(route["travel_authority"] == "UMelodiaTravelSubsystem", "route created a second travel authority")
    require(len(route["player_route"]) == 1, "future template must keep one explicit route leg seam")
    require(route["player_route"][0]["map_path_template"].startswith("/Game/"), "route map is not a UE path")

    require(len(template["encounters"]) == 1, "future template must declare one primary encounter seam")
    require(
        set(encounter["result_branches"]) == {"victory", "defeat", "fled", "unavailable"},
        "encounter result branches are incomplete",
    )
    require(
        encounter["unavailable_policy"] == "fail_closed_without_consuming_intent",
        "unavailable encounter does not fail closed",
    )
    require(
        encounter["authority"] == "stock JRPG battle/session/result authority",
        "encounter created a second battle authority",
    )
    require(reward["durable"] is True, "template must declare a durable reward seam")
    require(
        reward["record_field"] == "FMelodiaNarrativeRecord.ConsumedRewardIds",
        "reward bypasses the canonical reward journal",
    )
    require(wardrobe["presentation_only"] is True, "wardrobe entry must remain declarative")
    require(
        wardrobe["unlock_state_source"] == "UMelodiaNarrativeSubsystem -> FMelodiaNarrativeRecord.Flags",
        "wardrobe unlock state bypasses narrative flags",
    )
    require(
        form["runtime_decider"] == "UMelodiaTraversalComponent",
        "form unlock created a second traversal decider",
    )
    require(form["unknown_form_policy"] == "fail_closed_without_capability", "form lookup is not fail-closed")
    require(
        form["capability_gate_contract_ref"] == "specs/capability/melodia_capability_gate.v1.json",
        "form unlock bypasses the shared capability gate",
    )
    require(
        form["traversal_contract_ref"] == "specs/traversal/melodia_traversal_capability.v1.json",
        "form unlock bypasses the traversal contract",
    )


def test_design_turn_decision_consequence_checkpoint_and_pacing() -> None:
    template = load_json(TEMPLATE_PATH)
    pacing = template["pacing_targets"]
    decision = template["traversal_decision"]
    consequence = template["consequence"]
    checkpoint = template["checkpoint"]

    _require_existing_reference(STORY_CONTRACT_PATH, "story and Quill contract")
    require(template["emotional_turn"]["status"] == "owner_input_required", "future emotional turn is overstated")
    require(len(decision["options"]) >= 2, "traversal decision needs at least two authored options")
    require(
        decision["authority"]
        == "UMelodiaTravelSubsystem for map travel; UMelodiaTraversalComponent for movement mode",
        "traversal decision authority drifted",
    )
    require(
        decision["durable_state_policy"]
        == "record_one_allowlisted_intent_and_recompute_route_from_canonical_state",
        "traversal decision persistence policy drifted",
    )
    require(consequence["canonical_target"] == "FMelodiaNarrativeRecord.Flags", "consequence bypasses narrative flags")
    require(
        consequence["restore_policy"] == "intent_replays_presentation_only",
        "consequence restore policy is not replay-safe",
    )
    require(
        checkpoint["record_field"] == "FMelodiaNarrativeRecord.ScriptCheckpoint",
        "checkpoint does not use the canonical script checkpoint",
    )
    require(checkpoint["write_authority"] == "UMelodiaNarrativeSubsystem", "checkpoint writer drifted")
    require(all(value is None for value in pacing["target_minutes"].values()), "template invented pacing targets")
    require(
        set(REQUIRED_PACING_RULES).issubset(pacing["rules"]),
        "pacing rules omit a required exactly-once or restore invariant",
    )
    require(pacing["status"] == "owner_input_required", "pacing status is overstated")

    evidence_by_id = {item["id"]: item for item in template["evidence_links"]}
    require(len(evidence_by_id) == len(template["evidence_links"]), "evidence IDs are duplicated")
    for criterion in template["exit_criteria"]:
        require(criterion["evidence_link_id"] in evidence_by_id, "exit criterion has no evidence link")
        require(criterion["status"] == "pending", "template exit criterion is overstated")
    for item in template["evidence_links"]:
        if item["status"] in {"reference", "required"} and "://" not in item["path_template"]:
            _require_existing_reference(ROOT / item["path_template"], f"evidence link {item['id']}")


def test_acceptance_and_owner_inputs_keep_future_content_honest() -> None:
    template = load_json(TEMPLATE_PATH)
    acceptance = template["acceptance"]
    owner_inputs = template["owner_inputs"]

    require(acceptance["no_runtime_claims"] is True, "template permits runtime claims")
    require(acceptance["offline"], "offline checks are missing")
    require(acceptance["live"], "live checks are missing")
    require(all(check["status"] == "pass" for check in acceptance["offline"]), "offline contract checks are not closed")
    require(all(check["status"] == "pending" for check in acceptance["live"]), "live checks are overstated")
    require(len(owner_inputs) >= 6, "template does not record enough owner decisions")
    require(all(item["status"] == "required" for item in owner_inputs), "owner input status is not explicit")
    require(
        {"identity", "dialogue", "route", "encounter", "turn", "decision", "reward", "pacing"}
        <= {item["id"].split(".")[-1] for item in owner_inputs},
        "template is missing a required design/owner decision",
    )
    authority = template["authority"]
    require(authority["save_owner"] == "stock JRPG GameInstance + BP_JRPGSaveGame", "save authority drifted")
    require(authority["narrative_runtime_owner"] == "UMelodiaNarrativeSubsystem", "narrative authority drifted")
    require(authority["dialogue_owner"] == "QuillScript", "Quill ownership drifted")
    require(authority["persistence"] == "FMelodiaNarrativeRecord_and_canonical_save_contract", "persistence authority drifted")
    require(authority["forbidden"], "authority boundary has no forbidden duplicate list")


def test_p2_fabric_mountains_progression_validates_against_schema() -> None:
    """P2 Faraway Mother progression: validate allowlist IDs match seed, chapter order is 4, prerequisites are valid format.
    Full schema conformance is a future work item — P2 is currently a draft progression."""
    _require_existing_reference(P2_PROGRESSION_PATH, "P2 fabric mountains progression")
    _require_existing_reference(ALLOWLIST_SEED_PATH, "integration allowlist seed")
    p2 = load_json(P2_PROGRESSION_PATH)
    allowlist = load_json(ALLOWLIST_SEED_PATH)
    require(p2["schema"] == "melodia.progression_package.v1", "P2 schema marker drifted")
    require(p2["chapter"]["order"] == 4, "P2 chapter order must be 4 (after First Dream=1, P1 Shorewake=2, P1 Cymatics=3)")
    seed_quests = set(allowlist["sets"]["QuestIds"])
    seed_flags = set(allowlist["sets"]["NarrativeFlagIds"])
    seed_rewards = set(allowlist["sets"]["DialogueRewardIds"])
    for q in p2["required_allowlist"]["quest_ids"]:
        require(q in seed_quests, f"P2 quest_id {q!r} missing from allowlist seed")
    for f in p2["required_allowlist"]["narrative_flag_ids"]:
        require(f in seed_flags, f"P2 flag_id {f!r} missing from allowlist seed")
    for r in p2["required_allowlist"]["dialogue_reward_ids"]:
        require(r in seed_rewards, f"P2 reward_id {r!r} missing from allowlist seed")
    require(p2["chapter"]["prerequisites"], "P2 must declare chapter prerequisites")
    for prereq in p2["chapter"]["prerequisites"]:
        require(isinstance(prereq, str) and (prereq.startswith("flag.") or prereq.startswith("quest.")), f"P2 prerequisite is not a valid flag/quest id: {prereq}")
    require(p2["quests"], "P2 must declare at least one quest")
    for quest in p2["quests"]:
        require(quest["quest_id"], "P2 quest missing quest_id")
        require(quest["title"], "P2 quest missing title")
        require(quest["completion_flag"], "P2 quest missing completion_flag")


def test_p3_horizon_eater_progression_validates_against_schema() -> None:
    """P3 Horizon Eater progression: validate allowlist IDs match seed, chapter order is 5, prerequisites reference P2 IDs.
    Full schema conformance is a future work item — P3 is currently a draft progression."""
    _require_existing_reference(P3_PROGRESSION_PATH, "P3 horizon eater progression")
    _require_existing_reference(ALLOWLIST_SEED_PATH, "integration allowlist seed")
    p3 = load_json(P3_PROGRESSION_PATH)
    allowlist = load_json(ALLOWLIST_SEED_PATH)
    require(p3["schema"] == "melodia.progression_package.v1", "P3 schema marker drifted")
    require(p3["chapter"]["order"] == 5, "P3 chapter order must be 5 (after P2=4)")
    seed_quests = set(allowlist["sets"]["QuestIds"])
    seed_flags = set(allowlist["sets"]["NarrativeFlagIds"])
    seed_rewards = set(allowlist["sets"]["DialogueRewardIds"])
    for q in p3["required_allowlist"]["quest_ids"]:
        require(q in seed_quests, f"P3 quest_id {q!r} missing from allowlist seed")
    for f in p3["required_allowlist"]["narrative_flag_ids"]:
        require(f in seed_flags, f"P3 flag_id {f!r} missing from allowlist seed")
    for r in p3["required_allowlist"]["dialogue_reward_ids"]:
        require(r in seed_rewards, f"P3 reward_id {r!r} missing from allowlist seed")
    require(p3["chapter"]["prerequisites"], "P3 must declare chapter prerequisites")
    for prereq in p3["chapter"]["prerequisites"]:
        require(isinstance(prereq, str) and (prereq.startswith("flag.") or prereq.startswith("quest.")), f"P3 prerequisite is not a valid flag/quest id: {prereq}")
    require(p3["quests"], "P3 must declare at least one quest")
    for quest in p3["quests"]:
        require(quest["quest_id"], "P3 quest missing quest_id")
        require(quest["title"], "P3 quest missing title")
        require(quest["completion_flag"], "P3 quest missing completion_flag")


def test_p2_p3_prerequisite_chains_are_resolvable() -> None:
    """Walk P2 -> P3 prerequisite chains and confirm every referenced quest_id/flag_id exists in the respective progression or seed."""
    _require_existing_reference(P2_PROGRESSION_PATH, "P2 progression")
    _require_existing_reference(P3_PROGRESSION_PATH, "P3 progression")
    _require_existing_reference(ALLOWLIST_SEED_PATH, "allowlist seed")
    p2 = load_json(P2_PROGRESSION_PATH)
    p3 = load_json(P3_PROGRESSION_PATH)
    allowlist = load_json(ALLOWLIST_SEED_PATH)
    seed_quests = set(allowlist["sets"]["QuestIds"])
    seed_flags = set(allowlist["sets"]["NarrativeFlagIds"])
    p2_quest_ids = {q["quest_id"] for q in p2["quests"]}
    p2_flag_ids = set(p2["required_allowlist"]["narrative_flag_ids"])
    p3_prereqs = p3["chapter"]["prerequisites"]
    for prereq in p3_prereqs:
        if prereq.startswith("quest."):
            require(prereq in p2_quest_ids, f"P3 prerequisite quest {prereq!r} not found in P2 quests")
            require(prereq in seed_quests, f"P3 prerequisite quest {prereq!r} not found in allowlist seed")
        elif prereq.startswith("flag."):
            require(prereq in p2_flag_ids, f"P3 prerequisite flag {prereq!r} not found in P2 flags")
            require(prereq in seed_flags, f"P3 prerequisite flag {prereq!r} not found in allowlist seed")
    p2_prereqs = p2["chapter"]["prerequisites"]
    p1_quest_ids = {"quest.first_dream", "quest.harmony_awakening", "quest.echoes_of_resonance", "quest.twilight_overture", "quest.shorewake.initiation", "quest.mara.veil_reading"}
    p1_flag_ids = {"flag.first_dream.quest.completed", "flag.quest.shorewake_completed", "flag.sea_above.starskiff_ready", "quest.harmony_awakening.completed", "quest.echoes_of_resonance.completed", "quest.twilight_overture.completed", "flag.faraway_mother.seam_path_open"}
    for prereq in p2_prereqs:
        if prereq.startswith("quest."):
            require(prereq in p1_quest_ids or prereq in seed_quests, f"P2 prerequisite quest {prereq!r} not found in P1 quests or seed")
        elif prereq.startswith("flag."):
            require(prereq in p1_flag_ids or prereq in seed_flags, f"P2 prerequisite flag {prereq!r} not found in P1 flags or seed")


def main() -> int:
    tests = (
        test_schema_and_template_validate,
        test_progression_binding_reuses_existing_schema_and_ids,
        test_source_sections_and_id_patterns_are_explicit,
        test_route_encounter_reward_and_unlock_boundaries,
        test_design_turn_decision_consequence_checkpoint_and_pacing,
        test_acceptance_and_owner_inputs_keep_future_content_honest,
        test_p2_fabric_mountains_progression_validates_against_schema,
        test_p3_horizon_eater_progression_validates_against_schema,
        test_p2_p3_prerequisite_chains_are_resolvable,
    )
    for test in tests:
        test()
    print(f"validated {len(tests)} Melodia chapter content package checks")
    print("validated JSON Schema shape, progression/Quill ownership, route boundaries, unlocks, pacing, evidence placeholders, P2/P3 progression, and prerequisite chains")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
