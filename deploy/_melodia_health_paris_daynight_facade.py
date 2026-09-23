"""Headless verification for GN_PARIS_DayNightFacade (the duality slider).

Checks what a green build cannot show:

  * the tree builds, and core.link_failures() is empty for it;
  * ROUND / FLOOR / DIVIDE took (the grid + lit-count maths is index-driven, so
    a silently-defaulted op would misplace every window);
  * every declared param is a real interface socket;
  * the group evaluates to real geometry;
  * Night Mix=0 vs 1 CHANGES the build (the dark/lit split is live), and the
    counts derived from it do not error when it is 0 or 1 (empty streams);
  * optional pieces remove geometry when off (no hidden stubs);
  * Shutter Open rotates panels WITHOUT changing vertex count (a swing, not a
    rebuild - the same shape law as the ladder's Join Error).

Usage:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
      --background --factory-startup --python deploy/_melodia_health_paris_daynight_facade.py

Exit 0 only when build, links, operations, evaluation and toggles all pass.
"""
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY = os.path.dirname(os.path.abspath(__file__))
APPDATA_ADDONS = os.path.join(os.environ["APPDATA"], "Blender Foundation",
                              "Blender", "5.2", "scripts", "addons")

if os.environ.get("MELODIA_AUDIT_LIVE") == "1":
    sys.path.insert(0, APPDATA_ADDONS)
else:
    sys.path.insert(0, DEPLOY)          # checkout wins -> verifies uncommitted work
    sys.path.append(APPDATA_ADDONS)

import bpy  # noqa: E402
from surreal_arch.melodia_gn import core  # noqa: E402
from surreal_arch.melodia_gn import paris_daynight_facade  # noqa: E402,F401

BUILDER_ID = "GN_PARIS_DayNightFacade"
EXPECTED_MATH = (("ROUND", 1), ("FLOOR", 1), ("DIVIDE", 6), ("MULTIPLY", 20),
                 ("ADD", 20), ("SUBTRACT", 8), ("MAXIMUM", 2))
EXPECTED_BOOL = (("NOT", 6),)
EXPECTED_PARAMS = (
    "Bay Count", "Floor Count", "Bay Width", "Floor Height", "Wall Depth",
    "Plinth Height", "Window Width", "Window Height", "Window Base",
    "Window Recess", "Muntins", "Muntin Bars", "Night Mix", "Lit Pop",
    "Brass Trim", "Shutters", "Shutter Open", "Balconies", "Balcony Bars",
    "Rail Height", "Dentils", "Dentil Size", "Flower Boxes", "Bloom Count",
    "Bloom Size", "Portal Width", "Oculus", "Birds", "Bird Size",
    "Bird Lock", "Seed",
)

problems = []
notes = []


def set_param(tree, name, value):
    for item in tree.interface.items_tree:
        if (getattr(item, "name", "") == name
                and getattr(item, "in_out", "") == "INPUT"):
            try:
                item.default_value = value
                return True
            except Exception:
                return False
    return False


def eval_stats(tree):
    mesh = bpy.data.meshes.new("MEL_FacadeProbeMesh")
    obj = bpy.data.objects.new("MEL_FacadeProbe", mesh)
    bpy.context.scene.collection.objects.link(obj)
    mod = obj.modifiers.new("GNProbe", "NODES")
    mod.node_group = tree
    deps = bpy.context.evaluated_depsgraph_get()
    deps.update()
    ev = obj.evaluated_get(deps)
    m = ev.to_mesh()
    verts, polys = len(m.vertices), len(m.polygons)
    lo = hi = None
    if verts:
        xs = [v.co for v in m.vertices]
        lo = tuple(min(c[i] for c in xs) for i in range(3))
        hi = tuple(max(c[i] for c in xs) for i in range(3))
    ev.to_mesh_clear()
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(mesh)
    return verts, polys, lo, hi


print(f"[facade-health] builder={BUILDER_ID}")

if BUILDER_ID not in core.GROUP_BUILDERS:
    problems.append(f"{BUILDER_ID} is not registered (module not imported?)")
    tree = None
else:
    core.reset_link_failures()
    try:
        res = core.GROUP_BUILDERS[BUILDER_ID]()
        tree = res[0] if isinstance(res, (tuple, list)) else res
    except Exception as exc:
        problems.append(f"build raised {type(exc).__name__}: {exc}")
        tree = None

if tree is not None:
    print(f"[facade-health] tree='{tree.name}' nodes={len(tree.nodes)}")

    fails = core.link_failures()
    mine = fails.get(tree.name) or []
    if mine:
        for msg in mine:
            problems.append("dropped link: " + msg)
    else:
        notes.append("link_failures: none for this tree")

    math_ops, bool_ops = {}, {}
    for node in tree.nodes:
        if node.bl_idname == "ShaderNodeMath":
            math_ops[node.operation] = math_ops.get(node.operation, 0) + 1
        elif node.bl_idname == "FunctionNodeBooleanMath":
            bool_ops[node.operation] = bool_ops.get(node.operation, 0) + 1
    for op, need in EXPECTED_MATH:
        got = math_ops.get(op, 0)
        if got < need:
            problems.append(f"math op '{op}' used {got}x, expected >= {need} "
                            f"(assignment silently rejected?)")
    for op, need in EXPECTED_BOOL:
        got = bool_ops.get(op, 0)
        if got < need:
            problems.append(f"boolean op '{op}' used {got}x, expected >= {need}")
    notes.append(f"math ops={sorted(math_ops.items())} bool ops={sorted(bool_ops.items())}")

    have = set()
    for item in tree.interface.items_tree:
        if getattr(item, "in_out", "") == "INPUT":
            have.add(getattr(item, "name", ""))
    missing = [p for p in EXPECTED_PARAMS if p not in have]
    if missing:
        problems.append(f"params missing from group inputs: {missing}")
    else:
        notes.append(f"params: {len(EXPECTED_PARAMS)}/{len(EXPECTED_PARAMS)} present "
                     f"(interface inputs total={len(have)})")

    base = None
    try:
        base = eval_stats(tree)
        notes.append(f"verts/polys (defaults): {base[0]}/{base[1]}")
        if base[0] <= 0:
            problems.append("group evaluates to EMPTY geometry")
        elif base[0] < 3000:
            problems.append(f"only {base[0]} verts - a five-bay facade is "
                            "thousands; part of the build is missing")
    except Exception as exc:
        problems.append(f"evaluation failed: {type(exc).__name__}: {exc}")

    # Night Mix: 0 (all dark) vs 0.5 vs 1 (all lit) must change the build and
    # must not error at the extremes (empty dark or lit streams).
    try:
        counts = {}
        for mix in (0.0, 0.5, 1.0):
            set_param(tree, "Night Mix", mix)
            counts[mix] = eval_stats(tree)[0]
        notes.append(f"night mix verts: 0.0={counts[0.0]} 0.5={counts[0.5]} "
                     f"1.0={counts[1.0]}")
        if counts[0.0] == counts[1.0]:
            problems.append("Night Mix 0 and 1 give identical vertex counts - "
                            "the lit/dark window split is not live")
        if counts[0.0] <= 0 or counts[1.0] <= 0:
            problems.append("Night Mix extreme evaluates empty - the grid "
                            "streams error at 0 or 1")
        set_param(tree, "Night Mix", 0.0)
    except Exception as exc:
        problems.append(f"night-mix probe failed: {type(exc).__name__}: {exc}")

    # layout dials scale the build
    try:
        set_param(tree, "Bay Count", 2)
        bays2 = eval_stats(tree)[0]
        set_param(tree, "Bay Count", 5)
        bays5 = eval_stats(tree)[0]
        set_param(tree, "Floor Count", 1)
        fl1 = eval_stats(tree)[0]
        set_param(tree, "Floor Count", 3)
        fl3 = eval_stats(tree)[0]
        notes.append(f"bays 2->{bays2} 5->{bays5}; floors 1->{fl1} 3->{fl3}")
        if not (bays2 < bays5):
            problems.append("Bay Count does not add geometry")
        if not (fl1 < fl3):
            problems.append("Floor Count does not add geometry")
    except Exception as exc:
        problems.append(f"layout probe failed: {type(exc).__name__}: {exc}")

    # optional pieces remove geometry when off (no hidden stubs)
    try:
        deltas = {}
        for name in ("Shutters", "Balconies", "Flower Boxes", "Muntins"):
            set_param(tree, name, True)
            on = eval_stats(tree)[0]
            set_param(tree, name, False)
            off = eval_stats(tree)[0]
            set_param(tree, name, True)
            deltas[name] = on - off
        notes.append(f"toggle deltas: {deltas}")
        for name, delta in deltas.items():
            if delta < 50:
                problems.append(f"{name} off removes only {delta} verts - "
                                "optional pattern leaves a stub or dropped link")
    except Exception as exc:
        problems.append(f"toggle probe failed: {type(exc).__name__}: {exc}")

    # birds flock: 0 vs 14 on both streams
    try:
        set_param(tree, "Birds", 0)
        birds0 = eval_stats(tree)[0]
        set_param(tree, "Birds", 14)
        birds14 = eval_stats(tree)[0]
        notes.append(f"birds: 0 -> {birds0}, 14 -> {birds14} "
                     f"(delta {birds14 - birds0})")
        if birds14 - birds0 < 300:
            problems.append("the bird frieze adds almost nothing - the two "
                            "flocks are not instancing")
    except Exception as exc:
        problems.append(f"bird probe failed: {type(exc).__name__}: {exc}")

    # Shutter Open: a swing, not a rebuild - and the swing must be visible
    try:
        set_param(tree, "Shutter Open", 0.0)
        shut0 = eval_stats(tree)
        set_param(tree, "Shutter Open", 0.5)
        shut5 = eval_stats(tree)
        set_param(tree, "Shutter Open", 1.0)
        shut1 = eval_stats(tree)
        set_param(tree, "Shutter Open", 0.0)
        notes.append(f"shutter open: 0.0 -> {shut0[0]}v ymax {shut0[3][1]:.3f}; "
                     f"0.5 -> {shut5[0]}v ymax {shut5[3][1]:.3f}; "
                     f"1.0 -> {shut1[0]}v ymax {shut1[3][1]:.3f}")
        if shut0[0] != shut1[0]:
            problems.append("Shutter Open changed the vertex count - it must "
                            "swing the panels, not rebuild them")
        if shut5[3][1] - shut0[3][1] < 0.10:
            problems.append("Shutter Open 0.5 does not push the panels out "
                            f"(ymax delta {shut5[3][1] - shut0[3][1]:.3f}) - "
                            "the swing is a no-op")
    except Exception as exc:
        problems.append(f"shutter probe failed: {type(exc).__name__}: {exc}")

for n in notes:
    print(f"[facade-health] {n}")
for p in problems:
    print(f"[facade-health] PROBLEM: {p}")

print(f"[facade-health] problems={len(problems)}")
if problems:
    raise SystemExit(1)
print("[facade-health] PASS")
