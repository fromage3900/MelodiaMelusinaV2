"""Melusina runtime-clip gate. Run inside the editor (Claireon python_execute / Monolith run_python).

Contract (Jev 2026-10-02, Saved/Audit/ArcheryGoalSession_20261001/JevConverge_20261002.json):
  * Clips drive DEFORM bones only. No control-bone (c_*) or twist-bone rewrites, no per-clip fixes.
  * One skeleton: SK_Melusina_Skeleton (wardrobe leader-pose slots refuse any other).
  * Root height, face/eye rest and hand roll are measured against the proven baseline, not guessed.

Baseline measured 2026-10-02 over 61 production clips: root_x world z = 88 +/- 12; eye bones at rest;
hand roll (wrapped, vs ref) 10-52 deg locomotion, <=80 deg bow draw, 105 Death (outlier);
forearm twist bones static in every proven clip.

Usage:  import melusina_anim_gate as g; g.run(["/Game/.../A_Clip", ...])  -> list of dict rows with 'fail' reasons.
"""
import math

import unreal

BODY = "/Game/Melodia/Characters/Melusina/Outfits/V2/SK_Melusina_V2_Body"
SKELETON_TAG = "SK_Melusina_Skeleton"
ROOT_Z, ROOT_TOL = 88.0, 12.0
EYE_MAX_DEG = 1.0
HAND_ROLL_MAX_DEG = 110.0  # proven Death clip = 105; Sparrow draw/fire = 92-103 (source motion)
TWIST_MUST_BE_STATIC = True


def _wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def _roll(q):
    return _wrap(math.degrees(2.0 * math.atan2(q.y, q.w)))


def _qconj(q):
    return unreal.Quat(-q.x, -q.y, -q.z, q.w)


def _qmul(a, b):
    return unreal.Quat(
        a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
        a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
        a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w,
        a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z)


def _ang(q1, q2):
    d = abs(q1.x * q2.x + q1.y * q2.y + q1.z * q2.z + q1.w * q2.w)
    return math.degrees(2.0 * math.acos(min(1.0, d)))


def measure(path, samples=(0.0, 0.33, 0.66, 1.0)):
    mesh = unreal.load_asset(BODY)
    seq = unreal.load_asset(path)
    W, L = unreal.AnimPoseSpaces.WORLD, unreal.AnimPoseSpaces.LOCAL
    ln = seq.get_play_length()
    opt = unreal.AnimPoseEvaluationOptions()
    opt.set_editor_property("optional_skeletal_mesh", mesh)
    row = {"clip": path.split("/")[-1], "root_z_dev": 0.0, "eye_deg": 0.0, "hand_roll": 0.0, "twist_moved": 0.0}
    for s in samples:
        pose = unreal.AnimPoseExtensions.get_anim_pose_at_time(seq, min(ln * s, ln - 0.001), opt)
        P = unreal.AnimPoseExtensions
        dz = P.get_bone_pose(pose, "root_x", W).translation.z - ROOT_Z
        row["root_z_dev"] = max(row["root_z_dev"], abs(dz))
        for b in ("eye_l", "eye_r", "def_eye_l", "def_eye_r"):
            row["eye_deg"] = max(row["eye_deg"], _ang(P.get_bone_pose(pose, b, L).rotation, P.get_ref_bone_pose(pose, b, L).rotation))
        for side in ("l", "r"):
            def rel(b):
                return _roll(_qmul(_qconj(P.get_ref_bone_pose(pose, b, L).rotation), P.get_bone_pose(pose, b, L).rotation))
            row["hand_roll"] = max(row["hand_roll"], abs(rel("hand_" + side)))
            row["twist_moved"] = max(row["twist_moved"], abs(rel("forearm_twist_" + side)) + abs(rel("forearm_twist_2_" + side)))
    return row


def run(paths):
    out = []
    for p in paths:
        r = measure(p)
        fail = []
        if r["root_z_dev"] > ROOT_TOL:
            fail.append("root_z %.0f off" % r["root_z_dev"])
        if r["eye_deg"] > EYE_MAX_DEG:
            fail.append("eyes keyed %.1f deg" % r["eye_deg"])
        if r["hand_roll"] > HAND_ROLL_MAX_DEG:
            fail.append("hand roll %.0f deg" % r["hand_roll"])
        if TWIST_MUST_BE_STATIC and r["twist_moved"] > 1.0:
            fail.append("twist bones keyed (%.0f deg) - contract is deform-only" % r["twist_moved"])
        r["fail"] = fail
        out.append(r)
    return out
