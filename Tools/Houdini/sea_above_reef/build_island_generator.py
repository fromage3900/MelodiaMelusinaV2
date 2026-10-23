"""R4 floating-island generator — inverted-gravity islands (code-grown, Python SOPs).

Authored by the coordinator after the R4 subagent returned empty (verified:
file absent on disk). Same house pattern as build_coral_generator.py.

Look: rocky dome with a FLAT GAMEPLAY PLATEAU (points above the plateau line are
clamped), radial noise displacement on the dome, and hanging liquid-rock drips
underneath — the Sea Above signature. Scale: metres (UE import x100).

Outputs (Saved/Audit/sea_above/meshes/):
  SM_Island_A.obj/.bgeo.sc   r~6 m, 6-9 drips
  SM_Island_B.obj/.bgeo.sc   r~4 m, steeper, 4-6 drips
  SM_Island_C.obj/.bgeo.sc   r~8 m, broad plateau, 8-12 drips + one tendril
  SM_RockChunk_M.obj/.bgeo.sc  ~0.8 m scatter lump
  SM_RockChunk_L.obj/.bgeo.sc  ~1.6 m scatter lump
  island_mesh_manifest.json

Run:  hython Tools/Houdini/sea_above_reef/build_island_generator.py
"""

import json
import sys
from pathlib import Path

import hou

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_clutter_meshes import (  # noqa: E402
    OUT_DIR as MESH_OUT_DIR,
    SEED as SUITE_SEED,
    _geo,
    _python_sop,
    export_geo,
)

SEED = SUITE_SEED  # 20260828

ISLAND_CODE = r"""
import hou, math, random

node = hou.pwd()
geo = node.geometry()
if geo.findPointAttrib("uv") is None:
    geo.addAttrib(hou.attribType.Point, "uv", (0.0, 0.0))
if geo.findPointAttrib("Cd") is None:
    geo.addAttrib(hou.attribType.Point, "Cd", (1.0, 1.0, 1.0))

V = hou.Vector3

# PARAMS (injected per island)
RADIUS = __RADIUS__
PLATEAU_FRAC = __PLATEAU_FRAC__     # fraction of dome height where the plateau sits
N_DRIPS = __N_DRIPS__
TENDRIL = __TENDRIL__
SEED_OFF = __SEED_OFF__

rng = random.Random(SEED + SEED_OFF)

# --- dome: displaced, squashed sphere, plateau-clamped -----------------------
SEG, RINGS = 56, 30
ry = RADIUS * 0.62
plateau_y = ry * PLATEAU_FRAC
rows = []
for j in range(RINGS + 1):
    phi = j / RINGS * math.pi
    row = []
    for i in range(SEG):
        th = i / SEG * 2.0 * math.pi
        x = math.sin(phi) * math.cos(th)
        y = math.cos(phi)
        z = math.sin(phi) * math.sin(th)
        # radial noise displacement (domain-warped sum of sines)
        d = (0.085 * math.sin(3.1 * x + 1.0) * math.sin(2.7 * z + 2.0)
             + 0.05 * math.sin(5.3 * x + 4.0 * z + 0.5)
             + 0.035 * math.sin(7.0 * y + 3.0))
        rr = RADIUS * (1.0 + d)
        px, py, pz = rr * x, rr * y * 0.62, rr * z
        if py > plateau_y:
            # clamp to plateau, keep radial xz (flat gameplay surface)
            py = plateau_y
        p = geo.createPoint()
        p.setPosition(V(px, py, pz))
        p.setAttribValue(geo.findPointAttrib("uv"), (i / SEG, 1.0 - j / RINGS))
        row.append(p)
    rows.append(row)
for j in range(RINGS):
    for i in range(SEG):
        f = geo.createPolygon()
        for q in (rows[j][i], rows[j][(i + 1) % SEG],
                  rows[j + 1][(i + 1) % SEG], rows[j + 1][i]):
            f.addVertex(q)
# pole caps (top pole is inside the plateau clamp; cap both for watertight look)
top = geo.createPoint(); top.setPosition(V(0, plateau_y, 0))
top.setAttribValue(geo.findPointAttrib("uv"), (0.5, 1.0))
bot = geo.createPoint(); bot.setPosition(V(0, -ry, 0))
bot.setAttribValue(geo.findPointAttrib("uv"), (0.5, 0.0))
for i in range(SEG):
    f = geo.createPolygon()
    f.addVertex(rows[0][(i + 1) % SEG]); f.addVertex(rows[0][i]); f.addVertex(top)
    f2 = geo.createPolygon()
    f2.addVertex(rows[-1][i]); f2.addVertex(rows[-1][(i + 1) % SEG]); f2.addVertex(bot)

# --- hanging drips: stretched, squashed spheres under the dome --------------
DRIP_CD = (0.55, 0.50, 0.53)
def drip(cx, cy, cz, r, length):
    seg, rings = 14, 10
    rows2 = []
    for j in range(rings + 1):
        phi = j / rings * math.pi
        row = []
        for i in range(seg):
            th = i / seg * 2.0 * math.pi
            x = math.sin(phi) * math.cos(th)
            y = math.cos(phi)
            z = math.sin(phi) * math.sin(th)
            taper = 1.0 - 0.55 * (j / rings)   # tapers toward the hanging tip
            p = geo.createPoint()
            p.setPosition(V(cx + r * taper * x,
                            cy - length * 0.5 - length * 0.5 * (-y),
                            cz + r * taper * z))
            p.setAttribValue(geo.findPointAttrib("uv"), (i / seg, 1.0 - j / rings))
            p.setAttribValue(geo.findPointAttrib("Cd"), DRIP_CD)
            row.append(p)
        rows2.append(row)
    for j in range(rings):
        for i in range(seg):
            f = geo.createPolygon()
            for q in (rows2[j][i], rows2[j][(i + 1) % seg],
                      rows2[j + 1][(i + 1) % seg], rows2[j + 1][i]):
                f.addVertex(q)
    c = geo.createPoint()
    c.setPosition(V(cx, cy - length, cz))
    c.setAttribValue(geo.findPointAttrib("Cd"), DRIP_CD)
    for i in range(seg):
        f = geo.createPolygon()
        f.addVertex(rows2[-1][i]); f.addVertex(rows2[-1][(i + 1) % seg]); f.addVertex(c)

for k in range(N_DRIPS):
    a = k / N_DRIPS * 2.0 * math.pi + rng.uniform(-0.3, 0.3)
    rad = RADIUS * rng.uniform(0.25, 0.62)
    cx, cz = rad * math.cos(a), rad * math.sin(a)
    # attach under the dome surface (approx dome y at that radius)
    t = rad / RADIUS
    cy = -ry * math.sqrt(max(0.0, 1.0 - t * t)) * 0.92
    drip(cx, cy, cz, RADIUS * rng.uniform(0.10, 0.18), rng.uniform(0.8, 2.4))

if TENDRIL:
    a = rng.uniform(0, 6.28)
    rad = RADIUS * 0.30
    drip(rad * math.cos(a), -ry * 0.55, rad * math.sin(a),
         RADIUS * 0.07, rng.uniform(3.0, 4.2))

try:
    geo.computeVertexNormals()
except Exception:
    pass
"""

CHUNK_CODE = r"""
import hou, math, random

node = hou.pwd()
geo = node.geometry()
if geo.findPointAttrib("uv") is None:
    geo.addAttrib(hou.attribType.Point, "uv", (0.0, 0.0))

V = hou.Vector3
# PARAMS
SIZE = __SIZE__
SEED_OFF = __SEED_OFF__

rng = random.Random(SEED + SEED_OFF)

def lump(cx, cy, cz, r, seed_off):
    seg, rings = 22, 14
    lr = random.Random(SEED + seed_off)
    ph = [lr.uniform(0, 6.28) for _ in range(3)]
    rows3 = []
    for j in range(rings + 1):
        phi = j / rings * math.pi
        row = []
        for i in range(seg):
            th = i / seg * 2.0 * math.pi
            x = math.sin(phi) * math.cos(th)
            y = math.cos(phi)
            z = math.sin(phi) * math.sin(th)
            d = (0.16 * math.sin(3.0 * x + ph[0]) * math.sin(2.4 * z + ph[1])
                 + 0.10 * math.sin(5.0 * y + ph[2]))
            rr = r * (1.0 + d)
            p = geo.createPoint()
            p.setPosition(V(cx + rr * x, cy + rr * y * 0.8, cz + rr * z))
            p.setAttribValue(geo.findPointAttrib("uv"), (i / seg, 1.0 - j / rings))
            row.append(p)
        rows3.append(row)
    for j in range(rings):
        for i in range(seg):
            f = geo.createPolygon()
            for q in (rows3[j][i], rows3[j][(i + 1) % seg],
                      rows3[j + 1][(i + 1) % seg], rows3[j + 1][i]):
                f.addVertex(q)

lump(0, 0, 0, SIZE, SEED_OFF)
lump(SIZE * 0.7, SIZE * 0.15, SIZE * 0.3, SIZE * 0.55, SEED_OFF + 1)
lump(-SIZE * 0.6, SIZE * 0.1, -SIZE * 0.2, SIZE * 0.4, SEED_OFF + 2)
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
    manifests = []
    jobs = [
        ("SM_Island_A", ISLAND_CODE, dict(SEED=SEED, RADIUS=6.0, PLATEAU_FRAC=0.55,
                                          N_DRIPS=7, TENDRIL=False, SEED_OFF=61)),
        ("SM_Island_B", ISLAND_CODE, dict(SEED=SEED, RADIUS=4.0, PLATEAU_FRAC=0.62,
                                          N_DRIPS=5, TENDRIL=False, SEED_OFF=62)),
        ("SM_Island_C", ISLAND_CODE, dict(SEED=SEED, RADIUS=8.0, PLATEAU_FRAC=0.50,
                                          N_DRIPS=10, TENDRIL=True, SEED_OFF=63)),
        ("SM_RockChunk_M", CHUNK_CODE, dict(SEED=SEED, SIZE=0.8, SEED_OFF=64)),
        ("SM_RockChunk_L", CHUNK_CODE, dict(SEED=SEED, SIZE=1.6, SEED_OFF=65)),
    ]
    for stem, code, params in jobs:
        code = _inject(code, **params)
        code = code.replace("random.Random(SEED + SEED_OFF)",
                            f"random.Random({SEED} + SEED_OFF)")
        code = code.replace("random.Random(SEED + seed_off)",
                            f"random.Random({SEED} + seed_off)")
        g = _geo(stem)
        py = _python_sop(g, "gen_" + stem.lower(), code)
        out = g.createNode("null", "OUT")
        out.setInput(0, py)
        export_geo(g, out, stem, manifests)
    MESH_OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(MESH_OUT_DIR / "island_mesh_manifest.json", "w", encoding="utf-8") as f:
        json.dump({"schema": "melodia.sea_above_reef_meshes.v1",
                   "kind": "floating islands R4 (code-grown; dome + plateau clamp "
                           "+ hanging drips)",
                   "seed": SEED, "hython": hou.applicationVersionString(),
                   "plateau_note": "flat clamp = gameplay surface; drips darker via "
                                   "Cd vertex color (bgeo only; OBJ drops Cd)",
                   "ue_import": {"obj_scale": "100x (m -> cm)", "nanite": True},
                   "meshes": manifests}, f, indent=2)
    print(f"[island] manifest -> {MESH_OUT_DIR / 'island_mesh_manifest.json'}")


if __name__ == "__main__":
    main()
