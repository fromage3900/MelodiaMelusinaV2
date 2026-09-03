# -*- coding: utf-8 -*-
"""Import the live Blender idle NLA clip onto SK_Melusina_Skeleton.

NOT Lane A. New ARP/Blender sources fail four axes (dots, bone count, meters,
24 fps) unless remapped + cm-probed. See
Saved/Audit/melusina_idle_retarget_rca_2026-08-13.md.

Does not replace live SK meshes. Does not import inbox Quaternius takes.
Does not save the Blender stage. Does not wire locomotion unless
MELUSINA_WIRE_BLENDER_IDLE=1 (owner-gated; H3 — wait for PIE mocap idle).
Meter-scale imports are scaled x100 after import; a clip that stays in
meters is rejected.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import unreal

_TOOLS = Path(__file__).resolve().parents[2] / "Tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))
from melusina_anim_unit_guard import (  # noqa: E402
    classify_spine_translation,
    spine_matches_mocap_cm,
)

FBX = r"C:\EnvironmentPortfolio\BS_GodFile\Exports\MelusinaAnim\A_BL_Melusina_Idle_Loop_cm.fbx"
DEST_DIR = "/Game/Melodia/Characters/Melusina/Animations/Cascadeur"
DEST_NAME = "A_BL_Melusina_Idle_Loop"
DEST = f"{DEST_DIR}/{DEST_NAME}"
SKELETON = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
MESH = "/Game/Melodia/Characters/Melusina/SK_Melusina"
BLENDSPACE = "/Game/Melodia/Characters/Melusina/Animations/BS_Melusina_Locomotion"
MOCAP_IDLE = "/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Idle_Mocap_RootX"
OUT = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "melusina_blender_idle_wire.json"


def asset_path(obj) -> str:
    return obj.get_path_name().split(".")[0] if obj else ""


def prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def samples_of(blend):
    rows = []
    for i, sample in enumerate(prop(blend, "sample_data", []) or []):
        animation = prop(sample, "animation")
        value = prop(sample, "sample_value")
        rows.append({
            "index": i,
            "animation": asset_path(animation),
            "speed": float(value.x) if value else None,
        })
    return rows


def import_idle() -> dict:
    report = {"ok": False, "fbx": FBX, "dest": DEST}
    if not Path(FBX).is_file():
        report["error"] = "fbx_missing"
        return report
    skeleton = unreal.load_asset(SKELETON)
    mesh = unreal.load_asset(MESH)
    if not skeleton or not mesh:
        report["error"] = "skeleton_or_mesh_missing"
        return report

    unreal.EditorAssetLibrary.make_directory(DEST_DIR)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", FBX)
    task.set_editor_property("destination_path", DEST_DIR)
    task.set_editor_property("destination_name", DEST_NAME)
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
            # Header UnitScaleFactor is not trusted. Import 1:1, then probe
            # c_spine_02_x and x100 the tracks if they landed in meters.
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
    seq = unreal.load_asset(DEST)
    if not seq and imported:
        seq = unreal.load_asset(imported[0].split(".", 1)[0])
    if not seq:
        report["error"] = "import_returned_no_sequence"
        return report

    seq.set_editor_property("loop", True)
    try:
        seq.set_editor_property("enable_root_motion", False)
    except Exception:
        pass
    try:
        unreal.EditorAssetLibrary.save_loaded_asset(seq, False)
    except Exception as exc:
        report["save_seq_warn"] = str(exc)

    report["sequence"] = asset_path(seq)
    report["skeleton"] = asset_path(prop(seq, "skeleton"))
    report["loop"] = bool(prop(seq, "loop"))
    report["length"] = float(prop(seq, "sequence_length") or 0)
    report["frames"] = int(seq.get_number_of_frames()) if hasattr(seq, "get_number_of_frames") else None
    if report["skeleton"] != SKELETON:
        report["error"] = f"wrong_skeleton:{report['skeleton']}"
        return report
    unit = _ensure_cm_tracks(seq)
    report["unit"] = unit
    if unit.get("class") != "cm":
        report["error"] = f"meter_scale_rejected:{unit.get('class')}:spine_y={unit.get('spine_y')}"
        return report
    report["ok"] = True
    return report


def _probe_spine_y(seq) -> float | None:
    try:
        pose = unreal.AnimationLibrary.get_bone_pose_for_frame(seq, "c_spine_02_x", 0, False)
        return float(pose.translation.y)
    except Exception:
        return None


def _scale_tracks_x100(seq) -> dict:
    ctrl = seq.get_editor_property("controller")
    iface = seq.get_editor_property("data_model_interface")
    names = list(iface.get_bone_track_names())
    nkeys = 0
    if hasattr(iface, "get_number_of_keys"):
        try:
            nkeys = int(iface.get_number_of_keys())
        except Exception:
            nkeys = 0
    if nkeys <= 1 and hasattr(seq, "get_number_of_sampled_keys"):
        try:
            nkeys = int(seq.get_number_of_sampled_keys())
        except Exception:
            nkeys = 0
    if nkeys <= 1:
        nkeys = 24
    ctrl.open_bracket("Scale blender idle m to cm")
    for bone in names:
        positions, rotations, scales = [], [], []
        for frame in range(nkeys):
            pose = unreal.AnimationLibrary.get_bone_pose_for_frame(seq, bone, frame, False)
            loc = pose.translation
            positions.append(unreal.Vector(loc.x * 100.0, loc.y * 100.0, loc.z * 100.0))
            rotations.append(pose.rotation)
            scales.append(pose.scale3d)
        ctrl.set_bone_track_keys(bone, positions, rotations, scales)
    ctrl.close_bracket()
    try:
        unreal.EditorAssetLibrary.save_loaded_asset(seq, False)
    except Exception:
        pass
    return {"scaled_tracks": len(names), "nkeys": nkeys}


def _ensure_cm_tracks(seq) -> dict:
    y = _probe_spine_y(seq)
    unit = {"spine_y": y, "class": classify_spine_translation(y), "scaled_100": False}
    if unit["class"] == "meters":
        unit.update(_scale_tracks_x100(seq))
        unit["scaled_100"] = True
        y = _probe_spine_y(seq)
        unit["spine_y"] = y
        unit["class"] = classify_spine_translation(y)
    unit["matches_mocap_cm"] = spine_matches_mocap_cm(y)
    if unit["class"] == "cm" and not unit["matches_mocap_cm"]:
        unit["warn"] = "cm_class_but_spine_y_not_near_mocap_-12.84"
    return unit


def wire_idle(dest_path: str) -> dict:
    dest = unreal.load_asset(dest_path)
    blend = unreal.load_asset(BLENDSPACE)
    out = {"ok": False, "dest": dest_path}
    if not dest or not blend:
        out["error"] = "missing_dest_or_blendspace"
        return out
    before = samples_of(blend)
    kept = []
    replaced = False
    for sample in list(prop(blend, "sample_data", []) or []):
        value = prop(sample, "sample_value")
        speed = float(value.x) if value else None
        if speed is not None and abs(speed) < 0.1:
            sample.set_editor_property("animation", dest)
            sample.set_editor_property("rate_scale", 1.0)
            replaced = True
        kept.append(sample)
    if not replaced:
        new_sample = unreal.BlendSample()
        new_sample.set_editor_property("animation", dest)
        new_sample.set_editor_property("sample_value", unreal.Vector(0.0, 0.0, 0.0))
        new_sample.set_editor_property("rate_scale", 1.0)
        kept.append(new_sample)
    blend.modify()
    blend.set_editor_property("sample_data", kept)
    try:
        if hasattr(blend, "validate_sample_data"):
            blend.validate_sample_data()
        if hasattr(blend, "resample_data"):
            blend.resample_data()
        out["baked"] = True
    except Exception as exc:
        out["bake_error"] = str(exc)
    try:
        pkg = blend.get_package()
        saved = unreal.EditorLoadingAndSavingUtils.save_packages([pkg], False)
        out["save_packages"] = bool(saved)
    except Exception as exc:
        out["save_packages_error"] = str(exc)
    try:
        out["save_loaded"] = bool(unreal.EditorAssetLibrary.save_loaded_asset(blend, False))
    except Exception as exc:
        out["save_loaded_error"] = str(exc)
    after = samples_of(blend)
    idle_rows = [row for row in after if row["speed"] is not None and abs(row["speed"]) < 0.1]
    out["before"] = before
    out["after"] = after
    out["mocap_idle_still_on_disk"] = unreal.EditorAssetLibrary.does_asset_exist(MOCAP_IDLE)
    out["ok"] = (
        len(idle_rows) == 1
        and idle_rows[0]["animation"] == dest_path
        and out["mocap_idle_still_on_disk"]
    )
    if not out["ok"]:
        out["error"] = "verify_failed"
    return out


def main() -> dict:
    imported = import_idle()
    report = {
        "import": imported,
        "wire": None,
        "ok": False,
        "wired": False,
        "note": "Locomotion is not wired unless MELUSINA_WIRE_BLENDER_IDLE=1 after a cm probe.",
    }
    if not imported.get("ok"):
        report["error"] = imported.get("error")
        report["note"] = (
            "Blender clip did not land as cm on SK_Melusina_Skeleton; "
            "locomotion speed-0 left as-is."
        )
    elif os.environ.get("MELUSINA_WIRE_BLENDER_IDLE", "0") == "1":
        report["wire"] = wire_idle(imported["sequence"])
        report["wired"] = bool(report["wire"].get("ok"))
        report["ok"] = report["wired"]
        if not report["ok"]:
            report["error"] = report["wire"].get("error")
    else:
        report["ok"] = True
        report["note"] = (
            "Imported and cm-probed. Speed 0 stays A_Melusina_Idle_Mocap_RootX "
            "until PIE proves mocap idle looks normal."
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    payload = main()
    print("__BL_IDLE__" + json.dumps(payload), flush=True)
    unreal.log("MELUSINA_BLENDER_IDLE: " + json.dumps({"ok": payload.get("ok")}))
