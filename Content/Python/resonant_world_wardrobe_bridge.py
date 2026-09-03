"""Build a deterministic wardrobe-to-world voicing preview for Melodia.

This is the authoring/read-model seam between the three-layer wardrobe contract
and Resonant World movements.  It combines the real first-outfit catalog source,
the existing GMM outfit archetypes, movement asset resolution, water/FX
manifests, and an optional phrase manifest into one inspectable artifact.

It deliberately does not grant a capability, commit a challenge, write a save,
equip a cosmetic, or become a second traversal/style authority.  The runtime
owners remain the existing wardrobe, traversal, narrative, music-clock, and PCG
systems.  The output is useful both as a design preview and as the future input
to a narrow runtime request adapter.

Usage::

    python Content/Python/resonant_world_wardrobe_bridge.py \
        --seed 3900 --movement petal_cantata --archetype SakuraDreamer \
        --atlas Saved/Audit/resonant_world_asset_atlas.json \
        --phrase Saved/Audit/resonant_world_phrase_128bpm.json \
        --output Saved/Audit/resonant_wardrobe_voicing_sakura_3900.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from resonant_world_generator import WORLD_MOVEMENT_LIBRARY, WorldConfig, stable_float


VOICING_VERSION = "resonant_wardrobe_voicing_v1"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
WARDROBE_MANIFEST_PATH = PROJECT_ROOT / "specs" / "wardrobe" / "wardrobe_catalog_manifest.v1.json"
ARCHETYPE_LIBRARY_PATH = PROJECT_ROOT / "Content" / "Python" / "gmm" / "npc" / "archetype_library.json"
ARCHETYPE_PALETTE_PATH = PROJECT_ROOT / "Content" / "Python" / "gmm" / "npc" / "archetype_palettes.json"
WATER_PROFILE_PATH = PROJECT_ROOT / "Content" / "Python" / "gmm" / "fixtures" / "water_family_profiles.json"
NIAGARA_LIBRARY_PATH = PROJECT_ROOT / "Content" / "Python" / "gmm" / "fixtures" / "niagara_nikki_library.json"
CHALLENGE_FIXTURE_PATH = PROJECT_ROOT / "specs" / "blueprints" / "fixtures" / "first_resonance_world_challenge.v1.json"


# These are preview coefficients, not EMelodiaStyleScore values.  The reflected
# wardrobe type currently uses EMelodiaSpellElement for catalog styling, while
# resonance/cadence/lilt/etc. are still an authoring vocabulary in the world
# design.  Keeping this table here makes that distinction explicit and lets the
# future catalog importer replace it with authored style scores.
ARCHETYPE_VOICING: dict[str, dict[str, float]] = {
    "SakuraDreamer": {
        "resonance": 0.90,
        "cadence": 0.56,
        "lilt": 0.95,
        "flow": 0.74,
        "orbit": 0.30,
        "tension": 0.14,
    },
    "CosmicWeaver": {
        "resonance": 0.84,
        "cadence": 0.64,
        "lilt": 0.34,
        "flow": 0.48,
        "orbit": 0.98,
        "tension": 0.40,
    },
    "MirageDancer": {
        "resonance": 0.60,
        "cadence": 0.90,
        "lilt": 0.86,
        "flow": 0.78,
        "orbit": 0.42,
        "tension": 0.46,
    },
    # Melusina is a player-character source in the project, not a GMM NPC
    # archetype.  This neutral profile lets Liquid Cathedral and Cadence
    # Cathedral use her real identity without inventing NPC data.
    "Melusina": {
        "resonance": 0.76,
        "cadence": 0.70,
        "lilt": 0.70,
        "flow": 0.84,
        "orbit": 0.58,
        "tension": 0.32,
    },
}


def _read_json(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        raise FileNotFoundError(f"manifest not found: {target}")
    value = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"manifest root is not an object: {target}")
    return value


def _load_optional_json(path: str | Path | None) -> dict[str, Any] | None:
    return _read_json(path) if path else None


def _source_manifest() -> dict[str, Any]:
    return _read_json(WARDROBE_MANIFEST_PATH)


def _archetype_library() -> dict[str, Any]:
    data = _read_json(ARCHETYPE_LIBRARY_PATH)
    return dict(data.get("archetypes", {}))


def _archetype_palettes() -> dict[str, Any]:
    return _read_json(ARCHETYPE_PALETTE_PATH)


def _draft_records() -> list[dict[str, Any]]:
    draft_root = PROJECT_ROOT / "Plugins" / "MelodiaWardrobe" / "Content" / "MelodiaWardrobe" / "Drafts"
    records: list[dict[str, Any]] = []
    if not draft_root.exists():
        return records
    for path in sorted(draft_root.glob("*.json")):
        record = _read_json(path)
        record["source_file"] = path.relative_to(PROJECT_ROOT).as_posix()
        records.append(record)
    return records


def _first_outfit_records(source: Mapping[str, Any]) -> list[dict[str, Any]]:
    first_outfit = source.get("first_outfit", {})
    return [dict(record) for record in first_outfit.get("records", [])]


def _resolve_catalog_records(
    source: Mapping[str, Any],
    cosmetic_ids: Iterable[str] | None,
) -> tuple[list[dict[str, Any]], list[str]]:
    records = _first_outfit_records(source)
    by_id = {str(record.get("cosmetic_id")): record for record in records}
    requested = [str(value) for value in (cosmetic_ids or ())]
    if not requested:
        return records, []
    unknown = [value for value in requested if value not in by_id]
    if unknown:
        raise ValueError(f"cosmetic ids are not in the first-outfit source manifest: {unknown}")
    return [dict(by_id[value]) for value in requested], []


def _movement_assets(
    movement_id: str,
    movement: Any,
    atlas: Mapping[str, Any] | None,
) -> dict[str, Any]:
    record = dict((atlas or {}).get("world_movements", {}).get(movement_id, {}))
    resolved = dict(record.get("asset_resolution", {}))
    # The atlas intentionally separates logical refs from promoted Unreal
    # files.  Preserve that distinction while filling water from its authored
    # profile manifest, whose stable profile ids are already the project
    # contract even when no promoted asset has been scanned yet.
    def resolved_or_query(key: str, fallback: Iterable[str]) -> list[str]:
        values = resolved.get(key)
        return list(values) if values else list(fallback)

    return {
        "atlas_version": (atlas or {}).get("atlas_version"),
        "asset_resolution": {
            "pcg": resolved_or_query("pcg", movement.pcg_asset_fragments),
            "musical": resolved_or_query("musical", movement.musical_asset_fragments),
            "vfx": resolved_or_query("vfx", movement.vfx_systems),
            "water": resolved_or_query("water", movement.water_profiles),
            "outfit_and_archetype": list(
                resolved_or_query("outfit_and_archetype", movement.outfit_archetypes)
            ),
        },
        "logical_manifest_refs": list((atlas or {}).get("logical_manifest_refs", [])),
        "missing_required_families": list(record.get("missing_required_families", [])),
    }


def _water_selection(movement: Any) -> list[dict[str, Any]]:
    profiles = _read_json(WATER_PROFILE_PATH).get("profiles", {})
    selected: list[dict[str, Any]] = []
    for profile_id in movement.water_profiles:
        if profile_id in profiles:
            selected.append({"profile_id": profile_id, **dict(profiles[profile_id])})
        else:
            selected.append({"profile_id": profile_id, "status": "profile_missing"})
    return selected


def _vfx_selection(movement: Any) -> list[dict[str, Any]]:
    systems = _read_json(NIAGARA_LIBRARY_PATH).get("systems", {})
    selected: list[dict[str, Any]] = []
    for system_id in movement.vfx_systems:
        if system_id in systems:
            system = dict(systems[system_id])
            selected.append({
                "system_id": system_id,
                "path": system.get("path"),
                "description": system.get("description"),
                "audio_reactive": "/melusina/amp" in system.get("osr_routes", {}).values(),
                "routes": dict(system.get("osr_routes", {})),
            })
        else:
            selected.append({"system_id": system_id, "status": "manifest_missing"})
    return selected


def _fallback_archetype(archetype_id: str, config: WorldConfig) -> dict[str, Any]:
    if archetype_id != "Melusina":
        raise ValueError(f"unknown archetype id: {archetype_id}")
    return {
        "id": "Melusina",
        "display_name": "Melusina",
        "description": "Player-character identity; wardrobe presentation is authored by the Melodia wardrobe catalog.",
        "role": "Player",
        "element": "Tide",
        "bpm": float(config.bpm),
        "outfit_pieces": [],
        "optional_accessories": [],
        "spawn_zones": [],
        "source": "existing Melusina player-character assets",
    }


def _select_archetype(movement: Any, archetype_id: str | None, config: WorldConfig) -> tuple[str, dict[str, Any]]:
    library = _archetype_library()
    chosen = archetype_id or (movement.outfit_archetypes[0] if movement.outfit_archetypes else "Melusina")
    if chosen in library:
        return chosen, dict(library[chosen])
    return chosen, _fallback_archetype(chosen, config)


def _style_voicing(seed: int, archetype_id: str, movement: Any) -> dict[str, Any]:
    base = ARCHETYPE_VOICING.get(archetype_id, ARCHETYPE_VOICING["Melusina"])
    axes = ("resonance", "cadence", "lilt", "flow", "orbit", "tension")
    scores: dict[str, float] = {}
    for axis in axes:
        value = float(base.get(axis, 0.5))
        # Tiny deterministic variation makes two seeded worlds feel related,
        # while preserving the authored archetype silhouette.
        variation = (stable_float(seed, "wardrobe-voicing", archetype_id, axis) - 0.5) * 0.08
        scores[axis] = round(max(0.0, min(1.0, value + variation)), 3)
    active_axes = list(movement.style_axes)
    return {
        "active_axes": active_axes,
        "scores": scores,
        "active_axis_mean": round(sum(scores[axis] for axis in active_axes) / len(active_axes), 3)
        if active_axes else 0.0,
        "source": "movement grammar + authored archetype intent",
        "runtime_catalog_style_scores_present": False,
        "note": "Preview coefficients are not EMelodiaStyleScore values and do not gate gameplay.",
    }


def _phrase_summary(phrase: Mapping[str, Any] | None) -> dict[str, Any]:
    if not phrase:
        return {
            "present": False,
            "interpretation": "world_seed_motif",
            "runtime_audio_authority": "existing Harmonix/Melodia music clock",
        }
    voxels = list(phrase.get("voxels", []))
    material_counts: dict[str, int] = {}
    for voxel in voxels:
        material = str(voxel.get("material_id", "unknown"))
        material_counts[material] = material_counts.get(material, 0) + 1
    pitches = [int(voxel.get("pitch", 0)) for voxel in voxels]
    return {
        "present": True,
        "phrase_id": phrase.get("source", {}).get("phrase_id"),
        "midi_file_name": phrase.get("source", {}).get("midi_file_name"),
        "note_count": int(phrase.get("note_count", len(voxels))),
        "voxel_count": int(phrase.get("voxel_count", len(voxels))),
        "material_counts": material_counts,
        "pitch_span": [min(pitches), max(pitches)] if pitches else [],
        "runtime_audio_authority": phrase.get("rules", {}).get(
            "runtime_audio_authority", "existing Harmonix/Melodia music clock"
        ),
        "interpretation": "phrase_voxels_are_authoring_input_only",
    }


def _challenge_hook(movement_id: str) -> dict[str, Any]:
    fixture = _read_json(CHALLENGE_FIXTURE_PATH)
    package = fixture.get("package", {})
    definition = fixture.get("definition_contract", {})
    is_proof_movement = movement_id == "cadence_cathedral"
    return {
        "enabled_for_proof_preview": is_proof_movement,
        "challenge_id": definition.get("challenge_id", "challenge.first_resonance_echo"),
        "completion_flag_id": definition.get("completion_flag_id"),
        "reward_id": definition.get("reward_id"),
        "package_id": package.get("PackageId"),
        "adapter": "MelodiaPCGNarrativeChallengeBridgeComponent -> UMelodiaNarrativeSubsystem",
        "attempt_state": "runtime_only_until_commit",
        "commit_policy": "canonical_narrative_adapter_only",
        "preview_only": True,
    }


def _request_id(seed: int, movement_id: str, archetype_id: str, cosmetic_ids: Iterable[str]) -> str:
    payload = "|".join((str(int(seed)), movement_id, archetype_id, *sorted(str(value) for value in cosmetic_ids)))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def build_wardrobe_voicing_preview(
    world_seed: int = 3900,
    *,
    movement_id: str | None = None,
    archetype_id: str | None = None,
    cosmetic_ids: Iterable[str] | None = None,
    atlas: Mapping[str, Any] | None = None,
    phrase: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    config = WorldConfig.from_seed(world_seed)
    selected_movement_id = movement_id or config.movement_id
    if selected_movement_id not in WORLD_MOVEMENT_LIBRARY:
        raise ValueError(f"unknown movement id: {selected_movement_id}")
    movement = WORLD_MOVEMENT_LIBRARY[selected_movement_id]
    selected_archetype_id, archetype = _select_archetype(movement, archetype_id, config)

    source = _source_manifest()
    cosmetics, _ = _resolve_catalog_records(source, cosmetic_ids)
    palettes = _archetype_palettes()
    palette = dict(palettes.get(selected_archetype_id, {})) if selected_archetype_id in palettes else {}
    outfit_piece_ids = [
        *[str(value) for value in archetype.get("outfit_pieces", [])],
        *[str(value) for value in archetype.get("optional_accessories", [])],
    ]
    outfit_pieces = []
    all_pieces = _archetype_library().get("outfit_pieces", {})
    for piece_id in outfit_piece_ids:
        piece = dict(all_pieces.get(piece_id, {}))
        outfit_pieces.append({
            "piece_id": piece_id,
            "display_name": piece.get("display_name", piece_id),
            "slot_name": piece.get("slot_name"),
            "skeletal_mesh": piece.get("skeletal_mesh"),
            "material_slot": piece.get("material_slot"),
            "cloth_config": piece.get("cloth_config", {}),
            "status": "authored_archetype_piece" if piece else "archetype_piece_missing",
        })

    assets = _movement_assets(selected_movement_id, movement, atlas)
    voicing = _style_voicing(world_seed, selected_archetype_id, movement)
    request_id = _request_id(world_seed, selected_movement_id, selected_archetype_id, [
        str(record.get("cosmetic_id")) for record in cosmetics
    ])
    return {
        "format": "melodia_resonant_world_wardrobe_voicing",
        "schema_version": 1,
        "voicing_version": VOICING_VERSION,
        "request_id": request_id,
        "world": {
            "world_seed": int(world_seed),
            "root_note": config.root_note,
            "mode_id": config.mode_id,
            "bpm": config.bpm,
            "motif_id": config.motif_id,
            "movement_id": selected_movement_id,
        },
        "layers": {
            "cosmetic": {
                "catalog_asset": source.get("catalog_asset"),
                "source_manifest": "specs/wardrobe/wardrobe_catalog_manifest.v1.json",
                "outfit_id": source.get("first_outfit", {}).get("outfit_id"),
                "records": cosmetics,
                "catalog_policy": source.get("first_outfit", {}).get("resonant_form_policy"),
                "materialization_status": source.get(
                    "materialization_status", "source_ready_editor_materialization_pending"
                ),
                "draft_source_count": len(_draft_records()),
                "draft_reconciliation": source.get("draft_reconciliation", {}),
            },
            "form": {
                "requested_resonant_form_id": movement.resonant_form_id,
                "world_verb": movement.world_verb,
                "declares_only": True,
                "grants_capability": False,
                "resolution_status": "world_request_only_until_catalog_form_and_runtime_gate_readback",
            },
            "style": {
                "archetype_id": selected_archetype_id,
                "archetype": archetype,
                "palette": palette,
                "outfit_pieces": outfit_pieces,
                "voicing": voicing,
            },
        },
        "movement": movement.to_dict(),
        "asset_binding": assets,
        "world_response": {
            "verb": movement.world_verb,
            "request_id": request_id,
            "pcg_dressing": {
                "owner": "existing pcg_scale_world_pipeline + pcg_visual_chunk_builder",
                "query_fragments": list(movement.pcg_asset_fragments),
                "resolved_assets": assets["asset_resolution"]["pcg"],
                "preserve_authored_hero_graphs": True,
            },
            "presentation": {
                "vfx_systems": _vfx_selection(movement),
                "water_profiles": _water_selection(movement),
                "palette_bus": "MPC_Melodia_Palette",
                "phrase": _phrase_summary(phrase),
                "archetype_palette_name": archetype.get("palette_name", selected_archetype_id),
            },
            "route_request": {
                "soft_gate": True,
                "request_only": True,
                "authority": "UMelodiaTraversalComponent",
                "narrative_authority": "UMelodiaNarrativeSubsystem",
                "requested_effect": f"{movement.world_verb}_world_presentation",
            },
        },
        "challenge_hook": _challenge_hook(selected_movement_id),
        "authorities": {
            "wardrobe_state": "UMelodiaWardrobeSubsystem",
            "traversal": "UMelodiaTraversalComponent",
            "narrative_and_save": "UMelodiaNarrativeSubsystem",
            "combat_and_inventory": "TurnBased JRPG template",
            "music_clock": "existing Harmonix/Melodia music clock",
            "pcg_and_streaming": "existing PCG / World Partition pipeline",
        },
        "runtime_boundary": {
            "preview_only": True,
            "does_not_equip": True,
            "does_not_grant_capability": True,
            "does_not_commit_challenge": True,
            "does_not_write_save": True,
            "quantum_role": "optional asynchronous chooser between authored movement candidates; classical baseline remains valid",
        },
    }


def validate_wardrobe_voicing_preview(preview: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if preview.get("format") != "melodia_resonant_world_wardrobe_voicing":
        errors.append("unexpected wardrobe voicing format")
    if preview.get("voicing_version") != VOICING_VERSION:
        errors.append("unexpected wardrobe voicing version")
    movement_id = preview.get("world", {}).get("movement_id")
    if movement_id not in WORLD_MOVEMENT_LIBRARY:
        errors.append("world movement is not authored")
    layers = preview.get("layers", {})
    if not layers.get("cosmetic", {}).get("records"):
        errors.append("preview has no catalog cosmetic records")
    if layers.get("form", {}).get("grants_capability") is not False:
        errors.append("form layer must not grant a capability")
    boundary = preview.get("runtime_boundary", {})
    for key in ("preview_only", "does_not_equip", "does_not_grant_capability", "does_not_commit_challenge", "does_not_write_save"):
        if boundary.get(key) is not True:
            errors.append(f"runtime boundary {key} must be true")
    if preview.get("challenge_hook", {}).get("preview_only") is not True:
        errors.append("challenge hook must remain preview-only")
    return errors


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
    return data


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=3900)
    parser.add_argument("--movement")
    parser.add_argument("--archetype")
    parser.add_argument("--cosmetic-id", action="append", dest="cosmetic_ids")
    parser.add_argument("--atlas", type=Path)
    parser.add_argument("--phrase", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    preview = build_wardrobe_voicing_preview(
        args.seed,
        movement_id=args.movement,
        archetype_id=args.archetype,
        cosmetic_ids=args.cosmetic_ids,
        atlas=_load_atlas(args.atlas),
        phrase=_load_phrase(args.phrase),
    )
    preview["validation_errors"] = validate_wardrobe_voicing_preview(preview)
    preview["ok"] = not preview["validation_errors"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(preview, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": preview["ok"],
        "output": str(args.output),
        "movement": preview["world"]["movement_id"],
        "archetype": preview["layers"]["style"]["archetype_id"],
        "cosmetics": len(preview["layers"]["cosmetic"]["records"]),
        "errors": preview["validation_errors"],
    }, indent=2))
    return 0 if preview["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
