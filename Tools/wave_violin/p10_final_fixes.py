# -*- coding: utf-8 -*-
"""p10 — final fixes: orphan mats, f-hole scale, real spiral scroll, curved f-holes."""
import bpy, json, math, os
import bmesh
from mathutils import Vector

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p10] {m}", flush=True)
rep = {"phase": "p10", "ok": True}

def link_to(ob, cname):
    for c in list(ob.users_collection): c.objects.unlink(ob)
    bpy.data.collections[cname].objects.link(ob)

def kill(name):
    ob = bpy.data.objects.get(name)
    if ob:
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if me and getattr(me, "users", 1) == 0: bpy.data.meshes.remove(me)

# 1) assign missing mats
amber = bpy.data.materials.get("ME_MAT_Violin_AmberNight")
pearl = bpy.data.materials.get("ME_MAT_Violin_Pearl")
ebony = bpy.data.materials.get("ME_MAT_Violin_Ebony")
for nm in ("ME_WaveViolin_CBout_L", "ME_WaveViolin_CBout_R", "ME_WaveViolin_Pegbox"):
    ob = bpy.data.objects.get(nm)
    if ob and not ob.data.materials:
        ob.data.materials.append(amber)
        rep.setdefault("mats_assigned", []).append(nm)

# 2) real spiral scroll: archimedean volute, round profile
kill("ME_WaveViolin_Scroll")
cu = bpy.data.curves.new("ME_WaveViolin_Scroll_curve", "CURVE")
cu.dimensions = "3D"; cu.bevel_depth = 0.010; cu.bevel_resolution = 3; cu.resolution_u = 16
sp = cu.splines.new("POLY")
N = 40; sp.points.add(N - 1)
turns = 2.2
# lay the spiral in the Y-Z plane so it reads from the side like a real scroll
for i in range(N):
    t = i / (N - 1)
    a = t * turns * 2 * math.pi
    r = 0.032 * (1 - 0.72 * t)
    sp.points[i].co = (0.0, -r * math.sin(a), 0.640 + r * math.cos(a), 1.0)
scroll = bpy.data.objects.new("ME_WaveViolin_Scroll", cu)
link_to(scroll, "ME_WaveViolin_Assemblies")
scroll.data.materials.append(pearl)
# rebind crank driver (p03 pattern: control rot.x -PI/2..0 -> spin)
mc0 = bpy.data.objects["ME_WaveViolin_Control"]
fc = scroll.driver_add("rotation_euler", 2)
for v in list(fc.driver.variables): fc.driver.variables.remove(v)
fc.driver.expression = "((var + 1.5708) / 1.5708) * -6.2832"
v = fc.driver.variables.new(); v.name = "var"; v.type = 'SINGLE_PROP'
v.targets[0].id = mc0; v.targets[0].data_path = "rotation_euler[0]"
# taper handle from pegbox to volute
kill("ME_WaveViolin_ScrollNeck")
bm = bmesh.new()
prev = None
for i in range(7):
    t = i / 6
    v = bm.verts.new(Vector((0, 0.012 + 0.004 * t, 0.60 + 0.045 * t)))
    if prev: bm.edges.new((prev, v))
    prev = v
me = bpy.data.meshes.new("ME_WaveViolin_ScrollNeck")
bm.to_mesh(me); bm.free()
sn = bpy.data.objects.new("ME_WaveViolin_ScrollNeck", me)
sn.modifiers.new("ME_StringSkin", "SKIN")
for vv in me.skin_vertices[0].data: vv.radius = (0.011, 0.011)
link_to(sn, "ME_WaveViolin_Assemblies")
sn.data.materials.append(pearl)

# 3) f-holes: classic double-curve silhouette via poly-curve + skin, flanking bridge
for s, zn in ((-1, "L"), (1, "R")):
    nm = f"ME_WaveViolin_FHole_{zn}"
    kill(nm)
    bm = bmesh.new()
    pts = []
    zs = [0.06, 0.03, 0.00, -0.03, -0.06, -0.09, -0.12]
    offs = [0.010, 0.002, -0.004, -0.006, -0.004, 0.002, 0.010]
    prev = None
    for z, o in zip(zs, offs):
        v = bm.verts.new(Vector((s * 0.046 + s * o, -0.0365, -0.05 + z)))
        pts.append(v)
        if prev: bm.edges.new((prev, v))
        prev = v
    me = bpy.data.meshes.new(nm)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(nm, me)
    ob.modifiers.new("ME_FHoleSkin", "SKIN")
    radii = [0.0055, 0.0028, 0.0022, 0.0022, 0.0028, 0.0055, 0.0065]
    for vv, rr in zip(me.skin_vertices[0].data, radii):
        vv.radius = (rr, rr)
    link_to(ob, "ME_WaveViolin_Assemblies")
    vg = bpy.data.materials.get(f"ME_MAT_Violin_VentGlow_{zn}")
    ob.data.materials.append(vg or ebony)

# render both pose plates + save
scn = bpy.context.scene
scn.camera = bpy.data.objects["ME_WaveViolin_Cam_Presentation"]
mc = bpy.data.objects["ME_WaveViolin_Control"]
for tag, rx in (("stow", -1.5708), ("deploy", 0.0)):
    mc.rotation_euler.x = rx
    bpy.context.view_layer.update()
    scn.render.filepath = os.path.join(OUT, f"p10_{tag}.png")
    bpy.ops.render.render(write_still=True)
mc.rotation_euler.x = -1.5708
bpy.ops.wm.save_mainfile()
json.dump(rep, open(os.path.join(OUT, "p10_report.json"), "w"), indent=1)
log("done")
