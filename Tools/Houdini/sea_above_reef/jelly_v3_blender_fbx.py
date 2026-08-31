"""Jellyfish V3 SERAPH — JSON -> Blender -> FBX + QA renders.

Same contract as v2's converter, extended for the v3 structure:
  - JELLY_Seraph_Body.fbx : root armature + every static part (3 golden-ratio
    tiers, halo, 55 cilia) as meshes carrying Basis + 3 shape keys each
    (same pose names -> existing morph-driver wiring style).
  - JELLY_Seraph_Arms.fbx : 13 golden-angle ribbon arms (static).
  - Clay QA renders with the fixed rig (normal recalc, world ambient,
    bbox-scaled fill, clip_end=1e7), Blender 4.5.

Run:
  & "C:\\Program Files\\Blender Foundation\\Blender 4.5\\blender.exe" -b ^
      --factory-startup -noaudio --python Tools/Houdini/sea_above_reef/jelly_v3_blender_fbx.py
"""

import json
import sys
from pathlib import Path

import bmesh
import bpy
import mathutils

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MESH_JSON = PROJECT_ROOT / "Saved/Audit/sea_above/meshes/jellyfish_mesh_v3_seraph.json"
OUT_DIR = PROJECT_ROOT / "Saved/Audit/sea_above/meshes"
RENDER_DIR = PROJECT_ROOT / "Saved/Audit/sea_above/renders/jelly_v3"
POSES = ["PulseContract", "PulseExpand", "SurrealLurch"]


def build_mesh(name, pts, faces, uvs):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(pts, [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vi = mesh.loops[li].vertex_index
            uv_layer.data[li].uv = uvs[vi]
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def add_shapekeys(obj, part):
    bpy.context.view_layer.objects.active = obj
    obj.shape_key_add(name="Basis").interpolation = "KEY_LINEAR"
    for pose in POSES:
        sk = obj.shape_key_add(name=pose)
        sk.interpolation = "KEY_LINEAR"
        for vi, pos in enumerate(part["poses"][pose]["points"]):
            sk.data[vi].co = pos
        sk.value = 0.0


def diag(objects):
    lo = mathutils.Vector((1e9,) * 3)
    hi = mathutils.Vector((-1e9,) * 3)
    for o in objects:
        for c in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(c)
            lo = mathutils.Vector(map(min, lo, w))
            hi = mathutils.Vector(map(max, hi, w))
    return lo, hi, (hi - lo).length


def render_scene(objects, out_path):
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
    lo, hi, diag_len = diag(objects)
    center = (lo + hi) * 0.5
    cam_data = bpy.data.cameras.new("QA_Cam")
    cam_data.clip_start = 1.0
    cam_data.clip_end = 1e7
    cam = bpy.data.objects.new("QA_Cam", cam_data)
    bpy.context.collection.objects.link(cam)
    direction = mathutils.Vector((0.55, -0.8, 0.30)).normalized()
    cam.location = center + direction * (diag_len * 0.85)
    look = center - cam.location
    cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    sun_data = bpy.data.lights.new("QA_Sun", "SUN")
    sun_data.energy = 4.0
    sun = bpy.data.objects.new("QA_Sun", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (mathutils.Vector((0.4, 0.3, -1.0))).to_track_quat("Z", "Y").to_euler()
    fill_data = bpy.data.lights.new("QA_Fill", "AREA")
    fill_data.energy = max(100000.0, diag_len * diag_len * 4.0)
    fill_data.size = max(10.0, diag_len * 0.6)
    fill = bpy.data.objects.new("QA_Fill", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = center + direction * (diag_len * 0.7)
    fill.rotation_euler = (center - fill.location).to_track_quat("-Z", "Y").to_euler()
    world = bpy.data.worlds.get("QA_World") or bpy.data.worlds.new("QA_World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.05, 0.06, 0.08, 1.0)
        bg.inputs[1].default_value = 1.0
    clay = bpy.data.materials.get("QA_Clay") or bpy.data.materials.new("QA_Clay")
    clay.diffuse_color = (0.62, 0.72, 0.80, 1.0)
    for o in objects:
        if o.type == "MESH":
            o.data.materials.clear()
            o.data.materials.append(clay)
    bpy.ops.render.render(write_still=True)
    print(f"[seraph-fbx] render -> {out_path}")


def main():
    # optional argv: [json_path, body_fbx_name, arms_fbx_name, render_dir, render_prefix]
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    mesh_json = Path(argv[0]) if len(argv) > 0 else MESH_JSON
    body_name = argv[1] if len(argv) > 1 else "JELLY_Seraph_Body.fbx"
    arms_name = argv[2] if len(argv) > 2 else "JELLY_Seraph_Arms.fbx"
    render_dir = Path(argv[3]) if len(argv) > 3 else RENDER_DIR
    prefix = argv[4] if len(argv) > 4 else "SERAPH"
    payload = json.loads(mesh_json.read_text(encoding="utf-8"))
    bpy.ops.wm.read_factory_settings(use_empty=True)

    arm = bpy.data.armatures.new("JELLY_Seraph_Root")
    arm_obj = bpy.data.objects.new("JELLY_Seraph_Root", arm)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    bone = arm.edit_bones.new("root")
    bone.head = (0, 0, 0)
    bone.tail = (0, 0, 10)
    bpy.ops.object.mode_set(mode="OBJECT")

    static_objs = []
    for part_name, part in payload["static_parts"].items():
        obj = build_mesh(f"SERAPH_{part_name}", part["mesh"]["points"],
                         part["mesh"]["faces"], part["mesh"]["uvs"])
        add_shapekeys(obj, part)
        obj.parent = arm_obj
        static_objs.append(obj)

    arms = []
    for i, arm_geo in enumerate(payload["arms"]):
        arms.append(build_mesh(f"SERAPH_Arm_{i:02d}", arm_geo["points"],
                               arm_geo["faces"], arm_geo["uvs"]))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    render_dir.mkdir(parents=True, exist_ok=True)

    bpy.ops.object.select_all(action="DESELECT")
    for o in static_objs + [arm_obj]:
        o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(OUT_DIR / body_name),
                             use_selection=True, add_leaf_bones=False,
                             bake_anim=False, object_types={"ARMATURE", "MESH"},
                             mesh_smooth_type="OFF")
    bpy.ops.object.select_all(action="DESELECT")
    for a in arms:
        a.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(OUT_DIR / arms_name),
                             use_selection=True, add_leaf_bones=False,
                             bake_anim=False, object_types={"MESH"},
                             mesh_smooth_type="OFF")
    print(f"[seraph-fbx] FBX written: {body_name} "
          f"({len(static_objs)} parts) + {arms_name} ({len(arms)} arms)")

    render_scene(static_objs + arms, render_dir / f"{prefix}_Overview.png")
    tiers = [o for o in static_objs if "tier" in o.name or "halo" in o.name]
    render_scene(tiers + arms, render_dir / f"{prefix}_Crown.png")

    manifest = {
        "schema": "melodia.sea_above_reef_meshes.v1",
        "kind": f"jellyfish {prefix} FBX + QA renders",
        "static_parts": len(static_objs),
        "shapekey_sets": ["Basis"] + POSES,
        "arms": len(arms),
        "body_fbx": str(OUT_DIR / body_name),
        "arms_fbx": str(OUT_DIR / arms_name),
        "renders": [str(render_dir / f"{prefix}_Overview.png"),
                    str(render_dir / f"{prefix}_Crown.png")],
        "source_json": str(mesh_json),
        "blender": bpy.app.version_string,
    }
    (OUT_DIR / f"jellyfish_{prefix.lower()}_fbx_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[seraph-fbx] manifest -> jellyfish_{prefix.lower()}_fbx_manifest.json")


main()
