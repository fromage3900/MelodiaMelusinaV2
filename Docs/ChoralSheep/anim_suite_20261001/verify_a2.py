"""Gate for A2 takes. Re-opens the SAVED file (not the authoring session) and measures per take:
  - loop_close_mm : worst vertex gap between first and last frame, body+tail meshes (ignored for one-shots)
  - alive_mm      : peak vertex displacement from rest over the take (must be > ALIVE_MIN)
  - peak_target_mm: peak displacement of the take's intended region (head / ear / tail / jaw)
  - root_drift_mm : movement of the root/hoof area (a stationary take must not slide the character)
  - bad           : NaN/Inf frames or bbox blow-up (> 25% of rest bbox diagonal)
  - fcurve key counts per channel
Pass criteria are in GATES. Writes A2_verify_20261001.json. Does not modify the blend.
"""
import json
import math
import os
from pathlib import Path

import bpy
import numpy as np

LANE = Path(r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\choral_sheep\anim_suite_20261001")
SRC = LANE / "choral_sheep_ANIMSUITE_A2_20261001.blend"
bpy.ops.wm.open_mainfile(filepath=str(SRC), load_ui=False)
rig = bpy.data.objects["rig"]
body = bpy.data.objects["MrSheepFinalTHISONELOOK"]
tail = bpy.data.objects["MrSheepTail"]
sc = bpy.context.scene

TAKES = {  # name: (frames, loop, region_verts_selector, alive_min_mm, target_min_mm, target_max_mm)
    "Graze": (96, True, "head", 20.0, 60.0, 450.0),
    "Bleat": (48, False, "jaw", 3.0, 10.0, 120.0),
    "EarFlick": (24, False, "ear", 3.0, 8.0, 160.0),
    "TailWag": (60, True, "tail", 10.0, 40.0, 500.0),
    "Harmonize": (120, False, "head", 10.0, 25.0, 300.0),
}
LOOP_TOL_MM = 0.5
ROOT_TOL_MM = 5.0


def ev(ob):
    rig.update_tag()
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    e = ob.evaluated_get(dg)
    me = e.to_mesh()
    n = len(me.vertices)
    a = np.empty(n * 3)
    me.vertices.foreach_get("co", a)
    e.to_mesh_clear()
    return a.reshape(n, 3)


def snap():
    return ev(body), ev(tail)


def reset_pose():
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.rotation_mode = "XYZ" if pb.rotation_mode not in ("XYZ",) else pb.rotation_mode
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)


reset_pose()
rest_b, rest_t = snap()
diag = float(np.linalg.norm(rest_b.max(0) - rest_b.min(0)))
head_z = np.percentile(rest_b[:, 2], 75)
head_y = rest_b[:, 1].min()


def moved_by(ctrls, axis=0, deg=30.0, thresh_mm=2.0):
    """Vertices that actually respond to these controls (instrument derived from the rig, not guessed)."""
    reset_pose()
    for c in ctrls:
        e = [0.0, 0.0, 0.0]
        e[axis] = math.radians(deg)
        rig.pose.bones[c].rotation_euler = e
    b, _ = snap()
    reset_pose()
    return np.linalg.norm(b - rest_b, axis=1) * 1000 > thresh_mm


regions = {
    "head": rest_b[:, 1] < (head_y + 0.35),           # front 35 cm of the body (head/muzzle)
    "jaw": moved_by(["c_jawbone.x"], 0, 20.0),
    "ear": moved_by(["c_ear_01.l", "c_ear_02.l", "c_ear_01.r", "c_ear_02.r"], 0, 30.0),
    "tail": None,
}
# planted = true ground-contact verts: skinned >=0.95 to foot/toe bones.
# (The 0.5 mask wrongly included upper-leg verts that legitimately move with
# spine pitch; measured ground-contact drift at >=0.95 is <=2.7mm.)
vg_names = {g.index: g.name for g in body.vertex_groups}
foot_w = np.zeros(len(rest_b))
for v in body.data.vertices:
    foot_w[v.index] = sum(g.weight for g in v.groups if vg_names[g.group].startswith(("foot", "toes")))
ground = foot_w >= 0.95
out_regions = {k: (int(v.sum()) if v is not None else None) for k, v in regions.items()}
out_regions["planted_foot_verts"] = int(ground.sum())
assert regions["ear"].sum() > 0 and regions["jaw"].sum() > 0 and ground.sum() > 0, out_regions
out = {"rest_bbox_diag_m": round(diag, 3), "region_vertex_counts": out_regions, "takes": {}}

for name, (frames, loop, region, alive_min, tmin, tmax) in TAKES.items():
    act = bpy.data.actions["CHORAL_A2_%s_Rig" % name]
    reset_pose()
    rig.animation_data.action = act
    peak_alive = peak_target = 0.0
    root_drift = 0.0
    bad = []
    first = last = None
    peak_frame = 0
    for f in range(0, frames + 1):
        sc.frame_set(f)
        b, t = snap()
        if not (np.isfinite(b).all() and np.isfinite(t).all()):
            bad.append((f, "nan"))
            continue
        if float(np.linalg.norm(b.max(0) - b.min(0))) > diag * 1.25:
            bad.append((f, "bbox"))
        db = np.linalg.norm(b - rest_b, axis=1)
        dt = np.linalg.norm(t - rest_t, axis=1)
        alive = max(float(db.max()), float(dt.max()))
        peak_alive = max(peak_alive, alive)
        tgt = float(dt.max()) if region == "tail" else float(db[regions[region]].max())
        if tgt > peak_target:
            peak_target, peak_frame = tgt, f
        root_drift = max(root_drift, float(db[ground].max()))
        if f == 0:
            first = (b.copy(), t.copy())
        if f == frames:
            last = (b.copy(), t.copy())
    loop_gap = max(float(np.linalg.norm(first[0] - last[0], axis=1).max()),
                   float(np.linalg.norm(first[1] - last[1], axis=1).max()))
    keys = {}
    for l in act.layers:
        for st in l.strips:
            for cb in st.channelbags:
                for fc in cb.fcurves:
                    keys["%s[%d]" % (fc.data_path.split('"')[1], fc.array_index)] = len(fc.keyframe_points)
    kr = [kp.co[0] for l in act.layers for st in l.strips for cb in st.channelbags for fc in cb.fcurves for kp in fc.keyframe_points]
    res = {
        "frames": frames, "loop": loop, "key_range": [min(kr), max(kr)],
        "loop_close_mm": round(loop_gap * 1000, 3),
        "alive_mm": round(peak_alive * 1000, 1),
        "peak_target_mm": round(peak_target * 1000, 1), "peak_frame": peak_frame,
        "root_drift_mm": round(root_drift * 1000, 2),
        "bad_frames": bad[:5], "channels": len(keys),
    }
    res["gate"] = {
        "span": "PASS" if (res["key_range"][0] == 0 and res["key_range"][1] == frames) else "FAIL",
        "closed": "PASS" if (loop_gap * 1000 <= LOOP_TOL_MM) else ("FAIL" if loop else "n/a(one-shot)"),
        "alive": "PASS" if peak_alive * 1000 >= alive_min else "FAIL",
        "target": "PASS" if tmin <= peak_target * 1000 <= tmax else "FAIL",
        "planted": "PASS" if root_drift * 1000 <= ROOT_TOL_MM else "FAIL",
        "finite": "PASS" if not bad else "FAIL",
    }
    res["all_pass"] = all(v in ("PASS", "n/a(one-shot)") for v in res["gate"].values())
    out["takes"][name] = res
    print("VERIFY", name, json.dumps(res["gate"]), "alive=%s target=%s drift=%s loopgap=%s" % (
        res["alive_mm"], res["peak_target_mm"], res["root_drift_mm"], res["loop_close_mm"]), flush=True)

out["all_takes_pass"] = all(t["all_pass"] for t in out["takes"].values())
(LANE / "A2_verify_20261001.json").write_text(json.dumps(out, indent=1))
print("A2_VERIFY_ALL_PASS", out["all_takes_pass"], flush=True)
os._exit(0)
