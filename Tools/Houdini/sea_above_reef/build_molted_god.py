"""THE GOD THAT MOLTS — shell-recursion kit generator (Bible monolith #05).

"The Graveyard of Increasing Scale": the player never meets the organism; they
explore the exponentially-growing shells it leaves behind. One code path builds
the carapace; the instar ladder rescales and re-details it:

  SM_Molt_Settlement.obj   ~14 m   house-scale, pores readable as windows
  SM_Molt_Cathedral.obj    ~44 m   pores/seams become rooms and buttresses
  SM_Molt_Mountain.obj     ~280 m  pores become caves, joints become valleys
  SM_Molt_FreshMolt.obj    ~340 m  the newest shell, SPLIT along the dorsal
                                   midline with a jagged fracture

Surface math (all displacement on one parametric dome — Apprentice-safe, no
boolean/trim ops):
  - carapace cross-sections: half-ellipse stations along a spine; width and
    height profiles give the insectile read (pronotum hump near the head)
  - tergum segmentation: groove at every plate boundary (K bands, golden-ratio
    jitter on band width so the segmentation is perfect-but-strange)
  - pores: golden-angle distributed dimples (phi in (u,v), density per instar)
  - fracture: two half-grids (v split at the dorsal midline) offset apart with
    noise-jagged edges (fresh-molt only)

Static architecture: no morphs, no LUTs. OBJ via File SOP write (Apprentice-safe).

Outputs (Saved/Audit/molted_god/): 4 OBJs + molted_god_manifest.json

Run (isolated console):
  & "C:\\Program Files\\Side Effects Software\\Houdini 22.0.368\\bin\\hython.exe" ^
      Tools/Houdini/sea_above_reef/build_molted_god.py
"""

import json
import math
from pathlib import Path

import hou

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "Saved" / "Audit" / "molted_god"

SEED = 20260829
PHI = (1.0 + math.sqrt(5.0)) / 2.0
GOLDEN = 0.6180339887498949

INSTARS = [
    dict(name="Settlement", L=14.0, W=7.0, H=4.5, SEG=160, ARC=72,
         bands=9, pores=60, pore_depth=0.16, groove_depth=0.10, split=False),
    dict(name="Cathedral", L=44.0, W=22.0, H=15.0, SEG=192, ARC=88,
         bands=11, pores=110, pore_depth=0.9, groove_depth=0.55, split=False),
    dict(name="Mountain", L=280.0, W=150.0, H=95.0, SEG=260, ARC=110,
         bands=13, pores=170, pore_depth=6.5, groove_depth=4.0, split=False),
    dict(name="FreshMolt", L=340.0, W=180.0, H=115.0, SEG=260, ARC=110,
         bands=13, pores=170, pore_depth=7.5, groove_depth=4.6, split=True),
]

CODE = r"""
import hou, math, random

node = hou.pwd()
geo = node.geometry()
if geo.findPointAttrib("uv") is None:
    geo.addAttrib(hou.attribType.Point, "uv", (0.0, 0.0))

SEED = __SEED__
PHI = __PHI__
GOLDEN = __GOLDEN__
L = __L__; W = __W__; H = __H__
SEG = __SEG__; ARC = __ARC__
BANDS = __BANDS__; PORES = __PORES__
PORE_DEPTH = __PORE_DEPTH__; GROOVE_DEPTH = __GROOVE_DEPTH__
SPLIT = __SPLIT__

rng = random.Random(SEED)
lat = [[rng.uniform(-1.0, 1.0) for _ in range(9)] for _ in range(9)]

def vnoise(u, v):
    fu, fv = u * 8, v * 8
    iu, iv = min(int(fu), 7), min(int(fv), 7)
    tu, tv = min(fu - iu, 1.0), min(fv - iv, 1.0)
    su = tu * tu * (3 - 2 * tu)
    sv = tv * tv * (3 - 2 * tv)
    a = lat[iv][iu] * (1 - su) + lat[iv][iu + 1] * su
    b = lat[iv + 1][iu] * (1 - su) + lat[iv + 1][iu + 1] * su
    return a * (1 - sv) + b * sv

def width_profile(u):
    # narrow pronotum, widest just past mid, tapering abdomen
    return W * (math.sin(math.pi * (u ** 0.8)) ** 0.75)

def height_profile(u):
    h = H * (math.sin(math.pi * (u ** 0.7)) ** 0.6)
    h += 0.15 * H * math.exp(-(((u - 0.22) / 0.12) ** 2))   # pronotum hump
    return h

# tergum band boundaries: golden-ratio jittered (perfect-but-strange)
bands = []
u_acc = 0.06
for k in range(BANDS):
    bands.append(u_acc)
    u_acc += (0.88 / BANDS) * (1.0 + 0.18 * math.sin(k * PHI * 7.0))
bands.append(0.94)

def groove(u):
    g = 0.0
    for b in bands:
        d = (u - b) * L
        g += -GROOVE_DEPTH * math.exp(-(d * d) / (0.35 * 0.35))
    return g

# pores: golden-angle field in (u, v)
pore_list = []
for i in range(PORES):
    pu = 0.08 + 0.84 * (i * GOLDEN % 1.0)
    pv = 0.5 + 0.42 * math.sin(i * 2.399963)
    pr = 0.010 + 0.016 * ((i * 7 % 13) / 13.0)
    pore_list.append((pu, pv, pr, PORE_DEPTH * (0.6 + 0.4 * ((i * 5 % 7) / 7.0))))

def pores(u, v):
    d = 0.0
    for (pu, pv, pr, pd) in pore_list:
        du = (u - pu) * L
        dv = (v - pv) * W
        d += -pd * math.exp(-((du * du) / (pr * L) ** 2 + (dv * dv) / (pr * W) ** 2))
    return d

def surface(u, v):
    th = math.pi * (0.06 + 0.88 * v)
    w = width_profile(u)
    h = height_profile(u) + groove(u) + pores(u, v) \
        + 0.6 * vnoise(u * 3.0, v * 3.0)          # chitin irregularity
    x = u * L
    y = h * math.sin(th)
    z = w * math.cos(th)
    return (x, y, z)

def emit_grid(vs, ve, label):
    rows = []
    for i in range(SEG + 1):
        u = i / SEG
        row = []
        for k in range(ARC + 1):
            v = vs + (ve - vs) * k / ARC
            p = geo.createPoint()
            p.setPosition(hou.Vector3(*surface(u, v)))
            p.setAttribValue(geo.findPointAttrib("uv"), (u, k / ARC))
            row.append(p)
        rows.append(row)
    for i in range(SEG):
        for k in range(ARC):
            f = geo.createPolygon()
            for q in (rows[i][k], rows[i][k + 1], rows[i + 1][k + 1], rows[i + 1][k]):
                f.addVertex(q)
    return rows

if not SPLIT:
    emit_grid(0.02, 0.98, "full")
else:
    # fresh molt: halves separated along the horizontal, jagged fracture
    rng2 = random.Random(SEED + 42)
    gap = W * 0.14
    for (vs, ve, side) in ((0.02, 0.5, -1.0), (0.5, 0.98, +1.0)):
        rows = emit_grid(vs, ve, "half")
        jag_n = rng2.uniform(-0.25, 0.25)
        for row in rows:
            for p in row:
                pos = p.position()
                u = pos.x() / L
                jag = 1.0 + 0.6 * math.sin(u * 40.0 + jag_n) + 0.4 * vnoise(u * 6.0, 0.5)
                p.setPosition(pos + hou.Vector3(0.0, 0.0, side * gap * 0.5 * jag))
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
    entries = []
    for spec in INSTARS:
        name = spec["name"]
        for old in [n for n in obj.children() if n.name() == f"MOLT_{name}"]:
            old.destroy()
        g = obj.createNode("geo", f"MOLT_{name}", run_init_scripts=True)
        py = g.createNode("python", "gen_shell")
        code = _inject(CODE, SEED=SEED, PHI=PHI, GOLDEN=GOLDEN,
                       L=spec["L"], W=spec["W"], H=spec["H"], SEG=spec["SEG"],
                       ARC=spec["ARC"], BANDS=spec["bands"], PORES=spec["pores"],
                       PORE_DEPTH=spec["pore_depth"],
                       GROOVE_DEPTH=spec["groove_depth"], SPLIT=spec["split"])
        py.parm("python").set(code)
        try:
            py.cook(force=True)
        except Exception:
            pass
        err = " ".join(str(py.errors()).split()) if py.errors() else ""
        if err:
            print(f"[molt] {name} NODE ERROR: {err[:300]}")
            g.destroy()
            continue
        geo = py.geometry()

        obj_path = OUT_DIR / f"SM_Molt_{name}.obj"
        sop = g.createNode("file", "write_obj")
        sop.parm("file").set(str(obj_path))
        sop.parm("filemode").set("write")
        sop.setInput(0, py)
        try:
            sop.cook(force=True)
        except Exception:
            pass
        obj_ok = obj_path.exists()
        entries.append({
            "instar": name,
            "length_m": spec["L"], "width_m": spec["W"], "height_m": spec["H"],
            "split": spec["split"],
            "obj": str(obj_path), "obj_written": obj_ok,
            "obj_bytes": obj_path.stat().st_size if obj_ok else 0,
            "points": len(geo.points()), "faces": len(geo.prims()),
        })
        print(f"[molt] {name}: {len(geo.points())} pts / {len(geo.prims())} faces, "
              f"obj={obj_ok}")
        g.destroy()

    manifest = {
        "schema": "melodia.molted_god_terrain.v1",
        "kind": "shell-recursion kit v0 (Bible #05: The Graveyard of Increasing Scale)",
        "seed": SEED,
        "instars": entries,
        "hython": hou.applicationVersionString(),
        "design_notes": [
            "one code path, exponential instar ladder: 14 m -> 44 m -> 280 m -> 340 m",
            "tergum bands golden-ratio jittered; pores golden-angle distributed",
            "FreshMolt = dorsal split with noise-jagged fracture edges",
            "v0 displacement-only: pores are dimples, not through-holes; "
            "membrane interiors + fracture plate kit are the next pass",
        ],
        "ue_import": {"scale": "100x (m -> cm)", "nanite": True},
        "bible_source": "MONOLITH_LEVEL_DESIGN_BIBLE_2026-08-26.md #05",
    }
    (OUT_DIR / "molted_god_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print("[molt] manifest -> molted_god_manifest.json")


if __name__ == "__main__":
    main()
