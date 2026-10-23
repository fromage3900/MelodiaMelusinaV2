r"""render_frill_arch.py -- clay review renders of HDA_Faraway_FrillArch (hython 22.0.368).

Reuses the z-buffer rasteriser in render_review_clay.py (back faces paint magenta, so inverted shells are visible).
Usage: hython Tools/Houdini/faraway/render_frill_arch.py [--tag NAME] [--set parm=val ...]
Output: Saved/Audit/faraway_hda/frill_arch/<tag>_<view>.png
"""
import argparse
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import render_review_clay as rr  # noqa: E402

OUT = rr.ROOT / "Saved" / "Audit" / "faraway_hda" / "frill_arch"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="frill")
    ap.add_argument("--set", nargs="*")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    inst, g = rr.cook("HDA_Faraway_FrillArch", rr.ROOT / "hda" / "HDA_Faraway_FrillArch_1.0.hda", rr.parse_sets(a.set))
    tris, nr = rr.collect(g, smooth=False)
    P = np.array([p.position() for p in g.points()])
    lo, hi = P.min(0), P.max(0)
    c = (lo + hi) / 2
    print(f"[R] frill bbox {lo.round(2)} .. {hi.round(2)} tris={len(tris)}")
    views = {
        "front": ((c[0], c[1], hi[2] + 11.0), c),
        "q34": ((c[0] + 6.5, c[1] + 2.5, hi[2] + 8.5), c),
        "rosette": ((0.0, hi[1] - 0.2, hi[2] + 3.2), (0.0, hi[1] - 0.2, hi[2])),
    }
    for name, (eye, tgt) in views.items():
        im = rr.raster(tris, nr, eye, tgt, 1000, 800, fov_deg=35.0 if name != "rosette" else 30.0)
        f = OUT / f"{a.tag}_{name}.png"
        im.save(f)
        print("[R] wrote", f)


if __name__ == "__main__":
    main()
