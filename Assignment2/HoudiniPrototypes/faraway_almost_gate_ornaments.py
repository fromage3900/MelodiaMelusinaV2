"""Pure-Python ornaments for Faraway Mother's The Almost Gate v03.

Adds the ornate, feminine, musical layer on top of the v02 rock/silk monument:

  * scrollwork volutes (spiral filigree) on the outer flanks
  * heart frames and heart tokens (parametric heart curve, swept)
  * scallop shell fans (hinged rosette blades) at the shoulders
  * hanging vine tendrils under the crown ribs
  * falling ivy strands with alternating leaves on the outer spire flanks
  * wisteria racemes with clustered drooping bell blossoms under the rib arches
  * five-pointed star prisms: floating shards + inlaid badges
  * floating rock shards with WPO/animation metadata (float_phase, float_amp_m,
    orbit_radius_m, spin_rate) so UE can animate them without sim
  * hexagonal crystal clusters whose spawn density is driven by the canonical
    Faraway Mother Chladni field F(3,5), evaluated at each candidate surface
    anchor in global field coordinates (the "musical rockscape graph")

Deterministic in `seed`; no `hou` import; embedded verbatim in the v03 HDA.
Coordinates are Houdini metres, Y up. The spire profile math mirrors
faraway_almost_gate_geometry._ring_peak on purpose: ornaments anchor to the
same analytic rock skin the base generator builds.
"""
import math

PHI = 0.61803398875


def _frac(x):
    return x - math.floor(x)


def _hash01(i, seed):
    """Deterministic 0..1 from an integer index and the monument seed."""
    return _frac(math.sin((i + 1) * 12.9898 + seed * 78.233) * 43758.5453)


def _vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _vmul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _vdot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _vcross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def _vnorm(a):
    d = math.sqrt(max(_vdot(a, a), 1e-18))
    return (a[0] / d, a[1] / d, a[2] / d)


def _sweep_tube(path, radius, sides=8, taper=0.0, piece="ornament",
                material="ornament"):
    """Same swept-solid convention as the base geometry module."""
    pts = [tuple(float(v) for v in p) for p in path]
    rows = []
    for i, p in enumerate(pts):
        tangent = _vnorm(_vsub(pts[min(i + 1, len(pts) - 1)],
                               pts[max(0, i - 1)]))
        ref = (0.0, 0.0, 1.0) if abs(tangent[1]) > 0.82 else (0.0, 1.0, 0.0)
        side = _vnorm(_vcross(tangent, ref))
        up = _vnorm(_vcross(side, tangent))
        u = i / float(max(1, len(pts) - 1))
        rr = radius * (1.0 - taper * u)
        rows.append([_vadd(p, _vadd(_vmul(side, rr * math.cos(2 * math.pi * k / sides)),
                                    _vmul(up, rr * math.sin(2 * math.pi * k / sides))))
                     for k in range(sides)])
    faces = []
    for j in range(len(rows) - 1):
        for k in range(sides):
            kn = (k + 1) % sides
            faces.append((rows[j][k], rows[j][kn], rows[j + 1][kn], rows[j + 1][k]))
    faces.append(tuple(reversed(rows[0])))
    faces.append(tuple(rows[-1]))
    return {"piece": piece, "faces": faces, "material": material}


# ---------------------------------------------------------------------------
# Spire skin re-derivation (mirrors faraway_almost_gate_geometry._ring_peak)
# ---------------------------------------------------------------------------

def _spire_surface_point(cx, base_y, cz, height, rx, rz, seed, erosion,
                         t, a, lean_x=0.0, lean_z=0.0):
    profile = (1.0 - t) ** 0.68 * (0.76 + 0.48 * math.exp(-((t - 0.18) / 0.14) ** 2))
    profile *= 1.0 + 0.055 * math.sin(t * 13.0 + seed * 0.37)
    n = (0.38 * math.sin(3.0 * a + seed * 0.11 + t * 2.5)
         + 0.27 * math.sin(5.0 * a - seed * 0.07 + t * 4.1)
         + 0.19 * math.cos(9.0 * a + t * 7.0)
         + 0.16 * math.sin(15.0 * a + seed * 0.03 - t * 5.0))
    strata = (0.055 * math.sin(t * 37.0 + 1.2 * math.sin(a * 4.0 + seed))
              + 0.035 * math.sin(a * 11.0 + t * 9.0 + seed * 0.17))
    r = max(0.035, profile * (1.0 + erosion * n + strata))
    ax = cx + lean_x * t * t
    az = cz + lean_z * t * t
    return (ax + rx * r * math.cos(a), base_y + t * height, az + rz * r * math.sin(a))


def _spire_frames(p):
    """The five analytic rock masses the base generator builds (same numbers)."""
    height = float(p["height"]); width = float(p["width"])
    depth = float(p["depth"]); asym = float(p["asymmetry"])
    erosion = float(p["erosion"]); seed = int(p["seed"])
    aperture = float(p["aperture_width"])
    rx = width * 0.18; rz = depth * 0.40
    center = aperture * 0.5 + rx * 1.45 + 8.0
    left_x = -center - asym * 8.0
    right_x = center + asym * 11.0
    crown_base = float(p["aperture_height"]) + 24.0
    crown_x = -width * 0.075 + asym * 16.0
    crown_z = depth * 0.24
    crown_h = max(90.0, height - crown_base - 18.0)
    return [
        dict(cx=left_x, cy=float(p.get("ground_west", 0.0)), cz=-4.0,
             h=height * (1.0 + asym * 0.08), rx=rx, rz=rz, seed=seed + 19,
             ero=erosion, lx=-26.0 * asym, lz=-6.0, tag="west"),
        dict(cx=right_x, cy=float(p.get("ground_east", 0.0)), cz=7.0,
             h=height * (0.83 - asym * 0.06), rx=rx * 1.04, rz=rz * 0.92,
             seed=seed + 41, ero=erosion * 0.92, lx=13.0 * asym, lz=9.0, tag="east"),
        dict(cx=crown_x, cy=crown_base, cz=crown_z, h=crown_h,
             rx=width * 0.205, rz=depth * 0.31, seed=seed + 67,
             ero=erosion * 0.82, lx=20.0 * asym, lz=-8.0, tag="crown"),
        dict(cx=-width * 0.48, cy=0.0, cz=depth * 0.18, h=height * 0.64,
             rx=width * 0.13, rz=depth * 0.28, seed=seed + 89, ero=erosion,
             lx=-17.0 * asym, lz=5.0, tag="outer_west"),
        dict(cx=width * 0.47, cy=0.0, cz=-depth * 0.20, h=height * 0.53,
             rx=width * 0.12, rz=depth * 0.27, seed=seed + 103, ero=erosion * 0.90,
             lx=20.0 * asym, lz=-7.0, tag="outer_east"),
    ]


# ---------------------------------------------------------------------------
# Ornament primitives
# ---------------------------------------------------------------------------

def _volute(center, plane_u, plane_v, r0, turns, seed, idx, cw=1):
    """One spiral scroll: Archimedean volute swept as a tapering tube."""
    pts = []
    steps = 26
    for k in range(steps):
        t = k / float(steps - 1)
        theta = cw * turns * 2.0 * math.pi * t + _hash01(idx, seed) * 0.9
        r = r0 * (1.0 - 0.82 * t)
        wobble = 1.0 + 0.06 * math.sin(t * 9.0 + idx * 1.7)
        p = _vadd(center, _vadd(_vmul(plane_u, r * wobble * math.cos(theta)),
                                _vmul(plane_v, r * wobble * math.sin(theta))))
        pts.append(p)
    return _sweep_tube(pts, r0 * 0.14, 7, 0.86, "scrollwork", "ornament")


def _heart_path(center, size, plane_u, plane_v, tilt=0.0):
    """Classic parametric heart, centred, base of the heart at the centre."""
    pts = []
    steps = 40
    for k in range(steps + 1):
        t = 2.0 * math.pi * k / float(steps)
        hx = 16.0 * math.sin(t) ** 3
        hy = (13.0 * math.cos(t) - 5.0 * math.cos(2.0 * t)
              - 2.0 * math.cos(3.0 * t) - math.cos(4.0 * t))
        u = hx / 17.0
        v = hy / 17.0
        ca, sa = math.cos(tilt), math.sin(tilt)
        uu = u * ca - v * sa
        vv = u * sa + v * ca
        pts.append(_vadd(center, _vadd(_vmul(plane_u, uu * size),
                                       _vmul(plane_v, vv * size))))
    return pts


def _heart(center, size, plane_u, plane_v, seed, idx, tube=None, tilt=0.0):
    path = _heart_path(center, size, plane_u, plane_v, tilt)
    return _sweep_tube(path, tube or max(0.9, size * 0.085), 7, 0.28,
                       "heart_frame", "ornament")


def _star_polygon(center, plane_u, plane_v, r_out, depth, axis, seed, idx,
                  piece="star_shard", material="ornament"):
    """Five-pointed star prism; axis is the extrusion direction (unit)."""
    ring = []
    for k in range(10):
        r = r_out if k % 2 == 0 else r_out * 0.46
        a = 2.0 * math.pi * k / 10.0 - math.pi * 0.5 + _hash01(idx, seed) * 0.35
        ring.append(_vadd(center, _vadd(_vmul(plane_u, r * math.cos(a)),
                                        _vmul(plane_v, r * math.sin(a)))))
    back = [_vadd(q, _vmul(axis, -depth * 0.5)) for q in ring]
    front = [_vadd(q, _vmul(axis, depth * 0.5)) for q in ring]
    faces = [tuple(reversed(back)), tuple(front)]
    for k in range(10):
        kn = (k + 1) % 10
        faces.append((back[k], back[kn], front[kn], front[k]))
    return {"piece": piece, "faces": faces, "material": material}


def _shell_fan(hinge, facing, radius, blades, seed, idx):
    """Scallop shell: shared-radius blades fanning from a hinge, with a rim."""
    facing = _vnorm(facing)
    u = _vnorm(_vcross((0.0, 1.0, 0.0), facing))  # fan spread direction
    parts = []
    spread = math.pi * 0.86
    rim_pts = []
    for b in range(blades):
        a = -spread * 0.5 + spread * b / float(max(1, blades - 1))
        dirb = _vnorm(_vadd(_vmul(facing, math.cos(a)), _vmul(u, math.sin(a))))
        sweep = math.pi * (0.42 + 0.05 * math.sin(b * 2.3 + seed))
        pts = []
        for k in range(9):
            t = k / 8.0
            # blade arcs from hinge to rim, curving back as it rises
            p = _vadd(hinge, _vmul(dirb, radius * math.sin(t * sweep)))
            p = _vadd(p, (0.0, radius * (1.0 - math.cos(t * sweep)) * 0.72, 0.0))
            pts.append(p)
        rim_pts.append(pts[-1])
        parts.append(_sweep_tube(pts, radius * 0.035 * (1.15 - 0.5 * abs(a)), 6,
                                 0.55, "shell_fan", "ornament"))
    # scalloped rim arcs between adjacent blade tips
    for b in range(blades - 1):
        a, c = rim_pts[b], rim_pts[b + 1]
        mid = _vmul(_vadd(a, c), 0.5)
        lift = radius * (0.05 + 0.03 * math.sin(b * 3.1 + seed))
        arc = [a, _vadd(_vmul(_vadd(a, mid), 0.5), (0.0, lift, 0.0)),
               _vadd(mid, (0.0, lift * 1.35, 0.0)),
               _vadd(_vmul(_vadd(mid, c), 0.5), (0.0, lift, 0.0)), c]
        parts.append(_sweep_tube(arc, radius * 0.022, 5, 0.30,
                                 "shell_fan", "ornament"))
    return parts


def _vine_tendril(anchor, length, seed, idx):
    """Hanging damped-sine vine under the crown/ribs."""
    pts = []
    for k in range(17):
        t = k / 16.0
        sway = (1.0 - t) ** 0.7
        x = 5.0 * math.sin(t * 5.2 + idx * 1.9 + seed * 0.05) * sway
        z = 4.0 * math.cos(t * 4.1 + idx * 1.3) * sway
        pts.append((anchor[0] + x, anchor[1] - length * t, anchor[2] + z))
    return _sweep_tube(pts, 1.35, 6, 0.78, "vine_tendril", "rib")


_ICO_T = (1.0 + math.sqrt(5.0)) / 2.0
_ICO_VERTS = [
    (-1, _ICO_T, 0), (1, _ICO_T, 0), (-1, -_ICO_T, 0), (1, -_ICO_T, 0),
    (0, -1, _ICO_T), (0, 1, _ICO_T), (0, -1, -_ICO_T), (0, 1, -_ICO_T),
    (_ICO_T, 0, -1), (_ICO_T, 0, 1), (-_ICO_T, 0, -1), (-_ICO_T, 0, 1),
]
_ICO_FACES = [
    (0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
    (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
    (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
    (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1),
]


def _float_shard(center, size, seed, idx):
    """Irregular levitating rock chunk (deterministically displaced icosahedron)."""
    s1 = seed * 0.013 + idx * 1.71
    verts = []
    for v in _ICO_VERTS:
        n = _vnorm(v)
        d = 1.0 + 0.34 * math.sin(n[0] * 3.1 + s1) * math.sin(n[1] * 2.7 + s1 * 1.3) \
            + 0.18 * math.sin(n[2] * 5.3 + s1 * 0.7)
        verts.append(_vadd(center, _vmul(n, size * 0.5 * d)))
    faces = [(verts[a], verts[b], verts[c]) for a, b, c in _ICO_FACES]
    return {"piece": "float_shard", "faces": faces, "material": "stone"}


def _hex_crystal(center, axis, height, radius, seed, idx):
    """Hexagonal prism with a pyramidal tip; axis is the growth direction."""
    axis = _vnorm(axis)
    ref = (0.0, 0.0, 1.0) if abs(axis[1]) > 0.85 else (0.0, 1.0, 0.0)
    u = _vnorm(_vcross(ref, axis))
    v = _vcross(axis, u)
    prism_h = height * 0.62
    twist = _hash01(idx, seed) * math.pi
    ring = []
    for k in range(6):
        a = twist + 2.0 * math.pi * k / 6.0
        off = _vadd(_vmul(u, radius * math.cos(a)), _vmul(v, radius * math.sin(a)))
        ring.append(off)
    base = [_vadd(center, q) for q in ring]
    top = [_vadd(center, _vadd(q, _vmul(axis, prism_h))) for q in ring]
    apex = _vadd(center, _vmul(axis, height))
    faces = [tuple(reversed(base))]
    for k in range(6):
        kn = (k + 1) % 6
        faces.append((base[k], base[kn], top[kn], top[k]))
        faces.append((top[k], top[kn], apex))
    return {"piece": "crystal", "faces": faces, "material": "crystal"}


def _ivy_leaf(center, axis_u, axis_v, size, tilt):
    """Single pinnate ivy leaf approximated by a slightly cupped diamond."""
    ca, sa = math.cos(tilt), math.sin(tilt)
    tips = []
    for (du, dv) in ((0.0, 1.0), (0.62, 0.0), (0.0, -1.15), (-0.62, 0.0)):
        uu = (du * ca - dv * sa) * size
        vv = (du * sa + dv * ca) * size
        tips.append(_vadd(center, _vadd(_vmul(axis_u, uu), _vmul(axis_v, vv))))
    return [(tips[0], tips[1], tips[2]), (tips[0], tips[2], tips[3])]


def _ivy_strand(anchor, length, seed, idx):
    """Falling ivy: hanging stem with alternating diamond leaves."""
    parts = []
    pts = []
    hang = 11
    sway_phase = _hash01(idx + 1000, seed) * 2.0 * math.pi
    for k in range(hang):
        t = k / float(hang - 1)
        sway = (1.0 - 0.55 * t)
        x = 4.2 * math.sin(t * 4.6 + sway_phase) * sway
        z = 3.4 * math.cos(t * 3.9 + sway_phase * 1.3) * sway
        y = -length * t
        pts.append((anchor[0] + x, anchor[1] + y, anchor[2] + z))
    parts.append(_sweep_tube(pts, 0.85, 5, 0.55, "ivy_strand", "rib"))
    leaf_every = max(2, int(length / 9.0))
    li = 0
    for k in range(1, hang - 1):
        if k % leaf_every != 0:
            continue
        side = 1.0 if li % 2 == 0 else -1.0
        base = pts[k]
        c = (base[0] + side * 1.5, base[1] - 0.4, base[2] + side * 0.5)
        tilt = side * (0.5 + 0.3 * _hash01(idx * 31 + li, seed))
        size = 1.7 + 0.9 * _hash01(idx * 37 + li, seed)
        leaf_u = _vnorm((side, 0.30 * side, 0.0))
        leaf_v = _vnorm((0.0, 0.35, side))
        parts.append({"piece": "ivy_leaf", "faces": _ivy_leaf(c, leaf_u, leaf_v, size, tilt),
                      "material": "silk"})
        li += 1
    return parts


def _wisteria_bloom(center, radius, height, seed, idx):
    """Drooping four-sided bell blossom hanging from its attachment point."""
    u = (1.0, 0.0, 0.0)
    v = (0.0, 0.0, 1.0)
    ring = []
    twist = _hash01(idx + 2000, seed) * math.pi
    for k in range(4):
        a = twist + 2.0 * math.pi * k / 4.0
        ring.append(_vadd(center, _vadd(_vmul(u, radius * math.cos(a)),
                                        _vmul(v, radius * math.sin(a)))))
    tip = (center[0], center[1] - height, center[2])
    faces = []
    for k in range(4):
        kn = (k + 1) % 4
        faces.append((ring[k], ring[kn], tip))
    return {"piece": "wisteria_bloom", "faces": faces, "material": "silk"}


def _wisteria_raceme(anchor, length, seed, idx):
    """Hanging wisteria raceme: stem plus clustered drooping bell blossoms,
    dense toward the tip like the living flower."""
    parts = []
    hang = 13
    pts = []
    sway_phase = _hash01(idx + 3000, seed) * 2.0 * math.pi
    for k in range(hang):
        t = k / float(hang - 1)
        x = 2.6 * math.sin(t * 3.4 + sway_phase) * (1.0 - 0.4 * t)
        z = 2.2 * math.cos(t * 2.9 + sway_phase * 0.8) * (1.0 - 0.4 * t)
        y = -length * (t ** 1.08)
        pts.append((anchor[0] + x, anchor[1] + y, anchor[2] + z))
    parts.append(_sweep_tube(pts, 0.7, 5, 0.62, "wisteria_raceme", "rib"))
    blooms = int(10 + length * 0.30)
    for b in range(blooms):
        t = 0.30 + 0.70 * (b / float(max(1, blooms - 1)))
        ki = min(int(t * (hang - 1)), hang - 1)
        stem_pt = pts[ki]
        az = 2.0 * math.pi * _hash01(idx * 53 + b, seed)
        rad = 0.9 + 1.5 * _hash01(idx * 59 + b, seed)
        c = (stem_pt[0] + math.cos(az) * rad,
             stem_pt[1] - 0.5 - 1.3 * _hash01(idx * 61 + b, seed),
             stem_pt[2] + math.sin(az) * rad)
        parts.append(_wisteria_bloom(c, 0.85 + 0.4 * _hash01(idx * 67 + b, seed),
                                     1.7 + 0.9 * _hash01(idx * 71 + b, seed), seed,
                                     idx * 100 + b))
    return parts


# ---------------------------------------------------------------------------
# Public generator
# ---------------------------------------------------------------------------

FLOAT_PIECES = ("float_shard", "star_shard")


def generate_ornaments(p, field_f, collision=False):
    """Return ornament pieces plus per-piece motion/crystal metadata.

    `field_f(x, z)` evaluates the canonical global Chladni field F(3,5) at
    global field coordinates; crystal anchors spawn only where the field is
    above `chladni_threshold`, so the inlay pattern IS the rockscape graph.
    """
    seed = int(p["seed"])
    height = float(p["height"]); width = float(p["width"])
    depth = float(p["depth"]); asym = float(p["asymmetry"])
    aperture = float(p["aperture_width"])
    aperture_h = float(p["aperture_height"])
    half = aperture * 0.5
    parts = []
    motion = {}   # piece index-in-list -> motion dict (aligned with parts order)

    if collision:
        return parts, motion

    frames = _spire_frames(p)
    crown = next(f for f in frames if f["tag"] == "crown")
    crown_top = crown["cy"] + crown["h"]

    # -- Scrollwork volutes on the outer flanks ------------------------------
    n_scroll = int(p.get("scrollwork_count", 8))
    for i in range(n_scroll):
        side = -1 if i % 2 == 0 else 1
        layer = i // 2
        cx = side * (half + width * 0.185 + 6.0 + layer * 7.0 + asym * 6.0)
        cy = aperture_h * 0.55 + (i * 37.0 + seed) % (height * 0.34)
        cz = (-1 if (i // 2) % 2 == 0 else 1) * depth * (0.30 + 0.06 * _hash01(i, seed))
        u = (0.0, 1.0, 0.0)
        v = (0.0, 0.0, 1.0)
        r0 = 14.0 + 6.0 * _hash01(i + 50, seed)
        parts.append(_volute((cx, cy, cz), u, v, r0,
                             2.1 + 0.8 * _hash01(i + 90, seed), seed, i,
                             cw=-side))

    # -- Heart aperture frame crowning the opening ---------------------------
    heart_size = min(half * 1.02, 78.0)
    heart_center = (asym * 10.0, aperture_h + 34.0 + heart_size * 0.62, depth * 0.06)
    parts.append(_heart(heart_center, heart_size, (1.0, 0.0, 0.0), (0.0, 1.0, 0.0),
                        seed, 0, tube=4.6, tilt=math.pi))
    motion_tag = len(parts) - 1
    motion[motion_tag] = dict(float_phase=_hash01(991, seed), float_amp_m=0.0,
                              orbit_radius_m=0.0, spin_rate=0.0)

    # small heart tokens drifting up the outer spires
    n_hearts = int(p.get("heart_tokens", 5))
    for i in range(n_hearts):
        f = frames[i % len(frames)]
        t = 0.30 + 0.55 * _hash01(i + 200, seed)
        a = (-1 if f["cx"] < 0 else 1) * (0.35 + 0.5 * _hash01(i + 210, seed))
        surf = _spire_surface_point(f["cx"], f["cy"], f["cz"], f["h"], f["rx"], f["rz"],
                                    f["seed"], f["ero"], t, a, f["lx"], f["lz"])
        nrm = _vnorm(_vsub(surf, (f["cx"] + f["lx"] * t * t, surf[1],
                                  f["cz"] + f["lz"] * t * t)))
        c = _vadd(surf, _vmul(nrm, 3.0))
        size = 7.0 + 5.0 * _hash01(i + 220, seed)
        u = _vnorm(_vcross((0.0, 1.0, 0.0), nrm))
        vv = _vcross(nrm, u)
        parts.append(_heart(c, size, u, vv, seed, i + 1, tilt=math.pi))
        motion[len(parts) - 1] = dict(
            float_phase=_hash01(i + 300, seed),
            float_amp_m=1.2 + 1.6 * _hash01(i + 310, seed),
            orbit_radius_m=0.8 * _hash01(i + 320, seed),
            spin_rate=0.0)

    # -- Scallop shell fans at the shoulders ---------------------------------
    n_fans = int(p.get("shell_fans", 4))
    for i in range(n_fans):
        side = -1 if i % 2 == 0 else 1
        fb = -1 if (i // 2) % 2 == 0 else 1
        hinge = (side * (half + width * 0.16),
                 aperture_h + 26.0 + 12.0 * _hash01(i + 400, seed),
                 fb * depth * 0.34)
        facing = _vnorm((side * 0.85, 0.45 + 0.2 * _hash01(i + 410, seed),
                         fb * 0.25))
        parts.extend(_shell_fan(hinge, facing, 26.0 + 10.0 * _hash01(i + 420, seed),
                                7, seed, i))

    # -- Vine tendrils hanging under the crown ribs --------------------------
    n_vines = int(p.get("tendril_count", 6))
    for i in range(n_vines):
        side = -1 if i % 2 == 0 else 1
        anchor = (side * (half * (0.55 + 0.4 * _hash01(i + 500, seed))),
                  aperture_h + 46.0 + 18.0 * _hash01(i + 510, seed),
                  (-1 if (i // 2) % 2 == 0 else 1) * depth * 0.36)
        parts.append(_vine_tendril(anchor, 42.0 + 40.0 * _hash01(i + 520, seed),
                                   seed, i))

    # -- Falling ivy on the outer spire flanks -------------------------------
    # Anchors cling to the analytic spire skins on faces turned away from the
    # approach; strands hang down and sway, never entering the portal volume.
    n_ivy = int(p.get("ivy_strands", 10))
    for i in range(n_ivy):
        f = frames[i % len(frames)]
        side = -1 if f["cx"] < 0 else 1
        t = 0.28 + 0.38 * _hash01(i + 1100, seed)
        a = side * (math.pi * 0.5 + 0.55 * _hash01(i + 1110, seed))
        surf = _spire_surface_point(f["cx"], f["cy"], f["cz"], f["h"], f["rx"], f["rz"],
                                    f["seed"], f["ero"], t, a, f["lx"], f["lz"])
        nrm = _vnorm(_vsub(surf, (f["cx"] + f["lx"] * t * t, surf[1],
                                  f["cz"] + f["lz"] * t * t)))
        anchor = _vadd(surf, _vmul(nrm, 1.2))
        length = 34.0 + 46.0 * _hash01(i + 1120, seed)
        ivy = _ivy_strand(anchor, length, seed, i)
        first = len(parts)
        parts.extend(ivy)
        for j in range(first, len(parts)):
            motion[j] = dict(float_phase=_hash01(i + 1130, seed),
                             float_amp_m=0.5 + 0.7 * _hash01(i + 1140, seed),
                             orbit_radius_m=0.15, spin_rate=0.0)

    # -- Wisteria racemes under the rib arches -------------------------------
    # Anchors ride the same analytic rib curves as the woven_rib pieces but sit
    # below them, always above the clear aperture envelope.
    n_wist = int(p.get("wisteria_racemes", 12))
    for i in range(n_wist):
        side = -1 if i % 2 == 0 else 1
        fb = -1 if (i // 2) % 2 == 0 else 1
        layer = (i // 4) - 1
        t = 0.18 + 0.62 * _hash01(i + 1200, seed)
        x = side * (width * (0.49 - 0.43 * t)) + side * asym * 12.0 * t * t
        y = (aperture_h + 22.0 + height * (0.48 * math.sin(t * math.pi * 0.5))
             + height * asym * (0.035 if side > 0 else -0.018) * t * t)
        y -= 6.5 + 3.0 * _hash01(i + 1210, seed)
        z = fb * (depth * (0.34 - 0.09 * t) + 7.0 * math.sin(t * math.pi)) \
            + layer * depth * 0.075
        length = 26.0 + 34.0 * _hash01(i + 1220, seed)
        raceme = _wisteria_raceme((x, y, z), length, seed, i)
        first = len(parts)
        parts.extend(raceme)
        for j in range(first, len(parts)):
            motion[j] = dict(float_phase=_hash01(i + 1230, seed),
                             float_amp_m=0.4 + 0.6 * _hash01(i + 1240, seed),
                             orbit_radius_m=0.12, spin_rate=0.0)

    # -- Floating star shards above the crown --------------------------------
    n_stars = int(p.get("star_shards", 9))
    for i in range(n_stars):
        phi = 2.0 * math.pi * _frac(i * PHI + _hash01(i + 600, seed) * 0.25)
        band = 52.0 + 95.0 * _hash01(i + 610, seed)
        c = (crown["cx"] + math.cos(phi) * band,
             crown_top + 26.0 + 120.0 * _hash01(i + 620, seed),
             crown["cz"] + math.sin(phi) * band * 0.8)
        r_out = 6.0 + 6.5 * _hash01(i + 630, seed)
        u = (math.cos(phi + math.pi * 0.5), 0.0, math.sin(phi + math.pi * 0.5))
        axis = _vnorm((math.cos(phi) * 0.6, 0.5 + 0.4 * _hash01(i + 640, seed),
                       math.sin(phi) * 0.6))
        v = _vcross(axis, u)
        parts.append(_star_polygon(c, u, v, r_out, r_out * 0.5, axis, seed, i,
                                   piece="star_shard", material="ornament"))
        motion[len(parts) - 1] = dict(
            float_phase=_hash01(i + 650, seed),
            float_amp_m=2.5 + 3.0 * _hash01(i + 660, seed),
            orbit_radius_m=2.0 + 3.0 * _hash01(i + 670, seed),
            spin_rate=(0.2 + 0.5 * _hash01(i + 680, seed)) * (1 if i % 2 else -1))

    # -- Floating rock shards (the "moving pieces") --------------------------
    n_float = int(p.get("float_shards", 14))
    amp = float(p.get("float_amp_m", 6.0))
    orb = float(p.get("orbit_radius_m", 4.0))
    for i in range(n_float):
        phi = 2.0 * math.pi * _frac(i * PHI * 1.7 + _hash01(i + 700, seed) * 0.4)
        band = 34.0 + 120.0 * _hash01(i + 710, seed)
        c = (crown["cx"] + math.cos(phi) * band,
             crown_top - 30.0 + 170.0 * _hash01(i + 720, seed),
             crown["cz"] + math.sin(phi) * band * 0.85)
        size = 5.0 + 13.0 * _hash01(i + 730, seed)
        parts.append(_float_shard(c, size, seed, i))
        motion[len(parts) - 1] = dict(
            float_phase=_hash01(i + 740, seed),
            float_amp_m=amp * (0.5 + 0.9 * _hash01(i + 750, seed)),
            orbit_radius_m=orb * (0.3 + _hash01(i + 760, seed)),
            spin_rate=(0.08 + 0.30 * _hash01(i + 770, seed)) * (1 if i % 2 else -1))

    # -- Inlaid crystal clusters on the Chladni rockscape --------------------
    # Candidate anchors across all five spire skins are ranked by |F|: the
    # strongest antinodes of the musical rockscape crystallize first, so
    # crystal_density controls the count directly while the field controls
    # WHERE they land. chladni_threshold is a minimum |F| gate.
    density = int(p.get("crystal_density", 64))
    csize = float(p.get("crystal_size_m", 3.5))
    threshold = float(p.get("chladni_threshold", 0.55))
    crystal_meta = {}   # parts index -> (F, glow)
    anchors = []
    candidates = max(density * 6, 96)
    for i in range(candidates):
        f = frames[i % len(frames)]
        t = 0.06 + 0.86 * _hash01(i + 800, seed)
        a = 2.0 * math.pi * _frac(i * PHI + _hash01(i + 810, seed) * 0.5)
        surf = _spire_surface_point(f["cx"], f["cy"], f["cz"], f["h"], f["rx"], f["rz"],
                                    f["seed"], f["ero"], t, a, f["lx"], f["lz"])
        if abs(surf[0]) < half + 6.0 or surf[1] < 4.0:
            continue
        axis_pt = (f["cx"] + f["lx"] * t * t, surf[1], f["cz"] + f["lz"] * t * t)
        nrm = _vnorm(_vsub(surf, axis_pt))
        if nrm[1] < -0.35:
            continue
        F = float(field_f(surf[0], surf[2]))
        anchors.append((abs(F), F, i, surf, nrm))
    anchors.sort(key=lambda row: (-row[0], row[2]))
    kept = 0
    for absF, F, i, surf, nrm in anchors:
        if kept >= density or absF < threshold:
            break
        base = _vadd(surf, _vmul(nrm, csize * 0.10))
        h = csize * (0.8 + 0.9 * _hash01(i + 820, seed))
        r = csize * (0.22 + 0.14 * _hash01(i + 830, seed))
        parts.append(_hex_crystal(base, nrm, h, r, seed, i))
        glow = min(1.0, absF / 2.0)
        crystal_meta[len(parts) - 1] = (F, glow)
        kept += 1
        # one satellite crystal leaning off the main one
        if _hash01(i + 840, seed) > 0.45:
            s_axis = _vnorm(_vadd(nrm, (0.5 * math.sin(i), 0.2, 0.5 * math.cos(i * 1.3))))
            s_base = _vadd(base, _vadd(_vmul(nrm, h * 0.18),
                                       (0.6 * csize * math.sin(i * 2.1), 0.0,
                                        0.6 * csize * math.cos(i * 1.7))))
            parts.append(_hex_crystal(s_base, s_axis, h * 0.55, r * 0.7, seed, i + 1))
            crystal_meta[len(parts) - 1] = (F, glow * 0.8)

    # inlaid star badges on the outer faces (musical crest markers)
    for i, f in enumerate(frames):
        if f["tag"] == "crown":
            continue
        side = -1 if f["cx"] < 0 else 1
        t = 0.42 + 0.2 * _hash01(i + 900, seed)
        a = side * (math.pi * 0.5 + 0.4 * _hash01(i + 910, seed))
        surf = _spire_surface_point(f["cx"], f["cy"], f["cz"], f["h"], f["rx"], f["rz"],
                                    f["seed"], f["ero"], t, a, f["lx"], f["lz"])
        nrm = _vnorm(_vsub(surf, (f["cx"] + f["lx"] * t * t, surf[1],
                                  f["cz"] + f["lz"] * t * t)))
        c = _vadd(surf, _vmul(nrm, 1.6))
        r_out = 9.0 + 4.0 * _hash01(i + 920, seed)
        u = _vnorm(_vcross((0.0, 1.0, 0.0), nrm))
        v = _vcross(nrm, u)
        parts.append(_star_polygon(c, u, v, r_out, 3.2, nrm, seed, i + 40,
                                   piece="star_inlay", material="crystal"))

    meta = {"motion": motion, "crystal": crystal_meta}
    return parts, meta


__all__ = ["generate_ornaments", "FLOAT_PIECES"]
