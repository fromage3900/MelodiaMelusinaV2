# -*- coding: utf-8 -*-
"""Import KitbashExport ornament FBXs into /Game/EnvSandbox/Meshes/Ornament/.

Closes the Blender → UE gap from the ornament sculpt handoff:
  KitbashExport/OrnamentalMeshes/SM_Orn_*.fbx  →  /Game/EnvSandbox/Meshes/Ornament/

Run in Unreal Editor:
  py Content/Python/import_ornament_fbx.py
  py Content/Python/import_ornament_fbx.py --prep
  py Content/Python/import_ornament_fbx.py --only SM_Orn_VaultRibs,SM_Orn_TorusKnot

Does NOT use Live Link (/Game/LiveLink/). Sellable / gameplay path only.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import unreal
except ImportError:
    unreal = None  # type: ignore

from ornament_kitbash_catalog import MESHES as GOTHIC_MESHES, ORNAMENT_DIR as GOTHIC_DIR

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FBX_DIR = PROJECT_ROOT / "KitbashExport" / "OrnamentalMeshes"
AUDIT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "ornament_fbx_import.json"
DEST = GOTHIC_DIR  # /Game/EnvSandbox/Meshes/Ornament
MESHES = GOTHIC_MESHES


def _log(msg: str) -> None:
    line = f"[orn-import] {msg}"
    if unreal:
        unreal.log(line)
    print(line, flush=True)


def _parse_only(raw: str | None) -> set[str] | None:
    if not raw:
        return None
    return {x.strip() for x in raw.split(",") if x.strip()}


def _import_one(fbx_path: Path, dest_path: str) -> dict:
    entry = {
        "fbx": str(fbx_path),
        "dest": f"{dest_path}/{fbx_path.stem}",
        "ok": False,
        "error": None,
    }
    if not fbx_path.is_file():
        entry["error"] = "missing_fbx"
        return entry

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(fbx_path))
    task.set_editor_property("destination_path", dest_path)
    task.set_editor_property("destination_name", fbx_path.stem)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)

    # Static mesh only — no skeletal / anim
    try:
        options = unreal.FbxImportUI()
        options.set_editor_property("import_mesh", True)
        options.set_editor_property("import_as_skeletal", False)
        options.set_editor_property("import_animations", False)
        options.set_editor_property("import_materials", False)
        options.set_editor_property("import_textures", False)
        options.set_editor_property("automated_import_should_detect_type", False)
        options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
        sm = options.get_editor_property("static_mesh_import_data")
        if sm:
            sm.set_editor_property("combine_meshes", True)
            sm.set_editor_property("auto_generate_collision", True)
            sm.set_editor_property("convert_scene", True)
            sm.set_editor_property("force_front_x_axis", False)
            sm.set_editor_property("import_uniform_scale", 1.0)
        task.set_editor_property("options", options)
    except Exception as exc:
        _log(f"WARN FbxImportUI setup: {exc}")

    try:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        tools.import_asset_tasks([task])
        imported = list(task.get_editor_property("imported_object_paths") or [])
        entry["imported_paths"] = imported
        entry["ok"] = bool(imported) or bool(
            unreal.load_asset(f"{dest_path}/{fbx_path.stem}")
        )
        if not entry["ok"]:
            entry["error"] = "import_returned_empty"
    except Exception as exc:
        entry["error"] = str(exc)
        _log(f"FAIL {fbx_path.name}: {exc}")
    return entry


def _prep_imported(asset_names: list[str]) -> list[dict]:
    """Re-apply LOD / collision / Base+Trim slots after FBX replace."""
    from kitbash_prep_meshes import setup_collision, setup_lods, setup_material_slots

    results = []
    for name in asset_names:
        path = f"{DEST}/{name}"
        mesh = unreal.load_asset(path)
        row = {"asset": path, "lod_ok": False, "collision_ok": False, "materials_ok": False}
        if not mesh:
            row["error"] = "asset_missing"
            results.append(row)
            continue
        row["lod_ok"] = setup_lods(mesh, num_lods=3)
        row["collision_ok"] = setup_collision(mesh)
        row["materials_ok"] = setup_material_slots(mesh)
        try:
            unreal.EditorAssetLibrary.save_asset(path)
        except Exception:
            pass
        results.append(row)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import ornament FBXs into UE Ornament folder")
    parser.add_argument(
        "--only",
        default=None,
        help="Comma-separated SM_Orn_* asset names (or stems)",
    )
    parser.add_argument(
        "--prep",
        action="store_true",
        help="After import, re-apply LODs + collision + Base/Trim slots",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List planned imports without touching assets",
    )
    parser.add_argument(
        "--musical",
        action="store_true",
        help="Import musical kitbash (7 meshes) into OrnamentMusical instead of gothic 15",
    )
    args = parser.parse_args(argv)

    global MESHES, FBX_DIR, DEST, AUDIT_PATH
    if args.musical:
        from musical_ornament_kitbash_catalog import (
            FBX_EXPORT_DIR,
            MESHES as MUSICAL_MESHES,
            ORNAMENT_DIR as MUSICAL_DIR,
        )

        MESHES = MUSICAL_MESHES
        FBX_DIR = FBX_EXPORT_DIR
        DEST = MUSICAL_DIR
        AUDIT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "musical_ornament_fbx_import.json"

    if unreal is None:
        print(
            "[orn-import] FATAL: unreal module missing. Run inside UE Editor:\n"
            "  py Content/Python/import_ornament_fbx.py\n"
            "  py Content/Python/import_ornament_fbx.py --musical --prep",
            flush=True,
        )
        return 2

    only = _parse_only(args.only)
    planned = []
    for mesh in MESHES:
        stem = mesh.asset_name
        if only and stem not in only and f"{stem}.fbx" not in only:
            continue
        planned.append(mesh)

    _log(f"FBX_DIR={FBX_DIR} DEST={DEST} count={len(planned)} prep={args.prep}")

    if args.dry_run:
        for m in planned:
            fbx = FBX_DIR / m.fbx_name
            _log(f"DRY {m.asset_name} ← {fbx} exists={fbx.is_file()}")
        return 0

    results = []
    ok_names: list[str] = []
    for m in planned:
        fbx = FBX_DIR / m.fbx_name
        row = _import_one(fbx, DEST)
        row["asset_name"] = m.asset_name
        results.append(row)
        if row["ok"]:
            ok_names.append(m.asset_name)
            _log(f"OK {m.asset_name}")
        else:
            _log(f"FAIL {m.asset_name}: {row.get('error')}")

    prep_results = []
    if args.prep and ok_names:
        _log(f"prep LODs/collision/slots for {len(ok_names)} meshes")
        prep_results = _prep_imported(ok_names)

    audit = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "import_ornament_fbx.py",
        "fbx_dir": str(FBX_DIR),
        "dest": DEST,
        "ok": all(r.get("ok") for r in results) and bool(results),
        "imported": sum(1 for r in results if r.get("ok")),
        "total": len(results),
        "meshes": results,
        "prep": prep_results,
    }
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    _log(f"audit → {AUDIT_PATH} ok={audit['ok']} {audit['imported']}/{audit['total']}")
    return 0 if audit["ok"] else 1


if __name__ == "__main__":
    # UE `py` may pass extra args after --
    raw = sys.argv[1:]
    if "--" in raw:
        raw = raw[raw.index("--") + 1 :]
    raise SystemExit(main(raw))
