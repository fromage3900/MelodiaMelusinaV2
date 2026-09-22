# -*- coding: utf-8 -*-
"""Batch-import Rokoko mocap RootMotion clips onto SK_Melusina_Skeleton.

Source: Saved/Audit/MelusinaReexport_20260921/out_<Clip>/A_Melusina_<Clip>_Mocap_RootMotion.fbx
These are DIRECT-target clips (465 bones, underscore names, x100 cm, 30 fps,
-Z/Y) produced against the Cascadeur target rig that matches the live skeleton.
Root motion is ON (the injected `root` bone carries travel).

Guarded per import_blender_melusina_idle.py: skeleton check, cm-probe via
c_spine_02_x (rejects meter-scale lands), wrong-skeleton rejection.
Writes Saved/Audit/rokoko_mocap_import_report.json and prints __ROKOKO_IMPORT__.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import unreal

try:
    _HERE = Path(__file__).resolve()
except NameError:  # exec() context (Monolith run_python) has no __file__
    _HERE = Path(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/import_rokoko_mocap_batch.py")
_TOOLS = _HERE.parents[2] / "Tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))
from melusina_anim_unit_guard import classify_spine_translation  # noqa: E402

LANE = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "MelusinaReexport_20260921"
DEST_DIR = "/Game/Melodia/Characters/Melusina/Animations/Mocap"
SKELETON = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
OUT = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "rokoko_mocap_import_report.json"


def asset_path(obj) -> str:
    return obj.get_path_name().split(".")[0] if obj else ""


def prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def probe_spine_y(seq) -> float | None:
    try:
        pose = unreal.AnimationLibrary.get_bone_pose_for_frame(seq, "c_spine_02_x", 0, False)
        return float(pose.translation.y)
    except Exception:
        return None


def import_one(fbx: str, name: str) -> dict:
    report = {"ok": False, "fbx": fbx, "dest_name": name}
    skeleton = unreal.load_asset(SKELETON)
    if not skeleton:
        report["error"] = "skeleton_missing"
        return report

    unreal.EditorAssetLibrary.make_directory(DEST_DIR)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", fbx)
    task.set_editor_property("destination_path", DEST_DIR)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("automated", True)

    options = unreal.FbxImportUI()
    options.set_editor_property("skeleton", skeleton)
    options.set_editor_property("import_as_skeletal", True)
    options.set_editor_property("import_mesh", False)
    options.set_editor_property("import_animations", True)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    try:
        options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
    except Exception:
        pass
    try:
        anim = options.get_editor_property("anim_sequence_import_data")
        if anim:
            anim.set_editor_property("import_bone_tracks", True)
            anim.set_editor_property("do_not_import_curve_with_zero", False)
            anim.set_editor_property("remove_redundant_keys", False)
            try:
                anim.set_editor_property("import_uniform_scale", 1.0)
            except Exception:
                pass
            try:
                anim.set_editor_property("convert_scene_unit", False)
            except Exception:
                pass
    except Exception as exc:
        report["anim_data_warn"] = str(exc)

    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = [str(p) for p in (task.get_editor_property("imported_object_paths") or [])]
    report["imported"] = imported

    dest = f"{DEST_DIR}/{name}"
    seq = unreal.load_asset(dest)
    if not seq and imported:
        seq = unreal.load_asset(imported[0].split(".", 1)[0])
    if not seq:
        report["error"] = "import_returned_no_sequence"
        return report

    seq.set_editor_property("loop", False)
    try:
        seq.set_editor_property("enable_root_motion", True)
    except Exception:
        pass
    try:
        unreal.EditorAssetLibrary.save_loaded_asset(seq, False)
    except Exception:
        pass

    report["sequence"] = asset_path(seq)
    report["skeleton"] = asset_path(prop(seq, "skeleton"))
    report["length"] = float(prop(seq, "sequence_length") or 0)
    report["frames"] = int(seq.get_number_of_frames()) if hasattr(seq, "get_number_of_frames") else None
    if report["skeleton"] != SKELETON:
        report["error"] = f"wrong_skeleton:{report['skeleton']}"
        return report

    y = probe_spine_y(seq)
    cls = classify_spine_translation(y)
    report["spine_y"] = y
    report["unit_class"] = cls
    if cls != "cm":
        report["error"] = f"meter_scale_rejected:{cls}"
        return report
    report["ok"] = True
    return report


def main() -> dict:
    results = []
    fbx_files = sorted(glob.glob(str(LANE / "out_*" / "A_Melusina_*_Mocap_RootMotion.fbx")))
    for fbx in fbx_files:
        name = Path(fbx).stem  # A_Melusina_WalkElegant_Mocap_RootMotion
        results.append(import_one(fbx, name))
    ok_count = sum(1 for r in results if r.get("ok"))
    payload = {"ok": ok_count == len(results) and len(results) > 0,
               "imported": ok_count, "total": len(results), "clips": results}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    payload = main()
    print("__ROKOKO_IMPORT__" + json.dumps(payload), flush=True)
    unreal.log("ROKOKO_MOCAP_IMPORT: " + json.dumps({"ok": payload.get("ok")}))
