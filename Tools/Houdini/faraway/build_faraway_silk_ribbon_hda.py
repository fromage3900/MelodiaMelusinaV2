r"""build_faraway_silk_ribbon_hda.py -- Faraway Mother Silk Ribbon HDA (hython 22.0.368).

Builds HDA_Faraway_SilkRibbon_1.0.hda: wide floating cloth ribbons for the sky. Geometry source is
silk_ribbon_geometry.py, embedded verbatim in the HDA's Python SOP so the .hda is self-contained.

  input 0   OPTIONAL guide curve (first polyline prim, else points in order). Without it a built-in
            swooping 3D spline of `length` metres is used.
  output0   ribbon: front sheet + back sheet (oppositely wound, +-1.5 mm apart), UV u=length v=width,
            VAT/WPO point attrs rest_u / flutter_phase / edge_weight
  output1   guide curve resampled (points + polyline), @pscale = local ribbon width, @rest_u, v@tangent

Usage:
  hython Tools/Houdini/faraway/build_faraway_silk_ribbon_hda.py [--out PATH] [--verify]
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[2]
DEFAULT_OUT = PROJECT_ROOT / "hda" / "HDA_Faraway_SilkRibbon_1.0.hda"
MIRROR_OUT = PROJECT_ROOT / "Content" / "HDA" / "HDA_Faraway_SilkRibbon_1.0.hda"
TYPE_NAME = "HDA_Faraway_SilkRibbon"

sys.path.insert(0, str(PROJECT_ROOT / "Tools" / "Houdini"))
sys.path.insert(0, str(HERE))
import hda_promote_controls as promote  # noqa: E402

MATERIALS = {
    "front": "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_SilkWaterfall",
    "back": "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FarawayCelestialSilk",
    "guide": "",
}

# Controls: (name, label, kind, default, min, max)
CONTROLS = [
    ("preview_mode", "Preview Mode (low-res, 1/3 length segments)", "toggle", 0, None, None),
    ("length", "Ribbon Length (m; ignored when a curve is plugged in)", "float", 24.0, 2.0, 200.0),
    ("width", "Ribbon Width (m)", "float", 1.2, 0.1, 8.0),
    ("twist_turns", "Twist (full turns along length)", "float", 1.5, -8.0, 8.0),
    ("flutter_amp", "Edge Ripple Height (m)", "float", 0.35, 0.0, 3.0),
    ("flutter_wavelength", "Ripple Wavelength (m)", "float", 3.0, 0.3, 30.0),
    ("taper", "Taper to Tip (0 = none, 1 = point)", "float", 0.4, 0.0, 0.95),
    ("segments", "Length Segments", "int", 120, 8, 600),
    ("seed", "Seed", "int", 11, 0, 999999),
    ("base_roll", "Base Tilt (deg; 0 = upright curtain, 90 = flat sheet)", "float", 25.0, -180.0, 180.0),
]

SOP_CODE = (
    "import hou\n"
    + (HERE / "silk_ribbon_geometry.py").read_text(encoding="utf-8")
    + r'''

_node = hou.pwd()
_geo = _node.geometry()
_names = @@NAMES@@
_p = {n: _node.evalParm("../controls/" + n) for n in _names}

# optional input 0 = guide curve
_in = None
_ig = _node.inputGeometry(0)
if _ig is not None and len(_ig.points()) >= 2:
    _prs = [pr for pr in _ig.prims() if pr.numVertices() >= 2]
    if _prs:
        _in = [tuple(v.point().position()) for v in _prs[0].vertices()]
    else:
        _in = [tuple(pt.position()) for pt in _ig.points()]

_sheets, _guide, _meta = generate(_p, _in)
_mats = @@MATS@@
_geo.addAttrib(hou.attribType.Point, "uv", (0.0, 0.0, 0.0))
_geo.addAttrib(hou.attribType.Point, "rest_u", 0.0)
_geo.addAttrib(hou.attribType.Point, "flutter_phase", 0.0)
_geo.addAttrib(hou.attribType.Point, "edge_weight", 0.0)
_geo.addAttrib(hou.attribType.Point, "pscale", 0.0)
_geo.addAttrib(hou.attribType.Point, "tangent", (0.0, 0.0, 0.0))
_geo.addAttrib(hou.attribType.Prim, "piece", "")
_geo.addAttrib(hou.attribType.Prim, "unreal_material", "")
_geo.addAttrib(hou.attribType.Prim, "is_guide", 0)

for _name in ("front", "back"):
    _sh = _sheets[_name]
    _P = _sh["P"]
    _ni = len(_P)
    _nj = len(_P[0])
    _pts = []
    for _i in range(_ni):
        _row = []
        for _j in range(_nj):
            _pt = _geo.createPoint()
            _pt.setPosition(hou.Vector3(_P[_i][_j]))
            _pt.setAttribValue("uv", _sh["uv"][_i][_j])
            _pt.setAttribValue("rest_u", float(_sh["rest_u"][_i]))
            _pt.setAttribValue("flutter_phase", float(_sh["phase"][_i][_j]))
            _pt.setAttribValue("edge_weight", float(_sh["ew"][_j]))
            _row.append(_pt)
        _pts.append(_row)
    for _i in range(_ni - 1):
        for _j in range(_nj - 1):
            if _name == "front":   # faces +n: clockwise seen from +n (Houdini front = clockwise)
                _ring = (_pts[_i][_j], _pts[_i][_j + 1], _pts[_i + 1][_j + 1], _pts[_i + 1][_j])
            else:                  # faces -n: opposite winding
                _ring = (_pts[_i][_j], _pts[_i + 1][_j], _pts[_i + 1][_j + 1], _pts[_i][_j + 1])
            _pr = _geo.createPolygon()
            for _pt in _ring:
                _pr.addVertex(_pt)
            _pr.setAttribValue("piece", _name)
            _pr.setAttribValue("unreal_material", _mats[_name])

_gp = []
for _pos, _u, _w, _t in _guide:
    _pt = _geo.createPoint()
    _pt.setPosition(hou.Vector3(_pos))
    _pt.setAttribValue("rest_u", float(_u))
    _pt.setAttribValue("pscale", float(_w))
    _pt.setAttribValue("tangent", _t)
    _gp.append(_pt)
_gr = _geo.createPolygon()
_gr.setIsClosed(False)
for _pt in _gp:
    _gr.addVertex(_pt)
_gr.setAttribValue("piece", "guide")
_gr.setAttribValue("is_guide", 1)

_geo.addAttrib(hou.attribType.Global, "unreal_output_name", "SM_Faraway_SilkRibbon")
_geo.addAttrib(hou.attribType.Global, "ribbon_length", float(_meta["length"]))
_geo.addAttrib(hou.attribType.Global, "min_bend_radius", float(_meta["min_radius"]))
_geo.addAttrib(hou.attribType.Global, "from_input", int(1 if _meta["from_input"] else 0))
'''
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


def build_hda(out_path: Path) -> int:
    try:
        import hou
    except ImportError:
        print("[Error] hython required", file=sys.stderr)
        return 2

    print(f"[HDA] Faraway Silk Ribbon with Houdini {hou.applicationVersionString()}")
    obj = hou.node("/obj")
    old = obj.node("Faraway_SilkRibbon_Template")
    if old:
        old.destroy()
    geo = obj.createNode("geo", "Faraway_SilkRibbon_Template")
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

    # optional curve input: opinputpath("..", 0) is "" when nothing is connected (cooks clean)
    inp = geo.createNode("object_merge", "guide_curve_in")
    inp.parm("numobj").set(1)
    inp.parm("objpath1").setExpression('opinputpath("..", 0)', hou.exprLanguage.Hscript)

    py = geo.createNode("python", "generate_silk_ribbon")
    py.setInput(0, inp)
    code = SOP_CODE.replace("@@NAMES@@", repr([c[0] for c in CONTROLS])).replace("@@MATS@@", repr(MATERIALS))
    py.parm("python").set(code)

    # ---- output0 branch: ribbon sheets only
    rib = geo.createNode("blast", "ribbon_only")
    rib.setInput(0, py)
    rib.parm("group").set("@is_guide=1")
    rib.parm("grouptype").set(4)
    # detail wrangle, not an Attribute Delete SOP: attribdelete cooks an inner `output0` node that the repo gate
    # (which keys outputs by node name) mistook for this HDA's own output0 after the first parameter change
    rib_clean = geo.createNode("attribwrangle", "ribbon_drop_guide_attrs")
    rib_clean.setInput(0, rib)
    rib_clean.parm("class").set(0)
    rib_clean.parm("snippet").set('removepointattrib(0, "pscale");\nremovepointattrib(0, "tangent");\n')
    nrm = geo.createNode("normal", "compute_normals")
    nrm.setInput(0, rib_clean)
    nrm.parm("type").set(0)  # point normals (N on points)
    nrm.parm("cuspangle").set(60.0)  # sheets are separate point sets, so front/back never average
    flags = geo.createNode("attribwrangle", "unreal_flags")
    flags.parm("class").set(1)
    flags.parm("snippet").set("i@unreal_nanite_enabled = 1;\ni@unreal_collision_mode = 0;\n")
    flags.setInput(0, nrm)
    out0 = geo.createNode("output", "output0")
    out0.setInput(0, flags)
    out0.parm("outputidx").set(0)

    # ---- output1 branch: guide curve with @pscale = width
    gd = geo.createNode("blast", "guide_only")
    gd.setInput(0, py)
    gd.parm("group").set("@is_guide=0")
    gd.parm("grouptype").set(4)
    gd_clean = geo.createNode("attribwrangle", "guide_drop_ribbon_attrs")
    gd_clean.setInput(0, gd)
    gd_clean.parm("class").set(0)
    gd_clean.parm("snippet").set('removepointattrib(0, "uv");\nremovepointattrib(0, "flutter_phase");\n'
                                 'removepointattrib(0, "edge_weight");\n')
    gd_flags = geo.createNode("attribwrangle", "guide_flags")
    gd_flags.parm("class").set(0)  # detail
    gd_flags.parm("snippet").set('s@unreal_output_name = "SM_Faraway_SilkRibbon_Guide";\n')
    gd_flags.setInput(0, gd_clean)
    out1 = geo.createNode("output", "output1")
    out1.setInput(0, gd_flags)
    out1.parm("outputidx").set(1)

    out0.setDisplayFlag(True)
    out0.setRenderFlag(True)
    geo.layoutChildren()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    asset = geo.createDigitalAsset(
        name=TYPE_NAME,
        hda_file_name=str(out_path),
        description="Faraway Mother Silk Ribbon (BS_GodFile UE5.8)",
        min_num_inputs=0,
        max_num_inputs=1,
    )
    promote.stage2_promote_definition(asset, pairs, out_path)
    print(f"[HDA] saved {out_path} ({out_path.stat().st_size} B)")
    MIRROR_OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out_path, MIRROR_OUT)
    print(f"[HDA] mirrored -> {MIRROR_OUT}")
    return 0


def _all_errors(inst):
    return inst.errors() + tuple(e for c in inst.allSubChildren() for e in c.errors())


def _pos_hash(g):
    import hashlib
    h = hashlib.md5()
    for p in g.points():
        x, y, z = p.position()
        h.update(f"{x:.5f},{y:.5f},{z:.5f};".encode())
    return h.hexdigest()


def _center(pr):
    pts = [v.point().position() for v in pr.vertices()]
    return [sum(p[i] for p in pts) / len(pts) for i in range(3)]


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _facing_check(g, label, bad):
    """Houdini-normal checks on the double-sided ribbon, using prim.normal() only.

    1. pairing: front prim k and back prim k (same grid cell) -- the front normal must point from
       the back sheet toward the front sheet and vice versa (each sheet faces AWAY from the other)
    2. no fold-over: neighbouring prims along the strip have normals within 90 deg
    3. point N agrees with the prim normal it belongs to
    """
    front = [p for p in g.prims() if p.attribValue("piece") == "front"]
    back = [p for p in g.prims() if p.attribValue("piece") == "back"]
    if not front or len(front) != len(back):
        bad.append(f"{label}: sheets missing/unequal ({len(front)}/{len(back)})")
        return
    f_ok = b_ok = 0
    for fp, bp in zip(front, back):
        d = [a - b for a, b in zip(_center(fp), _center(bp))]  # back -> front
        if _dot(fp.normal(), d) > 0:
            f_ok += 1
        if _dot(bp.normal(), d) < 0:
            b_ok += 1
    n = len(front)
    print(f"[Verify] {label}: front faces away from back {f_ok}/{n}; back faces away from front {b_ok}/{n}")
    if f_ok != n or b_ok != n:
        bad.append(f"{label}: sheets not facing away from each other (front {f_ok}/{n}, back {b_ok}/{n})")
    cols = 8  # prims are emitted row-major over (length i, width j): neighbours along length are 8 apart
    folds = 0
    for sheet in (front, back):
        for k in range(len(sheet) - cols):
            if _dot(sheet[k].normal(), sheet[k + cols].normal()) <= 0.0:
                folds += 1
    print(f"[Verify] {label}: along-length normal flips (dot<=0) = {folds}")
    if folds:
        bad.append(f"{label}: {folds} fold-over flips")


def verify(hda_path: Path) -> int:
    import hou

    hou.hda.installFile(str(hda_path))
    obj = hou.node("/obj")
    inst = obj.createNode(TYPE_NAME, "verify_silkribbon")
    names = [c[0] for c in CONTROLS]
    missing = [n for n in names if inst.parm(n) is None]
    if missing:
        print(f"[Verify FAIL] missing promoted parms: {missing}", file=sys.stderr)
        return 1
    inst.cook(force=True)
    errs = _all_errors(inst)
    if errs:
        print(f"[Verify FAIL] node errors: {errs}", file=sys.stderr)
        return 1
    g0 = inst.node("output0").geometry()
    g1 = inst.node("output1").geometry()
    if g0 is None or g1 is None:
        print("[Verify FAIL] outputs did not cook: "
              f"{[e for c in inst.allSubChildren() for e in c.errors()]}", file=sys.stderr)
        return 1
    pts, prims = len(g0.points()), len(g0.prims())
    gp, gpr = len(g1.points()), len(g1.prims())
    print(f"[Verify] output0 {pts} pts / {prims} prims ; output1 {gp} pts / {gpr} prims")
    bad = []
    if prims < 100 or gp < 2 or gpr != 1:
        bad.append("empty outputs")
    for a in ("rest_u", "flutter_phase", "edge_weight", "uv", "N"):
        if g0.findPointAttrib(a) is None:
            bad.append(f"output0 missing point attr {a}")
    for a in ("pscale", "rest_u", "tangent"):
        if g1.findPointAttrib(a) is None:
            bad.append(f"output1 missing point attr {a}")
    if g0.findPointAttrib("pscale") is not None:
        bad.append("output0 still carries pscale")

    # metric size: guide length matches the control, ribbon bbox is sky scale
    L = g0.floatAttribValue("ribbon_length")
    gl = sum((g1.point(i + 1).position() - g1.point(i).position()).length() for i in range(gp - 1))
    bb = g0.boundingBox()
    sz = bb.sizevec()
    print(f"[Verify] guide polyline length {gl:.3f} m (control 24.0); ribbon bbox "
          f"{sz[0]:.2f} x {sz[1]:.2f} x {sz[2]:.2f} m")
    if abs(gl - 24.0) > 0.4:
        bad.append(f"guide length {gl:.3f} != 24")
    rmin = g0.floatAttribValue("min_bend_radius")
    print(f"[Verify] tightest guide bend radius {rmin:.2f} m (must exceed half width 0.6 m)")
    if rmin < 0.6:
        bad.append("guide bends tighter than half the ribbon width")
    w0 = g1.point(0).attribValue("pscale")
    w1 = g1.point(gp - 1).attribValue("pscale")
    print(f"[Verify] guide @pscale {w0:.3f} -> {w1:.3f} m (width 1.2, taper 0.4 => 1.2 -> 0.72)")
    if abs(w0 - 1.2) > 1e-4 or abs(w1 - 0.72) > 1e-3:
        bad.append("pscale not width*taper")
    # attribute ranges
    ru = [p.attribValue("rest_u") for p in g0.points()]
    ew = [p.attribValue("edge_weight") for p in g0.points()]
    fp = [p.attribValue("flutter_phase") for p in g0.points()]
    print(f"[Verify] rest_u {min(ru):.3f}..{max(ru):.3f}; edge_weight {min(ew):.3f}..{max(ew):.3f}; "
          f"flutter_phase {min(fp):.3f}..{max(fp):.3f}")
    if min(ru) != 0.0 or abs(max(ru) - 1.0) > 1e-6 or min(ew) != 0.0 or abs(max(ew) - 1.0) > 1e-6:
        bad.append("rest_u / edge_weight not spanning 0..1")
    if not (0.0 <= min(fp) and max(fp) < 1.0):
        bad.append("flutter_phase outside [0,1)")

    # centre column is rippled least: |displacement| of centre vs edge from the flat strip is checked
    # through the ripple parm drive below (flutter_amp 0 flattens edges)
    _facing_check(g0, "default", bad)
    uvs = [p.attribValue("uv") for p in g0.points()]
    print(f"[Verify] uv u {min(u[0] for u in uvs):.2f}..{max(u[0] for u in uvs):.2f}, "
          f"v {min(u[1] for u in uvs):.2f}..{max(u[1] for u in uvs):.2f}")

    # ---- parm drive
    h_def = _pos_hash(g0)
    results = {}

    def _try(parm, val, restore):
        inst.parm(parm).set(val)
        inst.cook(force=True)
        gg = inst.node("output0").geometry()
        results[parm] = (_pos_hash(gg), len(gg.points()), len(gg.prims()))
        inst.parm(parm).set(restore)

    _try("flutter_amp", 0.0, 0.35)
    _try("twist_turns", 3.0, 1.5)
    _try("width", 2.4, 1.2)
    _try("taper", 0.0, 0.4)
    _try("seed", 99, 11)
    _try("segments", 60, 120)
    _try("preview_mode", 1, 0)
    for k, (hsh, np_, npr) in results.items():
        print(f"[Verify] drive {k}: pts {np_} prims {npr} hash_changed={hsh != h_def}")
        if hsh == h_def:
            bad.append(f"{k} did not move geometry")
    if results["segments"][2] >= prims:
        bad.append("segments 120->60 did not reduce prims")
    if results["preview_mode"][2] >= prims * 0.4:
        bad.append("preview_mode not much lighter")

    # ripple profile: compare against the flutter_amp=0 cook, point by point (same topology).
    # centre column (edge_weight 0) must move far less than the edge columns.
    inst.parm("flutter_amp").set(0.0)
    inst.cook(force=True)
    flat_pos = [tuple(p.position()) for p in inst.node("output0").geometry().points()]  # snapshot: geometry() is live
    inst.parm("flutter_amp").set(0.35)
    inst.cook(force=True)
    gr = inst.node("output0").geometry()
    dc = []
    de = []
    for fp_, pr_ in zip(flat_pos, gr.points()):
        q = pr_.position()
        d = ((q[0] - fp_[0]) ** 2 + (q[1] - fp_[1]) ** 2 + (q[2] - fp_[2]) ** 2) ** 0.5
        (dc if pr_.attribValue("edge_weight") == 0.0 else de if pr_.attribValue("edge_weight") == 1.0 else []).append(d)
    print(f"[Verify] ripple displacement: centre max {max(dc):.3f} m, edge max {max(de):.3f} m (amp 0.35)")
    if not (max(de) > 0.25 and max(dc) < 0.35 * max(de)):
        bad.append("edge ripple not stronger than centre ripple")

    # twist: sum of row-to-row front-normal angle must grow with twist_turns
    def _turn(gg):
        fr_ = [p for p in gg.prims() if p.attribValue("piece") == "front"]
        tot = 0.0
        import math
        for k in range(4, len(fr_) - 8, 8):
            a_, b_ = fr_[k].normal(), fr_[k + 8].normal()
            tot += math.acos(max(-1.0, min(1.0, _dot(a_, b_))))
        return tot
    inst.parm("flutter_amp").set(0.0)
    inst.parm("twist_turns").set(0.0)
    inst.cook(force=True)
    t0 = _turn(inst.node("output0").geometry())
    inst.parm("twist_turns").set(1.5)
    inst.cook(force=True)
    t1 = _turn(inst.node("output0").geometry())
    inst.parm("flutter_amp").set(0.35)
    print(f"[Verify] accumulated row-to-row normal turn: twist 0 -> {t0:.2f} rad, twist 1.5 -> {t1:.2f} rad")
    if t1 < t0 + 2.0 * 3.14159 * 1.5 * 0.5:
        bad.append("twist_turns did not rotate the strip")

    # ---- curve input
    cg = obj.createNode("geo", "verify_curve")
    for c in cg.children():
        c.destroy()
    pysop = cg.createNode("python", "mk")
    pysop.parm("python").set(
        "import hou\n"
        "g=hou.pwd().geometry()\n"
        "pts=[(-6,2.0,-3),(-2,5.0,1),(3,3.0,-2),(8,9.0,4),(12,6.0,6)]\n"
        "ps=[g.createPoint() for _ in pts]\n"
        "for p,q in zip(ps,pts): p.setPosition(hou.Vector3(q))\n"
        "pr=g.createPolygon(); pr.setIsClosed(False)\n"
        "for p in ps: pr.addVertex(p)\n"
    )
    pysop.setDisplayFlag(True)
    pysop.setRenderFlag(True)
    inst.setInput(0, cg)
    inst.cook(force=True)
    errs = _all_errors(inst)
    gi = inst.node("output0").geometry()
    gi1 = inst.node("output1").geometry()
    if errs or gi is None or gi1 is None:
        bad.append(f"curve-input cook failed: {errs}")
    else:
        b0, b1 = gi1.boundingBox().minvec(), gi1.boundingBox().maxvec()
        s0 = gi1.point(0).position()
        sN = gi1.point(len(gi1.points()) - 1).position()
        print(f"[Verify] curve-input: from_input={gi.intAttribValue('from_input')} guide start "
              f"({s0[0]:.2f},{s0[1]:.2f},{s0[2]:.2f}) end ({sN[0]:.2f},{sN[1]:.2f},{sN[2]:.2f}) "
              f"guide bbox y {b0[1]:.2f}..{b1[1]:.2f}")
        if gi.intAttribValue("from_input") != 1:
            bad.append("curve input not recognised")
        if abs(s0[0] + 6) > 0.01 or abs(s0[1] - 2) > 0.01 or abs(sN[0] - 12) > 0.01 or abs(sN[1] - 6) > 0.01:
            bad.append("guide does not start/end on the input curve")
        _facing_check(gi, "curve-input", bad)
    inst.setInput(0, None)
    inst.cook(force=True)
    gback = inst.node("output0").geometry()
    if gback.intAttribValue("from_input") != 0 or len(gback.prims()) != prims:
        bad.append("disconnecting the curve did not restore the default ribbon")
    cg.destroy()

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
