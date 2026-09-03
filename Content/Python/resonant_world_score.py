"""Compose a persistent, replayable musical score for one world chunk.

The Resonant World generator can already produce deterministic columns and
the asset constellation can resolve existing project references.  This module
joins them into the player-facing unit of authored procedural content: a
short phrase with a call, a response, a route, a landmark gesture, and a
presentation voicing.

It is intentionally a read model.  The score is suitable for a future Unreal
PCG/materialization adapter, but it does not load assets, spawn actors, equip
wardrobe, grant traversal, award currency, or write a save.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from resonant_world_asset_constellation import (
    CONSTELLATION_VERSION,
    build_asset_constellation,
    validate_asset_constellation,
)
from resonant_world_generator import (
    GENERATOR_VERSION,
    GRID_SIZE,
    NOTE_NAMES,
    WORLD_MOVEMENT_LIBRARY,
    WorldConfig,
    edge_anchor,
    stable_int,
    surface_height,
)


SCORE_VERSION = "resonant_world_score_v1"
PHRASE_BEATS = 16
STAGE_IDS = ("invocation", "unfolding", "threshold", "release")
WORLD_ACTIONS = {
    "bloom": ("germinate", "open_flora", "draw_petal_route", "leave_a_bloom_rest"),
    "weave": ("pin_constellation", "connect_star_nodes", "reveal_hidden_thread", "settle_the_loom"),
    "conduct": ("gather_water", "conduct_surface_pulse", "expose_submerged_note", "return_the_tide"),
    "compose": ("place_tone_voxel", "align_instrument", "score_phrase", "commit_a_cadence_request"),
    "drift": ("raise_wind", "draw_ribbon_lane", "mirror_the_route", "land_on_the_downbeat"),
    "resolve": ("surface_dissonance", "hold_tension", "offer_a_resolving_degree", "resolve_or_rest"),
}


MOTIF_GRAMMARS: dict[str, dict[str, Any]] = {
    "bloom": {
        "name": "petal_fan",
        "degrees": (0, 2, 4, 2, 1, 3, 5, 4),
        "offsets": (0, 2, 3, 2, 0, -2, -3, -2),
        "gesture": "a flower opens on the return to tonic",
        "material_role": "flora",
        "ornament_role": "ornament",
    },
    "weave": {
        "name": "constellation_hem",
        "degrees": (0, 3, 5, 2, 4, 1, 6, 4),
        "offsets": (-2, -1, 1, 2, 2, 1, -1, -2),
        "gesture": "a sky-thread becomes walkable at the response",
        "material_role": "material",
        "ornament_role": "structure",
    },
    "conduct": {
        "name": "tide_chord",
        "degrees": (0, 2, 4, 6, 4, 2, 1, 0),
        "offsets": (0, 1, 0, -1, -2, -1, 0, 1),
        "gesture": "a surface pulse carries a chord to submerged memory",
        "material_role": "water",
        "ornament_role": "structure",
    },
    "compose": {
        "name": "cadence_stair",
        "degrees": (0, 1, 2, 3, 4, 5, 6, 0),
        "offsets": (0, 0, 1, 1, 2, 2, 3, 3),
        "gesture": "placed tone voxels rise into a readable cadence",
        "material_role": "material",
        "ornament_role": "ornament",
    },
    "drift": {
        "name": "ribbon_mirage",
        "degrees": (0, 4, 2, 5, 3, 6, 4, 1),
        "offsets": (0, 2, 1, -1, -2, -1, 1, 2),
        "gesture": "the wind reveals a route that answers the silhouette",
        "material_role": "flora",
        "ornament_role": "ornament",
    },
    "resolve": {
        "name": "beautiful_dissonance",
        "degrees": (0, 1, 6, 2, 5, 3, 1, 0),
        "offsets": (2, -2, 2, -2, 1, -1, 0, 0),
        "gesture": "an unresolved interval becomes a survivable portal",
        "material_role": "material",
        "ornament_role": "structure",
    },
}


def _ref_for_role(constellation: Mapping[str, Any], role: str, index: int) -> dict[str, Any] | None:
    refs = list(constellation.get("bindings", {}).get(role, []))
    if not refs:
        refs = list(constellation.get("asset_candidates", {}).get(role, []))
    if not refs:
        return None
    return dict(refs[int(index) % len(refs)])


def _route_points(seed: int, chunk_x: int, chunk_y: int, offsets: tuple[int, ...]) -> list[tuple[int, int]]:
    config = WorldConfig.from_seed(seed)
    west = edge_anchor(config, chunk_x, chunk_y, "west")
    east = edge_anchor(config, chunk_x, chunk_y, "east")
    points: list[tuple[int, int]] = []
    for beat in range(PHRASE_BEATS):
        t = beat / float(PHRASE_BEATS - 1)
        x = round(west["local_x"] + ((east["local_x"] - west["local_x"]) * t))
        y = round(west["local_y"] + ((east["local_y"] - west["local_y"]) * t))
        offset = int(offsets[beat % len(offsets)])
        if beat not in {0, PHRASE_BEATS - 1}:
            y += offset
        points.append((max(0, min(GRID_SIZE - 1, x)), max(0, min(GRID_SIZE - 1, y))))
    return points


def _event_id(seed: int, movement_id: str, chunk_x: int, chunk_y: int, beat: int) -> str:
    raw = f"{SCORE_VERSION}|{int(seed)}|{movement_id}|{int(chunk_x)}|{int(chunk_y)}|{int(beat)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def build_resonant_score(
    world_seed: int = 3900,
    *,
    movement_id: str | None = None,
    chunk_x: int = 0,
    chunk_y: int = 0,
    archetype_id: str | None = None,
    project_root: str | Path | None = None,
) -> dict[str, Any]:
    """Build one deterministic phrase, route, and asset voicing."""
    config = WorldConfig.from_seed(world_seed)
    selected_movement_id = movement_id or config.movement_id
    if selected_movement_id not in WORLD_MOVEMENT_LIBRARY:
        raise ValueError(f"unknown movement id: {selected_movement_id}")
    movement = WORLD_MOVEMENT_LIBRARY[selected_movement_id]
    grammar = MOTIF_GRAMMARS[movement.world_verb]
    root = Path(project_root).resolve() if project_root else Path(__file__).resolve().parents[2]
    constellation = build_asset_constellation(
        root,
        world_seed,
        movement_id=selected_movement_id,
        chunk_x=chunk_x,
        chunk_y=chunk_y,
        archetype_id=archetype_id,
    )
    constellation_errors = validate_asset_constellation(constellation)
    route = _route_points(world_seed, chunk_x, chunk_y, tuple(grammar["offsets"]))
    region = constellation.get("world", {})
    base_degree = int(constellation.get("movement", {}).get("mode_affinities", [config.mode_id]).index(config.mode_id)) if config.mode_id in constellation.get("movement", {}).get("mode_affinities", []) else 0
    actions = WORLD_ACTIONS[movement.world_verb]
    events: list[dict[str, Any]] = []
    for beat, (local_x, local_y) in enumerate(route):
        stage_index = min(len(STAGE_IDS) - 1, beat // (PHRASE_BEATS // len(STAGE_IDS)))
        stage_id = STAGE_IDS[stage_index]
        degree = (base_degree + int(grammar["degrees"][beat % len(grammar["degrees"])]) + (stable_int(world_seed, "score-degree", chunk_x, chunk_y, beat) % 2)) % 7
        pitch_class = (config.root_pitch_class + config.mode.intervals[degree]) % 12
        surface_z = surface_height(config, chunk_x, chunk_y, local_x, local_y)
        z_lift = (int(grammar["degrees"][beat % len(grammar["degrees"])]) + stable_int(world_seed, "score-z", chunk_x, chunk_y, beat) % 2) % 3
        z = min(7, surface_z + z_lift)
        phase = "call" if beat < PHRASE_BEATS // 2 else "response"
        music_ref = _ref_for_role(constellation, "music", beat)
        material_ref = _ref_for_role(constellation, str(grammar["material_role"]), beat)
        ornament_ref = _ref_for_role(constellation, str(grammar["ornament_role"]), beat)
        vfx_ref = _ref_for_role(constellation, "vfx", stage_index)
        events.append({
            "event_id": _event_id(world_seed, selected_movement_id, chunk_x, chunk_y, beat),
            "beat": beat,
            "phase": phase,
            "stage_id": stage_id,
            "cell": [local_x, local_y, z],
            "pitch_class": pitch_class,
            "pitch_name": NOTE_NAMES[pitch_class],
            "scale_degree": degree,
            "voice": "melody" if phase == "call" else "answer",
            "energy": 55 + stable_int(world_seed, "score-energy", chunk_x, chunk_y, beat) % 46,
            "world_action": actions[stage_index],
            "gesture": grammar["gesture"],
            "asset_voicing": {
                "music": music_ref,
                "material": material_ref,
                "ornament": ornament_ref,
                "vfx": vfx_ref,
                "wardrobe": _ref_for_role(constellation, "wardrobe", stage_index),
            },
        })

    west = edge_anchor(config, chunk_x, chunk_y, "west")
    east = edge_anchor(config, chunk_x, chunk_y, "east")
    score_id = hashlib.sha256(
        f"{SCORE_VERSION}|{int(world_seed)}|{selected_movement_id}|{int(chunk_x)}|{int(chunk_y)}".encode("utf-8")
    ).hexdigest()[:16]
    return {
        "format": "melodia_resonant_world_score",
        "schema_version": 1,
        "score_version": SCORE_VERSION,
        "score_id": score_id,
        "generator_versions": {
            "world": GENERATOR_VERSION,
            "constellation": CONSTELLATION_VERSION,
        },
        "world": {
            "seed": int(world_seed),
            "chunk": [int(chunk_x), int(chunk_y)],
            "movement_id": selected_movement_id,
            "movement_display_name": movement.display_name,
            "world_verb": movement.world_verb,
            "root_note": config.root_note,
            "mode_id": config.mode_id,
            "bpm": config.bpm,
            "motif_id": config.motif_id,
        },
        "motif": {
            "grammar_id": str(grammar["name"]),
            "gesture": str(grammar["gesture"]),
            "call_beats": list(range(PHRASE_BEATS // 2)),
            "response_beats": list(range(PHRASE_BEATS // 2, PHRASE_BEATS)),
            "response_rule": "the response mirrors the route while changing voicing and degree emphasis",
        },
        "route": {
            "kind": "edge_to_edge_phrase_lane",
            "request_only": True,
            "west": {"signature": west["signature"], "cell": [west["local_x"], west["local_y"]]},
            "east": {"signature": east["signature"], "cell": [east["local_x"], east["local_y"]]},
            "points": [[x, y] for x, y in route],
            "traversal_authority": "UMelodiaTraversalComponent",
        },
        "events": events,
        "stages": [
            {
                "stage_id": stage_id,
                "beat_range": [index * 4, (index + 1) * 4 - 1],
                "event_ids": [event["event_id"] for event in events[index * 4:(index + 1) * 4]],
                "trigger": "music_clock_on_beat",
                "world_action": actions[index],
            }
            for index, stage_id in enumerate(STAGE_IDS)
        ],
        "asset_constellation": {
            "constellation_id": constellation.get("constellation_id"),
            "required_role_coverage": constellation.get("coverage", {}).get("required_role_coverage"),
            "validation_errors": constellation_errors,
            "runtime_ready_reference_count": constellation.get("coverage", {}).get("runtime_ready_reference_count", 0),
        },
        "quantum_setup": constellation.get("quantum_setup", {}),
        "persistence": {
            "replay_key": score_id,
            "persist_before_apply": ["score_id", "constellation_id", "quantum_setup.rank_preview.trace_id"],
            "sparse_edit_model": "persist player edits by event_id/cell_id/intent_id, then regenerate the score",
            "save_authority": "UMelodiaNarrativeSubsystem / canonical save contract",
            "writes_save": False,
        },
        "runtime_boundary": {
            "authoring_or_read_model": True,
            "does_not_load_unreal_assets": True,
            "does_not_spawn_actors": True,
            "does_not_equip": True,
            "does_not_grant_capability": True,
            "does_not_apply_traversal": True,
            "does_not_grant_currency": True,
            "does_not_write_save": True,
            "does_not_select_individual_voxels_with_quantum": True,
        },
    }


def validate_resonant_score(score: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if score.get("format") != "melodia_resonant_world_score":
        errors.append("unexpected score format")
    if score.get("score_version") != SCORE_VERSION:
        errors.append("unexpected score version")
    world = score.get("world", {})
    movement_id = world.get("movement_id")
    if movement_id not in WORLD_MOVEMENT_LIBRARY:
        errors.append("score movement is not authored")
    events = list(score.get("events", []))
    if len(events) != PHRASE_BEATS:
        errors.append(f"score must contain exactly {PHRASE_BEATS} events")
    if len({event.get("event_id") for event in events}) != len(events):
        errors.append("score event ids are not unique")
    if {event.get("phase") for event in events[:PHRASE_BEATS // 2]} != {"call"}:
        errors.append("first half of score is not the call")
    if {event.get("phase") for event in events[PHRASE_BEATS // 2:]} != {"response"}:
        errors.append("second half of score is not the response")
    for event in events:
        cell = event.get("cell", [])
        if len(cell) != 3 or not (0 <= int(cell[0]) < GRID_SIZE and 0 <= int(cell[1]) < GRID_SIZE and 0 <= int(cell[2]) <= 7):
            errors.append(f"event has out-of-range cell: {event.get('event_id')}")
    route = score.get("route", {})
    points = list(route.get("points", []))
    if len(points) != PHRASE_BEATS:
        errors.append("route point count must equal phrase beat count")
    if points and points[0] != route.get("west", {}).get("cell"):
        errors.append("route does not begin at its west seam anchor")
    if points and points[-1] != route.get("east", {}).get("cell"):
        errors.append("route does not end at its east seam anchor")
    if len(score.get("stages", [])) != len(STAGE_IDS):
        errors.append("score must have four beat-driven stages")
    quantum = score.get("quantum_setup", {})
    if len(quantum.get("candidate_movements", [])) != 2:
        errors.append("score quantum setup must contain exactly two movement candidates")
    if quantum.get("quantum_is_selector_not_generator") is not True:
        errors.append("score quantum setup must be selector-not-generator")
    boundary = score.get("runtime_boundary", {})
    for key in ("does_not_apply_traversal", "does_not_write_save", "does_not_select_individual_voxels_with_quantum"):
        if boundary.get(key) is not True:
            errors.append(f"runtime boundary missing {key}")
    return errors


def build_score_portfolio(world_seed: int = 3900, project_root: str | Path | None = None) -> dict[str, Any]:
    scores = [
        build_resonant_score(world_seed, movement_id=movement_id, project_root=project_root)
        for movement_id in WORLD_MOVEMENT_LIBRARY
    ]
    errors = {
        score["world"]["movement_id"]: validate_resonant_score(score)
        for score in scores
    }
    return {
        "format": "melodia_resonant_world_score_portfolio",
        "schema_version": 1,
        "score_version": SCORE_VERSION,
        "world_seed": int(world_seed),
        "score_count": len(scores),
        "scores": scores,
        "validation_errors": {key: value for key, value in errors.items() if value},
        "ok": not any(errors.values()),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=3900)
    parser.add_argument("--movement", default="cadence_cathedral")
    parser.add_argument("--chunk-x", type=int, default=0)
    parser.add_argument("--chunk-y", type=int, default=0)
    parser.add_argument("--archetype")
    parser.add_argument("--all-movements", action="store_true")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = (
        build_score_portfolio(args.seed)
        if args.all_movements
        else build_resonant_score(
            args.seed,
            movement_id=args.movement,
            chunk_x=args.chunk_x,
            chunk_y=args.chunk_y,
            archetype_id=args.archetype,
        )
    )
    if not args.all_movements:
        result["validation_errors"] = validate_resonant_score(result)
        result["ok"] = not result["validation_errors"]
    encoded = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
