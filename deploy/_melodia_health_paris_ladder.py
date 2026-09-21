"""Headless verification for GN_PARIS_EscherLadder (the Belvedere ladder).

py_compile cannot see any of what this checks:

  * the tree builds at all - a wrong socket name raises here;
  * core.link_failures() is EMPTY for the builder. The house link helpers never
    raise on a dropped link, so a miswired tree still builds green;
  * every node OPERATION actually took. The house helpers wrap
    `node.operation = op` in try/except, so an operation name this Blender
    spells differently leaves the node on its DEFAULT (Math -> ADD,
    BooleanMath -> AND) and the maths is quietly wrong - a silent no-op with a
    green build. MAXIMUM / SQRT / ARCTAN2 / NOT are the ones worth proving;
  * the group EVALUATES to non-empty geometry (it is put on a real object and
    the depsgraph is read), and the optional pieces (Mansard Landing, Railing)
    actually REMOVE geometry when off rather than leaving a hidden stub.

Usage:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
      --background --factory-startup --python deploy/_melodia_health_paris_ladder.py

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
# Import the module EXPLICITLY: it self-registers via register_builder() at
# import time. melodia_gn/__init__.py is being edited by a concurrent lane, so
# the one-line `from . import paris_escher_ladder` wiring is deliberately left
# to that lane; importing here proves the builder itself works end to end.
from surreal_arch.melodia_gn import paris_escher_ladder  # noqa: E402,F401

BUILDER_ID = "GN_PARIS_EscherLadder"
# (operation, minimum node count) - the unusual ones are the real proof that
# the assignment took instead of silently staying on the node default.
EXPECTED_MATH = (("MAXIMUM", 3), ("SQRT", 1), ("ARCTAN2", 1), ("DIVIDE", 2),
                 ("SUBTRACT", 4), ("MULTIPLY", 8), ("ADD", 5))
EXPECTED_BOOL = (("NOT", 2),)
EXPECTED_PARAMS = (
    "Ladder Height", "Ladder Lean", "Rung Count", "Ladder Width", "Rung Depth",
    "Rung Thickness", "Join Error", "Floating Steps", "Landing Depth",
    "Landing Thickness", "Mansard Landing", "Railing", "Rail Height",
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
    """(verts, polys) for the group evaluated on a throwaway object."""
    mesh = bpy.data.meshes.new("MEL_LadderProbeMesh")
    obj = bpy.data.objects.new("MEL_LadderProbe", mesh)
    bpy.context.scene.collection.objects.link(obj)
    mod = obj.modifiers.new("GNProbe", "NODES")
    mod.node_group = tree
    deps = bpy.context.evaluated_depsgraph_get()
    deps.update()
    ev = obj.evaluated_get(deps)
    m = ev.to_mesh()
    verts, polys = len(m.vertices), len(m.polygons)
    ev.to_mesh_clear()
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(mesh)
    return verts, polys


print(f"[ladder-health] builder={BUILDER_ID}")

if BUILDER_ID not in core.GROUP_BUILDERS:
    problems.append(f"{BUILDER_ID} is not registered (module not imported?)")
    tree = gin = None
else:
    core.reset_link_failures()
    try:
        res = core.GROUP_BUILDERS[BUILDER_ID]()   # registered path (music pass incl.)
        tree = res[0] if isinstance(res, (tuple, list)) else res
        gin = res[1] if isinstance(res, (tuple, list)) and len(res) > 1 else None
    except Exception as exc:
        problems.append(f"build raised {type(exc).__name__}: {exc}")
        tree = gin = None

if tree is not None:
    print(f"[ladder-health] tree='{tree.name}' nodes={len(tree.nodes)}")

    # 1. dropped links (the silent-no-op class)
    fails = core.link_failures()
    mine = fails.get(tree.name) or []
    if mine:
        for msg in mine:
            problems.append("dropped link: " + msg)
    else:
        notes.append("link_failures: none for this tree")

    # 2. operations actually took
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

    # 3. declared params present as sockets. Read the tree INTERFACE (that is
    # where add_*_param puts them) - not the group-input node's outputs, which
    # is what a first version of this check wrongly used and then reported all
    # thirteen as missing while set_param() was finding them fine.
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

    # 4. evaluates to real geometry, incl. the join error both ways
    try:
        base = eval_stats(tree)
        notes.append(f"verts/polys (defaults): {base[0]}/{base[1]}")
        if base[0] <= 0:
            problems.append("group evaluates to EMPTY geometry")
        elif base[0] < 12 * 8:
            problems.append(f"only {base[0]} verts - fewer than the rung count "
                            f"implies; part of the ladder is missing")
    except Exception as exc:
        problems.append(f"evaluation failed: {type(exc).__name__}: {exc}")
        base = None

    # 5. Join Error must MOVE the ladder relative to the landing, not resize it
    try:
        if set_param(tree, "Join Error", 0.0):
            meet = eval_stats(tree)
        else:
            meet = None
            problems.append("could not set 'Join Error' default")
        if base and meet:
            notes.append(f"join error 0.0 -> verts/polys {meet[0]}/{meet[1]}")
            if meet[0] != base[0]:
                problems.append("changing Join Error changed the vertex count - it "
                                "must slide the ladder, not rebuild it")
    except Exception as exc:
        problems.append(f"join-error probe failed: {type(exc).__name__}: {exc}")

    # 6. optional pieces really remove geometry (no hidden stub), with a delta
    # per piece so a piece that contributes almost nothing is visible.
    try:
        set_param(tree, "Railing", True)
        set_param(tree, "Mansard Landing", True)
        with_opt = eval_stats(tree)
        set_param(tree, "Railing", False)
        rail_off = eval_stats(tree)
        set_param(tree, "Mansard Landing", False)
        both_off = eval_stats(tree)
        notes.append(f"verts: both on={with_opt[0]}, railing off={rail_off[0]} "
                     f"(delta {with_opt[0] - rail_off[0]}), both off={both_off[0]} "
                     f"(mansard delta {rail_off[0] - both_off[0]})")
        if both_off[0] >= with_opt[0]:
            problems.append("turning Railing+Mansard off did NOT remove geometry "
                            f"({both_off[0]} >= {with_opt[0]} verts) - the "
                            "optional pattern is leaving a stub")
        if with_opt[0] - rail_off[0] < 16:
            problems.append(
                f"railing adds only {with_opt[0] - rail_off[0]} verts - two "
                "handrails swept from an 8-gon profile should add ~32 (2 rails x "
                "2 rings x 8). Under that, the profile is not reaching Curve to "
                "Mesh and the rails are degenerate lines."
            )
        set_param(tree, "Railing", True)
        set_param(tree, "Mansard Landing", True)
    except Exception as exc:
        problems.append(f"option-toggle probe failed: {type(exc).__name__}: {exc}")

for n in notes:
    print(f"[ladder-health] {n}")
for p in problems:
    print(f"[ladder-health] PROBLEM: {p}")

print(f"[ladder-health] problems={len(problems)}")
if problems:
    raise SystemExit(1)
print("[ladder-health] PASS")
