"""Headless verification for GN_BRUTALIST_OfficeBlock.

Checks the classes a green build hides: dropped links, silently-rejected math
ops, declared params as real sockets, real geometry, and that the structural
dials actually do what they claim:
  * Pilotis off deletes the columns + lobby glass AND drops the floor stack
    to the ground (zmax must fall by the pilotis height);
  * Floors / Bay Count change the instance counts;
  * Stair Tower / Roof Plant toggles remove their geometry;
  * Formwork adds grooves to every band at every floor;
  * Parapet changes height without rebuilding the block.

Usage:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
      --background --factory-startup --python deploy/_melodia_health_brutalist_office.py

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
from surreal_arch.melodia_gn import brutalist_office  # noqa: E402,F401

BUILDER_ID = "GN_BRUTALIST_OfficeBlock"
EXPECTED_MATH = (("MULTIPLY", 15), ("ADD", 10), ("SUBTRACT", 10),
                 ("DIVIDE", 3), ("MAXIMUM", 1), ("ROUND", 1))
EXPECTED_BOOL = (("NOT", 6),)
EXPECTED_PARAMS = (
    "Block Width", "Block Depth", "Floors", "Floor Height", "Bay Count",
    "Pier Width", "Band Height", "Window Reveal", "Pilotis",
    "Pilotis Height", "Stair Tower", "Tower Width", "Slot Count",
    "Parapet Height", "Roof Plant", "Plant Height", "Formwork",
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
    mesh = bpy.data.meshes.new("MEL_BrutOfficeProbeMesh")
    obj = bpy.data.objects.new("MEL_BrutOfficeProbe", mesh)
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


print(f"[brutoffice-health] builder={BUILDER_ID}")

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
    print(f"[brutoffice-health] tree='{tree.name}' nodes={len(tree.nodes)}")

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
                     f"z {base[2][2]:.2f}..{base[3][2]:.2f}")
        if base[0] <= 0:
            problems.append("group evaluates to EMPTY geometry")
        elif base[0] < 400:
            problems.append(f"only {base[0]} verts - a 6-floor block should "
                            "carry piers + bands + glass at every floor")
    except Exception as exc:
        problems.append(f"evaluation failed: {type(exc).__name__}: {exc}")

    # pilotis: columns + lobby vanish AND the floors drop to the ground
    try:
        set_param(tree, "Pilotis", False)
        off = eval_stats(tree)
        set_param(tree, "Pilotis", True)
        on = eval_stats(tree)
        notes.append(f"pilotis: off {off[0]}v zmax {off[3][2]:.2f}; "
                     f"on {on[0]}v zmax {on[3][2]:.2f}")
        if on[0] - off[0] < 200:
            problems.append(f"Pilotis off removes only {on[0] - off[0]} verts "
                            "- columns/lobby are not guarded")
        if not (on[3][2] - off[3][2] > 3.0):
            problems.append("Pilotis on does not lift the floor stack - the "
                            "z0 maths is a no-op")
    except Exception as exc:
        problems.append(f"pilotis probe failed: {type(exc).__name__}: {exc}")

    # floors and bays change instance counts
    try:
        set_param(tree, "Floors", 1)
        f1 = eval_stats(tree)[0]
        set_param(tree, "Floors", 6)
        f6 = eval_stats(tree)[0]
        set_param(tree, "Bay Count", 4)
        b4 = eval_stats(tree)[0]
        set_param(tree, "Bay Count", 8)
        b8 = eval_stats(tree)[0]
        notes.append(f"floors 1->6: {f1}->{f6} verts; bays 4->8: "
                     f"{b4}->{b8} verts")
        if f6 - f1 < 100:
            problems.append("Floors does not stack geometry")
        if b8 - b4 < 50:
            problems.append("Bay Count does not add piers")
    except Exception as exc:
        problems.append(f"count probe failed: {type(exc).__name__}: {exc}")

    # toggles + formwork
    try:
        deltas = {}
        for name, off_val, on_val in (("Stair Tower", False, True),
                                      ("Roof Plant", False, True),
                                      ("Formwork", 0, 3)):
            set_param(tree, name, off_val)
            off = eval_stats(tree)[0]
            set_param(tree, name, on_val)
            on = eval_stats(tree)[0]
            deltas[name] = on - off
        notes.append(f"toggle deltas: {deltas}")
        for name, delta in deltas.items():
            if delta < 24:
                problems.append(f"{name} changes only {delta} verts - stub or "
                                "dropped link")
    except Exception as exc:
        problems.append(f"toggle probe failed: {type(exc).__name__}: {exc}")

    # parapet: height change, no rebuild.  Roof Plant and the Stair Tower are
    # both taller than the parapet, so isolate them first or the zmax is masked.
    try:
        set_param(tree, "Roof Plant", False)
        set_param(tree, "Stair Tower", False)
        set_param(tree, "Parapet Height", 0.0)
        p0 = eval_stats(tree)
        set_param(tree, "Parapet Height", 0.9)
        p9 = eval_stats(tree)
        notes.append(f"parapet 0.0 -> zmax {p0[3][2]:.2f}; 0.9 -> "
                     f"{p9[3][2]:.2f}")
        if p0[0] != p9[0]:
            problems.append("Parapet Height changed the vertex count - it "
                            "must slide, not rebuild")
        if p9[3][2] - p0[3][2] < 0.2:
            problems.append("Parapet Height is a no-op")
        set_param(tree, "Roof Plant", True)
        set_param(tree, "Stair Tower", True)
    except Exception as exc:
        problems.append(f"parapet probe failed: {type(exc).__name__}: {exc}")

for n in notes:
    print(f"[brutoffice-health] {n}")
for p in problems:
    print(f"[brutoffice-health] PROBLEM: {p}")

print(f"[brutoffice-health] problems={len(problems)}")
if problems:
    raise SystemExit(1)
print("[brutoffice-health] PASS")
