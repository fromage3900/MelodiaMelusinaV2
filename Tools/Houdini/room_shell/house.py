"""Melodia unified house assembler: ONE working procedural house system.

Composes the proven room cores (rect contact-floor + rounded salon) with
corridor links, switchback stairs, mansard roofs and a foundation pad — all in
the same material-role contract, socket frames, dressing surfaces and bay grid.
No second owner, no new material master, no new role vocabulary.

Frames: native module metres, Z-up, room interior corner at local origin.
Room placement = plan yaw about Z + plan offset. UE axis swap/mirror happens
once at emission, exactly like the room cores.
"""

import math
import json
import copy

try:  # standalone / hython: sibling library modules
    import room_shell as _rm
    import room_shell_rounded as _rr
    _RNS = {k: getattr(_rm, k) for k in dir(_rm) if not k.startswith('__')}
    _ONS = {k: getattr(_rr, k) for k in dir(_rr) if not k.startswith('__')}
except ImportError:  # embedded HDA PythonModule: packager exec() namespaces
    _RNS = _RectNS  # noqa: F821
    _ONS = _RoundedNS  # noqa: F821

ROLE_MATERIALS = _RNS['DEFAULT_ROLE_MATERIALS']
BAY_M = 2.4
RISE, RUN, STAIR_W = 0.17, 0.28, 1.20  # build_switchback_stairs walkability law

# Surface code order. Shared with the packager PCG branch: integer surf_id
# crosses the hou->VEX boundary (hou-written STRINGS read back empty in VEX),
# so the wrangle maps these codes back to names. Keep both lists identical.
SURF_ORDER = ['surface_floor', 'surface_wall', 'surface_ceiling',
              'surface_ledge', 'surface_sill', 'structure']


# ------------------------------------------------------------------ mesh ops
def _new():
    return _RNS['Mesh']()


def xform(M, yaw_deg=0.0, dx=0.0, dy=0.0, dz=0.0):
    """Plan yaw (degrees, CCW) about the local origin, then offset. In place."""
    c, s = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))
    M.P = [(x * c - y * s + dx, x * s + y * c + dy, z + dz) for (x, y, z) in M.P]
    return M


def _frame_pointoroset(pt, yaw_deg, dx, dy, dz=0.0):
    c, s = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))
    x, y = pt[0], pt[1]
    z = (pt[2] if len(pt) > 2 else 0.0) + dz
    return (x * c - y * s + dx, x * s + y * c + dy, z)


def merge(dst, src, group=None):
    """Append src mesh into dst; faces re-indexed, roles preserved.

    Per-face surface/room tags resolve in a final pass over recorded
    segments (see assemble); merge carries geometry + prim groups only.
    """
    base = len(dst.P)
    dst.P.extend(src.P)
    dst.F.extend([[i + base for i in f] for f in src.F])
    dst.R.extend(src.R)
    if group is not None:
        dst.G = getattr(dst, 'G', {})
        start = len(dst.F) - len(src.F)
        dst.G.setdefault(group, []).extend(range(start, len(dst.F)))
    return dst


def tag_classify(H, start, end, Hh, centre, room_id):
    """Classify faces [start:end) with the room-core surface rule."""
    surf = _RNS['dressing_surface']
    out = []
    for face, role in zip(H.F[start:end], H.R[start:end]):
        pts = [H.P[i] for i in reversed(face)]
        name = surf(role, pts, Hh, centre)
        out.append(((name or 'structure'), room_id))
    return out


def tag_force(H, start, end, value):
    """Uniform (surface, room) tag for non-classified spans."""
    return [value] * (end - start)


def slab_quad(M, q, t, role):
    """Closed thin slab over quad q (right-hand CCW from the dressed side).

    Both faces read correctly in UE. Returns the dressed-face index base;
    the dressed face is first, then back + 4 sides (6 faces total).
    """
    p0, p1, p2, p3 = q
    e1 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
    e2 = (p3[0] - p0[0], p3[1] - p0[1], p3[2] - p0[2])
    n = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2],
         e1[0] * e2[1] - e1[1] * e2[0])
    L = math.sqrt(sum(c * c for c in n)) or 1.0
    n = (n[0] / L * t, n[1] / L * t, n[2] / L * t)
    top = [(p[0] + n[0], p[1] + n[1], p[2] + n[2]) for p in q]
    base = len(M.P)
    M.P.extend(list(q) + top)
    # dressed face first (keeps meta alignment), then back + 4 sides
    M.F.append(list(reversed(range(base, base + 4))))
    M.R.append(role)
    M.F.append(list(range(base + 4, base + 8)))
    M.R.append(role)
    sides = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    for s in sides:
        M.F.append(list(reversed([base + k for k in s])))
        M.R.append(role)
    return 6


def _boxuv(P, face):
    a, b, c = P[face[0]], P[face[1]], P[face[2]]
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    n = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2],
         ab[0] * ac[1] - ab[1] * ac[0])
    ax = max(range(3), key=lambda i: abs(n[i]))
    if ax == 0:
        return [(P[i][1], P[i][2]) for i in face]
    if ax == 1:
        return [(P[i][0], P[i][2]) for i in face]
    return [(P[i][0], P[i][1]) for i in face]


def _poly_box(M, a, b, role):
    _RNS['box'](M, a, b, role)


# ------------------------------------------------------------------ rooms
def room_rect(spec):
    """Rect room from plan spec. Returns (M, sockets, surfaces, rep).

    Only variant-delta keys are passed; everything else inherits the
    converged module DEFAULTS (+ decor PRESETS), exactly like the staged
    variant HDAs. Invented values here once broke the panel/window gate.
    """
    kw = dict(W=spec['W'], D=spec['D'], H=spec['H'], wall_t=0.24,
              decor=spec.get('decor', 'paris_haussmann'),
              windows_long=spec.get('windows_long', 0),
              windows_short=spec.get('windows_short', 0),
              explicit_openings=spec.get('portals', []),
              simple_floor_collision=1,
              floor_medallion=spec.get('floor_medallion', True),
              skirting=spec.get('skirting', True),
              chair_rail=spec.get('chair_rail', True))
    M, rep = _RNS['build'](**kw)
    if not _RNS['gate'](M, rep).get('all_pass'):
        raise ValueError('rect room failed its own gate: %s' % spec.get('id'))
    sockets = [dict(s, room=spec.get('id')) for s in rep.get('opening_sockets', [])]
    return M, sockets, rep


def room_rounded(spec):
    """Rounded salon from plan spec. Returns (M, sockets, surfaces, rep)."""
    kw = dict(W=spec['W'], D=spec['D'], H=spec['H'], wall_t=0.24,
              floor_medallion=spec.get('floor_medallion', True),
              skirting=spec.get('skirting', True),
              chair_rail=spec.get('chair_rail', True),
              shape=spec.get('plan_shape', 'ellipse'),
              sides=spec.get('plan_sides', 16),
              exponent=spec.get('plan_exponent', 2.6),
              segments=spec.get('plan_segments', 96),
              bays=0, bay_m=spec.get('bay_m', BAY_M),
              tiers=spec.get('tiers', []),
              openings=spec.get('portals', []),
              portal_head=spec.get('portal_head', 'pointed'),
              arch_rise_ratio=spec.get('arch_rise_ratio', 0.55))
    M, rep = _ONS['build'](**kw)
    if not _ONS['gate'](M, rep).get('all_pass'):
        raise ValueError('rounded room failed its own gate: %s' % spec.get('id'))
    sockets = [dict(s, room=spec.get('id')) for s in rep.get('sockets', [])]
    return M, sockets, rep


def add_frill_polygons(mesh, parts, socket, offset=0.25, clearance=None):
    """Convert existing frill solids to a vertical portal frame, in metres."""
    cx, cy, cz = socket['center_world_m']
    ix, iy, _ = socket['inward_world']
    length = math.hypot(ix, iy)
    if length < 1e-8:
        raise ValueError('portal inward direction is zero')
    ix, iy = ix / length, iy / length
    tx, ty = -iy, ix
    if clearance is not None:
        width, height = clearance
        if width <= 0 or height <= 0:
            raise ValueError('clearance must be positive')
        for solids in parts.values():
            for faces in solids:
                for face in faces:
                    xs = [v[0] for v in face]
                    zs = [v[1] for v in face]
                    if min(xs) < width / 2 and max(xs) > -width / 2 and min(zs) < height and max(zs) > 0:
                        raise ValueError('frill face intersects clearance envelope')
    start = len(mesh.F)
    for part, solids in parts.items():
        role = 'ribbon_silk' if part == 'frill' else 'trim_gold'
        for faces in solids:
            for face in faces:
                mesh.poly([(cx + tx*x - ix*(depth+offset),
                            cy + ty*x - iy*(depth+offset), cz + height)
                           for x, height, depth in face], role)
    return len(mesh.F) - start


def place_room(M, sockets, spec):
    """Apply the plan transform; return world-frame sockets."""
    yaw, (dx, dy) = spec.get('yaw_deg', 0.0), spec.get('pos', [0.0, 0.0])
    dz = spec.get('dz', 0.0)
    xform(M, yaw, dx, dy, dz)
    out = []
    for s in sockets:
        c = s.get('center_local_m') or s.get('centre_local_m')
        inw = s.get('inward')
        pos = _frame_pointoroset(c, yaw, dx, dy, dz)
        ca, sa = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        inw2 = (inw[0] * ca - inw[1] * sa, inw[0] * sa + inw[1] * ca, 0.0)
        out.append(dict(s, center_world_m=pos, inward_world=inw2))
    return out


# ------------------------------------------------------------------ links
def solve_link(frame_a, portal_b_local):
    """Snap a room so its local portal frame coincides with world frame A.

    frame_a: world pos + inward. portal_b_local: local pos + inward.
    Returns (yaw_deg, dx, dy): yaw aligns -inwardB onto inwardA, offset lands
    the portal centres exactly on each other.
    """
    ax, ay = math.degrees(math.atan2(frame_a[4], frame_a[3])), 0.0
    bx, by = portal_b_local[0], portal_b_local[1]
    ang_a = math.degrees(math.atan2(-frame_a[4], -frame_a[3]))
    ang_b = math.degrees(math.atan2(by, bx)) if False else None
    ibx, iby = portal_b_local[2], portal_b_local[3]
    ang_b = math.degrees(math.atan2(iby, ibx))
    yaw = ang_a - ang_b
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    px, py = portal_b_local[0], portal_b_local[1]
    dx = frame_a[0] - (px * c - py * s)
    dy = frame_a[1] - (px * s + py * c)
    return yaw, dx, dy


def link_joint(M, fa, fb, width, height, wall_t=0.24):
    """Shared portal joint for two snapped rooms (coincident frames).

    Validates the clear openings match, then dresses the joint: a threshold
    plate in floor_stone plus a trim_gold architrave band on both faces.
    """
    if abs(width - 2.4) > 0.011 or abs(height - 3.2) > 0.011:
        raise ValueError('joint must carry the standard 2.4x3.2 portal')
    ax, ay, _, iax, iay = fa
    ux, uy = iax, iay
    nx, ny = -uy, ux
    hw = width / 2.0

    def obox(cx, cy, z0, z1, du, dv, role):
        b = [(cx - du * ux - dv * nx, cy - du * uy - dv * ny, z0),
             (cx + du * ux - dv * nx, cy + du * uy - dv * ny, z0),
             (cx + du * ux + dv * nx, cy + du * uy + dv * ny, z0),
             (cx - du * ux + dv * nx, cy - du * uy + dv * ny, z0),
             (cx - du * ux - dv * nx, cy - du * uy - dv * ny, z1),
             (cx + du * ux - dv * nx, cy + du * uy - dv * ny, z1),
             (cx + du * ux + dv * nx, cy + du * uy + dv * ny, z1),
             (cx - du * ux + dv * nx, cy - du * uy + dv * ny, z1)]
        _RNS['hexa'](M, b, role)

    oplate = [(ax - (hw + 0.05) * nx - 0.30 * ux, ay - (hw + 0.05) * ny - 0.30 * uy, -0.21),
              (ax + (hw + 0.05) * nx - 0.30 * ux, ay + (hw + 0.05) * ny - 0.30 * uy, -0.21),
              (ax + (hw + 0.05) * nx + 0.30 * ux, ay + (hw + 0.05) * ny + 0.30 * uy, -0.21),
              (ax - (hw + 0.05) * nx + 0.30 * ux, ay - (hw + 0.05) * ny + 0.30 * uy, -0.21),
              (ax - (hw + 0.05) * nx - 0.30 * ux, ay - (hw + 0.05) * ny - 0.30 * uy, 0.0),
              (ax + (hw + 0.05) * nx - 0.30 * ux, ay + (hw + 0.05) * ny - 0.30 * uy, 0.0),
              (ax + (hw + 0.05) * nx + 0.30 * ux, ay + (hw + 0.05) * ny + 0.30 * uy, 0.0),
              (ax - (hw + 0.05) * nx + 0.30 * ux, ay - (hw + 0.05) * ny + 0.30 * uy, 0.0)]
    _RNS['hexa'](M, oplate, 'floor_stone')
    for sgn in (1.0, -1.0):
        ox, oy = ux * sgn * (wall_t + 0.02), uy * sgn * (wall_t + 0.02)
        for sdx in (-1.0, 1.0):
            jx = ax + nx * sdx * (hw + 0.09) + ox
            jy = ay + ny * sdx * (hw + 0.09) + oy
            obox(jx, jy, 0.0, height + 0.12, 0.09, 0.09, 'trim_gold')
        obox(ax + ox, ay + oy, height, height + 0.21, hw + 0.18, 0.09, 'trim_gold')
    return dict(mode='joint', width_m=width, height_m=height)


def link_corridor(M, fa, fb, width, height, wall_t=0.24):
    """Straight corridor run between two world portal frames.

    fa/fb: (x, y, z, ix, iy) plan pos + inward. Ends stay open; the run carries
    floor, ceiling and two walls in the room contract roles.
    """
    ax, ay, _, iax, iay = fa
    bx, by, _, ibx, iby = fb
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy)
    if length < 0.3:
        raise ValueError('link run too short: %.3f' % length)
    ux, uy = dx / length, dy / length
    if ux * iax + uy * iay < 0.7 or (-ux) * ibx + (-uy) * iby < 0.7:
        raise ValueError('link run does not leave/enter through the portals')
    hw = width / 2.0
    nx, ny = -uy, ux
    corners = [(ax + nx * hw, ay + ny * hw), (ax - nx * hw, ay - ny * hw),
               (bx - nx * hw, by - ny * hw), (bx + nx * hw, by + ny * hw)]
    xs = [p[0] for p in corners] + [ax, bx]
    ys = [p[1] for p in corners] + [ay, by]
    lo = (min(xs) - wall_t, min(ys) - wall_t)
    hi = (max(xs) + wall_t, max(ys) + wall_t)

    def quad(p0, p1, p2, p3, role):
        base = len(M.P)
        M.P.extend([p0, p1, p2, p3])
        M.F.append(list(reversed(range(base, base + 4))))
        M.R.append(role)
        M.F.append(list(range(base, base + 4)))
        M.R.append(role)

    z0, z1 = 0.0, height
    quad((lo[0], lo[1], -0.2), (hi[0], lo[1], -0.2),
         (hi[0], hi[1], -0.2), (lo[0], hi[1], -0.2), 'floor_stone')
    quad((lo[0], lo[1], z1), (lo[0], hi[1], z1),
         (hi[0], hi[1], z1), (hi[0], lo[1], z1), 'wall_plaster')
    for sgn in (1.0, -1.0):
        ox, oy = nx * (hw + wall_t / 2) * sgn, ny * (hw + wall_t / 2) * sgn
        quad((ax + ox, ay + oy, 0.0), (bx + ox, by + oy, 0.0),
             (bx + ox, by + oy, z1), (ax + ox, ay + oy, z1), 'wall_plaster')
    return dict(length_m=round(length, 4), width_m=width, height_m=height)


# ------------------------------------------------------------------ stairs
def stair_run(M, x, y, z_top=0.0, drop=1.5, yaw_deg=0.0, width=STAIR_W):
    """Straight stair run descending away from a portal. Stone role.

    First tread sits one riser below the portal floor and extends outward
    along the local +X axis (yaw orients +X away from the room).
    """
    if drop <= 0:
        raise ValueError('stair must descend')
    n = max(1, int(math.ceil(drop / RISE)))
    rise = drop / n
    if rise > 0.20:
        raise ValueError('riser %.3f exceeds walkability' % rise)
    c, s = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))
    for i in range(n):
        zt = z_top - rise * i
        zb = zt - 0.3
        d0, d1 = i * RUN, (i + 1) * RUN
        corners = [(d0, -width / 2, zb), (d1, -width / 2, zb),
                   (d1, width / 2, zb), (d0, width / 2, zb),
                   (d0, -width / 2, zt), (d1, -width / 2, zt),
                   (d1, width / 2, zt), (d0, width / 2, zt)]
        pts = [(lx * c - ly * s + x, lx * s + ly * c + y, lz)
               for (lx, ly, lz) in corners]
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                  (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            base = len(M.P)
            M.P.extend([pts[k] for k in f])
            M.F.append(list(reversed(range(base, base + 4))))
            M.R.append('stone')
    return n


# ------------------------------------------------------------------ roof + pad
def roof_rect(M, W, D, H, wall_t=0.24, rise=1.8, overhang=0.6,
              yaw_deg=0.0, dx=0.0, dy=0.0):
    """Mansard sweep over a rect footprint. Pitch gated 15..60 deg."""
    pitch = math.degrees(math.atan2(rise, min(W, D) / 2.0 + overhang))
    if not 15.0 <= pitch <= 60.0:
        raise ValueError('roof pitch %.1f out of walkable-buildable band' % pitch)
    x0, x1 = -overhang, W + overhang
    y0, y1 = -overhang, D + overhang
    ridge = H + rise
    slopes = [((x0, y0, H), (x1, y0, H), (x1, y0 + D / 2, ridge), (x0, y0 + D / 2, ridge)),
              ((x0, y1, H), (x0, y0 + D / 2, ridge), (x1, y0 + D / 2, ridge), (x1, y1, H)),
              ((x0, y0, H), (x0, y0 + D / 2, ridge), (x0, y1, H), (x0, y0, H)),
              ((x1, y1, H), (x1, y0 + D / 2, ridge), (x1, y0, H), (x1, y1, H))]
    for q in slopes:
        base = len(M.P)
        M.P.extend([_frame_pointoroset(p, yaw_deg, dx, dy) for p in q])
        M.F.append(list(reversed(range(base, base + 4))))
        M.R.append('panel')
    c, s = math.cos(math.radians(yaw_deg)), math.sin(math.radians(yaw_deg))

    def beam_local(a, b, w, role):
        ax, ay = a[0] * c - a[1] * s + dx, a[0] * s + a[1] * c + dy
        bx, by = b[0] * c - b[1] * s + dx, b[0] * s + b[1] * c + dy
        _RNS['beam'](M, (ax, ay, a[2]), (bx, by, b[2]), w, w, role)

    beam_local((x0, y0 + D / 2, ridge), (x1, y0 + D / 2, ridge), 0.18, 'trim_gold')
    for ex, ey in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]:
        beam_local((ex, ey, H - 0.05), (ex, ey, H + 0.05), 0.24, 'trim_gold')
    return dict(pitch_deg=round(pitch, 2), ridge_m=round(ridge, 3))


def roof_round(M, W, D, H, tiers, yaw_deg=0.0, dx=0.0, dy=0.0,
               rise=1.6, overhang=0.5):
    """Conical tiered cap following the salon plan curve."""
    plan = _ONS['plan_curve']('ellipse', W / 2.0, D / 2.0, 16, 2.6, 96)
    top = tiers[-1] if tiers else 1.0
    levels = [(H, 1.0 + overhang / (W / 2.0)), (H + rise * 0.55, top * 0.72),
              (H + rise, top * 0.30)]
    for (z0, s0), (z1, s1) in zip(levels, levels[1:]):
        for (ax, ay), (bx, by) in zip(plan, plan[1:] + plan[:1]):
            p0 = _frame_pointoroset((ax * s0 + W / 2, ay * s0 + D / 2, z0), yaw_deg, dx, dy)
            p1 = _frame_pointoroset((bx * s0 + W / 2, by * s0 + D / 2, z0), yaw_deg, dx, dy)
            p2 = _frame_pointoroset((bx * s1 + W / 2, by * s1 + D / 2, z1), yaw_deg, dx, dy)
            p3 = _frame_pointoroset((ax * s1 + W / 2, ay * s1 + D / 2, z1), yaw_deg, dx, dy)
            base = len(M.P)
            M.P.extend([p0, p1, p2, p3])
            M.F.append(list(reversed(range(base, base + 4))))
            M.R.append('panel')
    cap = _frame_pointoroset((W / 2, D / 2, H + rise + 0.35), yaw_deg, dx, dy)
    _RNS['sphere'](M, cap, 0.22, 'trim_gold')
    return dict(levels=len(levels), cap_m=round(H + rise + 0.35, 3))


def pad_skirt(M, rooms, margin=1.2, top=-0.2, bottom=-1.4):
    """Foundation massing under the union footprint. Role stone."""
    xs, ys = [], []
    for r in rooms:
        xs += [r['bbox'][0][0] - margin, r['bbox'][1][0] + margin]
        ys += [r['bbox'][0][1] - margin, r['bbox'][1][1] + margin]
    _boxuv_box = None
    _poly_box(M, (min(xs), min(ys), bottom), (max(xs), max(ys), top), 'stone')
    return dict(x0=round(min(xs), 3), x1=round(max(xs), 3),
                y0=round(min(ys), 3), y1=round(max(ys), 3))


def _poly_box(M, a, b, role):
    _RNS['box'](M, a, b, role)


# ------------------------------------------------------------------ plans
SALON_FIRST = dict(
    rooms=[
        dict(id='salon', kind='rounded', W=16.8, D=12.0, H=7.2,
             floor_medallion=True, skirting=True, chair_rail=True,
             plan_shape='ellipse', plan_sides=16, plan_exponent=2.6,
             plan_segments=96, tiers=[1.0, 0.92, 0.84],
             portals=[dict(id='salon_entry', theta=0.25, width=2.4, height=3.2),
                      dict(id='salon_front', theta=0.75, width=2.4, height=3.2)],
             pos=[0.0, 0.0], yaw_deg=0.0, roof_rise=1.6),
        dict(id='landing', kind='rect', W=9.6, D=4.8, H=4.2,
             floor_medallion=True, skirting=True, chair_rail=True,
             decor='paris_haussmann', windows_long=1, windows_short=0,
             portals=[dict(id='landing_in', wall='W', s=2.4, width=2.4, height=3.2),
                      dict(id='landing_out', wall='E', s=2.4, width=2.4, height=3.2)],
             link_from=('salon', 'salon_front'), link_portal='landing_out',
             roof_rise=1.8),
    ],
    links=[dict(id='salon_landing_run',
                  pa=('salon', 'salon_front'), pb=('landing', 'landing_out'),
                  width=2.4, height=3.2)],
    stairs=[dict(id='porch_steps', room='landing', portal='landing_in',
                 run_m=1.5, width=2.4)],
    pad=dict(margin=1.2),
)


def _room_bbox(kind, spec):
    if kind == 'rect':
        return [[-0.24, -0.24, -0.2], [spec['W'] + 0.24, spec['D'] + 0.24, spec['H'] + 0.2]]
    return [[-0.24, -0.24, -0.12],
            [spec['W'] + 0.24, spec['D'] + 0.24, spec['H'] + 0.18]]


def assemble(plan):
    """Compose the whole house. Returns (M, rep). Fail-closed on every gate."""
    # Resolution adds diagnostic fields to links and stairs. Keep caller-owned
    # presets unchanged so repeated cooks do not carry results between runs.
    plan = copy.deepcopy(plan)
    H = _new()
    H.G = {}
    sockets_all = []
    rooms_built = []
    windows_all = []
    segs = []

    def grp(name, start):
        H.G.setdefault(name, []).extend(range(start, len(H.F)))

    placed = {}
    for spec in plan['rooms']:
        kind = spec['kind']
        if kind == 'rect':
            M, sockets, rep = room_rect(spec)
        elif kind == 'rounded':
            M, sockets, rep = room_rounded(spec)
        else:
            raise ValueError('unknown room kind: %s' % kind)
        if spec.get('link_from'):
            room_a, portal_a = spec['link_from']
            fa = next(s for s in sockets_all
                      if s['room'] == room_a and s['id'] == portal_a)
            pb = next(s for s in sockets if s['id'] == spec['link_portal'])
            c = pb.get('center_local_m') or pb.get('centre_local_m')
            ib = pb['inward']
            yaw, dx, dy = solve_link(
                (fa['center_world_m'][0], fa['center_world_m'][1], 0.0,
                 fa['inward_world'][0], fa['inward_world'][1]),
                (c[0], c[1], ib[0], ib[1]))
            spec = dict(spec, yaw_deg=yaw, pos=[dx, dy])
        if kind == 'rect':
            for window in rep.get('windows', []):
                wall = window['wall']
                midpoint = (window['s0'] + window['s1']) / 2.0
                zmid = (window['z0'] + window['z1']) / 2.0
                point = {'S': (midpoint, 0.0, zmid), 'N': (midpoint, spec['D'], zmid),
                         'W': (0.0, midpoint, zmid), 'E': (spec['W'], midpoint, zmid)}[wall]
                pos = spec.get('pos', [0.0, 0.0])
                world = _frame_pointoroset(point, spec.get('yaw_deg', 0.0), pos[0], pos[1], spec.get('dz', 0.0))
                nx, ny = {'S': (0.0, -1.0), 'N': (0.0, 1.0),
                          'W': (-1.0, 0.0), 'E': (1.0, 0.0)}[wall]
                angle = math.radians(spec.get('yaw_deg', 0.0))
                outward = (nx * math.cos(angle) - ny * math.sin(angle),
                           nx * math.sin(angle) + ny * math.cos(angle), 0.0)
                windows_all.append(dict(window, room=spec['id'], center_world_m=world,
                                        outward_world=outward, yaw_deg=spec.get('yaw_deg', 0.0)))
        sockets_w = place_room(M, sockets, spec)
        start = len(H.F)
        merge(H, M, group='room_' + spec['id'])
        yaw = spec.get('yaw_deg', 0.0)
        dx, dy = spec.get('pos', [0.0, 0.0])
        c, sn = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        wcx = (spec['W'] / 2.0) * c - (spec['D'] / 2.0) * sn + dx
        wcy = (spec['W'] / 2.0) * sn + (spec['D'] / 2.0) * c + dy
        segs.append(('classify', start, len(H.F), spec['H'], (wcx, wcy),
                     spec['id']))
        sockets_all.extend(sockets_w)
        placed[spec['id']] = spec
        xs = [p[0] for p in M.P]
        ys = [p[1] for p in M.P]
        rooms_built.append(dict(id=spec['id'], kind=kind, spec=spec,
                                bbox=[[min(xs), min(ys), -0.2],
                                      [max(xs), max(ys), spec['H'] + 0.2]]))

    for link in plan.get('links', []):
        fr = [s for s in sockets_all if (s['room'], s['id']) == tuple(link['pa'])]
        to = [s for s in sockets_all if (s['room'], s['id']) == tuple(link['pb'])]
        if len(fr) != 1 or len(to) != 1:
            raise ValueError('link %s must name exactly two portals'
                             % link.get('id'))
        fa, fb = fr[0], to[0]
        a = (fa['center_world_m'][0], fa['center_world_m'][1], 0.0,
             fa['inward_world'][0], fa['inward_world'][1])
        b = (fb['center_world_m'][0], fb['center_world_m'][1], 0.0,
             fb['inward_world'][0], fb['inward_world'][1])
        dist = math.hypot(b[0] - a[0], b[1] - a[1])
        if dist < 0.3:
            start = len(H.F)
            info = link_joint(H, a, b, link['width'], link['height'])
            info['mode'] = 'joint'
            mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
            segs.append(('classify', start, len(H.F), link['height'],
                         (mx, my), 'joint_' + link['id']))
            grp('joint_' + link['id'], start)
        else:
            start = len(H.F)
            info = link_corridor(H, a, b, link['width'], link['height'])
            info['mode'] = 'run'
            mx, my = (a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0
            segs.append(('classify', start, len(H.F), link['height'],
                         (mx, my), 'link_' + link['id']))
            grp('link_' + link['id'], start)
        link['resolved'] = info

    for st in plan.get('stairs', []):
        fr = next(s for s in sockets_all
                  if s['room'] == st['room'] and s['id'] == st['portal'])
        px, py = fr['center_world_m'][0], fr['center_world_m'][1]
        ix, iy = fr['inward_world'][0], fr['inward_world'][1]
        yaw_out = math.degrees(math.atan2(-iy, -ix))
        start = len(H.F)
        n = stair_run(H, px - ix * 0.3, py - iy * 0.3, z_top=0.0,
                      drop=st.get('drop_m', 1.5),
                      yaw_deg=yaw_out, width=st.get('width', STAIR_W))
        st['treads'] = n
        segs.append(('force', start, len(H.F),
                     ('structure', 'stair_' + st['id'])))
        grp('stair_' + st['id'], start)

    for rb in rooms_built:
        spec = rb['spec']
        start = len(H.F)
        if rb['kind'] == 'rect':
            rb['roof'] = roof_rect(H, spec['W'], spec['D'], spec['H'],
                                   yaw_deg=spec.get('yaw_deg', 0.0),
                                   dx=spec['pos'][0], dy=spec['pos'][1],
                                   rise=spec.get('roof_rise', 1.8))
        else:
            rb['roof'] = roof_round(H, spec['W'], spec['D'], spec['H'],
                                    spec.get('tiers', []),
                                    yaw_deg=spec.get('yaw_deg', 0.0),
                                    dx=spec['pos'][0], dy=spec['pos'][1],
                                    rise=spec.get('roof_rise', 1.6))
        segs.append(('force', start, len(H.F),
                     ('structure', 'roof_' + spec['id'])))
        grp('roof_' + spec['id'], start)
    start = len(H.F)
    pad = pad_skirt(H, rooms_built, **plan.get('pad', {}))
    pcx = (pad['x0'] + pad['x1']) / 2.0
    pcy = (pad['y0'] + pad['y1']) / 2.0
    segs.append(('classify', start, len(H.F), 1.0, (pcx, pcy), 'pad'))
    grp('pad', start)

    if plan.get('portal_frill'):
        spec = plan['portal_frill']
        socket = next(s for s in sockets_all if s['room'] == spec['room'] and s['id'] == spec['portal'])
        try:
            generator = _FrillNS['generate_frill']
        except NameError:
            from frill_arch_geometry import generate_frill as generator
        width = float(socket.get('clear_width_m', 2.4))
        params = dict(span=width+0.6, pier_height=1.2, lancet=1.0,
                      core_width=0.15, frill_layers=int(spec.get('layers', 3)),
                      frill_width=0.25, scallops=10, scallop_amp=0.02,
                      layer_dz=0.05, flower_petals=8, flower_radius=0.25,
                      arc_segments=48, seed=11)
        parts, _ = generator(params)
        start = len(H.F)
        add_frill_polygons(H, parts, socket, clearance=(1.2, 2.1))
        segs.append(('force', start, len(H.F), ('structure', 'portal_frill')))
        grp('portal_frill', start)

    H.meta = []
    for seg in segs:
        if seg[0] == 'classify':
            _, start, end, Hh, centre, room = seg
            H.meta.extend(tag_classify(H, start, end, Hh, centre, room))
        else:
            _, start, end, value = seg
            H.meta.extend(tag_force(H, start, end, value))
    assert len(H.meta) == len(H.F), 'meta/face count drift'
    face_area = _RNS['face_area']
    surfaces_total = {}
    for (name, _room), face in zip(H.meta, H.F):
        if name == 'structure':
            continue
        pts = [H.P[i] for i in reversed(face)]
        surfaces_total[name] = surfaces_total.get(name, 0.0) + face_area(pts)
    roles = {}
    for r in H.R:
        roles[r] = roles.get(r, 0) + 1
    rep = dict(rooms=rooms_built, links=plan.get('links', []),
               stairs=plan.get('stairs', []), pad=pad,
               sockets=sockets_all, windows=windows_all, surfaces=surfaces_total,
               roles=roles, prims=len(H.F), points=len(H.P))
    return H, rep


def gate(H, rep, plan):
    """House-level acceptance. Returns dict; all_pass is the only green."""
    out = {}
    out['rooms_all_pass'] = all(
        True for _ in rep['rooms']) and len(rep['rooms']) == len(plan['rooms'])
    out['links_resolved'] = all('resolved' in l for l in rep.get('links', []))
    out['roles_mapped'] = [r for r in rep['roles'] if r not in ROLE_MATERIALS]
    out['roles_mapped_ok'] = out['roles_mapped'] == []
    out['surfaces_nonzero'] = all(rep['surfaces'].get(k, 0.0) > 0.0
                                  for k in ('surface_floor', 'surface_wall',
                                            'surface_ceiling'))
    out['sockets_paired'] = len(rep['sockets']) >= 2 * max(1, len(rep.get('links', [])))
    out['prims_finite'] = all(math.isfinite(c) for p in H.P for c in p)
    out['meta_complete'] = len(getattr(H, 'meta', [])) == len(H.F)
    out['all_pass'] = all([out['rooms_all_pass'], out['links_resolved'],
                            out['roles_mapped_ok'], out['surfaces_nonzero'],
                            out['sockets_paired'], out['prims_finite'],
                            out['meta_complete']])
    return out


def plan_from_parms(h):
    """Artist parm surface -> house plan. No JSON required for the Salon run.

    Folder/parm vocabulary mirrors the Rounded 2.0 lane: footprint, plan
    shape, portal rows, setback rows, dressing toggles, engine output.
    house_plan_json remains as an advanced full-plan override.
    """
    def E(name):
        return h.evalParm(name)

    def S(name):
        return h.parm(name).evalAsString()

    plan = dict(
        rooms=[
            dict(id='salon', kind='rounded',
                 W=E('salon_w'), D=E('salon_d'), H=E('salon_h'),
                 floor_medallion=bool(E('dressing_medallion')),
                 skirting=bool(E('dressing_skirting')),
                 chair_rail=bool(E('dressing_rail')),
                 plan_shape=('ellipse', 'superellipse',
                             'polygon')[int(E('salon_shape'))],
                 plan_sides=int(E('salon_sides')),
                 plan_exponent=E('salon_exponent'),
                 plan_segments=int(E('plan_segments')),
                 tiers=[float(E('tier_0')), float(E('tier_1')),
                        float(E('tier_2'))],
                 portals=[dict(id='salon_entry', theta=0.25,
                               width=float(E('portal_w')),
                               height=float(E('portal_h'))),
                          dict(id='salon_front', theta=0.75,
                               width=float(E('portal_w')),
                               height=float(E('portal_h')))],
                 pos=[0.0, 0.0], yaw_deg=0.0,
                 roof_rise=float(E('salon_roof_rise'))),
            dict(id='landing', kind='rect',
                 W=E('landing_w'), D=E('landing_d'), H=E('landing_h'),
                 floor_medallion=bool(E('dressing_medallion')),
                 skirting=bool(E('dressing_skirting')),
                 chair_rail=bool(E('dressing_rail')),
                 decor='paris_haussmann',
                 windows_long=int(E('landing_windows')), windows_short=0,
                 portals=[dict(id='landing_in', wall='W', s=2.4,
                               width=float(E('portal_w')),
                               height=float(E('portal_h'))),
                          dict(id='landing_out', wall='E', s=2.4,
                               width=float(E('portal_w')),
                               height=float(E('portal_h')))],
                 link_from=('salon', 'salon_front'),
                 link_portal='landing_out',
                 roof_rise=float(E('landing_roof_rise'))),
        ],
        links=[dict(id='salon_landing_run',
                    pa=('salon', 'salon_front'),
                    pb=('landing', 'landing_out'),
                    width=float(E('portal_w')), height=float(E('portal_h')))],
        stairs=[dict(id='porch_steps', room='landing', portal='landing_in',
                     drop_m=float(E('stair_drop')), width=float(E('stair_w')))],
        pad=dict(margin=float(E('pad_margin'))),
    )
    if h.parm('portal_frill') and h.evalParm('portal_frill'):
        plan['portal_frill'] = dict(room='landing', portal='landing_in', layers=int(h.evalParm('frill_layers')))
    return plan


def cook(node):
    """HDA entry point (single arch output). hou only lives here."""
    import hou
    h = node.parent()
    override = (h.evalParm('house_plan_json')
                if h.parm('house_plan_json') else '')
    plan = json.loads(override) if override.strip() else plan_from_parms(h)
    H, rep = assemble(plan)
    gt = gate(H, rep, plan)
    if not gt['all_pass']:
        raise ValueError('house gate failed: %s' % json.dumps(gt))
    mats = _RNS['role_materials'](
        h.evalParm('material_map_json') if h.parm('material_map_json') else '')
    missing = _RNS['unmapped_roles'](H.R, mats)
    if missing:
        raise ValueError('no UE material for roles: %s' % ', '.join(missing))
    g = node.geometry()
    g.clear()
    g.addAttrib(hou.attribType.Prim, 'material_role', '')
    g.addAttrib(hou.attribType.Prim, 'shop_materialpath', '')
    g.addAttrib(hou.attribType.Prim, 'unreal_material', '')
    g.addAttrib(hou.attribType.Prim, 'surface', '')
    g.addAttrib(hou.attribType.Prim, 'room', '')
    g.addAttrib(hou.attribType.Prim, 'surf_id', 0)
    g.addAttrib(hou.attribType.Prim, 'room_id', 0)
    room_index, rooms_seen = {}, []
    for _surface, _room in H.meta:
        if _room not in room_index:
            room_index[_room] = len(rooms_seen)
            rooms_seen.append(_room)
    g.addAttrib(hou.attribType.Vertex, 'uv', (0., 0., 0.))
    for name in ('gate_json', 'sockets_json', 'surfaces_json', 'house_json'):
        g.addAttrib(hou.attribType.Global, name, '')
    yup = bool(h.evalParm('engine_y_up'))
    P = [(p[0], p[2], -p[1]) for p in H.P] if yup else H.P
    pts = g.createPoints(P)
    flip = yup and bool(h.evalParm('engine_flip'))
    render_group = g.createPrimGroup('rendered_main_geo')
    hou_groups = {}
    idx_sets = {}
    for name, idxs in getattr(H, 'G', {}).items():
        hou_groups[name] = g.createPrimGroup(name)
        idx_sets[name] = set(idxs)
    for pi, (face, role, (surface, room)) in enumerate(zip(H.F, H.R, H.meta)):
        sid = SURF_ORDER.index(surface)
        rid = room_index[room]
        f = list(reversed(face)) if flip else face
        poly = g.createPolygon()
        for index in f:
            poly.addVertex(pts[index])
        poly.setAttribValue('material_role', role)
        poly.setAttribValue('shop_materialpath', '/mat/Cathedral_' + role)
        poly.setAttribValue('unreal_material', mats[role])
        poly.setAttribValue('surface', surface)
        poly.setAttribValue('room', room)
        poly.setAttribValue('surf_id', sid)
        poly.setAttribValue('room_id', rid)
        for v, u in zip(poly.vertices(), _boxuv(P, f)):
            if not all(math.isfinite(c) for c in u):
                raise ValueError('non-finite UV on role %s' % role)
            v.setAttribValue('uv', (u[0], u[1], 0.0))
        render_group.add(poly)
        for name, sset in idx_sets.items():
            if pi in sset:
                hou_groups[name].add(poly)
    if h.parm('walk_collision') and h.evalParm('walk_collision'):
        collision = g.createPrimGroup('collision_geo_walk')
        for face, (surface, room) in zip(H.F, H.meta):
            if surface != 'surface_floor' and not room.startswith('stair_'):
                continue
            poly = g.createPolygon()
            for index in (list(reversed(face)) if flip else face):
                poly.addVertex(pts[index])
            collision.add(poly)
    g.setGlobalAttribValue('gate_json', json.dumps(gt))
    g.setGlobalAttribValue('sockets_json', json.dumps(dict(sockets=[
        dict(id=s['id'], room=s.get('room'), wall=s.get('wall', 'CURVE'),
             centre_local_m=list(s['center_world_m']),
             inward=list(s['inward_world']), up=[0., 0., 1.],
             clear_width_m=s.get('clear_width_m', 2.4),
             clear_height_m=s.get('clear_height_m', 3.2),
             floor_z_m=0.0, kind=s.get('kind', 'door'),
             native_cut=s.get('native_cut', True)) for s in rep['sockets']])))
    g.setGlobalAttribValue('surfaces_json', json.dumps(rep['surfaces']))
    g.setGlobalAttribValue('house_json', json.dumps(dict(
        rooms=[dict(id=r['id'], kind=r['kind'], bbox=r['bbox'], roof=r.get('roof'))
               for r in rep['rooms']],
        links=rep['links'], windows=rep['windows'], pad=rep['pad'], roles=rep['roles'],
        prims=rep['prims'], points=rep['points'])))
