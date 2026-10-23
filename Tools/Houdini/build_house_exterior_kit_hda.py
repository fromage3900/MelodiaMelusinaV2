"""Melusina's House exterior kit HDA (melodia::house_exterior_kit) - create-only baroque ornament for the exterior (goal 5m, REF_01).

Extends, never forks: the mesh DSL (Mesh, box, beam, ring, sphere, prism, pointed, star_pts, heart_pts, chladni_segments) is the
self-contained Tools/Houdini/room_shell/room_shell.py source, embedded verbatim into the Python SOP so Houdini Engine needs no project
imports. Attaches to the MEASURED live house volumes (UE metres, z-up, ground 0): salon, bedroom, corridor, porch. Adds only:
scalloped eave fascia, ridge cresting + finials (one treble clef), quoins, string courses, oculi with Chladni tracery, round-arched
entrance with carved surround + sunburst fanlight, round tower with onion/ogee/cone cap, porch posts + baluster rail + fretwork
brackets, lanterns, a curved stoop with volutes. Every feature is a parameter (toggle, count, size, seed).

Emits Houdini space (x, z, y) so Houdini Engine lands it at UE (x, y, z) unmirrored (proven for the terrain HDA), winding corrected.
Candidate only: Saved/Staging/HouseExterior_20261023/. Run: hython Tools/Houdini/build_house_exterior_kit_hda.py
"""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
STAGE = ROOT / "Saved" / "Staging" / "HouseExterior_20261023"
AUDIT = ROOT / "Saved" / "Audit" / "HouseExterior_20261023"
HDA_PATH = STAGE / "MelodiaHouseExteriorKit_1.0.hda"
TYPE_NAME = "melodia::house_exterior_kit::1.0"
ROOM_SHELL = ROOT / "Tools" / "Houdini" / "room_shell" / "room_shell.py"
FOOTPRINT = {"xmin": -11.82, "xmax": 25.70, "ymin": -11.79, "ymax": 0.27}
import hda_promote_controls as promote  # noqa: E402
import hou  # noqa: E402

# (name, label, default, lo, hi, kind)  kind: f float, i int
PARMS = [
    ("seed", "Seed", 7, 0, 99999, "i"),
    ("ornament_scale", "Ornament scale", 1.0, 0.4, 2.5, "f"),
    ("scallops", "Eave scallop fascia (0/1)", 1, 0, 1, "i"),
    ("scallop_r", "Scallop radius (m)", 0.26, 0.08, 0.8, "f"),
    ("scallop_drop", "Scallop drop (m)", 0.30, 0.05, 1.0, "f"),
    ("roof_skin", "Fish-scale roof skin (0/1)", 1, 0, 1, "i"),
    ("roof_scale_r", "Roof scale radius (m)", 0.36, 0.12, 0.8, "f"),
    ("roof_lift", "Roof skin lift above the roof (m)", 0.07, 0.0, 0.5, "f"),
    ("roof_k", "Roof curvature scale (1 = measured)", 1.0, 0.0, 3.0, "f"),
    ("cresting", "Ridge cresting + finials (0/1)", 1, 0, 1, "i"),
    ("finial_every_m", "Finial spacing (m)", 2.4, 0.8, 8.0, "f"),
    ("treble_clef", "Treble clef finial (0/1)", 1, 0, 1, "i"),
    ("quoins", "Corner quoins (0/1)", 1, 0, 1, "i"),
    ("string_course", "String course bands (0/1)", 1, 0, 1, "i"),
    ("oculus_count", "Oculus windows", 3, 0, 8, "i"),
    ("oculus_r", "Oculus radius (m)", 0.62, 0.25, 1.4, "f"),
    ("tracery_n", "Tracery Chladni mode n", 3, 1, 12, "i"),
    ("tracery_m", "Tracery Chladni mode m", 5, 1, 12, "i"),
    ("entrance", "Arched entrance surround (0/1)", 1, 0, 1, "i"),
    ("fan_rays", "Sunburst fanlight rays", 15, 5, 41, "i"),
    ("tower", "Round tower (0/1)", 1, 0, 1, "i"),
    ("tower_x", "Tower X (m)", 16.7, -20.0, 40.0, "f"),
    ("tower_y", "Tower Y (m)", -11.0, -30.0, 10.0, "f"),
    ("tower_r", "Tower radius (m)", 1.9, 0.8, 4.0, "f"),
    ("tower_h", "Tower wall height (m)", 10.4, 4.0, 20.0, "f"),
    ("cap_style", "Tower cap (0 onion, 1 ogee, 2 cone)", 0, 0, 2, "i"),
    ("cap_h", "Tower cap height (m)", 4.3, 1.0, 10.0, "f"),
    ("porch_rail", "Porch posts + baluster rail (0/1)", 1, 0, 1, "i"),
    ("baluster_every_m", "Baluster spacing (m)", 0.16, 0.06, 0.5, "f"),
    ("fretwork", "Fretwork brackets (0/1)", 1, 0, 1, "i"),
    ("stoop", "Curved stoop with volutes (0/1)", 1, 0, 1, "i"),
    ("stoop_steps", "Stoop steps", 3, 1, 6, "i"),
    ("lanterns", "Lanterns (0/1)", 1, 0, 1, "i"),
    ("engine_flip", "Reverse winding for Houdini Engine (0/1)", 1, 0, 1, "i"),
]
NAMES = [p[0] for p in PARMS]

KIT = r'''
import math, random
node = hou.pwd(); hda = node.parent()
def P(n): return hda.parm(n).eval()
rng = random.Random(int(P("seed")))
S = P("ornament_scale")
M = Mesh(); FEAT = []
def mark(n0, name, role):
    FEAT.extend([(name, M.R[i]) for i in range(n0, len(M.F))])
# measured live volumes (UE metres): x0, x1, y0, y1, eave z, ridge z
VOL = {"salon": (0.3, 16.1, -11.8, 0.2, 7.2, 8.9), "bedroom": (-11.9, 0.3, -10.7, -0.5, 4.9, 6.3), "corridor": (15.7, 23.3, -7.8, -3.8, 3.6, 5.0)}
PORCH = (22.9, 25.7, -7.8, -3.8)
ROOF = {"salon": (0.5, 15.9, -11.7, -0.1, 8.2, 8.88, 0.03), "bedroom": (-11.9, 0.3, -10.7, -0.5, -5.3, 6.3, 0.03), "corridor": (17.0, 23.4, -7.9, -3.7, 19.8, 4.82, 0.065)}   # x0, x1, y0, y1, xc, crest z, k (traced live)
def roofz(name, x): return ROOF[name][5] - ROOF[name][6] * P("roof_k") * (x - ROOF[name][4]) ** 2

def add(a, b): return (a[0] + b[0], a[1] + b[1], a[2] + b[2])
def mul(a, s): return (a[0] * s, a[1] * s, a[2] * s)
def cross(a, b): return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])

def plate(pts2, o, u, v, t, role):
    """Extrude a star-shaped CCW (u,v) polygon about origin o by thickness t along n = u x v; faces outward."""
    n = cross(u, v); h = t / 2.0
    fr = [add(o, add(mul(u, x), add(mul(v, y), mul(n, h)))) for x, y in pts2]
    bk = [add(o, add(mul(u, x), add(mul(v, y), mul(n, -h)))) for x, y in pts2]
    cf = add(o, mul(n, h)); cb = add(o, mul(n, -h)); k = len(pts2)
    for i in range(k):
        j = (i + 1) % k
        M.poly([cf, fr[i], fr[j]], role)
        M.poly([cb, bk[j], bk[i]], role)
        M.poly([fr[i], bk[i], bk[j], fr[j]], role)

def lathe(cx, cy, prof, role, seg=20):
    rings = [[(cx + r * math.cos(math.tau * j / seg), cy + r * math.sin(math.tau * j / seg), z) for j in range(seg)] for r, z in prof]
    for i in range(len(prof) - 1):
        for j in range(seg):
            a, b, c, d = rings[i][j], rings[i][(j + 1) % seg], rings[i + 1][(j + 1) % seg], rings[i + 1][j]
            r0, r1 = prof[i][0], prof[i + 1][0]
            if r0 < 1e-4 and r1 < 1e-4: continue
            if r0 < 1e-4: M.poly([a, c, d], role)
            elif r1 < 1e-4: M.poly([a, b, c], role)
            else: M.poly([a, b, c, d], role)

def arc_beams(c, u, v, r, a0, a1, n, w, d, role):
    pts = [add(c, add(mul(u, r * math.cos(a0 + (a1 - a0) * i / n)), mul(v, r * math.sin(a0 + (a1 - a0) * i / n)))) for i in range(n + 1)]
    for p, q in zip(pts, pts[1:]): beam(M, p, q, w, d, role)

def volute(c, u, v, r0, turns, n, w, d, role, sgn=1.0):
    pts = []
    for i in range(n + 1):
        th = sgn * turns * math.tau * i / n; r = r0 * math.exp(-0.9 * turns * i / n)
        pts.append(add(c, add(mul(u, r * math.cos(th)), mul(v, r * math.sin(th)))))
    for p, q in zip(pts, pts[1:]): beam(M, p, q, w, d, role)

def finial(x, y, z, s, role):
    beam(M, (x, y, z), (x, y, z + 0.30 * s), 0.05 * s, 0.05 * s, role)
    sphere(M, (x, y, z + 0.36 * s), 0.07 * s, role, 4, 8)
    for sx in (-1, 1):
        beam(M, (x, y, z + 0.18 * s), (x + sx * 0.14 * s, y, z + 0.30 * s), 0.035 * s, 0.035 * s, role)
    octa(M, (x, y, z + 0.52 * s), 0.05 * s, 0.10 * s, role)

def treble_clef(x, y, z, s, role):
    """Finial treble clef in the x-z plane: stem, upper loop, lower curl, ball."""
    u, v = (1, 0, 0), (0, 0, 1)
    beam(M, (x, y, z), (x, y, z + 1.1 * s), 0.05 * s, 0.05 * s, role)
    arc_beams((x, y, z + 0.80 * s), u, v, 0.22 * s, -math.pi * 0.4, math.pi * 1.6, 14, 0.04 * s, 0.05 * s, role)
    arc_beams((x - 0.02 * s, y, z + 0.30 * s), u, v, 0.18 * s, math.pi * 0.2, math.pi * 1.9, 12, 0.04 * s, 0.05 * s, role)
    sphere(M, (x - 0.18 * s, y, z - 0.02 * s), 0.05 * s, role, 4, 8)

def ring_vol(name):
    x0, x1, y0, y1, ez, rz = VOL[name]; return x0, x1, y0, y1, ez, rz

# ---- scalloped eave fascia (hanging half-discs under every roof edge)
if P("scallops"):
    n0 = len(M.F); r = P("scallop_r") * S; drop = P("scallop_drop") * S
    semi = [(-r, 0.0)] + [(r * math.cos(math.pi + math.pi * k / 10.0), -drop * math.sin(math.pi * k / 10.0)) for k in range(1, 10)] + [(r, 0.0)]
    for name in VOL:
        x0, x1, y0, y1, ez, rz = VOL[name]
        edges = [((x0, y0, ez), (1, 0, 0), x1 - x0), ((x1, y1, ez), (-1, 0, 0), x1 - x0), ((x1, y0, ez), (0, 1, 0), y1 - y0), ((x0, y1, ez), (0, -1, 0), y1 - y0)]
        for (start, ud, L) in edges:
            k = max(1, int(L / (2 * r)))
            for i in range(k):
                c = add(start, mul(ud, (i + 0.5) * L / k))
                if name in ROOF and ud[0] != 0:
                    c = (c[0], c[1], roofz(name, c[0]) - 0.02)
                plate(semi, c, ud, (0, 0, 1), 0.04, "scallop_fascia")
    mark(n0, "scallops", "scallop_fascia")

# ---- ridge cresting + finials along the real ridge (x = xc, running along y)
if P("cresting"):
    n0 = len(M.F)
    for name in ROOF:
        x0, x1, y0, y1, xc, zc = ROOF[name][:6]
        k = max(2, int((y1 - y0) / P("finial_every_m")))
        for i in range(k + 1):
            finial(xc, y0 + (y1 - y0) * i / k, zc, S * (1.4 if i in (0, k) else 1.0), "ridge_finial")
        beam(M, (xc, y0, zc), (xc, y1, zc), 0.12 * S, 0.09 * S, "ridge_finial")
    mark(n0, "cresting", "ridge_finial")
    if P("treble_clef"):
        n0 = len(M.F); x0, x1, y0, y1, xc, zc = ROOF["salon"][:6]
        treble_clef(xc, y0 - 0.1, zc + 0.5 * S, 1.3 * S, "ridge_finial"); mark(n0, "treble_clef", "ridge_finial")

# ---- fish-scale roof skin on the measured barrel arches
if P("roof_skin"):
    n0 = len(M.F); r = P("roof_scale_r") * S; lift = P("roof_lift"); kk = 1.0
    for name in ROOF:
        x0, x1, y0, y1, xc, zc = ROOF[name][:6]
        x = x0 - 0.15; row = 0
        while x <= x1 + 0.15:
            dz = -2.0 * ROOF[name][6] * P("roof_k") * (x - xc); left = x < xc
            ul = math.sqrt(1.0 + dz * dz)
            u = (1.0 / ul, 0.0, dz / ul); v = (0.0, 1.0, 0.0)
            if not left: u = mul(u, -1.0); v = (0.0, -1.0, 0.0)     # keep n = u x v pointing up; the scalloped edge faces downslope
            y = y0 - 0.2 + (r if row % 2 else 0.0)
            while y <= y1 + 0.2:
                c = (x, y, roofz(name, x) + lift + (0.012 if row % 2 else 0.0))
                pts2 = [(r * 0.7, -r), (0.0, -r)] + [(-r * math.sin(math.pi * t / 6.0), -r * math.cos(math.pi * t / 6.0)) for t in range(1, 6)] + [(0.0, r), (r * 0.7, r)]
                ptsw = [add(c, add(mul(u, a), mul(v, b))) for a, b in pts2]
                cf = c; kq = len(ptsw)
                for i in range(kq):
                    M.poly([cf, ptsw[i], ptsw[(i + 1) % kq]], "roof_scale" if row % 2 == 0 else "roof_scale_b")
                n = cross(u, v)
                for i in range(2, kq - 2):                          # the scalloped lip only: a thin skirt reads as overlapping tiles
                    a, b = ptsw[i], ptsw[(i + 1) % kq]
                    M.poly([a, add(a, mul(n, -0.035 * S)), add(b, mul(n, -0.035 * S)), b], "roof_scale" if row % 2 == 0 else "roof_scale_b")
                y += 2.0 * r
            x += 0.62 * r; row += 1
    mark(n0, "roof_skin", "roof_scale")

# ---- corner quoins + string courses
def wall_faces(name):
    x0, x1, y0, y1, ez, rz = VOL[name]; return x0, x1, y0, y1, ez
if P("quoins"):
    n0 = len(M.F)
    for name in ("salon", "bedroom"):
        x0, x1, y0, y1, ez = wall_faces(name)
        for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            z = 0.2; i = 0
            while z < ez - 0.3:
                h = 0.34; w = 0.46 if i % 2 == 0 else 0.30; w2 = 0.30 if i % 2 == 0 else 0.46
                box(M, (cx - (0.06 if sx > 0 else w) * 0 + min(0, sx * -0.06), cy, z), (cx, cy, z), "quoin") if False else None
                xa, xb = sorted((cx - sx * 0.05, cx + sx * w)); ya, yb = sorted((cy - sy * 0.05, cy + sy * 0.12))
                box(M, (xa, ya, z), (xb, yb, z + h - 0.02), "quoin")
                xa, xb = sorted((cx - sx * 0.05, cx + sx * 0.12)); ya, yb = sorted((cy - sy * 0.05, cy + sy * w2))
                box(M, (xa, ya, z), (xb, yb, z + h - 0.02), "quoin")
                z += h; i += 1
    mark(n0, "quoins", "quoin")
if P("string_course"):
    n0 = len(M.F)
    for name, z in (("salon", 3.3), ("bedroom", 2.6), ("corridor", 2.2)):
        x0, x1, y0, y1, ez, rz = VOL[name]; p = 0.07
        box(M, (x0 - p, y0 - p, z), (x1 + p, y0, z + 0.14), "string_course"); box(M, (x0 - p, y1, z), (x1 + p, y1 + p, z + 0.14), "string_course")
        box(M, (x0 - p, y0, z), (x0, y1, z + 0.14), "string_course"); box(M, (x1, y0, z), (x1 + p, y1, z + 0.14), "string_course")
    mark(n0, "string_course", "string_course")

# ---- oculus windows with Chladni tracery on the salon south wall (faces -y)
nO = int(P("oculus_count"))
if nO > 0:
    n0 = len(M.F); x0, x1, y0, y1, ez, rz = VOL["salon"]; r = P("oculus_r") * S
    u, v = (1, 0, 0), (0, 0, 1); span = (x1 - 3.0) - (x0 + 2.0)
    segs = chladni_segments(int(P("tracery_n")), int(P("tracery_m")), 40)
    for k in range(nO):
        cx = x0 + 2.0 + span * (k + 0.5) / nO; c = (cx, y0 - 0.03, 5.5)
        arc_beams(c, u, v, r, 0, math.tau, 28, 0.10 * S, 0.10 * S, "oculus_frame")
        arc_beams(c, u, v, r * 1.28, 0, math.tau, 32, 0.05 * S, 0.07 * S, "oculus_frame")
        for sgm in segs:
            (ax, az), (bx, bz) = sgm
            if ax * ax + az * az < 1.0 and bx * bx + bz * bz < 1.0:
                a = (c[0] + ax * r * 0.94, c[1] - 0.01, c[2] + az * r * 0.94); b = (c[0] + bx * r * 0.94, c[1] - 0.01, c[2] + bz * r * 0.94)
                beam(M, a, b, 0.025 * S, 0.03 * S, "tracery")
        for kk in range(8):
            th = math.tau * kk / 8
            beam(M, add(c, add(mul(u, r * 1.28 * math.cos(th)), mul(v, r * 1.28 * math.sin(th)))), add(c, add(mul(u, r * 1.5 * math.cos(th)), mul(v, r * 1.5 * math.sin(th)))), 0.04 * S, 0.05 * S, "oculus_frame")
    mark(n0, "oculi", "oculus_frame")

# ---- arched entrance surround + sunburst fanlight on the corridor east face (faces +x)
if P("entrance"):
    n0 = len(M.F); fx = VOL["corridor"][1] + 0.04; yc = (VOL["corridor"][2] + VOL["corridor"][3]) / 2.0; zs = 2.35; rr = 0.95 * S
    u, v = (0, 1, 0), (0, 0, 1); c = (fx, yc, zs)
    for sgn in (-1, 1):
        box(M, (fx, yc + sgn * rr - 0.09 * S, 0.0), (fx + 0.14 * S, yc + sgn * rr + 0.09 * S, zs), "carved_trim")
        box(M, (fx, yc + sgn * (rr + 0.30 * S) - 0.07 * S, 0.0), (fx + 0.10 * S, yc + sgn * (rr + 0.30 * S) + 0.07 * S, zs - 0.2), "carved_trim")
        volute(add(c, mul(u, sgn * (rr + 0.30 * S))), (0, sgn, 0), v, 0.24 * S, 1.6, 16, 0.045 * S, 0.06 * S, "carved_trim", sgn)
    arc_beams(c, u, v, rr, 0, math.pi, 20, 0.16 * S, 0.14 * S, "carved_trim")
    arc_beams(c, u, v, rr + 0.30 * S, 0, math.pi, 24, 0.10 * S, 0.10 * S, "carved_trim")
    for k in range(int(P("fan_rays"))):
        th = math.pi * (k + 0.5) / P("fan_rays")
        beam(M, c, add(c, add(mul(u, 0.88 * S * math.cos(th)), mul(v, 0.88 * S * math.sin(th)))), 0.025 * S, 0.04 * S, "fanlight")
    box(M, (fx, yc - 0.12 * S, zs + rr + 0.04), (fx + 0.16 * S, yc + 0.12 * S, zs + rr + 0.40 * S), "carved_trim")
    plate(heart_pts(0.20 * S, 0, 0, 18), (fx + 0.12 * S, yc, zs + rr + 0.62 * S), u, v, 0.06, "carved_trim")
    mark(n0, "entrance", "carved_trim")

# ---- round tower with banded wall + balcony + cap
if P("tower"):
    n0 = len(M.F); tx, ty, tr, th_ = P("tower_x"), P("tower_y"), P("tower_r") * S, P("tower_h")
    lathe(tx, ty, [(tr, 0.0), (tr, th_)], "tower_wall", 24)
    for z in (1.2, 3.4, 5.6, 7.8, th_ - 0.2):
        lathe(tx, ty, [(tr + 0.10, z), (tr + 0.10, z + 0.14)], "tower_wall", 24)
    lathe(tx, ty, [(tr + 0.05, 7.0), (tr + 0.55, 7.1), (tr + 0.55, 7.25), (tr + 0.05, 7.3)], "tower_wall", 24)
    for k in range(24):
        a = math.tau * k / 24; bx, by = tx + (tr + 0.52) * math.cos(a), ty + (tr + 0.52) * math.sin(a)
        beam(M, (bx, by, 7.25), (bx, by, 8.15), 0.04, 0.04, "tower_wall")
    lathe(tx, ty, [(tr + 0.55, 8.12), (tr + 0.55, 8.22)], "tower_wall", 24)
    for k in range(6):
        a = math.tau * (k + 0.5) / 6; wx, wy = tx + (tr + 0.02) * math.cos(a), ty + (tr + 0.02) * math.sin(a)
        plate(pointed(0.28, 0.5, 8)[:], (wx, wy, 5.0 + 0.0), (-math.sin(a), math.cos(a), 0), (0, 0, 1), 0.08, "tower_window")
    ch = P("cap_h") * S; cs = int(P("cap_style"))
    if cs == 0:
        prof = [(tr + 0.25, th_), (tr + 0.55, th_ + 0.35 * ch / 4.3), (tr + 0.70, th_ + 0.80 * ch / 4.3), (tr + 0.50, th_ + 1.45 * ch / 4.3), (tr * 0.62, th_ + 2.2 * ch / 4.3), (tr * 0.30, th_ + 3.0 * ch / 4.3), (tr * 0.10, th_ + 3.7 * ch / 4.3), (0.0, th_ + ch)]
    elif cs == 1:
        prof = [(tr + 0.25, th_), (tr + 0.35, th_ + 0.30 * ch / 4.3), (tr * 0.85, th_ + 1.2 * ch / 4.3), (tr * 0.55, th_ + 2.0 * ch / 4.3), (tr * 0.20, th_ + 3.3 * ch / 4.3), (0.0, th_ + ch)]
    else:
        prof = [(tr + 0.30, th_), (tr * 0.6, th_ + ch * 0.5), (0.0, th_ + ch)]
    lathe(tx, ty, prof, "tower_cap", 24)
    finial(tx, ty, th_ + ch, S * 1.8, "tower_cap")
    mark(n0, "tower", "tower_wall")

# ---- porch posts, baluster rail, fretwork brackets
px0, px1, py0, py1 = PORCH
if P("porch_rail"):
    n0 = len(M.F); s = 0.12 * S
    runs = [((px0, py0), (px1, py0)), ((px1, py0), (px1, py1)), ((px1, py1), (px0, py1))]
    for (a, b) in runs:
        L = math.hypot(b[0] - a[0], b[1] - a[1]); k = max(1, int(L / 1.0))
        for i in range(k + 1):
            x = a[0] + (b[0] - a[0]) * i / k; y = a[1] + (b[1] - a[1]) * i / k
            box(M, (x - s / 2, y - s / 2, 0.0), (x + s / 2, y + s / 2, 1.05 * S), "porch_post")
        beam(M, (a[0], a[1], 1.05 * S), (b[0], b[1], 1.05 * S), 0.10 * S, 0.07 * S, "porch_post")
        beam(M, (a[0], a[1], 0.12 * S), (b[0], b[1], 0.12 * S), 0.07 * S, 0.06 * S, "porch_post")
        nb = int(L / P("baluster_every_m"))
        for i in range(1, nb):
            x = a[0] + (b[0] - a[0]) * i / nb; y = a[1] + (b[1] - a[1]) * i / nb
            beam(M, (x, y, 0.14 * S), (x, y, 1.02 * S), 0.035 * S, 0.035 * S, "baluster")
    mark(n0, "porch_rail", "porch_post")
if P("fretwork"):
    n0 = len(M.F)
    for (x, y, ux, uy) in ((px1, py0, 0, 1), (px1, py1, 0, -1), (px1, (py0 + py1) / 2.0, 0, 1)):
        for sg in (-1, 1) if (x, y) == (px1, (py0 + py1) / 2.0) else (1,):
            c = (x, y, 2.5 * S)
            plate(star_pts(0.22 * S, 0.11 * S, 6, 0.0), c, (ux, uy, 0), (0, 0, 1), 0.05, "fretwork")
            beam(M, (x, y, 2.5 * S), (x, y, 1.05 * S), 0.06 * S, 0.06 * S, "porch_post")
    mark(n0, "fretwork", "fretwork")

# ---- curved stoop (low arc steps) with volutes
if P("stoop"):
    n0 = len(M.F); yc = (py0 + py1) / 2.0; ns = int(P("stoop_steps"))
    for k in range(ns):
        r_in = 0.0 if k == 0 else 0.0; r_out = 1.9 * S + 0.42 * S * (ns - 1 - k); hz = 0.10 * (k + 1)
        pts = [(px1 + r_out * math.cos(-math.pi / 2 + math.pi * i / 16), yc + r_out * 1.0 * math.sin(-math.pi / 2 + math.pi * i / 16)) for i in range(17)]
        prism(M, [(px1, yc - r_out)] + [(p[0], p[1]) for p in pts[1:-1]] + [(px1, yc + r_out)], 0.0, hz, "stoop", cx=px1, cy=yc) if False else None
        for a, b in zip(pts, pts[1:]):
            box(M, (min(a[0], b[0]), min(a[1], b[1]), 0.0), (max(a[0], b[0]) + 0.02, max(a[1], b[1]) + 0.02, hz), "stoop")
    r_end = 1.9 * S + 0.42 * S * (ns - 1)
    for sg in (-1, 1):
        volute((px1 + 0.1, yc + sg * r_end, 0.7 * S), (1, 0, 0), (0, 0, 1), 0.28 * S, 1.5, 14, 0.05 * S, 0.07 * S, "carved_trim", 1.0)
    mark(n0, "stoop", "stoop")

# ---- lanterns on the porch corner posts + tower base
if P("lanterns"):
    n0 = len(M.F)
    for (x, y) in ((px1, py0), (px1, py1), (px0, py0), (px0, py1)):
        beam(M, (x, y, 1.05 * S), (x, y, 1.38 * S), 0.05 * S, 0.05 * S, "porch_post")
        sphere(M, (x, y, 1.52 * S), 0.12 * S, "lantern", 4, 10)
        octa(M, (x, y, 1.72 * S), 0.08 * S, 0.10 * S, "lantern")
    mark(n0, "lanterns", "lantern")

assert len(FEAT) == len(M.F), (len(FEAT), len(M.F))
g = node.geometry(); g.clear()
g.addAttrib(hou.attribType.Prim, "material_role", ""); g.addAttrib(hou.attribType.Prim, "feature", "")
g.addAttrib(hou.attribType.Prim, "shop_materialpath", "")
flip = bool(P("engine_flip"))
pts = g.createPoints([(p[0], p[2], p[1]) for p in M.P])     # (x, z, y): Houdini Y-up -> UE (x, y, z) unmirrored
for face, (feat, role) in zip(M.F, FEAT):
    face = list(face) if flip else list(reversed(face))
    poly = g.createPolygon(); poly.setAttribValue("material_role", role); poly.setAttribValue("feature", feat)
    poly.setAttribValue("shop_materialpath", "/mat/House_" + role)
    for i in face: poly.addVertex(pts[i])
'''

MAT_VEX = r'''
string r = s@material_role;
string base = "/Game/Staging/HouseExterior/Materials/";
string m = "MI_HouseExt_PearlPlaster";
if (r == "scallop_fascia" || r == "tower_cap" || r == "roof_scale" || r == "roof_scale_b") m = "MI_HouseExt_LavenderScaleRoof";
else if (r == "ridge_finial" || r == "carved_trim" || r == "tracery" || r == "oculus_frame" || r == "fanlight" || r == "fretwork" || r == "tower_window") m = "MI_HouseExt_GiltTrim";
else if (r == "lantern") m = "MI_HouseExt_LanternGlow";
if (r == "roof_scale_b") m = "MI_HouseExt_BlueScaleRoof";
s@unreal_material = base + m + "." + m;
'''


def make_controls(geo):
    controls = geo.createNode("null", "controls")
    pg = controls.parmTemplateGroup()
    f = hou.FolderParmTemplate("kit", "Exterior Kit", folder_type=hou.folderType.Tabs)
    for name, label, default, lo, hi, kind in PARMS:
        if kind == "i":
            f.addParmTemplate(hou.IntParmTemplate(name, label, 1, default_value=(default,), min=lo, max=hi))
        else:
            f.addParmTemplate(hou.FloatParmTemplate(name, label, 1, default_value=(default,), min=lo, max=hi))
    pg.append(f)
    controls.setParmTemplateGroup(pg)
    return controls


def build_network(geo):
    controls = make_controls(geo)
    src = ROOM_SHELL.read_text(encoding="utf-8")
    py = geo.createNode("python", "build_exterior_kit")
    py.parm("python").set(src + "\n" + KIT)
    mat = geo.createNode("attribwrangle", "unreal_material_per_role")
    mat.setInput(0, py)
    mat.parm("class").set(1)
    mat.parm("snippet").set(MAT_VEX)
    out = geo.createNode("null", "OUT_HOUSE_EXTERIOR_KIT")
    out.setInput(0, mat)
    out.setDisplayFlag(True)
    out.setRenderFlag(True)
    for n in geo.children():
        n.moveToGoodPosition()
    return controls


def features(hda):
    g = hda.node("OUT_HOUSE_EXTERIOR_KIT").geometry()
    c = {}
    for pr in g.prims():
        k = pr.attribValue("feature")
        c[k] = c.get(k, 0) + 1
    return g, c


def sig(hda):
    g = hda.node("OUT_HOUSE_EXTERIOR_KIT").geometry()
    return round(sum(p.position()[0] * 1.3 + p.position()[1] * 0.7 + p.position()[2] * 0.3 for p in g.points()), 3), len(g.points())


def main():
    STAGE.mkdir(parents=True, exist_ok=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "MelodiaHouseExteriorKit")
    for c in geo.children():
        c.destroy()
    controls = build_network(geo)
    pairs = promote.stage1_promote(controls, geo, NAMES, hou)
    promote.stage1_wire(controls, pairs, hou)
    hda = geo.createDigitalAsset(name=TYPE_NAME, hda_file_name=str(HDA_PATH), description="Melodia House Exterior Kit (baroque ornament)", min_num_inputs=0, max_num_inputs=0, version="1.0")
    promote.stage2_promote_definition(hda, pairs, HDA_PATH, hou)
    hda.matchCurrentDefinition()

    t = time.time()
    g, cnt = features(hda)
    cook_s = round(time.time() - t, 2)
    bb = g.boundingBox()
    lo, hi = bb.minvec(), bb.maxvec()
    errs = list(hda.node("build_exterior_kit").errors()) + list(hda.node("unreal_material_per_role").errors())
    # Houdini (x, z, y) -> UE (x, y, z)
    ue_min, ue_max = (lo[0], lo[2], lo[1]), (hi[0], hi[2], hi[1])
    roles = sorted({pr.attribValue("material_role") for pr in g.prims()})
    a = {}
    a["no_cook_errors"] = not errs
    a["cook_under_5s"] = cook_s < 5.0
    expect = {"scallops": 40, "roof_skin": 5000, "cresting": 20, "treble_clef": 10, "quoins": 30, "string_course": 10, "oculi": 100, "entrance": 80, "tower": 400, "porch_rail": 60, "fretwork": 6, "stoop": 6, "lanterns": 20}
    for k, minimum in expect.items():
        a["feature_" + k] = cnt.get(k, 0) >= minimum
    a["bounds_attach_to_footprint"] = (ue_min[0] > FOOTPRINT["xmin"] - 4.0 and ue_max[0] < FOOTPRINT["xmax"] + 8.0 and ue_min[1] > FOOTPRINT["ymin"] - 4.0 and ue_max[1] < FOOTPRINT["ymax"] + 4.0 and ue_min[2] > -0.5 and ue_max[2] < 20.0)
    a["material_roles_set"] = all(r for r in roles) and len(roles) >= 14
    a["unreal_material_on_all_prims"] = all(pr.attribValue("unreal_material") for pr in g.prims()) if g.findPrimAttrib("unreal_material") else False
    # live-parameter drive probes: toggle a feature, count change; seed/oculus change geometry
    base = sig(hda)
    hda.parm("oculus_count").set(5)
    a["drive_oculus_count"] = features(hda)[1].get("oculi", 0) > cnt.get("oculi", 0)
    hda.parm("oculus_count").set(3)
    hda.parm("tower").set(0)
    a["drive_tower_off"] = features(hda)[1].get("tower", 0) == 0
    hda.parm("tower").set(1)
    hda.parm("tracery_n").set(4)
    a["drive_tracery_mode"] = sig(hda) != base
    hda.parm("tracery_n").set(3)
    hda.parm("cap_style").set(1)
    a["drive_cap_style"] = sig(hda) != base
    hda.parm("cap_style").set(0)
    hda.parm("roof_skin").set(0)
    a["drive_roof_skin_off"] = features(hda)[1].get("roof_skin", 0) == 0
    hda.parm("roof_skin").set(1)
    a["restored_after_probes"] = sig(hda) == base
    report = {"asset": str(HDA_PATH), "type": TYPE_NAME, "feature_prims": cnt, "points": len(g.points()), "prims": len(g.prims()), "cook_seconds": cook_s,
              "bounds_ue_m": [[round(v, 2) for v in ue_min], [round(v, 2) for v in ue_max]], "roles": roles, "errors": errs, "controls": {k: hda.parm(k).eval() for k in NAMES}, "assertions": a}
    (AUDIT / "exterior_kit_gate.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    hou.hipFile.save(str(AUDIT / "MelodiaHouseExteriorKit.hip"))
    failed = [k for k, v in a.items() if not v]
    print("GATE " + json.dumps({"failed": failed, "features": cnt, "points": len(g.points()), "bounds": report["bounds_ue_m"], "cook_s": cook_s, "errors": errs}))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
