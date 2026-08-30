"""Validate or apply the isolated Melodia Studio v3 WorldGen UE handoff.

Offline validation is the default.  --apply must run inside the one authorized
Unreal Editor Python session and creates only /Game/MelodiaStudioV3/Review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

SCHEMA = "melodia.planetary_terrain_ue_handoff.v3"
ROOT = "/Game/MelodiaStudioV3/Review/WorldGen"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(path):
    data = json.loads(Path(path).read_text(encoding="utf-8")); errors = []; seen = set()
    if data.get("schema") != SCHEMA: errors.append("schema mismatch")
    if data.get("ue", {}).get("content_root") != ROOT: errors.append("non-isolated content root")
    for index, row in enumerate(data.get("artifacts", [])):
        identity = (row.get("generator"), row.get("preset"), row.get("sample_time"), json.dumps(row.get("tile"), sort_keys=True))
        if identity in seen: errors.append(f"artifact[{index}] duplicate identity")
        seen.add(identity); fbx = row.get("fbx", {}); file = Path(str(fbx.get("path", "")))
        if not file.is_file(): errors.append(f"artifact[{index}] missing FBX"); continue
        if file.stat().st_size != fbx.get("bytes") or sha(file) != fbx.get("sha256"): errors.append(f"artifact[{index}] integrity mismatch")
        if not str(row.get("ue_destination", "")).startswith(ROOT + "/"): errors.append(f"artifact[{index}] destination escape")
    if not data.get("artifacts"): errors.append("no artifacts")
    return {"ok": not errors, "errors": errors, "data": data, "artifacts": len(data.get("artifacts", []))}


def apply(report):
    if not report["ok"]: raise RuntimeError("refusing failed handoff")
    import unreal
    tasks = []
    for row in report["data"]["artifacts"]:
        options = unreal.FbxImportUI(); options.set_editor_property("import_mesh", True); options.set_editor_property("import_as_skeletal", False)
        options.set_editor_property("import_materials", False); options.set_editor_property("import_textures", False)
        options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
        task = unreal.AssetImportTask(); task.set_editor_property("filename", row["fbx"]["path"])
        task.set_editor_property("destination_path", row["ue_destination"]); task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", True); task.set_editor_property("save", True); task.set_editor_property("options", options); tasks.append(task)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    imported = [p for task in tasks for p in task.get_editor_property("imported_object_paths")]
    if len(imported) != len(tasks): raise RuntimeError(f"import count mismatch: {len(imported)}/{len(tasks)}")
    map_path = report["data"]["ue"]["review_map"]
    unreal.EditorLevelLibrary.new_level(map_path)
    for index, asset_path in enumerate(imported):
        asset = unreal.load_asset(asset_path); actor = unreal.EditorLevelLibrary.spawn_actor_from_object(asset, unreal.Vector((index % 4) * 60000, (index // 4) * 60000, 0))
        actor.set_actor_label(f"V3_{index:02d}_{asset.get_name()}")
    unreal.EditorLevelLibrary.save_current_level()
    if not unreal.EditorAssetLibrary.does_asset_exist(map_path): raise RuntimeError("review map did not persist")
    return {"ok": True, "imported": imported, "review_map": map_path}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("manifest"); parser.add_argument("--apply", action="store_true"); args = parser.parse_args()
    report = validate(args.manifest); printable = {k: v for k, v in report.items() if k != "data"}
    if args.apply: printable["apply"] = apply(report)
    print(json.dumps(printable, indent=2)); return 0 if report["ok"] else 1


if __name__ == "__main__": raise SystemExit(main())
