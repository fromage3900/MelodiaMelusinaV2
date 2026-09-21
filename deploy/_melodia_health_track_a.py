"""Headless verification for the Paris Track A builders (FountainLoop, DayNightFacade).

Proves what py_compile cannot:

  * both builders register and both trees build;
  * core.link_failures() is EMPTY for both trees;
  * both trees EVALUATE to non-empty geometry via the depsgraph;
  * FountainLoop Wobble is live wiring: 0.0 still, 0.05 breathing, 0.25 strong;
  * DayNightFacade duality: 0.0 / 1.0 give two-level mirrored relief, 0.5 the
    flat Escher plate (single level), cluster gap = Relief;
  * every preset key of the new BUILDERS_PRESETS entries is a real input socket.

Run (Blender 5.2, factory startup):
  blender.exe --background --factory-startup --python deploy/_melodia_health_track_a.py

Exit 0 = PASS, 1 = FAIL.
"""
import importlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FAILURES = []


def check(name, ok, detail=""):
    print(("[PASS] " if ok else "[FAIL] ") + name + (f" -- {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


# Purge any AppData-autoloaded copies, then import from THIS checkout's deploy.
for m in [k for k in list(sys.modules) if k == "surreal_arch" or k.startswith("surreal_arch.")]:
    del sys.modules[m]
sys.path.insert(0, str(REPO / "deploy"))

import bpy  # noqa: E402

from surreal_arch.melodia_gn import core, paris_track_a  # noqa: E402

importlib.reload(paris_track_a)
assert str(Path(paris_track_a.__file__)).startswith(str(REPO)), (
    f"imported from {paris_track_a.__file__}, not this checkout")
print(f"[track-a] module source: {paris_track_a.__file__}")

for tree_name in ("GN_PARIS_FountainLoop", "GN_PARIS_DayNightFacade"):
    check(f"{tree_name} registered", tree_name in core.GROUP_BUILDERS)

tree_f, gin_f, gout_f = paris_track_a.build_paris_fountain_loop()
tree_d, gin_d, gout_d = paris_track_a.build_paris_day_night_facade()

for t in (tree_f, tree_d):
    try:
        lf = core.link_failures(t.name)
    except TypeError:
        lf = core.link_failures()
    except Exception as exc:  # noqa: BLE001
        lf = [f"link_failures error: {exc!r}"]
    check(f"{t.name} link failures empty", not lf, str(list(lf)[:4]))


def set_dial(tree, name, value):
    for item in tree.interface.items_tree:
        if (getattr(item, "item_type", "") == "SOCKET"
                and getattr(item, "in_out", "") == "INPUT"
                and item.name == name):
            item.default_value = value
            return True
    return False


def evaluate(tree):
    """Wire the tree to a 1-vert probe object and read evaluated geometry."""
    me = bpy.data.meshes.new("probe")
    me.from_pydata([(0.0, 0.0, 0.0)], [], [])
    ob = bpy.data.objects.new("probe", me)
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("probe", type="NODES")  # captures CURRENT defaults
    mod.node_group = tree
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    mesh = bpy.data.meshes.new_from_object(ev, depsgraph=dg)
    verts = [(v.co.x, v.co.y, v.co.z) for v in mesh.vertices]
    nv, np_ = len(mesh.vertices), len(mesh.polygons)
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(mesh)
    bpy.data.meshes.remove(me)
    return verts, nv, np_


def levels(coords, axis, tol=1e-3):
    """Distinct values along one axis (clustered by tol)."""
    vals = sorted({round(c[axis] / tol) * tol for c in coords})
    merged = []
    for v in vals:
        if not merged or v - merged[-1] > tol * 2:
            merged.append(v)
    return merged


# --- FountainLoop -----------------------------------------------------------
vf, nf, pf = evaluate(tree_f)
check("FountainLoop evaluates non-empty", nf > 100, f"verts={nf} polys={pf}")
xs = [v[0] for v in vf]
check("FountainLoop bounded", all(abs(c) < 3.0 for v in vf for c in v),
      f"x range {min(xs):.2f}..{max(xs):.2f}")

v_zero, _, _ = evaluate(tree_f)  # defaults (Wobble 0.0)
set_dial(tree_f, "Wobble", 0.05)
v_005, _, _ = evaluate(tree_f)
set_dial(tree_f, "Wobble", 0.25)
v_025, _, _ = evaluate(tree_f)
check("FountainLoop Wobble 0.0 == default eval", v_zero == vf)
check("FountainLoop Wobble 0.05 moves geometry", v_005 != v_zero)
check("FountainLoop Wobble 0.25 != 0.05", v_025 != v_005)

# --- DayNightFacade ---------------------------------------------------------
set_dial(tree_f, "Wobble", 0.0)  # leave the fountain tree as authored

relief = 0.06
set_dial(tree_d, "Duality", 0.0)
vd0, nd0, _ = evaluate(tree_d)
check("Facade Duality 0.0 evaluates", nd0 > 100, f"verts={nd0}")
lv0 = levels(vd0, 1)  # y axis: the stood grid's face-normal direction
set_dial(tree_d, "Duality", 0.5)
vd5, nd5, _ = evaluate(tree_d)
lv5 = levels(vd5, 1)
set_dial(tree_d, "Duality", 1.0)
vd1, nd1, _ = evaluate(tree_d)
lv1 = levels(vd1, 1)

check("Facade Duality 0.0 two-level relief", len(lv0) == 2, f"levels={lv0}")
check("Facade Duality 0.5 flat plate", len(lv5) == 1, f"levels={lv5}")
check("Facade Duality 1.0 two-level relief", len(lv1) == 2, f"levels={lv1}")
if len(lv0) == 2:
    gap0 = abs(lv0[1] - lv0[0])
    check("Facade relief gap = Relief", abs(gap0 - relief) < 0.005, f"gap={gap0:.4f}")
check("Facade Duality 0.0 != 1.0 (mirrored)", vd0 != vd1)

# --- preset keys are real sockets -------------------------------------------
sockets_f = {i.name for i in tree_f.interface.items_tree
             if getattr(i, "item_type", "") == "SOCKET"
             and getattr(i, "in_out", "") == "INPUT"}
sockets_d = {i.name for i in tree_d.interface.items_tree
             if getattr(i, "item_type", "") == "SOCKET"
             and getattr(i, "in_out", "") == "INPUT"}
try:
    from surreal_arch.melodia_gn.presets import BUILDERS_PRESETS
    for bid, sockets in (("GN_PARIS_FountainLoop", sockets_f),
                         ("GN_PARIS_DayNightFacade", sockets_d)):
        entry = BUILDERS_PRESETS.get(bid, {})
        for pname, params in (entry.get("presets") or {}).items():
            bad = [k for k in params if k not in sockets]
            check(f"{bid}/{pname} preset keys resolve", not bad, f"unknown: {bad}")
except Exception as exc:  # noqa: BLE001
    check("preset key audit", False, repr(exc))

print()
if FAILURES:
    print(f"TRACK A HEALTH: FAIL ({len(FAILURES)} problems)")
    sys.exit(1)
print("TRACK A HEALTH: PASS (problems=0)")
sys.exit(0)
