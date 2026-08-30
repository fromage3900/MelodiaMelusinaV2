"""Polyhedra & Platonic Solid GN group builders - Icosahedron, Dodecahedron, Octahedron, Kepler-Poinsot Star Polyhedra.

Integrates Platonic & Kepler-Poinsot polyhedral geometry into the Melodia GN system for Blender 5.1+.
"""

from __future__ import annotations

import math
import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, add_vector_param,
    make_group_input, register_builder, mesh_boolean_node, require_node, sock,
    add_music_influence_params, apply_universal_music_pass,
)


def build_polyhedra_icosahedron(group_name="MEL_polyhedra_icosahedron"):
    """Platonic Icosahedron / Geodesic Sphere GN builder - 20 triangular faces with subdivision control.

    Uses IcoSphere mesh primitive with scale, bevel, and shade smooth parameters.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Radius", 1.0, 0.1, 10.0)
    add_int_param(tree, "Subdivisions", 1, 1, 6)
    add_float_param(tree, "Wireframe Thickness", 0.03, 0.005, 0.2)
    add_bool_param(tree, "Use Wireframe", False)

    icosphere = safe_node(tree, "GeometryNodeMeshIcoSphere", (bx - 600, by + 200))
    link_sockets(tree, gin.outputs["Radius"], icosphere.inputs["Radius"])
    link_sockets(tree, gin.outputs["Subdivisions"], icosphere.inputs["Subdivisions"])

    # Wireframe mode option: Mesh to Curve -> Curve to Mesh with Profile Circle
    mesh_to_curve = safe_node(tree, "GeometryNodeMeshToCurve", (bx - 400, by - 100))
    link_sockets(tree, icosphere.outputs["Mesh"], mesh_to_curve.inputs["Mesh"])

    curve_profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 400, by - 300))
    link_sockets(tree, gin.outputs["Wireframe Thickness"], curve_profile.inputs["Radius"])
    curve_profile.inputs["Resolution"].default_value = 8

    curve_to_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 200, by - 100))
    link_sockets(tree, mesh_to_curve.outputs["Curve"], curve_to_mesh.inputs["Curve"])
    link_sockets(tree, curve_profile.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])

    # Switch logic: Wireframe vs Solid Mesh
    switch_geom = safe_node(tree, "GeometryNodeSwitch", (bx, by + 100))
    switch_geom.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Use Wireframe"], switch_geom.inputs["Switch"])
    link_sockets(tree, icosphere.outputs["Mesh"], switch_geom.inputs["False"])
    link_sockets(tree, curve_to_mesh.outputs["Mesh"], switch_geom.inputs["True"])

    smooth = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 200, by + 100))
    link_sockets(tree, switch_geom.outputs["Output"], smooth.inputs["Geometry"])

    link_sockets(tree, smooth.outputs["Geometry"], gout.inputs["Geometry"])

    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Icosahedron Primitive", "nodes": ("IcoSphere", "Mesh to Curve", "Switch"), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return tree


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


def _combine(tree, loc, x=None, y=None, z=None):
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


def _mesh_out(node):
    return sock(node, "Mesh", "Geometry", outputs=True)


def _ground_z(tree, loc, height_sock):
    """Cube primitives are origin-centered; lift by height/2 so the floor sits on Z=0."""
    half = _math(tree, "MULTIPLY", loc, height_sock, 0.5)
    return _combine(tree, (loc[0] + 180, loc[1]), 0.0, 0.0, half.outputs[0])


def _translate(tree, loc, geom, translation_sock):
    n = safe_node(tree, "GeometryNodeTransform", loc)
    link_sockets(tree, geom, n.inputs["Geometry"])
    link_sockets(tree, translation_sock, n.inputs["Translation"])
    return n.outputs["Geometry"]


def _switch_geo(tree, loc, switch_sock, if_true, if_false):
    sw = safe_node(tree, "GeometryNodeSwitch", loc)
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, switch_sock, sw.inputs.get("Switch") or sw.inputs[0])
    true_in = sw.inputs.get("True") or sw.inputs.get("TRUE") or sw.inputs.get("A")
    false_in = sw.inputs.get("False") or sw.inputs.get("FALSE") or sw.inputs.get("B")
    link_sockets(tree, if_true, true_in)
    link_sockets(tree, if_false, false_in)
    return sw.outputs.get("Output") or sw.outputs.get("Geometry") or sw.outputs[0]


def _sized_cube(tree, loc, size_x, size_y, size_z):
    cube = safe_node(tree, "GeometryNodeMeshCube", loc)
    link_float_to_vector(tree, size_x, cube, "Size", component=0, defaults=(1.0, 1.0, 1.0))
    link_float_to_vector(tree, size_y, cube, "Size", component=1, defaults=(1.0, 1.0, 1.0))
    link_float_to_vector(tree, size_z, cube, "Size", component=2, defaults=(1.0, 1.0, 1.0))
    return cube


def _clamp_min(tree, loc, value_sock, minimum=0.05):
    return _math(tree, "MAXIMUM", loc, value_sock, minimum)


def _inner_span(tree, loc, outer_sock, thick_sock, extra_cut=0.0):
    """outer - 2*thick, optionally plus extra_cut so a cutter punches through a face."""
    t2 = _math(tree, "MULTIPLY", (loc[0] - 160, loc[1]), thick_sock, 2.0)
    inner = _math(tree, "SUBTRACT", loc, outer_sock, t2.outputs[0])
    if extra_cut:
        inner = _math(tree, "ADD", (loc[0] + 160, loc[1]), inner.outputs[0], extra_cut)
        return _clamp_min(tree, (loc[0] + 320, loc[1]), inner.outputs[0])
    return _clamp_min(tree, (loc[0] + 160, loc[1]), inner.outputs[0])


def build_polyhedra_dodecahedron(group_name="MEL_polyhedra_dodecahedron"):
    """Platonic dodecahedron - dual of a regular icosahedron (12 pentagonal faces).

    IcoSphere subdivisions=1 is the icosahedron. Dual Mesh turns its 20 faces into
    20 vertices / 12 faces. Not a subdivided icosphere labeled as a dodecahedron.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Radius", 1.0, 0.1, 10.0)
    add_float_param(tree, "Bevel Thickness", 0.03, 0.005, 0.2)
    add_bool_param(tree, "Use Wireframe", False)

    icosphere = safe_node(tree, "GeometryNodeMeshIcoSphere", (bx - 800, by + 200))
    link_sockets(tree, gin.outputs["Radius"], icosphere.inputs["Radius"])
    try:
        icosphere.inputs["Subdivisions"].default_value = 1
    except Exception:
        pass

    dual = require_node(
        tree, "GeometryNodeDualMesh", (bx - 600, by + 200), "GeometryNodeMeshToDualMesh",
    )
    link_sockets(tree, _mesh_out(icosphere), sock(dual, "Mesh", "Geometry"))
    dual_mesh = sock(dual, "Dual Mesh", "Mesh", "Geometry", outputs=True)

    mesh_to_curve = safe_node(tree, "GeometryNodeMeshToCurve", (bx - 400, by - 100))
    link_sockets(tree, dual_mesh, mesh_to_curve.inputs["Mesh"])

    curve_profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 400, by - 300))
    link_sockets(tree, gin.outputs["Bevel Thickness"], curve_profile.inputs["Radius"])
    try:
        curve_profile.inputs["Resolution"].default_value = 8
    except Exception:
        pass

    curve_to_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 200, by - 100))
    link_sockets(tree, mesh_to_curve.outputs["Curve"], curve_to_mesh.inputs["Curve"])
    link_sockets(tree, curve_profile.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])

    solid = _switch_geo(
        tree, (bx, by + 100),
        gin.outputs["Use Wireframe"],
        _mesh_out(curve_to_mesh),
        dual_mesh,
    )

    smooth = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 200, by + 100))
    link_sockets(tree, solid, smooth.inputs["Geometry"])
    link_sockets(tree, smooth.outputs["Geometry"], gout.inputs["Geometry"])

    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Icosa Dual", "nodes": ("IcoSphere", "Dual Mesh"), "role": "geometry"},
        {"title": "Wireframe", "nodes": ("Mesh to Curve", "Curve to Mesh", "Switch"), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return tree


def build_greybox_room_kit(group_name="MEL_greybox_room_kit"):
    """Hollow greybox room: outer cube minus inner void (wall thickness, optional ceiling)."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Room Length", 8.0, 2.0, 30.0)
    add_float_param(tree, "Room Width", 6.0, 2.0, 30.0)
    add_float_param(tree, "Room Height", 4.0, 2.0, 15.0)
    add_float_param(tree, "Wall Thickness", 0.3, 0.1, 1.5)
    add_bool_param(tree, "Ceiling", True)
    add_music_influence_params(tree)

    length = gin.outputs["Room Length"]
    width = gin.outputs["Room Width"]
    height = gin.outputs["Room Height"]
    thick = gin.outputs["Wall Thickness"]

    outer = _sized_cube(tree, (bx - 700, by + 280), length, width, height)
    outer_geo = _translate(tree, (bx - 420, by + 280), _mesh_out(outer), _ground_z(tree, (bx - 700, by + 80), height).outputs["Vector"])

    inner_l = _inner_span(tree, (bx - 900, by - 40), length, thick)
    inner_w = _inner_span(tree, (bx - 900, by - 160), width, thick)
    inner_h_ceil = _inner_span(tree, (bx - 900, by - 280), height, thick)
    inner_h_open = _clamp_min(
        tree, (bx - 700, by - 400),
        _math(tree, "ADD", (bx - 860, by - 400), height, thick).outputs[0],
    )

    inner_ceil = _sized_cube(tree, (bx - 500, by - 80), inner_l.outputs[0], inner_w.outputs[0], inner_h_ceil.outputs[0])
    # Floor remains: lift inner by thickness + half inner height.
    ceil_z = _math(tree, "ADD", (bx - 500, by - 280), thick, _math(tree, "MULTIPLY", (bx - 680, by - 280), inner_h_ceil.outputs[0], 0.5).outputs[0])
    inner_ceil_geo = _translate(
        tree, (bx - 220, by - 80), _mesh_out(inner_ceil),
        _combine(tree, (bx - 400, by - 280), 0.0, 0.0, ceil_z.outputs[0]).outputs["Vector"],
    )

    inner_open = _sized_cube(tree, (bx - 500, by - 420), inner_l.outputs[0], inner_w.outputs[0], inner_h_open.outputs[0])
    open_z = _math(tree, "ADD", (bx - 500, by - 560), thick, _math(tree, "MULTIPLY", (bx - 680, by - 560), inner_h_open.outputs[0], 0.5).outputs[0])
    inner_open_geo = _translate(
        tree, (bx - 220, by - 420), _mesh_out(inner_open),
        _combine(tree, (bx - 400, by - 560), 0.0, 0.0, open_z.outputs[0]).outputs["Vector"],
    )

    inner_geo = _switch_geo(tree, (bx - 40, by - 200), gin.outputs["Ceiling"], inner_ceil_geo, inner_open_geo)
    bool_node, shell = mesh_boolean_node(tree, (bx + 160, by + 80), "DIFFERENCE", outer_geo, inner_geo)

    smooth = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 380, by + 80))
    try:
        smooth.inputs["Shade Smooth"].default_value = False
    except Exception:
        pass
    link_sockets(tree, shell, smooth.inputs["Geometry"])
    influenced = apply_universal_music_pass(tree, gin, smooth.outputs["Geometry"], (560, 80))
    link_sockets(tree, influenced, gout.inputs["Geometry"])
    color_node(bool_node, "math")

    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Outer Shell", "nodes": ("Mesh Cube", "Set Position"), "role": "geometry"},
        {"title": "Inner Void", "nodes": ("boolean", "Switch"), "role": "math"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return tree


def _join(tree, loc, *geoms):
    node = safe_node(tree, "GeometryNodeJoinGeometry", loc)
    for geom in geoms:
        if geom is not None:
            link_sockets(tree, geom, node.inputs["Geometry"])
    return node.outputs["Geometry"]


def _empty_geo(tree, loc):
    return _join(tree, loc)


def _span(tree, loc, outer_sock, thick_sock, punch=False):
    t2 = _math(tree, "MULTIPLY", (loc[0] - 160, loc[1]), thick_sock, 2.0)
    if punch:
        raw = _math(tree, "ADD", loc, outer_sock, t2.outputs[0])
    else:
        raw = _math(tree, "SUBTRACT", loc, outer_sock, t2.outputs[0])
    return _clamp_min(tree, (loc[0] + 180, loc[1]), raw.outputs[0])


def _hollow_box(tree, loc, length, width, height, thick, punch_x=False, punch_y=False):
    """Grounded outer cube minus inner void. punch_x/y open those ends."""
    bx, by = loc
    outer = _sized_cube(tree, (bx - 360, by + 80), length, width, height)
    outer_geo = _translate(
        tree, (bx - 120, by + 80), _mesh_out(outer),
        _ground_z(tree, (bx - 360, by - 80), height).outputs["Vector"],
    )
    inner_l = _span(tree, (bx - 520, by - 200), length, thick, punch=punch_x)
    inner_w = _span(tree, (bx - 520, by - 320), width, thick, punch=punch_y)
    inner_h = _span(tree, (bx - 520, by - 440), height, thick, punch=False)
    inner = _sized_cube(tree, (bx - 280, by - 280), inner_l.outputs[0], inner_w.outputs[0], inner_h.outputs[0])
    inner_z = _math(
        tree, "ADD", (bx - 280, by - 480), thick,
        _math(tree, "MULTIPLY", (bx - 440, by - 480), inner_h.outputs[0], 0.5).outputs[0],
    )
    inner_geo = _translate(
        tree, (bx - 40, by - 280), _mesh_out(inner),
        _combine(tree, (bx - 200, by - 480), 0.0, 0.0, inner_z.outputs[0]).outputs["Vector"],
    )
    _bool, shell = mesh_boolean_node(tree, (bx + 160, by), "DIFFERENCE", outer_geo, inner_geo)
    color_node(_bool, "math")
    return shell


def build_greybox_openings(group_name="MEL_greybox_openings"):
    """Boolean-cut door and window boxes from incoming geometry."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_bool_param(tree, "Cut Door", True)
    add_bool_param(tree, "Cut Window", True)
    add_float_param(tree, "Door Width", 0.9, 0.3, 4.0)
    add_float_param(tree, "Door Height", 2.1, 0.8, 5.0)
    add_float_param(tree, "Door X", 0.0, -20.0, 20.0)
    add_float_param(tree, "Window Width", 1.2, 0.3, 6.0)
    add_float_param(tree, "Window Height", 1.0, 0.3, 4.0)
    add_float_param(tree, "Window X", 1.8, -20.0, 20.0)
    add_float_param(tree, "Window Sill", 1.1, 0.2, 4.0)
    add_float_param(tree, "Cut Depth", 12.0, 0.2, 40.0)

    door = _sized_cube(
        tree, (bx - 500, by + 200),
        gin.outputs["Door Width"], gin.outputs["Cut Depth"], gin.outputs["Door Height"],
    )
    door_z = _math(tree, "MULTIPLY", (bx - 700, by + 40), gin.outputs["Door Height"], 0.5)
    door_geo = _translate(
        tree, (bx - 220, by + 200), _mesh_out(door),
        _combine(tree, (bx - 400, by + 40), gin.outputs["Door X"], 0.0, door_z.outputs[0]).outputs["Vector"],
    )

    win = _sized_cube(
        tree, (bx - 500, by - 200),
        gin.outputs["Window Width"], gin.outputs["Cut Depth"], gin.outputs["Window Height"],
    )
    win_half = _math(tree, "MULTIPLY", (bx - 700, by - 360), gin.outputs["Window Height"], 0.5)
    win_z = _math(tree, "ADD", (bx - 520, by - 360), gin.outputs["Window Sill"], win_half.outputs[0])
    win_geo = _translate(
        tree, (bx - 220, by - 200), _mesh_out(win),
        _combine(tree, (bx - 400, by - 360), gin.outputs["Window X"], 0.0, win_z.outputs[0]).outputs["Vector"],
    )

    empty = _empty_geo(tree, (bx - 40, by - 420))
    door_on = _switch_geo(tree, (bx - 40, by + 200), gin.outputs["Cut Door"], door_geo, empty)
    win_on = _switch_geo(tree, (bx - 40, by - 200), gin.outputs["Cut Window"], win_geo, empty)
    cutters = _join(tree, (bx + 160, by), door_on, win_on)
    _bool, cut = mesh_boolean_node(tree, (bx + 380, by), "DIFFERENCE", gin.outputs["Geometry"], cutters)
    color_node(_bool, "math")
    link_sockets(tree, cut, gout.inputs["Geometry"])

    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Cutters", "nodes": ("Mesh Cube", "Switch"), "role": "geometry"},
        {"title": "Boolean Cut", "nodes": ("boolean",), "role": "math"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return tree


def build_greybox_corridor(group_name="MEL_greybox_corridor"):
    """Tileable hollow hall with optional end caps."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Length", 8.0, 2.0, 40.0)
    add_float_param(tree, "Width", 2.4, 1.0, 12.0)
    add_float_param(tree, "Height", 3.2, 2.0, 12.0)
    add_float_param(tree, "Wall Thickness", 0.25, 0.08, 1.2)
    add_bool_param(tree, "End Cap", False)

    closed = _hollow_box(
        tree, (bx - 200, by + 160),
        gin.outputs["Length"], gin.outputs["Width"], gin.outputs["Height"],
        gin.outputs["Wall Thickness"], punch_x=False, punch_y=False,
    )
    open_ends = _hollow_box(
        tree, (bx - 200, by - 280),
        gin.outputs["Length"], gin.outputs["Width"], gin.outputs["Height"],
        gin.outputs["Wall Thickness"], punch_x=True, punch_y=False,
    )
    geo = _switch_geo(tree, (bx + 280, by), gin.outputs["End Cap"], closed, open_ends)
    link_sockets(tree, geo, gout.inputs["Geometry"])

    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Hall Shell", "nodes": ("boolean", "Switch"), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return tree


def build_greybox_junction(group_name="MEL_greybox_junction"):
    """T or X corridor join: union of hall volumes, then shell."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Size", 6.0, 2.0, 24.0)
    add_float_param(tree, "Width", 2.4, 1.0, 12.0)
    add_float_param(tree, "Height", 3.2, 2.0, 12.0)
    add_float_param(tree, "Wall Thickness", 0.25, 0.08, 1.2)
    add_bool_param(tree, "Cross Junction", False)

    stem = _hollow_box(
        tree, (bx - 400, by + 220),
        gin.outputs["Size"], gin.outputs["Width"], gin.outputs["Height"],
        gin.outputs["Wall Thickness"], punch_x=True, punch_y=False,
    )
    arm_x = _hollow_box(
        tree, (bx - 400, by - 80),
        gin.outputs["Width"], gin.outputs["Size"], gin.outputs["Height"],
        gin.outputs["Wall Thickness"], punch_x=False, punch_y=True,
    )
    half = _math(tree, "MULTIPLY", (bx - 700, by - 420), gin.outputs["Size"], 0.5)
    arm_t_len = _clamp_min(tree, (bx - 520, by - 420), half.outputs[0])
    arm_t = _hollow_box(
        tree, (bx - 400, by - 460),
        gin.outputs["Width"], arm_t_len.outputs[0], gin.outputs["Height"],
        gin.outputs["Wall Thickness"], punch_x=False, punch_y=True,
    )
    arm_t_shift = _math(tree, "MULTIPLY", (bx - 200, by - 620), arm_t_len.outputs[0], 0.5)
    arm_t_moved = _translate(
        tree, (bx - 40, by - 460), arm_t,
        _combine(tree, (bx - 200, by - 700), 0.0, arm_t_shift.outputs[0], 0.0).outputs["Vector"],
    )

    arm = _switch_geo(tree, (bx + 80, by - 200), gin.outputs["Cross Junction"], arm_x, arm_t_moved)
    union, joined = mesh_boolean_node(tree, (bx + 280, by), "UNION", stem, arm)
    color_node(union, "math")
    link_sockets(tree, joined, gout.inputs["Geometry"])

    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Stem and Arm", "nodes": ("boolean", "Switch"), "role": "geometry"},
        {"title": "Union", "nodes": ("union",), "role": "math"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return tree


def build_greybox_composer(group_name="MEL_greybox_composer"):
    """Join room, corridor, and junction groups. Snap is later."""
    tree, gin, gout = new_geometry_tree(group_name)
    make_group_input(tree, "NodeSocketGeometry", "Corridor")
    make_group_input(tree, "NodeSocketGeometry", "Junction")
    joined = _join(
        tree, (0, 0),
        gin.outputs["Geometry"],
        gin.outputs.get("Corridor"),
        gin.outputs.get("Junction"),
    )
    link_sockets(tree, joined, gout.inputs["Geometry"])
    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Join", "nodes": ("Join",), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return tree


# Register polyhedra & greybox builders into Melodia GN System
register_builder("MEL_polyhedra_icosahedron", build_polyhedra_icosahedron, "Icosahedron Solid", "20-faced Platonic Icosahedron with wireframe mode.", "primitives")
register_builder("MEL_polyhedra_dodecahedron", build_polyhedra_dodecahedron, "Dodecahedron Solid", "12-faced Platonic Dodecahedron (icosa dual), not an icosphere.", "primitives")
register_builder("MEL_greybox_room_kit", build_greybox_room_kit, "Greybox Room Kit", "Hollow greybox room with wall thickness and optional ceiling.", "structures")
register_builder("MEL_greybox_openings", build_greybox_openings, "Greybox Openings", "Door and window boxes boolean-cut from incoming geometry.", "structures")
register_builder("MEL_greybox_corridor", build_greybox_corridor, "Greybox Corridor", "Tileable hollow hall with length, width, height, thickness, optional end cap.", "structures")
register_builder("MEL_greybox_junction", build_greybox_junction, "Greybox Junction", "T or X corridor join via boolean union of hollow halls.", "structures")
register_builder("MEL_greybox_composer", build_greybox_composer, "Greybox Composer", "Join selected room, corridor, and junction groups.", "structures")
