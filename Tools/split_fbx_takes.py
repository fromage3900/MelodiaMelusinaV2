"""Split UAL1_Standard.fbx (Quaternius) into per-take FBX files for Cascadeur.

Each take becomes its own binary FBX: armature + baked animation only, 30 fps,
Y-up, no mesh, no leaf bones. One clip per file, as the pipeline contract
requires. Run with Blender 5.2 in background mode:

  blender --background --factory-startup --python Tools/split_fbx_takes.py -- \\
      Imports/Animations/Cascadeur/Source/Quaternius/UAL1_Standard.fbx \\
      Imports/Animations/Cascadeur/Source/Quaternius/Takes
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import bpy


def _args() -> tuple[Path, Path, list[str]]:
    rest = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(rest) < 2:
        raise SystemExit(
            "usage: blender --background --factory-startup --python split_fbx_takes.py -- source.fbx outdir [skip:Take1,Take2]"
        )
    source = Path(rest[0]).resolve()
    outdir = Path(rest[1]).resolve()
    skip = [t.strip() for t in rest[2].split(",") if t.strip()] if len(rest) > 2 else ["A_TPose"]
    return source, outdir, skip


def _take_name(action_name: str) -> str:
    return action_name.rsplit("|", 1)[-1]


def _assign_action_with_slot(arm, action) -> bool:
    """Assign an action to an armature under the 4.2+ slot system.

    Returns True when the action is active and carries at least one F-curve.
    """
    if arm.animation_data is None:
        arm.animation_data_create()
    arm.animation_data.action = action
    slot = None
    for layer in action.layers:
        for strip in layer.strips:
            for channelbag in strip.channelbags:
                if channelbag.slot is not None:
                    slot = channelbag.slot
                    break
            if slot is not None:
                break
        if slot is not None:
            break
    if slot is not None:
        arm.animation_data.action_slot = slot
    return arm.animation_data.action is action and any(
        fc for layer in action.layers for strip in layer.strips for channelbag in strip.channelbags for fc in channelbag.fcurves
    )


EXPORT_KWARGS = dict(
    use_selection=True,
    object_types={"ARMATURE"},
    add_leaf_bones=False,
    bake_anim=True,
    bake_anim_use_all_bones=True,
    bake_anim_use_nla_strips=False,
    bake_anim_use_all_actions=False,
    bake_anim_force_startend_keying=True,
    bake_anim_simplify_factor=0.0,
    axis_forward="-Z",
    axis_up="Y",
)


def main() -> None:
    source, outdir, skip = _args()
    if not source.is_file():
        raise SystemExit(f"source FBX not found: {source}")
    outdir.mkdir(parents=True, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(
        filepath=str(source),
        use_anim=True,
        use_image_search=False,
        use_custom_normals=False,
    )

    scene = bpy.context.scene
    scene.render.fps = 30
    scene.render.fps_base = 1

    armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    if not armatures:
        raise SystemExit("no armature found in source FBX")
    arm = armatures[0]
    for obj in bpy.data.objects:
        obj.select_set(obj is arm)
    bpy.context.view_layer.objects.active = arm
    if arm.animation_data is None:
        arm.animation_data_create()

    exported: list[dict] = []
    failures: list[dict] = []

    for action in sorted(bpy.data.actions, key=lambda a: _take_name(a.name)):
        take = _take_name(action.name)
        if take in skip:
            print(f"SKIP {take}")
            continue
        if not _assign_action_with_slot(arm, action):
            failures.append({"take": take, "error": "action could not be assigned with an active slot"})
            print(f"FAIL {take}: action slot assignment failed")
            continue
        scene.frame_start = int(action.frame_range[0])
        scene.frame_end = int(action.frame_range[1])
        out_path = outdir / f"CAS_Q_{take}.fbx"
        try:
            bpy.ops.export_scene.fbx(filepath=str(out_path), **EXPORT_KWARGS)
        except TypeError as exc:
            failures.append({"take": take, "error": f"export kwargs rejected: {exc}"})
            print(f"FAIL {take}: {exc}")
            continue
        exported.append({
            "take": take,
            "file": str(out_path),
            "frame_start": int(action.frame_range[0]),
            "frame_end": int(action.frame_range[1]),
            "frame_count": int(action.frame_range[1] - action.frame_range[0] + 1),
        })
        print(f"OK {take} -> {out_path.name}")

    summary = {
        "source": str(source),
        "outdir": str(outdir),
        "fps": 30,
        "skip": skip,
        "exported": exported,
        "failures": failures,
    }
    report = outdir / "_split_report.json"
    report.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    sys.stdout.flush()
    os._exit(0 if not failures else 1)


if __name__ == "__main__":
    main()
