r"""build_faraway_silk_peak_hda.py -- Faraway Mother Silk Peak tile HDA (hython 22.0.368).

HDA_Faraway_SilkPeak_1.0.hda: one terrain tile of pleated-silk landform, evaluated in
GLOBAL Faraway coordinates (8 km world, X/Y in [-4000, +4000] m, u=(X+4000)/8000) so
neighbouring tiles share edges exactly (plan 90bfa88: no tile-local UV resets).

Field = macro silk peaks (Gaussians) + pleats on ONE globally continuous phase
phi = X*cos(th) + Y*sin(th) + phase_warp*F(X,Y)  (F = the shared Chladni field, tools: chladni_field.py,
mode 3,5) + a gentle walkable valley where |F| < seam_width (ResonantSeamWay). The phase gradient stays in
[1-d, 1+d] with d = phase_warp*pi/1000 (0.25 at 80 m), so crests never alias or pinch (the old
dot(P, dir(P)) phase multiplied its own frequency and pinched at the origin). Normals are analytic
(central difference of the SAME height function at +-0.25 m), so tile borders match by construction.
No Vellum: this is the static far-field tile; hero cloth patches are a later, separate gate.

Usage: hython Tools/Houdini/faraway/build_faraway_silk_peak_hda.py [--out PATH] [--verify]
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[2]
DEFAULT_OUT = PROJECT_ROOT / "hda" / "HDA_Faraway_SilkPeak_1.0.hda"
MIRROR_OUT = PROJECT_ROOT / "Content" / "HDA" / "HDA_Faraway_SilkPeak_1.0.hda"
TYPE_NAME = "HDA_Faraway_SilkPeak"
sys.path.insert(0, str(PROJECT_ROOT / "Tools" / "Houdini"))
sys.path.insert(0, str(HERE))
import hda_promote_controls as promote  # noqa: E402
import chladni_field  # noqa: E402

CONTROLS = [
    ("tile_x", "Tile Origin X (m, global)", "float", -125.0, -4000.0, 4000.0),
    ("tile_y", "Tile Origin Y (m, global)", "float", -125.0, -4000.0, 4000.0),
    ("tile_size", "Tile Size (m)", "float", 250.0, 50.0, 1000.0),
    ("divisions", "Divisions", "int", 128, 16, 512),
    ("height_scale", "Peak Height (m)", "float", 90.0, 5.0, 400.0),
    ("pleat_wavelength", "Pleat Wavelength (m)", "float", 36.0, 4.0, 80.0),
    ("pleat_depth", "Pleat Depth (m)", "float", 4.5, 0.0, 20.0),
    ("pleat_angle", "Pleat Direction (deg, global)", "float", 35.0, -90.0, 90.0),
    ("phase_warp", "Pleat Phase Warp (m of F)", "float", 80.0, 0.0, 127.0),
    ("pleat_exponent", "Pleat Profile Exponent (>=1)", "float", 1.0, 1.0, 3.0),
    ("gather_length", "Gather Length (m, fold taper along crest)", "float", 180.0, 60.0, 600.0),
    ("gather_floor", "Gather Floor (min pleat strength 0-1)", "float", 0.25, 0.0, 1.0),
    ("seam_width", "Seam Valley Width (|Chladni|)", "float", 0.12, 0.02, 0.4),
    ("seam_depth", "Seam Valley Depth (m)", "float", 6.0, 0.0, 30.0),
    ("seed", "Seed (world seed; jitters peak anchors only)", "int", 3900, 0, 99999999),
]

VEX = chladni_field.vex_function() + r"""
// Global Faraway coordinates: world is +-4000 m, u=(X+4000)/8000. Never tile-local.
float silk_h(float wx; float wy) {
    float chl = chl_F(wx, wy, 3, 5);
    float sd = chi("../controls/seed") * 0.001;
    float hs = chf("../controls/height_scale");
    float h = 0;
    float ax[] = {-900, 400, 1500, -2200, 2600, -300};
    float ay[] = {300, -600, 900, -1400, -2000, 1800};
    float radii[]   = {520, 380, 640, 900, 700, 450};
    float heights[] = {1.00, 0.70, 0.85, 0.95, 0.60, 0.55};
    for (int i = 0; i < len(ax); i++) {
        float j = rand(sd + i*7.1) - 0.5;
        vector2 c = set(ax[i] + j*80, ay[i] + (rand(sd + i*3.3) - 0.5)*80);
        float d = length(set(wx, wy) - c);
        h += heights[i] * exp(-(d*d) / (2.0*radii[i]*radii[i]));
    }
    h *= hs;

    // pleats on the shared global phase (chl_pleat, chladni_field.py): |grad phi| in [1-d, 1+d], d = phase_warp*pi/1000
    float th = chf("../controls/pleat_angle");
    float pleat = chl_pleat(wx, wy, chf("../controls/pleat_wavelength"), th, chf("../controls/phase_warp"),
                            chf("../controls/pleat_exponent"));
    float ridge = clamp(h / max(hs, 1e-3), 0, 1);     // pleats live on the landform
    // folds swell and taper along their own length (lens-shaped gathers, not corrugation): a slow global envelope
    // crossing the crests at 90 deg; and they relax toward the nodal seam so the walkable route stays calm
    float ga = radians(th) + 0.5*M_PI;
    float gl = max(chf("../controls/gather_length"), 20.0);
    float env = 0.5 + 0.5*sin(2.0*M_PI*((wx*cos(ga) + wy*sin(ga)) / gl) + 0.37*chl);
    float gfl = clamp(chf("../controls/gather_floor"), 0.0, 1.0);
    float gath = (gfl + (1.0 - gfl)*env) * (0.45 + 0.55*smooth(0.0, 0.8, abs(chl)));
    h += pleat * chf("../controls/pleat_depth") * gath * (0.15 + 0.85*ridge);

    // ResonantSeamWay: smooth walkable valley along nodal lines
    h -= (1.0 - smooth(0.0, chf("../controls/seam_width"), abs(chl))) * chf("../controls/seam_depth");
    return h;
}

float wx = @P.x, wy = @P.z;                       // Houdini XZ plane = world XY
float u = (wx + 4000.0) / 8000.0, v = (wy + 4000.0) / 8000.0;
float e = 0.25;
@P.y = silk_h(wx, wy);
float hx = (silk_h(wx + e, wy) - silk_h(wx - e, wy)) / (2.0*e);
float hz = (silk_h(wx, wy + e) - silk_h(wx, wy - e)) / (2.0*e);
v@N = normalize(set(-hx, 1.0, -hz));              // analytic: identical on both sides of a tile border
float chl = chl_F(wx, wy, 3, 5);
vector2 g = chl_grad(wx, wy, 3, 5);
f@tension = clamp(length(g) * 8000.0 / (8.0*M_PI), 0, 1);   // |grad_uv F| over its true maximum (not the saturating /8)
f@resonance = clamp(abs(chl) / 2.0, 0, 1);
f@seam = 1.0 - smooth(0.0, chf("../controls/seam_width"), abs(chl));
v@uv = set(u, v, 0);                               // global UV
"""

ATTR = r"""
s@unreal_material = "/Game/EnvSandbox/Materials/Instances/FarawayMother/P2/MI_Mother_Mantle";
i@unreal_nanite_enabled = 1;
i@unreal_collision_mode = 1;
s@unreal_output_name = "SM_Faraway_SilkPeak_Tile";
"""


def build_hda(out_path: Path) -> int:
    import hou

    obj = hou.node("/obj")
    old = obj.node("Faraway_SilkPeak_Template")
    if old:
        old.destroy()
    geo = obj.createNode("geo", "Faraway_SilkPeak_Template")
    for c in geo.children():
        c.destroy()
    controls = geo.createNode("null", "controls")
    grp = controls.parmTemplateGroup()
    pre = {t.name() for t in grp.parmTemplates()}
    for name, label, kind, d, lo, hi in CONTROLS:
        if kind == "int":
            grp.append(hou.IntParmTemplate(name, label, 1, default_value=(d,), min=lo, max=hi))
        else:
            grp.append(hou.FloatParmTemplate(name, label, 1, default_value=(d,), min=lo, max=hi))
    controls.setParmTemplateGroup(grp)
    authored = [t.name() for t in controls.parmTemplateGroup().parmTemplates() if t.name() not in pre]
    pairs = promote.stage1_promote(controls, geo, authored)
    promote.stage1_wire(controls, pairs)

    grid = geo.createNode("grid", "tile_grid")
    grid.parm("orient").set(2)  # ZX plane, normal +Y
    grid.parm("sizex").setExpression('ch("../controls/tile_size")')
    grid.parm("sizey").setExpression('ch("../controls/tile_size")')
    grid.parm("rows").setExpression('ch("../controls/divisions")+1')
    grid.parm("cols").setExpression('ch("../controls/divisions")+1')
    # Grid is centred; shift so the tile origin is its min corner in global coords
    xf = geo.createNode("xform", "to_global")
    xf.setInput(0, grid)
    xf.parm("tx").setExpression('ch("../controls/tile_x") + ch("../controls/tile_size")*0.5')
    xf.parm("tz").setExpression('ch("../controls/tile_y") + ch("../controls/tile_size")*0.5')
    wr = geo.createNode("attribwrangle", "silk_field")
    wr.parm("class").set(2)  # points
    wr.parm("snippet").set(VEX)
    wr.setInput(0, xf)
    wr.setInput(1, controls)
    at = geo.createNode("attribwrangle", "unreal_attrs")   # N is analytic, set in silk_field (no Normal SOP)
    at.parm("class").set(1)
    at.parm("snippet").set(ATTR)
    at.setInput(0, wr)
    out = geo.createNode("output", "output0")
    out.setInput(0, at)
    out.setDisplayFlag(True)
    out.setRenderFlag(True)
    geo.layoutChildren()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    asset = geo.createDigitalAsset(name=TYPE_NAME, hda_file_name=str(out_path),
                                   description="Faraway Mother Silk Peak tile (BS_GodFile UE5.8)",
                                   min_num_inputs=0, max_num_inputs=0)
    promote.stage2_promote_definition(asset, pairs, out_path)
    MIRROR_OUT.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(out_path, MIRROR_OUT)
    print(f"[HDA] saved {out_path} ({out_path.stat().st_size} B), mirrored {MIRROR_OUT}")
    return 0


def verify(path: Path) -> int:
    import hou

    hou.hda.installFile(str(path))
    inst = hou.node("/obj").createNode(TYPE_NAME, "v_a")
    inst.parm("divisions").set(64)
    inst.cook(force=True)
    errs = inst.errors() + tuple(e for c in inst.allSubChildren() for e in c.errors())
    if errs:
        print("[Verify FAIL]", errs, file=sys.stderr)
        return 1
    g = inst.node("output0").geometry()
    if g is None:
        print('[Verify FAIL] output0 did not cook:', [e for c in inst.allSubChildren() for e in c.errors()], file=sys.stderr)
        return 1
    ys = [p.position()[1] for p in g.points()]
    print(f"[Verify] tile A: {len(g.points())} pts / {len(g.prims())} prims, height {min(ys):.1f}..{max(ys):.1f} m")
    up = sum(1 for pr in g.prims() if pr.normal()[1] > 0)
    print(f"[Verify] prims facing +Y: {up}/{len(g.prims())}")
    # G1-style border proof: tile B sits at +250 m in X; shared edge must match <= 0.01 m
    b = hou.node("/obj").createNode(TYPE_NAME, "v_b")
    b.parm("divisions").set(64)
    b.parm("tile_x").set(inst.parm("tile_x").eval() + 250.0)
    b.cook(force=True)
    gb = b.node("output0").geometry()
    ea = {round(p.position()[2], 2): p.position()[1] for p in g.points() if abs(p.position()[0] - 125.0) < 1e-3}
    eb = {round(p.position()[2], 2): p.position()[1] for p in gb.points() if abs(p.position()[0] - 125.0) < 1e-3}
    common = set(ea) & set(eb)
    worst = max(abs(ea[k] - eb[k]) for k in common) if common else 1e9
    print(f"[Verify] shared edge: {len(common)} samples, worst |dY| = {worst:.6f} m (limit 0.01)")
    bad = []
    if up < 0.99 * len(g.prims()):
        bad.append("faces not up")
    if len(common) < 60 or worst > 0.01:
        bad.append("border mismatch")
    if max(ys) - min(ys) < 10:
        bad.append("flat")
    h0 = max(ys)
    inst.parm("height_scale").set(180.0)
    inst.cook(force=True)
    h1 = max(p.position()[1] for p in inst.node("output0").geometry().points())
    print(f"[Verify] drive: height_scale 90->180 max {h0:.1f}->{h1:.1f}")
    if h1 <= h0 + 5:
        bad.append("height_scale did not drive")
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
