"""Dream flora — code-L-system growth (deterministic rewriting + turtle walk).

Three archetypes on one grammar engine (no L-System SOP parm roulette; the
rewriting IS the L-system):
  SM_Flora_GlassReed      tall reed, sparse side shoots, glass-clear tip bulb
  SM_Flora_ChimeBlossom   curved stem ending in a small bell (the Bell motif)
  SM_Flora_SpiralFern     log-spiral pinnae along a rising spine

Scale: metres (UE x100). Outputs: SM_Flora_*.obj/.bgeo.sc + manifest.
Run:  hython Tools/Houdini/sea_above_reef/build_dream_flora.py
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

FLORA_CODE = r"""
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

def _rot(v, axis, ang):
    c = math.cos(ang); s = math.sin(ang)
    a = axis.normalized()
    return v * c + a.cross(v) * s + a * (a.dot(v) * (1.0 - c))

def tube_along(pts, radii, seg=7):
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
    c = geo.createPoint(); c.setPosition(pts[-1])
    for k in range(seg):
        f = geo.createPolygon()
        f.addVertex(rings[-1][k]); f.addVertex(rings[-1][(k + 1) % seg]); f.addVertex(c)

def torus(center, normal, R, r, M=14, N=8):
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
            row.append(p)
        grid.append(row)
    for mi in range(M):
        mj = (mi + 1) % M
        for ni in range(N):
            nj = (ni + 1) % N
            f = geo.createPolygon()
            for q in (grid[mi][ni], grid[mj][ni], grid[mj][nj], grid[mi][nj]):
                f.addVertex(q)

def sphere(center, R, seg=18, rings=10, squash=(1.0, 1.0, 1.0)):
    rows = []
    for j in range(rings + 1):
        phi = j / rings * math.pi
        row = []
        for i in range(seg):
            th = i / seg * 2.0 * math.pi
            x = math.sin(phi) * math.cos(th)
            y = math.cos(phi)
            z = math.sin(phi) * math.sin(th)
            p = geo.createPoint()
            p.setPosition(center + V(R * squash[0] * x, R * squash[1] * y,
                                     R * squash[2] * z))
            row.append(p)
        rows.append(row)
    for j in range(rings):
        for i in range(seg):
            f = geo.createPolygon()
            for q in (rows[j][i], rows[j][(i + 1) % seg],
                      rows[j + 1][(i + 1) % seg], rows[j + 1][i]):
                f.addVertex(q)

ARCH = __ARCH__
rng = random.Random(SEED + hash(ARCH) % 997)

def lsystem_expand(premise, rules, depth):
    s = premise
    for _ in range(depth):
        s = "".join(rules.get(ch, ch) for ch in s)
    return s

def turtle(s, angle_deg, step, r0, r_decay):
    # F=draw, +=yaw left, -=yaw right, &=pitch down, ^=pitch up
    ang = math.radians(angle_deg)
    pos = V(0, 0, 0)
    d = V(0, 1, 0)
    segments = []
    stack = []
    for ch in s:
        if ch == "F":
            nxt = pos + d * step
            segments.append((pos, nxt))
            pos = nxt
            d = _rot(d, V(1, 0, 0), rng.uniform(-0.08, 0.08))  # organic jitter
        elif ch == "+":
            d = _rot(d, V(0, 0, 1), ang)
        elif ch == "-":
            d = _rot(d, V(0, 0, 1), -ang)
        elif ch == "^":
            d = _rot(d, V(1, 0, 0), -ang)
        elif ch == "&":
            d = _rot(d, V(1, 0, 0), ang)
        elif ch == "[":
            stack.append((pos, V(d.x(), d.y(), d.z())))
        elif ch == "]":
            pos, d = stack.pop()
    return segments

def draw(segments, r0, r_decay, bulb_at_end=False):
    for si, (a, b) in enumerate(segments):
        depth_frac = si / max(len(segments) - 1, 1)
        r = r0 * (r_decay ** si)
        steps = 4
        pts = [a + (b - a) * (i / steps) for i in range(steps + 1)]
        radii = [r * (1.0 - 0.5 * (i / steps)) for i in range(steps + 1)]
        tube_along(pts, radii, seg=6)

if ARCH == "reed":
    s = lsystem_expand("FFFA[+F][-F]FFA[-F][+F]F", {"A": "F[+F]FA", "F": "FF"}, 4)
    draw(turtle(s, 28, 0.55, 0.14, 0.9), 0.14, 0.9)
    sphere(V(0, 3.4, 0), 0.34, squash=(1.0, 1.5, 1.0))     # glass tip bulb

elif ARCH == "chime":
    s = lsystem_expand("FF[-FA][+FA]FFA", {"A": "F[&F][+F]FA"}, 4)
    segs = turtle(s, 32, 0.42, 0.12, 0.92)
    draw(segs, 0.12, 0.92)
    # chime bells at the last few segment ends (the Bell motif)
    for (a, b) in segs[-4:]:
        torus(b, V(0, 1, 0), 0.30, 0.08, M=12, N=7)
        sphere(b + V(0, -0.16, 0), 0.10)

elif ARCH == "fern":
    s = lsystem_expand("FFA[&F][&F]A[&F][&F]A[&F]F", {"A": "FFA[&F]"}, 3)
    segs = turtle(s, 38, 0.5, 0.10, 0.9)
    draw(segs, 0.10, 0.9)
    # pinnae: small side fronds on every segment midpoint
    for si, (a, b) in enumerate(segs):
        if si % 2 == 0:
            mid = (a + b) / 2.0
            frond = [mid, mid + V(0.9 * (1 if si % 4 else -1), 0.4, 0.15),
                     mid + V(1.5 * (1 if si % 4 else -1), 0.5, -0.1)]
            tube_along(frond, [0.05 * (1.0 - 0.1 * si / max(len(segs), 1) * 2)
                               for _ in frond], seg=5)

try:
    geo.computeVertexNormals()
except Exception:
    pass
"""


def main():
    manifests = []
    for arch in ("reed", "chime", "fern"):
        code = (FLORA_CODE.replace("__ARCH__", repr(arch))
                          .replace("random.Random(SEED + hash(ARCH) % 997)",
                                   f"random.Random({SEED} + hash('{arch}') % 997)"))
        g = _geo(f"SM_Flora_{arch.capitalize()}")
        py = _python_sop(g, f"gen_{arch}", code)
        try:
            py.cook(force=True)
        except Exception:
            pass
        err = " ".join(str(py.errors()).split()) if py.errors() else ""
        if err:
            print(f"[flora] NODE ERROR [{arch}]: {err[:300]}")
            g.destroy()
            continue
        out = g.createNode("null", "OUT")
        out.setInput(0, py)
        export_geo(g, out, f"SM_Flora_{arch.capitalize()}", manifests)
    with open(MESH_OUT_DIR / "flora_manifest.json", "w", encoding="utf-8") as f:
        json.dump({"schema": "melodia.sea_above_reef_meshes.v1",
                   "kind": "dream flora (code-L-system: rewriting + turtle walk)",
                   "seed": SEED, "hython": hou.applicationVersionString(),
                   "grammars": {"reed": "FFFA[+F][-F]FFA[-F][+F]F / A:F[+F]FA, F:FF",
                                "chime": "FF[-FA][+FA]FFA / A:F[&F][+F]FA (bell tips)",
                                "fern": "FFA[&F][&F]A[&F][&F]A[&F]F / A:FFA[&F] (spiral pinnae)"},
                   "ue_import": {"obj_scale": "100x (m -> cm)", "nanite": True,
                                 "scatter": "PCG-ready; tips take CoralSkin/Iridescence"},
                   "meshes": manifests}, f, indent=2)
    print(f"[flora] manifest -> {MESH_OUT_DIR / 'flora_manifest.json'}")


if __name__ == "__main__":
    main()
