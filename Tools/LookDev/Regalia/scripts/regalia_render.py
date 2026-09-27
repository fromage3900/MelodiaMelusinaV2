"""Render the circlet against the head proxy, HEADLESS, from the contract file.

Deliberately separate from the live session: a render over MCP blocked the socket
and the 2.4 GB file is unsafe to open headless. This opens only the 106 KB
regalia_contract.blend, so a crash here costs nothing.

Run: blender -b regalia_contract.blend --python regalia_render.py
"""

import bpy
import math
import os
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = HERE

# head axis, from regalia_landmarks.json
BROW = (-0.0044, -0.1335, 1.560)
TARGET = Vector((BROW[0], BROW[1], BROW[2]))

scn = bpy.context.scene
scn.render.engine = "BLENDER_EEVEE"
scn.render.resolution_x = 900
scn.render.resolution_y = 1100
scn.render.film_transparent = False
scn.view_settings.exposure = -0.2
# AgX (the default) desaturates strong emission; the surreal gem palette needs
# Standard. Verified on the stone sheet: mean saturation 0.46, clipped 0.000.
scn.view_settings.view_transform = "Standard"
scn.view_settings.look = "None"
try:
    scn.eevee.taa_render_samples = 64
except Exception:
    pass

# a gold material so the metal reads as metal
gold = bpy.data.materials.get("REGALIA_GOLD")
if gold is None:
    gold = bpy.data.materials.new("REGALIA_GOLD")
    gold.use_nodes = True
    bsdf = gold.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.83, 0.66, 0.30, 1.0)
        bsdf.inputs["Metallic"].default_value = 1.0
        bsdf.inputs["Roughness"].default_value = 0.25
# DO NOT repaint the object's materials. The GN tree assigns gold to the band and
# scrolls and REGALIA_STONE to the gems; clearing this list and appending gold
# repainted every face gold and erased the stones (they rendered as gold knobs).
ob = bpy.data.objects.get("Melusina_Circlet")
if ob is not None and len(ob.data.materials) == 0:
    ob.data.materials.append(gold)

# the proxy head, so the fit is visible
head = bpy.data.objects.get("Melusina_HeadProxy")
if head is not None:
    hm = bpy.data.materials.get("REGALIA_SKIN")
    if hm is None:
        hm = bpy.data.materials.new("REGALIA_SKIN")
        hm.use_nodes = True
        b2 = hm.node_tree.nodes.get("Principled BSDF")
        if b2:
            b2.inputs["Base Color"].default_value = (0.42, 0.36, 0.34, 1.0)
            b2.inputs["Roughness"].default_value = 0.6
    head.data.materials.clear()
    head.data.materials.append(hm)

# three-point rig
for nm, loc, energy, size in (("K", (0.85, -1.05, 2.15), 120, 1.1),
                              ("F", (-1.05, -0.75, 1.45), 45, 1.5),
                              ("R", (-0.25, 1.05, 1.85), 90, 0.8)):
    ld = bpy.data.lights.get("REGALIA_" + nm) or bpy.data.lights.new("REGALIA_" + nm, "AREA")
    ld.energy = energy
    ld.size = size
    lo = bpy.data.objects.get("REGALIA_" + nm)
    if lo is None:
        lo = bpy.data.objects.new("REGALIA_" + nm, ld)
        scn.collection.objects.link(lo)
    lo.location = loc

cam_data = bpy.data.cameras.get("REGALIA_CAM") or bpy.data.cameras.new("REGALIA_CAM")
cam_data.lens = 90
cam_data.clip_start = 0.01
cam = bpy.data.objects.get("REGALIA_CAM")
if cam is None:
    cam = bpy.data.objects.new("REGALIA_CAM", cam_data)
    scn.collection.objects.link(cam)
scn.camera = cam


def place(loc, target=TARGET):
    cam.location = Vector(loc)
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


# Camera distances chosen so the whole 0.41 x 0.46 x 0.52 head fits with margin.
# The first pass framed only the brow and the circlet was cropped out entirely.
SHOTS = {
    # she faces -Y, so the camera sits at -Y looking back at her
    "circlet_front": ((0.0, -1.35, 1.60), None),
    "circlet_side": ((1.30, -0.14, 1.60), None),
    "circlet_threequarter": ((1.00, -1.00, 1.92), None),
    "circlet_top": ((0.0, -0.62, 2.55), None),
}

for name, (loc, _) in SHOTS.items():
    place(loc)
    scn.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    print("SHOT", name, os.path.exists(scn.render.filepath))
print("RENDER-COMPLETE")
