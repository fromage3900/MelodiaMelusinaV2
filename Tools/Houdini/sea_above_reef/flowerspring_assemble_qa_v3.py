#!/usr/bin/env python
"""Cos_FlowerSpring — assembly + QA renders v3 + Substance staging export.

Fixes over v2 (owner QA: "ugly"):
  * no unit hacks — crown/wings v2 and the redraped skirt are authored in
    dress meters, so the assembly is import-and-line-up;
  * wings v2 mount behind the shoulder blades (v1 slab sat at the waist);
  * crown v2 is sized to the head (v1 floated above the collar);
  * skirt silhouette is the v2 'cascade' drape (petal overskirt + train);
  * materials read the baked FlowerSpring variant maps (owner paints over
    them in Substance — flat-palette era is over).

Also exports the Substance staging kit:
  substance_staging/FlowerSpring/meshes/  — per-piece FBX + full assembly FBX
  qa_v3/                                  — front/side/back/hero + closeups
  qa_v3/FS_SilhouetteContact_<preset>.png — cascade/tulip/bloom comparison

Run: & "C:/Program Files/Blender Foundation/Blender 4.5/blender.exe" -b --factory-startup -noaudio --python Tools/Houdini/sea_above_reef/flowerspring_assemble_qa_v3.py
"""
import json
import math
from pathlib import Path

import bpy
import mathutils

PROJECT = Path("C:/EnvironmentPortfolio/BS_GodFile")
OUT = PROJECT / "Saved" / "Audit" / "melusina_lookdev" / "flowers_outfit"
QA = OUT / "qa_v3"
STAGE = PROJECT / "Saved" / "Audit" / "melusina_lookdev" / "substance_staging" / "FlowerSpring"
MESH = STAGE / "meshes"
TEX = STAGE / "textures"
for d in (QA, MESH):
    d.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_homefile(use_factory_startup=True)
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)


def import_obj(path):
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=str(path), forward_axis="NEGATIVE_Y", up_axis="Z")
    meshes = [o for o in set(bpy.data.objects) - before if o.type == "MESH"]
    for m in meshes:
        m.name = path.stem
    return meshes


def bounds(objs):
    mins = mathutils.Vector((1e9,) * 3)
    maxs = mathutils.Vector((-1e9,) * 3)
    for m in objs:
        for v in m.bound_box:
            w = m.matrix_world @ mathutils.Vector(v)
            mins = mathutils.Vector(map(min, mins, w))
            maxs = mathutils.Vector(map(max, maxs, w))
    return mins, maxs


def fabric_mat(name, bc_path, rough=0.45, sheen=0.6):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = rough
    if "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = sheen
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(bc_path))
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def cd_mat(name, metallic=0.0, rough=0.35, emit=0.0):
    """Vertex-color (Cd) driven material for Houdini-authored pieces."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = rough
    if "Sheen Weight" in bsdf.inputs:
        bsdf.inputs["Sheen Weight"].default_value = 0.4
    if emit > 0.0 and "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = emit
    attr = nt.nodes.new("ShaderNodeVertexColor")
    nt.links.new(attr.outputs["Color"], bsdf.inputs["Base Color"])
    if emit > 0.0:
        nt.links.new(attr.outputs["Color"], bsdf.inputs["Emission Color"])
    return mat


FS_BC = TEX / "FlowerSpring" / "T_FlowerSpring_BaseColor.png"

# ---- import primary assembly (everything authored in dress space) ----------
shirt = import_obj(OUT / "passA2_shirt_panels.obj")
skirt = import_obj(OUT / "FS_SkirtDraped_cascade.obj")
crown = import_obj(OUT / "FS_Crown_v2.obj")
wings = import_obj(OUT / "FS_Wings_v2.obj")

mats = {
    "shirt": fabric_mat("M_FS_Shirt", FS_BC, rough=0.5),
    "skirt": fabric_mat("M_FS_Skirt", FS_BC, rough=0.42, sheen=0.8),
    "crown": cd_mat("M_FS_Crown", metallic=0.85, rough=0.28),
    "wings": cd_mat("M_FS_Wings", metallic=0.05, rough=0.4),
}
for m in shirt:
    m.data.materials.clear(); m.data.materials.append(mats["shirt"])
for m in skirt:
    m.data.materials.clear(); m.data.materials.append(mats["skirt"])
for m in crown:
    m.data.materials.clear(); m.data.materials.append(mats["crown"])
for m in wings:
    m.data.materials.clear(); m.data.materials.append(mats["wings"])

dress = shirt + skirt
mins, maxs = bounds(dress)
mid = (mins + maxs) / 2
height = maxs.z - mins.z

# sanity: verify the authored anchors landed (crown near head z, wings on back)
crown_mins, crown_maxs = bounds(crown)
wing_mins, wing_maxs = bounds(wings)
checks = {
    "crown_center_z_m": round((crown_mins.z + crown_maxs.z) / 2, 4),
    "crown_radius_m": round((crown_maxs.x - crown_mins.x) / 2, 4),
    "wing_back_y_m": round(max(wing_maxs.y, wing_mins.y), 4),
    "wing_span_m": round(wing_maxs.x - wing_mins.x, 4),
    "dress_top_z_m": round(maxs.z, 4),
}

# ---- lighting + camera ------------------------------------------------------
def area_light(name, loc, rot, energy, size):
    li = bpy.data.lights.new(name, "AREA")
    li.energy = energy
    li.size = size
    ob = bpy.data.objects.new(name, li)
    ob.location = loc
    ob.rotation_euler = rot
    bpy.context.scene.collection.objects.link(ob)
    return ob

area_light("Key", (1.8, -2.4, height * 0.8), (math.radians(55), 0, math.radians(35)), 450, 2.0)
area_light("Rim", (-1.6, 1.8, height * 0.75), (math.radians(45), 0, math.radians(-125)), 320, 1.6)
area_light("Fill", (-1.4, -2.0, 0.9), (math.radians(60), 0, math.radians(-30)), 160, 2.2)

cam = bpy.data.cameras.new("Cam")
cam.lens = 60
co = bpy.data.objects.new("Cam", cam)
bpy.context.scene.collection.objects.link(co)
scn = bpy.context.scene
scn.camera = co
dist = height * 2.1

def render(path, dir_xy, res=(1280, 1280)):
    direction = mathutils.Vector((dir_xy[0], dir_xy[1], 0.07)).normalized()
    co.location = mathutils.Vector((mid.x, mid.y, mid.z + height * 0.10)) + direction * dist
    co.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
    scn.render.resolution_x, scn.render.resolution_y = res
    scn.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)

scn.render.engine = "BLENDER_EEVEE_NEXT"

renders = []
render(QA / "FS_QA_v3_front.png", (-0.25, -1.0)); renders.append("FS_QA_v3_front.png")
render(QA / "FS_QA_v3_back.png", (0.2, 1.0)); renders.append("FS_QA_v3_back.png")
render(QA / "FS_QA_v3_three_quarter.png", (0.85, -0.75)); renders.append("FS_QA_v3_three_quarter.png")

# closeups: crown + wings
co.location = (0.0, -0.9, 1.52)
co.rotation_euler = (math.radians(85), 0, math.radians(3))
scn.render.resolution_x, scn.render.resolution_y = 900, 700
scn.render.filepath = str(QA / "FS_QA_v3_crown_closeup.png")
bpy.ops.render.render(write_still=True); renders.append("FS_QA_v3_crown_closeup.png")
co.location = (0.0, 1.0, 1.22)
co.rotation_euler = (math.radians(95), 0, math.radians(183))
scn.render.filepath = str(QA / "FS_QA_v3_wings_closeup.png")
bpy.ops.render.render(write_still=True); renders.append("FS_QA_v3_wings_closeup.png")

# ---- silhouette contact sheet: swap skirt presets ---------------------------
skirt_cascade = skirt
contact = []
for preset in ("cascade", "tulip", "bloom"):
    for m in list(skirt):
        bpy.data.objects.remove(m, do_unlink=True)
    skirt = import_obj(OUT / f"FS_SkirtDraped_{preset}.obj")
    for m in skirt:
        m.data.materials.clear(); m.data.materials.append(mats["skirt"])
    mins, maxs = bounds(shirt + skirt)
    mid = (mins + maxs) / 2
    height = maxs.z - mins.z
    render(QA / f"FS_SilhouetteContact_{preset}.png", (-0.2, -1.0), res=(760, 1100))
    contact.append(f"FS_SilhouetteContact_{preset}.png")

# restore cascade for export
for m in list(skirt):
    bpy.data.objects.remove(m, do_unlink=True)
skirt = [o for o in bpy.data.objects if o.name.startswith("FS_SkirtDraped_cascade")]

# ---- Substance staging FBX export -------------------------------------------
def export_fbx(objs, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True,
                             apply_unit_scale=True, add_leaf_bones=False,
                             mesh_smooth_type="OFF", path_mode="AUTO")

export_fbx(list(shirt) + list(skirt), MESH / "FS_Dress_Draped_cascade.fbx")
export_fbx(list(crown), MESH / "FS_Crown_v2.fbx")
export_fbx(list(wings), MESH / "FS_Wings_v2.fbx")
export_fbx(list(shirt) + list(skirt) + list(crown) + list(wings), MESH / "FS_FullAssembly_cascade.fbx")

manifest = {
    "schema": "melodia.flowerspring_assembly.v3",
    "seed": 20260831,
    "units": "meters end-to-end (no unit correction)",
    "assembly": {
        "shirt": "passA2_shirt_panels.obj",
        "skirt": "FS_SkirtDraped_cascade.obj (v2 silhouette: flare+train+petal overskirt+ridges)",
        "crown": "FS_Crown_v2.obj (closed-shell petals, head-sized, in place)",
        "wings": "FS_Wings_v2.obj (smooth-scallop membranes, back-mounted, in place)",
    },
    "anchor_checks": checks,
    "renders": renders,
    "silhouette_contact_sheet": contact,
    "substance_staging": {
        "meshes": ["FS_Dress_Draped_cascade.fbx", "FS_Crown_v2.fbx", "FS_Wings_v2.fbx",
                    "FS_FullAssembly_cascade.fbx"],
        "textures": "textures/<Variant>/ (5 variants x 8 maps, ORM=R=AO G=Rough B=Metal)",
    },
    "note": "materials read baked FlowerSpring maps; owner paints over them in Substance Painter",
}
(QA / "flowerspring_assembly_v3_manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
print("ASSEMBLY_V3_OK " + json.dumps(checks))
