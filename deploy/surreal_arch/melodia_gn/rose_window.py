"""Melodia Studio - Rose Window GN group builders.

Small circular tracery rose window with radial segments, gold metal frame,
and emissive stained-glass panels. Designed for dreamy Gothic / stylized
architecture (DREAMY_ARCH_PLAN_2026-09-09, Stage 2).

Builder:
  MEL_rose_window_small — radial tracery rose window (default 1.2 m diameter)
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree,
    add_float_param, add_int_param, add_bool_param,
    make_group_input, register_builder,
)


def _ensure_group_node(tree, group_name, builder, loc):
    """Ensure a helper node group exists and return a Group node referencing it."""
    if group_name not in bpy.data.node_groups:
        builder(group_name)
    node = safe_node(tree, "GeometryNodeGroup", loc)
    if node:
        node.node_tree = bpy.data.node_groups.get(group_name)
    return node


def build_rose_window_small(group_name="MEL_rose_window_small"):
    """Small radial tracery rose window.

    Generates a circular rose window with:
      - Outer gold metal frame ring (full-diameter annulus)
      - Radial tracery bars (spokes) dividing the circle into segments
      - Glass panels between bars with emissive stained-glass shader

    Parameters:
      window_diameter  — overall window size (default 1.2 m)
      segment_count    — number of radial segments / spokes (default 12)
      frame_thickness  — gold frame bar width (default 0.15 m)
      gold_frame       — toggle gold metal frame (default True)
      glass_emission   — emission strength for stained-glass panels (default 2.0)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "window_diameter", 1.2, 0.3, 6.0)
    add_int_param(tree, "segment_count", 12, 3, 32)
    add_float_param(tree, "frame_thickness", 0.15, 0.02, 0.5)
    add_bool_param(tree, "gold_frame", True)
    add_float_param(tree, "glass_emission", 2.0, 0.0, 10.0)

    # ── Derived radius math ─────────────────────────────────────────────
    # Outer radius = diameter / 2
    radius = safe_node(tree, "ShaderNodeMath", (bx - 900, by + 200))
    radius.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["window_diameter"], radius.inputs[0])
    radius.inputs[1].default_value = 0.5
    color_node(radius, "math")
    radius.label = "outer_radius"

    # Half frame thickness (for spoke cylinder radius)
    half_thick = safe_node(tree, "ShaderNodeMath", (bx - 900, by + 0))
    half_thick.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["frame_thickness"], half_thick.inputs[0])
    half_thick.inputs[1].default_value = 0.5
    color_node(half_thick, "math")
    half_thick.label = "half_thickness"

    # Inner radius for glass area = outer radius - frame thickness
    inner_r = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 0))
    inner_r.operation = "SUBTRACT"
    link_sockets(tree, radius.outputs[0], inner_r.inputs[0])
    link_sockets(tree, gin.outputs["frame_thickness"], inner_r.inputs[1])
    color_node(inner_r, "math")
    inner_r.label = "inner_radius"

    # Mid radius for spoke placement
    mid_r = safe_node(tree, "ShaderNodeMath", (bx - 700, by - 200))
    mid_r.operation = "ADD"
    link_sockets(tree, radius.outputs[0], mid_r.inputs[0])
    link_sockets(tree, inner_r.outputs[0], mid_r.inputs[1])
    half_op = safe_node(tree, "ShaderNodeMath", (bx - 550, by - 200))
    half_op.operation = "MULTIPLY"
    half_op.inputs[1].default_value = 0.5
    link_sockets(tree, mid_r.outputs[0], half_op.inputs[0])
    color_node(half_op, "math")
    half_op.label = "spoke_radius"

    # ── OUTER FRAME RING ────────────────────────────────────────────────
    # Outer ring: curve circle at full radius, swept with frame_thickness profile
    outer_circle = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 600, by + 300))
    link_sockets(tree, radius.outputs[0], outer_circle.inputs["Radius"])
    try:
        outer_circle.inputs["Resolution"].default_value = 64
    except Exception:
        pass
    color_node(outer_circle, "tracery")
    outer_circle.label = "outer_ring_curve"

    outer_transform = safe_node(tree, "GeometryNodeTransform", (bx - 400, by + 300))
    link_sockets(tree, outer_circle.outputs["Curve"], outer_transform.inputs["Geometry"])
    try:
        outer_transform.inputs["Rotation"].default_value = (math.radians(90), 0, 0)
    except Exception:
        pass
    color_node(outer_transform, "geometry")

    # Inner ring (subtracted from outer ring to create the annulus frame)
    inner_circle = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 600, by + 180))
    link_sockets(tree, inner_r.outputs[0], inner_circle.inputs["Radius"])
    try:
        inner_circle.inputs["Resolution"].default_value = 64
    except Exception:
        pass
    color_node(inner_circle, "tracery")

    inner_transform = safe_node(tree, "GeometryNodeTransform", (bx - 400, by + 180))
    link_sockets(tree, inner_circle.outputs["Curve"], inner_transform.inputs["Geometry"])
    try:
        inner_transform.inputs["Rotation"].default_value = (math.radians(90), 0, 0)
    except Exception:
        pass
    color_node(inner_transform, "geometry")

    # Sweep both rings with same profile
    frame_profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 600, by + 100))
    link_sockets(tree, gin.outputs["frame_thickness"], frame_profile.inputs["Radius"])
    try:
        frame_profile.inputs["Resolution"].default_value = 16
    except Exception:
        pass
    color_node(frame_profile, "tracery")

    profile_xform = safe_node(tree, "GeometryNodeTransform", (bx - 400, by + 100))
    link_sockets(tree, frame_profile.outputs["Curve"], profile_xform.inputs["Geometry"])
    try:
        profile_xform.inputs["Rotation"].default_value = (math.radians(90), 0, 0)
    except Exception:
        pass
    color_node(profile_xform, "geometry")

    outer_ring = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 200, by + 300))
    link_sockets(tree, outer_transform.outputs["Geometry"], outer_ring.inputs["Curve"])
    link_sockets(tree, profile_xform.outputs["Geometry"], outer_ring.inputs["Profile Curve"])
    color_node(outer_ring, "geometry")

    inner_ring = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 200, by + 180))
    link_sockets(tree, inner_transform.outputs["Geometry"], inner_ring.inputs["Curve"])
    link_sockets(tree, profile_xform.outputs["Geometry"], inner_ring.inputs["Profile Curve"])
    color_node(inner_ring, "geometry")

    # Boolean subtract inner ring from outer ring to create hollow annulus frame
    frame_bool = safe_node(tree, "GeometryNodeMeshBoolean", (bx, by + 300))
    try:
        frame_bool.operation = "DIFFERENCE"
    except Exception:
        pass
    try:
        frame_bool.solver = "EXACT"
    except Exception:
        pass
    link_sockets(tree, outer_ring.outputs["Mesh"], frame_bool.inputs["Mesh 1"])
    link_sockets(tree, inner_ring.outputs["Mesh"], frame_bool.inputs["Mesh 2"])
    color_node(frame_bool, "math")

    # Store is_frame=1 attribute on frame geometry
    store_frame_attr = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 200, by + 300))
    link_sockets(tree, frame_bool.outputs["Mesh"], store_frame_attr.inputs["Geometry"])
    store_frame_attr.data_type = "INT"
    try:
        store_frame_attr.inputs["Name"].default_value = "is_frame"
        store_frame_attr.inputs["Value"].default_value = 1
    except Exception:
        pass
    color_node(store_frame_attr, "attribute")

    # ── RADIAL TRACERY BARS (SPOKES) ────────────────────────────────────
    # Single spoke: cylinder from center outward along +X
    spoke_cyl = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 600, by - 100))
    link_sockets(tree, half_thick.outputs[0], spoke_cyl.inputs["Radius"])
    link_sockets(tree, inner_r.outputs[0], spoke_cyl.inputs["Depth"])
    try:
        spoke_cyl.inputs["Vertices"].default_value = 8
    except Exception:
        pass
    spoke_cyl.fill_type = "NGON"
    color_node(spoke_cyl, "tracery")

    # Position spoke so it starts at center. Cylinder is centered at origin,
    # so shift it half its length in +X so base is at center.
    spoke_half_len = safe_node(tree, "ShaderNodeMath", (bx - 400, by - 100))
    spoke_half_len.operation = "MULTIPLY"
    link_sockets(tree, inner_r.outputs[0], spoke_half_len.inputs[0])
    spoke_half_len.inputs[1].default_value = 0.5

    spoke_transform = safe_node(tree, "GeometryNodeTransform", (bx - 200, by - 100))
    link_sockets(tree, spoke_cyl.outputs["Mesh"], spoke_transform.inputs["Geometry"])
    link_float_to_vector(tree, spoke_half_len.outputs[0], spoke_transform, "Translation",
                         component=0, defaults=(0.0, 0.0, 0.0))
    color_node(spoke_transform, "geometry")

    # Instance spokes around a circle using MEL_circular_array
    circular_array = _ensure_group_node(tree, "MEL_circular_array", None, (bx, by - 300))
    if circular_array is None:
        # Fallback: manual instance on points
        circle_pts = safe_node(tree, "GeometryNodeMeshCircle", (bx - 100, by - 300))
        link_sockets(tree, inner_r.outputs[0], circle_pts.inputs["Radius"])
        link_sockets(tree, gin.outputs["segment_count"], circle_pts.inputs["Vertices"])
        circle_pts.fill_type = "NONE"
        circle_to_curve = safe_node(tree, "GeometryNodeMeshToCurve", (bx + 100, by - 300))
        link_sockets(tree, circle_pts.outputs["Mesh"], circle_to_curve.inputs["Mesh"])
        circle_points = safe_node(tree, "GeometryNodeCurveToPoints", (bx + 200, by - 300))
        try:
            circle_points.mode = "EVALUATED"
        except Exception:
            pass
        link_sockets(tree, circle_to_curve.outputs["Curve"], circle_points.inputs["Curve"])

        spoke_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 400, by - 300))
        link_sockets(tree, circle_points.outputs["Points"], spoke_inst.inputs["Points"])
        link_sockets(tree, spoke_transform.outputs["Geometry"], spoke_inst.inputs["Instance"])
        color_node(spoke_inst, "instance")
        realize_spokes = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 600, by - 300))
        link_sockets(tree, spoke_inst.outputs["Instances"], realize_spokes.inputs["Geometry"])
        color_node(realize_spokes, "instance")
        spokes_geo = realize_spokes.outputs["Geometry"]
    else:
        if circular_array.inputs.get("Geometry"):
            link_sockets(tree, spoke_transform.outputs["Geometry"], circular_array.inputs["Geometry"])
        if circular_array.inputs.get("Count"):
            link_sockets(tree, gin.outputs["segment_count"], circular_array.inputs["Count"])
        if circular_array.inputs.get("Radius"):
            link_sockets(tree, inner_r.outputs[0], circular_array.inputs["Radius"])
        color_node(circular_array, "instance")
        spokes_geo = circular_array.outputs.get("Geometry")

    # Store is_frame=0 on spokes
    store_spoke_attr = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 300, by - 100))
    if spokes_geo:
        link_sockets(tree, spokes_geo, store_spoke_attr.inputs["Geometry"])
    store_spoke_attr.data_type = "INT"
    try:
        store_spoke_attr.inputs["Name"].default_value = "is_frame"
        store_spoke_attr.inputs["Value"].default_value = 0
    except Exception:
        pass
    color_node(store_spoke_attr, "attribute")

    # ── JOIN ALL PARTS ──────────────────────────────────────────────────
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 400, by + 100))
    link_sockets(tree, store_frame_attr.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, store_spoke_attr.outputs["Geometry"], join.inputs["Geometry"])
    color_node(join, "geometry")

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 600, by + 100))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])
    color_node(shade, "geometry")

    return label_tree(tree, "MEL_rose_window_small", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Radius Math", "nodes": ("radius", "inner_r", "half_thick"), "role": "math"},
        {"title": "Frame Ring", "nodes": ("Ring", "Circle", "Sweep"), "role": "geometry"},
        {"title": "Radial Bars", "nodes": ("spoke", "instance", "realize"), "role": "instance"},
        {"title": "Output", "nodes": ("join", "shade", "Group Output"), "role": "output"},
    ])


# Register the builder into the Melodia GN system
register_builder(
    "MEL_rose_window_small",
    build_rose_window_small,
    "Rose Window Small",
    "Small radial tracery rose window with gold frame and emissive glass panels",
    "ornament",
)
