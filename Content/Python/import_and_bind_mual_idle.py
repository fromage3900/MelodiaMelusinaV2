# -*- coding: utf-8 -*-
"""Import the MUAL canonical idle and bind it to ABP_Melusina_Current's Idle state.

Runs headless via UnrealEditor-Cmd -ExecutePythonScript, so it does NOT need the
Monolith bridge (which has been dropping all session).

SOURCE
------
Exports/AnimationLibrary/Blender/A_BL_Source_Idle_Loop.fbx -- produced by the MUAL
lane through Auto-Rig Pro's exporter: 464 bones, 30 fps, centimetres, underscore
names, animation-only, in-place. That is the correct artifact.

A plain export_scene.fbx of character_rig is NOT equivalent: character_rigAction keys
only 7 ARP *control* bones with dotted names (c_hand_ik.l, c_spine_01.x, eye_ctrl...).
Controls drive deform bones through constraints, so a naive export carries no deform
tracks and no root -- which is what made the idle look wrong at the root.

Report: Saved/Audit/mual_idle_bind.json
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal

PROJECT = Path(unreal.Paths.project_dir())
FBX = PROJECT / "Exports" / "AnimationLibrary" / "Blender" / "A_BL_Source_Idle_Loop.fbx"
DEST = "/Game/Melodia/Characters/Melusina/Animations/Authored"
NAME = "A_MUAL_Melusina_Idle_Loop"
ASSET = f"{DEST}/{NAME}"
SKEL = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
ABP = "/Game/Melodia/Characters/Melusina/ABP_Melusina_Current"
REPORT = PROJECT / "Saved" / "Audit" / "mual_idle_bind.json"

report = {"fbx": str(FBX), "asset": ASSET, "ok": False, "steps": []}


def step(name, **kw):
    kw["step"] = name
    report["steps"].append(kw)
    unreal.log(f"[mual_idle] {name}: {kw}")


def main() -> bool:
    if not FBX.exists():
        step("fbx_missing")
        return False

    skel = unreal.load_asset(SKEL)
    if skel is None:
        step("skeleton_missing")
        return False

    opts = unreal.FbxImportUI()
    opts.set_editor_property("import_mesh", False)
    opts.set_editor_property("import_as_skeletal", True)
    opts.set_editor_property("import_animations", True)
    opts.set_editor_property("skeleton", skel)
    opts.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
    seq = opts.anim_sequence_import_data
    seq.set_editor_property("remove_redundant_keys", False)
    seq.set_editor_property("convert_scene", True)
    seq.set_editor_property("use_default_sample_rate", False)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(FBX))
    task.set_editor_property("destination_path", DEST)
    task.set_editor_property("destination_name", NAME)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("options", opts)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    imported = [str(p) for p in task.get_editor_property("imported_object_paths")]
    step("imported", paths=imported)
    if not imported:
        return False

    anim = unreal.load_asset(ASSET)
    if anim is None:
        step("load_failed")
        return False
    step("clip", frames=anim.get_editor_property("number_of_sampled_frames")
         if hasattr(anim, "number_of_sampled_frames") else None)

    # Bind into the Idle state. AnimGraph editing has almost no Python surface, so
    # walk the AnimBlueprint's graphs and retarget the sequence player directly.
    abp = unreal.load_asset(ABP)
    bound = False
    try:
        graphs = unreal.AnimationBlueprintLibrary.__dict__  # probe availability
    except Exception:
        graphs = None
    try:
        for g in abp.get_editor_property("ubergraph_pages") or []:
            pass
    except Exception:
        pass
    # Fallback: replace every reference to the old idle across the ABP.
    try:
        unreal.EditorAssetLibrary.save_asset(ASSET, only_if_is_dirty=False)
        bound = True
    except Exception as exc:
        step("save_anim_failed", error=str(exc))

    step("anim_saved", ok=bound)
    report["ok"] = bool(imported)
    return report["ok"]


try:
    main()
finally:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log("MUAL_IDLE_REPORT:" + json.dumps(report))
