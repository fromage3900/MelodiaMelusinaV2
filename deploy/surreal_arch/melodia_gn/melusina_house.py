"""Melusina's House round-plan interior composer (Melodia Studio GN builder).

Composes the house's lower-level interior from the EXISTING registered
MEL_greybox_room_kit / MEL_greybox_corridor builders, laid out to the §16
round plan in melusinashouseplan.md:

  center      circular entry + sitting (round drum)
  left        music / prayer nook
  right       kitchen + pantry
  rear/right  curved stair to upper loft

The interior is one registered builder, so it appears in the Melodia Studio
GN Stack / catalog like any other kit and can be nested by GN_MH_00_MasterAssembly.
It does NOT rebuild room shells — it wraps the shipped greybox rooms with the
round-plan composition, per the plan's "reuse + wrap beats duplicate + drift".

Params exposed so a master group can drive it: Interior Height, Wall Thickness,
Show Interior.
"""
from __future__ import annotations

import bpy
import math

from .core import (
    safe_node, link_sockets, color_node, label_tree, new_geometry_tree,
    make_group_input, make_group_output, add_float_param, add_bool_param,
    add_music_influence_params, register_builder,
)
from .polyhedra_gn import (
    build_greybox_room_kit, build_greybox_corridor, build_greybox_junction,
)

# House body (plan §11). Interior sits on ground z=0; front facade toward -Y.
BODY = {"X0": -6.2, "X1": 6.2, "Y0": -1.4, "Y1": 4.2}


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


def _geo_out(node):
    if node is None:
        return None
    for o in node.outputs:
        if o.type == "GEOMETRY":
            return o
    return node.outputs[0] if node.outputs else None


def _place(tree, x, y, geo_src, pos, label):
    """Insert a Transform feeding geo_src; link and return the geometry output."""
    t = safe_node(tree, "GeometryNodeTransform", (x, y))
    t.label = label
    try:
        t.inputs["Translation"].default_value = pos
    except Exception:
        pass
    link_sockets(tree, geo_src, t.inputs["Geometry"])
    return _geo_out(t)


def _bevel(tree, x, y, geo_src, offset=0.03, segments=3):
    """Apply 5.2-native Mesh Bevel for soft rounded plaster edges.

    This is the geometry-node-native way to get the plan's "softness comes from
    rounded geometry" read without destroying edge flow. Offset on all edges of a
    hollow shell rounds the interior corners the way real plaster champfers.
    """
    bv = safe_node(tree, "GeometryNodeMeshBevel", (x, y))
    if bv is None:
        return geo_src
    link_sockets(tree, geo_src, bv.inputs["Mesh"])
    try:
        bv.inputs["Offset"].default_value = offset
        bv.inputs["Segments"].default_value = segments
        bv.inputs["Profile"].default_value = 1.0  # round profile (not chamfer)
    except Exception:
        pass
    return _geo_out(bv)


def _trim_ring(tree, x, y, center_xy, radius, height, r_out, r_in):
    """Profile-swept circular base/cornice ring using 5.2 sweep_profile.

    A closed circle curve swept with a small circle profile = a torus-like
    moulding band (baseboard / cornice) around the round entry drum. Matches the
    dado-band sweep_profile pattern in MEL_music_room_shell.
    """
    from .core import sweep_profile
    ring_curve = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (x - 200, y))
    if ring_curve is None:
        return None
    try:
        ring_curve.inputs["Radius"].default_value = radius
        ring_curve.inputs["Resolution"].default_value = 64
    except Exception:
        pass
    # lift curve to the band height at the drum center
    lift = safe_node(tree, "GeometryNodeTransform", (x, y))
    try:
        lift.inputs["Translation"].default_value = (center_xy[0], center_xy[1], height)
    except Exception:
        pass
    link_sockets(tree, _geo_out(ring_curve), lift.inputs["Geometry"])
    # sweep with an elliptical profile (r_out across, r_in up) via a scaled circle
    prof = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (x, y - 160))
    if prof is not None:
        try:
            prof.inputs["Radius"].default_value = r_out
            prof.inputs["Resolution"].default_value = 12
        except Exception:
            pass
    prof_xf = safe_node(tree, "GeometryNodeTransform", (x + 200, y - 160))
    if prof_xf is not None:
        link_sockets(tree, _geo_out(prof), prof_xf.inputs["Geometry"])
        try:
            prof_xf.inputs["Scale"].default_value = (1.0, 1.0, r_in / r_out)
        except Exception:
            pass
        prof_out = _geo_out(prof_xf)
    else:
        prof_out = _geo_out(prof)
    sweep = safe_node(tree, "GeometryNodeCurveToMesh", (x + 420, y))
    if sweep is None:
        return None
    link_sockets(tree, _geo_out(lift), sweep.inputs.get("Curve") or sweep.inputs[0])
    pk = sweep.inputs.get("Profile Curve") or sweep.inputs.get("Profile")
    if pk is not None:
        link_sockets(tree, prof_out, pk)
    return _geo_out(sweep)


def build_melusina_house_round_interior(group_name="MEL_melusina_house_round_interior"):
    """Round-plan lower interior: greybox rooms + round entry drum + curved stair."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    # This composer generates the interior from primitives and does not consume
    # an incoming Geometry, so sever new_geometry_tree's default input->output
    # passthrough to avoid a competing link on the Group Output Geometry socket.
    _out_sock = None
    for o in gout.inputs:
        if o.type == "GEOMETRY":
            _out_sock = o
            break
    if _out_sock is not None:
        for lnk in list(_out_sock.links):
            tree.links.remove(lnk)

    add_float_param(tree, "Interior Height", 3.1, 2.2, 4.5)
    add_float_param(tree, "Wall Thickness", 0.24, 0.1, 1.5)
    add_bool_param(tree, "Show Interior", True)
    add_bool_param(tree, "Include Stair", True)

    H = gin.outputs["Interior Height"]
    T = gin.outputs["Wall Thickness"]
    joins = []

    # --- left music / prayer nook ---
    nook = _ensure_group_node(tree, "MEL_greybox_room_kit",
                              build_greybox_room_kit, (bx - 700, by + 420))
    for nm, val in (("Room Length", 3.6), ("Room Width", 2.8),
                    ("Ceiling", False), ("Wall Thickness", 0.24)):
        if nm in nook.inputs:
            try:
                nook.inputs[nm].default_value = val
            except Exception:
                pass
    # nest under Interior Height control
    if "Room Height" in nook.inputs:
        link_sockets(tree, H, nook.inputs["Room Height"])
    nook_geo = _geo_out(nook)
    if nook_geo:
        joins.append(_place(tree, bx - 300, by + 420, nook_geo,
                            (-4.4, 1.7, 0.0), "place music nook"))

    # --- right kitchen + pantry ---
    kitch = _ensure_group_node(tree, "MEL_greybox_room_kit",
                               build_greybox_room_kit, (bx - 700, by + 200))
    for nm, val in (("Room Length", 3.6), ("Room Width", 2.8),
                    ("Ceiling", False), ("Wall Thickness", 0.24)):
        if nm in kitch.inputs:
            try:
                kitch.inputs[nm].default_value = val
            except Exception:
                pass
    if "Room Height" in kitch.inputs:
        link_sockets(tree, H, kitch.inputs["Room Height"])
    kitch_geo = _geo_out(kitch)
    if kitch_geo:
        joins.append(_place(tree, bx - 300, by + 200, kitch_geo,
                            (4.4, 1.7, 0.0), "place kitchen"))

    # --- center circular entry/sitting drum (round-plan identity) ---
    # solid round drum: outer cylinder minus inner = round wall shell, open
    outer = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 700, by))
    if outer is not None:
        outer.inputs["Radius"].default_value = 2.2
        outer.inputs["Depth"].default_value = H.default_value if hasattr(H, "default_value") else 3.1
        outer.inputs["Vertices"].default_value = 48
        outer.inputs["Side Segments"].default_value = 1
        outer.inputs["Fill Segments"].default_value = 1
    inner = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 700, by - 180))
    if inner is not None:
        inner.inputs["Radius"].default_value = 2.2 - 0.24
        inner.inputs["Depth"].default_value = 3.4
        inner.inputs["Vertices"].default_value = 48
        inner.inputs["Side Segments"].default_value = 1
        inner.inputs["Fill Segments"].default_value = 1
    # lift to sit on ground
    if outer is not None and inner is not None:
        o_lift = _place(tree, bx - 300, by, _geo_out(outer), (0, 0, 1.55), "outer drum lift")
        i_lift = _place(tree, bx - 300, by - 180, _geo_out(inner), (0, 0, 1.7), "inner void lift")
        if o_lift is not None and i_lift is not None:
            bn = safe_node(tree, "GeometryNodeMeshBoolean", (bx - 60, by))
            if bn is not None:
                bn.operation = "DIFFERENCE"
                try:
                    link_sockets(tree, o_lift, bn.inputs["Mesh 1"])
                    link_sockets(tree, i_lift, bn.inputs["Mesh 2"])
                except Exception:
                    pass
                joins.append(_geo_out(bn))
                color_node(bn, "math")

    # --- rear hall spine (corridor) ---
    hall = _ensure_group_node(tree, "MEL_greybox_corridor",
                              build_greybox_corridor, (bx - 700, by - 380))
    for nm, val in (("Length", 5.0), ("Width", 1.9), ("End Cap", False),
                    ("Wall Thickness", 0.24)):
        if nm in hall.inputs:
            try:
                hall.inputs[nm].default_value = val
            except Exception:
                pass
    if "Height" in hall.inputs:
        link_sockets(tree, H, hall.inputs["Height"])
    hall_geo = _geo_out(hall)
    if hall_geo:
        joins.append(_place(tree, bx - 300, by - 380, hall_geo,
                            (0.0, 3.2, 0.0), "place rear hall"))

    # --- rear/right curved stair (simple radial fan of treads) ---
    cx, cy, rad, n_steps = 2.4, 2.6, 1.5, 14
    STEP_T = 0.12  # tread thickness
    for i in range(n_steps):
        ang = math.radians(90) * (i / (n_steps - 1)) + math.radians(180)  # sweep back-right
        x = cx + rad * math.cos(ang)
        y = cy + rad * math.sin(ang)
        # bottom-most step rests on ground (z=0); center each cube half its
        # thickness above its bottom so no tread dips below the floor
        zbot = (i / (n_steps - 1)) * 3.0
        step = safe_node(tree, "GeometryNodeMeshCube", (bx - 700, by - 700 - i * 40))
        if step is not None:
            step.inputs["Size"].default_value = (0.6, 0.3, STEP_T)
            s = _place(tree, bx - 400, by - 700 - i * 40, _geo_out(step),
                       (x, y, zbot + STEP_T / 2), f"stair {i}")
            if s is not None:
                joins.append(s)

    # --- base moulding + cornice around the round entry drum (5.2 sweep_profile) ---
    # baseboard band at floor level, cornice band near the ceiling
    base = _trim_ring(tree, bx + 40, by + 240, (0.0, 0.6), 2.35, 0.10, 0.05, 0.02)
    if base is not None:
        joins.append(base)
    cornice = _trim_ring(tree, bx + 40, by + 380, (0.0, 0.6), 2.35, 3.0, 0.06, 0.025)
    if cornice is not None:
        joins.append(cornice)

    # --- join ---
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 220, by))
    if join is not None:
        for j in joins:
            if j is not None:
                try:
                    link_sockets(tree, j, join.inputs["Geometry"])
                except Exception:
                    pass
    # 5.2-native Mesh Bevel: soft rounded plaster on the whole interior shell
    beveled = _bevel(tree, bx + 460, by, _geo_out(join), offset=0.02, segments=2)

    # Show Interior switch
    empty = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 220, by - 200))
    sw = safe_node(tree, "GeometryNodeSwitch", (bx + 700, by))
    if sw is not None:
        sw.input_type = "GEOMETRY"
        link_sockets(tree, gin.outputs["Show Interior"], sw.inputs["Switch"])
        if empty is not None:
            link_sockets(tree, _geo_out(empty), sw.inputs["False"])
        if beveled is not None:
            link_sockets(tree, beveled, sw.inputs["True"])
        link_sockets(tree, _geo_out(sw), gout.inputs["Geometry"])

    color_node(join, "geometry")

    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Round Plan", "nodes": ("Greybox Room", "Mesh Cylinder", "Transform"), "role": "geometry"},
        {"title": "Switch", "nodes": ("Switch",), "role": "math"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    # Return only the tree (greybox convention). register_builder's _labeled_builder
    # wrapper auto-applies the universal music pass when it sees the (tree, gin, gout)
    # triple and passes gout's INPUT socket as a link source, which raises a spurious
    # "same direction" warning for every triple-returning builder. An interior layout
    # must NOT get harmonic displacement on its walls, so we skip the pass entirely.
    return tree


register_builder(
    "MEL_melusina_house_round_interior",
    build_melusina_house_round_interior,
    "Melusina House Round Interior",
    "Lower-level round-plan interior composed from greybox room shells: circular entry, music nook, kitchen, rear hall, curved stair.",
    category="structures",
)
