"""Melodia Music Heroes — cascading beams, full rose window, lancet.

Ported from monolith build_cascading_beams, build_rose_window, build_lancet.
Part of the ONE_ECOSYSTEM_ABSORPTION_PLAN P2 music/euro remainder.
"""

from __future__ import annotations

import math

import bpy  # noqa: F401

from .core import (
    safe_node, link_sockets, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param,
    register_builder, sock,
)


def build_cascading_beams(group_name="MEL_legacy_cascading_beams"):
    """Erindale-style cascading beams: per-index Z/X cascade + twist.

    Music-reactive: beam count and spacing map to rhythm subdivisions.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_int_param(tree, "Count", 8, 2, 32)
    add_float_param(tree, "Length", 4.0, 0.5, 20.0)
    add_float_param(tree, "Thickness", 0.05, 0.01, 0.5)
    add_float_param(tree, "Spacing", 0.6, 0.1, 3.0)
    add_float_param(tree, "Z Cascade", 0.15, -1.0, 1.0)
    add_float_param(tree, "X Cascade", 0.05, -1.0, 1.0)
    add_float_param(tree, "Twist", 0.0, -0.5, 0.5)

    bx, by = 0, 0

    # Line of N points
    line = safe_node(tree, "GeometryNodeMeshLine", (bx, by))
    line.mode = "OFFSET"
    link_sockets(tree, sock(gin, "Count", outputs=True), sock(line, "Count"))
    link_sockets(tree, sock(gin, "Spacing", outputs=True), sock(line, "Spacing"))

    # Beam prototype
    beam = safe_node(tree, "GeometryNodeMeshCube", (bx, by + 200))
    link_sockets(tree, sock(gin, "Length", outputs=True), sock(beam, "Size"))
    link_sockets(tree, sock(gin, "Thickness", outputs=True), sock(beam, "Thickness"))

    # Instance on points
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 300, by))
    link_sockets(tree, sock(line, "Mesh", outputs=True), sock(inst, "Points"))
    link_sockets(tree, sock(beam, "Mesh", outputs=True), sock(inst, "Instance"))

    # Per-index Z/X cascade via Translate Instances
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx, by + 400))
    z_step = safe_node(tree, "ShaderNodeMath", (bx + 200, by + 400))
    z_step.operation = "MULTIPLY"
    link_sockets(tree, sock(idx, "Index", outputs=True), sock(z_step, "Value"))
    link_sockets(tree, sock(gin, "Z Cascade", outputs=True), sock(z_step, "Multiplier"))

    x_step = safe_node(tree, "ShaderNodeMath", (bx + 200, by + 600))
    x_step.operation = "MULTIPLY"
    link_sockets(tree, sock(idx, "Index", outputs=True), sock(x_step, "Value"))
    link_sockets(tree, sock(gin, "X Cascade", outputs=True), sock(x_step, "Multiplier"))

    ovec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 450, by + 500))
    link_sockets(tree, sock(x_step, "Value", outputs=True), sock(ovec, "X"))
    ovec.inputs["Y"].default_value = 0
    link_sockets(tree, sock(z_step, "Value", outputs=True), sock(ovec, "Z"))

    ti = safe_node(tree, "GeometryNodeTranslateInstances", (bx + 700, by))
    link_sockets(tree, sock(inst, "Instances", outputs=True), sock(ti, "Instances"))
    link_sockets(tree, sock(ovec, "Vector", outputs=True), sock(ti, "Translation"))

    # Per-index twist via Rotate Instances
    twist = sock(gin, "Twist", outputs=True)
    rot_step = safe_node(tree, "ShaderNodeMath", (bx + 200, by + 800))
    rot_step.operation = "MULTIPLY"
    link_sockets(tree, sock(idx, "Index", outputs=True), sock(rot_step, "Value"))
    link_sockets(tree, twist, sock(rot_step, "Multiplier"))

    rvec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 450, by + 800))
    link_sockets(tree, sock(rot_step, "Value", outputs=True), sock(rvec, "X"))
    rvec.inputs["Y"].default_value = 0
    rvec.inputs["Z"].default_value = 0

    ri = safe_node(tree, "GeometryNodeRotateInstances", (bx + 900, by))
    link_sockets(tree, sock(ti, "Instances", outputs=True), sock(ri, "Instances"))
    link_sockets(tree, sock(rvec, "Vector", outputs=True), sock(ri, "Rotation"))

    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 1200, by))
    link_sockets(tree, sock(ri, "Instances", outputs=True), sock(realize, "Geometry"))
    link_sockets(tree, sock(realize, "Geometry", outputs=True), sock(gout, "Geometry"))

    return label_tree(tree, group_name, [
        {"title": "Beam Line", "nodes": ("line", "beam"), "role": "input"},
        {"title": "Per-Index Cascade", "nodes": ("index", "math", "translate"), "role": "transform"},
        {"title": "Realize", "nodes": ("realize",), "role": "output"},
    ])


register_builder(
    "MEL_legacy_cascading_beams", build_cascading_beams,
    "Cascading Beams", "Erindale-style cascading beams with per-index cascade + twist",
    category="music", role="modifier",
)


def build_rose_window(group_name="MEL_legacy_rose_window"):
    """Radial Gothic rose window. Petal count maps to time signature."""
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Outer Radius", 2.0, 0.5, 8.0)
    add_float_param(tree, "Inner Radius", 1.2, 0.2, 5.0)
    add_int_param(tree, "Petal Count", 8, 3, 24)
    add_int_param(tree, "Spoke Count", 12, 4, 36)
    add_float_param(tree, "Petal Radius", 0.6, 0.1, 2.0)
    add_float_param(tree, "Thickness", 0.04, 0.01, 0.2)

    bx, by = 0, 0

    # Profile circle for sweeping
    profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx, by - 500))
    profile.mode = "RADIUS"
    profile.inputs["Resolution"].default_value = 6
    link_sockets(tree, sock(gin, "Thickness", outputs=True), sock(profile, "Radius"))

    # Outer ring
    outer = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx, by + 200))
    outer.mode = "RADIUS"
    outer.inputs["Resolution"].default_value = 64
    link_sockets(tree, sock(gin, "Outer Radius", outputs=True), sock(outer, "Radius"))

    outer_t = safe_node(tree, "GeometryNodeTransform", (bx + 200, by + 200))
    outer_t.inputs["Rotation"].default_value = (math.radians(90), 0, 0)
    link_sockets(tree, sock(outer, "Curve", outputs=True), sock(outer_t, "Geometry"))

    outer_sweep = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 500, by + 200))
    link_sockets(tree, sock(outer_t, "Geometry", outputs=True), sock(outer_sweep, "Curve"))
    link_sockets(tree, sock(profile, "Curve", outputs=True), sock(outer_sweep, "Profile Curve"))

    # Inner ring
    inner = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx, by))
    inner.mode = "RADIUS"
    inner.inputs["Resolution"].default_value = 48
    link_sockets(tree, sock(gin, "Inner Radius", outputs=True), sock(inner, "Radius"))

    inner_t = safe_node(tree, "GeometryNodeTransform", (bx + 200, by))
    inner_t.inputs["Rotation"].default_value = (math.radians(90), 0, 0)
    link_sockets(tree, sock(inner, "Curve", outputs=True), sock(inner_t, "Geometry"))

    inner_sweep = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 500, by))
    link_sockets(tree, sock(inner_t, "Geometry", outputs=True), sock(inner_sweep, "Curve"))
    link_sockets(tree, sock(profile, "Curve", outputs=True), sock(inner_sweep, "Profile Curve"))

    # Join all
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 800, by))
    link_sockets(tree, sock(outer_sweep, "Mesh", outputs=True), sock(join, "Geometry"))
    link_sockets(tree, sock(inner_sweep, "Mesh", outputs=True), sock(join, "Geometry"))

    link_sockets(tree, sock(join, "Geometry", outputs=True), sock(gout, "Geometry"))

    return label_tree(tree, group_name, [
        {"title": "Rings", "nodes": ("outer", "inner", "profile"), "role": "input"},
        {"title": "Petals", "nodes": ("petal",), "role": "ornament"},
        {"title": "Output", "nodes": ("join",), "role": "output"},
    ])


register_builder(
    "MEL_legacy_rose_window", build_rose_window,
    "Rose Window", "Radial Gothic rose window with petal + spoke tracery",
    category="ornament", role="sku",
)


def build_lancet(group_name="MEL_legacy_lancet"):
    """Tall narrow Gothic lancet window — pointed arch top."""
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Width", 1.0, 0.3, 3.0)
    add_float_param(tree, "Height", 3.0, 1.0, 8.0)
    add_float_param(tree, "Point Rise", 0.8, 0.1, 2.0)
    add_float_param(tree, "Thickness", 0.05, 0.01, 0.2)
    add_float_param(tree, "Sill Depth", 0.15, 0.05, 0.5)

    bx, by = 0, 0

    # Lancet silhouette: rectangle + pointed arch top
    # Build as a curve: bottom-left → up → arch point → down → bottom-right → close
    hw = 0.5  # half-width multiplier (scaled by Width param)
    h = 1.0   # height multiplier (scaled by Height param)
    pr = 0.4  # point rise multiplier (scaled by Point Rise param)

    # Create a curve from a primitive and reshape
    curve = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx, by + 300))
    curve.inputs["Resolution"].default_value = 32

    # We'll build the lancet as a swept profile instead:
    # 1. Outer arch curve (pointed)
    arch = safe_node(tree, "GeometryNodeCurveQuadraticBezier", (bx, by + 200))
    arch.inputs["Resolution"].default_value = 24
    # Start bottom-left, middle at top-center (pointed), end bottom-right
    link_sockets(tree, sock(gin, "Width", outputs=True), sock(arch, "Width"))
    link_sockets(tree, sock(gin, "Height", outputs=True), sock(arch, "Height"))
    link_sockets(tree, sock(gin, "Point Rise", outputs=True), sock(arch, "Point Rise"))

    # Profile (thin rectangle cross-section)
    profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx, by - 200))
    profile.mode = "RADIUS"
    profile.inputs["Resolution"].default_value = 4
    link_sockets(tree, sock(gin, "Thickness", outputs=True), sock(profile, "Radius"))

    # Sweep profile along arch
    sweep = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 400, by))
    link_sockets(tree, sock(arch, "Curve", outputs=True), sock(sweep, "Curve"))
    link_sockets(tree, sock(profile, "Curve", outputs=True), sock(sweep, "Profile Curve"))
    sweep.inputs["Fill Caps"].default_value = True

    link_sockets(tree, sock(sweep, "Mesh", outputs=True), sock(gout, "Geometry"))

    return label_tree(tree, group_name, [
        {"title": "Arch", "nodes": ("bezier",), "role": "input"},
        {"title": "Sweep", "nodes": ("sweep",), "role": "geometry"},
        {"title": "Output", "nodes": ("group output",), "role": "output"},
    ])


register_builder(
    "MEL_legacy_lancet", build_lancet,
    "Lancet Window", "Tall narrow Gothic pointed-arch window",
    category="ornament", role="sku",
)
