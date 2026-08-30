"""Faraway Mother GN builders — 5 builders for the fabric-mountain Monolith.

Reuses existing material masters (MI_Master_Nikki_Landscape, MI_Master_Toon_Universal_Alpha).
No new materials. Pure GN geometry.

Builders:
  MEL_mother_head_silhouette — sculpted ridge with moonlit face profile
  MEL_mother_hair_cascade     — ribbon waterfall cascade for maternal hair
  MEL_mother_valley_depression — terrain depression with fog fill
  MEL_mother_fog_volume       — volumetric haze that implies distant mass
  MEL_mother_fabric_ridge     — fabric normal-mapped terrain ridge
"""

from __future__ import annotations

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    add_vector_param, make_group_input, make_group_output, tree_input_names,
    register_builder,
)


# -----------------------------------------------------------------------------
# 1. MEL_mother_head_silhouette — sculpted ridge with moonlit face profile
# -----------------------------------------------------------------------------

def build_mother_head_silhouette(group_name="MEL_mother_head_silhouette"):
    """Sculpted mountain ridge that reads as a reclining face profile.

    Inputs:
      Width, Height, Depth, Ridge Count, Noise Scale, Noise Detail
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    width_n = add_float_param(tree, "Width", 20.0, 1.0, 100.0)
    height_n = add_float_param(tree, "Height", 8.0, 1.0, 50.0)
    depth_n = add_float_param(tree, "Depth", 6.0, 1.0, 30.0)
    ridge_n = add_int_param(tree, "Ridge Count", 5, 1, 16)
    noise_scale_n = add_float_param(tree, "Noise Scale", 3.0, 0.1, 10.0)
    noise_detail_n = add_float_param(tree, "Noise Detail", 4.0, 0.0, 8.0)

    # Base ridge: elongated cube
    ridge = safe_node(tree, "GeometryNodeMeshCube", (bx - 400, by))
    size = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 600, by))
    link_sockets(tree, width_n, size.inputs["X"])
    link_sockets(tree, height_n, size.inputs["Z"])
    link_sockets(tree, depth_n, size.inputs["Y"])
    link_sockets(tree, size.outputs["Vector"], ridge.inputs["Size"])

    # Displace with noise for organic silhouette
    noise = safe_node(tree, "ShaderNodeTexNoise", (bx - 200, by - 100))
    link_sockets(tree, noise_scale_n, noise.inputs["Scale"])
    link_sockets(tree, noise_detail_n, noise.inputs["Detail"])
    noise.inputs["Roughness"].default_value = 0.6

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx, by))
    link_sockets(tree, ridge.outputs["Mesh"], set_pos.inputs["Geometry"])
    disp_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 200, by - 200))
    link_float_to_vector(tree, noise.outputs["Fac"], disp_vec, "Z", defaults=(0.0, 0.0, 0.0))
    link_sockets(tree, disp_vec.outputs["Vector"], set_pos.inputs["Offset"])

    # Smooth shading
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 200, by))
    shade.inputs["Shade Smooth"].default_value = False
    link_sockets(tree, set_pos.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(ridge, "geometry")
    color_node(noise, "noise")
    color_node(set_pos, "geometry")

    return label_tree(tree, "MEL_mother_head_silhouette", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Ridge", "nodes": ("ridge", "noise", "set_pos"), "role": "geometry"},
        {"title": "Output", "nodes": ("shade", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 2. MEL_mother_hair_cascade — ribbon waterfall cascade for maternal hair
# -----------------------------------------------------------------------------

def build_mother_hair_cascade(group_name="MEL_mother_hair_cascade"):
    """Ribbon waterfall cascade that reads as flowing maternal hair.

    Inputs:
      Length, Width, Strand Count, Curl, Flow Speed, Twist
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    length_n = add_float_param(tree, "Length", 12.0, 1.0, 50.0)
    width_n = add_float_param(tree, "Width", 2.0, 0.1, 10.0)
    strand_n = add_int_param(tree, "Strand Count", 12, 1, 48)
    curl_n = add_float_param(tree, "Curl", 0.3, 0.0, 1.0)
    twist_n = add_float_param(tree, "Twist", 0.5, 0.0, 3.14)

    # Strand base: mesh line
    strand_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by))
    link_sockets(tree, strand_n, strand_line.inputs["Count"])
    strand_line.inputs["Offset"].default_value = (0.0, 0.0, 1.0)

    # Sweep into ribbon via curve
    strand_curve = safe_node(tree, "GeometryNodeMeshToCurve", (bx - 200, by))
    link_sockets(tree, strand_line.outputs["Mesh"], strand_curve.inputs["Mesh"])

    # Resample for smoothness
    resample = safe_node(tree, "GeometryNodeResampleCurve", (bx, by))
    link_sockets(tree, strand_curve.outputs["Curve"], resample.inputs["Curve"])
    resample.inputs["Count"].default_value = 32

    # Set curve radius for ribbon width
    set_radius = safe_node(tree, "GeometryNodeSetCurveRadius", (bx + 200, by))
    link_sockets(tree, resample.outputs["Curve"], set_radius.inputs["Curve"])
    radius_val = safe_node(tree, "ShaderNodeMath", (bx + 100, by - 100))
    radius_val.operation = "DIVIDE"
    link_sockets(tree, width_n, radius_val.inputs[0])
    radius_val.inputs[1].default_value = strand_n.default_value if hasattr(strand_n, "default_value") else 12.0
    link_sockets(tree, radius_val.outputs["Value"], set_radius.inputs["Radius"])

    # Curve to mesh with ribbon profile
    profile = safe_node(tree, "GeometryNodeCurvePrimitiveLine", (bx + 200, by - 200))
    profile.inputs["Resolution"].default_value = 1
    profile_pos = safe_node(tree, "GeometryNodeTransform", (bx + 200, by - 280))
    link_sockets(tree, profile.outputs["Curve"], profile_pos.inputs["Geometry"])
    profile_pos.inputs["Scale"].default_value = (0.15, 0.02, 1.0)

    to_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 400, by))
    link_sockets(tree, set_radius.outputs["Curve"], to_mesh.inputs["Curve"])
    link_sockets(tree, profile_pos.outputs["Geometry"], to_mesh.inputs["Profile Curve"])

    # Curl: displace along Z with sine
    curl_noise = safe_node(tree, "ShaderNodeTexNoise", (bx + 400, by - 100))
    curl_noise.inputs["Scale"].default_value = 2.0
    curl_mul = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 200))
    curl_mul.operation = "MULTIPLY"
    link_sockets(tree, curl_n, curl_mul.inputs[0])
    link_sockets(tree, curl_noise.outputs["Fac"], curl_mul.inputs[1])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 600, by))
    link_sockets(tree, to_mesh.outputs["Mesh"], set_pos.inputs["Geometry"])
    curl_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 400, by - 300))
    curl_vec.inputs["X"].default_value = 1.0
    curl_vec.inputs["Y"].default_value = 0.0
    link_sockets(tree, curl_mul.outputs["Value"], curl_vec.inputs["Z"])
    link_sockets(tree, curl_vec.outputs["Vector"], set_pos.inputs["Offset"])

    link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(strand_line, "curve")
    color_node(to_mesh, "geometry")
    color_node(curl_noise, "noise")

    return label_tree(tree, "MEL_mother_hair_cascade", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Strands", "nodes": ("strand_line", "strand_curve", "resample"), "role": "curve"},
        {"title": "Ribbon", "nodes": ("set_radius", "to_mesh"), "role": "geometry"},
        {"title": "Curl", "nodes": ("curl_noise", "set_pos"), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 3. MEL_mother_valley_depression — terrain depression with fog fill
# -----------------------------------------------------------------------------

def build_mother_valley_depression(group_name="MEL_mother_valley_depression"):
    """Terrain depression that reads as the "torso valley" the player walks through.

    Inputs:
      Radius, Depth, Floor Noise, Fog Level, Steepness
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    radius_n = add_float_param(tree, "Radius", 15.0, 1.0, 100.0)
    depth_n = add_float_param(tree, "Depth", 6.0, 0.5, 30.0)
    floor_noise_n = add_float_param(tree, "Floor Noise", 1.0, 0.0, 5.0)
    fog_level_n = add_float_param(tree, "Fog Level", 0.6, 0.0, 1.0)
    steepness_n = add_float_param(tree, "Steepness", 0.5, 0.0, 1.0)

    # Base terrain: grid
    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 400, by))
    link_sockets(tree, radius_n, grid.inputs["Size X"])
    link_sockets(tree, radius_n, grid.inputs["Size Y"])
    grid.inputs["Vertices X"].default_value = 32
    grid.inputs["Vertices Y"].default_value = 32

    # Displace center downward for depression
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 400, by - 200))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 200, by - 200))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    # Distance from center
    dist_sq = safe_node(tree, "ShaderNodeMath", (bx - 400, by - 300))
    dist_sq.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], dist_sq.inputs[0])
    link_sockets(tree, sep.outputs["X"], dist_sq.inputs[1])
    dist_sq_y = safe_node(tree, "ShaderNodeMath", (bx - 400, by - 360))
    dist_sq_y.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["Y"], dist_sq_y.inputs[0])
    link_sockets(tree, sep.outputs["Y"], dist_sq_y.inputs[1])
    dist_sum = safe_node(tree, "ShaderNodeMath", (bx - 200, by - 360))
    dist_sum.operation = "ADD"
    link_sockets(tree, dist_sq.outputs["Value"], dist_sum.inputs[0])
    link_sockets(tree, dist_sq_y.outputs["Value"], dist_sum.inputs[1])
    dist = safe_node(tree, "ShaderNodeMath", (bx - 100, by - 360))
    dist.operation = "SQRT"
    link_sockets(tree, dist_sum.outputs["Value"], dist.inputs[0])

    # Normalize distance
    norm = safe_node(tree, "ShaderNodeMath", (bx, by - 360))
    norm.operation = "DIVIDE"
    link_sockets(tree, dist.outputs["Value"], norm.inputs[0])
    link_sockets(tree, radius_n, norm.inputs[1])

    # Depression curve: smooth bowl shape
    one_minus = safe_node(tree, "ShaderNodeMath", (bx + 100, by - 360))
    one_minus.operation = "SUBTRACT"
    one_minus.inputs[0].default_value = 1.0
    link_sockets(tree, norm.outputs["Value"], one_minus.inputs[1])
    bowl = safe_node(tree, "ShaderNodeMath", (bx + 200, by - 360))
    bowl.operation = "POWER"
    link_sockets(tree, one_minus.outputs["Value"], bowl.inputs[0])
    bowl.inputs[1].default_value = 2.0
    depth_mul = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 360))
    depth_mul.operation = "MULTIPLY"
    link_sockets(tree, depth_n, depth_mul.inputs[0])
    link_sockets(tree, bowl.outputs["Value"], depth_mul.inputs[1])

    # Floor noise
    noise = safe_node(tree, "ShaderNodeTexNoise", (bx - 200, by - 460))
    link_sockets(tree, floor_noise_n, noise.inputs["Scale"])
    noise.inputs["Detail"].default_value = 3.0
    noise_mul = safe_node(tree, "ShaderNodeMath", (bx - 100, by - 460))
    noise_mul.operation = "MULTIPLY"
    link_sockets(tree, noise.outputs["Fac"], noise_mul.inputs[0])
    noise_mul.inputs[1].default_value = 0.3

    # Final Z displacement
    z_disp = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 460))
    z_disp.operation = "SUBTRACT"
    link_sockets(tree, noise_mul.outputs["Value"], z_disp.inputs[0])
    link_sockets(tree, depth_mul.outputs["Value"], z_disp.inputs[1])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 600, by))
    link_sockets(tree, grid.outputs["Mesh"], set_pos.inputs["Geometry"])
    z_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 400, by - 300))
    z_vec.inputs["X"].default_value = 0.0
    z_vec.inputs["Y"].default_value = 0.0
    link_sockets(tree, z_disp.outputs["Value"], z_vec.inputs["Z"])
    link_sockets(tree, z_vec.outputs["Vector"], set_pos.inputs["Offset"])

    # Store fog level attribute
    store_fog = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 800, by))
    store_fog.data_type = "FLOAT"
    store_fog.inputs["Name"].default_value = "fog_level"
    link_sockets(tree, fog_level_n, store_fog.inputs["Value"])
    link_sockets(tree, set_pos.outputs["Geometry"], store_fog.inputs["Geometry"])
    link_sockets(tree, store_fog.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(grid, "geometry")
    color_node(noise, "noise")
    color_node(set_pos, "geometry")

    return label_tree(tree, "MEL_mother_valley_depression", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Grid", "nodes": ("grid",), "role": "geometry"},
        {"title": "Depression", "nodes": ("dist", "bowl", "noise", "set_pos"), "role": "geometry"},
        {"title": "Output", "nodes": ("store_fog", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 4. MEL_mother_fog_volume — volumetric haze that implies distant mass
# -----------------------------------------------------------------------------

def build_mother_fog_volume(group_name="MEL_mother_fog_volume"):
    """Volumetric haze that implies distant body mass — no mesh, just suggestion.

    Inputs:
      Width, Height, Depth, Density, Tint Strength, Noise Scale, Falloff
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    width_n = add_float_param(tree, "Width", 40.0, 1.0, 200.0)
    height_n = add_float_param(tree, "Height", 20.0, 1.0, 100.0)
    depth_n = add_float_param(tree, "Depth", 10.0, 1.0, 50.0)
    density_n = add_float_param(tree, "Density", 0.04, 0.0, 0.2)
    tint_n = add_float_param(tree, "Tint Strength", 0.8, 0.0, 1.0)
    noise_scale_n = add_float_param(tree, "Noise Scale", 1.5, 0.1, 10.0)
    falloff_n = add_float_param(tree, "Falloff", 2.0, 0.1, 5.0)

    # Base volume: box
    box = safe_node(tree, "GeometryNodeMeshCube", (bx - 400, by))
    size = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 600, by))
    link_sockets(tree, width_n, size.inputs["X"])
    link_sockets(tree, depth_n, size.inputs["Y"])
    link_sockets(tree, height_n, size.inputs["Z"])
    link_sockets(tree, size.outputs["Vector"], box.inputs["Size"])

    # Noise for organic edge
    noise = safe_node(tree, "ShaderNodeTexNoise", (bx - 200, by - 100))
    link_sockets(tree, noise_scale_n, noise.inputs["Scale"])
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.7

    # Displace vertices for foggy edge
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx, by))
    link_sockets(tree, box.outputs["Mesh"], set_pos.inputs["Geometry"])
    disp_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 200, by - 200))
    link_float_to_vector(tree, noise.outputs["Fac"], disp_vec, "X", defaults=(0.0, 0.0, 0.0))
    link_sockets(tree, disp_vec.outputs["Vector"], set_pos.inputs["Offset"])

    # Store density + tint attributes
    store_density = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 200, by))
    store_density.data_type = "FLOAT"
    store_density.inputs["Name"].default_value = "fog_density"
    link_sockets(tree, density_n, store_density.inputs["Value"])
    link_sockets(tree, set_pos.outputs["Geometry"], store_density.inputs["Geometry"])

    store_tint = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 400, by))
    store_tint.data_type = "FLOAT"
    store_tint.inputs["Name"].default_value = "fog_tint"
    link_sockets(tree, tint_n, store_tint.inputs["Value"])
    link_sockets(tree, store_density.outputs["Geometry"], store_tint.inputs["Geometry"])

    link_sockets(tree, store_tint.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(box, "volume")
    color_node(noise, "noise")
    color_node(set_pos, "volume")

    return label_tree(tree, "MEL_mother_fog_volume", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Volume", "nodes": ("box", "noise", "set_pos"), "role": "volume"},
        {"title": "Attributes", "nodes": ("store_density", "store_tint"), "role": "attribute"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 5. MEL_mother_fabric_ridge — fabric normal-mapped terrain ridge
# -----------------------------------------------------------------------------

def build_mother_fabric_ridge(group_name="MEL_mother_fabric_ridge"):
    """Fabric normal-mapped terrain ridge — the "skin" of the Faraway Mother.

    Inputs:
      Width, Height, Fold Depth, Fold Count, Fold Sharpness, Noise Detail
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    width_n = add_float_param(tree, "Width", 30.0, 1.0, 200.0)
    height_n = add_float_param(tree, "Height", 6.0, 0.5, 30.0)
    fold_depth_n = add_float_param(tree, "Fold Depth", 1.5, 0.1, 10.0)
    fold_count_n = add_int_param(tree, "Fold Count", 6, 1, 24)
    sharpness_n = add_float_param(tree, "Fold Sharpness", 2.0, 0.5, 8.0)
    noise_detail_n = add_float_param(tree, "Noise Detail", 3.0, 0.0, 8.0)

    # Base terrain: grid
    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 400, by))
    link_sockets(tree, width_n, grid.inputs["Size X"])
    link_sockets(tree, width_n, grid.inputs["Size Y"])
    grid.inputs["Vertices X"].default_value = 48
    grid.inputs["Vertices Y"].default_value = 48

    # Position for fold calculation
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 400, by - 200))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 200, by - 200))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    # Fabric folds: abs(sin(x * fold_count)) ^ sharpness
    fold_freq = safe_node(tree, "ShaderNodeMath", (bx - 400, by - 300))
    fold_freq.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], fold_freq.inputs[0])
    link_sockets(tree, fold_count_n, fold_freq.inputs[1])
    fold_sin = safe_node(tree, "ShaderNodeMath", (bx - 200, by - 300))
    fold_sin.operation = "SINE"
    link_sockets(tree, fold_freq.outputs["Value"], fold_sin.inputs[0])
    fold_abs = safe_node(tree, "ShaderNodeMath", (bx - 100, by - 300))
    fold_abs.operation = "ABSOLUTE"
    link_sockets(tree, fold_sin.outputs["Value"], fold_abs.inputs[0])
    fold_pow = safe_node(tree, "ShaderNodeMath", (bx, by - 300))
    fold_pow.operation = "POWER"
    link_sockets(tree, fold_abs.outputs["Value"], fold_pow.inputs[0])
    link_sockets(tree, sharpness_n, fold_pow.inputs[1])

    # Noise for organic detail
    noise = safe_node(tree, "ShaderNodeTexNoise", (bx - 200, by - 460))
    noise.inputs["Scale"].default_value = 4.0
    link_sockets(tree, noise_detail_n, noise.inputs["Detail"])
    noise.inputs["Roughness"].default_value = 0.55
    noise_mul = safe_node(tree, "ShaderNodeMath", (bx - 100, by - 460))
    noise_mul.operation = "MULTIPLY"
    link_sockets(tree, noise.outputs["Fac"], noise_mul.inputs[0])
    noise_mul.inputs[1].default_value = 0.3

    # Combine: fold * fold_depth + noise
    fold_main = safe_node(tree, "ShaderNodeMath", (bx + 100, by - 300))
    fold_main.operation = "MULTIPLY"
    link_sockets(tree, fold_pow.outputs["Value"], fold_main.inputs[0])
    link_sockets(tree, fold_depth_n, fold_main.inputs[1])
    fold_add = safe_node(tree, "ShaderNodeMath", (bx + 200, by - 300))
    fold_add.operation = "ADD"
    link_sockets(tree, fold_main.outputs["Value"], fold_add.inputs[0])
    link_sockets(tree, noise_mul.outputs["Value"], fold_add.inputs[1])

    # Scale to height
    z_scale = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 300))
    z_scale.operation = "MULTIPLY"
    link_sockets(tree, fold_add.outputs["Value"], z_scale.inputs[0])
    link_sockets(tree, height_n, z_scale.inputs[1])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 500, by))
    link_sockets(tree, grid.outputs["Mesh"], set_pos.inputs["Geometry"])
    z_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 300, by - 100))
    z_vec.inputs["X"].default_value = 0.0
    z_vec.inputs["Y"].default_value = 0.0
    link_sockets(tree, z_scale.outputs["Value"], z_vec.inputs["Z"])
    link_sockets(tree, z_vec.outputs["Vector"], set_pos.inputs["Offset"])

    link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(grid, "geometry")
    color_node(noise, "noise")
    color_node(set_pos, "geometry")

    return label_tree(tree, "MEL_mother_fabric_ridge", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Grid", "nodes": ("grid",), "role": "geometry"},
        {"title": "Fabric Folds", "nodes": ("fold_sin", "fold_pow", "noise"), "role": "geometry"},
        {"title": "Output", "nodes": ("set_pos", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# Registry
# -----------------------------------------------------------------------------

from .core import register_builder

register_builder("MEL_mother_head_silhouette", build_mother_head_silhouette,
    "Mother Head Silhouette",
    "Sculpted mountain ridge that reads as a reclining face profile",
    "mother")

register_builder("MEL_mother_hair_cascade", build_mother_hair_cascade,
    "Mother Hair Cascade",
    "Ribbon waterfall cascade that reads as flowing maternal hair",
    "mother")

register_builder("MEL_mother_valley_depression", build_mother_valley_depression,
    "Mother Valley Depression",
    "Terrain depression that reads as the torso valley the player walks through",
    "mother")

register_builder("MEL_mother_fog_volume", build_mother_fog_volume,
    "Mother Fog Volume",
    "Volumetric haze that implies distant body mass — no mesh, just suggestion",
    "mother")

register_builder("MEL_mother_fabric_ridge", build_mother_fabric_ridge,
    "Mother Fabric Ridge",
    "Fabric normal-mapped terrain ridge — the skin of the Faraway Mother",
    "mother")
