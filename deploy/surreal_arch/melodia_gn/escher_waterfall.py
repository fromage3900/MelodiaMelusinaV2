"""Escher Waterfall -- HERO GN builder.

Impossible perpetually-descending water channel loop (Escher's "Waterfall",
a Penrose tribar illusion): a rectangular water channel where every side
reads as flowing DOWNHILL, yet the loop closes. The tall corner is capped
by a cascade falling from the highest level back to the start.

Every parameter is an editable named input on the node group.
"""

from __future__ import annotations

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
)


def _math(tree, operation, loc, a=None, b=None):
    n = safe_node(tree, "ShaderNodeMath", loc)
    try:
        n.operation = operation
    except Exception:
        pass
    if a is not None:
        if isinstance(a, (int, float)):
            n.inputs[0].default_value = a
        else:
            link_sockets(tree, a, n.inputs[0])
    if b is not None:
        if isinstance(b, (int, float)):
            n.inputs[1].default_value = b
        else:
            link_sockets(tree, b, n.inputs[1])
    return n


def _combine(tree, loc, x, y, z):
    n = safe_node(tree, "ShaderNodeCombineXYZ", loc)
    for comp, val in (("X", x), ("Y", y), ("Z", z)):
        if val is None:
            continue
        if isinstance(val, (int, float)):
            try:
                n.inputs[comp].default_value = val
            except Exception:
                pass
        else:
            link_sockets(tree, val, n.inputs[comp])
    return n


def _position_piece(tree, loc, geometry_sock, x=None, y=None, z=None):
	transform = safe_node(tree, "GeometryNodeTransform", loc)
	link_sockets(tree, geometry_sock, transform.inputs["Geometry"])
	if x is not None or y is not None or z is not None:
		pos = _combine(tree, (loc[0] - 200, loc[1] - 120), x, y, z)
		link_sockets(tree, pos.outputs["Vector"], transform.inputs["Translation"])
	return transform.outputs["Geometry"]


def _add_wobble(tree, geometry_sock, variation_sock, seed_sock, loc):
    pos = safe_node(tree, "GeometryNodeInputPosition", (loc[0] - 260, loc[1] - 140))
    noise = safe_node(tree, "ShaderNodeTexNoise", loc)
    seed_vec = _combine(tree, (loc[0] - 260, loc[1] + 100), seed_sock, 0.0, 0.0)
    noise_in = safe_node(tree, "ShaderNodeVectorMath", (loc[0] - 60, loc[1] + 100))
    noise_in.operation = "ADD"
    link_sockets(tree, pos.outputs["Position"], noise_in.inputs[0])
    link_sockets(tree, seed_vec.outputs["Vector"], noise_in.inputs[1])
    link_sockets(tree, noise_in.outputs["Vector"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = 1.8
    noise.inputs["Detail"].default_value = 2.0
    sub = _math(tree, "SUBTRACT", (loc[0] + 180, loc[1] - 140), noise.outputs["Fac"], 0.5)
    amp = _math(tree, "MULTIPLY", (loc[0] + 180, loc[1] - 260), variation_sock, 0.1)
    wob = _math(tree, "MULTIPLY", (loc[0] + 340, loc[1] - 140), sub.outputs[0], amp.outputs[0])
    offset = _combine(tree, (loc[0] + 500, loc[1] - 140), wob.outputs[0], wob.outputs[0], 0.0)
    vadd = safe_node(tree, "ShaderNodeVectorMath", (loc[0] + 340, loc[1] - 320))
    vadd.operation = "ADD"
    link_sockets(tree, pos.outputs["Position"], vadd.inputs[0])
    link_sockets(tree, offset.outputs["Vector"], vadd.inputs[1])
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (loc[0] + 680, loc[1] - 140))
    link_sockets(tree, geometry_sock, set_pos.inputs["Geometry"])
    link_sockets(tree, vadd.outputs["Vector"], set_pos.inputs["Position"])
    return set_pos.outputs["Geometry"]


def _channel_section(tree, gin, loc, length_sock):
    """One channel side: two walls + floor + water, oriented along X, at z=0."""
    bx, by = loc
    half = _math(tree, "MULTIPLY", (bx - 1200, by), gin.outputs["Channel Width"], 0.5)
    wall_l = safe_node(tree, "GeometryNodeMeshCube", (bx - 1000, by + 120))
    wall_l_size = _combine(tree, (bx - 1200, by + 60), length_sock,
                           gin.outputs["Channel Width"], gin.outputs["Channel Depth"])
    link_sockets(tree, wall_l_size.outputs["Vector"], wall_l.inputs["Size"])
    wall_l_out = _position_piece(tree, (bx - 800, by + 120), wall_l.outputs["Mesh"],
                                 x=0.0, y=half.outputs[0], z=0.0)

    wall_r = safe_node(tree, "GeometryNodeMeshCube", (bx - 1000, by - 120))
    wall_r_size = _combine(tree, (bx - 1200, by - 180), length_sock,
                           gin.outputs["Channel Width"], gin.outputs["Channel Depth"])
    link_sockets(tree, wall_r_size.outputs["Vector"], wall_r.inputs["Size"])
    wall_r_out = _position_piece(tree, (bx - 800, by - 120), wall_r.outputs["Mesh"],
                                 x=0.0, y=_math(tree, "MULTIPLY", (bx - 1200, by - 220),
                                                gin.outputs["Channel Width"], -0.5).outputs[0],
                                 z=0.0)

    floor = safe_node(tree, "GeometryNodeMeshCube", (bx - 1000, by))
    floor_size = _combine(tree, (bx - 1200, by - 60), length_sock,
                          gin.outputs["Channel Width"], 0.12)
    link_sockets(tree, floor_size.outputs["Vector"], floor.inputs["Size"])
    floor_out = _position_piece(tree, (bx - 800, by), floor.outputs["Mesh"],
                                x=0.0, y=0.0, z=-0.06)

    water = safe_node(tree, "GeometryNodeMeshCube", (bx - 1000, by - 320))
    water_w = _math(tree, "MULTIPLY", (bx - 1200, by - 320), gin.outputs["Channel Width"], 0.6)
    water_len = _math(tree, "MULTIPLY", (bx - 1200, by - 360), length_sock, 0.92)
    water_size = _combine(tree, (bx - 1000, by - 380), water_len.outputs[0], water_w.outputs[0],
                          gin.outputs["Water Level"])
    link_sockets(tree, water_size.outputs["Vector"], water.inputs["Size"])
    water_z = _math(tree, "ADD", (bx - 1200, by - 420), gin.outputs["Channel Depth"], 0.02)
    water_out = _position_piece(tree, (bx - 800, by - 320), water.outputs["Mesh"],
                                x=0.0, y=0.0, z=water_z.outputs[0])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 400, by))
    link_sockets(tree, wall_l_out, join.inputs["Geometry"])
    link_sockets(tree, wall_r_out, join.inputs["Geometry"])
    link_sockets(tree, floor_out, join.inputs["Geometry"])
    link_sockets(tree, water_out, join.inputs["Geometry"])
    return join.outputs["Geometry"]


def build_escher_waterfall(group_name="MEL_escher_waterfall"):
    """Escher Waterfall -- impossible descending water channel loop.

    Four channel sides, each lower than the last; a cascade at the tall
    corner returns the water to the start level.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Channel Length X", 6.0, 3.0, 12.0)
    add_float_param(tree, "Channel Length Y", 4.5, 3.0, 10.0)
    add_float_param(tree, "Channel Width", 1.0, 0.6, 2.0)
    add_float_param(tree, "Channel Depth", 0.5, 0.3, 1.2)
    add_float_param(tree, "Water Level", 0.15, 0.05, 0.4)
    add_float_param(tree, "Side Drop", 0.4, 0.1, 1.5)
    add_float_param(tree, "Cascade Width", 1.4, 0.8, 3.0)
    add_bool_param(tree, "Cascade", True)
    add_bool_param(tree, "Pillars", True)
    add_bool_param(tree, "Tribar Arch", True)
    add_bool_param(tree, "Splash Ring", True)
    add_float_param(tree, "Wobble", 0.05, 0.0, 0.3)
    add_int_param(tree, "Seed", 7, 0, 9999)

    # Four cardinal sides. X-length sides run along the top/bottom edges;
    # Y-length sides run along the left/right edges.
    sides = [0.0, 1.5708, 3.14159, 4.71239]
    pieces = []
    for i, rot in enumerate(sides):
        length_sock = gin.outputs["Channel Length X"] if i % 2 == 0 else gin.outputs["Channel Length Y"]
        side_z = _math(tree, "MULTIPLY", (bx - 1400, by - 200 + i * -260),
                       gin.outputs["Side Drop"], i * 1.0)
        section = _channel_section(tree, gin, (bx - 1000, by - 200 + i * -260), length_sock)
        rot_z = _math(tree, "MULTIPLY", (bx - 1200, by - 240 + i * -260), rot, 1.0)
        tx = safe_node(tree, "GeometryNodeTransform", (bx - 600, by - 200 + i * -260))
        link_sockets(tree, section, tx.inputs["Geometry"])
        link_float_to_vector(tree, rot_z.outputs[0], tx, "Rotation",
                             component=2, defaults=(0.0, 0.0, 0.0))
        half_x = _math(tree, "MULTIPLY", (bx - 1200, by - 280 + i * -260),
                       gin.outputs["Channel Length X"], 0.5)
        half_y = _math(tree, "MULTIPLY", (bx - 1200, by - 320 + i * -260),
                       gin.outputs["Channel Length Y"], 0.5)
        if i == 0:
            center_x, center_y = 0.0, half_y.outputs[0]
        elif i == 1:
            center_x, center_y = half_x.outputs[0], 0.0
        elif i == 2:
            center_x = 0.0
            center_y = _math(
                tree, "MULTIPLY", (bx - 1000, by - 360 + i * -260), half_y.outputs[0], -1.0
            ).outputs[0]
        else:
            center_x = _math(
                tree, "MULTIPLY", (bx - 1000, by - 360 + i * -260), half_x.outputs[0], -1.0
            ).outputs[0]
            center_y = 0.0
        tx_out = _position_piece(tree, (bx - 400, by - 200 + i * -260), tx.outputs["Geometry"],
                                 x=center_x, y=center_y, z=side_z.outputs[0])
        pieces.append(tx_out)

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx, by - 300))
    for p in pieces:
        link_sockets(tree, p, join.inputs["Geometry"])

    fall_h = _math(tree, "MULTIPLY", (bx + 300, by - 480), gin.outputs["Side Drop"], 3.0)
    half_x = _math(tree, "MULTIPLY", (bx + 100, by - 520), gin.outputs["Channel Length X"], 0.5)
    half_y = _math(tree, "MULTIPLY", (bx + 100, by - 560), gin.outputs["Channel Length Y"], 0.5)
    corner_x = _math(tree, "MULTIPLY", (bx + 300, by - 520), half_x.outputs[0], -1.0)

    # cascade at the tall corner (side 3 -> side 0): fall from 3*drop to 0
    casc = safe_node(tree, "GeometryNodeSwitch", (bx + 200, by - 400))
    casc.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Cascade"], casc.inputs["Switch"])
    waterfall = safe_node(tree, "GeometryNodeMeshCube", (bx + 100, by - 400))
    wf_size = _combine(tree, (bx - 100, by - 460), gin.outputs["Cascade Width"], 0.12, fall_h.outputs[0])
    link_sockets(tree, wf_size.outputs["Vector"], waterfall.inputs["Size"])
    wf_pos = _position_piece(tree, (bx + 300, by - 400), waterfall.outputs["Mesh"],
                             x=corner_x.outputs[0], y=half_y.outputs[0], z=fall_h.outputs[0])
    link_sockets(tree, wf_pos, casc.inputs["True"])
    pieces.append(casc.outputs["Output"])

    # tribar arch: impossible triangle leaning on the cascade corner
    tribar = safe_node(tree, "GeometryNodeSwitch", (bx + 200, by - 700))
    tribar.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Tribar Arch"], tribar.inputs["Switch"])
    t_base = safe_node(tree, "GeometryNodeMeshCube", (bx + 100, by - 700))
    t_base_size = _combine(tree, (bx - 100, by - 740), gin.outputs["Cascade Width"], 0.15, 0.15)
    link_sockets(tree, t_base_size.outputs["Vector"], t_base.inputs["Size"])
    t_base_z = _math(tree, "MULTIPLY", (bx + 100, by - 780), fall_h.outputs[0], 0.5)
    t_base_out = _position_piece(tree, (bx + 300, by - 700), t_base.outputs["Mesh"],
                                 x=corner_x.outputs[0], y=half_y.outputs[0], z=t_base_z.outputs[0])
    t_slant = safe_node(tree, "GeometryNodeMeshCube", (bx + 100, by - 840))
    t_slant_size = _combine(tree, (bx - 100, by - 880), 0.15, 0.15, fall_h.outputs[0])
    link_sockets(tree, t_slant_size.outputs["Vector"], t_slant.inputs["Size"])
    t_tilt = safe_node(tree, "GeometryNodeTransform", (bx + 300, by - 840))
    link_sockets(tree, t_slant.outputs["Mesh"], t_tilt.inputs["Geometry"])
    t_tilt.inputs["Rotation"].default_value[0] = 0.6
    t_slant_out = _position_piece(tree, (bx + 500, by - 840), t_tilt.outputs["Geometry"],
                                  x=corner_x.outputs[0], y=half_y.outputs[0], z=t_base_z.outputs[0])
    t_cap = safe_node(tree, "GeometryNodeMeshCube", (bx + 100, by - 940))
    t_cap_size = _combine(tree, (bx - 100, by - 980), gin.outputs["Cascade Width"], 0.15, 0.15)
    link_sockets(tree, t_cap_size.outputs["Vector"], t_cap.inputs["Size"])
    t_cap_z = _math(tree, "ADD", (bx + 100, by - 1020), t_base_z.outputs[0], fall_h.outputs[0])
    t_cap_out = _position_piece(tree, (bx + 300, by - 940), t_cap.outputs["Mesh"],
                                x=corner_x.outputs[0], y=half_y.outputs[0], z=t_cap_z.outputs[0])
    tribar_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 500, by - 940))
    link_sockets(tree, t_base_out, tribar_join.inputs["Geometry"])
    link_sockets(tree, t_slant_out, tribar_join.inputs["Geometry"])
    link_sockets(tree, t_cap_out, tribar_join.inputs["Geometry"])
    link_sockets(tree, tribar_join.outputs["Geometry"], tribar.inputs["True"])
    pieces.append(tribar.outputs["Output"])

    # splash ring at the cascade base
    splash = safe_node(tree, "GeometryNodeSwitch", (bx + 200, by - 600))
    splash.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Splash Ring"], splash.inputs["Switch"])
    ring = safe_node(tree, "GeometryNodeMeshCircle", (bx + 100, by - 600))
    ring.inputs["Vertices"].default_value = 24
    ring.inputs["Radius"].default_value = 0.5
    ring.fill_type = "NONE"
    extrude = safe_node(tree, "GeometryNodeExtrudeMesh", (bx + 300, by - 600))
    link_sockets(tree, ring.outputs["Mesh"], extrude.inputs["Mesh"])
    extrude.mode = "EDGES"
    extrude.inputs["Offset Scale"].default_value = 0.08
    sr = _math(tree, "MULTIPLY", (bx + 300, by - 640), gin.outputs["Cascade Width"], 0.4)
    ring_scale = _combine(tree, (bx + 200, by - 680), sr.outputs[0], sr.outputs[0], 1.0)
    ring_tx = safe_node(tree, "GeometryNodeTransform", (bx + 500, by - 600))
    link_sockets(tree, extrude.outputs["Mesh"], ring_tx.inputs["Geometry"])
    link_sockets(tree, ring_scale.outputs["Vector"], ring_tx.inputs["Scale"])
    ring_pos = _position_piece(tree, (bx + 700, by - 600), ring_tx.outputs["Geometry"],
                               x=corner_x.outputs[0], y=half_y.outputs[0], z=0.3)
    link_sockets(tree, ring_pos, splash.inputs["True"])
    pieces.append(splash.outputs["Output"])

    # pillars under the four corners
    pillar = safe_node(tree, "GeometryNodeSwitch", (bx + 200, by - 800))
    pillar.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Pillars"], pillar.inputs["Switch"])
    post = safe_node(tree, "GeometryNodeMeshCylinder", (bx + 100, by - 800))
    post.inputs["Radius"].default_value = 0.12
    post.inputs["Vertices"].default_value = 10
    post_h = _math(tree, "ADD", (bx + 100, by - 840), gin.outputs["Channel Depth"],
                   _math(tree, "MULTIPLY", (bx + 200, by - 840), gin.outputs["Side Drop"], 3.0).outputs[0])
    post_h = _math(tree, "ADD", (bx + 100, by - 880), post_h.outputs[0], 0.4)
    link_sockets(tree, post_h.outputs[0], post.inputs["Depth"])
    # four posts via a 2x2 grid
    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx + 100, by - 920))
    grid.inputs["Vertices X"].default_value = 2
    grid.inputs["Vertices Y"].default_value = 2
    half_x = _math(tree, "MULTIPLY", (bx + 300, by - 920), gin.outputs["Channel Length X"], 0.5)
    half_y = _math(tree, "MULTIPLY", (bx + 300, by - 960), gin.outputs["Channel Length Y"], 0.5)
    link_sockets(tree, half_x.outputs[0], grid.inputs["Size X"])
    link_sockets(tree, half_y.outputs[0], grid.inputs["Size Y"])
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 300, by - 840))
    link_sockets(tree, grid.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, post.outputs["Mesh"], inst.inputs["Instance"])
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 500, by - 840))
    link_sockets(tree, inst.outputs["Instances"], realize.inputs["Geometry"])
    post_z = _math(tree, "MULTIPLY", (bx + 500, by - 880), post_h.outputs[0], 0.5)
    posts_placed = _position_piece(tree, (bx + 700, by - 840), realize.outputs["Geometry"],
                                   x=0.0, y=0.0, z=post_z.outputs[0])
    link_sockets(tree, posts_placed, pillar.inputs["True"])
    pieces.append(pillar.outputs["Output"])

    join2 = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 900, by - 400))
    for p in pieces:
        link_sockets(tree, p, join2.inputs["Geometry"])

    wobbled = _add_wobble(tree, join2.outputs["Geometry"],
                          gin.outputs["Wobble"], gin.outputs["Seed"], (bx + 1300, by - 400))

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 2000, by - 400))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, wobbled, shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(shade, "geometry")

    return label_tree(tree, "MEL_escher_waterfall", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Channel Sides", "nodes": ("wall", "floor", "water"), "role": "geometry"},
        {"title": "Cascade", "nodes": ("waterfall", "splash", "ring"), "role": "geometry"},
        {"title": "Pillars", "nodes": ("grid", "instance", "post"), "role": "instance"},
        {"title": "Output", "nodes": ("shade", "Group Output"), "role": "output"},
    ])


# -- Registry --------------------------------------------------------------
from .core import register_builder

register_builder(
    "MEL_escher_waterfall",
    build_escher_waterfall,
    "Escher Waterfall",
    "Impossible perpetually-descending water channel loop with cascade, "
    "splash ring, pillars, and optional tribar arch.",
    "castle",
)
