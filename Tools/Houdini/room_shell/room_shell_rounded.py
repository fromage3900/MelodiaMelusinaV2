"""Melodia rounded room shell: a curved-plan salon shell (ellipse / superellipse / polygon)
with exact named floor-level portals, in the same native frame and output contract as
room_shell.py.

Metres, Z-up. The *interior* boundary is a closed plan curve inscribed in [0,W] x [0,D];
walls grow OUTWARD by wall_t, so the exterior AABB is [-t, W+t] x [-t, D+t] exactly like the
rectangular shell. Interior floor plane is z=0; clear ceiling is z=H.

Portals are addressed by `theta` (fraction of perimeter, 0..1, counter-clockwise from +X
through the room centre) and `width` (metres of true arc length). Every portal edge is
inserted as a plan vertex, so jambs land exactly on the cut instead of being stair-stepped
by the curve tessellation - that is what `aperture_jambs_exact` gates.

Self-contained (no project imports) so it can be embedded in an HDA PythonModule.
Faces are stored in Houdini's clockwise-front winding (Mesh.poly reverses a right-hand
outward face), mirrored from room_shell.py so both graphs share one winding contract.
"""
import json
import math

TAU = math.tau

# --------------------------------------------------------------------------- mesh helpers
# Mirrored from room_shell.py: identical storage contract (Mesh.poly reverses CCW input).
class Mesh:
    def __init__(self):
        self.P = []
        self.F = []
        self.R = []

    def poly(self, pts, role):
        s = len(self.P)
        self.P.extend(pts)
        self.F.append(list(reversed(range(s, len(self.P)))))
        self.R.append(role)


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a):
    l = math.sqrt(a[0] ** 2 + a[1] ** 2 + a[2] ** 2) or 1.0
    return (a[0] / l, a[1] / l, a[2] / l)


def box(M, a, b, role):
    x, y, z = a
    X, Y, Z = b
    p = [(x, y, z), (X, y, z), (X, Y, z), (x, Y, z), (x, y, Z), (X, y, Z), (X, Y, Z), (x, Y, Z)]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        M.poly([p[i] for i in f], role)


def hexa_rings(M, bot, top, role, flip=False):
    """Closed solid from a bottom ring and a top ring (each 4 pts, CCW seen from +z)."""
    if flip:
        bot = [bot[0], bot[3], bot[2], bot[1]]
        top = [top[0], top[3], top[2], top[1]]
    p = bot + top
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        M.poly([p[i] for i in f], role)


def prism(M, pts2, z0, z1, role, cx=None, cy=None):
    """Extrude a star-shaped CCW polygon (about its centroid) between z0 and z1."""
    n = len(pts2)
    cx = sum(p[0] for p in pts2) / n if cx is None else cx
    cy = sum(p[1] for p in pts2) / n if cy is None else cy
    for i in range(n):
        a, b = pts2[i], pts2[(i + 1) % n]
        M.poly([(cx, cy, z1), (a[0], a[1], z1), (b[0], b[1], z1)], role)
        M.poly([(cx, cy, z0), (b[0], b[1], z0), (a[0], a[1], z0)], role)
        M.poly([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], role)


def strip(M, p, q, w, z, role):
    dx, dy = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dy)
    if L < 1e-6:
        return
    nx, ny = -dy / L * w / 2, dx / L * w / 2
    M.poly([(p[0] - nx, p[1] - ny, z), (q[0] - nx, q[1] - ny, z), (q[0] + nx, q[1] + ny, z), (p[0] + nx, p[1] + ny, z)], role)


def _area2(ring):
    return sum(ring[i][0] * ring[(i + 1) % len(ring)][1] - ring[(i + 1) % len(ring)][0] * ring[i][1] for i in range(len(ring)))


def _ensure_ccw(ring):
    return list(ring) if _area2(ring) > 0 else list(reversed(ring))


def signed_volume_righthand(M):
    v = 0.0
    for f in M.F:
        pts = [M.P[i] for i in reversed(f)]
        a = pts[0]
        for i in range(1, len(pts) - 1):
            b, c = pts[i], pts[i + 1]
            n = _cross(_sub(b, a), _sub(c, a))
            v += (a[0] * n[0] + a[1] * n[1] + a[2] * n[2]) / 6
    return v


# --------------------------------------------------------------------------- plan curve
SHAPES = ("ellipse", "superellipse", "polygon")


def plan_curve(shape, a, b, sides, exponent, n):
    """Closed CCW plan polyline around (0,0), inscribed in the a x b half-extent box."""
    if shape not in SHAPES:
        raise ValueError("plan shape must be one of %s" % (SHAPES,))
    pts = []
    if shape == "polygon":
        if sides < 5 or sides > 64:
            raise ValueError("plan_sides must be between 5 and 64")
        verts = [(a * math.cos(TAU * k / sides), b * math.sin(TAU * k / sides)) for k in range(sides)]
        steps = max(2, int(round(n / sides)))
        for k in range(sides):
            p, q = verts[k], verts[(k + 1) % sides]
            for i in range(steps):
                t = i / steps
                pts.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
        return pts
    e = 1.0
    if shape == "superellipse":
        e = 2.0 / max(exponent, 2.0)
    for i in range(n):
        th = TAU * i / n
        c, s = math.cos(th), math.sin(th)
        if shape == "ellipse":
            x, y = a * c, b * s
        else:
            x = a * math.copysign(abs(c) ** e, c)
            y = b * math.copysign(abs(s) ** e, s)
        pts.append((x, y))
    return pts


def plan_at(shape, a, b, sides, exponent, t):
    """Single point at parametric angle t (fraction of a turn)."""
    e = 2.0 / max(exponent, 2.0) if shape == "superellipse" else 1.0
    th = TAU * t
    c, s = math.cos(th), math.sin(th)
    if shape == "ellipse":
        return (a * c, b * s)
    return (a * math.copysign(abs(c) ** e, c), b * math.copysign(abs(s) ** e, s))


class Arc:
    """Arc-length table over a closed polyline."""

    def __init__(self, pts):
        if len(pts) < 3:
            raise ValueError("plan polyline needs at least 3 points")
        self.pts = list(pts)
        self.cum = [0.0]
        for p, q in zip(self.pts, self.pts[1:] + self.pts[:1]):
            self.cum.append(self.cum[-1] + math.hypot(q[0] - p[0], q[1] - p[1]))
        self.total = self.cum[-1]
        if self.total <= 1e-6:
            raise ValueError("plan perimeter collapsed")

    def at(self, s):
        s = s % self.total
        lo, hi = 0, len(self.cum) - 1
        while lo < hi - 1:
            mid = (lo + hi) // 2
            if self.cum[mid] <= s:
                lo = mid
            else:
                hi = mid
        p, q = self.pts[lo % len(self.pts)], self.pts[(lo + 1) % len(self.pts)]
        span = self.cum[lo + 1] - self.cum[lo]
        t = 0.0 if span < 1e-12 else (s - self.cum[lo]) / span
        return (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)


def _outward(prev, nxt):
    dx, dy = nxt[0] - prev[0], nxt[1] - prev[1]
    n = (dy, -dx)
    L = math.hypot(n[0], n[1]) or 1.0
    return (n[0] / L, n[1] / L)


def _arc_pos(arc, p):
    """Arc-length position of the dense plan point nearest to p."""
    best, besti = 1e18, 0
    for i, q in enumerate(arc.pts):
        d = (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2
        if d < best:
            best, besti = d, i
    return arc.cum[besti]


def _poly_dist(pts, p):
    """Distance from p to a closed polyline."""
    best = 1e18
    n = len(pts)
    for i in range(n):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
        best = min(best, math.hypot(p[0] - (ax + dx * t), p[1] - (ay + dy * t)))
    return best


def _s_on_plan(pts, p):
    """Exact (arc position, distance) of p projected onto the closed plan polyline."""
    n = len(pts)
    cum = [0.0]
    for i in range(n):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % n]
        cum.append(cum[-1] + math.hypot(bx - ax, by - ay))
    best, best_s = 1e18, 0.0
    for i in range(n):
        ax, ay = pts[i]
        bx, by = pts[(i + 1) % n]
        dx, dy = bx - ax, by - ay
        L2 = dx * dx + dy * dy
        t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / L2))
        qx, qy = ax + dx * t, ay + dy * t
        d = math.hypot(p[0] - qx, p[1] - qy)
        if d < best:
            best, best_s = d, cum[i] + t * math.sqrt(L2)
    return best_s, best


# --------------------------------------------------------------------------- portals
def validate_openings(records, perimeter, H):
    """Named floor-level portals in native metres / perimeter fractions."""
    if not isinstance(records, list):
        raise ValueError("rounded openings must be an array")
    result = []
    ids = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("each opening must be an object")
        name = record.get("id")
        if not isinstance(name, str) or not name.strip() or name in ids:
            raise ValueError("opening ids must be unique nonempty strings")
        if record.get("kind", "door") != "door":
            raise ValueError("rounded openings currently support floor-level doors only")
        values = []
        for key in ("theta", "width", "height"):
            value = record.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("opening %s must be a finite number" % key)
            values.append(float(value))
        theta, width, height = values
        if not (0.0 <= theta <= 1.0):
            raise ValueError("opening theta is a perimeter fraction in [0,1]")
        theta = 0.0 if theta >= 1.0 else theta
        if width <= 0 or height <= 0 or height > H - 0.6:
            raise ValueError("opening size must be positive with 0.6 m of wall above")
        if width >= perimeter * 0.5:
            raise ValueError("opening width must be under half the perimeter")
        centre = theta * perimeter
        s0 = centre - width / 2.0
        for other in result:
            d = abs(((centre - other["s_centre"]) + perimeter / 2.0) % perimeter - perimeter / 2.0)
            if d < (width + other["width"]) / 2.0 - 1e-6:
                raise ValueError("openings on the same perimeter overlap or touch")
        result.append(dict(id=name, theta=theta, s_centre=centre, s0=s0, s1=s0 + width, width=width, height=height, kind="door"))
        ids.add(name)
    return result


def _in_arc(s, s0, width, P):
    return ((s - s0) % P) <= width


# --------------------------------------------------------------------------- build
DEFAULTS = dict(
    W=7.0, D=9.0, H=3.4, wall_t=0.24, shape="ellipse", sides=16, exponent=2.6,
    segments=96, floor_t=0.12, ceil_t=0.18, skirting=True, chair_rail=True, floor_medallion=True,
)


def build(**kw):
    p = dict(DEFAULTS)
    p.update({k: v for k, v in kw.items() if v is not None})
    W, D, H, t = float(p["W"]), float(p["D"]), float(p["H"]), float(p["wall_t"])
    if W <= 0 or D <= 0 or H <= 0 or t <= 0:
        raise ValueError("W, D, H and wall_t must be positive")
    if t >= min(W, D) * 0.25:
        raise ValueError("wall_t is too thick for this plan")
    shape, sides, exponent = p["shape"], int(p["sides"]), float(p["exponent"])
    segments = max(16, int(p["segments"]))
    cx, cy = W / 2.0, D / 2.0
    a, b = W / 2.0, D / 2.0

    dense = [(x + cx, y + cy) for x, y in plan_curve(shape, a, b, sides, exponent, 2048)]
    arc = Arc(dense)
    P = arc.total
    openings = validate_openings(p.get("openings") or [], P, H)

    # Boundaries: uniform tessellation plus every portal edge, so jambs are exact.
    cuts = set()
    for k in range(segments):
        cuts.add(round(P * k / segments, 6))
    for q in openings:
        cuts.add(round(q["s0"] % P, 6))
        cuts.add(round(q["s1"] % P, 6))
    boundaries = sorted(cuts) + [P]

    verts = [arc.at(s) for s in boundaries]
    nrm = []
    for i in range(len(boundaries) - 1):
        prev = verts[i - 1] if i > 0 else verts[-2]
        nxt = verts[i + 1]
        nrm.append(_outward(prev, nxt))
    nrm.append(_outward(verts[-2], verts[1]))

    M = Mesh()
    report = dict(params=dict(W=W, D=D, H=H, wall_t=t, shape=shape, sides=sides, exponent=exponent,
                              segments=segments, perimeter_m=round(P, 4), openings=len(openings)),
                  openings=[], sockets=[], joints=[], windows=[], door=None, chladni=None, streamers=None,
                  solids=0)

    # ---- walls (band segments, aperture-aware)
    half_open = []
    for i in range(len(boundaries) - 1):
        s_mid = (boundaries[i] + boundaries[i + 1]) / 2.0
        hit = None
        for q in openings:
            if _in_arc(s_mid, q["s0"], q["width"], P):
                hit = q
                break
        half_open.append(hit)

    for i, q in enumerate(half_open):
        pi, pj = verts[i], verts[i + 1]
        ni, nj = nrm[i], nrm[i + 1]
        qi = (pi[0] + ni[0] * t, pi[1] + ni[1] * t)
        qj = (pj[0] + nj[0] * t, pj[1] + nj[1] * t)
        ring2 = _ensure_ccw([pi, qi, qj, pj])
        if q is None:
            spans = [(0.0, H)]
        else:
            spans = [(q["height"], H)]
        for z0, z1 in spans:
            if z1 - z0 < 1e-6:
                continue
            hexa_rings(M, [(x, y, z0) for x, y in ring2], [(x, y, z1) for x, y in ring2], "wall")
            report["solids"] += 1

    # ---- floor slab, tucked under the wall band (outer curve)
    outer2 = [(verts[i][0] + nrm[i][0] * t, verts[i][1] + nrm[i][1] * t) for i in range(len(verts) - 1)]
    floor_ring = _ensure_ccw(outer2)
    prism(M, floor_ring, -float(p["floor_t"]), 0.0, "stone", cx, cy)
    report["solids"] += 1

    # ---- ceiling slab above the clear height
    prism(M, floor_ring, H, H + float(p["ceil_t"]), "wall_plaster", cx, cy)
    report["solids"] += 1

    # ---- interior bands follow the same curve: skirting / chair rail / cornice
    def band(z0, z1, proj, role, skip_portals=False):
        for i in range(len(boundaries) - 1):
            if skip_portals and half_open[i] is not None:
                continue
            pi, pj = verts[i], verts[i + 1]
            ni, nj = nrm[i], nrm[i + 1]
            ri = (pi[0] - ni[0] * proj, pi[1] - ni[1] * proj)
            rj = (pj[0] - nj[0] * proj, pj[1] - nj[1] * proj)
            ring2 = _ensure_ccw([pi, ri, rj, pj])
            hexa_rings(M, [(x, y, z0) for x, y in ring2], [(x, y, z1) for x, y in ring2], role)
            report["solids"] += 1

    if p["skirting"]:
        band(0.0, 0.14, 0.025, "panel", skip_portals=True)
    if p["chair_rail"]:
        band(0.92, 0.99, 0.035, "trim_gold", skip_portals=True)
    band(H - 0.28, H, 0.16, "panel")           # cove / cornice foot runs over every header
    band(H - 0.10, H, 0.22, "trim_gold")       # gold fillet at the ceiling line

    # ---- elliptical floor medallion (concentric inlays)
    if p["floor_medallion"]:
        for frac, w, role in ((0.30, 0.055, "trim_gold"), (0.62, 0.085, "trim_gold"), (0.88, 0.045, "panel")):
            ring_pts = [(cx + a * frac * math.cos(TAU * k / 128), cy + b * frac * math.sin(TAU * k / 128)) for k in range(129)]
            for u, v in zip(ring_pts, ring_pts[1:]):
                strip(M, u, v, w, 0.004, role)
            report["solids"] += 1

    # ---- sockets + report
    for q in openings:
        smid = q["s0"] + q["width"] / 2.0
        pin = arc.at(smid)
        pprev = arc.at(smid - 1e-3)
        pnext = arc.at(smid + 1e-3)
        nout = _outward(pprev, pnext)
        rep = dict(id=q["id"], wall="CURVE", theta=round(q["theta"], 6),
                   centre_local_m=[round(pin[0], 6), round(pin[1], 6), 0.0],
                   inward=[round(-nout[0], 6), round(-nout[1], 6), 0.0], up=[0.0, 0.0, 1.0],
                   clear_width_m=q["width"], clear_height_m=q["height"], floor_z_m=0.0,
                   s0=round(q["s0"] % P, 6), s1=round(q["s1"] % P, 6), kind="door", native_cut=True)
        report["sockets"].append(rep)
        report["openings"].append(dict(q, centre_local_m=rep["centre_local_m"], inward=rep["inward"]))

    report["params"]["perimeter_m"] = round(P, 4)
    report["room"] = dict(anchor_ue_cm=[0.0, 0.0, 0.0], room_yaw_ue=0.0,
                          plan_shape=shape, perimeter_m=round(P, 4), interior_axes_m=[W, D])
    # kept for the gate only (not serialised into the HDA payload)
    report["_dense"] = dense
    report["_boundary_s"] = boundaries
    report["_inner_pts"] = verts[:-1]
    report["_half_open"] = [i for i, q in enumerate(half_open) if q is not None]
    return M, report


# --------------------------------------------------------------------------- gates
def gate(M, rep):
    p = rep["params"]
    W, D, H, t = p["W"], p["D"], p["H"], p["wall_t"]
    out = {}
    out["solid_volume_positive"] = signed_volume_righthand(M) > 0

    xs = [q[0] for q in M.P]
    ys = [q[1] for q in M.P]
    zs = [q[2] for q in M.P]
    tol = 1e-4
    out["bounds_ok"] = (min(xs) >= -t - tol and max(xs) <= W + t + tol
                        and min(ys) >= -t - tol and max(ys) <= D + t + tol
                        and min(zs) >= -0.12 - tol and max(zs) <= H + 0.18 + tol)

    P = p["perimeter_m"]
    boundary_s = rep.get("_boundary_s") or []
    # every portal edge must be a real plan vertex, so jambs are cuts not tessellation steps
    jambs_ok = True
    for q in rep["openings"]:
        for edge in (q["s0"] % P, q["s1"] % P):
            if not any(abs(((edge - b) + P / 2.0) % P - P / 2.0) <= 1e-6 for b in boundary_s):
                jambs_ok = False
    out["aperture_jambs_exact"] = jambs_ok

    # no wall geometry inside a portal below its header (exact projection on the dense plan)
    empty = True
    dense = rep.get("_dense") or []
    if rep["openings"] and dense:
        wall_base = []
        for face, role in zip(M.F, M.R):
            if role != "wall":
                continue
            for idx in face:
                q = M.P[idx]
                if abs(q[2]) < 1e-6:
                    wall_base.append(q)
        for q in rep["openings"]:
            for bp in wall_base:
                s, d = _s_on_plan(dense, bp)
                if d > 2e-3:
                    continue
                off = (s - q["s0"]) % P
                if 2e-3 < off < q["width"] - 2e-3:
                    empty = False
    out["portals_empty_below_header"] = empty

    out["apertures_floor_level"] = all(q.get("sill", 0) == 0 for q in rep["openings"])
    out["apertures_header_clear"] = all(q["height"] <= H - 0.6 + 1e-9 for q in rep["openings"])
    out["sockets_match_apertures"] = len(rep["sockets"]) == len(rep["openings"]) and [
        q["id"] for q in rep["sockets"]] == [q["id"] for q in rep["openings"]]

    # plan profile sanity: every wall-base corner must lie on the requested analytic plan
    shape, sides, exponent = p["shape"], p["sides"], p["exponent"]
    a, b = W / 2.0, D / 2.0
    cx, cy = W / 2.0, D / 2.0
    inner = rep.get("_inner_pts") or []
    worst = 1e18
    if inner:
        if shape == "polygon":
            poly = [(x + cx, y + cy) for x, y in plan_curve("polygon", a, b, sides, exponent, 512)]
            worst = max(_poly_dist(poly, q) for q in inner)
        else:
            n = 2.0 if shape == "ellipse" else exponent
            worst = 0.0
            for q in inner:
                xn = abs((q[0] - cx) / a)
                yn = abs((q[1] - cy) / b)
                val = xn ** n + yn ** n
                grad = n * math.sqrt((xn ** (n - 1) / a) ** 2 + (yn ** (n - 1) / b) ** 2)
                if grad > 1e-9:
                    worst = max(worst, abs(val - 1.0) / grad)
    out["plan_profile_error_mm"] = round(worst * 1000.0, 4) if worst < 1e17 else None
    out["plan_matches_shape"] = bool(inner) and worst <= 0.002

    out["walls_present"] = rep["solids"] > 0 and len(M.F) > 6 * p["segments"]
    out["all_pass"] = all(v for k, v in out.items() if isinstance(v, bool))
    out["prims"] = len(M.F)
    out["points"] = len(M.P)
    return out


# ---------------------------------------------------------------- HDA glue (runs inside Houdini)
def _uv(P, face):
    a, b, c = P[face[0]], P[face[1]], P[face[2]]
    n = _cross(_sub(b, a), _sub(c, a))
    ax = max(range(3), key=lambda i: abs(n[i]))
    return [((P[i][1], P[i][2]) if ax == 0 else (P[i][0], P[i][2]) if ax == 1 else (P[i][0], P[i][1])) for i in face]


def cook(node):
    import hou
    h = node.parent()
    shape_idx = int(h.evalParm("plan_shape"))
    kw = dict(
        W=h.evalParm("room_w"), D=h.evalParm("room_d"), H=h.evalParm("room_h"),
        wall_t=h.evalParm("wall_t"), shape=SHAPES[max(0, min(2, shape_idx))],
        sides=int(h.evalParm("plan_sides")), exponent=h.evalParm("plan_exponent"),
        segments=int(h.evalParm("plan_segments")),
        skirting=bool(h.evalParm("skirting")), chair_rail=bool(h.evalParm("chair_rail")),
        floor_medallion=bool(h.evalParm("floor_medallion")),
    )
    if h.parm("openings_json"):
        records = json.loads(h.evalParm("openings_json"))
        if records:
            kw["openings"] = records
        elif records != []:
            raise ValueError("explicit openings must be an array")
    M, rep = build(**kw)
    gt = gate(M, rep)
    g = node.geometry()
    g.clear()
    g.addAttrib(hou.attribType.Prim, "material_role", "")
    g.addAttrib(hou.attribType.Prim, "shop_materialpath", "")
    g.addAttrib(hou.attribType.Vertex, "uv", (0.0, 0.0, 0.0))
    g.addAttrib(hou.attribType.Global, "gate_json", "")
    g.addAttrib(hou.attribType.Global, "sockets_json", "")
    yup = bool(h.evalParm("engine_y_up"))
    P = [(q[0], q[2], -q[1]) for q in M.P] if yup else M.P
    pts = g.createPoints(P)
    flip = yup and bool(h.evalParm("engine_flip"))
    for face, role in zip(M.F, M.R):
        face = list(reversed(face)) if flip else face
        poly = g.createPolygon()
        poly.setAttribValue("material_role", role)
        poly.setAttribValue("shop_materialpath", "/mat/Cathedral_" + role)
        uvs = _uv(M.P, face)
        for i, uv in zip(face, uvs):
            v = poly.addVertex(pts[i])
            v.setAttribValue("uv", (uv[0] * 0.5, uv[1] * 0.5, 0.0))
    payload = dict(sockets=rep["sockets"], windows=[], door=None, chladni=None, streamers=None,
                   room=rep["room"], opening_sockets=rep["sockets"], plan=rep["params"])
    g.setGlobalAttribValue("gate_json", json.dumps(gt))
    g.setGlobalAttribValue("sockets_json", json.dumps(payload))


# --------------------------------------------------------------------------- self-test
if __name__ == "__main__":
    import sys
    W, D, H = 15.84, 12.06, 7.6
    portals = [dict(id="salon_entry", theta=0.25, width=1.8, height=3.2),
               dict(id="salon_front", theta=0.75, width=2.4, height=3.2)]
    ok = True
    for shape, sides, expo in (("ellipse", 16, 2.0), ("superellipse", 16, 2.6), ("polygon", 16, 2.0)):
        M, rep = build(W=W, D=D, H=H, wall_t=0.24, shape=shape, sides=sides, exponent=expo, segments=96, openings=portals)
        gt = gate(M, rep)
        print(json.dumps(dict(shape=shape, prims=gt["prims"], points=gt["points"],
                              perimeter=rep["params"]["perimeter_m"],
                              checks={k: v for k, v in gt.items() if isinstance(v, bool)},
                              all_pass=gt["all_pass"])))
        ok = ok and gt["all_pass"]
    sys.exit(0 if ok else 1)
