"""Jellyfish V2 GRAND — JSON -> Blender -> FBX + QA renders.

Contract (matches the v1 engine path):
  - JELLY_Bell_V2.fbx : single root armature, basis (Neutral) + 3 shape keys
    (PulseContract / PulseExpand / SurrealLurch) — same names as v1 so the
    existing morph-driver wiring stays valid.
  - JELLY_Arms_V2.fbx : 12 ribbon arm meshes in one file (UE importer splits).
  - QA renders (clay + flat) with bbox-scaled rig and clip_end=1e7 (the cm-scale
    lesson), using Blender 4.5 (5.2 background color pipeline is broken on this
    box).

Run (headless, factory startup, no audio):
  & "C:\\Program Files\\Blender Foundation\\Blender 4.5\\blender.exe" -b ^
      --factory-startup -noaudio --python Tools/Houdini/sea_above_reef/jelly_v2_blender_fbx.py
"""

import json
import sys
from pathlib import Path

import bpy
import mathutils

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MESH_JSON = PROJECT_ROOT / "Saved/Audit/sea_above/meshes/jellyfish_mesh_v2_grand.json"
OUT_DIR = PROJECT_ROOT / "Saved/Audit/sea_above/meshes"
RENDER_DIR = PROJECT_ROOT / "Saved/Audit/sea_above/renders/jelly_v2"
POSES = ["PulseContract", "PulseExpand", "SurrealLurch"]


def build_mesh(name, pts, faces, uvs):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(pts, [], faces)
    mesh.update()
    import bmesh
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


def add_shapekeys(bell_obj, payload):
    bpy.context.view_layer.objects.active = bell_obj
    basis = bell_obj.shape_key_add(name="Basis")
    basis.interpolation = "KEY_LINEAR"
    for pose in POSES:
        sk = bell_obj.shape_key_add(name=pose)
        sk.interpolation = "KEY_LINEAR"
        pose_pts = payload["bell_poses"][pose]["points"]
        for vi, pos in enumerate(pose_pts):
            sk.data[vi].co = pos
        sk.value = 0.0


def add_root_armature(bell_obj):
    arm = bpy.data.armatures.new("JELLY_Root")
    arm_obj = bpy.data.objects.new("JELLY_Root", arm)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    bone = arm.edit_bones.new("root")
    bone.head = (0, 0, 0)
    bone.tail = (0, 0, 10)
    bpy.ops.object.mode_set(mode="OBJECT")
    bell_obj.parent = arm_obj
    return arm_obj


def diag(objects):
    lo = mathutils.Vector((1e9,) * 3)
    hi = mathutils.Vector((-1e9,) * 3)
    for o in objects:
        for c in o.bound_box:
            w = o.matrix_world @ mathutils.Vector(c)
            lo = mathutils.Vector(map(min, lo, w))
            hi = mathutils.Vector(map(max, hi, w))
    return lo, hi, (hi - lo).length


def render_scene(objects, out_path, suffix):
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
    direction = mathutils.Vector((0.55, -0.8, 0.35)).normalized()
    cam.location = center + direction * (diag_len * 0.9)
    look = center - cam.location
    cam.rotation_euler = look.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    sun_data = bpy.data.lights.new("QA_Sun", "SUN")
    sun_data.energy = 4.0
    sun = bpy.data.objects.new("QA_Sun", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (mathutils.Vector((0.4, 0.3, -1.0))).to_track_quat("Z", "Y").to_euler()
    # fill from the camera side + world ambient (the near-black render lesson)
    fill_data = bpy.data.lights.new("QA_Fill", "AREA")
    fill_data.energy = max(100000.0, diag_len * diag_len * 4.0)
    fill_data.size = max(10.0, diag_len * 0.6)
    fill = bpy.data.objects.new("QA_Fill", fill_data)
    bpy.context.collection.objects.link(fill)
    fill.location = center + direction * (diag_len * 0.7)
    aim = center - fill.location
    fill.rotation_euler = aim.to_track_quat("-Z", "Y").to_euler()
    world = bpy.data.worlds.get("QA_World") or bpy.data.worlds.new("QA_World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.05, 0.06, 0.08, 1.0)
        bg.inputs[1].default_value = 1.0
    for mat in bpy.data.materials:
        if mat.users == 0:
            bpy.data.materials.remove(mat)
    clay = bpy.data.materials.new(f"QA_Clay_{suffix}")
    clay.diffuse_color = (0.62, 0.72, 0.80, 1.0)
    for o in objects:
        if o.type == "MESH":
            o.data.materials.clear()
            o.data.materials.append(clay)
    bpy.ops.render.render(write_still=True)
    print(f"[jellyv2-fbx] render -> {out_path}")


def main():
    payload = json.loads(MESH_JSON.read_text(encoding="utf-8"))
    bpy.ops.wm.read_factory_settings(use_empty=True)

    bell = build_mesh("JELLY_Bell_V2", payload["bell"]["points"],
                      payload["bell"]["faces"], payload["bell"]["uvs"])
    add_shapekeys(bell, payload)
    add_root_armature(bell)

    arms = []
    for i, arm in enumerate(payload["arms"]):
        arms.append(build_mesh(f"JELLY_Arm_V2_{i:02d}", arm["points"],
                               arm["faces"], arm["uvs"]))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_homefile(use_empty=False) if False else None

    # FBX exports (selection-based)
    bpy.ops.object.select_all(action="DESELECT")
    bell.select_set(True)
    if bell.parent:
        bell.parent.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(OUT_DIR / "JELLY_Bell_V2.fbx"),
                             use_selection=True, add_leaf_bones=False,
                             bake_anim=False, object_types={"ARMATURE", "MESH"},
                             mesh_smooth_type="OFF")
    bpy.ops.object.select_all(action="DESELECT")
    for a in arms:
        a.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(OUT_DIR / "JELLY_Arms_V2.fbx"),
                             use_selection=True, add_leaf_bones=False,
                             bake_anim=False, object_types={"MESH"},
                             mesh_smooth_type="OFF")
    print(f"[jellyv2-fbx] FBX written: JELLY_Bell_V2.fbx + JELLY_Arms_V2.fbx "
          f"({len(arms)} arms)")

    # QA renders (clay, bbox-fitted — the cm-scale lessons)
    render_scene([bell] + arms, RENDER_DIR / "JELLY_V2_Overview.png", "ov")
    render_scene([bell], RENDER_DIR / "JELLY_V2_Bell.png", "bell")

    manifest = {
        "schema": "melodia.sea_above_reef_meshes.v1",
        "kind": "jellyfish v2 grand FBX + QA renders",
        "bell_shapekeys": ["Basis"] + POSES,
        "arms": len(arms),
        "bell_fbx": str(OUT_DIR / "JELLY_Bell_V2.fbx"),
        "arms_fbx": str(OUT_DIR / "JELLY_Arms_V2.fbx"),
        "renders": [str(RENDER_DIR / "JELLY_V2_Overview.png"),
                    str(RENDER_DIR / "JELLY_V2_Bell.png")],
        "source_json": str(MESH_JSON),
        "blender": bpy.app.version_string,
    }
    (OUT_DIR / "jellyfish_v2_grand_fbx_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print("[jellyv2-fbx] manifest -> jellyfish_v2_grand_fbx_manifest.json")


main()
