r"""g1_stitch_proof.py -- Faraway Mother G1 lab proof (hython 22.0.368, Houdini-only, no UE).

Plan: "Harmonic Continental Genesis" (commit 90bfa88, Docs/Art/FARAWAY_MOTHER_FABRIC_MOUNTAIN_BUILD_2026-09-02.md).
Uses the EXISTING hda/HDA_Faraway_SilkPeak_1.0.hda and hda/HDA_Faraway_HeartGate_1.0.hda; neither is modified.

What it does
  1. Cooks FOUR adjacent 250 m SilkPeak tiles (2x2 = 500 x 500 m crop) in GLOBAL metres, 128 divisions each.
  2. Border proof: shared-edge POSITIONS (<= 0.01 m) and NORMALS (dot >= 0.98), three stated methods:
       A  tile exported vertex normal  vs  neighbour tile exported vertex normal   (what a halo-less import shows)
       B  tile exported vertex normal  vs  normal of a MERGED + FUSED mesh        (Houdini Normal SOP, same parms as
          the HDA's compute_normals node) -- PRIMARY gate method
       C  tile exported vertex normal  vs  ANALYTIC normal of the global height field (central differences,
          heights evaluated by the HDA's own VEX snippet run in a scratch wrangle, so no re-implementation error)
  3. Nodal seam F=0 of the Chladni field (n=3,m=5, global metres) by marching squares on a 0.5 m lattice, run per
     tile, welded across tile borders by shared lattice-edge keys, compared with a single whole-crop pass.
  4. Conforms the longest in-crop seam polyline to the terrain and places the Heart Gate straddling it.
  5. Writes acceptance.json (measured values, PASS/FAIL/BLOCKED, SHA-256), seam_graph.json, tiles_2x2/, hero_views/.

Houdini frame: Houdini (x, y, z) = world (X, Height, Y). Terrain is the XZ plane, +Y up.
Usage: hython Tools/Houdini/faraway/g1_stitch_proof.py [--no-render] [--gate-scale 4.0]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "Saved" / "Audit" / "faraway_g1"
SILK_HDA = ROOT / "hda" / "HDA_Faraway_SilkPeak_1.0.hda"
GATE_HDA = ROOT / "hda" / "HDA_Faraway_HeartGate_1.0.hda"
SILK_T, GATE_T = "HDA_Faraway_SilkPeak", "HDA_Faraway_HeartGate"

CROP_MIN = (-1150.0, -100.0)      # world X, Y of the crop's min corner; peak anchor (-900, 300) is inside (100 m below the top edge)
STRESS_MIN = (-850.0, 400.0)      # field-only 2nd crop: anti-diagonal nodal line X+Y=0 crosses both internal borders at 45 deg
TILE = 250.0
DIV = 128
CROP = 2 * TILE                   # 500 m
DX = TILE / DIV                   # 1.953125 m (exact in binary)
DS = 0.5                          # marching-squares lattice spacing (m)
CHL_N, CHL_M = 3, 5
T0 = time.time()


def log(*a):
    print(f"[G1 {time.time() - T0:6.1f}s]", *a, flush=True)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def mem_mb():
    """(peak working set, current working set) in MB, Windows."""
    try:
        import ctypes
        from ctypes import wintypes

        class PMC(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        k32, psapi = ctypes.windll.kernel32, ctypes.windll.psapi
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        psapi.GetProcessMemoryInfo(k32.GetCurrentProcess(), ctypes.byref(pmc), pmc.cb)
        return pmc.PeakWorkingSetSize / 2**20, pmc.WorkingSetSize / 2**20
    except Exception:
        return float("nan"), float("nan")


def chladni(X, Y):
    u = (np.asarray(X) + 4000.0) / 8000.0
    v = (np.asarray(Y) + 4000.0) / 8000.0
    return np.cos(CHL_N * np.pi * u) * np.cos(CHL_M * np.pi * v) - np.cos(CHL_M * np.pi * u) * np.cos(CHL_N * np.pi * v)


# ---------------------------------------------------------------------------------------------- Houdini helpers
def extract(geo):
    """Quad mesh arrays from a hou.Geometry: P (n,3), pv (f,4) point idx, vN (f,4,3) vertex normals, pn (f,3) prim normals."""
    P = np.array(geo.pointFloatAttribValues("P"), float).reshape(-1, 3)
    prims = geo.prims()
    if geo.findVertexAttrib("N") is not None:
        VN = np.array(geo.vertexFloatAttribValues("N"), float).reshape(-1, 3)
    else:   # analytic normals are a POINT attribute: every vertex of a point carries that point's N
        PN = np.array(geo.pointFloatAttribValues("N"), float).reshape(-1, 3)
        VN = np.zeros((sum(len(pr.vertices()) for pr in prims), 3))
        for pr in prims:
            for v in pr.vertices():
                VN[v.linearNumber()] = PN[v.point().number()]
    pv = np.empty((len(prims), 4), int)
    vl = np.empty((len(prims), 4), int)
    pn = np.empty((len(prims), 3), float)
    for i, pr in enumerate(prims):
        vs = pr.vertices()
        if len(vs) != 4:
            raise RuntimeError(f"non-quad prim {i}")
        for k, v in enumerate(vs):
            pv[i, k] = v.point().number()
            vl[i, k] = v.linearNumber()
        n = pr.normal()
        pn[i] = (n[0], n[1], n[2])
    return P, pv, VN[vl], pn


def point_normals(npts, pv, vN):
    acc = np.zeros((npts, 3))
    cnt = np.zeros(npts)
    for k in range(4):
        np.add.at(acc, pv[:, k], vN[:, k, :])
        np.add.at(cnt, pv[:, k], 1)
    return acc / np.maximum(np.linalg.norm(acc, axis=1, keepdims=True), 1e-12)


class Oracle:
    """Exact height field: runs the HDA's own `silk_field` VEX snippet on arbitrary global points."""

    def __init__(self, hou, inst):
        self.hou = hou
        geo = hou.node("/obj").createNode("geo", "g1_oracle")
        for c in geo.children():
            c.destroy()
        ctl = geo.createNode("null", "controls")
        grp = ctl.parmTemplateGroup()
        for name in ("height_scale", "pleat_wavelength", "pleat_depth", "pleat_angle", "phase_warp", "pleat_exponent",
                     "gather_length", "gather_floor", "seam_width", "seam_depth"):
            grp.append(hou.FloatParmTemplate(name, name, 1, default_value=(inst.parm(name).eval(),)))
        grp.append(hou.IntParmTemplate("seed", "seed", 1, default_value=(int(inst.parm("seed").eval()),)))
        ctl.setParmTemplateGroup(grp)
        self.py = geo.createNode("python", "pts")
        self.wr = geo.createNode("attribwrangle", "silk_field")
        self.wr.parm("class").set(2)
        self.wr.parm("snippet").set(inst.node("silk_field").parm("snippet").eval())
        self.wr.setInput(0, self.py)
        self.wr.setInput(1, ctl)
        self.n = 0

    def height(self, X, Y):
        import __main__
        X = np.asarray(X, float).ravel()
        Y = np.asarray(Y, float).ravel()
        pts = np.stack([X, np.zeros_like(X), Y], 1)
        __main__._G1_PTS = pts
        self.n += 1
        self.py.parm("python").set(
            "import __main__\ngeo = hou.pwd().geometry()\n"
            "geo.createPoints([tuple(r) for r in __main__._G1_PTS.tolist()])\n"
            f"# call {self.n}\n")
        self.wr.cook(force=True)
        g = self.wr.geometry()
        if g is None:
            raise RuntimeError(f"oracle wrangle failed: {self.wr.errors()} {self.py.errors()}")
        P = np.array(g.pointFloatAttribValues("P"), float).reshape(-1, 3)
        if len(P) != len(X):
            raise RuntimeError("oracle point count mismatch")
        return P[:, 1]


# ---------------------------------------------------------------------------------------------- marching squares
def ms_segments(F, I0, J0, X0, Y0, ds, tile_id, pos, key_tiles):
    """Marching squares on lattice samples F[j,i] at global nodes (I0+i, J0+j). Returns list of (keyA, keyB).
    Key = (0,I,J) horizontal lattice edge (I,J)->(I+1,J); (1,I,J) vertical edge (I,J)->(I,J+1)."""
    s = F >= 0.0
    a, b, c, d = s[:-1, :-1], s[:-1, 1:], s[1:, 1:], s[1:, :-1]
    mixed = ~((a == b) & (b == c) & (c == d))
    segs = []
    for j, i in zip(*np.nonzero(mixed)):
        Fa, Fb, Fc, Fd = F[j, i], F[j, i + 1], F[j + 1, i + 1], F[j + 1, i]
        sa, sb, sc, sd = Fa >= 0, Fb >= 0, Fc >= 0, Fd >= 0
        I, J = I0 + int(i), J0 + int(j)
        e = {}
        if sa != sb:
            t = Fa / (Fa - Fb); e[0] = ((0, I, J), (X0 + (I + t) * ds, Y0 + J * ds))
        if sb != sc:
            t = Fb / (Fb - Fc); e[1] = ((1, I + 1, J), (X0 + (I + 1) * ds, Y0 + (J + t) * ds))
        if sc != sd:
            t = Fd / (Fd - Fc); e[2] = ((0, I, J + 1), (X0 + (I + t) * ds, Y0 + (J + 1) * ds))
        if sd != sa:
            t = Fa / (Fa - Fd); e[3] = ((1, I, J), (X0 + I * ds, Y0 + (J + t) * ds))
        if len(e) == 2:
            pairs = [tuple(e.keys())]
        else:  # saddle
            cp = (Fa + Fb + Fc + Fd) * 0.25 >= 0.0
            pairs = [(0, 1), (2, 3)] if cp == sa else [(3, 0), (1, 2)]
        for p, q in pairs:
            kp, pp = e[p]
            kq, pq = e[q]
            for k, pt in ((kp, pp), (kq, pq)):
                if k in pos:
                    pos[k] = (pos[k][0], max(pos[k][1], math.hypot(pos[k][0][0] - pt[0], pos[k][0][1] - pt[1])))
                else:
                    pos[k] = (pt, 0.0)
                key_tiles.setdefault(k, set()).add(tile_id)
            segs.append((kp, kq))
    return segs


def trace_polylines(segs):
    adj = {}
    for a, b in segs:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    anomalies = [k for k, v in adj.items() if len(v) > 2]
    used = set()
    lines = []

    def walk(start):
        path = [start]
        prev, cur = None, start
        while True:
            nxt = None
            for n in adj[cur]:
                ek = frozenset((cur, n))
                if ek in used:
                    continue
                nxt = n
                used.add(ek)
                break
            if nxt is None:
                break
            path.append(nxt)
            prev, cur = cur, nxt
            if cur == start:
                break
        return path

    ends = [k for k, v in adj.items() if len(v) == 1]
    for k in ends:
        if all(frozenset((k, n)) in used for n in adj[k]):
            continue
        lines.append(walk(k))
    for k in adj:
        if any(frozenset((k, n)) not in used for n in adj[k]):
            lines.append(walk(k))
    return lines, adj, anomalies


def extract_seam(X0, Y0):
    """Marching squares per 250 m tile (global lattice), weld by shared edge keys, compare with a whole-crop pass."""
    NL = int(round(CROP / DS))          # 1000 cells
    nt = int(round(TILE / DS))          # 500 cells per tile
    pos, key_tiles, tile_segs = {}, {}, {}
    all_segs = []
    for r in range(2):
        for c in range(2):
            I0, J0 = c * nt, r * nt
            ii = I0 + np.arange(nt + 1); jj = J0 + np.arange(nt + 1)
            F = chladni(X0 + ii[None, :] * DS + 0 * jj[:, None], Y0 + jj[:, None] * DS + 0 * ii[None, :])
            segs = ms_segments(F, I0, J0, X0, Y0, DS, (c, r), pos, key_tiles)
            tile_segs[(c, r)] = len(segs)
            all_segs += segs
    ii = np.arange(NL + 1)
    Fref = chladni(X0 + ii[None, :] * DS + 0 * ii[:, None], Y0 + ii[:, None] * DS + 0 * ii[None, :])
    pos_ref, kt_ref = {}, {}
    ref_segs = ms_segments(Fref, 0, 0, X0, Y0, DS, "whole", pos_ref, kt_ref)
    set_tiles = {frozenset(s) for s in all_segs}
    set_ref = {frozenset(s) for s in ref_segs}
    sets_equal = set_tiles == set_ref
    weld_keys = [k for k, v in key_tiles.items() if len(v) > 1]
    weld_disc = max((pos[k][1] for k in pos), default=0.0)
    cross_tile_pos_dev = max((math.hypot(pos[k][0][0] - pos_ref[k][0][0], pos[k][0][1] - pos_ref[k][0][1]) for k in pos
                              if k in pos_ref), default=0.0)
    lines, adj, anomalies = trace_polylines(all_segs)
    bx = by = nt                          # internal border lattice index
    breaks, polys = [], []
    for pid, path in enumerate(lines):
        pts = np.array([pos[k][0] for k in path])
        closed = path[0] == path[-1] and len(path) > 2
        seglen = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        endpoints = [] if closed else [path[0], path[-1]]
        for k in endpoints:
            if (k[0] == 1 and k[1] == bx) or (k[0] == 0 and k[2] == by):
                breaks.append(dict(polyline=pid, key=list(k), xy=list(map(float, pos[k][0]))))
        on_crop_edge = [k for k in endpoints if (k[0] == 1 and k[1] in (0, NL)) or (k[0] == 0 and k[2] in (0, NL))]
        crosses = bool(((pts[:, 0].min() < X0 + TILE) and (pts[:, 0].max() > X0 + TILE))
                       or ((pts[:, 1].min() < Y0 + TILE) and (pts[:, 1].max() > Y0 + TILE)))
        polys.append(dict(id=pid, closed=bool(closed), n_points=int(len(pts)), length_m=float(seglen.sum()),
                          ends_on_crop_boundary=len(on_crop_edge), crosses_internal_border=crosses,
                          points=np.round(pts, 3).tolist()))
    polys.sort(key=lambda p: -p["length_m"])
    for i, p in enumerate(polys):
        p["id"] = i
    seam = dict(
        crop=dict(min=[X0, Y0], max=[X0 + CROP, Y0 + CROP], tile_size_m=TILE, tiles=4),
        method="marching squares on a %.2f m global lattice, run per 250 m tile, welded by shared lattice-edge keys" % DS,
        field="F = cos(3*pi*u)*cos(5*pi*v) - cos(5*pi*u)*cos(3*pi*v); u=(X+4000)/8000, v=(Y+4000)/8000 (global m)",
        frame="world X,Y metres (Houdini x,z)", polylines=polys,
        summary=dict(polyline_count=len(polys), total_length_m=float(sum(p["length_m"] for p in polys)),
                     welded_border_keys=len(weld_keys), unintended_breaks=len(breaks),
                     tile_vs_whole_crop_segments_identical=sets_equal))
    return dict(polys=polys, seam=seam, set_tiles=set_tiles, ref_segs=ref_segs, weld_keys=weld_keys, breaks=breaks,
                anomalies=anomalies, sets_equal=sets_equal, weld_disc=weld_disc, cross_tile_pos_dev=cross_tile_pos_dev,
                tile_segs=tile_segs)


def onesided_split_dots(V):
    """Baseline: for every interior lattice node, dot of the area-weighted normals from the faces on the two sides of a
    row cut and of a column cut. This is what a tile border shows for ANY row/column of this terrain."""
    a, b, c, d = V[:-1, :-1], V[:-1, 1:], V[1:, 1:], V[1:, :-1]
    fn = np.cross(c - a, d - b)                       # area-weighted face normal; [j,i] = face above/right of node (j,i)
    fn = np.where(fn[..., 1:2] < 0, -fn, fn)
    nrm = lambda x: x / np.maximum(np.linalg.norm(x, axis=-1, keepdims=True), 1e-12)
    up = fn[1:, :-1] + fn[1:, 1:]; dn = fn[:-1, :-1] + fn[:-1, 1:]
    rt = fn[:-1, 1:] + fn[1:, 1:]; lf = fn[:-1, :-1] + fn[1:, :-1]
    return {"row": np.einsum("...k,...k->...", nrm(up), nrm(dn)),     # [J-1, I-1]
            "col": np.einsum("...k,...k->...", nrm(rt), nrm(lf))}


# ---------------------------------------------------------------------------------------------- rasteriser
def look(eye, tgt, up=(0, 1, 0)):
    eye = np.array(eye, float); tgt = np.array(tgt, float)
    f = tgt - eye; f /= np.linalg.norm(f)
    r = np.cross(f, np.array(up, float)); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return eye, r, u, f


def raster(tris, nrm, cols, chk, eye, tgt, W, H, fov=35.0, ortho_half=None, up=(0, 1, 0), ss=2,
           bg=(226, 228, 232)):
    from PIL import Image
    eye, r, u, f = look(eye, tgt, up)
    Ws, Hs = W * ss, H * ss
    rel = tris - eye
    xc, yc, zc = rel @ r, rel @ u, rel @ f
    if ortho_half:
        sx = xc / ortho_half * 0.5 * Hs + Ws * 0.5
        sy = Hs * 0.5 - yc / ortho_half * 0.5 * Hs
    else:
        fl = 0.5 * Hs / math.tan(math.radians(fov) * 0.5)
        zz = np.maximum(zc, 1e-3)
        sx = xc / zz * fl + Ws * 0.5
        sy = Hs * 0.5 - yc / zz * fl
    zb = np.full((Hs, Ws), np.inf)
    img = np.empty((Hs, Ws, 3)); img[:] = np.array(bg, float)
    lights = [(np.array((-0.5, 0.8, 0.6)), 0.85, np.array((1.0, 0.97, 0.92))),
              (np.array((0.7, 0.3, -0.4)), 0.30, np.array((0.8, 0.88, 1.0)))]
    lights = [(d / np.linalg.norm(d), k, c) for d, k, c in lights]
    back = np.array([230, 0, 200.0])
    cen = tris.mean(axis=1) - eye
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
        clay = cols[t]
        col = (0.30 + 0.18 * n[..., 1])[..., None] * clay * np.array([0.9, 0.93, 1.0])
        for dv, k, c in lights:
            col = col + (np.clip(n @ dv, 0, 1) * k)[..., None] * clay * c
        if chk[t]:
            vdir = -f if ortho_half else -cen[t] / np.linalg.norm(cen[t])
            if float(np.dot(np.mean(nrm[t], axis=0), vdir)) < 0:
                col = col * 0.3 + back * 0.7
        sub[win] = d[win]
        img[y0:y1 + 1, x0:x1 + 1][win] = np.clip(col, 0, 255)[win]
    return Image.fromarray(img.astype(np.uint8)).resize((W, H), Image.LANCZOS)


def ribbon(pts3, half_w, lift):
    """Quad strip along a 3D polyline (Houdini xyz), flat in plan. Returns tris (T,3,3)."""
    pts3 = np.asarray(pts3, float)
    t = np.gradient(pts3[:, [0, 2]], axis=0)
    t /= np.maximum(np.linalg.norm(t, axis=1, keepdims=True), 1e-9)
    nx = np.stack([-t[:, 1], t[:, 0]], 1) * half_w
    L = pts3.copy(); R = pts3.copy()
    L[:, 0] += nx[:, 0]; L[:, 2] += nx[:, 1]; R[:, 0] -= nx[:, 0]; R[:, 2] -= nx[:, 1]
    L[:, 1] += lift; R[:, 1] += lift
    tr = []
    for k in range(len(pts3) - 1):
        tr.append([L[k], R[k], R[k + 1]])
        tr.append([L[k], R[k + 1], L[k + 1]])
    return np.array(tr, float)


# ---------------------------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-render", action="store_true")
    ap.add_argument("--gate-scale", type=float, default=4.0)
    args = ap.parse_args()
    import hou

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "tiles_2x2").mkdir(exist_ok=True)
    (OUT / "hero_views").mkdir(exist_ok=True)
    gates = {}
    meas = {}
    notes = []
    hou.hipFile.clear(suppress_save_prompt=True)
    log("Houdini", hou.applicationVersionString(), "education/apprentice:", hou.isApprentice())
    in_hashes = {"silk_peak_hda": sha256(SILK_HDA), "heart_gate_hda": sha256(GATE_HDA)}

    # ---------------------------------------------------------------- 1. cook four tiles
    hou.hda.installFile(str(SILK_HDA))
    hou.hda.installFile(str(GATE_HDA))
    obj = hou.node("/obj")
    tiles = {}   # (c, r) -> dict
    cook_errs = []
    for r in range(2):
        for c in range(2):
            tx, ty = CROP_MIN[0] + c * TILE, CROP_MIN[1] + r * TILE
            inst = obj.createNode(SILK_T, f"g1_t{c}{r}")
            inst.parm("tile_x").set(tx); inst.parm("tile_y").set(ty)
            inst.parm("tile_size").set(TILE); inst.parm("divisions").set(DIV)
            inst.cook(force=True)
            errs = list(inst.errors()) + [e for ch in inst.allSubChildren() for e in ch.errors()]
            geo = inst.node("output0").geometry()
            if geo is None or errs:
                cook_errs.append((c, r, errs))
                continue
            P, pv, vN, pn = extract(geo)
            Np = point_normals(len(P), pv, vN)
            ix = np.rint((P[:, 0] - tx) / DX).astype(int)
            iz = np.rint((P[:, 2] - ty) / DX).astype(int)
            snap = float(max(np.abs(P[:, 0] - (tx + ix * DX)).max(), np.abs(P[:, 2] - (ty + iz * DX)).max()))
            H = np.full((DIV + 1, DIV + 1), np.nan); N = np.zeros((DIV + 1, DIV + 1, 3))
            Pg = np.zeros((DIV + 1, DIV + 1, 3))
            H[iz, ix] = P[:, 1]; N[iz, ix] = Np; Pg[iz, ix] = P
            tiles[(c, r)] = dict(inst=inst, geo=geo, P=P, pv=pv, vN=vN, pn=pn, H=H, N=N, Pg=Pg, tx=tx, ty=ty,
                                 snap=snap, npts=len(P), nprims=len(pn))
            log(f"tile c{c} r{r} origin ({tx:.0f},{ty:.0f}): {len(P)} pts / {len(pn)} prims, "
                f"height {P[:,1].min():.1f}..{P[:,1].max():.1f} m, lattice snap err {snap:.2e}")
    ok_cook = (not cook_errs and len(tiles) == 4 and all(t["npts"] == (DIV + 1) ** 2 for t in tiles.values())
               and all(not np.isnan(t["H"]).any() for t in tiles.values()))
    gates["G1.01_tiles_cook"] = dict(status="PASS" if ok_cook else "FAIL",
                                     detail=f"4 tiles x {(DIV+1)**2} pts, {DIV}x{DIV} quads each; errors={cook_errs}")
    if not ok_cook:
        _finish(gates, meas, notes, in_hashes, args)
        return 1
    gates["G1.02_global_coords"] = dict(
        status="PASS" if max(t["snap"] for t in tiles.values()) < 1e-3 else "FAIL",
        max_lattice_snap_m=max(t["snap"] for t in tiles.values()),
        detail="every tile vertex sits on the global lattice crop_min + k*1.953125 m")

    # tile files
    tile_files = []
    for (c, r), t in tiles.items():
        base = OUT / "tiles_2x2" / f"tile_c{c}_r{r}"
        np.savez_compressed(str(base) + ".npz", P=t["Pg"], N=t["N"], tile_origin=[t["tx"], t["ty"]], div=DIV, size=TILE)
        tile_files.append(Path(str(base) + ".npz"))
        try:
            t["geo"].saveToFile(str(base) + ".bgeo.sc")
            tile_files.append(Path(str(base) + ".bgeo.sc"))
        except Exception as ex:  # noqa: BLE001
            notes.append(f"bgeo.sc save failed for tile c{c}r{r}: {ex}")

    # ---------------------------------------------------------------- 2a. border positions
    pos_rows = []
    for name, (ta, tb, sa, sb) in {
        "x=-900 lower (c0r0|c1r0)": ((0, 0), (1, 0), "x", None),
        "x=-900 upper (c0r1|c1r1)": ((0, 1), (1, 1), "x", None),
        "y=200 left  (c0r0|c0r1)": ((0, 0), (0, 1), "y", None),
        "y=200 right (c1r0|c1r1)": ((1, 0), (1, 1), "y", None),
    }.items():
        A, B = tiles[ta], tiles[tb]
        if sa == "x":
            pa, pb = A["Pg"][:, DIV, :], B["Pg"][:, 0, :]
        else:
            pa, pb = A["Pg"][DIV, :, :], B["Pg"][0, :, :]
        dd = np.linalg.norm(pa - pb, axis=1)
        pos_rows.append(dict(edge=name, samples=int(len(dd)), max_pos_delta_m=float(dd.max()),
                             max_horizontal_m=float(np.abs(pa[:, [0, 2]] - pb[:, [0, 2]]).max()),
                             max_vertical_m=float(np.abs(pa[:, 1] - pb[:, 1]).max())))
    worst_pos = max(r["max_pos_delta_m"] for r in pos_rows)
    meas["border_positions"] = pos_rows
    gates["G1.03_border_positions"] = dict(status="PASS" if worst_pos <= 0.01 else "FAIL",
                                           worst_m=worst_pos, limit_m=0.01, edges=4,
                                           samples_per_edge=DIV + 1, rows=pos_rows)
    log("border positions worst 3D delta", worst_pos, "m")

    # ---------------------------------------------------------------- 2b. merged + fused mesh reference
    g2 = obj.createNode("geo", "g1_fuse")
    for ch in g2.children():
        ch.destroy()
    om = g2.createNode("object_merge", "om")
    om.parm("numobj").set(4)
    for k, (c, r) in enumerate(sorted(tiles), start=1):
        om.parm(f"objpath{k}").set(tiles[(c, r)]["inst"].path() + "/output0")
    fu = g2.createNode("fuse", "fuse")
    fu.setInput(0, om)
    fu.parm("usetol3d").set(1); fu.parm("tol3d").set(0.001)
    nm = g2.createNode("normal", "normal")
    src_nm = tiles[(0, 0)]["inst"].node("compute_normals")     # legacy HDA builds had one; analytic builds do not
    if src_nm is not None:
        for p_src in src_nm.parms():
            p_dst = nm.parm(p_src.name())
            if p_dst is not None:
                p_dst.set(p_src.eval())
    nm.setInput(0, fu)
    nm.cook(force=True)
    mg = nm.geometry()
    if mg is None:
        raise RuntimeError(f"merged/fused chain failed: {[n.errors() for n in (om, fu, nm)]}")
    MP, Mpv, MvN, Mpn = extract(mg)
    MN = point_normals(len(MP), Mpv, MvN)
    NG = 2 * DIV + 1
    mi = np.rint((MP[:, 0] - CROP_MIN[0]) / DX).astype(int)
    mj = np.rint((MP[:, 2] - CROP_MIN[1]) / DX).astype(int)
    MH = np.full((NG, NG), np.nan); MNg = np.zeros((NG, NG, 3))
    MH[mj, mi] = MP[:, 1]; MNg[mj, mi] = MN
    merged_ok = len(MP) == NG * NG and len(Mpn) == (2 * DIV) ** 2 and not np.isnan(MH).any()
    up_frac = float((Mpn[:, 1] > 0).mean())
    log(f"merged+fused: {len(MP)} pts (expect {NG*NG}), {len(Mpn)} prims, prims facing +Y {up_frac*100:.2f}%")
    gates["G1.04_merged_fused_mesh"] = dict(
        status="PASS" if merged_ok else "FAIL", points=len(MP), expected_points=NG * NG, prims=len(Mpn),
        detail="object_merge x4 -> fuse(0.001 m) -> Normal SOP with the HDA's own compute_normals parms; "
               "66049 = 257^2 means every internal border vertex fused with its twin")
    gates["G1.05_prims_face_up"] = dict(
        status="PASS" if up_frac >= 0.99 and Mpn[:, 1].min() > 0 else "FAIL",
        fraction_prim_normal_y_positive=up_frac, min_prim_normal_y=float(Mpn[:, 1].min()),
        detail="Houdini prim.normal() on the stitched mesh; terrain faces +Y")

    # ---------------------------------------------------------------- 2c. analytic (oracle) heights & normals
    orc = Oracle(hou, tiles[(0, 0)]["inst"])
    gi = np.arange(NG)
    XX = CROP_MIN[0] + gi[None, :] * DX + 0 * gi[:, None]
    ZZ = CROP_MIN[1] + gi[:, None] * DX + 0 * gi[None, :]
    e = 0.1
    q = np.stack([XX + e, XX - e, XX, XX], 0).reshape(4, -1)
    qz = np.stack([ZZ, ZZ, ZZ + e, ZZ - e], 0).reshape(4, -1)
    hh = orc.height(q.ravel(), qz.ravel()).reshape(4, NG, NG)
    hx = (hh[0] - hh[1]) / (2 * e)
    hz = (hh[2] - hh[3]) / (2 * e)
    AN = np.stack([-hx, np.ones_like(hx), -hz], -1)
    AN /= np.linalg.norm(AN, axis=-1, keepdims=True)
    h0 = orc.height(XX.ravel(), ZZ.ravel()).reshape(NG, NG)
    oracle_dev = float(np.abs(h0 - MH).max())
    log(f"oracle (HDA VEX at lattice) vs tile mesh heights: max |dh| = {oracle_dev:.3e} m")
    gates["G1.06_height_oracle_matches_tiles"] = dict(
        status="PASS" if oracle_dev <= 1e-3 else "FAIL", max_abs_dh_m=oracle_dev, points=NG * NG,
        detail="HDA's silk_field VEX re-run in a scratch wrangle at all 257x257 lattice nodes vs cooked tile Y")

    # ---------------------------------------------------------------- 2d. border normals, three methods
    def dots(a, b):
        return np.einsum("...k,...k->...", a, b)

    rows = []
    edges = [("x=-900 lower", (0, 0), (1, 0), "x"), ("x=-900 upper", (0, 1), (1, 1), "x"),
             ("y=200 left", (0, 0), (0, 1), "y"), ("y=200 right", (1, 0), (1, 1), "y")]
    allA, allB, allC, allD = [], [], [], []
    for name, ta, tb, ax in edges:
        A, B = tiles[ta], tiles[tb]
        if ax == "x":
            na, nb = A["N"][:, DIV, :], B["N"][:, 0, :]
            gI = np.full(DIV + 1, ta[0] * DIV + DIV); gJ = ta[1] * DIV + np.arange(DIV + 1)
        else:
            na, nb = A["N"][DIV, :, :], B["N"][0, :, :]
            gJ = np.full(DIV + 1, ta[1] * DIV + DIV); gI = ta[0] * DIV + np.arange(DIV + 1)
        mref, aref = MNg[gJ, gI], AN[gJ, gI]
        dA = dots(na, nb)
        dB = np.minimum(dots(na, mref), dots(nb, mref))
        dC = np.minimum(dots(na, aref), dots(nb, aref))
        dD = dots(mref, aref)
        allA.append(dA); allB.append(dB); allC.append(dC); allD.append(dD)
        rows.append(dict(edge=name, samples=int(len(dA)),
                         A_tile_vs_tile_min=float(dA.min()), A_mean=float(dA.mean()),
                         B_tile_vs_merged_min=float(dB.min()), B_mean=float(dB.mean()),
                         C_tile_vs_analytic_min=float(dC.min()), C_mean=float(dC.mean()),
                         D_merged_vs_analytic_min=float(dD.min())))
    cA, cB, cC, cD = (np.concatenate(x) for x in (allA, allB, allC, allD))
    meas["border_normals"] = dict(rows=rows, min_A=float(cA.min()), min_B=float(cB.min()), min_C=float(cC.min()),
                                  min_D=float(cD.min()),
                                  frac_below_0p98_A=float((cA < 0.98).mean()), frac_below_0p98_B=float((cB < 0.98).mean()),
                                  frac_below_0p98_C=float((cC < 0.98).mean()),
                                  worst_angle_deg_B=float(np.degrees(np.arccos(np.clip(cB.min(), -1, 1)))))
    # also: interior baseline - how different are normals one cell inside, mesh vs analytic (is the border special?)
    interior = dots(MNg[8:-8, 8:-8], AN[8:-8, 8:-8])
    meas["interior_mesh_vs_analytic"] = dict(min=float(interior.min()), mean=float(interior.mean()),
                                             frac_below_0p98=float((interior < 0.98).mean()))
    log(f"border normal min dots  A tile|tile {cA.min():.4f}  B tile|merged {cB.min():.4f}  "
        f"C tile|analytic {cC.min():.4f}  (D merged|analytic {cD.min():.4f}); "
        f"interior mesh|analytic min {interior.min():.4f}")
    gates["G1.07_border_normals"] = dict(
        status="PASS" if cB.min() >= 0.98 else "FAIL",
        primary_method="B: each tile's exported Normal-SOP vertex normal (point-averaged) vs the normal of the "
                       "merged+fused stitched mesh (same Normal SOP parms), both tiles, all 4 internal edges",
        min_dot_B=float(cB.min()), limit=0.98,
        min_dot_A_tile_vs_tile=float(cA.min()), min_dot_C_tile_vs_analytic=float(cC.min()),
        min_dot_D_merged_vs_analytic=float(cD.min()),
        pass_A=bool(cA.min() >= 0.98), pass_B=bool(cB.min() >= 0.98), pass_C=bool(cC.min() >= 0.98),
        detail="Tiles have no halo, so exported border normals are one-sided. A/B/C report how far from seamless "
               "they are. A normal taken from the global field (analytic) or the fused mesh is identical on both "
               "sides by construction (dot 1.0); the numbers here are about the tiles' OWN exported normals.",
        rows=rows)

    # one-sided baseline: is the border special, or is every row/column of this terrain like that?
    sd_ = onesided_split_dots(np.stack([XX, MH, ZZ], -1))
    rowd, cold = sd_["row"], sd_["col"]
    bi = DIV - 1                                     # array index of the internal-border row/col (lattice 128)
    int_r = np.array([j for j in range(rowd.shape[0]) if abs(j - bi) > 4])
    int_c = np.array([i for i in range(cold.shape[1]) if abs(i - bi) > 4])

    def stat(x):
        return dict(min=float(x.min()), median=float(np.median(x)), frac_below_0p98=float((x < 0.98).mean()))
    meas["onesided_baseline"] = dict(
        interior_row_cuts=stat(rowd[int_r, :]), interior_col_cuts=stat(cold[:, int_c]),
        y_border_row_cut=stat(rowd[bi, :]), x_border_col_cut=stat(cold[:, bi]),
        detail="dot of the two one-sided face-normal sums on either side of a row/column cut, for every interior node "
               "vs the internal border. If interior cuts are as bad, the failure is the terrain's sharpness at 1.95 m "
               "cells, not the tile stitching.")
    ob = meas["onesided_baseline"]
    log("one-sided split baseline  interior rows frac<0.98 %.2f (min %.3f) | y-border row %.2f (min %.3f) | "
        "interior cols %.2f | x-border col %.2f" % (
            ob["interior_row_cuts"]["frac_below_0p98"], ob["interior_row_cuts"]["min"],
            ob["y_border_row_cut"]["frac_below_0p98"], ob["y_border_row_cut"]["min"],
            ob["interior_col_cuts"]["frac_below_0p98"], ob["x_border_col_cut"]["frac_below_0p98"]))
    dhx = np.abs(np.diff(MH, axis=1)) / DX
    dhz = np.abs(np.diff(MH, axis=0)) / DX
    meas["terrain_slope"] = dict(
        max_edge_slope_deg=float(np.degrees(np.arctan(max(dhx.max(), dhz.max())))),
        frac_edges_over_45deg=float(((dhx > 1).sum() + (dhz > 1).sum()) / (dhx.size + dhz.size)),
        frac_edges_over_60deg=float(((dhx > 1.732).sum() + (dhz > 1.732).sum()) / (dhx.size + dhz.size)))
    log("terrain edge slopes:", meas["terrain_slope"])

    # ---------------------------------------------------------------- 3. seam by marching squares
    X0, Y0 = CROP_MIN
    NL = int(round(CROP / DS))
    sres = extract_seam(X0, Y0)
    polys, seam, set_tiles, ref_segs = sres["polys"], sres["seam"], sres["set_tiles"], sres["ref_segs"]
    weld_keys, breaks, anomalies = sres["weld_keys"], sres["breaks"], sres["anomalies"]
    sets_equal, weld_disc, cross_tile_pos_dev, tile_segs = (sres["sets_equal"], sres["weld_disc"],
                                                            sres["cross_tile_pos_dev"], sres["tile_segs"])
    (OUT / "seam_graph.json").write_text(json.dumps(seam, indent=1))
    log(f"seam: {len(polys)} polylines, total {seam['summary']['total_length_m']:.1f} m, "
        f"{len(weld_keys)} welded border keys, {len(breaks)} unintended breaks, tile==whole-crop {sets_equal}")
    meas["seam"] = dict(per_tile_segments=({f"c{c}r{r}": n for (c, r), n in tile_segs.items()}),
                        whole_crop_segments=len(ref_segs), union_segments=len(set_tiles),
                        sets_equal=sets_equal, welded_border_keys=len(weld_keys), breaks=breaks,
                        max_crossing_point_discrepancy_m=weld_disc, max_tile_vs_whole_pos_dev_m=cross_tile_pos_dev,
                        degree_gt2_keys=len(anomalies))
    gates["G1.08_seam_weld"] = dict(
        status="PASS" if (sets_equal and not breaks and not anomalies and weld_disc < 1e-9) else "FAIL",
        polyline_count=len(polys), welded_border_keys=len(weld_keys), unintended_breaks=len(breaks),
        degree_gt2=len(anomalies), tile_vs_whole_crop_identical=sets_equal, max_weld_discrepancy_m=weld_disc,
        detail="breaks = polyline endpoints on an INTERNAL tile border (open ends on the crop boundary are legitimate)")
    # supplementary: oblique nodal line (field-only) through the same code path, crossings off the lattice nodes
    ss_ = extract_seam(*STRESS_MIN)
    (OUT / "seam_graph_stress_oblique.json").write_text(json.dumps(ss_["seam"], indent=1))
    long_s = ss_["polys"][0] if ss_["polys"] else None
    meas["seam_stress_oblique"] = dict(crop_min=list(STRESS_MIN), polylines=len(ss_["polys"]),
                                       welded_border_keys=len(ss_["weld_keys"]), breaks=ss_["breaks"],
                                       sets_equal=ss_["sets_equal"], longest_m=(long_s["length_m"] if long_s else 0),
                                       crosses_border=(long_s["crosses_internal_border"] if long_s else False))
    gates["G1.08b_seam_weld_oblique_stress"] = dict(
        status="PASS" if (ss_["sets_equal"] and not ss_["breaks"] and not ss_["anomalies"] and ss_["weld_disc"] < 1e-9
                          and len(ss_["weld_keys"]) >= 2 and long_s is not None) else "FAIL",
        crop_min=list(STRESS_MIN), polylines=len(ss_["polys"]), welded_border_keys=len(ss_["weld_keys"]),
        unintended_breaks=len(ss_["breaks"]), tile_vs_whole_crop_identical=ss_["sets_equal"],
        longest_polyline_m=(long_s["length_m"] if long_s else 0.0),
        detail="field-only (no terrain cooked): the anti-diagonal nodal line X+Y=0 crosses both internal borders at "
               "45 deg, away from lattice nodes; the main crop's seam is the axis-aligned nodal line Y=0")
    log(f"stress seam: {len(ss_['polys'])} polylines, welded keys {len(ss_['weld_keys'])}, breaks {len(ss_['breaks'])}, "
        f"equal {ss_['sets_equal']}")
    if not polys:
        gates["G1.09_seam_found"] = dict(status="FAIL", detail="no F=0 contour in crop")
        _finish(gates, meas, notes, in_hashes, args)
        return 1
    L = polys[0]
    gates["G1.09_seam_found"] = dict(status="PASS" if L["length_m"] >= 100 else "FAIL",
                                     longest_polyline_id=0, longest_length_m=L["length_m"],
                                     longest_crosses_internal_border=L["crosses_internal_border"],
                                     longest_closed=L["closed"])

    # ---------------------------------------------------------------- 4. conform + gate
    def bil(Hm, X, Y):
        fx = (np.asarray(X) - X0) / DX; fy = (np.asarray(Y) - Y0) / DX
        i0 = np.clip(np.floor(fx).astype(int), 0, NG - 2); j0 = np.clip(np.floor(fy).astype(int), 0, NG - 2)
        tx_, ty_ = fx - i0, fy - j0
        return ((Hm[j0, i0] * (1 - tx_) + Hm[j0, i0 + 1] * tx_) * (1 - ty_)
                + (Hm[j0 + 1, i0] * (1 - tx_) + Hm[j0 + 1, i0 + 1] * tx_) * ty_)

    sp = np.array(L["points"])
    sh_mesh = bil(MH, sp[:, 0], sp[:, 1])
    sh_true = orc.height(sp[:, 0], sp[:, 1])
    dev_seam = np.abs(sh_mesh - sh_true)
    conf = dict(polyline_id=0, length_m=L["length_m"], height_source="stitched tile mesh, bilinear (true field alongside)",
                max_mesh_vs_true_field_m=float(dev_seam.max()), mean_mesh_vs_true_field_m=float(dev_seam.mean()),
                height_min_m=float(sh_mesh.min()), height_max_m=float(sh_mesh.max()),
                points_XYH=np.round(np.column_stack([sp, sh_mesh]), 3).tolist())
    (OUT / "seam_longest_conformed.json").write_text(json.dumps(conf))
    meas["seam_conform"] = {k: v for k, v in conf.items() if k != "points_XYH"}
    gates["G1.10_seam_conformed"] = dict(
        status="PASS" if np.isfinite(sh_mesh).all() else "FAIL", points=len(sp),
        height_range_m=[float(sh_mesh.min()), float(sh_mesh.max())],
        mesh_vs_true_max_m=float(dev_seam.max()), mesh_vs_true_mean_m=float(dev_seam.mean()))

    # gate geometry (default params)
    gi_ = obj.createNode(GATE_T, "g1_gate")
    gi_.cook(force=True)
    gerrs = list(gi_.errors()) + [e for ch in gi_.allSubChildren() for e in ch.errors()]
    gg = gi_.node("output0").geometry()
    if gg is None or gerrs:
        gates["G1.11_gate_cook"] = dict(status="FAIL", errors=gerrs)
        _finish(gates, meas, notes, in_hashes, args)
        return 1
    GP = np.array(gg.pointFloatAttribValues("P"), float).reshape(-1, 3)
    gpoly, gpiece, gpn = [], [], []
    for pr in gg.prims():
        gpoly.append([v.point().number() for v in pr.vertices()])
        gpiece.append(pr.attribValue("piece"))
        n = pr.normal(); gpn.append((n[0], n[1], n[2]))
    gpn = np.array(gpn)
    S = args.gate_scale
    HALF = float(max(abs(GP[:, 0].min()), GP[:, 0].max()))      # 3.12 m local half width
    DEPTH = float(GP[:, 2].max())
    GBOT = float(GP[:, 1].min())

    def solids(P, polys_, pieces, normals, origin=(0.0, 0.0, 0.0)):
        vol = {}
        o = np.asarray(origin, float)
        for idx, pc, n in zip(polys_, pieces, normals):
            p = P[idx]
            nw = np.zeros(3)
            for k in range(1, len(p) - 1):
                nw += np.cross(p[k] - p[0], p[k + 1] - p[0])
            A = 0.5 * np.linalg.norm(nw)
            vol[pc] = vol.get(pc, 0.0) + float(np.dot(p.mean(0) - o, n)) * A / 3.0
        return vol

    vol_local = solids(GP, gpoly, gpiece, gpn)
    # candidate seam points
    arc = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(sp, axis=0), axis=1))])
    ctr = np.array([X0 + CROP / 2, Y0 + CROP / 2])
    hs = HALF * S
    best = None
    margin = 60.0
    for k in range(10, len(sp) - 10, 4):
        c0 = sp[k]
        if (c0[0] - X0 < margin or X0 + CROP - c0[0] < margin or c0[1] - Y0 < margin or Y0 + CROP - c0[1] < margin):
            continue
        tg = sp[min(k + 6, len(sp) - 1)] - sp[max(k - 6, 0)]
        tg = tg / np.linalg.norm(tg)
        lat = np.array([tg[1], -tg[0]])
        hl, hr = bil(MH, *(c0 + lat * hs)), bil(MH, *(c0 - lat * hs))
        hf, hb = bil(MH, *(c0 + tg * 20)), bil(MH, *(c0 - tg * 20))
        fpts = np.array([c0 + lat * a_ + tg * b_ for a_ in np.linspace(-hs, hs, 13) for b_ in (-DEPTH * S, 0.0, DEPTH * S)])
        fh = bil(MH, fpts[:, 0], fpts[:, 1])
        fl, fr = chladni(*(c0 + lat * hs)), chladni(*(c0 - lat * hs))
        straddle = (fl > 0) != (fr > 0)
        cost = (fh.max() - fh.min()) + 0.5 * abs(hf - hb) + 0.02 * np.linalg.norm(c0 - ctr) + (0 if straddle else 100.0)
        if best is None or cost < best[0]:
            best = (cost, k, tg, lat, straddle, hl, hr, hf, hb)
    if best is None:
        gates["G1.11_gate_place"] = dict(status="FAIL", detail="no seam point with 60 m crop clearance")
        _finish(gates, meas, notes, in_hashes, args)
        return 1
    cost, kk, tg, lat, straddle, hl, hr, hf, hb = best
    cpt = sp[kk]
    if hf < hb:
        tg = -tg
        lat = np.array([tg[1], -tg[0]])
    # tangent measured independently at the seam point (+-2 m arc) for the alignment check
    kk2a, kk2b = int(np.searchsorted(arc, arc[kk] - 2.0)), int(np.searchsorted(arc, arc[kk] + 2.0))
    t_ind = sp[min(kk2b, len(sp) - 1)] - sp[kk2a]
    t_ind /= np.linalg.norm(t_ind)
    # rotation: local z -> seam tangent in plan, local y -> up, local x = y cross z
    az = np.array([tg[0], 0.0, tg[1]]); ay = np.array([0.0, 1.0, 0.0]); ax = np.cross(ay, az)
    R = np.stack([ax, ay, az], 1)
    yaw = math.degrees(math.atan2(tg[0], tg[1]))
    # grounding: sample the stitched mesh under the whole footprint (all 4 corners + dense grid)
    fx = np.linspace(-HALF * S, HALF * S, 25); fz = np.linspace(-DEPTH * S, DEPTH * S, 5)
    pts_f = [cpt + lat * a + tg * b for a in fx for b in fz]
    pts_f = np.array(pts_f)
    hfoot = bil(MH, pts_f[:, 0], pts_f[:, 1])
    base_y = float(hfoot.min())
    ty_gate = base_y
    foot_bottom = ty_gate + GBOT * S                    # lowest gate vertex (piers sink 0.09 m locally)
    embed_max = float(hfoot.max() - foot_bottom)
    float_gap = float(max(0.0, foot_bottom - hfoot.min()))
    place = dict(houdini_translate=[float(cpt[0]), ty_gate, float(cpt[1])], world_XY=[float(cpt[0]), float(cpt[1])],
                 base_height_m=ty_gate, houdini_rotate_y_deg=yaw, uniform_scale=S,
                 plan_tangent_XY=[float(tg[0]), float(tg[1])], plan_lateral_XY=[float(lat[0]), float(lat[1])],
                 seam_polyline_id=0, seam_arc_m=float(arc[kk]), local_extent_m=dict(half_span=HALF, depth=DEPTH * 2,
                 height=float(GP[:, 1].max() - GBOT)), hda="hda/HDA_Faraway_HeartGate_1.0.hda (default params)",
                 note="gate local +Z (passage axis) = seam tangent; local X spans the opening across the seam; "
                      "walking uphill along the seam enters the front (+Z).")
    (OUT / "gate_placement.json").write_text(json.dumps(place, indent=1))
    # placed geometry in a fresh hou.Geometry and checks with Houdini's own prim.normal()
    GW = (R @ (GP * S).T).T + np.array([cpt[0], ty_gate, cpt[1]])
    pg = hou.Geometry()
    pg.addAttrib(hou.attribType.Prim, "piece", "")
    hp = pg.createPoints([tuple(p) for p in GW.tolist()])
    for idx, pc in zip(gpoly, gpiece):
        poly = pg.createPolygon()
        for i in idx:
            poly.addVertex(hp[i])
        poly.setAttribValue("piece", pc)
    wn = np.array([tuple(pr.normal()) for pr in pg.prims()])
    vol_world = solids(GW, gpoly, gpiece, wn, origin=(cpt[0], ty_gate, cpt[1]))
    closed_pieces = ["pier", "rib", "cusp", "stretcher", "heart_frame", "heart_stem"]
    vrows = {p: dict(local_m3=vol_local.get(p), world_m3=vol_world.get(p),
                     ratio_to_S3=(vol_world[p] / (vol_local[p] * S ** 3)) if vol_local.get(p) else None)
             for p in closed_pieces if p in vol_local}
    vol_ok = all(v["world_m3"] > 0 and abs(v["ratio_to_S3"] - 1.0) < 1e-3 for v in vrows.values())
    # glow sheet: faces split front/back after placement
    gl = [i for i, p in enumerate(gpiece) if p == "heart_glow"]
    nloc = gpn[gl]; nwor = wn[gl]
    glow_dot = np.einsum('ij,ij->i', (R @ nloc.T).T, nwor)
    glow_ok = bool(glow_dot.min() > 0.999)
    gates["G1.11_gate_cook_outward"] = dict(
        status="PASS" if (vol_ok and glow_ok) else "FAIL", pts=len(GP), prims=len(gpoly), scale=S,
        solids_signed_volume_by_prim_normal=vrows, glow_normals_rotate_with_gate=glow_ok, glow_min_dot_local_rotated_vs_placed=float(glow_dot.min()),
        detail="divergence-theorem volume from Houdini prim.normal(); >0 = outward; world volume must equal local*S^3")
    ang = math.degrees(math.acos(float(np.clip(abs(np.dot(tg, t_ind)), -1, 1))))
    fl_, fr_ = float(chladni(*(cpt + lat * hs))), float(chladni(*(cpt - lat * hs)))
    # seam distance from the gate centre to the polyline
    dmin = float(np.min(np.linalg.norm(sp - cpt, axis=1)))
    gates["G1.12_gate_straddles_seam"] = dict(
        status="PASS" if (straddle and ang <= 2.0 and dmin <= 0.5) else "FAIL",
        chladni_at_left_pier=fl_, chladni_at_right_pier=fr_, piers_on_opposite_sides=bool(straddle),
        tangent_alignment_error_deg=ang, gate_centre_to_seam_m=dmin, opening_width_m=2 * hs,
        detail="piers sit at +-%.1f m across the seam; passage axis along the seam tangent" % hs)
    gates["G1.13_gate_grounded"] = dict(
        status="PASS" if (float_gap <= 1e-6 and embed_max <= 3.0 * S) else "FAIL",
        gate_base_height_m=ty_gate, terrain_under_footprint_m=[float(hfoot.min()), float(hfoot.max())],
        max_embed_m=embed_max, float_gap_m=float_gap, embed_limit_m=3.0 * S, embed_limit_rule='embed <= pier height (3 m * scale) and nothing floats',
        height_diff_across_opening_m=float(abs(hl - hr)), grade_along_seam_40m_m=float(abs(hf - hb)),
        detail="gate base set to the lowest terrain under its footprint (stitched mesh); piers on higher ground "
               "are embedded, none float. The embed is large (about half the pier height) because the pleats are "
               "~9 m peak-to-peak every 22 m and run along the seam, so any opening wider than ~10 m spans a corrugation: "
               "a real build needs pier skirts or a flattened pad.")
    meas["gate"] = dict(centre_XY=place["world_XY"], base_height_m=ty_gate, yaw_deg=yaw, scale=S,
                        total_height_m=float((GP[:, 1].max() - GBOT) * S), opening_width_m=2 * hs)
    log(f"gate: centre ({cpt[0]:.1f},{cpt[1]:.1f}) base {ty_gate:.1f} m yaw {yaw:.1f} deg scale {S}, "
        f"straddle={straddle}, align {ang:.3f} deg, embed {embed_max:.2f} m, float {float_gap:.3f} m")

    # ---------------------------------------------------------------- 5. renders
    render_files = []
    if not args.no_render:
        render_files = render_all(MH, AN, NG, sp, sh_mesh, polys, GW, gpoly, gpiece, wn, cpt, tg, lat, S, bil)
    gates["G1.14_hero_renders_written"] = dict(
        status=("PASS" if render_files and all(p.exists() and p.stat().st_size > 20000 for p in render_files)
                else ("BLOCKED" if args.no_render else "FAIL")),
        files=[str(p.relative_to(ROOT)).replace("\\", "/") for p in render_files],
        detail="numpy z-buffer clay rasteriser over the real cooked vertices (Mantra is slow/GL ROP segfaults here, "
               "see HYTHON_HEADLESS_RENDER_FACTS). Existence only; the visual read is recorded separately.")
    gates["G1.15_visual_review"] = dict(status="PENDING", detail="filled in by hand after looking at the PNGs")
    _finish(gates, meas, notes, in_hashes, args, extra_files=tile_files + render_files
            + [OUT / "seam_graph.json", OUT / "seam_longest_conformed.json", OUT / "gate_placement.json"])
    return 0


def render_all(MH, AN, NG, sp, sh_mesh, polys, GW, gpoly, gpiece, wn, cpt, tg, lat, S, bil):
    X0, Y0 = CROP_MIN
    gi = np.arange(NG)
    XX = X0 + gi[None, :] * DX + 0 * gi[:, None]
    ZZ = Y0 + gi[:, None] * DX + 0 * gi[None, :]
    V = np.stack([XX, MH, ZZ], -1)
    tris, nrm, tile_id = [], [], []
    a = V[:-1, :-1]; b = V[:-1, 1:]; c = V[1:, 1:]; d = V[1:, :-1]
    na = AN[:-1, :-1]; nb = AN[:-1, 1:]; nc = AN[1:, 1:]; nd = AN[1:, :-1]
    t1 = np.stack([a, b, c], 2).reshape(-1, 3, 3); t2 = np.stack([a, c, d], 2).reshape(-1, 3, 3)
    n1 = np.stack([na, nb, nc], 2).reshape(-1, 3, 3); n2 = np.stack([na, nc, nd], 2).reshape(-1, 3, 3)
    jj, ii = np.mgrid[0:NG - 1, 0:NG - 1]
    tid = ((jj // DIV) * 2 + (ii // DIV)).ravel()
    T_terr = np.concatenate([t1, t2]); N_terr = np.concatenate([n1, n2]); tid2 = np.concatenate([tid, tid])
    clay = np.array([196, 184, 170.0])
    tint = np.array([[1.0, 1.0, 1.0], [0.88, 0.96, 1.04], [1.04, 0.95, 0.88], [0.9, 1.04, 0.92]])
    # gate triangles
    gt, gn, gc = [], [], []
    pal = {"pier": (222, 178, 92), "heart_frame": (222, 178, 92), "heart_stem": (222, 178, 92),
           "rib": (236, 226, 238), "cusp": (236, 226, 238), "stretcher": (236, 226, 238), "heart_glow": (244, 118, 150)}
    for idx, pc, n in zip(gpoly, gpiece, wn):
        for k in range(1, len(idx) - 1):
            gt.append([GW[idx[0]], GW[idx[k]], GW[idx[k + 1]]]); gn.append([n, n, n]); gc.append(pal.get(pc, (200, 200, 200)))
    gt, gn, gc = np.array(gt), np.array(gn), np.array(gc, float)

    def seam_geo(hw, lift, step):
        T, N, C = [], [], []
        for p in polys:
            P = np.array(p["points"])[::step]
            if len(P) < 2:
                continue
            h = bil(MH, P[:, 0], P[:, 1])
            tr = ribbon(np.column_stack([P[:, 0], h, P[:, 1]]), hw, lift)
            T.append(tr); N.append(np.tile([0, 1.0, 0], (len(tr), 3, 1)))
            C.append(np.tile((255, 70, 30) if p["id"] else (255, 220, 40), (len(tr), 1)))
        return np.concatenate(T), np.concatenate(N), np.concatenate(C, 0).astype(float)

    def border_geo(hw, lift):
        T, N, C = [], [], []
        for line in (np.array([[X0 + TILE, Y0 + s] for s in np.linspace(0, CROP, 260)]),
                     np.array([[X0 + s, Y0 + TILE] for s in np.linspace(0, CROP, 260)])):
            h = bil(MH, line[:, 0], line[:, 1])
            tr = ribbon(np.column_stack([line[:, 0], h, line[:, 1]]), hw, lift)
            T.append(tr); N.append(np.tile([0, 1.0, 0], (len(tr), 3, 1))); C.append(np.tile((40, 200, 230), (len(tr), 1)))
        return np.concatenate(T), np.concatenate(N), np.concatenate(C, 0).astype(float)

    out = []
    W, H = 1100, 800
    hi = float(MH.max()); lo = float(MH.min())
    cx, cz = X0 + CROP / 2, Y0 + CROP / 2

    def go(name, tr_list, eye, tgt, **kw):
        T = np.concatenate([x[0] for x in tr_list]); Nn = np.concatenate([x[1] for x in tr_list])
        Cc = np.concatenate([x[2] for x in tr_list]); Kk = np.concatenate([x[3] for x in tr_list])
        im = raster(T, Nn, Cc, Kk, eye, tgt, W, H, **kw)
        f = OUT / "hero_views" / name
        im.save(f)
        log("wrote", f, f.stat().st_size, "B")
        out.append(f)

    terr_plain = (T_terr, N_terr, np.tile(clay, (len(T_terr), 1)), np.zeros(len(T_terr), bool))
    terr_tint = (T_terr, N_terr, clay * tint[tid2], np.zeros(len(T_terr), bool))
    gate_t = (gt, gn, gc, np.ones(len(gt), bool))
    sg = seam_geo(3.0, 3.5, 3)
    seam_t = (sg[0], sg[1], sg[2], np.zeros(len(sg[0]), bool))
    gate_up = (cpt[0], 0, cpt[1])
    # 1 oblique over the crop, gate enlarged with a beacon so it reads at 500 m
    go("hero_oblique_back.png", [terr_plain, seam_t, gate_t],
       (cx - 0.55 * CROP, hi + 0.45 * CROP, cz + 0.95 * CROP), (cx, lo + (hi - lo) * 0.35, cz), fov=40.0)
    # along the seam, from the west end, looking east over the gate
    go("hero_oblique.png", [terr_plain, seam_t, gate_t],
       (X0 - 0.10 * CROP, hi + 0.30 * CROP, Y0 - 0.30 * CROP), (cpt[0] + 60.0, lo + (hi - lo) * 0.35, 40.0), fov=40.0)
    # 2 top view with tile tint, borders and seam
    bg_ = border_geo(1.0, 1.2)
    bd_t = (bg_[0], bg_[1], bg_[2], np.zeros(len(bg_[0]), bool))
    sg2 = seam_geo(1.8, 1.4, 2)
    seam_t2 = (sg2[0], sg2[1], sg2[2], np.zeros(len(sg2[0]), bool))
    go("hero_top_tiles.png", [terr_tint, bd_t, seam_t2, gate_t], (cx, hi + 3 * CROP, cz + 0.001), (cx, lo, cz),
       ortho_half=CROP * 0.56, up=(0, 0, -1))
    # 3 gate close-up (3/4) and through-the-gate along the seam
    R = np.stack([np.cross([0, 1.0, 0], [tg[0], 0, tg[1]]), [0, 1.0, 0], [tg[0], 0, tg[1]]], 1)
    base = np.array([cpt[0], 0, cpt[1]])
    gy = float(GW[:, 1].min())
    sgc = seam_geo(0.5 * S / 4, 0.6, 1)
    seam_c = (sgc[0], sgc[1], sgc[2], np.zeros(len(sgc[0]), bool))

    def near(Tt, Nn, Cc, Kk, c0, rad):
        m = np.linalg.norm(Tt.mean(axis=1)[:, [0, 2]] - np.array([c0[0], c0[2]]), axis=1) < rad
        return Tt[m], Nn[m], Cc[m], Kk[m]
    cen = np.array([cpt[0], gy + 3.6 * S, cpt[1]])
    tn = near(*terr_plain, cen, 150.0)
    sn = near(*seam_c, cen, 150.0)
    for name, eloc in (("hero_gate_closeup.png", (5.5, 4.5, 13.0)), ("hero_gate_through.png", (0.6, 3.4, 15.0))):
        e = cen + (R @ (np.array(eloc) * S))
        e[1] = max(e[1], float(bil(MH, e[0], e[2])) + 3.0)
        go(name, [tn, sn, gate_t], e, cen, fov=35.0)
    # shared-border close-up: where the seam crosses the internal border x = crop_min + 250 m
    bf = border_geo(0.4, 2.0)
    bfine = (bf[0], bf[1], bf[2], np.zeros(len(bf[0]), bool))
    bx_, by_ = X0 + TILE, float(sp[np.argmin(np.abs(sp[:, 0] - (X0 + TILE))), 1])
    tgt_b = np.array([bx_, float(bil(MH, bx_, by_)) + 2.0, by_])
    cb_ = np.array([bx_, 0, by_])
    tb = near(*terr_tint, cb_, 90.0)
    sb_ = seam_geo(0.8, 2.4, 1)
    sbn = near(sb_[0], sb_[1], sb_[2], np.zeros(len(sb_[0]), bool), cb_, 90.0)
    bn = near(*bfine, cb_, 90.0)
    eb = tgt_b + np.array([-24.0, 46.0, -34.0])
    eb[1] = max(eb[1], float(bil(MH, eb[0], eb[2])) + 6.0)
    go("hero_border_closeup.png", [tb, bn, sbn], eb, tgt_b, fov=38.0)
    return out


def _finish(gates, meas, notes, in_hashes, args, extra_files=()):
    peak, cur = mem_mb()
    el = time.time() - T0
    fails = [k for k, v in gates.items() if v["status"] == "FAIL"]
    pend = [k for k, v in gates.items() if v["status"] in ("PENDING", "BLOCKED")]
    files = {}
    for p in extra_files:
        if Path(p).exists():
            files[str(Path(p).relative_to(ROOT)).replace("\\", "/")] = sha256(Path(p))
    files["Tools/Houdini/faraway/g1_stitch_proof.py"] = sha256(Path(__file__))
    acc = dict(
        id="g1_stitch_proof", houdini="22.0.368", crop=dict(min_XY=list(CROP_MIN), size_m=CROP, tiles=4,
                                                            tile_size_m=TILE, divisions=DIV, cell_m=DX),
        frame="world X,Y metres; Houdini x=X, y=height, z=Y", elapsed_s=round(el, 1),
        peak_working_set_mb=round(peak, 1), final_working_set_mb=round(cur, 1),
        overall=("FAIL" if fails else "PASS_PENDING_VISUAL" if pend else "PASS"),
        failed_gates=fails, pending_or_blocked=pend, gates=gates, measurements=meas, notes=notes,
        input_hda_sha256=in_hashes, output_sha256=files)
    (OUT / "acceptance.json").write_text(json.dumps(acc, indent=1, default=float))
    log(f"acceptance.json written: overall={acc['overall']} fails={fails} elapsed={el:.1f}s peakWS={peak:.0f} MB")


if __name__ == "__main__":
    sys.exit(main())
