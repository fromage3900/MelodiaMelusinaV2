"""Frozen cloth — banners/shrouds frozen mid-gesture, shipped as MORPH TARGETS.

Honest method note: poses are ANALYTIC drape (pinned-top catenary + harmonic
cascade + gust), not a Vellum sim — Vellum's headless parm mapping is a
documented upgrade task. The deliverable is identical: same-topology pose sets
-> shape keys -> UE morph targets via the proven Blender path.

Contents (metres; UE x100):
  SM_Banner   2 x 6 m hanging silk banner   (3 poses: SwayA, SwayB, Billow)
  SM_Shroud   4 x 5 m burial shroud         (3 poses: Gather, Drift, Settle)
  frozen_cloth_mesh.json  (jellyfish-schema: points/faces/uvs/poses)

Run:  hython Tools/Houdini/sea_above_reef/build_frozen_cloth.py
then: blender --background --python Tools/Houdini/sea_above_reef/cloth_shapekeys.py
"""

import json
from pathlib import Path

import hou

OUT_DIR = Path(__file__).resolve().parents[3] / "Saved" / "Audit" / "sea_above" / "meshes"

CLOTH_CODE = r"""
import hou, math

node = hou.pwd()
geo = node.geometry()
if geo.findPointAttrib("uv") is None:
    geo.addAttrib(hou.attribType.Point, "uv", (0.0, 0.0))
V = hou.Vector3

W = __W__            # width (m)
H = __H__            # height (m)
COLS, ROWS = __COLS__, __ROWS__
POSE = __POSE__      # injected pose name

rows = []
for r in range(ROWS + 1):
    t = r / ROWS                      # 0 = pinned top, 1 = free hem
    row = []
    for c in range(COLS + 1):
        u = c / COLS - 0.5
        # drape: catenary-ish sag grows with depth into the cloth
        sag = math.sin(math.pi * t) * (0.35 + 0.3 * math.sin(u * 3.0 + 1.0))
        x = u * W
        y = -H * t + sag * t * 0.6
        z = 0.0
        z += 0.18 * W * t * math.sin(u * 4.0 + t * 2.2 + PHASE)      # cascade
        z += 0.10 * W * t * t * math.sin(u * 7.0 - PHASE * 1.3)      # flutter
        z += 0.30 * W * t * t * GUST                                  # gust push
        if POSE == "Billow":
            z += 0.45 * W * t * t * (0.5 + 0.5 * math.sin(u * 2.0 + PHASE))
            x += 0.12 * W * t * math.sin(u * 5.0)
        if POSE == "Gather":
            x *= (1.0 - 0.35 * t)
            z += 0.22 * W * t * math.sin(u * 6.0 + PHASE * 2.0)
        if POSE == "Settle":
            z *= 0.45
            y += 0.10 * H * t
        p = geo.createPoint()
        p.setPosition(V(x, y, z))
        p.setAttribValue(geo.findPointAttrib("uv"), (u + 0.5, 1.0 - t))
        row.append(p)
    rows.append(row)
for r in range(ROWS):
    for c in range(COLS):
        f = geo.createPolygon()
        for q in (rows[r][c], rows[r][c + 1], rows[r + 1][c + 1], rows[r + 1][c]):
            f.addVertex(q)
try:
    geo.computeVertexNormals()
except Exception:
    pass
"""


def build(name, w, h, cols, rows_n, poses):
    obj = hou.node("/obj")
    for old in [n for n in obj.children() if n.name() == name]:
        old.destroy()
    g = obj.createNode("geo", name, run_init_scripts=True)
    payload = {"points": None, "faces": None, "uvs": None}
    pose_sets = {}
    for pose_name, phase, gust in poses:
        for old in [n for n in g.children() if n.name() == "gen"]:
            old.destroy()
        code = (CLOTH_CODE.replace("__W__", repr(w)).replace("__H__", repr(h))
                          .replace("__COLS__", repr(cols)).replace("__ROWS__", repr(rows_n))
                          .replace("__POSE__", repr(pose_name))
                          .replace("PHASE", repr(phase))
                          .replace("GUST", repr(gust)))
        py = g.createNode("python", "gen")
        py.parm("python").set(code)
        try:
            py.cook(force=True)
        except Exception:
            pass
        err = " ".join(str(py.errors()).split()) if py.errors() else ""
        if err:
            print(f"[cloth] NODE ERROR [{name}:{pose_name}]: {err[:300]}")
            continue
        geo = py.geometry()
        pts = [[round(c, 3) for c in p.position()] for p in geo.points()]
        uvs = [list(p.attribValue(geo.findPointAttrib("uv"))) for p in geo.points()]
        if payload["points"] is None:
            payload["points"] = pts
            payload["uvs"] = uvs
            payload["faces"] = [[v.point().number() for v in prim.vertices()]
                                for prim in geo.prims()]
        pose_sets[pose_name] = {"points": pts, "topology_matches":
                                len(pts) == len(payload["points"])}
        print(f"[cloth] {name}/{pose_name}: {len(pts)} pts")
    g.destroy()
    return payload, pose_sets


def main():
    banner, banner_poses = build("SM_Banner", 2.0, 6.0, 10, 30,
                                 [("SwayA", 0.0, 0.3), ("SwayB", 2.1, 0.8),
                                  ("Billow", 4.0, 1.4)])
    shroud, shroud_poses = build("SM_Shroud", 4.0, 5.0, 12, 26,
                                 [("Gather", 1.0, 0.5), ("Drift", 3.3, 1.0),
                                  ("Settle", 5.1, 0.2)])
    payload = {"schema": "melodia.frozen_cloth.v1", "seed": 20260828,
               "scale": "metres; UE import x100",
               "method": "analytic drape poses (Vellum sim upgrade documented)",
               "banner": banner, "banner_poses": banner_poses,
               "shroud": shroud, "shroud_poses": shroud_poses}
    out = OUT_DIR / "frozen_cloth_mesh.json"
    out.write_text(json.dumps(payload, separators=(",", ":")), encoding="utf-8")
    print(f"[cloth] wrote {out.name} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
