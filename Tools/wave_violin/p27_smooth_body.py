# -*- coding: utf-8 -*-
"""p27 — SMOOTH BODY: replace faceted blockout lobes with one true violin
silhouette mesh (profile curve -> ngon -> solidify -> bevel), rebuild the
Reel_Deploy split as a shape key with driver, restore fingerboard continuity.

Owner verdict 'looks busted' -> root art cause: bouts are stacked cylinders
+ corner boxes; at turn angles they read as a segmented platter. This pass is
the p02-level refinement that was never re-run on refined topology.
"""
import bpy, json, math, os
import bmesh
from mathutils import Vector

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p27] {m}", flush=True)
rep = {"phase": "p27", "ok": True}

def kill(name):
    ob = bpy.data.objects.get(name)
    if ob:
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if me and getattr(me, "users", 1) == 0: bpy.data.meshes.remove(me)

# ---------- violin half-width profile (z, w) ----------
prof = [(-0.470, 0.050), (-0.430, 0.084), (-0.380, 0.104), (-0.320, 0.117),
        (-0.240, 0.121), (-0.160, 0.114), (-0.090, 0.090), (-0.030, 0.064),
        ( 0.010, 0.058),   # waist
        ( 0.050, 0.064), ( 0.100, 0.082), ( 0.160, 0.101), ( 0.230, 0.107),
        ( 0.300, 0.099), ( 0.360, 0.080), ( 0.400, 0.052)]
# smooth-sample: Catmull-ish via numpy interp + sine blend is enough
import bisect
def w_at(z):
    for i in range(len(prof) - 1):
        z0, w0 = prof[i]; z1, w1 = prof[i+1]
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0)
            s = t * t * (3 - 2 * t)          # smoothstep
            return w0 + (w1 - w0) * s
    return 0.05

# closed outline: right side up, left side down
zs = []
N = 60
for i in range(N):
    zs.append(prof[0][0] + (prof[-1][0] - prof[0][0]) * i / (N - 1))
right = [( w_at(z), z) for z in zs]
left  = [(-w_at(z), z) for z in reversed(zs)]
pts = right + left

bm = bmesh.new()
verts = [bm.verts.new((x, 0.0, z)) for x, z in pts]
edges = [bm.edges.new((verts[i], verts[(i + 1) % len(verts)])) for i in range(len(verts))]
bmesh.ops.edgeloop_fill(bm, edges=edges)
me = bpy.data.meshes.new("ME_WaveViolin_Body")
bm.to_mesh(me); bm.free()
body = bpy.data.objects.new("ME_WaveViolin_Body", me)
bpy.data.collections["ME_WaveViolin_Assemblies"].objects.link(body)

sol = body.modifiers.new("ME_BodyDepth", "SOLIDIFY"); sol.thickness = 0.058; sol.offset = 0.15
bev = body.modifiers.new("ME_BodyBevel", "BEVEL"); bev.width = 0.006; bev.segments = 2
try:
    bpy.context.view_layer.objects.active = body
    body.select_set(True)
    bpy.ops.object.shade_auto_smooth(angle=math.radians(38))
    body.select_set(False)
except Exception:
    for p in me.polygons: p.use_smooth = True

# replace old blockout parts
for nm in ("ME_WaveViolin_UpperBout", "ME_WaveViolin_LowerBout", "ME_WaveViolin_Waist",
           "ME_WaveViolin_CBout_L", "ME_WaveViolin_CBout_R"):
    kill(nm)
amber = bpy.data.materials["ME_MAT_Violin_AmberNight"]
body.data.materials.append(amber)

# UVs: smart + bake layer
bpy.context.view_layer.objects.active = body
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True)
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
try:
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
except Exception as e:
    log(f"uv: {e}")
bpy.ops.object.mode_set(mode='OBJECT')
if "ME_BakeUV" not in [u.name for u in body.data.uv_layers]:
    body.data.uv_layers.new(name="ME_BakeUV")
body.data.uv_layers.active = body.data.uv_layers["ME_BakeUV"]

# ---------- Reel_Deploy split shape key + driver (p03 pattern) ----------
mc = bpy.data.objects["ME_WaveViolin_Control"]
EXPR_T = "max(0.0, min(1.0, (var + 1.5708) / 1.5708))"
body.shape_key_add(name="Basis", from_mix=False)
sk = body.shape_key_add(name="Reel_Deploy", from_mix=False)
for i, v in enumerate(me.vertices):
    z = v.co.z
    if z > 0.045:
        dx = 0.09
    elif z < -0.015:
        dx = -0.09
    else:
        t = (z + 0.015) / 0.06
        dx = -0.09 + 0.18 * (t * t * (3 - 2 * t))
    sk.data[i].co = v.co + Vector((dx, 0, 0))
sks = body.data.shape_keys
if not sks.animation_data: sks.animation_data_create()
fc = sks.driver_add('key_blocks["Reel_Deploy"].value')
for vv in list(fc.driver.variables): fc.driver.variables.remove(vv)
fc.driver.expression = EXPR_T
dvv = fc.driver.variables.new(); dvv.name = "var"; dvv.type = 'SINGLE_PROP'
dvv.targets[0].id = mc; dvv.targets[0].data_path = "rotation_euler[0]"
rep["deploy_key"] = "smooth body Reel_Deploy bound to control"

# ---------- fingerboard continuity: extend to bridge, ebony ----------
fb = bpy.data.objects.get("ME_WaveViolin_Fingerboard")
if fb:
    kill("ME_WaveViolin_Fingerboard")
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.028, 0.30))
fb = bpy.context.active_object; fb.name = "ME_WaveViolin_Fingerboard"
fb.scale = (0.017, 0.008, 0.34)
bpy.ops.object.transform_apply(scale=True)
for c in list(fb.users_collection): c.objects.unlink(fb)
bpy.data.collections["ME_WaveViolin_Assemblies"].objects.link(fb)
bev = fb.modifiers.new("ME_Bevel", "BEVEL"); bev.width = 0.004; bev.segments = 2
fb.data.materials.append(bpy.data.materials["ME_MAT_Violin_Ebony"])
if "ME_BakeUV" not in [u.name for u in fb.data.uv_layers]:
    if not fb.data.uv_layers: fb.data.uv_layers.new(name="UVMap")
    fb.data.uv_layers.new(name="ME_BakeUV")
rep["fingerboard"] = "ebony run pegbox->bridge"

bpy.ops.wm.save_mainfile()
json.dump(rep, open(os.path.join(OUT, "p27_report.json"), "w"), indent=1)
log("body smoothed + rig rebound; saved")
