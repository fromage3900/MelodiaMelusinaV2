"""Motion Blender FBX builder — frozen cloth drapes + 64f silk strip vertex anim

Reads surreal_sweep_wave2/motion/*.json produced by surreal_motion2.py
Writes FBXs to same motion/ dir:
  SM_SilkVeil_4m.fbx    (frozen drape, single mesh, clay material, root armature)
  SM_TatteredSail_6m.fbx
  SM_SilkStrip_64f.fbx  (64-frame vertex animation via shape keys + baked action)

Run:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background --python Tools/Houdini/sea_above_reef/motion_blender_fbx.py
"""
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MOTION_DIR = PROJECT_ROOT / "surreal_sweep_wave2" / "motion"

CLAY = (0.62, 0.60, 0.58)
VEIL_TINT = (0.86, 0.88, 0.90)
SAIL_TINT = (0.78, 0.74, 0.68)
STRIP_TINT = (0.88, 0.82, 0.86)

def clear():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for coll in [bpy.data.meshes, bpy.data.materials, bpy.data.armatures, bpy.data.actions]:
        for it in list(coll):
            if getattr(it, "users", 0) == 0:
                try:
                    coll.remove(it)
                except: pass

def build_static(name, points, faces, uvs, tint):
    mesh = bpy.data.meshes.new(name)
    verts = [tuple(c*100.0 for c in p) for p in points]
    mesh.from_pydata(verts, [], [tuple(f) for f in faces])
    mesh.update()
    # uvs per loop
    uv_layer = mesh.uv_layers.new(name="UVMap")
    # map vertex idx -> uv (points are per-vertex)
    # loops reference verts; set per-loop uv = uvs[vertex_index]
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vi = mesh.loops[li].vertex_index
            uv_layer.data[li].uv = uvs[vi]
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    # material
    mat = bpy.data.materials.new(name + "_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*tint, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.65
        # silk sheen
        try:
            bsdf.inputs["Sheen Weight"].default_value = 0.35
            bsdf.inputs["Sheen Tint"].default_value = 0.5
        except: pass
        # make tattered sail slightly translucent
        if "Sail" in name:
            bsdf.inputs["Base Color"].default_value = (*tint, 1.0)
            try:
                mat.blend_method = "OPAQUE"
            except: pass
        if "Veil" in name:
            # veil slight translucency via Transmission
            try:
                bsdf.inputs["Transmission Weight"].default_value = 0.12
            except: pass
    obj.data.materials.append(mat)
    try:
        mesh.calc_normals_split()
    except: pass
    # smooth shade
    for poly in mesh.polygons:
        poly.use_smooth = True
    # root armature for UE import consistency
    arm_data = bpy.data.armatures.new(name + "_Root")
    arm = bpy.data.objects.new(name + "_Root", arm_data)
    bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    bone = arm_data.edit_bones.new("root")
    bone.head = (0,0,0)
    bone.tail = (0,0,80)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.parent = arm
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    return obj, arm

def export_fbx(objs, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[-1]
    bpy.ops.export_scene.fbx(filepath=str(path), use_selection=True, add_leaf_bones=False,
                             use_mesh_modifiers=False, bake_anim=False,
                             object_types={"MESH","ARMATURE"}, axis_forward="-Z", axis_up="Y")

def build_vertex_anim():
    anim_json = MOTION_DIR / "silk_strip_anim.json"
    if not anim_json.exists():
        print(f"[fbx] missing {anim_json}")
        return None
    payload = json.loads(anim_json.read_text(encoding="utf-8"))
    strip = payload["strip"]
    name = strip["name"]
    points0 = strip["frames"][0] if False else None  # not used, frames already contain verts
    # use first frame as basis
    frames = strip["frames"]
    uvs = strip["uvs"]
    faces = strip["faces"]
    base_pts = frames[0]
    mesh = bpy.data.meshes.new(name)
    verts = [tuple(c*100.0 for c in p) for p in base_pts]
    mesh.from_pydata(verts, [], [tuple(f) for f in faces])
    mesh.update()
    uv_layer = mesh.uv_layers.new(name="UVMap")
    for poly in mesh.polygons:
        for li in poly.loop_indices:
            vi = mesh.loops[li].vertex_index
            uv_layer.data[li].uv = uvs[vi]
    for poly in mesh.polygons:
        poly.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    # material
    mat = bpy.data.materials.new(name+"_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*STRIP_TINT, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.55
        try:
            bsdf.inputs["Sheen Weight"].default_value = 0.45
        except: pass
        # slight emission for beauty
        try:
            bsdf.inputs["Emission Color"].default_value = (0.25,0.22,0.28,1.0)
            bsdf.inputs["Emission Strength"].default_value = 0.08
        except: pass
    obj.data.materials.append(mat)
    # shape keys for each frame (64)
    obj.shape_key_add(name="Basis")
    sks = []
    for f_idx, pts in enumerate(frames):
        key = obj.shape_key_add(name=f"f{f_idx:02d}")
        for i, p in enumerate(pts):
            key.data[i].co = Vector((p[0]*100.0, p[1]*100.0, p[2]*100.0))
        sks.append(key)
    # armature
    arm_data = bpy.data.armatures.new(name+"_Root")
    arm = bpy.data.objects.new(name+"_Root", arm_data)
    bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    bone = arm_data.edit_bones.new("root")
    bone.head = (0,0,0)
    bone.tail = (0,0,100)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.parent = arm
    mod = obj.modifiers.new("Armature","ARMATURE")
    mod.object = arm

    # animate shape keys: each frame one key =1 others 0, looping
    # Need to keyframe Basis? Keep Basis at 0 and animate f00..f63
    scene = bpy.context.scene
    scene.frame_start = 0
    scene.frame_end = 63
    scene.render.fps = 24
    # ensure animation data
    for f_idx, key in enumerate(sks):
        # keyframe 0 at frames where not active, 1 at active
        # optimize: key only at f_idx and neighbors
        # We'll brute force: for each frame, set all keys appropriately and keyframe
        pass
    # Insert keyframes per scene frame
    for frame in range(64):
        scene.frame_set(frame)
        for f_idx, key in enumerate(sks):
            v = 1.0 if f_idx == frame else 0.0
            key.value = v
            key.keyframe_insert(data_path="value", frame=frame)
        # Basis stays 0
        obj.data.shape_keys.key_blocks[0].value = 0.0
        obj.data.shape_keys.key_blocks[0].keyframe_insert(data_path="value", frame=frame)
    # set interpolation to linear for smooth loop (Blender default Bezier will overshoot)
    # Blender 5.x new Action API compatibility
    try:
        ad = obj.data.shape_keys.animation_data
        if ad and ad.action:
            act = ad.action
            # try legacy fcurves
            fcurves = getattr(act, "fcurves", None)
            if fcurves is None:
                # 4.4+ layered action: collect from strips/channelbags
                fcurves = []
                try:
                    for layer in act.layers:
                        for strip in layer.strips:
                            cb = getattr(strip, "channelbag", None) or getattr(strip, "channelbags", [None])[0]
                            if cb and hasattr(cb, "fcurves"):
                                fcurves.extend(cb.fcurves)
                except Exception:
                    fcurves = []
            for fc in fcurves:
                try:
                    for kp in fc.keyframe_points:
                        kp.interpolation = "LINEAR"
                except: pass
    except Exception as e:
        print(f"[fbx] interpolation set skipped: {e}")
    # linear handle also for close loop continuity frame 63->0 we keep linear; fcurve is cyclic linear
    print(f"[fbx] silk strip shape keys {len(sks)} + armature, animated 0..63 linear")
    return obj, arm

def main():
    MOTION_DIR.mkdir(parents=True, exist_ok=True)
    clear()
    cloth_json = MOTION_DIR / "frozen_cloth_meshes.json"
    if not cloth_json.exists():
        print(f"[fbx] missing cloth json {cloth_json} — run surreal_motion2.py first")
        return
    payload = json.loads(cloth_json.read_text(encoding="utf-8"))
    results = []

    for key, tint in [("veil", VEIL_TINT), ("sail", SAIL_TINT)]:
        c = payload["cloths"][key]
        clear()
        obj, arm = build_static(c["name"], c["points"], c["faces"], c["uvs"], tint)
        bpy.context.view_layer.update()
        out = MOTION_DIR / f"{c['name']}.fbx"
        export_fbx([obj, arm], out)
        print(f"[fbx] wrote {out.name} {out.stat().st_size} bytes  {len(c['points'])}v {len(c['faces'])}f")
        results.append((c["name"], out))

    # vertex anim strip
    clear()
    res = build_vertex_anim()
    if res:
        obj, arm = res
        bpy.context.view_layer.update()
        out = MOTION_DIR / "SM_SilkStrip_64f.fbx"
        # export with bake anim
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        arm.select_set(True)
        bpy.context.view_layer.objects.active = arm
        bpy.ops.export_scene.fbx(filepath=str(out), use_selection=True, add_leaf_bones=False,
                                 use_mesh_modifiers=False, bake_anim=True, bake_anim_use_all_actions=False,
                                 bake_anim_use_nla_strips=False, bake_anim_simplify_factor=0.0,
                                 object_types={"MESH","ARMATURE"}, axis_forward="-Z", axis_up="Y")
        print(f"[fbx] wrote {out.name} {out.stat().st_size} bytes  64f vertex anim")
        results.append(("SM_SilkStrip_64f", out))

    print(f"[fbx] done {len(results)} FBXs")

if __name__ == "__main__":
    main()
