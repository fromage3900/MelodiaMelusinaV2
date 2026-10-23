"""lace_bridge_geometry.py -- pure-Python Faraway Mother Lace Bridge generator.

No hou import: returns closed solids as lists of polygons so the same source can be
unit-tested outside Houdini and embedded verbatim in the HDA's Python SOP
(build_faraway_lace_bridge_hda.py reads this file's text).  The rib / cusp / stretcher
math is copied from heart_gate_geometry.py (kept import-free on purpose).

Frame
-----
Solids are authored in a STRAIGHT bridge frame: x = s (metres along the walkway, 0..L),
y = height (y = 0 is the deck top at both landings, Houdini Y-up), z = lateral offset.
meta["warp"](s, y, lat) maps that frame onto the plan path (input curve, or the built-in
gentle S-curve) -- tangent T, lateral N = T x Y, so the map keeps handedness and closed
solids stay outward after warping.

Real-life reference (see Docs/Houdini/FARAWAY_LACE_BRIDGE_HDA_2026-10-23.md):
  * rib arch: segmental / two-centred pointed arch (Rialto's single-span arch; pointed crown
    angle is a control: 0 = pure segmental arc)
  * openwork parapet: quatrefoil / trefoil rings between sill and handrail (Ulm Minster spire
    tracery, Gothic parapets)
  * cusped lappets under the intrados (Alhambra / Gothic cusping), radial ladder stretchers
  * lace read: Chantilly / Burano bobbin lace
Winding: Houdini's front face is CLOCKWISE (normal = -right-hand). Every closed solid is
oriented by signed volume, never by hand.
"""
import math


# ---------------------------------------------------------------- orientation helpers
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


def _orient(polys):
    if houdini_volume(polys) < 0.0:
        return [list(reversed(p)) for p in polys]
    return polys


def prism(poly2d, z0, z1):
    """Closed solid from a CONVEX 2D polygon (s,y) extruded z0..z1."""
    n = len(poly2d)
    front = [(x, y, z1) for x, y in poly2d]
    back = [(x, y, z0) for x, y in poly2d]
    polys = [front, list(reversed(back))]
    for i in range(n):
        j = (i + 1) % n
        polys.append([back[i], back[j], front[j], front[i]])
    return _orient(polys)


def strip_solid(outer, inner, z0, z1, closed):
    """Closed solid from two paired 2D curves (a band) extruded z0..z1."""
    n = len(outer)
    last = n if closed else n - 1
    polys = []
    for i in range(last):
        j = (i + 1) % n
        polys.append([(outer[i][0], outer[i][1], z1), (outer[j][0], outer[j][1], z1),
                      (inner[j][0], inner[j][1], z1), (inner[i][0], inner[i][1], z1)])
        polys.append([(inner[i][0], inner[i][1], z0), (inner[j][0], inner[j][1], z0),
                      (outer[j][0], outer[j][1], z0), (outer[i][0], outer[i][1], z0)])
        polys.append([(outer[i][0], outer[i][1], z0), (outer[j][0], outer[j][1], z0),
                      (outer[j][0], outer[j][1], z1), (outer[i][0], outer[i][1], z1)])
        polys.append([(inner[i][0], inner[i][1], z1), (inner[j][0], inner[j][1], z1),
                      (inner[j][0], inner[j][1], z0), (inner[i][0], inner[i][1], z0)])
    if not closed:
        for k in (0, n - 1):
            polys.append([(outer[k][0], outer[k][1], z0), (outer[k][0], outer[k][1], z1),
                          (inner[k][0], inner[k][1], z1), (inner[k][0], inner[k][1], z0)])
    return _orient(polys)


def sweep_box(ss, yb, yt, lat0, lat1):
    """Closed solid swept along stations ss (list of s) between yb(s)..yt(s), lat0..lat1."""
    n = len(ss)
    polys = []
    for i in range(n - 1):
        s0, s1 = ss[i], ss[i + 1]
        a0, a1, b0, b1 = yt(s0), yt(s1), yb(s0), yb(s1)
        polys.append([(s0, a0, lat0), (s1, a1, lat0), (s1, a1, lat1), (s0, a0, lat1)])   # top
        polys.append([(s0, b0, lat1), (s1, b1, lat1), (s1, b1, lat0), (s0, b0, lat0)])   # bottom
        polys.append([(s0, b0, lat0), (s1, b1, lat0), (s1, a1, lat0), (s0, a0, lat0)])   # lat0 side
        polys.append([(s0, a0, lat1), (s1, a1, lat1), (s1, b1, lat1), (s0, b0, lat1)])   # lat1 side
    s0, s1 = ss[0], ss[-1]
    polys.append([(s0, yb(s0), lat0), (s0, yt(s0), lat0), (s0, yt(s0), lat1), (s0, yb(s0), lat1)])
    polys.append([(s1, yb(s1), lat1), (s1, yt(s1), lat1), (s1, yt(s1), lat0), (s1, yb(s1), lat0)])
    return _orient(polys)


def box_sy(s0, s1, y0, y1, z0, z1):
    return prism([(s0, y0), (s1, y0), (s1, y1), (s0, y1)], z0, z1)


# ---------------------------------------------------------------- plan path
def _catmull(pts, per_seg):
    """Catmull-Rom spline through 2D pts (list of (x,z)); returns a dense polyline."""
    n = len(pts)
    out = []
    for i in range(n - 1):
        p0 = pts[max(i - 1, 0)]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[min(i + 2, n - 1)]
        for k in range(per_seg):
            t = k / float(per_seg)
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[c]) + (-p0[c] + p2[c]) * t +
                                    (2 * p0[c] - 5 * p1[c] + 4 * p2[c] - p3[c]) * t2 +
                                    (-p0[c] + 3 * p1[c] - 3 * p2[c] + p3[c]) * t3) for c in (0, 1)))
    out.append(pts[-1])
    return out


def build_plan(p, in_pts):
    """Returns (table, y0, from_input) ; table = [(s, x, z)] at ~0.1 m spacing."""
    from_input = bool(in_pts) and len(in_pts) >= 2
    if from_input:
        raw = [(q[0], q[2]) for q in in_pts]
        # drop coincident points
        pts = [raw[0]]
        for q in raw[1:]:
            if math.hypot(q[0] - pts[-1][0], q[1] - pts[-1][1]) > 1e-4:
                pts.append(q)
        if len(pts) < 2:
            from_input = False
        else:
            y0 = in_pts[0][1]
    if not from_input:
        span = p["span"]
        sway = p["sway"]
        pts = [(-span * 0.5 + span * i / 16.0, sway * math.sin(2.0 * math.pi * i / 16.0)) for i in range(17)]
        y0 = 0.0
    dense = _catmull(pts, 24) if len(pts) > 2 else [pts[0], pts[-1]]
    # resample to uniform arc length
    cum = [0.0]
    for i in range(1, len(dense)):
        cum.append(cum[-1] + math.hypot(dense[i][0] - dense[i - 1][0], dense[i][1] - dense[i - 1][1]))
    total = cum[-1]
    ds = 0.1
    n = max(int(math.ceil(total / ds)), 2)
    table = []
    j = 0
    for i in range(n + 1):
        s = total * i / float(n)
        while j < len(cum) - 2 and cum[j + 1] < s:
            j += 1
        seg = max(cum[j + 1] - cum[j], 1e-9)
        t = (s - cum[j]) / seg
        table.append((s, dense[j][0] + (dense[j + 1][0] - dense[j][0]) * t,
                      dense[j][1] + (dense[j + 1][1] - dense[j][1]) * t))
    return table, y0, from_input


def make_warp(table, y0):
    total = table[-1][0]
    n = len(table) - 1

    def pos(s):
        s = min(max(s, 0.0), total)
        f = s / total * n
        i = min(int(f), n - 1)
        t = f - i
        a, b = table[i], table[i + 1]
        return a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t

    def warp(s, y, lat):
        x, z = pos(s)
        xa, za = pos(s - 0.15)
        xb, zb = pos(s + 0.15)
        tx, tz = xb - xa, zb - za
        ln = math.hypot(tx, tz) or 1.0
        tx, tz = tx / ln, tz / ln
        # N = T x Y = (-tz, 0, tx)
        return (x - tz * lat, y0 + y, z + tx * lat)

    return warp, total


# ---------------------------------------------------------------- generator
def _lobed_outline(cx, cy, r0, lobes, segs, rot_up=True):
    """Star-shaped quatrefoil/trefoil outline around (cx,cy); lobe tips at r0, sharp cusps between."""
    pts = []
    for i in range(segs):
        th = 2.0 * math.pi * i / segs
        c = abs(math.cos(0.5 * lobes * th))      # th measured from "up"
        rho = r0 * (0.64 + 0.36 * c ** 0.7)
        # th from up -> screen angle
        ang = th + math.pi * 0.5
        pts.append((cx + rho * math.cos(ang), cy + rho * math.sin(ang)))
    return pts


def generate(p, in_pts=None):
    """p: dict of parameters. Returns (out, meta). out = {piece: [solid, ...]} in the straight
    frame (s, y, lat); meta['warp'](s,y,lat) -> world xyz ; meta['L'] bridge length."""
    W = p["deck_width"]
    rise = p["rise"]
    crown_deg = p["crown_point"]
    hump = p["deck_hump"]
    thick = p["deck_thickness"]
    layers = int(p["rib_layers"])
    rw = p["rib_width"]
    rd = p["rib_depth"]
    step = p["layer_step"]
    density = max(p["lace_density"], 0.3)
    ph = p["parapet_height"]
    res = max(p["resolution"], 0.5)
    seed = int(p["seed"])
    preview = bool(p.get("preview_mode", 0))
    if preview:
        res = max(res / 3.0, 0.5)

    table, y0, from_input = build_plan(p, in_pts)
    warp, L = make_warp(table, y0)
    a = L * 0.5

    def rnd(i):
        return (math.sin((i + 1) * 12.9898 + seed * 78.233) * 43758.5453) % 1.0

    # ---- deck profile (y = 0 at both landings, hump at crown)
    def yt(s):
        t = s / L
        return hump * 4.0 * t * (1.0 - t)

    def yb(s):
        return yt(s) - thick

    # ---- rib arch: two-centred pointed arch through (0,A) apex and (a, y_s) springing
    A = hump - thick                     # rib extrados touches deck underside at the crown
    y_s = A - rise                       # springing level
    tanb = math.tan(math.radians(min(max(crown_deg, 0.0), 45.0)))
    tanb = min(tanb, 0.85 * rise / a)    # keep R positive
    m = -tanb
    kk = 1.0 / math.sqrt(1.0 + m * m)
    R = (a * a + rise * rise) / (2.0 * kk * (a * m + rise))
    xc = R * m * kk
    yc = A - R * kk

    def ext_y(x):
        x = abs(x)
        return yc + math.sqrt(max(R * R - (x - xc) ** 2, 0.0))

    def theta_range(r):
        sn = (y_s - yc) / r
        if sn > 0.985:
            return None
        th_e = math.asin(max(min(sn, 1.0), -1.0))
        cs = -xc / r
        if cs >= 1.0:
            return None
        th_a = math.acos(max(min(cs, 1.0), -1.0))
        if th_a <= th_e:
            return None
        return th_e, th_a

    def arc_pts(r, n, t0=0.0, t1=1.0):
        """Right-half points apex-first for radius r (x measured from bridge centre)."""
        th_e, th_a = theta_range(r)
        pts = []
        for i in range(n + 1):
            t = t1 + (t0 - t1) * i / float(n)           # t1 -> t0 (apex -> springing)
            th = th_e + (th_a - th_e) * t
            pts.append((xc + r * math.cos(th), yc + r * math.sin(th)))
        return pts

    def full_curve(r, n):
        right = arc_pts(r, n)
        left = [(-x, y) for x, y in reversed(right)]
        c = left[:-1] + right
        return [(a + x, y) for x, y in c]

    out = {"deck": [], "rib": [], "stretcher": [], "cusp": [], "post": [], "tie": [],
           "rail": [], "mullion": [], "lace": [], "pier": []}

    # ---- deck slab (collision-proxy piece)
    nseg = max(int(math.ceil(L * res)), 4)
    ss = [L * i / float(nseg) for i in range(nseg + 1)]
    out["deck"].append(sweep_box(ss, yb, yt, -W * 0.5, W * 0.5))

    # ---- side rib arches (stack of concentric layers) on both sides
    rib_lat = W * 0.5 - rd * 0.5 - 0.04
    arc_len_half = 0.0
    n_arc = 8
    layer_radii = []
    for k in range(layers):
        r_out = R - k * step
        r_in = r_out - rw
        if r_in <= 0.5 or theta_range(r_out) is None or theta_range(r_in) is None:
            break
        layer_radii.append((r_out, r_in))
    if not layer_radii:
        r_out, r_in = R, R - rw
        layer_radii.append((r_out, r_in))
    th_e0, th_a0 = theta_range(layer_radii[0][0])
    arc_len_half = layer_radii[0][0] * (th_a0 - th_e0)
    n_arc = max(int(math.ceil(arc_len_half * res)), 8)
    for side in (-1, 1):
        lat_c = side * rib_lat
        for r_out, r_in in layer_radii:
            outer = full_curve(r_out, n_arc)
            inner = full_curve(r_in, n_arc)
            out["rib"].append(strip_solid(outer, inner, lat_c - rd * 0.5, lat_c + rd * 0.5, False))

    # ---- abutment piers (full-width wall blocks at both landings, under the deck ends)
    pier_w = 0.42
    pier_y0 = y_s - 0.35
    out["pier"].append(box_sy(0.0, pier_w, pier_y0, yb(0.0), -W * 0.5, W * 0.5))
    out["pier"].append(box_sy(L - pier_w, L, pier_y0, yb(L), -W * 0.5, W * 0.5))

    cell_n = max(int(round(L * density)), 2)
    cell = L / float(cell_n)
    lace_on = not preview

    # ---- radial ladder stretchers between adjacent layers
    if lace_on and len(layer_radii) > 1:
        n_st = max(int(round(0.5 * density * arc_len_half)), 2)
        for side in (-1, 1):
            lat_c = side * rib_lat
            for k in range(len(layer_radii) - 1):
                r_hi = layer_radii[k][1] + 0.01        # inner face of layer k
                r_lo = layer_radii[k + 1][0] - 0.01    # outer face of layer k+1
                r_mid = 0.5 * (r_hi + r_lo)
                te, ta = theta_range(r_mid)
                for hs in (-1, 1):
                    for j in range(n_st):
                        th = te + (ta - te) * (0.10 + 0.84 * (j + 0.5) / n_st)
                        ux, uy = math.cos(th), math.sin(th)
                        hw = 0.03
                        q0 = (xc + ux * r_lo, yc + uy * r_lo)
                        q1 = (xc + ux * r_hi, yc + uy * r_hi)
                        tx, ty = -uy, ux
                        quad = [(q0[0] - tx * hw, q0[1] - ty * hw), (q0[0] + tx * hw, q0[1] + ty * hw),
                                (q1[0] + tx * hw, q1[1] + ty * hw), (q1[0] - tx * hw, q1[1] - ty * hw)]
                        quad = [(a + hs * x, y) for x, y in quad]
                        if hs < 0:
                            quad = list(reversed(quad))
                        out["stretcher"].append(prism(quad, lat_c - rd * 0.3, lat_c + rd * 0.3))

    # ---- cusped lappets hanging from the innermost intrados
    if lace_on:
        r_cus = layer_radii[-1][1]
        te, ta = theta_range(r_cus)
        arc_i = r_cus * (ta - te)
        n_c = max(int(round(arc_i / cell)), 2)
        cs = min(max(0.34 * cell, 0.08), 0.30)
        for side in (-1, 1):
            lat_c = side * rib_lat
            for hs in (-1, 1):
                for j in range(n_c):
                    th = te + (ta - te) * (0.08 + 0.84 * (j + 0.5) / n_c)
                    ux, uy = math.cos(th), math.sin(th)
                    s_ = cs * (0.85 + 0.3 * rnd(j + (7 if hs > 0 else 0) + (3 if side > 0 else 0)))
                    bx, by = xc + ux * r_cus, yc + uy * r_cus
                    nx, ny = -ux, -uy
                    tx, ty = -uy, ux
                    loc = [(-0.5 * s_, -0.05), (0.5 * s_, -0.05), (0.30 * s_, 0.5 * s_),
                           (0.0, 1.5 * s_), (-0.30 * s_, 0.5 * s_)]
                    poly = [(a + hs * (bx + tx * u + nx * v), by + ty * u + ny * v) for u, v in loc]
                    if hs < 0:
                        poly = list(reversed(poly))
                    out["cusp"].append(prism(poly, lat_c - rd * 0.35, lat_c + rd * 0.35))

    # ---- spandrel posts + under-deck stretchers at the cell boundaries
    pw = 0.035
    for j in range(1, cell_n):
        s = cell * j
        x = s - a
        bot = ext_y(x) - 0.03
        top = yb(s) + 0.02
        if top - bot > 0.06:
            for side in (-1, 1):
                lat_c = side * rib_lat
                out["post"].append(box_sy(s - pw, s + pw, bot, top, lat_c - rd * 0.35, lat_c + rd * 0.35))
        if lace_on:
            lat_in = rib_lat - rd * 0.35
            out["tie"].append(box_sy(s - 0.03, s + 0.03, yb(s) - 0.09, yb(s) + 0.01, -lat_in, lat_in))

    # ---- openwork parapet on both deck edges
    sill_h = 0.10
    rail_h = 0.07
    pt = 0.09
    for side in (-1, 1):
        l0 = side * (W * 0.5 - pt - 0.01)
        l1 = side * (W * 0.5 - 0.01)
        lat0, lat1 = (l0, l1) if l0 < l1 else (l1, l0)
        out["rail"].append(sweep_box(ss, lambda s: yt(s), lambda s: yt(s) + sill_h, lat0, lat1))
        out["rail"].append(sweep_box(ss, lambda s: yt(s) + ph - rail_h, lambda s: yt(s) + ph, lat0, lat1))
        latc = 0.5 * (lat0 + lat1)
        for j in range(cell_n + 1):
            s = min(max(cell * j, 0.03), L - 0.03)
            out["mullion"].append(box_sy(s - 0.028, s + 0.028, yt(s) + sill_h - 0.01,
                                         yt(s) + ph - rail_h + 0.01, latc - pt * 0.4, latc + pt * 0.4))
        if lace_on:
            segs = 24
            bw = 0.032
            for j in range(cell_n):
                sc = cell * (j + 0.5)
                y_lo = yt(sc) + sill_h
                y_hi = yt(sc) + ph - rail_h
                cy = 0.5 * (y_lo + y_hi)
                r0 = min(0.5 * cell - 0.02, 0.5 * (y_hi - y_lo)) + 0.012
                if r0 < 0.05:
                    continue
                lobes = 4 if ((j + seed) % 2 == 0) else 3
                outl = _lobed_outline(sc, cy, r0, lobes, segs)
                kin = 1.0 - bw / (0.82 * r0)
                inn = [(sc + (x - sc) * kin, cy + (y - cy) * kin) for x, y in outl]
                out["lace"].append(strip_solid(outl, inn, latc - pt * 0.3, latc + pt * 0.3, True))

    meta = {"warp": warp, "L": L, "y0": y0, "from_input": from_input, "R": R,
            "springing_y": y_s, "crown_y": A, "layers": len(layer_radii), "preview": preview,
            "cell": cell, "cells": cell_n}
    return out, meta
