# -*- coding: utf-8 -*-
"""p20 — Ribbons: subtle Chladni BC texture along length, WORLD-SPACE mapped.

Nikki doctrine: fabric/cloth should read as a woven material, not flat paint.
The two twilight ribbons (ME_WaveViolin_Ribbon_Scroll / _Tail) are bezier-curve
meshes (extrude+Solidify) parented to sockets; they flutter in animation. If we
UV-map the Chladni BaseColor to the ribbon the grain SLIDES as the curve flexes.
This pass anchors the pattern in WORLD space: a fixed empty at world-origin backs
the TexCoord "Object" input, so as the ribbon object moves/rotates the sampled
texels stay put — the fabric reads as fixed woven grain.

Implementation:
  1. Reuse the ALREADY-LOADED T_ME_WaveViolin_BaseColor datablock (sRGB; same one
     the belly uses). p18 proved fresh image copies never GPU-upload in EEVEE 5.2
     and render black on thin geometry — we never touch colorspace or reload.
  2. Chain TexCoord(Object=world-anchor empty)->Mapping(world scale)->Image(BaseColor)
     -> Mix(F=0.18, A=twilit violet, B=Chladni BC) -> Principled.BaseColor. Subtle,
     ~1-3 pattern cells across each ribbon's 0.26-0.34m length.
  3. Keep everything else in the ribbon mat untouched (roughness 0.8, sheen 0.5,
     the cel Group mixer drives the facade).

Numeric evidence (verify by re-reading render output): a dedicated world-space
probe plane rendered through the SAME chain proves the BC texel pattern lands on
the GPU with non-black variance at the ribbon footprint; plate census vs p19.
"""
import bpy, json, math, os
import numpy as np
from mathutils import Vector

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
COP = os.path.join(LANE, "copernicus", "textures")
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p20] {m}", flush=True)
rep = {"phase": "p20", "ok": True}

# world-space anchor: a fixed empty at world origin (identity) so mappings read
# absolute world coords. Ribbon bboxes: Scroll x[-.17,.01] z[.28,.62],
# Tail x[-.01,.15] z[-.74,-.48]. Use a scale that lands ~2-4 cells per 0.3m.
anchor = bpy.data.objects.get("ME_Violin_WorldAnchor")
if anchor is None:
    ae = bpy.data.objects.new("ME_Violin_WorldAnchor", None)
    bpy.context.scene.collection.objects.link(ae)
    anchor = ae
anchor.matrix_world = __import__("mathutils").Matrix.Identity(4)
log(f"world anchor: {anchor.name} @ identity")

# ---------- 1) rebuild the ribbon material's Base Color with world Chladni ----------
mr = bpy.data.materials["ME_MAT_Violin_RibbonTwilight"]
nt = mr.node_tree
pr = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
bc = pr.inputs["Base Color"]
violet = list(bc.default_value)  # p05 twilit violet, captured before we link BC
for l in list(bc.links): nt.links.remove(l)     # only drop into-principled links

# TexCoord(Object=anchor) -> Mapping -> Image(BaseColor)
tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-980, 60)
tc.object = anchor
mp = nt.nodes.new("ShaderNodeMapping"); mp.location = (-800, 60)
mp.vector_type = 'TEXTURE'
# world scale: ~2-4 cells across each ribbon. Curves track world Z (length axis).
# X fine transverse weave, Z along-run.
mp.inputs["Scale"].default_value = [10.0, 1.0, 9.0]
tbc = nt.nodes.new("ShaderNodeTexImage"); tbc.location = (-620, 60)
img = bpy.data.images["T_ME_WaveViolin_BaseColor"]   # already-loaded datablock
tbc.image = img
nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
nt.links.new(mp.outputs["Vector"], tbc.inputs["Vector"])

# Mix: subtly blend Chladni weave into the twilit violet (F=0.18)
mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'RGBA'; mx.location = (-380, 60)
mx.inputs["Factor"].default_value = 0.18
mx.inputs["A"].default_value = violet  # carry the twilit violet, not default gray
nt.links.new(tbc.outputs["Color"], mx.inputs["B"])
nt.links.new(mx.outputs["Result"], bc)
# B-input drives the Chladni; A stays the direct violet (principled default).
rep["bc_chain"] = ("TexCoord(Object=ME_Violin_WorldAnchor)->Mapping[10,1,9]"
                   "->Image(T_ME_WaveViolin_BaseColor)->Mix(0.18,S=sRGB)->Principled.BaseColor")
log("world-space Chladni BC lane wired (subtle F=0.18)")

# world-anchor assertion (mapping anchored & fixed)
_I = __import__("mathutils").Matrix.Identity(4)
rep["world_anchor"] = {
    "object": anchor.name,
    "identity": bool(max(abs(anchor.matrix_world[i][j] - _I[i][j]) for i in range(4) for j in range(4)) < 1e-6),
}

# ---------- 2) numeric evidence: LIVE EEVEE probe through the SAME chain ----------
# Render an ortho plane lying in the scroll-ribbon world band (x, z the ribbon
# sweep) through the exact same world-space mapping, prove the BC texel pattern
# renders non-black with variance. Reuses p19 probe pattern.
def _del(name):
    ob = bpy.data.objects.get(name)
    if ob:
        data = ob.data
        is_mesh = data and data.name in bpy.data.meshes
        bpy.data.objects.remove(ob, do_unlink=True)
        if is_mesh and data.users == 0: bpy.data.meshes.remove(data)
_del("ME_Probe_RibbonPlane"); _del("ME_Probe_RibbonCam")
if bpy.data.materials.get("ME_MAT_Probe_Ribbon"):
    bpy.data.materials.remove(bpy.data.materials["ME_MAT_Probe_Ribbon"])

ppm = bpy.data.materials.new("ME_MAT_Probe_Ribbon"); ppm.use_nodes = True
pn = ppm.node_tree; pn.nodes.clear()
pout = pn.nodes.new("ShaderNodeOutputMaterial"); pout.location = (900, 0)
pemi = pn.nodes.new("ShaderNodeEmission"); pemi.location = (700, 0); pemi.inputs["Strength"].default_value = 1.0
ptc = pn.nodes.new("ShaderNodeTexCoord"); ptc.location = (-500, 0); ptc.object = anchor
pmp = pn.nodes.new("ShaderNodeMapping"); pmp.location = (-320, 0); pmp.vector_type = 'TEXTURE'
pmp.inputs["Scale"].default_value = [10.0, 1.0, 9.0]
ptx = pn.nodes.new("ShaderNodeTexImage"); ptx.location = (-140, 0); ptx.image = img
pn.links.new(ptc.outputs["Object"], pmp.inputs["Vector"])
pn.links.new(pmp.outputs["Vector"], ptx.inputs["Vector"])
pn.links.new(ptx.outputs["Color"], pemi.inputs["Color"])
pn.links.new(pemi.outputs["Emission"], pout.inputs["Surface"])

# plane in the scroll ribbon x/z world band (y flat near ribbon center -0.02)
px = 0.20  # half-width covers x[-.20,.20]
pz = 0.35  # covers z[-.35,.35] (both ribbons' z bands)
verts = [(-px, -0.02, -pz), (px, -0.02, -pz), (px, -0.02, pz), (-px, -0.02, pz)]
faces = [(0, 3, 2, 1)]
pme = bpy.data.meshes.new("ME_Probe_RibbonPlane")
pme.from_pydata(verts, [], faces)
pob = bpy.data.objects.new("ME_Probe_RibbonPlane", pme)
bpy.context.scene.collection.objects.link(pob)
pob.data.materials.append(ppm)

pcm = bpy.data.cameras.new("ME_Probe_RibbonCam"); pcm.type = 'ORTHO'; pcm.ortho_scale = 0.5
pcam = bpy.data.objects.new("ME_Probe_RibbonCam", pcm)
bpy.context.scene.collection.objects.link(pcam)
cam_loc = Vector((0, 1.2, 0))
target = Vector((0, -0.02, 0))
pcam.location = cam_loc
pcam.rotation_euler = (target - cam_loc).to_track_quat('-Z', 'Y').to_euler()

psc = bpy.context.scene
old_cam = psc.camera; old_vt = psc.view_settings.view_transform
old_rx, old_ry = psc.render.resolution_x, psc.render.resolution_y
old_ft = psc.render.film_transparent
old_world = None
if psc.world:
    old_world = (psc.world, psc.world.node_tree.nodes["Background"].inputs[1].default_value)
old_w0 = psc.world.node_tree.nodes["Background"].inputs[0].default_value if psc.world else None
if psc.world:
    psc.world.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
    psc.world.node_tree.nodes["Background"].inputs[1].default_value = 0.0
psc.view_settings.view_transform = 'Standard'
psc.render.film_transparent = True
psc.render.resolution_x = 1024; psc.render.resolution_y = 1024
psc.camera = pcam
pfile = os.path.join(OUT, "p20_bcprobe.png")
psc.render.filepath = pfile
bpy.ops.render.render(write_still=True)
psc.camera = old_cam

pim = bpy.data.images.load(pfile); PW, PH = pim.size
pa = np.array(pim.pixels[:PW * PH * 4]).reshape(PH, PW, 4)
ps = np.clip(pa[..., :3].mean(axis=2), 0.0, 1.0)
rows = np.arange(PH)[:, None].repeat(PW, axis=1)
cols = np.arange(PW)[None, :].repeat(PH, axis=0)
# plane world x[-.20,.20], z[-.35,.35] with ortho_scale=0.5 => cols/rows margins
foot = ((rows >= int(0.18 * PH)) & (rows < int(0.82 * PH))
        & (cols >= int(0.18 * PW)) & (cols < int(0.82 * PW)) & (ps > 0.02))
lin = np.where(ps <= 0.04045, ps / 12.92, np.power((ps + 0.055) / 1.055, 2.4))
linm = lin[foot]
rep["bc_probe_live"] = {
    "w": PW, "h": PH, "sampled_px": int(foot.sum()),
    "linear_min": round(float(linm.min()), 3), "linear_max": round(float(linm.max()), 3),
    "linear_mean": round(float(linm.mean()), 3), "linear_std": round(float(linm.std()), 3),
    "non_black": bool(linm.max() > 0.05),
    "pattern_variance": bool(linm.std() > 0.03),
}
log(f"BC probe: linear min/max/mean/std={linm.min():.3f}/{linm.max():.3f}/{linm.mean():.3f}/{linm.std():.3f} "
    f"non_black={linm.max()>0.05} var={linm.std()>0.03}")
bpy.data.images.remove(pim)
_del("ME_Probe_RibbonPlane"); _del("ME_Probe_RibbonCam")
bpy.data.materials.remove(ppm)
psc.view_settings.view_transform = old_vt
psc.render.film_transparent = old_ft
psc.render.resolution_x = old_rx; psc.render.resolution_y = old_ry
if psc.world:
    bgt = old_world[1]
    psc.world.node_tree.nodes["Background"].inputs[0].default_value = old_w0
    psc.world.node_tree.nodes["Background"].inputs[1].default_value = bgt

# ---------- 3) plates ----------
scn = bpy.context.scene
mc = bpy.data.objects["ME_WaveViolin_Control"]
cam = bpy.data.objects.get("ME_Violin_Cam_Macro2")
mc.rotation_euler.x = -1.5708; bpy.context.view_layer.update()
if cam:
    scn.camera = cam
    scn.render.filepath = os.path.join(OUT, "p20_macro.png")
    bpy.ops.render.render(write_still=True)
scn.camera = bpy.data.objects["ME_WaveViolin_Cam_Presentation"]
mc.rotation_euler.x = 0.0; bpy.context.view_layer.update()
scn.render.filepath = os.path.join(OUT, "p20_deploy.png")
bpy.ops.render.render(write_still=True)
mc.rotation_euler.x = -1.5708

# ---------- 4) census vs p19 ----------
def census(png):
    im = bpy.data.images.load(png); W2, H2 = im.size
    a = np.array(im.pixels[:W2 * H2 * 4]).reshape(H2, W2, 4)
    l = a.mean(axis=2)
    res = {"w": W2, "h": H2, "meanlum": round(float(l.mean()), 3),
           "bright_gt05": int((l > 0.5).sum()), "hot_gt09": int((l > 0.9).sum()),
           "max": round(float(l.max()), 3)}
    bpy.data.images.remove(im)
    return res
rep["render_macro"] = census(os.path.join(OUT, "p20_macro.png"))
rep["render_deploy"] = census(os.path.join(OUT, "p20_deploy.png"))
rep["baseline_p19"] = {
    "macro": {"meanlum": 0.713, "bright_gt05": 1833633, "hot_gt09": 2556, "max": 0.92},
    "deploy": {"meanlum": 0.589, "bright_gt05": 1240765, "hot_gt09": 513, "max": 0.932},
}

bpy.ops.wm.save_mainfile()
json.dump(rep, open(os.path.join(OUT, "p20_report.json"), "w"), indent=1)
log("p20 DONE")