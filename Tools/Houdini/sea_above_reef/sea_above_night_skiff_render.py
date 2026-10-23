"""Sea Above - Night Skiff beauty render (Blender headless, EEVEE).

Loads the v5 Starskiff FBX, swaps in the Houdini-cooked NIGHT lookdev set
(T_Starskiff_Night_*), and renders a night-ocean scene: glossy teal water,
glowing wake foam strip, starfield, moon disc, biolum rim lights.

Outputs (manifest-driven):
  Saved/Audit/sea_above/renders/sea_above_night_skiff_hero.png
  Saved/Audit/sea_above/renders/sea_above_night_skiff_bow.png
  Saved/Audit/sea_above/renders/sea_above_night_skiff_manifest.json

Run:  blender --background --factory-startup -P Tools/Houdini/sea_above_reef/sea_above_night_skiff_render.py
"""

import json
import math
import random
import sys
from pathlib import Path

import bpy
import mathutils  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reef_common as rc  # noqa: E402

ROOT = rc.PROJECT_ROOT
FBX = ROOT / "Exports" / "Starskiff" / "SM_Starskiff_Proxy.fbx"
TEX = ROOT / "Saved" / "Audit" / "sea_above" / "houdini_variants"
OUT = ROOT / "Saved" / "Audit" / "sea_above" / "renders"
SEED = 20260829

TEAL_WATER = (0.008, 0.085, 0.105)
MOON_WHITE = (0.98, 0.96, 0.88)


def fresh_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for obj in list(bpy.data.objects):
        obj.select_set(True)
    if bpy.data.objects:
        bpy.ops.object.delete(use_global=False)


def load_tex(name):
    img = bpy.data.images.load(str(TEX / name))
    img.colorspace_settings.name = "Non-Color" if "Normal" in name or "Roughness" in name or "Emission" in name else "sRGB"
    return img


def make_tex_material(mat_name, base_img, normal_img=None, rough_img=None,
                      emissive_img=None, emissive_strength=1.0, base_tint=None):
    mat = bpy.data.materials.new(mat_name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for n in list(nodes):
        nodes.remove(n)
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    out = nodes.new(type="ShaderNodeOutputMaterial")
    bsdf.location = (0, 0)
    out.location = (260, 0)
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    y = 0
    if base_img is not None:
        node = nodes.new(type="ShaderNodeTexImage")
        node.image = base_img
        node.location = (-300, y)
        links.new(node.outputs["Color"], bsdf.inputs["Base Color"])
        y -= 240
    if base_tint is not None:
        bsdf.inputs["Base Color"].default_value = (*base_tint, 1.0)
    if normal_img is not None:
        node = nodes.new(type="ShaderNodeTexImage")
        node.image = normal_img
        node.location = (-300, y)
        y -= 200
        nm = nodes.new(type="ShaderNodeNormalMap")
        nm.location = (-120, y + 40)
        links.new(node.outputs["Color"], nm.inputs["Color"])
        links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
        y -= 240
    if rough_img is not None:
        node = nodes.new(type="ShaderNodeTexImage")
        node.image = rough_img
        node.location = (-300, y)
        links.new(node.outputs["Color"], bsdf.inputs["Roughness"])
        y -= 240
    if emissive_img is not None:
        node = nodes.new(type="ShaderNodeTexImage")
        node.image = emissive_img
        node.location = (-300, y)
        links.new(node.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = emissive_strength
    return mat


def assign_by_prefix(obj_name, mat):
    for obj in bpy.data.objects:
        if obj.type == "MESH" and obj.name.startswith(obj_name):
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)


def build_water():
    bpy.ops.mesh.primitive_plane_add(size=90, location=(0, 0, 0.045))
    water = bpy.context.active_object
    water.name = "NightOcean"
    mat = bpy.data.materials.new("NightOcean_Mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for n in list(nodes):
        nodes.remove(n)
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    out = nodes.new(type="ShaderNodeOutputMaterial")
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Base Color"].default_value = (*TEAL_WATER, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.05
    bsdf.inputs["Metallic"].default_value = 0.0
    water.data.materials.append(mat)
    return water


def build_stars(count=550):
    rng = random.Random(SEED)
    star_mat = bpy.data.materials.new("StarMat")
    star_mat.use_nodes = True
    nodes = star_mat.node_tree.nodes
    links = star_mat.node_tree.links
    for n in list(nodes):
        nodes.remove(n)
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    out = nodes.new(type="ShaderNodeOutputMaterial")
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Base Color"].default_value = (*MOON_WHITE, 1.0)
    bsdf.inputs["Emission Color"].default_value = (*MOON_WHITE, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 40.0
    for _ in range(count):
        # uniform on upper hemisphere shell
        u = rng.random()
        v = rng.random()
        theta = 2.0 * math.pi * u
        phi = math.acos(1.0 - v)  # 0..pi; keep z > 0 -> phi < pi/2
        phi = min(phi, math.pi * 0.46)
        r = 55.0
        loc = (r * math.sin(phi) * math.cos(theta),
               r * math.sin(phi) * math.sin(theta),
               r * math.cos(phi))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.09, location=loc)
        o = bpy.context.active_object
        o.name = "Star_%04d" % len([x for x in bpy.data.objects if x.name.startswith("Star_")])
        o.data.materials.append(star_mat)
    # a couple of bigger twinklers
    for _ in range(12):
        theta = rng.random() * 2 * math.pi
        phi = math.acos(1.0 - rng.random())
        phi = min(phi, math.pi * 0.46)
        loc = (55 * math.sin(phi) * math.cos(theta), 55 * math.sin(phi) * math.sin(theta), 55 * math.cos(phi))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=loc)
        o = bpy.context.active_object
        o.name = "StarBig_%04d" % len([x for x in bpy.data.objects if x.name.startswith("StarBig_")])
        o.data.materials.append(star_mat)


def build_moon():
    bpy.ops.mesh.primitive_circle_add(vertices=96, radius=2.4, location=(26, -20, 20))
    moon = bpy.context.active_object
    moon.name = "NightMoon"
    moon.rotation_euler = (math.pi / 2, 0, 0)
    # face origin
    dx, dy, dz = -26, 20, -20
    moon.rotation_euler = (0, -math.asin(dz / math.sqrt(dx*dx + dz*dz)), math.atan2(dy, dx))
    mat = bpy.data.materials.new("MoonMat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for n in list(nodes):
        nodes.remove(n)
    bsdf = nodes.new(type="ShaderNodeBsdfPrincipled")
    out = nodes.new(type="ShaderNodeOutputMaterial")
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    bsdf.inputs["Base Color"].default_value = (*MOON_WHITE, 1.0)
    bsdf.inputs["Emission Color"].default_value = (*MOON_WHITE, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 12.0
    moon.data.materials.append(mat)
    return moon


def build_lights():
    bpy.ops.object.light_add(type="SUN", location=(12, -18, 14))
    sun = bpy.context.active_object
    sun.name = "MoonLight"
    sun.data.energy = 2.6
    sun.data.color = (0.55, 0.65, 1.0)
    sun.rotation_euler = (math.radians(50), 0, math.radians(30))
    bpy.ops.object.light_add(type="POINT", location=(-4, -2, 1.6))
    bio = bpy.context.active_object
    bio.name = "BioFill"
    bio.data.energy = 60
    bio.data.color = (0.2, 0.9, 0.85)
    bpy.ops.object.light_add(type="POINT", location=(0, 7, 4))
    fill = bpy.context.active_object
    fill.name = "FillBlue"
    fill.data.energy = 70
    fill.data.color = (0.55, 0.65, 0.95)
    bpy.ops.object.light_add(type="POINT", location=(9, 5, 3))
    rim = bpy.context.active_object
    rim.name = "RimMoon"
    rim.data.energy = 90
    rim.data.color = (0.7, 0.8, 1.0)


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

    # import v5 skiff FBX
    bpy.ops.import_scene.fbx(filepath=str(FBX))
    # remove imported materials; rebuild from texture set
    for mat in [m for m in bpy.data.materials if m.users == 0]:
        bpy.data.materials.remove(mat)
    img_base = load_tex("T_Starskiff_Night_BaseColor.png")
    img_norm = load_tex("T_Starskiff_Night_Normal.png")
    img_rough = load_tex("T_Starskiff_Night_Roughness.png")
    img_wake = load_tex("T_Starskiff_Night_Wake_Emission.png")

    hull_mat = make_tex_material("SkiffNight_Hull", img_base, img_norm, img_rough)
    brass_mat = make_tex_material("SkiffNight_Brass", None, None, None,
                                  base_tint=(0.20, 0.14, 0.05))
    brass_mat2 = bpy.data.materials["SkiffNight_Brass"]
    brass_mat2.use_nodes = True
    nodes = brass_mat2.node_tree.nodes
    for n in nodes:
        if n.type == "BSDF_PRINCIPLED":
            n.inputs["Metallic"].default_value = 0.85
            n.inputs["Roughness"].default_value = 0.32
            n.inputs["Emission Color"].default_value = (1.0, 0.7, 0.25, 1.0)
            n.inputs["Emission Strength"].default_value = 0.35
    sail_mat = make_tex_material("SkiffNight_Sail", None, None, None,
                                 base_tint=(0.16, 0.20, 0.26))
    wake_mat = make_tex_material("SkiffNight_Wake", None, None, None,
                                 emissive_img=img_wake, emissive_strength=6.0)

    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        if obj.name.startswith("Starskiff_HullMain") or obj.name.startswith("Starskiff_Keel") \
           or obj.name.startswith("Starskiff_Stern") or obj.name.startswith("Starskiff_BowFlare"):
            obj.data.materials.append(hull_mat)
        elif obj.name.startswith("Starskiff_BrassRing") or obj.name.startswith("Starskiff_Mast"):
            obj.data.materials.append(brass_mat2)
        elif obj.name.startswith("Starskiff_Sail"):
            obj.data.materials.append(sail_mat)
        elif obj.name.startswith("Starskiff_WakeFoam"):
            obj.data.materials.append(wake_mat)

    build_water()
    build_moon()
    build_stars(550)
    build_lights()

    # world: deep indigo
    scene.world = bpy.data.worlds.new("NightWorld")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.006, 0.012, 0.035, 1.0)
    bg.inputs["Strength"].default_value = 1.0

    # EEVEE + bloom
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except Exception:
        scene.render.engine = "BLENDER_EEVEE"
    print("[night] engine:", scene.render.engine)
    try:
        scene.eevee.use_bloom = True
        scene.eevee.bloom_threshold = 0.55
        scene.eevee.bloom_intensity = 0.6
    except Exception as exc:
        print("[night] bloom tweak skipped:", exc)

    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.image_settings.file_format = "PNG"

    OUT.mkdir(parents=True, exist_ok=True)
    shots = {
        "hero": ((4.6, -6.0, 2.3), (0.0, 0.0, 1.1)),
        "bow": ((3.4, 3.0, 1.7), (1.6, 0.0, 0.9)),
    }
    outputs = []
    for shot_name, (loc, target) in shots.items():
        cam = add_camera(shot_name, loc, target)
        scene.camera = cam
        out_path = OUT / f"sea_above_night_skiff_{shot_name}.png"
        scene.render.filepath = str(out_path)
        bpy.ops.render.render(write_still=True)
        outputs.append({"shot": shot_name, "path": str(out_path),
                        "bytes": out_path.stat().st_size,
                        "sha256": rc.sha256_of(out_path)})
        print(f"[night] rendered {shot_name} -> {out_path}")

    manifest = {
        "schema": "melodia.sea_above_night_skiff_render.v1",
        "seed": SEED,
        "params": {
            "generator": "sea_above_night_skiff_render.py",
            "runtime": "Blender headless EEVEE",
            "engine": scene.render.engine,
            "fbx": str(FBX),
            "textures": "T_Starskiff_Night_* (Houdini cook starskiff_night_lookdev.py)",
            "scene": "night ocean + starfield + moon + biolum wake",
            "objects": len(bpy.data.objects),
        },
        "outputs": outputs,
    }
    mp = OUT / "sea_above_night_skiff_manifest.json"
    mp.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("[night] manifest ->", mp)
    print("[night] DONE")


if __name__ == "__main__":
    main()