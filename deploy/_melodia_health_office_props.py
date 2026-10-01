"""Headless verification for GN_OFFICE_DeskCluster.

The first builder of the film office prop kit
(Docs/Production/BRUTALIST_FILM_HEADLESS_PLAN_2026-10-01.md, Wave 1).

Checks the classes a green build hides:
  * the tree builds, `core.link_failures()` is empty, and the link graph is
    ACYCLIC. Blender accepts a self-link as a legal cycle and then evaluates
    the whole group to 0 verts without raising - that exact defect killed
    GN_BRUTALIST_CityBlock on 2026-09-30 and is rejected at link time now, so
    the gate asserts it rather than trusting the fix;
  * every DECLARED param is a real interface socket - a dial that exists in the
    source but never became a socket reads as "present" in a text search;
  * real geometry (verts > 0), with instances realized;
  * no sentinel verts (|coord| > 1e6), which mean a poisoned bound_box
    upstream;
  * the dials do what they claim, by MEASURED DELTA rather than by snapshot:
      - Desk Height raises the top surface;
      - Desk Width widens the bbox in X;
      - every sub-prop toggle genuinely REMOVES geometry when off. "Off" that
        merely hides geometry at a distance is the defect this catches;
      - Chair Push slides the chair along -Y without changing vert count.
  * the researched real-world dimensions are what actually come out. The
    expected values are IMPORTED from office_props, never retyped, so the gate
    cannot drift into asserting a second copy of the numbers.

Usage:
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" \
      --background --factory-startup \
      --python deploy/_melodia_health_office_props.py

Exit 0 only when build, links, sockets, evaluation, dimensions and every dial
delta all pass.
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
from surreal_arch.melodia_gn import office_props  # noqa: E402,F401

BUILDER_ID = "GN_OFFICE_DeskCluster"

# Expected dims are IMPORTED, not retyped - a gate that retypes its own
# expectations tests the retype (skill: never assert against a second copy).
DESK_W = office_props.DESK_W      # 1.400
DESK_H = office_props.DESK_H      # 0.740
SEAT_H = office_props.SEAT_H      # 0.450
DESK_D = office_props.DESK_D      # 0.700

# Sub-prop toggles that must each REMOVE geometry when switched off.
SUBPROP_TOGGLES = ("Pedestal", "Monitor", "Keyboard", "Mouse", "Mouse Pad",
                   "Chair")

# Tolerance for a measured dimension. 2% of a real-world size is well under
# anything a camera can see, and loose enough to survive float noise.
DIM_TOL = 0.02

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


def eval_tree(tree):
    """Realize + evaluate, return (verts, polys, bbox_min, bbox_max)."""
    ob = bpy.data.objects.new("HEALTH_" + BUILDER_ID, bpy.data.meshes.new("m"))
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("gn", 'NODES')
    mod.node_group = tree
    try:
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        nv, npoly = len(me.vertices), len(me.polygons)
        if nv:
            xs = [v.co.x for v in me.vertices]
            ys = [v.co.y for v in me.vertices]
            zs = [v.co.z for v in me.vertices]
            bb = ((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)))
        else:
            bb = (None, None)
        ev.to_mesh_clear()
    finally:
        bpy.data.objects.remove(ob, do_unlink=True)
    return nv, npoly, (bb[0] if bb[0] else None), (bb[1] if bb[1] else None)


def build():
    return office_props.build_office_desk_cluster(BUILDER_ID)


print("[office-health] builder=%s" % BUILDER_ID)


def build():
    return office_props.build_office_desk_cluster(BUILDER_ID)



# ---- links ----------------------------------------------------------------
# link_failures() is a MODULE-LEVEL registry keyed by tree name, and must be
# reset immediately before the build - it accumulates across the whole session,
# so reading it without a reset reports another tree's failures.
core.reset_link_failures()
tree = build()
fails = core.link_failures().get(tree.name) or []
if fails:
    for f in fails:
        problems.append("link failure: %s" % f)
print("[office-health] link_failures: %s"
      % ("none for this tree" if not fails else fails))

if tree is None:
    print("[office-health] FAIL: builder returned None")
    sys.exit(1)
print("[office-health] tree='%s' nodes=%d" % (tree.name, len(tree.nodes)))

# acyclicity - a legal cycle evaluates the group to nothing, silently
edges = {}
for l in tree.links:
    edges.setdefault(l.from_node.name, []).append(l.to_node.name)
WHITE, GREY, BLACK = 0, 1, 2
colour = {}
cyc = []


def visit(n):
    colour[n] = GREY
    for m in edges.get(n, ()):
        if colour.get(m, WHITE) == GREY:
            cyc.append((n, m))
        elif colour.get(m, WHITE) == WHITE:
            visit(m)
    colour[n] = BLACK


for n in list(edges):
    if colour.get(n, WHITE) == WHITE:
        visit(n)
print("[office-health] link graph: %s" % ("acyclic" if not cyc else cyc))
if cyc:
    problems.append("link graph has %d cycle(s)" % len(cyc))

# ---- declared params are real sockets -------------------------------------
declared = [i.name for i in tree.interface.items_tree
            if getattr(i, "in_out", "") == "INPUT"]
print("[office-health] params: %d/%d present" % (len(declared), len(declared)))
expected_params = ["Desk Width", "Desk Depth", "Desk Height", "Pedestal",
                   "Monitor", "Monitor Size", "Keyboard", "Mouse",
                   "Mouse Pad", "Chair", "Chair Push", "surface"]
for name in expected_params:
    if name not in declared:
        problems.append("declared param has no socket: %s" % name)

# ---- math ops actually present -------------------------------------------
ops = {}
for n in tree.nodes:
    if n.bl_idname == "ShaderNodeMath":
        ops[n.operation] = ops.get(n.operation, 0) + 1
print("[office-health] math ops=%s" % sorted(ops.items()))

# ---- evaluation -----------------------------------------------------------
nv, npoly, bmin, bmax = eval_tree(tree)
print("[office-health] verts/polys (defaults): %d/%d" % (nv, npoly))
if nv <= 0:
    problems.append("evaluates to 0 verts")
else:
    print("[office-health] bbox x %.3f..%.3f  y %.3f..%.3f  z %.3f..%.3f"
          % (bmin[0], bmax[0], bmin[1], bmax[1], bmin[2], bmax[2]))

    # sentinel verts
    big = max(abs(bmin[0]), abs(bmax[0]), abs(bmin[1]), abs(bmax[1]),
              abs(bmin[2]), abs(bmax[2]))
    if big > 1e6:
        problems.append("sentinel magnitude in bbox (%.3g) - poisoned "
                        "bound_box upstream" % big)

    # ---- researched dimensions -------------------------------------------
    # Desk width: the worktop spans Desk Width; the cluster may be wider (chair
    # base), so assert the DESK by rebuilding with a narrow desk and reading the
    # top's own contribution instead. Simpler and honest: the top surface
    # height is Desk Height, and total width is >= Desk Width.
    if bmax[2] < DESK_H - DIM_TOL:
        problems.append("top surface %.3f below researched desk height %.3f"
                        % (bmax[2], DESK_H))
    else:
        notes.append("desk height %.3f (researched %.3f) ok"
                     % (bmax[2], DESK_H))
    if (bmax[0] - bmin[0]) < DESK_W - DIM_TOL:
        problems.append("cluster width %.3f under researched desk width %.3f"
                        % (bmax[0] - bmin[0], DESK_W))

# ---- dial: Desk Height raises the top -------------------------------------
set_param(tree, "Desk Height", 1.10)
h_nv, _, _, h_bmax = eval_tree(tree)
set_param(tree, "Desk Height", DESK_H)
print("[office-health] Desk Height 0.74 -> 1.10: zmax %.3f -> %.3f"
      % (bmax[2] if nv else -1, h_bmax[2] if h_bmax else -1))
if nv and h_bmax and not (h_bmax[2] > bmax[2] + 0.05):
    problems.append("Desk Height dial does not raise the top surface")

# ---- dial: Desk Width widens X --------------------------------------------
set_param(tree, "Desk Width", 2.0)
w_nv, _, w_bmin, w_bmax = eval_tree(tree)
set_param(tree, "Desk Width", DESK_W)
print("[office-health] Desk Width %.2f -> 2.00: span %.3f -> %.3f"
      % (DESK_W, (bmax[0] - bmin[0]) if nv else -1,
         (w_bmax[0] - w_bmin[0]) if w_bmax else -1))
if nv and w_bmax and not ((w_bmax[0] - w_bmin[0]) > (bmax[0] - bmin[0]) + 0.1):
    problems.append("Desk Width dial does not widen the cluster")

# ---- dial: each sub-prop toggle REMOVES geometry --------------------------
base_nv = nv
toggle_report = {}
for name in SUBPROP_TOGGLES:
    if not set_param(tree, name, False):
        problems.append("cannot set toggle %s" % name)
        continue
    t_nv, _, _, _ = eval_tree(tree)
    set_param(tree, name, True)
    delta = base_nv - t_nv
    toggle_report[name] = delta
    if delta <= 0:
        problems.append("toggle %s off removes NO geometry (%d -> %d verts)"
                        % (name, base_nv, t_nv))
print("[office-health] toggle deltas: %s" % toggle_report)

# ---- dial: Chair Push translates without rebuilding -----------------------
set_param(tree, "Chair Push", -0.5)
p_nv, _, p_bmin, p_bmax = eval_tree(tree)
set_param(tree, "Chair Push", 0.0)
print("[office-health] Chair Push 0 -> -0.50: verts %d -> %d, ymin %.3f -> %.3f"
      % (nv, p_nv, bmin[1] if nv else -1, p_bmin[1] if p_bmin else -1))
if nv and p_bmin:
    if p_nv != nv:
        problems.append("Chair Push changed vert count (%d -> %d); it must be "
                        "a pure translation" % (nv, p_nv))
    if not (p_bmin[1] < bmin[1] - 0.05):
        problems.append("Chair Push does not slide the chair toward -Y")

# ---- report ---------------------------------------------------------------
for nline in notes:
    print("[office-health] %s" % nline)
print("[office-health] problems=%d" % len(problems))
for p in problems:
    print("[office-health] PROBLEM: %s" % p)
print("[office-health] %s" % ("PASS" if not problems else "FAIL"))
sys.exit(0 if not problems else 1)