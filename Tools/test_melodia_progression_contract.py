"""Focused offline checks for the Melodia progression authority contract.

This test intentionally avoids Unreal, the editor, the shared contract runner,
PIE, and the opening Quill compiler.  It checks source-controlled package
shape, ordered transitions, exactly-once journals, tracker read-only rules, and
canonical-record restore semantics.
"""

from __future__ import annotations

import json
from pathlib import Path
import re

from melodia_objective_state import (
    InconsistentRecord,
    ObjectiveState,
    ObjectiveStateProjection,
    TransitionRejected,
    TransitionStatus,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "specs" / "schemas" / "melodia_progression_package.v1.schema.json"
PACKAGE_PATH = ROOT / "specs" / "progression" / "melodia_first_dream_progression.v1.json"
TRACKER_PATH = ROOT / "specs" / "progression" / "melodia_objective_tracker_presentation.v1.json"
ID_RE = re.compile(r"^[a-z][a-z0-9]*(?:[._:-][a-z0-9]+)*$")


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict), path
    return value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_schema_and_package_shape() -> None:
    schema = load(SCHEMA_PATH)
    package = load(PACKAGE_PATH)
    required = {
        "schema",
        "schema_version",
        "kind",
        "contract_id",
        "package",
        "content_refs",
        "authority",
        "required_allowlist",
        "chapter",
        "beats",
        "quests",
        "objectives",
        "rewards",
        "consequences",
        "intent_journal",
        "pacing",
        "acceptance",
    }
    require(required.issubset(schema["properties"]), "progression schema is missing required properties")
    require(package["schema"] == "melodia.progression_package.v1", "package schema marker drifted")
    require(package["schema_version"] == "1.0", "package schema version drifted")
    require(package["kind"] == "melodia_progression_package", "package kind drifted")
    require(package["package"]["status"] == "runtime_integration_pending", "package status must remain honest")
    require(
        package["content_refs"]["player_route"]
        == [
            "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
            "/Game/EnvSandbox/Environments/L_KaleidoNave",
        ],
        "first-chapter player route drifted",
    )
    require(
        package["content_refs"]["integration_proof_map"]
        == "/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap",
        "integration proof map reference drifted",
    )
    require(
        package["content_refs"]["source_notification_aliases"]
        == {"quest": "melodia_q_echo_01", "reward": "melodia_smoke_reward"},
        "legacy source aliases are not recorded as an explicit integration boundary",
    )
    require(
        package["authority"]["runtime_subsystem"] == "UMelodiaNarrativeSubsystem",
        "package created a different narrative authority",
    )
    require(
        package["authority"]["narrative_record"] == "FMelodiaNarrativeRecord",
        "package created a different persistence authority",
    )
    require(
        package["authority"]["save_field"] == "melodiaNarrativeRecord",
        "package does not point at the canonical save field",
    )
    source = PACKAGE_PATH.read_text(encoding="utf-8")
    for entity_group, id_key in (
        ("beats", "beat_id"),
        ("quests", "quest_id"),
        ("objectives", "objective_id"),
        ("rewards", "reward_id"),
        ("consequences", "consequence_id"),
    ):
        ids = [item[id_key] for item in package[entity_group]]
        require(len(ids) == len(set(ids)), f"duplicate IDs in {entity_group}")
        require(all(ID_RE.fullmatch(value) for value in ids), f"unstable ID in {entity_group}")
    require(".uasset" not in source, "progression package must not pretend to materialize an asset")
    allowlist = package["required_allowlist"]
    transition_flags = {
        transition["flag_id"]
        for objective in package["objectives"]
        for transition in (objective["completion"], objective["failure"])
        if transition is not None
    }
    consequence_flags = {
        consequence["target"]["id"]
        for consequence in package["consequences"]
        if consequence["target"]["type"] == "narrative_flag"
    }
    transition_flags.add(package["quests"][0]["completion_flag_id"])
    require(
        transition_flags | consequence_flags <= set(allowlist["narrative_flag_ids"]),
        "package transition writes are missing from its declared flag allowlist",
    )
    require(
        set(package["quests"][0]["reward_ids"]) <= set(allowlist["dialogue_reward_ids"]),
        "package reward is missing from its declared reward allowlist",
    )


def test_ordered_objectives_and_references() -> None:
    package = load(PACKAGE_PATH)
    chapter = package["chapter"]
    beats = {beat["beat_id"]: beat for beat in package["beats"]}
    quests = {quest["quest_id"]: quest for quest in package["quests"]}
    objectives = {objective["objective_id"]: objective for objective in package["objectives"]}
    rewards = {reward["reward_id"]: reward for reward in package["rewards"]}
    consequences = {
        consequence["consequence_id"]: consequence
        for consequence in package["consequences"]
    }

    require(
        [beat["order"] for beat in package["beats"]] == list(range(1, len(beats) + 1)),
        "beat order is not contiguous",
    )
    quest = quests["quest.first_dream"]
    require(
        [objectives[objective_id]["order"] for objective_id in quest["objective_ids"]]
        == list(range(1, len(quest["objective_ids"]) + 1)),
        "objective order is not contiguous",
    )
    require(chapter["beat_ids"] == [beat["beat_id"] for beat in package["beats"]], "chapter beat order drifted")
    require(chapter["quest_ids"] == ["quest.first_dream"], "chapter quest ownership drifted")
    require(
        set(chapter["exit_objective_ids"]).issubset(quest["objective_ids"]),
        "chapter exit objective is not in its quest",
    )

    objective_order = {
        objective_id: objective["order"] for objective_id, objective in objectives.items()
    }
    for objective in objectives.values():
        require(objective["quest_id"] == quest["quest_id"], "objective points at another quest authority")
        require(objective["beat_id"] in beats, f"unknown beat: {objective['beat_id']}")
        require(objective["state_rules"]["initial_state"] == "locked", "objective must start locked")
        require(objective["state_rules"]["ordered"] is True, "objective ordering is not explicit")
        for prerequisite in objective["prerequisites"]:
            if prerequisite["type"] == "objective":
                require(prerequisite["id"] in objectives, f"unknown objective prerequisite: {prerequisite['id']}")
                require(
                    objective_order[prerequisite["id"]] < objective["order"],
                    f"objective prerequisite points forward: {objective['objective_id']}",
                )
        for transition in (objective["completion"], objective["failure"]):
            if transition is None:
                continue
            for reward_id in transition["effects"]["reward_ids"]:
                require(reward_id in rewards, f"unknown reward effect: {reward_id}")
            for consequence_id in transition["effects"]["consequence_ids"]:
                require(consequence_id in consequences, f"unknown consequence effect: {consequence_id}")

    require(
        objectives["objective.first_dream.face_echo"]["state_rules"]["terminal_states"]
        == ["completed", "failed"],
        "battle objective must expose both terminal branches",
    )
    require(
        objectives["objective.first_dream.face_echo"]["completion"]["accepted_results"]
        == ["victory"],
        "victory result is not bound to the completion branch",
    )
    require(
        objectives["objective.first_dream.face_echo"]["failure"]["accepted_results"]
        == ["defeat", "fled"],
        "defeat/fled results are not bound to the failure branch",
    )
    require(
        objectives["objective.first_dream.record_consequence"]["prerequisites"][0]["satisfied_states"]
        == ["completed", "failed"],
        "consequence beat must accept both typed battle outcomes",
    )


def test_exactly_once_journal_and_pacing() -> None:
    package = load(PACKAGE_PATH)
    journal = package["intent_journal"]
    journal_by_id = {entry["intent_id"]: entry for entry in journal}
    require(len(journal) == len(journal_by_id), "intent journal contains duplicate IDs")
    require(all(entry["exactly_once"] is True for entry in journal), "journal entry is not exactly once")
    require(
        all(
            entry["record_field"]
            in (
                "FMelodiaNarrativeRecord.ConsumedIntentIds",
                "FMelodiaNarrativeRecord.ConsumedRewardIds",
            )
            for entry in journal
        ),
        "intent journal writes outside the canonical record",
    )

    expected_intents: set[str] = set()
    quest = package["quests"][0]
    expected_intents.update((quest["accept_intent_id"], quest["complete_intent_id"]))
    for objective in package["objectives"]:
        for transition in (objective["completion"], objective["failure"]):
            if transition is not None:
                expected_intents.add(transition["intent_id"])
    for reward in package["rewards"]:
        expected_intents.add(reward["grant_intent_id"])
    for consequence in package["consequences"]:
        expected_intents.add(consequence["intent_id"])
    require(set(journal_by_id) == expected_intents, "journal has an orphan or missing intent")

    package_beats = {beat["beat_id"]: beat for beat in package["beats"]}
    for beat in package["beats"]:
        require(
            set(beat["intent_ids"]).issubset(expected_intents),
            f"beat references an unjournaled intent: {beat['beat_id']}",
        )
        for prerequisite in beat["prerequisites"]:
            if prerequisite["type"] == "beat":
                require(
                    package_beats[prerequisite["id"]]["order"] < beat["order"],
                    f"beat prerequisite points forward: {beat['beat_id']}",
                )

    pacing = package["pacing"]
    windows = pacing["beat_windows"]
    require(
        [window["beat_id"] for window in windows] == package["chapter"]["beat_ids"],
        "pacing windows do not cover the authored beat order",
    )
    for previous, current in zip(windows, windows[1:]):
        require(previous["end_minute"] <= current["start_minute"], "pacing windows overlap")
    require(windows[-1]["end_minute"] <= pacing["target_minutes"]["maximum"], "pacing exceeds chapter target")
    rules = set(pacing["rules"])
    for required_rule in (
        "skip_or_advance_never_emits_a_second_intent",
        "interruption_restores_from_canonical_checkpoint",
        "missing_quill_fails_closed_without_mutating_canonical_state",
        "victory_defeat_and_fled_each_resolve_to_one_typed_objective_outcome",
        "replay_after_save_load_does_not_duplicate_intents_rewards_or_consequences",
    ):
        require(required_rule in rules, f"pacing rule missing: {required_rule}")


def test_tracker_is_read_only() -> None:
    package = load(PACKAGE_PATH)
    tracker = load(TRACKER_PATH)
    require(tracker["kind"] == "melodia_objective_tracker_presentation_contract", "tracker kind drifted")
    require(tracker["authority"]["read_subsystem"] == "UMelodiaNarrativeSubsystem", "tracker read authority drifted")
    require(tracker["authority"]["read_record"] == "FMelodiaNarrativeRecord", "tracker record authority drifted")
    require(tracker["authority"]["write_operations"] == [], "tracker is allowed to write gameplay state")
    require(tracker["materialization"]["widget_asset"] is None, "tracker contract materialized an asset")
    require(
        tracker["materialization"]["runtime_materialization_status"]
        == "blocked_without_live_editor_owner",
        "tracker live-editor status is overstated",
    )
    require(
        tracker["read_model"]["restore"]["write_back"] is False,
        "tracker restore is allowed to write back into the record",
    )
    require(
        tracker["read_model"]["current_objective"]["state"]
        == "locked|active|completed|failed",
        "tracker state vocabulary drifted",
    )
    require(
        tracker["read_model"]["optional_subobjectives"]["ordering"] == "quest.objective_ids order",
        "tracker sub-objectives do not use package order",
    )
    require(
        tracker["read_model"]["restore"]["source"]
        == [
            "FMelodiaNarrativeRecord.ActiveQuestIds",
            "FMelodiaNarrativeRecord.Flags",
            "FMelodiaNarrativeRecord.ConsumedIntentIds",
            "FMelodiaNarrativeRecord.ConsumedRewardIds",
            "FMelodiaNarrativeRecord.ScriptCheckpoint",
        ],
        "tracker restore does not read the canonical record fields",
    )
    require(
        package["authority"]["presentation"] == "specs/progression/melodia_objective_tracker_presentation.v1.json",
        "package does not point to tracker contract",
    )
    require(all(check["status"] == "pending" for check in tracker["acceptance"]["live"]), "tracker live status is overstated")


def _advance_to_battle(projection: ObjectiveStateProjection) -> None:
    projection.activate_quest("quest.first_dream")
    for objective_id in (
        "objective.first_dream.notice_absence",
        "objective.first_dream.choose_to_listen",
        "objective.first_dream.follow_quiet_chirp",
        "objective.first_dream.restore_resonance",
    ):
        require(
            projection.objective_state(objective_id) == ObjectiveState.ACTIVE,
            f"objective did not become active: {objective_id}",
        )
        result = projection.complete_objective(objective_id)
        require(result.status == TransitionStatus.APPLIED, f"objective did not apply: {objective_id}")
        replay = projection.complete_objective(objective_id)
        require(replay.status == TransitionStatus.ALREADY_APPLIED, f"objective replay was not idempotent: {objective_id}")


def test_objective_transitions_and_restore() -> None:
    package = load(PACKAGE_PATH)
    projection = ObjectiveStateProjection(package)
    require(
        projection.objective_state("objective.first_dream.notice_absence") == ObjectiveState.LOCKED,
        "objective became active before quest activation",
    )
    try:
        projection.complete_objective("objective.first_dream.notice_absence")
    except TransitionRejected:
        pass
    else:
        raise AssertionError("locked objective accepted a transition")

    _advance_to_battle(projection)
    require(
        projection.current_objective("quest.first_dream") == "objective.first_dream.face_echo",
        "current objective did not follow authored order",
    )
    victory = projection.complete_objective("objective.first_dream.face_echo", "complete")
    require(victory.status == TransitionStatus.APPLIED, "victory objective did not apply")
    snapshot_before_replay = projection.snapshot()
    replay = projection.complete_objective("objective.first_dream.face_echo", "complete")
    require(replay.status == TransitionStatus.ALREADY_APPLIED, "victory replay was not idempotent")
    require(projection.snapshot() == snapshot_before_replay, "victory replay mutated canonical state")
    require(
        projection.snapshot()["consumed_reward_ids"] == ["reward.first_resonance_echo"],
        "victory reward was not consumed exactly once",
    )
    projection.complete_objective("objective.first_dream.record_consequence")
    projection.complete_objective("objective.first_dream.checkpoint")
    completed = projection.complete_quest("quest.first_dream")
    require(completed.status == TransitionStatus.APPLIED, "quest did not complete")
    final_snapshot = projection.snapshot()
    require(
        projection.quest_state("quest.first_dream") == ObjectiveState.COMPLETED,
        "quest state did not restore to completed",
    )
    require(final_snapshot["script_checkpoint"] == "checkpoint.first_dream.complete", "chapter checkpoint missing")
    require(final_snapshot["consumed_intent_ids"] == sorted(final_snapshot["consumed_intent_ids"]), "snapshot intents are not deterministic")

    restored = ObjectiveStateProjection.from_snapshot(package, final_snapshot)
    require(restored.snapshot() == final_snapshot, "restored snapshot differs from source")
    require(
        restored.objective_state("objective.first_dream.face_echo") == ObjectiveState.COMPLETED,
        "restored objective lost its completed state",
    )
    require(
        restored.complete_objective("objective.first_dream.face_echo").status
        == TransitionStatus.ALREADY_APPLIED,
        "restored objective replay was not idempotent",
    )
    require(
        restored.complete_quest("quest.first_dream").status == TransitionStatus.ALREADY_APPLIED,
        "restored quest replay was not idempotent",
    )
    require(restored.snapshot() == final_snapshot, "restore replay changed canonical state")
    foreign_snapshot = json.loads(json.dumps(final_snapshot))
    foreign_snapshot["active_quest_ids"].append("quest.chapter_two.future")
    restored_with_foreign_state = ObjectiveStateProjection.from_snapshot(package, foreign_snapshot)
    require(
        "quest.chapter_two.future" in restored_with_foreign_state.snapshot()["active_quest_ids"],
        "progression package restore clobbered another chapter's canonical quest",
    )


def test_failure_branch_and_partial_restore_fail_closed() -> None:
    package = load(PACKAGE_PATH)
    projection = ObjectiveStateProjection(package)
    _advance_to_battle(projection)
    require(
        projection.objective_state("objective.first_dream.face_echo") == ObjectiveState.ACTIVE,
        "battle objective was not active",
    )
    failed = projection.complete_objective("objective.first_dream.face_echo", "fail")
    require(failed.status == TransitionStatus.APPLIED, "failure branch did not apply")
    require(
        projection.objective_state("objective.first_dream.face_echo") == ObjectiveState.FAILED,
        "failure branch did not expose failed state",
    )
    require(projection.snapshot()["consumed_reward_ids"] == [], "failure branch granted victory reward")
    projection.complete_objective("objective.first_dream.record_consequence")
    projection.complete_objective("objective.first_dream.checkpoint")
    projection.complete_quest("quest.first_dream")
    require(
        projection.quest_state("quest.first_dream") == ObjectiveState.COMPLETED,
        "failure branch could not finish the chapter checkpoint",
    )

    partial = ObjectiveStateProjection(package).snapshot()
    partial["flags"]["flag.first_dream.objective.notice_absence.completed"] = True
    try:
        ObjectiveStateProjection.from_snapshot(package, partial)
    except InconsistentRecord:
        pass
    else:
        raise AssertionError("partial objective marker was accepted during restore")


def main() -> int:
    tests = (
        test_schema_and_package_shape,
        test_ordered_objectives_and_references,
        test_exactly_once_journal_and_pacing,
        test_tracker_is_read_only,
        test_objective_transitions_and_restore,
        test_failure_branch_and_partial_restore_fail_closed,
    )
    for test in tests:
        test()
    print(f"validated {len(tests)} Melodia progression contract checks")
    print("validated ordered objective states, exactly-once journals, tracker read model, and restore semantics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
