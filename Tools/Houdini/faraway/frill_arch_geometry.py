"""frill_arch_geometry.py -- Faraway FrillValley arch: tiered scalloped flounces + brocade rosette.

Pure Python. Reuses prism/strip_solid/box/houdini_volume from heart_gate_geometry (in the HDA's Python SOP
both files share one namespace, so the import below is a no-op there).

Nikki lens (Docs/Research/EMERGING_NIKKI_PICK_2026-09-02.md): layered fashion fabric at the cheapest
representation that still reads -- stacked scalloped petticoat layers (each its own z plane), not simulated cloth.
Frill halves are parametrised on CONCENTRIC radii so both halves meet exactly on x=0 (no mitre gap at the cusp).
"""
import math

try:
    from heart_gate_geometry import prism, strip_solid, box, houdini_volume  # noqa: F401
except ImportError:  # embedded in the SOP: names already in the shared namespace
    pass


def _arch_pt(a, ph, R, r, t):
    """Point on the right arc at radius r, t in [0,1] from springing (0) to apex (1); x(t=1) == 0 exactly."""
    cxr = a - R
    th_end = math.acos(max(min(-cxr / r, 1.0), -1.0))
    th = t * th_end
    return (cxr + r * math.cos(th), ph + r * math.sin(th))


def generate_frill(p):
    span = p["span"]
    ph = p["pier_height"]
    R = max(p["lancet"], 0.78) * span
    a = span * 0.5
    cw = p["core_width"]
    layers = int(p["frill_layers"])
    fw = p["frill_width"]
    sc = int(p["scallops"])
    amp = p["scallop_amp"]
    dz = p["layer_dz"]
    segs = int(p["arc_segments"])
    petals = int(p["flower_petals"])
    fr = p["flower_radius"]
    seed = int(p["seed"])
    if p.get("preview_mode", 0):
        segs = max(12, segs // 3)
        layers = min(layers, 2)
        petals = max(5, petals // 2)

    def rnd(i):
        return (math.sin((i + 1) * 12.9898 + seed * 78.233) * 43758.5453) % 1.0

    out = {"core": [], "pier": [], "frill": [], "brocade_flower": []}
    r_core_out = R
    r_core_in = R - cw
    dep = 0.20
    z0, z1 = -dep * 0.5, dep * 0.5

    # core arch band (both halves share the apex x=0)
    for side in (1, -1):
        outer = [(side * x, y) for x, y in (_arch_pt(a, ph, R, r_core_out, i / float(segs)) for i in range(segs + 1))]
        inner = [(side * x, y) for x, y in (_arch_pt(a, ph, R, r_core_in, i / float(segs)) for i in range(segs + 1))]
        out["core"].append(strip_solid(outer, inner, z0, z1, False))
        xo, xi = outer[0][0], inner[0][0]
        out["pier"].append(box(0.5 * (xo + xi), ph * 0.5, abs(xo - xi) * 0.5, ph * 0.5, z0, z1))
        out["pier"].append(box(0.5 * (xo + xi), 0.07, abs(xo - xi) * 0.5 + 0.12, 0.07, z0 - 0.06, z1 + 0.06))

    # tiered scalloped flounces: each layer is a thin plane stacked in z, widest at the back, scallops phase-shifted
    zmax = z1
    for k in range(layers):
        width = fw * (1.0 - 0.55 * k / max(layers - 1, 1))
        freq = sc + 2 * k
        phase = rnd(k) * math.pi
        zc = z1 + 0.01 + k * dz if k else z1 + 0.01
        zl0, zl1 = zc, zc + 0.035
        zmax = max(zmax, zl1)
        th_half = math.acos(max(min(-(a - R) / r_core_out, 1.0), -1.0))
        scallop_w = r_core_out * th_half / float(freq)        # arc length of one scallop
        bump_h = min(width * 0.45, 0.5 * scallop_w)           # round arcs: height <= half the width
        fs = max(segs, 10 * freq)          # >= 10 samples per scallop so bumps are round, not sawtooth
        for side in (1, -1):
            inner, outer = [], []
            for i in range(fs + 1):
                t = i / float(fs)
                x_in, y_in = _arch_pt(a, ph, R, r_core_out, t)
                f = (freq * t + phase / math.pi) % 1.0
                bump = math.sqrt(max(0.0, 1.0 - (2.0 * f - 1.0) ** 2))     # semicircular scallop
                r_edge = r_core_out + width * 0.55 + bump_h * bump + amp * math.sin(2 * math.pi * freq * 0.37 * t + phase * 1.7)
                x_o, y_o = _arch_pt(a, ph, R, r_edge, t)
                inner.append((side * x_in, y_in))
                outer.append((side * x_o, y_o))
            out["frill"].append(strip_solid(outer, inner, zl0, zl1, False))

    # brocade rosette at the keystone: two petal rings + centre disc
    apex_y = max(y for s in out["frill"] for poly in s for _, y, _ in poly)
    cx, cy = 0.0, apex_y + fr * 0.15
    zf = zmax + 0.01
    for ring, (n, length, wid, zoff) in enumerate(((petals, fr, 0.30, 0.0), (petals, fr * 0.66, 0.34, 0.045))):
        rot0 = (math.pi / n) * ring
        for j in range(n):
            ang = rot0 + 2 * math.pi * j / n + math.pi * 0.5
            ux, uy = math.cos(ang), math.sin(ang)
            tx, ty = -uy, ux
            hw = wid * length * 0.5
            n_s = 6
            right = [(hw * math.sqrt(max(0.0, 1.0 - (2.0 * (i / float(n_s)) - 1.0) ** 2)) * (0.65 + 0.35 * i / float(n_s)), length * (0.04 + 0.96 * i / float(n_s))) for i in range(0, n_s + 1)]
            left = [(-u, v) for u, v in reversed(right[1:-1])]
            loc = right + left            # elliptical petal, convex
            poly = [(cx + ux * v + tx * u, cy + uy * v + ty * u) for u, v in loc]
            out["brocade_flower"].append(prism(poly, zf + zoff, zf + zoff + 0.04))
    disc = [(cx + 0.16 * fr * math.cos(2 * math.pi * i / 12), cy + 0.16 * fr * math.sin(2 * math.pi * i / 12)) for i in range(12)]
    out["brocade_flower"].append(prism(disc, zf + 0.09, zf + 0.15))

    meta = {"apex_y": apex_y, "R": R, "layers": layers, "z_front": zf + 0.15}
    return out, meta
