"""Dump a shirt FBX's per-vertex skin weights to JSON (read-only).

Used to build the route-(a) legal artefact from data instead of prose:
  hython Saved/Audit/ShirtBones_20261020/dump_weights.py --fbx PATH --out PATH

Output: {"fbx":..., "joints":[...], "verts":[{"i":0,"w":[[bone,weight],...]}, ...]}
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import hou


def pairs_of(pt):
    v = pt.attribValue("boneCapture")
    return [(int(v[i]), float(v[i + 1])) for i in range(0, len(v) - 1, 2)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fbx", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    fbx = Path(args.fbx)

    hou.hipFile.clear(suppress_save_prompt=True)
    geo = hou.node("/obj").createNode("geo", "dump")
    imp = geo.createNode("kinefx::fbxcharacterimport", "fbx_in")
    imp.parm("fbxfile").set(str(fbx.resolve()))
    try:
        imp.parm("convertunits").set(1)
    except Exception:
        pass
    skin = imp.geometry(0)
    rest = imp.geometry(1)

    rest_names = [str(p.attribValue("name")) for p in rest.points()]
    rest_pos = [list(p.position()) for p in rest.points()]
    idx_to_name = dict(enumerate(rest_names))

    verts = []
    for p in skin.points():
        prs = [(idx_to_name.get(i, f"<idx {i}>"), round(w, 6)) for i, w in pairs_of(p) if w > 1e-6]
        verts.append({"i": p.number(), "w": prs})

    out = {
        "fbx": str(fbx),
        "joint_count": len(rest_names),
        "joints": rest_names,
        "joint_positions_m": rest_pos,
        "vert_count": len(verts),
        "verts": verts,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out), encoding="utf-8")
    print("WROTE", args.out, "verts", len(verts), "joints", len(rest_names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
