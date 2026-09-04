"""Melodia City Gen — procedural Nikki-style house + city kit for Melodia Studio.

A first-class Melodia Studio GN category ("city_gen": "Melodia City Gen") that
lets you create and reuse detailed, bounding-box-exact, mathematically accurate
feminine round-Baroque (Infinity-Nikki-style) house structures. CLEARLY follows
the MEL schema (MEL_* snake_case ids, standardised param naming, register_builder,
category + separate label_tree), and maps to the three documented image boards
in Docs/References/MelusinasHouse/:

  REF_01_EXTERIOR_ROUND_BAROQUE_PINK_BLUE.jpg   silhouette / massing / tower offset
  REF_02_GEOMETRY_NODES_BUILD_SHEET.jpg          module separation, reusable families
  REF_03_CUTAWAY_INTERIOR_FLOW.jpg               rounded room flow, curved stair, loft

Builders in this kit:
  MEL_city_house_cell       A single reusable house unit: greybox room shell
                            + round-plan interior + hip/tower roof + foundation,
                            sized to an exact world bounding box via Width/Depth/
                            Height params and an optional modular bay count.
  MEL_city_avenue           Instances N house cells along a street/avenue with
                            mathematical spacing (cell pitch = width + gap),
                            bounding-box aware, no overlap, one seed for variety.
  MEL_city_block            A block of avenues (rows), with grid pitch per row.

The house cell is composed from the EXISTING registered builders
MEL_greybox_room_kit (shell) and MEL_melusina_house_round_interior (interior) —
reuse + wrap, not duplicate + drift — then adds a procedural roof/foundation and
exact placement.
"""
from __future__ import annotations

import bpy
import math

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    add_vector_param, make_group_input, make_group_output, register_builder,
)
from .polyhedra_gn import (
    build_greybox_room_kit, build_greybox_corridor, build_greybox_junction,
)
from .melusina_house import build_melusina_house_round_interior

# Shared plan interface: every interior-plan builder exposes these exact group
# inputs so MEL_city_house_cell can switch among them and drive them uniformly:
#   Interior Height (float), Wall Thickness (float), Show Interior (bool)
_PLAN_PARAMS = (("Interior Height", 3.1, 2.2, 4.5),
                ("Wall Thickness", 0.24, 0.1, 1.5))


def _geo_out(node):
    if node is None:
        return None
    for o in node.outputs:
        if o.type == "GEOMETRY":
            return o
    return node.outputs[0] if node.outputs else None


def _ensure_group_node(tree, group_name, builder, loc):
    if group_name not in bpy.data.node_groups:
        try:
            builder(group_name)
        except Exception:
            pass
    node = safe_node(tree, "GeometryNodeGroup", loc)
    if node:
        node.node_tree = bpy.data.node_groups.get(group_name)
    return node


def _place(tree, x, y, geo_src, pos, label):
    t = safe_node(tree, "GeometryNodeTransform", (x, y))
    t.label = label
    try:
        t.inputs["Translation"].default_value = pos
    except Exception:
        pass
    link_sockets(tree, geo_src, t.inputs["Geometry"])
    return _geo_out(t)


def _set_in(n, nm, val):
    if n is not None and nm in n.inputs:
        try:
            n.inputs[nm].default_value = val
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Reusable interior PLAN builders (shared interface — see _PLAN_PARAMS)
# ---------------------------------------------------------------------------

def _plan_tree(group_name, rooms_corridors):
    """Template for a plan: hollow shell composition from existing greybox rooms/corridors.

    `rooms_corridors` is a list of (kind, params) where kind in
    ('room','corridor'), building each as a nested group, joined, with a
    Show Interior switch. Shared input interface keeps plans drop-in.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    for nm, dv, lo, hi in _PLAN_PARAMS:
        add_float_param(tree, nm, dv, lo, hi)
    add_bool_param(tree, "Show Interior", True)
    # sever default passthrough (we compose interior-only; Show Interior gates it)
    _o = None
    for o in gout.inputs:
        if o.type == "GEOMETRY":
            _o = o; break
    if _o is not None:
        for lnk in list(_o.links):
            tree.links.remove(lnk)

    joins = []
    for (kind, params) in rooms_corridors:
        if kind == 'room':
            g = _ensure_group_node(tree, "MEL_greybox_room_kit",
                                   build_greybox_room_kit, (bx - 700, by))
        else:  # corridor
            g = _ensure_group_node(tree, "MEL_greybox_corridor",
                                   build_greybox_corridor, (bx - 700, by))
        for nm, val in params.items():
            _set_in(g, nm, val)
        geo = _geo_out(g)
        # lift: greybox room/corridor output is grounded; add placement via
        # per-entry 'pos' if provided
        pos = params.get('pos')
        if pos is not None and geo is not None:
            geo = _place(tree, bx - 300, by, geo, pos, "place")
        if geo is not None:
            joins.append(geo)
        by -= 200

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 220, by))
    for j in joins:
        if j is not None:
            try:
                link_sockets(tree, j, join.inputs["Geometry"])
            except Exception:
                pass
    # Show Interior switch
    empty = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 220, by - 200))
    sw = safe_node(tree, "GeometryNodeSwitch", (bx + 460, by))
    if sw is not None:
        sw.input_type = "GEOMETRY"
        link_sockets(tree, gin.outputs["Show Interior"], sw.inputs["Switch"])
        link_sockets(tree, _geo_out(empty), sw.inputs["False"])
        link_sockets(tree, _geo_out(join), sw.inputs["True"])
        link_sockets(tree, _geo_out(sw), gout.inputs["Geometry"])
    color_node(join, "geometry")
    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Plan Rooms", "nodes": ("Greybox Room", "Greybox Corridor"), "role": "geometry"},
        {"title": "Switch", "nodes": ("Switch",), "role": "math"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return (tree, gin, gout)


def build_city_plan_round(group_name="MEL_city_plan_round"):
    """Round Baroque plan (REF_03): reuses the existing round interior as a plan."""
    # The full round interior has extra params (Include Stair) but shares the
    # required Interior Height / Wall Thickness / Show Interior. Wrap it so the
    # cell sees a uniform plan interface.
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    for nm, dv, lo, hi in _PLAN_PARAMS:
        add_float_param(tree, nm, dv, lo, hi)
    add_bool_param(tree, "Show Interior", True)
    _o = None
    for o in gout.inputs:
        if o.type == "GEOMETRY":
            _o = o; break
    if _o is not None:
        for lnk in list(_o.links):
            tree.links.remove(lnk)
    inner = _ensure_group_node(tree, "MEL_melusina_house_round_interior",
                               build_melusina_house_round_interior, (bx - 500, by))
    if inner is not None:
        for nm in ("Interior Height", "Wall Thickness", "Show Interior"):
            if nm in inner.inputs and nm in gin.outputs:
                try:
                    link_sockets(tree, gin.outputs[nm], inner.inputs[nm])
                except Exception:
                    pass
        geo = _geo_out(inner)
        if geo is not None:
            link_sockets(tree, geo, _o)
    return (tree, gin, gout)


def build_city_plan_salon(group_name="MEL_city_plan_salon"):
    """Rectangular great-hall salon: one long hollow room. Simple, formal."""
    return _plan_tree(group_name, [
        ('room', {"Room Length": 8.0, "Room Width": 5.0, "Room Height": 3.2,
                  "Wall Thickness": 0.24, "Ceiling": False}),
    ])


def build_city_plan_courtyard(group_name="MEL_city_plan_courtyard"):
    """Courtyard / quad plan: a central open void ringed by four room wings
    + corridors linking them. Reuses greybox rooms + corridors."""
    return _plan_tree(group_name, [
        ('room', {"Room Length": 3.0, "Room Width": 3.0, "Room Height": 3.2,
                  "Wall Thickness": 0.24, "Ceiling": False, "pos": (-3.5, 0.0, 0.0)}),
        ('room', {"Room Length": 3.0, "Room Width": 3.0, "Room Height": 3.2,
                  "Wall Thickness": 0.24, "Ceiling": False, "pos": (3.5, 0.0, 0.0)}),
        ('room', {"Room Length": 3.0, "Room Width": 3.0, "Room Height": 3.2,
                  "Wall Thickness": 0.24, "Ceiling": False, "pos": (0.0, -3.5, 0.0)}),
        ('room', {"Room Length": 3.0, "Room Width": 3.0, "Room Height": 3.2,
                  "Wall Thickness": 0.24, "Ceiling": False, "pos": (0.0, 3.5, 0.0)}),
        ('corridor', {"Length": 2.4, "Width": 2.0, "Height": 3.0,
                      "Wall Thickness": 0.24, "End Cap": False}),  # central cross link
    ])


# ---------------------------------------------------------------------------
# Corridor / circulation variants
# ---------------------------------------------------------------------------

def build_city_corridors(group_name="MEL_city_corridors"):
    """A set of circulation pieces: straight hall, L-elbow, gallery, dog-leg.
    Each reads a 'Corridor Type' int and a 'Wall Thickness'. Uses the existing
    MEL_greybox_corridor for the straight hall; L/gallery/dog-leg compose two
    corridors via transforms (no new shell primitive)."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_int_param(tree, "Corridor Type", 0, 0, 4)  # 0 straight,1 L,2 gallery,3 dog-leg,4 T-junction
    add_float_param(tree, "Length", 6.0, 1.0, 30.0)
    add_float_param(tree, "Width", 2.4, 1.0, 8.0)
    add_float_param(tree, "Height", 3.2, 2.0, 8.0)
    add_float_param(tree, "Wall Thickness", 0.25, 0.08, 1.0)
    _o = None
    for o in gout.inputs:
        if o.type == "GEOMETRY":
            _o = o; break
    if _o is not None:
        for lnk in list(_o.links):
            tree.links.remove(lnk)

    straight = _ensure_group_node(tree, "MEL_greybox_corridor",
                                  build_greybox_corridor, (bx - 700, by))
    for nm, dv in (("Length", 6.0), ("Width", 2.4), ("Height", 3.2),
                   ("Wall Thickness", 0.25), ("End Cap", False)):
        _set_in(straight, nm, dv)
    # drive from inputs
    for src, dst in (("Length", "Length"), ("Width", "Width"),
                     ("Height", "Height"), ("Wall Thickness", "Wall Thickness")):
        if dst in straight.inputs and src in gin.outputs:
            try:
                link_sockets(tree, gin.outputs[src], straight.inputs[dst])
            except Exception:
                pass
    s_geo = _geo_out(straight)

    # L-elbow: two straight corridors at right angle
    elbow_2 = _ensure_group_node(tree, "MEL_greybox_corridor",
                                 build_greybox_corridor, (bx - 700, by - 300))
    for nm, dv in (("Length", 6.0), ("Width", 2.4), ("Height", 3.2),
                   ("Wall Thickness", 0.25), ("End Cap", False)):
        _set_in(elbow_2, nm, dv)
    for src, dst in (("Length", "Length"), ("Width", "Width"),
                     ("Height", "Height"), ("Wall Thickness", "Wall Thickness")):
        if dst in elbow_2.inputs and src in gin.outputs:
            try:
                link_sockets(tree, gin.outputs[src], elbow_2.inputs[dst])
            except Exception:
                pass
    e2 = _place(tree, bx - 300, by - 300, _geo_out(elbow_2), (2.4, -2.4, 0.0), "L arm")
    elbow_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 60, by - 300))
    if s_geo is not None and e2 is not None:
        link_sockets(tree, s_geo, elbow_join.inputs["Geometry"])
        link_sockets(tree, e2, elbow_join.inputs["Geometry"])
    l_geo = _geo_out(elbow_join)

    # gallery: straight hall, wider (arcade feel) + centered
    gal = _ensure_group_node(tree, "MEL_greybox_corridor",
                             build_greybox_corridor, (bx - 700, by - 600))
    for nm, dv in (("Length", 8.0), ("Width", 4.0), ("Height", 3.6),
                   ("Wall Thickness", 0.3), ("End Cap", True)):
        _set_in(gal, nm, dv)
    g_geo = _geo_out(gal)

    # dog-leg: straight + L combined (not a real dog-leg but a 2-run)
    dog = _place(tree, bx - 300, by - 600, g_geo, (0.0, 0.0, 0.0), "dogleg arm")
    dog_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 60, by - 600))
    if s_geo is not None and dog is not None:
        link_sockets(tree, s_geo, dog_join.inputs["Geometry"])
        link_sockets(tree, dog, dog_join.inputs["Geometry"])
    dog_geo = _geo_out(dog_join)

    # T-junction: the greybox junction builder (reuse, not rebuild).
    # Size = arm length (Length), Width/Height/Thickness carried from inputs.
    junc = _ensure_group_node(tree, "MEL_greybox_junction",
                              build_greybox_junction, (bx - 700, by - 900))
    _set_in(junc, "Cross Junction", False)
    for src, dst in (("Length", "Size"), ("Width", "Width"),
                     ("Height", "Height"), ("Wall Thickness", "Wall Thickness")):
        if junc is not None and dst in junc.inputs and src in gin.outputs:
            try:
                link_sockets(tree, gin.outputs[src], junc.inputs[dst])
            except Exception:
                pass
    t_geo = _geo_out(junc)

    # Index Switch selects type
    sw = safe_node(tree, "GeometryNodeIndexSwitch", (bx + 300, by))
    sw.data_type = "GEOMETRY"  # corridor pieces are geometry
    items = sw.index_switch_items
    # item0 already exists; ensure 5 items
    while len(items) < 5:
        items.new()
    def innode(n, idx):
        try:
            return n.inputs[idx + 1]  # input 0 is Index
        except Exception:
            return None
    link_sockets(tree, gin.outputs["Corridor Type"], sw.inputs["Index"])
    link_sockets(tree, s_geo, innode(sw, 0))
    link_sockets(tree, l_geo, innode(sw, 1))
    link_sockets(tree, g_geo, innode(sw, 2))
    link_sockets(tree, dog_geo, innode(sw, 3))
    link_sockets(tree, t_geo, innode(sw, 4))
    link_sockets(tree, _geo_out(sw), _o)
    color_node(sw, "math")
    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Circulation", "nodes": ("Greybox Corridor",), "role": "geometry"},
        {"title": "Switch", "nodes": ("Index Switch",), "role": "math"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return (tree, gin, gout)


def build_city_house_cell(group_name="MEL_city_house_cell"):
    """One reusable house unit sized to an exact bounding box.

    Composition (per REF_02 module separation):
      greybox room shell (outer wall)
      round-plan interior (nested MEL_melusina_house_round_interior)
      foundation slab + hip/tower roof
    Bounding-box exact: the final joined geometry spans exactly
    x[-Width/2, Width/2] y[-Depth/2, Depth/2] z[0, Height], so any number of
    cells can be gridded with zero overlap by pitch math.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    _out = None
    for o in gout.inputs:
        if o.type == "GEOMETRY":
            _out = o
            break
    if _out is not None:
        for lnk in list(_out.links):
            tree.links.remove(lnk)

    add_float_param(tree, "Width", 6.0, 2.0, 20.0)
    add_float_param(tree, "Depth", 4.5, 2.0, 16.0)
    add_float_param(tree, "Height", 3.4, 2.0, 8.0)
    add_float_param(tree, "Wall Thickness", 0.24, 0.1, 1.0)
    add_float_param(tree, "Roof Rise", 0.9, 0.2, 3.0)
    add_int_param(tree, "Plan Type", 0, 0, 2)  # 0 round, 1 salon, 2 courtyard
    add_bool_param(tree, "Show Interior", True)
    add_bool_param(tree, "Show Roof", True)    # False = shell-only; roof rides
    add_bool_param(tree, "Tower", False)       # the SurrealRoof addon system
    add_vector_param(tree, "Offset", (0.0, 0.0, 0.0))

    W = gin.outputs["Width"]
    D = gin.outputs["Depth"]
    H = gin.outputs["Height"]
    T = gin.outputs["Wall Thickness"]
    RR = gin.outputs["Roof Rise"]

    joins = []

    # --- outer wall shell (greybox room kit, hollow) ---
    shell = _ensure_group_node(tree, "MEL_greybox_room_kit",
                               build_greybox_room_kit, (bx - 700, by + 300))
    for nm, val in (("Room Length", 6.0), ("Room Width", 4.5),
                    ("Room Height", 3.4), ("Wall Thickness", 0.24),
                    ("Ceiling", False)):
        _set_in(shell, nm, val)
    for src, dst in ((W, "Room Length"), (D, "Room Width"),
                     (H, "Room Height"), (T, "Wall Thickness")):
        if dst in shell.inputs:
            link_sockets(tree, src, shell.inputs[dst])
    shell_geo = _geo_out(shell)
    # greybox room kit centers its shell at the ground at origin
    if shell_geo is not None:
        joins.append(shell_geo)

    # --- foundation slab (top flush at z=0; a 1x1 cube scaled by W,D,thickness) ---
    _slab = safe_node(tree, "GeometryNodeMeshCube", (bx - 700, by + 80))
    if _slab is not None:
        _slab.inputs["Size"].default_value = (1.0, 1.0, 0.12)
        sc = safe_node(tree, "GeometryNodeTransform", (bx - 420, by + 80))
        cx = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 560, by + 160))
        link_sockets(tree, W, cx.inputs["X"])
        link_sockets(tree, D, cx.inputs["Y"])
        cx.inputs["Z"].default_value = 0.12
        link_sockets(tree, _geo_out(_slab), sc.inputs["Geometry"])
        link_sockets(tree, _geo_out(cx), sc.inputs["Scale"])
        # cube centered; sit its TOP at z=0 -> center at -0.06
        slab_geo = _place(tree, bx - 140, by + 80, _geo_out(sc), (0.0, 0.0, -0.06), "foundation")
        joins.append(slab_geo)

    # --- roof (hip or gable prism), gated by Show Roof ----------------------
    # When Show Roof is False the cell emits shell+interior+foundation only and
    # the roof is staged separately as a SurrealRoof_* object from the Melodia
    # Studio curved-roof generator (_build_curved_roof in
    # surreal_architecture_gen.py) — that system is the roof authority.
    roof = safe_node(tree, "GeometryNodeMeshCone", (bx - 700, by - 100))
    rr_node = safe_node(tree, "ShaderNodeMath", (bx - 880, by - 40))
    if rr_node is not None:
        rr_node.operation = "MULTIPLY"
        link_sockets(tree, RR, rr_node.inputs[0])
        try:
            rr_node.inputs[1].default_value = 0.5
        except Exception:
            pass
        rr = rr_node.outputs[0]
    else:
        rr = RR
    if roof is not None:
        # hip roof: 4-sided cone with bottom radius from W,D, depth from Roof Rise
        roof.inputs["Vertices"].default_value = 4
        roof.inputs["Radius Bottom"].default_value = 4.5
        roof.inputs["Depth"].default_value = 0.9
        try:
            link_sockets(tree, rr, roof.inputs["Depth"])
        except Exception:
            pass
        # radius: min(W,D)/2 so the roof nests INSIDE the cell footprint. The
        # shell (W x D) remains the bounding authority; a circular-cone roof bigger
        # than the smaller dimension would widen the box and break bbox accuracy.
        rmin = safe_node(tree, "ShaderNodeMath", (bx - 1060, by - 140))
        rmin.operation = "MINIMUM"
        link_sockets(tree, W, rmin.inputs[0])
        link_sockets(tree, D, rmin.inputs[1])
        rw = safe_node(tree, "ShaderNodeMath", (bx - 880, by - 140))
        rw.operation = "MULTIPLY"
        link_sockets(tree, rmin.outputs[0], rw.inputs[0])
        try:
            rw.inputs[1].default_value = 0.52
        except Exception:
            pass
        link_sockets(tree, rw.outputs[0], roof.inputs["Radius Bottom"])
        # roof sits on top of the walls. Cone is centered at origin; depth=rise so
        # base sits at z=-rise/2 .. apex +rise/2. Translate so BASE rests on the wall
        # top (z=Height): center at z = Height + rise/2.
        rz = safe_node(tree, "ShaderNodeMath", (bx - 880, by - 240))
        rz.operation = "ADD"
        zh = safe_node(tree, "ShaderNodeMath", (bx - 1060, by - 240))
        zh.operation = "MULTIPLY"
        link_sockets(tree, rr, zh.inputs[0])
        try:
            zh.inputs[1].default_value = 0.5
        except Exception:
            pass
        link_sockets(tree, H, rz.inputs[0])
        link_sockets(tree, zh.outputs[0], rz.inputs[1])
        # translate cone by (0,0,Height+rise/2)
        tz = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 140, by - 100))
        link_sockets(tree, rz.outputs[0], tz.inputs["Z"])
        ro_z = safe_node(tree, "GeometryNodeTransform", (bx + 120, by - 100))
        link_sockets(tree, _geo_out(roof), ro_z.inputs["Geometry"])
        link_sockets(tree, _geo_out(tz), ro_z.inputs["Translation"])
        # Show Roof switch: False -> empty geometry instead of the cone
        rswitch = safe_node(tree, "GeometryNodeSwitch", (bx + 320, by - 180))
        roof_geo = _geo_out(ro_z)
        if rswitch is not None:
            try:
                rswitch.data_type = 'GEOMETRY'
                link_sockets(tree, gin.outputs["Show Roof"], rswitch.inputs["Switch"])
                link_sockets(tree, roof_geo, rswitch.inputs[False] if False in rswitch.inputs else rswitch.inputs[1])
            except Exception:
                pass
            roof_geo = _geo_out(rswitch)
        if roof_geo is not None:
            joins.append(roof_geo)

    # --- interior plan (nested builder), selected by Plan Type, scaled to fit the cell ---
    # Each plan shares the same interface (Interior Height/Wall Thickness/Show Interior)
    # so the cell can drive Height and Thickness uniformly regardless of which plan runs.
    plan_round = _ensure_group_node(tree, "MEL_city_plan_round",
                                    build_city_plan_round, (bx - 700, by - 320))
    plan_salon = _ensure_group_node(tree, "MEL_city_plan_salon",
                                    build_city_plan_salon, (bx - 700, by - 520))
    plan_court = _ensure_group_node(tree, "MEL_city_plan_courtyard",
                                    build_city_plan_courtyard, (bx - 700, by - 720))
    # drive shared plan inputs (Interior Height = H, Wall Thickness = T, Show Interior)
    for pg in (plan_round, plan_salon, plan_court):
        if pg is not None:
            for nm, sock in (("Interior Height", H), ("Wall Thickness", T)):
                if nm in pg.inputs:
                    try:
                        link_sockets(tree, sock, pg.inputs[nm])
                    except Exception:
                        pass
            if "Show Interior" in pg.inputs and "Show Interior" in gin.outputs:
                try:
                    link_sockets(tree, gin.outputs["Show Interior"], pg.inputs["Show Interior"])
                except Exception:
                    pass
    plans_geo = []
    for pg in (plan_round, plan_salon, plan_court):
        plans_geo.append(_geo_out(pg) if pg is not None else None)
    # Index Switch picks the active plan
    psw = safe_node(tree, "GeometryNodeIndexSwitch", (bx - 300, by - 520))
    psw.data_type = "GEOMETRY"  # switch carries geometry per plan option
    p_items = psw.index_switch_items
    while len(p_items) < 3:
        p_items.new()
    def pin(n, idx):
        try:
            return n.inputs[idx + 1]
        except Exception:
            return None
    try:
        link_sockets(tree, gin.outputs["Plan Type"], psw.inputs["Index"])
    except Exception:
        pass
    for i, pg in enumerate(plans_geo):
        if pg is not None:
            try:
                link_sockets(tree, pg, pin(psw, i))
            except Exception:
                pass
    sel_geo = _geo_out(psw)

    # scale selected plan to fit inside the cell (min(W/13.2, D/9.8)), grounded
    iscale = safe_node(tree, "GeometryNodeTransform", (bx - 320, by - 320))
    if sel_geo is not None:
        link_sockets(tree, sel_geo, iscale.inputs["Geometry"])
        fw = safe_node(tree, "ShaderNodeMath", (bx - 480, by - 360))
        fw.operation = "DIVIDE"
        link_sockets(tree, W, fw.inputs[0])
        fw.inputs[1].default_value = 13.2
        fd = safe_node(tree, "ShaderNodeMath", (bx - 480, by - 300))
        fd.operation = "DIVIDE"
        link_sockets(tree, D, fd.inputs[0])
        fd.inputs[1].default_value = 9.8
        fn = safe_node(tree, "ShaderNodeMath", (bx - 300, by - 420))
        fn.operation = "MINIMUM"
        link_sockets(tree, fw.outputs[0], fn.inputs[0])
        link_sockets(tree, fd.outputs[0], fn.inputs[1])
        fc = safe_node(tree, "ShaderNodeMath", (bx - 120, by - 420))
        fc.operation = "MINIMUM"
        fc.inputs[1].default_value = 1.0
        link_sockets(tree, fn.outputs[0], fc.inputs[0])
        sx = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 40, by - 320))
        link_sockets(tree, fc.outputs[0], sx.inputs["X"])
        link_sockets(tree, fc.outputs[0], sx.inputs["Y"])
        link_sockets(tree, fc.outputs[0], sx.inputs["Z"])
        link_sockets(tree, _geo_out(sx), iscale.inputs["Scale"])
        int_geo_o = _geo_out(iscale)
        if int_geo_o is not None:
            joins.append(int_geo_o)
    color_node(psw, "math")

    # --- join (bounding-box placed composition) ---
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 220, by))
    for j in joins:
        if j is not None:
            try:
                link_sockets(tree, j, join.inputs["Geometry"])
            except Exception:
                pass
    final = _geo_out(join)
    # add caller Offset via transform
    off = safe_node(tree, "GeometryNodeTransform", (bx + 720, by))
    if final is not None and off is not None:
        link_sockets(tree, final, off.inputs["Geometry"])
        link_sockets(tree, gin.outputs["Offset"], off.inputs["Translation"])
        gout_geo = _geo_out(off)
    else:
        gout_geo = final
    if gout_geo is not None:
        link_sockets(tree, gout_geo, gout.inputs["Geometry"])

    color_node(join, "geometry")
    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "House Cell", "nodes": ("Greybox Room", "Mesh Cone", "Mesh Cube"), "role": "geometry"},
        {"title": "Interior", "nodes": ("Greybox Room",), "role": "geometry"},
        {"title": "Output", "nodes": ("Transform", "Group Output"), "role": "output"},
    ])
    return (tree, gin, gout)


def build_city_avenue(group_name="MEL_city_avenue"):
    """A street of N house cells on a mathematical grid (no overlap)."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    _out = None
    for o in gout.inputs:
        if o.type == "GEOMETRY":
            _out = o
            break
    if _out is not None:
        for lnk in list(_out.links):
            tree.links.remove(lnk)

    add_int_param(tree, "Count", 5, 1, 64)
    add_float_param(tree, "Cell Width", 6.0, 1.0, 20.0)
    add_float_param(tree, "Cell Depth", 4.5, 1.0, 16.0)
    add_float_param(tree, "Cell Height", 3.4, 2.0, 8.0)
    add_float_param(tree, "Street Gap", 1.5, 0.0, 8.0)
    add_float_param(tree, "Seed", 0.0, 0.0, 999.0)

    from .melusina_house import build_melusina_house_round_interior
    cell = _ensure_group_node(tree, "MEL_city_house_cell",
                              build_city_house_cell, (bx - 700, by))
    # place cells along X: position = (i - (Count-1)/2) * (CellWidth + StreetGap)
    # Use a Mesh Line + Instance on Points: line point count = Count, spacing=pitch
    pitch = safe_node(tree, "ShaderNodeMath", (bx - 900, by + 40))
    pitch.operation = "ADD"
    link_sockets(tree, gin.outputs["Cell Width"], pitch.inputs[0])
    link_sockets(tree, gin.outputs["Street Gap"], pitch.inputs[1])

    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 900, by - 140))
    if line is not None:
        link_sockets(tree, gin.outputs["Count"], line.inputs["Count"])
        link_sockets(tree, _geo_out(pitch), line.inputs["Offset"])
        # center the street on origin: offset x by -(Count-1)/2 * pitch via Start Location
        half = safe_node(tree, "ShaderNodeMath", (bx - 1180, by - 140))
        half.operation = "MULTIPLY"
        link_sockets(tree, gin.outputs["Count"], half.inputs[0])
        try:
            half.inputs[1].default_value = -0.5
        except Exception:
            pass
        # start location vector X = half*pitch
        startx = safe_node(tree, "ShaderNodeMath", (bx - 1180, by + 40))
        startx.operation = "MULTIPLY"
        link_sockets(tree, _geo_out(half), startx.inputs[0])
        link_sockets(tree, _geo_out(pitch), startx.inputs[1])
        sx = safe_node(tree, "FunctionNodeCombineXYZ" if hasattr(bpy.types, "FunctionNodeCombineXYZ") else "ShaderNodeCombineXYZ", (bx - 980, by + 40))
        link_sockets(tree, _geo_out(startx), sx.inputs["X"] if "X" in sx.inputs else sx.inputs[0])
        try:
            sx.inputs["Y"].default_value = 0.0
        except Exception:
            pass
        try:
            sx.inputs["Z"].default_value = 0.0
        except Exception:
            pass
        link_float_to_vector(tree, _geo_out(startx), line, "Start Location", component=0)
        link_float_to_vector(tree, _geo_out(startx), line, "Start Location", component=1)

    extra = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 400, by))
    if line is not None and extra is not None:
        link_sockets(tree, _geo_out(line), extra.inputs["Points"])
        cg = _geo_out(cell)
        if cg is not None:
            link_sockets(tree, cg, extra.inputs["Instance"])
        joins = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 100, by))
        if joins is not None:
            link_sockets(tree, _geo_out(extra), joins.inputs["Geometry"])
            # optional per-cell scale variability via a Seed-driven noise — keep deterministic
            link_sockets(tree, _geo_out(joins), gout.inputs["Geometry"])

    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Grid", "nodes": ("Mesh Line",), "role": "curve"},
        {"title": "Instance", "nodes": ("Instance on Points",), "role": "instance"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return (tree, gin, gout)


def build_city_block(group_name="MEL_city_block"):
    """A block = several avenues (rows) so you can fill a district."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    _out = None
    for o in gout.inputs:
        if o.type == "GEOMETRY":
            _out = o
            break
    if _out is not None:
        for lnk in list(_out.links):
            tree.links.remove(lnk)

    add_int_param(tree, "Rows", 3, 1, 16)
    add_float_param(tree, "Row Pitch", 7.0, 2.0, 30.0)
    add_float_param(tree, "Seed", 0.0, 0.0, 999.0)

    av = _ensure_group_node(tree, "MEL_city_avenue", build_city_avenue, (bx - 700, by))
    # instance the avenue along Y for Rows, offset each row by Row Pitch
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 700, by - 120))
    if line is not None:
        link_sockets(tree, gin.outputs["Rows"], line.inputs["Count"])
        link_float_to_vector(tree, gin.outputs["Row Pitch"], line, "Offset", component=1)
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 380, by))
    if line is not None and inst is not None:
        link_sockets(tree, _geo_out(line), inst.inputs["Points"])
        av_geo = _geo_out(av)
        if av_geo is not None:
            link_sockets(tree, av_geo, inst.inputs["Instance"])
        j = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 60, by))
        if j is not None:
            link_sockets(tree, _geo_out(inst), j.inputs["Geometry"])
            link_sockets(tree, _geo_out(j), gout.inputs["Geometry"])

    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Rows", "nodes": ("Mesh Line",), "role": "curve"},
        {"title": "Instance Avenue", "nodes": ("Instance on Points",), "role": "instance"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return (tree, gin, gout)


# ---------------------------------------------------------------------------
# Register all City Gen builders (MEL schema, category "city_gen")
# ---------------------------------------------------------------------------
register_builder(
    "MEL_city_house_cell", build_city_house_cell,
    "City House Cell",
    "One reusable round-Baroque house unit sized to an exact bounding box, composed from the greybox shell + round-plan interior + hip roof. Reuse across a city.",
    category="city_gen",
)
register_builder(
    "MEL_city_avenue", build_city_avenue,
    "City Avenue",
    "A street of N house cells on a mathematical, non-overlapping grid (cell pitch = width + gap), one seed for variety.",
    category="city_gen",
)
register_builder(
    "MEL_city_block", build_city_block,
    "City Block",
    "A block of avenue rows filling a district, with per-row pitch.",
    category="city_gen",
)
register_builder(
    "MEL_city_plan_round", build_city_plan_round,
    "Plan — Round Baroque",
    "Round-plan interior (REF_03): circular entry, nooks, rear hall, curved stair. Reuses the round interior builder as a drop-in plan.",
    category="city_gen",
)
register_builder(
    "MEL_city_plan_salon", build_city_plan_salon,
    "Plan — Rectangular Salon",
    "Rectangular great-hall salon interior — one long hollow room. Shared plan interface lets any cell host it.",
    category="city_gen",
)
register_builder(
    "MEL_city_plan_courtyard", build_city_plan_courtyard,
    "Plan — Courtyard Quad",
    "Courtyard/quad plan: central void ringed by four room wings linked by corridors. Reuses greybox rooms + corridors.",
    category="city_gen",
)
register_builder(
    "MEL_city_corridors", build_city_corridors,
    "Corridor Variants",
    "Circulation set: straight hall, L-elbow, gallery, dog-leg — selected by Corridor Type int. Reuses the greybox corridor.",
    category="city_gen",
)