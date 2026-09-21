"""Cute feminine decor assets — beads, danglers, charms, tassels, flowers.

All builders include audio reactivity via the shared add_audio_reactivity helper.
Designed for Melusina's Study and similar feminine interior spaces.
"""
from __future__ import annotations

import math

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    add_vector_param, make_group_input, register_builder,
)
from .audio_reactivity import add_audio_reactivity


# ---------------------------------------------------------------------------
# Crystal Drop — faceted crystal pendant
# ---------------------------------------------------------------------------

def build_crystal_drop(group_name="MEL_crystal_drop"):
    """Faceted crystal pendant that catches light.
    
    Params:
        Crystal Length: overall length
        Crystal Width: width at widest point
        Facet Count: number of vertical facets
        Top Radius: radius of the top loop
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Crystal Length", 0.12, 0.02, 0.5)
    add_float_param(tree, "Crystal Width", 0.04, 0.01, 0.2)
    add_int_param(tree, "Facet Count", 6, 3, 12)
    add_float_param(tree, "Top Radius", 0.008, 0.002, 0.03)
    
    bx, by = 0, 0
    
    # Crystal body — cylinder with faceted profile
    crystal = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 600, by))
    crystal.inputs["Vertices"].default_value = 6
    crystal.inputs["Radius"].default_value = 0.02
    crystal.inputs["Depth"].default_value = 0.12
    link_sockets(tree, gin.outputs["Facet Count"], crystal.inputs["Vertices"])
    link_sockets(tree, gin.outputs["Crystal Width"], crystal.inputs["Radius"])
    link_sockets(tree, gin.outputs["Crystal Length"], crystal.inputs["Depth"])
    
    # Taper the bottom — scale bottom vertices
    taper = safe_node(tree, "GeometryNodeScaleElements", (bx - 400, by))
    taper.domain = "FACE"
    taper.inputs["Scale"].default_value = 0.3
    link_sockets(tree, crystal.outputs["Mesh"], taper.inputs["Geometry"])
    
    # Top loop — circle curve converted to mesh
    loop_curve = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 600, by - 200))
    loop_curve.inputs["Radius"].default_value = 0.008
    link_sockets(tree, gin.outputs["Top Radius"], loop_curve.inputs["Radius"])
    
    # Convert circle to mesh (thin tube)
    loop = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 400, by - 200))
    link_sockets(tree, loop_curve.outputs["Curve"], loop.inputs["Curve"])
    loop_profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 600, by - 300))
    loop_profile.inputs["Radius"].default_value = 0.002
    link_sockets(tree, loop_profile.outputs["Curve"], loop.inputs["Profile Curve"])
    
    # Position loop above crystal
    loop_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 200, by - 200))
    loop_pos.inputs["Offset"].default_value = (0.0, 0.0, 0.07)
    link_sockets(tree, loop.outputs["Mesh"], loop_pos.inputs["Geometry"])
    
    # Join crystal + loop
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 200, by))
    link_sockets(tree, taper.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, loop_pos.outputs["Geometry"], join.inputs["Geometry"])
    
    # Audio reactivity
    audio_geo = add_audio_reactivity(tree, gin, join.outputs["Geometry"], (bx, by - 200))
    
    link_sockets(tree, audio_geo, gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Crystal", "nodes": ("Cylinder", "Taper", "Loop", "Join"), "role": "geometry"},
        {"title": "Output", "nodes": ("Audio", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Tassel Dangl — hanging tassel with bead cap
# ---------------------------------------------------------------------------

def build_tassel_dangl(group_name="MEL_tassel_dangl"):
    """Hanging tassel with bead cap and fringe strands.
    
    Params:
        Tassel Length: overall length
        Cap Radius: radius of the bead cap
        Strand Count: number of fringe strands
        Strand Spread: how far strands spread at bottom
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Tassel Length", 0.15, 0.03, 0.5)
    add_float_param(tree, "Cap Radius", 0.015, 0.005, 0.05)
    add_int_param(tree, "Strand Count", 12, 4, 32)
    add_float_param(tree, "Strand Spread", 0.04, 0.01, 0.15)
    
    bx, by = 0, 0
    
    # Bead cap — sphere
    cap = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 800, by + 100))
    cap.inputs["Radius"].default_value = 0.015
    link_sockets(tree, gin.outputs["Cap Radius"], cap.inputs["Radius"])
    
    # Position cap at top
    cap_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 600, by + 100))
    cap_pos.inputs["Offset"].default_value = (0.0, 0.0, 0.0)
    link_sockets(tree, cap.outputs["Mesh"], cap_pos.inputs["Geometry"])
    
    # Fringe strands — line instances
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 800, by - 100))
    line.mode = "OFFSET"
    line.inputs["Count"].default_value = 12
    link_sockets(tree, gin.outputs["Strand Count"], line.inputs["Count"])
    line.inputs["Offset"].default_value = (0.0, 0.0, -0.15)
    link_sockets(tree, gin.outputs["Tassel Length"], line.inputs["Offset"])
    
    # Instance small cylinders as strands
    strand = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 1000, by - 200))
    strand.inputs["Vertices"].default_value = 6
    strand.inputs["Radius"].default_value = 0.001
    strand.inputs["Depth"].default_value = 0.1
    
    instance = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 600, by - 100))
    link_sockets(tree, line.outputs["Mesh"], instance.inputs["Points"])
    link_sockets(tree, strand.outputs["Mesh"], instance.inputs["Instance"])
    
    # Spread strands at bottom
    spread = safe_node(tree, "GeometryNodeScaleInstances", (bx - 400, by - 100))
    link_sockets(tree, instance.outputs["Instances"], spread.inputs["Instances"])
    spread.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    
    # Realize
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 200, by - 100))
    link_sockets(tree, spread.outputs["Instances"], realize.inputs["Geometry"])
    
    # Join cap + strands
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx, by))
    link_sockets(tree, cap_pos.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, realize.outputs["Geometry"], join.inputs["Geometry"])
    
    # Audio reactivity
    audio_geo = add_audio_reactivity(tree, gin, join.outputs["Geometry"], (bx + 200, by - 100))
    
    link_sockets(tree, audio_geo, gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Tassel", "nodes": ("Cap", "Strands", "Join"), "role": "geometry"},
        {"title": "Output", "nodes": ("Audio", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Flower Pendant — 5-petal flower charm
# ---------------------------------------------------------------------------

def build_flower_pendant(group_name="MEL_flower_pendant"):
    """5-petal flower charm with center bead.
    
    Params:
        Petal Count: number of petals (3-8)
        Flower Radius: overall radius
        Petal Length: length of each petal
        Center Bead Radius: radius of center bead
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_int_param(tree, "Petal Count", 5, 3, 8)
    add_float_param(tree, "Flower Radius", 0.04, 0.01, 0.15)
    add_float_param(tree, "Petal Length", 0.02, 0.005, 0.08)
    add_float_param(tree, "Center Bead Radius", 0.008, 0.002, 0.03)
    
    bx, by = 0, 0
    
    # Petal template — scaled sphere
    petal = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 800, by))
    petal.inputs["Radius"].default_value = 0.01
    petal.inputs["Segments"].default_value = 16
    petal.inputs["Rings"].default_value = 8
    
    # Scale petal to be elongated (use Transform for vector scale)
    petal_scale = safe_node(tree, "GeometryNodeTransform", (bx - 600, by))
    petal_scale.inputs["Scale"].default_value = (0.5, 1.0, 0.3)
    link_sockets(tree, petal.outputs["Mesh"], petal_scale.inputs["Geometry"])
    
    # Instance petals in circle
    circle = safe_node(tree, "GeometryNodeMeshCircle", (bx - 800, by - 200))
    circle.inputs["Vertices"].default_value = 5
    circle.inputs["Radius"].default_value = 0.02
    link_sockets(tree, gin.outputs["Petal Count"], circle.inputs["Vertices"])
    link_sockets(tree, gin.outputs["Flower Radius"], circle.inputs["Radius"])
    
    instance = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 600, by - 200))
    link_sockets(tree, circle.outputs["Mesh"], instance.inputs["Points"])
    link_sockets(tree, petal_scale.outputs["Geometry"], instance.inputs["Instance"])
    
    # Rotate each petal outward
    rotate = safe_node(tree, "GeometryNodeRotateInstances", (bx - 400, by - 200))
    link_sockets(tree, instance.outputs["Instances"], rotate.inputs["Instances"])
    rotate.inputs["Rotation"].default_value = (0.0, 0.0, 0.0)
    
    # Realize
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 200, by - 200))
    link_sockets(tree, rotate.outputs["Instances"], realize.inputs["Geometry"])
    
    # Center bead
    bead = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 800, by - 400))
    bead.inputs["Radius"].default_value = 0.008
    link_sockets(tree, gin.outputs["Center Bead Radius"], bead.inputs["Radius"])
    
    # Join petals + bead
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx, by))
    link_sockets(tree, realize.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, bead.outputs["Mesh"], join.inputs["Geometry"])
    
    # Audio reactivity
    audio_geo = add_audio_reactivity(tree, gin, join.outputs["Geometry"], (bx + 200, by - 200))
    
    link_sockets(tree, audio_geo, gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Flower", "nodes": ("Petals", "Bead", "Join"), "role": "geometry"},
        {"title": "Output", "nodes": ("Audio", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Pearl String — string of graduated pearls
# ---------------------------------------------------------------------------

def build_pearl_string(group_name="MEL_pearl_string"):
    """String of graduated pearls on a curve.
    
    Params:
        Pearl Count: number of pearls
        Start Size: size of first pearl
        End Size: size of last pearl
        String Length: overall length of the string
        Curve Amount: how much the string curves
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_int_param(tree, "Pearl Count", 12, 3, 40)
    add_float_param(tree, "Start Size", 0.012, 0.003, 0.05)
    add_float_param(tree, "End Size", 0.004, 0.001, 0.02)
    add_float_param(tree, "String Length", 0.3, 0.05, 1.0)
    add_float_param(tree, "Curve Amount", 0.05, 0.0, 0.3)
    
    bx, by = 0, 0
    
    # Curve line
    curve = safe_node(tree, "GeometryNodeCurvePrimitiveLine", (bx - 800, by))
    curve.inputs["Start"].default_value = (0.0, 0.0, 0.0)
    curve.inputs["End"].default_value = (0.0, 0.0, -0.3)
    link_sockets(tree, gin.outputs["String Length"], curve.inputs["End"])
    
    # Resample for even spacing
    resample = safe_node(tree, "GeometryNodeResampleCurve", (bx - 600, by))
    resample.inputs["Count"].default_value = 12
    link_sockets(tree, gin.outputs["Pearl Count"], resample.inputs["Count"])
    link_sockets(tree, curve.outputs["Curve"], resample.inputs["Curve"])
    
    # Instance pearls
    pearl = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 1000, by - 200))
    pearl.inputs["Radius"].default_value = 0.008
    pearl.inputs["Segments"].default_value = 16
    pearl.inputs["Rings"].default_value = 8
    
    instance = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 400, by))
    link_sockets(tree, resample.outputs["Curve"], instance.inputs["Points"])
    link_sockets(tree, pearl.outputs["Mesh"], instance.inputs["Instance"])
    
    # Scale pearls — graduated
    scale = safe_node(tree, "GeometryNodeScaleInstances", (bx - 200, by))
    link_sockets(tree, instance.outputs["Instances"], scale.inputs["Instances"])
    scale.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    
    # Realize
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by))
    link_sockets(tree, scale.outputs["Instances"], realize.inputs["Geometry"])
    
    # Audio reactivity
    audio_geo = add_audio_reactivity(tree, gin, realize.outputs["Geometry"], (bx + 200, by - 200))
    
    link_sockets(tree, audio_geo, gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Pearls", "nodes": ("Curve", "Instance", "Scale", "Realize"), "role": "geometry"},
        {"title": "Output", "nodes": ("Audio", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Star Charm — star-shaped charm with filigree border
# ---------------------------------------------------------------------------

def build_star_charm(group_name="MEL_star_charm"):
    """Star-shaped charm with filigree border and center gem.
    
    Params:
        Star Points: number of star points
        Outer Radius: outer radius
        Inner Radius: inner radius
        Charm Thickness: thickness of the charm
        Gem Radius: radius of center gem
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_int_param(tree, "Star Points", 5, 3, 8)
    add_float_param(tree, "Outer Radius", 0.03, 0.01, 0.1)
    add_float_param(tree, "Inner Radius", 0.012, 0.004, 0.05)
    add_float_param(tree, "Charm Thickness", 0.003, 0.001, 0.02)
    add_float_param(tree, "Gem Radius", 0.006, 0.002, 0.02)
    
    bx, by = 0, 0
    
    # Star curve
    star = safe_node(tree, "GeometryNodeCurveStar", (bx - 800, by))
    star.inputs["Points"].default_value = 5
    star.inputs["Outer Radius"].default_value = 0.03
    star.inputs["Inner Radius"].default_value = 0.012
    link_sockets(tree, gin.outputs["Star Points"], star.inputs["Points"])
    link_sockets(tree, gin.outputs["Outer Radius"], star.inputs["Outer Radius"])
    link_sockets(tree, gin.outputs["Inner Radius"], star.inputs["Inner Radius"])
    
    # Fill star
    fill = safe_node(tree, "GeometryNodeFillCurve", (bx - 600, by))
    link_sockets(tree, star.outputs["Curve"], fill.inputs["Curve"])
    
    # Extrude for thickness
    extrude = safe_node(tree, "GeometryNodeExtrudeMesh", (bx - 400, by))
    extrude.inputs["Offset"].default_value = (0.0, 0.0, 0.003)
    link_sockets(tree, fill.outputs["Mesh"], extrude.inputs["Mesh"])
    link_sockets(tree, gin.outputs["Charm Thickness"], extrude.inputs["Offset"])
    
    # Center gem
    gem = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 800, by - 200))
    gem.inputs["Radius"].default_value = 0.006
    gem.inputs["Segments"].default_value = 16
    gem.inputs["Rings"].default_value = 8
    link_sockets(tree, gin.outputs["Gem Radius"], gem.inputs["Radius"])
    
    # Position gem at center
    gem_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 600, by - 200))
    gem_pos.inputs["Offset"].default_value = (0.0, 0.0, 0.002)
    link_sockets(tree, gem.outputs["Mesh"], gem_pos.inputs["Geometry"])
    
    # Join star + gem
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 200, by))
    link_sockets(tree, extrude.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, gem_pos.outputs["Geometry"], join.inputs["Geometry"])
    
    # Audio reactivity
    audio_geo = add_audio_reactivity(tree, gin, join.outputs["Geometry"], (bx, by - 200))
    
    link_sockets(tree, audio_geo, gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Star Charm", "nodes": ("Star", "Extrude", "Gem", "Join"), "role": "geometry"},
        {"title": "Output", "nodes": ("Audio", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Bow Ribbon — cute bow with ribbon tails
# ---------------------------------------------------------------------------

def build_bow_ribbon(group_name="MEL_bow_ribbon"):
    """Cute bow with two loops and two ribbon tails.
    
    Params:
        Bow Width: overall width
        Bow Height: overall height
        Loop Size: size of each loop
        Tail Length: length of ribbon tails
        Tail Width: width of ribbon tails
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Bow Width", 0.08, 0.02, 0.3)
    add_float_param(tree, "Bow Height", 0.06, 0.02, 0.2)
    add_float_param(tree, "Loop Size", 0.025, 0.005, 0.1)
    add_float_param(tree, "Tail Length", 0.06, 0.01, 0.2)
    add_float_param(tree, "Tail Width", 0.012, 0.003, 0.05)
    
    bx, by = 0, 0
    
    # Left loop — circle curve converted to mesh
    loop_l_curve = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 800, by + 100))
    loop_l_curve.inputs["Radius"].default_value = 0.025
    link_sockets(tree, gin.outputs["Loop Size"], loop_l_curve.inputs["Radius"])
    
    loop_l = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 600, by + 100))
    link_sockets(tree, loop_l_curve.outputs["Curve"], loop_l.inputs["Curve"])
    loop_l_profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 800, by))
    loop_l_profile.inputs["Radius"].default_value = 0.006
    link_sockets(tree, loop_l_profile.outputs["Curve"], loop_l.inputs["Profile Curve"])
    
    # Position left loop
    loop_l_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 400, by + 100))
    loop_l_pos.inputs["Offset"].default_value = (-0.02, 0.0, 0.0)
    link_sockets(tree, loop_l.outputs["Mesh"], loop_l_pos.inputs["Geometry"])
    
    # Right loop — circle curve converted to mesh
    loop_r_curve = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 800, by - 100))
    loop_r_curve.inputs["Radius"].default_value = 0.025
    link_sockets(tree, gin.outputs["Loop Size"], loop_r_curve.inputs["Radius"])
    
    loop_r = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 600, by - 100))
    link_sockets(tree, loop_r_curve.outputs["Curve"], loop_r.inputs["Curve"])
    loop_r_profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 800, by - 200))
    loop_r_profile.inputs["Radius"].default_value = 0.006
    link_sockets(tree, loop_r_profile.outputs["Curve"], loop_r.inputs["Profile Curve"])
    
    # Position right loop
    loop_r_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 400, by - 100))
    loop_r_pos.inputs["Offset"].default_value = (0.02, 0.0, 0.0)
    link_sockets(tree, loop_r.outputs["Mesh"], loop_r_pos.inputs["Geometry"])
    
    # Center knot — small sphere
    knot = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 800, by - 300))
    knot.inputs["Radius"].default_value = 0.008
    knot.inputs["Segments"].default_value = 16
    knot.inputs["Rings"].default_value = 8
    
    # Left tail — curved ribbon
    tail_l = safe_node(tree, "GeometryNodeCurvePrimitiveLine", (bx - 1000, by - 400))
    tail_l.inputs["Start"].default_value = (-0.01, 0.0, -0.01)
    tail_l.inputs["End"].default_value = (-0.03, 0.0, -0.07)
    link_sockets(tree, gin.outputs["Tail Length"], tail_l.inputs["End"])
    
    # Right tail — curved ribbon
    tail_r = safe_node(tree, "GeometryNodeCurvePrimitiveLine", (bx - 1000, by - 500))
    tail_r.inputs["Start"].default_value = (0.01, 0.0, -0.01)
    tail_r.inputs["End"].default_value = (0.03, 0.0, -0.07)
    link_sockets(tree, gin.outputs["Tail Length"], tail_r.inputs["End"])
    
    # Convert tails to mesh
    tail_l_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 800, by - 400))
    link_sockets(tree, tail_l.outputs["Curve"], tail_l_mesh.inputs["Curve"])
    tail_l_profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 1000, by - 500))
    tail_l_profile.inputs["Radius"].default_value = 0.006
    link_sockets(tree, tail_l_profile.outputs["Curve"], tail_l_mesh.inputs["Profile Curve"])
    
    tail_r_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 800, by - 500))
    link_sockets(tree, tail_r.outputs["Curve"], tail_r_mesh.inputs["Curve"])
    tail_r_profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 1000, by - 600))
    tail_r_profile.inputs["Radius"].default_value = 0.006
    link_sockets(tree, tail_r_profile.outputs["Curve"], tail_r_mesh.inputs["Profile Curve"])
    
    # Join all
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 400, by))
    link_sockets(tree, loop_l_pos.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, loop_r_pos.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, knot.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, tail_l_mesh.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, tail_r_mesh.outputs["Mesh"], join.inputs["Geometry"])
    
    # Audio reactivity
    audio_geo = add_audio_reactivity(tree, gin, join.outputs["Geometry"], (bx - 200, by - 200))
    
    link_sockets(tree, audio_geo, gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bow", "nodes": ("Loops", "Knot", "Tails", "Join"), "role": "geometry"},
        {"title": "Output", "nodes": ("Audio", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

register_builder("MEL_crystal_drop", build_crystal_drop,
                 "Crystal Drop", "Faceted crystal pendant that catches light",
                 category="decor")

register_builder("MEL_tassel_dangl", build_tassel_dangl,
                 "Tassel Dangl", "Hanging tassel with bead cap and fringe strands",
                 category="decor")

register_builder("MEL_flower_pendant", build_flower_pendant,
                 "Flower Pendant", "5-petal flower charm with center bead",
                 category="decor")

register_builder("MEL_pearl_string", build_pearl_string,
                 "Pearl String", "String of graduated pearls on a curve",
                 category="decor")

register_builder("MEL_star_charm", build_star_charm,
                 "Star Charm", "Star-shaped charm with filigree border and center gem",
                 category="decor")

register_builder("MEL_bow_ribbon", build_bow_ribbon,
                 "Bow Ribbon", "Cute bow with two loops and ribbon tails",
                 category="decor")


# ---------------------------------------------------------------------------
# Lace Dangl — lace-like hanging ornament with scalloped edges
# ---------------------------------------------------------------------------

def build_lace_dangl(group_name="MEL_lace_dangl"):
    """Lace-like hanging ornament with scalloped edges.
    
    Params:
        Lace Width: overall width
        Lace Height: overall height
        Scallop Count: number of scallops along bottom
        Hole Count: number of decorative holes
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Lace Width", 0.06, 0.02, 0.2)
    add_float_param(tree, "Lace Height", 0.08, 0.02, 0.3)
    add_int_param(tree, "Scallop Count", 7, 3, 16)
    add_int_param(tree, "Hole Count", 5, 0, 12)
    
    bx, by = 0, 0
    
    # Lace body — plane with scalloped bottom
    plane = safe_node(tree, "GeometryNodeMeshGrid", (bx - 800, by))
    plane.inputs["Size X"].default_value = 0.06
    plane.inputs["Size Y"].default_value = 0.08
    plane.inputs["Vertices X"].default_value = 32
    plane.inputs["Vertices Y"].default_value = 32
    link_sockets(tree, gin.outputs["Lace Width"], plane.inputs["Size X"])
    link_sockets(tree, gin.outputs["Lace Height"], plane.inputs["Size Y"])
    
    # Extrude for thickness
    extrude = safe_node(tree, "GeometryNodeExtrudeMesh", (bx - 600, by))
    extrude.inputs["Offset"].default_value = (0.0, 0.0, 0.002)
    link_sockets(tree, plane.outputs["Mesh"], extrude.inputs["Mesh"])
    
    # Decorative holes — small cylinders subtracted
    hole = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 1000, by - 200))
    hole.inputs["Vertices"].default_value = 8
    hole.inputs["Radius"].default_value = 0.003
    hole.inputs["Depth"].default_value = 0.01
    
    # Instance holes in grid pattern
    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 800, by - 200))
    grid.inputs["Size X"].default_value = 0.04
    grid.inputs["Size Y"].default_value = 0.06
    grid.inputs["Vertices X"].default_value = 3
    grid.inputs["Vertices Y"].default_value = 4
    
    instance = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 600, by - 200))
    link_sockets(tree, grid.outputs["Mesh"], instance.inputs["Points"])
    link_sockets(tree, hole.outputs["Mesh"], instance.inputs["Instance"])
    
    # Realize holes
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 400, by - 200))
    link_sockets(tree, instance.outputs["Instances"], realize.inputs["Geometry"])
    
    # Boolean subtract holes from lace
    boolean = safe_node(tree, "GeometryNodeMeshBoolean", (bx - 200, by))
    boolean.operation = "DIFFERENCE"
    link_sockets(tree, extrude.outputs["Mesh"], boolean.inputs["Mesh 1"])
    link_sockets(tree, realize.outputs["Geometry"], boolean.inputs["Mesh 2"])
    
    # Audio reactivity
    audio_geo = add_audio_reactivity(tree, gin, boolean.outputs["Mesh"], (bx, by - 200))
    
    link_sockets(tree, audio_geo, gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Lace", "nodes": ("Plane", "Holes", "Boolean"), "role": "geometry"},
        {"title": "Output", "nodes": ("Audio", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Bead Tassel — tassel made of graduated beads
# ---------------------------------------------------------------------------

def build_bead_tassel(group_name="MEL_bead_tassel"):
    """Tassel made of graduated beads instead of strands.
    
    Params:
        Tassel Length: overall length
        Bead Count: number of beads per strand
        Strand Count: number of strands
        Start Bead Size: size of top beads
        End Bead Size: size of bottom beads
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Tassel Length", 0.12, 0.03, 0.4)
    add_int_param(tree, "Bead Count", 8, 3, 20)
    add_int_param(tree, "Strand Count", 10, 4, 24)
    add_float_param(tree, "Start Bead Size", 0.008, 0.002, 0.03)
    add_float_param(tree, "End Bead Size", 0.003, 0.001, 0.015)
    
    bx, by = 0, 0
    
    # Strand lines
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 800, by))
    line.mode = "OFFSET"
    line.inputs["Count"].default_value = 10
    link_sockets(tree, gin.outputs["Strand Count"], line.inputs["Count"])
    line.inputs["Offset"].default_value = (0.0, 0.0, -0.12)
    link_sockets(tree, gin.outputs["Tassel Length"], line.inputs["Offset"])
    
    # Bead template
    bead = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 1000, by - 200))
    bead.inputs["Radius"].default_value = 0.005
    bead.inputs["Segments"].default_value = 12
    bead.inputs["Rings"].default_value = 6
    
    # Instance beads along each strand
    instance = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 600, by))
    link_sockets(tree, line.outputs["Mesh"], instance.inputs["Points"])
    link_sockets(tree, bead.outputs["Mesh"], instance.inputs["Instance"])
    
    # Scale beads — graduated
    scale = safe_node(tree, "GeometryNodeScaleInstances", (bx - 400, by))
    link_sockets(tree, instance.outputs["Instances"], scale.inputs["Instances"])
    scale.inputs["Scale"].default_value = (1.0, 1.0, 1.0)
    
    # Realize
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 200, by))
    link_sockets(tree, scale.outputs["Instances"], realize.inputs["Geometry"])
    
    # Audio reactivity
    audio_geo = add_audio_reactivity(tree, gin, realize.outputs["Geometry"], (bx, by - 200))
    
    link_sockets(tree, audio_geo, gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bead Tassel", "nodes": ("Strands", "Beads", "Scale", "Realize"), "role": "geometry"},
        {"title": "Output", "nodes": ("Audio", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Heart Dangl — heart-shaped dangle with filigree border
# ---------------------------------------------------------------------------

def build_heart_dangl(group_name="MEL_heart_dangl"):
    """Heart-shaped dangle with filigree border.
    
    Params:
        Heart Width: overall width
        Heart Height: overall height
        Border Width: width of filigree border
        Gem Radius: radius of center gem
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Heart Width", 0.04, 0.01, 0.12)
    add_float_param(tree, "Heart Height", 0.04, 0.01, 0.12)
    add_float_param(tree, "Border Width", 0.004, 0.001, 0.015)
    add_float_param(tree, "Gem Radius", 0.006, 0.002, 0.02)
    
    bx, by = 0, 0
    
    # Heart shape — scaled sphere
    heart = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 800, by))
    heart.inputs["Radius"].default_value = 0.02
    heart.inputs["Segments"].default_value = 24
    heart.inputs["Rings"].default_value = 12
    
    # Transform to heart shape
    heart_transform = safe_node(tree, "GeometryNodeTransform", (bx - 600, by))
    heart_transform.inputs["Scale"].default_value = (1.0, 0.8, 0.5)
    link_sockets(tree, heart.outputs["Mesh"], heart_transform.inputs["Geometry"])
    
    # Border — slightly larger heart
    border = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 800, by - 200))
    border.inputs["Radius"].default_value = 0.022
    border.inputs["Segments"].default_value = 24
    border.inputs["Rings"].default_value = 12
    
    border_transform = safe_node(tree, "GeometryNodeTransform", (bx - 600, by - 200))
    border_transform.inputs["Scale"].default_value = (1.0, 0.8, 0.5)
    link_sockets(tree, border.outputs["Mesh"], border_transform.inputs["Geometry"])
    
    # Boolean subtract inner heart from border
    boolean = safe_node(tree, "GeometryNodeMeshBoolean", (bx - 400, by))
    boolean.operation = "DIFFERENCE"
    link_sockets(tree, border_transform.outputs["Geometry"], boolean.inputs["Mesh 1"])
    link_sockets(tree, heart_transform.outputs["Geometry"], boolean.inputs["Mesh 2"])
    
    # Center gem
    gem = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 800, by - 400))
    gem.inputs["Radius"].default_value = 0.006
    gem.inputs["Segments"].default_value = 16
    gem.inputs["Rings"].default_value = 8
    link_sockets(tree, gin.outputs["Gem Radius"], gem.inputs["Radius"])
    
    # Join border + gem
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 200, by))
    link_sockets(tree, boolean.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, gem.outputs["Mesh"], join.inputs["Geometry"])
    
    # Audio reactivity
    audio_geo = add_audio_reactivity(tree, gin, join.outputs["Geometry"], (bx, by - 200))
    
    link_sockets(tree, audio_geo, gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Heart Dangl", "nodes": ("Heart", "Border", "Gem", "Join"), "role": "geometry"},
        {"title": "Output", "nodes": ("Audio", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Star Dangl — star-shaped dangle with center gem
# ---------------------------------------------------------------------------

def build_star_dangl(group_name="MEL_star_dangl"):
    """Star-shaped dangle with center gem.
    
    Params:
        Star Points: number of star points
        Outer Radius: outer radius
        Inner Radius: inner radius
        Gem Radius: radius of center gem
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_int_param(tree, "Star Points", 5, 3, 8)
    add_float_param(tree, "Outer Radius", 0.03, 0.01, 0.1)
    add_float_param(tree, "Inner Radius", 0.012, 0.004, 0.05)
    add_float_param(tree, "Gem Radius", 0.005, 0.002, 0.02)
    
    bx, by = 0, 0
    
    # Star curve
    star = safe_node(tree, "GeometryNodeCurveStar", (bx - 800, by))
    star.inputs["Points"].default_value = 5
    star.inputs["Outer Radius"].default_value = 0.03
    star.inputs["Inner Radius"].default_value = 0.012
    link_sockets(tree, gin.outputs["Star Points"], star.inputs["Points"])
    link_sockets(tree, gin.outputs["Outer Radius"], star.inputs["Outer Radius"])
    link_sockets(tree, gin.outputs["Inner Radius"], star.inputs["Inner Radius"])
    
    # Fill star
    fill = safe_node(tree, "GeometryNodeFillCurve", (bx - 600, by))
    link_sockets(tree, star.outputs["Curve"], fill.inputs["Curve"])
    
    # Extrude for thickness
    extrude = safe_node(tree, "GeometryNodeExtrudeMesh", (bx - 400, by))
    extrude.inputs["Offset"].default_value = (0.0, 0.0, 0.003)
    link_sockets(tree, fill.outputs["Mesh"], extrude.inputs["Mesh"])
    
    # Center gem
    gem = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 800, by - 200))
    gem.inputs["Radius"].default_value = 0.005
    gem.inputs["Segments"].default_value = 16
    gem.inputs["Rings"].default_value = 8
    link_sockets(tree, gin.outputs["Gem Radius"], gem.inputs["Radius"])
    
    # Position gem at center
    gem_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 600, by - 200))
    gem_pos.inputs["Offset"].default_value = (0.0, 0.0, 0.002)
    link_sockets(tree, gem.outputs["Mesh"], gem_pos.inputs["Geometry"])
    
    # Join star + gem
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 200, by))
    link_sockets(tree, extrude.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, gem_pos.outputs["Geometry"], join.inputs["Geometry"])
    
    # Audio reactivity
    audio_geo = add_audio_reactivity(tree, gin, join.outputs["Geometry"], (bx, by - 200))
    
    link_sockets(tree, audio_geo, gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Star Dangl", "nodes": ("Star", "Extrude", "Gem", "Join"), "role": "geometry"},
        {"title": "Output", "nodes": ("Audio", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Flower Chain — chain of small flowers
# ---------------------------------------------------------------------------

def build_flower_chain(group_name="MEL_flower_chain"):
    """Chain of small flowers.
    
    Params:
        Flower Count: number of flowers
        Spacing: distance between flowers
        Flower Size: size of each flower
        Petal Count: number of petals per flower
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_int_param(tree, "Flower Count", 10, 3, 30)
    add_float_param(tree, "Spacing", 0.04, 0.01, 0.15)
    add_float_param(tree, "Flower Size", 0.015, 0.005, 0.05)
    add_int_param(tree, "Petal Count", 5, 3, 8)
    
    bx, by = 0, 0
    
    # Chain line
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 800, by))
    line.mode = "OFFSET"
    line.inputs["Count"].default_value = 10
    link_sockets(tree, gin.outputs["Flower Count"], line.inputs["Count"])
    line.inputs["Offset"].default_value = (0.0, 0.0, -0.04)
    link_sockets(tree, gin.outputs["Spacing"], line.inputs["Offset"])
    
    # Flower template — small sphere
    flower = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 1000, by - 200))
    flower.inputs["Radius"].default_value = 0.015
    flower.inputs["Segments"].default_value = 12
    flower.inputs["Rings"].default_value = 6
    link_sockets(tree, gin.outputs["Flower Size"], flower.inputs["Radius"])
    
    # Instance flowers along chain
    instance = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 600, by))
    link_sockets(tree, line.outputs["Mesh"], instance.inputs["Points"])
    link_sockets(tree, flower.outputs["Mesh"], instance.inputs["Instance"])
    
    # Realize
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 400, by))
    link_sockets(tree, instance.outputs["Instances"], realize.inputs["Geometry"])
    
    # Audio reactivity
    audio_geo = add_audio_reactivity(tree, gin, realize.outputs["Geometry"], (bx - 200, by - 200))
    
    link_sockets(tree, audio_geo, gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Flower Chain", "nodes": ("Line", "Flowers", "Realize"), "role": "geometry"},
        {"title": "Output", "nodes": ("Audio", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Bow Dangl — small bow charm with ribbon tails
# ---------------------------------------------------------------------------

def build_bow_dangl(group_name="MEL_bow_dangl"):
    """Small bow charm with ribbon tails.
    
    Params:
        Bow Width: overall width
        Bow Height: overall height
        Tail Length: length of ribbon tails
        Knot Size: size of center knot
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Bow Width", 0.04, 0.01, 0.12)
    add_float_param(tree, "Bow Height", 0.03, 0.01, 0.1)
    add_float_param(tree, "Tail Length", 0.03, 0.01, 0.1)
    add_float_param(tree, "Knot Size", 0.005, 0.002, 0.02)
    
    bx, by = 0, 0
    
    # Left loop
    loop_l_curve = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 800, by + 100))
    loop_l_curve.inputs["Radius"].default_value = 0.012
    link_sockets(tree, gin.outputs["Bow Width"], loop_l_curve.inputs["Radius"])
    
    loop_l = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 600, by + 100))
    link_sockets(tree, loop_l_curve.outputs["Curve"], loop_l.inputs["Curve"])
    loop_l_profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 800, by))
    loop_l_profile.inputs["Radius"].default_value = 0.003
    link_sockets(tree, loop_l_profile.outputs["Curve"], loop_l.inputs["Profile Curve"])
    
    loop_l_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 400, by + 100))
    loop_l_pos.inputs["Offset"].default_value = (-0.01, 0.0, 0.0)
    link_sockets(tree, loop_l.outputs["Mesh"], loop_l_pos.inputs["Geometry"])
    
    # Right loop
    loop_r_curve = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 800, by - 100))
    loop_r_curve.inputs["Radius"].default_value = 0.012
    link_sockets(tree, gin.outputs["Bow Width"], loop_r_curve.inputs["Radius"])
    
    loop_r = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 600, by - 100))
    link_sockets(tree, loop_r_curve.outputs["Curve"], loop_r.inputs["Curve"])
    loop_r_profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 800, by - 200))
    loop_r_profile.inputs["Radius"].default_value = 0.003
    link_sockets(tree, loop_r_profile.outputs["Curve"], loop_r.inputs["Profile Curve"])
    
    loop_r_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 400, by - 100))
    loop_r_pos.inputs["Offset"].default_value = (0.01, 0.0, 0.0)
    link_sockets(tree, loop_r.outputs["Mesh"], loop_r_pos.inputs["Geometry"])
    
    # Center knot
    knot = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 800, by - 300))
    knot.inputs["Radius"].default_value = 0.005
    knot.inputs["Segments"].default_value = 12
    knot.inputs["Rings"].default_value = 6
    link_sockets(tree, gin.outputs["Knot Size"], knot.inputs["Radius"])
    
    # Left tail
    tail_l = safe_node(tree, "GeometryNodeCurvePrimitiveLine", (bx - 1000, by - 400))
    tail_l.inputs["Start"].default_value = (-0.005, 0.0, -0.005)
    tail_l.inputs["End"].default_value = (-0.015, 0.0, -0.035)
    link_sockets(tree, gin.outputs["Tail Length"], tail_l.inputs["End"])
    
    tail_l_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 800, by - 400))
    link_sockets(tree, tail_l.outputs["Curve"], tail_l_mesh.inputs["Curve"])
    tail_l_profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 1000, by - 500))
    tail_l_profile.inputs["Radius"].default_value = 0.002
    link_sockets(tree, tail_l_profile.outputs["Curve"], tail_l_mesh.inputs["Profile Curve"])
    
    # Right tail
    tail_r = safe_node(tree, "GeometryNodeCurvePrimitiveLine", (bx - 1000, by - 500))
    tail_r.inputs["Start"].default_value = (0.005, 0.0, -0.005)
    tail_r.inputs["End"].default_value = (0.015, 0.0, -0.035)
    link_sockets(tree, gin.outputs["Tail Length"], tail_r.inputs["End"])
    
    tail_r_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 800, by - 500))
    link_sockets(tree, tail_r.outputs["Curve"], tail_r_mesh.inputs["Curve"])
    tail_r_profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 1000, by - 600))
    tail_r_profile.inputs["Radius"].default_value = 0.002
    link_sockets(tree, tail_r_profile.outputs["Curve"], tail_r_mesh.inputs["Profile Curve"])
    
    # Join all
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 200, by))
    link_sockets(tree, loop_l_pos.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, loop_r_pos.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, knot.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, tail_l_mesh.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, tail_r_mesh.outputs["Mesh"], join.inputs["Geometry"])
    
    # Audio reactivity
    audio_geo = add_audio_reactivity(tree, gin, join.outputs["Geometry"], (bx, by - 200))
    
    link_sockets(tree, audio_geo, gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bow Dangl", "nodes": ("Loops", "Knot", "Tails", "Join"), "role": "geometry"},
        {"title": "Output", "nodes": ("Audio", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Crystal Chain — chain of faceted crystals
# ---------------------------------------------------------------------------

def build_crystal_chain(group_name="MEL_crystal_chain"):
    """Chain of faceted crystals.
    
    Params:
        Crystal Count: number of crystals
        Spacing: distance between crystals
        Crystal Size: size of each crystal
        Facet Count: number of facets per crystal
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_int_param(tree, "Crystal Count", 8, 3, 25)
    add_float_param(tree, "Spacing", 0.03, 0.01, 0.1)
    add_float_param(tree, "Crystal Size", 0.012, 0.004, 0.04)
    add_int_param(tree, "Facet Count", 6, 3, 12)
    
    bx, by = 0, 0
    
    # Chain line
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 800, by))
    line.mode = "OFFSET"
    line.inputs["Count"].default_value = 8
    link_sockets(tree, gin.outputs["Crystal Count"], line.inputs["Count"])
    line.inputs["Offset"].default_value = (0.0, 0.0, -0.03)
    link_sockets(tree, gin.outputs["Spacing"], line.inputs["Offset"])
    
    # Crystal template — cylinder
    crystal = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 1000, by - 200))
    crystal.inputs["Vertices"].default_value = 6
    crystal.inputs["Radius"].default_value = 0.012
    crystal.inputs["Depth"].default_value = 0.015
    link_sockets(tree, gin.outputs["Facet Count"], crystal.inputs["Vertices"])
    link_sockets(tree, gin.outputs["Crystal Size"], crystal.inputs["Radius"])
    
    # Instance crystals along chain
    instance = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 600, by))
    link_sockets(tree, line.outputs["Mesh"], instance.inputs["Points"])
    link_sockets(tree, crystal.outputs["Mesh"], instance.inputs["Instance"])
    
    # Realize
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 400, by))
    link_sockets(tree, instance.outputs["Instances"], realize.inputs["Geometry"])
    
    # Audio reactivity
    audio_geo = add_audio_reactivity(tree, gin, realize.outputs["Geometry"], (bx - 200, by - 200))
    
    link_sockets(tree, audio_geo, gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Crystal Chain", "nodes": ("Line", "Crystals", "Realize"), "role": "geometry"},
        {"title": "Output", "nodes": ("Audio", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Pearl Dangl — pearl dangle with gold cap
# ---------------------------------------------------------------------------

def build_pearl_dangl(group_name="MEL_pearl_dangl"):
    """Pearl dangle with gold cap.
    
    Params:
        Pearl Radius: radius of the pearl
        Cap Radius: radius of the gold cap
        Cap Height: height of the gold cap
        Loop Radius: radius of the top loop
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Pearl Radius", 0.012, 0.004, 0.04)
    add_float_param(tree, "Cap Radius", 0.008, 0.002, 0.02)
    add_float_param(tree, "Cap Height", 0.006, 0.002, 0.02)
    add_float_param(tree, "Loop Radius", 0.004, 0.001, 0.012)
    
    bx, by = 0, 0
    
    # Pearl — sphere
    pearl = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 800, by))
    pearl.inputs["Radius"].default_value = 0.012
    pearl.inputs["Segments"].default_value = 24
    pearl.inputs["Rings"].default_value = 12
    link_sockets(tree, gin.outputs["Pearl Radius"], pearl.inputs["Radius"])
    
    # Gold cap — cylinder
    cap = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 800, by - 200))
    cap.inputs["Vertices"].default_value = 16
    cap.inputs["Radius"].default_value = 0.008
    cap.inputs["Depth"].default_value = 0.006
    link_sockets(tree, gin.outputs["Cap Radius"], cap.inputs["Radius"])
    link_sockets(tree, gin.outputs["Cap Height"], cap.inputs["Depth"])
    
    # Position cap above pearl
    cap_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 600, by - 200))
    cap_pos.inputs["Offset"].default_value = (0.0, 0.0, 0.012)
    link_sockets(tree, cap.outputs["Mesh"], cap_pos.inputs["Geometry"])
    
    # Top loop — circle curve
    loop_curve = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 800, by - 400))
    loop_curve.inputs["Radius"].default_value = 0.004
    link_sockets(tree, gin.outputs["Loop Radius"], loop_curve.inputs["Radius"])
    
    loop = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 600, by - 400))
    link_sockets(tree, loop_curve.outputs["Curve"], loop.inputs["Curve"])
    loop_profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 800, by - 500))
    loop_profile.inputs["Radius"].default_value = 0.001
    link_sockets(tree, loop_profile.outputs["Curve"], loop.inputs["Profile Curve"])
    
    # Position loop above cap
    loop_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 400, by - 400))
    loop_pos.inputs["Offset"].default_value = (0.0, 0.0, 0.02)
    link_sockets(tree, loop.outputs["Mesh"], loop_pos.inputs["Geometry"])
    
    # Join pearl + cap + loop
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 200, by))
    link_sockets(tree, pearl.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, cap_pos.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, loop_pos.outputs["Geometry"], join.inputs["Geometry"])
    
    # Audio reactivity
    audio_geo = add_audio_reactivity(tree, gin, join.outputs["Geometry"], (bx, by - 200))
    
    link_sockets(tree, audio_geo, gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Pearl Dangl", "nodes": ("Pearl", "Cap", "Loop", "Join"), "role": "geometry"},
        {"title": "Output", "nodes": ("Audio", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Register new builders
# ---------------------------------------------------------------------------

register_builder("MEL_lace_dangl", build_lace_dangl,
                 "Lace Dangl", "Lace-like hanging ornament with scalloped edges",
                 category="decor")

register_builder("MEL_bead_tassel", build_bead_tassel,
                 "Bead Tassel", "Tassel made of graduated beads",
                 category="decor")

register_builder("MEL_heart_dangl", build_heart_dangl,
                 "Heart Dangl", "Heart-shaped dangle with filigree border",
                 category="decor")

register_builder("MEL_star_dangl", build_star_dangl,
                 "Star Dangl", "Star-shaped dangle with center gem",
                 category="decor")

register_builder("MEL_flower_chain", build_flower_chain,
                 "Flower Chain", "Chain of small flowers",
                 category="decor")

register_builder("MEL_bow_dangl", build_bow_dangl,
                 "Bow Dangl", "Small bow charm with ribbon tails",
                 category="decor")

register_builder("MEL_crystal_chain", build_crystal_chain,
                 "Crystal Chain", "Chain of faceted crystals",
                 category="decor")

register_builder("MEL_pearl_dangl", build_pearl_dangl,
                 "Pearl Dangl", "Pearl dangle with gold cap",
                 category="decor")
