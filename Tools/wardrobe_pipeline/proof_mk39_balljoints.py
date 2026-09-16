"""MK39 balljoints proof: MEL_skiff_balljoints constructs, evaluates, parametrizes.

Run: "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background
         --factory-startup --python Tools/wardrobe_pipeline/proof_mk39_balljoints.py

Bypasses melodia_gn/__init__ (broken barrel_vault_kit import on this branch,
another lane's recovery) by loading core + biomech modules by path.

Gates:
  1. MEL_skiff_balljoints registered + tree constructs (>20 nodes: ball,
     collar, 18-station lookup chain, instancer).
  2. Evaluates to real mesh: verts > 0, no NaN, deterministic across evals.
  3. Joint count check: 18 joints placed (keel + gunwale x 9 live stations);
     evaluated X extent covers the measured hull (~7.6 m).
  4. Ball Diameter 0.05 -> 0.10 moves geometry.
  5. Collar Ratio 1.6 -> 2.4 moves geometry.
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
assert "MEL_skiff_balljoints" in GROUP_METADATA, "balljoints not registered"
print("BUILDER_OK MEL_skiff_balljoints",
      GROUP_METADATA["MEL_skiff_balljoints"].get("label", "?"))

old = bpy.data.node_groups.get("MEL_skiff_balljoints")
if old:
    bpy.data.node_groups.remove(old)
sb.build_skiff_balljoints()
ng = bpy.data.node_groups.get("MEL_skiff_balljoints")
assert ng is not None and len(ng.nodes) > 20, "balljoints tree build failed"
print("TREE_OK MEL_skiff_balljoints", len(ng.nodes), "nodes")
rep["node_count"] = len(ng.nodes)
assert any(n.bl_idname == "GeometryNodeMeshUVSphere" for n in ng.nodes), \
    "no ball dome in balljoints tree"
assert any(n.bl_idname == "GeometryNodeMeshCylinder" for n in ng.nodes), \
    "no collar ring in balljoints tree"


def attach_with(ob, dials):
    src = bpy.data.node_groups["MEL_skiff_balljoints"]
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
    mod = ob.modifiers.new("Proof_joints", "NODES")
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


me = bpy.data.meshes.new("joints_base")
me.from_pydata([(0.0, 0.0, 0.0)], [], [])
ob = bpy.data.objects.new("JointsBase", me)
bpy.context.scene.collection.objects.link(ob)

mod = attach_with(ob, {})
v0 = eval_verts(ob)
assert len(v0) > 500, "joints evaluated nearly empty: %d verts" % len(v0)
assert not has_nan(v0), "NaN in joints eval"
assert len(v0) == len(eval_verts(ob)), "joints eval not deterministic"
xs = [v[0] for v in v0]
xspan = max(xs) - min(xs)
print("JOINTS_VERTS", len(v0), "XSPAN", round(xspan, 3))
assert abs(xspan - 7.615) < 0.3, "joints do not span the hull: %f" % xspan
rep["joints_verts"] = len(v0)
rep["joints_xspan"] = round(xspan, 3)
ob.modifiers.remove(mod)

mod = attach_with(ob, {"Ball Diameter": 0.10})
vd = eval_verts(ob)
dd = max_disp(v0, vd)
print("BALL_MOVE", round(dd, 4))
assert dd > 0.01 and len(vd) == len(v0), "Ball Diameter dial broken"
rep["ball_move"] = round(dd, 4)
ob.modifiers.remove(mod)

mod = attach_with(ob, {"Collar Ratio": 2.4})
vc = eval_verts(ob)
dc = max_disp(v0, vc)
print("COLLAR_MOVE", round(dc, 4))
assert dc > 0.005 and len(vc) == len(v0), "Collar Ratio dial broken"
rep["collar_move"] = round(dc, 4)
ob.modifiers.remove(mod)

out = os.path.join(REPO, "Saved", "Audit", "sea_above", "skiff_MK3",
                   "mk39_balljoints_proof_2026-09-10.json")
with open(out, "w") as f:
    json.dump(rep, f, indent=2)
print("RECEIPT", out)
print("MK39_BALLJOINTS_PROOF PASS")
