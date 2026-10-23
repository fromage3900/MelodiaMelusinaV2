"""Blender headless render QA for ALL Sea Above reef work (R1-R5, R3 kelp, R4 islands).

Runs INSIDE Blender only:
  blender --background --python Tools/Houdini/sea_above_reef/render_qa_blender.py -- --all

What it produces (Saved/Audit/sea_above/renders/):
  meshes/<SM_*>.png        clay-shaded hero shot, 3-point rig (warm key / aqua fill /
                           cool rim - the SeaAbove palette), camera auto-fit, x100 scale
  textures/flat/<T_*>.png  straight-on shaded view (albedos via Principled, data maps
                           via emission so values read raw)
  textures/sphere/<T_*>.png  2-axis tilables wrapped x2 on a lit sphere (seam/value check)
  render_manifest.json     per-render record + engine/settings

Deterministic: fixed rig, fixed camera, fixed resolution. Sheet assembly happens in
system Python (assemble_contact_sheets.py) because Blender lacks Pillow.

Engine: Cycles CPU at low samples - reliable headless (EEVEE/Workbench may need a GPU
context that background Blender does not always get).
"""

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT_ROOT = Path(__file__).resolve().parents[3]
TEX_DIR = PROJECT_ROOT / "Content/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Textures"
MESH_DIR = PROJECT_ROOT / "Content/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes"
OUT_DIR = PROJECT_ROOT / "Saved/Audit/sea_above/renders"

KEY = (1.0, 0.88, 0.72)      # warm key
FILL = (0.50, 0.85, 0.90)    # aquamarine fill
RIM = (0.75, 0.88, 1.0)      # cool rim
WORLD = (0.035, 0.045, 0.065)

CLAY = (0.62, 0.60, 0.58)

# 2-axis tilables get a sphere render with repeat 2; everything else flat-only
TILABLE_HINTS = ("Sand", "ShellMask", "WetRock", "BarnacleCrust", "CoralSkin",
                 "Foam", "ClutterFloor")
ALBEDO_HINTS = ("Albedo", "_LUT_Band", "PulseBand", "Sediment", "Atlas")


def _clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
        for item in list(block):
            if item.users == 0:
                block.remove(item)


def _light(name, loc, color, energy, size=1.5):
    data = bpy.data.lights.new(name, type="AREA")
    data.energy = energy
    data.color = color
    data.size = size
    ob = bpy.data.objects.new(name, data)
    ob.location = loc
    bpy.context.collection.objects.link(ob)
    return ob


def _rig(center, diag, review_fix=True):
    """3-point SeaAbove rig + camera auto-fit. All distances/energies scale with
    the bounding diag (objects are in cm; fixed offsets put lights INSIDE meshes
    — the dark-render bug caught by the visual review)."""
    d = max(diag, 1.0)
    key = _light("Key", center + Vector((1.0, -1.2, 1.2)).normalized() * d * 1.1,
                 KEY, 900 * d * d)
    _light("Fill", center + Vector((-1.3, -0.65, 0.42)).normalized() * d * 1.3,
           FILL, 380 * d * d, 2.2 * d)
    _light("Rim", center + Vector((0.2, 1.1, 0.9)).normalized() * d * 1.25,
           RIM, 520 * d * d, 1.8 * d)
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 60
    cam_data.clip_start = 0.01
    cam_data.clip_end = 1e6   # cm-scale scenes overflow the default 100-unit far plane
    cam = bpy.data.objects.new("Cam", cam_data)
    dist = d * 1.65 + 0.35
    direction = Vector((1.0, -1.35, 0.62)).normalized()
    cam.location = center + direction * dist
    bpy.context.collection.objects.link(cam)
    target = bpy.data.objects.new("Target", None)
    target.location = center
    bpy.context.collection.objects.link(target)
    constraint = cam.constraints.new(type="TRACK_TO")
    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    _ = key
    return cam


def _setup_render(engine, samples, size):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES" if engine == "cycles" else engine
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.film_transparent = False
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (*WORLD, 1.0)
        bg.inputs[1].default_value = 1.0


def _material(name, color, texture_path=None, emission=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if texture_path and bsdf:
        tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(str(texture_path))
        tex.image.colorspace_settings.name = ("sRGB" if any(h in name for h in ALBEDO_HINTS)
                                              else "Non-Color")
        mat.node_tree.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    if emission and bsdf:
        bsdf.inputs["Emission Color"].default_value = (*color, 1.0) \
            if "Emission Color" in bsdf.inputs else (0, 0, 0, 1)
        try:
            bsdf.inputs["Emission Strength"].default_value = 1.0
        except Exception:
            pass
    if not texture_path and bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    if bsdf:
        bsdf.inputs["Roughness"].default_value = 0.55
    return mat


def _bbox_center_diag(objs):
    lo = Vector((1e9, 1e9, 1e9))
    hi = Vector((-1e9, -1e9, -1e9))
    for ob in objs:
        if ob.type != "MESH":
            continue
        for corner in ob.bound_box:
            world = ob.matrix_world @ Vector(corner)
            lo = Vector(map(min, lo, world))
            hi = Vector(map(max, hi, world))
    center = (lo + hi) / 2.0
    diag = (hi - lo).length
    return center, diag


def _import_obj(path):
    """Version-tolerant OBJ import (4.x/5.x wm.obj_import, 3.x import_scene.obj)."""
    before = set(bpy.data.objects)
    try:
        bpy.ops.wm.obj_import(filepath=str(path))
    except AttributeError:
        bpy.ops.import_scene.obj(filepath=str(path))
    return [o for o in bpy.data.objects if o not in before]


def _done(out_path, args):
    return (args.skip_existing and not args.force and Path(out_path).exists())


def render_meshes(args):
    out_dir = OUT_DIR / "meshes"
    out_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for obj_path in sorted(MESH_DIR.glob("*.obj")):
        target = out_dir / f"{obj_path.stem}.png"
        if _done(target, args):
            records.append({"asset": obj_path.stem, "render": str(target.relative_to(PROJECT_ROOT)),
                            "mode": "mesh_clay", "skipped_existing": True})
            print(f"[render] mesh {obj_path.stem} (existing)")
            continue
        _clear_scene()
        _setup_render(args.engine, args.samples, args.size)
        objs = _import_obj(obj_path)
        for ob in objs:
            if ob.type == "MESH":
                ob.scale = (100.0, 100.0, 100.0)   # metres -> UE cm
                ob.data.materials.clear()
                ob.data.materials.append(_material("Clay", CLAY))
        bpy.context.view_layer.update()
        center, diag = _bbox_center_diag(objs)
        cam = _rig(center, diag / 100.0 * 100.0)  # diag already in cm after scale
        bpy.context.scene.camera = cam
        name = obj_path.stem
        bpy.context.scene.render.filepath = str(out_dir / f"{name}.png")
        bpy.ops.render.render(write_still=True)
        records.append({"asset": name, "render": str((out_dir / f"{name}.png").relative_to(PROJECT_ROOT)),
                        "mode": "mesh_clay"})
        print(f"[render] mesh {name}")
    return records


def _plane(textures_dir, tex_path, out_dir, mode, records, args):
    _clear_scene()
    _setup_render(args.engine, args.samples, args.size)
    mat = _material(tex_path.stem, (0.8, 0.8, 0.8), texture_path=tex_path,
                    emission=not any(h in tex_path.stem for h in ALBEDO_HINTS))
    if mode == "sphere":
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=48, ring_count=24)
        ob = bpy.context.object
        mat.node_tree.nodes.new("ShaderNodeMapping")
        mapping = [n for n in mat.node_tree.nodes if n.type == "MAPPING"][-1]
        mapping.inputs["Scale"].default_value = (2.0, 2.0, 1.0)
        coord = mat.node_tree.nodes.new("ShaderNodeTexCoord")
        mat.node_tree.links.new(coord.outputs["UV"], mapping.inputs["Vector"])
        tex_node = [n for n in mat.node_tree.nodes if n.type == "TEX_IMAGE"][0]
        mat.node_tree.links.new(mapping.outputs["Vector"], tex_node.inputs["Vector"])
    else:
        bpy.ops.mesh.primitive_plane_add(size=2.2)
        ob = bpy.context.object
    ob.data.materials.append(mat)
    ob.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    center, diag = _bbox_center_diag([ob])
    cam = _rig(center, max(diag, 1.0) if mode == "sphere" else 2.4)
    bpy.context.scene.camera = cam
    bpy.context.scene.render.filepath = str(out_dir / f"{tex_path.stem}.png")
    bpy.ops.render.render(write_still=True)
    records.append({"asset": tex_path.stem, "render": str((out_dir / f"{tex_path.stem}.png").relative_to(PROJECT_ROOT)),
                    "mode": f"texture_{mode}"})
    print(f"[render] texture/{mode} {tex_path.stem}")


def render_textures(args, tex_dir=None, out_name=None):
    base = Path(tex_dir) if tex_dir else TEX_DIR
    tag = out_name or ("" if base == TEX_DIR else base.name)
    flat_dir = OUT_DIR / "textures" / "flat" / tag if tag else OUT_DIR / "textures" / "flat"
    sphere_dir = OUT_DIR / "textures" / "sphere" / tag if tag else OUT_DIR / "textures" / "sphere"
    flat_dir.mkdir(parents=True, exist_ok=True)
    sphere_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for tex_path in sorted(base.glob("*.png")):
        if _done(flat_dir / f"{tex_path.stem}.png", args):
            records.append({"asset": tex_path.stem,
                            "render": str((flat_dir / f"{tex_path.stem}.png").relative_to(PROJECT_ROOT)),
                            "mode": "texture_flat", "skipped_existing": True})
            print(f"[render] texture/flat {tex_path.stem} (existing)")
        else:
            _plane(base, tex_path, flat_dir, "flat", records, args)
        if any(h in tex_path.stem for h in TILABLE_HINTS):
            if _done(sphere_dir / f"{tex_path.stem}.png", args):
                records.append({"asset": tex_path.stem,
                                "render": str((sphere_dir / f"{tex_path.stem}.png").relative_to(PROJECT_ROOT)),
                                "mode": "texture_sphere", "skipped_existing": True})
                print(f"[render] texture/sphere {tex_path.stem} (existing)")
            else:
                _plane(base, tex_path, sphere_dir, "sphere", records, args)
    return records


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--meshes", action="store_true")
    ap.add_argument("--textures", action="store_true")
    ap.add_argument("--engine", default="cycles")
    ap.add_argument("--samples", type=int, default=24)
    ap.add_argument("--size", type=int, default=640)
    ap.add_argument("--skip-existing", action="store_true",
                    help="resume: skip renders whose PNG already exists")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--tex-dir", default=None,
                    help="override texture dir (e.g. the melusina_lookdev audit dir)")
    ap.add_argument("--tex-out", default=None,
                    help="override texture render output subdir name")
    args = ap.parse_args(argv)
    do_meshes = args.all or args.meshes
    do_textures = args.all or args.textures
    if not (do_meshes or do_textures):
        do_meshes = do_textures = True

    records = []
    if do_meshes:
        records += render_meshes(args)
    if do_textures:
        if args.tex_dir:                      # override mode: only the given dir
            records += render_textures(args, tex_dir=args.tex_dir, out_name=args.tex_out)
        else:
            records += render_textures(args)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "melodia.sea_above_render_qa.v1",
        "engine": args.engine, "samples": args.samples, "resolution": args.size,
        "lights": {"key": KEY, "fill": FILL, "rim": RIM, "world": WORLD},
        "renders": records,
    }
    (OUT_DIR / "render_manifest.json").write_text(json.dumps(payload, indent=2),
                                                  encoding="utf-8")
    print(f"[render] {len(records)} renders -> render_manifest.json")


if __name__ == "__main__":
    main()
