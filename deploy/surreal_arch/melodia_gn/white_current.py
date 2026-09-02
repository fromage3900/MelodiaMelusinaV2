"""The White Current GN builders — 6 builders for the white-seam Monolith.

Reuses existing material masters. No new materials. Pure GN geometry.

Builders:
  MEL_white_seam_spline   — white seam that follows a water spline
  MEL_eel_silhouette      — pale eel/oarfish silhouette beneath surface
  MEL_water_network       — connected water network spline system
  MEL_moonlit_surf        — moonlit water surface with white seam reflection
  MEL_white_haze_volume   — volumetric haze implying distant mass
  MEL_current_marker      — flow-direction arrows tracing the eel's path
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
# 1. MEL_white_seam_spline — white seam that follows a water spline
# -----------------------------------------------------------------------------

def build_white_seam_spline(group_name="MEL_white_seam_spline"):
    """White seam that follows a water spline — the visible trace of the eel.

    Inputs:
      Width, Flow Speed, Seam Intensity, Turbulence, Spline Resolution
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    width_n = add_float_param(tree, "Width", 0.15, 0.01, 2.0)
    flow_n = add_float_param(tree, "Flow Speed", 1.0, 0.0, 10.0)
    intensity_n = add_float_param(tree, "Seam Intensity", 1.5, 0.0, 5.0)
    turbulence_n = add_float_param(tree, "Turbulence", 0.3, 0.0, 2.0)
    res_n = add_int_param(tree, "Spline Resolution", 64, 8, 256)

    # Base spline: mesh line
    spline = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by))
    link_sockets(tree, res_n, spline.inputs["Count"])
    spline.inputs["Offset"].default_value = (1.0, 0.0, 0.0)

    # Convert to curve
    curve = safe_node(tree, "GeometryNodeMeshToCurve", (bx - 200, by))
    link_sockets(tree, spline.outputs["Mesh"], curve.inputs["Mesh"])

    # Resample for smoothness
    resample = safe_node(tree, "GeometryNodeResampleCurve", (bx, by))
    link_sockets(tree, curve.outputs["Curve"], resample.inputs["Curve"])
    resample.inputs["Count"].default_value = 64

    # Set curve radius for seam width
    set_radius = safe_node(tree, "GeometryNodeSetCurveRadius", (bx + 200, by))
    link_sockets(tree, resample.outputs["Curve"], set_radius.inputs["Curve"])
    link_sockets(tree, width_n, set_radius.inputs["Radius"])

    # Turbulence: displace along normal
    noise = safe_node(tree, "ShaderNodeTexNoise", (bx + 200, by - 100))
    link_sockets(tree, turbulence_n, noise.inputs["Scale"])
    noise.inputs["Detail"].default_value = 3.0

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 400, by))
    link_sockets(tree, set_radius.outputs["Curve"], set_pos.inputs["Geometry"])
    disp_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 200, by - 200))
    link_float_to_vector(tree, noise.outputs["Fac"], disp_vec, "X", defaults=(0.0, 0.0, 0.0))
    link_sockets(tree, disp_vec.outputs["Vector"], set_pos.inputs["Offset"])

    # Store seam intensity attribute
    store_intensity = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 600, by))
    store_intensity.data_type = "FLOAT"
    store_intensity.inputs["Name"].default_value = "seam_intensity"
    link_sockets(tree, intensity_n, store_intensity.inputs["Value"])
    link_sockets(tree, set_pos.outputs["Geometry"], store_intensity.inputs["Geometry"])

    # Store flow speed attribute
    store_flow = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 800, by))
    store_flow.data_type = "FLOAT"
    store_flow.inputs["Name"].default_value = "flow_speed"
    link_sockets(tree, flow_n, store_flow.inputs["Value"])
    link_sockets(tree, store_intensity.outputs["Geometry"], store_flow.inputs["Geometry"])

    # Curve to mesh
    profile = safe_node(tree, "GeometryNodeCurvePrimitiveLine", (bx + 400, by - 300))
    profile.inputs["Resolution"].default_value = 1
    profile_pos = safe_node(tree, "GeometryNodeTransform", (bx + 400, by - 380))
    link_sockets(tree, profile.outputs["Curve"], profile_pos.inputs["Geometry"])
    profile_pos.inputs["Scale"].default_value = (0.02, 0.005, 1.0)

    to_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 1000, by))
    link_sockets(tree, store_flow.outputs["Geometry"], to_mesh.inputs["Curve"])
    link_sockets(tree, profile_pos.outputs["Geometry"], to_mesh.inputs["Profile Curve"])
    link_sockets(tree, to_mesh.outputs["Mesh"], gout.inputs["Geometry"])

    color_node(spline, "curve")
    color_node(noise, "noise")
    color_node(to_mesh, "geometry")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Spline", "nodes": ("spline", "curve", "resample"), "role": "curve"},
        {"title": "Seam", "nodes": ("set_radius", "noise", "set_pos"), "role": "geometry"},
        {"title": "Output", "nodes": ("to_mesh", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 2. MEL_eel_silhouette — pale eel/oarfish silhouette beneath surface
# -----------------------------------------------------------------------------

def build_eel_silhouette(group_name="MEL_eel_silhouette"):
    """Pale eel/oarfish silhouette that moves beneath the water surface.

    Inputs:
      Length, Body Width, Fin Count, Glow Intensity, Translucency, Wave Phase
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    length_n = add_float_param(tree, "Length", 15.0, 1.0, 100.0)
    width_n = add_float_param(tree, "Body Width", 0.8, 0.01, 5.0)
    fin_n = add_int_param(tree, "Fin Count", 8, 0, 24)
    glow_n = add_float_param(tree, "Glow Intensity", 2.0, 0.0, 10.0)
    translucency_n = add_float_param(tree, "Translucency", 0.7, 0.0, 1.0)
    wave_n = add_float_param(tree, "Wave Phase", 0.0, 0.0, 6.28)

    # Body: elongated cylinder
    body = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 400, by))
    body.inputs["Vertices"].default_value = 24
    link_sockets(tree, width_n, body.inputs["Radius"])
    link_sockets(tree, length_n, body.inputs["Depth"])

    # Rotate to horizontal
    rot = safe_node(tree, "GeometryNodeTransform", (bx - 200, by))
    link_sockets(tree, body.outputs["Mesh"], rot.inputs["Geometry"])
    rot.inputs["Rotation"].default_value = (0, math.pi / 2, 0)

    # Wave displacement for swimming motion
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 200, by - 200))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx, by - 200))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    wave_freq = safe_node(tree, "ShaderNodeMath", (bx + 200, by - 200))
    wave_freq.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], wave_freq.inputs[0])
    wave_freq.inputs[1].default_value = 0.5

    wave_sin = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 200))
    wave_sin.operation = "SINE"
    link_sockets(tree, wave_freq.outputs["Value"], wave_sin.inputs[0])

    wave_offset = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 200))
    wave_offset.operation = "ADD"
    link_sockets(tree, wave_sin.outputs["Value"], wave_offset.inputs[0])
    link_sockets(tree, wave_n, wave_offset.inputs[1])

    wave_z = safe_node(tree, "ShaderNodeMath", (bx + 500, by - 200))
    wave_z.operation = "MULTIPLY"
    link_sockets(tree, wave_offset.outputs["Value"], wave_z.inputs[0])
    wave_z.inputs[1].default_value = 0.3

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 600, by))
    link_sockets(tree, rot.outputs["Geometry"], set_pos.inputs["Geometry"])
    z_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 400, by - 300))
    z_vec.inputs["X"].default_value = 0.0
    z_vec.inputs["Y"].default_value = 0.0
    link_sockets(tree, wave_z.outputs["Value"], z_vec.inputs["Z"])
    link_sockets(tree, z_vec.outputs["Vector"], set_pos.inputs["Offset"])

    # Fins: instanced small cones along body
    fin = safe_node(tree, "GeometryNodeMeshCone", (bx - 400, by - 400))
    fin.inputs["Vertices"].default_value = 4
    fin.inputs["Radius Bottom"].default_value = 0.05
    fin.inputs["Depth"].default_value = 0.3

    fin_pts = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by - 460))
    link_sockets(tree, fin_n, fin_pts.inputs["Count"])
    fin_pts.inputs["Offset"].default_value = (1.0, 0.0, 0.0)

    fin_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 200, by - 400))
    link_sockets(tree, fin_pts.outputs["Mesh"], fin_inst.inputs["Points"])
    link_sockets(tree, fin.outputs["Mesh"], fin_inst.inputs["Instance"])
    fin_real = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by - 400))
    link_sockets(tree, fin_inst.outputs["Instances"], fin_real.inputs["Geometry"])

    # Join body + fins
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 800, by))
    link_sockets(tree, set_pos.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, fin_real.outputs["Geometry"], join.inputs["Geometry"])

    # Store glow + translucency attributes
    store_glow = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 1000, by))
    store_glow.data_type = "FLOAT"
    store_glow.inputs["Name"].default_value = "glow_intensity"
    link_sockets(tree, glow_n, store_glow.inputs["Value"])
    link_sockets(tree, join.outputs["Geometry"], store_glow.inputs["Geometry"])

    store_trans = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 1200, by))
    store_trans.data_type = "FLOAT"
    store_trans.inputs["Name"].default_value = "translucency"
    link_sockets(tree, translucency_n, store_trans.inputs["Value"])
    link_sockets(tree, store_glow.outputs["Geometry"], store_trans.inputs["Geometry"])

    link_sockets(tree, store_trans.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(body, "geometry")
    color_node(fin, "geometry")
    color_node(wave_sin, "noise")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Body", "nodes": ("body", "rot"), "role": "geometry"},
        {"title": "Wave", "nodes": ("wave_sin", "set_pos"), "role": "geometry"},
        {"title": "Fins", "nodes": ("fin", "fin_inst", "fin_real"), "role": "geometry"},
        {"title": "Output", "nodes": ("store_glow", "store_trans", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 3. MEL_water_network — connected water network spline system
# -----------------------------------------------------------------------------

def build_water_network(group_name="MEL_water_network"):
    """Connected water network spline system — rivers, lakes, connected by white seam.

    Inputs:
      Node Count, Connection Density, Flow Direction, White Level, Network Scale
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    count_n = add_int_param(tree, "Node Count", 12, 2, 48)
    density_n = add_float_param(tree, "Connection Density", 0.5, 0.0, 1.0)
    flow_n = add_float_param(tree, "Flow Direction", 0.0, -3.14, 3.14)
    white_n = add_float_param(tree, "White Level", 0.8, 0.0, 1.0)
    scale_n = add_float_param(tree, "Network Scale", 20.0, 1.0, 200.0)

    # Scatter points for water nodes
    pts = safe_node(tree, "GeometryNodeDistributePointsOnFaces", (bx - 400, by))
    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 600, by))
    link_sockets(tree, scale_n, grid.inputs["Size X"])
    link_sockets(tree, scale_n, grid.inputs["Size Y"])
    grid.inputs["Vertices X"].default_value = 8
    grid.inputs["Vertices Y"].default_value = 8
    link_sockets(tree, grid.outputs["Mesh"], pts.inputs["Mesh"])
    pts.distribute_method = "RANDOM"
    link_sockets(tree, count_n, pts.inputs["Seed"])

    # Instance water discs at nodes
    disc = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 400, by - 200))
    disc.inputs["Vertices"].default_value = 16
    disc.inputs["Radius"].default_value = 1.5
    disc.inputs["Depth"].default_value = 0.1

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 200, by))
    link_sockets(tree, pts.outputs["Points"], inst.inputs["Points"])
    link_sockets(tree, disc.outputs["Mesh"], inst.inputs["Instance"])
    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by))
    link_sockets(tree, inst.outputs["Instances"], real.inputs["Geometry"])

    # Store white level + flow attributes
    store_white = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 200, by))
    store_white.data_type = "FLOAT"
    store_white.inputs["Name"].default_value = "white_level"
    link_sockets(tree, white_n, store_white.inputs["Value"])
    link_sockets(tree, real.outputs["Geometry"], store_white.inputs["Geometry"])

    store_flow = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 400, by))
    store_flow.data_type = "FLOAT"
    store_flow.inputs["Name"].default_value = "flow_direction"
    link_sockets(tree, flow_n, store_flow.inputs["Value"])
    link_sockets(tree, store_white.outputs["Geometry"], store_flow.inputs["Geometry"])

    link_sockets(tree, store_flow.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(grid, "geometry")
    color_node(disc, "geometry")
    color_node(pts, "points")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Nodes", "nodes": ("grid", "pts", "disc", "inst"), "role": "geometry"},
        {"title": "Output", "nodes": ("store_white", "store_flow", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 4. MEL_moonlit_surf — moonlit water surface with white seam reflection
# -----------------------------------------------------------------------------

def build_moonlit_surf(group_name="MEL_moonlit_surf"):
    """Moonlit water surface with white seam reflection.

    Inputs:
      Surface Size, Wave Height, Moon Reflection, Seam Visibility, Wave Scale
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    size_n = add_float_param(tree, "Surface Size", 30.0, 1.0, 200.0)
    wave_h_n = add_float_param(tree, "Wave Height", 0.3, 0.0, 5.0)
    moon_refl_n = add_float_param(tree, "Moon Reflection", 0.8, 0.0, 1.0)
    seam_vis_n = add_float_param(tree, "Seam Visibility", 0.8, 0.0, 1.0)
    wave_scale_n = add_float_param(tree, "Wave Scale", 2.0, 0.1, 10.0)

    # Base surface: grid
    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 400, by))
    link_sockets(tree, size_n, grid.inputs["Size X"])
    link_sockets(tree, size_n, grid.inputs["Size Y"])
    grid.inputs["Vertices X"].default_value = 48
    grid.inputs["Vertices Y"].default_value = 48

    # Wave displacement
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 400, by - 200))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 200, by - 200))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    noise = safe_node(tree, "ShaderNodeTexNoise", (bx - 200, by - 300))
    link_sockets(tree, wave_scale_n, noise.inputs["Scale"])
    noise.inputs["Detail"].default_value = 4.0

    wave_mul = safe_node(tree, "ShaderNodeMath", (bx, by - 300))
    wave_mul.operation = "MULTIPLY"
    link_sockets(tree, noise.outputs["Fac"], wave_mul.inputs[0])
    link_sockets(tree, wave_h_n, wave_mul.inputs[1])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 200, by))
    link_sockets(tree, grid.outputs["Mesh"], set_pos.inputs["Geometry"])
    z_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx, by - 100))
    z_vec.inputs["X"].default_value = 0.0
    z_vec.inputs["Y"].default_value = 0.0
    link_sockets(tree, wave_mul.outputs["Value"], z_vec.inputs["Z"])
    link_sockets(tree, z_vec.outputs["Vector"], set_pos.inputs["Offset"])

    # Store moon reflection + seam visibility
    store_moon = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 400, by))
    store_moon.data_type = "FLOAT"
    store_moon.inputs["Name"].default_value = "moon_reflection"
    link_sockets(tree, moon_refl_n, store_moon.inputs["Value"])
    link_sockets(tree, set_pos.outputs["Geometry"], store_moon.inputs["Geometry"])

    store_seam = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 600, by))
    store_seam.data_type = "FLOAT"
    store_seam.inputs["Name"].default_value = "seam_visibility"
    link_sockets(tree, seam_vis_n, store_seam.inputs["Value"])
    link_sockets(tree, store_moon.outputs["Geometry"], store_seam.inputs["Geometry"])

    link_sockets(tree, store_seam.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(grid, "geometry")
    color_node(noise, "noise")
    color_node(set_pos, "geometry")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Surface", "nodes": ("grid", "noise", "set_pos"), "role": "geometry"},
        {"title": "Output", "nodes": ("store_moon", "store_seam", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 5. MEL_white_haze_volume — volumetric haze implying distant mass
# -----------------------------------------------------------------------------

def build_white_haze_volume(group_name="MEL_white_haze_volume"):
    """Volumetric haze that implies the eel's distant mass.

    Inputs:
      Width, Height, Depth, Density, Tint Strength, Noise Scale, Falloff
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    w = add_float_param(tree, "Width", 50.0, 1.0, 200.0)
    h = add_float_param(tree, "Height", 15.0, 1.0, 100.0)
    d = add_float_param(tree, "Depth", 8.0, 1.0, 50.0)
    density_n = add_float_param(tree, "Density", 0.03, 0.0, 0.2)
    tint_n = add_float_param(tree, "Tint Strength", 0.85, 0.0, 1.0)
    ns = add_float_param(tree, "Noise Scale", 1.2, 0.1, 10.0)
    falloff_n = add_float_param(tree, "Falloff", 2.5, 0.1, 5.0)

    box = safe_node(tree, "GeometryNodeMeshCube", (bx - 400, by))
    size = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 600, by))
    link_sockets(tree, w, size.inputs["X"])
    link_sockets(tree, d, size.inputs["Y"])
    link_sockets(tree, h, size.inputs["Z"])
    link_sockets(tree, size.outputs["Vector"], box.inputs["Size"])

    noise = safe_node(tree, "ShaderNodeTexNoise", (bx - 200, by - 100))
    link_sockets(tree, ns, noise.inputs["Scale"])
    noise.inputs["Detail"].default_value = 3.0
    noise.inputs["Roughness"].default_value = 0.6

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx, by))
    link_sockets(tree, box.outputs["Mesh"], set_pos.inputs["Geometry"])
    disp = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 200, by - 200))
    link_float_to_vector(tree, noise.outputs["Fac"], disp, "X", defaults=(0.0, 0.0, 0.0))
    link_sockets(tree, disp.outputs["Vector"], set_pos.inputs["Offset"])

    store_density = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 200, by))
    store_density.data_type = "FLOAT"
    store_density.inputs["Name"].default_value = "haze_density"
    link_sockets(tree, density_n, store_density.inputs["Value"])
    link_sockets(tree, set_pos.outputs["Geometry"], store_density.inputs["Geometry"])

    store_tint = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 400, by))
    store_tint.data_type = "FLOAT"
    store_tint.inputs["Name"].default_value = "haze_tint"
    link_sockets(tree, tint_n, store_tint.inputs["Value"])
    link_sockets(tree, store_density.outputs["Geometry"], store_tint.inputs["Geometry"])

    link_sockets(tree, store_tint.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(box, "volume")
    color_node(noise, "noise")
    color_node(set_pos, "volume")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Volume", "nodes": ("box", "noise", "set_pos"), "role": "volume"},
        {"title": "Output", "nodes": ("store_density", "store_tint", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 6. MEL_current_marker — flow-direction arrows tracing the eel's path
# -----------------------------------------------------------------------------

def build_current_marker(group_name="MEL_current_marker"):
    """Flow-direction arrow instances that trace the eel's path.

    Inputs:
      Count, Spacing, Arrow Size, Glow Intensity, Flow Speed
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    count_n = add_int_param(tree, "Count", 16, 1, 64)
    spacing_n = add_float_param(tree, "Spacing", 2.0, 0.1, 20.0)
    size_n = add_float_param(tree, "Arrow Size", 0.3, 0.01, 2.0)
    glow_n = add_float_param(tree, "Glow Intensity", 1.5, 0.0, 5.0)
    flow_n = add_float_param(tree, "Flow Speed", 1.0, 0.0, 10.0)

    # Arrow path: mesh line
    path = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by))
    link_sockets(tree, count_n, path.inputs["Count"])
    path.inputs["Offset"].default_value = (1.0, 0.0, 0.0)

    # Arrow instance: small cone
    arrow = safe_node(tree, "GeometryNodeMeshCone", (bx - 400, by - 200))
    arrow.inputs["Vertices"].default_value = 4
    arrow.inputs["Radius Bottom"].default_value = 0.1
    arrow.inputs["Depth"].default_value = 0.4

    # Scale arrows
    arrow_scale = safe_node(tree, "GeometryNodeTransform", (bx - 200, by - 200))
    link_sockets(tree, arrow.outputs["Mesh"], arrow_scale.inputs["Geometry"])
    arrow_scale.inputs["Scale"].default_value = (1.0, 1.0, 1.0)

    # Instance arrows on path
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx, by))
    link_sockets(tree, path.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, arrow_scale.outputs["Geometry"], inst.inputs["Instance"])
    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 200, by))
    link_sockets(tree, inst.outputs["Instances"], real.inputs["Geometry"])

    # Store glow + flow attributes
    store_glow = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 400, by))
    store_glow.data_type = "FLOAT"
    store_glow.inputs["Name"].default_value = "marker_glow"
    link_sockets(tree, glow_n, store_glow.inputs["Value"])
    link_sockets(tree, real.outputs["Geometry"], store_glow.inputs["Geometry"])

    store_flow = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 600, by))
    store_flow.data_type = "FLOAT"
    store_flow.inputs["Name"].default_value = "marker_flow"
    link_sockets(tree, flow_n, store_flow.inputs["Value"])
    link_sockets(tree, store_glow.outputs["Geometry"], store_flow.inputs["Geometry"])

    link_sockets(tree, store_flow.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(path, "curve")
    color_node(arrow, "geometry")
    color_node(inst, "instance")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Path", "nodes": ("path",), "role": "curve"},
        {"title": "Arrows", "nodes": ("arrow", "arrow_scale", "inst"), "role": "geometry"},
        {"title": "Output", "nodes": ("store_glow", "store_flow", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# Registry
# -----------------------------------------------------------------------------

from .core import register_builder

register_builder("MEL_white_seam_spline", build_white_seam_spline,
    "White Seam Spline",
    "White seam that follows a water spline — the visible trace of the eel",
    "white_current")

register_builder("MEL_eel_silhouette", build_eel_silhouette,
    "Eel Silhouette",
    "Pale eel/oarfish silhouette that moves beneath the water surface",
    "white_current")

register_builder("MEL_water_network", build_water_network,
    "Water Network",
    "Connected water network spline system — rivers, lakes, connected by white seam",
    "white_current")

register_builder("MEL_moonlit_surf", build_moonlit_surf,
    "Moonlit Surf",
    "Moonlit water surface with white seam reflection",
    "white_current")

register_builder("MEL_white_haze_volume", build_white_haze_volume,
    "White Haze Volume",
    "Volumetric haze that implies the eel's distant mass",
    "white_current")

register_builder("MEL_current_marker", build_current_marker,
    "Current Marker",
    "Flow-direction arrow instances that trace the eel's path",
    "white_current")
