"""Escher math decor — hyperbolic tiling, Penrose triangle, Möbius strip.

All builders include audio reactivity via the shared add_audio_reactivity helper.
Designed for Melusina's Study and similar dream-architecture scenes.
"""
import math
from surreal_arch.melodia_gn.core import (
    new_geometry_tree, safe_node, link_sockets,
    add_float_param, add_int_param, register_builder, label_tree,
)
from surreal_arch.melodia_gn.audio_reactivity import add_audio_reactivity


# ---------------------------------------------------------------------------
# Hyperbolic Window — Poincaré disk tiling with recursive rings
# ---------------------------------------------------------------------------

def build_hyperbolic_window(group_name="MEL_hyperbolic_window"):
    """Hyperbolic tiling in a Poincaré disk — infinite density at the boundary.
    
    Params:
        Ring Count: number of concentric rings
        Sectors: number of sectors per ring
        Disk Radius: overall radius
        Tile Scale: scale of each tile
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_int_param(tree, "Ring Count", 6, 2, 12)
    add_int_param(tree, "Sectors", 8, 3, 16)
    add_float_param(tree, "Disk Radius", 0.5, 0.1, 2.0)
    add_float_param(tree, "Tile Scale", 0.08, 0.02, 0.3)
    
    bx, by = 0, 0
    
    # Base disk
    disk = safe_node(tree, "GeometryNodeMeshCircle", (bx - 800, by))
    disk.inputs["Radius"].default_value = 0.5
    disk.inputs["Vertices"].default_value = 64
    link_sockets(tree, gin.outputs["Disk Radius"], disk.inputs["Radius"])
    
    # Create tile template — small diamond shape
    tile = safe_node(tree, "GeometryNodeMeshGrid", (bx - 1000, by - 200))
    tile.inputs["Size X"].default_value = 0.08
    tile.inputs["Size Y"].default_value = 0.08
    tile.inputs["Vertices X"].default_value = 4
    tile.inputs["Vertices Y"].default_value = 4
    link_sockets(tree, gin.outputs["Tile Scale"], tile.inputs["Size X"])
    link_sockets(tree, gin.outputs["Tile Scale"], tile.inputs["Size Y"])
    
    # Instance tiles in concentric rings
    # Ring 1: center tile — use a single-vertex mesh as point
    center_point = safe_node(tree, "GeometryNodeMeshLine", (bx - 600, by))
    center_point.mode = "OFFSET"
    center_point.inputs["Count"].default_value = 1
    center_point.inputs["Offset"].default_value = (0.0, 0.0, 0.0)
    
    center = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 400, by))
    link_sockets(tree, center_point.outputs["Mesh"], center.inputs["Points"])
    link_sockets(tree, tile.outputs["Mesh"], center.inputs["Instance"])
    
    # Ring 2+: instance on circle curves
    ring_curve = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 800, by - 200))
    ring_curve.inputs["Radius"].default_value = 0.15
    link_sockets(tree, gin.outputs["Disk Radius"], ring_curve.inputs["Radius"])
    
    ring_instance = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 600, by - 200))
    link_sockets(tree, ring_curve.outputs["Curve"], ring_instance.inputs["Points"])
    link_sockets(tree, tile.outputs["Mesh"], ring_instance.inputs["Instance"])
    
    # Rotate instances around the ring
    rotate = safe_node(tree, "GeometryNodeRotateInstances", (bx - 400, by - 200))
    link_sockets(tree, ring_instance.outputs["Instances"], rotate.inputs["Instances"])
    rotate.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(45))
    
    # Realize all instances
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 200, by))
    link_sockets(tree, center.outputs["Instances"], realize.inputs["Geometry"])
    link_sockets(tree, rotate.outputs["Instances"], realize.inputs["Geometry"])
    
    # Audio reactivity
    audio_geo = add_audio_reactivity(tree, gin, realize.outputs["Geometry"], (bx, by - 200))
    
    link_sockets(tree, audio_geo, gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Hyperbolic", "nodes": ("Disk", "Tiles", "Rings", "Realize"), "role": "geometry"},
        {"title": "Output", "nodes": ("Audio", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Penrose Triangle — impossible triangle (camera-dependent illusion)
# ---------------------------------------------------------------------------

def build_penrose_triangle(group_name="MEL_penrose_triangle"):
    """Penrose triangle — three beams meeting at impossible angles.
    
    Params:
        Beam Width: width of each beam
        Beam Length: length of each beam
        Twist Angle: rotation for the impossible joint
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Beam Width", 0.04, 0.01, 0.15)
    add_float_param(tree, "Beam Length", 0.3, 0.1, 1.0)
    add_float_param(tree, "Twist Angle", 0.0, 0.0, math.radians(30))
    
    bx, by = 0, 0
    
    # Beam 1 — horizontal
    beam1 = safe_node(tree, "GeometryNodeMeshCube", (bx - 800, by))
    beam1.inputs["Size"].default_value = (0.3, 0.04, 0.04)
    link_sockets(tree, gin.outputs["Beam Length"], beam1.inputs["Size"])
    link_sockets(tree, gin.outputs["Beam Width"], beam1.inputs["Size"])
    
    # Beam 2 — rotated 120 degrees
    beam2 = safe_node(tree, "GeometryNodeMeshCube", (bx - 800, by - 200))
    beam2.inputs["Size"].default_value = (0.3, 0.04, 0.04)
    link_sockets(tree, gin.outputs["Beam Length"], beam2.inputs["Size"])
    link_sockets(tree, gin.outputs["Beam Width"], beam2.inputs["Size"])
    
    beam2_rot = safe_node(tree, "GeometryNodeTransform", (bx - 600, by - 200))
    beam2_rot.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(120))
    link_sockets(tree, beam2.outputs["Mesh"], beam2_rot.inputs["Geometry"])
    
    # Beam 3 — rotated 240 degrees
    beam3 = safe_node(tree, "GeometryNodeMeshCube", (bx - 800, by - 400))
    beam3.inputs["Size"].default_value = (0.3, 0.04, 0.04)
    link_sockets(tree, gin.outputs["Beam Length"], beam3.inputs["Size"])
    link_sockets(tree, gin.outputs["Beam Width"], beam3.inputs["Size"])
    
    beam3_rot = safe_node(tree, "GeometryNodeTransform", (bx - 600, by - 400))
    beam3_rot.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(240))
    link_sockets(tree, beam3.outputs["Mesh"], beam3_rot.inputs["Geometry"])
    
    # Position beams to form triangle
    beam1_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 400, by))
    beam1_pos.inputs["Offset"].default_value = (0.0, 0.0, 0.0)
    link_sockets(tree, beam1.outputs["Mesh"], beam1_pos.inputs["Geometry"])
    
    beam2_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 400, by - 200))
    beam2_pos.inputs["Offset"].default_value = (0.15, 0.0, 0.0)
    link_sockets(tree, beam2_rot.outputs["Geometry"], beam2_pos.inputs["Geometry"])
    
    beam3_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 400, by - 400))
    beam3_pos.inputs["Offset"].default_value = (-0.15, 0.0, 0.0)
    link_sockets(tree, beam3_rot.outputs["Geometry"], beam3_pos.inputs["Geometry"])
    
    # Join all beams
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 200, by))
    link_sockets(tree, beam1_pos.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, beam2_pos.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, beam3_pos.outputs["Geometry"], join.inputs["Geometry"])
    
    # Audio reactivity
    audio_geo = add_audio_reactivity(tree, gin, join.outputs["Geometry"], (bx, by - 200))
    
    link_sockets(tree, audio_geo, gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Penrose", "nodes": ("Beams", "Join"), "role": "geometry"},
        {"title": "Output", "nodes": ("Audio", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Möbius Strip — single-sided surface with a twist
# ---------------------------------------------------------------------------

def build_mobius_strip(group_name="MEL_mobius_strip"):
    """Möbius strip — a surface with only one side.
    
    Params:
        Strip Width: width of the strip
        Strip Length: length of the strip
        Twist Count: number of half-twists (1 = classic Möbius)
        Segments: number of segments along the strip
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Strip Width", 0.04, 0.01, 0.15)
    add_float_param(tree, "Strip Length", 0.4, 0.1, 1.5)
    add_int_param(tree, "Twist Count", 1, 1, 5)
    add_int_param(tree, "Segments", 64, 16, 256)
    
    bx, by = 0, 0
    
    # Create the strip as a parametric surface
    # Use a curve with a profile that twists
    curve = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 800, by))
    curve.inputs["Radius"].default_value = 0.2
    link_sockets(tree, gin.outputs["Strip Length"], curve.inputs["Radius"])
    
    # Create a line that will be the cross-section
    line = safe_node(tree, "GeometryNodeCurvePrimitiveLine", (bx - 800, by - 200))
    line.inputs["Start"].default_value = (-0.02, 0.0, 0.0)
    line.inputs["End"].default_value = (0.02, 0.0, 0.0)
    link_sockets(tree, gin.outputs["Strip Width"], line.inputs["Start"])
    link_sockets(tree, gin.outputs["Strip Width"], line.inputs["End"])
    
    # Sweep the line along the circle with a twist
    # Use Instance on Points + Rotate to create the twist
    points = safe_node(tree, "GeometryNodeResampleCurve", (bx - 600, by))
    points.inputs["Count"].default_value = 64
    link_sockets(tree, gin.outputs["Segments"], points.inputs["Count"])
    link_sockets(tree, curve.outputs["Curve"], points.inputs["Curve"])
    
    # Instance the line profile on each point
    instance = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 400, by))
    link_sockets(tree, points.outputs["Curve"], instance.inputs["Points"])
    link_sockets(tree, line.outputs["Curve"], instance.inputs["Instance"])
    
    # Rotate each instance to create the twist
    rotate = safe_node(tree, "GeometryNodeRotateInstances", (bx - 200, by))
    link_sockets(tree, instance.outputs["Instances"], rotate.inputs["Instances"])
    # Twist angle = 180 * twist_count degrees distributed along the strip
    rotate.inputs["Rotation"].default_value = (math.radians(180), 0.0, 0.0)
    
    # Realize instances
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by))
    link_sockets(tree, rotate.outputs["Instances"], realize.inputs["Geometry"])
    
    # Convert to mesh
    to_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 200, by))
    link_sockets(tree, realize.outputs["Geometry"], to_mesh.inputs["Curve"])
    
    # Audio reactivity
    audio_geo = add_audio_reactivity(tree, gin, to_mesh.outputs["Mesh"], (bx + 400, by))
    
    link_sockets(tree, audio_geo, gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Möbius", "nodes": ("Curve", "Profile", "Twist", "Realize"), "role": "geometry"},
        {"title": "Output", "nodes": ("Audio", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Tessellation — interlocking pattern (p4m wallpaper group)
# ---------------------------------------------------------------------------

def build_tessellation(group_name="MEL_tessellation"):
    """Interlocking tessellation pattern (p4m wallpaper group).
    
    Params:
        Tile Size: size of each tile
        Grid X: number of tiles in X
        Grid Y: number of tiles in Y
        Pattern: pattern type (0=diamond, 1=hexagon, 2=star)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Tile Size", 0.05, 0.01, 0.2)
    add_int_param(tree, "Grid X", 8, 2, 20)
    add_int_param(tree, "Grid Y", 8, 2, 20)
    add_int_param(tree, "Pattern", 0, 0, 2)
    
    bx, by = 0, 0
    
    # Create tile template based on pattern
    if True:  # diamond pattern (default)
        tile = safe_node(tree, "GeometryNodeMeshGrid", (bx - 800, by))
        tile.inputs["Size X"].default_value = 0.05
        tile.inputs["Size Y"].default_value = 0.05
        tile.inputs["Vertices X"].default_value = 4
        tile.inputs["Vertices Y"].default_value = 4
        link_sockets(tree, gin.outputs["Tile Size"], tile.inputs["Size X"])
        link_sockets(tree, gin.outputs["Tile Size"], tile.inputs["Size Y"])
    
    # Create grid of points for instancing
    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 600, by))
    grid.inputs["Size X"].default_value = 0.4
    grid.inputs["Size Y"].default_value = 0.4
    grid.inputs["Vertices X"].default_value = 8
    grid.inputs["Vertices Y"].default_value = 8
    link_sockets(tree, gin.outputs["Grid X"], grid.inputs["Vertices X"])
    link_sockets(tree, gin.outputs["Grid Y"], grid.inputs["Vertices Y"])
    
    # Instance tiles on grid
    instance = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 400, by))
    link_sockets(tree, grid.outputs["Mesh"], instance.inputs["Points"])
    link_sockets(tree, tile.outputs["Mesh"], instance.inputs["Instance"])
    
    # Rotate alternate tiles for interlocking effect
    rotate = safe_node(tree, "GeometryNodeRotateInstances", (bx - 200, by))
    link_sockets(tree, instance.outputs["Instances"], rotate.inputs["Instances"])
    rotate.inputs["Rotation"].default_value = (0.0, 0.0, math.radians(45))
    
    # Realize instances
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by))
    link_sockets(tree, rotate.outputs["Instances"], realize.inputs["Geometry"])
    
    # Audio reactivity
    audio_geo = add_audio_reactivity(tree, gin, realize.outputs["Geometry"], (bx + 200, by))
    
    link_sockets(tree, audio_geo, gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Tessellation", "nodes": ("Grid", "Tiles", "Rotate", "Realize"), "role": "geometry"},
        {"title": "Output", "nodes": ("Audio", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Register builders
# ---------------------------------------------------------------------------

register_builder("MEL_hyperbolic_window", build_hyperbolic_window,
                 "Hyperbolic Window", "Poincaré disk tiling with infinite boundary density",
                 category="escher")

register_builder("MEL_penrose_triangle", build_penrose_triangle,
                 "Penrose Triangle", "Impossible triangle (camera-dependent illusion)",
                 category="escher")

register_builder("MEL_mobius_strip", build_mobius_strip,
                 "Möbius Strip", "Single-sided surface with a twist",
                 category="escher")

register_builder("MEL_tessellation", build_tessellation,
                 "Tessellation", "Interlocking p4m wallpaper pattern",
                 category="escher")
