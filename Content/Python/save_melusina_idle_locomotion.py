# -*- coding: utf-8 -*-
"""Bake + persist Melusina idle locomotion wire. Does not touch ABP Idle graph
(Idle already plays BS_Melusina_Locomotion). Does not replace mocap idle on disk.
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

DEST = "/Game/Melodia/Characters/Melusina/Animations/Cascadeur/A_CAS_Melusina_Idle_Loop"
BLEND = "/Game/Melodia/Characters/Melusina/Animations/BS_Melusina_Locomotion"
MOCAP = "/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Idle_Mocap_RootX"
OUT = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "melusina_idle_locomotion_wire.json"


def path(obj):
    return obj.get_path_name().split(".")[0] if obj else None


def prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def save_pkg(obj) -> dict:
    result = {"path": path(obj), "ok": False}
    if not obj:
        result["error"] = "missing"
        return result
    pkg = obj.get_package()
    try:
        dirty_list = list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages() or [])
        result["dirty_before"] = pkg in dirty_list
    except Exception as e:
        result["dirty_before_error"] = str(e)
    try:
        saved = unreal.EditorLoadingAndSavingUtils.save_packages([pkg], False)
        result["save_packages"] = bool(saved)
    except Exception as e:
        result["save_packages_error"] = str(e)
    try:
        result["save_loaded"] = bool(unreal.EditorAssetLibrary.save_loaded_asset(obj, False))
    except Exception as e:
        result["save_loaded_error"] = str(e)
    try:
        result["save_asset"] = bool(unreal.EditorAssetLibrary.save_asset(path(obj), only_if_is_dirty=False))
    except Exception as e:
        result["save_asset_error"] = str(e)
    try:
        dirty_list = list(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages() or [])
        result["dirty_after"] = pkg in dirty_list
    except Exception as e:
        result["dirty_after_error"] = str(e)
    result["ok"] = bool(result.get("save_packages") or result.get("save_loaded") or result.get("save_asset"))
    if result.get("dirty_after") is False:
        result["ok"] = True
    return result


def samples_of(blend):
    rows = []
    for i, sample in enumerate(prop(blend, "sample_data", []) or []):
        animation = prop(sample, "animation")
        value = prop(sample, "sample_value")
        rows.append({
            "index": i,
            "animation": path(animation),
            "speed": float(value.x) if value else None,
        })
    return rows


def main() -> dict:
    dest = unreal.load_asset(DEST)
    blend = unreal.load_asset(BLEND)
    report = {
        "ok": False,
        "dest": DEST,
        "blendspace": BLEND,
        "abp_idle_state": "already BlendSpacePlayer BS_Melusina_Locomotion — not rewritten",
    }
    if not dest or not blend:
        report["error"] = "missing_assets"
        return report

    try:
        if hasattr(blend, "validate_sample_data"):
            blend.validate_sample_data()
        if hasattr(blend, "resample_data"):
            blend.resample_data()
        report["baked_python"] = True
    except Exception as e:
        report["bake_python_error"] = str(e)

    dest.set_editor_property("loop", True)
    try:
        dest.set_editor_property("enable_root_motion", False)
    except Exception:
        pass

    report["save_dest"] = save_pkg(dest)
    report["save_blend"] = save_pkg(blend)
    after = samples_of(blend)
    idle_rows = [row for row in after if row["speed"] is not None and abs(row["speed"]) < 0.1]
    report["samples"] = after
    report["mocap_idle_still_on_disk"] = unreal.EditorAssetLibrary.does_asset_exist(MOCAP)
    report["dest_loop"] = bool(prop(dest, "loop"))
    report["dest_length"] = float(prop(dest, "sequence_length") or 0)
    report["dest_skeleton"] = path(prop(dest, "skeleton"))
    report["ok"] = (
        len(idle_rows) == 1
        and idle_rows[0]["animation"] == DEST
        and report["dest_loop"]
        and report["mocap_idle_still_on_disk"]
        and bool(report["save_blend"].get("ok"))
        and bool(report["save_dest"].get("ok"))
    )
    if not report["ok"]:
        report["error"] = "verify_or_save_failed"
    return report


if __name__ == "__main__":
    payload = main()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("__IDLE_SAVE__" + json.dumps(payload), flush=True)
