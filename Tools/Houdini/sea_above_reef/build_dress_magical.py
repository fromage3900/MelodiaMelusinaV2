"""PASS B v2 — magical layer, self-writing SOPs (no node wiring to break).

Each Python SOP generates geometry AND writes its own OBJ (both base and
variant) + a JSON fragment. main() assembles the manifest. Same math as v1.

  ridges  : fluff tufts along skirt-hem boundary loops
            -> magical_ridges.obj (+ FluffInflate offsets in JSON)
  scales  : hex plates on bodice faces (Cd hue bands)
            -> magical_scales.obj + magical_scales_flip.obj (ScaleFlip morph)

Run:  hython Tools/Houdini/sea_above_reef/build_dress_magical.py
"""

import json
from pathlib import Path

import hou

PROJECT_ROOT = Path(__file__).resolve().parents[3]
POSED_OBJ = (PROJECT_ROOT / "Saved/Audit/melusina_lookdev/magical/posed"
             / "shorewake_all_meshes.obj")
OUT_DIR = PROJECT_ROOT / "Saved/Audit/melusina_lookdev/magical"
SEED = 20260828

CODE = r"""
import hou, math, random, json, os

node = hou.pwd()
geo = node.geometry()
if geo.findPointAttrib("uv") is None:
    geo.addAttrib(hou.attribType.Point, "uv", (0.0, 0.0))
if geo.findPointAttrib("Cd") is None:
    geo.addAttrib(hou.attribType.Point, "Cd", (1.0, 1.0, 1.0))
V = hou.Vector3
MODE = __MODE__
OUT_DIR_S = __OUT_DIR_S__

def _frame(tan):
    tan = tan.normalized()
    up = V(0, 1, 0)
    if abs(tan.dot(up)) > 0.95:
        up = V(1, 0, 0)
    x = tan.cross(up).normalized()
    y = tan.cross(x).normalized()
    return x, y, tan

def write_obj(path, geo_ref):
    with open(path, "w") as f:
        for p in geo_ref.points():
            pos = p.position()
            f.write("v %.5f %.5f %.5f\n" % (pos.x(), pos.y(), pos.z()))
        for pr in geo_ref.prims():
            idx = [v.point().number() + 1 for v in pr.vertices()]
            f.write("f " + " ".join(str(i) for i in idx) + "\n")
"""
if True:
    CODE += r"""

def _plate(geo, cen, nrm, size, hue, cd):
    x, y, _t = _frame(nrm)
    cpt = geo.createPoint()
    cpt.setPosition(cen + nrm * (size * 0.15))
    cpt.setAttribValue(cd, (0.5 + 0.5 * math.sin(hue * 6.28),
                            0.5 + 0.5 * math.sin(hue * 6.28 + 2.1),
                            0.5 + 0.5 * math.sin(hue * 6.28 + 4.2)))
    rim = []
    for k in range(6):
        aa = k / 6.0 * 2.0 * math.pi
        p2 = geo.createPoint()
        p2.setPosition(cen + x * (math.cos(aa) * size) + y * (math.sin(aa) * size))
        p2.setAttribValue(cd, (0.5 + 0.5 * math.sin(hue * 6.28),
                               0.5 + 0.5 * math.sin(hue * 6.28 + 2.1),
                               0.5 + 0.5 * math.sin(hue * 6.28 + 4.2)))
        rim.append(p2)
    for k in range(6):
        f2 = geo.createPolygon()
        f2.addVertex(cpt)
        f2.addVertex(rim[k])
        f2.addVertex(rim[(k + 1) % 6])

def _tf(p, cen, nrm, spin, push):
    # ScaleFlip: spin the plate 180 deg about its normal and push along it
    rel = p - cen
    a = nrm.normalized()
    c = math.cos(spin); s = math.sin(spin)
    rel = rel * c + a.cross(rel) * s + a * (a.dot(rel) * (1.0 - c))
    return cen + rel + nrm * push

if MODE == "detect":
    pair_count = {}
    for f in geo.prims():
        vs = [v.point().number() for v in f.vertices()]
        for i in range(len(vs)):
            a, b = vs[i], vs[(i + 1) % len(vs)]
            key = (min(a, b), max(a, b))
            pair_count[key] = pair_count.get(key, 0) + 1
    boundary = [k for k, c in pair_count.items() if c == 1]
    adj = {}
    for (a, b) in boundary:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    seen = set()
    loops = []
    allpts = geo.points()
    for (a, b) in boundary:
        if (min(a, b), max(a, b)) in seen:
            continue
        loop = [a, b]
        seen.add((min(a, b), max(a, b)))
        for end_is_last in (True, False):
            while True:
                cur = loop[-1] if end_is_last else loop[0]
                nxts = [p for p in adj.get(cur, [])
                        if (min(cur, p), max(cur, p)) not in seen]
                if not nxts:
                    break
                nxt = nxts[0]
                seen.add((min(cur, nxt), max(cur, nxt)))
                if end_is_last:
                    loop.append(nxt)
                else:
                    loop.insert(0, nxt)
        if len(loop) >= 8:
            loops.append(loop)
    data = []
    for lp in loops:
        my = sum(allpts[i].position().y() for i in lp) / len(lp)
        data.append({"meanY": round(my, 4),
                     "points": [list(round(c, 4) for c in allpts[i].position())
                                for i in lp]})
    with open(os.path.join(OUT_DIR_S, "boundary_loops.json"), "w") as f:
        json.dump({"loops": data}, f)
    print(f"[magical] detect: {len(loops)} loops -> boundary_loops.json")

elif MODE == "ridges":
    loops = json.load(open(os.path.join(OUT_DIR_S, "boundary_loops.json")))["loops"]
    ymin = min(min(p[1] for p in lp["points"]) for lp in loops)
    ymax = max(max(p[1] for p in lp["points"]) for lp in loops)
    cut = ymin + (ymax - ymin) * 0.30
    hems = [lp for lp in loops
            if sum(p[1] for p in lp["points"]) / len(lp["points"]) < cut]
    print(f"[magical] ridges: {len(hems)} hem loops of {len(loops)}")
    tufts = 0
    inflate = []          # per-vertex inflate offset for the morph
    vert_base = 0
    for li, lp in enumerate(hems):
        pts = [V(*p) for p in lp["points"]]
        pts.append(pts[0])
        n = len(pts)
        for i in range(n - 1):
            a, b = pts[i], pts[i + 1]
            steps = max(2, int((b - a).length() / 0.14))
            for si in range(steps):
                p0 = a + (b - a) * (si / steps)
                radial = V(p0.x(), 0, p0.z())
                radial = radial.normalized() if radial.length() > 1e-4 else V(1, 0, 0)
                wob = 0.05 * math.sin(p0.y() * 9.0 + li * 2.0)
                base_r = 0.10 + 0.06 * math.sin(si * 1.7 + li)
                c0 = p0 + radial * (base_r + wob)
                for k in range(4):
                    aa = k / 4.0 * 2.0 * math.pi + si
                    tip = c0 + radial * (0.10 + 0.08 * math.sin(aa * 3.0)) \
                        + V(0, 0.05 * math.sin(aa * 5.0 + si), 0) \
                        + V(math.cos(aa) * 0.05, 0, math.sin(aa) * 0.05)
                    pp = geo.createPoint()
                    pp.setPosition(c0)
                    pt = geo.createPoint()
                    pt.setPosition(tip)
                    f = geo.createPolygon()
                    f.addVertex(pp)
                    f.addVertex(pt)
                    tufts += 1
                    inflate.append([radial.x() * 0.16, radial.y() * 0.04,
                                    radial.z() * 0.16, 0.0])
    try:
        geo.computeVertexNormals()
    except Exception:
        pass
    write_obj(os.path.join(OUT_DIR_S, "magical_ridges.obj"), geo)
    with open(os.path.join(OUT_DIR_S, "ridges_inflate.json"), "w") as f:
        json.dump({"inflate": inflate, "tufts": tufts}, f)
    print(f"[magical] ridges done: {tufts} tufts, "
          f"{len(geo.points())} pts -> magical_ridges.obj")

elif MODE == "scales":
    rng = random.Random(SEED + 77)
    faces = []
    for f in geo.prims():
        vs = [v.point() for v in f.vertices()]
        cen = sum((p.position() for p in vs), V(0, 0, 0)) / len(vs)
        faces.append((cen, f.normal()))
    ymin = min(c.y() for c, _n in faces)
    ymax = max(c.y() for c, _n in faces)
    band = ymin + (ymax - ymin) * 0.72
    plates = []
    cd = geo.findPointAttrib("Cd")
    for fi, (cen, nrm) in enumerate(faces):
        if cen.y() < band or fi % 8 != 0:
            continue
        size = 0.055 + 0.02 * math.sin(fi * 2.1)
        hue = ((cen.y() - band) / max(ymax - band, 1e-4) * 0.5
               + fi % 5 * 0.1) % 1.0
        x, y, _t = _frame(nrm)
        # scale flow: rotate the hex so a tip points along projected world-up
        up_proj = (V(0, 1, 0) - nrm * nrm.dot(V(0, 1, 0))).normalized()
        ang = math.atan2(y.dot(up_proj), x.dot(up_proj))
        x2 = x * math.cos(ang) + y * math.sin(ang)
        y2 = -x * math.sin(ang) + y * math.cos(ang)
        cpt = geo.createPoint()
        cpt.setPosition(cen + nrm * (size * 0.15))
        cpt.setAttribValue(cd, (0.5 + 0.5 * math.sin(hue * 6.28),
                                0.5 + 0.5 * math.sin(hue * 6.28 + 2.1),
                                0.5 + 0.5 * math.sin(hue * 6.28 + 4.2)))
        rim = []
        for k in range(6):
            aa = k / 6.0 * 2.0 * math.pi + ang
            p2 = geo.createPoint()
            p2.setPosition(cen + x2 * (math.cos(aa) * size) + y2 * (math.sin(aa) * size))
            p2.setAttribValue(cd, (0.5 + 0.5 * math.sin(hue * 6.28),
                                   0.5 + 0.5 * math.sin(hue * 6.28 + 2.1),
                                   0.5 + 0.5 * math.sin(hue * 6.28 + 4.2)))
            rim.append(p2)
        for k in range(6):
            f2 = geo.createPolygon()
            f2.addVertex(cpt)
            f2.addVertex(rim[k])
            f2.addVertex(rim[(k + 1) % 6])
        plates.append({"center": [round(cen.x(), 4), round(cen.y(), 4),
                                  round(cen.z(), 4)],
                       "normal": [round(nrm.x(), 4), round(nrm.y(), 4),
                                  round(nrm.z(), 4)],
                       "size": round(size, 4), "hue": round(hue, 4)})
    with open(os.path.join(OUT_DIR_S, "magical_scales.obj"), "w") as f:
        # strip the input passthrough: export ONLY the plate points/faces
        in_pts = len(node.inputs()[0].geometry().points()) \
            if node.inputs() and node.inputs()[0].geometry() else 0
        remap = {}
        for p in geo.points():
            if p.number() < in_pts:
                continue
            remap[p.number()] = len(remap)
            pos = p.position()
            f.write("v %.5f %.5f %.5f\n" % (pos.x(), pos.y(), pos.z()))
        for pr in geo.prims():
            idx = [remap.get(v.point().number(), -1) for v in pr.vertices()]
            if any(i < 0 for i in idx):
                continue                     # prim touches input geometry - skip
            f.write("f " + " ".join(str(i) for i in idx) + "\n")
    with open(os.path.join(OUT_DIR_S, "scales_plates.json"), "w") as f:
        json.dump({"plates": plates}, f)
    print(f"[magical] scales done: {len(plates)} plates, "
          f"{len(geo.points())} pts -> magical_scales.obj")
"""


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = hou.node("/obj")
    for old in [n for n in obj.children() if n.name() == "MAGICAL"]:
        old.destroy()
    g = obj.createNode("geo", "MAGICAL", run_init_scripts=True)

    fileread = g.createNode("file", "posed_read")
    fileread.parm("file").set(str(POSED_OBJ))

    steps = [
        ("detect", {"OUT_DIR_S": str(OUT_DIR).replace("\\", "/")}, fileread),
        ("ridges", {"OUT_DIR_S": str(OUT_DIR).replace("\\", "/")}, None),
        ("scales", {"OUT_DIR_S": str(OUT_DIR).replace("\\", "/")}, fileread),

    ]
    ok = {}
    for mode, params, input_node in steps:
        py = g.createNode("python", f"gen_{mode}")
        code = (_inject(CODE, MODE=mode, SEED=SEED, **params)
                .replace("random.Random(SEED + hash(MODE) % 997)",
                         f"random.Random({SEED} + hash(MODE) % 997)")
                .replace("random.Random(SEED + 77)",
                         f"random.Random({SEED} + 77)"))
        py.parm("python").set(code)
        if input_node is not None:
            py.setInput(0, input_node)
        if not _cook_report(py, mode):
            ok[mode] = False
            continue
        ok[mode] = True
        print(f"[magical] {mode}: {len(py.geometry().points())} pts")
    g.destroy()

    manifest = {"schema": "melodia.dress_magical.v2", "seed": SEED,
                "hython": hou.applicationVersionString(),
                "source": str(POSED_OBJ),
                "steps_ok": ok,
                "outputs": ["magical_ridges.obj (+ridges_inflate.json)",
                            "magical_scales.obj (+scales_plates.json)",
                            "boundary_loops.json"],
                "scale_flip_recipe": "Pass C mirrors each plate through its "
                                     "centre+normal (scales_plates.json) for the "
                                     "ScaleFlip morph target",
                "space": "owner rig space (Y-up)"}
    (OUT_DIR / "dress_magical_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[magical] manifest -> dress_magical_manifest.json steps_ok={ok}")


def _inject(code, **params):
    for key, value in params.items():
        code = code.replace(f"__{key}__", repr(value))
    return code


def _cook_report(py, tag):
    try:
        py.cook(force=True)
    except Exception:
        pass
    err = " ".join(str(py.errors()).split()) if py.errors() else ""
    if err:
        print(f"[magical] NODE ERROR [{tag}]: {err[:400]}")
        return False
    return True


if __name__ == "__main__":
    main()
