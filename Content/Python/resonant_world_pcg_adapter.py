"""Adapt Resonant World manifests into the existing scale-world PCG owner.

This module is the first concrete bridge from the new musical world grammar to
the project's established PCG/World Partition pipeline.  It deliberately
does not spawn actors, save maps, or create a second PCG authority.  Instead it
decorates the existing reusable graph/profile and static-spec contracts with
Resonant movement data that an editor lane can consume.

The output is suitable for a proof-map setup script or a later native adapter:

    python Content/Python/resonant_world_pcg_adapter.py \
        --seed 3900 --radius 1 \
        --atlas Saved/Audit/resonant_world_asset_atlas.json \
        --output Saved/Audit/resonant_world_pcg_plan_3900.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

import pcg_scale_world_pipeline as scale
import pcg_visual_chunk_builder as chunk_builder
from resonant_world_asset_atlas import ATLAS_VERSION
from resonant_world_generator import (
    GENERATOR_VERSION as RESONANT_GENERATOR_VERSION,
    WORLD_MOVEMENT_LIBRARY,
    build_world_manifest,
)


ADAPTER_VERSION = "resonant_world_pcg_adapter_v1"
PROOF_LEVEL = scale.SCALE_WORLD_PROOF_LEVEL


def _visual_slot_for_landmark(landmark_id: str | None) -> str | None:
    """Return an existing visual graph slot for a Resonant landmark.

    MotifShrine intentionally reuses the authored cathedral graph until it
    has a dedicated PCG graph.  The original landmark id remains in the
    metadata, so this fallback cannot be mistaken for a new authored asset.
    """
    if not landmark_id:
        return None
    if landmark_id == "MotifShrine":
        return "ResonanceCathedral"
    return landmark_id if landmark_id in scale.VISUAL_GRAPH_BINDINGS else None


def _movement_binding(resonant_chunk: Mapping[str, Any]) -> dict[str, Any]:
    movement_id = str(resonant_chunk["movement_id"])
    movement = WORLD_MOVEMENT_LIBRARY[movement_id]
    region = dict(resonant_chunk["region"])
    return {
        "movement_id": movement_id,
        "movement_display_name": movement.display_name,
        "world_verb": movement.world_verb,
        "resonant_form_id": movement.resonant_form_id,
        "style_axes": list(movement.style_axes),
        "mode_affinities": list(movement.mode_affinities),
        "region_id": str(region["region_id"]),
        "degree_name": str(region["degree_name"]),
        "pitch_class": int(region["pitch_class"]),
        "asset_queries": {
            "pcg": list(movement.pcg_asset_fragments),
            "musical": list(movement.musical_asset_fragments),
            "vfx": list(movement.vfx_systems),
            "water": list(movement.water_profiles),
            "outfit_archetypes": list(movement.outfit_archetypes),
        },
        "npc_zones": list(movement.npc_zones),
        "quantum_objective": list(movement.quantum_objective),
        "motif_id": str(resonant_chunk["motif_id"]),
    }


def hero_graph_specs_from_resonant_plan(
    resonant_plan: Mapping[str, Any],
) -> list[tuple[str, str, tuple[float, float, float], dict[str, Any]]]:
    """Return proof-lane tuples without importing Unreal or the editor setup script."""
    specs: list[tuple[str, str, tuple[float, float, float], dict[str, Any]]] = []
    for source in resonant_plan.get("hero_volume_specs", []):
        label = str(source["label"]).replace("PCG Chunk ", "PCG ScaleWorld ", 1)
        graph = str(source["graph"])
        origin = tuple(float(value) for value in source["origin_cm"])
        specs.append((label, graph, origin, dict(source)))
    return specs


def _decorate_spec(spec: dict[str, Any], resonant_chunk: Mapping[str, Any]) -> dict[str, Any]:
    movement = _movement_binding(resonant_chunk)
    decorated = dict(spec)
    decorated["resonant_world"] = movement
    decorated["tags"] = [
        "ResonantWorld",
        f"ResonantMovement_{movement['movement_id']}",
        f"ResonantVerb_{movement['world_verb']}",
    ]
    identity = dict(decorated.get("identity_namespace", {}))
    identity["resonant_generator_version"] = RESONANT_GENERATOR_VERSION
    identity["movement_id"] = movement["movement_id"]
    identity["motif_id"] = movement["motif_id"]
    decorated["identity_namespace"] = identity
    return decorated


def _load_atlas(atlas_path: str | Path | None) -> dict[str, Any] | None:
    if not atlas_path:
        return None
    path = Path(atlas_path)
    if not path.exists():
        raise FileNotFoundError(f"asset atlas not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("format") != "melodia_resonant_world_asset_atlas":
        raise ValueError("asset atlas format is not melodia_resonant_world_asset_atlas")
    return data


def _load_phrase(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"phrase manifest not found: {target}")
    data = json.loads(target.read_text(encoding="utf-8"))
    if data.get("format") != "melodia_resonant_phrase_manifest":
        raise ValueError("phrase manifest format is not melodia_resonant_phrase_manifest")
    if not data.get("ok", True):
        raise ValueError(f"phrase manifest is invalid: {data.get('validation_errors', [])}")
    return data


def _load_wardrobe(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"wardrobe voicing preview not found: {target}")
    data = json.loads(target.read_text(encoding="utf-8"))
    if data.get("format") != "melodia_resonant_world_wardrobe_voicing":
        raise ValueError("wardrobe preview format is not melodia_resonant_world_wardrobe_voicing")
    if not data.get("ok", True):
        raise ValueError(f"wardrobe preview is invalid: {data.get('validation_errors', [])}")
    return data


def _load_magic_passage(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"magic passage not found: {target}")
    data = json.loads(target.read_text(encoding="utf-8"))
    if data.get("format") != "melodia_resonant_world_magic_passage":
        raise ValueError("magic passage format is not melodia_resonant_world_magic_passage")
    if not data.get("ok", True):
        raise ValueError(f"magic passage is invalid: {data.get('validation_errors', [])}")
    return data


def validate_resonant_pcg_plan(plan: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if plan.get("format") != "melodia_resonant_pcg_world_plan":
        errors.append("format is not melodia_resonant_pcg_world_plan")
    if plan.get("adapter_version") != ADAPTER_VERSION:
        errors.append("adapter version is not registered")
    if int(plan.get("chunk_count", 0)) != len(plan.get("chunks", [])):
        errors.append("chunk_count does not match chunks")
    for chunk in plan.get("chunks", []):
        movement_id = chunk.get("movement_id")
        if movement_id not in WORLD_MOVEMENT_LIBRARY:
            errors.append(f"chunk {chunk.get('chunk_x')},{chunk.get('chunk_y')} has unknown movement")
        if not chunk.get("resonant_world"):
            errors.append(f"chunk {chunk.get('chunk_x')},{chunk.get('chunk_y')} is missing resonant metadata")
    for key in ("hero_volume_specs", "static_specs"):
        for spec in plan.get(key, []):
            if not spec.get("resonant_world"):
                errors.append(f"{key} spec is missing resonant metadata")
            if key == "hero_volume_specs" and not str(spec.get("graph", "")).startswith("/Game/"):
                errors.append("hero volume graph is not an explicit /Game/ asset path")
    atlas = plan.get("asset_atlas")
    if atlas:
        if atlas.get("atlas_version") != ATLAS_VERSION:
            errors.append("embedded asset atlas version mismatch")
        if not atlas.get("ok"):
            errors.append("embedded asset atlas is not valid")
    phrase = plan.get("phrase_source")
    if phrase:
        if phrase.get("format") != "melodia_resonant_phrase_manifest":
            errors.append("embedded phrase source has an unexpected format")
        if int(phrase.get("note_count", 0)) <= 0:
            errors.append("embedded phrase source has no notes")
    wardrobe = plan.get("wardrobe_voicing")
    if wardrobe:
        if wardrobe.get("format") != "melodia_resonant_world_wardrobe_voicing":
            errors.append("embedded wardrobe source has an unexpected format")
        if wardrobe.get("world_seed") != plan.get("world_seed"):
            errors.append("embedded wardrobe source seed does not match PCG plan")
        if wardrobe.get("movement_id") not in WORLD_MOVEMENT_LIBRARY:
            errors.append("embedded wardrobe source movement is not authored")
        if wardrobe.get("does_not_grant_capability") is not True:
            errors.append("embedded wardrobe source must remain non-granting")
    passage = plan.get("magic_passage")
    if passage:
        if passage.get("format") != "melodia_resonant_world_magic_passage":
            errors.append("embedded magic passage has an unexpected format")
        if passage.get("world_seed") != plan.get("world_seed"):
            errors.append("embedded magic passage seed does not match PCG plan")
        if passage.get("movement_id") not in WORLD_MOVEMENT_LIBRARY:
            errors.append("embedded magic passage movement is not authored")
        if int(passage.get("stage_count", 0)) != 4:
            errors.append("embedded magic passage must have four stages")
        if passage.get("does_not_write_save") is not True:
            errors.append("embedded magic passage must not write save state")
    return errors


def build_resonant_pcg_plan(
    world_seed: int = 3900,
    radius: int = 1,
    *,
    atlas: Mapping[str, Any] | None = None,
    phrase: Mapping[str, Any] | None = None,
    wardrobe: Mapping[str, Any] | None = None,
    magic_passage: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    resonant_manifest = build_world_manifest(world_seed, radius=radius)
    scale_manifests = scale.build_chunk_grid(world_seed, radius=radius)
    resonant_by_coord = {
        (int(chunk["chunk_x"]), int(chunk["chunk_y"])): chunk
        for chunk in resonant_manifest["chunks"]
    }

    chunks: list[dict[str, Any]] = []
    hero_specs: list[dict[str, Any]] = []
    static_specs: list[dict[str, Any]] = []
    for scale_manifest in scale_manifests:
        coord = (scale_manifest.chunk_x, scale_manifest.chunk_y)
        resonant_chunk = resonant_by_coord[coord]
        landmark_id = resonant_chunk.get("landmark_id")
        visual_slot = _visual_slot_for_landmark(landmark_id)
        # Reuse the established PCG graph/profile and scale-world ownership.
        # The Resonant movement is metadata and input selection, not a second
        # actor or graph authority.
        graph_manifest = scale.make_chunk_manifest(
            world_seed,
            scale_manifest.chunk_x,
            scale_manifest.chunk_y,
            biome_id=f"resonant_{resonant_chunk['movement_id']}",
            hero_slot_assignments=(visual_slot,) if visual_slot else (),
        )
        movement = _movement_binding(resonant_chunk)
        chunk = graph_manifest.to_dict()
        chunk.update({
            "resonant_generator_version": RESONANT_GENERATOR_VERSION,
            "movement_id": movement["movement_id"],
            "movement": movement,
            "landmark_id": landmark_id,
            "visual_graph_slot": visual_slot,
            "resonant_world": resonant_chunk,
        })
        chunk["graph_profile_bindings"] = {
            slot: scale.reusable_graph_binding(slot)
            for slot in graph_manifest.hero_slot_assignments
        }
        chunks.append(chunk)

        hero_specs.extend(
            _decorate_spec(spec, resonant_chunk)
            for spec in chunk_builder.chunk_volume_specs(graph_manifest)
        )
        static_specs.extend(
            _decorate_spec(spec, resonant_chunk)
            for spec in chunk_builder.chunk_static_specs(graph_manifest)
        )

    plan: dict[str, Any] = {
        "format": "melodia_resonant_pcg_world_plan",
        "adapter_version": ADAPTER_VERSION,
        "world_seed": int(world_seed),
        "radius": max(0, int(radius)),
        "proof_level": PROOF_LEVEL,
        "source_manifests": {
            "resonant": "melodia_resonant_world_manifest",
            "scale_world": "musical_pcg_scale_v1",
        },
        "generator_versions": {
            "resonant": RESONANT_GENERATOR_VERSION,
            "scale_world": scale.GENERATOR_VERSION,
        },
        "world": resonant_manifest["world"],
        "graph_reuse": True,
        "pcg_owner": "existing pcg_scale_world_pipeline + pcg_visual_chunk_builder",
        "production_maps_touched": False,
        "chunks": chunks,
        "chunk_count": len(chunks),
        "hero_volume_specs": hero_specs,
        "hero_volume_count": len(hero_specs),
        "static_specs": static_specs,
        "static_spec_count": len(static_specs),
    }
    if atlas is not None:
        plan["asset_atlas"] = {
            "atlas_version": atlas.get("atlas_version"),
            "format": atlas.get("format"),
            "ok": atlas.get("ok"),
            "scanned_file_count": atlas.get("scan", {}).get("scanned_file_count"),
        }
    if phrase is not None:
        plan["phrase_source"] = {
            "format": phrase.get("format"),
            "phrase_generator_version": phrase.get("phrase_generator_version"),
            "phrase_id": phrase.get("source", {}).get("phrase_id"),
            "midi_file_name": phrase.get("source", {}).get("midi_file_name"),
            "note_count": phrase.get("note_count"),
            "voxel_count": phrase.get("voxel_count"),
            "movement_id": phrase.get("movement", {}).get("movement_id"),
        }
    if wardrobe is not None:
        style = wardrobe.get("layers", {}).get("style", {})
        cosmetic = wardrobe.get("layers", {}).get("cosmetic", {})
        form = wardrobe.get("layers", {}).get("form", {})
        boundary = wardrobe.get("runtime_boundary", {})
        plan["wardrobe_voicing"] = {
            "format": wardrobe.get("format"),
            "voicing_version": wardrobe.get("voicing_version"),
            "request_id": wardrobe.get("request_id"),
            "world_seed": wardrobe.get("world", {}).get("world_seed"),
            "movement_id": wardrobe.get("world", {}).get("movement_id"),
            "world_verb": wardrobe.get("world_response", {}).get("verb"),
            "catalog_asset": cosmetic.get("catalog_asset"),
            "cosmetic_record_count": len(cosmetic.get("records", [])),
            "archetype_id": style.get("archetype_id"),
            "active_style_axes": list(style.get("voicing", {}).get("active_axes", [])),
            "requested_resonant_form_id": form.get("requested_resonant_form_id"),
            "does_not_grant_capability": boundary.get("does_not_grant_capability"),
            "does_not_write_save": boundary.get("does_not_write_save"),
        }
    if magic_passage is not None:
        boundary = magic_passage.get("runtime_boundary", {})
        plan["magic_passage"] = {
            "format": magic_passage.get("format"),
            "passage_version": magic_passage.get("passage_version"),
            "passage_id": magic_passage.get("passage_id"),
            "world_seed": magic_passage.get("world", {}).get("world_seed"),
            "movement_id": magic_passage.get("world", {}).get("movement_id"),
            "world_verb": magic_passage.get("premise", {}).get("world_verb"),
            "stage_count": len(magic_passage.get("response_choreography", [])),
            "scene_preview_only": magic_passage.get("scene_preview", {}).get("photo_spot", {}).get("scene_preview_only"),
            "quantum_selection_stage": magic_passage.get("quantum_setup", {}).get("selection_stage"),
            "does_not_grant_capability": boundary.get("does_not_grant_capability"),
            "does_not_write_save": boundary.get("does_not_write_save"),
        }
    plan["validation_errors"] = validate_resonant_pcg_plan(plan)
    plan["ok"] = not plan["validation_errors"] and bool(resonant_manifest.get("ok"))
    return plan


def write_resonant_pcg_plan(
    path: str | Path,
    world_seed: int = 3900,
    radius: int = 1,
    *,
    atlas_path: str | Path | None = None,
    phrase_path: str | Path | None = None,
    wardrobe_path: str | Path | None = None,
    magic_passage_path: str | Path | None = None,
) -> dict[str, Any]:
    atlas = _load_atlas(atlas_path)
    phrase = _load_phrase(phrase_path)
    wardrobe = _load_wardrobe(wardrobe_path)
    magic_passage = _load_magic_passage(magic_passage_path)
    plan = build_resonant_pcg_plan(
        world_seed,
        radius,
        atlas=atlas,
        phrase=phrase,
        wardrobe=wardrobe,
        magic_passage=magic_passage,
    )
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    return plan


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=3900)
    parser.add_argument("--radius", type=int, default=1)
    parser.add_argument("--atlas", type=Path)
    parser.add_argument("--phrase", type=Path)
    parser.add_argument("--wardrobe", type=Path)
    parser.add_argument("--magic-passage", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    plan = write_resonant_pcg_plan(
        args.output,
        args.seed,
        args.radius,
        atlas_path=args.atlas,
        phrase_path=args.phrase,
        wardrobe_path=args.wardrobe,
        magic_passage_path=args.magic_passage,
    )
    print(json.dumps({
        "ok": plan["ok"],
        "output": str(args.output),
        "chunks": plan["chunk_count"],
        "hero_volume_specs": plan["hero_volume_count"],
        "static_specs": plan["static_spec_count"],
        "errors": plan["validation_errors"],
    }, indent=2))
    return 0 if plan["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
