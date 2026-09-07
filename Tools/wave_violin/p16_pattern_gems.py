# -*- coding: utf-8 -*-
"""p16 — belly pattern + gem facets (Nikki specialist lens).

Review said: nodal pattern not reading (metallic ORM washing to silver),
gems flat low-poly. Fixes:
1. belly: metallic channel scaled to 0.35, emissive lane back to 1.6,
   cel mix fac to 0.55 so candle-gold light-side dominates.
2. gems: subdivision=2 icosphere realized with slight random facet jitter
   + flat shading => cut-crystal read; rim flash ramp tightened.
3. macro cam re-aimed perpendicular to belly front so pattern faces lens.
"""
import bpy, json, os, math, random
import bmesh
from mathutils import Vector

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p16] {m}", flush=True)
rep = {"phase": "p16", "ok": True}

# 1) belly tuning
mb = bpy.data.materials["ME_MAT_Violin_BellyCymatic"]
nt = mb.node_tree
p = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
sep = next(n for n in nt.nodes if n.type == "SEPINPUT" or n.bl_idname == "ShaderNodeSeparateColor")
metal_mul = nt.nodes.new("ShaderNodeMath"); metal_mul.operation = 'MULTIPLY'; metal_mul.inputs[1].default_value = 0.35
metal_mul.location = (100, -150)
for l in list(p.inputs["Metallic"].links): nt.links.remove(l)
nt.links.new(sep.outputs["Blue"], metal_mul.inputs[0])
nt.links.new(metal_mul.outputs[0], p.inputs["Metallic"])
if p.inputs["Emission Strength"].default_value < 1.6:
    p.inputs["Emission Strength"].default_value = 1.6
mix = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeMixShader")
mix.inputs["Fac"].default_value = 0.55
rep["belly"] = "metallic*0.35, emission 1.6, cel 0.55"

# 2) gem re-facet: build a cut stone (octahedral-ish, jittered)
def kill(name):
    ob = bpy.data.objects.get(name)
    if ob:
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if me and getattr(me, "users", 1) == 0: bpy.data.meshes.remove(me)

kill("ME_WaveViolin_BeadProto"); kill("ME_WaveViolin_BeadProto.001")
bm = bmesh.new()
bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.0085)
random.seed(7)
for v in bm.verts:
    v.co += v.co.normalized() * random.uniform(-0.0012, 0.0018)
me = bpy.data.meshes.new("ME_WaveViolin_Bead")
for f in bm.faces: f.smooth = False
bm.to_mesh(me); bm.free()
bead = bpy.data.objects.new("ME_WaveViolin_BeadProto", me)
bead.hide_render = True; bead.hide_viewport = True
bpy.context.scene.collection.objects.link(bead)
bead.data.materials.append(bpy.data.materials["ME_MAT_Violin_DuskGem"])
# relink scatter node group object ref
ng = bpy.data.node_groups.get("ME_Violin_BeadScatter")
if ng:
    oi = next((n for n in ng.nodes if n.bl_idname == "GeometryNodeObjectInfo"), None)
    if oi: oi.inputs[0].default_value = bead
# gem rim flash tighter
mg = bpy.data.materials["ME_MAT_Violin_DuskGem"]
rmp = next(n for n in mg.node_tree.nodes if n.type == "VALTORGB")
els = sorted(rmp.color_ramp.elements, key=lambda e: e.position)
els[1].position = 0.42; els[2].position = 0.72
rep["gems"] = "jittered icosphere facets, flat shaded"

# 3) macro cam perpendicular to belly front (belly at y=-0.037, faces -Y)
cam = bpy.data.objects.get("ME_Violin_Cam_Macro2")
if cam:
    t = Vector((0, -0.037, -0.02))
    cam.location = t + Vector((0, -0.30, 0.03))
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = 70

scn = bpy.context.scene
mc = bpy.data.objects["ME_WaveViolin_Control"]
scn.camera = cam
mc.rotation_euler.x = -1.5708
bpy.context.view_layer.update()
scn.render.filepath = os.path.join(OUT, "p16_macro.png")
bpy.ops.render.render(write_still=True)
scn.camera = bpy.data.objects["ME_WaveViolin_Cam_Presentation"]
mc.rotation_euler.x = 0.0; bpy.context.view_layer.update()
scn.render.filepath = os.path.join(OUT, "p16_deploy.png")
bpy.ops.render.render(write_still=True)
mc.rotation_euler.x = -1.5708
bpy.ops.wm.save_mainfile()
json.dump(rep, open(os.path.join(OUT, "p16_report.json"), "w"), indent=1)
log("done")
