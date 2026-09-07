# -*- coding: utf-8 -*-
"""p17 — the real bug: ShaderNodeMix socket selection.

bpy inputs["A"] on ShaderNodeMix returns the FLOAT socket, not RGBA — every
"Result" we linked was a gray scalar. That is why the belly rendered silver.
Fix: explicit index access (RGBA: in 6/7, out 2; factor=0). Rebuild gems as
brilliant-cut bicones (crown table + pavilion tip), flat shaded.
"""
import bpy, json, os, math, bmesh
from mathutils import Vector

LANE = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Portfolio\wave_violin"
COP = os.path.join(LANE, "copernicus", "textures")
OUT = os.path.join(LANE, "render_out")
BLEND = os.path.join(LANE, "ME_WaveViolin.blend")
bpy.ops.wm.open_mainfile(filepath=BLEND)
log = lambda m: print(f"[vr-p17] {m}", flush=True)
rep = {"phase": "p17", "ok": True}

# ---------- 1) belly: rebuild emission chain on correct RGBA sockets ----------
mb = bpy.data.materials["ME_MAT_Violin_BellyCymatic"]
nt = mb.node_tree
p = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
tBC = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeTexImage" and n.image and "BaseColor" in n.image.name)
tEM = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeTexImage" and n.image and n.image.name.endswith("Emissive"))
tIRI = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeTexImage" and n.image and "Iridescence" in n.image.name)
sep = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeSeparateColor")
layer = next((n for n in nt.nodes if n.bl_idname == "ShaderNodeLayerWeight"), None)

# kill the float-socket mix nodes
for n in list(nt.nodes):
    if n.bl_idname == "ShaderNodeMix":
        nt.nodes.remove(n)

# AO multiply on RGBA: A=BaseColor, B=AO gray (Red->Color ok via auto), Factor 1.0
aomul = nt.nodes.new("ShaderNodeMix"); aomul.data_type = 'RGBA'
aomul.blend_type = 'MULTIPLY'; aomul.location = (-200, 400)
aomul.inputs[0].default_value = 1.0
nt.links.new(tBC.outputs["Color"], aomul.inputs[6])        # A color
nt.links.new(sep.outputs["Red"], aomul.inputs[7])          # B color (AO)
nt.links.new(aomul.outputs[2], p.inputs["Base Color"])     # Result color

# iridescence: facing * IRI added to Emissive texture (RGBA sockets)
imix = nt.nodes.new("ShaderNodeMix"); imix.data_type = 'RGBA'
imix.blend_type = 'ADD'; imix.location = (150, -300)
if layer:
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 0.45
    mul.location = (-50, -550)
    nt.links.new(layer.outputs["Facing"], mul.inputs[0])
    nt.links.new(mul.outputs[0], imix.inputs[0])
else:
    imix.inputs[0].default_value = 0.25
nt.links.new(tEM.outputs["Color"], imix.inputs[6])
nt.links.new(tIRI.outputs["Color"], imix.inputs[7])
nt.links.new(imix.outputs[2], p.inputs["Emission Color"])
p.inputs["Emission Strength"].default_value = 1.3
rep["belly"] = "RGBA sockets fixed; BC*AO, EM+Facing*IRI"

# ---------- 2) brilliant-cut gems ----------
def kill(name):
    ob = bpy.data.objects.get(name)
    if ob:
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if me and getattr(me, "users", 1) == 0: bpy.data.meshes.remove(me)
kill("ME_WaveViolin_BeadProto")
kill("ME_WaveViolin_BeadProto.001")
bm = bmesh.new()
N = 8; r_t = 0.0050; r_g = 0.0085; z_c = 0.0035; z_p = -0.011
table = [bm.verts.new((r_t*math.cos(2*math.pi*i/N), r_t*math.sin(2*math.pi*i/N), z_c)) for i in range(N)]
girdle = [bm.verts.new((r_g*math.cos(2*math.pi*(i+0.5)/N), r_g*math.sin(2*math.pi*(i+0.5)/N), 0.0)) for i in range(N)]
tip = bm.verts.new((0, 0, z_p))
ct = bm.verts.new((0, 0, z_c + 0.0008))
bm.faces.new(table); [bm.faces.new((ct, table[i], table[(i+1) % N])) for i in range(N)]
[bm.faces.new((table[i], girdle[i], table[(i+1) % N])) for i in range(N)]
[bm.faces.new((table[(i+1) % N], girdle[i], girdle[(i+1) % N])) for i in range(N)]
[bm.faces.new((tip, girdle[(i+1) % N], girdle[i])) for i in range(N)]
for f in bm.faces: f.smooth = False
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
me = bpy.data.meshes.new("ME_WaveViolin_Bead")
bm.to_mesh(me); bm.free()
bead = bpy.data.objects.new("ME_WaveViolin_BeadProto", me)
bead.hide_render = True; bead.hide_viewport = True
bpy.context.scene.collection.objects.link(bead)
bead.data.materials.append(bpy.data.materials["ME_MAT_Violin_DuskGem"])
ng = bpy.data.node_groups.get("ME_Violin_BeadScatter")
if ng:
    oi = next((n for n in ng.nodes if n.bl_idname == "GeometryNodeObjectInfo"), None)
    if oi: oi.inputs[0].default_value = bead
rep["gems"] = "brilliant-cut bicone N=8 flat"

# ---------- 3) plates ----------
scn = bpy.context.scene
mc = bpy.data.objects["ME_WaveViolin_Control"]
cam = bpy.data.objects.get("ME_Violin_Cam_Macro2")
mc.rotation_euler.x = -1.5708
if cam:
    scn.camera = cam
    scn.render.filepath = os.path.join(OUT, "p17_macro.png")
    bpy.ops.render.render(write_still=True)
scn.camera = bpy.data.objects["ME_WaveViolin_Cam_Presentation"]
mc.rotation_euler.x = 0.0
bpy.context.view_layer.update()
scn.render.filepath = os.path.join(OUT, "p17_deploy.png")
bpy.ops.render.render(write_still=True)
mc.rotation_euler.x = -1.5708
bpy.ops.wm.save_mainfile()
json.dump(rep, open(os.path.join(OUT, "p17_report.json"), "w"), indent=1)
log("done")
