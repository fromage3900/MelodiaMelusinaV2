r"""build_faraway_motherfold_basin_hda.py -- Faraway Mother "Motherfold Basin" HDA (hython 22.0.368).

HDA_Faraway_MotherfoldBasin_1.0.hda: one GLOBAL-coordinate terrain tile (world +-4000 m, same grid
convention as HDA_Faraway_SilkPeak) that carves a turquoise lake basin -- smooth bowl, flat shallow
shelf, travertine-stepped bank, low rim lip -- into a gentle pleated-silk base.

  output0  basin terrain tile   (point attrs: depth01 = 0 dry .. 1 deepest, carve, uv; prim piece="terrain")
  output1  shoreline polylines  (at water level; closed loops where the tile holds the whole shore,
                                 open polylines that end exactly on the tile border otherwise;
                                 prim @depth = max water depth m, @closed, @loop_id; sorted closed-first, longest-first)
  output2  water surface quad   (flat at water level, tile bounds clipped to the lake square, piece="water",
                                 world-metre UVs / 100 so neighbouring tiles tile seamlessly)

Water level (m, global) = base_height - basin_depth * (1 - water_level_frac). It depends only on the
basin controls, never on the tile, so neighbour tiles agree on it.

Usage: hython Tools/Houdini/faraway/build_faraway_motherfold_basin_hda.py [--out PATH] [--verify]
"""
from __future__ import annotations

import argparse
import math
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[2]
DEFAULT_OUT = PROJECT_ROOT / "hda" / "HDA_Faraway_MotherfoldBasin_1.0.hda"
MIRROR_OUT = PROJECT_ROOT / "Content" / "HDA" / "HDA_Faraway_MotherfoldBasin_1.0.hda"
TYPE_NAME = "HDA_Faraway_MotherfoldBasin"
sys.path.insert(0, str(PROJECT_ROOT / "Tools" / "Houdini"))
sys.path.insert(0, str(HERE))
import hda_promote_controls as promote  # noqa: E402

MAT_TERRAIN = "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Mantle"
MAT_WATER = "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_SilkWaterfall"
MAT_SHORE = "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Veil"

# (name, label, kind, default, min, max)
CONTROLS = [
    ("preview_mode", "Preview Mode (coarse grid)", "toggle", 0, None, None),
    ("tile_x", "Tile Origin X (m, global)", "float", -250.0, -4000.0, 4000.0),
    ("tile_y", "Tile Origin Y (m, global)", "float", -250.0, -4000.0, 4000.0),
    ("tile_size", "Tile Size (m)", "float", 500.0, 50.0, 1000.0),
    ("divisions", "Divisions", "int", 128, 16, 512),
    ("basin_x", "Lake Centre X (m, global)", "float", 0.0, -4000.0, 4000.0),
    ("basin_y", "Lake Centre Y (m, global)", "float", 0.0, -4000.0, 4000.0),
    ("basin_radius", "Lake Outer Radius (m)", "float", 180.0, 20.0, 1500.0),
    ("basin_depth", "Basin Depth below Rim (m)", "float", 24.0, 2.0, 120.0),
    ("shelf_width", "Shallow Shelf Width (m)", "float", 40.0, 0.0, 400.0),
    ("water_level_frac", "Water Level (0.3 low .. 0.95 brim)", "float", 0.8, 0.3, 0.95),
    ("base_height", "Land Height at Rim (m)", "float", 30.0, 0.0, 400.0),
    ("pleat_wavelength", "Silk Pleat Wavelength (m)", "float", 30.0, 6.0, 120.0),
    ("pleat_depth", "Silk Pleat Height (m)", "float", 1.2, 0.0, 10.0),
    ("seed", "Seed", "int", 20261023, 0, 99999999),
]

VEX = r"""
// Global Faraway coordinates: world is +-4000 m. Houdini XZ plane = world XY. Never tile-local.
float wx = @P.x, wy = @P.z;
float u = (wx + 4000.0) / 8000.0, v = (wy + 4000.0) / 8000.0;
float R  = chf("../controls/basin_radius");
float D  = chf("../controls/basin_depth");
float sh = chf("../controls/shelf_width");
float fr = chf("../controls/water_level_frac");
float B0 = chf("../controls/base_height");
float r  = length(set(wx, wy) - set(chf("../controls/basin_x"), chf("../controls/basin_y")));

// ---- basin profile c(r): 0 outside the lake, 0.30 on the shelf, 1.0 in the deep bowl
float bankw = 0.20 * R;
float r2 = R - bankw;                          // inner foot of the bank = outer edge of the shelf
float r3 = max(r2 - sh, 0.20 * R);             // shelf -> drop-off
float r4 = max(r3 - 0.22 * R, 0.0);            // drop-off -> flat bowl floor
float bnk = 1.0 - smooth(r2, R, r);            // 0 at the shore line of the bowl, 1 at the shelf
float bs = bnk * 5.0;                          // Pamukkale-style travertine steps on the bank (monotone)
float stp = (floor(bs) + smooth(0.3, 0.7, frac(bs))) / 5.0;
bnk = lerp(bnk, stp, 0.6);
float c = 0.30 * bnk + 0.70 * (1.0 - smooth(r4, r3, r));

// ---- gentle pleated-silk base
float sd = chi("../controls/seed") * 0.001;
float und = 0.55 * sin(2.0*M_PI*wx/2600.0 + sd*6.1) * cos(2.0*M_PI*wy/1900.0 + sd*3.7)
          + 0.45 * sin(2.0*M_PI*(wx + wy)/1100.0 + sd*1.3);
float ang = 0.6 + 0.5*sin(wx/1500.0 + sd) + 0.4*cos(wy/1300.0 + 2.0*sd);
float wl  = max(chf("../controls/pleat_wavelength"), 1.0);
float ph  = (wx*cos(ang) + wy*sin(ang)) * (2.0*M_PI / wl);
float pleat = pow(abs(sin(ph)), 0.8) * sign(sin(ph));
float raw = und * 2.5 + pleat * chf("../controls/pleat_depth") * (1.0 - 0.6*c);
// bound the base relief so dry land can never dip below the waterline (no stray puddles)
float lim = 0.8 * D * (1.0 - fr);
float noise = lim > 1e-4 ? lim * tanh(raw / lim) : 0.0;

// low travertine rim lip just outside the bank
float lip = 1.4 * exp(-pow((r - R*1.05) / (0.06*R + 1.0), 2.0));

float wlev = B0 - D * (1.0 - fr);              // water level, global metres
float y = B0 + noise - D * c + lip;
@P.y = y;
f@carve = c;
f@depth01 = clamp((wlev - y) / max(D * fr, 1e-3), 0.0, 1.0);
v@uv = set(u, v, 0);                           // global UV
"""

ATTR = r"""
s@piece = "terrain";
s@unreal_material = "@@MAT_TERRAIN@@";
i@unreal_nanite_enabled = 1;
i@unreal_collision_mode = 1;
s@unreal_output_name = "SM_Faraway_MotherfoldBasin_Terrain";
"""

SHORE_CODE = (
    "import hou\n"
    + (HERE / "motherfold_basin_geometry.py").read_text(encoding="utf-8")
    + r'''

_node = hou.pwd()
_geo = _node.geometry()
_c = lambda n: _node.evalParm("../controls/" + n)
_P = np.array(_node.inputGeometry(0).pointFloatAttribValues("P"), dtype=np.float64).reshape(-1, 3)
_geo.clear()  # a Python SOP starts as a copy of its input: keep only the contour
_wl = _c("base_height") - _c("basin_depth") * (1.0 - _c("water_level_frac"))
_maxdepth = _c("basin_depth") * _c("water_level_frac")
_geo.addAttrib(hou.attribType.Prim, "piece", "")
_geo.addAttrib(hou.attribType.Prim, "loop_id", 0)
_geo.addAttrib(hou.attribType.Prim, "closed", 0)
_geo.addAttrib(hou.attribType.Prim, "depth", 0.0)
_geo.addAttrib(hou.attribType.Prim, "unreal_material", "")
_geo.addAttrib(hou.attribType.Prim, "unreal_output_name", "")
_geo.addAttrib(hou.attribType.Prim, "unreal_nanite_enabled", 0)
for _i, (_closed, _pts) in enumerate(shoreline_chains(_P, _wl)):
    if len(_pts) < 2:
        continue
    _hp = [_geo.createPoint() for _ in _pts]
    for _pt, _q in zip(_hp, _pts):
        _pt.setPosition(hou.Vector3(_q))
    _pr = _geo.createPolygon()
    for _pt in _hp:
        _pr.addVertex(_pt)
    _pr.setIsClosed(bool(_closed))
    _pr.setAttribValue("piece", "shoreline")
    _pr.setAttribValue("loop_id", _i)
    _pr.setAttribValue("closed", 1 if _closed else 0)
    _pr.setAttribValue("depth", float(_maxdepth))
    _pr.setAttribValue("unreal_material", "@@MAT_SHORE@@")
    _pr.setAttribValue("unreal_output_name", "SM_Faraway_MotherfoldBasin_Shoreline")
'''
)

WATER_CODE = (
    "import hou\n"
    + (HERE / "motherfold_basin_geometry.py").read_text(encoding="utf-8")
    + r'''

_node = hou.pwd()
_geo = _node.geometry()
_c = lambda n: _node.evalParm("../controls/" + n)
_wl = _c("base_height") - _c("basin_depth") * (1.0 - _c("water_level_frac"))
_geo.addAttrib(hou.attribType.Point, "N", hou.Vector3(0, 1, 0))
_geo.addAttrib(hou.attribType.Point, "uv", hou.Vector3(0, 0, 0))
_geo.addAttrib(hou.attribType.Prim, "piece", "")
_geo.addAttrib(hou.attribType.Prim, "unreal_material", "")
_geo.addAttrib(hou.attribType.Prim, "unreal_output_name", "")
_geo.addAttrib(hou.attribType.Prim, "unreal_nanite_enabled", 0)
_geo.addAttrib(hou.attribType.Prim, "unreal_collision_mode", 0)
_geo.addAttrib(hou.attribType.Global, "water_level", float(_wl))
_r = water_rect(_c("tile_x"), _c("tile_y"), _c("tile_size"), _c("basin_x"), _c("basin_y"), _c("basin_radius"))
if _r is not None:
    _x0, _z0, _x1, _z1 = _r
    _pts = []
    for _x, _z in ((_x0, _z0), (_x1, _z0), (_x1, _z1), (_x0, _z1)):
        _pt = _geo.createPoint()
        _pt.setPosition(hou.Vector3(_x, _wl, _z))
        _pt.setAttribValue("uv", hou.Vector3(_x / 100.0, _z / 100.0, 0.0))
        _pts.append(_pt)
    _pr = _geo.createPolygon()
    for _pt in _pts:
        _pr.addVertex(_pt)
    _pr.setAttribValue("piece", "water")
    _pr.setAttribValue("unreal_material", "@@MAT_WATER@@")
    _pr.setAttribValue("unreal_output_name", "SM_Faraway_MotherfoldBasin_Water")
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

    print(f"[HDA] Faraway Motherfold Basin with Houdini {hou.applicationVersionString()}")
    obj = hou.node("/obj")
    old = obj.node("Faraway_MotherfoldBasin_Template")
    if old:
        old.destroy()
    geo = obj.createNode("geo", "Faraway_MotherfoldBasin_Template")
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

    # effective divisions: Preview Mode caps the grid at 32 cells
    eff = ('if(ch("../controls/preview_mode"), min(ch("../controls/divisions"), 32), '
           'ch("../controls/divisions"))+1')
    grid = geo.createNode("grid", "tile_grid")
    grid.parm("orient").set(2)  # ZX plane, normal +Y
    grid.parm("sizex").setExpression('ch("../controls/tile_size")')
    grid.parm("sizey").setExpression('ch("../controls/tile_size")')
    grid.parm("rows").setExpression(eff)
    grid.parm("cols").setExpression(eff)
    xf = geo.createNode("xform", "to_global")
    xf.setInput(0, grid)
    xf.parm("tx").setExpression('ch("../controls/tile_x") + ch("../controls/tile_size")*0.5')
    xf.parm("tz").setExpression('ch("../controls/tile_y") + ch("../controls/tile_size")*0.5')
    wr = geo.createNode("attribwrangle", "basin_field")
    wr.parm("class").set(2)  # points
    wr.parm("snippet").set(VEX)
    wr.setInput(0, xf)
    wr.setInput(1, controls)
    nrm = geo.createNode("normal", "compute_normals")
    nrm.setInput(0, wr)
    at = geo.createNode("attribwrangle", "unreal_attrs")
    at.parm("class").set(1)
    at.parm("snippet").set(ATTR.replace("@@MAT_TERRAIN@@", MAT_TERRAIN))
    at.setInput(0, nrm)

    shore = geo.createNode("python", "shoreline_curve")
    shore.parm("python").set(SHORE_CODE.replace("@@MAT_SHORE@@", MAT_SHORE))
    shore.setInput(0, wr)  # contour the raw field (same points as the tile, no normal pass needed)
    water = geo.createNode("python", "water_surface")
    water.parm("python").set(WATER_CODE.replace("@@MAT_WATER@@", MAT_WATER))

    for idx, src in enumerate((at, shore, water)):
        o = geo.createNode("output", f"output{idx}")
        o.setInput(0, src)
        o.parm("outputidx").set(idx)
        if idx == 0:
            o.setDisplayFlag(True)
            o.setRenderFlag(True)
    geo.layoutChildren()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    asset = geo.createDigitalAsset(
        name=TYPE_NAME,
        hda_file_name=str(out_path),
        description="Faraway Mother Motherfold Basin (BS_GodFile UE5.8)",
        min_num_inputs=0,
        max_num_inputs=0,
    )
    promote.stage2_promote_definition(asset, pairs, out_path)
    MIRROR_OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out_path, MIRROR_OUT)
    print(f"[HDA] saved {out_path} ({out_path.stat().st_size} B), mirrored {MIRROR_OUT}")
    return 0


# ----------------------------------------------------------------------------------------------
def _errs(inst):
    return inst.errors() + tuple(e for c in inst.allSubChildren() for e in c.errors())


def _out(inst, i):
    g = inst.node(f"output{i}").geometry()
    if g is None:
        raise RuntimeError(f"output{i} did not cook: {[e for c in inst.allSubChildren() for e in c.errors()]}")
    return g


def _water_y(inst):
    return inst.parm("base_height").eval() - inst.parm("basin_depth").eval() * (1.0 - inst.parm("water_level_frac").eval())


def _poshash(g):
    import hashlib
    return hashlib.md5(repr([tuple(round(c, 4) for c in p.position()) for p in g.points()]).encode()).hexdigest()


def verify(path: Path) -> int:
    import hou

    sys.path.insert(0, str(HERE))
    import motherfold_basin_geometry as mg

    hou.hda.installFile(str(path))
    bad = []
    inst = hou.node("/obj").createNode(TYPE_NAME, "v_default")
    missing = [c[0] for c in CONTROLS if inst.parm(c[0]) is None]
    if missing:
        print(f"[Verify FAIL] missing promoted parms: {missing}", file=sys.stderr)
        return 1
    inst.cook(force=True)
    if _errs(inst):
        print(f"[Verify FAIL] node errors: {_errs(inst)}", file=sys.stderr)
        return 1
    g0, g1, g2 = _out(inst, 0), _out(inst, 1), _out(inst, 2)
    wy = _water_y(inst)
    R = inst.parm("basin_radius").eval()
    print(f"[Verify] output0 {len(g0.points())} pts / {len(g0.prims())} prims ; output1 {len(g1.points())} pts / "
          f"{len(g1.prims())} prims ; output2 {len(g2.points())} pts / {len(g2.prims())} prims ; water level {wy:.3f} m")

    # --- terrain: outward = up by Houdini's own prim.normal(), depth mask, relief
    up = sum(1 for pr in g0.prims() if pr.normal()[1] > 0)
    ys = [p.position()[1] for p in g0.points()]
    d01 = g0.pointFloatAttribValues("depth01")
    print(f"[Verify] terrain prims facing +Y {up}/{len(g0.prims())}; Y {min(ys):.2f}..{max(ys):.2f} m; "
          f"depth01 {min(d01):.3f}..{max(d01):.3f}")
    if up < len(g0.prims()):
        bad.append("terrain faces not all up")
    if min(d01) < 0 or max(d01) > 1 or max(d01) < 0.9 or min(d01) != 0.0:
        bad.append("depth01 not a 0..1 mask reaching the floor")
    if min(ys) > wy - 0.5 * inst.parm("basin_depth").eval() * inst.parm("water_level_frac").eval():
        bad.append("basin not carved")
    dry_below = sum(1 for p in g0.points() if p.attribValue("depth01") == 0.0 and p.position()[1] < wy - 1e-6)
    if dry_below:
        bad.append(f"{dry_below} dry-mask points below water level")

    # --- shoreline: at water level, closed lake loop around the centre, consistent winding
    prims1 = g1.prims()
    closed = [p for p in prims1 if p.attribValue("closed") == 1]
    if not closed:
        bad.append("no closed shoreline loop")
    worst_y = max((abs(p.position()[1] - wy) for p in g1.points()), default=1e9)
    print(f"[Verify] shoreline {len(prims1)} chains ({len(closed)} closed); worst |y - water level| = {worst_y:.2e}")
    if worst_y > 1e-3:
        bad.append("shoreline not at water level")
    for pr in closed:
        pts = [tuple(v.point().position()) for v in pr.vertices()]
        area = mg.shoelace_xz(pts)
        cx = sum(p[0] for p in pts) / len(pts); cz = sum(p[2] for p in pts) / len(pts)
        mr = sum(math.hypot(p[0] - inst.parm("basin_x").eval(), p[2] - inst.parm("basin_y").eval()) for p in pts) / len(pts)
        print(f"[Verify]   loop {pr.attribValue('loop_id')}: {len(pts)} pts, area {area:.0f} m^2 (>0 = water inside), "
              f"mean radius {mr:.1f} m (outer radius {R:.0f})")
        if area <= 0 or not (0.45 * R < mr < R):
            bad.append("shoreline loop wrong winding / radius")
    if prims1 and prims1[0].attribValue("depth") <= 0:
        bad.append("shoreline @depth missing")
    # the water must be on the inside: terrain is wet at the centre, dry just outside the loop
    ctr = min(g0.points(), key=lambda p: (p.position()[0] - inst.parm("basin_x").eval()) ** 2
              + (p.position()[2] - inst.parm("basin_y").eval()) ** 2)
    if not ctr.position()[1] < wy:
        bad.append("lake centre is not below water level")

    # --- water quad: one flat up-facing quad at water level inside the tile + lake square, with UVs
    w = g2.prims()
    if len(w) != 1:
        bad.append(f"expected 1 water prim, got {len(w)}")
    else:
        n = w[0].normal()
        wys = {round(p.position()[1], 6) for p in g2.points()}
        xs = [p.position()[0] for p in g2.points()]; zs = [p.position()[2] for p in g2.points()]
        tx, ty, ts = (inst.parm(k).eval() for k in ("tile_x", "tile_y", "tile_size"))
        print(f"[Verify] water quad normal ({n[0]:.2f},{n[1]:.2f},{n[2]:.2f}), Y set {sorted(wys)}, "
              f"X {min(xs):.1f}..{max(xs):.1f} Z {min(zs):.1f}..{max(zs):.1f}, piece={w[0].attribValue('piece')}")
        if n[1] < 0.999 or len(wys) != 1 or abs(next(iter(wys)) - wy) > 1e-5:
            bad.append("water quad not flat/up/at level")
        if min(xs) < tx - 1e-6 or max(xs) > tx + ts + 1e-6 or min(zs) < ty - 1e-6 or max(zs) > ty + ts + 1e-6:
            bad.append("water quad outside tile bounds")
        if g2.findPointAttrib("uv") is None:
            bad.append("water quad has no uv")
        # every wet terrain point lies under the quad
        wet = [p.position() for p in g0.points() if p.attribValue("depth01") > 0]
        if wet and not all(min(xs) - 1e-6 <= q[0] <= max(xs) + 1e-6 and min(zs) - 1e-6 <= q[2] <= max(zs) + 1e-6 for q in wet):
            bad.append("wet terrain outside the water quad")

    # --- neighbour tiles: both contain part of the basin; shared edge |dY| <= 0.01 m
    a = hou.node("/obj").createNode(TYPE_NAME, "v_a"); b = hou.node("/obj").createNode(TYPE_NAME, "v_b")
    for n_ in (a, b):
        n_.parm("tile_size").set(250.0); n_.parm("divisions").set(64); n_.parm("tile_y").set(-250.0)
    a.parm("tile_x").set(-250.0); b.parm("tile_x").set(0.0)
    for n_ in (a, b):
        n_.cook(force=True)
        if _errs(n_):
            bad.append(f"neighbour tile errors {_errs(n_)}")
    ga, gb = _out(a, 0), _out(b, 0)
    ea = {round(p.position()[2], 2): p for p in ga.points() if abs(p.position()[0] - 0.0) < 1e-3}
    eb = {round(p.position()[2], 2): p for p in gb.points() if abs(p.position()[0] - 0.0) < 1e-3}
    common = sorted(set(ea) & set(eb))
    worst = max((abs(ea[k].position()[1] - eb[k].position()[1]) for k in common), default=1e9)
    worst_d = max((abs(ea[k].attribValue("depth01") - eb[k].attribValue("depth01")) for k in common), default=1e9)
    edge_min = min((ea[k].position()[1] for k in common), default=1e9)
    wet_edge = sum(1 for k in common if ea[k].attribValue("depth01") > 0)
    print(f"[Verify] neighbour edge x=0: {len(common)} samples, {wet_edge} wet / {len(common) - wet_edge} dry, edge min Y {edge_min:.2f}, "
          f"worst |dY| = {worst:.6f} m (limit 0.01), worst |d depth01| = {worst_d:.2e}")
    if len(common) < 60 or worst > 0.01 or worst_d > 1e-3 or wet_edge < 8 or len(common) - wet_edge < 8:
        bad.append("neighbour edge mismatch / basin not on both tiles")
    sa = [tuple(p.position()) for p in _out(a, 1).points() if abs(p.position()[0]) < 1e-3]
    sb = [tuple(p.position()) for p in _out(b, 1).points() if abs(p.position()[0]) < 1e-3]
    match = all(any(abs(pa[2] - pb[2]) < 0.01 and abs(pa[1] - pb[1]) < 0.01 for pb in sb) for pa in sa) if sa else False
    print(f"[Verify] shoreline endpoints on the shared border x=0: A {len(sa)} / B {len(sb)} (z={[round(q[2], 2) for q in sa]} "
          f"vs {[round(q[2], 2) for q in sb]}), all A matched in B: {match}; chains A/B: {len(_out(a, 1).prims())}/{len(_out(b, 1).prims())}")
    if len(sa) != 1 or len(sb) != 1 or not match:
        bad.append("shoreline endpoints do not meet across the tile border")
    wa, wb = _out(a, 2), _out(b, 2)
    if len(wa.prims()) != 1 or len(wb.prims()) != 1:
        bad.append("neighbour water quads missing")
    else:
        ex = max(p.position()[0] for p in wa.points()); sx = min(p.position()[0] for p in wb.points())
        if abs(ex - sx) > 1e-6:
            bad.append("neighbour water quads do not abut")

    # --- parm drive: every basin parm moves something it should
    base_hash = _poshash(g0)
    inst.parm("basin_depth").set(40.0); inst.cook(force=True)
    h_depth = _poshash(_out(inst, 0)); ymin_deep = min(p.position()[1] for p in _out(inst, 0).points())
    inst.parm("basin_depth").set(24.0)
    inst.parm("shelf_width").set(10.0); inst.cook(force=True); h_shelf = _poshash(_out(inst, 0))
    inst.parm("shelf_width").set(40.0)
    inst.parm("water_level_frac").set(0.6); inst.cook(force=True)
    wy2 = _water_y(inst)
    y2 = {round(p.position()[1], 4) for p in _out(inst, 1).points()}
    inst.parm("water_level_frac").set(0.8)
    inst.parm("basin_x").set(40.0); inst.cook(force=True); h_cx = _poshash(_out(inst, 0))
    inst.parm("basin_x").set(0.0)
    inst.parm("basin_radius").set(120.0); inst.cook(force=True); h_rad = _poshash(_out(inst, 0))
    inst.parm("basin_radius").set(180.0)
    inst.parm("preview_mode").set(1); inst.cook(force=True); pv = len(_out(inst, 0).points())
    inst.parm("preview_mode").set(0)
    print(f"[Verify] drive: depth 24->40 floor Y {min(ys):.1f}->{ymin_deep:.1f}; shelf/centre/radius/depth hashes differ: "
          f"{h_shelf != base_hash}/{h_cx != base_hash}/{h_rad != base_hash}/{h_depth != base_hash}; "
          f"water_level_frac 0.8->0.6 shoreline Y -> {sorted(y2)} (expect {wy2:.4f}); preview_mode points {len(g0.points())}->{pv}")
    if ymin_deep > min(ys) - 5 or not (h_shelf != base_hash and h_cx != base_hash and h_rad != base_hash and h_depth != base_hash):
        bad.append("basin parms did not drive geometry")
    if y2 != {round(wy2, 4)}:
        bad.append("water_level_frac did not move the shoreline to the new level")
    if pv >= len(g0.points()):
        bad.append("preview_mode did not coarsen the grid")

    if bad:
        print("[Verify FAIL] " + "; ".join(bad), file=sys.stderr)
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
