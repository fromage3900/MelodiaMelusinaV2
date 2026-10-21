#!/usr/bin/env python
"""Render Mr. Sheep variants from Painter exports — headless Blender 4.5.

For each variant dir under --exports (one subdir per variant with Painter
PBR maps), wire BaseColor / Roughness / Metallic / Normal / Emissive onto
a Principled material, drop a three-point rig, auto-frame the camera to the
mesh bounds, and write one Cycles still per variant.

Run:
  "C:/Program Files/Blender Foundation/Blender 4.5/blender.exe" -b -P \
      render_variants_blender.py -- --exports <dir> --fbx <sheep.fbx> \
      --outdir <dir> --res 512 --samples 48

Montage afterwards with montage_renders.py (local python + PIL).

Melodia / Melusina only. No Grok*.
"""
import argparse
import math
import os
import sys

import bpy
from mathutils import Vector


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--exports", required=True)
    ap.add_argument("--fbx", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--res", type=int, default=512)
    ap.add_argument("--samples", type=int, default=48)
    return ap.parse_args(argv)


MAP_SUFFIXES = {
    "basecolor": "BaseColor",
    "base_color": "BaseColor",
    "roughness": "Roughness",
    "metallic": "Metallic",
    "normal": "Normal",
    "emissive": "Emissive",
    "emission": "Emissive",
}


def find_map(dirpath, key):
    for f in sorted(os.listdir(dirpath)):
        if not f.lower().endswith(".png"):
            continue
        stem = os.path.splitext(f)[0].lower()
        for suffix, name in MAP_SUFFIXES.items():
            if name == key and (stem.endswith("_" + suffix)
                                or stem.endswith(suffix)):
                return os.path.join(dirpath, f)
    return None


def setup_material():
    mat = bpy.data.materials.new("MrSheep_Composer")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (250, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    tex = {}
    coords = nt.nodes.new("ShaderNodeTexCoord")
    coords.location = (-900, 0)
    for key, loc in (("BaseColor", (-600, 300)),
                     ("Roughness", (-600, 60)),
                     ("Metallic", (-600, -180)),
                     ("Normal", (-600, -420)),
                     ("Emissive", (-600, -660))):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.location = loc
        n.label = key
        nt.links.new(coords.outputs["UV"], n.inputs["Vector"])
        tex[key] = n
    for key in ("Roughness", "Metallic", "Normal"):
        tex[key].image = None
    nrm = nt.nodes.new("ShaderNodeNormalMap")
    nrm.location = (-250, -420)
    nt.links.new(tex["Normal"].outputs["Color"], nrm.inputs["Color"])
    nt.links.new(nrm.outputs["Normal"], bsdf.inputs["Normal"])
    nt.links.new(tex["BaseColor"].outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex["Roughness"].outputs["Color"], bsdf.inputs["Roughness"])
    nt.links.new(tex["Metallic"].outputs["Color"], bsdf.inputs["Metallic"])
    try:
        nt.links.new(tex["Emissive"].outputs["Color"],
                     bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 1.2
    except KeyError:
        pass
    return mat, tex


def set_image(node, path, srgb):
    if path and os.path.isfile(path):
        img = bpy.data.images.load(path, check_existing=False)
        try:
            img.colorspace_settings.name = "sRGB" if srgb else "Non-Color"
        except Exception:
            pass
        node.image = img
        node.mute = False
    else:
        node.mute = True


def main():
    args = parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=args.fbx)

    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        raise SystemExit("no meshes imported from %s" % args.fbx)

    mat, tex = setup_material()
    for ob in meshes:
        ob.data.materials.clear()
        ob.data.materials.append(mat)

    # bounds
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for ob in meshes:
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            lo = Vector((min(lo[i], w[i]) for i in range(3)))
            hi = Vector((max(hi[i], w[i]) for i in range(3)))
    center = (lo + hi) / 2
    size = max((hi - lo).length, 1e-3)

    # camera
    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    direction = Vector((0.9, -1.0, 0.45)).normalized()
    cam.location = center + direction * size * 1.35
    cam.rotation_euler = (center - cam.location).to_track_quat(
        "-Z", "Y").to_euler()
    cam_data.clip_start = size * 0.01
    cam_data.clip_end = size * 50
    bpy.context.scene.camera = cam

    # lights
    def add_light(name, kind, loc, energy, **kw):
        d = bpy.data.lights.new(name, kind)
        d.energy = energy
        for k, v in kw.items():
            setattr(d, k, v)
        o = bpy.data.objects.new(name, d)
        o.location = loc
        o.rotation_euler = (Vector(center) - Vector(loc)).to_track_quat(
            "-Z", "Y").to_euler()
        bpy.context.scene.collection.objects.link(o)
        return o

    add_light("Key", "SUN", center + Vector((1.2, -1.6, 1.8)) * size,
              3.2, angle=0.3)
    add_light("Fill", "AREA", center + Vector((-1.6, -0.9, 0.7)) * size,
              60.0, size=size)
    add_light("Rim", "AREA", center + Vector((-0.4, 1.6, 1.2)) * size,
              90.0, size=size * 0.7)

    world = bpy.data.worlds.new("W")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.02, 0.018, 0.03, 1.0)
        bg.inputs[1].default_value = 1.0

    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    try:
        scn.cycles.device = "CPU"
        scn.cycles.samples = args.samples
        scn.cycles.use_denoising = True
    except Exception:
        pass
    scn.render.resolution_x = args.res
    scn.render.resolution_y = args.res
    scn.render.image_settings.file_format = "PNG"

    os.makedirs(args.outdir, exist_ok=True)
    variants = sorted(d for d in os.listdir(args.exports)
                      if os.path.isdir(os.path.join(args.exports, d)))
    print("rendering variants:", variants)
    for v in variants:
        d = os.path.join(args.exports, v)
        set_image(tex["BaseColor"], find_map(d, "BaseColor"), True)
        set_image(tex["Roughness"], find_map(d, "Roughness"), False)
        set_image(tex["Metallic"], find_map(d, "Metallic"), False)
        set_image(tex["Normal"], find_map(d, "Normal"), False)
        set_image(tex["Emissive"], find_map(d, "Emissive"), True)
        for img in bpy.data.images:
            try:
                img.reload()
            except Exception:
                pass
        scn.render.filepath = os.path.join(args.outdir, v + ".png")
        print("render:", v)
        bpy.ops.render.render(write_still=True)
    print("done; renders in", args.outdir)


if __name__ == "__main__":
    main()
