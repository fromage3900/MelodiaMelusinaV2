"""Locomotion measurements for the 6 v4 clips in choral_sheep_Takes_v4_20260910.blend.

Measures per clip:
  - net displacement + avg/max ground speed (body-mesh centroid, 24 fps)
  - stride length + step count (dominant foot-group centroids, forward-axis peaks)
  - apex height (Jump) / fall (Death) / drift (Idle)
Writes locomotion_measurements_20261001.json. Read-only: never saves the blend.
"""
import json
import os
from pathlib import Path

import bpy
import numpy as np

LANE = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\choral_sheep\anim_suite_20261001")
SRC = LANE.parent / "choralsheep_Takes_v4_20260910.blend"
FPS = 24.0
# UE import durations (s) for the fps cross-check
UE_DUR = {"Idle": 6.25, "Walk": 2.667, "WalkSlow": 2.0, "Run": 0.833, "Jump": 1.125, "Death": 1.083}
CLIP_SPAN = {"Idle": 150, "Walk": 64, "WalkSlow": 48, "Run": 20, "Jump": 27, "Death": 26}

bpy.ops.wm.open_mainfile(filepath=str(SRC), load_ui=False)
sc = bpy.context.scene

# --- armature: the one whose bones best match the actions' fcurve paths ---
def action_bones(act):
    names = set()
    for l in act.layers:
        for st in l.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    dp = fc.data_path
                    if 'pose.bones["' in dp:
                        names.add(dp.split('pose.bones["')[1].split('"')[0])
    return names

arms = [ob for ob in sc.objects if ob.type == "ARMATURE"]
assert arms, "no armature in scene"
# production rig = largest armature (the 24-bone DonorSheep rig only drives the donor clips)
rig = max(arms, key=lambda o: len(o.data.bones))
rig_bones = {b.name for b in rig.data.bones}
sk_bones = set()
for act in bpy.data.actions:
    if act.name.startswith("SK_Sheep_"):
        sk_bones |= action_bones(act)
print("RIG", rig.name, "bones=%d sk_match=%.2f" % (
    len(rig.data.bones), (len(sk_bones & rig_bones) / len(sk_bones)) if sk_bones else -1), flush=True)

# --- body mesh: skinned mesh with the most vertices ---
meshes = [ob for ob in sc.objects if ob.type == "MESH" and len(ob.vertex_groups) > 10]
assert meshes, "no skinned body mesh found"
body = max(meshes, key=lambda o: len(o.data.vertices))
print("BODY", body.name, "verts=%d vgroups=%d" % (len(body.data.vertices), len(body.vertex_groups)), flush=True)

vg_names = {g.index: g.name for g in body.vertex_groups}  # object-level in 5.2
dom = ["" for _ in body.data.vertices]
for v in body.data.vertices:
    if v.groups:
        best = max(v.groups, key=lambda g: g.weight)
        dom[v.index] = vg_names[best.group]
foot_l = np.array([g.startswith(("foot", "toes")) and "l" in g.lower() for g in dom])
foot_r = np.array([g.startswith(("foot", "toes")) and "r" in g.lower() for g in dom])
print("FOOT_VERTS l=%d r=%d" % (int(foot_l.sum()), int(foot_r.sum())), flush=True)


def centroid(mask=None):
    rig.update_tag()
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    e = body.evaluated_get(dg)
    me = e.to_mesh()
    m = len(me.vertices)
    a = np.empty(m * 3)
    me.vertices.foreach_get("co", a)
    e.to_mesh_clear()
    a = a.reshape(m, 3)
    if mask is None:
        return a.mean(axis=0)
    sel = mask[:m]
    return a[sel].mean(axis=0) if sel.sum() else np.full(3, np.nan)


def key_range(act):
    kr = [kp.co[0] for l in act.layers for st in l.strips for cb in st.channelbags
          for fc in cb.fcurves for kp in fc.keyframe_points]
    return (int(round(min(kr))), int(round(max(kr)))) if kr else None


# --- match the 6 clips: by name first, then by span ---
acts = {}
for act in bpy.data.actions:
    kr = key_range(act)
    if kr:
        acts[act.name] = kr
matched = {}
for clip, span in CLIP_SPAN.items():
    # prefer the retargeted SK_Sheep_* set (drives the real rig); donor set is the 24-bone source
    cands = [n for n, (a, b) in acts.items() if n == "SK_Sheep_%s" % clip and (b - a) == span]
    if not cands:
        cands = [n for n, (a, b) in acts.items() if clip.lower() in n.lower() and (b - a) == span]
    if not cands:
        cands = [n for n, (a, b) in acts.items() if (b - a) == span]
    if cands:
        matched[clip] = cands[0]
    else:
        print("WARN no action for clip", clip, "span", span, flush=True)
print("MATCHED", json.dumps(matched), flush=True)

out = {"source": SRC.name, "fps_assumed": FPS, "fps_check": {}, "clips": {}}
for clip, aname in matched.items():
    act = bpy.data.actions[aname]
    a, b = key_range(act)
    rig.animation_data.action = act
    traj, fl, fr = [], [], []
    for f in range(a, b + 1):
        sc.frame_set(f)
        traj.append(centroid())
        fl.append(centroid(foot_l))
        fr.append(centroid(foot_r))
    traj = np.array(traj)
    fl = np.array(fl)
    fr = np.array(fr)
    n_frames = b - a
    dur = n_frames / FPS
    net = traj[-1] - traj[0]
    disp = float(np.linalg.norm(net))
    avg_speed = disp / dur
    step = np.linalg.norm(np.diff(traj, axis=0), axis=1) * FPS  # m/s per frame
    max_speed = float(step.max()) if len(step) else 0.0
    # forward axis: the sheep's head sits at min-Y (measured in verify_a2), so forward = -Y.
    # All locomotion clips are in-place (root drift <= 10 cm), so the root's net
    # displacement is NOT a usable forward axis; stride is measured relative to the body.
    fwd = np.array([0.0, -1.0])
    # stride: peaks of the left foot's forward offset RELATIVE to the body centroid
    fl_fwd = (fl[:, :2] - traj[:, :2]) @ fwd
    peaks = [i for i in range(1, len(fl_fwd) - 1)
             if fl_fwd[i] > fl_fwd[i - 1] and fl_fwd[i] >= fl_fwd[i + 1]]
    stride = None
    cycle_freq = None
    intended_speed = None
    if len(peaks) >= 2:
        stride = float(np.mean(np.diff(fl_fwd[peaks])))
        cycle_freq = (len(peaks) - 1) / dur  # full left-foot cycles per second
        intended_speed = stride * cycle_freq  # ground speed the clip implies
    res = {
        "action": aname,
        "frame_range": [a, b],
        "duration_s": round(dur, 3),
        "ue_duration_s": UE_DUR[clip],
        "fps_check_ok": abs(dur - UE_DUR[clip]) < 0.02,
        "net_displacement_cm": round(disp * 100, 2),
        "avg_ground_speed_cm_s": round(avg_speed * 100, 2),
        "max_speed_cm_s": round(max_speed * 100, 2),
        "forward_axis": [round(float(fwd[0]), 3), round(float(fwd[1]), 3)],
        "in_place": disp < 0.15,
        "stride_cm": round(stride * 100, 2) if stride is not None else None,
        "cycle_freq_hz": round(cycle_freq, 3) if cycle_freq is not None else None,
        "intended_speed_cm_s": round(intended_speed * 100, 2) if intended_speed is not None else None,
        "foot_peaks": len(peaks),
        "apex_above_start_cm": round(float((traj[:, 2].max() - traj[0, 2]) * 100), 2),
        "end_below_start_cm": round(float((traj[0, 2] - traj[-1, 2]) * 100), 2),
    }
    out["clips"][clip] = res
    print("LOCO", clip, json.dumps(res), flush=True)

out["foot_verts"] = {"left": int(foot_l.sum()), "right": int(foot_r.sum())}
(LANE / "locomotion_measurements_20261001.json").write_text(json.dumps(out, indent=1))
print("LOCO_DONE", flush=True)
os._exit(0)
