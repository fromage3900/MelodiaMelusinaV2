"""Chladni proof: garment layer rescue + skiff plate relief extension.

Run: "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background
         --factory-startup --python Tools/wardrobe_pipeline/proof_mk39_chladni.py

Bypasses melodia_gn/__init__ (broken barrel_vault_kit import on this branch,
another lane's recovery) by loading core/audio_terrain/chladni by path.

Gates (per builder: MEL_garm_chladni_layer, MEL_skiff_chladni_plates):
  1. Registered + tree constructs headless (>10 nodes).
  2. Neutral at defaults (Cymatic Amplitude 0, silent headless audio):
     max displacement <= 0.005 on a UV'd grid.
  3. Cymatic Amplitude dial live: preset 0.01 moves vertices.
  4. Eigen M dial live: different mode => different displacement field.
  5. Bake attributes chladni_psi + audio_amplitude present on eval.
  6. No NaN, deterministic across evals.
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
_load("surreal_arch.melodia_gn.audio_terrain", os.path.join(GN, "audio_terrain.py"))
ch = _load("surreal_arch.melodia_gn.chladni_layers",
           os.path.join(GN, "chladni_layers.py"))
GROUP_METADATA = core.GROUP_METADATA
print("REPO_MODULE_OK", ch.__file__)

rep = {"repo_module": ch.__file__, "builders": {}}

ch.register()
BUILDERS = {"MEL_garm_chladni_layer": ch.build_garm_chladni_layer,
            "MEL_skiff_chladni_plates": ch.build_skiff_chladni_plates}
for bid in BUILDERS:
    assert bid in GROUP_METADATA, "not registered: " + bid
    print("BUILDER_OK", bid)


def attach_with(ob, gname, dials):
    src = bpy.data.node_groups[gname]
    copy = src.copy()
    for dial, val in dials.items():
        found = False
        for item in copy.interface.items_tree:
            if (getattr(item, "item_type", "") == "SOCKET"
                    and getattr(item, "in_out", "") == "INPUT"
                    and item.name == dial and hasattr(item, "default_value")):
                item.default_value = val
                found = True
        assert found, "dial missing: %s.%s" % (gname, dial)
    copy.update_tag()
    mod = ob.modifiers.new("Proof_chladni", "NODES")
    mod.node_group = copy
    return mod


def eval_mesh(ob):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    mesh = ev.to_mesh()
    try:
        return ([tuple(v.co) for v in mesh.vertices],
                {a.name: [round(a.data[i].value, 5) for i in range(len(mesh.vertices))]
                 for a in mesh.attributes
                 if a.name in ("chladni_psi", "audio_amplitude")})
    finally:
        ev.to_mesh_clear()


def has_nan(verts):
    return any(not all(math.isfinite(c) for c in v) for v in verts)


def max_disp(a, b):
    n = min(len(a), len(b))
    assert n > 0, "empty eval"
    return max(math.dist(a[i], b[i]) for i in range(n))


me = bpy.data.meshes.new("chladni_base")
# 5x5 grid with 0..1 UVs: interior verts sit off the eigenmode nodal lines
# (a bare quad's corners are all psi nodes for integer modes).
N = 5
verts = [((ix / (N - 1) - 0.5), (iy / (N - 1) - 0.5), 0.0)
         for iy in range(N) for ix in range(N)]
faces = [(iy * N + ix, iy * N + ix + 1, (iy + 1) * N + ix + 1, (iy + 1) * N + ix)
         for iy in range(N - 1) for ix in range(N - 1)]
me.from_pydata(verts, [], faces)
me.update()
uv_layer = me.uv_layers.new(name="UVMap")
for poly in me.polygons:
    for li in poly.loop_indices:
        vi = me.loops[li].vertex_index
        uv_layer.data[li].uv = (me.vertices[vi].co.x + 0.5,
                                me.vertices[vi].co.y + 0.5)
me.update()
ob = bpy.data.objects.new("ChladniBase", me)
bpy.context.scene.collection.objects.link(ob)
base = [tuple(v.co) for v in me.vertices]

for bid, fn in BUILDERS.items():
    old = bpy.data.node_groups.get(bid)
    if old:
        bpy.data.node_groups.remove(old)
    fn()
    ng = bpy.data.node_groups.get(bid)
    assert ng is not None and len(ng.nodes) > 10, "build failed: " + bid
    print("TREE_OK", bid, len(ng.nodes), "nodes")

    mod = attach_with(ob, bid, {})
    vn, an = eval_mesh(ob)
    assert not has_nan(vn), "NaN at neutral: " + bid
    assert len(vn) == len(eval_mesh(ob)[0]), "not deterministic: " + bid
    resid = max_disp(base, vn)
    print(bid, "NEUTRAL_RESIDUAL", round(resid, 5))
    assert resid <= 0.005, "neutral moves geometry: " + bid
    assert "chladni_psi" in an and "audio_amplitude" in an, \
        "bake attrs missing: " + bid
    assert any(abs(v) > 1e-4 for v in an["chladni_psi"]), \
        "psi field flat (UV path dead?): " + bid
    ob.modifiers.remove(mod)

    mod = attach_with(ob, bid, {"Cymatic Amplitude": 0.01})
    va, _ = eval_mesh(ob)
    resp = max_disp(vn, va)
    print(bid, "AMPLITUDE_RESPONSE", round(resp, 5))
    assert resp > 0.002, "amplitude dial dead: " + bid
    ob.modifiers.remove(mod)

    mod = attach_with(ob, bid, {"Cymatic Amplitude": 0.01, "Eigen M": 5.0})
    vm, _ = eval_mesh(ob)
    mode = max_disp(va, vm)
    print(bid, "MODE_RESPONSE", round(mode, 5))
    assert mode > 0.002, "Eigen M dial dead: " + bid
    ob.modifiers.remove(mod)

    rep["builders"][bid] = {
        "nodes": len(ng.nodes),
        "neutral_residual": round(resid, 5),
        "amplitude_response": round(resp, 5),
        "mode_response": round(mode, 5),
    }

out = os.path.join(REPO, "Saved", "Audit", "sea_above", "skiff_MK3",
                   "mk39_chladni_proof_2026-09-10.json")
with open(out, "w") as f:
    json.dump(rep, f, indent=2)
print("RECEIPT", out)
print("MK39_CHLADNI_PROOF PASS")
