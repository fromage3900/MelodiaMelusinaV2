"""Headless verification for GN_PARIS_FountainLoop (the self-feeding fountain).

py_compile cannot see any of what this checks:

  * the tree builds at all - a wrong socket name raises here;
  * core.link_failures() is EMPTY for the builder (house link helpers never
    raise on a dropped link, so a miswired tree still builds green);
  * the unusual math operations actually took (POWER / MODULO / LESS_THAN /
    SINE / COSINE) - the helpers wrap `node.operation = op` in try/except, so
    a misspelled op leaves the node on its DEFAULT and the maths is silently
    wrong;
  * the group EVALUATES to non-empty geometry, tiers really add geometry,
    Tiers really REMOVES unreached slots, Self Feed really removes the whole
    channel, and Loop Error SLIDES the channel rather than rebuilding it.

Usage:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
      --background --factory-startup --python deploy/_melodia_health_paris_fountain_loop.py

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
from surreal_arch.melodia_gn import paris_fountain_loop  # noqa: E402,F401

BUILDER_ID = "GN_PARIS_FountainLoop"
EXPECTED_MATH = (("POWER", 4), ("MODULO", 1), ("LESS_THAN", 4),
                 ("SINE", 1), ("COSINE", 1), ("MAXIMUM", 1),
                 ("MULTIPLY", 15), ("ADD", 25), ("SUBTRACT", 8),
                 ("DIVIDE", 1))
EXPECTED_BOOL = (("NOT", 4),)
EXPECTED_PARAMS = (
    "Basin Radius", "Basin Height", "Flutes", "Shell Count", "Shell Size",
    "Rim Beads", "Bead Size", "Tiers", "Tier Rise", "Tier Shrink",
    "Crown Spikes", "Crown Size", "Water Level", "Ripple Amp",
    "Ripple Count", "Streams", "Stream Radius", "Droplets", "Droplet Size",
    "Self Feed", "Feed Rise", "Loop Error", "Channel Radius",
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
    """(verts, polys, bbox_min, bbox_max) for the group on a throwaway object."""
    mesh = bpy.data.meshes.new("MEL_FountainProbeMesh")
    obj = bpy.data.objects.new("MEL_FountainProbe", mesh)
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


print(f"[fountain-health] builder={BUILDER_ID}")

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
    print(f"[fountain-health] tree='{tree.name}' nodes={len(tree.nodes)}")

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
        notes.append(f"verts/polys (defaults): {base[0]}/{base[1]} bbox_z "
                     f"{base[2][2]:.3f}..{base[3][2]:.3f}" if base[2] else
                     f"verts/polys (defaults): {base[0]}/{base[1]}")
        if base[0] <= 0:
            problems.append("group evaluates to EMPTY geometry")
        elif base[0] < 2000:
            problems.append(f"only {base[0]} verts - a dressed fountain is "
                            "thousands; part of the build is missing")
    except Exception as exc:
        problems.append(f"evaluation failed: {type(exc).__name__}: {exc}")

    # tiers: more tiers = more geometry; slots beyond Tiers really vanish
    try:
        tiers = {}
        for count in (1, 2, 4):
            set_param(tree, "Tiers", count)
            tiers[count] = eval_stats(tree)[0]
        notes.append(f"tiers verts: 1={tiers[1]} 2={tiers[2]} 4={tiers[4]}")
        if not (tiers[1] < tiers[2] < tiers[4]):
            problems.append(f"tier verts not increasing with Tiers: {tiers} - the "
                            "DeleteGeometry slot guards are not removing slots")
        set_param(tree, "Tiers", 2)
    except Exception as exc:
        problems.append(f"tier probe failed: {type(exc).__name__}: {exc}")

    # Self Feed: OFF must remove the whole channel + spout
    try:
        set_param(tree, "Self Feed", True)
        on = eval_stats(tree)
        set_param(tree, "Self Feed", False)
        off = eval_stats(tree)
        set_param(tree, "Self Feed", True)
        delta = on[0] - off[0]
        notes.append(f"self feed: on={on[0]} off={off[0]} (delta {delta})")
        if delta < 100:
            problems.append(f"Self Feed off removes only {delta} verts - the "
                            "channel is not being deleted (stub or dropped link)")
    except Exception as exc:
        problems.append(f"self-feed probe failed: {type(exc).__name__}: {exc}")

    # Loop Error: must SLIDE the channel, not rebuild it
    try:
        set_param(tree, "Loop Error", 0.0)
        meet = eval_stats(tree)
        set_param(tree, "Loop Error", 0.40)
        high = eval_stats(tree)
        set_param(tree, "Loop Error", 0.0)
        notes.append(f"loop error: 0.0 -> {meet[0]}v zmax {meet[3][2]:.3f}; "
                     f"0.4 -> {high[0]}v zmax {high[3][2]:.3f}")
        if meet[0] != high[0]:
            problems.append("changing Loop Error changed the vertex count - it "
                            "must slide the channel, not rebuild it")
        if high[3][2] - meet[3][2] < 0.20:
            problems.append("Loop Error 0.4 did not raise the channel's top by "
                            ">= 0.2m - the dial is a no-op")
    except Exception as exc:
        problems.append(f"loop-error probe failed: {type(exc).__name__}: {exc}")

    # ornament dials actually add geometry
    try:
        set_param(tree, "Rim Beads", 0)
        beads_off = eval_stats(tree)[0]
        set_param(tree, "Rim Beads", 120)
        beads_on = eval_stats(tree)[0]
        notes.append(f"rim beads: 0 -> {beads_off}, 120 -> {beads_on} "
                     f"(delta {beads_on - beads_off})")
        if beads_on - beads_off < 3000:
            problems.append(f"120 rim beads add only {beads_on - beads_off} verts "
                            "- the bead ring is not instancing")
        set_param(tree, "Streams", 0)
        streams_off = eval_stats(tree)[0]
        set_param(tree, "Streams", 6)
        streams_on = eval_stats(tree)[0]
        notes.append(f"streams: 0 -> {streams_off}, 6 -> {streams_on} "
                     f"(delta {streams_on - streams_off})")
        if streams_on - streams_off < 100:
            problems.append("stream rings add almost nothing - not instancing")
    except Exception as exc:
        problems.append(f"ornament probe failed: {type(exc).__name__}: {exc}")

for n in notes:
    print(f"[fountain-health] {n}")
for p in problems:
    print(f"[fountain-health] PROBLEM: {p}")

print(f"[fountain-health] problems={len(problems)}")
if problems:
    raise SystemExit(1)
print("[fountain-health] PASS")
