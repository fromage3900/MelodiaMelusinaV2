#!/usr/bin/env python3
"""Melodia Universe Foundry v0.1 — deterministic mission compiler.

This is NOT a world generator and NOT a runtime authority.

It compiles:
    World Genome + exported/fixture World Delta
into:
    a deterministic mission DAG for Hermes to dispatch.

Jev may make only the closed decisions embedded in the genome. Existing Melodia
owners (World Compiler/PCG, Hython, TouchDesigner, Unreal, Echo) execute and
verify the actual work.

Usage:
  python Tools/universe_foundry.py validate \
      --genome specs/universe/faraway_mother.world_genome.v1.json \
      --delta specs/universe/faraway_mother.resolved_demo.world_delta.v1.json

  python Tools/universe_foundry.py compile \
      --genome specs/universe/faraway_mother.world_genome.v1.json \
      --delta specs/universe/faraway_mother.resolved_demo.world_delta.v1.json

  python Tools/universe_foundry.py show --mission Saved/UniverseFoundry/<world>/<mission>/mission.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
GENOME_SCHEMA = "melodia.world_genome/v1"
DELTA_SCHEMA = "melodia.world_delta/v1"
MISSION_SCHEMA = "melodia.universe_mission/v1"


class FoundryError(ValueError):
    pass


def _load(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FoundryError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise FoundryError(f"invalid JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise FoundryError(f"{path} must contain a JSON object")
    return data


def _canonical_bytes(data: Any) -> bytes:
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def content_hash(data: Any) -> str:
    return hashlib.sha256(_canonical_bytes(data)).hexdigest()


def _require_nonempty_string(data: dict[str, Any], key: str, errors: list[str]) -> None:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{key} must be a non-empty string")


def validate_genome(genome: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if genome.get("schema") != GENOME_SCHEMA:
        errors.append(f"schema must be {GENOME_SCHEMA!r}")

    _require_nonempty_string(genome, "world_id", errors)
    _require_nonempty_string(genome, "level_path", errors)

    if not isinstance(genome.get("seed"), int) or isinstance(genome.get("seed"), bool):
        errors.append("seed must be an integer")

    identity = genome.get("identity")
    if not isinstance(identity, dict):
        errors.append("identity must be an object")
    else:
        root = identity.get("root_pitch_class")
        if not isinstance(root, int) or isinstance(root, bool) or not (0 <= root <= 11):
            errors.append("identity.root_pitch_class must be an integer in [0,11]")
        bpm = identity.get("bpm")
        if not isinstance(bpm, int) or isinstance(bpm, bool) or not (40 <= bpm <= 220):
            errors.append("identity.bpm must be an integer in [40,220]")
        beats = identity.get("beats_per_bar")
        if not isinstance(beats, int) or isinstance(beats, bool) or not (1 <= beats <= 16):
            errors.append("identity.beats_per_bar must be an integer in [1,16]")
        for key in ("mode", "motif_id"):
            _require_nonempty_string(identity, key, errors)
        arc = identity.get("emotional_arc")
        if not isinstance(arc, list) or not arc or not all(isinstance(x, str) and x for x in arc):
            errors.append("identity.emotional_arc must be a non-empty string array")

    spatial = genome.get("spatial")
    if not isinstance(spatial, dict):
        errors.append("spatial must be an object")
    else:
        bounds = spatial.get("bounds_uu")
        if (
            not isinstance(bounds, list)
            or len(bounds) != 4
            or not all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in bounds)
        ):
            errors.append("spatial.bounds_uu must be [min_x,min_y,max_x,max_y]")
        elif not (bounds[0] < bounds[2] and bounds[1] < bounds[3]):
            errors.append("spatial.bounds_uu min values must be less than max values")

        basis = spatial.get("field_basis")
        if not isinstance(basis, dict) or basis.get("type") != "chladni":
            errors.append("spatial.field_basis.type must be 'chladni'")
        else:
            for key in ("mode_n", "mode_m"):
                value = basis.get(key)
                if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                    errors.append(f"spatial.field_basis.{key} must be a positive integer")

    content = genome.get("content")
    if not isinstance(content, dict):
        errors.append("content must be an object")
    else:
        for key in ("pcg_manifest", "resonance_integration_spec"):
            _require_nonempty_string(content, key, errors)
        recipe = content.get("world_compiler_recipe")
        if recipe is not None and (not isinstance(recipe, str) or not recipe):
            errors.append("content.world_compiler_recipe must be null or a non-empty string")

    decision_points = genome.get("decision_points")
    if not isinstance(decision_points, list):
        errors.append("decision_points must be an array")
    else:
        seen: set[str] = set()
        for idx, point in enumerate(decision_points):
            if not isinstance(point, dict):
                errors.append(f"decision_points[{idx}] must be an object")
                continue
            pid = point.get("id")
            if not isinstance(pid, str) or not pid:
                errors.append(f"decision_points[{idx}].id must be a non-empty string")
            elif pid in seen:
                errors.append(f"duplicate decision point id {pid!r}")
            else:
                seen.add(pid)
            if not isinstance(point.get("question"), str) or not point["question"]:
                errors.append(f"decision_points[{idx}].question must be non-empty")
            candidates = point.get("candidates")
            if (
                not isinstance(candidates, list)
                or len(candidates) < 2
                or not all(isinstance(x, str) and x for x in candidates)
            ):
                errors.append(f"decision_points[{idx}].candidates must have >=2 strings")
            elif len(set(candidates)) != len(candidates):
                errors.append(f"decision_points[{idx}].candidates must be unique")

    acceptance = genome.get("acceptance")
    if not isinstance(acceptance, dict):
        errors.append("acceptance must be an object")
    else:
        proofs = acceptance.get("required_proofs")
        if not isinstance(proofs, list) or not proofs or not all(isinstance(x, str) and x for x in proofs):
            errors.append("acceptance.required_proofs must be a non-empty string array")

    return errors


def validate_delta(delta: dict[str, Any], expected_world_id: str | None = None) -> list[str]:
    errors: list[str] = []
    if delta.get("schema") != DELTA_SCHEMA:
        errors.append(f"schema must be {DELTA_SCHEMA!r}")
    _require_nonempty_string(delta, "world_id", errors)
    if expected_world_id and delta.get("world_id") != expected_world_id:
        errors.append(
            f"delta world_id {delta.get('world_id')!r} does not match genome {expected_world_id!r}"
        )
    revision = delta.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        errors.append("revision must be a non-negative integer")
    source = delta.get("source_authority")
    if source not in {"game-save-export", "fixture"}:
        errors.append("source_authority must be 'game-save-export' or 'fixture'")
    fixture = delta.get("non_authoritative_fixture")
    if not isinstance(fixture, bool):
        errors.append("non_authoritative_fixture must be boolean")
    elif source == "fixture" and not fixture:
        errors.append("fixture source must set non_authoritative_fixture=true")
    elif source == "game-save-export" and fixture:
        errors.append("game-save-export must set non_authoritative_fixture=false")

    changes = delta.get("changes")
    if not isinstance(changes, list):
        errors.append("changes must be an array")
    else:
        seen: set[str] = set()
        allowed_domains = {"gameplay_export", "presentation", "ecology", "world_compiler_input"}
        for idx, change in enumerate(changes):
            if not isinstance(change, dict):
                errors.append(f"changes[{idx}] must be an object")
                continue
            cid = change.get("id")
            if not isinstance(cid, str) or not cid:
                errors.append(f"changes[{idx}].id must be non-empty")
            elif cid in seen:
                errors.append(f"duplicate change id {cid!r}")
            else:
                seen.add(cid)
            if change.get("domain") not in allowed_domains:
                errors.append(f"changes[{idx}].domain is not allowed")
            if "value" not in change:
                errors.append(f"changes[{idx}].value is required")
    return errors


def _task(
    task_id: str,
    phase: str,
    owner: str,
    depends_on: Iterable[str],
    mutation_surface: str,
    done_when: str,
    evidence_required: list[str],
    *,
    command: str | None = None,
    jev_decision: dict[str, Any] | None = None,
    brief: str | None = None,
) -> dict[str, Any]:
    return {
        "id": task_id,
        "phase": phase,
        "dispatcher": "hermes",
        "owner": owner,
        "depends_on": list(depends_on),
        "mutation_surface": mutation_surface,
        "command": command,
        "jev_decision": jev_decision,
        "brief": brief,
        "done_when": done_when,
        "evidence_required": evidence_required,
    }


def build_mission(genome: dict[str, Any], delta: dict[str, Any]) -> dict[str, Any]:
    genome_errors = validate_genome(genome)
    delta_errors = validate_delta(delta, genome.get("world_id"))
    if genome_errors or delta_errors:
        raise FoundryError(
            "validation failed:\n- " + "\n- ".join(genome_errors + delta_errors)
        )

    genome_hash = content_hash(genome)
    delta_hash = content_hash(delta)
    identity = f"{genome_hash}:{delta_hash}".encode("ascii")
    mission_short = hashlib.sha256(identity).hexdigest()[:16]
    mission_id = f"{genome['world_id']}-{mission_short}"

    tasks: list[dict[str, Any]] = []
    tasks.append(
        _task(
            "validate_inputs",
            "A_VALIDATE",
            "deterministic_validator",
            [],
            "none",
            "Genome and delta validate; referenced source contracts are identified.",
            [
                "validator_exit_zero",
                "genome_hash",
                "delta_hash",
            ],
            brief="Validate only. Do not mutate any DCC/editor/runtime surface.",
        )
    )

    decision_ids: list[str] = []
    for point in genome["decision_points"]:
        tid = f"jev_{point['id']}"
        decision_ids.append(tid)
        tasks.append(
            _task(
                tid,
                "B_DIRECTION",
                "jev",
                ["validate_inputs"],
                "none",
                "Jev returns exactly one candidate or HOLD with source/confidence preserved.",
                [
                    "source=jev-live_or_explicit_fallback",
                    "selected_candidate",
                    "confidence_or_distribution",
                    "independent_execution_result_later",
                ],
                jev_decision={
                    "decision_id": point["id"],
                    "question": point["question"],
                    "candidates": point["candidates"],
                    "closed_set": True,
                },
                brief=(
                    "Choose among the authored candidates only. Do not invent asset paths, "
                    "gameplay IDs, parameters, or mutation steps."
                ),
            )
        )

    world_recipe = genome["content"].get("world_compiler_recipe")
    recipe_task_id = "world_recipe_ready"
    if world_recipe:
        tasks.append(
            _task(
                recipe_task_id,
                "C_WORLD_DATA",
                "world_compiler",
                ["validate_inputs", *decision_ids],
                "repo/world-recipe-readonly-validation",
                "Existing World Compiler recipe validates without mutation.",
                ["world_compiler_validate_exit_zero"],
                command=f"python Tools/world_compiler.py validate {world_recipe}",
                brief="Validate the authored recipe. Do not compile in this task.",
            )
        )
    else:
        tasks.append(
            _task(
                recipe_task_id,
                "C_WORLD_DATA",
                "world_content_specialist",
                ["validate_inputs", *decision_ids],
                "repo/world-recipe-data-only",
                (
                    "A Faraway Mother World Compiler recipe exists and validates, reusing current "
                    "PCG/field/material contracts rather than creating a second compiler."
                ),
                [
                    "new_or_updated_recipe_path",
                    "world_compiler_validate_exit_zero",
                    "diff_shows_data_authoring_not_new_compiler",
                ],
                command=None,
                brief=(
                    "Author the missing World Compiler recipe from the existing Faraway Mother "
                    "PCG manifest and integration spec. Extend schema only if a proven content "
                    "requirement cannot be expressed."
                ),
            )
        )

    tasks.append(
        _task(
            "pcg_manifest_ready",
            "C_WORLD_DATA",
            "deterministic_pcg",
            ["validate_inputs"],
            "repo/generated-manifest",
            "Faraway Mother PCG manifest regenerates and validates deterministically.",
            ["pcg_manifest", "pcg_verify_exit_zero"],
            command=(
                "python Tools/PCG/build_faraway_mother_pcg_ecosystem.py --points-per-biome 30 "
                "&& python Tools/PCG/build_faraway_mother_pcg_ecosystem.py --verify"
            ),
        )
    )

    tasks.append(
        _task(
            "forge_static_field",
            "D_HYTHON",
            "hython",
            ["pcg_manifest_ready", recipe_task_id],
            "houdini/offline-only",
            "Static Faraway RGBA field + preview + manifest are generated and cross-check the PCG field math.",
            [
                "Saved/Audit/houdini_faraway_mother/T_FarawayMother_StaticField_RGBA.png",
                "Saved/Audit/houdini_faraway_mother/T_FarawayMother_StaticField_preview.png",
                "Saved/Audit/houdini_faraway_mother/resonance_field_manifest.json",
            ],
            command=(
                f"hython Tools/Houdini/vdm_fabric_mountains/faraway_static_field.py "
                f"--res 1024 --seed {genome['seed']}"
            ),
            brief="Forge deterministic source data only. Never mutate Unreal from Hython.",
        )
    )

    tasks.append(
        _task(
            "td_world_field",
            "E_TOUCHDESIGNER",
            "gemini_td",
            ["forge_static_field", *decision_ids],
            "MelodiaTouchDesigner/world_field-only",
            "Existing TD world_field scene consumes the static pack and replays QUIET->WORLD->AFTERIMAGE with zero touched-network cook errors.",
            [
                "td_commit_sha",
                "OUT_SHOW_FIELD_debug_capture",
                "replay_capture",
                "cook_errors_zero",
                "fps_and_cook_timing",
            ],
            command=None,
            brief=(
                "Work in fromage3900/MelodiaTouchDesigner through Embody/Envoy. Reuse the semantic "
                "bus and /project1/performance/scenes/world_field. Do not add a second OSC listener."
            ),
        )
    )

    tasks.append(
        _task(
            "ue_beauty_feed_live",
            "F_UNREAL_CANARY",
            "muse_ue",
            ["td_world_field"],
            "Unreal/single-editor-single-writer",
            "The canon UE_Beauty Spout2 sender is registered from the droppable sender actor and TD lookdev_comp shows the live feed.",
            [
                "beauty_feed_assets_ok",
                "spout_sender_registered_UE_Beauty",
                "td_spout_in_capture",
            ],
            command=None,
            brief=(
                "One sender name (UE_Beauty), one droppable actor "
                "(BP_UE_BeautySender over RT_UE_Beauty); never embed the sender "
                "in a production map and never invent a second sender name. "
                "Prove registration before claiming the live-lookdev lane."
            ),
        )
    )

    tasks.append(
        _task(
            "ue_field_receiver_canary",
            "F_UNREAL_CANARY",
            "muse_ue",
            ["td_world_field"],
            "Unreal/single-editor-single-writer",
            "TD OUT_SHOW_FIELD is visibly received in UE and diagnostic markers prove world/UV alignment.",
            [
                "receiver_transport_name",
                "debug_target_capture",
                "world_uv_alignment_capture",
                "scene_context_before_after",
            ],
            command=None,
            brief=(
                "Use one Unreal Editor and one chosen mutation writer. Prove the receiver on a debug "
                "target before touching production consumers."
            ),
        )
    )

    tasks.append(
        _task(
            "ue_three_consumers",
            "G_WORLD_RESPONSE",
            "muse_ue",
            ["ue_field_receiver_canary"],
            "Unreal/Faraway-presentation-only",
            "Fabric, Niagara, and Heart Gate/path presentation sample the same field while gameplay authority remains unchanged.",
            [
                "fabric_field_capture",
                "niagara_field_capture",
                "heart_gate_resolution_capture",
                "td_disconnected_fallback_capture",
            ],
            command=None,
            brief=(
                "Presentation only: no second MPC writer, no new gameplay authority, no runtime Houdini, "
                "no second Niagara framework."
            ),
        )
    )

    tasks.append(
        _task(
            "persistence_roundtrip",
            "H_PERSISTENCE",
            "ue_runtime_owner",
            ["ue_three_consumers"],
            "Unreal/save-and-regeneration-existing-owners",
            (
                "A real game-save-export delta is captured, generated world content is rebuilt from the "
                "same genome, and the exported player consequence is reapplied through canonical owners."
            ),
            [
                "real_game_save_export_delta",
                "pre_destroy_state_capture",
                "regenerated_state_capture",
                "restart_or_reload_proof",
                "no_fixture_used_for_acceptance",
            ],
            command=None,
            brief=(
                "The Foundry consumes the exported delta; it never becomes SaveGame authority. "
                "The committed resolved_demo delta is only a fixture and cannot satisfy this gate."
            ),
        )
    )

    tasks.append(
        _task(
            "accept_world_zero",
            "I_ACCEPT",
            "echo_plus_owner",
            ["persistence_roundtrip"],
            "evidence-only",
            "Every required proof named by the genome has independent evidence; no producing agent self-certifies.",
            list(genome["acceptance"]["required_proofs"]),
            command=None,
            brief="Independent acceptance only. CURRENT_STATE may change only after real proof.",
        )
    )

    return {
        "schema": MISSION_SCHEMA,
        "mission_id": mission_id,
        "world_id": genome["world_id"],
        "genome_hash": genome_hash,
        "delta_hash": delta_hash,
        "delta_source_authority": delta["source_authority"],
        "delta_non_authoritative_fixture": delta["non_authoritative_fixture"],
        "authority": {
            "owner_intent": "human",
            "mission_dispatch": "hermes",
            "bounded_judgment": "jev",
            "world_authoring": "existing World Compiler / PCG owners",
            "dcc_forge": "Hython offline only",
            "touchdesigner": "presentation-only visual instrument",
            "runtime_truth": "Unreal gameplay/save owners",
            "acceptance": "Echo + independent owner evidence",
            "forbidden": [
                "second World Compiler",
                "second save authority",
                "Jev editor mutation",
                "Hermes editor mutation",
                "runtime Houdini authority",
                "second OSC semantic bridge",
                "second MPC/audio writer",
                "second beauty-feed sender (UE_Beauty is the single name)",
            ],
        },
        "world": {
            "seed": genome["seed"],
            "level_path": genome["level_path"],
            "identity": genome["identity"],
            "spatial": genome["spatial"],
            "content": genome["content"],
        },
        "delta": {
            "revision": delta["revision"],
            "changes": delta["changes"],
        },
        "tasks": tasks,
    }


def validate_mission(mission: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if mission.get("schema") != MISSION_SCHEMA:
        errors.append(f"schema must be {MISSION_SCHEMA!r}")
    tasks = mission.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append("tasks must be a non-empty array")
        return errors

    ids = [t.get("id") for t in tasks if isinstance(t, dict)]
    if len(ids) != len(set(ids)):
        errors.append("task ids must be unique")
    known = set(ids)
    for idx, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(f"tasks[{idx}] must be an object")
            continue
        deps = task.get("depends_on")
        if not isinstance(deps, list):
            errors.append(f"tasks[{idx}].depends_on must be an array")
            continue
        unknown = [d for d in deps if d not in known]
        if unknown:
            errors.append(f"task {task.get('id')!r} has unknown dependencies {unknown}")
        if task.get("owner") in {"jev", "hermes"} and task.get("mutation_surface") != "none":
            errors.append(f"{task.get('owner')} task {task.get('id')} must not own mutation")
    return errors


def default_output_path(mission: dict[str, Any]) -> Path:
    return (
        ROOT
        / "Saved"
        / "UniverseFoundry"
        / mission["world_id"]
        / mission["mission_id"]
        / "mission.json"
    )


def _print_errors(errors: list[str]) -> int:
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("OK")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    genome = _load(Path(args.genome))
    delta = _load(Path(args.delta))
    errors = validate_genome(genome) + validate_delta(delta, genome.get("world_id"))
    if errors:
        return _print_errors(errors)
    mission = build_mission(genome, delta)
    errors = validate_mission(mission)
    if errors:
        return _print_errors(errors)
    print(f"OK world={genome['world_id']} genome={content_hash(genome)} delta={content_hash(delta)}")
    return 0


def cmd_compile(args: argparse.Namespace) -> int:
    genome = _load(Path(args.genome))
    delta = _load(Path(args.delta))
    mission = build_mission(genome, delta)
    errors = validate_mission(mission)
    if errors:
        return _print_errors(errors)

    out = Path(args.out) if args.out else default_output_path(mission)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(mission, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(out)
    print(f"mission_id={mission['mission_id']}")
    print(f"tasks={len(mission['tasks'])}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    mission = _load(Path(args.mission))
    errors = validate_mission(mission)
    if errors:
        return _print_errors(errors)
    print(f"{mission['mission_id']}  world={mission['world_id']}")
    for task in mission["tasks"]:
        deps = ",".join(task["depends_on"]) or "-"
        print(
            f"{task['phase']:16} {task['id']:34} owner={task['owner']:24} deps={deps}"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command_name", required=True)

    p_validate = sub.add_parser("validate")
    p_validate.add_argument("--genome", required=True)
    p_validate.add_argument("--delta", required=True)
    p_validate.set_defaults(func=cmd_validate)

    p_compile = sub.add_parser("compile")
    p_compile.add_argument("--genome", required=True)
    p_compile.add_argument("--delta", required=True)
    p_compile.add_argument("--out")
    p_compile.set_defaults(func=cmd_compile)

    p_show = sub.add_parser("show")
    p_show.add_argument("--mission", required=True)
    p_show.set_defaults(func=cmd_show)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except FoundryError as exc:
        print(f"ERROR: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
