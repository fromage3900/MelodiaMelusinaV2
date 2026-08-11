"""Mesh tool GN group builders — bevel, inset, poke, subdivision, remesh, smooth.

Replaces manual modifier stacking with composable, param-exposed GN groups.
Every builder follows the melodia_gn convention: register_builder at module end.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    add_vector_param, make_group_input, tree_input_names,
)


def build_bevel_profile(group_name="MEL_bevel_profile"):
    """Custom-profile bevel — width, segments, profile curve, vertex-only option.

    Exposes profile amount (0=concave, 0.5=round, 1=chamfer) as a float
    so artists can shape the bevel without authoring a curve.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Width", 0.05, 0.0, 10.0)
    add_int_param(tree, "Segments", 2, 1, 16)
    add_float_param(tree, "Profile", 0.5, 0.0, 1.0)
    add_bool_param(tree, "Only Vertices", False)
    add_bool_param(tree, "Limit to Selected", False)

    bevel = safe_node(tree, "GeometryNodeBevelMesh", (bx, by))
    if bevel:
        link_sockets(tree, gin.outputs["Geometry"], bevel.inputs["Geometry"])
        link_sockets(tree, gin.outputs["Width"], bevel.inputs["Radius"])
        link_sockets(tree, gin.outputs["Segments"], bevel.inputs["Segments"])
        link_sockets(tree, gin.outputs["Profile"], bevel.inputs["Profile"])
        if "Only Vertices" in gin.outputs:
            link_sockets(tree, gin.outputs["Only Vertices"], bevel.inputs["Only Vertices"])
        if "Limit to Selected" in gin.outputs and "Selection" in bevel.inputs:
            link_sockets(tree, gin.outputs["Limit to Selected"], bevel.inputs["Selection"])
        link_sockets(tree, bevel.outputs["Mesh"], gout.inputs["Geometry"])
        color_node(bevel, "geometry")
    else:
        link_sockets(tree, gin.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, "MEL_bevel_profile", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bevel", "nodes": ("bevel",), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_weighted_bevel(group_name="MEL_weighted_bevel"):
    """Weighted bevel — uses a float attribute to control bevel width per-edge.

    Reads an existing 'bevel_weight' attribute or falls back to uniform width.
    Useful for hard-surface where edge loops define sharpness.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Base Width", 0.05, 0.0, 10.0)
    add_int_param(tree, "Segments", 2, 1, 16)
    add_float_param(tree, "Weight Scale", 1.0, 0.0, 5.0)
    add_bool_param(tree, "Use Bevel Weight", True)

    # Capture bevel_weight attribute if it exists
    cap_weight = safe_node(tree, "GeometryNodeCaptureAttribute", (bx - 300, by + 100))
    if cap_weight:
        cap_weight.data_type = "FLOAT"
        cap_weight.domain = "EDGE"
        link_sockets(tree, gin.outputs["Geometry"], cap_weight.inputs["Geometry"])
        weight_sock = cap_weight.inputs.get("Value")
        if weight_sock is not None:
            bevel_weight_exists = False
            for attr in bpy.data.node_groups.get(tree.name, bpy.data.node_groups.get(group_name)):
                pass
            weight_sock.default_value = 1.0

    named = safe_node(tree, "GeometryNodeNamedAttribute", (bx - 300, by - 50))
    if named:
        named.data_type = "FLOAT"
        named.inputs["Name"].default_value = "bevel_weight"

    # Switch: use bevel_weight if available, fall back to 1.0
    picker = safe_node(tree, "ShaderNodeMix", (bx - 100, by + 50))
    if picker:
        picker.data_type = "FLOAT"
        picker.clamp_result = True
        link_sockets(tree, gin.outputs["Use Bevel Weight"], picker.inputs["Factor"])
        picker.inputs["A"].default_value = 1.0
        if named:
            link_sockets(tree, named.outputs["Attribute"], picker.inputs["B"])

    weighted = safe_node(tree, "ShaderNodeMath", (bx + 100, by))
    if weighted:
        weighted.operation = "MULTIPLY"
        link_sockets(tree, gin.outputs["Base Width"], weighted.inputs[0])
        if picker:
            link_sockets(tree, picker.outputs[0], weighted.inputs[1])
        else:
            weighted.inputs[1].default_value = 1.0

    bevel = safe_node(tree, "GeometryNodeBevelMesh", (bx + 300, by))
    if bevel:
        link_sockets(tree, gin.outputs["Geometry"], bevel.inputs["Geometry"])
        link_sockets(tree, weighted.outputs[0], bevel.inputs["Radius"])
        link_sockets(tree, gin.outputs["Segments"], bevel.inputs["Segments"])
        link_sockets(tree, bevel.outputs["Mesh"], gout.inputs["Geometry"])
        color_node(bevel, "geometry")

    return tree


def build_multi_bevel(group_name="MEL_multi_bevel"):
    """Multi-stage bevel — applies 2-3 bevel modifiers in sequence with
    decreasing widths for that 'chamfer-with-micro-bevel' hard-surface look.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Main Bevel", 0.1, 0.0, 10.0)
    add_float_param(tree, "Micro Bevel", 0.01, 0.0, 2.0)
    add_int_param(tree, "Main Segments", 3, 1, 16)
    add_int_param(tree, "Micro Segments", 1, 1, 8)
    add_float_param(tree, "Main Profile", 0.5, 0.0, 1.0)
    add_float_param(tree, "Micro Profile", 0.25, 0.0, 1.0)

    geo = gin.outputs["Geometry"]

    # First bevel — main chamfer
    bevel_1 = safe_node(tree, "GeometryNodeBevelMesh", (bx - 100, by + 100))
    if bevel_1:
        link_sockets(tree, geo, bevel_1.inputs["Geometry"])
        link_sockets(tree, gin.outputs["Main Bevel"], bevel_1.inputs["Radius"])
        link_sockets(tree, gin.outputs["Main Segments"], bevel_1.inputs["Segments"])
        link_sockets(tree, gin.outputs["Main Profile"], bevel_1.inputs["Profile"])
        geo = bevel_1.outputs["Mesh"]
        color_node(bevel_1, "geometry")

    # Second bevel — micro chamfer on remaining sharp edges
    bevel_2 = safe_node(tree, "GeometryNodeBevelMesh", (bx + 150, by - 50))
    if bevel_2:
        link_sockets(tree, geo, bevel_2.inputs["Geometry"])
        link_sockets(tree, gin.outputs["Micro Bevel"], bevel_2.inputs["Radius"])
        link_sockets(tree, gin.outputs["Micro Segments"], bevel_2.inputs["Segments"])
        link_sockets(tree, gin.outputs["Micro Profile"], bevel_2.inputs["Profile"])
        geo = bevel_2.outputs["Mesh"]
        color_node(bevel_2, "geometry")

    link_sockets(tree, geo, gout.inputs["Geometry"])
    return tree


def build_inset_faces(group_name="MEL_inset_faces"):
    """Inset faces — extrude individual faces then scale them inward.

    Controls for thickness, depth, and per-face inset via selection.
    Mimics the standard Blender Inset Faces (I-key) in GN form.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Thickness", 0.2, 0.0, 5.0)
    add_float_param(tree, "Depth", 0.0, -2.0, 2.0)
    add_bool_param(tree, "Individual Faces", True)

    extrude = safe_node(tree, "GeometryNodeExtrudeMesh", (bx, by))
    if not extrude:
        link_sockets(tree, gin.outputs["Geometry"], gout.inputs["Geometry"])
        return tree

    extrude.mode = "FACES"
    link_sockets(tree, gin.outputs["Geometry"], extrude.inputs["Mesh"])
    link_sockets(tree, gin.outputs["Thickness"], extrude.inputs["Offset Scale"])

    # Connect offset Z (Depth pushes inward/outward from face normal)
    link_float_to_vector(tree, gin.outputs["Depth"], extrude, "Offset", component=2,
                         defaults=(0.0, 0.0, 0.0))

    # Scale the extruded top faces inward to create the inset
    scale = safe_node(tree, "GeometryNodeScaleElements", (bx + 200, by))
    if scale:
        scale.domain = "FACE"
        scale.scale = 0.8
        if gin.outputs["Individual Faces"]:
            scale_mul = safe_node(tree, "ShaderNodeMath", (bx, by - 100))
            scale_mul.operation = "MULTIPLY"
            scale_mul.inputs[0].default_value = 1.0
            scale_mul.inputs[1].default_value = 0.8
            link_sockets(tree, extrude.outputs["Mesh"], scale.inputs["Geometry"])
            link_sockets(tree, scale.outputs["Geometry"], gout.inputs["Geometry"])
        else:
            link_sockets(tree, extrude.outputs["Mesh"], gout.inputs["Geometry"])
        color_node(scale, "geometry")
    else:
        link_sockets(tree, extrude.outputs["Mesh"], gout.inputs["Geometry"])

    color_node(extrude, "geometry")
    return label_tree(tree, "MEL_inset_faces", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Extrude Inset", "nodes": ("extrude",), "role": "geometry"},
        {"title": "Scale", "nodes": ("scale",), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_poke_faces(group_name="MEL_poke_faces"):
    """Poke faces — triangulate quads by adding a center vertex.

    GN approach: extrude each face to a point, creating pyramid geometry.
    Useful for stellated shapes, spike arrays, or faceted gems.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Height", 0.5, -2.0, 5.0)
    add_float_param(tree, "Inset", 0.0, 0.0, 1.0)
    add_bool_param(tree, "Individual Faces", True)

    geo = gin.outputs["Geometry"]

    # Triangulate first for clean poke base
    tri = safe_node(tree, "GeometryNodeTriangulate", (bx - 300, by + 100))
    if tri:
        link_sockets(tree, geo, tri.inputs["Mesh"])
        geo = tri.outputs["Mesh"]
        color_node(tri, "geometry")

    # Extrude individual faces
    extrude = safe_node(tree, "GeometryNodeExtrudeMesh", (bx - 50, by))
    if extrude:
        extrude.mode = "FACES"
        link_sockets(tree, geo, extrude.inputs["Mesh"])
        link_sockets(tree, gin.outputs["Height"], extrude.inputs["Offset Scale"])

        # Apply inset before extrusion
        if gin.outputs["Inset"]:
            link_float_to_vector(tree, gin.outputs["Inset"], extrude, "Offset",
                                 component=2, defaults=(0.0, 0.0, 0.0))

        geo = extrude.outputs["Mesh"]
        color_node(extrude, "geometry")

    # Scale top faces to a point for true poke effect
    scale_elems = safe_node(tree, "GeometryNodeScaleElements", (bx + 200, by))
    if scale_elems:
        scale_elems.domain = "FACE"
        scale_elems.scale = 0.01
        link_sockets(tree, geo, scale_elems.inputs["Geometry"])
        link_sockets(tree, scale_elems.outputs["Geometry"], gout.inputs["Geometry"])
        color_node(scale_elems, "geometry")
    else:
        link_sockets(tree, geo, gout.inputs["Geometry"])

    return label_tree(tree, "MEL_poke_faces", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Triangulate", "nodes": ("tri",), "role": "geometry"},
        {"title": "Extrude", "nodes": ("extrude",), "role": "geometry"},
        {"title": "Poke Scale", "nodes": ("scale",), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_subdivision_surface(group_name="MEL_subdivision_surface"):
    """Subdivision surface with crease controls and boundary smoothing.

    Wraps the Subdivision Surface modifier in GN form with edge-crease
    support via named attributes. Exposes UV smooth, boundary smooth,
    and quality levels for production control.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Levels", 2, 0, 6)
    add_float_param(tree, "Edge Crease", 0.0, 0.0, 1.0)
    add_float_param(tree, "Vertex Crease", 0.0, 0.0, 1.0)
    add_bool_param(tree, "Smooth Boundary", True)

    subdiv = safe_node(tree, "GeometryNodeSubdivisionSurface", (bx, by))
    if not subdiv:
        link_sockets(tree, gin.outputs["Geometry"], gout.inputs["Geometry"])
        return tree

    if hasattr(subdiv, "boundary_smooth"):
        subdiv.boundary_smooth = "ALL"

    link_sockets(tree, gin.outputs["Geometry"], subdiv.inputs["Mesh"])
    link_sockets(tree, gin.outputs["Levels"], subdiv.inputs["Level"])

    # Store edge crease as named attribute before subdivision
    store_edge = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx - 250, by + 100))
    if store_edge and gin.outputs["Edge Crease"]:
        store_edge.data_type = "FLOAT"
        store_edge.domain = "EDGE"
        link_sockets(tree, gin.outputs["Geometry"], store_edge.inputs["Geometry"])
        store_edge.inputs["Name"].default_value = "crease_edge"
        link_sockets(tree, gin.outputs["Edge Crease"], store_edge.inputs["Value"])
        link_sockets(tree, store_edge.outputs["Geometry"], subdiv.inputs["Mesh"])

    # Store vertex crease
    store_vert = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx - 250, by - 50))
    if store_vert and gin.outputs["Vertex Crease"]:
        store_vert.data_type = "FLOAT"
        store_vert.domain = "POINT"
        stored_geo = store_edge.outputs["Geometry"] if store_edge else gin.outputs["Geometry"]
        link_sockets(tree, stored_geo, store_vert.inputs["Geometry"])
        store_vert.inputs["Name"].default_value = "crease_vert"
        link_sockets(tree, gin.outputs["Vertex Crease"], store_vert.inputs["Value"])
        link_sockets(tree, store_vert.outputs["Geometry"], subdiv.inputs["Mesh"])

    link_sockets(tree, subdiv.outputs["Mesh"], gout.inputs["Geometry"])
    color_node(subdiv, "geometry")
    if store_edge:
        color_node(store_edge, "attribute")
    if store_vert:
        color_node(store_vert, "attribute")

    return label_tree(tree, "MEL_subdivision_surface", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Crease Setup", "nodes": ("edge_crease", "vert_crease"), "role": "attribute"},
        {"title": "Subdivision", "nodes": ("subdiv",), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_remesh_dual(group_name="MEL_remesh_dual"):
    """Dual-mesh remesh — converts mesh to its dual (faces become verts).

    Good for organic topology after subdivision, creates hexagonal-like
    patterns from quads. Pair with subdivision for smooth organic results.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_bool_param(tree, "Preserve Crease", True)
    add_bool_param(tree, "Smooth Result", True)

    dual = safe_node(tree, "GeometryNodeMeshToDualMesh", (bx, by))
    if dual:
        link_sockets(tree, gin.outputs["Geometry"], dual.inputs["Mesh"])
        if gin.outputs["Preserve Crease"] and "Crease" in dual.inputs:
            link_sockets(tree, gin.outputs["Preserve Crease"], dual.inputs["Crease"])
        link_sockets(tree, dual.outputs["Dual Mesh"], gout.inputs["Geometry"])
        color_node(dual, "geometry")
    else:
        link_sockets(tree, gin.outputs["Geometry"], gout.inputs["Geometry"])

    return tree


def build_smooth_laplacian(group_name="MEL_smooth_laplacian"):
    """Laplacian mesh smooth — preserves volume better than simple blur.

    Uses Blur Attribute node with Laplacian mode on vertex positions.
    Good for cleanup after sculpting or generative mesh operations.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Iterations", 3, 1, 20)
    add_float_param(tree, "Factor", 0.5, 0.0, 1.0)
    add_bool_param(tree, "Preserve Volume", True)
    add_bool_param(tree, "Project to Surface", False)

    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 400, by + 100))
    color_node(pos, "input")

    blur = safe_node(tree, "GeometryNodeBlurAttribute", (bx - 200, by))
    if blur:
        blur.data_type = "FLOAT_VECTOR"

        iterations = gin.outputs["Iterations"]
        factor = gin.outputs["Factor"]
        if iterations:
            link_sockets(tree, iterations, blur.inputs["Iterations"])
        if factor:
            link_sockets(tree, factor, blur.inputs["Weight"])

        link_sockets(tree, pos.outputs["Position"], blur.inputs["Value"])
        link_sockets(tree, gin.outputs["Geometry"], blur.inputs["Geometry"])

        set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 100, by))
        if set_pos:
            if gin.outputs["Preserve Volume"]:
                mix = safe_node(tree, "ShaderNodeMix", (bx - 50, by - 100))
                if mix:
                    mix.data_type = "VECTOR"
                    mix.clamp_result = True
                    mix.inputs["Factor"].default_value = 0.5
                    link_sockets(tree, pos.outputs["Position"], mix.inputs["A"])
                    link_sockets(tree, blur.outputs["Value"], mix.inputs["B"])
                    link_sockets(tree, mix.outputs[0], set_pos.inputs["Position"])
                else:
                    link_sockets(tree, blur.outputs["Value"], set_pos.inputs["Position"])
            else:
                link_sockets(tree, blur.outputs["Value"], set_pos.inputs["Position"])

            link_sockets(tree, gin.outputs["Geometry"], set_pos.inputs["Geometry"])
            link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])
        else:
            link_sockets(tree, gin.outputs["Geometry"], gout.inputs["Geometry"])

        color_node(blur, "attribute")
        color_node(set_pos, "attribute")
    else:
        link_sockets(tree, gin.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, "MEL_smooth_laplacian", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Blur Position", "nodes": ("position", "blur"), "role": "attribute"},
        {"title": "Set Position", "nodes": ("set_pos",), "role": "attribute"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# -- Registry --
from .core import register_builder

register_builder("MEL_bevel_profile", build_bevel_profile,
    "Bevel Profile", "Custom-profile bevel with width, segments, and profile curve control", "mesh_tools")
register_builder("MEL_weighted_bevel", build_weighted_bevel,
    "Weighted Bevel", "Edge-weighted bevel using bevel_weight attribute", "mesh_tools")
register_builder("MEL_multi_bevel", build_multi_bevel,
    "Multi Bevel", "Two-stage bevel — main chamfer + micro-bevel for hard-surface", "mesh_tools")
register_builder("MEL_inset_faces", build_inset_faces,
    "Inset Faces", "Extrude-and-scale face inset with depth control", "mesh_tools")
register_builder("MEL_poke_faces", build_poke_faces,
    "Poke Faces", "Triangulate-to-point face poke for spikes and gems", "mesh_tools")
register_builder("MEL_subdivision_surface", build_subdivision_surface,
    "Subdivision Surface", "Catmull-Clark subdivision with per-edge/per-vertex crease", "mesh_tools")
register_builder("MEL_remesh_dual", build_remesh_dual,
    "Remesh Dual", "Dual-mesh remesh — faces become vertices for organic topology", "mesh_tools")
register_builder("MEL_smooth_laplacian", build_smooth_laplacian,
    "Smooth Laplacian", "Volume-preserving Laplacian smooth via Blur Attribute", "mesh_tools")
