r"""build_faraway_orchard_tree_hda.py -- Faraway Mother Listening Orchard hero tree HDA (hython 22.0.368).

Builds HDA_Faraway_ListeningOrchardTree_1.0.hda: gnarled blossom tree (fluted twisting trunk,
buttress roots, recursive tapered-tube limbs, blossom card cloud, low-poly canopy proxy).
Geometry source is orchard_tree_geometry.py, embedded verbatim in the HDA's Python SOP so the
.hda is self-contained.

  output0  trunk + roots + branches + blossom_cards + canopy_proxy (LOD volume)
  output1  trunk-only collision cylinder proxy

Usage:
  hython Tools/Houdini/faraway/build_faraway_orchard_tree_hda.py [--out PATH] [--verify]
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[2]
DEFAULT_OUT = PROJECT_ROOT / "hda" / "HDA_Faraway_ListeningOrchardTree_1.0.hda"
MIRROR_OUT = PROJECT_ROOT / "Content" / "HDA" / "HDA_Faraway_ListeningOrchardTree_1.0.hda"
TYPE_NAME = "HDA_Faraway_ListeningOrchardTree"

sys.path.insert(0, str(PROJECT_ROOT / "Tools" / "Houdini"))
sys.path.insert(0, str(HERE))
import hda_promote_controls as promote  # noqa: E402

WOOD = "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_CherryBlossomWood"
BLOSSOM = "/Game/EnvSandbox/Materials/Instances/Environment/MI_ProcFoliage_Sakura"
MATERIALS = {
    "trunk": WOOD,
    "root": WOOD,
    "branch": WOOD,
    "trunk_collision": WOOD,
    "blossom_cards": BLOSSOM,
    "canopy_proxy": BLOSSOM,
}

# Controls: (name, label, kind, default, min, max)
CONTROLS = [
    ("preview_mode", "Preview Mode (fast viewport)", "toggle", 0, None, None),
    ("height", "Tree Height (m)", "float", 9.0, 3.0, 25.0),
    ("trunk_radius", "Trunk Radius (m)", "float", 0.75, 0.15, 2.0),
    ("branch_levels", "Branch Levels (1-4)", "int", 3, 1, 4),
    ("branch_spread", "Branch Spread (wider = flatter crown)", "float", 1.0, 0.3, 2.0),
    ("twist", "Trunk Twist (turns)", "float", 0.8, 0.0, 3.0),
    ("blossom_density", "Blossom Cards per Metre of Twig", "float", 36.0, 0.0, 80.0),
    ("seed", "Seed", "int", 11, 0, 999999),
]

SOP_CODE = (
    "import hou\n"
    + (HERE / "orchard_tree_geometry.py").read_text(encoding="utf-8").split('if __name__ == "__main__":')[0]
    + r'''

_node = hou.pwd()
_geo = _node.geometry()
_names = @@NAMES@@
_p = {n: _node.evalParm("../controls/" + n) for n in _names}
_prims, _meta = generate(_p)
_mats = @@MATS@@
_geo.addAttrib(hou.attribType.Prim, "piece", "")
_geo.addAttrib(hou.attribType.Prim, "unreal_material", "")
_geo.addAttrib(hou.attribType.Prim, "collision_proxy", 0)
_geo.addAttrib(hou.attribType.Prim, "blossom_id", -1)
_geo.addAttrib(hou.attribType.Prim, "blossom_tint", 0.0)
_geo.addAttrib(hou.attribType.Prim, "branch_level", 0)
_geo.addAttrib(hou.attribType.Prim, "solid_id", -1)
_geo.addAttrib(hou.attribType.Vertex, "uv", (0.0, 0.0, 0.0))

for _r in _prims:
    _pts = [_geo.createPoint() for _ in _r["poly"]]
    for _pt, _q in zip(_pts, _r["poly"]):
        _pt.setPosition(hou.Vector3(_q))
    _pr = _geo.createPolygon()
    for _pt in _pts:
        _pr.addVertex(_pt)
    for _v, _uv in zip(_pr.vertices(), _r["uv"]):
        _v.setAttribValue("uv", (float(_uv[0]), float(_uv[1]), 0.0))
    _pr.setAttribValue("piece", _r["piece"])
    _pr.setAttribValue("unreal_material", _mats[_r["piece"]])
    _pr.setAttribValue("collision_proxy", int(_r["coll"]))
    _pr.setAttribValue("blossom_id", int(_r["bid"]))
    _pr.setAttribValue("blossom_tint", float(_r["tint"]))
    _pr.setAttribValue("branch_level", int(_r["level"]))
    _pr.setAttribValue("solid_id", int(_r["solid"]))
_geo.addAttrib(hou.attribType.Global, "unreal_output_name", "SM_Faraway_ListeningOrchardTree")
_geo.addAttrib(hou.attribType.Global, "tree_height_m", float(_meta["tip_y"]))
_geo.addAttrib(hou.attribType.Global, "canopy_radius_m", float(_meta["canopy_radius"]))
_geo.addAttrib(hou.attribType.Global, "card_count", int(_meta["card_count"]))
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

    print(f"[HDA] Faraway Listening Orchard Tree with Houdini {hou.applicationVersionString()}")
    obj = hou.node("/obj")
    old = obj.node("Faraway_OrchardTree_Template")
    if old:
        old.destroy()
    geo = obj.createNode("geo", "Faraway_OrchardTree_Template")
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

    py = geo.createNode("python", "generate_orchard_tree")
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

    # output0: everything except the collision cylinder; output1: the collision cylinder only
    drop = geo.createNode("blast", "drop_collision")
    drop.setInput(0, flags)
    drop.parm("group").set("@collision_proxy=1")
    drop.parm("grouptype").set(4)
    only = geo.createNode("blast", "collision_only")
    only.setInput(0, flags)
    only.parm("group").set("@collision_proxy=0")
    only.parm("grouptype").set(4)
    out0 = geo.createNode("output", "output0")
    out0.setInput(0, drop)
    out0.parm("outputidx").set(0)
    out1 = geo.createNode("output", "output1")
    out1.setInput(0, only)
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
        description="Faraway Mother Listening Orchard Tree (BS_GodFile UE5.8)",
        min_num_inputs=0,
        max_num_inputs=0,
    )
    promote.stage2_promote_definition(asset, pairs, out_path)
    print(f"[HDA] saved {out_path} ({out_path.stat().st_size} B)")
    MIRROR_OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out_path, MIRROR_OUT)
    print(f"[HDA] mirrored -> {MIRROR_OUT}")
    return 0


def _center(pr):
    pts = [v.point().position() for v in pr.vertices()]
    return [sum(p[i] for p in pts) / len(pts) for i in range(3)]


def _sig(g):
    return sorted((round(p.position()[0], 4), round(p.position()[1], 4), round(p.position()[2], 4))
                  for p in g.points())


def _cook(inst):
    inst.cook(force=True)
    errs = inst.errors() + tuple(e for c in inst.allSubChildren() for e in c.errors())
    return errs, inst.node("output0").geometry(), inst.node("output1").geometry()


def _vol(prims):
    v = 0.0
    for pr in prims:
        n = pr.normal()
        c = _center(pr)
        v += (c[0] * n[0] + c[1] * n[1] + c[2] * n[2]) * pr.intrinsicValue("measuredarea")
    return v / 3.0


def verify(hda_path: Path) -> int:
    import hou

    hou.hda.installFile(str(hda_path))
    inst = hou.node("/obj").createNode(TYPE_NAME, "verify_orchardtree")
    names = [c[0] for c in CONTROLS]
    missing = [n for n in names if inst.parm(n) is None]
    if missing:
        print(f"[Verify FAIL] missing promoted parms: {missing}", file=sys.stderr)
        return 1
    errs, g0, g1 = _cook(inst)
    if errs:
        print(f"[Verify FAIL] node errors: {errs}", file=sys.stderr)
        return 1
    if g0 is None or g1 is None:
        print("[Verify FAIL] output geometry is None", file=sys.stderr)
        return 1
    pts, prims = len(g0.points()), len(g0.prims())
    print(f"[Verify] output0 {pts} pts / {prims} prims ; output1 {len(g1.points())} pts / {len(g1.prims())} prims")
    if prims < 500 or len(g1.prims()) < 8:
        print("[Verify FAIL] empty outputs", file=sys.stderr)
        return 1
    bad = []
    pieces = {}
    for pr in g0.prims():
        pieces.setdefault(pr.attribValue("piece"), []).append(pr)
    for need in ("trunk", "root", "branch", "blossom_cards", "canopy_proxy"):
        if need not in pieces:
            bad.append(f"{need}: none")
    if "trunk_collision" in pieces:
        bad.append("trunk_collision leaked into output0")
    # per-SOLID outward check with Houdini's own prim normals (every tube / blob, not just per piece)
    per = {}
    for pr in list(g0.prims()) + list(g1.prims()):
        sid = pr.attribValue("solid_id")
        if sid >= 0:
            per.setdefault(sid, []).append(pr)
    inverted = [sid for sid, pl in per.items() if _vol(pl) <= 0.0]
    print(f"[Verify] closed solids {len(per)}, inverted {len(inverted)}")
    if inverted:
        bad.append(f"inverted solids: {inverted[:8]}")
    for piece in ("trunk", "root", "branch", "canopy_proxy"):
        v = _vol(pieces.get(piece, []))
        print(f"[Verify] {piece:14s} {len(pieces.get(piece, [])):5d} prims  signed volume {v:+.4f} m^3")
        if v <= 0:
            bad.append(f"{piece}: inverted ({v:+.4f})")
    cv = _vol(list(g1.prims()))
    print(f"[Verify] trunk_collision {len(g1.prims())} prims  signed volume {cv:+.4f} m^3")
    if cv <= 0:
        bad.append("collision cylinder inverted")
    # UP check: topmost trunk cap faces up, and the collision cylinder's top cap faces up
    for label, prs in (("trunk", pieces.get("trunk", [])), ("collision", list(g1.prims()))):
        caps = [pr for pr in prs if len(pr.vertices()) >= 6]
        top = max(caps, key=lambda pr: _center(pr)[1])
        bot = min(caps, key=lambda pr: _center(pr)[1])
        print(f"[Verify] {label} top cap ny {top.normal()[1]:+.2f}, bottom cap ny {bot.normal()[1]:+.2f}")
        if top.normal()[1] < 0.3 or bot.normal()[1] > -0.3:
            bad.append(f"{label} end caps not facing outward (up/down)")
    # cards
    cards = pieces.get("blossom_cards", [])
    ids = [pr.attribValue("blossom_id") for pr in cards]
    if len(set(ids)) != len(ids) or min(ids) != 0:
        bad.append("blossom_id not unique / zero based")
    uvs = [v.attribValue("uv") for pr in cards for v in pr.vertices()]
    if not uvs or any(not (0.0 <= u[0] <= 1.0 and 0.0 <= u[1] <= 1.0) for u in uvs):
        bad.append("card UVs outside 0-1")
    cen = [sum(p.position()[i] for p in g0.points()) / len(g0.points()) for i in range(3)]
    outward = sum(1 for pr in cards if sum((_center(pr)[i] - cen[i]) * pr.normal()[i] for i in range(3)) > 0)
    print(f"[Verify] cards {len(cards)}, unique ids ok, normals outward {outward}/{len(cards)}")
    if outward < 0.5 * len(cards):
        bad.append("card normals mostly point into the canopy")
    ys = [p.position()[1] for p in g0.points()]
    th = g0.floatAttribValue("tree_height_m")
    cr = g0.floatAttribValue("canopy_radius_m")
    print(f"[Verify] measured tree_height_m {th:.2f}  canopy_radius_m {cr:.2f}  bbox y {min(ys):.2f}..{max(ys):.2f}")
    # parm drive
    base_sig = _sig(g0)

    def with_parm(name, val):
        old = inst.parm(name).eval()
        inst.parm(name).set(val)
        _, a, _ = _cook(inst)
        r = (len(a.points()), len(a.prims()), _sig(a))
        inst.parm(name).set(old)
        return r

    for name, val, kind in (("branch_levels", 2, "count"), ("blossom_density", 8.0, "count"),
                            ("height", 14.0, "pos"), ("branch_spread", 1.6, "pos"),
                            ("twist", 2.0, "pos"), ("trunk_radius", 1.0, "pos"), ("seed", 12, "pos")):
        r = with_parm(name, val)
        moved = r[2] != base_sig
        cnt = (r[0], r[1]) != (pts, prims)
        print(f"[Verify] drive {name}={val}: pts/prims {pts}/{prims} -> {r[0]}/{r[1]}  positions_moved={moved}")
        if not moved or (kind == "count" and not cnt):
            bad.append(f"parm {name} did not drive geometry")
    _, a, _ = _cook(inst)
    if _sig(a) != base_sig:
        bad.append("not deterministic across cooks")
    inst.parm("preview_mode").set(1)
    perr, a, _ = _cook(inst)
    pp = len(a.prims())
    print(f"[Verify] preview_mode on: {pp} prims (default {prims})")
    if pp >= prims * 0.6 or perr:
        bad.append("preview_mode not lighter / errors")
    inst.parm("preview_mode").set(0)
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
