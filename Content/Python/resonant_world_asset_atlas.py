"""Build an asset-driven atlas for Melodia's long-term Resonant World.

The atlas is an authoring and audit artifact, not a runtime loader.  It scans
the project for the asset families that already exist, reads the small JSON
manifests that describe those families, and resolves each authored world
movement against real files.  This keeps procedural generation imaginative
without letting it silently invent an Unreal path.

Usage from the repository root::

    python Content/Python/resonant_world_asset_atlas.py \
        --output Saved/Audit/resonant_world_asset_atlas.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping

from resonant_world_generator import WORLD_MOVEMENT_LIBRARY, WorldMovement


ATLAS_VERSION = "resonant_asset_atlas_v1"
SCAN_ROOTS = ("Content", "Plugins", "Products", "Imports", "generated")
MAX_SAMPLES_PER_FAMILY = 16


# A file may belong to more than one family.  For example, a Melusina hair
# material is simultaneously character, water, and material authoring data.
# Multi-tagging is useful here because the atlas describes cross-system reuse.
FAMILY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("melusina_character", ("Content/Melodia/Characters/Melusina", "Content/Characters/Melusina", "Melusina")),
    ("wardrobe", ("Plugins/MelodiaWardrobe", "wardrobe", "Cos_", "ClothAsset_", "ResonantForm")),
    ("musical_pcg", ("Content/EnvSandbox/PCG/Musical", "PCG_Musical", "PCG_Hero_")),
    ("sakura_pcg", ("PCG/Sakura", "PCG_Nikki", "Sakura", "Phy llotaxis", "Phyllotaxis")),
    ("cosmic_pcg", ("PCG/Cosmic", "CosmicOrrery", "SpaceCathedral", "Astral")),
    ("grotto_pcg", ("BaroqueGrotto", "PCG/Grotto", "PCG_WP_Escher", "Cyberpunk")),
    ("water", ("Content/MelodiaIntegration/Water", "Content/EnvSandbox/Water", "water_family_profiles")),
    ("niagara_nikki", ("VFX/Nikki", "niagara_nikki_library", "NS_Nikki_")),
    ("quantum", ("Content/Python/quantum", "QUANTUM_GAMEPLAY", "QuantumReaction", "QuantumEntropy")),
    ("musical_ornaments", ("MusicalOrnamentKitbash", "MusicalOrnament", "SM_Orn_", "SheetMusic")),
    ("audio_midi", ("Content/MelodiaIntegration/MIDI", "Content/Melodia/Characters/Melusina/Audio", "Imports/Audio", ".mid", ".wav")),
    ("gmm_archetypes", ("Content/Python/gmm/npc", "archetype_", "population_PCG")),
    ("materials", ("Content/EnvSandbox/Materials", "Content/Melodia/_PROJECT/04_Materials", "MPC_Melodia", "M_Master_Toon")),
)


MANIFEST_FILES = {
    "archetypes": "Content/Python/gmm/npc/archetype_library.json",
    "archetype_palettes": "Content/Python/gmm/npc/archetype_palettes.json",
    "population": "Content/Python/gmm/npc/population_PCGTest_Forest.json",
    "water_profiles": "Content/Python/gmm/fixtures/water_family_profiles.json",
    "niagara_nikki": "Content/Python/gmm/fixtures/niagara_nikki_library.json",
}


def _normalise(value: str) -> str:
    return value.replace("\\", "/").lower()


def _iter_project_files(project_root: Path) -> Iterable[Path]:
    for root_name in SCAN_ROOTS:
        root = project_root / root_name
        if not root.exists():
            continue
        yield from (path for path in root.rglob("*") if path.is_file())


def _families_for_path(relative_path: str) -> list[str]:
    normalised = _normalise(relative_path)
    families: list[str] = []
    for family, fragments in FAMILY_RULES:
        if any(_normalise(fragment) in normalised for fragment in fragments):
            families.append(family)
    return families or ["uncategorized"]


def _scan_files(project_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    extensions: dict[str, Counter[str]] = defaultdict(Counter)
    samples: dict[str, list[str]] = defaultdict(list)

    for path in sorted(_iter_project_files(project_root), key=lambda item: item.as_posix().lower()):
        relative = path.relative_to(project_root).as_posix()
        families = _families_for_path(relative)
        suffix = path.suffix.lower() or "[none]"
        rows.append({"path": relative, "suffix": suffix, "families": families})
        for family in families:
            counts[family] += 1
            extensions[family][suffix] += 1
            if len(samples[family]) < MAX_SAMPLES_PER_FAMILY:
                samples[family].append(relative)

    summary = {
        "scanned_file_count": len(rows),
        "family_counts": dict(sorted(counts.items())),
        "families": {
            family: {
                "file_count": counts[family],
                "extension_counts": dict(sorted(extensions[family].items())),
                "sample_paths": samples[family],
            }
            for family in sorted(counts)
        },
    }
    return rows, summary


def _load_json_manifests(project_root: Path) -> tuple[dict[str, Any], dict[str, str]]:
    manifests: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for key, relative_path in MANIFEST_FILES.items():
        path = project_root / relative_path
        try:
            manifests[key] = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - this is an audit diagnostic
            errors[key] = f"{type(exc).__name__}: {exc}"
    return manifests, errors


def _resolve_fragments(
    rows: list[dict[str, Any]],
    fragments: Iterable[str],
    logical_refs: Iterable[str] = (),
) -> list[str]:
    lower_rows = [(row["path"], _normalise(row["path"])) for row in rows]
    lower_logical_refs = [(ref, _normalise(ref)) for ref in logical_refs]
    resolved: list[str] = []
    for fragment in fragments:
        token = _normalise(fragment)
        matches = [path for path, lower in lower_rows if token in lower]
        matches.extend(ref for ref, lower in lower_logical_refs if token in lower)
        resolved.extend(matches[:MAX_SAMPLES_PER_FAMILY])
    return sorted(set(resolved))


def _movement_record(
    rows: list[dict[str, Any]],
    movement: WorldMovement,
    logical_refs: Iterable[str] = (),
) -> dict[str, Any]:
    pcg_assets = _resolve_fragments(rows, movement.pcg_asset_fragments, logical_refs)
    musical_assets = _resolve_fragments(rows, movement.musical_asset_fragments, logical_refs)
    vfx_assets = _resolve_fragments(rows, movement.vfx_systems, logical_refs)
    water_assets = _resolve_fragments(rows, movement.water_profiles, logical_refs)
    archetype_assets = _resolve_fragments(rows, movement.outfit_archetypes, logical_refs)
    missing = []
    for label, values in (
        ("pcg", pcg_assets),
        ("musical", musical_assets),
        ("vfx", vfx_assets),
        ("water", water_assets),
        ("archetype", archetype_assets),
    ):
        if not values and label not in {"water"}:
            missing.append(label)
    return {
        "movement_id": movement.movement_id,
        "display_name": movement.display_name,
        "world_verb": movement.world_verb,
        "resonant_form_id": movement.resonant_form_id,
        "style_axes": list(movement.style_axes),
        "mode_affinities": list(movement.mode_affinities),
        "asset_resolution": {
            "pcg": pcg_assets,
            "musical": musical_assets,
            "vfx": vfx_assets,
            "water": water_assets,
            "outfit_and_archetype": archetype_assets,
        },
        "asset_counts": {
            "pcg": len(pcg_assets),
            "musical": len(musical_assets),
            "vfx": len(vfx_assets),
            "water": len(water_assets),
            "outfit_and_archetype": len(archetype_assets),
        },
        "missing_required_families": missing,
        "quantum_objective": list(movement.quantum_objective),
        "npc_zones": list(movement.npc_zones),
        "outfit_archetypes": list(movement.outfit_archetypes),
    }


def _summarise_manifests(manifests: Mapping[str, Any]) -> dict[str, Any]:
    archetypes = manifests.get("archetypes", {}).get("archetypes", {})
    palettes = manifests.get("archetype_palettes", {})
    population = manifests.get("population", {})
    water = manifests.get("water_profiles", {})
    niagara = manifests.get("niagara_nikki", {})
    return {
        "archetypes": {
            key: {
                "display_name": value.get("display_name"),
                "role": value.get("role"),
                "element": value.get("element"),
                "bpm": value.get("bpm"),
                "outfit_pieces": value.get("outfit_pieces", []),
                "spawn_zones": value.get("spawn_zones", []),
                "affinity_rewards": value.get("affinity_rewards", {}),
            }
            for key, value in sorted(archetypes.items())
        },
        "palette_ids": sorted(palettes),
        "population": {
            "zone_name": population.get("zone_name"),
            "spawn_count": len(population.get("spawns", population.get("population", []))) if isinstance(population, dict) else 0,
            "keys": sorted(population) if isinstance(population, dict) else [],
        },
        "water_profiles": {
            key: {
                "mesh": value.get("mesh"),
                "material": value.get("material"),
                "rhythm": value.get("rhythm"),
            }
            for key, value in sorted(water.items())
            if isinstance(value, dict)
        },
        "niagara_systems": {
            key: {
                "path": value.get("path"),
                "description": value.get("description"),
                "max_particles": value.get("max_particles"),
                "audio_routes": sorted(
                    route for route in value.get("osr_routes", {})
                    if "audio" in route or "melusina" in route or "pitch" in route
                ),
            }
            for key, value in sorted(niagara.get("systems", {}).items())
            if isinstance(value, dict)
        },
    }


def _logical_manifest_refs(manifests: Mapping[str, Any]) -> list[str]:
    """Return named records from JSON manifests as resolvable authoring refs.

    Some useful project assets are currently represented by a fixture or
    catalog before their final .uasset is promoted.  Keeping those records in
    the atlas makes the gap explicit instead of pretending a filename match
    proves runtime availability.
    """
    refs: list[str] = []
    archetypes = manifests.get("archetypes", {}).get("archetypes", {})
    refs.extend(f"manifest:archetypes/{key}" for key in archetypes)
    niagara = manifests.get("niagara_nikki", {}).get("systems", {})
    refs.extend(f"manifest:niagara/{key}" for key in niagara)
    water = manifests.get("water_profiles", {})
    if isinstance(water, dict):
        refs.extend(f"manifest:water/{key}" for key in water)
    return refs


def build_asset_atlas(project_root: str | Path) -> dict[str, Any]:
    root = Path(project_root).resolve()
    rows, scan_summary = _scan_files(root)
    manifests, manifest_errors = _load_json_manifests(root)
    logical_refs = _logical_manifest_refs(manifests)
    movement_records = {
        movement_id: _movement_record(rows, movement, logical_refs)
        for movement_id, movement in sorted(WORLD_MOVEMENT_LIBRARY.items())
    }
    atlas = {
        "format": "melodia_resonant_world_asset_atlas",
        "atlas_version": ATLAS_VERSION,
        "generator_version": "resonant_world_v1",
        "project_root_name": root.name,
        "scan_roots": list(SCAN_ROOTS),
        "scan": scan_summary,
        "manifest_sources": {
            key: {
                "path": relative_path,
                "loaded": key not in manifest_errors,
                "error": manifest_errors.get(key),
            }
            for key, relative_path in MANIFEST_FILES.items()
        },
        "manifest_summary": _summarise_manifests(manifests),
        "logical_manifest_refs": logical_refs,
        "world_movements": movement_records,
        "rules": {
            "movement_asset_queries_are_authoring_only": True,
            "unreal_asset_paths_are_resolved_before_runtime_binding": True,
            "missing_asset_families_are_reported_not_synthesised": True,
            "quantum_can_select_between_authored_movements_only": True,
        },
    }
    atlas["validation_errors"] = validate_asset_atlas(atlas)
    atlas["ok"] = not atlas["validation_errors"]
    return atlas


def validate_asset_atlas(atlas: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if atlas.get("format") != "melodia_resonant_world_asset_atlas":
        errors.append("format is not melodia_resonant_world_asset_atlas")
    if atlas.get("atlas_version") != ATLAS_VERSION:
        errors.append("atlas version is not registered")
    scan = atlas.get("scan", {})
    if int(scan.get("scanned_file_count", 0)) <= 0:
        errors.append("no project files were scanned")
    for family in ("musical_pcg", "wardrobe", "water", "niagara_nikki", "quantum"):
        if int(scan.get("family_counts", {}).get(family, 0)) <= 0:
            errors.append(f"expected asset family is empty: {family}")
    movements = atlas.get("world_movements", {})
    if set(movements) != set(WORLD_MOVEMENT_LIBRARY):
        errors.append("movement records do not match the authored movement library")
    for movement_id, record in movements.items():
        required = record.get("missing_required_families", [])
        if required:
            errors.append(f"movement {movement_id} is missing required asset families: {', '.join(required)}")
    return errors


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    atlas = build_asset_atlas(args.root)
    encoded = json.dumps(atlas, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    else:
        print(encoded)
    return 0 if atlas["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
