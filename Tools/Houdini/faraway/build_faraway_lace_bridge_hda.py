r"""build_faraway_lace_bridge_hda.py -- Faraway Mother Lace Bridge HDA (hython 22.0.368).

Builds HDA_Faraway_LaceBridge_1.0.hda: a thin arched footbridge -- deck, two stepped rib
arches, spandrel posts, under-deck ties, cusped lappets and an openwork quatrefoil/trefoil
parapet. Geometry source is lace_bridge_geometry.py, embedded verbatim in the HDA's Python
SOP so the .hda is self-contained.

  input 0   OPTIONAL plan curve (first polyline prim, else the points in order). Only X/Z
            shape + the first point's Y are used. With nothing connected the HDA cooks a
            built-in gentle S-curve of `span` metres.
  output0   bridge (deck, ribs, piers, posts, ties, stretchers, cusps, rails, mullions, lace)
  output1   collision proxy: the walkable deck slab only (prims with collision_proxy=1)

Usage:
  hython Tools/Houdini/faraway/build_faraway_lace_bridge_hda.py [--out PATH] [--verify]
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[2]
DEFAULT_OUT = PROJECT_ROOT / "hda" / "HDA_Faraway_LaceBridge_1.0.hda"
MIRROR_OUT = PROJECT_ROOT / "Content" / "HDA" / "HDA_Faraway_LaceBridge_1.0.hda"
TYPE_NAME = "HDA_Faraway_LaceBridge"

sys.path.insert(0, str(PROJECT_ROOT / "Tools" / "Houdini"))
sys.path.insert(0, str(HERE))
import hda_promote_controls as promote  # noqa: E402
import lace_bridge_geometry as lb  # noqa: E402

P2 = "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/"
CO = "/Game/EnvSandbox/Materials/Instances/Copernicus/"
MATERIALS = {
    "deck": P2 + "MI_Mother_Cradle",
    "rib": P2 + "MI_Mother_Veil",
    "stretcher": P2 + "MI_Mother_Veil",
    "cusp": P2 + "MI_Mother_Veil",
    "post": P2 + "MI_Mother_Veil",
    "tie": P2 + "MI_Mother_Veil",
    "lace": P2 + "MI_Mother_Ornament",
    "rail": CO + "MI_Copernicus_GildedLoom",
    "mullion": CO + "MI_Copernicus_GildedLoom",
    "pier": P2 + "MI_Mother_Mantle",
}
SOLID_PIECES = list(MATERIALS.keys())

# Controls: (name, label, kind, default, min, max)
CONTROLS = [
    ("preview_mode", "Preview Mode (no lace)", "toggle", 0, None, None),
    ("span", "Span if No Curve (m)", "float", 14.0, 4.0, 40.0),
    ("sway", "S-Curve Sway if No Curve (m)", "float", 0.7, 0.0, 4.0),
    ("deck_width", "Deck Width (m)", "float", 2.4, 1.0, 6.0),
    ("deck_thickness", "Deck Thickness (m)", "float", 0.14, 0.05, 0.5),
    ("deck_hump", "Deck Hump at Crown (m)", "float", 0.9, 0.0, 3.0),
    ("rise", "Arch Rise under Deck (m)", "float", 3.6, 1.0, 10.0),
    ("crown_point", "Crown Point Angle (deg; 0 = round arc)", "float", 14.0, 0.0, 40.0),
    ("rib_layers", "Rib Layers", "int", 3, 1, 5),
    ("rib_width", "Rib Width (m)", "float", 0.16, 0.05, 0.4),
    ("rib_depth", "Rib Thickness Sideways (m)", "float", 0.20, 0.06, 0.6),
    ("layer_step", "Layer Step (m)", "float", 0.26, 0.1, 0.8),
    ("lace_density", "Lace Cells per Metre", "float", 1.6, 0.4, 3.0),
    ("parapet_height", "Parapet Height (m)", "float", 1.0, 0.5, 1.8),
    ("resolution", "Mesh Resolution (samples/m)", "float", 2.5, 1.0, 6.0),
    ("seed", "Seed", "int", 11, 0, 999999),
]

SOP_CODE = (
    "import hou\n"
    + (HERE / "lace_bridge_geometry.py").read_text(encoding="utf-8")
    + r'''

_node = hou.pwd()
_geo = _node.geometry()
_names = @@NAMES@@
_p = {n: _node.evalParm("../controls/" + n) for n in _names}

# optional input 0 = plan curve
_in = None
_ig = _node.inputGeometry(0)
if _ig is not None and len(_ig.points()) >= 2:
    _prs = [pr for pr in _ig.prims() if pr.numVertices() >= 2]
    if _prs:
        _in = [tuple(v.point().position()) for v in _prs[0].vertices()]
    else:
        _in = [tuple(pt.position()) for pt in _ig.points()]

_out, _meta = generate(_p, _in)
_warp = _meta["warp"]
_L = _meta["L"]
_W = _p["deck_width"]
_geo.addAttrib(hou.attribType.Point, "uv", (0.0, 0.0, 0.0))
_geo.addAttrib(hou.attribType.Prim, "piece", "")
_geo.addAttrib(hou.attribType.Prim, "unreal_material", "")
_geo.addAttrib(hou.attribType.Prim, "collision_proxy", 0)
_mats = @@MATS@@

def _emit(piece, poly, col):
    pts = []
    for q in poly:
        pt = _geo.createPoint()
        pt.setPosition(hou.Vector3(_warp(q[0], q[1], q[2])))
        pt.setAttribValue("uv", (q[0] / _L, 0.5 + q[2] / _W + 0.15 * q[1], 0.0))
        pts.append(pt)
    pr = _geo.createPolygon()
    for pt in pts:
        pr.addVertex(pt)
    pr.setAttribValue("piece", piece)
    pr.setAttribValue("unreal_material", _mats[piece])
    pr.setAttribValue("collision_proxy", col)

for _piece, _solids in _out.items():
    for _s in _solids:
        for _poly in _s:
            _emit(_piece, _poly, 1 if _piece == "deck" else 0)
_geo.addAttrib(hou.attribType.Global, "unreal_output_name", "SM_Faraway_LaceBridge")
_geo.addAttrib(hou.attribType.Global, "bridge_length", float(_L))
_geo.addAttrib(hou.attribType.Global, "from_input", int(1 if _meta["from_input"] else 0))
_geo.addAttrib(hou.attribType.Global, "springing_y", float(_meta["springing_y"]))
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

    print(f"[HDA] Faraway Lace Bridge with Houdini {hou.applicationVersionString()}")
    obj = hou.node("/obj")
    old = obj.node("Faraway_LaceBridge_Template")
    if old:
        old.destroy()
    geo = obj.createNode("geo", "Faraway_LaceBridge_Template")
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
    inp = geo.createNode("object_merge", "plan_curve_in")
    inp.parm("numobj").set(1)
    inp.parm("objpath1").setExpression('opinputpath("..", 0)', hou.exprLanguage.Hscript)

    py = geo.createNode("python", "generate_lace_bridge")
    py.setInput(0, inp)
    code = SOP_CODE.replace("@@NAMES@@", repr([c[0] for c in CONTROLS])).replace("@@MATS@@", repr(MATERIALS))
    py.parm("python").set(code)

    fuse = geo.createNode("fuse", "fuse_corners")
    fuse.setInput(0, py)
    fuse.parm("tol3d").set(0.0005)
    nrm = geo.createNode("normal", "compute_normals")
    nrm.setInput(0, fuse)
    nrm.parm("cuspangle").set(50.0)

    flags = geo.createNode("attribwrangle", "unreal_flags")
    flags.parm("class").set(1)
    flags.parm("snippet").set("i@unreal_nanite_enabled = 1;\ni@unreal_collision_mode = 0;\n")
    flags.setInput(0, nrm)

    # output1: collision proxy = flat deck prism only
    blast = geo.createNode("blast", "collision_only")
    blast.setInput(0, flags)
    blast.parm("group").set("@collision_proxy=0")
    blast.parm("grouptype").set(4)
    out0 = geo.createNode("output", "output0")
    out0.setInput(0, flags)
    out0.parm("outputidx").set(0)
    out1 = geo.createNode("output", "output1")
    out1.setInput(0, blast)
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
        description="Faraway Mother Lace Bridge (BS_GodFile UE5.8)",
        min_num_inputs=0,
        max_num_inputs=1,
    )
    promote.stage2_promote_definition(asset, pairs, out_path)
    print(f"[HDA] saved {out_path} ({out_path.stat().st_size} B)")
    MIRROR_OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out_path, MIRROR_OUT)
    print(f"[HDA] mirrored -> {MIRROR_OUT}")
    return 0


def _centroid(pr):
    pts = [v.point().position() for v in pr.vertices()]
    return [sum(p[i] for p in pts) / len(pts) for i in range(3)]


def _all_errors(inst):
    return inst.errors() + tuple(e for c in inst.allSubChildren() for e in c.errors())


def _bbox(geo):
    b = geo.boundingBox()
    return tuple(b.minvec()), tuple(b.maxvec())


def verify(hda_path: Path) -> int:
    import hou

    hou.hda.installFile(str(hda_path))
    inst = hou.node("/obj").createNode(TYPE_NAME, "verify_lacebridge")
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
        sub = [(c.name(), c.errors()) for c in inst.allSubChildren() if c.errors()]
        print(f"[Verify FAIL] output geometry is None (Python SOP error?): {sub}", file=sys.stderr)
        return 1
    pts, prims = len(g0.points()), len(g0.prims())
    print(f"[Verify] output0 {pts} pts / {prims} prims ; output1 {len(g1.points())} pts / {len(g1.prims())} prims")
    print(f"[Verify] no-input cook: from_input={g0.intAttribValue('from_input')} "
          f"bridge_length={g0.floatAttribValue('bridge_length'):.3f} m  bbox={_bbox(g0)}")
    bad = []
    bb_default = _bbox(g0)
    if prims < 500 or len(g1.prims()) < 1:
        bad.append("empty outputs")
    if g0.intAttribValue("from_input") != 0:
        bad.append("no-input cook claims from_input")

    # per-piece outward check with Houdini's own normals (closed solids only)
    for piece in SOLID_PIECES:
        sub = [p for p in g0.prims() if p.attribValue("piece") == piece]
        if not sub:
            bad.append(f"{piece}: none")
            continue
        v = 0.0
        for pr in sub:
            n = pr.normal()
            c = _centroid(pr)
            v += (c[0] * n[0] + c[1] * n[1] + c[2] * n[2]) * pr.intrinsicValue("measuredarea")
        v /= 3.0
        print(f"[Verify] {piece:9s} {len(sub):5d} prims  signed volume {v:+.5f} m^3")
        if v <= 0:
            bad.append(f"{piece}: inverted ({v:+.5f})")

    # deck: upward / downward faces by prim.normal()
    deck = [p for p in g0.prims() if p.attribValue("piece") == "deck"]
    top = max(deck, key=lambda p: _centroid(p)[1])
    bot = min(deck, key=lambda p: _centroid(p)[1])
    up_n = sum(1 for p in deck if p.normal()[1] > 0.5)
    dn_n = sum(1 for p in deck if p.normal()[1] < -0.5)
    print(f"[Verify] deck normals: highest prim ny={top.normal()[1]:+.3f}, lowest prim ny={bot.normal()[1]:+.3f}, "
          f"up {up_n} / down {dn_n}")
    if top.normal()[1] <= 0.5 or bot.normal()[1] >= -0.5 or up_n == 0 or dn_n == 0:
        bad.append("deck: top not up / underside not down")

    # collision proxy = flat deck prism only
    col_pieces = {p.attribValue("piece") for p in g1.prims()}
    gb0, gb1 = _bbox(g1)
    print(f"[Verify] output1 pieces={sorted(col_pieces)} bbox y {gb0[1]:.3f}..{gb1[1]:.3f}")
    if col_pieces != {"deck"}:
        bad.append(f"output1 not deck-only: {col_pieces}")

    # walkable: deck top lands at y=0 at both ends and humps at the crown
    ymax = max(_centroid(p)[1] for p in deck if p.normal()[1] > 0.5)
    print(f"[Verify] deck top max centroid y {ymax:.3f} (hump control 0.9)")

    base = {"hash": hash(tuple(round(c, 4) for p in g0.points() for c in p.position())), "prims": prims}

    def recook(**kw):
        old = {}
        for k, v in kw.items():
            old[k] = inst.parm(k).eval()
            inst.parm(k).set(v)
        inst.cook(force=True)
        g = inst.node("output0").geometry()
        r = (hash(tuple(round(c, 4) for p in g.points() for c in p.position())), len(g.prims()), g)
        for k, v in old.items():
            inst.parm(k).set(v)
        return r

    h_rise, p_rise, _ = recook(rise=5.0)
    h_lace, p_lace, _ = recook(lace_density=2.4)
    h_lay, p_lay, _ = recook(rib_layers=2)
    h_prev, p_prev, _ = recook(preview_mode=1)
    print(f"[Verify] drive: rise 3.6->5.0 pos-hash differs={h_rise != base['hash']} prims {prims}->{p_rise} ; "
          f"lace_density 1.6->2.4 prims {prims}->{p_lace} ; rib_layers 3->2 prims ->{p_lay} ; preview prims ->{p_prev}")
    if h_rise == base["hash"]:
        bad.append("rise did not move positions")
    if p_lace == prims:
        bad.append("lace_density did not change prim count")
    if p_lay >= prims:
        bad.append("rib_layers 3->2 did not reduce prims")
    if p_prev >= prims * 0.6:
        bad.append("preview_mode not much lighter")

    # optional input curve: a dog-leg curve far from the S-curve default
    obj = hou.node("/obj")
    cg = obj.createNode("geo", "verify_curve")
    for c in cg.children():
        c.destroy()
    pysop = cg.createNode("python", "mk")
    pysop.parm("python").set(
        "import hou\n"
        "g=hou.pwd().geometry()\n"
        "pts=[(-9,2.0,-3),(-4,2.0,1),(2,2.0,-2),(7,2.0,4),(10,2.0,5)]\n"
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
    if errs or gi is None:
        bad.append(f"curve-input cook failed: {errs}")
    else:
        bi0, bi1 = _bbox(gi)
        bb0, bb1 = bb_default
        print(f"[Verify] curve-input cook: from_input={gi.intAttribValue('from_input')} "
              f"len={gi.floatAttribValue('bridge_length'):.2f} m bbox x {bi0[0]:.2f}..{bi1[0]:.2f} "
              f"z {bi0[2]:.2f}..{bi1[2]:.2f} ; deck-top y offset follows curve y=2.0 (bbox ymax {bi1[1]:.2f}, "
              f"default {bb1[1]:.2f})")
        if gi.intAttribValue("from_input") != 1 or bi1[0] < 9.5 or bi0[0] > -8.5 or bi1[2] < 3.5:
            bad.append("curve input not followed")
        if abs((bi1[1] - bb1[1]) - 2.0) > 0.1:
            bad.append("curve start height not applied")
        # outward still true after warping on a bent path
        v = 0.0
        for pr in [p for p in gi.prims() if p.attribValue("piece") == "deck"]:
            n = pr.normal()
            c = _centroid(pr)
            v += (c[0] * n[0] + c[1] * n[1] + c[2] * n[2]) * pr.intrinsicValue("measuredarea")
        # centre-relative: shift by deck centroid so the origin offset does not bias the test
        dc = [sum(_centroid(p)[i] for p in gi.prims() if p.attribValue("piece") == "deck") /
              max(1, sum(1 for p in gi.prims() if p.attribValue("piece") == "deck")) for i in range(3)]
        v = 0.0
        for pr in [p for p in gi.prims() if p.attribValue("piece") == "deck"]:
            n = pr.normal()
            c = _centroid(pr)
            v += ((c[0] - dc[0]) * n[0] + (c[1] - dc[1]) * n[1] + (c[2] - dc[2]) * n[2]) * pr.intrinsicValue("measuredarea")
        v /= 3.0
        print(f"[Verify] curve-input deck signed volume {v:+.4f} m^3")
        if v <= 0:
            bad.append("curve-input deck inverted")
    inst.setInput(0, None)
    cg.destroy()

    if bad:
        print("[Verify FAIL] " + "; ".join(bad), file=sys.stderr)
        return 1
    # leave a clean re-cook for the numbers the registry must match
    inst.cook(force=True)
    g = inst.node("output0").geometry()
    print(f"[Verify] DEFAULT output0 {len(g.points())} pts / {len(g.prims())} prims ; "
          f"output1 {len(inst.node('output1').geometry().points())} pts / {len(inst.node('output1').geometry().prims())} prims")
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
