"""Route (b): verify the 2026-10-17 staged shirt FBX against the live canonical skeleton.

Read-only. Imports the FBX twice (KineFX character import for skin/rest, scene
import for node hierarchy), then reports:
  * joint census vs the live 465-bone SK_Melusina_Skeleton
  * unknown / missing bone names (the "same USkeleton" legality test)
  * capture weights: max influences, sum, zero-weight points, leg-bound points
  * which bones the lower hem actually uses
  * rest-pose comparison where available

  hython Saved/Audit/ShirtBones_20261020/verify_shirt_fbx.py [--fbx PATH] [--out PATH]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import hou

REPO = Path("C:/EnvironmentPortfolio/BS_GodFile")
DEFAULT_FBX = REPO / "Saved/Staging/WaveHarpScythe_20261017/SK_Melusina_V2_Shirt_Flared.fbx"
CANON_JSON = REPO / "Saved/Audit/ShirtBones_20261020/canonical_skeleton.json"
OUT = REPO / "Saved/Audit/ShirtBones_20261020/route_b_verification.json"

LEG_HINTS = ("thigh", "leg_stretch", "leg_", "foot", "toes", "ik_foot", "calf", "shin")
HEM_HINTS = ("hem", "kilt", "root")


def pairs_of(pt):
    v = pt.attribValue("boneCapture")
    return [(int(v[i]), float(v[i + 1])) for i in range(0, len(v) - 1, 2)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fbx", default=str(DEFAULT_FBX))
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()
    fbx = Path(args.fbx)

    canon = json.loads(CANON_JSON.read_text(encoding="utf-8"))
    canon_names = [b["name"] for b in canon["bones"]]
    canon_set = set(canon_names)

    rep: dict = {
        "schema": "melodia.shirt_fbx_route_b_verification.v1",
        "fbx": str(fbx),
        "fbx_exists": fbx.exists(),
        "fbx_bytes": fbx.stat().st_size if fbx.exists() else None,
        "canonical_skeleton": canon.get("asset_path"),
        "canonical_bone_count": len(canon_names),
    }

    # ---------- pass 1: KineFX character import (skin + rest joints) ----------
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "verify_shirt")
    imp = geo.createNode("kinefx::fbxcharacterimport", "fbx_in")
    imp.parm("fbxfile").set(str(fbx.resolve()))
    try:
        imp.parm("convertunits").set(1)
    except Exception:
        pass
    skin = imp.geometry(0)
    rest = imp.geometry(1)

    if skin is None or rest is None:
        rep["fatal"] = "fbxcharacterimport returned empty geometry"
        Path(args.out).write_text(json.dumps(rep, indent=1), encoding="utf-8")
        print("FATAL: empty geometry")
        return 1

    rest_names = [str(p.attribValue("name")) for p in rest.points()]
    # KineFX capture indices index the rest-joint point order.
    idx_to_name = {i: n for i, n in enumerate(rest_names)}

    rep["rest_joint_count"] = len(rest_names)
    rep["rest_joint_names_sample"] = rest_names[:8]
    rep["skin_point_count"] = len(skin.points())
    rep["skin_prim_count"] = len(skin.prims())
    rep["skin_point_attrs"] = [a.name() for a in skin.pointAttribs()]
    rep["skin_prim_attrs"] = [a.name() for a in skin.primAttribs()]

    unknown = sorted({n for n in rest_names if n not in canon_set})
    missing = sorted(canon_set - set(rest_names))
    rep["unknown_bones_not_in_canonical"] = unknown[:60]
    rep["unknown_bone_count"] = len(unknown)
    rep["missing_canonical_bones_count"] = len(missing)
    rep["missing_canonical_bones_sample"] = missing[:40]
    rep["legality_same_skeleton"] = (len(unknown) == 0 and len(missing) == 0)

    # ---------- weights ----------
    has_capture = skin.findPointAttrib("boneCapture") is not None
    rep["has_boneCapture_attrib"] = has_capture
    if has_capture:
        max_inf = 0
        bad_sum = 0
        zero = []
        leg_bound = []
        hem_bound = []
        leg_point_count = 0
        used_idx = set()
        per_point = []
        for p in skin.points():
            prs = [(i, w) for i, w in pairs_of(p) if w > 1e-6]
            if not prs:
                zero.append(p.number())
                continue
            max_inf = max(max_inf, len(prs))
            s = sum(w for _, w in prs)
            if abs(s - 1.0) > 1e-3:
                bad_sum += 1
            domin = max(prs, key=lambda t: t[1])[0]
            used_idx.add(domin)
            names = [idx_to_name.get(i, f"<idx {i}>") for i, _ in prs]
            for i, w in prs:
                nm = idx_to_name.get(i, "")
                if any(h in nm.lower() for h in LEG_HINTS) and w > 0.01:
                    leg_point_count += 1
                    leg_bound.append(p.number())
                    break
            for i, w in prs:
                nm = idx_to_name.get(i, "")
                if "hem" in nm.lower():
                    hem_bound.append(p.number())
                    break
            per_point.append((p.number(), prs, p.position()))

        rep["weights"] = {
            "max_influences": max_inf,
            "points_with_sum_not_1": bad_sum,
            "zero_weight_points": len(zero),
            "zero_weight_sample": zero[:20],
            "leg_bound_points": leg_point_count,
            "leg_bound_distinct_points": len(set(leg_bound)),
            "hem_influenced_points": len(set(hem_bound)),
            "distinct_dominant_bones": len(used_idx),
        }

        # dominant-bone histogram (all points)
        hist: dict[str, int] = {}
        for p in skin.points():
            prs = [(i, w) for i, w in pairs_of(p) if w > 1e-6]
            if not prs:
                continue
            d = max(prs, key=lambda t: t[1])[0]
            nm = idx_to_name.get(d, f"<idx {d}>")
            hist[nm] = hist.get(nm, 0) + 1
        top = sorted(hist.items(), key=lambda kv: -kv[1])[:25]
        rep["dominant_bone_top25"] = top

        # what drives the lowest band (hem region, low Z in SOP metres)
        if per_point:
            zs = sorted(pt[2][2] for pt in per_point)
            z_lo, z_hi = zs[0], zs[-1]
            rep["height_span_m"] = [round(z_lo, 4), round(z_hi, 4)]
            cut = z_lo + (z_hi - z_lo) * 0.30
            lower = [pt for pt in per_point if pt[2][2] <= cut]
            lh: dict[str, int] = {}
            for _, prs, _pos in lower:
                top_w = sorted(prs, key=lambda t: -t[1])[:2]
                for i, w in top_w:
                    nm = idx_to_name.get(i, f"<idx {i}>")
                    lh[nm] = lh.get(nm, 0) + 1
            rep["lower_band_point_count"] = len(lower)
            rep["lower_band_bone_hist"] = sorted(lh.items(), key=lambda kv: -kv[1])[:15]

        # leg-hint bones that carry any weight at all, with counts
        leg_hist: dict[str, int] = {}
        for p in skin.points():
            for i, w in pairs_of(p):
                if w <= 1e-4:
                    continue
                nm = idx_to_name.get(i, "")
                if any(h in nm.lower() for h in LEG_HINTS):
                    leg_hist[nm] = leg_hist.get(nm, 0) + 1
        rep["leg_hint_bones_with_weight"] = sorted(leg_hist.items(), key=lambda kv: -kv[1])[:15]

    # ---------- pass 2: scene import for hierarchy ----------
    hou.hipFile.clear(suppress_save_prompt=True)
    hou.hipFile.importFBX(str(fbx.resolve()))
    obj = hou.node("/obj")

    joints = []
    stack = list(obj.children())
    while stack:
        n = stack.pop()
        t = n.type().name()
        if t in ("bone", "null"):
            joints.append((n.name(), n.parent().name() if n.parent() else None, t))
        stack.extend(n.children())

    rep["scene_joint_node_count"] = len(joints)
    rep["scene_joint_sample"] = joints[:8]

    verified_parents = 0
    parent_mismatch = []
    canon_parent = {b["name"]: b.get("parent_name") for b in canon["bones"]}
    for name, parent, _t in joints:
        if name in canon_parent:
            expected = canon_parent.get(name)
            got = parent
            # scene import may nest under a wrapper subnet / root object
            if expected is None:
                if got is None or got not in canon_set:
                    verified_parents += 1
            elif got == expected:
                verified_parents += 1
            else:
                parent_mismatch.append({"bone": name, "expected": expected, "fbx_parent": got})
    rep["parent_verified_count"] = verified_parents
    rep["parent_mismatch_count"] = len(parent_mismatch)
    rep["parent_mismatch_sample"] = parent_mismatch[:15]

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(rep, indent=1), encoding="utf-8")
    print("WROTE", args.out)
    print("REST_JOINTS", rep["rest_joint_count"], "SKIN_PTS", rep["skin_point_count"])
    print("LEGALITY", rep["legality_same_skeleton"], "UNKNOWN", rep["unknown_bone_count"],
          "MISSING", rep["missing_canonical_bones_count"])
    if "weights" in rep:
        print("WEIGHTS", json.dumps(rep["weights"]))
        print("LOWER_BAND", json.dumps(rep["lower_band_bone_hist"][:8]))
    print("SCENE_JOINTS", rep["scene_joint_node_count"], "PARENT_OK", rep["parent_verified_count"],
          "PARENT_BAD", rep["parent_mismatch_count"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
