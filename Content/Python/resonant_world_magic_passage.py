"""Compile an authored wardrobe/world response into a magical Resonant Passage.

A passage is Melodia's answer to a quest room or a Minecraft redstone build:
not a stat buff, but a short, replayable choreography that lets a movement
change the reading of a place.  It stages PCG dressing, Niagara effects, water,
NPC presence, musical phrase windows, and a scene-preview/photo moment.

The compiler consumes the existing wardrobe voicing preview and asset atlas.
It does not spawn actors, apply traversal, commit narrative state, or write a
save.  The output is an authoring/runtime-read-model handoff for the existing
PCG, music-clock, wardrobe, traversal, narrative, and JRPG authorities.

Usage::

    python Content/Python/resonant_world_magic_passage.py \
        --seed 3900 --movement petal_cantata --archetype SakuraDreamer \
        --atlas Saved/Audit/resonant_world_asset_atlas.json \
        --phrase Saved/Audit/resonant_world_phrase_128bpm.json \
        --output Saved/Audit/resonant_magic_passage_petal_3900.json

    python Content/Python/resonant_world_magic_passage.py \
        --seed 3900 --all-movements --atlas Saved/Audit/resonant_world_asset_atlas.json \
        --output Saved/Audit/resonant_magic_passage_portfolio_3900.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from resonant_world_generator import (
    GRID_SIZE,
    VOXEL_SIZE_CM,
    WORLD_MOVEMENT_LIBRARY,
    WorldConfig,
    stable_float,
    stable_int,
)
from resonant_world_wardrobe_bridge import (
    _phrase_summary,
    build_wardrobe_voicing_preview,
)


PASSAGE_VERSION = "resonant_magic_passage_v1"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CURRENCY_REGISTRY_PATH = PROJECT_ROOT / "specs" / "economy" / "melodia_currency_registry.v1.json"


WORLD_ACTIONS: dict[str, tuple[str, str, str, str]] = {
    "bloom": ("germinate", "open_flora", "draw_petal_route", "leave_a_bloom_rest"),
    "weave": ("pin_constellation", "connect_star_nodes", "reveal_hidden_thread", "settle_the_loom"),
    "conduct": ("gather_water", "conduct_surface_pulse", "expose_submerged_note", "return_the_tide"),
    "compose": ("place_tone_voxel", "align_instrument", "score_phrase", "commit_a_cadence_request"),
    "drift": ("raise_wind", "draw_ribbon_lane", "mirror_the_route", "land_on_the_downbeat"),
    "resolve": ("surface_dissonance", "hold_tension", "offer_a_resolving_degree", "resolve_or_rest"),
}


STAGE_JOBS = ("introduce", "unfold", "turn", "resolve")
STAGE_IDS = ("invocation", "unfolding", "threshold", "release")
STAGE_TRIGGERS = ("on_entry", "on_phrase_motion", "on_answer_or_dissonance", "on_resolution_or_rest")

MOVEMENT_ELEMENTS = {
    "petal_cantata": "Radiant",
    "star_loom": "Arcane",
    "liquid_cathedral": "Tide",
    "cadence_cathedral": "Forte",
    "mirage_gala": "Gale",
    "dissonant_expanse": "Umbral",
}


def _read_json(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"manifest not found: {target}")
    value = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"manifest root is not an object: {target}")
    return value


def _load_atlas(path: Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    data = _read_json(path)
    if data.get("format") != "melodia_resonant_world_asset_atlas":
        raise ValueError("asset atlas format is not melodia_resonant_world_asset_atlas")
    return data


def _load_phrase(path: Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    data = _read_json(path)
    if data.get("format") != "melodia_resonant_phrase_manifest":
        raise ValueError("phrase format is not melodia_resonant_phrase_manifest")
    if not data.get("ok", True):
        raise ValueError(f"phrase manifest is invalid: {data.get('validation_errors', [])}")
    return data


def _load_wardrobe(path: Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    data = _read_json(path)
    if data.get("format") != "melodia_resonant_world_wardrobe_voicing":
        raise ValueError("wardrobe format is not melodia_resonant_world_wardrobe_voicing")
    if not data.get("ok", True):
        raise ValueError(f"wardrobe preview is invalid: {data.get('validation_errors', [])}")
    return data


def _pick(values: Iterable[Any], index: int) -> Any | None:
    values = list(values)
    return values[index % len(values)] if values else None


def _phrase_windows(phrase: Mapping[str, Any] | None, stage_count: int = 4) -> list[dict[str, Any]]:
    if not phrase:
        return [
            {"note_count": 0, "resonant_count": 0, "dissonant_count": 0, "mean_energy": 0.0}
            for _ in range(stage_count)
        ]
    voxels = list(phrase.get("voxels", []))
    if not voxels:
        return [
            {"note_count": 0, "resonant_count": 0, "dissonant_count": 0, "mean_energy": 0.0}
            for _ in range(stage_count)
        ]
    steps = [int(voxel.get("time_step", 0)) for voxel in voxels]
    minimum, maximum = min(steps), max(steps)
    span = max(1, maximum - minimum + 1)
    windows: list[dict[str, Any]] = []
    for stage_index in range(stage_count):
        lower = minimum + (span * stage_index) // stage_count
        upper = minimum + (span * (stage_index + 1)) // stage_count
        selected = [voxel for voxel in voxels if lower <= int(voxel.get("time_step", 0)) < upper]
        if not selected:
            selected = [voxels[min(len(voxels) - 1, stage_index * len(voxels) // stage_count)]]
        energies = [int(voxel.get("energy", 0)) for voxel in selected]
        windows.append({
            "time_step_range": [lower, max(lower, upper - 1)],
            "note_count": len(selected),
            "resonant_count": sum(voxel.get("material_id") == "resonant_note" for voxel in selected),
            "dissonant_count": sum(voxel.get("material_id") == "dissonant_note" for voxel in selected),
            "mean_energy": round(sum(energies) / len(energies), 2),
            "voices": sorted({str(voxel.get("voice", "unknown")) for voxel in selected}),
        })
    return windows


def _effect_toggles(presentation: Mapping[str, Any]) -> list[dict[str, Any]]:
    toggles: list[dict[str, Any]] = []
    for system in presentation.get("vfx_systems", []):
        system_id = str(system.get("system_id"))
        toggles.append({
            "toggle_id": f"fx.{system_id}.visible",
            "label": f"Show {system_id}",
            "default": True,
            "source": "existing Niagara manifest",
            "routes": dict(system.get("routes", {})),
        })
    toggles.append({
        "toggle_id": "audio.palette_pulse",
        "label": "Music-reactive palette pulse",
        "default": True,
        "source": "existing MPC_Melodia_Palette / music-clock path",
    })
    return toggles


def _photo_spot(seed: int, movement_id: str) -> dict[str, Any]:
    cell_x = stable_int(seed, "magic-photo", movement_id, "x") % GRID_SIZE
    cell_y = stable_int(seed, "magic-photo", movement_id, "y") % GRID_SIZE
    return {
        "chunk": [0, 0],
        "cell": [cell_x, cell_y],
        "world_origin_cm": [cell_x * VOXEL_SIZE_CM, cell_y * VOXEL_SIZE_CM, 0],
        "camera_intent": "hero silhouette + one magical accent + readable route",
        "lighting_presets": ["dawn", "moonlight", "rain", "resonance_peak"],
        "scene_preview_only": True,
    }


def _evolution_preview(archetype: Mapping[str, Any]) -> dict[str, Any]:
    rewards = archetype.get("affinity_rewards", {})
    stages = []
    for affinity, reward in sorted(rewards.items(), key=lambda item: int(item[0])):
        stages.append({
            "affinity": int(affinity),
            "reward_id": str(reward),
            "status": "authored_archetype_preview",
            "does_not_grant_runtime_reward": True,
        })
    return {
        "source": "existing GMM archetype affinity_rewards",
        "stages": stages,
        "runtime_owner": "existing affinity/progression authority",
    }


def _currency_affordance(movement_id: str, archetype: Mapping[str, Any]) -> dict[str, Any]:
    """Describe collection through the existing wallet, never a new reward path."""
    movement_element = MOVEMENT_ELEMENTS.get(movement_id)
    archetype_element = str(archetype.get("element")) if archetype.get("element") else None
    element = str(movement_element or archetype_element or "Forte")
    registry: dict[str, Any] = {}
    if CURRENCY_REGISTRY_PATH.exists():
        registry = _read_json(CURRENCY_REGISTRY_PATH)
    rows = {str(row.get("currency_id")): dict(row) for row in registry.get("currencies", [])}
    currency = rows.get(element)
    if currency is None:
        element = MOVEMENT_ELEMENTS.get(movement_id, "Forte")
        currency = rows.get(element, {"currency_id": element, "kind": "Shard"})
    return {
        "currency_id": currency.get("currency_id", element),
        "kind": currency.get("kind", "Shard"),
        "element": element,
        "archetype_element": archetype_element,
        "display_name": currency.get("display_name", f"{element} Shard"),
        "source_registry": "specs/economy/melodia_currency_registry.v1.json",
        "collection_material": "resonant_matter_fragment",
        "grant_authority": "UMelodiaTokenWalletSubsystem through existing canonical reward adapter",
        "amount": "authored_by_existing_challenge_or_pickup_definition",
        "preview_only": True,
        "does_not_grant_currency": True,
    }


def _quantum_setup(
    seed: int,
    movement_id: str,
    mode_id: str,
    atlas: Mapping[str, Any] | None,
) -> dict[str, Any]:
    compatible = [
        candidate_id
        for candidate_id, movement in WORLD_MOVEMENT_LIBRARY.items()
        if mode_id in movement.mode_affinities
    ]
    if movement_id not in compatible:
        compatible.insert(0, movement_id)
    candidates = compatible[:2]
    rank_preview: dict[str, Any] | None = None
    if atlas and len(candidates) >= 1:
        try:
            from quantum.resonant_movement_ranker import candidates_from_atlas, rank_movements

            rank_candidates = candidates_from_atlas(atlas, candidates)
            if rank_candidates:
                # Ask for the narrow quantum path when the setup has exactly two
                # authored candidates.  The ranker records a classical baseline
                # and falls back truthfully when Q# is unavailable.
                requested_backend = "qsharp-simulator" if len(rank_candidates) == 2 else "classical-baseline"
                rank_preview = rank_movements(seed, rank_candidates, backend=requested_backend)
        except Exception as exc:  # pragma: no cover - environment-dependent Q# import
            rank_preview = {"status": "classical_rank_preview_unavailable", "reason": str(exc)}
    return {
        "selection_stage": "world_preparation_only",
        "candidate_movements": candidates,
        "backend_policy": {
            "preferred": "qsharp-simulator",
            "fallback": "classical-baseline",
            "requires_exactly_two_candidates_for_qsharp": True,
        },
        "rank_preview": rank_preview,
        "persisted_fields": ["winner_movement_id", "classical_baseline_winner_id", "backend", "trace_id"],
        "not_allowed": ["per_frame_traversal", "individual_voxel_selection", "player_input_grading"],
    }


def _passage_id(seed: int, movement_id: str, wardrobe_request_id: str) -> str:
    return hashlib.sha256(
        f"{PASSAGE_VERSION}|{int(seed)}|{movement_id}|{wardrobe_request_id}".encode("utf-8")
    ).hexdigest()[:16]


def build_magic_passage(
    world_seed: int = 3900,
    *,
    wardrobe: Mapping[str, Any] | None = None,
    movement_id: str | None = None,
    archetype_id: str | None = None,
    atlas: Mapping[str, Any] | None = None,
    phrase: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    config = WorldConfig.from_seed(world_seed)
    if wardrobe is None:
        wardrobe = build_wardrobe_voicing_preview(
            world_seed,
            movement_id=movement_id,
            archetype_id=archetype_id,
            atlas=atlas,
            phrase=phrase,
        )
    selected_movement_id = str(wardrobe.get("world", {}).get("movement_id", movement_id or config.movement_id))
    if selected_movement_id not in WORLD_MOVEMENT_LIBRARY:
        raise ValueError(f"unknown movement id: {selected_movement_id}")
    movement = WORLD_MOVEMENT_LIBRARY[selected_movement_id]
    style = wardrobe.get("layers", {}).get("style", {})
    archetype = style.get("archetype", {})
    presentation = wardrobe.get("world_response", {}).get("presentation", {})
    binding = wardrobe.get("asset_binding", {}).get("asset_resolution", {})
    actions = WORLD_ACTIONS[movement.world_verb]
    phrase_windows = _phrase_windows(phrase, len(STAGE_IDS))
    pcg_fragments = list(movement.pcg_asset_fragments)
    pcg_resolved = list(binding.get("pcg", pcg_fragments)) or pcg_fragments
    musical_fragments = list(binding.get("musical", movement.musical_asset_fragments)) or list(movement.musical_asset_fragments)
    water_profiles = [item.get("profile_id") for item in presentation.get("water_profiles", []) if item.get("profile_id")]
    if not water_profiles:
        water_profiles = list(movement.water_profiles)
    vfx_systems = [dict(item) for item in presentation.get("vfx_systems", [])]
    request_id = str(wardrobe.get("request_id", "0000000000000000"))
    passage_id = _passage_id(world_seed, selected_movement_id, request_id)
    stages: list[dict[str, Any]] = []
    for index, (stage_id, job, trigger, action) in enumerate(zip(STAGE_IDS, STAGE_JOBS, STAGE_TRIGGERS, actions)):
        vfx = _pick(vfx_systems, index)
        stages.append({
            "stage_id": stage_id,
            "musical_job": job,
            "trigger": trigger,
            "beat_range": [index * config.beats_per_bar, ((index + 1) * config.beats_per_bar) - 1],
            "world_action": action,
            "pcg_dressing": {
                "query_fragment": _pick(pcg_fragments, index),
                "resolved_asset": _pick(pcg_resolved, index),
                "owner": "existing PCG / World Partition pipeline",
            },
            "musical_asset": _pick(musical_fragments, index),
            "water_profile": _pick(water_profiles, index),
            "vfx_system": vfx.get("system_id") if vfx else None,
            "phrase_window": phrase_windows[index],
            "npc_zone": _pick(movement.npc_zones, index),
            "style_axes": list(style.get("voicing", {}).get("active_axes", movement.style_axes)),
        })
    return {
        "format": "melodia_resonant_world_magic_passage",
        "schema_version": 1,
        "passage_version": PASSAGE_VERSION,
        "passage_id": passage_id,
        "world": {
            "world_seed": int(world_seed),
            "root_note": config.root_note,
            "mode_id": config.mode_id,
            "bpm": config.bpm,
            "motif_id": config.motif_id,
            "movement_id": selected_movement_id,
        },
        "premise": {
            "display_name": f"{movement.display_name} Resonant Passage",
            "world_verb": movement.world_verb,
            "resonant_form_id": movement.resonant_form_id,
            "description": movement.description,
            "player_facing_rule": "attire changes the world's interpretation, not the canonical save or combat state",
        },
        "wardrobe_source": {
            "request_id": request_id,
            "archetype_id": style.get("archetype_id"),
            "cosmetic_record_count": len(wardrobe.get("layers", {}).get("cosmetic", {}).get("records", [])),
            "active_style_axes": list(style.get("voicing", {}).get("active_axes", movement.style_axes)),
            "resonant_form_declares_only": wardrobe.get("layers", {}).get("form", {}).get("declares_only", True),
        },
        "response_choreography": stages,
        "scene_preview": {
            "photo_spot": _photo_spot(world_seed, selected_movement_id),
            "effect_toggles": _effect_toggles(presentation),
            "outfit_evolution_preview": _evolution_preview(archetype),
            "source_inspiration": "Infinity Nikki-style scene preview and outfit effect controls",
        },
        "ensemble": {
            "archetype_id": style.get("archetype_id"),
            "display_name": archetype.get("display_name"),
            "role": archetype.get("role"),
            "element": archetype.get("element"),
            "zones": list(movement.npc_zones),
            "schedule_is_authored_input": True,
            "spawn_authority": "existing NPC/PCG population owner",
        },
        "collection_affordance": _currency_affordance(selected_movement_id, archetype),
        "phrase": _phrase_summary(phrase),
        "quantum_setup": _quantum_setup(world_seed, selected_movement_id, config.mode_id, atlas),
        "canonical_routes": {
            "wardrobe": "UMelodiaWardrobeSubsystem",
            "traversal": "UMelodiaTraversalComponent",
            "narrative_and_save": "UMelodiaNarrativeSubsystem",
            "challenge_adapter": "MelodiaPCGNarrativeChallengeBridgeComponent",
            "music_clock": "existing Harmonix/Melodia music clock",
            "pcg_streaming": "existing PCG / World Partition pipeline",
        },
        "state_model": {
            "entry": "unvoiced",
            "active": "passage_running",
            "resolved": "canonical_adapter_request",
            "interrupted": "presentation_reset_without_reward",
            "persistent_payload": "world edits, discovered motifs, and canonical challenge state only",
        },
        "runtime_boundary": {
            "authoring_or_read_model": True,
            "does_not_spawn_actors": True,
            "does_not_equip": True,
            "does_not_grant_capability": True,
            "does_not_commit_challenge": True,
            "does_not_write_save": True,
            "does_not_control_per_frame_traversal": True,
        },
    }


def build_magic_passage_portfolio(
    world_seed: int = 3900,
    *,
    atlas: Mapping[str, Any] | None = None,
    phrase: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    passages = []
    for movement_id in WORLD_MOVEMENT_LIBRARY:
        wardrobe = build_wardrobe_voicing_preview(
            world_seed,
            movement_id=movement_id,
            atlas=atlas,
            phrase=phrase,
        )
        passages.append(build_magic_passage(world_seed, wardrobe=wardrobe, atlas=atlas, phrase=phrase))
    return {
        "format": "melodia_resonant_world_magic_passage_portfolio",
        "schema_version": 1,
        "passage_version": PASSAGE_VERSION,
        "world_seed": int(world_seed),
        "atlas_summary": {
            "atlas_version": (atlas or {}).get("atlas_version"),
            "scanned_file_count": (atlas or {}).get("scan", {}).get("scanned_file_count"),
            "family_counts": (atlas or {}).get("scan", {}).get("family_counts", {}),
        },
        "passage_count": len(passages),
        "passages": passages,
    }


def validate_magic_passage(passage: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if passage.get("format") != "melodia_resonant_world_magic_passage":
        errors.append("unexpected magic passage format")
    if passage.get("passage_version") != PASSAGE_VERSION:
        errors.append("unexpected magic passage version")
    if passage.get("world", {}).get("movement_id") not in WORLD_MOVEMENT_LIBRARY:
        errors.append("magic passage movement is not authored")
    stages = passage.get("response_choreography", [])
    if len(stages) != 4:
        errors.append("magic passage must have four authored stages")
    for stage in stages:
        if not stage.get("world_action"):
            errors.append("magic passage stage is missing a world action")
        if not stage.get("pcg_dressing", {}).get("owner"):
            errors.append("magic passage stage is missing PCG ownership")
    boundary = passage.get("runtime_boundary", {})
    for key in (
        "authoring_or_read_model",
        "does_not_spawn_actors",
        "does_not_equip",
        "does_not_grant_capability",
        "does_not_commit_challenge",
        "does_not_write_save",
        "does_not_control_per_frame_traversal",
    ):
        if boundary.get(key) is not True:
            errors.append(f"runtime boundary {key} must be true")
    if passage.get("scene_preview", {}).get("photo_spot", {}).get("scene_preview_only") is not True:
        errors.append("scene preview must remain preview-only")
    return errors


def validate_magic_passage_portfolio(portfolio: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if portfolio.get("format") != "melodia_resonant_world_magic_passage_portfolio":
        errors.append("unexpected magic passage portfolio format")
    passages = list(portfolio.get("passages", []))
    if int(portfolio.get("passage_count", 0)) != len(passages):
        errors.append("passage_count does not match passages")
    if len(passages) != len(WORLD_MOVEMENT_LIBRARY):
        errors.append("portfolio does not cover every authored movement")
    ids = [str(passage.get("passage_id")) for passage in passages]
    if len(ids) != len(set(ids)):
        errors.append("portfolio passage ids are not unique")
    for passage in passages:
        errors.extend(validate_magic_passage(passage))
    return errors


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=3900)
    parser.add_argument("--movement")
    parser.add_argument("--archetype")
    parser.add_argument("--atlas", type=Path)
    parser.add_argument("--phrase", type=Path)
    parser.add_argument("--wardrobe", type=Path)
    parser.add_argument("--all-movements", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    atlas = _load_atlas(args.atlas)
    phrase = _load_phrase(args.phrase)
    if args.all_movements:
        result = build_magic_passage_portfolio(args.seed, atlas=atlas, phrase=phrase)
        errors = validate_magic_passage_portfolio(result)
    else:
        wardrobe = _load_wardrobe(args.wardrobe)
        result = build_magic_passage(
            args.seed,
            wardrobe=wardrobe,
            movement_id=args.movement,
            archetype_id=args.archetype,
            atlas=atlas,
            phrase=phrase,
        )
        errors = validate_magic_passage(result)
    result["validation_errors"] = errors
    result["ok"] = not errors
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": result["ok"],
        "output": str(args.output),
        "format": result["format"],
        "passages": result.get("passage_count", 1),
        "movement": result.get("world", {}).get("movement_id"),
        "errors": errors,
    }, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
