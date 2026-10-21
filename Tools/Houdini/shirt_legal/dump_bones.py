"""Dump the hem-bone geometry of the legal shirt FBX for the skeleton-delta manifest.

Blender is the only writer that knows bone tails (the KineFX rest geometry in
Houdini carries joint heads only). Prints every bone's parent, head and tail in
the FBX's own centimetre frame, plus a reference bone (spine_03_x) so the
conversion to the UE skeleton component frame can be checked independently.

  "C:\\Program Files\\Blender Foundation\\Blender 4.5\\blender.exe" -b --python dump_bones.py
"""
import json
import os

import bpy

FBX = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\ShirtBones_20261020\SK_Melusina_V2_Shirt_HemRig_Legal.fbx"
OUT = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\ShirtBones_20261020\legality_bones.json"

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
try:
    bpy.ops.import_scene.fbx(filepath=FBX, use_anim=False)
except TypeError:
    bpy.ops.import_scene.fbx(filepath=FBX)

arms = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
arm = max(arms, key=lambda o: len(o.data.bones))
scale = [arm.scale.x, arm.scale.y, arm.scale.z]
world = arm.matrix_world

bones = {}
for b in arm.data.bones:
    h = list(b.head_local)
    t = list(b.tail_local)
    bones[b.name] = {
        "parent": b.parent.name if b.parent else None,
        "head_local": [round(v, 5) for v in h],
        "tail_local": [round(v, 5) for v in t],
        "length_local": round((b.tail_local - b.head_local).length, 5),
        "use_deform": bool(b.use_deform),
        "world_head": [round(v, 6) for v in (world @ b.head_local)],
        "world_tail": [round(v, 6) for v in (world @ b.tail_local)],
    }

rep = {
    "fbx": FBX,
    "armature": arm.name,
    "bone_count": len(bones),
    "armature_object_scale": [round(v, 6) for v in scale],
    "armature_matrix_world": [round(v, 6) for row in world for v in row],
    "reference_bones": {k: bones[k] for k in ("root_x", "c_root_x", "spine_03_x", "neck_x") if k in bones},
    "hem_bones": {k: v for k, v in sorted(bones.items()) if "hem" in k.lower()},
    "non_deform_hem_bones": [k for k, v in bones.items() if "hem" in k.lower() and not v["use_deform"]],
}

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(rep, fh, indent=1)
print("BONES=" + json.dumps(rep)[:2500])
