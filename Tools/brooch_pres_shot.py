"""brooch_pres_shot.py — render the luxury still set with PRES_RIG (outline off, 3 views).

Usage: blender -b FlowerBrooch.blend --python Tools/brooch_pres_shot.py
Writes Saved/Audit/pres_front.png / pres_tq.png / pres_macro.png
"""
import bpy
import math
from mathutils import Vector

OUT = r"P:/MelodiaMelusinaV2-Laptop/Saved/Audit/"


def _arg(name, default=None):
    import sys
    a = sys.argv
    if name in a:
        i = a.index(name)
        if i + 1 < len(a):
            return a[i + 1]
    return default


SKY = _arg("--sky", None)
PREFIX = ("sky_%s_" % SKY) if SKY else "pres_"

scn = bpy.context.scene
scn.frame_set(1)
if bpy.data.collections.get("PRES_RIG") is None:
    print("PRES_RIG missing -- run Tools/brooch_pres_rig.py first")
    raise SystemExit(1)

# frame from the MEASURED piece bbox (robust against aim drift)
dg = bpy.context.evaluated_depsgraph_get()
lo = Vector((1e9, 1e9, 1e9))
hi = Vector((-1e9, -1e9, -1e9))
for nm in ("FlowerBrooch", "FlowerBrooch_Dangles"):
    o = bpy.data.objects.get(nm)
    if not o:
        continue
    ev = o.evaluated_get(dg)
    for c in ev.bound_box:
        w = ev.matrix_world @ Vector(c)
        lo = Vector((min(lo[i], w[i]) for i in range(3)))
        hi = Vector((max(hi[i], w[i]) for i in range(3)))
ctr = (lo + hi) * 0.5
size = max((hi - lo).x, (hi - lo).y, (hi - lo).z)
print("piece bbox center %.3f %.3f %.3f size %.3f" % (ctr.x, ctr.y, ctr.z, size))

cam = bpy.data.objects.get("LAB_Cam")
scn.camera = cam
cam.data.lens = 60.0
scn.render.resolution_x = 1600
scn.render.resolution_y = 2000
scn.render.resolution_percentage = 100

# luxury stills: toon outline off (game-look device; restore after)
saved = []
for nm in ("FlowerBrooch", "FlowerBrooch_Dangles"):
    o = bpy.data.objects.get(nm)
    if not o:
        continue
    for m in o.modifiers:
        if m.name.startswith("Outline"):
            saved.append((m, m.show_render))
            m.show_render = False


def aim(loc, tgt):
    cam.location = Vector(loc)
    d = (Vector(tgt) - Vector(loc)).normalized()
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


D = size * 1.35
shots = (
    (PREFIX + "front.png", (0.0, -D, ctr.z + size * 0.10), ctr, 60.0),
    (PREFIX + "tq.png", (-D * 0.68, -D * 0.80, ctr.z + size * 0.42), ctr, 60.0),
    (PREFIX + "macro.png", (-size * 0.35, -size * 0.80, ctr.z - size * 0.10),
     Vector((ctr.x, ctr.y, ctr.z - size * 0.16)), 70.0),
)
for fname, loc, tgt, lens in shots:
    cam.data.lens = lens
    aim(loc, tgt)
    scn.render.filepath = OUT + fname
    bpy.ops.render.render(write_still=True)
    print("shot:", scn.render.filepath)

for m, v in saved:
    m.show_render = v
print("done pres shots")
