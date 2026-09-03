# -*- coding: utf-8 -*-
"""Wire the already-imported Melusina-skeleton idle into locomotion.

Does NOT:
  - replace A_Melusina_Idle_Mocap_RootX on disk
  - import Quaternius UAL1 FBX onto a new skeleton
  - touch SK_Melusina / SK_MelusinaHair meshes

Source (already SK_Melusina_Skeleton):
  /Game/Melodia/Characters/Melusina/Animations/SourceRetargeted/SK_QuaterniusArmature_Idle_Loop
Copy:
  /Game/Melodia/Characters/Melusina/Animations/Cascadeur/A_CAS_Melusina_Idle_Loop
Then replace only the speed-0 sample on BS_Melusina_Locomotion.
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

SRC = "/Game/Melodia/Characters/Melusina/Animations/SourceRetargeted/SK_QuaterniusArmature_Idle_Loop"
DEST = "/Game/Melodia/Characters/Melusina/Animations/Cascadeur/A_CAS_Melusina_Idle_Loop"
BLENDSPACE = "/Game/Melodia/Characters/Melusina/Animations/BS_Melusina_Locomotion"
SKELETON = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
MOCAP_IDLE = "/Game/Melodia/Characters/Melusina/Animations/Locomotion/A_Melusina_Idle_Mocap_RootX"
OUT = Path(unreal.Paths.project_dir()) / "Saved" / "Audit" / "melusina_idle_locomotion_wire.json"


def asset_path(obj) -> str:
    return obj.get_path_name().split(".")[0] if obj else ""


def prop(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def main() -> dict:
    report = {"ok": False, "src": SRC, "dest": DEST, "blendspace": BLENDSPACE}
    src = unreal.load_asset(SRC)
    if not src:
        report["error"] = "source_idle_missing"
        return report
    if asset_path(prop(src, "skeleton")) != SKELETON:
        report["error"] = f"source_wrong_skeleton:{asset_path(prop(src, 'skeleton'))}"
        return report

    unreal.EditorAssetLibrary.make_directory("/Game/Melodia/Characters/Melusina/Animations/Cascadeur")
    if unreal.EditorAssetLibrary.does_asset_exist(DEST):
        dest = unreal.load_asset(DEST)
        report["copied"] = False
    else:
        if not unreal.EditorAssetLibrary.duplicate_asset(SRC, DEST):
            report["error"] = "duplicate_failed"
            return report
        dest = unreal.load_asset(DEST)
        report["copied"] = True
    if not dest:
        report["error"] = "dest_load_failed"
        return report

    dest.set_editor_property("loop", True)
    try:
        dest.set_editor_property("enable_root_motion", False)
    except Exception:
        pass
    if not unreal.EditorAssetLibrary.save_asset(DEST, only_if_is_dirty=False):
        report["warn_save_seq"] = True

    blend = unreal.load_asset(BLENDSPACE)
    if not blend:
        report["error"] = "blendspace_missing"
        return report

    samples = list(prop(blend, "sample_data", []) or [])
    before = []
    kept = []
    replaced = False
    for sample in samples:
        animation = prop(sample, "animation")
        value = prop(sample, "sample_value")
        speed = float(value.x) if value else None
        before.append({"animation": asset_path(animation), "speed": speed})
        if speed is not None and abs(speed) < 0.1:
            sample.set_editor_property("animation", dest)
            sample.set_editor_property("rate_scale", 1.0)
            kept.append(sample)
            replaced = True
            continue
        kept.append(sample)

    if not replaced:
        new_sample = unreal.BlendSample()
        new_sample.set_editor_property("animation", dest)
        new_sample.set_editor_property("sample_value", unreal.Vector(0.0, 0.0, 0.0))
        new_sample.set_editor_property("rate_scale", 1.0)
        kept.append(new_sample)

    blend.modify()
    blend.set_editor_property("sample_data", kept)
    if not unreal.EditorAssetLibrary.save_loaded_asset(blend, False):
        report["error"] = "blendspace_save_failed"
        return report

    after = []
    for sample in prop(blend, "sample_data", []) or []:
        animation = prop(sample, "animation")
        value = prop(sample, "sample_value")
        after.append({"animation": asset_path(animation), "speed": float(value.x) if value else None})

    idle_rows = [row for row in after if row["speed"] is not None and abs(row["speed"]) < 0.1]
    report["before"] = before
    report["after"] = after
    report["mocap_idle_still_on_disk"] = unreal.EditorAssetLibrary.does_asset_exist(MOCAP_IDLE)
    report["dest_loop"] = bool(prop(dest, "loop"))
    report["dest_length"] = float(prop(dest, "sequence_length") or 0)
    report["ok"] = (
        len(idle_rows) == 1
        and idle_rows[0]["animation"] == DEST
        and report["dest_loop"]
        and report["mocap_idle_still_on_disk"]
    )
    if not report["ok"]:
        report["error"] = "verify_failed"
    return report


if __name__ == "__main__":
    payload = main()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("__IDLE__" + json.dumps(payload), flush=True)
    unreal.log("MELUSINA_IDLE_WIRED: " + json.dumps({"ok": payload.get("ok"), "dest": DEST}))
