"""terraced_island_geometry.py -- pure-Python Faraway Mother floating terraced island.

No `hou` import: returns triangle lists so the same source can be unit-tested outside
Houdini and embedded verbatim in the HDA's Python SOP (build_faraway_terraced_island_hda.py
reads this file's text).

Layout (metric, Y-up, island axis = Y, origin = base of the lowest cliff):
  * N terrace strata, stratum k spans y = k*H .. (k+1)*H. Each is a steep cliff face
    (leaning inward by `cliff_slope`, split into stacked strata bands with small ledge
    lips) topped by a flat tread; the last tread is the plateau cap at y = N*H.
  * Every stratum outline is r(theta) = R0 * s_k * (1 + amp * noise_k(theta)) -- a
    seeded low-order Fourier series (periodic, so no seam). s_k shrinks 1.0 -> 0.5
    from the lowest to the top stratum, so treads stay open (clamped >= min_tread).
  * Underside: rings tapering to an apex at depth 0.85*R0 (tepui / hanging-rock taper).
  * Waterfalls: ledge-lip points on cliff tops. Each fall is a ribbon strip hugging the
    cliff (UV v runs down the fall) plus one emitter point at the lip.
  * Collision proxy: the same ring profile at 16 angular samples, conservative radius
    envelope (max over the sample's angular neighbourhood, divided by cos(pi/16)).

Winding: Houdini's front face is CLOCKWISE (normal = -right-hand). The island and the
collision hull are each ONE closed surface built with a consistent winding and then
oriented by signed volume; ribbons are oriented to face radially outward.
"""
import math
import random

TILE = 10.0  # metres per UV tile


# ----------------------------------------------------------------------------- maths
def _newell(a, b, c):
    """Right-hand (CCW) area normal of triangle abc (unnormalised, 2*area*n)."""
    ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
    return (uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx)


def houdini_volume(tris):
    """Signed volume using Houdini's convention (normal = -right-hand). >0 == outward."""
    v = 0.0
    for t in tris:
        a, b, c = t[0], t[1], t[2]
        n = _newell(a, b, c)
        ctr = ((a[0] + b[0] + c[0]) / 3.0, (a[1] + b[1] + c[1]) / 3.0, (a[2] + b[2] + c[2]) / 3.0)
        v += -(ctr[0] * n[0] + ctr[1] * n[1] + ctr[2] * n[2])
    return v / 6.0


class _Mesh:
    def __init__(self):
        self.tris = []  # (a, b, c, uva, uvb, uvc, attrs)

    def add(self, a, b, c, uva, uvb, uvc, **attrs):
        self.tris.append([a, b, c, uva, uvb, uvc, attrs])

    def flip_all(self):
        for t in self.tris:
            t[1], t[2] = t[2], t[1]
            t[4], t[5] = t[5], t[4]

    def orient_by_volume(self):
        if houdini_volume(self.tris) < 0.0:
            self.flip_all()
        return houdini_volume(self.tris)


class _Outline:
    """Seeded periodic outline noise, clamped to |n| <= 1 (RMS ~0.5)."""

    HARMONICS = (2, 3, 4, 5, 7)

    def __init__(self, seed):
        rng = random.Random(int(seed) * 7919 + 101)
        w = [1.0 / (h ** 0.7) for h in self.HARMONICS]
        tot = math.sqrt(sum(x * x for x in w))
        self.a = [0.7 * x / tot for x in w]   # RMS ~0.5, peaks ~1; n() clamps to [-1, 1]
        self.phi = [rng.uniform(0.0, 2.0 * math.pi) for _ in self.HARMONICS]
        self.drift = [rng.uniform(-0.8, 0.8) for _ in self.HARMONICS]

    def n(self, layer, th):
        s = 0.0
        for h, a, p, d in zip(self.HARMONICS, self.a, self.phi, self.drift):
            s += a * math.sin(h * th + p + layer * d)
        return max(-1.0, min(1.0, s))


# --------------------------------------------------------------------------- profile
class _Profile:
    def __init__(self, p):
        self.R0 = float(p["radius"])
        self.N = max(3, min(6, int(p["terrace_count"])))
        self.H = float(p["terrace_height"])
        self.amp = float(p["outline_noise"])
        self.slope = math.radians(float(p["cliff_slope"]))
        self.seed = int(p["seed"])
        self.preview = bool(int(p["preview_mode"]))
        self.ol = _Outline(self.seed)
        self.tread_nom = 0.5 * self.R0 / (self.N - 1)
        self.inset = min(self.H * math.tan(self.slope), 0.35 * self.tread_nom)
        self.min_tread = 0.04 * self.R0
        self.depth = 0.85 * self.R0
        self.nb = 1 if self.preview else 3                 # strata bands per cliff
        self.U = 3 if self.preview else 6                  # underside rings
        self.lip = min(0.3, 0.05 * self.H) if self.nb > 1 else 0.0

    def RA(self, k, th):
        raw = self.R0 * (1.0 - 0.5 * k / (self.N - 1)) * (1.0 + self.amp * self.ol.n(k, th))
        if k > 0:
            raw = min(raw, self.RB(k - 1, th) - self.min_tread)
        return max(raw, 0.12 * self.R0)

    def RB(self, k, th):
        return self.RA(k, th) - self.inset

    def under_r(self, i, th):
        t = i / (self.U + 1.0)
        ra0 = self.RA(0, th)
        r = ra0 * (1.0 - t) ** 0.7 * (1.0 + 0.5 * self.amp * self.ol.n(100 + i, th))
        return min(ra0, max(r, 0.02 * self.R0))

    def under_y(self, i):
        return -self.depth * i / (self.U + 1.0)

    def rings(self, coarse_env=None):
        """Bottom->top list of (y, radius_fn(th), tag). tag describes the gap INTO this ring.
        coarse_env: None for the render mesh, else a function wrapping fn -> envelope fn
        (and bands are dropped for the collision hull)."""
        out = []
        UND = dict(piece="underside", strata=-1, cliff=0, band=-1)
        env = coarse_env or (lambda f, add=0.0: f)
        for i in range(self.U, 0, -1):
            out.append((self.under_y(i), env(lambda th, i=i: self.under_r(i, th)), UND))
        out.append((0.0, env(lambda th: self.RA(0, th), self.lip if coarse_env else 0.0), UND))
        for k in range(self.N):
            y0 = k * self.H
            if k > 0:
                out.append((y0, env(lambda th, k=k: self.RA(k, th), self.lip if coarse_env else 0.0),
                            dict(piece="tread", strata=k - 1, cliff=0, band=-1)))
            if coarse_env:
                out.append(((k + 1) * self.H,
                            env(lambda th, k=k: self.RB(k, th), self.lip),
                            dict(piece="cliff", strata=k, cliff=1, band=0)))
            else:
                for b in range(1, self.nb + 1):
                    ly = self.lip if b < self.nb else 0.0
                    out.append((y0 + self.H * b / self.nb,
                                (lambda th, k=k, b=b, ly=ly:
                                 self.RA(k, th) - self.inset * b / self.nb + ly),
                                dict(piece="cliff", strata=k, cliff=1, band=b - 1)))
        return out


def _ring_mesh(prof, M, rings, tile=TILE):
    """Closed surface from bottom apex over rings to a top centre fan; returns _Mesh."""
    mesh = _Mesh()
    pts = []   # pts[i][j], j = 0..M (col M duplicates col 0 position)
    uvs = []
    for i, (y, fn, _tag) in enumerate(rings):
        row, urow = [], []
        for j in range(M + 1):
            th = 2.0 * math.pi * (j % M) / M
            r = fn(th)
            row.append((r * math.cos(th), y, r * math.sin(th)))
        pts.append(row)
    # uv: u around, v = cumulative profile arc length per column
    apex = (0.0, -prof.depth, 0.0)
    vcum = [[0.0] * (M + 1) for _ in rings]
    for j in range(M + 1):
        v = 0.0
        prev = apex
        # apex -> ring 0 distance counted from the apex so the underside starts at v=0
        for i in range(len(rings)):
            q = pts[i][j]
            v += math.dist(prev, q)
            vcum[i][j] = v / tile
            prev = q
    ucirc = 2.0 * math.pi * prof.R0 / tile

    def uv(i, j):
        return (ucirc * j / M, vcum[i][j], 0.0)

    first = rings[0][2]
    for j in range(M):
        a, b = pts[0][j], pts[0][j + 1]
        ua, ub = uv(0, j), uv(0, j + 1)
        ua0 = (0.5 * (ua[0] + ub[0]), 0.0, 0.0)
        mesh.add(apex, b, a, ua0, ub, ua, **first)
    for i in range(1, len(rings)):
        tag = rings[i][2]
        for j in range(M):
            a0, a1 = pts[i - 1][j], pts[i - 1][j + 1]
            b0, b1 = pts[i][j], pts[i][j + 1]
            mesh.add(a0, a1, b1, uv(i - 1, j), uv(i - 1, j + 1), uv(i, j + 1), **tag)
            mesh.add(a0, b1, b0, uv(i - 1, j), uv(i, j + 1), uv(i, j), **tag)
    top = (0.0, prof.N * prof.H, 0.0)
    L = len(rings) - 1
    cap = dict(piece="plateau", strata=prof.N - 1, cliff=0, band=-1)
    for j in range(M):
        a, b = pts[L][j], pts[L][j + 1]
        mesh.add(top, a, b, (top[0] / tile + 0.5, top[2] / tile + 0.5, 0.0),
                 (a[0] / tile + 0.5, a[2] / tile + 0.5, 0.0),
                 (b[0] / tile + 0.5, b[2] / tile + 0.5, 0.0), **cap)
    return mesh


def _envelope(M):
    d = math.pi / M
    k = 1.0 / math.cos(d)

    def make(fn, add=0.0):
        def f(th):
            # 17 samples over the sector + 5 cm safety (outline clamps leave kinks between samples)
            return (max(fn(th + (i / 8.0 - 1.0) * d) for i in range(17)) + add + 0.05) * k
        return f
    return make


# ------------------------------------------------------------------------ waterfalls
def _waterfalls(prof, nwf, preview):
    """Returns (ribbon_tris, emitters). Ribbon tris share the _Mesh tri format."""
    mesh = _Mesh()
    emitters = []
    if nwf <= 0:
        return mesh, emitters
    rng = random.Random(prof.seed * 104729 + 17)
    rows = 4 if preview else 10
    wnom = min(max(0.06 * prof.R0, 1.2), 6.0)
    placed = []
    min_sep = math.pi / nwf
    base_off = prof.lip + 0.12
    phi = math.atan2(prof.inset, prof.H)
    for wid in range(nwf):
        if wid == 0:
            k = prof.N - 1
        elif wid == 1:
            k = 0
        else:
            k = rng.randrange(prof.N)
        th = 0.0
        for _try in range(60):
            th = rng.uniform(0.0, 2.0 * math.pi)
            if all(abs(((th - t0 + math.pi) % (2.0 * math.pi)) - math.pi) >= min_sep for t0 in placed):
                break
        placed.append(th)
        width = wnom * rng.uniform(0.7, 1.3)
        flow = 0.5 + 0.5 * min(1.0, width / (1.3 * wnom))
        smax = 3.0 if k == 0 else 1.0
        fall_h = prof.H * smax
        ytop = (k + 1) * prof.H
        ra, rb = prof.RA(k, th), prof.RB(k, th)
        cx, cz = math.cos(th), math.sin(th)
        tx, tz = -cz, cx
        # emitter at the ledge lip
        emitters.append(dict(
            P=(rb * cx, ytop, rb * cz),
            N=(cx * math.sin(phi), -math.cos(phi), cz * math.sin(phi)),
            fall_height=fall_h, width=width, flow=flow, strata=k, wf_id=wid))
        # ribbon: (rows+1) rows x 2 columns
        grid = []
        for r in range(rows + 1):
            t = r / rows
            s = t * smax
            y = ytop - s * prof.H
            if k > 0 and r == rows:
                y += 0.05
            rad = (rb + prof.inset * s) if s <= 1.0 else ra
            off = base_off + 0.8 * math.exp(-(6.0 * s) ** 2) + (0.15 * (s - 1.0) if s > 1.0 else 0.0)
            rr = rad + off
            hw = 0.5 * width * (1.0 + 0.3 * t)
            L = (rr * cx - tx * hw, y, rr * cz - tz * hw)
            Rr = (rr * cx + tx * hw, y, rr * cz + tz * hw)
            grid.append((L, Rr, t))
        attrs = dict(piece="waterfall", strata=k, cliff=0, band=-1, wf_id=wid, flow=flow,
                     fall_height=fall_h)
        vscale = 1.0  # v in 0..1 down the fall, u across
        quad = []
        for r in range(rows):
            L0, R0_, t0 = grid[r]
            L1, R1, t1 = grid[r + 1]
            quad.append((L0, R0_, R1, L1, t0 * vscale, t1 * vscale))
        tris = []
        for L0, R0_, R1, L1, v0, v1 in quad:
            tris.append([L0, R0_, R1, (0.0, v0, 0.0), (1.0, v0, 0.0), (1.0, v1, 0.0), dict(attrs)])
            tris.append([L0, R1, L1, (0.0, v0, 0.0), (1.0, v1, 0.0), (0.0, v1, 0.0), dict(attrs)])
        # orient: Houdini normal (= -newell) must point radially outward
        t = tris[0]
        n = _newell(t[0], t[1], t[2])
        hn = (-n[0], -n[1], -n[2])
        if hn[0] * cx + hn[2] * cz < 0.0:
            for t in tris:
                t[1], t[2] = t[2], t[1]
                t[4], t[5] = t[5], t[4]
        mesh.tris.extend(tris)
    return mesh, emitters


# ----------------------------------------------------------------------------- API
MATERIALS = {
    "underside": "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Mantle",
    "cliff": "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Mantle",
    "tread": "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Gown",
    "plateau": "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Gown",
    "waterfall": "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_SilkWaterfall",
}


def generate(p):
    """Return dict(island=[tris], collision=[tris], emitters=[dict], meta=dict).

    tri = [a, b, c, uva, uvb, uvc, attrs]; island tris include the waterfall ribbons.
    """
    prof = _Profile(p)
    prev = prof.preview
    M = 24 if prev else 72
    island = _ring_mesh(prof, M, prof.rings())
    vol = island.orient_by_volume()
    ribbons, emitters = _waterfalls(prof, int(p["waterfall_count"]), prev)
    Mc = 16
    hull = _ring_mesh(prof, Mc, prof.rings(coarse_env=_envelope(Mc)))
    hvol = hull.orient_by_volume()
    tris = island.tris + ribbons.tris
    meta = dict(volume=vol, hull_volume=hvol, height=prof.N * prof.H, inset=prof.inset,
                depth=prof.depth, M=M)
    return dict(island=tris, collision=hull.tris, emitters=emitters, meta=meta)
