"""Monolith GN group builders -- gothic coastal monolith kit for Sea Above.

Five builders forming a reusable monolith kit, matching the P0 concept-art
direction from Docs/Art/MONOLITH_CONCEPT_ART_BACKLOG_2026-08-26.md (The Last
Reflection: "Moonlit basalt coast filled with tide pools and broken mirrors,
every reflection showing the same impossible pale ocean, a vast manta-ray
silhouette gliding beneath a puddle..., gothic coastal monolith").

Each builder is a self-contained Geometry Nodes group. They share a visual
language: dark basalt, broken mirrors / reflective inlays, tide-pool basins,
and manta-ray silhouette curves.

Pure Python + bpy. Registers into the GN registry via register_builder.

Category: monolith
"""

from __future__ import annotations

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    make_group_input, make_group_output, tree_input_names,
)


# -----------------------------------------------------------------------------
# 1. MEL_monolith_spire
# -----------------------------------------------------------------------------

def build_monolith_spire(group_name="MEL_monolith_spire"):
    """Gothic coastal monolith spire -- a single tall basalt spire with
    optional fractured-mirror inlay slit and tide-pool basin at the base.

    The spire reads as the visible fragment of something far larger: the
    implication is that the rest is buried in the cliff or under the sea.
    Designed to be instanced via circular / linear arrays into monolith fields.

    Inputs:
      Height, Base Width, Taper, Fracture Count, Mirror Inlay, Tide Pool Depth
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    # --- Profile curve (the spire silhouette) ---
    # Use a cubic bezier-like stack: curve line + curve fill + extrusion is
    # too heavy for a primitive builder. Instead: cylinder + displace top +
    # random fracture via voronoi-style noise (white noise on normal).
    base_n = add_float_param(tree, "Base Width", 3.0, 0.1, 30.0)
    height_n = add_float_param(tree, "Height", 12.0, 0.5, 120.0)
    taper_n = add_float_param(tree, "Taper", 0.32, 0.02, 1.0)
    fracture_n = add_int_param(tree, "Fracture Count", 4, 0, 24)
    mirror_n = add_float_param(tree, "Mirror Inlay", 0.18, 0.0, 1.0)
    tide_depth_n = add_float_param(tree, "Tide Pool Depth", 0.45, 0.0, 5.0)

    # Base cylinder (hexagonal basalt column feel)
    cyl = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 400, by + 400))
    cyl.inputs["Vertices"].default_value = 6
    link_sockets(tree, base_n, cyl.inputs["Radius"])
    link_sockets(tree, height_n, cyl.inputs["Depth"])

    # Taper: scale top face inward using Transform on a realized copy
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 200, by + 400))
    link_sockets(tree, cyl.outputs["Mesh"], realize.inputs["Geometry"])

    taper_scale = safe_node(tree, "GeometryNodeTransform", (bx, by + 400))
    link_sockets(tree, realize.outputs["Geometry"], taper_scale.inputs["Geometry"])
    link_float_to_vector(tree, taper_n, taper_scale, "Scale", component=0, defaults=(0.0, 1.0, 1.0))
    # Mirror Y so it tapers uniformly on XZ
    taper_scale.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    # Override: set X and Z to taper, keep Y at 1
    taper_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 200, by + 280))
    link_sockets(tree, taper_n, taper_vec.inputs["X"])
    taper_vec.inputs["Y"].default_value = 1.0
    link_sockets(tree, taper_n, taper_vec.inputs["Z"])
    link_sockets(tree, taper_vec.outputs["Vector"], taper_scale.inputs["Scale"])

    # Fracture displacement: random per-vertex offset along normal via Set Position + Noise
    noise = safe_node(tree, "ShaderNodeTexNoise", (bx - 200, by + 180))
    noise.inputs["Scale"].default_value = 2.4
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Roughness"].default_value = 0.6

    # Map noise to displacement strength controlled by Fracture Count
    frac_mul = safe_node(tree, "ShaderNodeMath", (bx - 200, by + 80))
    frac_mul.operation = "MULTIPLY"
    link_sockets(tree, fracture_n, frac_mul.inputs[0])
    frac_mul.inputs[1].default_value = 0.04

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 200, by + 400))
    link_sockets(tree, taper_scale.outputs["Geometry"], set_pos.inputs["Geometry"])
    disp_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx, by + 80))
    link_float_to_vector(tree, frac_mul.outputs["Value"], disp_vec, "X", defaults=(0.0, 0.0, 0.0))
    link_sockets(tree, disp_vec.outputs["Vector"], set_pos.inputs["Offset"])

    # Mirror inlay: a thin emissive slit down the front face
    inlay = safe_node(tree, "GeometryNodeMeshCube", (bx - 200, by - 100))
    inlay.inputs["Size"].default_value = (0.04, 0.02, 1.0)
    inlay_scale = safe_node(tree, "GeometryNodeTransform", (bx, by - 100))
    link_sockets(tree, inlay.outputs["Mesh"], inlay_scale.inputs["Geometry"])
    link_float_to_vector(tree, mirror_n, inlay_scale, "Scale", component=0, defaults=(0.0, 1.0, 1.0))
    inlay_scale.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    inlay_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 200, by - 220))
    link_sockets(tree, mirror_n, inlay_vec.inputs["X"])
    inlay_vec.inputs["Y"].default_value = 1.0
    inlay_vec.inputs["Z"].default_value = 1.0
    link_sockets(tree, inlay_vec.outputs["Vector"], inlay_scale.inputs["Scale"])

    # Position inlay at front face of spire
    inlay_pos = safe_node(tree, "GeometryNodeTransform", (bx + 200, by - 100))
    link_sockets(tree, inlay_scale.outputs["Geometry"], inlay_pos.inputs["Geometry"])
    inlay_offset = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 100, by - 220))
    half_w = safe_node(tree, "ShaderNodeMath", (bx - 100, by - 280))
    half_w.operation = "MULTIPLY"
    link_sockets(tree, base_n, half_w.inputs[0])
    half_w.inputs[1].default_value = 0.5
    link_sockets(tree, half_w.outputs["Value"], inlay_offset.inputs["X"])
    inlay_offset.inputs["Y"].default_value = 0.02
    half_h = safe_node(tree, "ShaderNodeMath", (bx - 100, by - 340))
    half_h.operation = "MULTIPLY"
    link_sockets(tree, height_n, half_h.inputs[0])
    half_h.inputs[1].default_value = 0.5
    link_sockets(tree, half_h.outputs["Value"], inlay_offset.inputs["Z"])
    link_sockets(tree, inlay_offset.outputs["Vector"], inlay_pos.inputs["Translation"])

    # Tide pool basin: a shallow cylinder carved into the base
    tide = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 200, by - 400))
    tide.inputs["Vertices"].default_value = 24
    tide_r = safe_node(tree, "ShaderNodeMath", (bx - 400, by - 460))
    tide_r.operation = "MULTIPLY"
    link_sockets(tree, base_n, tide_r.inputs[0])
    tide_r.inputs[1].default_value = 0.85
    link_sockets(tree, tide_r.outputs["Value"], tide.inputs["Radius"])
    link_sockets(tree, tide_depth_n, tide.inputs["Depth"])
    tide_pos = safe_node(tree, "GeometryNodeTransform", (bx, by - 400))
    link_sockets(tree, tide.outputs["Mesh"], tide_pos.inputs["Geometry"])
    tide_offset = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 100, by - 520))
    tide_offset.inputs["X"].default_value = 0.0
    tide_offset.inputs["Y"].default_value = 0.0
    tide_offset.inputs["Z"].default_value = 0.02
    link_sockets(tree, tide_offset.outputs["Vector"], tide_pos.inputs["Translation"])

    # Join spire + inlay + tide pool
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 400, by + 200))
    link_sockets(tree, set_pos.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, inlay_pos.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, tide_pos.outputs["Geometry"], join.inputs["Geometry"])

    # Smooth shading
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 600, by + 200))
    shade.inputs["Shade Smooth"].default_value = False
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(cyl, "geometry")
    color_node(set_pos, "geometry")
    color_node(inlay, "emissive")
    color_node(tide, "water")
    color_node(join, "geometry")

    return label_tree(tree, "MEL_monolith_spire", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Spire Body", "nodes": ("cylinder", "realize", "taper", "noise", "set_pos"), "role": "geometry"},
        {"title": "Mirror Inlay", "nodes": ("inlay", "inlay_scale", "inlay_pos"), "role": "emissive"},
        {"title": "Tide Pool", "nodes": ("tide", "tide_pos"), "role": "water"},
        {"title": "Output", "nodes": ("join", "shade", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 2. MEL_monolith_field
# -----------------------------------------------------------------------------

def build_monolith_field(group_name="MEL_monolith_field"):
    """Scatter monolith spires across a 2D plane -- the overworld monolith
    field the player traverses. Uses a grid of points + instance on points
    with per-instance scale/rotation driven by noise so no two spires read
    the same.

    Inputs:
      Field Width, Field Depth, Density, Height Variation, Seed
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    width_n = add_float_param(tree, "Field Width", 40.0, 1.0, 400.0)
    depth_n = add_float_param(tree, "Field Depth", 40.0, 1.0, 400.0)
    density_n = add_int_param(tree, "Density", 16, 1, 256)
    height_var_n = add_float_param(tree, "Height Variation", 0.6, 0.0, 1.0)
    seed_n = add_int_param(tree, "Seed", 3900, 0, 99999)

    # Grid of points
    grid = safe_node(tree, "MeshLine", (bx - 400, by + 400)) if False else None
    # Use Distribute Points on Faces for even coverage
    plane = safe_node(tree, "GeometryNodeMeshGrid", (bx - 400, by + 400))
    link_sockets(tree, width_n, plane.inputs["Size X"])
    link_sockets(tree, depth_n, plane.inputs["Size Y"])
    res_x = safe_node(tree, "ShaderNodeMath", (bx - 600, by + 320))
    res_x.operation = "MULTIPLY"
    link_sockets(tree, density_n, res_x.inputs[0])
    res_x.inputs[1].default_value = 1.0
    res_x_int = safe_node(tree, "ShaderNodeMath", (bx - 600, by + 260))
    res_x_int.operation = "CEIL"
    link_sockets(tree, res_x.outputs["Value"], res_x_int.inputs[0])
    link_sockets(tree, res_x_int.outputs["Value"], plane.inputs["Vertices X"])
    link_sockets(tree, res_x_int.outputs["Value"], plane.inputs["Vertices Y"])

    # Distribute points
    pts = safe_node(tree, "GeometryNodeDistributePointsOnFaces", (bx - 200, by + 400))
    link_sockets(tree, plane.outputs["Mesh"], pts.inputs["Mesh"])
    pts.distribute_method = "RANDOM"
    seed_off = safe_node(tree, "ShaderNodeMath", (bx - 400, by + 280))
    seed_off.operation = "ADD"
    link_sockets(tree, seed_n, seed_off.inputs[0])
    seed_off.inputs[1].default_value = 0.0
    link_sockets(tree, seed_off.outputs["Value"], pts.inputs["Seed"])

    # Instance the spire group on each point
    spire = safe_node(tree, "GeometryNodeGroup", (bx, by + 400))
    spire.node_tree = _get_or_create_spire_tree()

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 200, by + 400))
    link_sockets(tree, pts.outputs["Points"], inst.inputs["Points"])
    link_sockets(tree, spire.outputs["Geometry"], inst.inputs["Instance"])

    # Per-instance scale from noise
    noise = safe_node(tree, "ShaderNodeTexNoise", (bx, by + 200))
    noise.inputs["Scale"].default_value = 1.5
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.55
    noise.inputs["Lacunarity"].default_value = 2.0

    # Map noise [0,1] to [1-height_var, 1+height_var]
    n_map = safe_node(tree, "ShaderNodeMapRange", (bx + 200, by + 200))
    n_map.inputs["From Min"].default_value = 0.0
    n_map.inputs["From Max"].default_value = 1.0
    n_map.inputs["To Min"].default_value = 1.0
    n_map.inputs["To Max"].default_value = 1.0
    # Override To Min/Max with height_var
    to_min = safe_node(tree, "ShaderNodeMath", (bx + 100, by + 100))
    to_min.operation = "SUBTRACT"
    to_min.inputs[0].default_value = 1.0
    link_sockets(tree, height_var_n, to_min.inputs[1])
    to_max = safe_node(tree, "ShaderNodeMath", (bx + 100, by + 40))
    to_max.operation = "ADD"
    to_max.inputs[0].default_value = 1.0
    link_sockets(tree, height_var_n, to_max.inputs[1])
    link_sockets(tree, to_min.outputs["Value"], n_map.inputs["To Min"])
    link_sockets(tree, to_max.outputs["Value"], n_map.inputs["To Max"])
    link_sockets(tree, noise.outputs["Fac"], n_map.inputs["Value"])

    scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 400, by + 400))
    link_sockets(tree, inst.outputs["Instances"], scale_inst.inputs["Instances"])
    link_sockets(tree, n_map.outputs["Result"], scale_inst.inputs["Scale"])

    # Realize + output
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 600, by + 400))
    link_sockets(tree, scale_inst.outputs["Instances"], realize.inputs["Geometry"])
    link_sockets(tree, realize.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(plane, "geometry")
    color_node(pts, "points")
    color_node(inst, "instance")
    color_node(scale_inst, "instance")

    return label_tree(tree, "MEL_monolith_field", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Grid", "nodes": ("plane",), "role": "geometry"},
        {"title": "Points", "nodes": ("pts",), "role": "points"},
        {"title": "Instances", "nodes": ("spire", "inst", "noise", "n_map", "scale_inst"), "role": "instance"},
        {"title": "Output", "nodes": ("realize", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 3. MEL_monolith_manta_silhouette
# -----------------------------------------------------------------------------

def build_monolith_manta_silhouette(group_name="MEL_monolith_manta_silhouette"):
    """Manta-ray silhouette curve -- the implied body beneath the reflection
    pools. A flat, wide, winged curve that reads as a ray/manta seen from
    directly above or below. Used as a decal, shadow-catcher, or water
    displacement mask.

    Inputs:
      Wingspan, Body Length, Wing Curve, Fin Detail, Subdiv
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    span_n = add_float_param(tree, "Wingspan", 18.0, 1.0, 200.0)
    body_n = add_float_param(tree, "Body Length", 6.0, 0.5, 60.0)
    curve_n = add_float_param(tree, "Wing Curve", 0.45, 0.0, 1.0)
    fin_n = add_int_param(tree, "Fin Detail", 32, 3, 128)
    subd_n = add_int_param(tree, "Subdivisions", 6, 1, 24)

    # Build the manta profile as a 2D curve: body ellipse + two swept wings
    # Use a Bezier Segment with custom endpoints to approximate wing sweep
    body = safe_node(tree, "GeometryNodeCurveSpiral", (bx - 400, by + 400)) if False else None
    # Simpler: mesh line for body + two wing curves
    body_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by + 400))
    body_line.mode = "END_POINTS"
    body_line.inputs["Count"].default_value = 2
    body_start = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 600, by + 320))
    half_body = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 260))
    half_body.operation = "MULTIPLY"
    link_sockets(tree, body_n, half_body.inputs[0])
    half_body.inputs[1].default_value = -0.5
    link_sockets(tree, half_body.outputs["Value"], body_start.inputs["X"])
    body_start.inputs["Y"].default_value = 0.0
    body_start.inputs["Z"].default_value = 0.0
    link_sockets(tree, body_start.outputs["Vector"], body_line.inputs["Start"])
    body_end = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 600, by + 380))
    link_sockets(tree, half_body.outputs["Value"], body_end.inputs["X"])
    # Negate for the other end
    neg = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 440))
    neg.operation = "MULTIPLY"
    link_sockets(tree, half_body.outputs["Value"], neg.inputs[0])
    neg.inputs[1].default_value = -1.0
    link_sockets(tree, neg.outputs["Value"], body_end.inputs["X"])
    body_end.inputs["Y"].default_value = 0.0
    body_end.inputs["Z"].default_value = 0.0
    link_sockets(tree, body_end.outputs["Vector"], body_line.inputs["End"])

    # Wing curves: two bezier-like arcs from body tips outward
    wing_l = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by + 200))
    wing_l.mode = "END_POINTS"
    link_sockets(tree, fin_n, wing_l.inputs["Count"])
    wing_l_start = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 600, by + 140))
    link_sockets(tree, half_body.outputs["Value"], wing_l_start.inputs["X"])
    wing_l_start.inputs["Y"].default_value = 0.0
    wing_l_start.inputs["Z"].default_value = 0.0
    link_sockets(tree, wing_l_start.outputs["Vector"], wing_l.inputs["Start"])
    wing_l_end = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 600, by + 260))
    half_span = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 260))
    half_span.operation = "MULTIPLY"
    link_sockets(tree, span_n, half_span.inputs[0])
    half_span.inputs[1].default_value = 0.5
    link_sockets(tree, half_span.outputs["Value"], wing_l_end.inputs["X"])
    wing_curve_y = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 200))
    wing_curve_y.operation = "MULTIPLY"
    link_sockets(tree, span_n, wing_curve_y.inputs[0])
    link_sockets(tree, curve_n, wing_curve_y.inputs[1])
    wing_curve_y.inputs[1].default_value = 0.15
    link_sockets(tree, wing_curve_y.outputs["Value"], wing_l_end.inputs["Y"])
    wing_l_end.inputs["Z"].default_value = 0.0
    link_sockets(tree, wing_l_end.outputs["Vector"], wing_l.inputs["End"])

    # Right wing (mirror of left)
    wing_r = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by + 60))
    wing_r.mode = "END_POINTS"
    link_sockets(tree, fin_n, wing_r.inputs["Count"])
    wing_r_start = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 600, by))
    link_sockets(tree, neg.outputs["Value"], wing_r_start.inputs["X"])
    wing_r_start.inputs["Y"].default_value = 0.0
    wing_r_start.inputs["Z"].default_value = 0.0
    link_sockets(tree, wing_r_start.outputs["Vector"], wing_r.inputs["Start"])
    wing_r_end = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 600, by + 120))
    neg_span = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 120))
    neg_span.operation = "MULTIPLY"
    link_sockets(tree, half_span.outputs["Value"], neg_span.inputs[0])
    neg_span.inputs[1].default_value = -1.0
    link_sockets(tree, neg_span.outputs["Value"], wing_r_end.inputs["X"])
    link_sockets(tree, wing_curve_y.outputs["Value"], wing_r_end.inputs["Y"])
    wing_r_end.inputs["Z"].default_value = 0.0
    link_sockets(tree, wing_r_end.outputs["Vector"], wing_r.inputs["End"])

    # Join body + wings
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 200, by + 200))
    link_sockets(tree, body_line.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, wing_l.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, wing_r.outputs["Mesh"], join.inputs["Geometry"])

    # Resample for smoothness
    resample = safe_node(tree, "GeometryNodeResampleCurve", (bx, by + 200))
    link_sockets(tree, join.outputs["Geometry"], resample.inputs["Curve"])
    link_sockets(tree, subd_n, resample.inputs["Count"])

    # Set curve radius for visibility
    set_radius = safe_node(tree, "GeometryNodeSetCurveRadius", (bx + 200, by + 200))
    link_sockets(tree, resample.outputs["Curve"], set_radius.inputs["Curve"])
    set_radius.inputs["Radius"].default_value = 0.06

    # Curve to mesh (flat ribbon)
    to_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 400, by + 200))
    link_sockets(tree, set_radius.outputs["Curve"], to_mesh.inputs["Curve"])
    # Profile: thin rectangle
    profile = safe_node(tree, "GeometryNodeCurvePrimitiveLine", (bx + 200, by + 80))
    profile.inputs["Resolution"].default_value = 1
    profile_pos = safe_node(tree, "GeometryNodeTransform", (bx + 200, by + 20))
    link_sockets(tree, profile.outputs["Curve"], profile_pos.inputs["Geometry"])
    profile_pos.inputs["Scale"].default_value = (0.18, 0.02, 1.0)
    link_sockets(tree, profile_pos.outputs["Geometry"], to_mesh.inputs["Profile Curve"])

    link_sockets(tree, to_mesh.outputs["Mesh"], gout.inputs["Geometry"])

    color_node(body_line, "geometry")
    color_node(wing_l, "geometry")
    color_node(wing_r, "geometry")
    color_node(join, "geometry")
    color_node(resample, "curve")
    color_node(to_mesh, "geometry")

    return label_tree(tree, "MEL_monolith_manta_silhouette", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Body", "nodes": ("body_line",), "role": "curve"},
        {"title": "Wings", "nodes": ("wing_l", "wing_r"), "role": "curve"},
        {"title": "Resample", "nodes": ("join", "resample", "set_radius"), "role": "curve"},
        {"title": "Output", "nodes": ("to_mesh", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 4. MEL_monolith_tide_pool
# -----------------------------------------------------------------------------

def build_monolith_tide_pool(group_name="MEL_monolith_tide_pool"):
    """Tide pool basin with reflective water plane and broken mirror shards.
    The pool shows the same impossible pale ocean regardless of what's above.

    Inputs:
      Radius, Depth, Shard Count, Water Level, Reflection Tint
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    radius_n = add_float_param(tree, "Radius", 2.5, 0.1, 30.0)
    depth_n = add_float_param(tree, "Depth", 0.6, 0.05, 10.0)
    shard_n = add_int_param(tree, "Shard Count", 8, 0, 64)
    water_level_n = add_float_param(tree, "Water Level", 0.7, 0.0, 1.0)

    # Basin: cylinder with open top
    basin = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 400, by + 400))
    basin.inputs["Vertices"].default_value = 32
    basin.inputs["Fill Type"].default_value = 1  # Ngon
    link_sockets(tree, radius_n, basin.inputs["Radius"])
    link_sockets(tree, depth_n, basin.inputs["Depth"])
    basin_pos = safe_node(tree, "GeometryNodeTransform", (bx - 200, by + 400))
    link_sockets(tree, basin.outputs["Mesh"], basin_pos.inputs["Geometry"])
    basin_pos.inputs["Translation"].default_value = (0.0, 0.0, 0.0)

    # Water plane: circle at water level
    water = safe_node(tree, "GeometryNodeMeshCircle", (bx - 400, by + 200))
    water.inputs["Vertices"].default_value = 32
    water.fill_type = "NGON"
    water_r = safe_node(tree, "ShaderNodeMath", (bx - 600, by + 140))
    water_r.operation = "MULTIPLY"
    link_sockets(tree, radius_n, water_r.inputs[0])
    link_sockets(tree, water_level_n, water_r.inputs[1])
    link_sockets(tree, water_r.outputs["Value"], water.inputs["Radius"])
    water_pos = safe_node(tree, "GeometryNodeTransform", (bx - 200, by + 200))
    link_sockets(tree, water.outputs["Mesh"], water_pos.inputs["Geometry"])
    water_z = safe_node(tree, "ShaderNodeMath", (bx - 400, by + 80))
    water_z.operation = "MULTIPLY"
    link_sockets(tree, depth_n, water_z.inputs[0])
    link_sockets(tree, water_level_n, water_z.inputs[1])
    water_offset = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 400, by + 20))
    water_offset.inputs["X"].default_value = 0.0
    water_offset.inputs["Y"].default_value = 0.0
    link_sockets(tree, water_z.outputs["Value"], water_offset.inputs["Z"])
    link_sockets(tree, water_offset.outputs["Vector"], water_pos.inputs["Translation"])

    # Broken mirror shards: small cubes scattered on the basin rim
    shard_pts = safe_node(tree, "GeometryNodeDistributePointsOnFaces", (bx - 400, by))
    link_sockets(tree, basin.outputs["Mesh"], shard_pts.inputs["Mesh"])
    shard_pts.distribute_method = "RANDOM"
    shard_seed = safe_node(tree, "ShaderNodeMath", (bx - 600, by - 60))
    shard_seed.operation = "ADD"
    link_sockets(tree, shard_n, shard_seed.inputs[0])
    shard_seed.inputs[1].default_value = 3900.0
    link_sockets(tree, shard_seed.outputs["Value"], shard_pts.inputs["Seed"])

    shard_cube = safe_node(tree, "GeometryNodeMeshCube", (bx - 200, by))
    shard_cube.inputs["Size"].default_value = (0.08, 0.02, 0.12)
    shard_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx, by))
    link_sockets(tree, shard_pts.outputs["Points"], shard_inst.inputs["Points"])
    link_sockets(tree, shard_cube.outputs["Mesh"], shard_inst.inputs["Instance"])
    shard_realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 200, by))
    link_sockets(tree, shard_inst.outputs["Instances"], shard_realize.inputs["Geometry"])

    # Join basin + water + shards
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 400, by + 200))
    link_sockets(tree, basin_pos.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, water_pos.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, shard_realize.outputs["Geometry"], join.inputs["Geometry"])

    link_sockets(tree, join.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(basin, "geometry")
    color_node(water, "water")
    color_node(shard_cube, "emissive")
    color_node(join, "geometry")

    return label_tree(tree, "MEL_monolith_tide_pool", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Basin", "nodes": ("basin", "basin_pos"), "role": "geometry"},
        {"title": "Water", "nodes": ("water", "water_pos"), "role": "water"},
        {"title": "Shards", "nodes": ("shard_pts", "shard_cube", "shard_inst", "shard_realize"), "role": "emissive"},
        {"title": "Output", "nodes": ("join", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# 5. MEL_monolith_reflection_portal
# -----------------------------------------------------------------------------

def build_monolith_reflection_portal(group_name="MEL_monolith_reflection_portal"):
    """Reflection portal frame -- a broken arch or doorway that shows the
    same impossible ocean in every reflective surface. The frame is the
    readable structure; the reflection is implied via material (emissive +
    planar reflection in the MI layer).

    Inputs:
      Width, Height, Arch Point, Frame Thickness, Broken Top
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    width_n = add_float_param(tree, "Width", 4.0, 0.5, 40.0)
    height_n = add_float_param(tree, "Height", 7.0, 0.5, 60.0)
    arch_n = add_float_param(tree, "Arch Point", 0.35, 0.0, 1.0)
    frame_n = add_float_param(tree, "Frame Thickness", 0.35, 0.02, 3.0)
    broken_n = add_float_param(tree, "Broken Top", 0.3, 0.0, 1.0)

    # Outer frame: rectangle
    outer = safe_node(tree, "GeometryNodeMeshCube", (bx - 400, by + 400))
    outer_size = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 600, by + 320))
    link_sockets(tree, width_n, outer_size.inputs["X"])
    link_sockets(tree, height_n, outer_size.inputs["Z"])
    outer_size.inputs["Y"].default_value = frame_n.outputs["Value"].default_value if hasattr(frame_n, "outputs") else 0.35
    link_sockets(tree, outer_size.outputs["Vector"], outer.inputs["Size"])

    # Inner cutout: slightly smaller rectangle
    inner = safe_node(tree, "GeometryNodeMeshCube", (bx - 400, by + 200))
    inner_size = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 600, by + 140))
    inner_w = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 80))
    inner_w.operation = "SUBTRACT"
    link_sockets(tree, width_n, inner_w.inputs[0])
    link_sockets(tree, frame_n, inner_w.inputs[1])
    link_sockets(tree, inner_w.outputs["Value"], inner_size.inputs["X"])
    inner_h = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 200))
    inner_h.operation = "SUBTRACT"
    link_sockets(tree, height_n, inner_h.inputs[0])
    link_sockets(tree, frame_n, inner_h.inputs[1])
    link_sockets(tree, inner_h.outputs["Value"], inner_size.inputs["Z"])
    inner_size.inputs["Y"].default_value = 2.0
    link_sockets(tree, inner_size.outputs["Vector"], inner.inputs["Size"])

    # Boolean difference: outer minus inner = frame
    boolean = safe_node(tree, "GeometryNodeMeshBoolean", (bx - 200, by + 300))
    boolean.operation = "DIFFERENCE"
    link_sockets(tree, outer.outputs["Mesh"], boolean.inputs["Mesh 1"])
    link_sockets(tree, inner.outputs["Mesh"], boolean.inputs["Mesh 2"])

    # Arch cap: cone on top for gothic pointed-arch feel
    arch = safe_node(tree, "GeometryNodeMeshCone", (bx - 400, by))
    arch.inputs["Vertices"].default_value = 8
    arch_r = safe_node(tree, "ShaderNodeMath", (bx - 600, by - 60))
    arch_r.operation = "MULTIPLY"
    link_sockets(tree, width_n, arch_r.inputs[0])
    arch_r.inputs[1].default_value = 0.55
    link_sockets(tree, arch_r.outputs["Value"], arch.inputs["Radius Bottom"])
    arch.inputs["Radius Top"].default_value = 0.0
    arch_h = safe_node(tree, "ShaderNodeMath", (bx - 600, by - 120))
    arch_h.operation = "MULTIPLY"
    link_sockets(tree, height_n, arch_h.inputs[0])
    link_sockets(tree, arch_n, arch_h.inputs[1])
    link_sockets(tree, arch_h.outputs["Value"], arch.inputs["Depth"])
    arch_pos = safe_node(tree, "GeometryNodeTransform", (bx - 200, by))
    link_sockets(tree, arch.outputs["Mesh"], arch_pos.inputs["Geometry"])
    arch_z = safe_node(tree, "ShaderNodeMath", (bx - 400, by - 180))
    arch_z.operation = "MULTIPLY"
    link_sockets(tree, height_n, arch_z.inputs[0])
    arch_z.inputs[1].default_value = 0.5
    arch_offset = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 400, by - 240))
    arch_offset.inputs["X"].default_value = 0.0
    arch_offset.inputs["Y"].default_value = 0.0
    link_sockets(tree, arch_z.outputs["Value"], arch_offset.inputs["Z"])
    link_sockets(tree, arch_offset.outputs["Vector"], arch_pos.inputs["Translation"])

    # Broken top: scale the arch down and offset it to look fractured
    broken_scale = safe_node(tree, "GeometryNodeTransform", (bx, by))
    link_sockets(tree, arch_pos.outputs["Geometry"], broken_scale.inputs["Geometry"])
    broken_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 200, by - 300))
    one_minus = safe_node(tree, "ShaderNodeMath", (bx - 300, by - 360))
    one_minus.operation = "SUBTRACT"
    one_minus.inputs[0].default_value = 1.0
    link_sockets(tree, broken_n, one_minus.inputs[1])
    link_sockets(tree, one_minus.outputs["Value"], broken_vec.inputs["X"])
    broken_vec.inputs["Y"].default_value = 1.0
    link_sockets(tree, one_minus.outputs["Value"], broken_vec.inputs["Z"])
    link_sockets(tree, broken_vec.outputs["Vector"], broken_scale.inputs["Scale"])

    # Join frame + arch
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200, by + 200))
    link_sockets(tree, boolean.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, broken_scale.outputs["Geometry"], join.inputs["Geometry"])

    link_sockets(tree, join.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(outer, "geometry")
    color_node(inner, "geometry")
    color_node(boolean, "geometry")
    color_node(arch, "geometry")
    color_node(join, "geometry")

    return label_tree(tree, "MEL_monolith_reflection_portal", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Frame", "nodes": ("outer", "inner", "boolean"), "role": "geometry"},
        {"title": "Arch", "nodes": ("arch", "arch_pos", "broken_scale"), "role": "geometry"},
        {"title": "Output", "nodes": ("join", "Group Output"), "role": "output"},
    ])


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def _get_or_create_spire_tree():
    """Get or create the shared spire node tree for instancing."""
    name = "MEL_monolith_spire"
    if name in bpy.data.node_groups:
        return bpy.data.node_groups[name]
    return build_monolith_spire(name).node_tree if False else None


# -----------------------------------------------------------------------------
# Registry
# -----------------------------------------------------------------------------

from .core import register_builder

register_builder("MEL_monolith_spire", build_monolith_spire, "Monolith Spire",
    "Gothic coastal basalt spire with mirror inlay and tide-pool basin",
    "monolith")

register_builder("MEL_monolith_field", build_monolith_field, "Monolith Field",
    "Scatter monolith spires across a 2D plane with noise-driven variation",
    "monolith")

register_builder("MEL_monolith_manta_silhouette", build_monolith_manta_silhouette, "Manta Silhouette",
    "Manta-ray silhouette curve -- implied body beneath reflection pools",
    "monolith")

register_builder("MEL_monolith_tide_pool", build_monolith_tide_pool, "Tide Pool",
    "Tide pool basin with reflective water plane and broken mirror shards",
    "monolith")

register_builder("MEL_monolith_reflection_portal", build_monolith_reflection_portal, "Reflection Portal",
    "Broken gothic arch frame showing the same impossible ocean in every reflection",
    "monolith")
