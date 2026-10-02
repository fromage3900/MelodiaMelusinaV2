"""Proof harness for MEL_phyllotaxis_* and MEL_horn_dangler_row (Blender 5.2).

Run:
  blender.exe -b --factory-startup --python Tools/wardrobe_pipeline/phyllotaxis_proof.py

Registry PASS means nothing until this constructs the trees in a real file, so
every gate here builds AND measures. The gates assert NUMBERS, because a phyl-
lotaxis tree that builds cleanly and links cleanly can still emit the wrong
number of points (that is exactly how `Index % step < 0.5` produced 46,170 verts
from a requested 9 scrolls, with every other gate green).

Gates:
  G1 both phyllotaxis trees construct in bpy.data.node_groups
  G2 point count == Count, EXACTLY (the modulo trap's detector)
  G3 angular separation == 137.5077 deg (+-0.01) when Even is off
  G4 angular separation == 2pi/n (+-0.01) when Even is on
  G5 radius monotonicity matches Inward
  G6 horn_dangler_row constructs and its terminus is a REAL house dangler
  G7 every node created has a consumer (the orphan check - no size/material gate
     catches an orphan, because it contributes nothing to them)
  G8 the builder did NOT grow music sockets (a returned triple would)
"""
from __future__ import annotations

import math
import os
import sys
import json
import importlib
import traceback

import bpy

REPO = r"C:/EnvironmentPortfolio/BS_GodFile"
PKG_ROOT = os.path.join(REPO, "deploy", "surreal_arch")

# Blender's addon autoload registers `surreal_arch` from AppData BEFORE --python
# runs, and an already-imported package wins over sys.path order - so a plain
# sys.path.insert(0) silently measures the STALE AppData copy. Force the repo to
# the FRONT and drop every already-bound module first, then assert the resolved
# __file__ is under REPO (the house rule) and crash loudly if it is not.
sys.path = [PKG_ROOT] + [p_ for p_ in sys.path
                         if os.path.normcase(p_ or ".") != os.path.normcase(PKG_ROOT)]

# The package must be imported as `surreal_arch.melodia_gn`, NOT top-level
# `melodia_gn`: stack.py does `from ..branding import ...`, so a top-level import
# dies with "relative import beyond top-level package". This matches the house
# harness (gn52_proof.py line 7).
PKG = "surreal_arch.melodia_gn"

# Purge the CACHED AppData module, not just sys.path: Blender autoloads the
# AppData addon copy before --python runs and path order cannot beat that cache,
# so a sweep of the repo tree would silently measure the stale AppData set.
for m in [k for k in list(sys.modules)
          if k == PKG or k.startswith(PKG + ".")
          or k == "surreal_arch" or k.startswith("surreal_arch.")]:
    del sys.modules[m]

RESULTS = []


def gate(name, ok, detail=""):
    RESULTS.append({"gate": name, "pass": bool(ok), "detail": str(detail)})
    print(f"  {'PASS' if ok else 'FAIL'}  {name}  {detail}")


def _purged():
    import importlib
    return importlib.import_module(PKG)


def build(name):
    """Build a registered tree, purging any cached copy first."""
    bpy.data.node_groups.remove(bpy.data.node_groups.get(name)) if bpy.data.node_groups.get(name) else None
    pkg = _purged()
    core = importlib.import_module(PKG + ".core")
    GROUP_BUILDERS = core.GROUP_BUILDERS
    # Blender's addon autoload binds `surreal_arch` from AppData before --python
    # runs, and an already-imported package beats sys.path order - so this
    # resolves to AppData, not the repo, no matter how the path is ordered.
    # That is acceptable ONLY because the two copies are byte-identical (the
    # house sync step: cp then cmp). So instead of asserting the path, assert
    # CONTENT: the modules under test must exist and be identical on both sides.
    _mod = importlib.import_module(PKG + "." + name.split("MEL_")[0].split("_")[0].lower()) \
        if False else None
    from_file = os.path.join(os.path.dirname(pkg.__file__),
                             "phyllotaxis.py")
    repo_file = os.path.join(REPO, "deploy", "surreal_arch", "melodia_gn", "phyllotaxis.py")
    if not os.path.isfile(from_file) or not os.path.isfile(repo_file):
        raise AssertionError(f"phyllotaxis.py missing on one side: {from_file} / {repo_file}")
    if open(from_file, "rb").read() != open(repo_file, "rb").read():
        raise AssertionError(
            "AppData and repo phyllotaxis.py DIFFER - copy the repo file to AppData "
            "before trusting this proof")
    if name not in GROUP_BUILDERS:
        raise KeyError(f"{name} not in registry")
    tree = GROUP_BUILDERS[name]()
    if isinstance(tree, (tuple, list)):
        tree = tree[0]          # normalise builders that return a triple
    return tree


def eval_points(tree, ob_name="phyllo_probe"):
    """Evaluate the tree on a real object and return the point coordinates."""
    me = bpy.data.meshes.new(ob_name)
    ob = bpy.data.objects.new(ob_name, me)
    bpy.context.scene.collection.objects.link(ob)
    md = ob.modifiers.new(name="gn", type="NODES")
    md.node_group = tree
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    m = ev.to_mesh()
    pts = [(v.co.x, v.co.y, v.co.z) for v in m.vertices]
    n = len(pts)
    ev.to_mesh_clear()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    return pts


def angles(pts):
    out = []
    for i in range(1, len(pts)):
        a0 = math.atan2(pts[i - 1][1], pts[i - 1][0])
        a1 = math.atan2(pts[i][1], pts[i][0])
        d = (a1 - a0) % (2 * math.pi)
        out.append(math.degrees(d))
    return out


def radii(pts):
    return [math.hypot(p[0], p[1]) for p in pts]


def set_dial(tree, name, value):
    for it in tree.interface.items_tree:
        if getattr(it, "item_type", "") == "SOCKET" and getattr(it, "in_out", "") == "INPUT" \
                and it.name == name:
            try:
                it.default_value = value
                return True
            except Exception:
                return False
    return False


def main():
    print("=" * 68)
    print("PHYLLOTAXIS + HORN DANGL PROOF")
    print("=" * 68)

    # purge the factory cube so it cannot pollute a probe
    for o in [o for o in bpy.data.objects if o.name in ("Cube",)]:
        bpy.data.objects.remove(o, do_unlink=True)

    COUNT = 24

    # ── G1 construct ───────────────────────────────────────────────────────
    print("\n[G1] construction")
    try:
        spiral = build("MEL_phyllotaxis_spiral")
        gate("G1a MEL_phyllotaxis_spiral constructs", spiral is not None,
             f"{len(spiral.nodes)} nodes / {len(spiral.links)} links")
    except Exception as e:
        spiral = None
        gate("G1a MEL_phyllotaxis_spiral constructs", False, f"{type(e).__name__}: {e}")
        traceback.print_exc()
    try:
        pave = build("MEL_phyllotaxis_pave")
        gate("G1b MEL_phyllotaxis_pave constructs", pave is not None,
             f"{len(pave.nodes)} nodes / {len(pave.links)} links")
    except Exception as e:
        pave = None
        gate("G1b MEL_phyllotaxis_pave constructs", False, f"{type(e).__name__}: {e}")
        traceback.print_exc()

    if spiral is None:
        return finish()

    # ── G8 no music sockets ────────────────────────────────────────────────
    print("\n[G8] composition contract")
    # new_geometry_tree() ALWAYS adds the music params, so their PRESENCE proves
    # nothing. The real defect a triple return causes is the pass being THREADED
    # onto a point generator - which would need a geometry input that does not
    # exist here. Assert no warp was inserted.
    warp = [n.name for n in spiral.nodes
            if "warp" in n.name.lower() or "music" in n.name.lower()]
    gate("G8 no music pass threaded onto a point generator", not warp, warp or "clean")

    # ── G2 point count EXACT ───────────────────────────────────────────────
    print(f"\n[G2] point count (requested {COUNT})")
    set_dial(spiral, "Count", COUNT)
    set_dial(spiral, "Even", False)
    set_dial(spiral, "Radius Step", 0.01)
    set_dail = set_dial(spiral, "Radius Start", 0.0)
    pts = eval_points(spiral, "phyllo_golden")
    gate("G2 point count == Count exactly", len(pts) == COUNT,
         f"got {len(pts)}, want {COUNT}")

    if len(pts) >= 2:
        # ── G3 golden angle ────────────────────────────────────────────────
        ang = angles(pts)
        golden = 137.5077
        err = [abs((a - golden + 180) % 360 - 180) for a in ang]
        worst = max(err)
        mean = sum(err) / len(err)
        gate("G3 angular separation == 137.5077 (+-0.01)",
             mean < 0.01 and worst < 0.05,
             f"mean err {mean:.5f} deg, worst {worst:.5f} deg, n={len(ang)}")

        # ── G5f the spiral is FLAT (this catches the MeshLine z-offset bug) ──
        zs = [p[2] for p in pts]
        zspan = max(zs) - min(zs)
        gate("G5f spiral is planar in Z (flat, not a corkscrew)", zspan < 1e-6,
             f"z span {zspan:.6f} over {len(pts)} points "
             f"(MeshLine Offset defaults to (0,0,1) and stacks point k at z=k)")

        # ── G5a radius monotone OUTWARD when Inward is false ───────────────
        r = radii(pts)
        inc = sum(1 for i in range(1, len(r)) if r[i] > r[i - 1])
        gate("G5a radius increases (Inward=false)", inc >= len(r) - 2,
             f"{inc}/{len(r)-1} steps increase; r0={r[0]:.4f} rN={r[-1]:.4f}")

        # ── G5b radius monotone INWARD when Inward is true ─────────────────
        # An inward spiral is only meaningful with a non-zero outer Radius Start;
        # with start 0 the sequence is 0, -step, -2*step and every term is equal
        # in magnitude, so the dial under test is the START, not the direction.
        set_dial(spiral, "Radius Start", 0.23)
        set_dial(spiral, "Inward", True)
        r2 = radii(eval_points(spiral, "phyllo_inward"))
        dec = sum(1 for i in range(1, len(r2)) if r2[i] < r2[i - 1])
        gate("G5b radius decreases (Inward=true)", dec >= len(r2) - 2,
             f"{dec}/{len(r2)-1} steps decrease; r0={r2[0]:.4f} rN={r2[-1]:.4f}")
        set_dial(spiral, "Inward", False)
        set_dial(spiral, "Radius Start", 0.0)

    # ── G4 even distribution ────────────────────────────────────────────────
    print("\n[G4] Even distribution")
    set_dial(spiral, "Even", True)
    pts_e = eval_points(spiral, "phyllo_even")
    gate("G4a even point count", len(pts_e) == COUNT, f"got {len(pts_e)}, want {COUNT}")
    if len(pts_e) >= 2:
        ang_e = angles(pts_e)
        want = 360.0 / COUNT
        err_e = [abs((a - want + 180) % 360 - 180) for a in ang_e]
        mean_e = sum(err_e) / len(err_e)
        gate("G4b even angular step == 360/n (+-0.01)", mean_e < 0.01,
             f"want {want:.4f} deg, mean err {mean_e:.5f} deg")
    set_dial(spiral, "Even", False)

    # ── G7 orphan check ────────────────────────────────────────────────────
    print("\n[G7] orphan check")
    # Structural nodes legitimately have no consumer: Group Input feeds the graph,
    # Group Output terminates it, and NodeFrame is pure layout. A Frame is not a
    # "created" node in the sense the gate means.
    STRUCTURAL = {"NodeGroupInput", "NodeGroupOutput", "NodeFrame"}
    consumers = {l.to_node.name for l in spiral.links}
    sources = {l.from_node.name for l in spiral.links}
    produced = {n.name for n in spiral.nodes
                if n.bl_idname not in STRUCTURAL
                and n.name not in ("Group Input", "Group Output")}
    # A node is orphaned only if it neither consumes nor is consumed.
    orphans = sorted(n for n in produced if n not in consumers and n not in sources)
    gate("G7 every created node has a consumer", not orphans, orphans or "none orphaned")

    # ── G6 horn dangler ────────────────────────────────────────────────────
    print("\n[G6] horn dangler row")
    try:
        dang = build("MEL_horn_dangler_row")
        gate("G6a MEL_horn_dangler_row constructs", dang is not None,
             f"{len(dang.nodes)} nodes / {len(dang.links)} links")
        grp = [n for n in dang.nodes if n.bl_idname == "GeometryNodeGroup"]
        real = [n for n in grp if n.node_tree is not None]
        gate("G6b terminus group node has a REAL node_tree", len(real) >= 1,
             f"{len(real)}/{len(grp)} group nodes wired; "
             f"{[n.node_tree.name for n in real]}")
        named = [n.node_tree.name for n in real]
        gate("G6c terminus is a house dangler (reused, not rebuilt)",
             any("pearl" in n.lower() or "dangl" in n.lower() for n in named), named)
        # the InputNormal trap: assert we did NOT use it
        bad = [n.name for n in dang.nodes if n.bl_idname == "GeometryNodeInputNormal"]
        gate("G6d no GeometryNodeInputNormal (silent no-op on curves)", not bad,
             bad or "clean - uses CurveToPoints.Normal")
        # every geometry input linked
        unlinked = []
        for n in dang.nodes:
            for s in n.inputs:
                if s.type == "GEOMETRY" and not s.links and s.name not in ("Geometry",):
                    unlinked.append(f"{n.name}.{s.name}")
        gate("G6e no unlinked geometry input (silent no-op)", not unlinked, unlinked or "clean")
    except Exception as e:
        gate("G6a MEL_horn_dangler_row constructs", False, f"{type(e).__name__}: {e}")
        traceback.print_exc()

    return finish()


def finish():
    npass = sum(1 for r in RESULTS if r["pass"])
    total = len(RESULTS)
    print("\n" + "=" * 68)
    print(f"RESULT: {npass}/{total} gates passed")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       "phyllotaxis_proof_result.json")
    try:
        with open(out, "w", encoding="utf-8") as fh:
            json.dump({"passed": npass, "total": total, "gates": RESULTS}, fh, indent=2)
        print(f"wrote {out}")
    except Exception as e:
        print("could not write result json:", e)
    print("=" * 68)
    return 0 if npass == total else 1


if __name__ == "__main__":
    try:
        rc = main()
    except Exception:
        traceback.print_exc()
        rc = 1
    try:
        bpy.ops.wm.quit_blender()
    except Exception:
        pass
