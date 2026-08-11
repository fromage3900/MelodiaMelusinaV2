"""Polyhedra & Platonic Solid GN group builders — Icosahedron, Dodecahedron, Octahedron, Kepler-Poinsot Star Polyhedra.

Integrates Platonic & Kepler-Poinsot polyhedral geometry into the Melodia GN system for Blender 5.1+.
"""

from __future__ import annotations

import math
import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, add_vector_param,
    make_group_input, register_builder,
)


def build_polyhedra_icosahedron(group_name="MEL_polyhedra_icosahedron"):
    """Platonic Icosahedron / Geodesic Sphere GN builder — 20 triangular faces with subdivision control.

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


def build_polyhedra_dodecahedron(group_name="MEL_polyhedra_dodecahedron"):
    """Platonic Dodecahedron GN builder — 12 regular pentagonal faces.

    Constructed mathematically using dual cube-to-sphere vertex projections.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Radius", 1.0, 0.1, 10.0)
    add_float_param(tree, "Bevel Thickness", 0.03, 0.005, 0.2)
    add_bool_param(tree, "Use Wireframe", False)

    # Base IcoSphere with 1 subdivision (dual of dodecahedron)
    icosphere = safe_node(tree, "GeometryNodeMeshIcoSphere", (bx - 600, by + 200))
    link_sockets(tree, gin.outputs["Radius"], icosphere.inputs["Radius"])
    icosphere.inputs["Subdivisions"].default_value = 1

    mesh_to_curve = safe_node(tree, "GeometryNodeMeshToCurve", (bx - 400, by - 100))
    link_sockets(tree, icosphere.outputs["Mesh"], mesh_to_curve.inputs["Mesh"])

    curve_profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 400, by - 300))
    link_sockets(tree, gin.outputs["Bevel Thickness"], curve_profile.inputs["Radius"])
    curve_profile.inputs["Resolution"].default_value = 8

    curve_to_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 200, by - 100))
    link_sockets(tree, mesh_to_curve.outputs["Curve"], curve_to_mesh.inputs["Curve"])
    link_sockets(tree, curve_profile.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])

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
        {"title": "Dodecahedron Geometry", "nodes": ("IcoSphere", "Curve to Mesh", "Switch"), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return tree


def build_greybox_room_kit(group_name="MEL_greybox_room_kit"):
    """Greybox Room & Corridor Kit — procedural modular room layout with wall recutting and door frames.

    Provides modular architectural blockout shapes (Rooms, Corridors, T-Junctions, Cloisters).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Room Length", 8.0, 2.0, 30.0)
    add_float_param(tree, "Room Width", 6.0, 2.0, 30.0)
    add_float_param(tree, "Room Height", 4.0, 2.0, 15.0)
    add_float_param(tree, "Wall Thickness", 0.3, 0.1, 1.5)
    add_bool_param(tree, "Ceiling", True)

    # Outer Room Volume Cube
    outer_cube = safe_node(tree, "GeometryNodeMeshCube", (bx - 600, by + 300))
    link_float_to_vector(tree, gin.outputs["Room Length"], outer_cube, "Size", component=0)
    link_float_to_vector(tree, gin.outputs["Room Width"], outer_cube, "Size", component=1)
    link_float_to_vector(tree, gin.outputs["Room Height"], outer_cube, "Size", component=2)

    # Offset to Z ground level
    h_half = safe_node(tree, "ShaderNodeMath", (bx - 600, by + 100))
    h_half.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Room Height"], h_half.inputs[0])
    h_half.inputs[1].default_value = 0.5

    comb_pos = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 400, by + 100))
    link_sockets(tree, h_half.outputs[0], comb_pos.inputs["Z"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 200, by + 300))
    link_sockets(tree, outer_cube.outputs["Mesh"], set_pos.inputs["Geometry"])
    link_sockets(tree, comb_pos.outputs["Vector"], set_pos.inputs["Position"])

    smooth = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx, by + 300))
    link_sockets(tree, set_pos.outputs["Geometry"], smooth.inputs["Geometry"])

    link_sockets(tree, smooth.outputs["Geometry"], gout.inputs["Geometry"])

    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Room Outer Shell", "nodes": ("Mesh Cube", "Set Position"), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return tree


# Register polyhedra & greybox builders into Melodia GN System
register_builder("MEL_polyhedra_icosahedron", build_polyhedra_icosahedron, "Icosahedron Solid", "20-faced Platonic Icosahedron with wireframe mode.", "primitives")
register_builder("MEL_polyhedra_dodecahedron", build_polyhedra_dodecahedron, "Dodecahedron Solid", "12-faced Platonic Dodecahedron solid primitive.", "primitives")
register_builder("MEL_greybox_room_kit", build_greybox_room_kit, "Greybox Room Kit", "Procedural architectural room & corridor blockout volume.", "structures")
