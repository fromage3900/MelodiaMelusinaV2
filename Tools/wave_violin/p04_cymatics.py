# -*- coding: utf-8 -*-
"""p04 — cymatics: eigen Chladni on belly plate + vent glow + string energy.

Uses Saved/Audit/eigenplate baked Height/Normal (brass 3_5 primary, plus
two string-frequency modes) wired into the AmberNight hybrid on the belly.
Adds warm candle-gold emission to f-hole vents and a faint energy lane to
strings. Renders macro plate.
"""
import bpy, json, os

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
EIG = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\eigenplate"
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p04] {m}", flush=True)

def load_img(name, path, noncolor=True):
    img = bpy.data.images.get(name)
    if img is None:
        img = bpy.data.images.load(path, check_existing=True); img.name = name
    img.filepath = path
    if noncolor: img.colorspace_settings.name = "Non-Color"
    return img

# --- belly plate: eigen normal + bump into Principled (lesson: feed BSDF, not output) ---
m = bpy.data.materials["ME_MAT_Violin_AmberNight"]
nt = m.node_tree
p = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
texN = nt.nodes.new("ShaderNodeTexImage"); texN.name = "ME_ViolinEigenN"
texN.image = load_img("T_Eigen_3_5_brass_Normal", os.path.join(EIG, "T_EigenPlate_3_5_brass_Normal.png"))
texH = nt.nodes.new("ShaderNodeTexImage"); texH.name = "ME_ViolinEigenH"
texH.image = load_img("T_Eigen_3_5_brass_Height", os.path.join(EIG, "T_EigenPlate_3_5_brass_Height.png"))
nmap = nt.nodes.new("ShaderNodeNormalMap"); nmap.inputs["Strength"].default_value = 0.55
bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.12
nt.links.new(texN.outputs["Color"], nmap.inputs["Color"])
nt.links.new(texH.outputs["Color"], bump.inputs["Height"])
nt.links.new(nmap.outputs["Normal"], bump.inputs["Normal"])
nt.links.new(bump.outputs["Normal"], p.inputs["Normal"])
# BUT this mat is on all body parts — isolate: give belly plate its own mat copy
belly = bpy.data.objects["ME_WaveViolin_BellyPlate"]
mb = m.copy(); mb.name = "ME_MAT_Violin_BellyCymatic"
belly.data.materials.clear(); belly.data.materials.append(mb)

# --- f-hole vent glow: candle-gold emission ---
for s in ("L", "R"):
    ob = bpy.data.objects.get(f"ME_WaveViolin_FHole_{s}")
    if not ob or not ob.data.materials: continue
    mat = ob.data.materials[0].copy(); mat.name = f"ME_MAT_Violin_VentGlow_{s}"
    pp = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    ec = pp.inputs.get("Emission Color"); ei = pp.inputs.get("Emission Strength")
    if ec: ec.default_value = (1.0, 0.62, 0.25, 1)
    if ei: ei.default_value = 4.0
    ob.data.materials[0] = mat

# --- strings: faint energy emissive ---
ms = bpy.data.materials.get("ME_MAT_Violin_StringEnergy") or bpy.data.materials["ME_MAT_Violin_PaleBrass"].copy()
ms.name = "ME_MAT_Violin_StringEnergy"
pp = next(n for n in ms.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
ec = pp.inputs.get("Emission Color"); ei = pp.inputs.get("Emission Strength")
if ec: ec.default_value = (0.75, 0.55, 1.0, 1)
if ei: ei.default_value = 0.6
for i in (1,2,3,4):
    ob = bpy.data.objects.get(f"ME_WaveViolin_String_{i}")
    if ob: ob.data.materials.clear(); ob.data.materials.append(ms)

# --- macro plate on belly ---
cam_data = bpy.data.cameras.new("ME_Violin_Cam_Macro"); cam_data.lens = 80
cam = bpy.data.objects.new("ME_Violin_Cam_Macro", cam_data)
bpy.data.collections["ME_WaveViolin_Presentation"].objects.link(cam)
target = belly.matrix_world.translation
from mathutils import Vector
cam.location = target + Vector((0.18, -0.34, 0.16))
d = target - cam.location
cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
scn = bpy.context.scene
scn.camera = cam
scn.render.filepath = os.path.join(OUT, "p04_macro.png")
bpy.ops.render.render(write_still=True)
scn.camera = bpy.data.objects["ME_WaveViolin_Cam_Presentation"]
scn.render.filepath = os.path.join(OUT, "p04_deploy.png")
mc = bpy.data.objects["ME_WaveViolin_Control"]
mc.rotation_euler.x = 0.0
bpy.ops.render.render(write_still=True)
mc.rotation_euler.x = -1.5708
bpy.ops.wm.save_mainfile()
json.dump({"phase":"p04","ok":True,"eigen":"3_5 brass on belly","vents":"candle-gold 4.0",
           "strings":"energy 0.6","plates":["p04_macro.png","p04_deploy.png"]},
          open(os.path.join(OUT,"p04_report.json"),"w"), indent=1)
log("done")
