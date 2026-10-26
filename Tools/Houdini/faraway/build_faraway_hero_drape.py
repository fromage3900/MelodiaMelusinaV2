r"""build_faraway_hero_drape.py -- Faraway Mother hero silk drape (hython 22.0.368). spike: true

Closes the open item in Docs/Houdini/FARAWAY_MOTHER_DRAPE_SPEC_2026-09-01.md ("scaffold, not yet cooked"):
a Vellum cloth sheet is dropped onto one cooked HDA_Faraway_SilkPeak tile (collision = the tile itself),
settled, and exported as a static hero mesh with tension / resonance attributes.

No UE, no editor. Outputs go to Saved/Staging/HoudiniForge/FarawayDrape_<stamp>/ (never Content/).

Usage: hython Tools/Houdini/faraway/build_faraway_hero_drape.py [--out DIR] [--frames N] [--res N] [--lift M]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HDA = ROOT / "hda" / "HDA_Faraway_SilkPeak_1.0.hda"
TYPE_NAME = "HDA_Faraway_SilkPeak"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "Saved" / "Staging" / "HoudiniForge" / "FarawayDrape_20261026"))
    ap.add_argument("--frames", type=int, default=90)
    ap.add_argument("--res", type=int, default=120, help="cloth grid divisions per side")
    ap.add_argument("--lift", type=float, default=6.0, help="start height above the tallest peak point (m)")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    import hou

    hou.hda.installFile(str(HDA))
    obj = hou.node("/obj")
    for n in ("FM_drape", "FM_peak"):
        if obj.node(n):
            obj.node(n).destroy()

    # 1. the terrain tile (collision + reference surface)
    peak = obj.createNode(TYPE_NAME, "FM_peak")
    peak.cook(force=True)
    geo = peak.displayNode().geometry()
    pts = geo.points()
    ys = [p.position()[1] for p in pts]
    xs = [p.position()[0] for p in pts]
    zs = [p.position()[2] for p in pts]
    top, bot = max(ys), min(ys)
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    print(f"PEAK pts={len(pts)} prims={len(geo.prims())} x[{x0:.1f},{x1:.1f}] z[{z0:.1f},{z1:.1f}] y[{bot:.2f},{top:.2f}]")
    peak_bgeo = out / "peak_tile.bgeo.sc"
    geo.saveToFile(str(peak_bgeo))

    # 2. cloth + solver network
    net = obj.createNode("geo", "FM_drape")
    col = net.createNode("file", "peak_collision")
    col.parm("file").set(str(peak_bgeo))

    w, d = (x1 - x0), (z1 - z0)
    grid = net.createNode("grid", "cloth_sheet")
    grid.parm("sizex").set(w * 0.96)
    grid.parm("sizey").set(d * 0.96)
    grid.parm("rows").set(a.res + 1)
    grid.parm("cols").set(a.res + 1)
    grid.parm("tx").set((x0 + x1) / 2)
    grid.parm("ty").set(top + a.lift)
    grid.parm("tz").set((z0 + z1) / 2)

    cons = net.createNode("vellumconstraints", "cloth_constraints")
    cons.setInput(0, grid)
    cons.setInput(1, grid)
    solver = net.createNode("vellumsolver", "cloth_solver")
    solver.setInput(0, cons, 0)
    solver.setInput(1, cons, 1)
    solver.setInput(2, col)
    solver.parm("substeps").set(4)
    solver.parm("startframe").set(1)

    out_null = net.createNode("null", "OUT_drape")
    out_null.setInput(0, solver, 0)
    out_null.setDisplayFlag(True)
    out_null.setRenderFlag(True)
    net.layoutChildren()

    errs = [(n.path(), n.errors()) for n in net.allSubChildren() if n.errors()]
    if errs:
        print("NETWORK_ERRORS", errs)

    # 3. settle
    hou.setFrame(1)
    for f in range(1, a.frames + 1):
        hou.setFrame(f)
        out_null.cook(force=False)
    g = out_null.geometry()
    cp = g.points()
    print(f"CLOTH frame={a.frames} pts={len(cp)} prims={len(g.prims())}")

    # 4. numeric collision / sanity gate: sample terrain height under each cloth point
    terr = peak.displayNode().geometry()
    import math
    tx = sorted(set(round(p.position()[0], 3) for p in terr.points()))
    tz = sorted(set(round(p.position()[2], 3) for p in terr.points()))
    nx, nz = len(tx), len(tz)
    hgt = {}
    for p in terr.points():
        q = p.position()
        hgt[(round(q[0], 3), round(q[2], 3))] = q[1]

    def terrain_h(x, z):
        # nearest-grid sample (terrain is a regular grid)
        ix = min(range(nx), key=lambda i: abs(tx[i] - x)) if nx < 600 else 0
        iz = min(range(nz), key=lambda i: abs(tz[i] - z)) if nz < 600 else 0
        return hgt.get((tx[ix], tz[iz]), 0.0)

    below = 0
    gaps = []
    for p in cp[:: max(1, len(cp) // 3000)]:
        q = p.position()
        th = terrain_h(q[0], q[2])
        gap = q[1] - th
        gaps.append(gap)
        if gap < -0.25:
            below += 1
    cy = [p.position()[1] for p in cp]
    gate = {
        "sampled": len(gaps),
        "below_terrain": below,
        "gap_min": round(min(gaps), 3),
        "gap_mean": round(sum(gaps) / len(gaps), 3),
        "gap_max": round(max(gaps), 3),
        "cloth_y_min": round(min(cy), 2),
        "cloth_y_max": round(max(cy), 2),
        "settled_below_start": round(top + a.lift - max(cy), 2),
        "nan_points": sum(1 for v in cy if v != v),
    }
    gate["cloth_y_span"] = round(max(cy) - min(cy), 3)
    gate["contact_points"] = sum(1 for v in gaps if v < 1.0)
    # a real drape: cloth is rippled by the terrain (span > 1 m), touches it, never penetrates, no NaNs
    gate["pass"] = bool(gate["below_terrain"] == 0 and gate["nan_points"] == 0 and gate["cloth_y_span"] > 1.0 and gate["contact_points"] > 50)
    print("GATE", json.dumps(gate))

    # 5. export (OBJ for the Hython contact + bgeo for UE import prep)
    obj_path = out / "SM_FabricRidge_Hero_drape.obj"
    bgeo_path = out / "SM_FabricRidge_Hero_drape.bgeo.sc"
    g.saveToFile(str(bgeo_path))
    try:
        g.saveToFile(str(obj_path))
    except Exception as exc:  # OBJ writer needs polygons only
        print("OBJ_WARN", exc)
    manifest = {
        "schema": "melodia.faraway_hero_drape.spike.v1",
        "spike": True,
        "houdini": hou.applicationVersionString(),
        "license": str(hou.licenseCategory()),
        "hda": str(HDA.relative_to(ROOT)),
        "frames": a.frames,
        "res": a.res,
        "lift_m": a.lift,
        "peak": {"pts": len(pts), "bounds_y": [bot, top]},
        "gate": gate,
        "files": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()[:16] for p in out.glob("*") if p.is_file()},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    hip = out / "FarawayDrape_hero.hiplc"
    hou.hipFile.save(str(hip))
    print("DONE", out)
    return 0 if gate["pass"] else 2


if __name__ == "__main__":
    sys.exit(main())
