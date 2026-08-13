# -*- coding: utf-8 -*-
"""Import Flip Fluids Alembic as a Geometry Cache cine asset (Layer C).

Does NOT:
  - replace SK_MelusinaHair / MI_Melusina_WaterHair / ABP_Melusina_WaterHair
  - spawn into the currently loaded gameplay map
  - launch a second UnrealEditor

Source ABC (already cm via Blender global_scale=100):
  G:\\EnvironmentPortfolio\\BS_GodFile\\Exports\\MelusinaWaterHair\\GC_MelusinaHairFlip_v22.abc

In already-open editor:
  py Content/Python/import_hair_flip_geometry_cache.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import unreal
except ImportError:
    unreal = None  # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ABC_CANDIDATES = [
    Path(r"G:\EnvironmentPortfolio\BS_GodFile\Exports\MelusinaWaterHair\GC_MelusinaHairFlip_v22.abc"),
    PROJECT_ROOT / "Exports" / "MelusinaWaterHair" / "GC_MelusinaHairFlip_v22.abc",
]
DEST = "/Game/Cinematics/MelusinaWaterHair"
ASSET_NAME = "GC_MelusinaHairFlip_v22"
AUDIT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "hair_flip_geometry_cache_import.json"
FRAME_START = 1
FRAME_END = 96


def _log(msg: str) -> None:
    line = f"[hair-gc-import] {msg}"
    if unreal:
        unreal.log(line)
    print(line, flush=True)


def _abc_path() -> Path | None:
    for p in ABC_CANDIDATES:
        if p.is_file():
            return p
    return None


def _configure_abc_settings():
    """Prefer AlembicImporter AbcImportSettings; return None if plugin/API missing."""
    settings = unreal.AbcImportSettings()
    import_type = getattr(unreal.AlembicImportType, "GEOMETRY_CACHE", None)
    if import_type is None:
        raise RuntimeError("AlembicImportType.GEOMETRY_CACHE missing — AlembicImporter plugin off?")
    settings.set_editor_property("import_type", import_type)

    sampling = settings.get_editor_property("sampling_settings")
    if sampling:
        sampling.set_editor_property("frame_start", FRAME_START)
        sampling.set_editor_property("frame_end", FRAME_END)
        try:
            sampling.set_editor_property("frame_steps", 1)
        except Exception:
            pass

    conv = settings.get_editor_property("conversion_settings")
    if conv:
        # ABC already exported in centimeters.
        try:
            conv.set_editor_property("scale", unreal.Vector(1.0, 1.0, 1.0))
        except Exception:
            pass

    gc = settings.get_editor_property("geometry_cache_settings")
    if gc:
        for prop, val in (
            ("flatten_tracks", True),
            ("apply_constant_topology_optimizations", True),
            ("compressed_position_precision", 0.01),
        ):
            try:
                gc.set_editor_property(prop, val)
            except Exception:
                pass
    return settings


def main() -> int:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "import_hair_flip_geometry_cache.py",
        "dest": f"{DEST}/{ASSET_NAME}",
        "ok": False,
    }
    if unreal is None:
        payload["error"] = "not_in_unreal"
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2), flush=True)
        return 2

    abc = _abc_path()
    payload["abc"] = str(abc) if abc else None
    if abc is None:
        payload["error"] = "abc_missing"
        payload["tried"] = [str(p) for p in ABC_CANDIDATES]
        AUDIT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        _log("FATAL missing ABC")
        print(json.dumps(payload, indent=2), flush=True)
        return 1

    payload["abc_bytes"] = abc.stat().st_size
    unreal.EditorAssetLibrary.make_directory(DEST)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(abc))
    task.set_editor_property("destination_path", DEST)
    task.set_editor_property("destination_name", ASSET_NAME)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)

    try:
        task.set_editor_property("options", _configure_abc_settings())
        payload["importer"] = "AbcImportSettings"
    except Exception as exc:
        payload["importer_warn"] = str(exc)
        _log(f"WARN AbcImportSettings: {exc}")

    try:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        tools.import_asset_tasks([task])
        imported = list(task.get_editor_property("imported_object_paths") or [])
        payload["imported_paths"] = imported
        loaded = unreal.load_asset(f"{DEST}/{ASSET_NAME}")
        payload["loaded_class"] = str(loaded.get_class().get_name()) if loaded else None
        payload["ok"] = bool(imported) or bool(loaded)
        if not payload["ok"]:
            payload["error"] = "import_returned_empty"
        if payload["loaded_class"] and "SkeletalMesh" in payload["loaded_class"]:
            payload["ok"] = False
            payload["error"] = "imported_as_skeletal_mesh_not_geometry_cache"
    except Exception as exc:
        payload["error"] = str(exc)
        _log(f"FAIL {exc}")

    payload["note"] = (
        "Cine Geometry Cache only. Leave SK_MelusinaHair + MI_Melusina_WaterHair "
        "+ ABP_Melusina_WaterHair as gameplay Layer A. Socket a new GeometryCacheActor to head."
    )
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _log(f"audit → {AUDIT_PATH} ok={payload['ok']}")
    print(json.dumps(payload, indent=2), flush=True)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
