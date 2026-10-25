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
def validate_tiers(records):
    """Tier setbacks are exterior massing ratios: finite, in (0, 1], non-increasing, base 1.0.

    tiers[0] must be 1.0 so the floor slab (built at the full wall thickness) and
    the base footprint keep matching the interior AABB. A zero or negative ratio
    would emit a degenerate wall band, and an increasing ratio would grow the
    upper massing outward past the base - both are rejected instead of cooked.
    """
    if records is None or records == []:
        return [1.0]
    if not isinstance(records, (list, tuple)):
        raise ValueError("tier setbacks must be an array of ratios")
    tiers = []
    for value in records:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError("tier setback must be a finite number")
        value = float(value)
        if not 0.0 < value <= 1.0 + 1e-9:
            raise ValueError("tier setback must be in (0, 1]")
        tiers.append(min(value, 1.0))
    if abs(tiers[0] - 1.0) > 1e-9:
        raise ValueError("base tier must be 1.0 so the floor slab and base footprint stay exact")
    for lower, upper in zip(tiers, tiers[1:]):
        if upper > lower + 1e-9:
            raise ValueError("tier setbacks must be non-increasing")
    return tiers


def validate_openings(records, perimeter, H, bays=0):
    """Named floor-level portals in native metres / perimeter fractions / bay indices."""
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
        bay = 0
        if record.get("theta") is not None:
            theta = record.get("theta")
            if isinstance(theta, bool) or not isinstance(theta, (int, float)) or not math.isfinite(theta):
                raise ValueError("opening theta must be a finite number")
            theta = float(theta)
        elif record.get("bay") is not None:
            index = record.get("bay")
            if bays <= 0 or isinstance(index, bool) or not isinstance(index, (int, float)) or not math.isfinite(index):
                raise ValueError("opening bay needs a positive bay count and a finite index")
            bay = int(index)
            if bay < 1 or bay > bays:
                raise ValueError("opening bay index is 1-based and must fall inside the bay count")
            theta = (bay - 0.5) / float(bays)
        else:
            raise ValueError("opening needs theta (perimeter fraction) or bay (1-based bay index)")
        values = []
        for key in ("width", "height"):
            value = record.get(key)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
                raise ValueError("opening %s must be a finite number" % key)
            values.append(float(value))
        width, height = values
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
        result.append(dict(id=name, theta=theta, s_centre=centre, s0=s0, s1=s0 + width, width=width,
                           height=height, kind="door", bay=bay))
        ids.add(name)
    return result


def _in_arc(s, s0, width, P):
    return ((s - s0) % P) <= width


def _solid_ok(M, start):
    """Flip a just-added closed solid if its signed volume came out inward."""
    v = 0.0
    for f in M.F[start:]:
        pts = [M.P[i] for i in reversed(f)]
        a = pts[0]
        for i in range(1, len(pts) - 1):
            b, c = pts[i], pts[i + 1]
            n = _cross(_sub(b, a), _sub(c, a))
            v += (a[0] * n[0] + a[1] * n[1] + a[2] * n[2]) / 6.0
    if v < 0:
        for k in range(start, len(M.F)):
            M.F[k] = list(reversed(M.F[k]))
    return v


def beam3(M, a, b, w, d, role):
    """Rectangular section tube between two 3D points (curved-wall cord, mullion, archivolt)."""
    dx, dy, dz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
    L = math.sqrt(dx * dx + dy * dy + dz * dz)
    if L < 1e-9:
        return
    u = (dx / L, dy / L, dz / L)
    up = (0.0, 0.0, 1.0)
    s = _cross(u, up)
    if math.sqrt(s[0] ** 2 + s[1] ** 2 + s[2] ** 2) < 1e-6:
        s = _cross(u, (1.0, 0.0, 0.0))
    s = _norm(s)
    t = _norm(_cross(s, u))
    hw, hd = w / 2.0, d / 2.0

    def ring(p):
        return [
            (p[0] + s[0] * hw + t[0] * hd, p[1] + s[1] * hw + t[1] * hd, p[2] + s[2] * hw + t[2] * hd),
            (p[0] - s[0] * hw + t[0] * hd, p[1] - s[1] * hw + t[1] * hd, p[2] - s[2] * hw + t[2] * hd),
            (p[0] - s[0] * hw - t[0] * hd, p[1] - s[1] * hw - t[1] * hd, p[2] - s[2] * hw - t[2] * hd),
            (p[0] + s[0] * hw - t[0] * hd, p[1] + s[1] * hw - t[1] * hd, p[2] + s[2] * hw - t[2] * hd),
        ]

    start = len(M.F)
    p8 = ring(a) + ring(b)
    e1 = _sub(p8[1], p8[0])
    e2 = _sub(p8[3], p8[0])
    e3 = _sub(p8[4], p8[0])
    if _cross(e1, e2)[0] * e3[0] + _cross(e1, e2)[1] * e3[1] + _cross(e1, e2)[2] * e3[2] < 0:
        p8 = [p8[3], p8[2], p8[1], p8[0], p8[7], p8[6], p8[5], p8[4]]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        M.poly([p8[i] for i in f], role)
    _solid_ok(M, start)


def sphere(M, c, r, role, lat=4, lon=7):
    """Low-poly bead. Winding is fixed by _solid_ok, so pearls can never render inside-out."""
    start = len(M.F)
    cx, cy, cz = c
    grid = []
    for i in range(lat + 1):
        th = math.pi * i / lat
        ring = []
        for j in range(lon):
            ph = TAU * j / lon
            ring.append((cx + r * math.sin(th) * math.cos(ph), cy + r * math.sin(th) * math.sin(ph), cz + r * math.cos(th)))
        grid.append(ring)
    for i in range(lat):
        for j in range(lon):
            j2 = (j + 1) % lon
            M.poly([grid[i][j], grid[i + 1][j], grid[i + 1][j2], grid[i][j2]], role)
    _solid_ok(M, start)


def star_pts(r_out, r_in, n=8, rot=0.0, cx=0.0, cy=0.0):
    return [((r_out if k % 2 == 0 else r_in) * math.cos(rot + TAU * k / (2 * n)) + cx,
             (r_out if k % 2 == 0 else r_in) * math.sin(rot + TAU * k / (2 * n)) + cy) for k in range(2 * n)]


def pointed_z(x, half, rise):
    """Two-centred pointed arch profile: 0 at the springing edges, `rise` at the apex."""
    if rise <= 1e-9 or half <= 1e-9:
        return 0.0
    c = (rise * rise - half * half) / (2.0 * half)
    R = half + c
    v = R * R - (abs(x) + c) ** 2
    return math.sqrt(v) if v > 0.0 else 0.0


def arch_cuts(half, rise, n=10):
    """x marks along a two-centred arch, sampled uniformly in arc angle on both halves."""
    if rise <= 1e-9 or half <= 1e-9:
        return [0.0]
    c = (rise * rise - half * half) / (2.0 * half)
    R = half + c
    out = []
    t0 = math.acos(max(-1.0, min(1.0, -c / R)))
    for i in range(n + 1):
        th = math.pi + (t0 - math.pi) * (i / float(n))
        out.append(c + R * math.cos(th))
    t1 = math.acos(max(-1.0, min(1.0, c / R)))
    for i in range(1, n + 1):
        th = t1 + (0.0 - t1) * (i / float(n))
        out.append(-c + R * math.cos(th))
    return out


# --------------------------------------------------------------------------- build
DEFAULTS = dict(
    W=7.0, D=9.0, H=3.4, wall_t=0.24, shape="ellipse", sides=16, exponent=2.6,
    segments=96, floor_t=0.12, ceil_t=0.18, skirting=True, chair_rail=True, floor_medallion=True,
    bays=0, bay_m=2.4, wall_panels=True, wall_beads=True, swag=True, arch_medallion=True,
    portal_head="pointed", arch_rise_ratio=0.55, archivolt=True,
    tiers=[],  # setback ratios per tier, e.g. [1.0, 0.85, 0.70]; empty = single volume
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

    # ---- bay rhythm: one bay is one bar of 4/4 on the 0.6 m beat grid
    bays = int(p["bays"])
    if bays <= 0:
        bays = max(4, int(round(P / max(0.6, float(p["bay_m"])))))
    bays = max(4, min(96, bays))
    bay_m = P / float(bays)

    tiers = validate_tiers(p.get("tiers"))

    openings = validate_openings(p.get("openings") or [], P, H, bays)

    # ---- portal heads: a pointed arch cut into the curve, apex at the clear height
    head = str(p["portal_head"]).lower()
    rise_ratio = float(p["arch_rise_ratio"])
    for q in openings:
        rise = 0.0
        if head in ("pointed", "ogive", "arch"):
            rise = min(q["width"] * rise_ratio, q["height"] - 1.95, q["height"] * 0.62)
            if rise < q["width"] * 0.5 * 0.75:
                rise = 0.0
        q["arch_rise"] = max(0.0, rise)
        q["spring"] = q["height"] - q["arch_rise"]
        q["pier_m"] = round(max(0.0, bay_m - q["width"]) / 2.0, 4)

    # Boundaries: uniform tessellation, every portal edge, and the arch's own angle-sampled
    # marks, so jambs are exact cuts and the arch soffit is a smooth staircase, not a wedge.
    cuts = set()
    for k in range(segments):
        cuts.add(round(P * k / segments, 6))
    for q in openings:
        cuts.add(round(q["s0"] % P, 6))
        cuts.add(round(q["s1"] % P, 6))
        if q["arch_rise"] > 0:
            for x in arch_cuts(q["width"] / 2.0, q["arch_rise"], 10):
                cuts.add(round((q["s_centre"] + x) % P, 6))
    ordered = sorted(cuts)
    boundaries = [b for i, b in enumerate(ordered) if i == 0 or b - ordered[i - 1] > 1e-6]
    if boundaries[0] > 1e-9:
        boundaries.insert(0, 0.0)
    if boundaries[-1] < P - 1e-9:
        boundaries.append(P)

    verts = [arc.at(s) for s in boundaries]
    nrm = []
    for i in range(len(boundaries) - 1):
        prev = verts[i - 1] if i > 0 else verts[-2]
        nxt = verts[i + 1]
        nrm.append(_outward(prev, nxt))
    nrm.append(_outward(verts[-2], verts[1]))

    M = Mesh()
    report = dict(params=dict(W=W, D=D, H=H, wall_t=t, shape=shape, sides=sides, exponent=exponent,
                              segments=segments, perimeter_m=round(P, 4), openings=len(openings), tiers=tiers),
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

    # ---- walls: tiered setbacks for solid segments, full-radius arch for portals
    tiers = [float(x) for x in (p.get("tiers") or [])]
    if not tiers:
        tiers = [1.0]
    n_tiers = len(tiers)
    tier_z = [H * (i + 1) / n_tiers for i in range(n_tiers)]
    tier_z0 = [0.0] + tier_z[:-1]

    for i, q in enumerate(half_open):
        in_portal = (q is not None)
        pi, pj = verts[i], verts[i + 1]
        ni, nj = nrm[i], nrm[i + 1]

        if in_portal:
            # full radius, arch profile all the way up
            qi = (pi[0] + ni[0] * t, pi[1] + ni[1] * t)
            qj = (pj[0] + nj[0] * t, pj[1] + nj[1] * t)
            ring2 = _ensure_ccw([pi, qi, qj, pj])
            s_mid = (boundaries[i] + boundaries[i + 1]) / 2.0
            if q["arch_rise"] > 0:
                dx = ((s_mid - q["s_centre"]) + P / 2.0) % P - P / 2.0
                z_clear = q["spring"] + pointed_z(dx, q["width"] / 2.0, q["arch_rise"])
            else:
                z_clear = q["height"]
            z0 = z_clear
            z1 = H
            if z1 - z0 >= 1e-6:
                hexa_rings(M, [(x, y, z0) for x, y in ring2], [(x, y, z1) for x, y in ring2], "wall")
                report["solids"] += 1
        else:
            # tiered setbacks for solid segments
            for tier_idx in range(n_tiers):
                setback = tiers[tier_idx]
                t_tier = t * setback
                z_bot = tier_z0[tier_idx]
                z_top = tier_z[tier_idx]
                qi = (pi[0] + ni[0] * t_tier, pi[1] + ni[1] * t_tier)
                qj = (pj[0] + nj[0] * t_tier, pj[1] + nj[1] * t_tier)
                ring2 = _ensure_ccw([pi, qi, qj, pj])
                z0 = z_bot
                z1 = z_top
                if z1 - z0 < 1e-6:
                    continue
                hexa_rings(M, [(x, y, z0) for x, y in ring2], [(x, y, z1) for x, y in ring2], "wall")
                report["solids"] += 1

    # cornice ledges at tier transitions (solid segments only)
    for tier_idx in range(n_tiers - 1):
        t_inner = t * tiers[tier_idx + 1]
        t_outer = t * tiers[tier_idx]
        z_ledge = tier_z[tier_idx]
        for i in range(len(boundaries) - 1):
            if half_open[i] is not None:
                continue
            pi, pj = verts[i], verts[i + 1]
            ni, nj = nrm[i], nrm[i + 1]
            oi = (pi[0] + ni[0] * t_outer, pi[1] + ni[1] * t_outer)
            oj = (pj[0] + nj[0] * t_outer, pj[1] + nj[1] * t_outer)
            ii = (pi[0] + ni[0] * t_inner, pi[1] + ni[1] * t_inner)
            ij = (pj[0] + nj[0] * t_inner, pj[1] + nj[1] * t_inner)
            ring2 = _ensure_ccw([oi, ii, ij, oj])
            ledge_h = 0.12
            hexa_rings(M, [(x, y, z_ledge) for x, y in ring2],
                       [(x, y, z_ledge + ledge_h) for x, y in ring2], "panel")
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

    epsn = 0.02

    def wall_pt(s, z, depth=0.0):
        """Interior wall-face point at arc mark `s`, height `z`, `depth` metres proud of the face."""
        pt = arc.at(s)
        n = _outward(arc.at(s - epsn), arc.at(s + epsn))
        return (pt[0] - n[0] * depth, pt[1] - n[1] * depth, z)

    def raised_field(s_a, s_b, z0, z1, proj, role):
        """Curve-following raised panel between two arc marks; doorway segments are skipped."""
        marks = [s_a] + [b for b in boundaries if s_a + 1e-6 < b < s_b - 1e-6] + [s_b]
        for u, v in zip(marks, marks[1:]):
            if v - u < 1e-6:
                continue
            if any(_in_arc((u + v) / 2.0, q["s0"], q["width"], P) for q in openings):
                continue
            pu, pv = arc.at(u), arc.at(v)
            nu = _outward(arc.at(u - epsn), arc.at(u + epsn))
            nv = _outward(arc.at(v - epsn), arc.at(v + epsn))
            ring2 = _ensure_ccw([pu, (pu[0] - nu[0] * proj, pu[1] - nu[1] * proj),
                                 (pv[0] - nv[0] * proj, pv[1] - nv[1] * proj), pv])
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

    # ---- bay-rhythm decoration: boiserie fields, bead strings, pearl swags, archivolts
    decor = dict(bays=bays, bay_m=round(bay_m, 4), beat_m=round(bay_m / 4.0, 4),
                 panels=0, bead_strings=0, beads=0, swags=0, archivolts=0, medallions=0)
    z_field0, z_field1 = 0.16, H - 0.46

    if p["wall_panels"] and bay_m >= 1.2:
        for k in range(bays):
            raised_field(k * bay_m + 0.10, (k + 1) * bay_m - 0.10,
                         z_field0 + 0.05, z_field1 - 0.05, 0.012, "panel")
            decor["panels"] += 1
        for k in range(1, bays):
            sc = k * bay_m
            if any(abs(((sc - q["s_centre"]) + P / 2.0) % P - P / 2.0) < q["width"] / 2.0 + 0.06 for q in openings):
                continue
            raised_field(sc - 0.028, sc + 0.028, z_field0, z_field1, 0.032, "panel")
            decor["panels"] += 1
        if not any(abs(((0.0 - q["s_centre"]) + P / 2.0) % P - P / 2.0) < q["width"] / 2.0 + 0.06 for q in openings):
            raised_field(0.0, 0.028, z_field0, z_field1, 0.032, "panel")
            raised_field(P - 0.028, P, z_field0, z_field1, 0.032, "panel")
            decor["panels"] += 2

    if p["wall_beads"]:
        z_top, z_bot, step = H - 0.55, 1.35, 0.13
        count = max(1, int((z_top - z_bot) / step))
        for k in range(1, bays, 3):
            sc = k * bay_m
            if any(abs(((sc - q["s_centre"]) + P / 2.0) % P - P / 2.0) < q["width"] / 2.0 + 0.06 for q in openings):
                continue
            prev = None
            for j in range(count + 1):
                c = wall_pt(sc, z_bot + j * step, 0.034)
                sphere(M, c, 0.0238, "pearl_shell", lat=3, lon=6)
                if prev is not None:
                    beam3(M, prev, c, 0.005, 0.005, "trim_gold")
                prev = c
            decor["bead_strings"] += 1
            decor["beads"] += count + 1
            report["solids"] += 1

    if p["swag"]:
        z_swag, droop, n_swag = H - 0.34, 0.20, 11
        for k in range(bays):
            sa, sb = k * bay_m + 0.09, (k + 1) * bay_m - 0.09
            prev = None
            for j in range(n_swag + 1):
                f = j / float(n_swag)
                c = wall_pt(sa + (sb - sa) * f, z_swag - droop * math.sin(math.pi * f), 0.058)
                end = j in (0, n_swag)
                sphere(M, c, 0.032 if end else 0.026, "trim_gold" if end else "pearl_shell", lat=3, lon=6)
                if prev is not None:
                    beam3(M, prev, c, 0.005, 0.005, "trim_gold")
                prev = c
            decor["swags"] += 1
            report["solids"] += 1

    if p["archivolt"]:
        for q in openings:
            if q["arch_rise"] <= 0:
                continue
            half = q["width"] / 2.0
            for band_i, (off, role, w) in enumerate(((0.0, "trim_gold", 0.050), (0.085, "panel", 0.065))):
                prev = None
                for j in range(29):
                    x = (j / 28.0 * 2.0 - 1.0) * (half + off)
                    c = wall_pt(q["s_centre"] + x,
                                q["spring"] + pointed_z(x, half + off, q["arch_rise"] + off),
                                0.024 + band_i * 0.014)
                    if prev is not None:
                        beam3(M, prev, c, w, w * 0.6, role)
                    prev = c
                decor["archivolts"] += 1
            apex = wall_pt(q["s_centre"], q["spring"] + q["arch_rise"] + 0.03, 0.038)
            box(M, (apex[0] - 0.058, apex[1] - 0.058, apex[2] - 0.05),
                (apex[0] + 0.058, apex[1] + 0.058, apex[2] + 0.15), "trim_gold")
            decor["archivolts"] += 1

    if p["arch_medallion"]:
        for q in openings:
            zc = q["height"] + 0.30
            for rr, role, w in ((0.19, "trim_gold", 0.022), (0.12, "panel", 0.028)):
                prev = None
                for j in range(25):
                    ang = TAU * j / 24.0
                    c = wall_pt(q["s_centre"] + rr * math.cos(ang), zc + rr * math.sin(ang), 0.022)
                    if prev is not None:
                        beam3(M, prev, c, w, w * 0.6, role)
                    prev = c
            star = star_pts(0.105, 0.048, 8, rot=math.pi / 2.0)
            loop = [(q["s_centre"] + x, zc + y) for x, y in star]
            for u, v in zip(loop, loop[1:] + loop[:1]):
                beam3(M, wall_pt(u[0], u[1], 0.024), wall_pt(v[0], v[1], 0.024), 0.018, 0.014, "trim_gold")
            decor["medallions"] += 1

    # ---- sockets + report
    for q in openings:
        smid = q["s0"] + q["width"] / 2.0
        pin = arc.at(smid)
        pprev = arc.at(smid - 1e-3)
        pnext = arc.at(smid + 1e-3)
        nout = _outward(pprev, pnext)
        rep = dict(id=q["id"], wall="CURVE", theta=round(q["theta"], 6), bay=q["bay"],
                   centre_local_m=[round(pin[0], 6), round(pin[1], 6), 0.0],
                   inward=[round(-nout[0], 6), round(-nout[1], 6), 0.0], up=[0.0, 0.0, 1.0],
                   clear_width_m=q["width"], clear_height_m=q["height"], floor_z_m=0.0,
                   spring_z_m=round(q["spring"], 6), arch_rise_m=round(q["arch_rise"], 6),
                   arch_profile="pointed" if q["arch_rise"] > 0 else "flat",
                   pier_m=q["pier_m"],
                   s0=round(q["s0"] % P, 6), s1=round(q["s1"] % P, 6), kind="door", native_cut=True)
        report["sockets"].append(rep)
        report["openings"].append(dict(q, centre_local_m=rep["centre_local_m"], inward=rep["inward"]))

    report["params"]["perimeter_m"] = round(P, 4)
    report["params"]["bays"] = bays
    report["params"]["bay_m_actual"] = round(bay_m, 4)
    report["decor"] = decor
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

    # ---- musical bay rhythm: the panelisation must land near one bar of 4/4
    bay_m = p.get("bay_m_actual") or 0.0
    out["bay_rhythm_ok"] = bool(p.get("bays")) and 1.2 <= bay_m <= 4.0

    # ---- pointed heads: the wall soffit above a portal must follow the arch profile
    tiers = p.get("tiers") or [1.0]
    n_tiers = len(tiers)
    out["tiers_valid"] = (abs(tiers[0] - 1.0) <= 1e-9
                          and all(0.0 < t <= 1.0 + 1e-9 for t in tiers)
                          and all(b <= a + 1e-9 for a, b in zip(tiers, tiers[1:])))
    soffit = []
    for face, role in zip(M.F, M.R):
        if role != "wall":
            continue
        for idx in face:
            v = M.P[idx]
            if not (1e-6 < v[2] <= 3.3 and v[2] < H - 1e-6):
                continue
            # only base-tier vertices (full radius) follow the arch profile
            s, d = _s_on_plan(dense, (v[0], v[1]))
            if abs(d - t) > 0.02:
                continue  # upper tier (setback) - skip
            soffit.append(v)
    worst_arch = 0.0
    for q in rep["openings"]:
        if q.get("arch_rise", 0.0) <= 0 or not soffit:
            continue
        half = q["width"] / 2.0
        for v in soffit:
            off = (_s_on_plan(dense, (v[0], v[1]))[0] - q["s0"]) % P
            if not (2e-3 < off < q["width"] - 2e-3):
                continue
            expect = q["spring"] + pointed_z(off - half, half, q["arch_rise"])
            worst_arch = max(worst_arch, abs(v[2] - expect))
    out["portal_arch_max_dev_m"] = round(worst_arch, 4)
    out["portal_arch_follows_profile"] = worst_arch <= 0.15

    # ---- decor must never run through a doorway
    in_door = False
    for face, role in zip(M.F, M.R):
        if role not in ("panel", "pearl_shell"):
            continue
        pts = [M.P[i] for i in face]
        for q in rep["openings"]:
            hits = 0
            for v in pts:
                s, d = _s_on_plan(dense, (v[0], v[1]))
                if d > 0.40:
                    continue
                off = (s - q["s0"]) % P
                if 2e-3 < off < q["width"] - 2e-3 and v[2] < q.get("spring", q["height"]) - 0.05:
                    hits += 1
            if hits == len(pts):
                in_door = True
    out["decor_clear_of_doorways"] = not in_door

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
    if h.parm("tiers_json"):
        raw = h.evalParm("tiers_json").strip()
        if raw:
            tiers = json.loads(raw)
            if not isinstance(tiers, list):
                raise ValueError("tier setbacks must be a JSON array")
            kw["tiers"] = tiers
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
