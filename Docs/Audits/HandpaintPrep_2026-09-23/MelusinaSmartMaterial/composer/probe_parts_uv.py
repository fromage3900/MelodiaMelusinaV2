"""Probe: per-object UV bounding boxes + world centroids of the sheep FBX.

Answers: which mesh object owns the chest, and which atlas zone each object
samples — so the hero band can be painted into the zone that the camera sees.

Melodia / Melusina only. No Grok*.
"""
import bpy
import json
import sys
from mathutils import Vector

argv = sys.argv
argv = argv[argv.index("--") + 1:] if "--" in argv else []
fbx = argv[0]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)

out = []
for ob in bpy.context.scene.objects:
    if ob.type != "MESH":
        continue
    me = ob.data
    uvl = me.uv_layers.active
    if not uvl:
        out.append({"name": ob.name, "uv": None})
        continue
    us = [l.uv[0] for l in uvl.data]
    vs = [l.uv[1] for l in uvl.data]
    c = ob.matrix_world @ (sum((Vector(b) for b in ob.bound_box),
                               Vector()) / 8.0)
    out.append({
        "name": ob.name,
        "uv_u": [round(min(us), 3), round(max(us), 3)],
        "uv_v": [round(min(vs), 3), round(max(vs), 3)],
        "centroid": [round(c.x, 1), round(c.y, 1), round(c.z, 1)],
        "verts": len(me.vertices),
    })

print("PROBE_JSON:" + json.dumps(out))
