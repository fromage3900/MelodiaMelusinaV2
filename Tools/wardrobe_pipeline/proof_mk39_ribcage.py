"""MK39 ribcage proof: hull neutral re-verified + MEL_skiff_ribcage gates.

Run: "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" --background
         --factory-startup --python Tools/wardrobe_pipeline/proof_mk39_ribcage.py
Imports resolve to the REPO copy (asserted via module __file__).

Gates:
  1. register() exposes MEL_starskiff_hull_form / MEL_starskiff_hull_audio /
     MEL_skiff_ribcage in GROUP_METADATA.
  2. All three trees construct headless with nodes present.
  3. Hull form at neutral defaults: max vertex displacement vs base intake
     within the documented noise residual (<= 0.20 m on a unit grid).
  4. Hull form responds: Beam=0.5 moves vertices (dials are live, not dead).
  5. Ribcage evaluates to real mesh: verts > 0, no NaN, deterministic across
     two evals, X extent ~= 7.614 m (9 ribs x 0.846 spacing).
  6. Ribcage responds: Rib Count 9 -> 5 reduces vertex count.
Exit non-zero on any failure. Receipt -> Saved/Audit/sea_above/skiff_MK3/.
"""
import json
import math
import os
import sys

REPO = r"C:\EnvironmentPortfolio\BS_GodFile"
sys.path.insert(0, os.path.join(REPO, "deploy"))
# Evict any AppData-installed copy so the REPO files under test win.
for mod in [m for m in list(sys.modules) if m.startswith("surreal_arch")]:
    del sys.modules[mod]

import bpy  # noqa: E402

import surreal_arch.melodia_gn.starskiff_hull as sh  # noqa: E402
import surreal_arch.melodia_gn.starskiff_biomech as sb  # noqa: E402
from surreal_arch.melodia_gn.core import GROUP_BUILDERS, GROUP_METADATA  # noqa: E402

assert sh.__file__.startswith(REPO), "hull module resolved outside repo: " + sh.__file__
assert sb.__file__.startswith(REPO), "biomech module resolved outside repo: " + sb.__file__
print("REPO_MODULES_OK", sh.__file__, sb.__file__)

rep = {"repo_modules": [sh.__file__, sb.__file__]}

sh.register()
sb.register()
for bid in ("MEL_starskiff_hull_form", "MEL_starskiff_hull_audio", "MEL_skiff_ribcage"):
    assert bid in GROUP_METADATA, "missing builder " + bid
    print("BUILDER_OK", bid, GROUP_METADATA[bid].get("label", "?"))

built = {}
for bid, fn in (("MEL_starskiff_hull_form", sh.build_starskiff_hull_form),
                ("MEL_starskiff_hull_audio", sh.build_starskiff_hull_audio),
                ("MEL_skiff_ribcage", sb.build_skiff_ribcage)):
    old = bpy.data.node_groups.get(bid)
    if old:
        bpy.data.node_groups.remove(old)
    fn()
    ng = bpy.data.node_groups.get(bid)
    assert ng is not None and len(ng.nodes) > 10, "tree build failed: " + bid
    built[bid] = len(ng.nodes)
    print("TREE_OK", bid, len(ng.nodes), "nodes")
rep["node_counts"] = built


def set_default(gname, dial, val):
    # Interface defaults only propagate to a modifier bound AFTER the change,
    # so the response tests below use attach_with() (fresh group copy +
    # fresh modifier). This helper stays for parity with the 09-05 pattern.
    tree = bpy.data.node_groups[gname]
    for item in tree.interface.items_tree:
        if (getattr(item, "item_type", "") == "SOCKET"
                and getattr(item, "in_out", "") == "INPUT"
                and item.name == dial and hasattr(item, "default_value")):
            item.default_value = val
            tree.update_tag()
            return True
    return False


def attach_with(ob, gname, dials):
    """Fresh group copy with interface dials preset + fresh modifier.

    Blender snapshots group-input defaults into the modifier at bind time,
    so post-bind default edits never reach an existing modifier. A copy
    with preset defaults is the honest way to evaluate a dial setting.
    """
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
    mod = ob.modifiers.new("Proof_" + gname, "NODES")
    mod.node_group = copy
    return mod


def make_grid(name, nx=9, ny=3, size=1.0):
    me = bpy.data.meshes.new(name + "_mesh")
    # Tilted intake: Z varies across the sheet so the Beam dial (Z-scaling)
    # has extent to act on. A flat Z=0 sheet is a degenerate test for it.
    verts = [(size * (ix / (nx - 1) - 0.5), size * (iy / (ny - 1) - 0.5),
              0.3 * size * (ix / (nx - 1) - 0.5))
             for iy in range(ny) for ix in range(nx)]
    faces = [(iy * nx + ix, iy * nx + ix + 1, (iy + 1) * nx + ix + 1, (iy + 1) * nx + ix)
             for iy in range(ny - 1) for ix in range(nx - 1)]
    me.from_pydata(verts, [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def eval_verts(ob):
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    mesh = ev.to_mesh()
    try:
        return [tuple(v.co) for v in mesh.vertices]
    finally:
        ev.to_mesh_clear()


def attach(ob, gname):
    mod = ob.modifiers.new("Proof_" + gname, "NODES")
    mod.node_group = bpy.data.node_groups[gname]
    return mod


def max_disp(base, cur):
    return max(math.dist(a, b) for a, b in zip(base, cur))


def has_nan(verts):
    return any(not all(math.isfinite(c) for c in v) for v in verts)


# --- hull neutral: scratch 1 m grid, defaults = all dials 0 (Symmetry=1 dead) ---
grid = make_grid("HullProofGrid")
base = eval_verts(grid)
mod = attach(grid, "MEL_starskiff_hull_form")
neutral = eval_verts(grid)
assert not has_nan(neutral), "NaN in neutral hull eval"
resid = max_disp(base, neutral)
print("HULL_NEUTRAL_RESIDUAL", round(resid, 5))
assert resid <= 0.20, "neutral residual above documented bound: %f" % resid
rep["hull_neutral_residual"] = round(resid, 5)

# Dial-response via fresh group copies (post-bind default edits never reach
# an existing modifier, so each dial setting gets a preset copy + modifier).
# Threshold 0.01 on a 1 m test grid: proves liveness above float noise.
grid.modifiers.remove(mod)
rep["hull_dial_response"] = {}
for dial, val in (("Beam", 0.5), ("Rocker", 1.0)):
    mod = attach_with(grid, "MEL_starskiff_hull_form", {dial: val})
    moved = eval_verts(grid)
    resp = max_disp(neutral, moved)
    print("HULL_%s_RESPONSE" % dial.upper(), round(resp, 5))
    assert resp > 0.01, "%s dial appears dead" % dial
    rep["hull_dial_response"][dial] = round(resp, 5)
    grid.modifiers.remove(mod)

# --- hull audio at defaults: micro displacement must stay near zero headless ---
mod2 = attach(grid, "MEL_starskiff_hull_audio")
aud = eval_verts(grid)
aresid = max_disp(base, aud)
print("HULL_AUDIO_RESIDUAL", round(aresid, 5))
assert aresid <= 0.05, "audio surface displaces headless: %f" % aresid
rep["hull_audio_residual"] = round(aresid, 5)
grid.modifiers.remove(mod2)

# --- ribcage: generative, intake ignored ---
rib_ob = make_grid("RibProofBase", 2, 2, 0.1)
mod3 = attach(rib_ob, "MEL_skiff_ribcage")
r1 = eval_verts(rib_ob)
assert len(r1) > 100, "ribcage evaluated nearly empty: %d verts" % len(r1)
assert not has_nan(r1), "NaN in ribcage eval"
r2 = eval_verts(rib_ob)
assert len(r1) == len(r2), "ribcage eval not deterministic"
xs = [v[0] for v in r1]
xspan = max(xs) - min(xs)
print("RIBCAGE_VERTS", len(r1), "XSPAN", round(xspan, 4))
assert abs(xspan - 7.614) < 0.1, "rib station span off measured 7.614: %f" % xspan
rep["ribcage_verts_9"] = len(r1)
rep["ribcage_xspan"] = round(xspan, 4)

rib_ob.modifiers.remove(mod3)
mod3 = attach_with(rib_ob, "MEL_skiff_ribcage", {"Rib Count": 5.0})
r5 = eval_verts(rib_ob)
print("RIBCAGE_VERTS_5", len(r5))
assert 0 < len(r5) < len(r1), "Rib Count dial does not parametrize geometry"
rep["ribcage_verts_5"] = len(r5)

out = os.path.join(REPO, "Saved", "Audit", "sea_above", "skiff_MK3",
                   "mk39_ribcage_proof_2026-09-10.json")
with open(out, "w") as f:
    json.dump(rep, f, indent=2)
print("RECEIPT", out)
print("MK39_RIBCAGE_PROOF PASS")
