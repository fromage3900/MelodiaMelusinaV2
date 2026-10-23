"""THE LEVIATHAN — colossal sunken sea-bone ribcage (owner 'something cool' #1).

A dead leviathan resting on the abyss floor, fossilized mid-ascent: the spine
arches and the tail LIFTS toward the sea above — it died swimming upward.
Scale: metres (UE import x100). Spine run ~140 m, ribs to ~34 m, skull ~14 m.

Parts (all code-grown tubes/rings, single mesh):
  22 vertebrae      torus rings, tapering head->tail, neural spines up,
                    last 4 tilted upward (the rising tail)
  11 rib pairs      arcs from the spine, curving down then inward at the tips
  stylized skull    cranium dome + jaw arc + two eye rings (silhouette-led)

Outputs: Saved/Audit/sea_above/meshes/SM_Leviathan.obj/.bgeo.sc + manifest.
Run:  hython Tools/Houdini/sea_above_reef/build_leviathan.py
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
if geo.findPointAttrib("Cd") is None:
    geo.addAttrib(hou.attribType.Point, "Cd", (1.0, 1.0, 1.0))

V = hou.Vector3

def _frame(tan):
    tan = tan.normalized()
    up = V(0, 1, 0)
    if abs(tan.dot(up)) > 0.95:
        up = V(1, 0, 0)
    x = tan.cross(up).normalized()
    y = tan.cross(x).normalized()
    return x, y, tan

def tube_along(pts, radii, seg=8, cap_start=True, cap_end=True):
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
        ring = []
        for k in range(seg):
            a = k / seg * 2.0 * math.pi
            off = x * (math.cos(a) * radii[i]) + y * (math.sin(a) * radii[i])
            p = geo.createPoint()
            p.setPosition(pos + off)
            p.setAttribValue(geo.findPointAttrib("uv"), (k / seg, i / max(n - 1, 1)))
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

def torus(center, normal, R, r, M=18, N=9):
    x, y, n = _frame(normal)
    grid = []
    for mi in range(M):
        ca = mi / M * 2.0 * math.pi
        rc = center + (x * math.cos(ca) + y * math.sin(ca)) * R
        row = []
        for ni in range(N):
            na = ni / N * 2.0 * math.pi
            p = geo.createPoint()
            p.setPosition(rc + (x * math.cos(ca) + y * math.sin(ca)) * (r * math.cos(na))
                          + n * (r * math.sin(na)))
            p.setAttribValue(geo.findPointAttrib("uv"), (mi / M, ni / N))
            row.append(p)
        grid.append(row)
    for mi in range(M):
        mj = (mi + 1) % M
        for ni in range(N):
            nj = (ni + 1) % N
            f = geo.createPolygon()
            for q in (grid[mi][ni], grid[mj][ni], grid[mj][nj], grid[mi][nj]):
                f.addVertex(q)

# --- spine curve: head (-58, 8) to tail (+82, rising to ~26) -----------------
def spine_point(s):
    x = -58.0 + s * 140.0
    sag = -6.0 * math.sin(math.pi * s)
    rise = 30.0 * max(0.0, s - 0.80) ** 1.7          # the tail lifts
    return V(x, 6.0 + sag + rise, 0.0)

def spine_tan(s):
    e = 0.002
    return spine_point(min(1.0, s + e)) - spine_point(max(0.0, s - e))

# --- vertebrae ---------------------------------------------------------------
N_V = 22
for vi in range(N_V):
    s = 0.04 + vi / (N_V - 1.0) * 0.92
    c = spine_point(s)
    tan = spine_tan(s).normalized()
    x, y, t = _frame(tan)
    R = 2.6 * (1.0 - 0.55 * s)                       # taper head -> tail
    tilt = 0.35 * max(0.0, s - 0.80) * 8.0           # tail vertebrae tilt upward
    nrm = _rot(t, x, tilt) if tilt > 0.001 else t
    torus(c, nrm, R, R * 0.30, M=18, N=9)
    # neural spine: upward spike
    spike_top = c + V(0, 1, 0) * (R * 1.1 + 1.4) + tan * 0.3
    tube_along([c + V(0, R * 0.4, 0), (c + spike_top) / 2.0, spike_top],
               [R * 0.16, R * 0.11, R * 0.04], seg=6, cap_start=False, cap_end=True)

# --- ribs: 11 pairs ----------------------------------------------------------
for pair in range(11):
    s = 0.14 + pair / 10.0 * 0.56
    c = spine_point(s)
    tan = spine_tan(s).normalized()
    x, y, _t = _frame(tan)
    rib_len = 30.0 * math.sin(math.pi * (0.25 + 0.55 * pair / 10.0)) + 6.0
    r0 = 0.62 * (1.0 - 0.4 * pair / 10.0)
    for side in (-1.0, 1.0):
        d0 = (side * x + y * 0.25).normalized()
        pts = []
        for i in range(9):
            t = i / 8.0
            pos = c + d0 * (rib_len * t * 0.85) + V(0, -26.0 * t * t, 0) \
                  + (x * side) * (-14.0 * t ** 2.5)
            pts.append(pos)
        radii = [r0 * (1.0 - 0.75 * (i / 8.0)) for i in range(9)]
        tube_along(pts, radii, seg=7, cap_start=True, cap_end=True)
        # iridescent scale shingles on the OUTER face (alternating overlap)
        cd_attrib = geo.findPointAttrib("Cd")
        for i in range(2, 8):
            t = i / 8.0
            hue = (pair / 11.0 + t * 0.5) % 1.0
            for (tt, sz) in ((t, 0.55), (t + 0.06, 0.42)):
                ii = min(int(tt * 8.0), 8)
                frac = tt * 8.0 - ii
                a2 = pts[ii]
                b2 = pts[min(ii + 1, 8)]
                pos = a2 + (b2 - a2) * frac + (x * side) * (radii[ii] * 0.5)
                normal = ((x * side) * 0.7 + (b2 - a2).normalized() * 0.3).normalized()
                cdx = 0.5 + 0.5 * math.sin(hue * 2.0 * math.pi)
                cdy = 0.5 + 0.5 * math.sin(hue * 2.0 * math.pi + 2.1)
                cdz = 0.5 + 0.5 * math.sin(hue * 2.0 * math.pi + 4.2)
                x1, y1, _n1 = _frame(normal)
                cpt = geo.createPoint()
                cpt.setPosition(pos + normal * (sz * 0.12))
                cpt.setAttribValue(cd_attrib, (cdx, cdy, cdz))
                rim2 = []
                for k in range(6):
                    aa = k / 6.0 * 2.0 * math.pi
                    p2 = geo.createPoint()
                    p2.setPosition(pos + x1 * (math.cos(aa) * sz)
                                   + y1 * (math.sin(aa) * sz))
                    p2.setAttribValue(cd_attrib, (cdx, cdy, cdz))
                    rim2.append(p2)
                for k in range(6):
                    f2 = geo.createPolygon()
                    f2.addVertex(cpt)
                    f2.addVertex(rim2[k])
                    f2.addVertex(rim2[(k + 1) % 6])

# --- stylized skull ----------------------------------------------------------
sk = spine_point(0.0) + V(-9.0, 3.5, 0.0)
SEG, RINGS = 40, 24
rows = []
for j in range(RINGS + 1):
    phi = j / RINGS * math.pi
    row = []
    for i in range(SEG):
        th = i / SEG * 2.0 * math.pi
        x0 = math.sin(phi) * math.cos(th)
        y0 = math.cos(phi)
        z0 = math.sin(phi) * math.sin(th)
        rr = 7.0 * (1.0 + 0.03 * math.sin(6.0 * th + 1.0))
        p = geo.createPoint()
        p.setPosition(sk + V(rr * x0 * 1.18, rr * y0 * 0.92, rr * z0 * 1.02))
        p.setAttribValue(geo.findPointAttrib("uv"), (i / SEG, 1.0 - j / RINGS))
        row.append(p)
    rows.append(row)
for j in range(RINGS):
    for i in range(SEG):
        f = geo.createPolygon()
        for q in (rows[j][i], rows[j][(i + 1) % SEG],
                  rows[j + 1][(i + 1) % SEG], rows[j + 1][i]):
            f.addVertex(q)
# eye rings + jaw arc
for ez in (-2.6, 2.6):
    torus(sk + V(-4.6, 1.2, ez), V(-1, 0, 0), 1.5, 0.38, M=14, N=7)
jaw = []
for i in range(9):
    t = i / 8.0
    jaw.append(sk + V(-7.0 + 3.0 * t, -5.2 + 1.4 * math.sin(math.pi * t),
                      -6.0 + 12.0 * t))
tube_along(jaw, [1.1 * (1.0 - 0.1 * i / 8.0) for i in range(9)], seg=8,
           cap_start=True, cap_end=True)

try:
    geo.computeVertexNormals()
except Exception:
    pass
"""

# Rodrigues helper is referenced by the vertebra tilt; inject it
CODE = CODE.replace(
    "def _frame(tan):",
    """def _rot(v, axis, ang):
    c = math.cos(ang); s = math.sin(ang)
    a = axis.normalized()
    return v * c + a.cross(v) * s + a * (a.dot(v) * (1.0 - c))

def _frame(tan):""", 1)
CODE = CODE.replace("random.Random(SEED", f"random.Random({SEED}")  # no-op safety
CODE = CODE.replace("rng = random.Random(", "rng = random.Random(")


def main():
    manifests = []
    g = _geo("SM_Leviathan")
    py = _python_sop(g, "gen_leviathan", CODE)
    out = g.createNode("null", "OUT")
    out.setInput(0, py)
    export_geo(g, out, "SM_Leviathan", manifests)
    MESH_OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(MESH_OUT_DIR / "leviathan_manifest.json", "w", encoding="utf-8") as f:
        json.dump({"schema": "melodia.sea_above_reef_meshes.v1",
                   "kind": "leviathan ribcage (static; Nanite-able; no skinning)",
                   "seed": SEED, "hython": hou.applicationVersionString(),
                   "design": "died swimming upward: spine run 140 m, tail rises 30 m, "
                             "11 rib pairs to ~34 m, stylized skull with eye rings",
                   "ue_import": {"obj_scale": "100x (m -> cm)", "nanite": True},
                   "meshes": manifests}, f, indent=2)
    print(f"[leviathan] manifest -> {MESH_OUT_DIR / 'leviathan_manifest.json'}")


if __name__ == "__main__":
    main()
