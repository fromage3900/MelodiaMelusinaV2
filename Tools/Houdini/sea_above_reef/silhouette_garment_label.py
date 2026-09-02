"""Silhouette-geometry garment layer labeler for the Shorewake dress (v2).

Data-calibrated v2. Reads the slotted 48-panel OBJ, computes per-panel
silhouette descriptors relative to the GLOBAL dress axis (mean x,y of all
verts; z-range from the whole dress), then assigns each panel to a semantic
garment layer and a merged material group.

Classifier rules are calibrated to the observed silhouette geometry of this
specific dress (axis x≈0.0 y≈0.155, z −0.16..1.50, ~1.66 m tall). Merging
groups panels whose silhouettes read as the same garment piece/layer so they
can share one labeled material.

Deterministic. Headless, numpy only.
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

OBJ = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_lookdev/bake/"
    r"night_pkg_2026-08-31/SM_ShorewakeDress_48MAT_v2_slotted.obj")
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(
    r"C:/EnvironmentPortfolio/BS_GodFile/Saved/Audit/melusina_lookdev/"
    r"night_pkg_2026-08-31/garment_layers_manifest.json")
SEED = 20260902


def load(obj):
    verts = []
    faces = defaultdict(list)
    cur = None
    with open(obj, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("v "):
                verts.append([float(x) for x in line.split()[1:4]])
            elif line.startswith("usemtl "):
                cur = line.split()[1]
            elif line.startswith("f ") and cur is not None:
                faces[cur].extend(int(t.split("/")[0]) - 1 for t in line.split()[1:])
    return np.array(verts), faces


def pid(name):
    return int("".join(c for c in name if c.isdigit()) or 0)


def classify(r):
    """Assign garment_layer + material_group from silhouette features."""
    zlo, zhi, zsp = r["zlo"], r["zhi"], r["zsp"]
    rmean, rmax = r["rmean"], r["rmax"]
    w, d = r["w"], r["d"]
    azlo, azhi = r["azlo"], r["azhi"]
    verts = r["verts"]
    azspan = azhi - azlo
    wraps = azlo < -170 and azhi > 170  # spans the ±180 seam

    # --- full/upper-wide main masses ---
    if wrapt := (w > 0.9):  # widest single pieces
        if zhi > 1.3 and zlo > 0.8:
            return "Bodice_Torso", "M_Bodice_Torso", "Huge bust/torso shell, widest shoulder span"
        if zlo < 0.0:
            return "Skirt_Main", "M_Skirt_Full", "Full-length outer skirt mass, reaches floor"
        return "Wide_Mid", "M_Skirt_Full", "Wide mid band, skirt family"

    # --- long vertical skirt/underskirt panels (thin, tall) ---
    if zsp > 0.7:
        return "Skirt_Body_Long", "M_Skirt_Full", "Long vertical panel, skirt body"

    # --- upper bodice band (0.9..1.4) ---
    if zlo > 0.9:
        # wrap (crosses seam) + thin = collar / basque band
        if wraps and w < 0.3 and d < 0.3 and zsp < 0.4:
            return "Collar_Band", "M_Collar", "Wrapping collar/neckline band"
        # very short tiny decorative cluster
        if verts <= 40 and zsp <= 0.03 and w <= 0.15:
            return "Shoulder_Ornament", "M_Shoulder_Ornament", "Tiny cap cluster — decorative studs/beads"
        # 168-vert caps on the shoulder (right/back azimuth)
        if 150 <= verts <= 300 and w <= 0.08 and zsp <= 0.05:
            return "Shoulder_Armcap", "M_Shoulder_Trim", "Small shoulder/armhole cap trim"
        # mid bodice band panels (w 0.02..0.2): front chest / yoke row
        if w <= 0.25 and zsp <= 0.25:
            if azspan <= 50 or wraps:
                return "Bodice_Front", "M_Bodice_Front", "Front chest/yoke panel row"
            return "Bodice_Side", "M_Bodice_Side", "Side torso panel"
        return "Bodice_Upper", "M_Bodice_Upper", "Upper bodice band"

    # --- lower-to-mid: sleeves (az negative) vs underskirt vs mid body ---
    if zhi > 0.95 and zlo < 0.85 and w < 0.3:
        return "Sleeve_Uppermid", "M_Sleeve", "Sleeve/arm panel, mid-upper span"
    if zlo < 0.85 and zhi > 0.9:
        return "Underskirt", "M_Underskirt", "Mid skirt/slip panel"
    return "Mid_Tier", "M_Skirt_Full", "Mid-height skirt tier"


def main():
    A, faces = load(OBJ)
    axis_xy = A[:, :2].mean(axis=0)
    zmin, zmax = A[:, 2].min(), A[:, 2].max()
    print(f"[garment] axis xy={axis_xy.round(3)} z range [{zmin:.2f},{zmax:.2f}] [{len(faces)} panels]")
    rows = []
    for name, idxs in faces.items():
        v = A[np.unique(np.clip(np.array(idxs, dtype=np.int64), 0, len(A) - 1))]
        r = np.linalg.norm(v[:, :2] - axis_xy, axis=1)
        rz = v[:, 2]
        ang = np.degrees(np.arctan2(v[:, 1] - axis_xy[1], v[:, 0] - axis_xy[0]))
        f = {
            "panel": name,
            "zlo": round(float(rz.min()), 3),
            "zhi": round(float(rz.max()), 3),
            "zsp": round(float(rz.max() - rz.min()), 3),
            "rmean": round(float(r.mean()), 3),
            "rmax": round(float(r.max()), 3),
            "w": round(float(v[:, 0].max() - v[:, 0].min()), 3),
            "d": round(float(v[:, 1].max() - v[:, 1].min()), 3),
            "azlo": int(round(float(ang.min()))),
            "azhi": int(round(float(ang.max()))),
            "verts": int(len(v)),
        }
        layer, group, why = classify(f)
        f["garment_layer"] = layer
        f["material_group"] = group
        f["rationale"] = why
        rows.append(f)

    rows.sort(key=lambda r: pid(r["panel"]))
    groups = defaultdict(list)
    for r in rows:
        groups[r["material_group"]].append(r["panel"])
    grouped = {g: {"panels": sorted(v, key=pid), "count": len(v)} for g, v in groups.items()}

    manifest = {
        "schema": "melodia.shorewake_garment_layers.v2",
        "seed": SEED,
        "source": str(OBJ),
        "axis_xy": [round(float(x), 4) for x in axis_xy],
        "z_range": [round(zmin, 3), round(zmax, 3)],
        "panel_count": len(rows),
        "method": "silhouette geometry relative to the global dress axis (cylindrical "
                   "radial spread, z-elevation band, width/depth, azimuth, wrap-across-"
                   "seam, size) -> garment layer + merged material group",
        "material_groups": grouped,
        "panels": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[garment] wrote {OUT}")
    print(f"[garment] merged material groups ({len(grouped)}):")
    for g in sorted(grouped):
        print(f"   {g:22s} {grouped[g]['count']:2d}  {', '.join(grouped[g]['panels'])}")


if __name__ == "__main__":
    main()