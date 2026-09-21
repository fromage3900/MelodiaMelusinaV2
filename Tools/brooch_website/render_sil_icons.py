# READ-ONLY icon-gate script for the silhouette presets (no save).
# Builds each preset runtime-only (Tools/brooch_silhouettes.py), renders beauty +
# white-field silhouette icons at 256/128/64 native pixels per the FULL_PLAN P1 gate.
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, r"P:/MelodiaMelusinaV2-Laptop/Tools")
import brooch_silhouettes as sil

OUT = r"P:/MelodiaMelusinaV2-Laptop/Website/Brooch/_evidence/sil_icons/"
os.makedirs(OUT, exist_ok=True)
scn = bpy.context.scene
scn.frame_set(1)

hero = bpy.data.objects["FlowerBrooch"]
petals = bpy.data.objects.get("FlowerBrooch_Petals")
dangles = bpy.data.objects.get("FlowerBrooch_Dangles")
sparkles = bpy.data.objects.get("FlowerBrooch_Sparkles")
for ob in (dangles, sparkles):
    if ob:
        ob.hide_render = True

world0 = scn.world
vt0 = scn.view_settings.view_transform

black = bpy.data.materials.get("SIL_BlackEmit")
if black is None:
    black = bpy.data.materials.new("SIL_BlackEmit")
black.use_nodes = True
nt = black.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
em = nt.nodes.new('ShaderNodeEmission')
em.inputs['Color'].default_value = (0, 0, 0, 1)
em.inputs['Strength'].default_value = 1.0
outn = nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(em.outputs['Emission'], outn.inputs['Surface'])


def white_field(on):
    if on:
        w = bpy.data.worlds.get("ICON_White")
        if w is None:
            w = bpy.data.worlds.new("ICON_White")
            w.use_nodes = True
            for n in w.node_tree.nodes:
                if n.type == 'BACKGROUND':
                    n.inputs['Color'].default_value = (1, 1, 1, 1)
                    n.inputs['Strength'].default_value = 1.0
        scn.world = w
        scn.view_settings.view_transform = 'Standard'
    else:
        scn.world = world0
        scn.view_settings.view_transform = vt0


def frame_shot(objs, tag, sizes=(256, 128, 64)):
    bpy.context.view_layer.update()
    lo, hi = sil.measured_bbox(objs)
    ctr = (lo + hi) * 0.5
    size = max((hi - lo).x, (hi - lo).y, (hi - lo).z)
    cam = bpy.data.objects["LAB_Cam"]
    scn.camera = cam
    cam.data.lens = 60.0
    d = size * 1.9
    loc = Vector((0.0, -d, ctr.z + size * 0.05))
    cam.location = loc
    v = (ctr - loc).normalized()
    cam.rotation_euler = v.to_track_quat('-Z', 'Y').to_euler()
    for s in sizes:
        scn.render.resolution_x = s
        scn.render.resolution_y = s
        scn.render.filepath = OUT + "%s_%d.png" % (tag, s)
        bpy.ops.render.render(write_still=True)
    print("[icon] shot:", tag)


for p in ("flower", "star_citadel", "lissajous_veil"):
    sil_ob = None
    if p != "flower":
        info = sil.build_silhouette(p, hero=hero)
        sil_ob = info["object"]
    for ob in (hero, petals, sil_ob):
        if ob:
            ob.hide_render = False
    bpy.context.view_layer.update()
    frame_shot([o for o in (hero, petals, sil_ob) if o], p + "_beauty")
    if petals:
        petals.hide_render = True
    sm = None
    if sil_ob:
        sm = next(n for n in sil_ob.modifiers[0].node_group.nodes
                  if n.type == 'SET_MATERIAL')
        sm.inputs['Material'].default_value = black
    white_field(True)
    bpy.context.view_layer.update()
    frame_shot([o for o in (hero, sil_ob) if o], p + "_sil")
    white_field(False)
    if sm is not None:
        gold = bpy.data.materials.get(sil.SIL_GOLD)
        sm.inputs['Material'].default_value = gold
    if sil_ob:
        sil_ob.hide_render = True

for ob in (dangles, sparkles):
    if ob:
        ob.hide_render = False
print("ICON GATE RENDERS DONE")
