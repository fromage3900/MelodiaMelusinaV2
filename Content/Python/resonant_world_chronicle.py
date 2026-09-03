"""Project a long-lived Resonant World history without becoming a save system.

The generator can recreate a chunk and the score can recreate a phrase, but a
creative world also needs memory: discovered movements, completed phrases,
style voicings, and sparse player-built note edits.  This module turns an
append-only event stream into a deterministic projection of that memory.

It is deliberately a read model.  The canonical narrative/save subsystem
owns storage and transaction boundaries; this module validates and projects
events but never writes a save, applies Unreal state, grants a capability, or
publishes a capture.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from resonant_world_asset_constellation import (
    build_asset_constellation,
    validate_asset_constellation,
)
from resonant_world_generator import (
    GENERATOR_VERSION,
    ResonantEdit,
    WORLD_MOVEMENT_LIBRARY,
    WorldConfig,
)
from resonant_world_score import build_resonant_score, validate_resonant_score


CHRONICLE_VERSION = "resonant_world_chronicle_v1"
CHRONICLE_FORMAT = "melodia_resonant_world_chronicle"
EVENT_TYPES = (
    "world_opened",
    "movement_attuned",
    "discovery",
    "score_completed",
    "style_voicing",
    "voxel_edit",
    "voxel_remove",
)
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()[:16]


def _normalise_chunk(value: Any) -> list[int] | None:
    if value is None:
        return None
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)) or len(value) != 2:
        raise ValueError("event chunk must be [x, y]")
    return [int(value[0]), int(value[1])]


def _normalise_event(raw: Mapping[str, Any], index: int) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise ValueError(f"event {index} must be an object")
    sequence = int(raw.get("sequence", index))
    event_type = str(raw.get("event_type", raw.get("type", "")))
    if event_type not in EVENT_TYPES:
        raise ValueError(f"event {index} has unknown event_type: {event_type}")
    payload = dict(raw.get("payload", {}))
    intent_id = str(raw.get("intent_id", payload.get("intent_id", event_type)))
    chunk = _normalise_chunk(raw.get("chunk", payload.get("chunk")))
    source = dict(raw.get("source", {}))
    identity = {
        "sequence": sequence,
        "event_type": event_type,
        "intent_id": intent_id,
        "chunk": chunk,
        "payload": payload,
        "source": source,
    }
    event_id = str(raw.get("event_id") or f"chronicle_event_{_digest(identity)}")
    return {
        "event_id": event_id,
        "sequence": sequence,
        "event_type": event_type,
        "intent_id": intent_id,
        "chunk": chunk,
        "payload": payload,
        "source": source,
    }


def _asset_provenance(constellation: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for role, refs in constellation.get("bindings", {}).items():
        result[str(role)] = [
            {
                "reference": item.get("reference"),
                "source": item.get("source"),
                "unreal_path": item.get("unreal_path"),
                "disk_path": item.get("disk_path"),
                "runtime_ready": bool(item.get("runtime_ready")),
                "evidence": list(item.get("evidence", [])),
            }
            for item in refs
            if isinstance(item, Mapping)
        ]
    return result


def _edit_from_event(event: Mapping[str, Any]) -> ResonantEdit | None:
    if event.get("event_type") not in {"voxel_edit", "voxel_remove"}:
        return None
    payload = dict(event.get("payload", {}))
    chunk = event.get("chunk") or payload.get("chunk")
    cell = payload.get("cell")
    if not isinstance(chunk, Sequence) or not isinstance(cell, Sequence) or len(chunk) != 2 or len(cell) != 3:
        return None
    material_id = "air" if event.get("event_type") == "voxel_remove" else str(payload.get("material_id", "note_block"))
    return ResonantEdit(
        int(chunk[0]),
        int(chunk[1]),
        int(cell[0]),
        int(cell[1]),
        int(cell[2]),
        material_id,
        int(payload.get("pitch_class", 0)) % 12,
        str(payload.get("timbre", "silence" if material_id == "air" else "harp")),
        str(event.get("intent_id", payload.get("intent_id", event.get("event_id")))),
    )


def _project_events(events: Sequence[Mapping[str, Any]], base_movement_id: str, base_score_id: str) -> dict[str, Any]:
    ordered = sorted(events, key=lambda item: int(item.get("sequence", 0)))
    attuned_movement_id = base_movement_id
    discovered: set[str] = set()
    visited_chunks: set[tuple[int, int]] = set()
    completed_scores: list[str] = []
    styles: dict[str, dict[str, Any]] = {}
    edits: dict[str, ResonantEdit] = {}
    for event in ordered:
        chunk = event.get("chunk")
        if isinstance(chunk, Sequence) and len(chunk) == 2:
            visited_chunks.add((int(chunk[0]), int(chunk[1])))
        event_type = event.get("event_type")
        payload = dict(event.get("payload", {}))
        if event_type == "movement_attuned":
            movement_id = str(payload.get("movement_id", ""))
            if movement_id in WORLD_MOVEMENT_LIBRARY:
                attuned_movement_id = movement_id
                discovered.add(movement_id)
        elif event_type == "discovery":
            movement_id = str(payload.get("movement_id", ""))
            if movement_id in WORLD_MOVEMENT_LIBRARY:
                discovered.add(movement_id)
        elif event_type == "score_completed":
            score_id = str(payload.get("score_id") or event.get("source", {}).get("score_id") or base_score_id)
            if score_id and score_id not in completed_scores:
                completed_scores.append(score_id)
        elif event_type == "style_voicing":
            key = _canonical({"chunk": chunk, "archetype_id": payload.get("archetype_id", "Melusina")})
            styles[key] = {
                "event_id": event.get("event_id"),
                "sequence": int(event.get("sequence", 0)),
                "chunk": list(chunk) if isinstance(chunk, Sequence) else None,
                "archetype_id": payload.get("archetype_id", "Melusina"),
                "movement_id": payload.get("movement_id", attuned_movement_id),
                "style_axes": list(payload.get("style_axes", [])),
                "source": dict(event.get("source", {})),
            }
        else:
            edit = _edit_from_event(event)
            if edit:
                edits[edit.cell_id] = edit
    if not discovered:
        discovered.add(base_movement_id)
    return {
        "attuned_movement_id": attuned_movement_id,
        "discovered_movement_ids": sorted(discovered),
        "visited_chunks": [[x, y] for x, y in sorted(visited_chunks)],
        "completed_score_ids": completed_scores,
        "style_voicings": sorted(styles.values(), key=lambda item: (item["sequence"], item["event_id"])),
        "voxel_edits": [edit.to_dict() for _, edit in sorted(edits.items())],
        "motif_memory": {
            "base_score_id": base_score_id,
            "completed_phrase_count": len(completed_scores),
            "last_event_id": ordered[-1].get("event_id") if ordered else None,
            "memory_digest": _digest({"scores": completed_scores, "styles": styles, "edits": sorted(edits)}),
        },
    }


def validate_chronicle(chronicle: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if chronicle.get("format") != CHRONICLE_FORMAT:
        errors.append("unexpected chronicle format")
    if chronicle.get("chronicle_version") != CHRONICLE_VERSION:
        errors.append("unregistered chronicle version")
    world = chronicle.get("world", {})
    if world.get("movement_id") not in WORLD_MOVEMENT_LIBRARY:
        errors.append("chronicle base movement is not authored")
    events = list(chronicle.get("events", []))
    sequences = [int(event.get("sequence", -1)) for event in events]
    if sequences != sorted(sequences) or len(set(sequences)) != len(sequences):
        errors.append("chronicle event sequences must be unique and ascending")
    event_ids = [str(event.get("event_id", "")) for event in events]
    if not all(event_ids) or len(set(event_ids)) != len(event_ids):
        errors.append("chronicle event IDs must be unique and non-empty")
    for event in events:
        if event.get("event_type") not in EVENT_TYPES:
            errors.append(f"unknown chronicle event type: {event.get('event_type')}")
        if event.get("event_type") in {"voxel_edit", "voxel_remove"} and _edit_from_event(event) is None:
            errors.append(f"voxel event lacks a valid chunk/cell: {event.get('event_id')}")
    projection = chronicle.get("projection", {})
    if projection.get("attuned_movement_id") not in WORLD_MOVEMENT_LIBRARY:
        errors.append("projected attuned movement is not authored")
    boundary = chronicle.get("runtime_boundary", {})
    for key in ("read_model_only", "does_not_write_save", "does_not_apply_unreal", "does_not_grant_capability"):
        if boundary.get(key) is not True:
            errors.append(f"runtime boundary missing {key}")
    if chronicle.get("materialization", {}).get("writes_project_state") is not False:
        errors.append("chronicle crossed the materialization boundary")
    return errors


def build_chronicle(
    world_seed: int = 3900,
    *,
    movement_id: str | None = None,
    chunk_x: int = 0,
    chunk_y: int = 0,
    events: Sequence[Mapping[str, Any]] = (),
    project_root: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(project_root).resolve() if project_root else PROJECT_ROOT
    config = WorldConfig.from_seed(world_seed)
    selected_movement_id = str(movement_id or config.movement_id)
    if selected_movement_id not in WORLD_MOVEMENT_LIBRARY:
        raise ValueError(f"unknown movement id: {selected_movement_id}")
    normalised_events = [_normalise_event(event, index) for index, event in enumerate(events)]
    score = build_resonant_score(
        world_seed,
        movement_id=selected_movement_id,
        chunk_x=chunk_x,
        chunk_y=chunk_y,
        project_root=root,
    )
    constellation = build_asset_constellation(
        root,
        world_seed,
        movement_id=selected_movement_id,
        chunk_x=chunk_x,
        chunk_y=chunk_y,
    )
    score_errors = validate_resonant_score(score)
    constellation_errors = validate_asset_constellation(constellation)
    chronicle_identity = {
        "version": CHRONICLE_VERSION,
        "world_seed": int(world_seed),
        "movement_id": selected_movement_id,
        "chunk": [int(chunk_x), int(chunk_y)],
        "events": normalised_events,
    }
    chronicle_id = _digest(chronicle_identity)
    projection = _project_events(normalised_events, selected_movement_id, str(score.get("score_id")))
    rank_preview = constellation.get("quantum_setup", {}).get("rank_preview") or {}
    result = {
        "format": CHRONICLE_FORMAT,
        "schema_version": 1,
        "chronicle_version": CHRONICLE_VERSION,
        "chronicle_id": chronicle_id,
        "generator_version": GENERATOR_VERSION,
        "world": {
            **config.to_dict(),
            "movement_id": selected_movement_id,
            "chunk": [int(chunk_x), int(chunk_y)],
        },
        "source_provenance": {
            "score_id": score.get("score_id"),
            "constellation_id": constellation.get("constellation_id"),
            "score_validation_errors": score_errors,
            "constellation_validation_errors": constellation_errors,
            "asset_bindings": _asset_provenance(constellation),
            "quantum": {
                "winner_movement_id": rank_preview.get("winner_movement_id"),
                "classical_baseline_winner_id": rank_preview.get("classical_baseline_winner_id"),
                "backend": rank_preview.get("backend"),
                "backend_requested": rank_preview.get("backend_requested"),
                "trace_id": rank_preview.get("trace_id"),
                "provenance_embedded_in_trace": rank_preview.get("provenance", {}).get("source_evidence_embedded_in_trace", False),
            },
        },
        "events": normalised_events,
        "projection": projection,
        "persistence": {
            "storage_owner": "UMelodiaNarrativeSubsystem / canonical save contract",
            "writes_save": False,
            "replay_key": chronicle_id,
            "model": "append_only_events_to_deterministic_projection",
            "conflict_policy": "last_write_wins_per_cell_id_for_sparse_voxel_edits",
        },
        "runtime_boundary": {
            "read_model_only": True,
            "does_not_write_save": True,
            "does_not_apply_unreal": True,
            "does_not_spawn_actors": True,
            "does_not_grant_capability": True,
            "does_not_grant_currency": True,
            "does_not_drive_traversal": True,
        },
        "materialization": {"performed": False, "writes_project_state": False},
    }
    result["validation_errors"] = validate_chronicle(result)
    result["ok"] = not result["validation_errors"]
    return result


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=3900)
    parser.add_argument("--movement", default="petal_cantata")
    parser.add_argument("--chunk-x", type=int, default=0)
    parser.add_argument("--chunk-y", type=int, default=0)
    parser.add_argument("--events", type=Path, help="JSON array of append-only chronicle events")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    events = []
    if args.events:
        loaded = json.loads(args.events.read_text(encoding="utf-8"))
        if not isinstance(loaded, list):
            raise ValueError("--events must contain a JSON array")
        events = loaded
    result = build_chronicle(
        args.seed,
        movement_id=args.movement,
        chunk_x=args.chunk_x,
        chunk_y=args.chunk_y,
        events=events,
    )
    encoded = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
