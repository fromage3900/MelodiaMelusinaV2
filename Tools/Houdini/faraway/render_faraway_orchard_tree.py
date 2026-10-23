r"""render_faraway_orchard_tree.py -- headless clay-colour review renders of the Listening Orchard Tree (hython).

numpy z-buffer rasteriser over the HDA's real cooked geometry (same approach as render_review_clay.py:
Mantra is slow/watermarked here, OpenGL ROP needs a GPU). Colour is per piece (bark / blossom cards /
canopy proxy); shading uses Houdini's own prim.normal(). A visible BACK face of a closed solid is
painted magenta (exposes inverted faces); cards are two-sided by design and shaded either way.

Usage:
  hython Tools/Houdini/faraway/render_faraway_orchard_tree.py [--set parm=val ...] [--tag NAME]
Output: Saved/Audit/faraway_hda/orchard_tree/<tag>_<view>.png
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
OUT = ROOT / "Saved" / "Audit" / "faraway_hda" / "orchard_tree"
TYPE_NAME = "HDA_Faraway_ListeningOrchardTree"

COLORS = {
    "trunk": (118, 84, 66), "root": (104, 74, 58), "branch": (126, 92, 74),
    "blossom_cards": (246, 168, 196), "canopy_proxy": (222, 150, 178),
}


def lookat(eye, tgt, up=(0, 1, 0)):
    eye = np.array(eye, float); tgt = np.array(tgt, float)
    f = tgt - eye; f /= np.linalg.norm(f)
    r = np.cross(f, np.array(up, float)); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return eye, r, u, f


def raster(tris, nrm, cols, two_sided, eye, tgt, W, H, fov=35.0, ss=2, bg=(222, 226, 234)):
    eye, r, u, f = lookat(eye, tgt)
    Ws, Hs = W * ss, H * ss
    rel = tris - eye
    xc, yc, zc = rel @ r, rel @ u, rel @ f
    fl = 0.5 * Hs / math.tan(math.radians(fov) * 0.5)
    zz = np.maximum(zc, 1e-3)
    sx = xc / zz * fl + Ws * 0.5
    sy = Hs * 0.5 - yc / zz * fl
    zb = np.full((Hs, Ws), np.inf)
    img = np.empty((Hs, Ws, 3)); img[:] = np.array(bg, float)
    # gentle vertical gradient background
    grad = np.linspace(1.04, 0.94, Hs)[:, None, None]
    img = np.clip(img * grad, 0, 255)
    lights = [(np.array((-0.5, 0.8, 0.6)) / 1.1, 0.85, np.array((1.0, 0.97, 0.92))),
              (np.array((0.7, 0.3, -0.4)) / 0.9, 0.30, np.array((0.8, 0.88, 1.0)))]
    back = np.array([230, 0, 200], float)
    order = np.argsort(-zc.mean(axis=1))  # far first (z-buffer anyway)
    for t in order:
        if np.any(zc[t] <= 1e-3):
            continue
        x, y = sx[t], sy[t]
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
        d = l0 * zc[t, 0] + l1 * zc[t, 1] + l2 * zc[t, 2]
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        win = m & (d < sub)
        if not win.any():
            continue
        n = (l0[..., None] * nrm[t, 0] + l1[..., None] * nrm[t, 1] + l2[..., None] * nrm[t, 2])
        n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
        vdir = -(tris[t].mean(axis=0) - eye)
        vdir /= np.linalg.norm(vdir)
        facing = float(np.dot(nrm[t].mean(axis=0), vdir))
        if facing < 0 and two_sided[t]:
            n = -n
        amb = 0.32 + 0.20 * n[..., 1]
        base = np.array(cols[t], float)
        col = amb[..., None] * base
        for dv, k, c in lights:
            nl = n @ dv
            if two_sided[t]:
                nl = 0.5 + 0.5 * nl   # wrap lighting: translucent blossom cards never go black
            col = col + (np.clip(nl, 0, 1) * k)[..., None] * base * c
        if facing < 0 and not two_sided[t]:
            col = col * 0.3 + back * 0.7
        sub[win] = d[win]
        img[y0:y1 + 1, x0:x1 + 1][win] = np.clip(col, 0, 255)[win]
    return Image.fromarray(img.astype(np.uint8)).resize((W, H), Image.LANCZOS)


def collect(geom, only=None, skip=None):
    tris, nrm, cols, two = [], [], [], []
    has_n = geom.findPointAttrib("N") is not None
    for pr in geom.prims():
        piece = pr.attribValue("piece")
        if only and piece not in only:
            continue
        if skip and piece in skip:
            continue
        vs = [v.point() for v in pr.vertices()]
        pn = tuple(pr.normal())
        P = [tuple(p.position()) for p in vs]
        N = [tuple(p.attribValue("N")) if (has_n and piece != "blossom_cards") else pn for p in vs]
        tint = pr.attribValue("blossom_tint")
        base = COLORS.get(piece, (200, 200, 200))
        if piece == "blossom_cards":
            base = tuple(min(255, int(c * (0.88 + 0.14 * tint))) for c in base)
        for i in range(1, len(vs) - 1):
            tris.append([P[0], P[i], P[i + 1]]); nrm.append([N[0], N[i], N[i + 1]])
            cols.append(base); two.append(piece == "blossom_cards")
    return np.array(tris, float), np.array(nrm, float), cols, two


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="default")
    ap.add_argument("--set", nargs="*")
    ap.add_argument("--w", type=int, default=1000)
    ap.add_argument("--h", type=int, default=800)
    ap.add_argument("--view", nargs="*")
    a = ap.parse_args()
    import hou
    hou.hda.installFile(str(ROOT / "hda" / "HDA_Faraway_ListeningOrchardTree_1.0.hda"))
    inst = hou.node("/obj").createNode(TYPE_NAME, "review_orchard")
    for s in a.set or []:
        k, v = s.split("=")
        inst.parm(k).set(float(v) if "." in v else int(v))
    inst.cook(force=True)
    g = inst.node("output0").geometry()
    if g is None:
        raise SystemExit("output0 did not cook: " + repr([e for c in inst.allSubChildren() for e in c.errors()]))
    OUT.mkdir(parents=True, exist_ok=True)
    P = np.array([p.position() for p in g.points()])
    lo, hi = P.min(0), P.max(0)
    print(f"[R] bbox {lo.round(2)} .. {hi.round(2)}")
    cy = (lo[1] + hi[1]) * 0.5
    ext = max(hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2])
    D = ext * 1.9
    views = {
        # name: (eye, target, only, skip)
        "front": ((0, cy, D), (0, cy, 0), None, {"canopy_proxy"}),
        "q34": ((D * 0.72, cy + ext * 0.12, D * 0.72), (0, cy, 0), None, {"canopy_proxy"}),
        "bare": ((D * 0.72, cy + ext * 0.1, D * 0.72), (0, cy, 0), {"trunk", "root", "branch"}, None),
        "trunk": ((3.2, 1.4, 4.2), (0, 1.3, 0), {"trunk", "root", "branch"}, None),
        "proxy": ((D * 0.72, cy + ext * 0.12, D * 0.72), (0, cy, 0), {"trunk", "root", "canopy_proxy"}, None),
        "top": ((0.01, D * 1.2, 0.01), (0, 3.0, 0), None, {"canopy_proxy"}),
    }
    for name, (eye, tgt, only, skip) in views.items():
        if a.view and name not in a.view:
            continue
        tris, nrm, cols, two = collect(g, only, skip)
        fov = 35.0 if name != "trunk" else 40.0
        im = raster(tris, nrm, cols, two, eye, tgt, a.w, a.h, fov=fov)
        if name == "top":
            pass
        f = OUT / f"{a.tag}_{name}.png"
        im.save(f)
        print("[R] wrote", f, "tris", len(tris))


if __name__ == "__main__":
    main()
