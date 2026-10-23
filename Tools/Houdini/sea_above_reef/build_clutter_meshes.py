"""Houdini headless builder: underwater clutter MESHES (Sea Above reef lane).

Verified pipeline facts (2026-08-28):
- hython 22.0.368 runs headless; Engine license NOT required for SOP baking.
- FBX export is NOT available in Apprentice ("FBX export is not supported") ->
  exports are **Alembic (.abc)**, the same format the Choral Sheep groom lane
  already uses and ingests (ingest_grooms.py validates Ogawa magic).
- Geometry is built inside **Python SOPs** (stable hou.Geometry API) instead of
  hand-setting version-fragile SOP parm names. Only the Alembic ROP is touched
  by name.

  hython Tools/Houdini/sea_above_reef/build_clutter_meshes.py

Outputs Saved/Audit/sea_above/meshes/:
  SM_Clutter_PebbleSet.abc   ~14 jittered, squashed UV spheres (deterministic)
  SM_Clutter_Starfish.abc    star profile -> polyextrude -> smooth
  SM_Clutter_SpiralShell.abc log-spiral polyline swept by a circle
  SM_Clutter_SeaWeed.abc     sway-curved polyline swept by a small circle
  clutter_mesh_manifest.json

UE import: Alembic -> import as static mesh (Interchange), Nanite on, assign
MI_SeaAbove_* materials. Scale note: meshes are in metres (Houdini default) ->
set UE import uniform scale to 100 (cm) or author at cm scale on import.
"""

import json
import math
from pathlib import Path

import hou

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "Saved" / "Audit" / "sea_above" / "meshes"
SEED = 20260828

# ---------------------------------------------------------------------------
# Python-SOP code blocks (stable hou.Geometry API; version-proof)
# ---------------------------------------------------------------------------

SPHERE_HELPERS = r"""
import hou, math

node = hou.pwd()
geo = node.geometry()  # H22 Python SOP does not prebind geo (verified)

if geo.findPointAttrib("uv") is None:
    geo.addAttrib(hou.attribType.Point, "uv", (0.0, 0.0))

def _uv_sphere(geo, cx, cy, cz, rx, ry, rz, seg=18, rings=10):
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
            p.setPosition(hou.Vector3(cx + rx * x, cy + ry * y, cz + rz * z))
            p.setAttribValue(geo.findPointAttrib("uv"), (th / (2.0 * math.pi), 1.0 - phi / math.pi))
            row.append(p)
        rows.append(row)
    faces = []
    for j in range(rings):
        for i in range(seg):
            a = rows[j][i]
            b = rows[j][(i + 1) % seg]
            c = rows[j + 1][(i + 1) % seg]
            d = rows[j + 1][i]
            f = geo.createPolygon()
            for q in (a, b, c, d):
                f.addVertex(q)
            faces.append(f)
    # pole caps
    top = geo.createPoint()
    top.setPosition(hou.Vector3(cx, cy + ry, cz))
    bot = geo.createPoint()
    bot.setPosition(hou.Vector3(cx, cy - ry, cz))
    top.setAttribValue(geo.findPointAttrib("uv"), (0.5, 1.0))
    bot.setAttribValue(geo.findPointAttrib("uv"), (0.5, 0.0))
    for i in range(seg):
        f = geo.createPolygon()
        f.addVertex(rows[0][(i + 1) % seg]); f.addVertex(rows[0][i]); f.addVertex(top)
        f2 = geo.createPolygon()
        f2.addVertex(rows[-1][i]); f2.addVertex(rows[-1][(i + 1) % seg]); f2.addVertex(bot)
    try:
        geo.computeVertexNormals()
    except Exception:
        pass
"""

PEBBLES_CODE = SPHERE_HELPERS + r"""
import random
rng = random.Random(20260828)
count = 14
placed = []
for k in range(count):
    for attempt in range(24):
        cx = rng.uniform(-1.05, 1.05)
        cz = rng.uniform(-1.05, 1.05)
        r = rng.uniform(0.09, 0.20)
        ok = True
        for (px, pz, pr) in placed:
            if (cx - px) ** 2 + (cz - pz) ** 2 < (r + pr) ** 2 * 0.9:
                ok = False
                break
        if ok:
            break
    placed.append((cx, cz, r))
    _uv_sphere(geo, cx, r * rng.uniform(0.45, 0.62), cz,
               r, r * rng.uniform(0.42, 0.60), r * rng.uniform(0.8, 1.1))
"""

STAR_CODE = SPHERE_HELPERS + r"""
# starfish: closed star polygon with planar UVs, puffed by polyextrude downstream
arms = 5
poly = geo.createPolygon()  # closed
for i in range(arms * 2 + 1):
    a = i * math.pi / arms - math.pi / 2
    r = 0.5 if i % 2 == 0 else 0.18
    p = geo.createPoint()
    p.setPosition(hou.Vector3(r * math.cos(a), 0.0, r * math.sin(a)))
    p.setAttribValue(geo.findPointAttrib("uv"), (0.5 + 0.5 * r * math.cos(a) / 0.5,
                                                 0.5 + 0.5 * r * math.sin(a) / 0.5))
    poly.addVertex(p)
"""

SPIRAL_CODE = r"""
import math
node = hou.pwd()
geo = node.geometry()
if geo.findPointAttrib("uv") is None:
    geo.addAttrib(hou.attribType.Point, "uv", (0.0, 0.0))

# logarithmic-spiral spine points
b = 0.22
pts = []
for i in range(60):
    t = i / 59.0 * 4.0 * math.pi
    r = 0.05 + 0.5 * math.exp(b * t) / math.exp(b * 4.0 * math.pi)
    pts.append(hou.Vector3(r * math.cos(t), 0.02 * t, r * math.sin(t)))

# tube in code (Sweep SOP produced 0 prims headless - replaced by explicit rings)
R0, TAPER, SEG = 0.09, 0.55, 10
n = len(pts)
rings = []
for i, pos in enumerate(pts):
    if i == 0:
        tan = pts[1] - pts[0]
    elif i == n - 1:
        tan = pts[-1] - pts[-2]
    else:
        tan = pts[i + 1] - pts[i - 1]
    tan = tan.normalized()
    up = hou.Vector3(0, 1, 0)
    if abs(tan.dot(up)) > 0.95:
        up = hou.Vector3(1, 0, 0)
    x = tan.cross(up).normalized()
    y = tan.cross(x).normalized()
    radius = R0 * (1.0 - TAPER * i / (n - 1))
    ring = []
    for k in range(SEG):
        a = k / SEG * 2.0 * math.pi
        off = x * (math.cos(a) * radius) + y * (math.sin(a) * radius)
        p = geo.createPoint()
        p.setPosition(pos + off)
        p.setAttribValue(geo.findPointAttrib("uv"), (k / SEG, i / (n - 1)))
        ring.append(p)
    rings.append(ring)
for i in range(n - 1):
    for k in range(SEG):
        f = geo.createPolygon()
        for q in (rings[i][k], rings[i][(k + 1) % SEG], rings[i + 1][(k + 1) % SEG], rings[i + 1][k]):
            f.addVertex(q)
for ring, ci in ((rings[0], 0), (rings[-1], n - 1)):
    cap = geo.createPoint()
    cap.setPosition(pts[ci])
    for k in range(SEG):
        f = geo.createPolygon()
        f.addVertex(ring[k]); f.addVertex(ring[(k + 1) % SEG]); f.addVertex(cap)
try:
    geo.computeVertexNormals()
except Exception:
    pass
"""

SEAWEED_CODE = r"""
import math
node = hou.pwd()
geo = node.geometry()
if geo.findPointAttrib("uv") is None:
    geo.addAttrib(hou.attribType.Point, "uv", (0.0, 0.0))

# sway-curved stalk points
pts = []
n_pts, height = 24, 1.6
for i in range(n_pts):
    t = i / (n_pts - 1.0)
    y = height * t
    x = 0.26 * math.sin(y * 3.1 + 0.7) * t
    z = 0.12 * math.sin(y * 2.3 + 1.9) * t
    pts.append(hou.Vector3(x, y, z))

# tapered tube in code
R0, TAPER, SEG = 0.045, 0.75, 8
n = len(pts)
rings = []
for i, pos in enumerate(pts):
    if i == 0:
        tan = pts[1] - pts[0]
    elif i == n - 1:
        tan = pts[-1] - pts[-2]
    else:
        tan = pts[i + 1] - pts[i - 1]
    tan = tan.normalized()
    up = hou.Vector3(0, 1, 0)
    if abs(tan.dot(up)) > 0.95:
        up = hou.Vector3(1, 0, 0)
    x = tan.cross(up).normalized()
    y = tan.cross(x).normalized()
    radius = R0 * (1.0 - TAPER * i / (n - 1))
    ring = []
    for k in range(SEG):
        a = k / SEG * 2.0 * math.pi
        off = x * (math.cos(a) * radius) + y * (math.sin(a) * radius)
        p = geo.createPoint()
        p.setPosition(pos + off)
        p.setAttribValue(geo.findPointAttrib("uv"), (k / SEG, i / (n - 1)))
        ring.append(p)
    rings.append(ring)
for i in range(n - 1):
    for k in range(SEG):
        f = geo.createPolygon()
        for q in (rings[i][k], rings[i][(k + 1) % SEG], rings[i + 1][(k + 1) % SEG], rings[i + 1][k]):
            f.addVertex(q)
top = geo.createPoint()
top.setPosition(pts[-1])
for k in range(SEG):
    f = geo.createPolygon()
    f.addVertex(rings[-1][k]); f.addVertex(rings[-1][(k + 1) % SEG]); f.addVertex(top)
base = geo.createPoint()
base.setPosition(pts[0])
for k in range(SEG):
    f = geo.createPolygon()
    f.addVertex(rings[0][(k + 1) % SEG]); f.addVertex(rings[0][k]); f.addVertex(base)
try:
    geo.computeVertexNormals()
except Exception:
    pass
"""


def setp(node, name, value, warn=True):
    """Set a scalar or tuple parm defensively."""
    p = node.parm(name)
    if p is not None:
        try:
            p.set(value)
            return True
        except Exception as e:
            if warn:
                print(f"[warn] {node.name()}.{name} set failed: {e}")
            return False
    pt = node.parmTuple(name)
    if pt is not None:
        try:
            n = len(pt)
            if isinstance(value, (tuple, list)):
                for i, v in enumerate(value[:n]):
                    pt[i].set(v)
            else:
                for i in range(n):
                    pt[i].set(value)
            return True
        except Exception as e:
            if warn:
                print(f"[warn] {node.name()}.{name} tuple set failed: {e}")
            return False
    if warn:
        print(f"[warn] parm not found: {node.name()}.{name}")
    return False


def _geo(name):
    obj = hou.node("/obj")
    for old in [n for n in obj.children() if n.name() == name]:
        old.destroy()
    return obj.createNode("geo", name, run_init_scripts=True)


def _python_sop(g, name, code):
    node = g.createNode("python", name)
    if node.parm("python") is None:
        print(f"[error] {name}: python parm missing - node type is {node.type().name()}")
    else:
        node.parm("python").set(code)
    return node


def _ensure_uv_attrib(g):
    """Pre-create the point 'uv' attrib on every node so Python SOP code can
    set it (findPointAttrib returns None until the attrib exists)."""
    a = g.createNode("attribcreate", "mk_uv")
    setp(a, "name", "uv")
    setp(a, "class", 1)  # point class
    setp(a, "size", 2)
    setp(a, "type", 2)   # float
    return a


def _circle_profile(g, rad):
    c = g.createNode("circle", "profile")
    setp(c, "rad", rad)
    return c


def _dump_node_errors(g, tag):
    for n in g.children():
        try:
            err = n.errors()
        except Exception as e:
            err = f"<errors() raised: {e}>"
        err = " ".join(str(err).split()) if err else ""
        if err:
            print(f"[node-error:{tag}] {n.name()}: {err[:600]}")


def export_geo(g, out_node, stem, manifests):
    """Write via the File SOP in write mode - the ONLY geometry export Apprentice
    allows (FBX and Alembic ROPs are Core/FX-gated, verified 2026-08-28).
    Writes .obj (UE-native import today) and .bgeo.sc (Houdini-native, for the
    Engine-licensed import path later)."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        out_node.cook(force=True)
        if out_node.errors():
            print(f"[cook] {stem}: upstream errors:")
            _dump_node_errors(g, stem)
    except Exception as e:
        print(f"[cook] {stem}: cook exception: {e}")
        _dump_node_errors(g, stem)
    wrote = {}
    for ext in (".obj", ".bgeo.sc"):
        target = OUT_DIR / (stem + ext)
        f = g.createNode("file", "writer" + ext.replace(".", "_"))
        setp(f, "file", str(target))
        # menu tokens verified by probe_file_write.py: auto/read/write/none
        setp(f, "filemode", "write")
        f.setInput(0, out_node)
        try:
            f.cook(force=True)
        except Exception as e:
            print(f"[error] {ext} write failed for {stem}: {e}")
            _dump_node_errors(g, stem)
        if target.exists() and target.stat().st_size > 0:
            wrote[ext] = target
            print(f"[clutter-mesh] wrote {target.name} ({target.stat().st_size} bytes)")
        else:
            print(f"[error] missing after cook: {target}")
        f.destroy()
    if wrote:
        manifests.append({"mesh": stem, "source_geo": g.name(), "seed": SEED,
                          "formats": {k: str(v) for k, v in wrote.items()},
                          "bytes": {k: v.stat().st_size for k, v in wrote.items()}})
    else:
        print(f"[error] no format wrote for {stem}")


def build_pebbles():
    g = _geo("SM_Clutter_PebbleSet")
    py = _python_sop(g, "gen_pebbles", PEBBLES_CODE)
    out = g.createNode("null", "OUT")
    out.setInput(0, py)
    return g, out


def build_starfish():
    g = _geo("SM_Clutter_Starfish")
    py = _python_sop(g, "gen_star", STAR_CODE)
    extrude = g.createNode("polyextrude", "puff")
    setp(extrude, "dist", 0.08)
    extrude.setInput(0, py)
    smooth = g.createNode("smooth", "soften")
    setp(smooth, "iterations", 6)
    smooth.setInput(0, extrude)
    out = g.createNode("null", "OUT")
    out.setInput(0, smooth)
    return g, out


def build_spiral_shell():
    g = _geo("SM_Clutter_SpiralShell")
    py = _python_sop(g, "gen_spiral_tube", SPIRAL_CODE)
    out = g.createNode("null", "OUT")
    out.setInput(0, py)
    return g, out


def build_seaweed():
    g = _geo("SM_Clutter_SeaWeed")
    py = _python_sop(g, "gen_stalk_tube", SEAWEED_CODE)
    out = g.createNode("null", "OUT")
    out.setInput(0, py)
    return g, out


def main():
    manifests = []
    jobs = [
        (build_pebbles, "SM_Clutter_PebbleSet"),
        (build_starfish, "SM_Clutter_Starfish"),
        (build_spiral_shell, "SM_Clutter_SpiralShell"),
        (build_seaweed, "SM_Clutter_SeaWeed"),
    ]
    for builder, stem in jobs:
        g, out_node = builder()
        export_geo(g, out_node, stem, manifests)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "clutter_mesh_manifest.json", "w", encoding="utf-8") as f:
        json.dump({"schema": "melodia.sea_above_reef_meshes.v1",
                   "seed": SEED, "hython": hou.applicationVersionString(),
                   "format": "obj + bgeo.sc via File SOP write mode "
                             "(FBX and Alembic ROP export are Apprentice-blocked, verified)",
                   "ue_import": {"obj_scale": "100x (m -> cm) or author at cm on import",
                                 "nanite": True,
                                 "bgeo_sc": "requires Houdini Engine license to read in UE"},
                   "meshes": manifests}, f, indent=2)
    print(f"[clutter-mesh] manifest -> {OUT_DIR / 'clutter_mesh_manifest.json'}")


if __name__ == "__main__":
    main()
