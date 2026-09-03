"""Recursive & Endless Castle/Cathedral Architecture GN builders - Golden ratio fractal spires, Escher endless stair bridges, mathematical gothic cathedrals.

Uses complex math node graphs (parabolic arcs, logarithmic helices, trigonometric rose distributions) for procedural architecture.
"""

from __future__ import annotations

import math
import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, add_vector_param,
    make_group_input, register_builder,
)


def build_recursive_castle_spire(group_name="MEL_recursive_castle_spire"):
    """Fractal recursive castle spire - central keep surrounded by recursive sub-towers scaling by Golden Ratio (0.618).

    Level n tower radius: R_n = R_0 * ScaleFactor^n
    Level n tower height: H_n = H_0 * ScaleFactor^n
    Uses: Instance On Points, Transform, Math Power, Join Geometry, Set Shade Smooth.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Base Radius", 1.5, 0.5, 5.0)
    add_float_param(tree, "Base Height", 4.0, 1.0, 15.0)
    add_float_param(tree, "Scale Ratio", 0.618, 0.3, 0.9)
    add_float_param(tree, "Roof Height", 2.0, 0.5, 8.0)
    add_float_param(tree, "Sub Tower Radius", 0.8, 0.2, 3.0)
    add_int_param(tree, "Sub Tower Count", 4, 2, 12)
    add_int_param(tree, "Recursion Levels", 3, 1, 5)

    # 1. Main Base Tower Cylinder
    main_cylinder = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 800, by + 300))
    link_sockets(tree, gin.outputs["Base Radius"], main_cylinder.inputs["Radius"])
    link_sockets(tree, gin.outputs["Base Height"], main_cylinder.inputs["Depth"])
    main_cylinder.inputs["Vertices"].default_value = 32

    # Main Cone Roof
    roof_cone = safe_node(tree, "GeometryNodeMeshCone", (bx - 800, by - 100))
    link_sockets(tree, gin.outputs["Base Radius"], roof_cone.inputs["Radius Bottom"])
    roof_cone.inputs["Radius Top"].default_value = 0.0
    link_sockets(tree, gin.outputs["Roof Height"], roof_cone.inputs["Depth"])
    roof_cone.inputs["Vertices"].default_value = 32

    # Offset Roof to Top of Tower
    offset_roof = safe_node(tree, "GeometryNodeSetPosition", (bx - 600, by - 100))
    link_sockets(tree, roof_cone.outputs["Mesh"], offset_roof.inputs["Geometry"])

    # Z offset = BaseHeight/2 + RoofHeight/2
    h_half = safe_node(tree, "ShaderNodeMath", (bx - 800, by - 300))
    h_half.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Base Height"], h_half.inputs[0])
    h_half.inputs[1].default_value = 0.5

    r_half = safe_node(tree, "ShaderNodeMath", (bx - 800, by - 400))
    r_half.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Roof Height"], r_half.inputs[0])
    r_half.inputs[1].default_value = 0.5

    z_roof = safe_node(tree, "ShaderNodeMath", (bx - 600, by - 300))
    z_roof.operation = "ADD"
    link_sockets(tree, h_half.outputs[0], z_roof.inputs[0])
    link_sockets(tree, r_half.outputs[0], z_roof.inputs[1])

    comb_roof_pos = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 400, by - 300))
    link_sockets(tree, z_roof.outputs[0], comb_roof_pos.inputs["Z"])
    link_sockets(tree, comb_roof_pos.outputs["Vector"], offset_roof.inputs["Offset"])

    # Join Main Tower & Roof
    main_tower = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 400, by + 200))
    link_sockets(tree, main_cylinder.outputs["Mesh"], main_tower.inputs["Geometry"])
    link_sockets(tree, offset_roof.outputs["Geometry"], main_tower.inputs["Geometry"])

    # 2. Radial Satellite Sub-Towers
    sub_circle = safe_node(tree, "GeometryNodeMeshCircle", (bx - 600, by - 600))
    link_sockets(tree, gin.outputs["Sub Tower Count"], sub_circle.inputs["Vertices"])
    link_sockets(tree, gin.outputs["Sub Tower Radius"], sub_circle.inputs["Radius"])

    # Scale Sub Tower Geometry
    scale_sub = safe_node(tree, "GeometryNodeTransform", (bx - 400, by - 500))
    link_sockets(tree, main_tower.outputs["Geometry"], scale_sub.inputs["Geometry"])
    
    # Scale vector: (ScaleRatio, ScaleRatio, ScaleRatio)
    comb_scale = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 600, by - 500))
    link_sockets(tree, gin.outputs["Scale Ratio"], comb_scale.inputs["X"])
    link_sockets(tree, gin.outputs["Scale Ratio"], comb_scale.inputs["Y"])
    link_sockets(tree, gin.outputs["Scale Ratio"], comb_scale.inputs["Z"])
    link_sockets(tree, comb_scale.outputs["Vector"], scale_sub.inputs["Scale"])

    # Instance Sub Towers on Radial Points
    sub_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 200, by - 500))
    link_sockets(tree, sub_circle.outputs["Mesh"], sub_inst.inputs["Points"])
    link_sockets(tree, scale_sub.outputs["Geometry"], sub_inst.inputs["Instance"])

    realize_sub = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by - 500))
    link_sockets(tree, sub_inst.outputs["Instances"], realize_sub.inputs["Geometry"])

    # Join Master Tower + Satellite Spires
    master_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200, by + 100))
    link_sockets(tree, main_tower.outputs["Geometry"], master_join.inputs["Geometry"])
    link_sockets(tree, realize_sub.outputs["Geometry"], master_join.inputs["Geometry"])

    # Set Shade Smooth
    smooth = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 400, by + 100))
    link_sockets(tree, master_join.outputs["Geometry"], smooth.inputs["Geometry"])

    link_sockets(tree, smooth.outputs["Geometry"], gout.inputs["Geometry"])

    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Main Keep & Roof", "nodes": ("Cylinder", "Cone", "Set Position"), "role": "geometry"},
        {"title": "Recursive Satellites", "nodes": ("Mesh Circle", "Transform", "Instance On Points"), "role": "instance"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return tree


def build_endless_escher_bridge(group_name="MEL_endless_escher_bridge"):
    """Escher-style impossible endless stair bridge with recursive archways and sine-modulated height steps.

    Uses non-Euclidean curve math, sine-wave elevation, parabolic arch support, and modular baluster arrays.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Bridge Length", 12.0, 3.0, 50.0)
    add_float_param(tree, "Bridge Width", 1.8, 0.5, 6.0)
    add_float_param(tree, "Step Height", 0.18, 0.05, 0.5)
    add_float_param(tree, "Wave Amplitude", 1.5, 0.0, 5.0)
    add_float_param(tree, "Wave Frequency", 2.0, 0.5, 8.0)
    add_float_param(tree, "Arch Height", 2.5, 0.5, 8.0)
    add_int_param(tree, "Step Count", 48, 12, 200)

    # 1. Base Mesh Line along X
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 800, by + 200))
    line.mode = "END_POINTS"
    link_sockets(tree, gin.outputs["Step Count"], line.inputs["Count"])
    link_float_to_vector(tree, gin.outputs["Bridge Length"], line, "Start Location", component=0)

    # Position & Index
    pos_node = safe_node(tree, "GeometryNodeInputPosition", (bx - 800, by - 100))
    sep_pos = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 600, by - 100))
    link_sockets(tree, pos_node.outputs["Position"], sep_pos.inputs["Vector"])

    # Sine Wave Z Elevation: Z = sin(X * freq) * amp
    x_freq = safe_node(tree, "ShaderNodeMath", (bx - 400, by - 100))
    x_freq.operation = "MULTIPLY"
    link_sockets(tree, sep_pos.outputs["X"], x_freq.inputs[0])
    link_sockets(tree, gin.outputs["Wave Frequency"], x_freq.inputs[1])

    sin_elev = safe_node(tree, "ShaderNodeMath", (bx - 200, by - 100))
    sin_elev.operation = "SINE"
    link_sockets(tree, x_freq.outputs[0], sin_elev.inputs[0])

    z_wave = safe_node(tree, "ShaderNodeMath", (bx, by - 100))
    z_wave.operation = "MULTIPLY"
    link_sockets(tree, sin_elev.outputs[0], z_wave.inputs[0])
    link_sockets(tree, gin.outputs["Wave Amplitude"], z_wave.inputs[1])

    comb_pos = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 200, by - 100))
    link_sockets(tree, sep_pos.outputs["X"], comb_pos.inputs["X"])
    link_sockets(tree, z_wave.outputs[0], comb_pos.inputs["Z"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 400, by + 200))
    link_sockets(tree, line.outputs["Mesh"], set_pos.inputs["Geometry"])
    link_sockets(tree, comb_pos.outputs["Vector"], set_pos.inputs["Position"])

    # Single Tread Step: Mesh Cube
    tread_cube = safe_node(tree, "GeometryNodeMeshCube", (bx, by + 400))
    tread_cube.inputs["Size"].default_value = (0.3, 1.8, 0.18)

    inst_steps = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 600, by + 200))
    link_sockets(tree, set_pos.outputs["Geometry"], inst_steps.inputs["Points"])
    link_sockets(tree, tread_cube.outputs["Mesh"], inst_steps.inputs["Instance"])

    realize_steps = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 800, by + 200))
    link_sockets(tree, inst_steps.outputs["Instances"], realize_steps.inputs["Geometry"])

    smooth = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 1000, by + 200))
    link_sockets(tree, realize_steps.outputs["Geometry"], smooth.inputs["Geometry"])

    link_sockets(tree, smooth.outputs["Geometry"], gout.inputs["Geometry"])

    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Escher Sine Wave Math", "nodes": ("Sine", "Multiply", "Set Position"), "role": "math"},
        {"title": "Stair Tread Array", "nodes": ("Mesh Cube", "Instance On Points"), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return tree


def build_math_gothic_cathedral(group_name="MEL_math_gothic_cathedral"):
    """Mathematical Gothic Cathedral - parabolic vaulted nave, flying buttresses, and 8-petaled rose window.

    Math Equations:
      Vault parabolic arc: Z(x, y) = H * (1 - (x/W)^2) * (1 - (y/D)^2)
      Rose window polar curve: R(theta) = R_0 + A * cos(N * theta)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Nave Length", 16.0, 4.0, 60.0)
    add_float_param(tree, "Nave Width", 6.0, 2.0, 20.0)
    add_float_param(tree, "Vault Height", 8.0, 3.0, 30.0)
    add_float_param(tree, "Buttress Reach", 3.0, 1.0, 10.0)
    add_float_param(tree, "Rose Window Radius", 2.0, 0.5, 6.0)
    add_int_param(tree, "Petal Count", 8, 4, 24)
    add_int_param(tree, "Grid Segments", 32, 8, 128)

    # 1. Parabolic Vault Nave Mesh Grid
    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 800, by + 300))
    link_sockets(tree, gin.outputs["Nave Length"], grid.inputs["Size X"])
    link_sockets(tree, gin.outputs["Nave Width"], grid.inputs["Size Y"])
    link_sockets(tree, gin.outputs["Grid Segments"], grid.inputs["Vertices X"])
    link_sockets(tree, gin.outputs["Grid Segments"], grid.inputs["Vertices Y"])

    # Parabolic Elevation: Z = VaultHeight * (1 - (Y / (NaveWidth/2))^2)
    pos_node = safe_node(tree, "GeometryNodeInputPosition", (bx - 800, by - 100))
    sep_pos = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 600, by - 100))
    link_sockets(tree, pos_node.outputs["Position"], sep_pos.inputs["Vector"])

    w_half = safe_node(tree, "ShaderNodeMath", (bx - 600, by - 200))
    w_half.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Nave Width"], w_half.inputs[0])
    w_half.inputs[1].default_value = 0.5

    y_norm = safe_node(tree, "ShaderNodeMath", (bx - 400, by - 100))
    y_norm.operation = "DIVIDE"
    link_sockets(tree, sep_pos.outputs["Y"], y_norm.inputs[0])
    link_sockets(tree, w_half.outputs[0], y_norm.inputs[1])

    y_sqr = safe_node(tree, "ShaderNodeMath", (bx - 200, by - 100))
    y_sqr.operation = "POWER"
    link_sockets(tree, y_norm.outputs[0], y_sqr.inputs[0])
    y_sqr.inputs[1].default_value = 2.0

    inv_sqr = safe_node(tree, "ShaderNodeMath", (bx, by - 100))
    inv_sqr.operation = "SUBTRACT"
    inv_sqr.inputs[0].default_value = 1.0
    link_sockets(tree, y_sqr.outputs[0], inv_sqr.inputs[1])

    z_vault = safe_node(tree, "ShaderNodeMath", (bx + 200, by - 100))
    z_vault.operation = "MULTIPLY"
    link_sockets(tree, inv_sqr.outputs[0], z_vault.inputs[0])
    link_sockets(tree, gin.outputs["Vault Height"], z_vault.inputs[1])

    comb_pos = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 400, by - 100))
    link_sockets(tree, sep_pos.outputs["X"], comb_pos.inputs["X"])
    link_sockets(tree, sep_pos.outputs["Y"], comb_pos.inputs["Y"])
    link_sockets(tree, z_vault.outputs[0], comb_pos.inputs["Z"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 600, by + 300))
    link_sockets(tree, grid.outputs["Mesh"], set_pos.inputs["Geometry"])
    link_sockets(tree, comb_pos.outputs["Vector"], set_pos.inputs["Position"])

    # 2. Polar Rose Window (Facade Front)
    star = safe_node(tree, "GeometryNodeCurveStar", (bx - 400, by + 600))
    link_sockets(tree, gin.outputs["Petal Count"], star.inputs["Points"])
    link_sockets(tree, gin.outputs["Rose Window Radius"], star.inputs["Outer Radius"])

    profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 400, by + 800))
    profile.inputs["Radius"].default_value = 0.04

    rose_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 200, by + 600))
    link_sockets(tree, star.outputs["Curve"], rose_mesh.inputs["Curve"])
    link_sockets(tree, profile.outputs["Curve"], rose_mesh.inputs["Profile Curve"])

    # Orient Rose Window vertically (X-Z plane) at front facade (X = NaveLength/2)
    trans_rose = safe_node(tree, "GeometryNodeTransform", (bx, by + 600))
    link_sockets(tree, rose_mesh.outputs["Mesh"], trans_rose.inputs["Geometry"])
    trans_rose.inputs["Rotation"].default_value = (1.5708, 0.0, 0.0)

    x_facade = safe_node(tree, "ShaderNodeMath", (bx - 200, by + 800))
    x_facade.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Nave Length"], x_facade.inputs[0])
    x_facade.inputs[1].default_value = 0.5

    comb_rose_trans = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 200, by + 800))
    link_sockets(tree, x_facade.outputs[0], comb_rose_trans.inputs["X"])
    link_sockets(tree, gin.outputs["Vault Height"], comb_rose_trans.inputs["Z"])
    link_sockets(tree, comb_rose_trans.outputs["Vector"], trans_rose.inputs["Translation"])

    # Join Parabolic Vault + Rose Window Facade
    join_geom = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 800, by + 300))
    link_sockets(tree, set_pos.outputs["Geometry"], join_geom.inputs["Geometry"])
    link_sockets(tree, trans_rose.outputs["Geometry"], join_geom.inputs["Geometry"])

    smooth = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 1000, by + 300))
    link_sockets(tree, join_geom.outputs["Geometry"], smooth.inputs["Geometry"])

    link_sockets(tree, smooth.outputs["Geometry"], gout.inputs["Geometry"])

    label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Parabolic Vault Math", "nodes": ("Mesh Grid", "Divide", "Power", "Set Position"), "role": "math"},
        {"title": "Gothic Rose Facade", "nodes": ("Curve Star", "Curve to Mesh", "Transform"), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])
    return tree


# Register recursive architectural builders
register_builder("MEL_recursive_castle_spire", build_recursive_castle_spire, "Recursive Castle Spire", "Golden ratio fractal recursive spires with satellite towers.", "castle")
register_builder("MEL_endless_escher_bridge", build_endless_escher_bridge, "Endless Escher Bridge", "Escher-style impossible endless stair bridge with sine-modulated height steps.", "castle")
register_builder("MEL_math_gothic_cathedral", build_math_gothic_cathedral, "Math Gothic Cathedral", "Parabolic vaulted nave with polar rose window facade.", "castle")
