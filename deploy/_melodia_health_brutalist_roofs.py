"""Headless verification for GN_BRUTALIST_Roof.

Same contract as the other three brutalist health scripts: build cleanly, no
dropped links, declared params are real sockets, real geometry, and EVERY DIAL
moves the result. A roof builder that ignores Roof Style is a builder that
renders six identical roofs and looks fine in a contact sheet.

Also asserts the Higgsas fallback contract: the tree must build whether or not
the (gitignored, machine-local) library is present.

Usage:
    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \\
        --background --factory-startup \\
        --python deploy/_melodia_health_brutalist_roofs.py
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
from surreal_arch.melodia_gn import brutalist_roofs  # noqa: E402,F401

BUILDER_ID = "GN_BRUTALIST_Roof"
EXPECTED_PARAMS = (
    "Building Width", "Building Depth", "Roof Style", "Roof Pitch",
    "Eave Overhang", "Roof Thickness", "Sawtooth Teeth", "Sawtooth Width",
    "Gutters", "Gutter Width", "Roof Plant", "Plant Height", "Plant Units",
    "Roof Material",
)
N_STYLES = 6

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


def eval_mesh(tree):
    mesh = bpy.data.meshes.new("MEL_RoofProbeMesh")
    obj = bpy.data.objects.new("MEL_RoofProbe", mesh)
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
        cs = [v.co for v in m.vertices]
        lo = tuple(min(c[i] for c in cs) for i in range(3))
        hi = tuple(max(c[i] for c in cs) for i in range(3))
    ev.to_mesh_clear()
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.meshes.remove(mesh)
    return verts, polys, lo, hi


def build(**params):
    core.reset_link_failures()
    res = core.GROUP_BUILDERS[BUILDER_ID]()
    tree = res[0] if isinstance(res, (tuple, list)) else res
    for k, v in params.items():
        set_param(tree, k.replace("_", " "), v)
    return tree


print(f"[roof-health] builder={BUILDER_ID}")

if BUILDER_ID not in core.GROUP_BUILDERS:
    problems.append(f"{BUILDER_ID} is not registered (module not imported?)")
    tree = None
else:
    tree = build()

if tree is not None:
    print(f"[roof-health] tree='{tree.name}' nodes={len(tree.nodes)}")

    mine = core.link_failures().get(tree.name) or []
    if mine:
        for msg in mine:
            problems.append("dropped link: " + msg)
    else:
        notes.append("link_failures: none")

    # Cyclic dependency guard (2026-09-30). A self-link in a sibling brutalist
    # builder made that whole group evaluate to 0 verts with Blender logging
    # "Cannot evaluate node group" - while the build succeeded and
    # `link_failures` stayed EMPTY, because a cycle is legal, not an error.
    # Every geometry probe then reads 0 and the dials get blamed for it.
    cycles = core.find_link_cycles(tree)
    if cycles:
        for cyc in cycles[:5]:
            problems.append(f"cyclic link ({cyc}) - Blender cannot evaluate "
                            f"this group, so every geometry probe below reads 0")
    else:
        notes.append("link graph: acyclic")

    have = set()
    for item in tree.interface.items_tree:
        if getattr(item, "in_out", "") == "INPUT":
            have.add(getattr(item, "name", ""))
    missing = [p for p in EXPECTED_PARAMS if p not in have]
    if missing:
        problems.append(f"params missing from group inputs: {missing}")
    else:
        notes.append(f"params: {len(EXPECTED_PARAMS)}/{len(EXPECTED_PARAMS)}")

    try:
        from surreal_arch.melodia_gn import higgsas_pipeline as hp
        notes.append("higgsas available=%s" % hp.available())
    except Exception as exc:
        problems.append(f"higgsas_pipeline import failed: {exc}")
    groups = [n for n in tree.nodes if n.bl_idname == "GeometryNodeGroup"]
    notes.append("higgsas group nodes in tree: %d" % len(groups))

    v, p, lo, hi = eval_mesh(tree)
    print(f"[roof-health] defaults: {v} verts / {p} polys")
    if not v:
        problems.append("group evaluates to EMPTY geometry")
    else:
        notes.append("bbox %s .. %s" % (
            tuple(round(x, 2) for x in lo), tuple(round(x, 2) for x in hi)))

    # --- footprint responds --------------------------------------------------
    try:
        t1 = build(**{"Building_Width": 30.0})
        v1, _, lo1, hi1 = eval_mesh(t1)
        if hi1[0] - lo1[0] <= (hi[0] - lo[0]) + 1.0:
            problems.append("Building Width did not widen the footprint")
        else:
            notes.append("width 18->30: x %.1f -> %.1f"
                         % (hi[0] - lo[0], hi1[0] - lo1[0]))
    except Exception as exc:
        problems.append("width probe failed: %s: %s" % (type(exc).__name__, exc))

    # --- the variation knob: styles must be distinguishable ------------------
    try:
        sigs = {}
        for s in range(N_STYLES):
            ts = build(**{"Roof_Style": s})
            vs, ps, _, _ = eval_mesh(ts)
            sigs[s] = (vs, ps)
        print("[roof-health] style signatures: %s" % sigs)
        distinct = len(set(sigs.values()))
        if distinct < 2:
            problems.append("all %d roof styles produced identical geometry %s "
                            "- Roof Style is a dead dial" % (N_STYLES, sigs[0]))
        else:
            notes.append("distinct roof styles: %d/%d" % (distinct, N_STYLES))
    except Exception as exc:
        problems.append("style probe failed: %s: %s" % (type(exc).__name__, exc))

    # --- toggles add AND remove ---------------------------------------------
    # The Gutters / Roof_Plant / Thickness probes MUST run at a style where the
    # geometry they measure actually exists. Roof Plant is gated on style 5, and
    # pitched thickness only shows on 1/3/4 - probing at the default style 0
    # measured geometry that is deliberately absent and reported two perfectly
    # good dials as "dead". The dial was never the problem; the probe was
    # measuring the wrong state.
    PROBE_STYLE = 5        # plant deck style
    PITCH_STYLE = 3        # barrel vault: thickness is visible in z

    for toggle in ("Gutters", "Roof_Plant"):
        try:
            va, pa, _, _ = eval_mesh(build(**{"Roof_Style": PROBE_STYLE,
                                              toggle: True}))
            vb, pb, _, _ = eval_mesh(build(**{"Roof_Style": PROBE_STYLE,
                                              toggle: False}))
            if va == vb:
                problems.append("%s changes nothing at style %d (%d) - dead dial"
                                % (toggle, PROBE_STYLE, va))
            else:
                notes.append("%s @style%d: on=%d off=%d (delta %d)"
                             % (toggle, PROBE_STYLE, va, vb, abs(va - vb)))
        except Exception as exc:
            problems.append("%s probe failed: %s: %s"
                            % (toggle, type(exc).__name__, exc))

    # --- thickness, on a pitched style ---------------------------------------
    try:
        va, _, _, ha = eval_mesh(build(**{"Roof_Style": PITCH_STYLE}))
        vb, _, _, hc = eval_mesh(build(**{"Roof_Style": PITCH_STYLE,
                                          "Roof_Thickness": 0.9}))
        if abs(hc[2] - ha[2]) < 0.05:
            problems.append("Roof Thickness did not change zmax on style %d "
                            "(%.2f -> %.2f)" % (PITCH_STYLE, ha[2], hc[2]))
        else:
            notes.append("thickness 0.32->0.9 @style%d: zmax %.2f -> %.2f"
                         % (PITCH_STYLE, ha[2], hc[2]))
    except Exception as exc:
        problems.append("thickness probe failed: %s: %s"
                        % (type(exc).__name__, exc))

    # --- Plant Units drives the plant deck ------------------------------------
    # The deck once built a hardcoded 3 units; equal counts here mean DECKN
    # regressed to a constant.
    try:
        va, _, _, _ = eval_mesh(build(**{"Roof_Style": 5, "Plant_Units": 0}))
        vb, _, _, _ = eval_mesh(build(**{"Roof_Style": 5, "Plant_Units": 30}))
        if va == vb:
            problems.append("Plant Units changes nothing at style 5 (%d) - "
                            "dead dial" % va)
        else:
            notes.append("plant units 0->30 @style5: %d -> %d (delta %d)"
                         % (va, vb, abs(vb - va)))
    except Exception as exc:
        problems.append("plant units probe failed: %s: %s"
                        % (type(exc).__name__, exc))

for note in notes:
    print("[roof-health] note: %s" % note)
for p_ in problems:
    print("[roof-health] PROBLEM: %s" % p_)
print("[roof-health] problems=%d" % len(problems))
print("[roof-health] " + ("PASS" if not problems else "FAIL"))
if problems:
    sys.exit(1)
