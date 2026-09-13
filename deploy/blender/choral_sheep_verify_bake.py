"""Verify the baked Choral Sheep FBXs offline, before anyone imports them into UE.

    blender -b --factory-startup --enable-autoexec <takes.blend> --python deploy/blender/choral_sheep_verify_bake.py -- <target_export.fbx> <out_dir>

Checks, per take:
  1. rest fidelity  - re-imported armature rest pose equals the target export skeleton's rest pose
  2. motion fidelity - at sampled frames, each baked bone's world transform equals
                       rig_pose_world * rig_rest_world^-1 * target_rest_world (the bake contract)
  3. it moves        - the take is not a static pose (max bone displacement across frames > 0)
"""

import json
import os
import sys

import bpy

POS_TOL = 1e-3   # metres (world, after unit scale)
DEG_TOL = 0.5


def norm(name):
    return name.replace(".", "_")


def import_arm(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path, anim_offset=0.0)  # importer default shifts keys +1 frame
    new = [o for o in bpy.data.objects if o not in before]
    arm = next(o for o in new if o.type == "ARMATURE")
    for o in new:
        if o.type != "ARMATURE":
            bpy.data.objects.remove(o, do_unlink=True)
    return arm


def mdiff(a, b):
    ang = a.to_quaternion().rotation_difference(b.to_quaternion()).angle * 57.2958
    # q and -q are the same rotation; rotation_difference can report ~360 deg for identity
    return (a.translation - b.translation).length, min(ang, 360.0 - ang)


def main():
    target_fbx, out_dir = sys.argv[sys.argv.index("--") + 1:]
    report = json.load(open(os.path.join(out_dir, "bake_report.json"), encoding="utf-8"))
    scene = bpy.context.scene
    rig = bpy.data.objects["rig"]
    rig_pb = {norm(pb.name): pb for pb in rig.pose.bones}
    ref = import_arm(target_fbx)
    ref_rest = {b.name: ref.matrix_world @ b.matrix_local for b in ref.data.bones}

    results = {}
    for take, info in report["takes"].items():
        if not isinstance(info, dict):
            results[take] = "missing in bake"
            continue
        arm = import_arm(os.path.join(out_dir, info["out"]))
        r = {"bones": len(arm.data.bones)}
        worst_rest = max((mdiff(arm.matrix_world @ b.matrix_local, ref_rest[b.name]) for b in arm.data.bones if b.name in ref_rest),
                         key=lambda d: d[0] * 1000 + d[1])
        r["rest_max_pos"], r["rest_max_deg"] = round(worst_rest[0], 6), round(worst_rest[1], 4)
        r["rest_ok"] = worst_rest[0] < POS_TOL and worst_rest[1] < DEG_TOL

        rig.animation_data.action = bpy.data.actions[take]
        f0, f1 = info["frames"]
        frames = sorted({f0, (f0 + f1) // 2, f1, f0 + (f1 - f0) // 4})
        worst = (0.0, 0.0, None, None)
        travel = 0.0
        first = {}
        for f in frames:
            scene.frame_set(f)
            for pb in arm.pose.bones:
                n = pb.name
                rpb = rig_pb.get(norm(n))
                if rpb is None:
                    continue
                expect = (rig.matrix_world @ rpb.matrix) @ (rig.matrix_world @ rpb.bone.matrix_local).inverted() @ ref_rest[n]
                got = arm.matrix_world @ pb.matrix
                p, d = mdiff(got, expect)
                if p * 1000 + d > worst[0] * 1000 + worst[1]:
                    worst = (p, d, n, f)
                if n in first:
                    travel = max(travel, (got.translation - first[n]).length)
                else:
                    first[n] = got.translation.copy()
        r["motion_max_pos"], r["motion_max_deg"], r["worst_bone"], r["worst_frame"] = round(worst[0], 6), round(worst[1], 4), worst[2], worst[3]
        r["motion_ok"] = worst[0] < POS_TOL and worst[1] < DEG_TOL
        r["max_travel"] = round(travel, 4)
        r["moves"] = travel > 1e-3
        results[take] = r
        bpy.data.objects.remove(arm, do_unlink=True)

    ok = all(isinstance(v, dict) and v["rest_ok"] and v["motion_ok"] and v["moves"] for v in results.values())
    out = {"verdict": "PASS" if ok else "FAIL", "takes": results}
    with open(os.path.join(out_dir, "verify_report.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
    print("VERIFYJSON " + json.dumps(out))


main()
