"""Kelp ribbon meshes for the R3 sway system (uv.y = growth axis, 0=base, 1=tip).

Pairs with T_SeaAbove_KelpSway_LUT (kelp_vat_textures.py): the material's World
Position Offset samples the LUT at (time, uv.y), so the mesh only needs a clean
uv.y growth gradient — no vertex-ID plumbing, works from plain OBJ.

Outputs (Saved/Audit/sea_above/meshes/):
  SM_Kelp_Tall.obj/.bgeo.sc     h=2.0 m, w=0.16
  SM_Kelp_Mid.obj/.bgeo.sc      h=1.5 m, w=0.24
  SM_Kelp_Cluster.obj/.bgeo.sc  3 merged stalks (scatter starter)
  kelp_mesh_manifest.json

Run:  hython Tools/Houdini/sea_above_reef/build_kelp_vat.py
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

SEED = SUITE_SEED

KELP_CODE = r"""
import hou, math, random

node = hou.pwd()
geo = node.geometry()
if geo.findPointAttrib("uv") is None:
    geo.addAttrib(hou.attribType.Point, "uv", (0.0, 0.0))

V = hou.Vector3

def ribbon(height, width, rows, cols, curve_x, curve_z, twist, seed_off):
    # spine: S-curved stalk in X/Y, gentle lean in Z
    rng = random.Random(SEED + seed_off)
    ph = rng.uniform(0, 6.28)
    spine = []
    for i in range(rows + 1):
        t = i / rows
        x = curve_x * t * t * math.sin(2.2 * t + ph)
        y = height * t
        z = curve_z * t * math.sin(1.4 * t + ph * 0.7)
        spine.append(V(x, y, z))
    # width profile: narrow base, bulge mid, taper to tip
    def wprof(t):
        return width * (0.35 + 0.65 * math.sin(math.pi * min(1.0, 0.15 + 0.85 * t))) \
               * (1.0 - 0.55 * t)
    grid = []
    for i, pos in enumerate(spine):
        t = i / rows
        if i == 0:
            tan = spine[1] - spine[0]
        elif i == rows:
            tan = spine[-1] - spine[-2]
        else:
            tan = spine[i + 1] - spine[i - 1]
        tan = tan.normalized()
        side = tan.cross(V(0, 0, 1))
        if side.length() < 1e-4:
            side = V(1, 0, 0)
        side = side.normalized()
        w = wprof(t)
        row = []
        for k in range(cols + 1):
            u = k / cols - 0.5                     # -0.5..0.5 across
            arc = (u * u * 4.0 - 1.0) * width * 0.12   # slight cup across width
            tw = twist * t
            su, cu = math.sin(tw), math.cos(tw)
            ux = u * cu
            uz = u * su
            p = geo.createPoint()
            p.setPosition(pos + side * (w * ux) + V(0, 0, w * uz) + V(0, arc, 0))
            p.setAttribValue(geo.findPointAttrib("uv"), (u + 0.5, t))
            row.append(p)
        grid.append(row)
    for i in range(rows):
        for k in range(cols):
            f = geo.createPolygon()
            for q in (grid[i][k], grid[i][k + 1], grid[i + 1][k + 1], grid[i + 1][k]):
                f.addVertex(q)
    return grid

# BASE_PINS + PARAMS injected below by the builder (see replacements)
"""

TALL_PARAMS = """
# SM_Kelp_Tall
ribbon(height=2.0, width=0.16, rows=40, cols=6,
       curve_x=0.22, curve_z=0.10, twist=0.6, seed_off=41)
"""

MID_PARAMS = """
# SM_Kelp_Mid
ribbon(height=1.5, width=0.24, rows=34, cols=6,
       curve_x=0.30, curve_z=0.16, twist=-0.5, seed_off=42)
"""

CLUSTER_PARAMS = """
# SM_Kelp_Cluster: three stalks, small offsets/rotations, merged
for (dx, dz, rot, h, w, seed_off) in ((0.0, 0.0, 0.0, 1.9, 0.18, 43),
                                      (0.14, 0.06, 1.1, 1.4, 0.22, 44),
                                      (-0.12, 0.10, 2.3, 1.1, 0.20, 45)):
    grid = ribbon(height=h, width=w, rows=30, cols=6,
                  curve_x=0.26, curve_z=0.14, twist=0.7, seed_off=seed_off)
try:
    geo.computeVertexNormals()
except Exception:
    pass
"""

TALL_CODE = KELP_CODE + TALL_PARAMS + """
try:
    geo.computeVertexNormals()
except Exception:
    pass
"""
MID_CODE = KELP_CODE + MID_PARAMS + """
try:
    geo.computeVertexNormals()
except Exception:
    pass
"""


def main():
    manifests = []
    jobs = [
        (TALL_CODE, "gen_kelp_tall", "SM_Kelp_Tall"),
        (MID_CODE, "gen_kelp_mid", "SM_Kelp_Mid"),
        (KELP_CODE + CLUSTER_PARAMS, "gen_kelp_cluster", "SM_Kelp_Cluster"),
    ]
    for code, node_name, stem in jobs:
        code = code.replace("random.Random(SEED + seed_off)",
                            f"random.Random({SEED} + seed_off)")
        g = _geo(stem)
        py = _python_sop(g, node_name, code)
        out = g.createNode("null", "OUT")
        out.setInput(0, py)
        export_geo(g, out, stem, manifests)
    MESH_OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(MESH_OUT_DIR / "kelp_mesh_manifest.json", "w", encoding="utf-8") as f:
        json.dump({"schema": "melodia.sea_above_reef_meshes.v1",
                   "kind": "kelp ribbons (R3)",
                   "seed": SEED, "hython": hou.applicationVersionString(),
                   "uv_contract": "uv.y = growth axis (0=base, 1=tip) — LUT V lookup",
                   "sway": "material WPO samples T_SeaAbove_KelpSway_LUT at "
                           "(time, uv.y); amplitude *= (1 + 1.5 * User.SeaAbovePulse)",
                   "ue_import": {"obj_scale": "100x (m -> cm)", "nanite": True,
                                 "material": "two-sided (single-layer ribbon)"},
                   "meshes": manifests}, f, indent=2)
    print(f"[kelp] manifest -> {MESH_OUT_DIR / 'kelp_mesh_manifest.json'}")


if __name__ == "__main__":
    main()
