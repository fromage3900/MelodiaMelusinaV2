"""Headless verification for GN_PARIS_PenroseArch (the tribar doorway).

The dial that matters is `Impossibility`: at 0 the join blocks are flush
(honest arch); at +/-1 they slide in opposite y directions.  The probe proves
the blocks MOVE (bbox grows) while the vertex count stays identical - a slide,
not a rebuild - and that every optional piece really removes geometry.

Usage:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
      --background --factory-startup --python deploy/_melodia_health_paris_penrose_arch.py
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
from surreal_arch.melodia_gn import paris_penrose_arch  # noqa: E402,F401

BUILDER_ID = "GN_PARIS_PenroseArch"
EXPECTED_MATH = (("MULTIPLY", 15), ("ADD", 10), ("SUBTRACT", 5),
                 ("DIVIDE", 1), ("MAXIMUM", 1))
EXPECTED_BOOL = (("NOT", 6),)
EXPECTED_PARAMS = (
    "Arch Width", "Arch Height", "Jamb Width", "Jamb Depth", "Lintel Height",
    "Impossibility", "Swap Offset", "Keystone", "Keystone Size", "Plinths",
    "Plinth Height", "Brackets", "Bracket Size", "Crown", "Crown Size",
    "Panel", "Panel Size", "Door", "Door Panels",
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
    mesh = bpy.data.meshes.new("MEL_ArchProbeMesh")
    obj = bpy.data.objects.new("MEL_ArchProbe", mesh)
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


print(f"[arch-health] builder={BUILDER_ID}")

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
    print(f"[arch-health] tree='{tree.name}' nodes={len(tree.nodes)}")

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
        elif base[0] < 64:
            problems.append(f"only {base[0]} verts - jambs+lintel alone are 24; "
                            "part of the arch is missing")
    except Exception as exc:
        problems.append(f"evaluation failed: {type(exc).__name__}: {exc}")

    # Impossibility: blocks slide in opposite y directions - same verts, the
    # arch's y extent grows, and the two directions mirror each other
    try:
        set_param(tree, "Impossibility", 0.0)
        honest = eval_stats(tree)
        set_param(tree, "Impossibility", 1.0)
        swap_a = eval_stats(tree)
        set_param(tree, "Impossibility", -1.0)
        swap_b = eval_stats(tree)
        set_param(tree, "Impossibility", 0.0)
        span0 = honest[3][1] - honest[2][1]
        spanA = swap_a[3][1] - swap_a[2][1]
        spanB = swap_b[3][1] - swap_b[2][1]
        notes.append(f"impossibility y-span: 0.0={span0:.3f} "
                     f"+1={spanA:.3f} -1={spanB:.3f}")
        if honest[0] != swap_a[0] or honest[0] != swap_b[0]:
            problems.append("Impossibility changed the vertex count - the join "
                            "blocks must slide, not rebuild")
        if spanA - span0 < 0.25:
            problems.append("Impossibility +1 does not push the join blocks "
                            f"out of plane (span delta {spanA - span0:.3f}) - "
                            "the tribar read is a no-op")
        if abs(spanA - spanB) > 0.05:
            problems.append("+1 and -1 give different spans - the swap is not "
                            "symmetric (mirror direction expected)")
    except Exception as exc:
        problems.append(f"impossibility probe failed: {type(exc).__name__}: {exc}")

    # optional pieces remove geometry when off
    try:
        deltas = {}
        for name in ("Keystone", "Plinths", "Brackets", "Crown", "Panel",
                     "Door"):
            set_param(tree, name, True)
            on = eval_stats(tree)[0]
            set_param(tree, name, False)
            off = eval_stats(tree)[0]
            set_param(tree, name, True)
            deltas[name] = on - off
        notes.append(f"toggle deltas: {deltas}")
        for name, delta in deltas.items():
            if delta < 8:
                problems.append(f"{name} off removes only {delta} verts - "
                                "stub or dropped link")
    except Exception as exc:
        problems.append(f"toggle probe failed: {type(exc).__name__}: {exc}")

for n in notes:
    print(f"[arch-health] {n}")
for p in problems:
    print(f"[arch-health] PROBLEM: {p}")

print(f"[arch-health] problems={len(problems)}")
if problems:
    raise SystemExit(1)
print("[arch-health] PASS")
