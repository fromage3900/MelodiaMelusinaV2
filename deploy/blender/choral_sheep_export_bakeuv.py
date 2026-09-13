"""Put the master's packed BakeUV on the canonical Choral Sheep export, as UV channel 0.

    blender -b --factory-startup <choralsheep_Final.blend> --python choral_sheep_export_bakeuv.py -- <canonical.fbx> <out.fbx>

The canonical FBX already carries the right skeleton, weights and rest pose; only its BakeUV is stale
(UVPackmaster repack happened in the master afterwards). This copies the master MrSheepFinal BakeUV
loop-for-loop onto that mesh and exports it first, so M_Master_Toon_Character (TexCoord 0) samples the
packed layout. The old UVMap is kept as channel 1. Refuses unless topology and the unchanged UVMap agree
loop for loop, then re-imports the result and checks UVs and rest pose.
"""

import sys

import bpy

canon_fbx, out_fbx = sys.argv[sys.argv.index("--") + 1:]


def uvs(mesh, name):
    return [tuple(round(c, 5) for c in d.uv) for d in mesh.uv_layers[name].data]


src = bpy.data.objects["MrSheepFinal"].data
src_bake = uvs(src, "BakeUV")
src_uvmap = uvs(src, "UVMap")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=canon_fbx)
arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
skin = next(o for o in bpy.data.objects if o.type == "MESH")
me = skin.data
rest_before = {b.name: (arm.matrix_world @ b.matrix_local).copy() for b in arm.data.bones}

if len(me.loops) != len(src_bake) or uvs(me, "UVMap") != src_uvmap:
    raise SystemExit("REFUSE: canonical mesh loops/UVMap do not match the master MrSheepFinal")

old_uvmap = uvs(me, "UVMap")
while me.uv_layers:
    me.uv_layers.remove(me.uv_layers[0])
for name, data in (("BakeUV", src_bake), ("UVMap", old_uvmap)):
    layer = me.uv_layers.new(name=name)
    for d, uv in zip(layer.data, data):
        d.uv = uv
me.uv_layers["BakeUV"].active = True
me.uv_layers["BakeUV"].active_render = True

for o in bpy.data.objects:
    o.select_set(o in (arm, skin))
bpy.ops.export_scene.fbx(
    filepath=out_fbx, use_selection=True, object_types={"ARMATURE", "MESH"}, add_leaf_bones=False,
    primary_bone_axis="Y", secondary_bone_axis="X", armature_nodetype="NULL", bake_anim=False,
    apply_unit_scale=True, global_scale=1.0,
)

vert_count = len(me.vertices)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=out_fbx)
arm2 = next(o for o in bpy.data.objects if o.type == "ARMATURE")
me2 = next(o for o in bpy.data.objects if o.type == "MESH").data
names = [l.name for l in me2.uv_layers]
uv_ok = names[:1] == ["BakeUV"] and uvs(me2, "BakeUV") == src_bake and len(me2.vertices) == vert_count
worst = 0.0
for b in arm2.data.bones:
    m = arm2.matrix_world @ b.matrix_local
    worst = max(worst, (m.translation - rest_before[b.name].translation).length)
print("EXPORTBAKEUV uv_layers=%s uv_ok=%s verts=%d bones=%d rest_worst_m=%.6f verdict=%s" % (
    names, uv_ok, len(me2.vertices), len(arm2.data.bones), worst, "PASS" if uv_ok and worst < 1e-4 else "FAIL"))
