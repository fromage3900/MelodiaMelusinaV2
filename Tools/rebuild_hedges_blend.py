"""Rebuild the MelodiaHedges GN .blend from the surviving melodia_gn addon source.

Run headless:
  "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe" --background --factory-startup \
      --python Tools/rebuild_hedges_blend.py

Why this exists: Saved/Staging/MelusinaBlooms/release/MelodiaHedges_v0.1/MelodiaHedges_Demo.blend
was deleted with the Staging cleanup on 2026-10-28. The generator source survives in the
Blender addon (melodia_gn/hedge_clutter.py, SHA256 BFC3214587A1D32C), so the node groups
can be rebuilt. This script recreates the hedge/topiary/clutter node groups and a demo
object per group, then saves a fresh .blend to D:.

Outputs:
  D:\\MelodiaVault\\recovery_20261029\\MelodiaHedges_Rebuilt_20261029.blend
  D:\\MelodiaVault\\recovery_20261029\\MelodiaHedges_Rebuilt_20261029.json
"""
import json
import os
import sys

import bpy

ADDONS = os.path.join(os.environ.get("APPDATA", ""), "Blender Foundation", "Blender", "5.2", "scripts", "addons")
if ADDONS not in sys.path:
    sys.path.insert(0, ADDONS)

OUT_DIR = r"D:\MelodiaVault\recovery_20261029"
OUT_BLEND = os.path.join(OUT_DIR, "MelodiaHedges_Rebuilt_20261029.blend")
OUT_JSON = os.path.join(OUT_DIR, "MelodiaHedges_Rebuilt_20261029.json")

import melodia_gn  # noqa: E402
import melodia_gn.hedge_clutter as hc  # noqa: E402


def make_demo_object(tree, name):
    mesh = bpy.data.meshes.new(name + "_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    mod = obj.modifiers.new("GN_" + tree.name, "NODES")
    mod.node_group = tree
    return obj


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    built = []
    for label, fn in (
        ("MEL_hedge", hc.build_hedge),
        ("MEL_hedge_wild", hc.build_hedge_wild),
        ("MEL_topiary_ball", hc.build_topiary_ball),
        ("MEL_topiary_cone", hc.build_topiary_cone),
        ("MEL_topiary_spline", hc.build_topiary_spline),
        ("MEL_foliage_clutter", hc.build_foliage_clutter),
    ):
        try:
            tree = fn()
            obj = make_demo_object(tree, label)
            built.append({"group": tree.name, "object": obj.name, "nodes": len(tree.nodes)})
            print("BUILT", tree.name, "nodes", len(tree.nodes), "->", obj.name)
        except Exception as exc:
            built.append({"group": label, "error": str(exc)[:200]})
            print("BUILD_FAIL", label, str(exc)[:200])

    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND)
    with open(OUT_JSON, "w") as fh:
        json.dump({"schema": "melodia.hedges_rebuild.v1", "blend": OUT_BLEND,
                   "source": os.path.join(ADDONS, "melodia_gn", "hedge_clutter.py"),
                   "built": built}, fh, indent=1)
    print("SAVED", OUT_BLEND)
    print("REPORT", OUT_JSON)


main()
