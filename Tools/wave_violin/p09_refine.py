# -*- coding: utf-8 -*-
"""p09 — shape refine: real violin silhouette per the 6/10 review.

Fixes: (1) pinched C-bout waist instead of straight cube block,
(2) slender neck + pegbox bridging to scroll,
(3) instrument logic: strings down center over a proper bridge,
    f-holes flanking the bridge, tailpiece anchored below.
Keeps object names stable so p02/p03/p04 reruns re-bind everything.
"""
import bpy, json, math, os
import numpy as np
import bmesh
from mathutils import Vector

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p09] {m}", flush=True)
COLL = "ME_WaveViolin_Assemblies"

def kill(name):
    ob = bpy.data.objects.get(name)
    if ob:
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if me and me.users == 0: bpy.data.meshes.remove(me)

def profiled_lobe(name, z0, z1, keys, depth, verts=36):
    """cylinder along Y whose XZ cross-section half-width follows keys(z)."""
    kill(name)
    bm = bmesh.new()
    zs = np.linspace(0, 1, 9)
    zkeys = np.array([k[0] for k in keys]); wk = np.array([k[1] for k in keys])
    rings = []
    for t in zs:
        z = z0 + (z1 - z0) * t
        w = float(np.interp(t, zkeys, wk))
        ring = []
        for i in range(verts):
            a = 2 * math.pi * i / verts
            x = w * math.cos(a) * (1.0 if abs(math.cos(a)) < 0.999 else 1.0)
            zz = z + (z1 - z0) * 0.06 * math.sin(a) * 0.0  # keep circular in X, flatten z-mod
            ring.append((bm.verts.new((x, -depth/2, z)), bm.verts.new((x, depth/2, z))))
        rings.append(ring)
    # bridge rings with quads on both faces + cap ends
    for ri in range(len(rings) - 1):
        for i in range(verts):
            j = (i + 1) % verts
            a, b = rings[ri][i], rings[ri][j]
            c, d = rings[ri+1][i], rings[ri+1][j]
            try:
                bm.faces.new((a[0], b[0], d[0], c[0]))   # front
                bm.faces.new((b[1], a[1], c[1], d[1]))   # back
            except ValueError:
                pass
    # side wall between front/back of each ring
    for ring in rings:
        for i in range(verts):
            a, b = ring[i], ring[(i+1) % verts]
            try: bm.faces.new((a[1], a[0], b[0], b[1]))
            except ValueError: pass
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.data.collections[COLL].objects.link(ob)
    bev = ob.modifiers.new("ME_Bevel", "BEVEL"); bev.width = 0.004; bev.segments = 2
    for p in me.polygons: p.use_smooth = True
    return ob

# --- (1) lobes with violin half-width profiles (t-local) ---
upper = profiled_lobe("ME_WaveViolin_UpperBout", 0.095, 0.40,
    [(0.0, 0.064), (0.35, 0.088), (0.75, 0.106), (1.0, 0.062)], 0.055)
lower = profiled_lobe("ME_WaveViolin_LowerBout", -0.47, 0.015,
    [(0.0, 0.052), (0.28, 0.108), (0.62, 0.120), (0.86, 0.096), (1.0, 0.064)], 0.055)
# waist: narrow connector + C-bout corner blocks
kill("ME_WaveViolin_Waist")
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0.055))
waist = bpy.context.active_object; waist.name = "ME_WaveViolin_Waist"
waist.scale = (0.060, 0.026, 0.065)
bpy.ops.object.transform_apply(scale=True)
for c in list(waist.users_collection): c.objects.unlink(waist)
bpy.data.collections[COLL].objects.link(waist)
for s in (-1, 1):
    cn = f"ME_WaveViolin_CBout_{'L' if s < 0 else 'R'}"
    kill(cn)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(s * 0.072, 0, 0.055))
    cb = bpy.context.active_object; cb.name = cn
    cb.scale = (0.020, 0.024, 0.055)
    bpy.ops.object.transform_apply(scale=True)
    for c in list(cb.users_collection): c.objects.unlink(cb)
    bpy.data.collections[COLL].objects.link(cb)
    mb = cb.modifiers.new("ME_Bevel", "BEVEL"); mb.width = 0.005; mb.segments = 2

# --- belly plate flush to new front ---
kill("ME_WaveViolin_BellyPlate")
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.033, -0.02))
belly = bpy.context.active_object; belly.name = "ME_WaveViolin_BellyPlate"
belly.scale = (0.098, 0.004, 0.42)
bpy.ops.object.transform_apply(scale=True)
for c in list(belly.users_collection): c.objects.unlink(belly)
bpy.data.collections[COLL].objects.link(belly)
mb = belly.modifiers.new("ME_Bevel", "BEVEL"); mb.width = 0.008; mb.segments = 3

# --- (2) slender neck + pegbox ---
kill("ME_WaveViolin_Neck")
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.010, 0.44))
neck = bpy.context.active_object; neck.name = "ME_WaveViolin_Neck"
neck.scale = (0.015, 0.011, 0.16)
bpy.ops.object.transform_apply(scale=True)
for c in list(neck.users_collection): c.objects.unlink(neck)
bpy.data.collections[COLL].objects.link(neck)
kill("ME_WaveViolin_Pegbox")
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.012, 0.575))
pb = bpy.context.active_object; pb.name = "ME_WaveViolin_Pegbox"
pb.scale = (0.020, 0.016, 0.055)
bpy.ops.object.transform_apply(scale=True)
for c in list(pb.users_collection): c.objects.unlink(pb)
bpy.data.collections[COLL].objects.link(pb)
# move scroll onto pegbox top
scr = bpy.data.objects.get("ME_WaveViolin_Scroll")
if scr: scr.location = (0, 0.014, 0.635)

# fingerboard: long, over neck, to just past upper bout
kill("ME_WaveViolin_Fingerboard")
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.004, 0.42))
fb = bpy.context.active_object; fb.name = "ME_WaveViolin_Fingerboard"
fb.scale = (0.019, 0.011, 0.27)
bpy.ops.object.transform_apply(scale=True)
for c in list(fb.users_collection): c.objects.unlink(fb)
bpy.data.collections[COLL].objects.link(fb)

# --- (3) instrument logic: bridge between f-holes, strings over it ---
kill("ME_WaveViolin_BridgeHub")
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.0375, -0.02))
br = bpy.context.active_object; br.name = "ME_WaveViolin_BridgeHub"
br.scale = (0.034, 0.003, 0.016)
bpy.ops.object.transform_apply(scale=True)
for c in list(br.users_collection): c.objects.unlink(br)
bpy.data.collections[COLL].objects.link(br)
mb = br.modifiers.new("ME_Bevel", "BEVEL"); mb.width = 0.003; mb.segments = 2

for s, zn in ((-1, "L"), (1, "R")):
    cn = f"ME_WaveViolin_FHole_{zn}"
    kill(cn)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(s * 0.048, -0.0355, -0.06))
    fh = bpy.context.active_object; fh.name = cn
    fh.scale = (0.005, 0.002, 0.075)
    fh.rotation_euler = (0, math.radians(-s * 6), 0)
    for c in list(fh.users_collection): c.objects.unlink(fh)
    bpy.data.collections[COLL].objects.link(fh)

# tailpiece below bridge on the lower bout slope
tp = bpy.data.objects.get("ME_WaveViolin_Tailpiece")
if tp:
    tp.location = (0, -0.028, -0.34)

# strings: fan from bridge foot (±0.008) up to pegbox (±0.014)
for i in (1, 2, 3, 4):
    kill(f"ME_WaveViolin_String_{i}")
xs_bot = np.linspace(-0.009, 0.009, 4)
xs_top = np.linspace(-0.0135, 0.0135, 4)
for i in range(4):
    x0, x1 = float(xs_bot[i]), float(xs_top[i])
    z0, z1 = -0.015, 0.60
    y0, y1 = -0.0415, -0.021
    kill(f"ME_WaveViolin_String_{i+1}")
    bm = bmesh.new()
    segs = 12
    prev = None
    for sidx in range(segs + 1):
        t = sidx / segs
        x = x0 + (x1 - x0) * t
        z = z0 + (z1 - z0) * t
        y = y0 + (y1 - y0) * t - math.sin(t * math.pi) * 0.004  # slight arc off the plate
        v = bm.verts.new((x, y, z))
        if prev: bm.edges.new((prev, v))
        prev = v
    me = bpy.data.meshes.new(f"ME_WaveViolin_String_{i+1}")
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(f"ME_WaveViolin_String_{i+1}", me)
    md = ob.modifiers.new("ME_StringSkin", "SKIN")
    for vv in me.skin_vertices[0].data: vv.radius = (0.0013, 0.0013)
    bpy.data.collections["ME_WaveViolin_Strings"].objects.link(ob)

log("geometry refined; re-chaining p02 -> p03 -> p04 via saved file")
bpy.ops.wm.save_mainfile()
json.dump({"phase": "p09", "ok": True, "rebuilt": ["lobes", "waist+cbouts", "belly", "neck+pegbox",
          "bridge", "fholes", "tailpiece", "strings"]},
          open(os.path.join(OUT, "p09_report.json"), "w"), indent=1)
