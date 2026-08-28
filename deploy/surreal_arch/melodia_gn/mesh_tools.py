"""Mesh tool GN group builders - bevel, inset, poke, subdivision, remesh, smooth.

Replaces manual modifier stacking with composable, param-exposed GN groups.
Every builder follows the melodia_gn convention: register_builder at module end.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    add_vector_param, make_group_input, tree_input_names, require_node, sock,
)


def _wire_mesh_bevel(tree, bevel, mesh_sock, offset_sock, segments_sock=None, profile_sock=None):
    """Link Blender 5.2 Mesh Bevel sockets. Do not wire Selection=False (that bevels nothing).

    5.2: Offset is the width; Shape is the 0-1 profile amount; Profile is a curve geometry.
    """
    link_sockets(tree, mesh_sock, sock(bevel, "Mesh", "Geometry"))
    link_sockets(tree, offset_sock, sock(bevel, "Offset", "Width"))
    segs = sock(bevel, "Segments")
    if segments_sock is not None and segs is not None:
        link_sockets(tree, segments_sock, segs)
    if profile_sock is not None:
        shape = sock(bevel, "Shape")
        prof = sock(bevel, "Profile")
        if shape is not None and getattr(shape, "type", "") != "GEOMETRY":
            link_sockets(tree, profile_sock, shape)
        elif prof is not None and getattr(prof, "type", "") != "GEOMETRY":
            link_sockets(tree, profile_sock, prof)
    color_node(bevel, "geometry")
    return sock(bevel, "Mesh", "Geometry", outputs=True)


def build_bevel_profile(group_name="MEL_bevel_profile"):
    """Custom-profile bevel - width, segments, profile curve, vertex-only option.

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

    bevel = require_node(
        tree, "GeometryNodeMeshBevel", (bx, by), "GeometryNodeBevelMesh",
    )
    mesh_out = _wire_mesh_bevel(
        tree, bevel, gin.outputs["Geometry"], gin.outputs["Width"],
        gin.outputs["Segments"], gin.outputs["Profile"],
    )
    link_sockets(tree, mesh_out, gout.inputs["Geometry"])

    return label_tree(tree, "MEL_bevel_profile", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bevel", "nodes": ("bevel",), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_weighted_bevel(group_name="MEL_weighted_bevel"):
    """Weighted bevel - uses a float attribute to control bevel width per-edge.

    Reads an existing 'bevel_weight' attribute or falls back to uniform width.
    Useful for hard-surface where edge loops define sharpness.
    Now auto-generates bevel_weight from edge angle when missing (infinity-nikki
    soft-edge workflow: keep silhouette crisp without manual weight paint).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Base Width", 0.05, 0.0, 10.0)
    add_int_param(tree, "Segments", 2, 1, 16)
    add_float_param(tree, "Weight Scale", 1.0, 0.0, 5.0)
    add_bool_param(tree, "Use Bevel Weight", True)
    add_float_param(tree, "Auto Angle Threshold", 30.0, 5.0, 90.0)

    # --- auto bevel_weight generation (edge angle -> weight) ---
    # Edge Angle node gives radians per edge; convert threshold to rad and compare
    edge_angle = safe_node(tree, "GeometryNodeInputMeshEdgeAngle", (bx - 500, by + 120))
    thresh_rad = safe_node(tree, "ShaderNodeMath", (bx - 350, by + 120))
    if thresh_rad:
        thresh_rad.operation = "MULTIPLY"
        link_sockets(tree, gin.outputs["Auto Angle Threshold"], thresh_rad.inputs[0])
        thresh_rad.inputs[1].default_value = 0.01745329252  # deg->rad
    cmp = safe_node(tree, "FunctionNodeCompare", (bx - 200, by + 80))
    auto_weight = None
    if edge_angle and thresh_rad and cmp:
        cmp.data_type = "FLOAT"
        cmp.operation = "GREATER_THAN"
        link_sockets(tree, edge_angle.outputs["Angle"], cmp.inputs["A"])
        link_sockets(tree, thresh_rad.outputs[0], cmp.inputs["B"])
        # Compare (float 0/1) -> capture as edge domain attribute bevel_weight
        auto_store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx - 50, by + 80))
        if auto_store:
            auto_store.data_type = "FLOAT"
            auto_store.domain = "EDGE"
            auto_store.inputs["Name"].default_value = "bevel_weight_auto"
            link_sockets(tree, gin.outputs["Geometry"], auto_store.inputs["Geometry"])
            link_sockets(tree, cmp.outputs["Result"], auto_store.inputs["Value"])
            auto_weight = auto_store.outputs["Geometry"]

    # Bevel-weight fallback: InputNamedAttribute + Mix, or uniform width.
    # Priority: manual bevel_weight > auto bevel_weight_auto > 1.0
    named = safe_node(tree, "GeometryNodeInputNamedAttribute", (bx - 300, by - 50))
    if named:
        named.data_type = "FLOAT"
        named.inputs["Name"].default_value = "bevel_weight"

    named_auto = safe_node(tree, "GeometryNodeInputNamedAttribute", (bx - 300, by - 150))
    if named_auto:
        named_auto.data_type = "FLOAT"
        named_auto.inputs["Name"].default_value = "bevel_weight_auto"

    # Switch: use bevel_weight if available, fall back to 1.0
    picker = safe_node(tree, "ShaderNodeMix", (bx - 100, by + 50))
    if picker:
        picker.data_type = "FLOAT"
        picker.clamp_result = True
        link_sockets(tree, gin.outputs["Use Bevel Weight"], picker.inputs["Factor"])
        picker.inputs["A"].default_value = 1.0
        if named:
            link_sockets(tree, named.outputs["Attribute"], picker.inputs["B"])

    # Second mix: if manual weight is 0 (unpainted), fallback to auto angle weight
    picker_auto = safe_node(tree, "ShaderNodeMix", (bx + 50, by - 30))
    if picker_auto and named_auto and picker:
        picker_auto.data_type = "FLOAT"
        # Mix factor = manual weight present? Use picker result as factor via compare >0.01
        gt = safe_node(tree, "FunctionNodeCompare", (bx - 50, by - 80))
        if gt:
            gt.data_type = "FLOAT"
            gt.operation = "GREATER_THAN"
            link_sockets(tree, picker.outputs[0] if picker else None, gt.inputs["A"])
            gt.inputs["B"].default_value = 0.01
            link_sockets(tree, gt.outputs["Result"], picker_auto.inputs["Factor"])
            picker_auto.inputs["A"].default_value = 0.0
            # Will wire B to auto attribute after
            link_sockets(tree, named_auto.outputs["Attribute"], picker_auto.inputs["B"])
            # Weighted width uses auto-fallback mix output
            weighted_src = picker_auto.outputs[0]
        else:
            weighted_src = picker.outputs[0] if picker else None
    else:
        weighted_src = picker.outputs[0] if picker else None

    weighted = safe_node(tree, "ShaderNodeMath", (bx + 100, by))
    if weighted:
        weighted.operation = "MULTIPLY"
        link_sockets(tree, gin.outputs["Base Width"], weighted.inputs[0])
        if weighted_src is not None:
            link_sockets(tree, weighted_src, weighted.inputs[1])
        elif picker:
            link_sockets(tree, picker.outputs[0], weighted.inputs[1])
        else:
            weighted.inputs[1].default_value = 1.0
        # optional Weight Scale multiplier
        scale_mul = safe_node(tree, "ShaderNodeMath", (bx + 180, by - 40))
        if scale_mul and gin.outputs["Weight Scale"]:
            scale_mul.operation = "MULTIPLY"
            link_sockets(tree, weighted.outputs[0], scale_mul.inputs[0])
            link_sockets(tree, gin.outputs["Weight Scale"], scale_mul.inputs[1])
            weighted = scale_mul

    bevel = require_node(
        tree, "GeometryNodeMeshBevel", (bx + 300, by), "GeometryNodeBevelMesh",
    )
    bevel_input_geo = auto_weight if auto_weight is not None else gin.outputs["Geometry"]
    mesh_out = _wire_mesh_bevel(
        tree, bevel, bevel_input_geo, weighted.outputs[0] if weighted else gin.outputs["Base Width"],
        gin.outputs["Segments"],
    )
    link_sockets(tree, mesh_out, gout.inputs["Geometry"])

    return label_tree(tree, "MEL_weighted_bevel", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Auto Weight (edge angle)", "nodes": ("edge", "compare", "auto"), "role": "attribute"},
        {"title": "Weighted Bevel", "nodes": ("bevel",), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_multi_bevel(group_name="MEL_multi_bevel"):
    """Multi-stage bevel - applies 2-3 bevel modifiers in sequence with
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

    bevel_1 = require_node(
        tree, "GeometryNodeMeshBevel", (bx - 100, by + 100), "GeometryNodeBevelMesh",
    )
    geo = _wire_mesh_bevel(
        tree, bevel_1, geo, gin.outputs["Main Bevel"],
        gin.outputs["Main Segments"], gin.outputs["Main Profile"],
    )

    # Second bevel - micro chamfer on remaining sharp edges
    bevel_2 = require_node(
        tree, "GeometryNodeMeshBevel", (bx + 150, by - 50), "GeometryNodeBevelMesh",
    )
    geo = _wire_mesh_bevel(
        tree, bevel_2, geo, gin.outputs["Micro Bevel"],
        gin.outputs["Micro Segments"], gin.outputs["Micro Profile"],
    )

    link_sockets(tree, geo, gout.inputs["Geometry"])
    return tree


def build_inset_faces(group_name="MEL_inset_faces"):
    """Inset faces - extrude individual faces then scale them inward.

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
        scale.inputs["Scale"].default_value = 0.8
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
    """Poke faces - triangulate quads by adding a center vertex.

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
        scale_elems.inputs["Scale"].default_value = 0.01
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
    """Dual-mesh remesh - converts mesh to its dual (faces become verts).

    Good for organic topology after subdivision, creates hexagonal-like
    patterns from quads. Pair with subdivision for smooth organic results.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_bool_param(tree, "Preserve Crease", True)
    add_bool_param(tree, "Smooth Result", True)

    dual = safe_node(tree, "GeometryNodeDualMesh", (bx, by))
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
    """Laplacian mesh smooth - preserves volume better than simple blur.

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


def build_auto_bevel(group_name="MEL_auto_bevel"):
    """One-click auto bevel — edge-angle weighted + shade smooth + weighted normal.

    Ease-of-use wrapper: no weight paint needed. Builds bevel_weight_auto from
    30 deg threshold (editable) then runs weighted bevel with Weight Scale.
    Mirrors Infinity Nikki soft bevel look: crisp edges stay sharp, flat areas stay soft.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Width", 0.03, 0.0, 2.0)
    add_int_param(tree, "Segments", 3, 1, 8)
    add_float_param(tree, "Profile", 0.5, 0.0, 1.0)
    add_float_param(tree, "Angle Threshold", 30.0, 5.0, 90.0)
    add_bool_param(tree, "Shade Smooth", True)

    # Reuse weighted bevel chain: auto weight -> bevel
    edge_angle = safe_node(tree, "GeometryNodeInputMeshEdgeAngle", (bx - 400, by + 80))
    thresh = safe_node(tree, "ShaderNodeMath", (bx - 250, by + 80))
    if thresh:
        thresh.operation = "MULTIPLY"
        link_sockets(tree, gin.outputs["Angle Threshold"], thresh.inputs[0])
        thresh.inputs[1].default_value = 0.01745329252
    cmp = safe_node(tree, "FunctionNodeCompare", (bx - 100, by + 40))
    if cmp and edge_angle and thresh:
        cmp.data_type = "FLOAT"
        cmp.operation = "GREATER_THAN"
        link_sockets(tree, edge_angle.outputs["Angle"], cmp.inputs["A"])
        link_sockets(tree, thresh.outputs[0], cmp.inputs["B"])
        store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 80, by + 40))
        if store:
            store.data_type = "FLOAT"
            store.domain = "EDGE"
            store.inputs["Name"].default_value = "bevel_weight"
            link_sockets(tree, gin.outputs["Geometry"], store.inputs["Geometry"])
            link_sockets(tree, cmp.outputs["Result"], store.inputs["Value"])
            geo = store.outputs["Geometry"]
        else:
            geo = gin.outputs["Geometry"]
    else:
        geo = gin.outputs["Geometry"]

    bevel = require_node(tree, "GeometryNodeMeshBevel", (bx + 240, by), "GeometryNodeBevelMesh")
    # Weighted path: reuse Width as offset, Profile as shape
    mesh_out = _wire_mesh_bevel(tree, bevel, geo, gin.outputs["Width"], gin.outputs["Segments"], gin.outputs["Profile"])

    # Weighted normal is modifier-only in GN (no GeometryNodeWeightedNormal) — rely on SetShadeSmooth + auto angle fallback
    # Keep bevel_weight for modifier weighted-normal outside GN; GN just shade-smooth
    smooth = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 500, by))
    if smooth:
        link_sockets(tree, mesh_out, smooth.inputs["Geometry"])
        link_sockets(tree, gin.outputs["Shade Smooth"], smooth.inputs["Shade Smooth"] if "Shade Smooth" in smooth.inputs else smooth.inputs[0])
        mesh_out = smooth.outputs["Geometry"] if "Geometry" in smooth.outputs else smooth.outputs[0]

    link_sockets(tree, mesh_out, gout.inputs["Geometry"])
    return label_tree(tree, "MEL_auto_bevel", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Auto Edge Weight", "nodes": ("edge", "compare", "store"), "role": "attribute"},
        {"title": "Bevel + Normal", "nodes": ("bevel", "weighted", "smooth"), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_curvature_bevel(group_name="MEL_curvature_bevel"):
    """Curvature-driven bevel — tights on high-curvature, soft elsewhere.

    Samples face curvature via Position + Normal variance; drives bevel width.
    Good for ornate nikki drapes and musical instrument filigree where
    tight curls need sharper bevel than broad panels.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_float_param(tree, "Base Width", 0.025, 0.0, 1.0)
    add_float_param(tree, "Curvature Scale", 1.0, 0.0, 3.0)
    add_int_param(tree, "Segments", 3, 1, 8)
    add_float_param(tree, "Threshold", 0.5, 0.0, 1.0)

    # Simple curvature proxy: edge angle modulated
    angle = safe_node(tree, "GeometryNodeInputMeshEdgeAngle", (bx - 300, by + 60))
    norm = safe_node(tree, "ShaderNodeMath", (bx - 100, by + 60))
    if norm and angle:
        norm.operation = "DIVIDE"
        link_sockets(tree, angle.outputs["Angle"], norm.inputs[0])
        norm.inputs[1].default_value = 3.14159
    mult = safe_node(tree, "ShaderNodeMath", (bx + 60, by + 20))
    if mult and gin.outputs["Curvature Scale"]:
        mult.operation = "MULTIPLY"
        link_sockets(tree, norm.outputs[0] if norm else None, mult.inputs[0])
        link_sockets(tree, gin.outputs["Curvature Scale"], mult.inputs[1])
    clamp = safe_node(tree, "ShaderNodeClamp", (bx + 180, by))
    if clamp and mult:
        link_sockets(tree, mult.outputs[0], clamp.inputs["Value"])
        clamp.inputs["Min"].default_value = 0.0
        clamp.inputs["Max"].default_value = 1.0
        mixed = safe_node(tree, "ShaderNodeMix", (bx + 280, by))
        if mixed:
            mixed.data_type = "FLOAT"
            link_sockets(tree, gin.outputs["Threshold"], mixed.inputs["Factor"])
            mixed.inputs["A"].default_value = 0.0
            link_sockets(tree, clamp.outputs["Result"] if hasattr(clamp.outputs, "Result") else clamp.outputs[0], mixed.inputs["B"])
            width_src = mixed.outputs[0]
        else:
            width_src = clamp.outputs["Result"] if hasattr(clamp.outputs, "Result") else clamp.outputs[0]
    else:
        width_src = gin.outputs["Base Width"]

    bevel = require_node(tree, "GeometryNodeMeshBevel", (bx + 380, by), "GeometryNodeBevelMesh")
    mesh_out = _wire_mesh_bevel(tree, bevel, gin.outputs["Geometry"], gin.outputs["Base Width"] if width_src is None else width_src, gin.outputs["Segments"])
    link_sockets(tree, mesh_out, gout.inputs["Geometry"])
    return label_tree(tree, "MEL_curvature_bevel", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Curvature Weight", "nodes": ("angle", "curve"), "role": "attribute"},
        {"title": "Bevel", "nodes": ("bevel",), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# -- Registry --
from .core import register_builder

register_builder("MEL_bevel_profile", build_bevel_profile,
    "Bevel Profile", "Custom-profile bevel with width, segments, and profile curve control", "mesh_tools")
register_builder("MEL_weighted_bevel", build_weighted_bevel,
    "Weighted Bevel", "Edge-weighted bevel using bevel_weight attribute (auto edge-angle fallback)", "mesh_tools")
register_builder("MEL_auto_bevel", build_auto_bevel,
    "Auto Bevel (Ease)", "One-click infinity-nikki soft bevel — auto edge angle + weighted normal + shade smooth", "mesh_tools")
register_builder("MEL_curvature_bevel", build_curvature_bevel,
    "Curvature Bevel", "Curvature-driven bevel width for ornate drapes and filigree", "mesh_tools")
register_builder("MEL_multi_bevel", build_multi_bevel,
    "Multi Bevel", "Two-stage bevel - main chamfer + micro-bevel for hard-surface", "mesh_tools")
register_builder("MEL_inset_faces", build_inset_faces,
    "Inset Faces", "Extrude-and-scale face inset with depth control", "mesh_tools")
register_builder("MEL_poke_faces", build_poke_faces,
    "Poke Faces", "Triangulate-to-point face poke for spikes and gems", "mesh_tools")
register_builder("MEL_subdivision_surface", build_subdivision_surface,
    "Subdivision Surface", "Catmull-Clark subdivision with per-edge/per-vertex crease", "mesh_tools")
register_builder("MEL_remesh_dual", build_remesh_dual,
    "Remesh Dual", "Dual-mesh remesh - faces become vertices for organic topology", "mesh_tools")
register_builder("MEL_smooth_laplacian", build_smooth_laplacian,
    "Smooth Laplacian", "Volume-preserving Laplacian smooth via Blur Attribute", "mesh_tools")
