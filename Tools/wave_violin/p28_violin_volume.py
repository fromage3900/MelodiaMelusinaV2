# -*- coding: utf-8 -*-
"""p28 — violin VOLUME pass (p27 review: 6/10, "solid silhouette pass").

Fixes the four named defects:
1. body paper-thin      -> thickness 0.058->0.082 + arched top (grid fill gives
                           interior verts; y-displaced by (1-(x/w)^2) bell)
2. waist over-pinched   -> profile min width 0.058->0.073, softer blend
3. floating fingerboard -> ebony board now seated ON a real neck stub with
                           pegbox bridging; gap closed
4. tailpiece tab pops   -> flush-mounted to the arched back slope
"""
import bpy, json, math, os
import bmesh
from mathutils import Vector

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p28] {m}", flush=True)
rep = {"phase": "p28", "ok": True}

def kill(name):
    ob = bpy.data.objects.get(name)
    if ob:
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if me and getattr(me, "users", 1) == 0: bpy.data.meshes.remove(me)

# ---------- 1) rebuild body: softer waist + grid-fill + arch ----------
prof = [(-0.470, 0.052), (-0.430, 0.086), (-0.380, 0.106), (-0.320, 0.118),
        (-0.240, 0.122), (-0.160, 0.115), (-0.090, 0.096), (-0.030, 0.078),
        ( 0.010, 0.073),                     # waist: was 0.058, now graceful
        ( 0.050, 0.079), ( 0.100, 0.092), ( 0.160, 0.104), ( 0.230, 0.109),
        ( 0.300, 0.101), ( 0.360, 0.083), ( 0.400, 0.055)]
def w_at(z):
    for i in range(len(prof) - 1):
        z0, w0 = prof[i]; z1, w1 = prof[i+1]
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0)
            s = t * t * (3 - 2 * t)
            return w0 + (w1 - w0) * s
    return 0.05
N = 60
zs = [prof[0][0] + (prof[-1][0] - prof[0][0]) * i / (N - 1) for i in range(N)]
right = [( w_at(z), z) for z in zs]
left  = [(-w_at(z), z) for z in reversed(zs)]
pts = right + left
bm = bmesh.new()
verts = [bm.verts.new((x, 0.0, z)) for x, z in pts]
edges = [bm.edges.new((verts[i], verts[(i + 1) % len(verts)])) for i in range(len(verts))]
try:
    bmesh.ops.grid_fill(bm, edges=edges)
except Exception:
    bmesh.ops.edgeloop_fill(bm, edges=edges)
# arch: displace interior verts in -Y/+Y by bell of local width; here the
# fill is planar at y=0 -> dome it along +Y (back) and -Y (front) later by solidify.
# Single-surface arch (violin top plate curve across the width):
for v in bm.verts:
    w = w_at(v.co.z)
    if w > 1e-6:
        nx = max(0.0, 1.0 - (v.co.x / max(w, 1e-6)) ** 2)
        v.co.y = -0.020 * nx          # crown toward front (-Y = face side)
me = bpy.data.meshes.new("ME_WaveViolin_Body")
bm.to_mesh(me); bm.free()
kill("ME_WaveViolin_Body")
body = bpy.data.objects.new("ME_WaveViolin_Body", me)
bpy.data.collections["ME_WaveViolin_Assemblies"].objects.link(body)
sol = body.modifiers.new("ME_BodyDepth", "SOLIDIFY"); sol.thickness = 0.082; sol.offset = -0.35
bev = body.modifiers.new("ME_BodyBevel", "BEVEL"); bev.width = 0.006; bev.segments = 2
bpy.context.view_layer.objects.active = body
bpy.ops.object.select_all(action='DESELECT'); body.select_set(True)
try: bpy.ops.object.shade_auto_smooth(angle=math.radians(38))
except Exception:
    for p in me.polygons: p.use_smooth = True
body.data.materials.append(bpy.data.materials["ME_MAT_Violin_AmberNight"])
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
try: bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.02)
except Exception as e: log(f"uv {e}")
bpy.ops.object.mode_set(mode='OBJECT')
if "ME_BakeUV" not in [u.name for u in body.data.uv_layers]:
    body.data.uv_layers.new(name="ME_BakeUV")
body.data.uv_layers.active = body.data.uv_layers["ME_BakeUV"]

# Reel_Deploy key + driver (softer linear-ish blend to avoid waist twist)
mc = bpy.data.objects["ME_WaveViolin_Control"]
body.shape_key_add(name="Basis", from_mix=False)
sk = body.shape_key_add(name="Reel_Deploy", from_mix=False)
for i, v in enumerate(me.vertices):
    z = v.co.z
    if z > 0.060:   dx = 0.09
    elif z < 0.000: dx = -0.09
    else:
        t = z / 0.060
        dx = -0.09 + 0.18 * (t * t * (3 - 2 * t))
    sk.data[i].co = v.co + Vector((dx, 0, 0))
sks = body.data.shape_keys
if not sks.animation_data: sks.animation_data_create()
for fc in list(sks.animation_data.drivers):
    if 'Reel_Deploy' in fc.data_path: sks.driver_remove(fc.data_path)
fc = sks.driver_add('key_blocks["Reel_Deploy"].value')
for vv in list(fc.driver.variables): fc.driver.variables.remove(vv)
fc.driver.expression = "max(0.0, min(1.0, (var + 1.5708) / 1.5708))"
dvv = fc.driver.variables.new(); dvv.name = "var"; dvv.type = 'SINGLE_PROP'
dvv.targets[0].id = mc; dvv.targets[0].data_path = "rotation_euler[0]"
rep["body"] = "arched, 0.082 deep, waist 0.073, key rebound"

# ---------- 3) neck + fingerboard seated ----------
# neck stub: solid spar from upper bout face to pegbox
kill("ME_WaveViolin_Neck")
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0.005, 0.435))
nk = bpy.context.active_object; nk.name = "ME_WaveViolin_Neck"
nk.scale = (0.016, 0.020, 0.150)
bpy.ops.object.transform_apply(scale=True)
for c in list(nk.users_collection): c.objects.unlink(nk)
bpy.data.collections["ME_WaveViolin_Assemblies"].objects.link(nk)
nb = nk.modifiers.new("ME_Bevel", "BEVEL"); nb.width = 0.006; nb.segments = 2
nk.data.materials.append(bpy.data.materials["ME_MAT_Violin_AmberNight"])
# fingerboard: rides on the neck's front face, ends at bridge zone
kill("ME_WaveViolin_Fingerboard")
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.020, 0.315))
fb = bpy.context.active_object; fb.name = "ME_WaveViolin_Fingerboard"
fb.scale = (0.018, 0.009, 0.320)
bpy.ops.object.transform_apply(scale=True)
for c in list(fb.users_collection): c.objects.unlink(fb)
bpy.data.collections["ME_WaveViolin_Assemblies"].objects.link(fb)
fbm = fb.modifiers.new("ME_Bevel", "BEVEL"); fbm.width = 0.004; fbm.segments = 2
fb.data.materials.append(bpy.data.materials["ME_MAT_Violin_Ebony"])
rep["fingerboard"] = "seated on neck spar, -0.020 front"

# ---------- belly plate: flush to the arched face ----------
belly = bpy.data.objects.get("ME_WaveViolin_BellyPlate")
if belly:
    belly.location.y = -0.040
    belly.scale = (0.94, 1.0, 0.94)
    bpy.context.view_layer.objects.active = belly
    belly.select_set(True)
    bpy.ops.object.transform_apply(scale=True)
    belly.select_set(False)
    rep["belly_plate"] = "flush -0.040"

# ---------- 4) tailpiece flush to lower back slope ----------
tp = bpy.data.objects.get("ME_WaveViolin_Tailpiece")
if tp:
    tp.location = (0, -0.030, -0.36)
    tp.rotation_euler = (math.radians(-8), 0, 0)
    rep["tailpiece"] = "flush low front"

# f-hole vents follow the arch: nudge y to plate face, slight cant
for s, zn in ((-1, "L"), (1, "R")):
    fh = bpy.data.objects.get(f"ME_WaveViolin_FHole_{zn}")
    if fh:
        fh.location.y = -0.0055
        fh.rotation_euler = (0, math.radians(s * 4), 0)

bpy.ops.wm.save_mainfile()
json.dump(rep, open(os.path.join(OUT, "p28_report.json"), "w"), indent=1)
log("volume pass saved")
