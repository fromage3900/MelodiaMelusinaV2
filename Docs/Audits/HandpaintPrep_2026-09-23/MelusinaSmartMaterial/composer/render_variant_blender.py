#!/usr/bin/env python
"""Render ONE Mr. Sheep variant from Painter exports — headless Blender 4.5.

Per-invocation design: a fresh Blender process per variant removes all
cross-render image/materials cross-talk (a single-process batch proved
unreliable here). Two modes:

  beauty (default): Principled material wired to BaseColor / Roughness /
      Metallic / Normal / Emissive + three-point rig — "what it looks like".
  albedo (--albedo): UNLIT pass — BaseColor straight into Emission with the
      Standard view transform — "what the variant IS"; makes hue identity
      unmistakable on the model.

Run (per variant):
  "C:/Program Files/Blender Foundation/Blender 4.5/blender.exe" -b -P \
      render_variant_blender.py -- --exports <dir> --fbx <mesh> \
      --outdir <dir> --variant Verse [--albedo] [--res 512] [--samples 48]

Montage afterwards with montage_renders.py (local python + PIL).

(This supersedes render_variants_blender.py, whose single-process batch
muted the variant map swaps. Kept alongside for reference.)

Melodia / Melusina only. No Grok*.
"""
import argparse
import os
import sys

import bpy
from mathutils import Vector

MAP_SUFFIXES = {
    "basecolor": "BaseColor",
    "base_color": "BaseColor",
    "roughness": "Roughness",
    "metallic": "Metallic",
    "normal": "Normal",
    "emissive": "Emissive",
    "emission": "Emissive",
    # SMS2 iridescence kit (optional; loaders degrade silently when absent)
    "coatcolor": "CoatColor",
    "coatopacity": "CoatOpacity",
    "coatroughness": "CoatRoughness",
    "sheencolor": "SheenColor",
    "sheenopacity": "SheenOpacity",
    "specularedgecolor": "SpecularEdgeColor",
}


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--exports", required=True)
    ap.add_argument("--fbx", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--variant", required=True)
    ap.add_argument("--albedo", action="store_true")
    ap.add_argument("--res", type=int, default=512)
    ap.add_argument("--samples", type=int, default=48)
    ap.add_argument("--zoom", type=float, default=1.0)
    return ap.parse_args(argv)


def find_map(dirpath, key):
    for f in sorted(os.listdir(dirpath)):
        if not f.lower().endswith(".png"):
            continue
        stem = os.path.splitext(f)[0].lower()
        for suffix, name in MAP_SUFFIXES.items():
            # underscore-anchored only: "…_coatroughness" must NOT satisfy
            # Roughness (the loose clause did, and poisoned the render)
            if name == key and stem.endswith("_" + suffix):
                return os.path.join(dirpath, f)
    return None


def load_image(path, srgb):
    if not path or not os.path.isfile(path):
        return None
    img = bpy.data.images.load(path, check_existing=False)
    try:
        img.colorspace_settings.name = "sRGB" if srgb else "Non-Color"
    except Exception:
        pass
    return img


def setup_material(variant_dir, albedo):
    mat = bpy.data.materials.new("MrSheep_Composer")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (600, 0)
    coords = nt.nodes.new("ShaderNodeTexCoord")
    coords.location = (-900, 0)

    if albedo:
        emit = nt.nodes.new("ShaderNodeEmission")
        emit.location = (250, 0)
        emit.inputs["Strength"].default_value = 1.0
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.location = (-500, 0)
        tex.label = "BaseColor"
        tex.image = load_image(find_map(variant_dir, "BaseColor"), True)
        nt.links.new(coords.outputs["UV"], tex.inputs["Vector"])
        nt.links.new(tex.outputs["Color"], emit.inputs["Color"])
        nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
        return mat

    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (250, 0)
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    tex = {}
    for key, loc in (("BaseColor", (-600, 300)),
                     ("Roughness", (-600, 60)),
                     ("Metallic", (-600, -180)),
                     ("Normal", (-600, -420)),
                     ("Emissive", (-600, -660))):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.location = loc
        n.label = key
        if loc[1] > 200 or key == "Emissive":
            n.image = load_image(find_map(variant_dir, key), True)
        else:
            n.image = load_image(find_map(variant_dir, key), False)
        if n.image is None:
            n.mute = True
        nt.links.new(coords.outputs["UV"], n.inputs["Vector"])
        tex[key] = n
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
        # notes must GLOW (Nikki lens) — 1.0 read as "not glowing"
        bsdf.inputs["Emission Strength"].default_value = 2.2
    except KeyError:
        pass

    # ---- SMS2 iridescence kit: coat + sheen, loaded when the export
    # carries them (rich preset); silently skipped otherwise.
    def _try_link(path, inname, srgb=True):
        img = load_image(path, srgb)
        if img is None:
            return False
        n = nt.nodes.new("ShaderNodeTexImage")
        n.location = (-600, -900)
        n.image = img
        nt.links.new(coords.outputs["UV"], n.inputs["Vector"])
        for out_name in ("Color", "Alpha"):
            try:
                nt.links.new(n.outputs[out_name], bsdf.inputs[inname])
                return True
            except Exception:
                continue
        return False

    coat_c = _try_link(find_map(variant_dir, "CoatColor"), "Coat Tint")
    _try_link(find_map(variant_dir, "CoatRoughness"), "Coat Roughness",
              srgb=False)
    if not _try_link(find_map(variant_dir, "CoatOpacity"), "Coat Weight",
                     srgb=False) and coat_c:
        try:
            bsdf.inputs["Coat Weight"].default_value = 0.40
        except Exception:
            pass
    _try_link(find_map(variant_dir, "SheenColor"), "Sheen Tint")
    if _try_link(find_map(variant_dir, "SheenOpacity"), "Sheen Weight",
                 srgb=False):
        try:
            bsdf.inputs["Sheen Roughness"].default_value = 0.50
        except Exception:
            pass
    return mat


def main():
    args = parse_args()
    vdir = os.path.join(args.exports, args.variant)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=args.fbx)
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    if not meshes:
        raise SystemExit("no meshes imported from %s" % args.fbx)

    mat = setup_material(vdir, args.albedo)
    for ob in meshes:
        ob.data.materials.clear()
        ob.data.materials.append(mat)

    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for ob in meshes:
        for c in ob.bound_box:
            w = ob.matrix_world @ Vector(c)
            lo = Vector((min(lo[i], w[i]) for i in range(3)))
            hi = Vector((max(hi[i], w[i]) for i in range(3)))
    center = (lo + hi) / 2
    size = max((hi - lo).length, 1e-3)

    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    direction = Vector((0.9, -1.0, 0.45)).normalized()
    target = center
    if args.zoom < 1.0:
        # close-up: aim at the chest (front quadrant, slightly high)
        direction = Vector((-0.55, -1.0, 0.30)).normalized()
        target = center + Vector((0.0, 0.0, size * 0.10))
    cam.location = target + direction * size * 1.35 * args.zoom
    cam.rotation_euler = (target - cam.location).to_track_quat(
        "-Z", "Y").to_euler()
    cam_data.clip_start = size * 0.01
    cam_data.clip_end = size * 50
    bpy.context.scene.camera = cam

    if not args.albedo:
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
                  4.5, angle=0.3)
        add_light("Fill", "AREA", center + Vector((-1.6, -0.9, 0.7)) * size,
                  95.0, size=size)
        add_light("Rim", "AREA", center + Vector((-0.4, 1.6, 1.2)) * size,
                  150.0, size=size * 0.7)

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
        scn.cycles.use_denoising = not args.albedo
    except Exception:
        pass
    try:
        scn.view_settings.view_transform = "Standard"
    except Exception:
        pass
    scn.render.resolution_x = args.res
    scn.render.resolution_y = args.res
    scn.render.image_settings.file_format = "PNG"

    # Bloom for the beauty pass — the "magical" read needs glare; Cycles
    # itself has none, so wire a Fog Glow in the compositor.
    if not args.albedo:
        try:
            scn.use_nodes = True
            ntree = scn.node_tree
            for n in list(ntree.nodes):
                ntree.nodes.remove(n)
            rl = ntree.nodes.new("CompositorNodeRLayers")
            glare = ntree.nodes.new("CompositorNodeGlare")
            glare.glare_type = "FOG_GLOW"
            try:
                glare.quality = "HIGH"
            except Exception:
                pass
            for attr, val in (("threshold", 0.85), ("size", 7),
                              ("mix", -0.25)):
                try:
                    setattr(glare, attr, val)
                except Exception:
                    pass
            comp = ntree.nodes.new("CompositorNodeComposite")
            ntree.links.new(rl.outputs["Image"], glare.inputs[0])
            ntree.links.new(glare.outputs[0], comp.inputs[0])
        except Exception:
            pass

    os.makedirs(args.outdir, exist_ok=True)
    scn.render.filepath = os.path.join(args.outdir, args.variant + ".png")
    print("render:", args.variant, "albedo" if args.albedo else "beauty")
    bpy.ops.render.render(write_still=True)
    print("done:", scn.render.filepath)


if __name__ == "__main__":
    main()
