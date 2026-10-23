"""THE FARAWAY MOTHER — hero assets v0 (Bible #10, the money-shot monolith).

Three builds, one code file, all Apprentice-safe OBJ:

  SM_FM_MotherSilhouette  4 km reclined figure: the horizon form. NOT detailed
                          anatomy — a landform that READS as a reclined maternal
                          body (head dome, chin notch, shoulder, hip swell,
                          knees taper), fabric pleats draping across it, and a
                          whisper of a face profile. Built to sit on the far
                          horizon at constant apparent size (Beat E).
  SM_FM_EyeLandmark       the Blink (Beat H): a closed eye as a landform —
                          eyelid dome, iris striations beneath (64 radial
                          grooves), 33-filament lash fringe (Fibonacci). Reads
                          as a hill from afar, an eye from the air.
  SM_FM_Lantern           Melusina-scale lantern prop for the foreground of the
                          shot: 6-rib cage, glass core, hanging ring.

Deterministic (seed 20260829). Manifest records every constant + staging notes.

Outputs -> Saved/Audit/faraway_mother/heroes/

Run (isolated console):
  & "C:\\Program Files\\Side Effects Software\\Houdini 22.0.368\\bin\\hython.exe" ^
      Tools/Houdini/sea_above_reef/build_faraway_mother_heroes.py
"""

import json
import math
from pathlib import Path

import hou

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "Saved" / "Audit" / "faraway_mother" / "heroes"

SEED = 20260829
PHI = (1.0 + math.sqrt(5.0)) / 2.0

CODE = r"""
import hou, math, random

node = hou.pwd()
geo = node.geometry()
if geo.findPointAttrib("uv") is None:
    geo.addAttrib(hou.attribType.Point, "uv", (0.0, 0.0))

MODE = __MODE__
SEED = __SEED__
rng = random.Random(SEED)

LAT = 12
lat = [[rng.uniform(-1.0, 1.0) for _ in range(LAT + 1)] for _ in range(LAT + 1)]

def vnoise(u, v):
    fu, fv = u * LAT, v * LAT
    iu, iv = min(int(fu), LAT - 1), min(int(fv), LAT - 1)
    tu, tv = min(fu - iu, 1.0), min(fv - iv, 1.0)
    su = tu * tu * (3 - 2 * tu)
    sv = tv * tv * (3 - 2 * tv)
    a = lat[iv][iu] * (1 - su) + lat[iv][iu + 1] * su
    b = lat[iv + 1][iu] * (1 - su) + lat[iv + 1][iu + 1] * su
    return a * (1 - sv) + b * sv

def mother_silhouette():
    # 4000 m reclined figure ridge. x = along body (head at low x).
    LEN = 4000.0; DEPTH = 1300.0
    GRID_L, GRID_D = 512, 128
    head_x, shoulder_x, hip_x, knee_x = 0.12, 0.30, 0.58, 0.76
    def body_h(xn):
        h = 40.0
        h += 150.0 * math.exp(-(((xn - head_x) / 0.085) ** 2))       # head dome
        h -= 18.0 * math.exp(-(((xn - head_x - 0.055) / 0.02) ** 2)) # chin notch
        h += 95.0 * math.exp(-(((xn - shoulder_x) / 0.10) ** 2))     # shoulder
        h += 120.0 * math.exp(-(((xn - 0.44) / 0.11) ** 2))          # breast/ribcage
        h -= 34.0 * math.exp(-(((xn - 0.50) / 0.05) ** 2))           # waist
        h += 135.0 * math.exp(-(((xn - hip_x) / 0.12) ** 2))         # hip
        h += 80.0 * math.exp(-(((xn - knee_x) / 0.08) ** 2))         # knees
        return h
    def body_w(xn):
        w = 260.0
        w *= 0.45 + 0.55 * math.exp(-(((xn - head_x) / 0.16) ** 2))  # head narrows
        w = max(w, 90.0 + 180.0 * math.exp(-(((xn - 0.5) / 0.30) ** 2)))
        w *= 0.5 + 0.5 * math.exp(-(((xn - 0.97) / 0.10) ** 2))      # feet taper
        return w
    def face(xn, yn):
        # whisper of a profile on the head dome: brow / nose / lips (imply only)
        if abs(xn - head_x) > 0.06 or abs(yn - 0.5) > 0.045:
            return 0.0
        prof = 0.0
        prof += 7.0 * math.exp(-(((xn - (head_x + 0.028)) / 0.008) ** 2))   # nose
        prof += 4.0 * math.exp(-(((xn - (head_x + 0.048)) / 0.006) ** 2))   # lips
        prof -= 3.0 * math.exp(-(((xn - (head_x + 0.012)) / 0.006) ** 2))   # eye hollow
        return prof * math.exp(-(((yn - 0.5) / 0.03) ** 2))
    rows = []
    for j in range(GRID_D + 1):
        yn = j / GRID_D
        row = []
        for i in range(GRID_L + 1):
            xn = i / GRID_L
            across = (yn - 0.5) * 2.0
            w = body_w(xn)
            cross = math.exp(-((across * DEPTH / w) ** 2))
            h = 8.0 + body_h(xn) * cross
            # fabric pleats drape ACROSS the body, amplitude follows the slope
            pleat_env = 0.5 + 0.5 * vnoise(xn * 3.0 + 3.0, yn * 1.2)
            h += 9.0 * pleat_env * cross * abs(math.sin(yn * DEPTH / 46.0 * math.pi))
            h += 6.0 * vnoise(xn * 6.0, yn * 6.0) * cross
            h += face(xn, yn) * cross
            p = geo.createPoint()
            p.setPosition(hou.Vector3(xn * LEN - LEN * 0.5, h, (yn - 0.5) * DEPTH))
            p.setAttribValue(geo.findPointAttrib("uv"), (xn, yn))
            row.append(p)
        rows.append(row)
    for j in range(GRID_D):
        for i in range(GRID_L):
            f = geo.createPolygon()
            for q in (rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]):
                f.addVertex(q)

def eye_landmark():
    # a closed eye as a landform: eyelid dome + striated iris beneath + lashes
    LEN = 240.0; WID = 130.0; LID_H = 34.0
    GRID_L, GRID_W = 256, 128
    rows = []
    for j in range(GRID_W + 1):
        yn = j / GRID_W
        row = []
        for i in range(GRID_L + 1):
            xn = i / GRID_L
            across = (yn - 0.5) * 2.0
            # lid: soft dome peaking toward the outer third (the lid fold)
            lid = LID_H * math.exp(-(((xn - 0.5) / 0.34) ** 2)) * \
                math.cos(across * math.pi * 0.5) ** 1.5
            # brow ridge behind the lid
            brow = 14.0 * math.exp(-(((xn - 0.30) / 0.16) ** 2)) * \
                math.exp(-(((yn - 0.5) / 0.42) ** 2))
            # iris disc beneath the lid edge, 64 radial striations (mathematically perfect)
            iris_d = math.hypot((xn - 0.62) * LEN / 46.0, (yn - 0.5) * WID / 46.0)
            iris = 0.0
            if iris_d < 1.0:
                ang = math.atan2(yn - 0.5, xn - 0.62)
                iris = 2.6 * math.sin(ang * 64.0) * (1.0 - iris_d) \
                    - 3.2 * (1.0 - iris_d * iris_d)
            base = 6.0
            h = base + lid + brow + iris + 0.8 * vnoise(xn * 5.0, yn * 5.0)
            p = geo.createPoint()
            p.setPosition(hou.Vector3(xn * LEN - LEN * 0.5, h, (yn - 0.5) * WID))
            p.setAttribValue(geo.findPointAttrib("uv"), (xn, yn))
            row.append(p)
        rows.append(row)
    for j in range(GRID_W):
        for i in range(GRID_L):
            f = geo.createPolygon()
            for q in (rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]):
                f.addVertex(q)
    # 33 lash filaments (Fibonacci) along the lid edge
    N = 33
    for li in range(N):
        t = li / (N - 1)
        lx = 0.28 + 0.46 * t
        ly = 0.5 + 0.34 * math.sin(t * math.pi)
        a = rng.uniform(0, 6.28)
        llen = 16.0 + 7.0 * math.sin(t * math.pi)
        rows2 = []
        for s in range(25):
            ss = s / 24.0
            sway = math.sin(a * 2.0 + ss * 3.0) * 3.0 * ss
            w = 0.9 * (1.0 - 0.8 * ss)
            rr = []
            for k in range(3):
                u2 = k / 2.0 - 0.5
                p = geo.createPoint()
                p.setPosition(hou.Vector3(lx * LEN - LEN * 0.5 + sway,
                                          LID_H * 0.55 * math.exp(-(((lx - 0.5) / 0.34) ** 2)) + ss * llen * 0.35,
                                          (ly - 0.5) * WID + w * u2))
                p.setAttribValue(geo.findPointAttrib("uv"), (ss, k / 2.0))
                rr.append(p)
            rows2.append(rr)
        for s in range(24):
            for k in range(2):
                f = geo.createPolygon()
                for q in (rows2[s][k], rows2[s][k + 1], rows2[s + 1][k + 1], rows2[s + 1][k]):
                    f.addVertex(q)

def lantern():
    # Melusina-scale lantern: 6-rib cage, glass core, top cap + hanging ring
    H = 46.0; R = 13.0; RIBS = 6
    # glass core: hex prism (soft, translucent later)
    for ring, (rr, yy) in enumerate([(R * 0.8, 6.0), (R * 0.95, H * 0.5), (R * 0.8, H - 6.0)]):
        ring_pts = []
        for k in range(RIBS + 1):
            a = k / RIBS * 2.0 * math.pi
            p = geo.createPoint()
            p.setPosition(hou.Vector3(rr * math.cos(a), yy, rr * math.sin(a)))
            p.setAttribValue(geo.findPointAttrib("uv"), (k / RIBS, ring / 2.0))
            ring_pts.append(p)
        for k in range(RIBS):
            f = geo.createPolygon()
            for q in (ring_pts[k], ring_pts[k + 1]):
                f.addVertex(q)
    # ribs
    for k in range(RIBS):
        a = k / RIBS * 2.0 * math.pi
        prev = None
        for s in range(13):
            ss = s / 12.0
            rr = R * (0.7 + 0.45 * math.sin(ss * math.pi)) + 1.2
            y = ss * H
            p = geo.createPoint()
            p.setPosition(hou.Vector3(rr * math.cos(a), y, rr * math.sin(a)))
            if prev is not None:
                for sub in range(3):
                    f = geo.createPolygon()
                    f.addVertex(prev)
                    f.addVertex(p)
            prev = p
    # top cap + hanging ring
    cap = []
    for k in range(RIBS + 1):
        a = k / RIBS * 2.0 * math.pi
        p = geo.createPoint()
        p.setPosition(hou.Vector3(R * 0.55 * math.cos(a), H + 3.0, R * 0.55 * math.sin(a)))
        cap.append(p)
    apex = geo.createPoint()
    apex.setPosition(hou.Vector3(0, H + 9.0, 0))
    for k in range(RIBS):
        f = geo.createPolygon()
        f.addVertex(cap[k]); f.addVertex(cap[k + 1]); f.addVertex(apex)
    ring_pts = []
    for k in range(25):
        a = k / 24.0 * 2.0 * math.pi
        p = geo.createPoint()
        p.setPosition(hou.Vector3(4.5 * math.cos(a), H + 13.0, 4.5 * math.sin(a)))
        p.setAttribValue(geo.findPointAttrib("uv"), (k / 24.0, 0.0))
        ring_pts.append(p)
    for k in range(24):
        f = geo.createPolygon()
        f.addVertex(ring_pts[k]); f.addVertex(ring_pts[k + 1])

if MODE == "silhouette":
    mother_silhouette()
elif MODE == "eye":
    eye_landmark()
else:
    lantern()
try:
    geo.computeVertexNormals()
except Exception:
    pass
"""


def _inject(code, **params):
    for key, value in params.items():
        code = code.replace(f"__{key}__", repr(value))
    return code


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = hou.node("/obj")
    builds = [("silhouette", "SM_FM_MotherSilhouette"),
              ("eye", "SM_FM_EyeLandmark"),
              ("lantern", "SM_FM_Lantern")]
    entries = []
    for mode, name in builds:
        for old in [n for n in obj.children() if n.name() == name]:
            old.destroy()
        g = obj.createNode("geo", name, run_init_scripts=True)
        py = g.createNode("python", "gen")
        code = _inject(CODE, MODE=mode, SEED=SEED)
        py.parm("python").set(code)
        try:
            py.cook(force=True)
        except Exception:
            pass
        err = " ".join(str(py.errors()).split()) if py.errors() else ""
        if err:
            print(f"[fm] {name} NODE ERROR: {err[:300]}")
            g.destroy()
            continue
        geo = py.geometry()
        obj_path = OUT_DIR / f"{name}.obj"
        sop = g.createNode("file", "write_obj")
        sop.parm("file").set(str(obj_path))
        sop.parm("filemode").set("write")
        sop.setInput(0, py)
        try:
            sop.cook(force=True)
        except Exception:
            pass
        ok = obj_path.exists()
        entries.append({"asset": name, "obj": str(obj_path), "written": ok,
                        "bytes": obj_path.stat().st_size if ok else 0,
                        "points": len(geo.points()), "faces": len(geo.prims())})
        print(f"[fm] {name}: {len(geo.points())} pts / {len(geo.prims())} faces, obj={ok}")
        g.destroy()

    manifest = {
        "schema": "melodia.faraway_mother_terrain.v1",
        "kind": "Faraway Mother hero assets v0 (money-shot set)",
        "seed": SEED,
        "assets": entries,
        "staging_notes": {
            "MotherSilhouette": "far horizon card: place ~6-9 km out, scale constant via "
                                "level-scripted offset (Bible Beat E: no parallax); fog + "
                                "moonlight occlusion only, never model more anatomy",
            "EyeLandmark": "Beat H reveal site: reads as a hill from ground level, an eye "
                           "from the air; iris striations are 64-fold — the 'mathematically "
                           "perfect yet strange' register",
            "Lantern": "Melusina-scale foreground prop; glass core expects a translucent MI "
                       "(LanternGlass pattern), warm emissive for the shot",
        },
        "hython": hou.applicationVersionString(),
        "ue_import": {"scale": "100x (m -> cm)", "nanite": True,
                      "note": "silhouette imports at 100x; consider import scale 25-40x "
                              "if placed via level instead"},
        "bible_source": "MONOLITH_LEVEL_DESIGN_BIBLE_2026-08-26.md #10",
    }
    (OUT_DIR / "faraway_mother_heroes_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print("[fm] manifest -> faraway_mother_heroes_manifest.json")


if __name__ == "__main__":
    main()
