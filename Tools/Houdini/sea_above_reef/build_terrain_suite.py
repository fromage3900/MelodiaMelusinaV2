"""THE FARAWAY MOTHER — cloth-terrain SUITE v0.1 (textile-landscape pipeline).

Five deterministic biome tiles mapping the Bible's beat progression
(#10 The Faraway Mother), each exported as:
  - SM_<Tile>.obj       hero Nanite mesh (m -> cm x100 on import)
  - HM_<Tile>.r16       16-bit raw heightmap (UE Landscape import option,
                        little-endian uint16, dimensions in the manifest)
  - one suite manifest

v0.1 fixes over the v0 tile: pleat amplitude is MODULATED (strata fade in and
out along strike) and pleat phase is WARPED (strata curve), so the surface
reads as draped cloth rather than ploughed fields. Each biome sets its own
pleat strike angle, fold scale, seam set, and embroidery field.

Tiles (Bible beat -> spec):
  A hemlands           gentle fabric hills, one shallow seam, soft motifs
  B pleated_range      kilometre-scale folds, deep canyon seams
  C embroidered_basin  near-flat basin, basin-wide embroidery field (3 paths)
  D veiled_mountains   tall curving folds for fog/mist work
  E seam_road          a road carved through a fold: flat-floored channel

Run (isolated console):
  & "C:\\Program Files\\Side Effects Software\\Houdini 22.0.368\\bin\\hython.exe" ^
      Tools/Houdini/sea_above_reef/build_terrain_suite.py
"""

import json
import math
from pathlib import Path

import hou

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "Saved" / "Audit" / "faraway_mother" / "terrain"

SEED = 20260829
PHI = (1.0 + math.sqrt(5.0)) / 2.0

TILES = [
    dict(name="Hemlands", grid=384, base_h=60.0, pleat_amp=22.0, pleat_period=120.0,
         pleat_angle_deg=15.0, warp=1.6, seams=1, seam_depth=26.0, seam_width=30.0,
         motif_paths=1, motif_h=6.0, motif_period=46.0),
    dict(name="PleatedRange", grid=512, base_h=120.0, pleat_amp=340.0, pleat_period=300.0,
         pleat_angle_deg=70.0, warp=1.2, seams=2, seam_depth=300.0, seam_width=60.0,
         motif_paths=0, motif_h=0.0, motif_period=46.0),
    dict(name="EmbroideredBasin", grid=512, base_h=35.0, pleat_amp=12.0, pleat_period=200.0,
         pleat_angle_deg=30.0, warp=2.0, seams=0, seam_depth=0.0, seam_width=30.0,
         motif_paths=3, motif_h=14.0, motif_period=60.0),
    dict(name="VeiledMountains", grid=512, base_h=200.0, pleat_amp=220.0, pleat_period=160.0,
         pleat_angle_deg=100.0, warp=3.2, seams=0, seam_depth=0.0, seam_width=40.0,
         motif_paths=0, motif_h=0.0, motif_period=46.0),
    dict(name="SeamRoad", grid=512, base_h=90.0, pleat_amp=130.0, pleat_period=140.0,
         pleat_angle_deg=55.0, warp=1.4, seams=1, seam_depth=95.0, seam_width=22.0,
         road_flat=True, motif_paths=0, motif_h=0.0, motif_period=46.0),
]

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
PLEAT_ANGLE = __PLEAT_ANGLE__
WARP = __WARP__
N_SEAMS = __N_SEAMS__
SEAM_DEPTH = __SEAM_DEPTH__
SEAM_WIDTH = __SEAM_WIDTH__
ROAD_FLAT = __ROAD_FLAT__
MOTIF_PATHS = __MOTIF_PATHS__
MOTIF_H = __MOTIF_H__
MOTIF_PERIOD = __MOTIF_PERIOD__

rng = random.Random(SEED)

LAT = 12
lat = [[rng.uniform(-1.0, 1.0) for _ in range(LAT + 1)] for _ in range(LAT + 1)]

def vnoise(u, v):
    fu, fv = u * LAT, v * LAT
    iu, iv = min(int(fu), LAT - 1), min(int(fv), LAT - 1)
    tu, tv = min(fu - iu, 1.0), min(fv - iv, 1.0)
    su = tu * tu * (3 - 2 * tu)
    sv = tv * tv * (3 - 2 * tv)
    a = lat[iv][iu] * (1 - su) + lat[iv][iu + 1] * su
    b = lat[iv + 1][iu] * (1 - su) + lat[iv + 1][iu + 1] * su
    return a * (1 - sv) + b * sv

def seam_curves(n):
    out = []
    for k in range(n):
        y0 = 0.10 + 0.8 * (k % 3) / 3.0 + rng.uniform(-0.04, 0.04)
        mx = 0.35 + 0.3 * ((k % 2) - 0.5) + rng.uniform(-0.05, 0.05)
        y1 = rng.uniform(0.3, 0.7)
        y2 = 0.10 + 0.8 * ((k + 1) % 3) / 3.0 + rng.uniform(-0.04, 0.04)
        pts = []
        for i in range(0, 241, 4):
            t = i / 240.0
            mt = 1 - t
            pts.append((mt * mt * 0.02 + 2 * mt * t * mx + t * t * 0.98,
                        mt * mt * y0 + 2 * mt * t * y1 + t * t * y2))
        out.append(pts)
    return out

CURVES = seam_curves(N_SEAMS) if N_SEAMS > 0 else []

def dist_to_curve(xn, yn, curve):
    best = 1e18
    for (cx, cy) in curve:
        d = (xn - cx) ** 2 + (yn - cy) ** 2
        if d < best:
            best = d
    return math.sqrt(best)

def motif_field(xn, yn):
    if MOTIF_PATHS <= 0 or MOTIF_H <= 0.0:
        return 0.0
    h = 0.0
    for k in range(MOTIF_PATHS):
        off = (k - (MOTIF_PATHS - 1) / 2.0) * 0.16
        t = yn
        path_x = 0.5 + off + 0.22 * math.sin(t * math.pi * 1.6 + 0.4 + k)
        d = xn - path_x
        along = (t + k * 0.13) * TILE
        phase = (along % MOTIF_PERIOD) / MOTIF_PERIOD
        motif = (math.sin(phase * math.pi * 2.0) ** 2) * (math.cos(d * 40.0) ** 2)
        gate = math.exp(-(d ** 2) / 0.0012)
        h += MOTIF_H * motif * gate
    return h

ca = math.cos(PLEAT_ANGLE)
sa = math.sin(PLEAT_ANGLE)

rows = []
for j in range(GRID + 1):
    row = []
    for i in range(GRID + 1):
        xn = i / GRID
        yn = j / GRID
        x = xn * TILE
        # pleat coordinate: rotate the strata axis by PLEAT_ANGLE
        u = x * ca + yn * TILE * sa
        # amplitude modulation: strata fade in and out along strike (v0.1 fix)
        env = 0.55 + 0.45 * vnoise(xn * 0.8 + 3.1, yn * 0.8 + 7.7)
        # phase warp: strata curve instead of running ruler-straight (v0.1 fix)
        warp_phase = WARP * 3.0 * vnoise(xn * 0.5 + 13.7, yn * 0.5 + 2.9)
        strata = math.sin((u / PLEAT_PERIOD) * math.pi + warp_phase)
        pleat = PLEAT_AMP * env * (abs(strata) ** 0.7) \
            * (0.75 + 0.25 * vnoise(xn * 2.0, yn * 2.0))
        drape = BASE_H * (0.5 + 0.5 * vnoise(xn * 1.4 + 11.2, yn * 1.4 + 5.5)) \
            + 0.35 * BASE_H * vnoise(xn * 3.7, yn * 3.7)
        seam = 0.0
        for c in CURVES:
            d = dist_to_curve(xn, yn, c) * TILE
            v = SEAM_DEPTH * math.exp(-(d * d) / (SEAM_WIDTH * SEAM_WIDTH))
            if ROAD_FLAT:
                # carve a road: flat floor at depth, hard shoulders
                if d < SEAM_WIDTH * 0.55:
                    v = SEAM_DEPTH
                elif d < SEAM_WIDTH * 0.8:
                    v = SEAM_DEPTH * (1.0 - (d - SEAM_WIDTH * 0.55) / (SEAM_WIDTH * 0.25))
                else:
                    v = 0.0
            lip = SEAM_DEPTH * 0.18 * math.exp(-((d - SEAM_WIDTH * 2.2) ** 2) / (SEAM_WIDTH * SEAM_WIDTH)) \
                if SEAM_DEPTH > 0 else 0.0
            seam += -v + lip
        h = drape + pleat + seam + motif_field(xn, yn)
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
    entries = []
    for spec in TILES:
        name = spec["name"]
        for old in [n for n in obj.children() if n.name() == f"FM_{name}"]:
            old.destroy()
        g = obj.createNode("geo", f"FM_{name}", run_init_scripts=True)
        py = g.createNode("python", "gen")
        code = _inject(CODE, SEED=SEED, TILE=2000.0, GRID=spec["grid"],
                       BASE_H=spec["base_h"], PLEAT_AMP=spec["pleat_amp"],
                       PLEAT_PERIOD=spec["pleat_period"],
                       PLEAT_ANGLE=math.radians(spec["pleat_angle_deg"]),
                       WARP=spec["warp"], N_SEAMS=spec["seams"],
                       SEAM_DEPTH=spec["seam_depth"], SEAM_WIDTH=spec["seam_width"],
                       ROAD_FLAT=spec.get("road_flat", False),
                       MOTIF_PATHS=spec["motif_paths"], MOTIF_H=spec["motif_h"],
                       MOTIF_PERIOD=spec["motif_period"])
        py.parm("python").set(code)
        try:
            py.cook(force=True)
        except Exception:
            pass
        err = " ".join(str(py.errors()).split()) if py.errors() else ""
        if err:
            print(f"[suite] {name} NODE ERROR: {err[:300]}")
            g.destroy()
            continue
        geo = py.geometry()

        # heights for the r16 export (single points() call — O(n), not O(n^2))
        all_pts = geo.points()
        heights = []
        for j in range(spec["grid"] + 1):
            row = [all_pts[j * (spec["grid"] + 1) + i].position().y()
                   for i in range(spec["grid"] + 1)]
            heights.append(row)

        obj_path = OUT_DIR / f"SM_FM_{name}.obj"
        sop = g.createNode("file", "write_obj")
        sop.parm("file").set(str(obj_path))
        sop.parm("filemode").set("write")
        sop.setInput(0, py)
        try:
            sop.cook(force=True)
        except Exception:
            pass
        obj_ok = obj_path.exists()

        r16_bytes, hlo, hhi = _heights(heights)
        r16_path = OUT_DIR / f"HM_FM_{name}.r16"
        r16_path.write_bytes(r16_bytes)

        entries.append({
            "tile": name, "bible_beat": spec["name"],
            "obj": str(obj_path), "obj_written": obj_ok,
            "obj_bytes": obj_path.stat().st_size if obj_ok else 0,
            "points": len(geo.points()), "faces": len(geo.prims()),
            "heightmap": {"path": str(r16_path), "format": "r16 LE uint16",
                          "size": f"{spec['grid'] + 1}x{spec['grid'] + 1}",
                          "h_min_m": round(hlo, 2), "h_max_m": round(hhi, 2)},
            "spec": {k: v for k, v in spec.items()},
        })
        print(f"[suite] {name}: {len(geo.points())} pts, obj={obj_ok}, "
              f"r16={r16_path.stat().st_size} bytes")
        g.destroy()

    manifest = {
        "schema": "melodia.faraway_mother_terrain.v1",
        "kind": "cloth-terrain suite v0.1 (five biome tiles, Bible beat order)",
        "seed": SEED,
        "tiles": entries,
        "hython": hou.applicationVersionString(),
        "ue_import": {"mesh_scale": "100x (m -> cm)", "nanite": True,
                      "heightmap": "Landscape import: .r16, dimensions from manifest, "
                                   "scale Z from h_min/h_max"},
        "bible_source": "MONOLITH_LEVEL_DESIGN_BIBLE_2026-08-26.md #10",
    }
    (OUT_DIR / "terrain_suite_v01_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[suite] manifest -> terrain_suite_v01_manifest.json ({len(entries)} tiles)")


def _heights(heights):
    import struct
    lo = min(min(r) for r in heights)
    hi = max(max(r) for r in heights)
    span = (hi - lo) or 1.0
    out = bytearray()
    for r in heights:
        for h in r:
            out += struct.pack("<H", int(round((h - lo) / span * 65535.0)))
    return bytes(out), lo, hi


if __name__ == "__main__":
    main()
