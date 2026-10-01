"""Headless verification for GN_BRUTALIST_CityBlock.

Checks the classes a green build hides, plus the ones unique to a CITY:

  * dropped links (incl. a float linked into RandomValue's VECTOR Min, which is a
    recorded drop, not a silent pass);
  * declared params are real sockets; real geometry;
  * Blocks X / Blocks Y grow both the vertex count and the footprint;
  * Street Width moves the footprint WITHOUT changing the vertex count - it is a
    pure layout dial, so a change in verts means something rebuilt;
  * **Height Min / Height Max actually drive the massing.** A dropped Scale link
    leaves every block 1 unit tall, so `zmax >= Height Min` is the assertion that
    catches it. Same trap the CubicleFarm Rows guard is written against;
  * Seed changes the skyline but not the vertex count (structure is seed-independent);
  * every toggle removes geometry instead of leaving stubs.

Usage:
    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \\
        --background --factory-startup \\
        --python deploy/_melodia_health_brutalist_city.py

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
from surreal_arch.melodia_gn import brutalist_city  # noqa: E402,F401

BUILDER_ID = "GN_BRUTALIST_CityBlock"
EXPECTED_MATH = (("MULTIPLY", 18), ("ADD", 8), ("SUBTRACT", 5))
EXPECTED_BOOL = (("NOT", 5),)
EXPECTED_PARAMS = (
    "Blocks X", "Blocks Y", "Lot Width", "Lot Depth", "Street Width", "Setback",
    "Height Min", "Height Max", "Seed", "Ground", "Roads", "Sidewalks",
    "Parapet", "Piers",
    "Facade Style", "Window Floors", "Window Bay", "Window Band Height",
    "Window Reveal", "Fin Depth", "Fin Count",
    "Massing Material", "Ground Material", "Glazing Material",
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
    mesh = bpy.data.meshes.new("MEL_CityProbeMesh")
    obj = bpy.data.objects.new("MEL_CityProbe", mesh)
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


print(f"[city-health] builder={BUILDER_ID}")

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
    print(f"[city-health] tree='{tree.name}' nodes={len(tree.nodes)}")

    mine = (core.link_failures().get(tree.name) or [])
    if mine:
        for msg in mine:
            problems.append("dropped link: " + msg)
    else:
        notes.append("link_failures: none for this tree")

    # Cyclic dependency guard. Added 2026-09-30 after a self-link in
    # _build_facade made this whole group evaluate to 0 verts while every dial
    # probe above reported "0" and blamed the facade dials. Blender accepts a
    # cycle without error, so neither `link_failures` nor a successful build
    # catches it - the group simply stops evaluating, with "Cannot evaluate
    # node group" in the log. Assert the graph is acyclic BEFORE trusting any
    # geometry number below, or a dead group reads as a dead dial.
    cycles = core.find_link_cycles(tree)
    if cycles:
        for cyc in cycles[:5]:
            problems.append(f"cyclic link ({cyc}) - Blender cannot evaluate "
                            f"this group, so every geometry probe below reads 0")
    else:
        notes.append("link graph: acyclic")

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
            problems.append(f"boolean op '{op}' used {got}x, expected >= {need} "
                            f"({len(EXPECTED_PARAMS) - 3} guards each emit one NOT)")
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
        notes.append(f"params: {len(EXPECTED_PARAMS)}/{len(EXPECTED_PARAMS)} present")

    # ---- baseline ----------------------------------------------------------
    try:
        base = eval_stats(tree)
        notes.append(f"verts/polys (defaults): {base[0]}/{base[1]} "
                     f"bbox x {base[2][0]:.2f}..{base[3][0]:.2f} "
                     f"y {base[2][1]:.2f}..{base[3][1]:.2f} "
                     f"z {base[2][2]:.2f}..{base[3][2]:.2f}")
        if base[0] <= 0:
            problems.append("group evaluates to EMPTY geometry")
        elif base[0] < 400:
            problems.append(f"only {base[0]} verts - a 3x3 grid with streets, "
                            f"sidewalks and massing should carry more")
    except Exception as exc:
        problems.append(f"evaluation failed: {type(exc).__name__}: {exc}")

    # ---- grid density ------------------------------------------------------
    try:
        set_param(tree, "Blocks X", 1); set_param(tree, "Blocks Y", 1)
        g1 = eval_stats(tree)[0]
        set_param(tree, "Blocks X", 3); set_param(tree, "Blocks Y", 3)
        g3 = eval_stats(tree)[0]
        set_param(tree, "Blocks X", 5); set_param(tree, "Blocks Y", 5)
        g5 = eval_stats(tree)
        notes.append(f"grid 1x1/3x3/5x5: {g1}/{g3}/{g5[0]} verts, "
                     f"xmax {g5[3][0]:.2f}")
        if not (g3 > g1 and g5[0] > g3):
            problems.append("Blocks X/Y do not scale geometry - a MeshLine count "
                            "or the lot grid is not wired")
        set_param(tree, "Blocks X", 3); set_param(tree, "Blocks Y", 3)
    except Exception as exc:
        problems.append(f"grid probe failed: {type(exc).__name__}: {exc}")

    # ---- street width: pure layout dial ------------------------------------
    try:
        set_param(tree, "Street Width", 6.0)
        s6 = eval_stats(tree)
        set_param(tree, "Street Width", 14.0)
        s14 = eval_stats(tree)
        notes.append(f"street 6->14: verts {s6[0]}->{s14[0]}, "
                     f"xmax {s6[3][0]:.2f}->{s14[3][0]:.2f}")
        if s6[0] != s14[0]:
            problems.append("Street Width changed the vertex count - it is a pure "
                            "layout dial and must not rebuild")
        if not (s14[3][0] - s6[3][0] > 10.0):
            problems.append("Street Width does not widen the block - the road/pitch "
                            "maths is a no-op")
        set_param(tree, "Street Width", 8.0)
    except Exception as exc:
        problems.append(f"street probe failed: {type(exc).__name__}: {exc}")

    # ---- height drives the massing (catches a dropped Scale link) ----------
    try:
        set_param(tree, "Height Min", 20.0); set_param(tree, "Height Max", 20.0)
        fixed = eval_stats(tree)
        set_param(tree, "Height Min", 20.0); set_param(tree, "Height Max", 60.0)
        ranged = eval_stats(tree)
        notes.append(f"height fixed 20: zmax {fixed[3][2]:.2f}; "
                     f"range 20-60: zmax {ranged[3][2]:.2f}")
        if abs(fixed[3][2] - 20.0) > 0.01:
            problems.append(f"Height Min==Height Max==20 gave zmax "
                            f"{fixed[3][2]:.3f}, not 20.000 - the per-instance "
                            f"Z scale or the RandomValue float Min/Max link is "
                            f"not taking (a dropped Scale link leaves 1-unit "
                            f"blocks)")
        if not (20.0 <= ranged[3][2] <= 60.001):
            problems.append(f"Height Max=60 gave zmax {ranged[3][2]:.3f} - outside "
                            f"the requested band")
        set_param(tree, "Height Min", 12.0); set_param(tree, "Height Max", 34.0)
    except Exception as exc:
        problems.append(f"height probe failed: {type(exc).__name__}: {exc}")

    # ---- seed: changes the skyline, not the structure ----------------------
    try:
        set_param(tree, "Seed", 11)
        sa = eval_stats(tree)
        set_param(tree, "Seed", 4242)
        sb = eval_stats(tree)
        notes.append(f"seed 11/4242: verts {sa[0]}/{sb[0]}, "
                     f"zmax {sa[3][2]:.2f}/{sb[3][2]:.2f}")
        if sa[0] != sb[0]:
            problems.append("Seed changed the vertex count - it must only change "
                            "per-lot heights, not topology")
        if abs(sa[3][2] - sb[3][2]) < 0.01:
            problems.append("Seed does not change the skyline - the RandomValue "
                            "seed link is a no-op")
        set_param(tree, "Seed", 7)
    except Exception as exc:
        problems.append(f"seed probe failed: {type(exc).__name__}: {exc}")

    # ---- facade styles: 1/2/3 must be pairwise-distinct --------------------
    # Styles 1-3 once built the same ring-band; identical signatures here mean
    # the Punched / Colonnade branches regressed to Ribbon.
    try:
        set_param(tree, "Facade Style", 1)
        s1 = eval_stats(tree)
        set_param(tree, "Facade Style", 2)
        s2 = eval_stats(tree)
        set_param(tree, "Facade Style", 3)
        s3 = eval_stats(tree)
        notes.append(f"facade styles 1/2/3: {s1[0]}/{s2[0]}/{s3[0]} verts")
        if len({s1[0], s2[0], s3[0]}) < 3:
            problems.append(f"Facade Styles 1/2/3 not pairwise-distinct "
                            f"({s1[0]}/{s2[0]}/{s3[0]} verts) - Punched or "
                            f"Colonnade regressed to Ribbon")
        set_param(tree, "Facade Style", 0)
    except Exception as exc:
        problems.append(f"facade style probe failed: {type(exc).__name__}: {exc}")

    # ---- Window Bay drives the Punched grid ---------------------------------
    try:
        set_param(tree, "Facade Style", 2)
        set_param(tree, "Window Bay", 0.6)
        b_lo = eval_stats(tree)
        set_param(tree, "Window Bay", 6.0)
        b_hi = eval_stats(tree)
        notes.append(f"bay 0.6->6.0 @style2: verts {b_lo[0]}->{b_hi[0]}")
        if b_lo[0] == b_hi[0]:
            problems.append(f"Window Bay changes nothing at Facade Style 2 "
                            f"({b_lo[0]} verts) - dead dial")
        set_param(tree, "Window Bay", 2.4)
        set_param(tree, "Facade Style", 0)
    except Exception as exc:
        problems.append(f"bay probe failed: {type(exc).__name__}: {exc}")

    # ---- Fin Count drives the Colonnade fins --------------------------------
    try:
        set_param(tree, "Facade Style", 3)
        set_param(tree, "Fin Count", 0)
        f0 = eval_stats(tree)
        set_param(tree, "Fin Count", 40)
        f40 = eval_stats(tree)
        notes.append(f"fins 0->40 @style3: verts {f0[0]}->{f40[0]}")
        if f0[0] == f40[0]:
            problems.append(f"Fin Count changes nothing at Facade Style 3 "
                            f"({f0[0]} verts) - dead dial")
        set_param(tree, "Fin Count", 6)
        set_param(tree, "Facade Style", 0)
    except Exception as exc:
        problems.append(f"fin probe failed: {type(exc).__name__}: {exc}")

    # ---- style 0 emits no facade geometry ------------------------------------
    try:
        set_param(tree, "Facade Style", 0)
        f_off = eval_stats(tree)[0]
        set_param(tree, "Facade Style", 1)
        f_on = eval_stats(tree)[0]
        notes.append(f"facade off/on: verts {f_off}/{f_on}")
        if not (f_on > f_off):
            problems.append("Facade Style 0 leaves facade geometry behind - "
                            "the style gate is not deleting")
        set_param(tree, "Facade Style", 0)
    except Exception as exc:
        problems.append(f"facade gate probe failed: {type(exc).__name__}: {exc}")

    # ---- toggles -----------------------------------------------------------
    try:
        # Ground is a SINGLE slab (8 verts), so a `delta >= 20` threshold here would
        # be a calibration lie - it would fail a correctly working builder. Assert it
        # by the bbox instead: the ground is the only geometry below z=0.
        set_param(tree, "Ground", False)
        g_off = eval_stats(tree)
        set_param(tree, "Ground", True)
        g_on = eval_stats(tree)
        notes.append(f"ground off/on: verts {g_off[0]}/{g_on[0]}, "
                     f"zmin {g_off[2][2]:.2f}/{g_on[2][2]:.2f}")
        if g_on[0] - g_off[0] <= 0:
            problems.append("Ground off removes no geometry - guard did not delete")
        if g_off[2][2] < -0.30:
            problems.append(f"Ground off still leaves geometry at z="
                            f"{g_off[2][2]:.2f} (expected the only sub-zero slab "
                            f"to be gone)")

        deltas = {"Ground": g_on[0] - g_off[0]}
        for name in ("Roads", "Sidewalks", "Parapet", "Piers"):
            set_param(tree, name, False)
            off = eval_stats(tree)[0]
            set_param(tree, name, True)
            on = eval_stats(tree)[0]
            deltas[name] = on - off
        notes.append(f"toggle deltas: {deltas}")
        for name, delta in deltas.items():
            if name == "Ground":
                continue          # asserted by bbox above
            if delta < 20:
                problems.append(f"{name} changes only {delta} verts - stub or "
                                f"dropped link (guard did not delete)")
    except Exception as exc:
        problems.append(f"toggle probe failed: {type(exc).__name__}: {exc}")

for n in notes:
    print(f"[city-health] {n}")
for p in problems:
    print(f"[city-health] PROBLEM: {p}")

print(f"[city-health] problems={len(problems)}")
if problems:
    raise SystemExit(1)
print("[city-health] PASS")

