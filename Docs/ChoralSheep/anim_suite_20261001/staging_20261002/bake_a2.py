"""Bake the Choral Sheep takes from the Auto-Rig Pro control rig onto the canonical export skeleton.

Run headless (factory startup - user add-ons hang -b runs):
    blender -b --factory-startup --enable-autoexec <takes.blend> --python deploy/blender/choral_sheep_bake_takes.py -- <target_export.fbx> <out_dir>

The takes (SK_Sheep_*) animate the 474-bone control rig `rig`. UE's SK_ChoralSheep_Skeleton is the
117-bone ARP export skeleton (+ the `root` armature node). Bone names match once `.` becomes `_`.
Rest poses match except where ARP's exporter moves bones (root_x is flipped 180 deg, the
thigh_stretch bones are offset), so motion is transferred RELATIVE TO REST:

    target_world = rig_pose_world * rig_rest_world^-1 * target_rest_world

which leaves the export skeleton's rest pose untouched and carries only the animation. One FBX per
take, written to <out_dir>. Nothing is written into Content/.

The skinned mesh is exported alongside the armature on purpose: an armature-only FBX carries no
BindPose, so importers rebuild "rest" from whatever frame was current at export.
"""

import json
import os
import sys

import bpy

TAKES = ["CHORAL_A2_Graze_Rig","CHORAL_A2_Bleat_Rig","CHORAL_A2_EarFlick_Rig","CHORAL_A2_TailWag_Rig","CHORAL_A2_Harmonize_Rig"]


def norm(name):
    return name.replace(".", "_")


def mdiff(a, b):
    ang = a.to_quaternion().rotation_difference(b.to_quaternion()).angle * 57.2958
    return (a.translation - b.translation).length, min(ang, 360.0 - ang)


def main():
    target_fbx, out_dir = sys.argv[sys.argv.index("--") + 1:]
    os.makedirs(out_dir, exist_ok=True)
    scene = bpy.context.scene
    rig = bpy.data.objects["rig"]

    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=target_fbx)
    imported = [o for o in bpy.data.objects if o not in before]
    tgt = next(o for o in imported if o.type == "ARMATURE")
    skins = [o for o in imported if o.type == "MESH"]
    for o in imported:
        if o.type not in ("ARMATURE", "MESH"):
            bpy.data.objects.remove(o, do_unlink=True)

    rig_pb = {norm(pb.name): pb for pb in rig.pose.bones}
    # parents first, so a child's parent pose is already solved
    order = []
    stack = [b for b in tgt.data.bones if b.parent is None]
    while stack:
        b = stack.pop(0)
        order.append(b.name)
        stack.extend(b.children)
    missing = [n for n in order if norm(n) not in rig_pb]
    if missing:
        raise SystemExit("target bones missing on rig: %s" % missing[:10])

    tw = tgt.matrix_world
    tw_inv = tw.inverted()
    rw = rig.matrix_world
    # constant per bone: rig_rest_world^-1 * target_rest_world
    offset = {}
    for n in order:
        rb = rig_pb[norm(n)].bone
        offset[n] = (rw @ rb.matrix_local).inverted() @ (tw @ tgt.data.bones[n].matrix_local)

    for pb in tgt.pose.bones:
        pb.rotation_mode = "QUATERNION"

    report = {"target_fbx": os.path.basename(target_fbx), "bones": len(order), "skins": [s.name for s in skins], "takes": {}}
    if tgt.animation_data is None:
        tgt.animation_data_create()

    for take in TAKES:
        act = bpy.data.actions.get(take)
        if act is None:
            report["takes"][take] = "MISSING"
            continue
        rig.animation_data.action = act
        f0, f1 = int(round(act.frame_range[0])), int(round(act.frame_range[1]))
        out_name = "A_ChoralSheep_" + take.replace("CHORAL_A2_", "").replace("_Rig", "")
        new_act = bpy.data.actions.new(out_name)
        tgt.animation_data.action = new_act
        prev_q = {}

        for f in range(f0, f1 + 1):
            scene.frame_set(f)
            solved = {}
            for n in order:
                tb = tgt.data.bones[n]
                want = tw_inv @ (rw @ rig_pb[norm(n)].matrix) @ offset[n]  # armature space
                solved[n] = want
                if tb.parent:
                    basis = tb.matrix_local.inverted() @ tb.parent.matrix_local @ solved[tb.parent.name].inverted() @ want
                else:
                    basis = tb.matrix_local.inverted() @ want
                loc, rot, scl = basis.decompose()
                if n in prev_q and prev_q[n].dot(rot) < 0.0:
                    rot.negate()
                prev_q[n] = rot
                pb = tgt.pose.bones[n]
                pb.location = loc
                pb.rotation_quaternion = rot
                pb.scale = scl
                pb.keyframe_insert("location", frame=f, group=n)
                pb.keyframe_insert("rotation_quaternion", frame=f, group=n)
                pb.keyframe_insert("scale", frame=f, group=n)

        # Self-check before export: re-evaluate the keyed action and compare to the bake contract.
        # This isolates bake maths from FBX round-trip effects.
        check = {"pos": 0.0, "deg": 0.0, "bone": None, "frame": None}
        for f in sorted({f0, (f0 + f1) // 2, f1}):
            scene.frame_set(f)
            for n in order:
                expect = (rw @ rig_pb[norm(n)].matrix) @ offset[n]
                got = tw @ tgt.pose.bones[n].matrix
                p, a = mdiff(got, expect)
                if p * 1000 + a > check["pos"] * 1000 + check["deg"]:
                    check.update(pos=round(p, 6), deg=round(a, 4), bone=n, frame=f)

        scene.frame_start, scene.frame_end = f0, f1
        scene.frame_set(f0)
        bpy.ops.object.select_all(action="DESELECT")
        tgt.select_set(True)
        for s in skins:
            s.select_set(True)
        bpy.context.view_layer.objects.active = tgt
        path = os.path.join(out_dir, out_name + ".fbx")
        bpy.ops.export_scene.fbx(
            filepath=path, use_selection=True, object_types={"ARMATURE", "MESH"}, add_leaf_bones=False,
            primary_bone_axis="Y", secondary_bone_axis="X", armature_nodetype="NULL",
            bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False,
            bake_anim_use_all_actions=False, bake_anim_force_startend_keying=True,
            bake_anim_simplify_factor=0.0, apply_unit_scale=True, global_scale=1.0,
        )
        report["takes"][take] = {"out": out_name + ".fbx", "frames": [f0, f1], "bytes": os.path.getsize(path),
                                 "self_check": check}

    with open(os.path.join(out_dir, "bake_report.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print("BAKEJSON " + json.dumps(report))


main()
