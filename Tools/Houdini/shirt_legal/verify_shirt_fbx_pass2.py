"""Route (b) pass 2: severity + bind-pose check for the 2026-10-17 shirt FBX.

Read-only. Answers the three questions pass 1 could not:
  1. how far off are the 207 non-normalised weight sums?
  2. where are the 25 unweighted vertices (which part of the garment)?
  3. does the FBX rest geometry match the live skeleton's reference pose?
     (axis-invariant test: pairwise landmark distances, cm)

  hython Saved/Audit/ShirtBones_20261020/verify_shirt_fbx_pass2.py
"""
from __future__ import annotations

import argparse
import itertools
import json
from pathlib import Path

import hou

REPO = Path("C:/EnvironmentPortfolio/BS_GodFile")
FBX = REPO / "Saved/Staging/WaveHarpScythe_20261017/SK_Melusina_V2_Shirt_Flared.fbx"
REF = REPO / "Saved/Audit/ShirtBones_20261020/canonical_ref_pose.json"
OUT = REPO / "Saved/Audit/ShirtBones_20261020/route_b_verification_pass2.json"

LANDMARKS = [
    "spine_01_x", "spine_02_x", "spine_03_x", "neck_x", "head_x",
    "shoulder_l", "shoulder_r", "arm_stretch_l", "arm_stretch_r",
    "c_kilt_master_x", "root_x", "thigh_stretch_l", "thigh_stretch_r",
]


def pairs_of(pt):
    v = pt.attribValue("boneCapture")
    return [(int(v[i]), float(v[i + 1])) for i in range(0, len(v) - 1, 2)]


def dist(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fbx", default=str(FBX))
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    fbx = Path(args.fbx)
    out_path = Path(args.out)

    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "verify2")
    imp = geo.createNode("kinefx::fbxcharacterimport", "fbx_in")
    imp.parm("fbxfile").set(str(fbx.resolve()))
    try:
        imp.parm("convertunits").set(1)
    except Exception:
        pass
    skin = imp.geometry(0)
    rest = imp.geometry(1)

    rest_pts = [p.position() for p in rest.points()]
    rest_names = [str(p.attribValue("name")) for p in rest.points()]
    idx_to_name = dict(enumerate(rest_names))
    name_to_pos = {n: rest_pts[i] for i, n in enumerate(rest_names)}

    rep: dict = {"schema": "melodia.shirt_fbx_route_b_pass2.v1", "fbx": str(fbx)}

    # ---- 1. weight-sum distribution ----
    sums = []
    zero_pts = []
    for p in skin.points():
        prs = [(i, w) for i, w in pairs_of(p) if w > 1e-6]
        s = sum(w for _, w in prs)
        sums.append((p.number(), s, len(prs)))
        if not prs:
            zero_pts.append(p.number())

    buckets = {"0 (unweighted)": 0, "0-0.5": 0, "0.5-0.9": 0, "0.9-0.999": 0,
               "0.999-1.001": 0, "1.001-1.1": 0, "1.1-2.0": 0, ">2.0": 0}
    for _n, s, _c in sums:
        if s <= 1e-6:
            buckets["0 (unweighted)"] += 1
        elif s < 0.5:
            buckets["0-0.5"] += 1
        elif s < 0.9:
            buckets["0.5-0.9"] += 1
        elif s < 0.999:
            buckets["0.9-0.999"] += 1
        elif s <= 1.001:
            buckets["0.999-1.001"] += 1
        elif s <= 1.1:
            buckets["1.001-1.1"] += 1
        elif s <= 2.0:
            buckets["1.1-2.0"] += 1
        else:
            buckets[">2.0"] += 1
    rep["weight_sum_buckets"] = buckets
    off = [(n, round(s, 4)) for n, s, _c in sums if abs(s - 1.0) > 1e-3 and s > 1e-6]
    off.sort(key=lambda t: abs(t[1] - 1.0), reverse=True)
    rep["worst_off_sum_sample"] = off[:15]
    rep["off_sum_count"] = len(off)

    # ---- 2. where are the unweighted vertices ----
    pts = [p.position() for p in skin.points()]
    if zero_pts:
        zp = [pts[i] for i in zero_pts]
        ext = [round(max(c) - min(c), 4) for c in zip(*zp)]
        cen = [round(sum(c) / len(zp), 4) for c in zip(*zp)]
        rep["zero_weight"] = {
            "count": len(zero_pts),
            "centroid_m": cen,
            "extent_m": ext,
            "span_m": [round(min(c), 4) for c in zip(*zp)] + [round(max(c), 4) for c in zip(*zp)],
        }
        # nearest rest joint for each unweighted point (diagnosis only)
        near = {}
        for i in zero_pts:
            best = min(rest_pts, key=lambda rp: dist(pts[i], rp))
            j = rest_pts.index(best)
            nm = rest_names[j]
            near[nm] = near.get(nm, 0) + 1
        rep["zero_weight_nearest_joints"] = sorted(near.items(), key=lambda kv: -kv[1])[:10]

    # ---- 3. garment height bands (Z in SOP metres) ----
    zs = [p[2] for p in pts]
    z_lo, z_hi = min(zs), max(zs)
    rep["z_span_m"] = [round(z_lo, 4), round(z_hi, 4)]
    band_h = (z_hi - z_lo)
    # hem band = bottom 10% of garment height, excluding points far out on X (sleeves)
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    med_r = sorted(dist((p[0], p[1], 0), (cx, cy, 0)) for p in pts)[len(pts) // 2]
    hem_pts = []
    for i, p in enumerate(pts):
        if p[2] <= z_lo + band_h * 0.12:
            r = dist((p[0], p[1], 0), (cx, cy, 0))
            if r <= med_r * 1.35:
                hem_pts.append(i)
    hem_hist: dict[str, int] = {}
    for i in hem_pts:
        prs = [(j, w) for j, w in pairs_of(skin.points()[i]) if w > 1e-6]
        for j, _w in prs:
            nm = idx_to_name.get(j, f"<idx {j}>")
            hem_hist[nm] = hem_hist.get(nm, 0) + 1
    rep["hem_band"] = {
        "candidate_points": len(hem_pts),
        "median_radius_m": round(med_r, 3),
        "bone_hist": sorted(hem_hist.items(), key=lambda kv: -kv[1])[:12],
    }

    # ---- 4. bind/rest pose vs live reference pose (axis-invariant) ----
    ref = json.loads(REF.read_text(encoding="utf-8"))
    ref_pos = {}
    for b in ref["bones"]:
        c = b.get("component", {}).get("location", {})
        ref_pos[b["name"]] = (c.get("x", 0.0), c.get("y", 0.0), c.get("z", 0.0))

    common = [n for n in LANDMARKS if n in name_to_pos and n in ref_pos]
    rows = []
    for a, b in itertools.combinations(common, 2):
        fbx_d = dist(name_to_pos[a], name_to_pos[b]) * 100.0  # m -> cm
        ref_d = dist(ref_pos[a], ref_pos[b])
        rows.append({"pair": f"{a}|{b}", "fbx_cm": round(fbx_d, 3), "ref_cm": round(ref_d, 3),
                     "delta_mm": round((fbx_d - ref_d) * 10.0, 2)})
    deltas = [abs(r["delta_mm"]) for r in rows] if rows else []
    rep["landmarks_compared"] = common
    rep["pairwise_distance_rows"] = rows
    rep["pairwise_delta_mm_max"] = max(deltas) if deltas else None
    rep["pairwise_delta_mm_median"] = sorted(deltas)[len(deltas) // 2] if deltas else None
    rep["rest_pose_matches_within_1mm"] = bool(deltas) and max(deltas) <= 1.0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print("WROTE", out_path)
    print("BUCKETS", json.dumps(buckets))
    print("OFF_SUM", rep["off_sum_count"], "worst", json.dumps(rep["worst_off_sum_sample"][:5]))
    print("ZERO", json.dumps(rep.get("zero_weight", {})))
    print("ZERO_NEAR", json.dumps(rep.get("zero_weight_nearest_joints")))
    print("HEM", json.dumps(rep["hem_band"]))
    print("REST_MATCH", rep["rest_pose_matches_within_1mm"], "max_mm",
          rep["pairwise_delta_mm_max"], "median_mm", rep["pairwise_delta_mm_median"])
    print("WORST_PAIRS", json.dumps(sorted(rows, key=lambda r: -abs(r["delta_mm"]))[:5]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
