# -*- coding: utf-8 -*-
"""Sheep stage build (headless, off a COPY): canonical rig verified -> stage the
retopo mesh with v2 PC_C coat albedo + the staged sculpted normal, save stage."""
import bpy, json, os, shutil, math

SRC = r"C:\Users\froma\OneDrive\Desktop\choralsheep.blend"
STAGE_DIR = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\choral_sheep"
STAGE = os.path.join(STAGE_DIR, "choralsheep_stage_20260908.blend")
V2 = r"Saved/Audit/choral_sheep/houdini_variants_v2"
NORM = r"Saved/Audit/choral_sheep/sculpted_normals/T_ChoralSheep_Normal.png"
os.makedirs(STAGE_DIR, exist_ok=True)
if not os.path.exists(STAGE):
    shutil.copy2(SRC, STAGE)
    print("STAGE copied from Desktop source")
bpy.ops.wm.open_mainfile(filepath=STAGE)

def img(name, path, noncolor):
    i = bpy.data.images.get(name)
    if i is None:
        i = bpy.data.images.load(path, check_existing=True); i.name = name
    i.colorspace_settings.name = "Non-Color" if noncolor else "sRGB"
    return i

albedo = img("T_SheepCoat_PC_C", os.path.abspath(os.path.join(V2, "ChoralWool_PC_C.png")), False)
normal = img("T_ChoralSheep_Normal", os.path.abspath(NORM), True)

mat = bpy.data.materials.get("ME_Sheep_Coat_PC_C") or bpy.data.materials.new("ME_Sheep_Coat_PC_C")
mat.use_nodes = True
nt = mat.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
p = nt.nodes.new("ShaderNodeBsdfPrincipled"); p.location = (-300, 0)
p.inputs["Roughness"].default_value = 0.55
sw = p.inputs.get("Sheen Weight") or p.inputs.get("Sheen")
if sw: sw.default_value = 0.45
ta = nt.nodes.new("ShaderNodeTexImage"); ta.image = albedo; ta.location = (-700, 200)
tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = normal; tn.location = (-700, -150)
nm = nt.nodes.new("ShaderNodeNormalMap"); nm.inputs["Strength"].default_value = 0.85; nm.location = (-450, -150)
nt.links.new(ta.outputs["Color"], p.inputs["Base Color"])
nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
nt.links.new(nm.outputs["Normal"], p.inputs["Normal"])
nt.links.new(p.outputs[0], out.inputs["Surface"])

mesh = bpy.data.objects["Retopo_Skin_Sheep_ZSpheres2"]
mesh.data.materials.clear(); mesh.data.materials.append(mat)

# simple presentation: hide control meshes, view layer to solid+texture
for ob in bpy.data.objects:
    if ob.type == "MESH" and ob.name.startswith("cs_"):
        ob.hide_render = True
        try: ob.hide_set(True)
        except Exception: pass
mesh.hide_set(False); mesh.hide_render = False
ar = bpy.data.objects.get("rig");  ar and (setattr(ar, "hide_render", False))
bpy.ops.wm.save_mainfile()
print("STAGE_SAVED", STAGE)
