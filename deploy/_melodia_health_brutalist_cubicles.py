"""Headless verification for GN_BRUTALIST_CubicleFarm.

Checks the classes a green build hides: dropped links, silently-rejected math
ops (LESS_THAN drives the eight row guards - a bad name would keep every row
forever), declared params as real sockets, real geometry, and that the dials
do what they claim:
  * Rows down deletes whole rows (guarded instances, no hidden geometry);
  * Columns changes the per-row cell count;
  * Drift slides rows sideways WITHOUT rebuilding (same verts, moved bbox);
  * Monitor / Chair / Overhead Bin toggles remove their furniture;
  * Ceiling Grid removes beams + lights + slab;
  * Plants instancing adds geometry.

Usage:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
      --background --factory-startup --python deploy/_melodia_health_brutalist_cubicles.py

Exit 0 only when build, links, operations, evaluation and dials all pass.
"""
import os
import sys

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
from surreal_arch.melodia_gn import brutalist_cubicles  # noqa: E402,F401

BUILDER_ID = "GN_BRUTALIST_CubicleFarm"
EXPECTED_MATH = (("MULTIPLY", 12), ("ADD", 8), ("SUBTRACT", 10),
                 ("DIVIDE", 3), ("LESS_THAN", 8), ("MAXIMUM", 2))
EXPECTED_BOOL = (("NOT", 8),)
EXPECTED_PARAMS = (
    "Rows", "Columns", "Cell Width", "Cell Depth", "Partition Height",
    "Partition Thickness", "Desk Height", "Desk Depth", "Monitor",
    "Monitor Size", "Chair", "Overhead Bin", "Drift", "Ceiling Grid",
    "Grid Beams", "Ceiling Height", "Lights", "Plants",
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
    mesh = bpy.data.meshes.new("MEL_CubicleProbeMesh")
    obj = bpy.data.objects.new("MEL_CubicleProbe", mesh)
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


print(f"[cubicle-health] builder={BUILDER_ID}")

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
    print(f"[cubicle-health] tree='{tree.name}' nodes={len(tree.nodes)}")

    mine = (core.link_failures().get(tree.name) or [])
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
    notes.append(f"math ops={sorted(math_ops.items())} "
                 f"bool ops={sorted(bool_ops.items())}")

    have = set()
    for item in tree.interface.items_tree:
        if getattr(item, "in_out", "") == "INPUT":
            have.add(getattr(item, "name", ""))
    missing = [p for p in EXPECTED_PARAMS if p not in have]
    if missing:
        problems.append(f"params missing from group inputs: {missing}")
    else:
        notes.append(f"params: {len(EXPECTED_PARAMS)}/"
                     f"{len(EXPECTED_PARAMS)} present")

    base = None
    try:
        base = eval_stats(tree)
        notes.append(f"verts/polys (defaults): {base[0]}/{base[1]} bbox "
                     f"x {base[2][0]:.2f}..{base[3][0]:.2f} "
                     f"y {base[2][1]:.2f}..{base[3][1]:.2f} "
                     f"z {base[2][2]:.2f}..{base[3][2]:.2f}")
        if base[0] <= 0:
            problems.append("group evaluates to EMPTY geometry")
        elif base[0] < 600:
            problems.append(f"only {base[0]} verts - a 3x4 grid with desks, "
                            "monitors and a ceiling should carry more")
    except Exception as exc:
        problems.append(f"evaluation failed: {type(exc).__name__}: {exc}")

    # rows: guarded instances must delete whole rows
    try:
        set_param(tree, "Rows", 1)
        r1 = eval_stats(tree)
        set_param(tree, "Rows", 3)
        r3 = eval_stats(tree)
        set_param(tree, "Rows", 8)
        r8 = eval_stats(tree)
        notes.append(f"rows 1/3/8: {r1[0]}/{r3[0]}/{r8[0]} verts, "
                     f"ymin {r1[2][1]:.2f}/{r3[2][1]:.2f}/{r8[2][1]:.2f}")
        if not (r3[0] > r1[0] and r8[0] > r3[0]):
            problems.append("Rows does not scale geometry - guards or row "
                            "instances are broken")
        if not (r8[2][1] < r3[2][1] < r1[2][1]):
            problems.append("extra rows do not extend the grid (ymin does not "
                            "move) - row placement is wrong")
        set_param(tree, "Rows", 3)
    except Exception as exc:
        problems.append(f"rows probe failed: {type(exc).__name__}: {exc}")

    # columns
    try:
        set_param(tree, "Columns", 2)
        c2 = eval_stats(tree)[0]
        set_param(tree, "Columns", 6)
        c6 = eval_stats(tree)[0]
        notes.append(f"columns 2->6: {c2}->{c6} verts")
        if c6 - c2 < 100:
            problems.append("Columns does not add cells")
        set_param(tree, "Columns", 4)
    except Exception as exc:
        problems.append(f"columns probe failed: {type(exc).__name__}: {exc}")

    # drift: pure translation - same verts, moved bbox
    try:
        set_param(tree, "Drift", 0.0)
        d0 = eval_stats(tree)
        set_param(tree, "Drift", 1.0)
        d1 = eval_stats(tree)
        notes.append(f"drift 0->1: verts {d0[0]}->{d1[0]}, "
                     f"xmax {d0[3][0]:.2f}->{d1[3][0]:.2f}")
        if d0[0] != d1[0]:
            problems.append("Drift changed the vertex count - it must slide "
                            "rows, not rebuild")
        if not (d1[3][0] - d0[3][0] > 1.0):
            problems.append("Drift does not move the rows sideways - the "
                            "per-row offset maths is a no-op")
        set_param(tree, "Drift", 0.0)
    except Exception as exc:
        problems.append(f"drift probe failed: {type(exc).__name__}: {exc}")

    # furniture + ceiling toggles
    try:
        deltas = {}
        for name in ("Monitor", "Chair", "Overhead Bin"):
            set_param(tree, name, False)
            off = eval_stats(tree)[0]
            set_param(tree, name, True)
            on = eval_stats(tree)[0]
            deltas[name] = on - off
        set_param(tree, "Ceiling Grid", False)
        ceil_off = eval_stats(tree)[0]
        set_param(tree, "Ceiling Grid", True)
        ceil_on = eval_stats(tree)[0]
        deltas["Ceiling Grid"] = ceil_on - ceil_off
        set_param(tree, "Plants", 0)
        p0 = eval_stats(tree)[0]
        set_param(tree, "Plants", 3)
        p3 = eval_stats(tree)[0]
        deltas["Plants"] = p3 - p0
        notes.append(f"toggle deltas: {deltas}")
        for name, delta in deltas.items():
            # single-box furniture per cell: 4 cells is ~24-32 verts, so the
            # floor that proves "the toggle removes geometry" is 20, not 30
            if delta < 20:
                problems.append(f"{name} changes only {delta} verts - stub or "
                                "dropped link")
    except Exception as exc:
        problems.append(f"toggle probe failed: {type(exc).__name__}: {exc}")

for n in notes:
    print(f"[cubicle-health] {n}")
for p in problems:
    print(f"[cubicle-health] PROBLEM: {p}")

print(f"[cubicle-health] problems={len(problems)}")
if problems:
    raise SystemExit(1)
print("[cubicle-health] PASS")
