r"""build_faraway_terraced_island_hda.py -- Faraway Mother Terraced Island HDA (hython 22.0.368).

Builds HDA_Faraway_TerracedIsland_1.0.hda: a floating, flat-topped terraced rock island with
stepped cliff strata, a tapering underside and ledge waterfalls. Geometry source is
terraced_island_geometry.py, embedded verbatim in the HDA's Python SOPs so the .hda is
self-contained.

  output0  island (underside, cliffs, treads, plateau) + waterfall ribbons (piece="waterfall")
  output1  waterfall emitter points (@N down-slope, @fall_height, @width, @flow) -- NOT collision
  output2  collision proxy (low-poly stepped hull, collision_proxy=1)

Usage:
  hython Tools/Houdini/faraway/build_faraway_terraced_island_hda.py [--out PATH] [--verify]
"""
from __future__ import annotations

import argparse
import math
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[2]
DEFAULT_OUT = PROJECT_ROOT / "hda" / "HDA_Faraway_TerracedIsland_1.0.hda"
MIRROR_OUT = PROJECT_ROOT / "Content" / "HDA" / "HDA_Faraway_TerracedIsland_1.0.hda"
TYPE_NAME = "HDA_Faraway_TerracedIsland"

sys.path.insert(0, str(PROJECT_ROOT / "Tools" / "Houdini"))
sys.path.insert(0, str(HERE))
import hda_promote_controls as promote  # noqa: E402
import terraced_island_geometry as tig  # noqa: E402

# Controls: (name, label, kind, default, min, max)
CONTROLS = [
    ("preview_mode", "Preview Mode (low-poly)", "toggle", 0, None, None),
    ("radius", "Island Radius (m)", "float", 40.0, 8.0, 200.0),
    ("terrace_count", "Terrace Count (3-6)", "int", 4, 3, 6),
    ("terrace_height", "Terrace Height (m)", "float", 5.0, 1.0, 30.0),
    ("outline_noise", "Outline Roughness (0-0.5)", "float", 0.3, 0.0, 0.5),
    ("cliff_slope", "Cliff Lean (deg from vertical)", "float", 12.0, 0.0, 35.0),
    ("waterfall_count", "Waterfall Count", "int", 3, 0, 12),
    ("seed", "Seed", "int", 7, 0, 999999),
]

SOP_CODE = (
    "import hou\n"
    + (HERE / "terraced_island_geometry.py").read_text(encoding="utf-8")
    + r'''

_MODE = "@@MODE@@"
_node = hou.pwd()
_geo = _node.geometry()
_names = @@NAMES@@
_p = {n: _node.evalParm("../controls/" + n) for n in _names}
_res = generate(_p)

def _build_surface(tris, collision):
    _geo.addAttrib(hou.attribType.Prim, "piece", "")
    _geo.addAttrib(hou.attribType.Prim, "unreal_material", "")
    _geo.addAttrib(hou.attribType.Prim, "strata", 0)
    _geo.addAttrib(hou.attribType.Prim, "cliff", 0)
    _geo.addAttrib(hou.attribType.Prim, "band", 0)
    _geo.addAttrib(hou.attribType.Prim, "wf_id", -1)
    _geo.addAttrib(hou.attribType.Prim, "flow", 0.0)
    _geo.addAttrib(hou.attribType.Prim, "fall_height", 0.0)
    _geo.addAttrib(hou.attribType.Prim, "collision_proxy", 0)
    _geo.addAttrib(hou.attribType.Vertex, "uv", (0.0, 0.0, 0.0))
    _cache = {}
    def _pt(q):
        key = (round(q[0], 5), round(q[1], 5), round(q[2], 5))
        pt = _cache.get(key)
        if pt is None:
            pt = _geo.createPoint()
            pt.setPosition(hou.Vector3(q))
            _cache[key] = pt
        return pt
    for t in tris:
        a = t[6]
        pr = _geo.createPolygon()
        for q in t[0:3]:
            pr.addVertex(_pt(q))
        for i in range(3):
            pr.vertex(i).setAttribValue("uv", t[3 + i])
        pr.setAttribValue("piece", a["piece"])
        pr.setAttribValue("unreal_material", "" if collision else MATERIALS[a["piece"]])
        pr.setAttribValue("strata", a["strata"])
        pr.setAttribValue("cliff", a["cliff"])
        pr.setAttribValue("band", a["band"])
        pr.setAttribValue("wf_id", a.get("wf_id", -1))
        pr.setAttribValue("flow", float(a.get("flow", 0.0)))
        pr.setAttribValue("fall_height", float(a.get("fall_height", 0.0)))
        pr.setAttribValue("collision_proxy", 1 if collision else 0)

if _MODE == "island":
    _build_surface(_res["island"], False)
    _geo.addAttrib(hou.attribType.Global, "plateau_y", float(_res["meta"]["height"]))
    _geo.addAttrib(hou.attribType.Global, "underside_depth", float(_res["meta"]["depth"]))
elif _MODE == "collision":
    _build_surface(_res["collision"], True)
else:
    _geo.addAttrib(hou.attribType.Point, "N", (0.0, 0.0, 0.0))
    _geo.addAttrib(hou.attribType.Point, "fall_height", 0.0)
    _geo.addAttrib(hou.attribType.Point, "width", 0.0)
    _geo.addAttrib(hou.attribType.Point, "flow", 0.0)
    _geo.addAttrib(hou.attribType.Point, "strata", 0)
    _geo.addAttrib(hou.attribType.Point, "wf_id", 0)
    for e in _res["emitters"]:
        pt = _geo.createPoint()
        pt.setPosition(hou.Vector3(e["P"]))
        pt.setAttribValue("N", e["N"])
        pt.setAttribValue("fall_height", float(e["fall_height"]))
        pt.setAttribValue("width", float(e["width"]))
        pt.setAttribValue("flow", float(e["flow"]))
        pt.setAttribValue("strata", int(e["strata"]))
        pt.setAttribValue("wf_id", int(e["wf_id"]))
'''
)

ISLAND_FLAGS = (
    'i@unreal_nanite_enabled = (s@piece == "waterfall") ? 0 : 1;\n'
    "i@unreal_collision_mode = 0;\n"
    's@unreal_output_name = (s@piece == "waterfall") ? "SM_Faraway_TerracedIsland_Falls" : "SM_Faraway_TerracedIsland";\n'
)
COLLISION_FLAGS = (
    "i@unreal_nanite_enabled = 0;\n"
    's@unreal_output_name = "UCX_SM_Faraway_TerracedIsland_00";\n'
)


def _templates(hou):
    out = []
    for name, label, kind, default, lo, hi in CONTROLS:
        if kind == "toggle":
            out.append(hou.ToggleParmTemplate(name, label, default_value=bool(default)))
        elif kind == "int":
            out.append(hou.IntParmTemplate(name, label, 1, default_value=(default,), min=lo, max=hi))
        else:
            out.append(hou.FloatParmTemplate(name, label, 1, default_value=(default,), min=lo, max=hi))
    return out


def _py_sop(geo, name, mode):
    py = geo.createNode("python", name)
    code = SOP_CODE.replace("@@NAMES@@", repr([c[0] for c in CONTROLS])).replace("@@MODE@@", mode)
    py.parm("python").set(code)
    return py


def build_hda(out_path: Path) -> int:
    try:
        import hou
    except ImportError:
        print("[Error] hython required", file=sys.stderr)
        return 2

    print(f"[HDA] Faraway Terraced Island with Houdini {hou.applicationVersionString()}")
    obj = hou.node("/obj")
    old = obj.node("Faraway_TerracedIsland_Template")
    if old:
        old.destroy()
    geo = obj.createNode("geo", "Faraway_TerracedIsland_Template")
    for c in geo.children():
        c.destroy()

    controls = geo.createNode("null", "controls")
    group = controls.parmTemplateGroup()
    pre = {t.name() for t in group.parmTemplates()}
    for t in _templates(hou):
        group.append(t)
    controls.setParmTemplateGroup(group)
    authored = [t.name() for t in controls.parmTemplateGroup().parmTemplates() if t.name() not in pre]
    pairs = promote.stage1_promote(controls, geo, authored)
    promote.stage1_wire(controls, pairs)

    # output0: island + falls
    py_i = _py_sop(geo, "generate_island", "island")
    nrm = geo.createNode("normal", "compute_normals")
    nrm.setInput(0, py_i)
    nrm.parm("cuspangle").set(50.0)
    fl_i = geo.createNode("attribwrangle", "unreal_flags")
    fl_i.parm("class").set(1)
    fl_i.parm("snippet").set(ISLAND_FLAGS)
    fl_i.setInput(0, nrm)
    out0 = geo.createNode("output", "output0")
    out0.setInput(0, fl_i)
    out0.parm("outputidx").set(0)

    # output1: waterfall emitter points
    py_e = _py_sop(geo, "generate_emitters", "emitters")
    out1 = geo.createNode("output", "output1")
    out1.setInput(0, py_e)
    out1.parm("outputidx").set(1)

    # output2: collision proxy
    py_c = _py_sop(geo, "generate_collision", "collision")
    fl_c = geo.createNode("attribwrangle", "collision_flags")
    fl_c.parm("class").set(1)
    fl_c.parm("snippet").set(COLLISION_FLAGS)
    fl_c.setInput(0, py_c)
    out2 = geo.createNode("output", "output2")
    out2.setInput(0, fl_c)
    out2.parm("outputidx").set(2)

    out0.setDisplayFlag(True)
    out0.setRenderFlag(True)
    geo.layoutChildren()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    asset = geo.createDigitalAsset(
        name=TYPE_NAME,
        hda_file_name=str(out_path),
        description="Faraway Mother Terraced Island (BS_GodFile UE5.8)",
        min_num_inputs=0,
        max_num_inputs=0,
    )
    promote.stage2_promote_definition(asset, pairs, out_path)
    print(f"[HDA] saved {out_path} ({out_path.stat().st_size} B)")
    MIRROR_OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out_path, MIRROR_OUT)
    print(f"[HDA] mirrored -> {MIRROR_OUT}")
    return 0


# ------------------------------------------------------------------------------ verify
def _centroid(pr):
    pts = [v.point().position() for v in pr.vertices()]
    return [sum(p[i] for p in pts) / len(pts) for i in range(3)]


def _ray_max_r(tris, y, dx, dz):
    """Max horizontal distance from the axis at which a ray (0,y,0)+t(dx,0,dz) crosses tris."""
    best = -1.0
    for a, b, c in tris:
        e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        e2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        d = (dx, 0.0, dz)
        px = d[1] * e2[2] - d[2] * e2[1]
        py = d[2] * e2[0] - d[0] * e2[2]
        pz = d[0] * e2[1] - d[1] * e2[0]
        det = e1[0] * px + e1[1] * py + e1[2] * pz
        if abs(det) < 1e-12:
            continue
        inv = 1.0 / det
        tv = (0.0 - a[0], y - a[1], 0.0 - a[2])
        u = (tv[0] * px + tv[1] * py + tv[2] * pz) * inv
        if u < 0.0 or u > 1.0:
            continue
        qx = tv[1] * e1[2] - tv[2] * e1[1]
        qy = tv[2] * e1[0] - tv[0] * e1[2]
        qz = tv[0] * e1[1] - tv[1] * e1[0]
        v = (d[0] * qx + d[1] * qy + d[2] * qz) * inv
        if v < 0.0 or u + v > 1.0:
            continue
        t = (e2[0] * qx + e2[1] * qy + e2[2] * qz) * inv
        if t > best:
            best = t
    return best


def _stats(inst):
    g0 = inst.node("output0").geometry()
    g1 = inst.node("output1").geometry()
    g2 = inst.node("output2").geometry()
    return g0, g1, g2


def verify(hda_path: Path) -> int:
    import hou
    import random

    hou.hda.installFile(str(hda_path))
    inst = hou.node("/obj").createNode(TYPE_NAME, "verify_terraced_island")
    names = [c[0] for c in CONTROLS]
    missing = [n for n in names if inst.parm(n) is None]
    if missing:
        print(f"[Verify FAIL] missing promoted parms: {missing}", file=sys.stderr)
        return 1
    inst.cook(force=True)
    errs = inst.errors() + tuple(e for c in inst.allSubChildren() for e in c.errors())
    if errs:
        print(f"[Verify FAIL] node errors: {errs}", file=sys.stderr)
        return 1
    g0, g1, g2 = _stats(inst)
    if g0 is None or g1 is None or g2 is None:
        print("[Verify FAIL] an output did not cook: "
              + str([(c.path(), e) for c in inst.allSubChildren() for e in c.errors()]), file=sys.stderr)
        return 1
    n0, n1, n2 = len(g0.prims()), len(g1.points()), len(g2.prims())
    print(f"[Verify] output0 {len(g0.points())} pts / {n0} prims ; output1 {n1} emitter pts / "
          f"{len(g1.prims())} prims ; output2 {len(g2.points())} pts / {n2} prims")
    bad = []
    R0 = inst.parm("radius").eval()
    H = inst.parm("terrace_height").eval()
    N = inst.parm("terrace_count").eval()
    nwf = inst.parm("waterfall_count").eval()
    bb = g0.boundingBox()
    print(f"[Verify] bbox size {bb.sizevec()[0]:.1f} x {bb.sizevec()[1]:.1f} x {bb.sizevec()[2]:.1f} m, "
          f"y {bb.minvec()[1]:.1f}..{bb.maxvec()[1]:.1f}")

    # --- orientation with Houdini's own prim normals
    rock = [p for p in g0.prims() if p.attribValue("piece") != "waterfall"]
    vol = 0.0
    for pr in rock:
        n = pr.normal()
        c = _centroid(pr)
        vol += (c[0] * n[0] + c[1] * n[1] + c[2] * n[2]) * pr.intrinsicValue("measuredarea")
    vol /= 3.0
    print(f"[Verify] island signed volume {vol:+.1f} m^3 ({len(rock)} rock prims)")
    if vol <= 0:
        bad.append(f"island inverted ({vol:+.1f})")
    by = {}
    for pr in rock:
        by.setdefault(pr.attribValue("piece"), []).append(pr)
    for piece in ("plateau", "tread"):
        sub = by.get(piece, [])
        up = sum(1 for p in sub if p.normal()[1] > 0.99)
        print(f"[Verify] {piece:9s} {len(sub):5d} prims, normal +Y: {up}")
        if not sub or up != len(sub):
            bad.append(f"{piece}: {up}/{len(sub)} facing up")
    cl = by.get("cliff", [])
    out_c = 0
    for p in cl:
        n, c = p.normal(), _centroid(p)
        if n[0] * c[0] + n[2] * c[2] > 0 and abs(n[1]) < 0.6:
            out_c += 1
    print(f"[Verify] cliff     {len(cl):5d} prims, outward/near-vertical: {out_c}")
    if not cl or out_c < len(cl):
        bad.append(f"cliff: {out_c}/{len(cl)} outward")
    un = by.get("underside", [])
    down = sum(1 for p in un if p.normal()[1] < 0.1)
    print(f"[Verify] underside {len(un):5d} prims, facing down/out: {down}")
    if not un or down < 0.97 * len(un):
        bad.append(f"underside: {down}/{len(un)} facing down/out")
    wf = [p for p in g0.prims() if p.attribValue("piece") == "waterfall"]
    wout = sum(1 for p in wf if p.normal()[0] * _centroid(p)[0] + p.normal()[2] * _centroid(p)[2] > 0)
    # uv.v must increase downward
    vdown = 0
    for p in wf:
        vs = [(v.point().position()[1], v.attribValue("uv")[1]) for v in p.vertices()]
        ys = sorted(vs)
        if ys[0][1] >= ys[-1][1]:
            vdown += 1
    print(f"[Verify] waterfall {len(wf):5d} prims, outward {wout}, v increases downward {vdown}")
    if nwf > 0 and (not wf or wout != len(wf) or vdown != len(wf)):
        bad.append("waterfall ribbon orientation / uv")
    for a in ("strata", "cliff"):
        if g0.findPrimAttrib(a) is None:
            bad.append(f"missing prim attrib {a}")
    strata_vals = sorted({p.attribValue("strata") for p in cl})
    print(f"[Verify] cliff strata values {strata_vals} (expect 0..{N-1}); plateau y {g0.attribValue('plateau_y'):.1f}")
    if strata_vals != list(range(N)):
        bad.append(f"strata values {strata_vals}")

    # --- emitters (output1)
    if n1 != nwf:
        bad.append(f"emitters {n1} != waterfall_count {nwf}")
    bad_e = 0
    for pt in g1.points():
        nn = pt.attribValue("N")
        py = pt.position()[1]
        if not (nn[1] < -0.9 and pt.attribValue("fall_height") > 0 and pt.attribValue("width") > 0
                and abs(py / H - round(py / H)) < 1e-3 and 1 <= round(py / H) <= N):
            bad_e += 1
    print(f"[Verify] emitters: {n1}, bad {bad_e}; output1 prims {len(g1.prims())} (must be 0: not collision)")
    if bad_e or len(g1.prims()) != 0:
        bad.append("emitter attrs / output1 not pure points")

    # --- collision proxy (output2): outward by normals + conservative containment
    cvol = 0.0
    for pr in g2.prims():
        n, c = pr.normal(), _centroid(pr)
        cvol += (c[0] * n[0] + c[1] * n[1] + c[2] * n[2]) * pr.intrinsicValue("measuredarea")
    cvol /= 3.0
    print(f"[Verify] collision signed volume {cvol:+.1f} m^3, {n2} prims vs island {n0}")
    if cvol <= 0 or n2 >= n0 / 3 or n2 < 30:
        bad.append(f"collision hull invalid (vol {cvol:+.1f}, prims {n2})")
    hull = [tuple(tuple(v.point().position()) for v in pr.vertices()) for pr in g2.prims()]
    rng = random.Random(3)
    pts = [p for p in g0.points()]
    pr_of_rock = set()
    for pr in rock:
        for v in pr.vertices():
            pr_of_rock.add(v.point().number())
    sample = rng.sample(sorted(pr_of_rock), min(400, len(pr_of_rock)))
    worst = 0.0
    worst_q = None
    for num in sample:
        q = g0.point(num).position()
        r = math.hypot(q[0], q[2])
        if r < 1e-6:
            continue
        ang = math.atan2(q[2], q[0]) + 1.7e-4   # nudge off hull edges (columns sit exactly on theta = k*22.5 deg)
        hit = _ray_max_r(hull, q[1] - 0.003, math.cos(ang), math.sin(ang))
        over = r - hit if hit >= 0 else r
        if over > worst:
            worst, worst_q = over, (tuple(round(c, 2) for c in q), round(hit, 2))
    print(f"[Verify] containment: worst island-point overshoot beyond hull {worst:.3f} m over {len(sample)} samples (worst at {worst_q})")
    if worst > 0.05:
        bad.append(f"collision hull does not contain island (overshoot {worst:.3f} m)")

    # --- parm drive
    def snap():
        inst.cook(force=True)
        a, b, c = _stats(inst)
        import hashlib
        h = hashlib.sha1(repr([tuple(round(x, 4) for x in p.position()) for p in a.points()]).encode()).hexdigest()
        return len(a.prims()), len(b.points()), h

    base = snap()

    def drive(parm, val, label):
        old = inst.parm(parm).eval()
        inst.parm(parm).set(val)
        s = snap()
        inst.parm(parm).set(old)
        print(f"[Verify] drive {label}: prims {base[0]}->{s[0]} emitters {base[1]}->{s[1]} hash_changed {s[2] != base[2]}")
        return s

    s = drive("terrace_count", 5, "terrace_count 4->5")
    if s[0] == base[0]:
        bad.append("terrace_count did not change prim count")
    s = drive("radius", 60.0, "radius 40->60")
    if s[2] == base[2]:
        bad.append("radius did not move points")
    s = drive("seed", 99, "seed 7->99")
    if s[2] == base[2]:
        bad.append("seed did not move points")
    s = drive("outline_noise", 0.0, "outline_noise 0.3->0")
    if s[2] == base[2]:
        bad.append("outline_noise did not move points")
    s = drive("cliff_slope", 0.0, "cliff_slope 12->0")
    if s[2] == base[2]:
        bad.append("cliff_slope did not move points")
    s = drive("terrace_height", 8.0, "terrace_height 5->8")
    if s[2] == base[2]:
        bad.append("terrace_height did not move points")
    s = drive("waterfall_count", 5, "waterfall_count 3->5")
    if s[1] != 5 or s[0] == base[0]:
        bad.append("waterfall_count did not drive emitters/ribbons")
    s = drive("preview_mode", 1, "preview_mode 0->1")
    if s[0] >= base[0]:
        bad.append("preview_mode did not reduce prims")
    inst.parm("terrace_count").set(3)
    inst.parm("waterfall_count").set(0)
    inst.cook(force=True)
    z0, z1, _ = _stats(inst)
    print(f"[Verify] edge case N=3, waterfalls=0: output0 {len(z0.prims())} prims, emitters {len(z1.points())}")
    if len(z1.points()) != 0 or any(p.attribValue("piece") == "waterfall" for p in z0.prims()):
        bad.append("waterfall_count=0 still emits falls")
    inst.parm("terrace_count").set(6)
    inst.parm("outline_noise").set(0.5)
    inst.parm("waterfall_count").set(12)
    inst.cook(force=True)
    e0, e1, e2 = _stats(inst)
    eerrs = inst.errors() + tuple(e for c in inst.allSubChildren() for e in c.errors())
    print(f"[Verify] edge case N=6 noise 0.5 falls 12: output0 {len(e0.prims())} prims, emitters {len(e1.points())}, errors {eerrs}")
    if eerrs or len(e1.points()) != 12:
        bad.append("stress case failed")
    if bad:
        print("[Verify FAIL] " + "; ".join(bad), file=sys.stderr)
        return 1
    print("[Verify PASS]")
    inst.destroy()
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    rc = build_hda(a.out)
    if rc == 0 and a.verify:
        rc = verify(a.out)
    return rc


if __name__ == "__main__":
    sys.exit(main())
