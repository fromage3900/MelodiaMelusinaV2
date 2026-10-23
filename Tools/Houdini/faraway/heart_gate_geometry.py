"""heart_gate_geometry.py -- pure-Python Faraway Mother Heart Gate generator.

No `hou` import: returns closed solids as lists of polygons so the same source
can be unit-tested outside Houdini and embedded verbatim in the HDA's Python SOP
(build_faraway_heart_gate_hda.py reads this file's text).

Layout: gate lies in the XY plane (Y up), depth along Z, centred on x=0, floor y=0.

Reference geometry (see Docs/Houdini/FARAWAY_HEART_GATE_HDA_2026-10-23.md):
  * two-centred pointed arch: radius R = lancet * span, arc centres on the
    opposite springing points when lancet == 1 (equilateral, apex = 0.866*span).
    Concentric offsets keep every rib exactly parallel and every apex on x=0.
  * cusped lappets on the innermost intrados (Alhambra / Gothic cusping)
  * radial stretchers between ribs (Ulm / Cologne openwork "ladder" lace)
  * cordiform opening: x=16sin^3 t, y=13cos t-5cos2t-2cos3t-cos4t
Winding: Houdini's front face is CLOCKWISE (normal = -right-hand). Every closed
solid is oriented by signed volume, never by hand.
"""
import math


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


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
    """Signed volume using Houdini's convention (normal = -right-hand).

    Positive == outward-facing closed solid.
    """
    v = 0.0
    for p in polys:
        n = _newell(p)
        c = (sum(q[0] for q in p) / len(p), sum(q[1] for q in p) / len(p), sum(q[2] for q in p) / len(p))
        v += -(c[0] * n[0] + c[1] * n[1] + c[2] * n[2])
    return v / 3.0


def _orient(polys):
    """Flip a closed solid so Houdini sees it outward-facing."""
    if houdini_volume(polys) < 0.0:
        return [list(reversed(p)) for p in polys]
    return polys


def prism(poly2d, z0, z1):
    """Closed solid from a CONVEX 2D polygon extruded z0..z1."""
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


def box(cx, cy, hx, hy, z0, z1):
    return prism([(cx - hx, cy - hy), (cx + hx, cy - hy), (cx + hx, cy + hy), (cx - hx, cy + hy)], z0, z1)


def _arch_curve(a, ph, R, radius, segs):
    """Left->right polyline of the two-centred arch at `radius` (same centres)."""
    cxr = a - R  # right arc centre x (left arc mirrors)
    ya = math.sqrt(max(radius * radius - cxr * cxr, 0.0))
    th_a = math.acos(max(min((-cxr) / radius, 1.0), -1.0))
    right = []
    for i in range(segs + 1):
        th = th_a * (1.0 - i / float(segs))  # apex -> springing
        right.append((cxr + radius * math.cos(th), ph + radius * math.sin(th)))
    left = [(-x, y) for x, y in reversed(right)]
    # left runs springing -> apex ; drop duplicate apex
    return left[:-1] + right, (cxr, ph), (-cxr, ph), th_a, ya


def heart_outline(scale, segs):
    pts = []
    for i in range(segs):
        t = 2.0 * math.pi * i / segs
        x = 16.0 * math.sin(t) ** 3
        y = 13.0 * math.cos(t) - 5.0 * math.cos(2 * t) - 2.0 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x * scale, y * scale))
    return pts


def generate(p):
    """p: dict of parameters. Returns {piece_name: [solid, solid, ...]} (each solid = list of polys)
    plus a 'sheets' list of (name, poly) flat polygons (heart glow)."""
    span = p["span"]
    ph = p["pier_height"]
    lancet = max(p["lancet"], 0.78)  # < 0.78 makes R-a negative (rounded, not pointed)
    layers = int(p["rib_layers"])
    rw = p["rib_width"]
    rd = p["rib_depth"]
    step = p["layer_step"]
    cusps = int(p["cusps_per_rib"])
    cs = p["cusp_size"]
    stretchers = int(p["stretchers"])
    segs = int(p["arc_segments"])
    hsegs = int(p["heart_segments"])
    seed = int(p["seed"])
    preview = bool(p.get("preview_mode", 0))
    if preview:
        segs = max(6, segs // 4)
        hsegs = max(16, hsegs // 3)
        cusps = 0
        stretchers = 0

    a = span * 0.5
    R = lancet * span
    out = {"rib": [], "pier": [], "cusp": [], "stretcher": [], "heart_frame": [], "heart_stem": []}
    sheets = []

    def rnd(i):
        return (math.sin((i + 1) * 12.9898 + seed * 78.233) * 43758.5453) % 1.0

    z0, z1 = -rd * 0.5, rd * 0.5
    curves = []
    for k in range(layers):
        d = k * step
        r_out = R - d
        r_in = R - d - rw
        outer, c_r, c_l, th_a, ya_out = _arch_curve(a, ph, R, r_out, segs)
        inner, _, _, _, ya_in = _arch_curve(a, ph, R, r_in, segs)
        curves.append((outer, inner, r_out, r_in))
        out["rib"].append(strip_solid(outer, inner, z0, z1, False))
        # pier column under this rib (springing at x = +-(a - d - ...)); width follows the rib
        for side in (-1, 1):
            xo = side * outer[-1][0] if side > 0 else outer[0][0]
            xi = side * inner[-1][0] if side > 0 else inner[0][0]
            cx = 0.5 * (xo + xi)
            out["pier"].append(box(cx, ph * 0.5, abs(xo - xi) * 0.5, ph * 0.5, z0, z1))

    # plinth under both piers
    for side in (-1, 1):
        out["pier"].append(box(side * (a - step * (layers - 1) * 0.5 - rw * 0.5), 0.0,
                               rw * 0.5 + step * (layers - 1) * 0.5 + 0.12, 0.09, z0 - 0.08, z1 + 0.08))

    # innermost clear opening
    in_outer, in_inner, r_out_i, r_in_i = curves[-1]
    apex_in_y = max(y for _, y in in_inner)

    # radial stretchers between adjacent ribs
    if stretchers > 0 and layers > 1:
        cxr = a - R
        th_a_full = math.acos(max(min((-cxr) / (R - rw), 1.0), -1.0))
        for k in range(layers - 1):
            r_hi = R - k * step - rw
            r_lo = R - (k + 1) * step
            for side in (-1, 1):
                for j in range(stretchers):
                    th = th_a_full * (0.12 + 0.82 * (j + 0.5) / stretchers)
                    cx_c = side * cxr
                    ux = math.cos(th) * (1 if side > 0 else -1)
                    uy = math.sin(th)
                    hw = 0.035
                    p0 = (cx_c + ux * r_lo, ph + uy * r_lo)
                    p1 = (cx_c + ux * r_hi, ph + uy * r_hi)
                    tx, ty = -uy, ux
                    quad = [(p0[0] - tx * hw, p0[1] - ty * hw), (p0[0] + tx * hw, p0[1] + ty * hw),
                            (p1[0] + tx * hw, p1[1] + ty * hw), (p1[0] - tx * hw, p1[1] - ty * hw)]
                    out["stretcher"].append(prism(quad, z0 * 0.6, z1 * 0.6))

    # cordiform heart, hung from the apex on a stem
    hw_req = p["heart_width"]
    cy = ph + p["heart_height_frac"] * (apex_in_y - ph)
    s_w = hw_req / 32.0
    s_h = (apex_in_y - cy - 0.30) / 29.0
    # opening half-width at the heart's widest height must clear the innermost rib
    s_c = (a - (layers - 1) * step - rw - 0.25) / 16.0
    s = max(min(s_w, s_h, s_c), 0.02)
    outline = heart_outline(s, hsegs)
    outline = [(x, y + cy + 17.0 * s) for x, y in outline]  # tip floats above cy-ish; keep cy as tip height
    ox, oy = 0.0, cy + 17.0 * s
    # cusp keep-out: the heart outline grown by 0.08 m; cusps that touch it are skipped
    # (review 2026-10-23: the two cusps nearest the lobes pierced the heart frame)
    _grow = 1.0 + 0.08 / (16.0 * s)
    keepout = [(ox + (x - ox) * _grow, oy + (y - oy) * _grow) for x, y in outline]
    def _in_poly(pt, poly):
        x, y = pt
        c = False
        for i in range(len(poly)):
            x0, y0 = poly[i]
            x1, y1 = poly[(i + 1) % len(poly)]
            if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
                c = not c
        return c

    # cusps hang from the innermost intrados (spearhead leaf)
    if cusps > 0:
        cxr = a - R
        for side in (-1, 1):
            cx_c = side * cxr
            th_a2 = math.acos(max(min((-cxr) / r_in_i, 1.0), -1.0))
            for j in range(cusps):
                th = th_a2 * (0.10 + 0.84 * (j + 0.5) / cusps)
                ux = math.cos(th) * (1 if side > 0 else -1)
                uy = math.sin(th)
                cj = cs * (0.85 + 0.3 * rnd(j + (7 if side > 0 else 0)))
                bx, by = cx_c + ux * r_in_i, ph + uy * r_in_i
                nx, ny = -ux, -uy          # inward (toward arc centre)
                tx, ty = -uy, ux
                loc = [(-0.5 * cj, -0.05), (0.5 * cj, -0.05), (0.30 * cj, 0.5 * cj), (0.0, 1.5 * cj), (-0.30 * cj, 0.5 * cj)]
                poly = [(bx + tx * u + nx * v, by + ty * u + ny * v) for u, v in loc]
                probe = []
                for q in range(len(poly)):
                    q0, q1 = poly[q], poly[(q + 1) % len(poly)]
                    probe += [(q0[0] + (q1[0] - q0[0]) * f, q0[1] + (q1[1] - q0[1]) * f) for f in (0.0, 0.33, 0.66)]
                if any(_in_poly(pt, keepout) for pt in probe) or any(_in_poly(pt, poly) for pt in outline):
                    continue
                out["cusp"].append(prism(poly, z0 * 0.7, z1 * 0.7))

    fw = p["heart_frame_width"]
    half = 16.0 * s
    k = max(1.0 - fw / half, 0.15)
    inner_h = [(ox + (x - ox) * k, oy + (y - oy) * k) for x, y in outline]
    hz0, hz1 = -rd * 0.3, rd * 0.3
    out["heart_frame"].append(strip_solid(outline, inner_h, hz0, hz1, True))
    # glow sheets (front +Z / back -Z), fan from the curve origin
    for zc, nz in ((0.0 + 0.005, 1.0), (0.0 - 0.005, -1.0)):
        for i in range(hsegs):
            j = (i + 1) % hsegs
            tri = [(ox, oy, zc), (inner_h[i][0], inner_h[i][1], zc), (inner_h[j][0], inner_h[j][1], zc)]
            nrm = _newell(tri)
            # Houdini normal = -rhs ; want sign(nz)
            if (-nrm[2]) * nz < 0.0:
                tri = list(reversed(tri))
            sheets.append(("heart_glow", tri))
    # stem from heart cleft (y at x=0 is 5s above origin) to the apex intrados
    cleft_y = oy + 5.0 * s
    top = apex_in_y + 0.03
    out["heart_stem"].append(box(0.0, 0.5 * (cleft_y - 0.02 + top), 0.03, 0.5 * (top - cleft_y + 0.02), -0.04, 0.04))

    meta = {"apex_y": apex_in_y, "heart_scale": s, "heart_centre_y": oy,
            "outer_apex_y": max(y for _, y in curves[0][0]),
            "R": R, "segments": segs, "preview": preview}
    return out, sheets, meta
