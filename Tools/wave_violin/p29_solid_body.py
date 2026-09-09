# -*- coding: utf-8 -*-
"""p29 — REAL body: parametric arched violin plate (explicit grid mesh).

Root cause found: p27/p28 body meshes had 120 verts and ZERO polygons — the
edgeloop/grid fill silently produced nothing, so the body never rendered;
tailpiece/endpin "floated" because there was no plate behind them.
Fix: build the surface deterministically as a z-by-x grid (no fill operators),
arched crown, planar UVs written by hand, Reel_Deploy key + driver rebound.
"""
import bpy, json, math, os
import bmesh
from mathutils import Vector

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p29] {m}", flush=True)

prof = [(-0.470, 0.052), (-0.430, 0.086), (-0.380, 0.106), (-0.320, 0.118),
        (-0.240, 0.122), (-0.160, 0.115), (-0.090, 0.096), (-0.030, 0.078),
        ( 0.010, 0.073), ( 0.050, 0.079), ( 0.100, 0.092), ( 0.160, 0.104),
        ( 0.230, 0.109), ( 0.300, 0.101), ( 0.360, 0.083), ( 0.400, 0.055)]
def w_at(z):
    if z <= prof[0][0] or z >= prof[-1][0]: return 0.0
    for i in range(len(prof) - 1):
        z0, w0 = prof[i]; z1, w1 = prof[i+1]
        if z0 <= z <= z1:
            t = (z - z0) / (z1 - z0)
            s = t * t * (3 - 2 * t)
            return w0 + (w1 - w0) * s
    return 0.001

Z0, Z1 = -0.470, 0.400
NZ, NX = 57, 25
# grid verts: x from -w(z) to +w(z); interior of outline -> rounded ends via bell on |x|/w
bm = bmesh.new()
grid = {}
for iz in range(NZ):
    z = Z0 + (Z1 - Z0) * iz / (NZ - 1)
    w = w_at(z)
    for ix in range(NX):
        u = ix / (NX - 1) * 2 - 1          # -1..1
        x = u * w
        y = -0.022 * (1 - u * u)            # crown toward -Y (face side)
        grid[(iz, ix)] = bm.verts.new((x, y, z))
for iz in range(NZ - 1):
    for ix in range(NX - 1):
        a = grid[(iz, ix)]; b = grid[(iz, ix + 1)]
        c = grid[(iz + 1, ix + 1)]; d = grid[(iz + 1, ix)]
        try: bm.faces.new((a, b, c, d))
        except ValueError: pass
for f in bm.faces: f.recalc_normal if hasattr(f,'recalc_normal') else None
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
# ensure normals face -Y (front): sample center face
center = min(bm.faces, key=lambda f: abs(f.calc_center_median().x) + abs(f.calc_center_median().z))
if center.normal.y > 0:
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
me = bpy.data.meshes.new("ME_WaveViolin_Body")
bm.to_mesh(me); bm.free()
# sanity
polys = len(me.polygons)
assert polys > 1000, f"fill failed again: {polys}"
# planar UVs (front projection) on UVMap + ME_BakeUV
uvl = me.uv_layers.new(name="UVMap")
uvb = me.uv_layers.new(name="ME_BakeUV")
for poly in me.polygons:
    for li in poly.loop_indices:
        co = me.vertices[me.loops[li].vertex_index].co
        u = (co.x + 0.13) / 0.26
        v = (co.z + 0.50) / 0.92
        uvl.data[li].uv = (u, v)
        uvb.data[li].uv = (u, v)

old = bpy.data.objects.get("ME_WaveViolin_Body")
parent = old.parent if old else None
mworld = old.matrix_world.copy() if old else None
if old:
    ome = old.data
    bpy.data.objects.remove(old, do_unlink=True)
    if ome.users == 0: bpy.data.meshes.remove(ome)
body = bpy.data.objects.new("ME_WaveViolin_Body", me)
bpy.data.collections["ME_WaveViolin_Assemblies"].objects.link(body)
if parent:
    body.parent = parent
    body.matrix_parent_inverse = parent.matrix_world.inverted() @ mworld
sol = body.modifiers.new("ME_BodyDepth", "SOLIDIFY"); sol.thickness = 0.082; sol.offset = 0.35
bev = body.modifiers.new("ME_BodyBevel", "BEVEL"); bev.width = 0.005; bev.segments = 2
body.data.materials.append(bpy.data.materials["ME_MAT_Violin_BellyCymatic"])

# Reel_Deploy shape key + driver
mc = bpy.data.objects["ME_WaveViolin_Control"]
mc.rotation_euler.x = -math.pi / 2
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
if "ME_BakeUV" in [u.name for u in me.uv_layers]:
    me.uv_layers.active = me.uv_layers["ME_BakeUV"]

bpy.context.view_layer.update()
ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
eme = ev.to_mesh()
bb = [ev.matrix_world @ Vector(c) for c in ev.bound_box]
print(f"BODY polys_base={polys} eval_polys={len(eme.polygons)} "
      f"x[{min(b.x for b in bb):.3f},{max(b.x for b in bb):.3f}] "
      f"y[{min(b.y for b in bb):.3f},{max(b.y for b in bb):.3f}] "
      f"z[{min(b.z for b in bb):.2f},{max(b.z for b in bb):.2f}]")
ev.to_mesh_clear()
me2 = body.data
rep = {"phase": "p29", "ok": True, "polys_base": polys}
bpy.ops.wm.save_mainfile()
scn = bpy.context.scene
try: scn.view_settings.view_transform = "AgX"
except Exception: pass
scn.view_settings.exposure = -1.2
try: scn.view_settings.look = "AgX - Punchy"
except Exception: pass
scn.render.resolution_x = 1100; scn.render.resolution_y = 1100
scn.camera = bpy.data.objects["ME_WaveViolin_Cam_Presentation"]
for fr, tag in ((1, "stow"), (2, "spin45")):
    scn.frame_set(fr)
    scn.render.filepath = os.path.join(OUT, f"p29_{tag}.png")
    bpy.ops.render.render(write_still=True)
scn.frame_set(1)
bpy.ops.wm.save_mainfile()
json.dump(rep, open(os.path.join(OUT, "p29_report.json"), "w"), indent=1)
log("solid body rebuilt")
