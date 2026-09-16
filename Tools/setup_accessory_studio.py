"""
Accessory studio pass - Fade Sky + eyewear-origin framing for accessory lookdev.

Frames cameras to world origin (0,0,0) where the eyewear host sits.
No character-rig dependencies; uses 3-point lighting (Key/Rim/Fill area lights)
and Fade Assets Sky Night world.

Runs in open Blender 5.1+ on a base scene with an eyewear host at origin.

- Fade Assets sky world (Sky Night from data.blend)
- Studio cyclorama (Ground + Backdrop + FloorCard)
- 3-point lighting: Key (warm), Rim (pink), Fill (cool)
- 5 cameras: Beauty / Front / Macro / Low / Turntable, all clip_start=0.001
- Render: EEVEE, 1600x2000, 64 TAA, bloom 0.05

Usage:
  exec(open(r"P:\\MelodiaMelusinaV2-Laptop\\Tools\\setup_accessory_studio.py").read())
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(r"P:\MelodiaMelusinaV2-Laptop")
SAVE = ROOT / "Saved" / "Accessories"

# Fade Assets data.blend — adjust per machine if needed
FADE_DATA = Path(
    r"C:\Users\brenn\AppData\Roaming\Blender Foundation\Blender\5.1"
    r"\extensions\user_default\fadeassets\data\data.blend"
)
FADE_SKY = "Sky Night"
WORLD_NAME = "W_Melodia_AccessoryStudio"

# Portrait plate
RES_X, RES_Y = 1600, 2000

# Melodia-tinted night (multiplied into Fade sky BG if editable)
TINT_HORIZON = (0.55, 0.35, 0.62, 1.0)
TINT_ZENITH = (0.08, 0.06, 0.18, 1.0)

# Eyewear host position — world origin
HOST_ORIGIN = Vector((0.0, 0.0, 0.0))


def log(msg: str) -> None:
    print(f"[accessory-studio] {msg}", flush=True)


def ensure_collection(name: str) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


def link_obj(obj: bpy.types.Object, col: bpy.types.Collection) -> None:
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    col.objects.link(obj)


def aim_camera(cam: bpy.types.Object, target: Vector) -> None:
    direction = target - cam.matrix_world.translation
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_fade_sky() -> str:
    """Append Fade Assets sky world and assign to scene."""
    if not FADE_DATA.is_file():
        raise FileNotFoundError(f"Fade Assets data missing: {FADE_DATA}")

    sky_name = FADE_SKY
    existing = bpy.data.worlds.get(WORLD_NAME) or bpy.data.worlds.get(sky_name)
    if existing is None:
        before = {w.name for w in bpy.data.worlds}
        with bpy.data.libraries.load(str(FADE_DATA), link=False) as (data_from, data_to):
            if sky_name not in data_from.worlds:
                raise RuntimeError(f"Fade sky '{sky_name}' not in library: {list(data_from.worlds)}")
            data_to.worlds = [sky_name]
        added = [w for w in bpy.data.worlds if w.name not in before]
        world = added[0] if added else bpy.data.worlds.get(sky_name)
        if world is None:
            raise RuntimeError("Failed to append Fade sky world")
        world.name = WORLD_NAME
    else:
        world = existing
        if world.name != WORLD_NAME:
            world.name = WORLD_NAME

    bpy.context.scene.world = world
    world.use_nodes = True

    nt = world.node_tree
    if nt:
        bgs = [n for n in nt.nodes if n.type == "BACKGROUND"]
        if len(bgs) >= 2:
            bgs[0].inputs[0].default_value = TINT_ZENITH
            bgs[1].inputs[0].default_value = TINT_HORIZON
        elif len(bgs) == 1:
            bgs[0].inputs[0].default_value = TINT_HORIZON
            if bgs[0].inputs[1].default_value < 0.35:
                bgs[0].inputs[1].default_value = 0.55

    if hasattr(world, "mist_settings"):
        world.mist_settings.use_mist = True
        world.mist_settings.start = 4.0
        world.mist_settings.depth = 18.0
        world.mist_settings.falloff = "QUADRATIC"

    log(f"Fade sky active: {world.name}")
    return world.name


def setup_studio_set() -> dict:
    """Cyclorama: ground plane, backdrop, floor card."""
    studio = ensure_collection("Studio")
    report: dict = {"ground": None, "backdrop": None, "floorcard": None}

    # Ground
    ground = bpy.data.objects.get("Ground")
    if ground is None:
        bpy.ops.mesh.primitive_plane_add(size=12.0, location=(0, 0, 0))
        ground = bpy.context.active_object
        ground.name = "Ground"
    link_obj(ground, studio)
    ground.scale = (1.4, 1.4, 1.0)
    if hasattr(ground, "is_shadow_catcher"):
        ground.is_shadow_catcher = False
    report["ground"] = ground.name

    # Cyclorama backdrop behind host
    backdrop = bpy.data.objects.get("Studio_Backdrop")
    if backdrop is None:
        bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0, 3.2, 1.6))
        backdrop = bpy.context.active_object
        backdrop.name = "Studio_Backdrop"
        backdrop.scale = (7.0, 4.2, 1.0)
        backdrop.rotation_euler = (math.radians(90), 0, 0)
    link_obj(backdrop, studio)
    report["backdrop"] = backdrop.name

    # Soft floor card ring
    ring = bpy.data.objects.get("Studio_FloorCard")
    if ring is None:
        bpy.ops.mesh.primitive_circle_add(vertices=64, radius=2.4, fill_type="NGON", location=(0, 0, 0.002))
        ring = bpy.context.active_object
        ring.name = "Studio_FloorCard"
    link_obj(ring, studio)
    report["floorcard"] = ring.name

    return report


def setup_cameras(target: Vector) -> dict:
    """Create/position 5 cameras framed to eyewear host at world origin."""
    specs = {
        "Cam_Beauty": {
            "loc": Vector((1.20, -1.80, 0.18)),
            "lens": 50.0,
            "look": target,
            "dof_dist": None,
        },
        "Cam_Front": {
            "loc": Vector((0.0, -1.90, 0.0)),
            "lens": 55.0,
            "look": target,
            "dof_dist": None,
        },
        "Cam_Macro": {
            "loc": Vector((0.35, -0.70, 0.08)),
            "lens": 90.0,
            "look": target,
            "dof_dist": None,
        },
        "Cam_Low": {
            "loc": Vector((1.00, -1.40, -0.30)),
            "lens": 42.0,
            "look": target,
            "dof_dist": None,
        },
        "Cam_Turntable": {
            "loc": Vector((1.40, -1.85, 0.20)),
            "lens": 52.0,
            "look": target,
            "dof_dist": None,
        },
    }

    cams_c = ensure_collection("Cameras")
    out = {}
    for name, spec in specs.items():
        cam = bpy.data.objects.get(name)
        if cam is None or cam.type != "CAMERA":
            data = bpy.data.cameras.new(name)
            cam = bpy.data.objects.new(name, data)
            cams_c.objects.link(cam)
        cam.location = spec["loc"]
        cam.data.lens = spec["lens"]
        cam.data.clip_start = 0.001
        cam.data.clip_end = 50.0
        cam.data.sensor_width = 36.0
        aim_camera(cam, spec["look"])
        if hasattr(cam.data, "dof"):
            cam.data.dof.use_dof = False
        out[name] = {
            "loc": [round(x, 3) for x in cam.location],
            "lens": cam.data.lens,
            "look": [round(x, 3) for x in spec["look"]],
        }
        log(f"{name} -> loc={out[name]['loc']} lens={cam.data.lens} clip_start=0.001")

    beauty = bpy.data.objects.get("Cam_Beauty")
    if beauty:
        bpy.context.scene.camera = beauty
    return out


def setup_3point_lights() -> dict:
    """Key / Rim / Fill area lights for accessory lookdev."""
    lights_c = ensure_collection("Lights_AccessoryStudio")
    report = {}

    # Key (warm) — main light
    key = bpy.data.objects.get("L_Key")
    if key is None:
        data = bpy.data.lights.new("L_Key", type="AREA")
        key = bpy.data.objects.new("L_Key", data)
        lights_c.objects.link(key)
    key.location = Vector((0.6, -0.5, 0.8))
    key.data.energy = 400.0
    key.data.color = (1.0, 0.93, 0.84)
    key.data.size = 0.5
    aim_camera(key, HOST_ORIGIN)
    report["L_Key"] = {"energy": 400.0, "loc": [round(x, 3) for x in key.location]}

    # Rim (pink) — edge separation
    rim = bpy.data.objects.get("L_Rim")
    if rim is None:
        data = bpy.data.lights.new("L_Rim", type="AREA")
        rim = bpy.data.objects.new("L_Rim", data)
        lights_c.objects.link(rim)
    rim.location = Vector((-0.5, 0.3, 0.6))
    rim.data.energy = 250.0
    rim.data.color = (1.0, 0.45, 0.72)
    rim.data.size = 0.4
    aim_camera(rim, HOST_ORIGIN)
    report["L_Rim"] = {"energy": 250.0, "loc": [round(x, 3) for x in rim.location]}

    # Fill (cool) — soft shadow fill
    fill = bpy.data.objects.get("L_Fill")
    if fill is None:
        data = bpy.data.lights.new("L_Fill", type="AREA")
        fill = bpy.data.objects.new("L_Fill", data)
        lights_c.objects.link(fill)
    fill.location = Vector((-0.4, -0.6, 0.3))
    fill.data.energy = 120.0
    fill.data.color = (0.45, 0.82, 1.0)
    fill.data.size = 0.6
    aim_camera(fill, HOST_ORIGIN)
    report["L_Fill"] = {"energy": 120.0, "loc": [round(x, 3) for x in fill.location]}

    return report


def setup_render() -> dict:
    """EEVEE, 1600x2000, 64 TAA, bloom 0.05."""
    scene = bpy.context.scene
    engines = {e.identifier for e in scene.bl_rna.properties["render"].fixed_type.properties["engine"].enum_items}
    if "BLENDER_EEVEE_NEXT" in engines:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    else:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = RES_X
    scene.render.resolution_y = RES_Y
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    if hasattr(scene, "eevee"):
        ee = scene.eevee
        if hasattr(ee, "taa_render_samples"):
            ee.taa_render_samples = 64
        if hasattr(ee, "use_bloom"):
            ee.use_bloom = True
        if hasattr(ee, "bloom_intensity"):
            ee.bloom_intensity = 0.05
    return {
        "engine": scene.render.engine,
        "res": [RES_X, RES_Y],
        "camera": scene.camera.name if scene.camera else None,
    }


def save_blend(filepath: Path) -> None:
    """Save the current .blend to the given path."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(filepath))
    log(f"Saved blend: {filepath}")


def main() -> dict:
    target = HOST_ORIGIN
    log(f"Framing cameras to eyewear host at {target}")

    world = setup_fade_sky()
    set_report = setup_studio_set()
    cams = setup_cameras(target)
    lights = setup_3point_lights()
    render = setup_render()

    # Save the accessory studio blend
    output_path = SAVE / "Melodia_Accessory_Studio_v1.blend"
    save_blend(output_path)

    result = {
        "world": world,
        "target": [round(x, 3) for x in target],
        "cameras": cams,
        "lights": lights,
        "set": set_report,
        "render": render,
        "saved_blend": str(output_path),
    }
    log(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    main()
