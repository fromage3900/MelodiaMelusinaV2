r"""build_faraway_heart_gate_hda.py -- Faraway Mother Heart Gate HDA (hython 22.0.368).

Builds HDA_Faraway_HeartGate_1.0.hda: lace-rib pointed-arch gate with a hung
cordiform opening. Geometry source is heart_gate_geometry.py, embedded verbatim
in the HDA's Python SOP so the .hda is self-contained.

  output0  gate (ribs, piers, cusps, stretchers, heart frame/stem, heart glow)
  output1  collision proxy (pier boxes only -- the doorway stays walkable)

Usage:
  hython Tools/Houdini/faraway/build_faraway_heart_gate_hda.py [--out PATH] [--verify]
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[2]
DEFAULT_OUT = PROJECT_ROOT / "hda" / "HDA_Faraway_HeartGate_1.0.hda"
MIRROR_OUT = PROJECT_ROOT / "Content" / "HDA" / "HDA_Faraway_HeartGate_1.0.hda"
TYPE_NAME = "HDA_Faraway_HeartGate"

sys.path.insert(0, str(PROJECT_ROOT / "Tools" / "Houdini"))
sys.path.insert(0, str(HERE))
import hda_promote_controls as promote  # noqa: E402
import heart_gate_geometry as hg  # noqa: E402

MATERIALS = {
    "rib": "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Veil",
    "stretcher": "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Veil",
    "cusp": "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Veil",
    "pier": "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_GildedLoom",
    "heart_frame": "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_GildedLoom",
    "heart_stem": "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_GildedLoom",
    "heart_glow": "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_FinalDreamweaver",
}

# Controls: (name, label, kind, default, min, max)
CONTROLS = [
    ("preview_mode", "Preview Mode", "toggle", 0, None, None),
    ("span", "Span (m)", "float", 6.0, 2.0, 16.0),
    ("pier_height", "Pier Height (m)", "float", 3.0, 0.5, 10.0),
    ("lancet", "Lancet (R/span; 1 = equilateral)", "float", 1.0, 0.78, 2.0),
    ("rib_layers", "Rib Layers", "int", 3, 1, 6),
    ("rib_width", "Rib Width (m)", "float", 0.22, 0.05, 0.6),
    ("rib_depth", "Rib Depth (m)", "float", 0.45, 0.1, 1.5),
    ("layer_step", "Layer Step (m)", "float", 0.34, 0.15, 1.0),
    ("cusps_per_rib", "Cusps per Side", "int", 9, 0, 24),
    ("cusp_size", "Cusp Size (m)", "float", 0.22, 0.05, 0.8),
    ("stretchers", "Stretchers per Side", "int", 5, 0, 16),
    ("arc_segments", "Arc Segments", "int", 24, 8, 64),
    ("heart_width", "Heart Width (m)", "float", 1.4, 0.3, 3.0),
    ("heart_height_frac", "Heart Height (0-1 of rise)", "float", 0.55, 0.2, 0.8),
    ("heart_frame_width", "Heart Frame Width (m)", "float", 0.12, 0.03, 0.4),
    ("heart_segments", "Heart Segments", "int", 48, 16, 128),
    ("seed", "Seed", "int", 7, 0, 999999),
]

SOP_CODE = (
    "import hou\n"
    + (HERE / "heart_gate_geometry.py").read_text(encoding="utf-8")
    + r'''

_node = hou.pwd()
_geo = _node.geometry()
_names = @@NAMES@@
_p = {n: _node.evalParm("../controls/" + n) for n in _names}
_out, _sheets, _meta = generate(_p)
_geo.addAttrib(hou.attribType.Prim, "piece", "")
_geo.addAttrib(hou.attribType.Prim, "unreal_material", "")
_geo.addAttrib(hou.attribType.Prim, "collision_proxy", 0)
_mats = @@MATS@@

def _emit(piece, poly, col=0):
    pts = [_geo.createPoint() for _ in poly]
    for pt, q in zip(pts, poly):
        pt.setPosition(hou.Vector3(q))
    pr = _geo.createPolygon()
    # Houdini builds the polygon with the vertex order given
    for pt in pts:
        pr.addVertex(pt)
    pr.setAttribValue("piece", piece)
    pr.setAttribValue("unreal_material", _mats[piece])
    pr.setAttribValue("collision_proxy", col)

for _piece, _solids in _out.items():
    for _s in _solids:
        for _poly in _s:
            _emit(_piece, _poly, 1 if _piece == "pier" else 0)
for _piece, _poly in _sheets:
    _emit(_piece, _poly)
_geo.addAttrib(hou.attribType.Global, "unreal_output_name", "SM_Faraway_HeartGate")
_geo.addAttrib(hou.attribType.Global, "apex_y", float(_meta["apex_y"]))
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

    print(f"[HDA] Faraway Heart Gate with Houdini {hou.applicationVersionString()}")
    obj = hou.node("/obj")
    old = obj.node("Faraway_HeartGate_Template")
    if old:
        old.destroy()
    geo = obj.createNode("geo", "Faraway_HeartGate_Template")
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

    py = geo.createNode("python", "generate_heart_gate")
    code = SOP_CODE.replace("@@NAMES@@", repr([c[0] for c in CONTROLS])).replace("@@MATS@@", repr(MATERIALS))
    py.parm("python").set(code)

    # fuse shared corners, then smooth normals with a hard-edge cusp
    fuse = geo.createNode("fuse", "fuse_corners")
    fuse.setInput(0, py)
    fuse.parm("tol3d").set(0.0005)
    nrm = geo.createNode("normal", "compute_normals")
    nrm.setInput(0, fuse)
    nrm.parm("cuspangle").set(50.0)

    # planar UVs on the gate face (u across span, v up the rise)
    uvw = geo.createNode("attribwrangle", "gate_uv")
    uvw.parm("class").set(0)  # points
    uvw.parm("snippet").set(
        "float s = max(chf('../controls/span'), 0.001);\n"
        "v@uv = set(@P.x / s + 0.5, @P.y / s, 0.0);\n"
    )
    uvw.setInput(0, nrm)
    uvw.setInput(1, controls)

    flags = geo.createNode("attribwrangle", "unreal_flags")
    flags.parm("class").set(1)
    flags.parm("snippet").set("i@unreal_nanite_enabled = 1;\ni@unreal_collision_mode = 0;\n")
    flags.setInput(0, uvw)

    # output1: collision proxy = pier boxes
    blast = geo.createNode("blast", "collision_only")
    blast.setInput(0, flags)
    blast.parm("group").set("@collision_proxy=0")
    blast.parm("grouptype").set(4)  # primitives
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
        description="Faraway Mother Heart Gate (BS_GodFile UE5.8)",
        min_num_inputs=0,
        max_num_inputs=0,
    )
    promote.stage2_promote_definition(asset, pairs, out_path)
    print(f"[HDA] saved {out_path} ({out_path.stat().st_size} B)")
    MIRROR_OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out_path, MIRROR_OUT)
    print(f"[HDA] mirrored -> {MIRROR_OUT}")
    return 0


def hou_center(pr):
    pts = [v.point().position() for v in pr.vertices()]
    return [sum(p[i] for p in pts) / len(pts) for i in range(3)]


def verify(hda_path: Path) -> int:
    import hou

    hou.hda.installFile(str(hda_path))
    inst = hou.node("/obj").createNode(TYPE_NAME, "verify_heartgate")
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
    g0 = inst.node("output0").geometry()
    g1 = inst.node("output1").geometry()
    pts, prims = len(g0.points()), len(g0.prims())
    print(f"[Verify] output0 {pts} pts / {prims} prims ; output1 {len(g1.points())} pts / {len(g1.prims())} prims")
    if prims < 100 or len(g1.prims()) < 1:
        print("[Verify FAIL] empty outputs", file=sys.stderr)
        return 1
    # per-piece outward check with Houdini's own normals (closed solids only)
    bad = []
    for piece in ("rib", "pier", "cusp", "stretcher", "heart_frame", "heart_stem"):
        sub = [p for p in g0.prims() if p.attribValue("piece") == piece]
        if not sub:
            bad.append(f"{piece}: none")
            continue
        v = 0.0
        for pr in sub:
            n = pr.normal()
            c = hou_center(pr)
            v += (c[0] * n[0] + c[1] * n[1] + c[2] * n[2]) * pr.intrinsicValue("measuredarea")
        v /= 3.0
        print(f"[Verify] {piece:12s} {len(sub):5d} prims  signed volume {v:+.4f} m^3")
        if v <= 0:
            bad.append(f"{piece}: inverted ({v:+.4f})")
    glow = [p for p in g0.prims() if p.attribValue("piece") == "heart_glow"]
    up = sum(1 for p in glow if p.normal()[2] > 0) , sum(1 for p in glow if p.normal()[2] < 0)
    print(f"[Verify] heart_glow {len(glow)} tris, +Z {up[0]} / -Z {up[1]}")
    if up[0] == 0 or up[1] == 0:
        bad.append("heart_glow: missing a side")
    # parm drive: lancet must move the apex; rib_layers must change prim count
    h0 = g0.floatAttribValue("apex_y")
    inst.parm("lancet").set(1.4)
    inst.cook(force=True)
    h1 = inst.node("output0").geometry().floatAttribValue("apex_y")
    inst.parm("lancet").set(1.0)
    inst.parm("rib_layers").set(2)
    inst.cook(force=True)
    p2 = len(inst.node("output0").geometry().prims())
    print(f"[Verify] drive: lancet 1.0->1.4 apex {h0:.3f}->{h1:.3f} ; rib_layers 3->2 prims {prims}->{p2}")
    if abs(h1 - h0) < 0.05 or p2 >= prims:
        bad.append("parm drive did not move geometry")
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
