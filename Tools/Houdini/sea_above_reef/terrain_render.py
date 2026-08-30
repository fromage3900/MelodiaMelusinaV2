"""Cloth-mountain v0 — OBJ clay QA render (Blender 4.5, fixed rig).

Run:
  & "C:\\Program Files\\Blender Foundation\\Blender 4.5\\blender.exe" -b ^
      --factory-startup -noaudio --python Tools/Houdini/sea_above_reef/terrain_render.py
"""

import json
import math
from pathlib import Path

import bpy
import mathutils

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OBJ = PROJECT_ROOT / "Saved/Audit/faraway_mother/SM_ClothMountains_v0.obj"
RENDER_DIR = PROJECT_ROOT / "Saved/Audit/faraway_mother/renders"


def diag(objects):
    lo = mathutils.Vector((1e9,) * 3)
    hi = mathutils.Vector((-1e9,) * 3)
    for o in objects:
        for c in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(c)
            lo = mathutils.Vector(map(min, lo, w))
            hi = mathutils.Vector(map(max, hi, w))
    return lo, hi, (hi - lo).length


def render(objects, out_path, angle_deg, cam_h):
    scene = bpy.context.scene
    for eng in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE", "CYCLES"):
        try:
            scene.render.engine = eng
            break
        except TypeError:
            continue
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.filepath = str(out_path)
    lo, hi, d = diag(objects)
    center = (lo + hi) * 0.5
    a = math.radians(angle_deg)
    direction = mathutils.Vector((math.cos(a), -math.sin(a), 0.0))
    cam_data = bpy.data.cameras.new("QA_Cam")
    cam_data.clip_start = 1.0
    cam_data.clip_end = 1e7
    cam = bpy.data.objects.new("QA_Cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = center + direction * (d * 0.9) + mathutils.Vector((0, 0, cam_h))
    cam.rotation_euler = (center - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    sun_data = bpy.data.lights.new("QA_Sun", "SUN")
    sun_data.energy = 4.0
    sun = bpy.data.objects.new("QA_Sun", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (mathutils.Vector((0.5, 0.35, -1.0))).to_track_quat("Z", "Y").to_euler()
    fill_data = bpy.data.lights.new("QA_Fill", "AREA")
    fill_data.energy = max(100000.0, d * d * 4.0)
    fill_data.size = max(10.0, d * 0.6)
    fill = bpy.data.objects.new("QA_Fill", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = center + direction * (d * 0.7) + mathutils.Vector((0, 0, cam_h * 0.6))
    fill.rotation_euler = (center - fill.location).to_track_quat("-Z", "Y").to_euler()
    world = bpy.data.worlds.get("QA_World") or bpy.data.worlds.new("QA_World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.05, 0.06, 0.08, 1.0)
        bg.inputs[1].default_value = 1.0
    clay = bpy.data.materials.get("QA_Clay") or bpy.data.materials.new("QA_Clay")
    clay.diffuse_color = (0.65, 0.70, 0.78, 1.0)
    for o in objects:
        if o.type == "MESH":
            o.data.materials.clear()
            o.data.materials.append(clay)
    bpy.ops.render.render(write_still=True)
    print(f"[cloth-render] -> {out_path}")


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.obj_import(filepath=str(OBJ))
    meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    render(meshes, RENDER_DIR / "ClothMountains_v0_North.png", 0.0, 500.0)
    render(meshes, RENDER_DIR / "ClothMountains_v0_Aerial.png", 40.0, 1600.0)
    manifest = {
        "schema": "melodia.faraway_mother_terrain.v1",
        "kind": "cloth-mountain v0 clay QA renders",
        "renders": [str(RENDER_DIR / "ClothMountains_v0_North.png"),
                    str(RENDER_DIR / "ClothMountains_v0_Aerial.png")],
        "source_obj": str(OBJ),
        "blender": bpy.app.version_string,
    }
    (RENDER_DIR / "cloth_mountains_v0_render_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print("[cloth-render] manifest written")


main()
