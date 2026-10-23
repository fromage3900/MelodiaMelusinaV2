#!/usr/bin/env python
"""Cos_FlowerSpring — assembly + QA renders v2 (Blender 4.5).

Fixes over v1: Houdini pieces are cm-units (dress is meters) -> explicit unit
correction; default startup Cube/Light/Camera purged; flat palette preview
materials (no vertex-color dependency); measured camera framing.

Run: blender4.5 -b --factory-startup -noaudio --python flowerspring_assemble_qa.py
"""
import json
import math
from pathlib import Path

import bpy
import mathutils

PROJECT = Path("C:/EnvironmentPortfolio/BS_GodFile")
OUT = PROJECT / "Saved" / "Audit" / "melusina_lookdev" / "flowers_outfit"

bpy.ops.wm.read_homefile(use_factory_startup=True)
# purge default startup objects
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)

pieces = {}
for name in ("passA2_shirt_panels", "passA2_skirt_panels", "FS_Crown", "FS_Wings"):
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=str(OUT / f"{name}.obj"),
                          forward_axis="NEGATIVE_Y", up_axis="Z")
    pieces[name] = [o for o in set(bpy.data.objects) - before if o.type == "MESH"]

# unit correction: Houdini authored in cm-as-units; dress is in meters
UNIT = {"passA2_shirt_panels": 1.0, "passA2_skirt_panels": 1.0,
        "FS_Crown": 0.0065, "FS_Wings": 0.0145}
# flat palette previews (final look = owner Substance paint over the warm-spring kit)
PREVIEW = {"passA2_shirt_panels": (0.99, 0.88, 0.60),   # butter
           "passA2_skirt_panels": (1.00, 0.70, 0.48),   # peach
           "FS_Crown": (0.91, 0.72, 0.29),              # gold
           "FS_Wings": (0.95, 0.63, 0.66)}              # blush

for name, meshes in pieces.items():
    mat = bpy.data.materials.new(f"M_Preview_{name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*PREVIEW[name], 1.0)
    bsdf.inputs["Roughness"].default_value = 0.45
    for m in meshes:
        m.scale = (UNIT[name], UNIT[name], UNIT[name])
        m.data.materials.clear()
        m.data.materials.append(mat)

dress = pieces["passA2_shirt_panels"] + pieces["passA2_skirt_panels"]
mins = mathutils.Vector((1e9,) * 3)
maxs = mathutils.Vector((-1e9,) * 3)
for m in dress:
    for v in m.bound_box:
        w = m.matrix_world @ mathutils.Vector(v)
        mins = mathutils.Vector(map(min, mins, w))
        maxs = mathutils.Vector(map(max, maxs, w))
top_z, center_x = maxs.z, (mins.x + maxs.x) / 2
back_y = mins.y
height = top_z - mins.z

for m in pieces["FS_Crown"]:
    m.location = (center_x, (mins.y + maxs.y) / 2, top_z + 0.02)
for m in pieces["FS_Wings"]:
    # stand the flat-authored wings up and fan them above the skirt line
    m.rotation_euler = (math.radians(58), 0, math.radians(0))
    m.location = (center_x, back_y - 0.30, mins.z + height * 0.76)

# lighting: 3-point, meter-scale
def area_light(name, loc, rot, energy, size):
    li = bpy.data.lights.new(name, "AREA")
    li.energy = energy
    li.size = size
    ob = bpy.data.objects.new(name, li)
    ob.location = loc
    ob.rotation_euler = rot
    bpy.context.scene.collection.objects.link(ob)
    return ob

area_light("Key", (1.8, -2.4, height * 0.8), (math.radians(55), 0, math.radians(35)), 450, 2.0)
area_light("Rim", (-1.6, 1.8, height * 0.75), (math.radians(45), 0, math.radians(-125)), 320, 1.6)
fill = area_light("Fill", (-1.4, -2.0, 0.9), (math.radians(60), 0, math.radians(-30)), 160, 2.2)

cam = bpy.data.cameras.new("Cam")
cam.lens = 60
co = bpy.data.objects.new("Cam", cam)
bpy.context.scene.collection.objects.link(co)
scn = bpy.context.scene
scn.camera = co
mid = (mins + maxs) / 2
dist = height * 2.1
co.location = (mid.x + 0.4, mid.y - dist, mid.z + height * 0.10)
co.rotation_euler = (math.radians(89), 0, math.radians(9))

scn.render.engine = "BLENDER_EEVEE_NEXT"
scn.render.resolution_x = 1280
scn.render.resolution_y = 1280
scn.render.filepath = str(OUT / "FS_QA_front.png")
bpy.ops.render.render(write_still=True)

co.location = (mid.x - 0.3, mid.y + dist, mid.z + height * 0.1)
co.rotation_euler = (math.radians(85), 0, math.radians(194))
scn.render.filepath = str(OUT / "FS_QA_back.png")
bpy.ops.render.render(write_still=True)

(OUT / "flowerspring_assembly_manifest.json").write_text(json.dumps({
    "schema": "melodia.flowerspring_assembly.v2",
    "seed": 20260831,
    "unit_correction": UNIT,
    "dress_bounds_min": [round(v, 4) for v in mins],
    "dress_bounds_max": [round(v, 4) for v in maxs],
    "crown_radius_m": round(17.0 * UNIT["FS_Crown"], 4),
    "wing_fore_span_m": round(34.0 * UNIT["FS_Wings"], 4),
    "renders": ["FS_QA_front.png", "FS_QA_back.png"],
    "note": "preview materials are flat palette; final look = owner Substance paint",
}, indent=1), encoding="utf-8")
print("ASSEMBLY_OK " + json.dumps({k: len(v) for k, v in pieces.items()}))
