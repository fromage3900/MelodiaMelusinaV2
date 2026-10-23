r"""render_review_clay.py -- headless clay review renders of the Faraway HDAs (hython 22.0.368).

Mantra here is slow and watermarked, and the OpenGL ROP segfaults without a GPU
(Docs/Houdini/HYTHON_HEADLESS_RENDER_FACTS_2026-10-05.md), so this is a small numpy
z-buffer rasteriser over the HDA's real cooked geometry. Shading uses Houdini's own
prim.normal() (outward = front). Any visible BACK-facing fragment is painted magenta,
which exposes inverted faces / see-through shells directly.

Usage:
  hython Tools/Houdini/faraway/render_review_clay.py gate  [--tag NAME] [--set parm=val ...]
  hython Tools/Houdini/faraway/render_review_clay.py peak  [--tag NAME] [--tile X Y] [--set parm=val ...]
Output: Saved/Audit/faraway_hda/review/<tag>_<view>.png
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "Saved" / "Audit" / "faraway_hda" / "review"


def lookat(eye, tgt, up=(0, 1, 0)):
    eye = np.array(eye, float); tgt = np.array(tgt, float)
    f = tgt - eye; f /= np.linalg.norm(f)
    r = np.cross(f, np.array(up, float)); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return eye, r, u, f


def raster(tris, nrm_v, eye, tgt, W, H, fov_deg=35.0, ortho=None, ss=2, bg=(226, 228, 232), light_dirs=None, up=(0, 1, 0)):
    """tris (T,3,3); nrm_v (T,3,3) per-corner outward normals. Returns RGB uint8."""
    eye, r, u, f = lookat(eye, tgt, up)
    Ws, Hs = W * ss, H * ss
    rel = tris - eye
    xc = rel @ r; yc = rel @ u; zc = rel @ f
    if ortho:
        sx = xc / ortho * 0.5 * Hs + Ws * 0.5
        sy = Hs * 0.5 - yc / ortho * 0.5 * Hs
        dep = zc
    else:
        fl = 0.5 * Hs / math.tan(math.radians(fov_deg) * 0.5)
        zz = np.maximum(zc, 1e-3)
        sx = xc / zz * fl + Ws * 0.5
        sy = Hs * 0.5 - yc / zz * fl
        dep = zc
    zb = np.full((Hs, Ws), np.inf, np.float64)
    img = np.empty((Hs, Ws, 3), np.float64)
    img[:] = np.array(bg, float)
    # lights (world dirs pointing TOWARD light)
    if light_dirs is None:
        light_dirs = [((-0.5, 0.8, 0.6), 0.85, (1.0, 0.97, 0.92)), ((0.7, 0.3, -0.4), 0.30, (0.8, 0.88, 1.0))]
    ld = [(np.array(d, float) / np.linalg.norm(d), k, np.array(c, float)) for d, k, c in light_dirs]
    clay = np.array([196, 184, 170], float)
    back = np.array([230, 0, 200], float)
    fc = tris.mean(axis=1) - eye
    for t in range(len(tris)):
        if np.any(zc[t] <= 1e-3):
            continue
        x = sx[t]; y = sy[t]
        x0 = max(int(math.floor(x.min())), 0); x1 = min(int(math.ceil(x.max())), Ws - 1)
        y0 = max(int(math.floor(y.min())), 0); y1 = min(int(math.ceil(y.max())), Hs - 1)
        if x1 < x0 or y1 < y0:
            continue
        den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if abs(den) < 1e-12:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        l0 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / den
        l1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / den
        l2 = 1.0 - l0 - l1
        m = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        if not m.any():
            continue
        d = l0 * dep[t, 0] + l1 * dep[t, 1] + l2 * dep[t, 2]
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        win = m & (d < sub)
        if not win.any():
            continue
        n = (l0[..., None] * nrm_v[t, 0] + l1[..., None] * nrm_v[t, 1] + l2[..., None] * nrm_v[t, 2])
        n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
        vdir = -fc[t] / np.linalg.norm(fc[t]) if not ortho else -f
        facing = float(np.dot(np.mean(nrm_v[t], axis=0), vdir))
        amb = 0.30 + 0.18 * n[..., 1]          # hemisphere ambient, brighter facing sky
        col = amb[..., None] * clay * np.array([0.9, 0.93, 1.0])
        for dvec, k, c in ld:
            col = col + (np.clip(n @ dvec, 0, 1) * k)[..., None] * clay * c
        if facing < 0:
            col = col * 0.3 + back * 0.7
        col = np.clip(col, 0, 255)
        sub[win] = d[win]
        img[y0:y1 + 1, x0:x1 + 1][win] = col[win]
    im = Image.fromarray(img.astype(np.uint8)).resize((W, H), Image.LANCZOS)
    return im


def collect(geom, smooth):
    """Triangulate a hou.Geometry. smooth -> use point 'N' (if present) else prim normal."""
    tris = []; nrms = []
    has_n = geom.findPointAttrib("N") is not None
    for pr in geom.prims():
        vs = [v.point() for v in pr.vertices()]
        if len(vs) < 3:
            continue
        pn = tuple(pr.normal())
        P = [tuple(p.position()) for p in vs]
        N = [tuple(p.attribValue("N")) if (smooth and has_n) else pn for p in vs]
        for i in range(1, len(vs) - 1):
            tris.append([P[0], P[i], P[i + 1]])
            nrms.append([N[0], N[i], N[i + 1]])
    return np.array(tris, float), np.array(nrms, float)


def cook(type_name, hda, sets):
    import hou
    hou.hda.installFile(str(hda))
    inst = hou.node("/obj").createNode(type_name, "review_" + type_name)
    for k, v in sets.items():
        p = inst.parm(k)
        if p is None:
            raise SystemExit(f"no parm {k}")
        p.set(v)
    inst.cook(force=True)
    out = inst.node("output0")
    g = out.geometry()
    if g is None:
        raise SystemExit("output0 did not cook: " + repr([e for c in inst.allSubChildren() for e in c.errors()]))
    return inst, g


def parse_sets(items):
    d = {}
    for s in items or []:
        k, v = s.split("=")
        d[k] = float(v) if "." in v or "e" in v.lower() else int(v)
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["gate", "peak"])
    ap.add_argument("--tag", default=None)
    ap.add_argument("--tile", nargs=2, type=float)
    ap.add_argument("--set", nargs="*")
    ap.add_argument("--w", type=int, default=1100)
    ap.add_argument("--h", type=int, default=800)
    ap.add_argument("--view", nargs="*")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    sets = parse_sets(a.set)
    W, H = a.w, a.h
    if a.what == "gate":
        tag = a.tag or "gate"
        inst, g = cook("HDA_Faraway_HeartGate", ROOT / "hda" / "HDA_Faraway_HeartGate_1.0.hda", sets)
        tris, nr = collect(g, smooth=False)
        P = np.array([p.position() for p in g.points()])
        lo, hi = P.min(0), P.max(0)
        c = (lo + hi) / 2
        print(f"[R] gate bbox {lo.round(2)} .. {hi.round(2)} tris={len(tris)}")
        views = {
            "front": ((c[0], c[1], hi[2] + 14.0), c, None),
            "q34": ((c[0] + 9.0, c[1] + 4.0, hi[2] + 11.0), c, None),
            "side": ((c[0] + 14.0, c[1], c[2]), c, None),
            "heartclose": ((c[0], hi[1] * 0.75, hi[2] + 5.0), (0, hi[1] * 0.72, 0), None),
        }
        for name, (eye, tgt, ortho) in views.items():
            if a.view and name not in a.view:
                continue
            im = raster(tris, nr, eye, tgt, W, H, fov_deg=35.0 if name != "heartclose" else 30.0)
            f = OUT / f"{tag}_{name}.png"
            im.save(f)
            print("[R] wrote", f)
    else:
        tag = a.tag or "peak"
        if a.tile:
            sets["tile_x"] = float(a.tile[0]); sets["tile_y"] = float(a.tile[1])
        inst, g = cook("HDA_Faraway_SilkPeak", ROOT / "hda" / "HDA_Faraway_SilkPeak_1.0.hda", sets)
        tris, nr = collect(g, smooth=True)
        P = np.array([p.position() for p in g.points()])
        lo, hi = P.min(0), P.max(0)
        c = (lo + hi) / 2
        ts = max(hi[0] - lo[0], hi[2] - lo[2])
        print(f"[R] tile bbox {lo.round(1)} .. {hi.round(1)} tris={len(tris)} relief={hi[1]-lo[1]:.1f}")
        tgt = (c[0], lo[1] + (hi[1] - lo[1]) * 0.35, c[2])
        views = {
            "oblique": ((c[0] - 0.55 * ts, hi[1] + 0.45 * ts, c[2] + 0.95 * ts), tgt, None),
            "top": ((c[0], c[1] + 3.0 * ts, c[2] + 0.001), (c[0], c[1], c[2]), ts * 1.05),
            "lowside": ((c[0] - 0.9 * ts, hi[1] + 0.12 * ts, c[2] + 0.2 * ts), tgt, None),
        }
        for name, (eye, tg, ortho) in views.items():
            if a.view and name not in a.view:
                continue
            im = raster(tris, nr, eye, tg, W, H, fov_deg=40.0, ortho=ortho,
                        up=(0, 0, -1) if name == "top" else (0, 1, 0))
            f = OUT / f"{tag}_{name}.png"
            im.save(f)
            print("[R] wrote", f)


if __name__ == "__main__":
    main()
