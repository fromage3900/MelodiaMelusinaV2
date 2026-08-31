"""Faraway Mother GN builders V3 — 16 builders for the fabric-mountain Monolith.

Reuses existing material masters (MI_Master_Nikki_Landscape, MI_Master_Toon_Universal_Alpha).
No new materials. Pure GN geometry.

Builders (8 existing + 8 new):
  EXISTING:
    MEL_mother_head_silhouette — sculpted ridge with moonlit face profile
    MEL_mother_hair_cascade     — ribbon waterfall cascade for maternal hair
    MEL_mother_valley_depression — terrain depression with fog fill
    MEL_mother_fog_volume       — volumetric haze that implies distant mass
    MEL_mother_fabric_ridge     — fabric normal-mapped terrain ridge
    MEL_mother_shoulder_fold    — shoulder/chest fold terrain
    MEL_mother_heart_gate       — rhythm checkpoint gate
    MEL_mother_moonlight_rig    — lighting rig for moonlit key
  NEW (V3):
    MEL_mother_walkway_straight — straight fabric walkway
    MEL_mother_walkway_curved   — curved fabric walkway (90 degree arc)
    MEL_mother_frill_rock       — frill rock formation
    MEL_mother_frill_arch       — frill arch (walk-through)
    MEL_mother_lace_tree        — tree with lace canopy
    MEL_mother_pearl_bush       — bush with pearl-like berries
    MEL_mother_silk_vine        — vine with silk ribbon leaves
    MEL_mother_brocade_flower   — flower with brocade petals
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    add_vector_param, make_group_input, make_group_output, tree_input_names,
    register_builder,
)


# -----------------------------------------------------------------------------
# 9. MEL_mother_walkway_straight — straight fabric walkway
# -----------------------------------------------------------------------------

def build_mother_walkway_straight(group_name="MEL_mother_walkway_straight"):
    """Straight fabric walkway — a path of draped cloth.

    Inputs:
      Length, Width, Fold Depth, Fold Frequency, Tension
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    length_n = add_float_param(tree, "Length", 200.0, 10.0, 1000.0)
    width_n = add_float_param(tree, "Width", 20.0, 1.0, 100.0)
    fold_depth_n = add_float_param(tree, "Fold Depth", 0.5, 0.0, 5.0)
    fold_freq_n = add_float_param(tree, "Fold Frequency", 0.01, 0.001, 0.1)
    tension_n = add_float_param(tree, "Tension", 0.7, 0.0, 1.0)

    # Base grid
    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 400, by))
    link_sockets(tree, length_n, grid.inputs["Size X"])
    link_sockets(tree, width_n, grid.inputs["Size Y"])
    grid.inputs["Vertices X"].default_value = 64
    grid.inputs["Vertices Y"].default_value = 16

    # Position for fold calculation
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 400, by - 200))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 200, by - 200))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    # Fabric folds: abs(sin(x * fold_freq))^2 * fold_depth
    fold_freq = safe_node(tree, "ShaderNodeMath", (bx - 400, by - 300))
    fold_freq.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], fold_freq.inputs[0])
    link_sockets(tree, fold_freq_n, fold_freq.inputs[1])
    fold_sin = safe_node(tree, "ShaderNodeMath", (bx - 200, by - 300))
    fold_sin.operation = "SINE"
    link_sockets(tree, fold_freq.outputs["Value"], fold_sin.inputs[0])
    fold_abs = safe_node(tree, "ShaderNodeMath", (bx - 100, by - 300))
    fold_abs.operation = "ABSOLUTE"
    link_sockets(tree, fold_sin.outputs["Value"], fold_abs.inputs[0])
    fold_pow = safe_node(tree, "ShaderNodeMath", (bx, by - 300))
    fold_pow.operation = "POWER"
    link_sockets(tree, fold_abs.outputs["Value"], fold_pow.inputs[0])
    fold_pow.inputs[1].default_value = 2.0
    fold_mul = safe_node(tree, "ShaderNodeMath", (bx + 100, by - 300))
    fold_mul.operation = "MULTIPLY"
    link_sockets(tree, fold_pow.outputs["Value"], fold_mul.inputs[0])
    link_sockets(tree, fold_depth_n, fold_mul.inputs[1])

    # Tension sag: catenary-like curve along length
    tension_sag = safe_node(tree, "ShaderNodeMath", (bx + 200, by - 300))
    tension_sag.operation = "MULTIPLY"
    link_sockets(tree, tension_n, tension_sag.inputs[0])
    tension_sag.inputs[1].default_value = -0.3

    # Combine fold + sag
    z_combined = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 300))
    z_combined.operation = "ADD"
    link_sockets(tree, fold_mul.outputs["Value"], z_combined.inputs[0])
    link_sockets(tree, tension_sag.outputs["Value"], z_combined.inputs[1])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 500, by))
    link_sockets(tree, grid.outputs["Mesh"], set_pos.inputs["Geometry"])
    z_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 300, by - 100))
    z_vec.inputs["X"].default_value = 0.0
    z_vec.inputs["Y"].default_value = 0.0
    link_sockets(tree, z_combined.outputs["Value"], z_vec.inputs["Z"])
    link_sockets(tree, z_vec.outputs["Vector"], set_pos.inputs["Offset"])

    link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, "MEL_mother_walkway_straight", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Grid", "nodes": ("grid",), "role": "geometry"},
        {"title": "Folds", "nodes": ("fold_sin", "fold_pow", "tension_sag"), "role": "deform"},
        {"title": "Output", "nodes": ("set_pos", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 10. MEL_mother_walkway_curved — curved fabric walkway
# -----------------------------------------------------------------------------

def build_mother_walkway_curved(group_name="MEL_mother_walkway_curved"):
    """Curved fabric walkway — 90 degree arc.

    Inputs:
      Radius, Angle, Width, Fold Depth, Fold Frequency
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    radius_n = add_float_param(tree, "Radius", 200.0, 10.0, 1000.0)
    angle_n = add_float_param(tree, "Angle", 90.0, 10.0, 360.0)
    width_n = add_float_param(tree, "Width", 20.0, 1.0, 100.0)
    fold_depth_n = add_float_param(tree, "Fold Depth", 0.5, 0.0, 5.0)
    fold_freq_n = add_float_param(tree, "Fold Frequency", 0.01, 0.001, 0.1)

    # Arc curve
    arc = safe_node(tree, "GeometryNodeCurveArc", (bx - 400, by))
    link_sockets(tree, radius_n, arc.inputs["Radius"])
    arc.inputs["Resolution"].default_value = 64
    link_sockets(tree, angle_n, arc.inputs["Angle"])

    # Convert to mesh with width
    curve_to_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 200, by))
    link_sockets(tree, arc.outputs["Curve"], curve_to_mesh.inputs["Curve"])

    # Profile for width
    profile = safe_node(tree, "GeometryNodeCurvePrimitiveLine", (bx - 200, by - 200))
    link_sockets(tree, width_n, profile.inputs["Resolution"])

    # Folds along curve
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx, by - 200))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx + 200, by - 200))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    fold = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 200))
    fold.operation = "SINE"
    link_sockets(tree, sep.outputs["X"], fold.inputs[0])
    fold_mul = safe_node(tree, "ShaderNodeMath", (bx + 600, by - 200))
    fold_mul.operation = "MULTIPLY"
    link_sockets(tree, fold.outputs["Value"], fold_mul.inputs[0])
    link_sockets(tree, fold_depth_n, fold_mul.inputs[1])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 800, by))
    link_sockets(tree, curve_to_mesh.outputs["Mesh"], set_pos.inputs["Geometry"])
    z_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 600, by - 100))
    z_vec.inputs["X"].default_value = 0.0
    z_vec.inputs["Y"].default_value = 0.0
    link_sockets(tree, fold_mul.outputs["Value"], z_vec.inputs["Z"])
    link_sockets(tree, z_vec.outputs["Vector"], set_pos.inputs["Offset"])

    link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, "MEL_mother_walkway_curved", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Arc", "nodes": ("arc", "curve_to_mesh"), "role": "curve"},
        {"title": "Folds", "nodes": ("fold", "set_pos"), "role": "deform"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 11. MEL_mother_frill_rock — frill rock formation
# -----------------------------------------------------------------------------

def build_mother_frill_rock(group_name="MEL_mother_frill_rock"):
    """Frill rock formation — rock that is actually frozen fabric.

    Inputs:
      Height, Frill Count, Frill Depth, Base Radius, Sharpness
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    height_n = add_float_param(tree, "Height", 80.0, 5.0, 200.0)
    frill_count_n = add_int_param(tree, "Frill Count", 12, 3, 48)
    frill_depth_n = add_float_param(tree, "Frill Depth", 2.0, 0.1, 10.0)
    base_radius_n = add_float_param(tree, "Base Radius", 10.0, 1.0, 50.0)
    sharpness_n = add_float_param(tree, "Sharpness", 2.0, 0.5, 8.0)

    # Base cone (rock shape)
    cone = safe_node(tree, "GeometryNodeMeshCone", (bx - 400, by))
    link_sockets(tree, base_radius_n, cone.inputs["Radius Bottom"])
    cone.inputs["Radius Top"].default_value = 0.5
    link_sockets(tree, height_n, cone.inputs["Depth"])
    cone.inputs["Vertices"].default_value = 32

    # Frill displacement
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 400, by - 200))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 200, by - 200))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    # Angular position for frills
    angle = safe_node(tree, "ShaderNodeMath", (bx - 400, by - 300))
    angle.operation = "ARCTANGENT"
    link_sockets(tree, sep.outputs["Y"], angle.inputs[0])
    link_sockets(tree, sep.outputs["X"], angle.inputs[1])

    # Frill pattern: abs(sin(angle * frill_count))^sharpness
    frill_freq = safe_node(tree, "ShaderNodeMath", (bx - 200, by - 300))
    frill_freq.operation = "MULTIPLY"
    link_sockets(tree, angle.outputs["Value"], frill_freq.inputs[0])
    link_sockets(tree, frill_count_n, frill_freq.inputs[1])
    frill_sin = safe_node(tree, "ShaderNodeMath", (bx - 100, by - 300))
    frill_sin.operation = "SINE"
    link_sockets(tree, frill_freq.outputs["Value"], frill_sin.inputs[0])
    frill_abs = safe_node(tree, "ShaderNodeMath", (bx, by - 300))
    frill_abs.operation = "ABSOLUTE"
    link_sockets(tree, frill_sin.outputs["Value"], frill_abs.inputs[0])
    frill_pow = safe_node(tree, "ShaderNodeMath", (bx + 100, by - 300))
    frill_pow.operation = "POWER"
    link_sockets(tree, frill_abs.outputs["Value"], frill_pow.inputs[0])
    link_sockets(tree, sharpness_n, frill_pow.inputs[1])
    frill_mul = safe_node(tree, "ShaderNodeMath", (bx + 200, by - 300))
    frill_mul.operation = "MULTIPLY"
    link_sockets(tree, frill_pow.outputs["Value"], frill_mul.inputs[0])
    link_sockets(tree, frill_depth_n, frill_mul.inputs[1])

    # Height taper
    height_taper = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 300))
    height_taper.operation = "SUBTRACT"
    height_taper.inputs[0].default_value = 1.0
    link_sockets(tree, sep.outputs["Z"], height_taper.inputs[1])
    height_norm = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 400))
    height_norm.operation = "DIVIDE"
    link_sockets(tree, height_taper.outputs["Value"], height_norm.inputs[0])
    link_sockets(tree, height_n, height_norm.inputs[1])

    # Combine
    frill_final = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 300))
    frill_final.operation = "MULTIPLY"
    link_sockets(tree, frill_mul.outputs["Value"], frill_final.inputs[0])
    link_sockets(tree, height_norm.outputs["Value"], frill_final.inputs[1])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 600, by))
    link_sockets(tree, cone.outputs["Mesh"], set_pos.inputs["Geometry"])
    offset_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 400, by - 100))
    link_sockets(tree, frill_final.outputs["Value"], offset_vec.inputs["X"])
    offset_vec.inputs["Y"].default_value = 0.0
    offset_vec.inputs["Z"].default_value = 0.0
    link_sockets(tree, offset_vec.outputs["Vector"], set_pos.inputs["Offset"])

    link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, "MEL_mother_frill_rock", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Cone", "nodes": ("cone",), "role": "geometry"},
        {"title": "Frills", "nodes": ("frill_sin", "frill_pow", "set_pos"), "role": "deform"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 12. MEL_mother_frill_arch — frill arch (walk-through)
# -----------------------------------------------------------------------------

def build_mother_frill_arch(group_name="MEL_mother_frill_arch"):
    """Frill arch — walk-through arch formation.

    Inputs:
      Span, Height, Thickness, Frill Count, Frill Depth
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    span_n = add_float_param(tree, "Span", 40.0, 5.0, 200.0)
    height_n = add_float_param(tree, "Height", 50.0, 5.0, 200.0)
    thickness_n = add_float_param(tree, "Thickness", 15.0, 1.0, 50.0)
    frill_count_n = add_int_param(tree, "Frill Count", 8, 2, 24)
    frill_depth_n = add_float_param(tree, "Frill Depth", 1.2, 0.1, 8.0)

    # Arch curve (semicircle)
    arc = safe_node(tree, "GeometryNodeCurveArc", (bx - 400, by))
    link_sockets(tree, span_n, arc.inputs["Radius"])
    arc.inputs["Angle"].default_value = 180.0
    arc.inputs["Resolution"].default_value = 48

    # Convert to mesh
    curve_to_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 200, by))
    link_sockets(tree, arc.outputs["Curve"], curve_to_mesh.inputs["Curve"])

    # Profile
    profile = safe_node(tree, "GeometryNodeCurvePrimitiveLine", (bx - 200, by - 200))
    link_sockets(tree, thickness_n, profile.inputs["Resolution"])

    # Frill displacement
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx, by - 200))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx + 200, by - 200))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    angle = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 200))
    angle.operation = "ARCTANGENT"
    link_sockets(tree, sep.outputs["Y"], angle.inputs[0])
    link_sockets(tree, sep.outputs["X"], angle.inputs[1])

    frill = safe_node(tree, "ShaderNodeMath", (bx + 600, by - 200))
    frill.operation = "SINE"
    link_sockets(tree, angle.outputs["Value"], frill.inputs[0])
    frill_abs = safe_node(tree, "ShaderNodeMath", (bx + 800, by - 200))
    frill_abs.operation = "ABSOLUTE"
    link_sockets(tree, frill.outputs["Value"], frill_abs.inputs[0])
    frill_mul = safe_node(tree, "ShaderNodeMath", (bx + 1000, by - 200))
    frill_mul.operation = "MULTIPLY"
    link_sockets(tree, frill_abs.outputs["Value"], frill_mul.inputs[0])
    link_sockets(tree, frill_depth_n, frill_mul.inputs[1])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 1200, by))
    link_sockets(tree, curve_to_mesh.outputs["Mesh"], set_pos.inputs["Geometry"])
    offset_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 1000, by - 100))
    offset_vec.inputs["X"].default_value = 0.0
    link_sockets(tree, frill_mul.outputs["Value"], offset_vec.inputs["Y"])
    offset_vec.inputs["Z"].default_value = 0.0
    link_sockets(tree, offset_vec.outputs["Vector"], set_pos.inputs["Offset"])

    link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, "MEL_mother_frill_arch", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Arch", "nodes": ("arc", "curve_to_mesh"), "role": "curve"},
        {"title": "Frills", "nodes": ("frill", "set_pos"), "role": "deform"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 13. MEL_mother_lace_tree — tree with lace canopy
# -----------------------------------------------------------------------------

def build_mother_lace_tree(group_name="MEL_mother_lace_tree"):
    """Tree with lace canopy — foliage-fabric bridge.

    Inputs:
      Height, Canopy Size, Lace Density, Trunk Radius
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    height_n = add_float_param(tree, "Height", 50.0, 5.0, 200.0)
    canopy_size_n = add_float_param(tree, "Canopy Size", 30.0, 5.0, 100.0)
    lace_density_n = add_float_param(tree, "Lace Density", 0.3, 0.0, 1.0)
    trunk_radius_n = add_float_param(tree, "Trunk Radius", 1.5, 0.1, 10.0)

    # Trunk (cylinder)
    trunk = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 400, by))
    link_sockets(tree, trunk_radius_n, trunk.inputs["Radius"])
    link_sockets(tree, height_n, trunk.inputs["Depth"])
    trunk.inputs["Vertices"].default_value = 16

    # Canopy (sphere)
    canopy = safe_node(tree, "GeometryNodeMeshIcoSphere", (bx - 400, by - 200))
    link_sockets(tree, canopy_size_n, canopy.inputs["Radius"])
    canopy.inputs["Subdivisions"].default_value = 3

    # Position canopy at top of trunk
    canopy_pos = safe_node(tree, "GeometryNodeTransform", (bx - 200, by - 200))
    link_sockets(tree, canopy.outputs["Mesh"], canopy_pos.inputs["Geometry"])
    canopy_offset = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 400, by - 300))
    canopy_offset.inputs["X"].default_value = 0.0
    canopy_offset.inputs["Y"].default_value = 0.0
    link_sockets(tree, height_n, canopy_offset.inputs["Z"])
    link_sockets(tree, canopy_offset.outputs["Vector"], canopy_pos.inputs["Translation"])

    # Lace pattern (SDF-like using noise)
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx, by - 200))
    noise = safe_node(tree, "ShaderNodeTexNoise", (bx + 200, by - 200))
    link_sockets(tree, pos.outputs["Position"], noise.inputs["Vector"])
    noise.inputs["Scale"].default_value = 5.0
    noise.inputs["Detail"].default_value = 4.0

    # Threshold for lace cutout
    lace_threshold = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 200))
    lace_threshold.operation = "GREATER_THAN"
    link_sockets(tree, noise.outputs["Fac"], lace_threshold.inputs[0])
    link_sockets(tree, lace_density_n, lace_threshold.inputs[1])

    # Join trunk + canopy
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 600, by))
    link_sockets(tree, trunk.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, canopy_pos.outputs["Geometry"], join.inputs["Geometry"])

    link_sockets(tree, join.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, "MEL_mother_lace_tree", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Trunk", "nodes": ("trunk",), "role": "geometry"},
        {"title": "Canopy", "nodes": ("canopy", "canopy_pos"), "role": "geometry"},
        {"title": "Output", "nodes": ("join", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 14. MEL_mother_pearl_bush — bush with pearl-like berries
# -----------------------------------------------------------------------------

def build_mother_pearl_bush(group_name="MEL_mother_pearl_bush"):
    """Bush with pearl-like berries — foliage-jewel bridge.

    Inputs:
      Size, Pearl Count, Pearl Density, Bush Height
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    size_n = add_float_param(tree, "Size", 20.0, 1.0, 100.0)
    pearl_count_n = add_int_param(tree, "Pearl Count", 50, 5, 500)
    pearl_density_n = add_float_param(tree, "Pearl Density", 0.3, 0.0, 1.0)
    bush_height_n = add_float_param(tree, "Bush Height", 15.0, 1.0, 50.0)

    # Bush base (sphere)
    bush = safe_node(tree, "GeometryNodeMeshIcoSphere", (bx - 400, by))
    link_sockets(tree, size_n, bush.inputs["Radius"])
    bush.inputs["Subdivisions"].default_value = 2

    # Flatten vertically
    bush_scale = safe_node(tree, "GeometryNodeTransform", (bx - 200, by))
    link_sockets(tree, bush.outputs["Mesh"], bush_scale.inputs["Geometry"])
    bush_scale.inputs["Scale"].default_value = (1.0, 1.0, 0.5)

    # Pearl instances on points
    points = safe_node(tree, "GeometryNodeDistributePointsOnFaces", (bx, by))
    link_sockets(tree, bush_scale.outputs["Mesh"], points.inputs["Mesh"])
    link_sockets(tree, pearl_count_n, points.inputs["Count"])

    # Pearl geometry (small sphere)
    pearl = safe_node(tree, "GeometryNodeMeshIcoSphere", (bx, by - 200))
    pearl.inputs["Radius"].default_value = 0.3
    pearl.inputs["Subdivisions"].default_value = 1

    # Instance pearls on points
    instance = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 200, by))
    link_sockets(tree, points.outputs["Points"], instance.inputs["Points"])
    link_sockets(tree, pearl.outputs["Mesh"], instance.inputs["Instance"])

    # Realize instances
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 400, by))
    link_sockets(tree, instance.outputs["Instances"], realize.inputs["Geometry"])

    link_sockets(tree, realize.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, "MEL_mother_pearl_bush", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bush", "nodes": ("bush", "bush_scale"), "role": "geometry"},
        {"title": "Pearls", "nodes": ("points", "pearl", "instance"), "role": "instance"},
        {"title": "Output", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 15. MEL_mother_silk_vine — vine with silk ribbon leaves
# -----------------------------------------------------------------------------

def build_mother_silk_vine(group_name="MEL_mother_silk_vine"):
    """Vine with silk ribbon leaves — foliage-fabric bridge.

    Inputs:
      Length, Sag, Ribbon Width, Leaf Count
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    length_n = add_float_param(tree, "Length", 100.0, 10.0, 500.0)
    sag_n = add_float_param(tree, "Sag", 20.0, 0.0, 100.0)
    ribbon_width_n = add_float_param(tree, "Ribbon Width", 1.0, 0.1, 10.0)
    leaf_count_n = add_int_param(tree, "Leaf Count", 20, 2, 100)

    # Vine curve (catenary-like)
    curve_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by))
    curve_line.inputs["Count"].default_value = 64
    curve_line.inputs["Offset"].default_value = (1.0, 0.0, 0.0)

    # Convert to curve
    mesh_to_curve = safe_node(tree, "GeometryNodeMeshToCurve", (bx - 200, by))
    link_sockets(tree, curve_line.outputs["Mesh"], mesh_to_curve.inputs["Mesh"])

    # Resample
    resample = safe_node(tree, "GeometryNodeResampleCurve", (bx, by))
    link_sockets(tree, mesh_to_curve.outputs["Curve"], resample.inputs["Curve"])
    resample.inputs["Count"].default_value = 64

    # Sag displacement
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx, by - 200))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx + 200, by - 200))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    # Catenary sag
    x_norm = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 200))
    x_norm.operation = "DIVIDE"
    link_sockets(tree, sep.outputs["X"], x_norm.inputs[0])
    link_sockets(tree, length_n, x_norm.inputs[1])
    sag_curve = safe_node(tree, "ShaderNodeMath", (bx + 600, by - 200))
    sag_curve.operation = "POWER"
    link_sockets(tree, x_norm.outputs["Value"], sag_curve.inputs[0])
    sag_curve.inputs[1].default_value = 2.0
    sag_mul = safe_node(tree, "ShaderNodeMath", (bx + 800, by - 200))
    sag_mul.operation = "MULTIPLY"
    link_sockets(tree, sag_curve.outputs["Value"], sag_mul.inputs[0])
    link_sockets(tree, sag_n, sag_mul.inputs[1])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 1000, by))
    link_sockets(tree, resample.outputs["Curve"], set_pos.inputs["Geometry"])
    z_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 800, by - 100))
    z_vec.inputs["X"].default_value = 0.0
    z_vec.inputs["Y"].default_value = 0.0
    link_sockets(tree, sag_mul.outputs["Value"], z_vec.inputs["Z"])
    link_sockets(tree, z_vec.outputs["Vector"], set_pos.inputs["Offset"])

    # Ribbon profile
    curve_to_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 1200, by))
    link_sockets(tree, set_pos.outputs["Geometry"], curve_to_mesh.inputs["Curve"])
    profile = safe_node(tree, "GeometryNodeCurvePrimitiveLine", (bx + 1200, by - 200))
    link_sockets(tree, ribbon_width_n, profile.inputs["Resolution"])

    link_sockets(tree, curve_to_mesh.outputs["Mesh"], gout.inputs["Geometry"])

    return label_tree(tree, "MEL_mother_silk_vine", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Vine", "nodes": ("curve_line", "resample"), "role": "curve"},
        {"title": "Sag", "nodes": ("sag_curve", "set_pos"), "role": "deform"},
        {"title": "Output", "nodes": ("curve_to_mesh", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 16. MEL_mother_brocade_flower — flower with brocade petals
# -----------------------------------------------------------------------------

def build_mother_brocade_flower(group_name="MEL_mother_brocade_flower"):
    """Flower with brocade petals — foliage-fabric bridge.

    Inputs:
      Petal Count, Size, Curl, Height
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    petal_count_n = add_int_param(tree, "Petal Count", 8, 3, 24)
    size_n = add_float_param(tree, "Size", 5.0, 0.5, 30.0)
    curl_n = add_float_param(tree, "Curl", 0.3, 0.0, 1.0)
    height_n = add_float_param(tree, "Height", 10.0, 1.0, 50.0)

    # Stem
    stem = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 400, by))
    stem.inputs["Radius"].default_value = 0.2
    link_sockets(tree, height_n, stem.inputs["Depth"])
    stem.inputs["Vertices"].default_value = 8

    # Petal base (cone)
    petal = safe_node(tree, "GeometryNodeMeshCone", (bx - 400, by - 200))
    petal.inputs["Radius Bottom"].default_value = 0.5
    petal.inputs["Radius Top"].default_value = 0.0
    link_sockets(tree, size_n, petal.inputs["Depth"])
    petal.inputs["Vertices"].default_value = 8

    # Instance petals around center
    points = safe_node(tree, "GeometryNodeDistributePointsOnFaces", (bx - 200, by - 200))
    link_sockets(tree, petal.outputs["Mesh"], points.inputs["Mesh"])
    link_sockets(tree, petal_count_n, points.inputs["Count"])

    instance = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx, by - 200))
    link_sockets(tree, points.outputs["Points"], instance.inputs["Points"])
    link_sockets(tree, petal.outputs["Mesh"], instance.inputs["Instance"])

    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 200, by - 200))
    link_sockets(tree, instance.outputs["Instances"], realize.inputs["Geometry"])

    # Join stem + petals
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 400, by))
    link_sockets(tree, stem.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, realize.outputs["Geometry"], join.inputs["Geometry"])

    link_sockets(tree, join.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, "MEL_mother_brocade_flower", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Stem", "nodes": ("stem",), "role": "geometry"},
        {"title": "Petals", "nodes": ("petal", "points", "instance"), "role": "instance"},
        {"title": "Output", "nodes": ("join", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# Registry (V3 — all 16 builders)
# -----------------------------------------------------------------------------

register_builder("MEL_mother_walkway_straight", build_mother_walkway_straight,
    "Mother Walkway Straight",
    "Straight fabric walkway — a path of draped cloth",
    "mother")

register_builder("MEL_mother_walkway_curved", build_mother_walkway_curved,
    "Mother Walkway Curved",
    "Curved fabric walkway — 90 degree arc",
    "mother")

register_builder("MEL_mother_frill_rock", build_mother_frill_rock,
    "Mother Frill Rock",
    "Frill rock formation — rock that is actually frozen fabric",
    "mother")

register_builder("MEL_mother_frill_arch", build_mother_frill_arch,
    "Mother Frill Arch",
    "Frill arch — walk-through arch formation",
    "mother")

register_builder("MEL_mother_lace_tree", build_mother_lace_tree,
    "Mother Lace Tree",
    "Tree with lace canopy — foliage-fabric bridge",
    "mother")

register_builder("MEL_mother_pearl_bush", build_mother_pearl_bush,
    "Mother Pearl Bush",
    "Bush with pearl-like berries — foliage-jewel bridge",
    "mother")

register_builder("MEL_mother_silk_vine", build_mother_silk_vine,
    "Mother Silk Vine",
    "Vine with silk ribbon leaves — foliage-fabric bridge",
    "mother")

register_builder("MEL_mother_brocade_flower", build_mother_brocade_flower,
    "Mother Brocade Flower",
    "Flower with brocade petals — foliage-fabric bridge",
    "mother")
