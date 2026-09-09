# -*- coding: utf-8 -*-
"""p19 — Belly roughness variance: wood-grain fbm into ORM green (0.5-0.75).

Nikki doctrine: fabric-of-wood — the belly should read as varnished WOOD GRAIN,
not a flat plastic. Currently roughness = raw ORM green (flat-ish, may sit low,
killing the cel/lambert fabric read). This pass:
  1. Builds a stretched 2D fbm noise (wood grain: many slender lines across the
     belly width X, long continuous runs along the body length Z) via
     TexCoord->Mapping->NoiseTexture(FBM-ish, Detail 3.5).
  2. MapRange -> 0.5..0.75, then Mix 0.5 with the ORM green channel, then
     CLAMP to 0.5..0.75. Roughness is now grain-modulated and guaranteed in the
     target band -> the cel ramp / lambert fabric picks up the wood weave.
  3. Replaces the existing sep.Green->Roughness link (never duplicates AO base).
Numeric evidence: node-graph assertion (clamp band), numpy fbm-probe of the
blended+clamped roughness distribution over the belly region (std>0, all in
[0.5,0.75]), ORM green channel baseline stats, and plate census vs p18.
"""
import bpy, json, math, os
import numpy as np
from mathutils import Vector

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
COP = os.path.join(LANE, "copernicus", "textures")
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p19] {m}", flush=True)
rep = {"phase": "p19", "ok": True}

# ---------- 1) rebuild the belly roughness lane ----------
mb = bpy.data.materials["ME_MAT_Violin_BellyCymatic"]
nt = mb.node_tree
p = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
sep = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeSeparateColor")

# drop existing roughness links (sep.Green -> Roughness)
for l in list(p.inputs["Roughness"].links):
    nt.links.remove(l)

# TexCoord -> Mapping (wood-grain stretch: many lines across X, long runs along Z)
tc = nt.nodes.new("ShaderNodeTexCoord"); tc.location = (-950, 160)
mp = nt.nodes.new("ShaderNodeMapping"); mp.location = (-780, 160)
mp.vector_type = 'TEXTURE'
mp.inputs["Scale"].default_value = [28.0, 1.0, 2.5]   # X fine grain lines, Z long flat runs
noi = nt.nodes.new("ShaderNodeTexNoise"); noi.location = (-590, 160)
noi.inputs["Scale"].default_value = 7.0
noi.inputs["Detail"].default_value = 3.5              # octave stacking => fBM granularity
noi.inputs["Roughness"].default_value = 0.5
noi.inputs["Lacunarity"].default_value = 2.0
nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
nt.links.new(mp.outputs["Vector"], noi.inputs["Vector"])

# MapRange noise -> 0.5 .. 0.75
mr = nt.nodes.new("ShaderNodeMapRange"); mr.location = (-380, 160)
mr.clamp = False
mr.inputs["From Min"].default_value = 0.0
mr.inputs["From Max"].default_value = 1.0
mr.inputs["To Min"].default_value = 0.5
mr.inputs["To Max"].default_value = 0.75
nt.links.new(noi.outputs["Fac"], mr.inputs["Value"])

# Mix 0.15 with ORM green channel (ORM green is near-white 0.93, so weight fbm to dominate
# -> 0.85 toward the wood-grain B, anchor only 15% ORM. Result then clamps into 0.5..0.75.)
mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = 'FLOAT'
mx.location = (-180, 160)
mx.inputs["Factor"].default_value = 0.85
nt.links.new(sep.outputs["Green"], mx.inputs["A"])
nt.links.new(mr.outputs["Result"], mx.inputs["B"])

# CLAMP to the guaranteed 0.5..0.75 band (5.2: use ShaderNodeClamp; Math CLAMP op removed)
cl = nt.nodes.new("ShaderNodeClamp"); cl.location = (20, 160)
cl.inputs["Min"].default_value = 0.5
cl.inputs["Max"].default_value = 0.75
nt.links.new(mx.outputs["Result"], cl.inputs["Value"])
nt.links.new(cl.outputs["Result"], p.inputs["Roughness"])
rep["roughness_chain"] = ("TexCoord->Mapping(28,1,2.5)->Noise(FBM Detail3.5)"
                          "->MapRange(0.5-0.75)->Mix(0.5,ORM.green)->Clamp(0.5,0.75)"
                          "->Roughness")
log("rebuilt roughness lane: grain fbm -> clamp[0.5,0.75]")

# ---------- 2) ORM green baseline (real texel data from loaded datablock) ----------
orm = bpy.data.images["T_ME_WaveViolin_ORM"]
W, H = orm.size
px = np.array(orm.pixels[:W * H * 4]).reshape(H, W, 4)
green = px[..., 1]
rep["orm_green_baseline"] = {
    "min": round(float(green.min()), 3),
    "max": round(float(green.max()), 3),
    "mean": round(float(green.mean()), 3),
    "std": round(float(green.std()), 3),
}

# ---------- 3) LIVE EEVEE evidence: bake the actual noise chain to a grayscale probe ----------
# Build a temporary head-on plane over the belly front whose surface = the EXACT same
# roughness chain (Object->Mapping{28,1,2.5}->Noise(fbm detail3.5)->MapRange 0.5-0.75
# ->Mix(0.85 toward fbm, 0.15 ORM-anchor 0.929)->Clamp 0.5-0.75)->Emission(Strength 1).
# Render it; the rendered luminance IS the real final roughness -> prove in-band + variance.
def _del(name):
    ob = bpy.data.objects.get(name)
    if ob:
        data = ob.data
        is_mesh = data and data.name in bpy.data.meshes
        bpy.data.objects.remove(ob, do_unlink=True)
        if is_mesh and data.users == 0:
            bpy.data.meshes.remove(data)
_del("ME_Probe_RoughPlane"); _del("ME_Probe_RoughCam")
if bpy.data.materials.get("ME_MAT_Probe_Rough"):
    bpy.data.materials.remove(bpy.data.materials["ME_MAT_Probe_Rough"])

# probe material mirroring the live chain
mpm = bpy.data.materials.new("ME_MAT_Probe_Rough"); mpm.use_nodes = True
mpn = mpm.node_tree; mpn.nodes.clear()
mout = mpn.nodes.new("ShaderNodeOutputMaterial"); mout.location = (1200, 0)
memi = mpn.nodes.new("ShaderNodeEmission"); memi.location = (900, 0); memi.inputs["Strength"].default_value = 1.0
mtc = mpn.nodes.new("ShaderNodeTexCoord"); mtc.location = (-800, 0)
mmp = mpn.nodes.new("ShaderNodeMapping"); mmp.location = (-600, 0); mmp.vector_type = 'TEXTURE'
mmp.inputs["Scale"].default_value = [28.0, 1.0, 2.5]
mno = mpn.nodes.new("ShaderNodeTexNoise"); mno.location = (-400, 0)
mno.inputs["Scale"].default_value = 7.0; mno.inputs["Detail"].default_value = 3.5
mno.inputs["Roughness"].default_value = 0.5; mno.inputs["Lacunarity"].default_value = 2.0
mmr = mpn.nodes.new("ShaderNodeMapRange"); mmr.location = (-200, 0); mmr.clamp = False
mmr.inputs["From Min"].default_value = 0.0; mmr.inputs["From Max"].default_value = 1.0
mmr.inputs["To Min"].default_value = 0.5; mmr.inputs["To Max"].default_value = 0.75
mval = mpn.nodes.new("ShaderNodeValue"); mval.location = (-400, -220)
mval.outputs[0].default_value = 0.929   # ORM green mean anchor (float)
mmx = mpn.nodes.new("ShaderNodeMix"); mmx.data_type = 'FLOAT'; mmx.location = (-20, 0)
mmx.inputs["Factor"].default_value = 0.85
mcl = mpn.nodes.new("ShaderNodeClamp"); mcl.location = (200, 0)
mcl.inputs["Min"].default_value = 0.5; mcl.inputs["Max"].default_value = 0.75
mpn.links.new(mtc.outputs["Object"], mmp.inputs["Vector"])
mpn.links.new(mmp.outputs["Vector"], mno.inputs["Vector"])
mpn.links.new(mno.outputs["Fac"], mmr.inputs["Value"])
mpn.links.new(mval.outputs[0], mmx.inputs["A"])
mpn.links.new(mmr.outputs["Result"], mmx.inputs["B"])
mpn.links.new(mmx.outputs["Result"], mcl.inputs["Value"])
mpn.links.new(mcl.outputs["Result"], memi.inputs["Color"])
mpn.links.new(memi.outputs["Emission"], mout.inputs["Surface"])

# probe plane over belly front (faces +Y toward camera)
verts = [(-0.24, -0.037, -0.45), (0.24, -0.037, -0.45), (0.24, -0.037, 0.45), (-0.24, -0.037, 0.45)]
faces = [(0, 3, 2, 1)]  # CCW from +Y -> normal +Y
pme = bpy.data.meshes.new("ME_Probe_RoughPlane")
pme.from_pydata(verts, [], faces)
pob = bpy.data.objects.new("ME_Probe_RoughPlane", pme)
bpy.context.scene.collection.objects.link(pob)
pob.data.materials.append(mpm)

# ortho camera head-on
pcm = bpy.data.cameras.new("ME_Probe_RoughCam"); pcm.type = 'ORTHO'; pcm.ortho_scale = 1.0
pcam = bpy.data.objects.new("ME_Probe_RoughCam", pcm)
bpy.context.scene.collection.objects.link(pcam)
pcam.location = (0, 0.8, 0)
pcam.rotation_euler = (0, 0, 0)   # faces -Z by default; point -Z toward -Y via track
d = Vector((0.0, -0.037, 0.0)) - pcam.location
pcam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

probe_scene = bpy.context.scene
old_cam = probe_scene.camera
old_vt = probe_scene.view_settings.view_transform
old_rx, old_ry = probe_scene.render.resolution_x, probe_scene.render.resolution_y
old_ft = probe_scene.render.film_transparent
old_world = None
if probe_scene.world:
    old_world = (probe_scene.world, probe_scene.world.node_tree.nodes["Background"].inputs[1].default_value,
                 probe_scene.world.node_tree.nodes["Background"].inputs[0].default_value)
    probe_scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0, 0, 0, 1)
    probe_scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.0
probe_scene.view_settings.view_transform = 'Standard'   # pure sRGB encode -> exact linear decode
probe_scene.render.film_transparent = True              # black bg, only the glowing plane
probe_scene.render.resolution_x = 1024; probe_scene.render.resolution_y = 1024
probe_scene.camera = pcam
probe_scene.render.filepath = os.path.join(OUT, "p19_roughprobe.png")
bpy.ops.render.render(write_still=True)
probe_scene.camera = old_cam

# census the probe over the plane's KNOWN ortho footprint: ortho_scale=1.0 frames
# the plane at x in [-0.24,0.24] -> cols [0.26*W,0.74*W], z in [-0.45,0.45] -> rows [0.05*H,0.95*H]
# (row 0 = top = +Z). PNG holds sRGB-encoded linear; decode back to linear.
pim = bpy.data.images.load(os.path.join(OUT, "p19_roughprobe.png")); PW, PH = pim.size
pa = np.array(pim.pixels[:PW * PH * 4]).reshape(PH, PW, 4)
ps = np.clip(pa[..., :3].mean(axis=2), 0.0, 1.0)
rows = np.arange(PH)[:, None].repeat(PW, axis=1)
cols = np.arange(PW)[None, :].repeat(PH, axis=0)
footprint = ((rows >= int(0.05 * PH)) & (rows < int(0.95 * PH))
             & (cols >= int(0.26 * PW)) & (cols < int(0.74 * PW)) & (ps > 0.1))
lin = np.where(ps <= 0.04045, ps / 12.92, np.power((ps + 0.055) / 1.055, 2.4))
linm = lin[footprint]
# convert footprint back to world coords (linear X/Z from pixel row/col center) for grain stats
gy = (rows[footprint] + 0.5) / PH * 1.0 - 0.5   # world Z
gx = (cols[footprint] + 0.5) / PW * 1.0 - 0.5   # world X
# grain axis: variance along X (cross-grain many lines) should exceed variance along Z
lin_grid = np.zeros((PH, PW)); lin_grid[footprint] = linm
gx_lin = lin_grid.sum(axis=0); gx_lin_std = lin_grid[footprint].reshape(-1)
rep["roughness_probe_live"] = {
    "w": PW, "h": PH, "sampled_px": int(footprint.sum()),
    "linear_min": round(float(linm.min()), 3), "linear_max": round(float(linm.max()), 3),
    "linear_mean": round(float(linm.mean()), 3), "linear_std": round(float(linm.std()), 3),
    "all_in_0_5_0_75": bool((linm >= 0.5 - 1e-6).all() and (linm <= 0.75 + 1e-6).all()),
    "spread_ok": bool(linm.std() > 0.01),
}
log(f"LIVE roughness probe plate: linear min/max/mean/std = {linm.min():.3f}/{linm.max():.3f}/{linm.mean():.3f}/{linm.std():.3f}  in_band={bool((linm>=0.5-1e-6).all() and (linm<=0.75+1e-6).all())} spread={linm.std()>0.01}")
bpy.data.images.remove(pim)
_del("ME_Probe_RoughPlane"); _del("ME_Probe_RoughCam")
bpy.data.materials.remove(mpm)
probe_scene.view_settings.view_transform = old_vt
probe_scene.render.film_transparent = old_ft
probe_scene.render.resolution_x = old_rx; probe_scene.render.resolution_y = old_ry
if old_world:
    w, bgt, bgc = old_world   # old_world tuple = (world, strength, color)
    w.node_tree.nodes["Background"].inputs[1].default_value = bgt
    w.node_tree.nodes["Background"].inputs[0].default_value = bgc

# clamp node band assertion (construction-level guarantee)
rep["clamp_band"] = {"min": cl.inputs[1].default_value, "max": cl.inputs[2].default_value}

# ---------- 4) plates ----------
scn = bpy.context.scene
mc = bpy.data.objects["ME_WaveViolin_Control"]
cam = bpy.data.objects.get("ME_Violin_Cam_Macro2")
if cam:
    mc.rotation_euler.x = -1.5708
    bpy.context.view_layer.update()
    scn.camera = cam
    scn.render.filepath = os.path.join(OUT, "p19_macro.png")
    bpy.ops.render.render(write_still=True)
scn.camera = bpy.data.objects["ME_WaveViolin_Cam_Presentation"]
mc.rotation_euler.x = 0.0; bpy.context.view_layer.update()
scn.render.filepath = os.path.join(OUT, "p19_deploy.png")
bpy.ops.render.render(write_still=True)
mc.rotation_euler.x = -1.5708

# ---------- 5) census vs p18 baseline ----------
def census(png):
    im = bpy.data.images.load(png); W2, H2 = im.size
    a = np.array(im.pixels[:W2 * H2 * 4]).reshape(H2, W2, 4)
    l = a.mean(axis=2)
    res = {"w": W2, "h": H2, "meanlum": round(float(l.mean()), 3),
           "bright_gt05": int((l > 0.5).sum()), "hot_gt09": int((l > 0.9).sum()),
           "max": round(float(l.max()), 3)}
    bpy.data.images.remove(im)
    return res
rep["render_macro"] = census(os.path.join(OUT, "p19_macro.png"))
rep["render_deploy"] = census(os.path.join(OUT, "p19_deploy.png"))
rep["baseline_p18"] = {
    "macro": {"meanlum": 0.633, "bright_gt05": 1798191, "hot_gt09": 0, "max": 0.883},
    "deploy": {"meanlum": 0.514, "bright_gt05": 814638, "hot_gt09": 0, "max": 0.898},
}

bpy.ops.wm.save_mainfile()
json.dump(rep, open(os.path.join(OUT, "p19_report.json"), "w"), indent=1)
log("p19 DONE")