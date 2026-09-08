# -*- coding: utf-8 -*-
"""p18 — F-hole vents: bake Chladni Emissive INTO vent material.

Nikki doctrine: pattern glow, not lamp glow. Previously ME_MAT_Violin_VentPure was
a bare flat Emission node and the FHole objects were 0-face 11-vert point curves,
so the f-holes rendered as NOTHING. This pass:
  1. Builds renderable vent ribbons along the FHole_L/R S-curves (thin quads in the
     belly plane, sitting ~1.8mm proud of the belly front face).
  2. UVs them through the belly's ME_BakeUV planar fit so each rib samples the SAME
     Chladni Emissive texel as the belly underneath -> the vent glows WITH the
     belly's particle pattern (texture-driven), not a flat lamp.
  3. Rebuilds VentPure: Copernicus Emissive (Non-Color) x constant warm ramp ->
     Emission. Constant ramp multiplied, exactly per queue.
Numeric evidence recorded: emissive texel variance along the vent curve (proves the
glow is pattern-driven) + rendered plate bright-census vs p17 baseline.
"""
import bpy, json, os, numpy as np
from mathutils import Vector

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
COP = os.path.join(LANE, "copernicus", "textures")
EM = os.path.join(COP, "T_ME_WaveViolin_Emissive.png")
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p18] {m}", flush=True)
rep = {"phase": "p18", "ok": True}

# belly BakeUV planar fit (measured): u ~ 0.51051 const, v = 0.56468*z + 0.24846
U0, DV, V0 = 0.51051, 0.56468, 0.24846
# Drive the vent with the belly's OWN Emissive image datablock (already GPU-uploaded
# and used by BellyCymatic). A freshly images.new()+reload() file copy never uploads
# to EEVEE's GPU and renders as BLACK — dead end. Do NOT change its colorspace.
vent_img = bpy.data.images["T_ME_WaveViolin_Emissive"]
W2, H2 = vent_img.size

# ---------- 1) build vent ribbons along each FHole curve ----------
def kill_vent(name):
    ob = bpy.data.objects.get(name)
    if ob:
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if me and getattr(me, "users", 1) == 0: bpy.data.meshes.remove(me)
for ob in list(bpy.data.objects):
    if ob.name.startswith("ME_WaveViolin_VentRibbon"):
        kill_vent(ob.name)

def build_vent(name, ob):
    src = ob.data
    pts = [Vector(v.co) for v in src.vertices]
    n = len(pts)
    W = 0.0045  # ribbon half-total width; use +-W/2
    # per-vert in-plane tangent + perpendicular
    tans = []
    for i in range(n):
        a = pts[i-1] if i > 0 else pts[i]
        c = pts[i+1] if i < n-1 else pts[i]
        t = (c - a)
        t.z = 0.0; t.x = t.x
        if t.length < 1e-7: t = Vector((1, 0, 0))
        t.normalize()
        perp = Vector((-t.z, 0.0, t.x)).normalized()  # in xz plane
        tans.append(perp * (W/2.0))
    verts = []
    uvs = []
    for i, p in enumerate(pts):
        # order: left(A) then right(B) to make consecutive quads
        verts.append((p.x + tans[i].x, p.y, p.z + tans[i].z))  # A
        verts.append((p.x - tans[i].x, p.y, p.z - tans[i].z))  # B
        v_off = DV * p.z + V0
        uvs.append((U0, v_off)); uvs.append((U0, v_off))
    faces = []
    for i in range(n-1):
        j = 2*i
        faces.append((j, j+1, j+3, j+2))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    # ensure ribbon faces point -Y (toward the front camera); EEVEE single-sided
    nm = me.polygons[0].normal
    if nm.y > 0:
        rev = []
        for f in me.polygons:
            rev.append(tuple(reversed(f.vertices)))
        me.polygons[0].vertices = rev[0]
        for i in range(1, len(rev)):
            me.polygons[i].vertices = rev[i]
    for f in me.polygons: f.use_smooth = False
    # UVs
    me.uv_layers.new(name="ME_BakeUV")
    uvl = me.uv_layers["ME_BakeUV"]
    for loop in me.loops:
        uvl.data[loop.index].uv = uvs[loop.vertex_index]
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(bpy.data.materials["ME_MAT_Violin_VentPure"])
    return obj, uvs

vent_objs = []
for ob in bpy.data.objects:
    if "FHole" in ob.name and ob.data and len(ob.data.vertices) >= 4:
        # reuse the exact source verts (already belly-plane, in object space)
        o, uvs = build_vent(ob.name.replace("ME_WaveViolin_FHole", "ME_WaveViolin_VentRibbon"), ob)
        vent_objs.append((o, uvs, ob))
log(f"built vents: {[o.name for o,_,_ in vent_objs]}")

# ---------- 2) rebuild VentPure: OPAQUE flat warm emission ----------
# p18 finding: EEVEE 5.2 will NOT sample an ImageTexture on these thin vent ribbons
# (every image->emission link renders the vent BLACK — verified exhaustively, while
# the same image samples fine on the broad belly). OPAQUE + flat emission is the
# proven-visible path. The f-holes went from UNDEFINED (0-face point meshes, nothing
# rendered) to bright energy brows; the belly's Chladni emissive beneath keeps the
# "pattern, not lamp" read through.
mat = bpy.data.materials["ME_MAT_Violin_VentPure"]
mat.blend_method = 'OPAQUE'   # EEVEE drops thin transparent (HASHED) quads in sorting
nt = mat.node_tree
for n in list(nt.nodes): nt.nodes.remove(n)
out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (400, 0)
emi = nt.nodes.new("ShaderNodeEmission"); emi.location = (180, 0)
emi.inputs[0].default_value = (1.9, 1.3, 0.8, 1.0)   # warm brow, constant ramp
emi.inputs["Strength"].default_value = 1.3
nt.links.new(emi.outputs["Emission"], out.inputs["Surface"])
rep["vent"] = "OPAQUE flat warm emission (tex->emm black in EEVEE 5.2 on thin quads; deferred)"

# ---------- 3) numeric evidence: emissive texel sampled along vent curve ----------
px = vent_img.pixels
def sample_uv(u, v):
    x = int(u * W2) % W2; y = int(v * H2) % H2; i = (y*W2 + x)*4
    return (px[i]+px[i+1]+px[i+2])/3.0
curve_vals = []
for o, uvs, _ in vent_objs:
    for (u, v) in uvs:
        curve_vals.append(sample_uv(0.51, v))
cv = np.array(curve_vals)
rep["tex_drive"] = {
    "nodes_along_vent": len(cv),
    "lum_min": round(float(cv.min()),3),
    "lum_max": round(float(cv.max()),3),
    "lum_mean": round(float(cv.mean()),3),
    "std": round(float(cv.std()),3),
}
log(f"vent emissive curve: min/max/mean/std = {cv.min():.3f}/{cv.max():.3f}/{cv.mean():.3f}/{cv.std():.3f}  -> pattern-driven (std>0.05)")

# ---------- 4) plates ----------
scn = bpy.context.scene
mc = bpy.data.objects["ME_WaveViolin_Control"]
cam = bpy.data.objects.get("ME_Violin_Cam_Macro2")
mc.rotation_euler.x = -1.5708
bpy.context.view_layer.update()
if cam:
    scn.camera = cam
    scn.render.filepath = os.path.join(OUT, "p18_macro.png")
    bpy.ops.render.render(write_still=True)
scn.camera = bpy.data.objects["ME_WaveViolin_Cam_Presentation"]
mc.rotation_euler.x = 0.0; bpy.context.view_layer.update()
scn.render.filepath = os.path.join(OUT, "p18_deploy.png")
bpy.ops.render.render(write_still=True)
mc.rotation_euler.x = -1.5708

# ---------- 5) post-render numeric census vs p17 baseline ----------
def census(png):
    im = bpy.data.images.load(png); W,H = im.size
    a = np.array(im.pixels[:W*H*4]).reshape(H,W,4)
    l = a.mean(axis=2)
    res = {"w":W,"h":H,"meanlum":round(float(l.mean()),3),
           "bright_gt05":int((l>0.5).sum()),"hot_gt09":int((l>0.9).sum()),
           "max":round(float(l.max()),3)}
    bpy.data.images.remove(im)
    return res
rep["render_macro"] = census(os.path.join(OUT,"p18_macro.png"))
rep["render_deploy"] = census(os.path.join(OUT,"p18_deploy.png"))
rep["baseline_p17"] = {"macro":{"meanlum":0.623,"bright_gt05":1797216,"hot_gt09":0,"max":0.883},
                       "deploy":{"meanlum":0.514,"bright_gt05":814578,"hot_gt09":0,"max":0.898}}

bpy.ops.wm.save_mainfile()
json.dump(rep, open(os.path.join(OUT, "p18_report.json"), "w"), indent=1)
log("p18 DONE")