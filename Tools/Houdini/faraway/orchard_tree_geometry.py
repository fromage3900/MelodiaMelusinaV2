"""orchard_tree_geometry.py -- pure-Python Listening Orchard hero blossom tree.

No `hou` import: returns flat primitive records so the same source can be unit-tested
outside Houdini and embedded verbatim in the HDA's Python SOP
(build_faraway_orchard_tree_hda.py reads this file's text).

Layout: tree stands at the origin, Y up, metric (1 unit = 1 m), ground at y = 0.

Method (deterministic by seed, no external RNG state):
  * trunk  -- tapered, fluted tube along a sinuous, twisting centreline (parallel-transport
              frames), flared at the base.
  * roots  -- buttress roots: tapered tubes that start inside the trunk flare, run outward and
              dive under the ground.
  * limbs  -- recursive tapered-tube branching (L-system style): level 1 limbs leave the top of
              the trunk, every further level hangs 2-3 children off its parent (Murray-style
              radius split, shorter + thinner each level, drooping at the tips).
  * cards  -- blossom CARD cloud: one quad per card scattered along the terminal twigs, random
              orientation (camera-facing-agnostic), per-card @blossom_id, UVs 0-1.
  * canopy -- low-poly lumpy ellipsoid volumes (one per limb + a crown blob) for far LODs.
  * collision -- one tapered 8-sided trunk cylinder.
Every tube / blob is a CLOSED solid (end caps) oriented by signed volume. Houdini faces are
CLOCKWISE-front (prim normal = -right-hand normal); orientation is decided by volume, never by hand.
"""
import math
import random


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _len(a):
    return math.sqrt(_dot(a, a))


def _norm(a):
    l = _len(a)
    if l < 1e-12:
        return (0.0, 1.0, 0.0)
    return (a[0] / l, a[1] / l, a[2] / l)


def _lerp(a, b, f):
    return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f)


def _perp(t):
    a = (1.0, 0.0, 0.0) if abs(t[0]) < 0.9 else (0.0, 0.0, 1.0)
    return _norm(_cross(t, a))


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def _newell(poly):
    """Right-hand (CCW) area-normal of a polygon."""
    nx = ny = nz = 0.0
    n = len(poly)
    for i in range(n):
        x0, y0, z0 = poly[i]
        x1, y1, z1 = poly[(i + 1) % n]
        nx += (y0 - y1) * (z0 + z1)
        ny += (z0 - z1) * (x0 + x1)
        nz += (x0 - x1) * (y0 + y1)
    return (nx * 0.5, ny * 0.5, nz * 0.5)


def houdini_volume(polys):
    """Signed volume using Houdini's convention (normal = -right-hand). Positive == outward."""
    v = 0.0
    for p in polys:
        n = _newell(p)
        c = (sum(q[0] for q in p) / len(p), sum(q[1] for q in p) / len(p), sum(q[2] for q in p) / len(p))
        v += -(c[0] * n[0] + c[1] * n[1] + c[2] * n[2])
    return v / 3.0


def orient(solid):
    """solid = [(poly, uv), ...]. Flip so Houdini sees it outward-facing."""
    if houdini_volume([p for p, _ in solid]) < 0.0:
        return [(list(reversed(p)), list(reversed(u))) for p, u in solid]
    return solid


def tube(pts, radii, sides, flute=None, tile_u=1, v_scale=0.6):
    """Closed tapered tube along polyline `pts` (>=2 points) with per-point `radii`.

    flute = (amp, k, [phase per point]) adds k spiral lobes. Returns an oriented solid.
    Frames by parallel transport so the sweep never flips.
    """
    n = len(pts)
    tang = []
    for i in range(n):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n - 1)]
        tang.append(_norm(_sub(b, a)))
    nrm = _perp(tang[0])
    rings = []
    vs = []
    s = 0.0
    for i in range(n):
        t = tang[i]
        if i > 0:
            s += _len(_sub(pts[i], pts[i - 1]))
            nrm = _sub(nrm, _mul(t, _dot(nrm, t)))
            nrm = _norm(nrm)
        bn = _cross(t, nrm)
        ring = []
        for k in range(sides):
            th = 2.0 * math.pi * k / sides
            r = radii[i]
            if flute is not None:
                r = r * (1.0 + flute[0] * math.cos(flute[1] * th - flute[2][i]))
            ring.append(_add(pts[i], _add(_mul(nrm, r * math.cos(th)), _mul(bn, r * math.sin(th)))))
        rings.append(ring)
        vs.append(s / v_scale)
    solid = []
    for i in range(n - 1):
        for k in range(sides):
            k1 = (k + 1) % sides
            u0 = tile_u * k / float(sides)
            u1 = tile_u * (k + 1) / float(sides)
            solid.append(([rings[i][k], rings[i][k1], rings[i + 1][k1], rings[i + 1][k]],
                          [(u0, vs[i]), (u1, vs[i]), (u1, vs[i + 1]), (u0, vs[i + 1])]))
    capuv = [(0.5 + 0.5 * math.cos(2.0 * math.pi * k / sides), 0.5 + 0.5 * math.sin(2.0 * math.pi * k / sides))
             for k in range(sides)]
    solid.append((list(reversed(rings[0])), list(reversed(capuv))))
    solid.append((list(rings[-1]), list(capuv)))
    return orient(solid)


def blob(c, rx, ry, rz, lon, lat, rng, lump):
    """Closed lumpy ellipsoid (UV sphere, pole fans). Returns an oriented solid."""
    rings = []
    for i in range(1, lat):
        th = math.pi * i / lat
        ring = []
        for k in range(lon):
            ph = 2.0 * math.pi * k / lon
            m = 1.0 + lump * (rng.random() * 2.0 - 1.0)
            ring.append((c[0] + rx * m * math.sin(th) * math.cos(ph),
                         c[1] + ry * m * math.cos(th),
                         c[2] + rz * m * math.sin(th) * math.sin(ph)))
        rings.append(ring)
    top = (c[0], c[1] + ry, c[2])
    bot = (c[0], c[1] - ry, c[2])
    solid = []
    for k in range(lon):
        k1 = (k + 1) % lon
        solid.append(([top, rings[0][k1], rings[0][k]],
                      [(0.5, 1.0), ((k + 1) / float(lon), 1.0 - 1.0 / lat), (k / float(lon), 1.0 - 1.0 / lat)]))
    for i in range(len(rings) - 1):
        for k in range(lon):
            k1 = (k + 1) % lon
            v0 = 1.0 - (i + 1) / float(lat)
            v1 = 1.0 - (i + 2) / float(lat)
            solid.append(([rings[i][k], rings[i][k1], rings[i + 1][k1], rings[i + 1][k]],
                          [(k / float(lon), v0), ((k + 1) / float(lon), v0),
                           ((k + 1) / float(lon), v1), (k / float(lon), v1)]))
    for k in range(lon):
        k1 = (k + 1) % lon
        solid.append(([bot, rings[-1][k], rings[-1][k1]],
                      [(0.5, 0.0), (k / float(lon), 1.0 / lat), ((k + 1) / float(lon), 1.0 / lat)]))
    return orient(solid)


def edge_consistent(polys, nd=5):
    """True when every directed edge is paired with exactly one opposite edge (closed + consistently wound)."""
    cnt = {}
    for p in polys:
        q = [tuple(round(c, nd) for c in v) for v in p]
        for i in range(len(q)):
            e = (q[i], q[(i + 1) % len(q)])
            cnt[e] = cnt.get(e, 0) + 1
    for (a, b), c in cnt.items():
        if c != 1 or cnt.get((b, a), 0) != 1:
            return False
    return True


# piece -> level tables -----------------------------------------------------------------
_SIDES = {1: 8, 2: 6, 3: 5, 4: 4}
_SIDES_PREVIEW = {1: 4, 2: 3, 3: 3, 4: 3}
_SEGS = {1: 8, 2: 6, 3: 5, 4: 4}
_SEGS_PREVIEW = {1: 4, 2: 3, 3: 3, 4: 2}
_WANDER = {1: 0.30, 2: 0.40, 3: 0.50, 4: 0.50}
_DROOP = {1: 0.04, 2: 0.12, 3: 0.22, 4: 0.28}
_UPTROP = {1: 0.10, 2: 0.04, 3: 0.0, 4: 0.0}
_CHILDREN = {1: 3, 2: 3, 3: 2, 4: 2}


def generate(p):
    """p: dict of parameters. Returns (prims, meta).

    prims: list of dict(piece, poly, uv, level, solid, bid, tint, coll) -- one per polygon.
    """
    height = float(p["height"])
    R0 = float(p["trunk_radius"])
    levels = max(1, min(4, int(p["branch_levels"])))
    spread = float(p["branch_spread"])
    twist = float(p["twist"])
    dens = float(p["blossom_density"])
    seed = int(p["seed"])
    preview = bool(p.get("preview_mode", 0))
    sides_t = _SIDES_PREVIEW if preview else _SIDES
    segs_t = _SEGS_PREVIEW if preview else _SEGS
    if preview:
        dens *= 0.25

    rng = random.Random(seed * 1013 + 7)
    prims = []
    solid_counter = [0]

    def add_solid(piece, solid, level, coll=0):
        sid = solid_counter[0]
        solid_counter[0] += 1
        for poly, uv in solid:
            prims.append({"piece": piece, "poly": poly, "uv": uv, "level": level, "solid": sid,
                          "bid": -1, "tint": 0.0, "coll": coll})

    # ---------------- trunk ----------------
    Ht = 0.30 * height
    nseg_t = 8 if preview else 16
    phase0 = rng.uniform(0.0, 2.0 * math.pi)
    lean = 0.10 * Ht
    tpts, trad, tph = [], [], []
    for i in range(nseg_t + 1):
        t = i / float(nseg_t)
        y = -0.2 + t * (Ht + 0.2)
        ang = phase0 + twist * 2.0 * math.pi * 0.6 * t
        amp = 0.5 * R0 * (0.35 + 0.35 * twist) * math.sin(math.pi * t)
        ox = amp * math.cos(ang) + lean * t * t * math.cos(phase0 + 1.0)
        oz = amp * math.sin(ang) + lean * t * t * math.sin(phase0 + 1.0)
        tpts.append((ox, y, oz))
        trad.append(R0 * (1.0 - 0.42 * t) * (1.0 + 0.55 * math.exp(-max(y, 0.0) / 0.9)))
        tph.append(twist * 2.0 * math.pi * t)
    trunk_sides = 6 if preview else 10
    add_solid("trunk", tube(tpts, trad, trunk_sides, flute=(0.12, 3, tph),
                            tile_u=max(1, int(round(2.0 * math.pi * R0 / 0.6)))), 0)
    r_top = trad[-1]

    def trunk_at(y):
        f = _clamp((y + 0.2) / (Ht + 0.2), 0.0, 1.0) * nseg_t
        i0 = min(int(f), nseg_t - 1)
        return _lerp(tpts[i0], tpts[i0 + 1], f - i0)

    # collision cylinder (straight, base->top)
    rc0 = trad[0] * 0.9
    rc1 = r_top
    add_solid("trunk_collision", tube([(0.0, -0.05, 0.0), tpts[-1]], [rc0, rc1], 8, tile_u=1), 0, coll=1)

    # ---------------- buttress roots ----------------
    nroot = 5
    base_psi = rng.uniform(0.0, 2.0 * math.pi)
    y0 = 1.1
    c0 = trunk_at(y0)
    for j in range(nroot):
        psi = base_psi + 2.0 * math.pi * j / nroot + rng.uniform(-0.3, 0.3)
        rho_end = R0 * rng.uniform(2.3, 3.1)
        nr = 3 if preview else 6
        rpts, rrad = [], []
        r_start = 0.65 * R0
        r_end = max(0.14 * R0, 0.03)
        for i in range(nr + 1):
            s = i / float(nr)
            psi_s = psi + 0.18 * math.sin(s * 2.0 * math.pi + j)
            rho = rho_end * s ** 0.9
            y = y0 * (1.0 - s ** 1.5) - 0.18 * s
            rpts.append((c0[0] + rho * math.cos(psi_s), y, c0[2] + rho * math.sin(psi_s)))
            rrad.append(r_end + (r_start - r_end) * (1.0 - s)) 
        add_solid("root", tube(rpts, rrad, 4 if preview else 6, tile_u=2), -1)

    # ---------------- branches (recursive) ----------------
    branches = []
    up = (0.0, 1.0, 0.0)

    def grow(start, d, length, r0, r1, level, limb):
        nseg = segs_t[level]
        step = length / nseg
        pts = [start]
        for _ in range(nseg):
            rv = (rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))
            sw = _mul(_cross(up, d), twist * 0.08)
            d = _norm(_add(_add(d, _mul(rv, _WANDER[level])),
                           _add(sw, (0.0, _UPTROP[level] - _DROOP[level], 0.0))))
            q = _add(pts[-1], _mul(d, step))
            if q[1] < 0.5:
                q = (q[0], 0.5, q[2])
                d = _norm((d[0], abs(d[1]), d[2]))
            pts.append(q)
        rad = [r1 + (r0 - r1) * (1.0 - i / float(nseg)) ** 1.2 for i in range(nseg + 1)]
        b = {"pts": pts, "rad": rad, "level": level, "len": length, "limb": limb}
        branches.append(b)
        if level < levels:
            nc = _CHILDREN[level]
            ph = rng.uniform(0.0, 2.0 * math.pi)
            for j in range(nc):
                f = 0.28 + 0.62 * (j + rng.uniform(0.1, 0.9)) / nc
                idx = f * nseg
                i0 = min(int(idx), nseg - 1)
                fr = idx - i0
                pos = _lerp(pts[i0], pts[i0 + 1], fr)
                tg = _norm(_sub(pts[i0 + 1], pts[i0]))
                U = _perp(tg)
                V = _cross(tg, U)
                alpha = math.radians(_clamp(36.0 * spread * rng.uniform(0.75, 1.25), 12.0, 80.0))
                phi = ph + j * 2.4 + rng.uniform(-0.4, 0.4)
                dc = _add(_mul(tg, math.cos(alpha)),
                          _mul(_add(_mul(U, math.cos(phi)), _mul(V, math.sin(phi))), math.sin(alpha)))
                dc = _norm(_add(dc, (0.0, 0.20 if level == 1 else 0.05, 0.0)))
                rpar = rad[i0] + (rad[i0 + 1] - rad[i0]) * fr
                r0c = max(rpar * 0.68, 0.02)
                r1c = max(0.012, r0c * 0.18)
                r0c = max(r0c, r1c * 1.3)
                grow(pos, dc, length * (0.72 - 0.38 * f), r0c, r1c, level + 1, limb)

    nlimb = 5
    phi1 = rng.uniform(0.0, 2.0 * math.pi)
    for j in range(nlimb):
        sj = 0.75 if j == 0 else rng.uniform(0.62, 1.0)
        pos = trunk_at(sj * Ht)
        az = phi1 + j * 2.399963 + rng.uniform(-0.25, 0.25)
        if j == 0:
            el = math.radians(80.0)   # central leader continues the trunk (hides the trunk's top cap)
        else:
            el = math.radians(_clamp(40.0 - 20.0 * (spread - 1.0) + rng.uniform(-10.0, 10.0), 15.0, 75.0))
        d0 = (math.cos(az) * math.cos(el), math.sin(el), math.sin(az) * math.cos(el))
        if j == 0:   # leader follows the trunk's own end tangent so its start cap stays buried
            tt = _norm(_sub(tpts[-1], tpts[-2]))
            d0 = _norm(_add(_mul(tt, 0.8), _mul(d0, 0.4)))
        L1 = 0.66 * height * rng.uniform(0.85, 1.1)
        rl = r_top * (0.80 if j == 0 else 0.62)
        grow(pos, d0, L1 * (0.8 if j == 0 else 1.0), rl, max(0.012, rl * 0.18), 1, j)

    names = {1: "branch", 2: "branch", 3: "branch", 4: "branch"}
    tip_y = 0.0
    for b in branches:
        lv = b["level"]
        add_solid(names[lv], tube(b["pts"], b["rad"], sides_t[lv], tile_u=1, v_scale=0.8), lv)
        tip_y = max(tip_y, max(q[1] for q in b["pts"]))

    # ---------------- blossom cards on terminal twigs ----------------
    term = [b for b in branches if b["level"] == levels]
    sub_term = [b for b in branches if b["level"] == levels - 1] if levels > 1 else []
    allpts = [q for b in term for q in b["pts"]]
    cc = (sum(q[0] for q in allpts) / len(allpts), sum(q[1] for q in allpts) / len(allpts),
          sum(q[2] for q in allpts) / len(allpts))
    crng = random.Random(seed * 7919 + 13)
    bid = 0
    card_r = 0.0
    for b in term:
        nc = int(round(dens * b["len"] * 0.8))
        if dens > 0.0:
            nc = max(nc, 1)
        npt = len(b["pts"]) - 1
        for j in range(nc):
            s = (0.25 + 0.75 * (j + crng.random()) / nc) * npt
            i0 = min(int(s), npt - 1)
            c = _lerp(b["pts"][i0], b["pts"][i0 + 1], s - i0)
            c = _add(c, (crng.uniform(-0.22, 0.22), crng.uniform(-0.22, 0.22), crng.uniform(-0.22, 0.22)))
            out = _norm(_sub(c, cc))
            rv = (crng.uniform(-1, 1), crng.uniform(-1, 1), crng.uniform(-1, 1))
            n = _norm(_add(_add(_mul(out, 0.55), _mul(rv, 0.9)), (0.0, 0.15, 0.0)))
            cx_ = _cross(n, rv)
            u0 = _norm(cx_) if _len(cx_) > 1e-6 else _perp(n)
            v0 = _cross(n, u0)
            h = 0.5 * crng.uniform(0.34, 0.55)
            ua, va = _mul(u0, h), _mul(v0, h)
            poly = [_add(_add(c, _mul(ua, -1)), va), _add(_add(c, ua), va),
                    _add(_sub(c, va), ua), _sub(_sub(c, va), ua)]
            prims.append({"piece": "blossom_cards", "poly": poly,
                          "uv": [(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)],
                          "level": levels, "solid": -1, "bid": bid, "tint": crng.random(), "coll": 0})
            bid += 1
            card_r = max(card_r, math.hypot(c[0], c[2]))

    # a lighter dusting on the outer 45% of the branches one level below the twigs (fills the crown)
    for b in sub_term:
        nc = int(round(dens * b["len"] * 0.25)) if dens > 0.0 else 0
        npt = len(b["pts"]) - 1
        for j in range(nc):
            s = (0.55 + 0.45 * (j + crng.random()) / nc) * npt
            i0 = min(int(s), npt - 1)
            c = _lerp(b["pts"][i0], b["pts"][i0 + 1], s - i0)
            c = _add(c, (crng.uniform(-0.22, 0.22), crng.uniform(-0.22, 0.22), crng.uniform(-0.22, 0.22)))
            out = _norm(_sub(c, cc))
            rv = (crng.uniform(-1, 1), crng.uniform(-1, 1), crng.uniform(-1, 1))
            n = _norm(_add(_add(_mul(out, 0.55), _mul(rv, 0.9)), (0.0, 0.15, 0.0)))
            cx_ = _cross(n, rv)
            u0 = _norm(cx_) if _len(cx_) > 1e-6 else _perp(n)
            v0 = _cross(n, u0)
            h = 0.5 * crng.uniform(0.34, 0.55)
            ua, va = _mul(u0, h), _mul(v0, h)
            poly = [_add(_add(c, _mul(ua, -1)), va), _add(_add(c, ua), va),
                    _add(_sub(c, va), ua), _sub(_sub(c, va), ua)]
            prims.append({"piece": "blossom_cards", "poly": poly,
                          "uv": [(0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)],
                          "level": levels - 1, "solid": -1, "bid": bid, "tint": crng.random(), "coll": 0})
            bid += 1
            card_r = max(card_r, math.hypot(c[0], c[2]))

    # ---------------- canopy volume proxy (LOD) ----------------
    prng = random.Random(seed * 104729 + 3)
    lon, lat = 8, 5
    for limb in range(nlimb):
        lp = [q for b in term if b["limb"] == limb for q in b["pts"]]
        if not lp:
            continue
        ctr = (sum(q[0] for q in lp) / len(lp), sum(q[1] for q in lp) / len(lp), sum(q[2] for q in lp) / len(lp))
        r = max(_len(_sub(q, ctr)) for q in lp) * 0.72 + 0.25
        add_solid("canopy_proxy", blob(ctr, r, 0.8 * r, r, lon, lat, prng, 0.10), levels)
    rmax = max(_len(_sub(q, cc)) for q in allpts)
    add_solid("canopy_proxy", blob(cc, 0.5 * rmax, 0.4 * rmax, 0.5 * rmax, lon, lat, prng, 0.10), levels)

    meta = {"tip_y": tip_y, "canopy_radius": card_r, "card_count": bid, "trunk_height": Ht,
            "branch_count": len(branches), "solid_count": solid_counter[0], "preview": preview}
    return prims, meta


if __name__ == "__main__":
    # self-test outside Houdini: closed + consistently wound + outward (Houdini volume > 0)
    P = dict(height=9.0, trunk_radius=0.75, branch_levels=3, branch_spread=1.0, twist=0.8,
             blossom_density=36.0, seed=11, preview_mode=0)
    pr, meta = generate(P)
    solids = {}
    for q in pr:
        if q["solid"] >= 0:
            solids.setdefault((q["solid"], q["piece"]), []).append(q["poly"])
    bad = 0
    for (sid, piece), polys in solids.items():
        v = houdini_volume(polys)
        ok = edge_consistent(polys)
        if v <= 0 or not ok:
            bad += 1
            print("BAD", sid, piece, v, ok)
    print(len(pr), "prims", len(solids), "solids", "bad", bad, meta)
