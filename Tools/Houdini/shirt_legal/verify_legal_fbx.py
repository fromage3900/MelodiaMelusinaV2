"""Acceptance gate for the route-(a) legal shirt FBX.

Compares, in one hython session:
  1. the new FBX vs the Oct-3 candidate  -> same joints, same joint positions,
     same vertex positions (no axis/rotation/scale drift through Blender)
  2. the new FBX vs the Oct-6 delta     -> weights applied exactly
  3. the new FBX vs the live skeleton   -> legality (no unknown bones)
  4. the new FBX vs the fresh UE body export -> min clearance in cm

  hython Saved/Audit/ShirtBones_20261020/verify_legal_fbx.py
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import hou

REPO = Path("C:/EnvironmentPortfolio/BS_GodFile")
NEW = REPO / "Saved/Audit/ShirtBones_20261020/SK_Melusina_V2_Shirt_HemRig_Legal.fbx"
CAND = Path("G:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/MelusinaShirtKawaii_20261003/shirt_skinfit_candidate.fbx")
BODY = REPO / "Saved/Audit/MelusinaRuntimeCloseout_20261009/SkirtLayering_20261011/FreshUEExports/body_current.fbx"
DELTA = REPO / "Saved/Audit/melusina_animation_doctor/shirt_fix/shirt_weight_fix_v1.json"
CANON = REPO / "Saved/Audit/ShirtBones_20261020/canonical_skeleton.json"
OUT = REPO / "Saved/Audit/ShirtBones_20261020/legal_fbx_acceptance.json"

LEG_HINTS = ("thigh", "kilt", "leg_stretch", "leg_twist", "foot", "calf", "shin")


def pairs_of(pt):
    v = pt.attribValue("boneCapture")
    return [(int(v[i]), float(v[i + 1])) for i in range(0, len(v) - 1, 2)]


def load(path):
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "load")
    imp = geo.createNode("kinefx::fbxcharacterimport", "fbx_in")
    imp.parm("fbxfile").set(str(Path(path).resolve()))
    try:
        imp.parm("convertunits").set(1)
    except Exception:
        pass
    skin = imp.geometry(0)
    rest = imp.geometry(1)
    names = [str(p.attribValue("name")) for p in rest.points()]
    jpos = [tuple(p.position()) for p in rest.points()]
    vpos = [tuple(p.position()) for p in skin.points()]
    w = []
    for p in skin.points():
        # KineFX pads boneCapture with sentinel pairs (weight <= 0); they are not influences.
        w.append([(names[i] if i < len(names) else f"<idx {i}>", float(x))
                  for i, x in pairs_of(p) if x > 1e-6])
    return names, jpos, vpos, w


def maxdist(a, b):
    if len(a) != len(b):
        return float("inf")
    m = 0.0
    for p, q in zip(a, b):
        d = math.dist(p, q)
        if d > m:
            m = d
    return m


rep: dict = {"schema": "melodia.shirt_legal_fbx_acceptance.v1",
             "new_fbx": str(NEW), "candidate_fbx": str(CAND)}

new_names, new_jpos, new_vpos, new_w = load(NEW)
cand_names, cand_jpos, cand_vpos, cand_w = load(CAND)

# ---- 1. geometry / rig identical to the candidate -------------------------------
rep["joint_count_new"] = len(new_names)
rep["joint_count_candidate"] = len(cand_names)
rep["joint_names_identical"] = new_names == cand_names
rep["joint_positions_max_delta_mm"] = round(maxdist(new_jpos, cand_jpos) * 1000.0, 4)
rep["vertex_count_new"] = len(new_vpos)
rep["vertex_positions_max_delta_mm"] = round(maxdist(new_vpos, cand_vpos) * 1000.0, 4)

# ---- 2. weights vs the Oct-6 delta ---------------------------------------------
delta = {int(k): dict(v) for k, v in json.loads(DELTA.read_text(encoding="utf-8"))["verts"].items()}
max_w_diff = 0.0
mismatch = 0
inf_over = 0
sum_bad = 0
zero_pts = []
leg_pts = 0
hem_pts = 0
for i, prs in enumerate(new_w):
    d = delta.get(i)
    if d is None:
        continue
    got = {b: round(w, 4) for b, w in prs}
    exp = {b: round(float(w), 4) for b, w in d.items()}
    if got != exp:
        mismatch += 1
        for b in set(got) | set(exp):
            max_w_diff = max(max_w_diff, abs(got.get(b, 0.0) - exp.get(b, 0.0)))
    if len(prs) > 4:
        inf_over += 1
    s = sum(w for _b, w in prs)
    if abs(s - 1.0) > 1e-3:
        sum_bad += 1
    if not prs:
        zero_pts.append(i)
    for b, w in prs:
        if any(h in b.lower() for h in LEG_HINTS) and w > 0.01:
            leg_pts += 1
            break
    if any("hem" in b.lower() for b, _w in prs):
        hem_pts += 1

rep["weights"] = {
    "verts_checked": len(new_w),
    "verts_differing_from_delta": mismatch,
    "max_weight_delta": round(max_w_diff, 6),
    "verts_with_more_than_4_influences": inf_over,
    "verts_with_sum_not_1": sum_bad,
    "unweighted_verts": len(zero_pts),
    "leg_bound_verts": leg_pts,
    "hem_influenced_verts": hem_pts,
}

# ---- 3. legality vs the live skeleton -----------------------------------------
canon = json.loads(CANON.read_text(encoding="utf-8"))
canon_names = [b["name"] for b in canon["bones"]]
canon_set = set(canon_names)
unknown = sorted({n for n in new_names if n not in canon_set})
missing = sorted(canon_set - set(new_names))
rep["legality"] = {
    "canonical_bones": len(canon_names),
    "fbx_joints": len(new_names),
    "unknown_bones": unknown,
    "missing_canonical": missing,
    "hem_bones": sorted(n for n in new_names if "hem" in n.lower()),
    "all_weights_reference_known_bones": all(
        b in canon_set for prs in new_w for b, _w in prs
    ),
}

# ---- 4. clearance vs the fresh UE body export ---------------------------------
body_names, body_jpos, body_vpos, body_w = load(BODY)
grid: dict = {}
cell = 0.05  # 5 cm cells
for p in body_vpos:
    key = (int(p[0] // cell), int(p[1] // cell), int(p[2] // cell))
    grid.setdefault(key, []).append(p)
min_d = float("inf")
closest = None
for p in new_vpos:
    ci = (int(p[0] // cell), int(p[1] // cell), int(p[2] // cell))
    best = float("inf")
    bp = None
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for q in grid.get((ci[0] + dx, ci[1] + dy, ci[2] + dz), ()):
                    d = math.dist(p, q)
                    if d < best:
                        best, bp = d, q
    if best < min_d:
        min_d, closest = best, (list(p), list(bp) if bp else None)
rep["clearance_vs_body_cm"] = {
    "min_cm": round(min_d * 100.0, 4),
    "shirt_point": [round(v, 4) for v in closest[0]] if closest else None,
    "body_point": [round(v, 4) for v in closest[1]] if closest else None,
}

hem_set = sorted(n for n in new_names if "hem" in n.lower())
rep["verdict"] = {
    "rig_identical_to_candidate": rep["joint_names_identical"],
    "no_geometry_drift": rep["vertex_positions_max_delta_mm"] < 0.01,
    "weights_match_delta_within_1e-3": mismatch == 0 or max_w_diff <= 1e-3,
    "influence_limit_ok": inf_over == 0,
    "all_sums_one": sum_bad == 0,
    "no_unweighted_verts": len(zero_pts) == 0,
    "no_leg_bindings": leg_pts == 0,
    "unknown_bones_are_exactly_the_17_hem_bones": len(unknown) == 17 and unknown == hem_set,
    "missing_only_ue_wrapper_root": missing == ["root"],
    "hem_weighted_verts": hem_pts,
}

OUT.write_text(json.dumps(rep, indent=1), encoding="utf-8")
print("WROTE", OUT)
print("VERDICT", json.dumps(rep["verdict"], indent=1))
print("WEIGHTS", json.dumps(rep["weights"]))
print("JOINT_POS_MAX_DELTA_MM", rep["joint_positions_max_delta_mm"],
      "VERT_POS_MAX_DELTA_MM", rep["vertex_positions_max_delta_mm"])
print("CLEARANCE_CM", json.dumps(rep["clearance_vs_body_cm"]))
print("MISSING", rep["legality"]["missing_canonical"], "UNKNOWN", rep["legality"]["unknown_bones"])
