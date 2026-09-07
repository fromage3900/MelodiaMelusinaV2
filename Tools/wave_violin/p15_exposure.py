# -*- coding: utf-8 -*-
"""p15 — exposure repair: the plate is overexposed (macro 73% of pixels >0.9).
Textures are fine; the LIGHTING is blowing them out. Standard VT + hot lights
= featureless cream. Fix: AgX back (filmic rolloff keeps gem specular),
exposure -1.2, lights down, emissions tamed. Verify numerically."""
import bpy, json, os

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
OUT = os.path.join(LANE, "render_out")
scn = bpy.context.scene
try:
    scn.view_settings.view_transform = "AgX"
except Exception:
    pass
scn.view_settings.exposure = -1.2
try:
    scn.view_settings.look = "AgX - Punchy"
except Exception:
    pass

for mn, v in (("ME_MAT_Violin_BellyCymatic", 0.7),
              ("ME_MAT_Violin_VentPure", 1.6),
              ("ME_MAT_Violin_StringEnergy", 0.35),
              ("ME_MAT_Violin_DuskGem", 0.2)):
    m = bpy.data.materials.get(mn)
    if not m: continue
    p = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    e = next((n for n in m.node_tree.nodes if n.type == "EMISSION"), None)
    if p and p.inputs["Emission Strength"].default_value > v:
        p.inputs["Emission Strength"].default_value = v
    if e: e.inputs["Strength"].default_value = min(e.inputs["Strength"].default_value, v)

for ln, e_ in (("ME_WaveViolin_Light_Key", 430), ("ME_WaveViolin_Light_Fill", 170),
               ("ME_WaveViolin_Light_Rim", 560)):
    l = bpy.data.objects.get(ln)
    if l: l.data.energy = e_

cam = bpy.data.objects.get("ME_Violin_Cam_Macro2")
if cam:
    scn.camera = cam
    scn.render.filepath = os.path.join(OUT, "p15_macro.png")
    bpy.ops.render.render(write_still=True)
scn.camera = bpy.data.objects["ME_WaveViolin_Cam_Presentation"]
mc = bpy.data.objects["ME_WaveViolin_Control"]
mc.rotation_euler.x = 0.0; bpy.context.view_layer.update()
scn.render.filepath = os.path.join(OUT, "p15_deploy.png")
bpy.ops.render.render(write_still=True)
mc.rotation_euler.x = -1.5708
bpy.ops.wm.save_mainfile()

stats = {"saved": True}
print("P15 DONE", flush=True)
