"""Build a deterministic, offline Melusina world-gen handoff bundle.

The bundle joins the canonical MIDI phrase bridge, Resonant World manifest,
score, PCG adapter plan, proof envelope, and an optional Blender-generated
mesh manifest.  It is an authoring artifact only: it never imports ``unreal``,
opens an editor, applies a map change, or writes gameplay/save state.

Example::

    python Content/Python/melusina_offline_world_bundle.py \
        --midi Content/MelodiaIntegration/MIDI/128BPMarpeggiomelody.mid \
        --movement petal_cantata \
        --blender-manifest Saved/Blender/MelodiaStudio/current_midi_environment.manifest.json \
        --output Saved/Blender/MelodiaStudio/OfflineWorldGen/PetalCantata_3900
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
PYTHON_ROOT = PROJECT_ROOT / "Content" / "Python"
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from resonant_world_generator import (  # noqa: E402
    build_world_manifest,
    validate_world_manifest,
)
from resonant_world_pcg_adapter import (  # noqa: E402
    build_resonant_pcg_plan,
    validate_resonant_pcg_plan,
)
from resonant_world_phrase_bridge import (  # noqa: E402
    build_phrase_manifest,
    validate_phrase_manifest,
)
from resonant_world_proof_handoff import (  # noqa: E402
    build_proof_handoff,
    validate_proof_handoff,
)
from resonant_world_score import (  # noqa: E402
    build_resonant_score,
    build_score_portfolio,
    validate_resonant_score,
)


BUNDLE_FORMAT = "melodia_melusina_offline_world_bundle"
BUNDLE_VERSION = "melusina_offline_world_bundle_v1"
DEFAULT_MIDI = PROJECT_ROOT / "Content" / "MelodiaIntegration" / "MIDI" / "128BPMarpeggiomelody.mid"
DEFAULT_ATLAS = PROJECT_ROOT / "Saved" / "Audit" / "resonant_world_asset_atlas.json"
DEFAULT_WARDROBE = PROJECT_ROOT / "Saved" / "Audit" / "resonant_wardrobe_voicing_sakura_3900.json"
DEFAULT_MAGIC_PASSAGE = PROJECT_ROOT / "Saved" / "Audit" / "resonant_magic_passage_petal_3900.json"


def _read_json(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    value = json.loads(target.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root is not an object: {target}")
    return value


def _write_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _path_record(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    try:
        display = resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        display = str(resolved)
    return {
        "path": str(resolved),
        "project_relative_path": display,
        "exists": resolved.is_file(),
        "bytes": resolved.stat().st_size if resolved.is_file() else 0,
        "sha256": _sha256(resolved) if resolved.is_file() else None,
    }


def _load_optional(path: str | Path | None) -> dict[str, Any] | None:
    if not path:
        return None
    target = Path(path)
    return _read_json(target) if target.is_file() else None


def _blender_handoff(
    manifest_path: str | Path | None,
    *,
    fbx_path: str | Path | None = None,
    blend_path: str | Path | None = None,
) -> tuple[dict[str, Any], list[str]]:
    if not manifest_path:
        return {"provided": False, "validated": False, "manifest": None, "mesh": None, "fbx": None, "blend": None}, []

    manifest_file = Path(manifest_path).resolve()
    errors: list[str] = []
    if not manifest_file.is_file():
        return {"provided": True, "validated": False, "manifest": _path_record(manifest_file), "mesh": None, "fbx": None, "blend": None}, [
            f"Blender manifest is missing: {manifest_file}"
        ]

    manifest = _read_json(manifest_file)
    if manifest.get("format") != "melodia_blender_midi_environment_manifest":
        errors.append("unexpected Blender MIDI environment manifest format")
    boundary = manifest.get("runtime_boundary", {})
    for key in ("offline_only", "does_not_call_unreal", "does_not_save_portfolio_stage", "does_not_write_gameplay_save"):
        if boundary.get(key) is not True:
            errors.append(f"Blender manifest boundary is not true: {key}")
    mesh_value = manifest.get("obj_path")
    mesh_file = Path(mesh_value) if mesh_value else manifest_file.with_suffix(".obj")
    if not mesh_file.is_absolute():
        mesh_file = (manifest_file.parent / mesh_file).resolve()
    mesh_record = _path_record(mesh_file)
    if not mesh_record["exists"]:
        errors.append(f"Blender OBJ is missing: {mesh_file}")

    export_records: dict[str, Any] = {}
    for label, value in (("fbx", fbx_path), ("blend", blend_path)):
        if value:
            record = _path_record(Path(value))
            export_records[label] = record
            if not record["exists"]:
                errors.append(f"Blender export is missing: {record['path']}")

    return {
        "provided": True,
        "validated": not errors,
        "manifest": _path_record(manifest_file),
        "mesh": mesh_record,
        "fbx": export_records.get("fbx"),
        "blend": export_records.get("blend"),
        "note_count": manifest.get("note_count"),
        "voxel_count": manifest.get("voxel_count"),
        "source_midi": manifest.get("source_midi"),
    }, errors


def build_offline_world_bundle(
    *,
    midi_path: str | Path,
    output_dir: str | Path,
    world_seed: int = 3900,
    movement_id: str = "petal_cantata",
    archetype_id: str = "SakuraDreamer",
    radius: int = 1,
    atlas_path: str | Path | None = DEFAULT_ATLAS,
    wardrobe_path: str | Path | None = DEFAULT_WARDROBE,
    magic_passage_path: str | Path | None = DEFAULT_MAGIC_PASSAGE,
    blender_manifest_path: str | Path | None = None,
    blender_fbx_path: str | Path | None = None,
    blender_blend_path: str | Path | None = None,
) -> dict[str, Any]:
    output = Path(output_dir).resolve()
    output.mkdir(parents=True, exist_ok=True)
    midi = Path(midi_path).resolve()
    atlas = _load_optional(atlas_path)
    wardrobe = _load_optional(wardrobe_path)
    magic_passage = _load_optional(magic_passage_path)

    phrase = build_phrase_manifest(midi, world_seed)
    phrase_errors = validate_phrase_manifest(phrase)
    phrase_path = output / "phrase.json"
    _write_json(phrase_path, {**phrase, "validation_errors": phrase_errors, "ok": not phrase_errors})

    world = build_world_manifest(world_seed, radius=radius, include_voxels=True)
    world_errors = validate_world_manifest(world)
    world_path = output / "world.json"
    _write_json(world_path, {**world, "validation_errors": world_errors, "ok": not world_errors})

    score = build_resonant_score(
        world_seed,
        movement_id=movement_id,
        archetype_id=archetype_id,
        project_root=PROJECT_ROOT,
    )
    score_errors = validate_resonant_score(score)
    score_path = output / "score.json"
    _write_json(score_path, {**score, "validation_errors": score_errors, "ok": not score_errors})

    score_portfolio = build_score_portfolio(world_seed, project_root=PROJECT_ROOT)
    score_portfolio_errors = score_portfolio.get("validation_errors", {})
    score_portfolio_path = output / "score_portfolio.json"
    _write_json(score_portfolio_path, score_portfolio)

    pcg = build_resonant_pcg_plan(
        world_seed,
        radius,
        atlas=atlas,
        phrase=phrase,
        wardrobe=wardrobe,
        magic_passage=magic_passage,
    )
    pcg_errors = validate_resonant_pcg_plan(pcg)
    pcg_path = output / "pcg_plan.json"
    _write_json(pcg_path, pcg)

    proof = build_proof_handoff(pcg, source_path=pcg_path)
    proof_errors = validate_proof_handoff(proof)
    proof_path = output / "proof_handoff.json"
    _write_json(proof_path, {**proof, "validation_errors": proof_errors, "ok": not proof_errors})

    blender, blender_errors = _blender_handoff(
        blender_manifest_path,
        fbx_path=blender_fbx_path,
        blend_path=blender_blend_path,
    )
    errors = {
        "phrase": phrase_errors,
        "world": world_errors,
        "score": score_errors,
        "score_portfolio": score_portfolio_errors,
        "pcg": pcg_errors,
        "proof": proof_errors,
        "blender": blender_errors,
    }
    artifacts = {
        "midi": _path_record(midi),
        "phrase": _path_record(phrase_path),
        "world": _path_record(world_path),
        "score": _path_record(score_path),
        "score_portfolio": _path_record(score_portfolio_path),
        "pcg_plan": _path_record(pcg_path),
        "proof_handoff": _path_record(proof_path),
    }
    if blender.get("mesh"):
        artifacts["blender_obj"] = blender["mesh"]
    if blender.get("manifest"):
        artifacts["blender_manifest"] = blender["manifest"]
    if blender.get("fbx"):
        artifacts["blender_fbx"] = blender["fbx"]
    if blender.get("blend"):
        artifacts["blender_blend"] = blender["blend"]

    bundle = {
        "format": BUNDLE_FORMAT,
        "schema_version": 1,
        "bundle_version": BUNDLE_VERSION,
        "world": {
            "world_seed": int(world_seed),
            "movement_id": movement_id,
            "archetype_id": archetype_id,
            "radius": max(0, int(radius)),
            "chunk_count": len(world.get("chunks", [])),
            "pcg_hero_volume_count": int(pcg.get("hero_volume_count", 0)),
            "pcg_static_spec_count": int(pcg.get("static_spec_count", 0)),
            "score_count": int(score_portfolio.get("score_count", 0)),
        },
        "source": {
            "midi": artifacts["midi"],
            "generator_authority": "Content/Python + Tools/midi_to_voxel",
            "blender_authority": "Tools/BlenderAddons/melodia_studio",
        },
        "artifacts": artifacts,
        "blender": blender,
        "ue_import": {
            "required": True,
            "performed": False,
            "asset_kind": "StaticMesh",
            "source_fbx": blender.get("fbx"),
            "source_obj": blender.get("mesh"),
            "recommended_content_path": "/Game/_PROJECT/ResonantWorld/Offline/MelodiaMIDIEnvironment",
            "voxel_size_meters": 1.0,
            "voxel_size_centimeters": 100.0,
            "import_from_blender_only": True,
            "production_maps_touched": False,
            "gameplay_save_written": False,
        },
        "runtime_boundary": {
            "offline_only": True,
            "does_not_call_unreal": True,
            "does_not_apply_pcg": True,
            "does_not_write_gameplay_save": True,
            "does_not_modify_protected_maps": True,
        },
        "validation_errors": errors,
        "ok": not any(errors.values()),
    }
    _write_json(output / "bundle.json", bundle)
    return bundle


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--midi", type=Path, default=DEFAULT_MIDI)
    parser.add_argument("--seed", type=int, default=3900)
    parser.add_argument("--movement", default="petal_cantata")
    parser.add_argument("--archetype", default="SakuraDreamer")
    parser.add_argument("--radius", type=int, default=1)
    parser.add_argument("--atlas", type=Path, default=DEFAULT_ATLAS)
    parser.add_argument("--wardrobe", type=Path, default=DEFAULT_WARDROBE)
    parser.add_argument("--magic-passage", type=Path, default=DEFAULT_MAGIC_PASSAGE)
    parser.add_argument("--blender-manifest", type=Path)
    parser.add_argument("--blender-fbx", type=Path)
    parser.add_argument("--blender-blend", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    bundle = build_offline_world_bundle(
        midi_path=args.midi,
        output_dir=args.output,
        world_seed=args.seed,
        movement_id=args.movement,
        archetype_id=args.archetype,
        radius=args.radius,
        atlas_path=args.atlas,
        wardrobe_path=args.wardrobe,
        magic_passage_path=args.magic_passage,
        blender_manifest_path=args.blender_manifest,
        blender_fbx_path=args.blender_fbx,
        blender_blend_path=args.blender_blend,
    )
    print(json.dumps({
        "ok": bundle["ok"],
        "output": str(Path(args.output).resolve()),
        "seed": bundle["world"]["world_seed"],
        "movement": bundle["world"]["movement_id"],
        "chunks": bundle["world"]["chunk_count"],
        "hero_volume_specs": bundle["world"]["pcg_hero_volume_count"],
        "static_specs": bundle["world"]["pcg_static_spec_count"],
        "score_count": bundle["world"]["score_count"],
        "blender_validated": bundle["blender"]["validated"],
        "errors": bundle["validation_errors"],
    }, indent=2))
    return 0 if bundle["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
