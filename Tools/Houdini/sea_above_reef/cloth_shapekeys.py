"""Frozen cloth -> FBX morph targets (banners + shrouds), via the proven
jelly-bell path: same-topology pose JSON -> shape keys -> single-root armature
-> FBX. Reads Saved/Audit/sea_above/meshes/frozen_cloth_mesh.json.
Writes SM_Banner.fbx + SM_Shroud.fbx (UE morph targets) + manifest.
Run:  blender -b --factory-startup -noaudio --python cloth_shapekeys.py
"""

import json
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT_ROOT = Path(__file__).resolve().parents[3]
JSON_IN = PROJECT_ROOT / "Saved/Audit/sea_above/meshes/frozen_cloth_mesh.json"
OUT_DIR = PROJECT_ROOT / "Saved/Audit/sea_above/meshes"


def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def build(name, data, poses):
    mesh = bpy.data.meshes.new(name)
    verts = [tuple(c * 100.0 for c in p) for p in data["points"]]  # m -> cm
    mesh.from_pydata(verts, [], [tuple(f) for f in data["faces"]])
    mesh.update()
    uv = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vi = mesh.loops[li].vertex_index
            uv.data[li].uv = data["uvs"][vi]
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.shape_key_add(name="Basis")
    for pose_name, pose in poses.items():
        pts = pose["points"] if isinstance(pose, dict) else pose
        key = obj.shape_key_add(name=pose_name)
        for i, p in enumerate(pts):
            key.data[i].co = Vector((p[0] * 100.0, p[1] * 100.0, p[2] * 100.0))
    # single root armature -> UE imports a drivable skeletal mesh
    ad = bpy.data.armatures.new(name + "_Root")
    arm = bpy.data.objects.new(name + "_Root", ad)
    bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    bone = ad.edit_bones.new("root")
    bone.head = (0, 0, 0)
    bone.tail = (0, 0, 100.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.parent = arm
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    return obj, arm


def export(obj, arm, path):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    arm.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True,
                             add_leaf_bones=False, use_mesh_modifiers=False,
                             bake_anim=False, object_types={"MESH", "ARMATURE"})


def main():
    payload = json.loads(JSON_IN.read_text(encoding="utf-8"))
    clear()
    manifest = {"schema": "melodia.frozen_cloth_fbx.v1", "items": []}
    for name, base_key in (("SM_Banner", "banner"), ("SM_Shroud", "shroud")):
        obj, arm = build(name, payload[base_key], payload[f"{base_key}_poses"])
        path = OUT_DIR / f"{name}.fbx"
        export(obj, arm, path)
        morphs = ["Basis"] + list(payload[f"{base_key}_poses"].keys())
        manifest["items"].append({"asset": name, "file": str(path),
                                  "bytes": path.stat().st_size,
                                  "morph_targets": morphs})
        print(f"[cloth-bpy] wrote {path.name} morphs={morphs}")
    (OUT_DIR / "frozen_cloth_fbx_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print("[cloth-bpy] manifest -> frozen_cloth_fbx_manifest.json")


if __name__ == "__main__":
    main()
