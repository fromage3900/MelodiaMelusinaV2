"""Meadow health field cook for L_MelusinaMorning (hython).

Usage: hython morning_meadow_field.py [--seed 3900] [--out recipes/houdini_field] [--name morning_meadow_field]
Builds /obj/meadow_field (python SOP -> 5 attribute wrangles), reads point attrs back, writes CSV/JSON/hipnc/PNG.
"""
import argparse, csv, hashlib, json, os, sys
import hou

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
PROBE_REL = "recipes/ground/morning_rainbow_bloom_ground_probe.json"
N = 49
POND = (-950.0, 2300.0, 380.0)
HERO = (-2560.0, 1250.0)
BED = (900.0, 2300.0, 1100.0)

# Probe rows are x-major (x outer, y inner): point number = ix*49 + iy.
BUILD_PY = """
import json, hou
node = hou.pwd(); geo = node.geometry()
d = json.load(open(node.userData("probe")))
for n in ("ix", "iy", "soil"):
    geo.addAttrib(hou.attribType.Point, n, 0)
geo.addAttrib(hou.attribType.Point, "zc", 0.0)
for i, (x, y, z, lab, cls) in enumerate(d["rows"]):
    p = geo.createPoint()
    p.setPosition((x, y, 0.0))
    p.setAttribValue("ix", i // 49)
    p.setAttribValue("iy", i % 49)
    soil = 1 if (z is not None and lab and lab.startswith("BrushifyIsland_")) else 0
    p.setAttribValue("soil", soil)
    p.setAttribValue("zc", float(z) if z is not None else 0.0)
"""

VEX_SLOPE = r'''
// neighbours by point number (ix*49+iy); non-soil/out-of-range neighbours fall back to own z
float z0 = f@zc;
float zn[];
int dix[] = {1,-1,0,0};
int diy[] = {0,0,1,-1};
foreach (int k; int d; dix) {
    int jx = i@ix + dix[k];
    int jy = i@iy + diy[k];
    float zz = z0;
    if (jx >= 0 && jx < 49 && jy >= 0 && jy < 49) {
        int pn = jx*49 + jy;
        if (point(0, "soil", pn) == 1) zz = point(0, "zc", pn);
    }
    append(zn, zz);
}
float step = 100.0;
float gx = (zn[0]-zn[1])/(2.0*step);
float gy = (zn[2]-zn[3])/(2.0*step);
float grad = sqrt(gx*gx + gy*gy);
f@slope = clamp(grad/1.0, 0, 1) * i@soil;
f@lapcm = (zn[0]+zn[1]+zn[2]+zn[3]-4.0*z0);
'''
VEX_CONC = r'''
f@concavity = clamp(0.5 + f@lapcm*0.01, 0, 1) * i@soil;
'''
VEX_MOIST = r'''
vector2 pond = set(-950.0, 2300.0);
float dpond = distance(set(@P.x, @P.y), pond);
float seed = chf("seed");
vector q = @P*0.0009 + set(seed*0.137, seed*0.291, seed*0.053);
float fbm = 0.5*noise(q) + 0.25*noise(q*2.0+11.7) + 0.125*noise(q*4.0+23.1);
fbm /= 0.875;
float m = exp(-dpond/1500.0) + 0.35*fbm + 0.25*f@concavity;
f@moisture = clamp(m, 0, 1) * i@soil;
'''
VEX_HEALTH = r'''
vector2 xy = set(@P.x, @P.y);
float dpond = distance(xy, set(-950.0, 2300.0));
float dhero = distance(xy, set(-2560.0, 1250.0));
float dbed  = distance(xy, set(900.0, 2300.0));
float hero_boost = exp(-dhero/900.0);
float h = 0.30 + 0.55*f@moisture - 0.85*max(0, f@slope-0.35) + 0.20*hero_boost;
h = clamp(h, 0, 1) * i@soil;
if (dbed < 1100.0 || dpond < 380.0) h = 0;
f@health = h;
'''
VEX_TUFT = r'''
float seed = chf("seed");
vector q = @P*0.0031 + set(seed*0.719 + 101.3, seed*0.331 + 57.9, seed*0.113 + 9.1);
f@tuft = clamp(noise(q), 0, 1);
'''


def build(seed, probe_path, hip_path):
    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "meadow_field")
    for c in geo.children():
        c.destroy()
    py = geo.createNode("python", "probe_points")
    py.setUserData("probe", probe_path)
    py.parm("python").set(BUILD_PY)
    prev = py
    for name, code in (("slope", VEX_SLOPE), ("concavity", VEX_CONC), ("moisture", VEX_MOIST),
                       ("health", VEX_HEALTH), ("tuft", VEX_TUFT)):
        w = geo.createNode("attribwrangle", "vex_" + name)
        w.setInput(0, prev)
        w.parm("class").set(2)  # 0=detail,1=prim,2=point
        w.parm("snippet").set(code)
        if 'chf("seed")' in code:
            t = w.parmTemplateGroup()
            t.append(hou.FloatParmTemplate("seed", "Seed", 1, default_value=(float(seed),)))
            w.setParmTemplateGroup(t)
            w.parm("seed").set(float(seed))
        prev = w
    prev.setDisplayFlag(True)
    prev.setRenderFlag(True)
    geo.layoutChildren()
    hou.hipFile.save(hip_path)
    return prev


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=3900)
    ap.add_argument("--out", default=os.path.join(ROOT, "recipes", "houdini_field"))
    ap.add_argument("--name", default="morning_meadow_field")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    probe = os.path.join(ROOT, PROBE_REL)
    raw = open(probe, "rb").read()
    sha = hashlib.sha256(raw).hexdigest()
    d = json.loads(raw)
    assert len(d["rows"]) == N * N
    hip = os.path.join(a.out, a.name + ".hipnc").replace("\\", "/")
    sink = build(a.seed, probe.replace("\\", "/"), hip)
    g = sink.geometry()
    errs = [(n.path(), n.errors()) for n in sink.inputAncestors() if n.errors()]
    if sink.errors():
        errs.append((sink.path(), sink.errors()))
    if errs:
        print("COOK ERRORS", errs)
        sys.exit(2)
    ints = ("ix", "iy", "soil")
    names = ["ix", "iy", "soil", "slope", "concavity", "moisture", "health", "tuft"]
    cols = {n: (g.pointIntAttribValues(n) if n in ints else g.pointFloatAttribValues(n)) for n in names}
    rows = d["rows"]
    xs = sorted({r[0] for r in rows})
    ys = sorted({r[1] for r in rows})
    out = []
    for i, r in enumerate(rows):
        ix, iy = cols["ix"][i], cols["iy"][i]
        assert xs[ix] == r[0] and ys[iy] == r[1], "lattice ordering mismatch"
        out.append((ix, iy, r[0], r[1], r[2], cols["soil"][i], cols["slope"][i], cols["concavity"][i],
                    cols["moisture"][i], cols["health"][i], cols["tuft"][i]))
    csv_path = os.path.join(a.out, a.name + ".csv")
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow("ix,iy,x,y,z,soil,slope,concavity,moisture,health,tuft".split(","))
        for ix, iy, x, y, z, soil, sl, co, mo, he, tu in out:
            w.writerow([ix, iy, "%.4f" % x, "%.4f" % y, "" if z is None else "%.4f" % z, soil,
                        "%.4f" % sl, "%.4f" % co, "%.4f" % mo, "%.4f" % he, "%.4f" % tu])
    soilrows = [o for o in out if o[5] == 1]
    stats = {}
    for nm, idx in (("slope", 6), ("concavity", 7), ("moisture", 8), ("health", 9), ("tuft", 10)):
        v = [o[idx] for o in soilrows]
        stats[nm] = {"min": min(v), "max": max(v), "mean": sum(v) / len(v)}
    zs = [o[4] for o in soilrows]
    stats["z_cm"] = {"min": min(zs), "max": max(zs), "mean": sum(zs) / len(zs)}
    js = {
        "schema": "melodia.houdini_field.v1",
        "source_probe": PROBE_REL, "source_probe_sha256": sha, "seed": a.seed,
        "lattice": {"nx": N, "ny": N, "step_cm": d["step_cm"], "center_cm": d["center_cm"],
                    "row_order": "point = ix*49+iy; ix indexes x, iy indexes y"},
        "houdini": {"version": hou.applicationVersionString(), "license_category": str(hou.licenseCategory()),
                    "note": "Apprentice/non-commercial; scene saved as .hipnc"},
        "world_sources_cm": {"pond": {"center": list(POND[:2]), "radius": POND[2]}, "hero": list(HERO),
                             "bedroom_keepout": {"center": list(BED[:2]), "radius": BED[2]}},
        "soil_cells": len(soilrows), "health_gt_0_5": sum(1 for o in soilrows if o[9] > 0.5),
        "channel_stats_over_soil": stats,
        "vex": {"slope": VEX_SLOPE, "concavity": VEX_CONC, "moisture": VEX_MOIST,
                "health": VEX_HEALTH, "tuft": VEX_TUFT},
        "hip_file": "recipes/houdini_field/" + a.name + ".hipnc",
        "csv_file": "recipes/houdini_field/" + a.name + ".csv",
    }
    json.dump(js, open(os.path.join(a.out, a.name + ".json"), "w"), indent=2)
    try:
        import numpy as np
        from PIL import Image
        for nm, idx in (("health", 9), ("moisture", 8)):
            img = np.zeros((N, N, 3), dtype=np.uint8)
            for o in out:
                ix, iy = o[0], o[1]
                row = N - 1 - iy
                if o[5] == 0:
                    img[row, ix] = (30, 30, 40)
                else:
                    v = o[idx]
                    if nm == "health":
                        img[row, ix] = (int(200 * (1 - v)), int(60 + 195 * v), int(40 + 40 * v))
                    else:
                        img[row, ix] = (int(40 * (1 - v)), int(80 + 100 * v), int(120 + 135 * v))
            Image.fromarray(img).resize((N * 8, N * 8), Image.NEAREST).save(
                os.path.join(a.out, a.name + "_%s.png" % nm))
    except ImportError as e:
        print("PNG preview skipped:", e)
    print("OK seed=%d soil=%d health>0.5=%d" % (a.seed, len(soilrows), js["health_gt_0_5"]))
    print(json.dumps(stats))


main()
