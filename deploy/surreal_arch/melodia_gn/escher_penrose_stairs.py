"""Escher Penrose Stairs -- HERO GN builder.

An impossible infinite staircase (Escher's "Ascending and Descending" /
Penrose steps): N stair runs arranged in a closed loop polygon. Each run
ascends by (Step Rise x Steps per Run); around the loop the runs step UP
(run i sits at base z = i x rise), yet the loop visually closes -- the
impossible read. An optional second tier creates the endless effect.

Every parameter is an editable named input on the node group.
"""

from __future__ import annotations

import math

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


def _gate(tree, loc, geo_sock, count_sock, index):
    """Return geometry: geo if count > index else empty."""
    show = safe_node(tree, "GeometryNodeSwitch", loc)
    show.input_type = "GEOMETRY"
    link_sockets(tree, geo_sock, show.inputs["True"])
    gate = safe_node(tree, "FunctionNodeCompare", (loc[0] - 200, loc[1]))
    gate.data_type = "INT"
    gate.operation = "GREATER_THAN"
    link_sockets(tree, count_sock, gate.inputs["A"])
    gate.inputs["B"].default_value = index
    link_sockets(tree, gate.outputs["Result"], show.inputs["Switch"])
    return show.outputs["Output"]


def _build_run(tree, gin, loc, i, runs_sock, base_z_sock, radius_sock, total_rise_sock):
    """One ascending stair run placed on the loop polygon edge i."""
    bx, by = loc
    angle_2pi = _math(tree, "MULTIPLY", (bx - 1200, by), 6.2831853, i * 1.0)
    angle = _math(tree, "DIVIDE", (bx - 1000, by), angle_2pi.outputs[0], runs_sock)

    cos_a = _math(tree, "COSINE", (bx - 800, by + 60), angle.outputs[0], None)
    sin_a = _math(tree, "SINE", (bx - 800, by - 40), angle.outputs[0], None)

    # run center position on the inscribed polygon
    px = _math(tree, "MULTIPLY", (bx - 600, by + 60), cos_a.outputs[0], radius_sock)
    py = _math(tree, "MULTIPLY", (bx - 600, by - 40), sin_a.outputs[0], radius_sock)
    run_z = _math(tree, "MULTIPLY", (bx - 600, by - 140), base_z_sock, 1.0)

    # Build actual individual treads. The previous graph emitted one sloped
    # slab, so Steps per Run changed only metadata/math and never produced
    # stair geometry.
    step_count_minus_one = _math(
        tree, "SUBTRACT", (bx - 1200, by - 300), gin.outputs["Steps per Run"], 1.0
    )
    step_count_safe = _math(
        tree, "MAXIMUM", (bx - 1000, by - 300), step_count_minus_one.outputs[0], 1.0
    )
    step_pitch = _math(
        tree, "DIVIDE", (bx - 800, by - 300), gin.outputs["Run Length"], step_count_safe.outputs[0]
    )
    step_depth_limit = _math(
        tree, "MULTIPLY", (bx - 600, by - 300), step_pitch.outputs[0], 0.95
    )
    step_depth = _math(
        tree, "MINIMUM", (bx - 400, by - 300), gin.outputs["Step Depth"], step_depth_limit.outputs[0]
    )
    step_height = _math(
        tree, "MAXIMUM", (bx - 200, by - 300), gin.outputs["Step Rise"], 0.04
    )

    step_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 1000, by - 520))
    step_line.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Steps per Run"], step_line.inputs["Count"])
    step_start_x = _math(
        tree, "ADD", (bx - 1200, by - 600),
        _math(tree, "MULTIPLY", (bx - 1400, by - 600), gin.outputs["Run Length"], -0.5).outputs[0],
        _math(tree, "MULTIPLY", (bx - 1400, by - 660), step_pitch.outputs[0], 0.5).outputs[0],
    )
    step_start_z = _math(
        tree, "MULTIPLY", (bx - 1000, by - 660), step_height.outputs[0], 0.5
    )
    step_start = _combine(tree, (bx - 800, by - 620), step_start_x.outputs[0], 0.0, step_start_z.outputs[0])
    step_offset = _combine(tree, (bx - 800, by - 760), step_pitch.outputs[0], 0.0, gin.outputs["Step Rise"])
    link_sockets(tree, step_start.outputs["Vector"], step_line.inputs["Start Location"])
    link_sockets(tree, step_offset.outputs["Vector"], step_line.inputs["Offset"])

    step = safe_node(tree, "GeometryNodeMeshCube", (bx - 600, by - 520))
    step_size = _combine(tree, (bx - 800, by - 420), step_depth.outputs[0], gin.outputs["Run Width"], step_height.outputs[0])
    link_sockets(tree, step_size.outputs["Vector"], step.inputs["Size"])
    step_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 400, by - 520))
    link_sockets(tree, step_line.outputs["Mesh"], step_inst.inputs["Points"])
    link_sockets(tree, step.outputs["Mesh"], step_inst.inputs["Instance"])
    step_real = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 200, by - 520))
    link_sockets(tree, step_inst.outputs["Instances"], step_real.inputs["Geometry"])

    # Top landing at the end of the run.
    landing = safe_node(tree, "GeometryNodeMeshCube", (bx - 1000, by - 500))
    land_size = _combine(tree, (bx - 1200, by - 560),
                         step_pitch.outputs[0], gin.outputs["Run Width"], 0.1)
    link_sockets(tree, land_size.outputs["Vector"], landing.inputs["Size"])
    land_x = _math(tree, "MULTIPLY", (bx - 1000, by - 540), gin.outputs["Run Length"], 0.5)
    land_z = _math(tree, "ADD", (bx - 900, by - 540), total_rise_sock, 0.05)
    land_placed = _position_piece(tree, (bx - 600, by - 500), landing.outputs["Mesh"],
                                  x=land_x.outputs[0], y=0.0, z=land_z.outputs[0])

    # railing on the outer edge
    rail = safe_node(tree, "GeometryNodeSwitch", (bx - 600, by - 640))
    rail.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Railings"], rail.inputs["Switch"])
    rail_box = safe_node(tree, "GeometryNodeMeshCube", (bx - 800, by - 640))
    rail_size = _combine(tree, (bx - 1000, by - 700),
                         gin.outputs["Run Length"], 0.05, 0.6)
    link_sockets(tree, rail_size.outputs["Vector"], rail_box.inputs["Size"])
    rail_edge = _math(tree, "MULTIPLY", (bx - 1000, by - 740), gin.outputs["Run Width"], 0.5)
    rail_z = _math(tree, "MULTIPLY", (bx - 1000, by - 780), total_rise_sock, 0.6)
    rail_placed = _position_piece(tree, (bx - 600, by - 640), rail_box.outputs["Mesh"],
                                  x=0.0, y=rail_edge.outputs[0], z=rail_z.outputs[0])
    link_sockets(tree, rail_placed, rail.inputs["True"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 400, by - 300))
    link_sockets(tree, step_real.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, land_placed, join.inputs["Geometry"])
    link_sockets(tree, rail.outputs["Output"], join.inputs["Geometry"])

    # Rotate run to the polygon tangent and translate out to the edge midpoint.
    rot = safe_node(tree, "GeometryNodeTransform", (bx - 200, by - 300))
    link_sockets(tree, join.outputs["Geometry"], rot.inputs["Geometry"])
    tangent_angle = _math(tree, "ADD", (bx - 400, by - 420), angle.outputs[0], math.pi * 0.5)
    link_float_to_vector(tree, tangent_angle.outputs[0], rot, "Rotation",
                         component=2, defaults=(0.0, 0.0, 0.0))
    trans = _combine(tree, (bx - 200, by - 380), px.outputs[0], py.outputs[0], run_z.outputs[0])
    set_final = safe_node(tree, "GeometryNodeTransform", (bx, by - 300))
    link_sockets(tree, rot.outputs["Geometry"], set_final.inputs["Geometry"])
    link_sockets(tree, trans.outputs["Vector"], set_final.inputs["Translation"])
    return set_final.outputs["Geometry"]


def build_escher_penrose_stairs(group_name="MEL_escher_penrose_stairs"):
    """Penrose stairs -- impossible ascending loop staircase.

    Modes via params: Runs (3-8), steps/rise/depth, railings, second tier.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Runs", 4, 3, 8)
    add_float_param(tree, "Run Length", 4.0, 2.0, 10.0)
    add_float_param(tree, "Run Width", 1.6, 0.8, 3.0)
    add_int_param(tree, "Steps per Run", 5, 2, 12)
    add_float_param(tree, "Step Rise", 0.22, 0.1, 0.5)
    add_float_param(tree, "Step Depth", 0.45, 0.2, 1.0)
    add_bool_param(tree, "Railings", True)
    add_bool_param(tree, "Second Loop", True)
    add_float_param(tree, "Loop Offset", 0.9, 0.0, 2.0)
    add_float_param(tree, "Wobble", 0.05, 0.0, 0.3)
    add_int_param(tree, "Seed", 7, 0, 9999)

    total_rise = _math(tree, "MULTIPLY", (bx - 1400, by + 200),
                       gin.outputs["Steps per Run"], gin.outputs["Step Rise"])
    # radius of inscribed polygon: RunLength / (2 * tan(pi / Runs))
    pi_div = _math(tree, "DIVIDE", (bx - 1400, by + 120), 3.14159, gin.outputs["Runs"])
    tan_pi = _math(tree, "TANGENT", (bx - 1200, by + 120), pi_div.outputs[0], None)
    denom = _math(tree, "MULTIPLY", (bx - 1400, by + 40), tan_pi.outputs[0], 2.0)
    radius = _math(tree, "DIVIDE", (bx - 1200, by + 40), gin.outputs["Run Length"], denom.outputs[0])

    parts = []
    for i in range(8):
        base_z = _math(tree, "MULTIPLY", (bx - 1200, by - 120 + i * -200),
                       gin.outputs["Step Rise"],
                       _math(tree, "MULTIPLY", (bx - 1300, by - 120 + i * -200),
                             gin.outputs["Steps per Run"], i * 1.0).outputs[0])
        run_geo = _build_run(tree, gin, (bx - 800, by - 120 + i * -200),
                             i, gin.outputs["Runs"], base_z.outputs[0],
                             radius.outputs[0], total_rise.outputs[0])
        parts.append(_gate(tree, (bx - 200, by - 120 + i * -200), run_geo,
                           gin.outputs["Runs"], i))

    # second ascending tier for the endless read
    loop2 = safe_node(tree, "GeometryNodeSwitch", (bx + 200, by - 200))
    loop2.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Second Loop"], loop2.inputs["Switch"])
    parts2 = []
    for i in range(8):
        base_z2 = _math(tree, "MULTIPLY", (bx - 1000, by - 1900 + i * -200),
                        gin.outputs["Step Rise"],
                        _math(tree, "MULTIPLY", (bx - 1100, by - 1900 + i * -200),
                              gin.outputs["Steps per Run"], i * 1.0).outputs[0])
        base_z2 = _math(tree, "ADD", (bx - 900, by - 1900 + i * -200),
                        base_z2.outputs[0], gin.outputs["Loop Offset"])
        run_geo2 = _build_run(tree, gin, (bx - 600, by - 1900 + i * -200),
                              i, gin.outputs["Runs"], base_z2.outputs[0],
                              radius.outputs[0], total_rise.outputs[0])
        parts2.append(_gate(tree, (bx - 200, by - 1900 + i * -200), run_geo2,
                            gin.outputs["Runs"], i))
    join2 = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 400, by - 1900))
    for p in parts2:
        link_sockets(tree, p, join2.inputs["Geometry"])
    link_sockets(tree, join2.outputs["Geometry"], loop2.inputs["True"])

    join1 = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 600, by - 200))
    for p in parts:
        link_sockets(tree, p, join1.inputs["Geometry"])
    link_sockets(tree, loop2.outputs["Output"], join1.inputs["Geometry"])

    wobbled = _add_wobble(tree, join1.outputs["Geometry"],
                          gin.outputs["Wobble"], gin.outputs["Seed"], (bx + 1200, by - 200))

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 1900, by - 200))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, wobbled, shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(shade, "geometry")

    return label_tree(tree, "MEL_escher_penrose_stairs", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Loop Math", "nodes": ("cosine", "sine", "tangent"), "role": "math"},
        {"title": "Stair Runs", "nodes": ("step", "landing", "rail"), "role": "geometry"},
        {"title": "Second Loop", "nodes": ("loop",), "role": "instance"},
        {"title": "Output", "nodes": ("shade", "Group Output"), "role": "output"},
    ])


# -- Registry --------------------------------------------------------------
from .core import register_builder

register_builder(
    "MEL_escher_penrose_stairs",
    build_escher_penrose_stairs,
    "Escher Penrose Stairs",
    "Impossible ascending staircase loop (Ascending and Descending): N stair "
    "runs climbing around a closed polygon, with an optional endless second tier.",
    "castle",
)
