"""THE FARAWAY MOTHER — cloth-mountain terrain generator v0 (textile-landscape pipeline).

Bible canon (Docs/Art/MONOLITH_LEVEL_DESIGN_BIBLE_2026-08-26.md #10):
  "Mountain faces have unusually smooth, pleated strata. Valleys follow seam-like
   lines. Forests form repeated decorative motifs. Roads appear carved through
   folds rather than rock."

This v0 builds ONE 2 km hero tile as a deterministic heightfield with:
  - PLEATED STRATA: smooth parallel fold ridges (fabric strata, never rocky noise)
  - SEAM VALLEYS: two bezier seam curves cut as V channels with fold lips
  - EMBROIDERY MOTIFS: a repeated stitch-motif stamped along a pilgrimage path
    (the "forests as decorative motifs" read)
  - BASE DRAPE: low-frequency value-noise rolling cloth

Deterministic (seeded); geometry leaves as OBJ via File SOP write (Apprentice-safe:
no FBX/Alembic export). Manifest records every constant.

Outputs (Saved/Audit/faraway_mother/):
  SM_ClothMountains_v0.obj
  cloth_mountains_v0_manifest.json

Run (isolated console):
  & "C:\\Program Files\\Side Effects Software\\Houdini 22.0.368\\bin\\hython.exe" ^
      Tools/Houdini/sea_above_reef/build_cloth_mountains.py
"""

import json
import math
from pathlib import Path

import hou

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "Saved" / "Audit" / "faraway_mother"

SEED = 20260829
TILE = 2000.0                # metres
GRID = 384                   # heightfield resolution (GRID+1)^2 points
BASE_H = 140.0               # rolling drape amplitude
PLEAT_AMP = 60.0             # strata fold amplitude
PLEAT_PERIOD = 88.0          # metres between strata
PLEAT_WARP = 0.012           # slow warp so strata stay parallel but alive
SEAM_DEPTH = 90.0
SEAM_WIDTH = 26.0            # metres, gaussian falloff
MOTIF_PERIOD = 46.0          # stitch spacing along the path
MOTIF_H = 9.0                # embroidery bump height

CODE = r"""
import hou, math, random

node = hou.pwd()
geo = node.geometry()

SEED = __SEED__
TILE = __TILE__
GRID = __GRID__
BASE_H = __BASE_H__
PLEAT_AMP = __PLEAT_AMP__
PLEAT_PERIOD = __PLEAT_PERIOD__
PLEAT_WARP = __PLEAT_WARP__
SEAM_DEPTH = __SEAM_DEPTH__
SEAM_WIDTH = __SEAM_WIDTH__
MOTIF_PERIOD = __MOTIF_PERIOD__
MOTIF_H = __MOTIF_H__

rng = random.Random(SEED)

# deterministic value noise on a 12x12 lattice, bilinear + smoothstep
LAT = 12
lat = [[rng.uniform(-1.0, 1.0) for _ in range(LAT + 1)] for _ in range(LAT + 1)]

def vnoise(u, v):
    fu, fv = u * LAT, v * LAT
    iu, iv = min(int(fu), LAT - 1), min(int(fv), LAT - 1)
    tu, tv = fu - iu, fv - iv
    tu, tv = min(tu, 1.0), min(tv, 1.0)
    su = tu * tu * (3 - 2 * tu)
    sv = tv * tv * (3 - 2 * tv)
    a = lat[iv][iu] * (1 - su) + lat[iv][iu + 1] * su
    b = lat[iv + 1][iu] * (1 - su) + lat[iv + 1][iu + 1] * su
    return a * (1 - sv) + b * sv

def seam_curves():
    # two bezier seams across the tile (seam-like valleys)
    def bez(p0, p1, p2, t):
        mt = 1 - t
        return (mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
                mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1])
    c1 = [bez((0.05, 0.15), (0.45, 0.35), (0.95, 0.55), i / 240.0) for i in range(241)]
    c2 = [bez((0.95, 0.10), (0.55, 0.62), (0.10, 0.92), i / 240.0) for i in range(241)]
    return [c1, c2]

CURVES = seam_curves()

def dist_to_curve(xn, yn, curve):
    # xn/yn in 0..1 normalized tile space
    best = 1e18
    for (cx, cy) in curve:
        d = (xn - cx) ** 2 + (yn - cy) ** 2
        if d < best:
            best = d
    return math.sqrt(best)

def embroidery(xn, yn):
    # stitch-motif stamps along a pilgrimage path (a gentle S across the tile)
    t = yn
    path_x = 0.5 + 0.28 * math.sin(t * math.pi * 1.6 + 0.4)
    d = (xn - path_x)
    along = t * TILE
    phase = (along % MOTIF_PERIOD) / MOTIF_PERIOD
    motif = (math.sin(phase * math.pi * 2.0) ** 2) * (math.cos(d * 40.0) ** 2)
    gate = math.exp(-(d ** 2) / 0.0012)
    return MOTIF_H * motif * gate

rows = []
for j in range(GRID + 1):
    row = []
    for i in range(GRID + 1):
        xn = i / GRID
        yn = j / GRID
        x = xn * TILE
        # pleated strata: smooth parallel folds with slow warp (fabric, not rock)
        warp = vnoise(xn * 0.9 + 3.1, yn * 0.9 + 7.7) * PLEAT_WARP
        strata = math.sin((x / PLEAT_PERIOD) * math.pi + warp * 40.0)
        pleat = PLEAT_AMP * (abs(strata) ** 0.7) * (0.75 + 0.25 * vnoise(xn * 2.0, yn * 2.0))
        # base drape
        drape = BASE_H * (0.5 + 0.5 * vnoise(xn * 1.4 + 11.2, yn * 1.4 + 5.5)) \
            + 0.35 * BASE_H * vnoise(xn * 3.7, yn * 3.7)
        # seam valleys: V channels with a small fold lip
        seam = 0.0
        for c in CURVES:
            d = dist_to_curve(xn, yn, c) * TILE
            seam += -SEAM_DEPTH * math.exp(-(d * d) / (SEAM_WIDTH * SEAM_WIDTH)) \
                + SEAM_DEPTH * 0.18 * math.exp(-((d - SEAM_WIDTH * 2.2) ** 2) / (SEAM_WIDTH * SEAM_WIDTH))
        h = drape + pleat + seam + embroidery(xn, yn)
        row.append((x, h, yn * TILE))
    rows.append(row)

grid_pts = []
for row in rows:
    gpt = []
    for (x, h, z) in row:
        p = geo.createPoint()
        p.setPosition(hou.Vector3(x, h, z))
        gpt.append(p)
    grid_pts.append(gpt)
for j in range(GRID):
    for i in range(GRID):
        f = geo.createPolygon()
        for q in (grid_pts[j][i], grid_pts[j][i + 1], grid_pts[j + 1][i + 1], grid_pts[j + 1][i]):
            f.addVertex(q)
try:
    geo.computeVertexNormals()
except Exception:
    pass
"""


def _inject(code, **params):
    for key, value in params.items():
        code = code.replace(f"__{key}__", repr(value))
    return code


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = hou.node("/obj")
    for old in [n for n in obj.children() if n.name() == "CLOTH_MOUNTAINS_V0"]:
        old.destroy()
    g = obj.createNode("geo", "CLOTH_MOUNTAINS_V0", run_init_scripts=True)
    py = g.createNode("python", "gen_cloth_mountain")
    code = _inject(CODE, SEED=SEED, TILE=TILE, GRID=GRID, BASE_H=BASE_H,
                   PLEAT_AMP=PLEAT_AMP, PLEAT_PERIOD=PLEAT_PERIOD,
                   PLEAT_WARP=PLEAT_WARP, SEAM_DEPTH=SEAM_DEPTH,
                   SEAM_WIDTH=SEAM_WIDTH, MOTIF_PERIOD=MOTIF_PERIOD,
                   MOTIF_H=MOTIF_H)
    py.parm("python").set(code)
    try:
        py.cook(force=True)
    except Exception:
        pass
    err = " ".join(str(py.errors()).split()) if py.errors() else ""
    if err:
        print(f"[cloth] NODE ERROR: {err[:500]}")
        g.destroy()
        return
    geo = py.geometry()
    pts = len(geo.points())
    prims = len(geo.prims())

    # Apprentice-safe export: File SOP write (menu token "write", not index)
    file_out = OUT_DIR / "SM_ClothMountains_v0.obj"
    sop = g.createNode("file", "write_obj")
    sop.parm("file").set(str(file_out))
    sop.parm("filemode").set("write")
    sop.setInput(0, py)
    try:
        sop.cook(force=True)
    except Exception:
        pass
    err2 = " ".join(str(sop.errors()).split()) if sop.errors() else ""
    ok = file_out.exists()
    print(f"[cloth] grid {pts} pts / {prims} faces; obj written={ok} "
          f"({file_out.stat().st_size if ok else 0} bytes); sop_err='{err2[:200]}'")
    g.destroy()

    manifest = {
        "schema": "melodia.faraway_mother_terrain.v1",
        "kind": "cloth-mountain hero tile v0 (pleated strata + seam valleys + embroidery path)",
        "seed": SEED,
        "tile_m": TILE, "grid": GRID,
        "constants": {"BASE_H": BASE_H, "PLEAT_AMP": PLEAT_AMP,
                      "PLEAT_PERIOD": PLEAT_PERIOD, "SEAM_DEPTH": SEAM_DEPTH,
                      "SEAM_WIDTH": SEAM_WIDTH, "MOTIF_PERIOD": MOTIF_PERIOD,
                      "MOTIF_H": MOTIF_H},
        "obj": str(file_out), "obj_written": ok,
        "hython": hou.applicationVersionString(),
        "ue_import": {"scale": "100x (m -> cm)", "nanite": True,
                      "note": "landscape-sculpture candidate; keep as hero mesh for v0"},
        "bible_source": "MONOLITH_LEVEL_DESIGN_BIBLE_2026-08-26.md #10",
    }
    (OUT_DIR / "cloth_mountains_v0_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print("[cloth] manifest -> cloth_mountains_v0_manifest.json")


if __name__ == "__main__":
    main()
