# -*- coding: utf-8 -*-
"""Export the hand-keyframed idle from the v22 stage blend as a pre-retarget FBX.

THE CLIP
--------
Located 2026-08-16 in Melodia_Portfolio_Stage_v22_FINAL_2026-08-15.blend:

    ARMATURE character_rig (1124 bones)
      NLA track "idle_animation"
        strip "characteridle_handkeyframed"  -> action character_rigAction  (frames 1-24)

That is the owner's authored idle. Every idle currently in UE is either a bad
retarget or a Lane A import that fails the contract; this is the real source.

ROUTE NOTE
----------
This receipt proves the owner-authored ARP stage lineage only. It is not proof that
the resulting FBX is a live-skeleton animation and it must not be imported directly
onto SK_Melusina_Skeleton. The hand-keyed take must continue through the source-rig
contract and a dedicated IK retargeter before any target validation or promotion.

STAGE SAFETY
------------
Never saves the stage blend (AGENTS.md stage-save gate,
MELUSINA_BLENDER_WARDROBE_SSOT). All renaming is in memory; only the FBX and a
report are written.

RUN
---
    blender <stage>.blend -b -P Tools/export_melusina_idle_v22.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy

TOOLS = Path(__file__).resolve().parent
PROJECT = TOOLS.parent
OUT_DIR = PROJECT / "Exports" / "MelusinaAnims"
OUT_FBX = OUT_DIR / "A_Melusina_Idle_v22.fbx"
REPORT = PROJECT / "Saved" / "Audit" / "melusina_idle_v22_export.json"

ARM_NAME = "character_rig"
NLA_TRACK = "idle_animation"
ACTION_HINT = "character_rigAction"


def log(m):
    print(f"[idle_v22] {m}")


def main() -> int:
    sys.path.insert(0, str(TOOLS))
    import remap_melusina_rig_to_contract as remap

    report = {"blend": bpy.data.filepath, "ok": False}
    report["ue_import"] = False
    report["requires_ik_retarget"] = True
    report["export_role"] = "arp_source_pre_retarget"

    arm = bpy.data.objects.get(ARM_NAME) or remap.find_character_rig()
    if arm is None:
        report["error"] = "character_rig not found"
        _write(report)
        return 1
    report["armature"] = arm.name
    report["bone_count_before"] = len(arm.data.bones)

    # 1. Find the idle action via the NLA track (name is authoritative, not the
    #    action name -- the action is generically named character_rigAction).
    action = None
    ad = arm.animation_data
    if ad:
        for t in ad.nla_tracks:
            if t.name == NLA_TRACK:
                for s in t.strips:
                    if s.action:
                        action = s.action
                        report["strip"] = s.name
                        break
    if action is None:
        action = bpy.data.actions.get(ACTION_HINT)
    if action is None:
        report["error"] = f"no action on NLA track {NLA_TRACK!r}"
        _write(report)
        return 1

    report["action"] = action.name
    report["frame_range"] = [float(x) for x in action.frame_range]
    report["fcurves"] = len(action.fcurves)
    log(f"idle action {action.name} {report['frame_range']} fcurves={len(action.fcurves)}")

    # 2. Remap bones to the UE contract, in memory only.
    plan = remap.rename_plan(arm)
    remap.apply_plan(arm, plan)
    report["renamed"] = len(plan)
    report["bone_count_after"] = len(arm.data.bones)
    log(f"remapped {len(plan)} bones -> contract names")

    # 3. Bind the action directly and mute NLA so the strip cannot double-apply.
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    for t in arm.animation_data.nla_tracks:
        t.mute = True

    start, end = (int(round(v)) for v in action.frame_range)
    bpy.context.scene.frame_start = start
    bpy.context.scene.frame_end = end
    report["exported_range"] = [start, end]

    # 4. Export armature only, animation baked. No mesh -- UE imports this as an
    #    AnimSequence onto the existing skeleton.
    bpy.ops.object.select_all(action="DESELECT")
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=str(OUT_FBX),
        use_selection=True,
        object_types={"ARMATURE"},
        add_leaf_bones=False,
        bake_anim=True,
        bake_anim_use_all_bones=True,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False,
        bake_anim_force_startend_keying=True,
        bake_anim_step=1.0,
        global_scale=1.0,
        apply_scale_options="FBX_SCALE_NONE",
        axis_forward="-Z",
        axis_up="Y",
    )

    report["fbx"] = str(OUT_FBX)
    report["fbx_bytes"] = OUT_FBX.stat().st_size if OUT_FBX.exists() else 0
    report["ok"] = report["fbx_bytes"] > 0
    _write(report)
    log(f"wrote {OUT_FBX} ({report['fbx_bytes']} bytes)")
    log("stage NOT saved (per stage-save gate)")
    return 0 if report["ok"] else 1


def _write(report):
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("REPORT:", json.dumps(report))


if __name__ == "__main__":
    sys.exit(main())
