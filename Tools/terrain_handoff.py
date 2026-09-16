"""Unified Melodia terrain-handoff contract (``melodia.terrain_handoff.v1``).

Converges the three terrain-authoring lanes onto one Mesh Terrain intake schema:

- **midi_voxel**   -- ``melodia_studio`` MIDI->heightfield lane, manifest written by
  ``gaea_erosion_processor.build_mesh_terrain_handoff``
  (``ue_handoff/handoff_manifest.json``, kind ``melodia_mesh_terrain_handoff``).
- **audio_gn_5_2** -- Blender 5.2 audio Geometry Nodes lane, written by
  ``Tools/audio_terrain_pipeline.py``
  (``*.audio_terrain_handoff.json``, schema ``melodia.audio_terrain_ue_handoff.v1``).
- **gaea**         -- Gaea 2 native graphs, contracts under ``Docs/WorldGen/GAEA_SETUP_*.json``
  (schema ``melodia.gaea_setup.v1``).

All three lanes already agree on the load-bearing facts (UE 5.8, target "Mesh Terrain",
100 cm/m import scale, ``classic_landscape_used: false``, ``/Game/`` namespace).  This module
makes that agreement explicit and verifiable: each lane keeps its native handoff as the
authoritative lane artifact, and emits a sibling ``terrain_handoff.json`` in the unified
schema as the cross-lane intake/validation surface.

Offline-safe and pure stdlib: no bpy, no unreal, no third-party packages.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

HANDOFF_SCHEMA = "melodia.terrain_handoff.v1"

LANES = ("midi_voxel", "audio_gn_5_2", "gaea")

NATIVE_SCHEMAS = {
    "midi_voxel": "melodia_mesh_terrain_handoff",
    "audio_gn_5_2": "melodia.audio_terrain_ue_handoff.v1",
    "gaea": "melodia.gaea_setup.v1",
}

MESH_TERRAIN_PLUGINS = [
    "MeshPartition",
    "MeshTerrainMode",
    "MeshPartitionWater",
    "PCGMeshPartitionInterop",
]

# Repository root of the checkout this module ships in.
REPO_ROOT = Path(__file__).resolve().parents[1]

_ARTIFACT_KEYS = ("mesh_obj", "heightfield_png16", "dressing_plan",
                  "handoff_manifest", "blend")


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(value: Any) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "")).strip("_") or "unnamed"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve_file(path: Any, repo_root: Optional[Path]) -> Path:
    p = Path(str(path))
    if not p.is_absolute():
        p = Path(repo_root or REPO_ROOT) / p
    return p


def _load_doc(data_or_path: Any) -> tuple[dict, Optional[str]]:
    """Load a lane handoff: returns (doc dict, source path or None)."""
    if isinstance(data_or_path, (str, Path)):
        p = Path(data_or_path)
        with p.open("r", encoding="utf-8") as stream:
            return json.load(stream), str(p)
    return data_or_path, None


# ----------------------------------------------------------------- lane sniffing

def detect_lane(data: Any) -> Optional[str]:
    """Return the lane id for a native lane handoff, or None if unrecognized."""
    if not isinstance(data, dict):
        return None
    schema = data.get("schema")
    if schema == NATIVE_SCHEMAS["audio_gn_5_2"]:
        return "audio_gn_5_2"
    if schema == NATIVE_SCHEMAS["gaea"]:
        return "gaea"
    if data.get("kind") == NATIVE_SCHEMAS["midi_voxel"]:
        return "midi_voxel"
    return None


# ------------------------------------------------------------------ converters

def from_audio_gn(data_or_path: Any) -> dict:
    """Convert a ``melodia.audio_terrain_ue_handoff.v1`` doc to the unified schema."""
    data, source_path = _load_doc(data_or_path)
    if data.get("schema") != NATIVE_SCHEMAS["audio_gn_5_2"]:
        raise ValueError("expected schema %r, got %r"
                         % (NATIVE_SCHEMAS["audio_gn_5_2"], data.get("schema")))
    cs = data.get("coordinate_system") or {}
    tg = data.get("tile_grid") or {}
    ue = data.get("ue") or {}
    artifacts = data.get("artifacts") or []
    source_audio = data.get("source_audio")
    if source_audio:
        ingest_id = _slug(Path(str(source_audio)).stem)
    else:
        ingest_id = _slug(data.get("blend") or "audio_terrain")

    builders = sorted({str(a.get("builder")) for a in artifacts if a.get("builder")})
    presets = sorted({str(a.get("preset")) for a in artifacts if a.get("preset")})
    sample_times = sorted({a.get("sample_time") for a in artifacts
                           if a.get("sample_time") is not None})
    bands = sorted({tuple(a.get("frequency_hz") or ()) for a in artifacts
                    if a.get("frequency_hz")})

    # Flatten fbx-bearing artifacts so the unified schema is self-describing.
    fbx_entries = []
    for a in artifacts:
        fbx = a.get("fbx")
        if not isinstance(fbx, dict):
            continue
        entry = {
            "path": fbx.get("path"),
            "bytes": fbx.get("bytes"),
            "sha256": fbx.get("sha256"),
        }
        for key in ("object", "builder", "preset", "sample_time", "tile",
                    "world_origin_m", "frequency_hz", "named_attributes"):
            if key in a:
                entry[key] = a[key]
        fbx_entries.append(entry)

    scale = cs.get("unreal_scale_cm_per_meter", 100.0)
    width = depth = None
    try:
        if tg.get("x") and tg.get("tile_size_m"):
            width = float(tg["x"]) * float(tg["tile_size_m"])
        if tg.get("y") and tg.get("tile_size_m"):
            depth = float(tg["y"]) * float(tg["tile_size_m"])
    except (TypeError, ValueError):
        pass
    origin = None
    if artifacts:
        o = artifacts[0].get("world_origin_m")
        if isinstance(o, (list, tuple)) and len(o) == 3:
            origin = [float(v) for v in o]

    return {
        "schema": HANDOFF_SCHEMA,
        "handoff_id": "audio_gn:%s" % ingest_id,
        "lane": "audio_gn_5_2",
        "created_utc": _now_utc(),
        "converted_from_schema": NATIVE_SCHEMAS["audio_gn_5_2"],
        "source": {
            "kind": "audio_wav",
            "path": source_audio,
            "preset": None,
            "provider": "Blender 5.2 GeometryNodes (Sample Sound Frequencies)",
            "builders": builders,
            "presets": presets,
        },
        "coordinate_system": {
            "source_units": "meters",
            "unreal_scale_cm_per_meter": scale,
            "description": cs.get("source"),
            "tile_grid": {
                "x": tg.get("x"),
                "y": tg.get("y"),
                "tile_size_m": tg.get("tile_size_m"),
            },
        },
        "extent": {
            "width_m": width,
            "depth_m": depth,
            "height_range_m": None,
            "target_resolution": None,
            "world_origin_m": origin,
        },
        "artifacts": {
            "mesh_obj": None,
            "heightfield_png16": None,
            "dressing_plan": None,
            "handoff_manifest": None,
            "masks": None,
            "mesh_fbx": fbx_entries or None,
            "blend": data.get("blend"),
        },
        "ue5_8": {
            "engine": ue.get("engine") or "5.8",
            "target": "Mesh Terrain",
            "asset_kind": ue.get("asset_kind"),
            "content_namespace": ue.get("recommended_content_path"),
            "classic_landscape_used": False,
            "mesh_terrain_import_scale_cm_per_m": scale,
            "required_plugins": list(MESH_TERRAIN_PLUGINS),
            "pcg_profile": None,
            "runtime_audio_authority": ue.get("runtime_audio_authority"),
        },
        "evidence": {
            "artifact_count": len(artifacts),
            "sample_times": sample_times,
            "frequency_bands": [list(b) for b in bands],
        },
        "provenance": {
            "generator": "audio_terrain_pipeline.py (audio_gn_5_2 lane)",
            "generator_schema": NATIVE_SCHEMAS["audio_gn_5_2"],
            "unified_schema": HANDOFF_SCHEMA,
            "converted_utc": _now_utc(),
            "source_doc": source_path,
        },
    }


def from_gaea_setup(data_or_path: Any) -> dict:
    """Convert a ``melodia.gaea_setup.v1`` contract to the unified schema."""
    data, source_path = _load_doc(data_or_path)
    if data.get("schema") != NATIVE_SCHEMAS["gaea"]:
        raise ValueError("expected schema %r, got %r"
                         % (NATIVE_SCHEMAS["gaea"], data.get("schema")))
    mb = data.get("musical_binding") or {}
    src = data.get("source") or {}
    gr = data.get("gaea_reference") or {}
    recipe = data.get("recipe") or {}
    outputs = data.get("outputs") or {}
    ue = data.get("ue5_8") or {}
    evidence = data.get("evidence") or {}

    open_extent = (recipe.get("output_extent_m")
                   or src.get("working_window_m")
                   or src.get("source_extent_m") or [])
    width = None
    depth = None
    if isinstance(open_extent, (list, tuple)) and len(open_extent) >= 2:
        width, depth = float(open_extent[0]), float(open_extent[1])
    scale = ue.get("mesh_terrain_import_scale_cm_per_m", 100.0)

    hrange = recipe.get("height_range_m")
    if isinstance(hrange, (list, tuple)):
        hrange = [float(v) for v in hrange]

    return {
        "schema": HANDOFF_SCHEMA,
        "handoff_id": "gaea:%s" % _slug(data.get("setup_id") or "unnamed"),
        "lane": "gaea",
        "created_utc": _now_utc(),
        "converted_from_schema": NATIVE_SCHEMAS["gaea"],
        "source": {
            "kind": "gaea_graph",
            "path": gr.get("path"),
            "preset": mb.get("midi_preset"),
            "provider": src.get("provider") or "Gaea %s" % gr.get("gaea_version"),
            "dataset": src.get("dataset"),
            "movement_id": mb.get("movement_id"),
            "dressing_style": mb.get("dressing_style"),
            "design_intent": mb.get("design_intent"),
        },
        "coordinate_system": {
            "source_units": src.get("source_units") or "meters",
            "unreal_scale_cm_per_meter": scale,
            "description": ue.get("gaea2unreal_role"),
            "tile_grid": None,
        },
        "extent": {
            "width_m": width,
            "depth_m": depth,
            "height_range_m": hrange,
            "target_resolution": recipe.get("target_resolution"),
            "world_origin_m": [0.0, 0.0, 0.0],
        },
        "artifacts": {
            "mesh_obj": outputs.get("mesh_obj"),
            "heightfield_png16": outputs.get("heightfield_png16"),
            "dressing_plan": None,
            "handoff_manifest": outputs.get("manifest"),
            "masks": list(outputs.get("masks")) if outputs.get("masks") else None,
            "mesh_fbx": None,
            "blend": None,
        },
        "ue5_8": {
            "engine": "5.8",
            "target": ue.get("target") or "Mesh Terrain",
            "asset_kind": None,
            "content_namespace": ue.get("content_namespace"),
            "classic_landscape_used": bool(ue.get("classic_landscape_used", False)),
            "mesh_terrain_import_scale_cm_per_m": scale,
            "required_plugins": list(MESH_TERRAIN_PLUGINS),
            "pcg_profile": ue.get("pcg_profile"),
            "runtime_audio_authority": None,
        },
        "evidence": {
            "setup_status": data.get("status"),
            "display_name": data.get("display_name"),
            "world_seed": data.get("world_seed"),
            "export_status": outputs.get("export_status"),
            "native_gaea_export_verified": evidence.get("native_gaea_export_verified"),
            "mesh_terrain_handoff_verified": evidence.get("mesh_terrain_handoff_verified"),
            "gates": list(data.get("gates")) if data.get("gates") else None,
        },
        "provenance": {
            "generator": "Docs/WorldGen GAEA_SETUP_*.json (gaea lane)",
            "generator_schema": NATIVE_SCHEMAS["gaea"],
            "unified_schema": HANDOFF_SCHEMA,
            "converted_utc": _now_utc(),
            "source_doc": source_path,
        },
    }


def from_midi_handoff(data_or_path: Any) -> dict:
    """Convert a ``melodia_mesh_terrain_handoff`` manifest to the unified schema."""
    data, source_path = _load_doc(data_or_path)
    if data.get("kind") != NATIVE_SCHEMAS["midi_voxel"]:
        raise ValueError("expected kind %r, got %r"
                         % (NATIVE_SCHEMAS["midi_voxel"], data.get("kind")))
    ue = data.get("ue") or {}
    arts = data.get("artifacts") or {}
    validation = data.get("validation") or {}
    hf = arts.get("heightfield") or {}
    dp = arts.get("dressing_plan") or {}
    reproj = validation.get("dressing_reprojection") or {}
    preset = _slug(data.get("preset_id") or "unnamed")
    scale = ue.get("import_scale_cm_per_meter", 100.0)

    return {
        "schema": HANDOFF_SCHEMA,
        "handoff_id": "midi_voxel:%s" % preset,
        "lane": "midi_voxel",
        "created_utc": _now_utc(),
        "converted_from_schema": (
            "%s (schema_version %s)" % (NATIVE_SCHEMAS["midi_voxel"],
                                        data.get("schema_version"))),
        "source": {
            "kind": "midi",
            "path": None,
            "preset": preset,
            "provider": "midi_voxel_v3 -> melodia_studio",
            "movement_id": None,
            "dressing_style": None,
        },
        "coordinate_system": {
            "source_units": "voxel_grid_units",
            "unreal_scale_cm_per_meter": scale,
            "description": None,
            "tile_grid": None,
        },
        "extent": {
            "width_m": None,
            "depth_m": None,
            "height_range_m": None,
            "target_resolution": None,
            "world_origin_m": None,
        },
        "artifacts": {
            "mesh_obj": None,
            "heightfield_png16": hf.get("path"),
            "dressing_plan": dp.get("path"),
            "handoff_manifest": None,
            "masks": None,
            "mesh_fbx": None,
            "blend": None,
        },
        "ue5_8": {
            "engine": "5.8",
            "target": ue.get("target") or "Mesh Terrain",
            "asset_kind": None,
            "content_namespace": ue.get("recommended_content_path"),
            "classic_landscape_used": bool(ue.get("classic_landscape_used", False)),
            "mesh_terrain_import_scale_cm_per_m": scale,
            "required_plugins": list(ue.get("required_plugins") or MESH_TERRAIN_PLUGINS),
            "pcg_profile": None,
            "runtime_audio_authority": None,
        },
        "evidence": {
            "pixel_dimensions": validation.get("pixel_dimensions"),
            "dressing_reprojection_items_updated": reproj.get("items_updated"),
        },
        "provenance": {
            "generator": "gaea_erosion_processor.build_mesh_terrain_handoff (midi_voxel lane)",
            "generator_schema": NATIVE_SCHEMAS["midi_voxel"],
            "unified_schema": HANDOFF_SCHEMA,
            "converted_utc": _now_utc(),
            "source_doc": source_path,
        },
    }


def convert_document(data: Any) -> dict:
    """Dispatch a native lane handoff to its unified-schema converter."""
    lane = detect_lane(data)
    if lane == "audio_gn_5_2":
        return from_audio_gn(data)
    if lane == "gaea":
        return from_gaea_setup(data)
    if lane == "midi_voxel":
        return from_midi_handoff(data)
    raise ValueError("no converter for schema %r / kind %r"
                     % (data.get("schema") if isinstance(data, dict) else None,
                        data.get("kind") if isinstance(data, dict) else None))


# ---------------------------------------------------------------- validation

def validate_handoff(doc: Any,
                     strict_files: bool = False,
                     repo_root: Optional[Path] = None) -> dict:
    """Validate a unified-handoff document against ``melodia.terrain_handoff.v1``.

    Returns ``{"ok": bool, "errors": [...], "warnings": [...]}``.  ``strict_files``
    additionally requires referenced artifact files to exist on disk (with byte
    size / SHA-256 checks for ``mesh_fbx``); pending Gaea exports are exempt
    because their files are intentionally not produced yet.
    """
    if isinstance(doc, (str, Path)):
        doc, _ = _load_doc(doc)
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(doc, dict):
        return {"ok": False, "errors": ["handoff must be a JSON object"],
                "warnings": warnings}

    if doc.get("schema") != HANDOFF_SCHEMA:
        errors.append("schema must be %r, got %r"
                      % (HANDOFF_SCHEMA, doc.get("schema")))
    lane = doc.get("lane")
    if lane not in LANES:
        errors.append("lane must be one of %s, got %r" % (LANES, lane))

    source = doc.get("source")
    if not isinstance(source, dict) or not source.get("kind"):
        errors.append("source.kind is required")

    cs = doc.get("coordinate_system")
    if not isinstance(cs, dict):
        errors.append("coordinate_system must be an object")
    else:
        scale = cs.get("unreal_scale_cm_per_meter")
        if scale not in (100, 100.0):
            errors.append("unreal_scale_cm_per_meter must be 100.0, got %r" % (scale,))
        tg = cs.get("tile_grid")
        if tg is not None and not isinstance(tg, dict):
            errors.append("coordinate_system.tile_grid must be an object or null")

    ue = doc.get("ue5_8")
    if not isinstance(ue, dict):
        errors.append("ue5_8 must be an object")
    else:
        if ue.get("engine") != "5.8":
            errors.append("ue5_8.engine must be '5.8', got %r" % (ue.get("engine"),))
        if ue.get("target") != "Mesh Terrain":
            errors.append("ue5_8.target must be 'Mesh Terrain', got %r"
                          % (ue.get("target"),))
        namespace = ue.get("content_namespace") or ""
        if not namespace.startswith("/Game/"):
            errors.append("ue5_8.content_namespace must start with /Game/, got %r"
                          % (namespace,))
        if ue.get("classic_landscape_used") is not False:
            errors.append("ue5_8.classic_landscape_used must be false "
                          "for a Mesh Terrain target")

    arts = doc.get("artifacts")
    if not isinstance(arts, dict):
        errors.append("artifacts must be an object")
    else:
        present = any(arts.get(key) for key in _ARTIFACT_KEYS)
        fbx = arts.get("mesh_fbx")
        if isinstance(fbx, list) and fbx:
            present = True
        if not present:
            errors.append("artifacts must carry at least one path or mesh_fbx entry")

    if strict_files:
        root = Path(repo_root) if repo_root else REPO_ROOT
        pending = False
        evidence = doc.get("evidence")
        if isinstance(evidence, dict):
            for key in ("export_status", "setup_status"):
                value = str(evidence.get(key) or "")
                if value.startswith("pending") or ("pending" in value and "export" in value):
                    pending = True
                    break
        if not pending:
            if not isinstance(arts, dict):
                arts = {}
            for key in _ARTIFACT_KEYS:
                value = arts.get(key)
                if isinstance(value, str) and value.strip():
                    resolved = _resolve_file(value, root)
                    if not resolved.is_file():
                        errors.append("artifact %s missing on disk: %s"
                                      % (key, value))
            fblist = arts.get("mesh_fbx")
            if isinstance(fblist, list):
                for index, entry in enumerate(fblist):
                    if not isinstance(entry, dict):
                        continue
                    path = entry.get("path")
                    if not isinstance(path, str) or not path.strip():
                        continue
                    fp = _resolve_file(path, root)
                    if not fp.is_file():
                        errors.append("mesh_fbx[%d] missing on disk: %s"
                                      % (index, path))
                        continue
                    try:
                        if entry.get("bytes") is not None:
                            expected = int(entry["bytes"])
                            if fp.stat().st_size != expected:
                                errors.append("mesh_fbx[%d] byte size mismatch: %s"
                                              % (index, path))
                        if entry.get("sha256") and _sha256(fp) != entry["sha256"]:
                            errors.append("mesh_fbx[%d] SHA-256 mismatch: %s"
                                          % (index, path))
                    except OSError as exc:
                        errors.append("mesh_fbx[%d] unreadable: %s" % (index, exc))

    return {"ok": not errors, "errors": errors, "warnings": warnings}


def emit_unified(doc: dict,
                 out_path: Any,
                 strict_files: bool = False,
                 repo_root: Optional[Path] = None) -> dict:
    """Write a unified handoff to ``out_path`` and return its validation report."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    report = validate_handoff(doc, strict_files=strict_files, repo_root=repo_root)
    report["path"] = str(out.resolve())
    return report


# ----------------------------------------------------------------------- CLI

def _expand(items: list[str]) -> list[str]:
    """Expand glob patterns in CLI file arguments (PowerShell does not glob)."""
    expanded: list[str] = []
    for item in items:
        if glob.has_magic(item):
            expanded.extend(sorted(glob.glob(item)))
        else:
            expanded.append(item)
    return expanded


def _cmd_validate(args: argparse.Namespace) -> int:
    files = _expand(list(args.files))
    if not files:
        print("no handoff files given")
        return 2
    bad = 0
    for path in files:
        try:
            doc, _ = _load_doc(path)
        except Exception as exc:
            print("ERROR %s: unreadable: %r" % (path, exc))
            bad += 1
            continue
        report = validate_handoff(doc, strict_files=args.strict)
        if report["ok"]:
            print("PASS %s" % path)
        else:
            bad += 1
            print("FAIL %s" % path)
            for error in report["errors"]:
                print("    - %s" % error)
    print("%d passed, %d failed" % (len(files) - bad, bad))
    return 1 if bad else 0


def _unified_name(src_path: Any) -> str:
    """Emitted sibling filename: strip a trailing ``.audio_terrain_handoff`` so the
    unified file is named ``<source>.terrain_handoff.json`` consistently across
    lanes (same stem as the native handoff's sibling suffix)."""
    stem = Path(src_path).stem
    suffix = ".audio_terrain_handoff"
    if stem.endswith(suffix):
        stem = stem[: -len(suffix)]
    return stem + ".terrain_handoff.json"


def _cmd_convert(args: argparse.Namespace) -> int:
    files = _expand(list(args.files))
    if not files:
        print("no lane handoff files given")
        return 2
    bad = 0
    for path in files:
        try:
            doc, _ = _load_doc(path)
            lane = detect_lane(doc)
            if lane is None:
                raise ValueError("not a terrain lane handoff "
                                 "(expected one of %s)" % (NATIVE_SCHEMAS.values(),))
            unified = convert_document(doc)
            if args.out_dir:
                out = Path(args.out_dir) / _unified_name(path)
            else:
                out = Path(path).with_name(_unified_name(path))
            report = emit_unified(unified, out)
            if not report["ok"]:
                raise ValueError("; ".join(report["errors"]))
            print("OK %s -> %s [%s]" % (os_path(path), os_path(str(out)), lane))
        except Exception as exc:
            bad += 1
            print("FAIL %s: %r" % (path, exc))
    print("%d converted, %d failed" % (len(files) - bad, bad))
    return 1 if bad else 0


def _cmd_convert_batch(args: argparse.Namespace) -> int:
    pattern = "*.json" if not args.recursive else "**/*.json"
    hits = [p for p in Path(args.dir).glob(pattern) if p.is_file()]
    converted = bad = skipped = 0
    for path in hits:
        try:
            doc, _ = _load_doc(path)
        except Exception:
            skipped += 1
            continue
        if detect_lane(doc) is None:
            skipped += 1
            continue
        try:
            unified = convert_document(doc)
            out_dir = Path(args.out_dir) if args.out_dir else path.parent
            out = out_dir / _unified_name(path)
            report = emit_unified(unified, out)
            if not report["ok"]:
                raise ValueError("; ".join(report["errors"]))
            converted += 1
            if args.verbose:
                print("OK %s -> %s" % (os_path(str(path)), os_path(str(out))))
        except Exception as exc:
            bad += 1
            print("FAIL %s: %r" % (path, exc))
    print("converted=%d failed=%d skipped=%d" % (converted, bad, skipped))
    return 1 if bad else 0


def os_path(path: Any) -> str:
    """Print path using the OS separator (cosmetic only)."""
    return str(path)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="terrain_handoff",
        description="Unified Melodia terrain handoff (melodia.terrain_handoff.v1): "
                    "convert, validate and index the midi_voxel / audio_gn_5_2 / gaea "
                    "terrain-authoring lanes onto one Mesh Terrain intake schema.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub_validate = sub.add_parser("validate", help="validate unified handoff documents")
    sub_validate.add_argument("files", nargs="+", help="path(s) or glob to terrain_handoff.json")
    sub_validate.add_argument("--strict", action="store_true",
                              help="also require referenced artifact files on disk")
    sub_validate.set_defaults(func=_cmd_validate)

    sub_convert = sub.add_parser("convert", help="convert native lane handoffs to the unified schema")
    sub_convert.add_argument("files", nargs="+",
                             help="native lane handoff(s) or glob (lane schema is auto-detected)")
    sub_convert.add_argument("--out-dir", default=None,
                             help="directory for the emitted terrain_handoff.json (default: beside source)")
    sub_convert.set_defaults(func=_cmd_convert)

    sub_batch = sub.add_parser("convert-batch", help="convert every lane handoff found in a directory")
    sub_batch.add_argument("--dir", required=True, help="directory to scan for lane handoffs")
    sub_batch.add_argument("--recursive", action="store_true")
    sub_batch.add_argument("--out-dir", default=None)
    sub_batch.add_argument("--verbose", action="store_true")
    sub_batch.set_defaults(func=_cmd_convert_batch)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())