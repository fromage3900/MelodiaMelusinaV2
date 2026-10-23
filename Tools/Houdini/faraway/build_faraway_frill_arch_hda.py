r"""build_faraway_frill_arch_hda.py -- Faraway FrillValley arch HDA (hython 22.0.368).

HDA_Faraway_FrillArch_1.0.hda: pointed arch wrapped in tiered scalloped flounces with a layered brocade rosette
at the keystone (Nikki-lens "layered fashion fabric at the cheapest representation").
Geometry: frill_arch_geometry.py (+ the shared helpers from heart_gate_geometry.py), embedded in a Python SOP.
  output0 arch  /  output1 collision proxy (pier boxes)

Usage: hython Tools/Houdini/faraway/build_faraway_frill_arch_hda.py [--out PATH] [--verify]
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[2]
DEFAULT_OUT = PROJECT_ROOT / "hda" / "HDA_Faraway_FrillArch_1.0.hda"
MIRROR_OUT = PROJECT_ROOT / "Content" / "HDA" / "HDA_Faraway_FrillArch_1.0.hda"
TYPE_NAME = "HDA_Faraway_FrillArch"
sys.path.insert(0, str(PROJECT_ROOT / "Tools" / "Houdini"))
sys.path.insert(0, str(HERE))
import hda_promote_controls as promote  # noqa: E402

MATERIALS = {
    "core": "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Mantle",
    "frill": "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Gown",
    "brocade_flower": "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Corset",
    "pier": "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_GildedLoom",
}
CONTROLS = [
    ("preview_mode", "Preview Mode", "toggle", 0, None, None),
    ("span", "Span (m)", "float", 5.0, 2.0, 14.0),
    ("pier_height", "Pier Height (m)", "float", 2.0, 0.5, 8.0),
    ("lancet", "Lancet (R/span; 1 = equilateral)", "float", 1.0, 0.78, 2.0),
    ("core_width", "Core Arch Width (m)", "float", 0.28, 0.08, 0.8),
    ("frill_layers", "Frill Layers", "int", 4, 1, 8),
    ("frill_width", "Frill Width (m)", "float", 0.7, 0.15, 2.0),
    ("scallops", "Scallops per Layer", "int", 14, 4, 40),
    ("scallop_amp", "Scallop Ripple (m)", "float", 0.05, 0.0, 0.3),
    ("layer_dz", "Layer Spacing (m)", "float", 0.05, 0.02, 0.2),
    ("flower_petals", "Rosette Petals", "int", 8, 4, 16),
    ("flower_radius", "Rosette Radius (m)", "float", 0.5, 0.15, 1.5),
    ("arc_segments", "Arc Segments", "int", 48, 12, 128),
    ("seed", "Seed", "int", 11, 0, 999999),
]
SOP_CODE = (
    "import hou\n"
    + (HERE / "heart_gate_geometry.py").read_text(encoding="utf-8")
    + "\n"
    + (HERE / "frill_arch_geometry.py").read_text(encoding="utf-8")
    + r'''

_node = hou.pwd()
_geo = _node.geometry()
_names = @@NAMES@@
_p = {n: _node.evalParm("../controls/" + n) for n in _names}
_out, _meta = generate_frill(_p)
_geo.addAttrib(hou.attribType.Prim, "piece", "")
_geo.addAttrib(hou.attribType.Prim, "unreal_material", "")
_geo.addAttrib(hou.attribType.Prim, "collision_proxy", 0)
_mats = @@MATS@@
for _piece, _solids in _out.items():
    for _s in _solids:
        for _poly in _s:
            _pts = [_geo.createPoint() for _ in _poly]
            for _pt, _q in zip(_pts, _poly):
                _pt.setPosition(hou.Vector3(_q))
            _pr = _geo.createPolygon()
            for _pt in _pts:
                _pr.addVertex(_pt)
            _pr.setAttribValue("piece", _piece)
            _pr.setAttribValue("unreal_material", _mats[_piece])
            _pr.setAttribValue("collision_proxy", 1 if _piece == "pier" else 0)
_geo.addAttrib(hou.attribType.Global, "unreal_output_name", "SM_Faraway_FrillArch")
_geo.addAttrib(hou.attribType.Global, "apex_y", float(_meta["apex_y"]))
'''
)


def build_hda(out_path: Path) -> int:
    import hou

    obj = hou.node("/obj")
    old = obj.node("Faraway_FrillArch_Template")
    if old:
        old.destroy()
    geo = obj.createNode("geo", "Faraway_FrillArch_Template")
    for c in geo.children():
        c.destroy()
    controls = geo.createNode("null", "controls")
    grp = controls.parmTemplateGroup()
    pre = {t.name() for t in grp.parmTemplates()}
    for name, label, kind, d, lo, hi in CONTROLS:
        if kind == "toggle":
            grp.append(hou.ToggleParmTemplate(name, label, default_value=bool(d)))
        elif kind == "int":
            grp.append(hou.IntParmTemplate(name, label, 1, default_value=(d,), min=lo, max=hi))
        else:
            grp.append(hou.FloatParmTemplate(name, label, 1, default_value=(d,), min=lo, max=hi))
    controls.setParmTemplateGroup(grp)
    authored = [t.name() for t in controls.parmTemplateGroup().parmTemplates() if t.name() not in pre]
    pairs = promote.stage1_promote(controls, geo, authored)
    promote.stage1_wire(controls, pairs)

    py = geo.createNode("python", "generate_frill_arch")
    py.parm("python").set(SOP_CODE.replace("@@NAMES@@", repr([c[0] for c in CONTROLS])).replace("@@MATS@@", repr(MATERIALS)))
    fuse = geo.createNode("fuse", "fuse_corners")
    fuse.setInput(0, py)
    fuse.parm("tol3d").set(0.0005)
    nrm = geo.createNode("normal", "compute_normals")
    nrm.setInput(0, fuse)
    nrm.parm("cuspangle").set(50.0)
    uvw = geo.createNode("attribwrangle", "gate_uv")
    uvw.parm("class").set(2)
    uvw.parm("snippet").set("float s = max(chf('../controls/span'), 0.001);\nv@uv = set(@P.x / s + 0.5, @P.y / s, 0.0);\n")
    uvw.setInput(0, nrm)
    uvw.setInput(1, controls)
    fl = geo.createNode("attribwrangle", "unreal_flags")
    fl.parm("class").set(1)
    fl.parm("snippet").set("i@unreal_nanite_enabled = 1;\ni@unreal_collision_mode = 0;\n")
    fl.setInput(0, uvw)
    blast = geo.createNode("blast", "collision_only")
    blast.setInput(0, fl)
    blast.parm("group").set("@collision_proxy=0")
    blast.parm("grouptype").set(4)
    o0 = geo.createNode("output", "output0")
    o0.setInput(0, fl)
    o0.parm("outputidx").set(0)
    o1 = geo.createNode("output", "output1")
    o1.setInput(0, blast)
    o1.parm("outputidx").set(1)
    o0.setDisplayFlag(True)
    o0.setRenderFlag(True)
    geo.layoutChildren()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    asset = geo.createDigitalAsset(name=TYPE_NAME, hda_file_name=str(out_path),
                                   description="Faraway FrillValley Arch (BS_GodFile UE5.8)", min_num_inputs=0, max_num_inputs=0)
    promote.stage2_promote_definition(asset, pairs, out_path)
    MIRROR_OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out_path, MIRROR_OUT)
    print(f"[HDA] saved {out_path} ({out_path.stat().st_size} B), mirrored {MIRROR_OUT}")
    return 0


def _vol(prims):
    v = 0.0
    for pr in prims:
        n = pr.normal()
        pts = [x.point().position() for x in pr.vertices()]
        c = [sum(q[i] for q in pts) / len(pts) for i in range(3)]
        v += (c[0] * n[0] + c[1] * n[1] + c[2] * n[2]) * pr.intrinsicValue("measuredarea")
    return v / 3.0


def verify(path: Path) -> int:
    import hou

    hou.hda.installFile(str(path))
    inst = hou.node("/obj").createNode(TYPE_NAME, "v_frill")
    missing = [c[0] for c in CONTROLS if inst.parm(c[0]) is None]
    if missing:
        print("[Verify FAIL] missing parms", missing, file=sys.stderr)
        return 1
    inst.cook(force=True)
    g0 = inst.node("output0").geometry()
    g1 = inst.node("output1").geometry()
    if g0 is None or g1 is None:
        print("[Verify FAIL] no geometry:", [e for c in inst.allSubChildren() for e in c.errors()], file=sys.stderr)
        return 1
    prims = len(g0.prims())
    print(f"[Verify] output0 {len(g0.points())} pts / {prims} prims ; output1 {len(g1.points())} / {len(g1.prims())}")
    bad = []
    for piece in ("core", "pier", "frill", "brocade_flower"):
        sub = [p for p in g0.prims() if p.attribValue("piece") == piece]
        v = _vol(sub) if sub else 0.0
        print(f"[Verify] {piece:15s} {len(sub):5d} prims  signed volume {v:+.4f} m^3")
        if not sub or v <= 0:
            bad.append(f"{piece}: {'none' if not sub else 'inverted'}")
    h0 = g0.floatAttribValue("apex_y")
    inst.parm("frill_layers").set(2)
    inst.cook(force=True)
    p2 = len(inst.node("output0").geometry().prims())
    inst.parm("frill_layers").set(4)
    inst.parm("lancet").set(1.4)
    inst.cook(force=True)
    h1 = inst.node("output0").geometry().floatAttribValue("apex_y")
    print(f"[Verify] drive: frill_layers 4->2 prims {prims}->{p2} ; lancet 1.0->1.4 apex {h0:.2f}->{h1:.2f}")
    if p2 >= prims or abs(h1 - h0) < 0.05:
        bad.append("parm drive")
    if bad:
        print("[Verify FAIL]", bad, file=sys.stderr)
        return 1
    print("[Verify PASS]")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    rc = build_hda(a.out)
    return verify(a.out) if rc == 0 and a.verify else rc


if __name__ == "__main__":
    sys.exit(main())
