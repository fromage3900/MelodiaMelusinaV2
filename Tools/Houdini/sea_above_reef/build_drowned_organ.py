"""THE DROWNED ORGAN — cathedral pipe organ, 12 pitch-class ranks (owner #2).

24 pipes in an arc (two per pitch class, PC00 deepest/longest -> PC11 shortest),
uv.x mapped so each pipe occupies its own 1/12 band -> the material tints each
rank from `T_SeaAbove_PulseBand_LUT` (the reef's shared chromatic system) and
the mouth emissive follows `User.SeaAbovePulse` (one-writer rule). Console +
arch frame complete the cathedral read.

Scale: metres (UE import x100). Pipes 3.5-12.5 m tall.
Outputs: Saved/Audit/sea_above/meshes/SM_DrownedOrgan.obj/.bgeo.sc + manifest.
Run:  hython Tools/Houdini/sea_above_reef/build_drowned_organ.py
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
)

SEED = SUITE_SEED

CODE = r"""
import hou, math, random

node = hou.pwd()
geo = node.geometry()
if geo.findPointAttrib("uv") is None:
    geo.addAttrib(hou.attribType.Point, "uv", (0.0, 0.0))

V = hou.Vector3

def _frame(tan):
    tan = tan.normalized()
    up = V(0, 1, 0)
    if abs(tan.dot(up)) > 0.95:
        up = V(1, 0, 0)
    x = tan.cross(up).normalized()
    y = tan.cross(x).normalized()
    return x, y, tan

def tube(pts, radii, seg=10, u0=0.0, u1=1.0, cap_start=True, cap_end=False, flare=1.0):
    n = len(pts)
    rings = []
    for i, pos in enumerate(pts):
        if i == 0:
            tan = pts[1] - pts[0]
        elif i == n - 1:
            tan = pts[-1] - pts[-2]
        else:
            tan = pts[i + 1] - pts[i - 1]
        x, y, _t = _frame(tan)
        t = i / (n - 1.0)
        r = radii[i] * (flare ** t)
        ring = []
        for k in range(seg):
            a = k / seg * 2.0 * math.pi
            off = x * (math.cos(a) * r) + y * (math.sin(a) * r)
            p = geo.createPoint()
            p.setPosition(pos + off)
            p.setAttribValue(geo.findPointAttrib("uv"),
                             (u0 + (u1 - u0) * k / seg, t))
            ring.append(p)
        rings.append(ring)
    for i in range(n - 1):
        for k in range(seg):
            f = geo.createPolygon()
            for q in (rings[i][k], rings[i][(k + 1) % seg],
                      rings[i + 1][(k + 1) % seg], rings[i + 1][k]):
                f.addVertex(q)
    if cap_start:
        c = geo.createPoint(); c.setPosition(pts[0])
        for k in range(seg):
            f = geo.createPolygon()
            f.addVertex(rings[0][(k + 1) % seg]); f.addVertex(rings[0][k]); f.addVertex(c)
    if cap_end:
        c = geo.createPoint(); c.setPosition(pts[-1])
        for k in range(seg):
            f = geo.createPolygon()
            f.addVertex(rings[-1][k]); f.addVertex(rings[-1][(k + 1) % seg]); f.addVertex(c)

# --- 24 pipes: 2 per PC, arc layout, tallest at centre -----------------------
N_PC = 12
u_per_pc = 1.0 / N_PC
for pc in range(N_PC):
    # pitch: PC00 = deepest = tallest
    h = 12.5 - 9.0 * (pc / (N_PC - 1.0)) ** 1.15
    r = 0.62 - 0.24 * (pc / (N_PC - 1.0))
    for dup in (0, 1):
        slot = pc * 2 + dup
        fx = -15.0 + 30.0 * (slot / 23.0)
        arc = math.sin(slot / 23.0 * math.pi) * 1.6          # facade arc
        base = V(fx, arc, 0.0)
        lean = (slot - 11.5) / 11.5 * 0.05
        pts = []
        steps = 10
        for i in range(steps + 1):
            t = i / steps
            pts.append(base + V(lean * t * h, h * t, 0.0))
        radii = [r * (1.0 - 0.10 * t) for t in (i / steps for i in range(steps + 1))]
        u0 = pc * u_per_pc + dup * (u_per_pc / 2.0)
        u1 = u0 + u_per_pc / 2.0
        # cap_start closes the foot; the mouth (top) stays OPEN with a flare
        tube(pts, radii, seg=12, u0=u0, u1=u1, cap_start=True, cap_end=False,
             flare=1.14)
        # mouth lip ring (the glowing slit) just below the open top
        lip = []
        for i in range(3):
            t = 0.94 + 0.03 * i
            lip.append(base + V(lean * t * h, h * t, 0.0))
        tube(lip, [r * 1.16, r * 1.18, r * 1.16], seg=12,
             u0=u0 + u_per_pc * 0.25, u1=u0 + u_per_pc * 0.75,
             cap_start=False, cap_end=False)

# --- console (keydesk block) --------------------------------------------------
def box(center, size, rot=0.0):
    cx, cy, cz = center
    sx, sy, sz = size
    cr, sr = math.cos(rot), math.sin(rot)
    corners = []
    for dy in (-1.0, 1.0):
        for dz in (-1.0, 1.0):
            for dx in (-1.0, 1.0):
                x0, z0 = dx * sx / 2.0, dz * sz / 2.0
                pos = V(cx + x0 * cr - z0 * sr,
                        cy + dy * sy / 2.0,
                        cz + x0 * sr + z0 * cr)
                p = geo.createPoint()
                p.setPosition(pos)
                corners.append(p)          # addVertex needs hou.Point, not Vector
    order = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 2, 6, 4),
             (1, 5, 7, 3), (0, 4, 5, 1), (2, 3, 7, 6)]
    for face in order:
        f = geo.createPolygon()
        for idx in face:
            f.addVertex(corners[idx])

box(V(0, 0.8, 5.2), (7.0, 1.6, 2.6))
box(V(0, 1.9, 6.1), (6.4, 0.6, 1.2))          # keydesk slab

# --- arch frame over the pipes ------------------------------------------------
def arc_tube(cx, cy, cz, R, thickness, a0, a1, seg=16, r=0.30):
    pts = []
    for i in range(seg + 1):
        a = a0 + (a1 - a0) * i / seg
        pts.append(V(cx + R * math.cos(a), cy + R * math.sin(a), cz))
    radii = [r * (1.0 - 0.2 * i / seg) for i in range(seg + 1)]
    tube(pts, radii, seg=8, cap_start=True, cap_end=True)

arc_tube(0.0, 0.4, -1.6, 17.0, 0.5, math.pi * 0.10, math.pi * 0.90, seg=20, r=0.42)
arc_tube(0.0, 0.4, 1.6, 17.0, 0.5, math.pi * 0.10, math.pi * 0.90, seg=20, r=0.42)
tube([V(-16.6, 0.0, -1.6), V(-16.6, 0.0, 1.6)], [0.42, 0.42], seg=8)
tube([V(16.6, 0.0, -1.6), V(16.6, 0.0, 1.6)], [0.42, 0.42], seg=8)

try:
    geo.computeVertexNormals()
except Exception:
    pass
"""


def main():
    manifests = []
    g = _geo("SM_DrownedOrgan")
    py = _python_sop(g, "gen_organ", CODE)
    out = g.createNode("null", "OUT")
    out.setInput(0, py)
    export_geo(g, out, "SM_DrownedOrgan", manifests)
    MESH_OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(MESH_OUT_DIR / "organ_manifest.json", "w", encoding="utf-8") as f:
        json.dump({"schema": "melodia.sea_above_reef_meshes.v1",
                   "kind": "drowned organ (static; Nanite-able; no skinning)",
                   "seed": SEED, "hython": hou.applicationVersionString(),
                   "design": "24 pipes in 12 pitch-class ranks (uv.x = PC band -> "
                             "tint via T_SeaAbove_PulseBand_LUT); mouth rings emissive "
                             "x User.SeaAbovePulse (one-writer); console + arch",
                   "ue_import": {"obj_scale": "100x (m -> cm)", "nanite": True},
                   "meshes": manifests}, f, indent=2)
    print(f"[organ] manifest -> {MESH_OUT_DIR / 'organ_manifest.json'}")


if __name__ == "__main__":
    main()
