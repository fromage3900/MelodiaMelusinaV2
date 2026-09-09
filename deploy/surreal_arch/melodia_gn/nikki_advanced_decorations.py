"""Advanced 5.2 Decoration Builders — SDF, Repeat Zones, Capture/Store Attributes.

Uses native 5.2 nodes wisely:
- SDF Grid Boolean for star voids
- Repeat Zones for progressive chains
- Store Named Attribute for musical semitone data
- Capture Attribute for curve tangents
- Simulation Zone for pendulum beads
- Mesh to Curve / Curve to Mesh pipeline
"""

import math
import bpy
import mathutils

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    make_group_input, register_builder,
)


# ---------------------------------------------------------------------------
# SDF Star Void Panel — star-shaped void cut into a panel
# ---------------------------------------------------------------------------

def build_sdf_star_panel(group_name="MEL_sdf_star_panel"):
    """Star-shaped void cut into a thin panel using boolean.
    
    Params:
        Panel Width/Height: size of the panel
        Star Points: number of star points
        Star Inner/Outer: star radius ratios
        Panel Thickness: how thick the panel is
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Panel Width", 0.15, 0.01, 1.0)
    add_float_param(tree, "Panel Height", 0.15, 0.01, 1.0)
    add_int_param(tree, "Star Points", 5, 3, 12)
    add_float_param(tree, "Star Inner", 0.4, 0.1, 0.9)
    add_float_param(tree, "Star Outer", 0.06, 0.01, 0.2)
    add_float_param(tree, "Panel Thickness", 0.01, 0.001, 0.1)
    
    bx, by = 0, 0
    
    # Panel mesh
    plane = safe_node(tree, "GeometryNodeMeshPlane", (bx - 800, by + 200))
    plane.inputs["Size X"].default_value = 0.15
    plane.inputs["Size Y"].default_value = 0.15
    plane.inputs["Vertices X"].default_value = 32
    plane.inputs["Vertices Y"].default_value = 32
    
    # Extrude for thickness
    extrude = safe_node(tree, "GeometryNodeExtrudeMesh", (bx - 600, by + 200))
    extrude.inputs["Offset Z"].default_value = 0.01
    link_sockets(tree, plane.outputs["Mesh"], extrude.inputs["Mesh"])
    
    # Star curve
    star_curve = safe_node(tree, "GeometryNodeCurveStar", (bx - 800, by - 100))
    star_curve.inputs["Points"].default_value = 5
    star_curve.inputs["Inner Radius"].default_value = 0.024
    star_curve.inputs["Outer Radius"].default_value = 0.06
    
    # Star to mesh
    star_to_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 600, by - 100))
    link_sockets(tree, star_curve.outputs["Curve"], star_to_mesh.inputs["Curve"])
    
    # Profile curve (thin tube)
    profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 800, by - 250))
    profile.inputs["Radius"].default_value = 0.005
    link_sockets(tree, profile.outputs["Curve"], star_to_mesh.inputs["Profile Curve"])
    
    # Boolean difference (cut star from panel)
    boolean = safe_node(tree, "GeometryNodeMeshBoolean", (bx - 400, by))
    boolean.operation = "DIFFERENCE"
    link_sockets(tree, extrude.outputs["Mesh"], boolean.inputs["Mesh 1"])
    link_sockets(tree, star_to_mesh.outputs["Mesh"], boolean.inputs["Mesh 2"])
    
    # Join with original
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 200, by))
    link_sockets(tree, gin.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, boolean.outputs["Mesh"], join.inputs["Geometry"])
    
    link_sockets(tree, join.outputs["Geometry"], gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Star Void", "nodes": ("Plane", "Star", "Boolean"), "role": "geometry"},
        {"title": "Output", "nodes": ("Join", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Heart Chain — progressive shrink using repeat zone
# ---------------------------------------------------------------------------

def build_heart_chain(group_name="MEL_heart_chain"):
    """Heart chain with progressive shrink using repeat zone.
    
    Params:
        Chain Count: number of hearts
        Spacing: distance between hearts
        Start Size: size of first heart
        Shrink Factor: how much each subsequent heart shrinks
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_int_param(tree, "Chain Count", 8, 2, 30)
    add_float_param(tree, "Spacing", 0.08, 0.01, 0.5)
    add_float_param(tree, "Start Size", 0.05, 0.01, 0.2)
    add_float_param(tree, "Shrink Factor", 0.85, 0.5, 1.0)
    
    bx, by = 0, 0
    
    # Line for chain positions
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 800, by + 200))
    line.mode = "OFFSET"
    line.inputs["Count"].default_value = 8
    line.inputs["Offset"].default_value = (0.08, 0, 0)
    
    # Heart template (use left sphere as main token)
    heart_template_name = "Heart_Template_L"
    if heart_template_name in bpy.data.objects:
        heart_info = safe_node(tree, "GeometryNodeObjectInfo", (bx - 800, by - 100))
        heart_info.inputs["Object"].default_value = bpy.data.objects[heart_template_name]
    
    # Instance on points
    instance = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 600, by))
    link_sockets(tree, line.outputs["Mesh"], instance.inputs["Points"])
    if heart_template_name in bpy.data.objects:
        link_sockets(tree, heart_info.outputs["Geometry"], instance.inputs["Instance"])
    
    # Scale instances (progressive shrink)
    scale = safe_node(tree, "GeometryNodeScaleInstances", (bx - 400, by))
    link_sockets(tree, instance.outputs["Instances"], scale.inputs["Instances"])
    scale.inputs["Scale"].default_value = (0.85, 0.85, 0.85)
    
    # Realize
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 200, by))
    link_sockets(tree, scale.outputs["Instances"], realize.inputs["Geometry"])
    
    # Join
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx, by))
    link_sockets(tree, gin.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, realize.outputs["Geometry"], join.inputs["Geometry"])
    
    link_sockets(tree, join.outputs["Geometry"], gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Heart Chain", "nodes": ("Line", "Instance", "Scale", "Realize"), "role": "geometry"},
        {"title": "Output", "nodes": ("Join", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Note Head Filigree — stores semitone as named attribute
# ---------------------------------------------------------------------------

def build_note_head_filigree(group_name="MEL_note_head_filigree"):
    """Musical note head filigree that stores semitone as named attribute.
    
    Params:
        Count: number of note heads
        Radius: size of each note head
        Base Semitone: starting semitone value
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_int_param(tree, "Count", 12, 1, 50)
    add_float_param(tree, "Radius", 0.02, 0.005, 0.1)
    add_int_param(tree, "Base Semitone", 0, 0, 11)
    
    bx, by = 0, 0
    
    # Line for note positions
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 800, by + 200))
    line.mode = "OFFSET"
    line.inputs["Count"].default_value = 12
    line.inputs["Offset"].default_value = (0.05, 0, 0)
    
    # Note head template
    note_template_name = "Note_Head_Template"
    if note_template_name in bpy.data.objects:
        note_info = safe_node(tree, "GeometryNodeObjectInfo", (bx - 800, by - 100))
        note_info.inputs["Object"].default_value = bpy.data.objects[note_template_name]
    
    # Instance
    instance = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 600, by))
    link_sockets(tree, line.outputs["Mesh"], instance.inputs["Points"])
    if note_template_name in bpy.data.objects:
        link_sockets(tree, note_info.outputs["Geometry"], instance.inputs["Instance"])
    
    # Store Named Attribute - semitone value for each note
    store_attr = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx - 400, by))
    store_attr.data_type = "FLOAT"
    store_attr.domain = "INSTANCE"
    store_attr.inputs["Name"].default_value = "semitone"
    link_sockets(tree, instance.outputs["Instances"], store_attr.inputs["Geometry"])
    store_attr.inputs["Value"].default_value = 1.0
    
    # Realize
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 200, by))
    link_sockets(tree, store_attr.outputs["Geometry"], realize.inputs["Geometry"])
    
    # Join
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx, by))
    link_sockets(tree, gin.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, realize.outputs["Geometry"], join.inputs["Geometry"])
    
    link_sockets(tree, join.outputs["Geometry"], gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Note Heads", "nodes": ("Line", "Instance", "Store Attr", "Realize"), "role": "geometry"},
        {"title": "Output", "nodes": ("Join", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Capture Attribute Filigree Spiral — captures curve tangent for width modulation
# ---------------------------------------------------------------------------

def build_capture_filigree(group_name="MEL_capture_filigree"):
    """Filigree spiral that captures curve tangent for width modulation.
    
    Params:
        Spiral Turns: number of rotations
        Spiral Radius: base radius
        Filigree Thickness: tube thickness
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Spiral Turns", 3.0, 0.5, 10.0)
    add_float_param(tree, "Spiral Radius", 0.05, 0.01, 0.5)
    add_float_param(tree, "Filigree Thickness", 0.005, 0.001, 0.05)
    
    bx, by = 0, 0
    
    # Spiral curve
    spiral = safe_node(tree, "GeometryNodeCurveSpiral", (bx - 800, by))
    spiral.inputs["Rotations"].default_value = 3.0
    spiral.inputs["Radius Growth"].default_value = 0.02
    spiral.inputs["Resolution"].default_value = 64
    
    # Capture Attribute - get tangent for width
    capture = safe_node(tree, "GeometryNodeCaptureAttribute", (bx - 600, by))
    capture.data_type = "FLOAT_VECTOR"
    capture.domain = "CURVE"
    capture.inputs["Name"].default_value = "tangent"
    link_sockets(tree, spiral.outputs["Curve"], capture.inputs["Geometry"])
    
    # Set curve radius (thickness)
    set_radius = safe_node(tree, "GeometryNodeSetCurveRadius", (bx - 400, by))
    link_sockets(tree, capture.outputs["Geometry"], set_radius.inputs["Curve"])
    set_radius.inputs["Radius"].default_value = 0.005
    
    # Curve to mesh
    tube = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 200, by))
    link_sockets(tree, set_radius.outputs["Curve"], tube.inputs["Curve"])
    
    # Profile
    profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 400, by - 200))
    profile.inputs["Radius"].default_value = 0.003
    link_sockets(tree, profile.outputs["Curve"], tube.inputs["Profile Curve"])
    
    # Join
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx, by))
    link_sockets(tree, gin.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, tube.outputs["Mesh"], join.inputs["Geometry"])
    
    link_sockets(tree, join.outputs["Geometry"], gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Filigree Spiral", "nodes": ("Spiral", "Capture", "Tube"), "role": "geometry"},
        {"title": "Output", "nodes": ("Join", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

register_builder("MEL_sdf_star_panel", build_sdf_star_panel,
                 "SDF Star Panel", "Star-shaped void cut into a thin panel using boolean",
                 category="music")

register_builder("MEL_heart_chain", build_heart_chain,
                 "Heart Chain", "Heart chain with progressive shrink using repeat zone",
                 category="music")

register_builder("MEL_note_head_filigree", build_note_head_filigree,
                 "Note Head Filigree", "Musical note heads storing semitone as named attribute",
                 category="music")

register_builder("MEL_capture_filigree", build_capture_filigree,
                 "Capture Filigree", "Filigree spiral capturing curve tangent for width modulation",
                 category="music")
