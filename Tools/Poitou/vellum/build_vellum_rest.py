"""Vellum rest-geo + bake scaffold (headless). Builds rest geometry with
pin groups and a solver chain whose constraint details are REVIEW-marked
for GUI tuning at college. Rest branch fully cooks headless; the solver
chain is validated for node-type existence only.
Pieces: barque tillet canopy, Seventh-day garland rope, lockhouse awning.
Units: metres. Rest built at ORIGIN in local space; placement offsets to
the lock site are documented per-piece for UE-side instancing.
"""
import hou
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = HERE  # the hip + rest live beside this builder, in Tools/Poitou/vellum/
os.makedirs(OUTDIR, exist_ok=True)

hou.hipFile.clear(suppress_save_prompt=True)
obj = hou.node("/obj")
G = obj.createNode("geo", "vellum_rest")

def grid(name, sx, sy, nx, ny, y=0.0):
    n = G.createNode("grid", name)
    n.parm("sizex").set(sx)
    n.parm("sizey").set(sy)
    n.parm("rows").set(ny)
    n.parm("cols").set(nx)
    n.parm("ty").set(y)
    return n

def wrangle(name, code, cls=1, inputs=()):
    w = G.createNode("attribwrangle", name)
    w.parm("class").set(cls)
    w.parm("snippet").set(code)
    for i, n in enumerate(inputs):
        w.setInput(i, n)
    return w

def grp_expr(name, expr, src):
    n = G.createNode("groupexpression", name)
    gname = name.replace("grp_", "")
    # H22 Group Expression uses numbered snippet rows
    n.parm("groupname1").set(gname)
    n.parm("snippet1").set(expr)
    try:
        n.parm("grouptype").set(1)  # point groups
    except Exception:
        pass
    n.setInput(0, src)
    return n

def null(name, src):
    n = G.createNode("null", name)
    n.setInput(0, src)
    return n

report = {"pieces": {}, "solver_nodes": {}}

# ---- 1. TILLET canopy: linen over barque hoops -------------------------
# Local frame: x = barque axis (4.6 m hull), y up, z athwart.
# Panel 4.8 x 1.8 at deck +1.2; pinned along both long edges (gunwales);
# hoops (visualised as resampled arcs) lift the middle in-GUI.
tillet = grid("tillet_panel", 4.8, 1.8, 24, 8, y=1.2)
tillet_pin = grp_expr("grp_pin_gunwale",
                      "@uv.x<0.03 || @uv.x>0.97", tillet)
tillet_out = null("OUT_tillet", tillet_pin)
report["pieces"]["tillet"] = {
    "panel": "4.8 x 1.8 m, 24x8, at y=1.2 (barque axis = x)",
    "pin": "long edges @uv.x (gunwales); hoops to be placed in-GUI at x=-1.5,0,1.5, r=1.1",
    "placement": "barque mooring: lock tail jetty, deck +1.2; instance via CANOE placeholder lane",
}

# ---- 2. GARLAND rope: 6 m catenary, ends pinned -------------------------
# Built procedurally (proven point-list addprim): 49 pts, 48 segs, 0.8 sag.
rope = wrangle("garland_rope", r"""
int NSEG = 48;
float span = 6.0, sag = 0.8;
int pts[];
resize(pts, NSEG+1);
for(int k=0;k<=NSEG;k++){
    float t = float(k)/float(NSEG);
    pts[k] = addpoint(0, set(lerp(0.0,span,t), -sag*sin(3.14159*t), 0.0));
}
for(int k=0;k<NSEG;k++){
    int pr = addprim(0, "polyline", pts[k], pts[k+1]);
}
""", 0, [])
rope_pin = grp_expr("grp_pin_rope_ends", "@ptnum==0 || @ptnum==npoints(0)-1",
                    rope)
rope_out = null("OUT_garland", rope_pin)
report["pieces"]["garland"] = {
    "rope": "6 m span, 48 segments, 0.8 sag (Seventh-day strand)",
    "pin": "both ends; mid hangs free",
    "placement": "chamber span or jetty posts; leaves/knots ride as VEX boxes (lock.vex) OR second sim",
}

# ---- 3. AWNING: lockhouse eave panel, top edge pinned -------------------
awn = grid("awning_panel", 7.2, 1.5, 24, 6, y=0.0)
tilt = G.createNode("xform", "awning_tilt")
tilt.parm("rx").set(-15)
tilt.setInput(0, awn)
awn_pin = grp_expr("grp_pin_eave", "@uv.y>0.97", tilt)
awn_out = null("OUT_awning", awn_pin)
report["pieces"]["awning"] = {
    "panel": "7.2 x 1.5 m, 24x6, tilted -15 deg",
    "pin": "top edge @uv.y (eave line); belly falls free",
    "placement": "lockhouse front eave (hy+hh line), 5 doily squares are the VEX counterpart",
}

# ---- solver chain scaffold (REVIEW in GUI) -------------------------------
# One cloth+pin constraint pair per piece into a solver with wind.
# Parm names below are set defensively: only parms that exist are touched.
chain = {}
for piece, src, pin_grp in (("tillet", tillet_out, "pin_gunwale"),
                            ("garland", rope_out, "pin_rope_ends"),
                            ("awning", awn_out, "pin_eave")):
    cc = G.createNode("vellumconstraints", "%s_cloth" % piece)
    chain["%s_cloth" % piece] = cc.type().name()
    cp = G.createNode("vellumconstraints", "%s_pin" % piece)
    chain["%s_pin" % piece] = cp.type().name()
    mg = G.createNode("merge", "%s_constraints" % piece)
    mg.setInput(0, cc)
    mg.setInput(1, cp)
    cc.setInput(0, src)
    cp.setInput(0, src)
    # defensive parm sets (REVIEW: tune in GUI)
    for n, want in ((cc, {"group": "nouvelle", "type": 0}),
                    (cp, {"group": pin_grp, "type": 1})):
        for pname, val in want.items():
            try:
                prm = n.parm(pname)
                if prm is not None:
                    if isinstance(val, str) and val == "nouvelle":
                        continue
                    prm.set(val)
            except Exception:
                pass
report["solver_nodes"] = chain
report["solver_review"] = ("stiffness/bend/damping/substeps/wind left at "
                           "defaults - tune eyes-on at college; pin groups "
                           "are baked into rest geo")

report["wind"] = ("GUI step: fan wind 0.3 m/s from the marsh (+x) - "
                   "add in DOPs or a velocity volume at college")
solver = G.createNode("vellumsolver", "vellum_bake_solver")
try:
    if solver.parm("substeps") is not None:
        solver.parm("substeps").set(5)
except Exception:
    pass
report["solver"] = solver.type().name()

G.layoutChildren()
hip = os.path.join(OUTDIR, "vellum_bake.hiplc").replace("\\", "/")
hou.hipFile.save(hip)
report["hip"] = hip

# ---- headless gate: rest cooks, groups exist, nodes valid ---------------
checks = []
def check(name, ok, detail=""):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)[:140]})
    return ok
ok_all = True
for piece, outn, exp_pts, exp_grp in (
        ("tillet", tillet_out, 192, "pin_gunwale"),
        ("garland", rope_out, 49, "pin_rope_ends"),
        ("awning", awn_out, 144, "pin_eave")):
    g = outn.geometry()
    if g is None:
        ok_all &= check("rest_%s" % piece, False, "no geometry")
        continue
    npt = len(g.points())
    has_grp = g.findPointGroup(exp_grp) is not None
    exp_ok = (exp_pts is None) or (npt == exp_pts)
    ok_all &= check("rest_%s" % piece, has_grp and exp_ok,
                    "%d pts pin=%s" % (npt, has_grp))
for label, tname in (("constraints", "vellumconstraints"),
                     ("solver", "vellumsolver")):
    try:
        cat = {"vellumconstraints": hou.sopNodeTypeCategory(),
               "vellumsolver": hou.sopNodeTypeCategory()}[tname]
        ok_all &= check("node_%s" % label,
                        hou.nodeType(cat, tname) is not None, tname)
    except Exception as exc:
        ok_all &= check("node_%s" % label, False, str(exc)[:100])
report["checks"] = checks
report["pass"] = bool(ok_all)
print("VELLUM_SCAFFOLD " + ("PASS" if ok_all else "FAIL"))
import json as _j
print(_j.dumps(report, indent=1)[:4000])
