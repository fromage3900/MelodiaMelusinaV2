"""Sir Melodious Vellum clothes bake v2 (hython, headless, staging only).

v1 failed on scale: the scene is centimetre-native (bird ~80 units wide) and
Vellum's default mass/stiffness/gravity relationships assume a METRE scene.
Measured symptom: the 20,736-pt collar stretched ~6x and formed a huge loop
(the 344-pt tie settled plausibly). v2 converts the sim to metres
(scale 0.01), uses -9.81 m/s^2 gravity, and scales the cache back to cm on
write so downstream stages see the same space as the FBX.

Gravity axis (measured, not guessed): head.x centroid z=+30.1 cm, feet
z=-2.5 cm -> character up = +Z, so gravity = -Z. Tie hangs knot z=+17.8 ->
tip z=+8.7, same -Z.

Pieces:
  CLOTH 0  sirmelodious_Retopo_PM3D_Cube3D1_002   tie, 344 pts (cc_tie_*)
  CLOTH 1  sirmelodious_B__zierCurve_002          collar/ruffles, 20736 pts
  COLLIDER SirMelodiousBody (+ crest)             3892+2344 pts

Pins: per piece, points within the closest-N quantile (default 0.20) by
distance to the collider are pinned hard. Thresholds measured + reported.

Output: bgeo.sc sequence + vellum_bake_report.json under
Saved/Audit/sirmelodious_kinefx_doctor/vellum/. Nothing in Content/ touched.

  hython Tools/Houdini/sir_kinefx/sir_vellum_clothes_bake.py -- \
      --frames 48 --pin-q 0.20 [--wind 0]
"""
import argparse
import json
import os
import sys
import time

import hou

REPO = "C:/EnvironmentPortfolio/BS_GodFile"
AUDIT = REPO + "/Saved/Audit/SirMelodious_FlightUnit_20261003"
FBX = AUDIT + "/exports/ue_arp/SKM_SirMelodious_ARP_CrestTie_v5_tailfix.fbx"
OUT = REPO + "/Saved/Audit/sirmelodious_kinefx_doctor/vellum"

CLOTH = ("sirmelodious_Retopo_PM3D_Cube3D1_002",
         "sirmelodious_B__zierCurve_002")
COLLIDER = ("SirMelodiousBody", "sirmelodious_Crest")
SCALE = 0.01          # cm -> m for the sim; 100 back on write
FPS = 24
GRAVITY_M = -9.80665  # on -Z


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames", type=int, default=48)
    ap.add_argument("--pin-q", type=float, default=0.20)
    ap.add_argument("--wind", type=float, default=0.0,
                    help="wind speed in m/s (0 = settle only)")
    ap.add_argument("--thickness", type=float, default=0.0005,
                    help="cloth thickness in metres (min mesh edge is 0.67mm)")
    ap.add_argument("--niter", type=int, default=100)
    ap.add_argument("--substeps", type=int, default=5)
    ap.add_argument("--suffix", type=str, default="v3")
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = [a for a in argv[1:] if a.startswith("-")]
    return ap.parse_args(argv)


def bbox_pair(geo):
    bb = geo.boundingBox()
    return ([round(v, 3) for v in bb.minvec()],
            [round(v, 3) for v in bb.maxvec()])


def main():
    args = parse_args()
    frames = args.frames

    os.makedirs(OUT, exist_ok=True)
    report = {"schema": "melodia.sir_vellum_clothes." + args.suffix,
              "fbx": FBX, "frames": frames, "fps": FPS,
              "cloth": list(CLOTH), "colliders": list(COLLIDER),
              "scale": SCALE, "gravity_m_s2": GRAVITY_M,
              "pin_quantile": args.pin_q, "wind_m_s": args.wind}

    hou.hipFile.clear(suppress_save_prompt=True)
    hou.setFps(FPS)
    hou.hipFile.importFBX(FBX)
    obj = hou.node("/obj")
    sub = [c for c in obj.children() if c.type().name() == "subnet"][0]

    def src(name):
        return sub.node(name).displayNode().path()

    geo = obj.createNode("geo", "sir_vellum_clothes")

    cloth_mg = geo.createNode("merge", "cloth")
    for i, name in enumerate(CLOTH):
        om = geo.createNode("object_merge", "om_cloth_%d" % i)
        om.parm("objpath1").set(src(name))
        pid = geo.createNode("attribwrangle", "pid_%d" % i)
        pid.setInput(0, om)
        pid.parm("snippet").set("i@pieceid = %d;\n" % i)
        cloth_mg.setInput(i, pid)
    cloth_xf = geo.createNode("xform", "cloth_scale")
    cloth_xf.setInput(0, cloth_mg)
    cloth_xf.parm("scale").set(SCALE)

    coll_mg = geo.createNode("merge", "collider")
    for i, name in enumerate(COLLIDER):
        om = geo.createNode("object_merge", "om_coll_%d" % i)
        om.parm("objpath1").set(src(name))
        coll_mg.setInput(i, om)
    coll_xf = geo.createNode("xform", "coll_scale")
    coll_xf.setInput(0, coll_mg)
    coll_xf.parm("scale").set(SCALE)

    pin = geo.createNode("attribwrangle", "pins")
    pin.setInput(0, cloth_xf)
    pin.setInput(1, coll_xf)

    def snippet(thr0, thr1):
        return (
            "float d = 1e9;\n"
            "int pts[] = pcfind(1, \"P\", @P, 1e9, 4);\n"
            "foreach (int p; pts) {\n"
            "    float dd = distance(@P, point(1, \"P\", p));\n"
            "    if (dd < d) d = dd;\n"
            "}\n"
            "f@dbd = d;\n"
            "float thr = (i@pieceid == 0) ? %.8f : %.8f;\n"
            "if (d <= thr) setpointgroup(0, \"pins\", @ptnum, 1);\n"
            % (thr0, thr1))

    pin.parm("snippet").set(snippet(1e9, 1e9))
    g = pin.geometry()
    per_piece = {}
    for p in g.points():
        pid = p.attribValue("pieceid")
        per_piece.setdefault(pid, []).append(p.attribValue("dbd"))
    thrs = {}
    for pid, dists in sorted(per_piece.items()):
        dists.sort()
        idx = max(0, min(len(dists) - 1, int(len(dists) * args.pin_q)))
        thrs[pid] = dists[idx]
    report["pin_threshold_m"] = {str(k): round(v, 6) for k, v in thrs.items()}
    report["piece_points"] = {str(k): len(v) for k, v in per_piece.items()}

    pin.parm("snippet").set(snippet(thrs.get(0, 0.005), thrs.get(1, 0.005)))
    g = pin.geometry()
    pinned = {}
    for p in g.points():
        if p.attribValue("dbd") <= thrs.get(p.attribValue("pieceid"), 0.0):
            k = str(p.attribValue("pieceid"))
            pinned[k] = pinned.get(k, 0) + 1
    report["pinned"] = pinned
    report["cloth_bbox_m"] = bbox_pair(g)
    report["cloth_points"] = len(g.points())

    con = geo.createNode("vellumconstraints", "constraints")
    con.setInput(0, pin)
    con.parm("constrainttype").set("cloth")
    con.parm("pingroup").set("pins")
    con.parm("dothickness").set("on")
    con.parm("thickness").set(args.thickness)

    solver = geo.createNode("vellumsolver", "solver")
    solver.setInput(0, con, 0)
    solver.setInput(1, con, 1)
    solver.setInput(2, coll_xf)
    solver.parm("startframe").set(1)
    solver.parm("enablecollisions").set(1)
    solver.parm("gravityx").set(0.0)
    solver.parm("gravityy").set(0.0)
    solver.parm("gravityz").set(GRAVITY_M)
    solver.parm("dosubstep").set(1)
    solver.parm("substeps").set(args.substeps)
    solver.parm("niter").set(args.niter)
    solver.parm("thickness").set(args.thickness)
    solver.parm("dowind").set(1 if args.wind > 0 else 0)
    solver.parm("windx").set(0.0)
    solver.parm("windy").set(0.0)
    solver.parm("windz").set(-1.0)
    solver.parm("windspeed").set(args.wind)

    # scale the cache back to centimetres so downstream stages and the proof
    # renders see the same space as the FBX (cm-native)
    back = geo.createNode("xform", "back_to_cm")
    back.setInput(0, solver)
    back.parm("scale").set(1.0 / SCALE)
    geo.layoutChildren()

    hou.playbar.setFrameRange(1, frames)
    hou.playbar.setPlaybackRange(1, frames)

    t0 = time.time()
    out = hou.node("/out")
    rop = None
    for tname in ("geometry", "rop_geometry"):
        try:
            rop = out.createNode(tname, "sir_vellum_bake")
            break
        except Exception:
            continue
    if rop is None:
        raise RuntimeError("no geometry ROP type available")
    rop.parm("soppath").set(back.path())
    rop.parm("sopoutput").set(OUT + "/sir_clothes_" + args.suffix + ".$F4.bgeo.sc")
    rop.parm("trange").set(1)
    rop.parm("f1").set(1)
    rop.parm("f2").set(frames)
    rop.parm("f3").set(1)
    rop.render()
    report["bake_seconds"] = round(time.time() - t0, 1)

    files = sorted(f for f in os.listdir(OUT) if f.startswith("sir_clothes_" + args.suffix + "."))
    report["cache_files"] = len(files)
    report["first"] = files[0] if files else None
    report["last"] = files[-1] if files else None
    report["cache_mb"] = round(sum(
        os.path.getsize(os.path.join(OUT, f)) for f in files) / 1e6, 2)

    # --- verification (all in sim space, metres) --------------------------------
    try:
        rd = geo.createNode("file", "verify_read")
        if files:
            rd.parm("file").set(OUT + "/sir_clothes_" + args.suffix + ".0001.bgeo.sc")
            g1 = rd.geometry()
            p1 = {p.number(): p.position() for p in g1.points()}
            e1 = {}
            for pr in g1.prims():
                vs = [v.point().number() for v in pr.vertices()]
                for i in range(len(vs)):
                    a, b = vs[i], vs[(i + 1) % len(vs)]
                    e1[(min(a, b), max(a, b))] = (
                        p1[a] - p1[b]).length()
            rd.parm("file").set(
                OUT + "/sir_clothes_" + args.suffix + ".%04d.bgeo.sc" % frames)
            gl = rd.geometry()
            pl = {p.number(): p.position() for p in gl.points()}
            ds = [(pl[i] - p1[i]).length()
                  for i in p1 if i in pl]
            stretch = 0.0
            stretch_mm = 0.0
            n_mm = 0
            over_mm = 0
            for pr in gl.prims():
                vs = [v.point().number() for v in pr.vertices()]
                for i in range(len(vs)):
                    a, b = vs[i], vs[(i + 1) % len(vs)]
                    key = (min(a, b), max(a, b))
                    if key in e1 and e1[key] > 1e-9:
                        r = (pl[a] - pl[b]).length() / e1[key]
                        stretch = max(stretch, r)
                        if e1[key] >= 0.1:  # cm: >= 1 mm real edge
                            n_mm += 1
                            if r > 1.5:
                                over_mm += 1
                            stretch_mm = max(stretch_mm, r)
            data = {"f1_points": len(p1), "f_last_points": len(pl)}
            if ds:
                # cache is back in cm (back_to_cm xform), so ds is already cm
                data["disp_max_cm"] = round(max(ds), 3)
                data["disp_mean_cm"] = round(sum(ds) / len(ds), 3)
            data["max_edge_stretch_ratio_all"] = round(stretch, 3)
            data["max_edge_stretch_ratio_mm_plus"] = round(stretch_mm, 3)
            data["mm_plus_edges"] = n_mm
            data["mm_plus_edges_over_1_5x"] = over_mm
            # pass gate: no real (>=1mm) edge stretched beyond 1.5x
            data["pass"] = over_mm == 0
            report["verify"] = data
    except Exception as exc:
        report["verify_error"] = str(exc)[-500:]

    json.dump(report, open(OUT + "/vellum_bake_report.json", "w"), indent=1)
    print("VELLUM " + json.dumps({k: report.get(k) for k in
                                  ("cache_files", "cache_mb", "pinned",
                                   "pin_threshold_m", "verify")}))


if __name__ == "__main__":
    main()
