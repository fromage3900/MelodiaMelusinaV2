# -*- coding: utf-8 -*-
"""Import Melusina updated meshes as V2 test copies. Does NOT replace live SK.

PORTFOLIO / CINE ONLY. SM_MelusinaBase/Shirt/Skirt/Boots/Accessories/Hair/Hair1
land as STATIC meshes under SK_MelusinaRigARP_V2Test — a separate ARP skeleton
(dotted names, meters), NOT SK_Melusina_Skeleton. Do not switch gameplay to
these pieces (would force a retarget/redirector). Gameplay path is wardrobe
re-skin onto SK_Melusina_Skeleton + SetLeaderPoseComponent.
See Saved/Audit/melusina_idle_retarget_rca_2026-08-13.md.

Source: G:\\MelusinaRigFinalSeparate\\*.fbx
Dest:   /Game/Melodia/Characters/Melusina/V2Test/*_V2Test

replace_existing=False. Does not touch:
  /Game/Melodia/Characters/Melusina/SK_Melusina
  /Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair

Do not re-import SK_MelusinaRigARP.fbx (~33 MB Interchange hang) unless
--include-rig. This file is not a Lane A animation importer.
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
SRC_DIR = Path(r"G:\MelusinaRigFinalSeparate")
DEST = "/Game/Melodia/Characters/Melusina/V2Test"
AUDIT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "melusina_v2_test_import.json"
FOLDER = "Melusina_V2Test"
# Offset from CathedralKit_Review (Y=4500) so both review strips are visible.
ORIGIN = (0.0, 5200.0, 0.0)
SPACING = 180.0

# Static pieces first. SK_MelusinaRigARP is 33 MB ARP and Interchange-blocks the
# editor for many minutes — opt in with --include-rig. Never overwrite live SK.
FBX_FILES = [
    "SM_MelusinaBase.fbx",
    "SM_MelusinaShirt.fbx",
    "SM_MelusinaSkirt.fbx",
    "SM_MelusinaBoots.fbx",
    "SM_MelusinaAccessories.fbx",
    "SM_MelusinaHair.fbx",
    "SM_MelusinaHair1.fbx",
]
RIG_FBX = "SK_MelusinaRigARP.fbx"


def _log(msg: str) -> None:
    line = f"[melusina-v2] {msg}"
    if unreal:
        unreal.log(line)
    print(line, flush=True)


LIVE_DUPES = [
    ("/Game/Melodia/Characters/Melusina/SK_Melusina", "SK_Melusina_V2Test"),
    ("/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair", "SK_MelusinaHair_V2Test"),
    ("/Game/Melodia/Characters/Melusina/SK_Melusina_FIXED_Hair", "SK_Melusina_FIXED_Hair_V2Test"),
]


def duplicate_live_heroes() -> list[dict]:
    """Copy live SK assets into V2Test. Does not overwrite the source packages."""
    out = []
    for src, name in LIVE_DUPES:
        dest = f"{DEST}/{name}"
        row = {"src": src, "dest": dest, "ok": False}
        if not unreal.EditorAssetLibrary.does_asset_exist(src):
            row["error"] = "src_missing"
            out.append(row)
            continue
        if unreal.EditorAssetLibrary.does_asset_exist(dest):
            row["ok"] = True
            row["skipped"] = "already_exists_v2test"
            out.append(row)
            continue
        copied = unreal.EditorAssetLibrary.duplicate_asset(src, dest)
        row["ok"] = bool(copied) or unreal.EditorAssetLibrary.does_asset_exist(dest)
        if row["ok"]:
            try:
                unreal.EditorAssetLibrary.save_asset(dest)
            except Exception:
                pass
        else:
            row["error"] = "duplicate_failed"
        out.append(row)
        _log(f"{'OK' if row['ok'] else 'FAIL'} dupe {src} -> {dest}")
    return out
    if stem.endswith("_V2Test"):
        return stem
    return f"{stem}_V2Test"


def _import_one(fbx_path: Path) -> dict:
    dest_name = _dest_name(fbx_path.stem)
    game_path = f"{DEST}/{dest_name}"
    entry = {
        "fbx": str(fbx_path),
        "dest": game_path,
        "skeletal": fbx_path.name.startswith("SK_"),
        "ok": False,
        "error": None,
    }
    if not fbx_path.is_file():
        entry["error"] = "missing_fbx"
        return entry
    if unreal.EditorAssetLibrary.does_asset_exist(game_path):
        entry["ok"] = True
        entry["skipped"] = "already_exists_v2test"
        return entry
    if dest_name in ("SK_Melusina", "SK_MelusinaHair") or DEST.rstrip("/") == "/Game/Melodia/Characters/Melusina":
        entry["error"] = "refused_live_path"
        return entry

    skeletal = entry["skeletal"]
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(fbx_path))
    task.set_editor_property("destination_path", DEST)
    task.set_editor_property("destination_name", dest_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", False)

    try:
        options = unreal.FbxImportUI()
        options.set_editor_property("import_mesh", True)
        options.set_editor_property("import_as_skeletal", skeletal)
        options.set_editor_property("import_animations", False)
        options.set_editor_property("import_materials", False)
        options.set_editor_property("import_textures", False)
        options.set_editor_property("automated_import_should_detect_type", False)
        if skeletal:
            options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
            options.set_editor_property("create_physics_asset", False)
            try:
                options.set_editor_property("skeleton", None)
            except Exception:
                pass
            sk = options.get_editor_property("skeletal_mesh_import_data")
            if sk:
                sk.set_editor_property("import_morph_targets", True)
                sk.set_editor_property("convert_scene", True)
                sk.set_editor_property("force_front_x_axis", False)
                sk.set_editor_property("import_uniform_scale", 1.0)
        else:
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
        _log(f"WARN FbxImportUI: {exc}")

    try:
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        imported = list(task.get_editor_property("imported_object_paths") or [])
        entry["imported_paths"] = imported
        loaded = unreal.load_asset(game_path)
        entry["loaded_class"] = str(loaded.get_class().get_name()) if loaded else None
        entry["ok"] = bool(imported) or bool(loaded)
        if not entry["ok"]:
            entry["error"] = "import_returned_empty"
        if loaded and "SK_Melusina." in str(loaded.get_path_name()) and "V2Test" not in str(loaded.get_path_name()):
            entry["ok"] = False
            entry["error"] = "landed_on_live_sk_melusina"
    except Exception as exc:
        entry["error"] = str(exc)
        _log(f"FAIL {fbx_path.name}: {exc}")
    return entry


def spawn_review_strip(imported: list[dict]) -> dict:
    eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    existing = []
    for actor in eas.get_all_level_actors() or []:
        try:
            if str(actor.get_folder_path()) == FOLDER:
                existing.append(str(actor.get_actor_label()))
        except Exception:
            pass
    if existing:
        return {"skipped": True, "existing": existing}

    spawned = []
    ox, oy, oz = ORIGIN
    i = 0
    for row in imported:
        if not row.get("ok"):
            continue
        path = row["dest"]
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if not asset:
            spawned.append({"dest": path, "ok": False, "error": "load_failed"})
            continue
        loc = unreal.Vector(ox + i * SPACING, oy, oz)
        cls_name = asset.get_class().get_name()
        if cls_name == "SkeletalMesh":
            actor = eas.spawn_actor_from_class(unreal.SkeletalMeshActor, loc, unreal.Rotator(0, 0, 0))
            if actor:
                skc = actor.skeletal_mesh_component
                try:
                    skc.set_editor_property("skeletal_mesh_asset", asset)
                except Exception:
                    skc.set_editor_property("skeletal_mesh", asset)
        else:
            actor = eas.spawn_actor_from_class(unreal.StaticMeshActor, loc, unreal.Rotator(0, 0, 0))
            if actor:
                actor.static_mesh_component.set_editor_property("static_mesh", asset)
        label = f"V2 test — {Path(path).name}"
        if actor:
            actor.set_actor_label(label)
            actor.set_folder_path(FOLDER)
            spawned.append({"label": label, "ok": True, "loc": [loc.x, loc.y, loc.z], "class": cls_name})
        else:
            spawned.append({"dest": path, "ok": False, "error": "spawn_failed"})
        i += 1
    return {"skipped": False, "saved_map": False, "folder": FOLDER, "spawned": spawned}


def main() -> int:
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "generated_by": "import_melusina_v2_test.py",
        "src": str(SRC_DIR),
        "dest": DEST,
        "ok": False,
        "live_untouched": [
            "/Game/Melodia/Characters/Melusina/SK_Melusina",
            "/Game/Melodia/Characters/Melusina/Hair/SK_MelusinaHair",
        ],
    }
    if unreal is None:
        payload["error"] = "not_in_unreal"
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        AUDIT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, indent=2), flush=True)
        return 2

    unreal.EditorAssetLibrary.make_directory(DEST)
    dupes = duplicate_live_heroes()
    results = []
    for name in FBX_FILES:
        row = _import_one(SRC_DIR / name)
        results.append(row)
        _log(f"{'OK' if row['ok'] else 'FAIL'} {name}: {row.get('error') or row.get('loaded_class') or row.get('skipped')}")

    payload["dupes"] = dupes
    payload["meshes"] = results
    payload["imported"] = sum(1 for r in results if r.get("ok")) + sum(1 for r in dupes if r.get("ok"))
    payload["total"] = len(results) + len(dupes)
    payload["ok"] = payload["imported"] == payload["total"] and payload["total"] > 0
    payload["place"] = spawn_review_strip(dupes + results)
    payload["note"] = (
        "V2 test copies only. Live SK_Melusina / SK_MelusinaHair not replaced. "
        "Level actors labeled 'V2 test — …' in folder Melusina_V2Test. Umap not saved."
    )
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    AUDIT_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2), flush=True)
    _log(f"audit {AUDIT_PATH} ok={payload['ok']} {payload['imported']}/{payload['total']}")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
