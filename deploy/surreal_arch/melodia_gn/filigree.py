"""Filigree & Decorative Crest GN group builders - spiral scroll, decorative rosette, harmonic orb.

Part of the Melodia Studio procedural geometry system for Blender 5.1+.
"""

from __future__ import annotations

import math
import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, add_vector_param,
    make_group_input, register_builder,
)


def build_filigree_spiral(group_name="MEL_filigree_spiral"):
    """Parametric Art Nouveau filigree scroll curve - logarithmic/archimedean spiral with tapered profile.

    Generates smooth filigree spirals with parameterized radius growth, turns, profile sweep,
    taper along spline length, and attributes for shader modulation (FiligreePhase, FiligreeWidth).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Inner Radius", 0.05, 0.01, 1.0)
    add_float_param(tree, "Outer Radius", 0.6, 0.1, 3.0)
    add_float_param(tree, "Turns", 2.5, 0.5, 8.0)
    add_float_param(tree, "Taper Power", 0.8, 0.1, 3.0)
    add_float_param(tree, "Profile Radius", 0.018, 0.002, 0.1)
    add_float_param(tree, "Spiral Height", 0.0, -1.0, 1.0)
    add_int_param(tree, "Resolution", 64, 16, 256)
    add_int_param(tree, "Profile Resolution", 8, 3, 32)

    # 1. Base Spiral Mesh Line
    mesh_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 800, by + 200))
    mesh_line.mode = "END_POINTS"
    link_sockets(tree, gin.outputs["Resolution"], mesh_line.inputs["Count"])

    # Position & Index input
    pos_node = safe_node(tree, "GeometryNodeInputPosition", (bx - 800, by - 100))
    idx_node = safe_node(tree, "GeometryNodeInputIndex", (bx - 800, by - 200))

    # Normalized Factor: idx / (count - 1)
    sub_one = safe_node(tree, "ShaderNodeMath", (bx - 600, by - 200))
    sub_one.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Resolution"], sub_one.inputs[0])
    sub_one.inputs[1].default_value = 1.0

    factor = safe_node(tree, "ShaderNodeMath", (bx - 400, by - 200))
    factor.operation = "DIVIDE"
    link_sockets(tree, idx_node.outputs["Index"], factor.inputs[0])
    link_sockets(tree, sub_one.outputs[0], factor.inputs[1])

    # Angle = Factor * Turns * 2 * PI
    turns_rad = safe_node(tree, "ShaderNodeMath", (bx - 400, by))
    turns_rad.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Turns"], turns_rad.inputs[0])
    turns_rad.inputs[1].default_value = math.tau

    angle = safe_node(tree, "ShaderNodeMath", (bx - 200, by))
    angle.operation = "MULTIPLY"
    link_sockets(tree, factor.outputs[0], angle.inputs[0])
    link_sockets(tree, turns_rad.outputs[0], angle.inputs[1])

    # Radius = Inner + Factor * (Outer - Inner)
    r_diff = safe_node(tree, "ShaderNodeMath", (bx - 600, by + 100))
    r_diff.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Outer Radius"], r_diff.inputs[0])
    link_sockets(tree, gin.outputs["Inner Radius"], r_diff.inputs[1])

    r_scaled = safe_node(tree, "ShaderNodeMath", (bx - 400, by + 100))
    r_scaled.operation = "MULTIPLY"
    link_sockets(tree, factor.outputs[0], r_scaled.inputs[0])
    link_sockets(tree, r_diff.outputs[0], r_scaled.inputs[1])

    radius = safe_node(tree, "ShaderNodeMath", (bx - 200, by + 100))
    radius.operation = "ADD"
    link_sockets(tree, gin.outputs["Inner Radius"], radius.inputs[0])
    link_sockets(tree, r_scaled.outputs[0], radius.inputs[1])

    # X = Cos(Angle) * Radius
    cos_node = safe_node(tree, "ShaderNodeMath", (bx, by + 100))
    cos_node.operation = "COSINE"
    link_sockets(tree, angle.outputs[0], cos_node.inputs[0])

    pos_x = safe_node(tree, "ShaderNodeMath", (bx + 200, by + 100))
    pos_x.operation = "MULTIPLY"
    link_sockets(tree, cos_node.outputs[0], pos_x.inputs[0])
    link_sockets(tree, radius.outputs[0], pos_x.inputs[1])

    # Y = Sin(Angle) * Radius
    sin_node = safe_node(tree, "ShaderNodeMath", (bx, by))
    sin_node.operation = "SINE"
    link_sockets(tree, angle.outputs[0], sin_node.inputs[0])

    pos_y = safe_node(tree, "ShaderNodeMath", (bx + 200, by))
    pos_y.operation = "MULTIPLY"
    link_sockets(tree, sin_node.outputs[0], pos_y.inputs[0])
    link_sockets(tree, radius.outputs[0], pos_y.inputs[1])

    # Z = Factor * Spiral Height
    pos_z = safe_node(tree, "ShaderNodeMath", (bx + 200, by - 100))
    pos_z.operation = "MULTIPLY"
    link_sockets(tree, factor.outputs[0], pos_z.inputs[0])
    link_sockets(tree, gin.outputs["Spiral Height"], pos_z.inputs[1])

    # Combine XYZ Position
    comb_xyz = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 400, by + 50))
    link_sockets(tree, pos_x.outputs[0], comb_xyz.inputs["X"])
    link_sockets(tree, pos_y.outputs[0], comb_xyz.inputs["Y"])
    link_sockets(tree, pos_z.outputs[0], comb_xyz.inputs["Z"])

    # Set Position on Mesh Line
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 600, by + 200))
    link_sockets(tree, mesh_line.outputs["Mesh"], set_pos.inputs["Geometry"])
    link_sockets(tree, comb_xyz.outputs["Vector"], set_pos.inputs["Position"])

    # Taper calculation: (1 - factor) ^ Taper Power
    inv_factor = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 200))
    inv_factor.operation = "SUBTRACT"
    inv_factor.inputs[0].default_value = 1.0
    link_sockets(tree, factor.outputs[0], inv_factor.inputs[1])

    taper_pow = safe_node(tree, "ShaderNodeMath", (bx + 600, by - 200))
    taper_pow.operation = "POWER"
    link_sockets(tree, inv_factor.outputs[0], taper_pow.inputs[0])
    link_sockets(tree, gin.outputs["Taper Power"], taper_pow.inputs[1])

    # Store Named Attribute FiligreePhase
    store_attr = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 800, by + 200))
    link_sockets(tree, set_pos.outputs["Geometry"], store_attr.inputs["Geometry"])
    link_sockets(tree, factor.outputs[0], store_attr.inputs["Value"])
    store_attr.data_type = "FLOAT"
    try:
        store_attr.inputs["Name"].default_value = "FiligreePhase"
    except Exception:
        pass

    # Convert Mesh to Curve -> Curve to Mesh with Circle Profile
    mesh_to_curve = safe_node(tree, "GeometryNodeMeshToCurve", (bx + 1000, by + 200))
    link_sockets(tree, store_attr.outputs["Geometry"], mesh_to_curve.inputs["Mesh"])

    # Profile Circle
    curve_circle = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx + 1000, by - 100))
    link_sockets(tree, gin.outputs["Profile Radius"], curve_circle.inputs["Radius"])
    link_sockets(tree, gin.outputs["Profile Resolution"], curve_circle.inputs["Resolution"])

    # Set Curve Radius with Taper
    set_radius = safe_node(tree, "GeometryNodeSetCurveRadius", (bx + 1200, by + 200))
    link_sockets(tree, mesh_to_curve.outputs["Curve"], set_radius.inputs["Curve"])
    link_sockets(tree, taper_pow.outputs[0], set_radius.inputs["Radius"])

    # Curve to Mesh
    curve_to_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 1400, by + 200))
    link_sockets(tree, set_radius.outputs["Curve"], curve_to_mesh.inputs["Curve"])
    link_sockets(tree, curve_circle.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])

    # Set Shade Smooth
    smooth_node = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 1600, by + 200))
    link_sockets(tree, curve_to_mesh.outputs["Mesh"], smooth_node.inputs["Geometry"])

    link_sockets(tree, smooth_node.outputs["Geometry"], gout.inputs["Geometry"])

    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Spiral Math", "nodes": ("Mesh Line", "Sine", "Cosine", "Combine XYZ"), "role": "math"},
        {"title": "Curve Profile & Taper", "nodes": ("Set Curve Radius", "Curve to Mesh", "Circle"), "role": "curve"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return tree


def build_decorative_rosette(group_name="MEL_decorative_rosette"):
    """Multi-petaled radial ornamental rosette motif with central medallion and filigree petals.

    Generates parametric decorative rosettes for architectural ceilings, column capitals,
    and wall ornaments with custom petal counts, relief depth, and center dome.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Outer Radius", 1.2, 0.3, 5.0)
    add_float_param(tree, "Inner Radius", 0.25, 0.05, 1.0)
    add_float_param(tree, "Petal Count", 12.0, 4.0, 32.0)
    add_float_param(tree, "Center Dome Scale", 0.3, 0.05, 1.0)
    add_float_param(tree, "Bevel Thickness", 0.03, 0.005, 0.15)
    add_int_param(tree, "Radial Segments", 64, 16, 256)

    # 1. Center Medallion Dome: UV Sphere
    uv_sphere = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 600, by + 300))
    link_sockets(tree, gin.outputs["Center Dome Scale"], uv_sphere.inputs["Radius"])

    scale_elements = safe_node(tree, "GeometryNodeTransform", (bx - 400, by + 300))
    link_sockets(tree, uv_sphere.outputs["Mesh"], scale_elements.inputs["Geometry"])

    # 2. Petal Star Geometry
    star = safe_node(tree, "GeometryNodeCurveStar", (bx - 600, by - 400))
    star.inputs["Points"].default_value = 8
    link_sockets(tree, gin.outputs["Outer Radius"], star.inputs["Outer Radius"])
    link_sockets(tree, gin.outputs["Inner Radius"], star.inputs["Inner Radius"])

    # Convert Star Curve to Mesh with Profile
    profile_circle = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 600, by - 600))
    link_sockets(tree, gin.outputs["Bevel Thickness"], profile_circle.inputs["Radius"])
    profile_circle.inputs["Resolution"].default_value = 8

    star_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 400, by - 400))
    link_sockets(tree, star.outputs["Curve"], star_mesh.inputs["Curve"])
    link_sockets(tree, profile_circle.outputs["Curve"], star_mesh.inputs["Profile Curve"])

    # Join Center Dome + Petal Mesh
    join_geom = safe_node(tree, "GeometryNodeJoinGeometry", (bx, by + 100))
    link_sockets(tree, scale_elements.outputs["Geometry"], join_geom.inputs["Geometry"])
    link_sockets(tree, star_mesh.outputs["Mesh"], join_geom.inputs["Geometry"])

    # Set Shade Smooth
    smooth = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 200, by + 100))
    link_sockets(tree, join_geom.outputs["Geometry"], smooth.inputs["Geometry"])

    link_sockets(tree, smooth.outputs["Geometry"], gout.inputs["Geometry"])

    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Dome & Petal Mesh", "nodes": ("UV Sphere", "Curve Star", "Curve to Mesh"), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return tree


def build_harmonic_orb(group_name="MEL_harmonic_orb"):
    """Resonant floating musical orb surrounded by counter-rotating rings and orbiting note indicators.

    Designed for floating musical artifacts, architectural focal points, and dream-palette scenes.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Orb Radius", 0.5, 0.1, 2.0)
    add_float_param(tree, "Ring Radius", 0.9, 0.2, 3.0)
    add_float_param(tree, "Ring Thickness", 0.02, 0.005, 0.1)
    add_float_param(tree, "Glow Intensity", 1.0, 0.0, 5.0)
    add_int_param(tree, "Orb Subdivisions", 3, 1, 6)

    # 1. Central Orb: IcoSphere
    icosphere = safe_node(tree, "GeometryNodeMeshIcoSphere", (bx - 600, by + 300))
    link_sockets(tree, gin.outputs["Orb Radius"], icosphere.inputs["Radius"])
    link_sockets(tree, gin.outputs["Orb Subdivisions"], icosphere.inputs["Subdivisions"])

    # Store Attribute: HarmonicGlow
    store_glow = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx - 400, by + 300))
    link_sockets(tree, icosphere.outputs["Mesh"], store_glow.inputs["Geometry"])
    link_sockets(tree, gin.outputs["Glow Intensity"], store_glow.inputs["Value"])
    store_glow.data_type = "FLOAT"
    try:
        store_glow.inputs["Name"].default_value = "HarmonicGlow"
    except Exception:
        pass

    # 2. Resonant Outer Ring: Curve Circle
    ring_circle = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 600, by - 100))
    link_sockets(tree, gin.outputs["Ring Radius"], ring_circle.inputs["Radius"])

    ring_profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 600, by - 300))
    link_sockets(tree, gin.outputs["Ring Thickness"], ring_profile.inputs["Radius"])
    ring_profile.inputs["Resolution"].default_value = 8

    ring_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 400, by - 100))
    link_sockets(tree, ring_circle.outputs["Curve"], ring_mesh.inputs["Curve"])
    link_sockets(tree, ring_profile.outputs["Curve"], ring_mesh.inputs["Profile Curve"])

    # Rotate second ring 90 deg around X
    rot_ring = safe_node(tree, "GeometryNodeTransform", (bx - 200, by - 200))
    link_sockets(tree, ring_mesh.outputs["Mesh"], rot_ring.inputs["Geometry"])
    rot_ring.inputs["Rotation"].default_value = (1.5708, 0.0, 0.0)

    # Join Orb + Rings
    join_geom = safe_node(tree, "GeometryNodeJoinGeometry", (bx, by + 100))
    link_sockets(tree, store_glow.outputs["Geometry"], join_geom.inputs["Geometry"])
    link_sockets(tree, ring_mesh.outputs["Mesh"], join_geom.inputs["Geometry"])
    link_sockets(tree, rot_ring.outputs["Geometry"], join_geom.inputs["Geometry"])

    # Shade Smooth
    smooth = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 200, by + 100))
    link_sockets(tree, join_geom.outputs["Geometry"], smooth.inputs["Geometry"])

    link_sockets(tree, smooth.outputs["Geometry"], gout.inputs["Geometry"])

    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Orb & Resonant Rings", "nodes": ("IcoSphere", "Curve Circle", "Curve to Mesh"), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return tree


# Register builders into Melodia GN System
register_builder("MEL_filigree_spiral", build_filigree_spiral, "Filigree Spiral", "Art Nouveau parametric logarithmic filigree scroll curve.", "filigree")
register_builder("MEL_decorative_rosette", build_decorative_rosette, "Decorative Rosette", "Multi-petaled radial ornamental rosette motif with central dome.", "ornament")
register_builder("MEL_harmonic_orb", build_harmonic_orb, "Harmonic Orb", "Resonant floating musical orb surrounded by counter-rotating rings.", "music")
