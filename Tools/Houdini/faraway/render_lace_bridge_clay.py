r"""render_lace_bridge_clay.py -- clay review renders of HDA_Faraway_LaceBridge (hython 22.0.368).

Reuses the numpy z-buffer rasteriser in render_review_clay.py (Mantra is slow/watermarked and the
OpenGL ROP segfaults headless -- Docs/Houdini/HYTHON_HEADLESS_RENDER_FACTS_2026-10-05.md).
Back-facing fragments paint magenta, exposing inverted faces.

  hython Tools/Houdini/faraway/render_lace_bridge_clay.py [--tag NAME] [--curve] [--set parm=val ...]
Output: Saved/Audit/faraway_hda/lace_bridge/<tag>_<view>.png
"""
import argparse
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import render_review_clay as rr  # noqa: E402

ROOT = HERE.parents[2]
OUT = ROOT / "Saved" / "Audit" / "faraway_hda" / "lace_bridge"
HDA = ROOT / "hda" / "HDA_Faraway_LaceBridge_1.0.hda"


def main():
    import hou
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="bridge")
    ap.add_argument("--curve", action="store_true", help="feed a dog-leg curve into input 0")
    ap.add_argument("--set", nargs="*")
    ap.add_argument("--w", type=int, default=1100)
    ap.add_argument("--h", type=int, default=720)
    ap.add_argument("--view", nargs="*")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    hou.hda.installFile(str(HDA))
    inst = hou.node("/obj").createNode("HDA_Faraway_LaceBridge", "review_bridge")
    for k, v in rr.parse_sets(a.set).items():
        inst.parm(k).set(v)
    if a.curve:
        cg = hou.node("/obj").createNode("geo", "curve_src")
        for c in cg.children():
            c.destroy()
        py = cg.createNode("python", "mk")
        py.parm("python").set(
            "import hou\ng=hou.pwd().geometry()\n"
            "pts=[(-9,0,-3),(-4,0,1),(2,0,-2),(7,0,4),(10,0,5)]\n"
            "ps=[g.createPoint() for _ in pts]\n"
            "for p,q in zip(ps,pts): p.setPosition(hou.Vector3(q))\n"
            "pr=g.createPolygon(); pr.setIsClosed(False)\n"
            "for p in ps: pr.addVertex(p)\n")
        py.setDisplayFlag(True)
        py.setRenderFlag(True)
        inst.setInput(0, cg)
    inst.cook(force=True)
    g = inst.node("output0").geometry()
    if g is None:
        raise SystemExit("no geometry: " + repr([e for c in inst.allSubChildren() for e in c.errors()]))
    tris, nr = rr.collect(g, smooth=False)
    P = np.array([p.position() for p in g.points()])
    lo, hi = P.min(0), P.max(0)
    c = (lo + hi) / 2
    ext = float(np.linalg.norm(hi - lo))
    print(f"[R] bbox {lo.round(2)} .. {hi.round(2)} tris={len(tris)} prims={len(g.prims())}")
    views = {
        "q34": ((c[0] - 0.55 * ext, c[1] + 0.28 * ext, c[2] + 0.75 * ext), c, None),
        "side": ((c[0], c[1] + 0.05 * ext, c[2] + 1.1 * ext), c, None),
        "under": ((c[0] - 0.35 * ext, lo[1] - 0.05 * ext, c[2] + 0.55 * ext), (c[0], c[1] + 0.1 * ext, c[2]), None),
        "top": ((c[0], c[1] + 3.0 * ext, c[2] + 0.001), c, ext * 0.75),
    }
    for name, (eye, tgt, ortho) in views.items():
        if a.view and name not in a.view:
            continue
        im = rr.raster(tris, nr, eye, tgt, a.w, a.h, fov_deg=35.0, ortho=ortho,
                       up=(0, 0, -1) if name == "top" else (0, 1, 0))
        f = OUT / f"{a.tag}_{name}.png"
        im.save(f)
        print("[R] wrote", f)


if __name__ == "__main__":
    main()
