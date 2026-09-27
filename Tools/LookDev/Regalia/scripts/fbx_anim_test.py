"""FBX ANIMATION ROUND-TRIP TEST.

Settles the load-bearing assumption of the regalia animation plan (§5): that
armature bone keys survive FBX into UE, while GN SceneTime animation does not.

The plan currently ASSERTS this from knowledge. This measures it. The test:

  1. build a mesh parented to a bone, key the bone's rotation
  2. export to FBX
  3. re-import into a CLEAN scene in a fresh Blender process
  4. read the animation back and report the actual euler at two frames

If the euler differs between the keyed frames, bone motion survives. Also exports
a GN SceneTime-driven variant, which is the control: it should arrive static,
because FBX has no representation for a modifier.

Run (two stages, separate processes -- that is the point):
  blender -b --factory-startup --python fbx_anim_test.py -- export
  blender -b --factory-startup --python fbx_anim_test.py -- verify
"""

import math
import os
import sys

import bpy
from mathutils import Vector, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
FBX = os.path.join(HERE, "fbx_anim_test.fbx")
REPORT = os.path.join(HERE, "fbx_anim_test.json")

STAGE = "export"
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if argv:
    STAGE = argv[0]


def _reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def _new_armature(name="rig"):
    arm = bpy.data.armatures.new(name)
    ob = bpy.data.objects.new(name, arm)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    eb = arm.edit_bones.new("spin")
    eb.head = (0, 0, 0)
    eb.tail = (0, 0, 0.2)
    bpy.ops.object.mode_set(mode="OBJECT")
    return ob


def _marker(name, mat, parent_bone=None):
    """A real tetra, NOT an empty mesh.

    The first version of this test created empty meshes. FBX then had no geometry
    to carry and the GN control had nothing a modifier could be applied to, so the
    round-trip was meaningless. An asymmetric 4-vert tetra means any rotation of
    its bounding-box centre is unambiguous.
    """
    me = bpy.data.meshes.new(name)
    verts = [(0.0, 0.0, 0.0), (0.10, 0.0, 0.0), (0.0, 0.08, 0.0), (0.0, 0.0, 0.11)]
    me.from_pydata(verts, [], [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)])
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    if parent_bone:
        ob.parent = bpy.data.objects["rig"]
        ob.parent_type = "BONE"
        ob.parent_bone = parent_bone
    return ob


def do_export():
    _reset()
    scn = bpy.context.scene
    scn.frame_start = 1
    scn.frame_end = 60

    mat = bpy.data.materials.new("M")
    mat.use_nodes = True
    rig = _new_armature()

    # --- A: bone-driven. A marker parented to the spin bone, bone keyframed.
    bone_marker = _marker("BONE_MARKER", mat, parent_bone="spin")
    pb = rig.pose.bones["spin"]
    for frame, deg in ((1, 0.0), (60, 180.0)):
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = Euler((0.0, 0.0, math.radians(deg)), "XYZ")
        pb.keyframe_insert(data_path="rotation_euler", frame=frame)

    # --- B: GN SceneTime. The control case.
    gn_marker = _marker("GN_MARKER", mat)
    ng = bpy.data.node_groups.new("GN_TIME", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    go = ng.nodes.new("NodeGroupOutput")
    st = ng.nodes.new("GeometryNodeInputSceneTime")
    # seconds -> radians, so the marker visibly turns over the frame range
    m = ng.nodes.new("ShaderNodeMath")
    m.operation = "MULTIPLY"
    m.inputs[1].default_value = math.radians(180.0) / 60.0
    ng.links.new(st.outputs["Seconds"], m.inputs[0])
    xf = ng.nodes.new("FunctionNodeAlignRotationToVector")
    ng.links.new(m.outputs[0], xf.inputs["Factor"])
    ng.links.new(xf.outputs[0], go.inputs[0])
    md = gn_marker.modifiers.new("spin", "NODES")
    md.node_group = ng

    # park them apart so a render could tell them apart too
    bone_marker.location = (-0.3, 0, 0)
    gn_marker.location = (0.3, 0, 0)

    scn.frame_set(1)
    bpy.context.view_layer.update()
    bpy.ops.export_scene.fbx(
        filepath=FBX, use_selection=False, bake_anim=True,
        bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False, add_leaf_bones=False,
        object_types={"ARMATURE", "MESH", "EMPTY"},
    )
    print("EXPORT wrote %s (%d bytes)" % (FBX, os.path.getsize(FBX)))


def _sample(ob, frame, scn):
    """Where the marker's GEOMETRY actually is at `frame`.

    The first version of this test read ob.matrix_world.to_euler() and reported
    0.0 for BOTH markers -- including the GN control, which should have baked
    something. That was the harness being wrong, not the claim: a bone-parented
    mesh is deformed by the armature, so the OBJECT's own transform never
    changes. Vertex positions are the only honest measurement.
    """
    scn.frame_set(frame)
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    oe = ob.evaluated_get(dg)
    me = oe.to_mesh()
    try:
        if me is None or len(me.vertices) == 0:
            return None, None, 0
        mw = oe.matrix_world
        pts = [mw @ v.co for v in me.vertices]
        xs = [p.x for p in pts]
        ys = [p.y for p in pts]
        cx = (min(xs) + max(xs)) * 0.5
        cy = (min(ys) + max(ys)) * 0.5
        return cx, cy, len(me.vertices)
    finally:
        oe.to_mesh_clear()


def do_verify():
    _reset()
    scn = bpy.context.scene
    bpy.ops.import_scene.fbx(filepath=FBX)
    scn.frame_start = 1
    scn.frame_end = 60

    out = {"fbx_bytes": os.path.getsize(FBX), "objects": {}}
    for name in ("BONE_MARKER", "GN_MARKER"):
        ob = bpy.data.objects.get(name)
        if ob is None:
            # FBX may suffix on name collision; find by stem
            cands = [o for o in bpy.data.objects if o.name.startswith(name)]
            ob = cands[0] if cands else None
        if ob is None:
            out["objects"][name] = {"found": False}
            continue
        x1, y1, n1 = _sample(ob, 1, scn)
        x30, y30, _ = _sample(ob, 30, scn)
        x60, y60, _ = _sample(ob, 60, scn)
        if x1 is None:
            out["objects"][name] = {"found": True, "sampled": False,
                                    "note": "no geometry to measure"}
            print("%-12s NO GEOMETRY" % name)
            continue
        travel = abs(x60 - x1) + abs(y60 - y1)
        rec = {
            "found": True,
            "sampled": True,
            "verts": n1,
            "has_modifier": any(m.type == "NODES" for m in ob.modifiers),
            "modifiers": [m.type for m in ob.modifiers],
            "centre_f1": [round(x1, 5), round(y1, 5)],
            "centre_f30": [round(x30, 5), round(y30, 5)],
            "centre_f60": [round(x60, 5), round(y60, 5)],
            "travel_f1_to_f60_m": round(travel, 5),
            "moved": travel > 0.002,      # 2 mm
        }
        out["objects"][name] = rec
        print("%-12s mods=%-22s v=%d  travel=%.4f m  moved=%s" % (
            name, str(rec["modifiers"]), n1, travel, rec["moved"]))

    bone = out["objects"].get("BONE_MARKER", {})
    gn = out["objects"].get("GN_MARKER", {})
    out["VERDICT"] = {
        "bone_anim_survives_fbx": bool(bone.get("moved")),
        "bone_marker_kept_modifier": bool(gn.get("has_modifier")) if gn else None,
        "gn_time_is_static": (not gn.get("moved")) if gn.get("found") else None,
    }
    print("VERDICT %s" % out["VERDICT"])
    with open(REPORT, "w", encoding="utf-8") as fh:
        import json
        json.dump(out, fh, indent=2)
    print("WROTE", REPORT)


if __name__ == "__main__":
    if STAGE == "export":
        do_export()
    else:
        do_verify()
