"""Headless verification for GN_PARIS_Mansard (the Haussmann roof band).

Checks the classes a green build hides: dropped links, silently-rejected math
ops (ARCTANGENT / SQRT are the ones that matter here - a bad op name leaves
the node on ADD and every panel tilts wrong), declared params as real sockets,
real geometry, and that each ornament dial actually adds/removes geometry.

Usage:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
      --background --factory-startup --python deploy/_melodia_health_paris_mansard.py

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
    sys.path.insert(0, DEPLOY)
    sys.path.append(APPDATA_ADDONS)

import bpy  # noqa: E402
from surreal_arch.melodia_gn import core  # noqa: E402
from surreal_arch.melodia_gn import paris_mansard  # noqa: E402,F401

BUILDER_ID = "GN_PARIS_Mansard"
EXPECTED_MATH = (("ARCTANGENT", 2), ("SQRT", 2), ("DIVIDE", 6),
                 ("MULTIPLY", 20), ("ADD", 20), ("SUBTRACT", 6),
                 ("MAXIMUM", 3))
EXPECTED_BOOL = (("NOT", 1),)
EXPECTED_PARAMS = (
    "Band Width", "Band Depth", "Lower Slope", "Upper Slope", "Break Point",
    "Cornice Lip", "Dormers", "Dormer Width", "Dormer Height",
    "Oculus Dormers", "Zinc Ribs", "Rib Size", "Chimneys", "Chimney Height",
    "Chimney Pots", "Iron Cresting", "Cresting",
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
    mesh = bpy.data.meshes.new("MEL_MansardProbeMesh")
    obj = bpy.data.objects.new("MEL_MansardProbe", mesh)
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


print(f"[mansard-health] builder={BUILDER_ID}")

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
    print(f"[mansard-health] tree='{tree.name}' nodes={len(tree.nodes)}")

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
        notes.append(f"verts/polys (defaults): {base[0]}/{base[1]} bbox "
                     f"y {base[2][1]:.2f}..{base[3][1]:.2f} z {base[2][2]:.2f}..{base[3][2]:.2f}")
        if base[0] <= 0:
            problems.append("group evaluates to EMPTY geometry")
        elif base[0] < 300:
            problems.append(f"only {base[0]} verts - panels alone are ~64; "
                            "part of the roof is missing")
    except Exception as exc:
        problems.append(f"evaluation failed: {type(exc).__name__}: {exc}")

    # slopes: profile change slides panels, must NOT rebuild (same verts) but
    # MUST change the roof height (zmax)
    try:
        set_param(tree, "Upper Slope", 0.05)
        low = eval_stats(tree)
        set_param(tree, "Upper Slope", 0.70)
        high = eval_stats(tree)
        set_param(tree, "Upper Slope", 0.25)
        notes.append(f"upper slope: 0.05 -> zmax {low[3][2]:.3f}; "
                     f"0.70 -> zmax {high[3][2]:.3f}")
        if low[0] != high[0]:
            problems.append("changing Upper Slope changed the vertex count - "
                            "the profile must slide, not rebuild")
        if high[3][2] - low[3][2] < 0.3:
            problems.append("Upper Slope does not change the roof height - "
                            "the profile maths is a no-op")
    except Exception as exc:
        problems.append(f"slope probe failed: {type(exc).__name__}: {exc}")

    # ornament dials add / remove geometry
    try:
        deltas = {}
        for name, off_val, on_val in (("Dormers", 0, 4),
                                      ("Zinc Ribs", 0, 14),
                                      ("Chimneys", 0, 2),
                                      ("Cresting", 0, 16)):
            set_param(tree, name, off_val)
            off = eval_stats(tree)[0]
            set_param(tree, name, on_val)
            on = eval_stats(tree)[0]
            deltas[name] = on - off
        set_param(tree, "Iron Cresting", False)
        crest_off = eval_stats(tree)[0]
        set_param(tree, "Iron Cresting", True)
        crest_on = eval_stats(tree)[0]
        notes.append(f"deltas: {deltas}; cresting toggle {crest_on - crest_off}")
        for name, delta in deltas.items():
            if delta < 40:
                problems.append(f"{name} adds only {delta} verts - the line is "
                                "not instancing")
        if crest_on - crest_off < 100:
            problems.append("Iron Cresting off removes almost nothing - stub "
                            "or dropped link")
    except Exception as exc:
        problems.append(f"ornament probe failed: {type(exc).__name__}: {exc}")

for n in notes:
    print(f"[mansard-health] {n}")
for p in problems:
    print(f"[mansard-health] PROBLEM: {p}")

print(f"[mansard-health] problems={len(problems)}")
if problems:
    raise SystemExit(1)
print("[mansard-health] PASS")
