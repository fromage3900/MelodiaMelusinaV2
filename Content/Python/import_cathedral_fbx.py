# -*- coding: utf-8 -*-
"""Import KitbashExport/CathedralKit FBXs into /Game/EnvSandbox/Meshes/Cathedral/.

Closes the P0 KaleidoNave gap: 41 SM_Cathedral_*.fbx, 0 uassets on disk.

Run in the already-open Unreal Editor (do not spawn UnrealEditor-Cmd):
  py Content/Python/import_cathedral_fbx.py
  py Content/Python/import_cathedral_fbx.py --only SM_Cathedral_VaultBay,SM_Cathedral_Portal

automated=True so the FBX dialog cannot MODAL_OPEN the editor.
Does not load or save L_KaleidoNave. Placement is a separate pass.
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

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FBX_DIR = PROJECT_ROOT / "KitbashExport" / "CathedralKit"
AUDIT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "cathedral_fbx_import.json"
DEST = "/Game/EnvSandbox/Meshes/Cathedral"


def _log(msg: str) -> None:
    line = f"[cathedral-import] {msg}"
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
        entry["ok"] = bool(imported) or bool(unreal.load_asset(f"{dest_path}/{fbx_path.stem}"))
        if not entry["ok"]:
            entry["error"] = "import_returned_empty"
    except Exception as exc:
        entry["error"] = str(exc)
        _log(f"FAIL {fbx_path.name}: {exc}")
    return entry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import Cathedral kit FBXs")
    parser.add_argument("--only", default=None, help="Comma-separated SM_Cathedral_* stems")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    if unreal is None:
        print(
            "[cathedral-import] FATAL: unreal module missing. Run inside UE Editor:\n"
            "  py Content/Python/import_cathedral_fbx.py",
            flush=True,
        )
        return 2

    only = _parse_only(args.only)
    fbx_files = sorted(FBX_DIR.glob("SM_Cathedral_*.fbx"))
    if only:
        fbx_files = [
            p
            for p in fbx_files
            if p.stem in only or p.name in only
        ]

    _log(f"FBX_DIR={FBX_DIR} DEST={DEST} count={len(fbx_files)}")
    if args.dry_run:
        for p in fbx_files:
            _log(f"DRY {p.stem} exists={p.is_file()} bytes={p.stat().st_size}")
        return 0

    results = []
    for fbx in fbx_files:
        row = _import_one(fbx, DEST)
        row["asset_name"] = fbx.stem
        results.append(row)
        _log(f"{'OK' if row['ok'] else 'FAIL'} {fbx.stem}: {row.get('error') or row.get('imported_paths')}")

    audit = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "import_cathedral_fbx.py",
        "fbx_dir": str(FBX_DIR),
        "dest": DEST,
        "ok": all(r.get("ok") for r in results) and bool(results),
        "imported": sum(1 for r in results if r.get("ok")),
        "total": len(results),
        "meshes": results,
        "note": "Assets only. Did not load or save L_KaleidoNave.",
    }
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    _log(f"audit → {AUDIT_PATH} ok={audit['ok']} {audit['imported']}/{audit['total']}")
    return 0 if audit["ok"] else 1


if __name__ == "__main__":
    raw = sys.argv[1:]
    if "--" in raw:
        raw = raw[raw.index("--") + 1 :]
    raise SystemExit(main(raw))
