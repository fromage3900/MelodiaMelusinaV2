r"""render_motherfold_basin_clay.py -- headless clay review of HDA_Faraway_MotherfoldBasin (hython 22.0.368).

Numpy z-buffer rasteriser over the HDA's real cooked geometry (Mantra/OpenGL ROP are unusable here, see
Docs/Houdini/HYTHON_HEADLESS_RENDER_FACTS_2026-10-05.md). Terrain is shaded with Houdini's own point N,
tinted turquoise by the exported @depth01 mask; the water quad is alpha-blended over it; the shoreline
polylines are drawn in red. Any BACK-facing terrain/water fragment is painted magenta.

  hython Tools/Houdini/faraway/render_motherfold_basin_clay.py [--set parm=val ...] [--tag NAME]
Output: Saved/Audit/faraway_hda/motherfold_basin/<tag>_{oblique,top,lowside}.png
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "Saved" / "Audit" / "faraway_hda" / "motherfold_basin"
sys.path.insert(0, str(HERE))
import render_review_clay as RC  # noqa: E402  (lookat only)


def project(P, eye, tgt, W, H, fov, ortho, up):
    eye, r, u, f = RC.lookat(eye, tgt, up)
    rel = np.asarray(P, float) - eye
    xc, yc, zc = rel @ r, rel @ u, rel @ f
    if ortho:
        sx = xc / ortho * 0.5 * H + W * 0.5
        sy = H * 0.5 - yc / ortho * 0.5 * H
    else:
        fl = 0.5 * H / math.tan(math.radians(fov) * 0.5)
        zz = np.maximum(zc, 1e-3)
        sx = xc / zz * fl + W * 0.5
        sy = H * 0.5 - yc / zz * fl
    return sx, sy, zc, f


def raster(tris, cols, nrm, zb, img, eye, tgt, fov, ortho, up, alpha=1.0, mark_back=True):
    Hs, Ws = zb.shape
    sx, sy, zc, f = project(tris.reshape(-1, 3), eye, tgt, Ws, Hs, fov, ortho, up)
    sx, sy, zc = sx.reshape(-1, 3), sy.reshape(-1, 3), zc.reshape(-1, 3)
    light = np.array([-0.5, 0.8, 0.6]); light /= np.linalg.norm(light)
    for t in range(len(tris)):
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
        n = l0[..., None] * nrm[t, 0] + l1[..., None] * nrm[t, 1] + l2[..., None] * nrm[t, 2]
        n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
        base = l0[..., None] * cols[t, 0] + l1[..., None] * cols[t, 1] + l2[..., None] * cols[t, 2]
        lam = 0.34 + 0.18 * n[..., 1] + 0.80 * np.clip(n @ light, 0, 1)
        col = np.clip(base * lam[..., None], 0, 255)
        if mark_back:
            vdir = -(tris[t].mean(axis=0) - np.asarray(eye, float)) if not ortho else None
            if ortho:
                vdir = -RC.lookat(eye, tgt, up)[3]
            if float(np.dot(nrm[t].mean(axis=0), vdir)) < 0:
                col = col * 0.3 + np.array([230, 0, 200.0]) * 0.7
        if alpha < 1.0:
            col = img[y0:y1 + 1, x0:x1 + 1] * (1 - alpha) + col * alpha
            img[y0:y1 + 1, x0:x1 + 1][win] = col[win]
        else:
            sub[win] = d[win]
            img[y0:y1 + 1, x0:x1 + 1][win] = col[win]


def main():
    import hou

    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="default")
    ap.add_argument("--set", nargs="*")
    ap.add_argument("--w", type=int, default=1000)
    ap.add_argument("--h", type=int, default=720)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    hou.hda.installFile(str(ROOT / "hda" / "HDA_Faraway_MotherfoldBasin_1.0.hda"))
    inst = hou.node("/obj").createNode("HDA_Faraway_MotherfoldBasin", "render_mb")
    for s in a.set or []:
        k, v = s.split("=")
        inst.parm(k).set(float(v) if "." in v else int(v))
    inst.cook(force=True)
    g0, g1, g2 = (inst.node(f"output{i}").geometry() for i in range(3))
    if g0 is None or g1 is None or g2 is None:
        raise SystemExit("an output did not cook")

    P = np.array(g0.pointFloatAttribValues("P")).reshape(-1, 3)
    D = np.array(g0.pointFloatAttribValues("depth01"))
    idx = []
    N = np.zeros_like(P)  # smooth point normals = area-agnostic mean of Houdini's own prim.normal()
    for pr in g0.prims():
        v = [x.point().number() for x in pr.vertices()]
        idx.append([v[0], v[1], v[2]]); idx.append([v[0], v[2], v[3]])
        for q in v:
            N[q] += np.array(pr.normal())
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-9)
    idx = np.array(idx)
    tris, nrm = P[idx], N[idx]
    clay = np.array([204, 190, 172.0]); turq = np.array([70, 190, 196.0])
    vc = clay[None, :] * (1 - D[:, None]) + turq[None, :] * D[:, None]
    cols = vc[idx]
    wy = g2.floatAttribValue("water_level")
    wp = np.array([p.position() for p in g2.points()])
    wtris = np.array([[wp[0], wp[1], wp[2]], [wp[0], wp[2], wp[3]]])
    wn = np.tile(np.array([0, 1, 0.0]), (2, 3, 1))
    wc = np.tile(np.array([40, 205, 215.0]), (2, 3, 1))
    shore = [[tuple(v.point().position()) for v in pr.vertices()] for pr in g1.prims()]
    lo, hi = P.min(0), P.max(0)
    c = (lo + hi) / 2
    ts = max(hi[0] - lo[0], hi[2] - lo[2])
    print(f"[R] tile {lo.round(1)}..{hi.round(1)} water level {wy:.2f} tris={len(tris)} shoreline chains={len(shore)}")
    tgt = (c[0], wy - 2.0, c[2])
    views = {
        "oblique": ((c[0] - 0.40 * ts, hi[1] + 0.34 * ts, c[2] + 0.80 * ts), tgt, None, (0, 1, 0)),
        "top": ((c[0], c[1] + 3.0 * ts, c[2] + 0.001), (c[0], c[1], c[2]), ts * 1.05, (0, 0, -1)),
        "lowside": ((c[0] - 0.85 * ts, hi[1] + 0.07 * ts, c[2] + 0.25 * ts), tgt, None, (0, 1, 0)),
    }
    ss = 2
    for name, (eye, tg, ortho, up) in views.items():
        Ws, Hs = a.w * ss, a.h * ss
        zb = np.full((Hs, Ws), np.inf)
        img = np.empty((Hs, Ws, 3)); img[:] = np.array([226, 228, 232.0])
        raster(tris, cols, nrm, zb, img, eye, tg, 38.0, ortho, up)
        raster(wtris, wc, wn, zb, img, eye, tg, 38.0, ortho, up, alpha=0.5)
        im = Image.fromarray(img.astype(np.uint8)).resize((a.w, a.h), Image.LANCZOS)
        dr = ImageDraw.Draw(im)
        for ch in shore:
            sx, sy, zc, _ = project(np.array(ch), eye, tg, a.w, a.h, 38.0, ortho, up)
            pts = [(float(x), float(y)) for x, y, z in zip(sx, sy, zc) if z > 1e-3]
            if len(pts) > 1:
                dr.line(pts + ([pts[0]] if len(pts) == len(ch) and len(ch) > 2 else []), fill=(200, 30, 40), width=3)
        f = OUT / f"{a.tag}_{name}.png"
        im.save(f)
        print("[R] wrote", f, f.stat().st_size)


if __name__ == "__main__":
    main()
