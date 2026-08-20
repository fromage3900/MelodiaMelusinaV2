# -*- coding: utf-8 -*-
"""Remap ARP dotted bone names to UE underscores in an animation-only FBX.

Run with a factory Blender, never the live v22 file:
  blender --background --factory-startup --python this.py -- raw.fbx out.fbx
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


def remap(name: str) -> str:
    return name.replace(".", "_")


def main() -> None:
    rest = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(rest) < 2:
        raise SystemExit("usage: blender --background --factory-startup --python remap.py -- raw.fbx out.fbx")
    src = Path(rest[0]).resolve()
    dst = Path(rest[1]).resolve()
    if not src.is_file():
        raise SystemExit(f"missing {src}")

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(src), use_anim=True, use_image_search=False, use_custom_normals=False)

    armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    if not armatures:
        raise SystemExit("no armature in raw FBX")
    arm = armatures[0]
    before = [b.name for b in arm.data.bones]
    renamed = 0
    collisions = []
    existing = {b.name for b in arm.data.bones}
    for bone in list(arm.data.bones):
        new_name = remap(bone.name)
        if new_name == bone.name:
            continue
        if new_name in existing and new_name != bone.name:
            collisions.append({"from": bone.name, "to": new_name})
            continue
        old = bone.name
        bone.name = new_name
        existing.discard(old)
        existing.add(new_name)
        renamed += 1

    scene = bpy.context.scene
    scene.render.fps = 24
    scene.render.fps_base = 1.0
    scene.frame_start = 1
    scene.frame_end = 24

    for obj in bpy.data.objects:
        obj.select_set(obj is arm)
    bpy.context.view_layer.objects.active = arm

    dst.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=str(dst),
        use_selection=True,
        object_types={"ARMATURE"},
        add_leaf_bones=False,
        use_armature_deform_only=True,
        bake_anim=True,
        bake_anim_use_all_bones=True,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False,
        bake_anim_force_startend_keying=True,
        bake_anim_simplify_factor=0.0,
        axis_forward="-Z",
        axis_up="Y",
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        global_scale=100.0,
    )

    after = [b.name for b in arm.data.bones]
    report = {
        "src": str(src),
        "dst": str(dst),
        "bytes": dst.stat().st_size if dst.is_file() else 0,
        "bone_count": len(after),
        "renamed": renamed,
        "collisions": collisions[:20],
        "sample_before": before[:15],
        "sample_after": after[:15],
        "has_c_hand_ik_l": "c_hand_ik_l" in after,
        "has_c_spine_02_x": "c_spine_02_x" in after,
        "has_root": "root" in after,
        "has_root_x": "root_x" in after,
    }
    report_path = dst.with_suffix(".remap.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
