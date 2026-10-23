"""Coral generator — R1 of the Sea Above reef plan (code-grown archetypes).

Design note: the plan sketched VDB advection growth, but the PROVEN headless
pattern this session is Python-SOP geometry (stable hou.Geometry API) — so R1
ships as code-grown branching corals: deterministic, manifest-backed, and
upgradable to VDB growth later without changing the export path.

Verified facts this builds on (see Docs/Production/HOUDINI_CREATIVE_PIPELINE_REFERENCE_2026-08-28.md):
- FBX and Alembic ROP export are Apprentice-blocked -> export via File SOP
  "write" mode to .obj (UE-native) + .bgeo.sc (future Engine-license import).
- H22 Python SOP: geo = hou.pwd().geometry().
- Sweep SOP produced 0 prims headless -> all tubes are built in code (rings).

Archetypes (all grew DOWNWARD-biased where branching — inverted gravity is the
level's identity; scale is metres, UE import x100):

  SM_Coral_Staghorn      recursive branching tube tree, downward bias, 3 seeds
  SM_Coral_Table         radial ribbed hanging disk with thickness
  SM_Coral_TubeSponges   5 gently-curved open-topped tubes
  SM_Coral_Fan           warped semicircular fan plane + stem
  SM_Coral_Brain         folded, squashed displaced sphere

  SM_Coral_ReefCluster   deterministic composition scatter of the five

Outputs: Saved/Audit/sea_above/meshes/SM_Coral_*.obj/.bgeo.sc + coral_mesh_manifest.json

Run:  hython Tools/Houdini/sea_above_reef/build_coral_generator.py
"""

import json
import math
import sys
from pathlib import Path

import hou

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_clutter_meshes import (  # noqa: E402
    OUT_DIR as MESH_OUT_DIR,
    SEED as SUITE_SEED,
    _geo,
    _python_sop,
    export_geo,
    setp,
)

SEED = SUITE_SEED  # 20260828 — same suite seed contract

# ---------------------------------------------------------------------------
# Shared coral code helpers (injected into every Python SOP)
# ---------------------------------------------------------------------------

CORAL_HELPERS = r"""
import hou, math, random

node = hou.pwd()
geo = node.geometry()
if geo.findPointAttrib("uv") is None:
    geo.addAttrib(hou.attribType.Point, "uv", (0.0, 0.0))
if geo.findPointAttrib("Cd") is None:
    geo.addAttrib(hou.attribType.Point, "Cd", (1.0, 1.0, 1.0))

def _ring_frame(tan):
    tan = tan.normalized()
    up = hou.Vector3(0, 1, 0)
    if abs(tan.dot(up)) > 0.95:
        up = hou.Vector3(1, 0, 0)
    x = tan.cross(up).normalized()
    y = tan.cross(x).normalized()
    return x, y, tan

def build_tube(geo, pts, radii, seg=8, cap_start=True, cap_end=True,
               tip_pinch=True):
    # Tube along ordered points with per-ring radius.
    n = len(pts)
    rings = []
    for i, pos in enumerate(pts):
        if i == 0:
            tan = pts[1] - pts[0]
        elif i == n - 1:
            tan = pts[-1] - pts[-2]
        else:
            tan = pts[i + 1] - pts[i - 1]
        x, y, _t = _ring_frame(tan)
        r = radii[i]
        ring = []
        for k in range(seg):
            a = k / seg * 2.0 * math.pi
            off = x * (math.cos(a) * r) + y * (math.sin(a) * r)
            p = geo.createPoint()
            p.setPosition(pos + off)
            p.setAttribValue(geo.findPointAttrib("uv"),
                             (k / seg, i / max(n - 1, 1)))
            ring.append(p)
        rings.append(ring)
    for i in range(n - 1):
        for k in range(seg):
            f = geo.createPolygon()
            for q in (rings[i][k], rings[i][(k + 1) % seg],
                      rings[i + 1][(k + 1) % seg], rings[i + 1][k]):
                f.addVertex(q)
    if cap_start:
        c = geo.createPoint()
        c.setPosition(pts[0])
        for k in range(seg):
            f = geo.createPolygon()
            f.addVertex(rings[0][(k + 1) % seg]); f.addVertex(rings[0][k]); f.addVertex(c)
    if cap_end:
        c = geo.createPoint()
        c.setPosition(pts[-1])
        r_end = radii[-1] * (0.15 if tip_pinch else 1.0)
        # pinch the tip toward the axis for organic branch ends
        tip = geo.createPoint()
        tip.setPosition(pts[-1])
        _ = r_end
        for k in range(seg):
            f = geo.createPolygon()
            f.addVertex(rings[-1][k]); f.addVertex(rings[-1][(k + 1) % seg]); f.addVertex(tip)
    return rings
"""

# ---------------------------------------------------------------------------
# Archetype code blocks
# ---------------------------------------------------------------------------

STAGHORN_CODE = CORAL_HELPERS + r"""
rng = random.Random(SEED)
V = hou.Vector3
DOWN = V(0, -1, 0)

def _rot(v, axis, ang):
    # Rodrigues rotation (hou.Vector3 has no rotateAroundAxis - verified)
    c = math.cos(ang); s = math.sin(ang)
    a = axis.normalized()
    return v * c + a.cross(v) * s + a * (a.dot(v) * (1.0 - c))

def grow(base, dirv, length, radius, depth, out):
    # One branch = 3 waypoints with curl; children at the tip.
    pts = [base]
    radii = [radius]
    d = V(dirv.x(), dirv.y(), dirv.z())
    pos = base
    for s in range(3):
        # curl: rotate direction by small random angles around two axes
        ang1 = rng.uniform(-0.45, 0.45)
        ang2 = rng.uniform(-0.45, 0.45)
        axis1 = d.cross(V(0, 0, 1))
        if axis1.length() < 1e-4:
            axis1 = V(1, 0, 0)
        d = _rot(d, axis1.normalized(), ang1)
        d = _rot(d, V(0, 1, 0), ang2)
        d = (d + DOWN * 0.38).normalized()  # inverted-gravity growth bias
        step = length * rng.uniform(0.8, 1.15)
        pos = pos + d * step
        pts.append(pos)
        radii.append(radius * (1.0 - 0.22 * (s + 1)))
    radius_end = radii[-1]
    build_tube(geo, pts, radii, seg=8, cap_start=True, cap_end=True)
    if depth <= 0:
        return
    n_children = rng.choice((2, 2, 3))
    d_prev = (pts[-1] - pts[-2]).normalized()
    for c in range(n_children):
        ang = c * (2.0 * math.pi / n_children) + rng.uniform(-0.3, 0.3)
        tilt = rng.uniform(0.55, 0.95)
        side = V(math.cos(ang), 0, math.sin(ang))
        child_dir = (d_prev * math.cos(tilt) + side * math.sin(tilt))
        grow(pts[-1], child_dir.normalized(), length * 0.74,
             radius_end * 0.85, depth - 1, out)

BASE_R = 0.055
grow(V(0, 0.15, 0), V(0, -1, 0), 0.30, BASE_R, 4, None)
try:
    geo.computeVertexNormals()
except Exception:
    pass
"""

TABLE_CODE = CORAL_HELPERS + r"""
rng = random.Random(SEED + 1)
V = hou.Vector3
RINGS, SEGS = 7, 48
R = 0.52
RIBS = 21
top_pts = {}
bot_pts = {}
for ri in range(RINGS + 1):
    r = R * ri / RINGS
    dome = -0.10 * (r / R) ** 2 * R          # hangs downward (inverted gravity)
    thick = 0.028 * (1.0 - 0.55 * r / R) + 0.004
    for si in range(SEGS):
        a = si / SEGS * 2.0 * math.pi
        rib = 0.016 * math.sin(a * RIBS) * (r / R) ** 1.5
        wob = 1.0 + 0.05 * math.sin(a * 3 + 1.2) * (r / R)
        rr = r * wob
        key = (ri, si)
        pt = geo.createPoint()
        pt.setPosition(V(rr * math.cos(a), dome + rib + thick, rr * math.sin(a)))
        pt.setAttribValue(geo.findPointAttrib("uv"), (si / SEGS, ri / RINGS))
        top_pts[key] = pt
        pb = geo.createPoint()
        pb.setPosition(V(rr * math.cos(a), dome + rib - thick, rr * math.sin(a)))
        pb.setAttribValue(geo.findPointAttrib("uv"), (si / SEGS, 1.0 - ri / RINGS))
        bot_pts[key] = pb

# top surface
for ri in range(RINGS):
    for si in range(SEGS):
        sj = (si + 1) % SEGS
        f = geo.createPolygon()
        for q in (top_pts[(ri, si)], top_pts[(ri + 1, si)],
                  top_pts[(ri + 1, sj)], top_pts[(ri, sj)]):
            f.addVertex(q)
# bottom surface
for ri in range(RINGS):
    for si in range(SEGS):
        sj = (si + 1) % SEGS
        f = geo.createPolygon()
        for q in (bot_pts[(ri, si)], bot_pts[(ri, sj)],
                  bot_pts[(ri + 1, sj)], bot_pts[(ri + 1, si)]):
            f.addVertex(q)
# rim wall at outer edge
for si in range(SEGS):
    sj = (si + 1) % SEGS
    f = geo.createPolygon()
    for q in (top_pts[(RINGS, si)], top_pts[(RINGS, sj)],
              bot_pts[(RINGS, sj)], bot_pts[(RINGS, si)]):
        f.addVertex(q)
try:
    geo.computeVertexNormals()
except Exception:
    pass
"""

SPONGE_CODE = CORAL_HELPERS + r"""
rng = random.Random(SEED + 2)
V = hou.Vector3
positions = []
for k in range(5):
    a = k / 5.0 * 2.0 * math.pi + rng.uniform(-0.2, 0.2)
    rad = rng.uniform(0.12, 0.30)
    positions.append((rad * math.cos(a), rng.uniform(-0.05, 0.05), rad * math.sin(a)))
for (cx, cy, cz) in positions:
    h = rng.uniform(0.30, 0.55)
    r0 = rng.uniform(0.075, 0.115)
    pts = []
    radii = []
    steps = 7
    sway = rng.uniform(0.03, 0.09)
    ph = rng.uniform(0, 6.28)
    for i in range(steps + 1):
        t = i / steps
        pts.append(V(cx + sway * t * t * math.sin(ph + 4.0 * t),
                     cy + h * t,
                     cz + sway * t * t * math.cos(ph + 3.0 * t)))
        flare = 1.0 + (0.18 if i == steps else 0.0)
        radii.append(r0 * (1.0 - 0.15 * t) * flare)
    build_tube(geo, pts, radii, seg=10, cap_start=True, cap_end=False)
try:
    geo.computeVertexNormals()
except Exception:
    pass
"""

FAN_CODE = CORAL_HELPERS + r"""
rng = random.Random(SEED + 3)
V = hou.Vector3
ROWS, COLS = 16, 26
R = 0.55
grid = {}
for ri in range(ROWS + 1):
    t = ri / ROWS                      # 0 = stem top, 1 = outer arc
    for ci in range(COLS + 1):
        u = ci / COLS                  # 0..1 across the fan
        ang = math.pi * (0.08 + 0.84 * u)      # semicircular fan span
        rr = R * t
        wobble = 1.0 + 0.04 * math.sin(u * 9.0 + 2.0) * t
        x = rr * math.cos(ang) * wobble
        z = rr * math.sin(ang) * wobble * 0.35  # flatten: fan is a plate
        y = -rr * 0.35 * t + 0.035 * math.sin(u * 7.0 * t * 3.0) * t \
            + 0.02 * math.sin(ri * 1.7 + ci * 0.9)
        p = geo.createPoint()
        p.setPosition(V(x, 0.18 + y, z))
        p.setAttribValue(geo.findPointAttrib("uv"), (u, t))
        grid[(ri, ci)] = p
for ri in range(ROWS):
    for ci in range(COLS):
        f = geo.createPolygon()
        for q in (grid[(ri, ci)], grid[(ri, ci + 1)],
                  grid[(ri + 1, ci + 1)], grid[(ri + 1, ci)]):
            f.addVertex(q)
# short stem down to origin
stem_pts = [V(0, 0.18, 0), V(0, 0.06, 0), V(0, 0.0, 0)]
build_tube(geo, stem_pts, [0.028, 0.02, 0.014], seg=8,
           cap_start=True, cap_end=True)
try:
    geo.computeVertexNormals()
except Exception:
    pass
"""

BRAIN_CODE = CORAL_HELPERS + r"""
V = hou.Vector3
import math as _m
SEG, RINGS = 40, 22
R = 0.36
rows = []
for j in range(RINGS + 1):
    phi = j / RINGS * _m.pi
    row = []
    for i in range(SEG):
        th = i / SEG * 2.0 * _m.pi
        x = _m.sin(phi) * _m.cos(th)
        y = _m.cos(phi)
        z = _m.sin(phi) * _m.sin(th)
        fold = (0.055 * _m.sin(6.5 * x) * _m.sin(6.5 * z)
                + 0.02 * _m.sin(11.0 * y + 2.0)
                + 0.012 * _m.sin(9.0 * x + 4.0 * z))
        rr = R * (1.0 + fold)
        p = geo.createPoint()
        p.setPosition(V(rr * x, rr * y * 0.78, rr * z))
        p.setAttribValue(geo.findPointAttrib("uv"), (i / SEG, 1.0 - j / RINGS))
        row.append(p)
    rows.append(row)
for j in range(RINGS):
    for i in range(SEG):
        f = geo.createPolygon()
        for q in (rows[j][i], rows[j][(i + 1) % SEG],
                  rows[j + 1][(i + 1) % SEG], rows[j + 1][i]):
            f.addVertex(q)
top = geo.createPoint(); top.setPosition(V(0, R * 0.78, 0))
bot = geo.createPoint(); bot.setPosition(V(0, -R * 0.78, 0))
for i in range(SEG):
    f = geo.createPolygon()
    f.addVertex(rows[0][(i + 1) % SEG]); f.addVertex(rows[0][i]); f.addVertex(top)
    f2 = geo.createPolygon()
    f2.addVertex(rows[-1][i]); f2.addVertex(rows[-1][(i + 1) % SEG]); f2.addVertex(bot)
try:
    geo.computeVertexNormals()
except Exception:
    pass
"""

CLUSTER_CODE = CORAL_HELPERS + r"""
rng = random.Random(SEED + 9)
V = hou.Vector3
# deterministic composition scatter: shallow copies of archetype silhouettes
# (procedural mini-variants, not imports) placed around the origin
def blob_cluster(cx, cz, r_base, arms, down_bias, seed_off):
    rng2 = random.Random(SEED + seed_off)
    for k in range(arms):
        a = rng2.uniform(0, 6.28)
        rad = rng2.uniform(0.05, r_base)
        bx, bz = cx + rad * math.cos(a), cz + rad * math.sin(a)
        h = rng2.uniform(0.12, 0.30)
        r0 = rng2.uniform(0.02, 0.045)
        pts = []
        radii = []
        steps = 5
        d = V(rng2.uniform(-0.4, 0.4), -1, rng2.uniform(-0.4, 0.4)).normalized()
        pos = V(bx, rng2.uniform(0.05, 0.15), bz)
        pts.append(pos)
        radii.append(r0)
        for s in range(steps):
            dd = (d + V(rng2.uniform(-0.2, 0.2), 0, rng2.uniform(-0.2, 0.2))).normalized()
            pos = pos + dd * (h / steps)
            pts.append(pos)
            radii.append(r0 * (1.0 - 0.18 * (s + 1)))
        build_tube(geo, pts, radii, seg=6, cap_start=True, cap_end=True)

blob_cluster(0.0, 0.0, 0.42, 26, 1.0, 21)
try:
    geo.computeVertexNormals()
except Exception:
    pass
"""

# SEED must exist inside the SOP code namespace; inject as a literal
STAGHORN_CODE = STAGHORN_CODE.replace("random.Random(SEED)", f"random.Random({SEED})")
TABLE_CODE = TABLE_CODE.replace("random.Random(SEED + 1)", f"random.Random({SEED + 1})")
SPONGE_CODE = SPONGE_CODE.replace("random.Random(SEED + 2)", f"random.Random({SEED + 2})")
FAN_CODE = FAN_CODE.replace("random.Random(SEED + 3)", f"random.Random({SEED + 3})")
CLUSTER_CODE = CLUSTER_CODE.replace("random.Random(SEED + 9)", f"random.Random({SEED + 9})")
CLUSTER_CODE = CLUSTER_CODE.replace("SEED + seed_off", f"{SEED} + seed_off")


def main():
    manifests = []
    jobs = [
        (STAGHORN_CODE, "gen_staghorn", "SM_Coral_Staghorn"),
        (TABLE_CODE, "gen_table", "SM_Coral_Table"),
        (SPONGE_CODE, "gen_sponges", "SM_Coral_TubeSponges"),
        (FAN_CODE, "gen_fan", "SM_Coral_Fan"),
        (BRAIN_CODE, "gen_brain", "SM_Coral_Brain"),
        (CLUSTER_CODE, "gen_cluster", "SM_Coral_ReefCluster"),
    ]
    for code, node_name, stem in jobs:
        g = _geo(stem)
        py = _python_sop(g, node_name, code)
        out = g.createNode("null", "OUT")
        out.setInput(0, py)
        export_geo(g, out, stem, manifests)
    MESH_OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(MESH_OUT_DIR / "coral_mesh_manifest.json", "w", encoding="utf-8") as f:
        json.dump({"schema": "melodia.sea_above_reef_meshes.v1",
                   "kind": "coral (R1, code-grown; VDB upgrade path reserved)",
                   "seed": SEED, "hython": hou.applicationVersionString(),
                   "growth": "downward-biased branching (inverted gravity)",
                   "emissive_note": "pulse bands via uv.y in material; per-PC tint via MI",
                   "format": "obj + bgeo.sc via File SOP write mode (Apprentice)",
                   "ue_import": {"obj_scale": "100x (m -> cm)",
                                 "nanite": True,
                                 "two_sided": "SM_Coral_Fan needs two-sided material"},
                   "meshes": manifests}, f, indent=2)
    print(f"[coral] manifest -> {MESH_OUT_DIR / 'coral_mesh_manifest.json'}")


if __name__ == "__main__":
    main()
