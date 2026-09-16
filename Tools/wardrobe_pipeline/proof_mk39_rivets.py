"""MK39 rivets proof: MEL_skiff_rivet_lattice constructs, evaluates, parametrizes.

Run: "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background
         --factory-startup --python Tools/wardrobe_pipeline/proof_mk39_rivets.py

Bypasses melodia_gn/__init__ (broken barrel_vault_kit import on this branch,
another lane's recovery) by loading core + biomech modules by path.

Gates:
  1. MEL_skiff_rivet_lattice registered + tree constructs (>15 nodes:
     row template, bay edge lines, field/collar split, head instancers).
  2. Evaluates to real mesh: verts > 0, no NaN, deterministic across evals.
  3. Rivet Bays 9 -> 4 reduces vertex count.
  4. Rivet Diameter 0.012 -> 0.024 moves geometry (heads scale).
  5. Collar Scale 1.4 -> 2.2 moves geometry (studs scale).
Exit non-zero on any failure. Receipt -> Saved/Audit/sea_above/skiff_MK3/.
"""
import json
import math
import os
import sys

REPO = r"C:\EnvironmentPortfolio\BS_GodFile"
GN = os.path.join(REPO, "deploy", "surreal_arch", "melodia_gn")
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
assert "MEL_skiff_rivet_lattice" in GROUP_METADATA, "rivets not registered"
print("BUILDER_OK MEL_skiff_rivet_lattice",
      GROUP_METADATA["MEL_skiff_rivet_lattice"].get("label", "?"))

old = bpy.data.node_groups.get("MEL_skiff_rivet_lattice")
if old:
    bpy.data.node_groups.remove(old)
sb.build_skiff_rivet_lattice()
ng = bpy.data.node_groups.get("MEL_skiff_rivet_lattice")
assert ng is not None and len(ng.nodes) > 15, "rivets tree build failed"
print("TREE_OK MEL_skiff_rivet_lattice", len(ng.nodes), "nodes")
rep["node_count"] = len(ng.nodes)
assert any(n.bl_idname == "GeometryNodeMeshUVSphere" for n in ng.nodes), \
    "no rivet-head dome in rivets tree"
assert any(n.bl_idname == "GeometryNodeSeparateGeometry" for n in ng.nodes), \
    "no field/collar split in rivets tree"


def attach_with(ob, dials):
    src = bpy.data.node_groups["MEL_skiff_rivet_lattice"]
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
    mod = ob.modifiers.new("Proof_rivets", "NODES")
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


def max_disp(a, b):
    n = min(len(a), len(b))
    assert n > 0, "empty eval"
    return max(math.dist(a[i], b[i]) for i in range(n))


me = bpy.data.meshes.new("rivets_base")
me.from_pydata([(0.0, 0.0, 0.0)], [], [])
ob = bpy.data.objects.new("RivetsBase", me)
bpy.context.scene.collection.objects.link(ob)

mod = attach_with(ob, {})
v9 = eval_verts(ob)
assert len(v9) > 500, "rivets evaluated nearly empty: %d verts" % len(v9)
assert not has_nan(v9), "NaN in rivets eval"
assert len(v9) == len(eval_verts(ob)), "rivets eval not deterministic"
print("RIVETS_VERTS_9", len(v9))
rep["rivets_verts_9"] = len(v9)
ob.modifiers.remove(mod)

mod = attach_with(ob, {"Rivet Bays": 4.0})
v4 = eval_verts(ob)
print("RIVETS_VERTS_4", len(v4))
assert 0 < len(v4) < len(v9), "Rivet Bays dial does not parametrize"
rep["rivets_verts_4"] = len(v4)
ob.modifiers.remove(mod)

mod = attach_with(ob, {"Rivet Diameter": 0.024})
vd = eval_verts(ob)
dd = max_disp(v9, vd)
print("DIAMETER_MOVE", round(dd, 4))
assert dd > 0.005 and len(vd) == len(v9), "Rivet Diameter dial broken"
rep["diameter_move"] = round(dd, 4)
ob.modifiers.remove(mod)

mod = attach_with(ob, {"Collar Scale": 2.5})
vc = eval_verts(ob)
dc = max_disp(v9, vc)
print("COLLAR_MOVE", round(dc, 4))
assert dc > 0.005 and len(vc) == len(v9), "Collar Scale dial broken"
rep["collar_move"] = round(dc, 4)
ob.modifiers.remove(mod)

out = os.path.join(REPO, "Saved", "Audit", "sea_above", "skiff_MK3",
                   "mk39_rivets_proof_2026-09-10.json")
with open(out, "w") as f:
    json.dump(rep, f, indent=2)
print("RECEIPT", out)
print("MK39_RIVETS_PROOF PASS")
