# -*- coding: utf-8 -*-
"""Import the live Blender idle NLA clip onto SK_Melusina_Skeleton.

Does not replace live SK meshes. Does not import inbox Quaternius takes.
Does not save the Blender stage.
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

FBX = r"C:\EnvironmentPortfolio\BS_GodFile\Exports\MelusinaAnim\A_BL_Melusina_Idle_Loop.fbx"
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
            # Blender meters -> UE centimeters. Mocap rest for c_spine_02_x is ~-12.84.
            try:
                anim.set_editor_property("import_uniform_scale", 100.0)
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
    report["ok"] = True
    return report


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
    report = {"import": imported, "wire": None, "ok": False}
    if imported.get("ok"):
        report["wire"] = wire_idle(imported["sequence"])
        report["ok"] = bool(report["wire"].get("ok"))
    else:
        report["error"] = imported.get("error")
        report["note"] = "Blender clip did not land; locomotion speed-0 left as-is (Quaternius try still in editor if previously wired)."
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    payload = main()
    print("__BL_IDLE__" + json.dumps(payload), flush=True)
    unreal.log("MELUSINA_BLENDER_IDLE: " + json.dumps({"ok": payload.get("ok")}))
