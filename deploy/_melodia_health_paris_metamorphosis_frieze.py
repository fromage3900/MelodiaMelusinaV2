"""Headless verification for GN_PARIS_MetamorphosisFrieze (the morph band).

Checks: build + links + op census (ROUND / MINIMUM drive the three cell
windows - a silently-rejected op would misplace every motif), all params as
real sockets, real geometry, and the morph behaviour: Morph 0 = all birds,
1 = all fish (different vert counts - the species differ), the seam ADDS both
species on shared cells, and the bead rail toggles cleanly.

Usage:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
      --background --factory-startup --python deploy/_melodia_health_paris_metamorphosis_frieze.py
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
    sys.path.insert(0, DEPLOY)
    sys.path.append(APPDATA_ADDONS)

import bpy  # noqa: E402
from surreal_arch.melodia_gn import core  # noqa: E402
from surreal_arch.melodia_gn import paris_metamorphosis_frieze  # noqa: E402,F401

BUILDER_ID = "GN_PARIS_MetamorphosisFrieze"
EXPECTED_MATH = (("ROUND", 1), ("FLOOR", 1), ("MINIMUM", 2), ("DIVIDE", 2),
                 ("MULTIPLY", 15), ("ADD", 10), ("SUBTRACT", 8), ("MAXIMUM", 1))
EXPECTED_BOOL = (("NOT", 1),)
EXPECTED_PARAMS = (
    "Band Length", "Band Height", "Band Depth", "Cells", "Morph",
    "Seam Width", "Interlock", "Motif Scale", "Bird Wing Spread",
    "Fin Count", "Fish Flip", "Bead Rail", "Rail Beads", "Bead Size",
    "Reveal",
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
    mesh = bpy.data.meshes.new("MEL_FriezeProbeMesh")
    obj = bpy.data.objects.new("MEL_FriezeProbe", mesh)
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


print(f"[frieze-health] builder={BUILDER_ID}")

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
    print(f"[frieze-health] tree='{tree.name}' nodes={len(tree.nodes)}")

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
        elif base[0] < 500:
            problems.append(f"only {base[0]} verts - motifs + rail should be "
                            "thousands at defaults")
    except Exception as exc:
        problems.append(f"evaluation failed: {type(exc).__name__}: {exc}")

    # morph: all birds vs all fish must DIFFER (different species geometry)
    try:
        set_param(tree, "Morph", 0.0)
        birds = eval_stats(tree)[0]
        set_param(tree, "Morph", 1.0)
        fish = eval_stats(tree)[0]
        set_param(tree, "Morph", 0.5)
        notes.append(f"morph: birds-only {birds} verts, fish-only {fish} verts")
        if birds == fish:
            problems.append("Morph 0 and 1 give identical vert counts - the "
                            "species streams are not distinct")
    except Exception as exc:
        problems.append(f"morph probe failed: {type(exc).__name__}: {exc}")

    # seam: adds BOTH species on shared cells -> verts grow with Seam Width
    try:
        set_param(tree, "Seam Width", 0)
        seam0 = eval_stats(tree)[0]
        set_param(tree, "Seam Width", 3)
        seam3 = eval_stats(tree)[0]
        notes.append(f"seam: 0 -> {seam0} verts, 3 -> {seam3} "
                     f"(delta {seam3 - seam0})")
        if seam3 - seam0 < 100:
            problems.append("Seam Width adds almost nothing - the interlock "
                            "zone is not instancing both species")
    except Exception as exc:
        problems.append(f"seam probe failed: {type(exc).__name__}: {exc}")

    # rail: count + toggle
    try:
        set_param(tree, "Rail Beads", 0)
        beads_off = eval_stats(tree)[0]
        set_param(tree, "Rail Beads", 60)
        beads_on = eval_stats(tree)[0]
        set_param(tree, "Bead Rail", False)
        rail_off = eval_stats(tree)[0]
        set_param(tree, "Bead Rail", True)
        notes.append(f"rail beads: 0 -> {beads_off}, 60 -> {beads_on}; "
                     f"rail toggle off -> {rail_off}")
        if beads_on - beads_off < 2000:
            problems.append("60 rail beads add almost nothing - not instancing")
        if beads_on - rail_off < 2000:
            problems.append("Bead Rail off does not remove the beads - stub "
                            "or dropped link")
    except Exception as exc:
        problems.append(f"rail probe failed: {type(exc).__name__}: {exc}")

for n in notes:
    print(f"[frieze-health] {n}")
for p in problems:
    print(f"[frieze-health] PROBLEM: {p}")

print(f"[frieze-health] problems={len(problems)}")
if problems:
    raise SystemExit(1)
print("[frieze-health] PASS")
