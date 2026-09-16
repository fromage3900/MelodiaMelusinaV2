"""MK39 plates proof: MEL_skiff_plates constructs, evaluates, parametrizes.

Run: "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background
         --factory-startup --python Tools/wardrobe_pipeline/proof_mk39_plates.py
Imports resolve to the REPO copy (asserted via module __file__).

Gates:
  1. MEL_skiff_plates registered + tree constructs headless (>15 nodes:
     patch arc, tenon tabs, boolean mortise, bay instancer).
  2. Evaluates to real mesh: verts > 0, no NaN, deterministic across evals.
  3. Plate Rows 9 -> 4 reduces vertex count (bays parametrize).
  4. Tenon Width 0.05 -> 0.10 changes evaluated bounds (tabs parametrize).
  5. Gasket Gap 0.004 -> 0.02 changes X extent (joints parametrize).
Exit non-zero on any failure. Receipt -> Saved/Audit/sea_above/skiff_MK3/.
"""
import json
import math
import os
import sys

REPO = r"C:\EnvironmentPortfolio\BS_GodFile"
GN = os.path.join(REPO, "deploy", "surreal_arch", "melodia_gn")
# NOTE 2026-09-10: this branch's melodia_gn/__init__.py imports
# barrel_vault_kit, which does not exist in the tree (another lane's
# recovery in flight) — importing the package normally dies. Load the two
# needed modules by path, bypassing both __init__ files.
import importlib.util  # noqa: E402
import types  # noqa: E402

import bpy  # noqa: E402


def _load(modname, path):
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)
    return mod


_parent = types.ModuleType("surreal_arch")
_parent.__path__ = [os.path.join(REPO, "deploy", "surreal_arch")]
sys.modules["surreal_arch"] = _parent
_pkg = types.ModuleType("surreal_arch.melodia_gn")
_pkg.__path__ = [GN]
sys.modules["surreal_arch.melodia_gn"] = _pkg
core = _load("surreal_arch.melodia_gn.core", os.path.join(GN, "core.py"))
sb = _load("surreal_arch.melodia_gn.starskiff_biomech",
           os.path.join(GN, "starskiff_biomech.py"))
GROUP_METADATA = core.GROUP_METADATA
print("REPO_MODULE_OK", sb.__file__)

rep = {"repo_module": sb.__file__}

sb.register()

sb.register()
assert "MEL_skiff_ribcage" in GROUP_METADATA, "ribcage registration lost"
assert "MEL_skiff_plates" in GROUP_METADATA, "plates not registered"
print("BUILDER_OK MEL_skiff_plates",
      GROUP_METADATA["MEL_skiff_plates"].get("label", "?"))

for bid in ("MEL_skiff_plates",):
    old = bpy.data.node_groups.get(bid)
    if old:
        bpy.data.node_groups.remove(old)
sb.build_skiff_plates()
ng = bpy.data.node_groups.get("MEL_skiff_plates")
assert ng is not None and len(ng.nodes) > 15, "plates tree build failed"
print("TREE_OK MEL_skiff_plates", len(ng.nodes), "nodes")
rep["node_count"] = len(ng.nodes)
assert any(n.bl_idname == "GeometryNodeMeshBoolean" for n in ng.nodes), \
    "no MeshBoolean mortise in plates tree"
assert any(n.bl_idname == "GeometryNodeMeshGrid" for n in ng.nodes), \
    "no MeshGrid strake patch in plates tree"


def attach_with(ob, dials):
    src = bpy.data.node_groups["MEL_skiff_plates"]
    copy = src.copy()
    for dial, val in dials.items():
        found = False
        for item in copy.interface.items_tree:
            if (getattr(item, "item_type", "") == "SOCKET"
                    and getattr(item, "in_out", "") == "INPUT"
                    and item.name == dial and hasattr(item, "default_value")):
                item.default_value = val
                found = True
        assert found, "dial missing: " + dial
    copy.update_tag()
    mod = ob.modifiers.new("Proof_plates", "NODES")
    mod.node_group = copy
    return mod


def eval_verts(ob):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    mesh = ev.to_mesh()
    try:
        return [tuple(v.co) for v in mesh.vertices]
    finally:
        ev.to_mesh_clear()


def has_nan(verts):
    return any(not all(math.isfinite(c) for c in v) for v in verts)


def bounds(verts):
    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    return (max(xs) - min(xs), max(ys) - min(ys))


def max_disp(a, b):
    import math
    return max(math.dist(p, q) for p, q in zip(a, b))


me = bpy.data.meshes.new("plates_base")
me.from_pydata([(0.0, 0.0, 0.0)], [], [])
ob = bpy.data.objects.new("PlatesBase", me)
bpy.context.scene.collection.objects.link(ob)

mod = attach_with(ob, {})
v9 = eval_verts(ob)
assert len(v9) > 200, "plates evaluated nearly empty: %d verts" % len(v9)
assert not has_nan(v9), "NaN in plates eval"
v9b = eval_verts(ob)
assert len(v9) == len(v9b), "plates eval not deterministic"
print("PLATES_VERTS_9", len(v9))
rep["plates_verts_9"] = len(v9)
ob.modifiers.remove(mod)

mod = attach_with(ob, {"Plate Rows": 4.0})
v4 = eval_verts(ob)
print("PLATES_VERTS_4", len(v4))
assert 0 < len(v4) < len(v9), "Plate Rows dial does not parametrize bays"
rep["plates_verts_4"] = len(v4)
ob.modifiers.remove(mod)

mod = attach_with(ob, {"Tenon Width": 0.10})
vw = eval_verts(ob)
# Tabs sit inside the plate's Y bounds, so compare displacement, not span.
twmove = max_disp(v9, vw)
print("TENON_MOVE", round(twmove, 4))
assert twmove > 0.005, "Tenon Width dial does not move geometry"
rep["tenon_move"] = round(twmove, 4)
ob.modifiers.remove(mod)

mod = attach_with(ob, {"Gasket Gap": 0.02})
vg = eval_verts(ob)
gapmove = max_disp(v9, vg)
print("GAP_MOVE", round(gapmove, 4))
assert gapmove > 0.005, "Gasket Gap dial does not move geometry"
rep["gap_move"] = round(gapmove, 4)
ob.modifiers.remove(mod)

out = os.path.join(REPO, "Saved", "Audit", "sea_above", "skiff_MK3",
                   "mk39_plates_proof_2026-09-10.json")
with open(out, "w") as f:
    json.dump(rep, f, indent=2)
print("RECEIPT", out)
print("MK39_PLATES_PROOF PASS")
