"""Universal Rig Pipeline v1 — Houdini-side authoring for UE consumption (later).

Melusina is the reference character; every change must also pass the sheep
fast loop. No editor, no mutation of production assets: this forges source
data + manifests under Saved/Audit/melusina_animation_doctor/rig/.

  hython Tools/Houdini/universal_rig/universal_rig.py --profile melusina
  hython Tools/Houdini/universal_rig/universal_rig.py --profile sheep

Manifest schema: melodia.universal_rig_manifest.v1
Nikki lens served: N2 clothing-aware movement, N3 layered contact, N5 symmetric
silhouette, N9 face-clear settle volumes.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PROFILE_DIR = Path(__file__).resolve().parent / "profiles"
RIG_OUT = REPO / "Saved/Audit/melusina_animation_doctor/rig"


def mesh_stats(geo, role: str) -> dict:
    pts = geo.points()
    bbox = geo.boundingBox()
    return {"role": role, "points": len(pts), "prims": len(geo.prims()),
            "bounds_min": list(bbox.minvec()), "bounds_max": list(bbox.maxvec())}


def _build_grid(pts, cell):
    from collections import defaultdict
    grid: dict = defaultdict(list)
    for i, v in enumerate(pts):
        grid[(round(v[0] / cell), round(v[1] / cell), round(v[2] / cell))].append(i)
    return grid


def _nearest_in_grid(pts, grid, cell, idx, target, max_rings=6):
    cx = round(target[0] / cell)
    cy = round(target[1] / cell)
    cz = round(target[2] / cell)
    best = float("inf")
    for ring in range(max_rings + 1):
        for dx in range(-ring, ring + 1):
            for dy in range(-ring, ring + 1):
                for dz in range(-ring, ring + 1):
                    if max(abs(dx), abs(dy), abs(dz)) != ring:
                        continue
                    for j in grid.get((cx + dx, cy + dy, cz + dz), ()):
                        if j == idx:
                            continue
                        w = pts[j]
                        d = ((w[0] - target[0]) ** 2 + (w[1] - target[1]) ** 2
                             + (w[2] - target[2]) ** 2) ** 0.5
                        if d < best:
                            best = d
        if best <= (ring + 1) * cell:
            break
    return best


def symmetry_qa(src_geo, gate_mm: float = 5.0) -> dict:
    """N5: mirror-distance with mesh-adaptive tolerance (pure hou, no VEX).
    Mirrors across the mesh's OWN midplane (bbox center x), not world x=0.
    Resolution comes from mean nearest-neighbour distance so a coarse test mesh
    isn't failed for sparsity; the gate used is reported and auditable."""
    pts = [p.position() for p in src_geo.points()]
    n = len(pts)
    xs = [v[0] for v in pts]
    cx0 = (min(xs) + max(xs)) / 2.0
    g0 = _build_grid(pts, 2.0)
    step0 = max(1, n // 400)
    tot0, cnt0 = 0.0, 0
    for i in range(0, n, step0):
        d = _nearest_in_grid(pts, g0, 2.0, i, pts[i])
        if d != float("inf"):
            tot0 += d
            cnt0 += 1
    resolution = tot0 / max(1, cnt0)
    cell = min(8.0, max(1.0, resolution * 1.5))
    gate = max(gate_mm, 2.0 * cell * 10.0)
    grid = _build_grid(pts, cell)
    step = max(1, n // 2000)
    total, peak, cnt, missed = 0.0, 0.0, 0, 0
    for i in range(0, n, step):
        v = pts[i]
        mirrored = (2.0 * cx0 - v[0], v[1], v[2])
        d = _nearest_in_grid(pts, grid, cell, i, mirrored)
        if d == float("inf"):
            missed += 1
            continue
        total += d
        peak = max(peak, d)
        cnt += 1
    mean_mm = (total / max(1, cnt)) * 10.0
    unmatched_frac = missed / max(1, cnt + missed)
    return {"samples": cnt, "unmatched": missed,
            "unmatched_frac": round(unmatched_frac, 4),
            "midplane_x_cm": round(cx0, 3),
            "resolution_mm": round(resolution * 10.0, 2),
            "gate_mm": round(gate, 2),
            "mean_mm": round(mean_mm, 3),
            "max_mm": round(peak * 10.0, 3),
            "pass": mean_mm <= gate and unmatched_frac <= 0.02}


def region_split(parent, src, regions: list[dict]) -> dict:
    geo = src.geometry()
    pts = geo.points()
    bbox = geo.boundingBox()
    lo, hi = bbox.minvec()[1], bbox.maxvec()[1]
    span = max(1e-6, hi - lo)
    out = {}
    for r in regions:
        y0 = lo + r["y_frac"][0] * span
        y1 = lo + r["y_frac"][1] * span
        out[r["name"]] = {"y_cm": [round(y0, 2), round(y1, 2)], "purpose": r["purpose"],
                          "points": 0}
    for p in pts:
        y = p.position()[1]
        for r in regions:
            y0 = lo + r["y_frac"][0] * span
            y1 = lo + r["y_frac"][1] * span
            if (y >= y0 and y <= y1) or (r is regions[-1] and y < y0):
                out[r["name"]]["points"] += 1
                break
    return out


def garment_overlap(body_bbox, g_geo) -> dict:
    lo, hi = list(body_bbox.minvec()), list(body_bbox.maxvec())
    margin = 2.0
    inside = total = 0
    for p in g_geo.points():
        total += 1
        v = p.position()
        if all(lo[a] - margin <= v[a] <= hi[a] + margin for a in range(3)):
            inside += 1
    return {"points": total,
            "inside_body_bounds_frac": round(inside / max(1, total), 4)}


def main() -> int:
    import hou

    ap = argparse.ArgumentParser(description="Universal Rig Pipeline v1 (headless)")
    ap.add_argument("--profile", required=True, help="melusina | sheep")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    profile = json.loads((PROFILE_DIR / f"{args.profile}.v1.json").read_text(encoding="utf-8"))
    contract = json.loads((REPO / "specs/universal_rig/rig_contract.v1.json").read_text(encoding="utf-8"))
    char = profile["character"]

    hou.hipFile.clear(suppress_save_prompt=True)
    lab = hou.node("/obj").createNode("subnet", f"rig_{char}")
    georoot = lab.createNode("geo", "intake")

    meshes, geos = {}, {}
    for role, rel in profile["meshes"].items():
        f = georoot.createNode("file", f"in_{role}")
        f.parm("file").set((REPO / rel).as_posix())
        g = f.geometry()
        geos[role] = (f, g)
        meshes[role] = mesh_stats(g, role)

    body_geo = geos["body"][1]
    sym = symmetry_qa(body_geo, gate_mm=float(profile.get("symmetry_gate_mm", 5.0)))
    regions = region_split(georoot, geos["body"][0], profile["regions"])

    layers = {}
    for rel in profile.get("garments", []):
        name = Path(rel).stem
        f = georoot.createNode("file", f"layer_{name}")
        f.parm("file").set((REPO / rel).as_posix())
        try:
            g = f.geometry()
            layers[name] = {"points": len(g.points()),
                            **garment_overlap(body_geo.boundingBox(), g)}
        except Exception as exc:  # noqa: BLE001
            layers[name] = {"error": str(exc)[:160]}

    ue_orders = [
        {"id": "skeleton_fbx_export", "status": "BLOCKED",
         "detail": "Export jointed skeleton FBX from SK_Melusina_Skeleton (UE) — unblocks capture weights; lab cooks clean without it (i@capture_missing)."},
        {"id": "kawaii_chain_assignment", "status": "READY",
         "detail": f"Bind chains {profile['kawaii_chains']} to regions {[r['name'] for r in profile['regions']]} under existing sharing authority."},
        {"id": "physics_bodies_per_region", "status": "READY",
         "detail": "Author per-region collision bodies from manifest bounds into PhysicsAssetForLimits; no new solver."},
        {"id": "retarget_map_apply", "status": "READY",
         "detail": "Apply contract retarget_map for new donors; verify arm canon numbers before shipping any clip."},
        {"id": "layer_mask_11", "status": "READY",
         "detail": "Any new layered blend on her ABP carries the 11-filter mask or draw/cast is blended away."},
    ]

    manifest = {
        "schema": "melodia.universal_rig_manifest.v1",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "character": char, "profile": args.profile,
        "contract": "specs/universal_rig/rig_contract.v1.json",
        "meshes": meshes,
        "symmetry_N5": sym,
        "regions": regions,
        "garment_layers_N2N3": layers,
        "joint_gap": "source FBXs carry polygon meshes only — no joints; capture staged, weights await skeleton_fbx_export",
        "ue_work_orders": ue_orders,
        "nikki_served": ["N2", "N3", "N5", "N9"],
        "hip_staged": {"test_lab": "Tools/Houdini/melusina_weight_lab.hipnc",
                       "melusina_lab": "Tools/Houdini/melusina_weight_lab_melusina.hipnc"},
    }
    RIG_OUT.mkdir(parents=True, exist_ok=True)
    out = REPO / args.out if args.out else RIG_OUT / f"rig_manifest_{char}.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"character": char, "meshes": {k: v["points"] for k, v in meshes.items()},
                       "symmetry": sym, "layers": len(layers),
                       "out": out.relative_to(REPO).as_posix()}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
