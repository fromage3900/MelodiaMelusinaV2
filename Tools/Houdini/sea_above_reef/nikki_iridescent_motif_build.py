"""Nikki Iridescent Motif Set - Blender hero objects + showcase render.

Builds five Infinity-Nikki-style pieces using the Houdini-cooked T_Nikki_*
texture family: pearl, seashell, soap bubble, ribbon bow, gold ring.
Principled BSDF with Iridescence on; EEVEE bloom; dark violet stage with
pink/teal/gold rim lights.

Outputs (manifest-driven):
  Saved/Audit/sea_above/renders/nikki_motif_hero.png
  Saved/Audit/sea_above/renders/nikki_motif_macro.png
  Saved/Audit/sea_above/renders/nikki_motif_manifest.json

Run:  blender --background --factory-startup -P Tools/Houdini/sea_above_reef/nikki_iridescent_motif_build.py
"""

import json
import math
import sys
from pathlib import Path

import bpy
import mathutils  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc  # noqa: E402

ROOT = rc.PROJECT_ROOT
TEX = ROOT / "Saved" / "Audit" / "sea_above" / "houdini_variants"
OUT = ROOT / "Saved" / "Audit" / "sea_above" / "renders"
SEED = 20260829

GOLD = (0.96, 0.74, 0.34)


def fresh_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for obj in list(bpy.data.objects):
        obj.select_set(True)
    if bpy.data.objects:
        bpy.ops.object.delete(use_global=False)


def load_tex(name, noncolor=True):
    img = bpy.data.images.load(str(TEX / name))
    img.colorspace_settings.name = "Non-Color" if noncolor else "sRGB"
    return img


def make_principled(mat_name, base_img=None, normal_img=None, rough_img=None,
                    emissive_img=None, emissive_strength=0.0, base_tint=None,
                    metallic=0.0, roughness=0.2, transmission=0.0,
                    iridescence=1.0, ior=1.35, thickness=420.0, thickness_max=1400.0,
                    anisotropic=0.0):
    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for n in list(nodes):
        nodes.remove(n)
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    out = nodes.new(type="ShaderNodeOutputMaterial")
    bsdf.location = (0, 0)
    out.location = (280, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    def _set(key, value):
        try:
            bsdf.inputs[key].default_value = value
        except Exception:
            pass

    _set("Metallic", metallic)
    _set("Roughness", roughness)
    if transmission:
        try:
            bsdf.inputs["Transmission Weight"].default_value = transmission
        except Exception:
            try:
                bsdf.inputs["Transmission"].default_value = transmission
            except Exception:
                pass
    if iridescence:
        _set("Iridescence", iridescence)
        _set("Iridescence IOR", ior)
        _set("Iridescence Thickness", thickness)
        _set("Iridescence Thickness Max", thickness_max)
    if anisotropic:
        _set("Anisotropic", anisotropic)

    y = 0
    if base_img is not None:
        node = nodes.new(type="ShaderNodeTexImage")
        node.image = base_img
        node.location = (-320, y)
        links.new(node.outputs["Color"], bsdf.inputs["Base Color"])
        y -= 220
    if base_tint is not None:
        _set("Base Color", (*base_tint, 1.0))
    if normal_img is not None:
        node = nodes.new(type="ShaderNodeTexImage")
        node.image = normal_img
        node.location = (-320, y)
        y -= 200
        nm = nodes.new(type="ShaderNodeNormalMap")
        nm.location = (-140, y + 40)
        links.new(node.outputs["Color"], nm.inputs["Color"])
        links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
        y -= 220
    if rough_img is not None:
        node = nodes.new(type="ShaderNodeTexImage")
        node.image = rough_img
        node.location = (-320, y)
        links.new(node.outputs["Color"], bsdf.inputs["Roughness"])
        y -= 220
    if emissive_img is not None and emissive_strength:
        node = nodes.new(type="ShaderNodeTexImage")
        node.image = emissive_img
        node.location = (-320, y)
        links.new(node.outputs["Color"], bsdf.inputs["Emission Color"])
        _set("Emission Strength", emissive_strength)
    return mat


def build_pearl(loc):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.9, location=loc)
    o = bpy.context.active_object
    o.name = "Nikki_Pearl"
    o.scale = (1.0, 1.0, 1.05)
    o.modifiers.new("sub", "SUBSURF")
    o.modifiers["sub"].levels = 2
    return o


def build_shell(loc):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=loc)
    o = bpy.context.active_object
    o.name = "Nikki_Shell"
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="DESELECT")
    import bmesh
    bm = bmesh.from_edit_mesh(o.data)
    for v in bm.verts:
        if v.co.z < -0.02:
            v.select = True
    bmesh.update_edit_mesh(o.data)
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")
    o.scale = (1.7, 1.25, 0.55)
    bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.new()
    bm.from_mesh(o.data)
    for v in bm.verts:
        if abs(v.co.z) < 0.05:
            ang = math.atan2(v.co.y, v.co.x)
            v.co.z += math.sin(ang * 7.0) * 0.07 + 0.03
    bm.to_mesh(o.data)
    bm.free()
    o.data.update()
    o.modifiers.new("sub", "SUBSURF")
    o.modifiers["sub"].levels = 1
    return o


def build_bubble(loc):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.85, location=loc)
    o = bpy.context.active_object
    o.name = "Nikki_Bubble"
    o.modifiers.new("sub", "SUBSURF")
    o.modifiers["sub"].levels = 2
    return o


def build_ribbon(loc):
    bpy.ops.mesh.primitive_grid_add(size=1.7, x_subdivisions=7, y_subdivisions=7,
                                    location=loc)
    bpy.ops.transform.rotate(value=math.radians(38), orient_axis="Y")
    wing_a = bpy.context.active_object
    wing_a.name = "Nikki_Ribbon_A"
    bpy.ops.mesh.primitive_grid_add(size=1.7, x_subdivisions=7, y_subdivisions=7,
                                    location=(loc[0], loc[1] - 0.25, loc[2] - 0.1))
    bpy.ops.transform.rotate(value=math.radians(-38), orient_axis="Y")
    bpy.ops.transform.rotate(value=math.radians(28), orient_axis="Z")
    wing_b = bpy.context.active_object
    wing_b.name = "Nikki_Ribbon_B"
    bpy.ops.mesh.primitive_torus_add(major_radius=0.30, minor_radius=0.09,
                                     location=(loc[0], loc[1], loc[2] + 0.25))
    knot = bpy.context.active_object
    knot.name = "Nikki_Ribbon_Knot"
    return [wing_a, wing_b, knot]


def build_ring(loc):
    bpy.ops.mesh.primitive_torus_add(major_radius=0.72, minor_radius=0.11,
                                     location=loc)
    o = bpy.context.active_object
    o.name = "Nikki_GoldRing"
    o.rotation_euler = (math.radians(78), math.radians(12), 0)
    return o


def add_camera(name, loc, target):
    cam_data = bpy.data.cameras.new(name + "_cam")
    cam_data.lens = 50
    cam = bpy.data.objects.new(name, cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = loc
    direction = mathutils.Vector(target) - mathutils.Vector(loc)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    return cam


def main():
    fresh_scene()
    scene = bpy.context.scene

    img_base = load_tex("T_Nikki_Motif_BaseColor.png", noncolor=False)
    img_norm = load_tex("T_Nikki_Motif_Normal.png", noncolor=True)
    img_rough = load_tex("T_Nikki_Motif_Roughness.png", noncolor=True)
    img_emis = load_tex("T_Nikki_Motif_Emissive.png", noncolor=True)

    pearl_mat = make_principled("Nikki_Pearl_Mat", img_base, img_norm, img_rough,
                                img_emis, emissive_strength=0.35,
                                iridescence=1.0, thickness=420)
    shell_mat = make_principled("Nikki_Shell_Mat", img_base, img_norm, img_rough,
                                img_emis, emissive_strength=0.45,
                                iridescence=1.0, thickness=520, transmission=0.12)
    bubble_mat = make_principled("Nikki_Bubble_Mat", None, None, None,
                                 img_emis, emissive_strength=0.15,
                                 transmission=0.9, iridescence=1.0, thickness=300)
    ribbon_mat = make_principled("Nikki_Ribbon_Mat", img_base, img_norm, img_rough,
                                 img_emis, emissive_strength=0.25,
                                 iridescence=0.85, thickness=380, anisotropic=0.85,
                                 roughness=0.28)
    gold_mat = make_principled("Nikki_Gold_Mat", None, None, None, None, 0.0,
                               metallic=1.0, roughness=0.24, iridescence=0.0)
    gold_mat.node_tree.nodes  # ensure exists
    for n in gold_mat.node_tree.nodes:
        if n.type == "BSDF_PRINCIPLED":
            n.inputs["Base Color"].default_value = (*GOLD, 1.0)

    pearl = build_pearl((-3.1, 0.2, 1.15))
    shell = build_shell((-0.5, -0.3, 0.85))
    ring = build_ring((0.0, 1.1, 0.5))
    bubble = build_bubble((3.1, -0.2, 1.7))
    ribbons = build_ribbon((-0.9, -1.0, 2.3))

    pearl.data.materials.append(pearl_mat)
    shell.data.materials.append(shell_mat)
    ring.data.materials.append(gold_mat)
    bubble.data.materials.append(bubble_mat)
    for r in ribbons:
        r.data.materials.append(ribbon_mat)

    # floor: dark glossy violet
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "Nikki_Floor"
    fmat = bpy.data.materials.new("Nikki_Floor_Mat")
    fmat.use_nodes = True
    nodes = fmat.node_tree.nodes
    links = fmat.node_tree.links
    for n in list(nodes):
        nodes.remove(n)
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    out = nodes.new(type="ShaderNodeOutputMaterial")
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Base Color"].default_value = (0.012, 0.008, 0.03, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.08
    floor.data.materials.append(fmat)

    # lights: Nikki tri-color rims + gold key
    bpy.ops.object.light_add(type="POINT", location=(4.5, -3.5, 3.2))
    pink = bpy.context.active_object
    pink.name = "RimPink"
    pink.data.energy = 160
    pink.data.color = (1.0, 0.45, 0.75)
    bpy.ops.object.light_add(type="POINT", location=(-4.5, 2.5, 3.0))
    teal = bpy.context.active_object
    teal.name = "RimTeal"
    teal.data.energy = 140
    teal.data.color = (0.30, 0.90, 0.85)
    bpy.ops.object.light_add(type="POINT", location=(0.5, 4.2, 4.5))
    gold = bpy.context.active_object
    gold.name = "KeyGold"
    gold.data.energy = 90
    gold.data.color = (1.0, 0.80, 0.55)
    bpy.ops.object.light_add(type="POINT", location=(0, -4.5, 1.6))
    fill = bpy.context.active_object
    fill.name = "FillBlue"
    fill.data.energy = 60
    fill.data.color = (0.45, 0.55, 0.9)

    scene.world = bpy.data.worlds.new("NikkiWorld")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.01, 0.007, 0.022, 1.0)

    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except Exception:
        scene.render.engine = "BLENDER_EEVEE"
    print("[nikki] engine:", scene.render.engine)
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.image_settings.file_format = "PNG"

    OUT.mkdir(parents=True, exist_ok=True)
    shots = {
        "hero": ((5.2, -5.8, 3.4), (0.0, 0.0, 1.25)),
        "macro": ((1.9, -2.1, 1.6), (0.9, 0.0, 1.25)),
    }
    outputs = []
    for shot_name, (loc, target) in shots.items():
        cam = add_camera(shot_name, loc, target)
        scene.camera = cam
        out_path = OUT / f"nikki_motif_{shot_name}.png"
        scene.render.filepath = str(out_path)
        bpy.ops.render.render(write_still=True)
        outputs.append({"shot": shot_name, "path": str(out_path),
                        "bytes": out_path.stat().st_size,
                        "sha256": rc.sha256_of(out_path)})
        print(f"[nikki] rendered {shot_name} -> {out_path}")

    manifest = {
        "schema": "melodia.nikki_iridescent_motif_render.v1",
        "seed": SEED,
        "params": {
            "generator": "nikki_iridescent_motif_build.py",
            "runtime": "Blender headless EEVEE",
            "engine": scene.render.engine,
            "textures": "T_Nikki_* (Houdini cook nikki_iridescent_lookdev.py)",
            "objects": ["Nikki_Pearl", "Nikki_Shell", "Nikki_SoapBubble",
                        "Nikki_Ribbon_A/B/Knot", "Nikki_GoldRing"],
            "iridescence": "Principled BSDF Iridescence (IOR 1.35, film 300-520nm)",
            "stage": "dark violet gloss floor; pink/teal/gold rims; EEVEE bloom",
        },
        "outputs": outputs,
    }
    mp = OUT / "nikki_motif_manifest.json"
    mp.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("[nikki] manifest ->", mp)
    print("[nikki] DONE")


if __name__ == "__main__":
    main()