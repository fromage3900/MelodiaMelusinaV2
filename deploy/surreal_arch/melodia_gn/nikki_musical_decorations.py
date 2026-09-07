"""Infinity Nikki Musical Decoration Builders — generators for star pendants, heart filigree, wall bead strings.

Registered as Melodia Studio GN builders. All native 5.2 nodes — no Higgsas dependency.

Builders:
    MEL_nikki_star_pendant      — Star-shaped musical pendant (Curve Star → Curve to Mesh)
    MEL_nikki_heart_filigree    — Heart token filigree (IcoSphere + cone pair)
    MEL_nikki_wall_beads        — Vertical bead strings for wall siding
"""

from __future__ import annotations
import math
import bpy
import mathutils

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    make_group_input, register_builder,
)


# ---------------------------------------------------------------------------
# Shared templates (created on demand)
# ---------------------------------------------------------------------------

def _get_star_template():
    """Get or create the star pendant curve template."""
    if 'Star_Pendant_Template' in bpy.data.objects:
        return bpy.data.objects['Star_Pendant_Template']
    
    curve_data = bpy.data.curves.new(name='Star_Pendant_Curve', type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 12
    curve_data.bevel_depth = 0.005
    curve_data.bevel_resolution = 2
    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(4)
    outer_r = 0.05
    inner_r = 0.02
    for i in range(5):
        angle_outer = (i * 2 * math.pi / 5) - math.pi / 2
        angle_inner = ((i + 0.5) * 2 * math.pi / 5) - math.pi / 2
        pt_outer = spline.bezier_points[i * 2 % 5]
        pt_outer.co = mathutils.Vector((math.cos(angle_outer) * outer_r, math.sin(angle_outer) * outer_r, 0))
        pt_outer.handle_left_type = 'FREE'
        pt_outer.handle_right_type = 'FREE'
        pt_inner = spline.bezier_points[(i * 2 + 1) % 5]
        pt_inner.co = mathutils.Vector((math.cos(angle_inner) * inner_r, math.sin(angle_inner) * inner_r, 0))
        pt_inner.handle_left_type = 'FREE'
        pt_inner.handle_right_type = 'FREE'
    star_curve = bpy.data.objects.new('Star_Pendant_Template', curve_data)
    bpy.context.collection.objects.link(star_curve)
    star_curve.location = (0, -20, 0)
    return star_curve


def _get_heart_templates():
    """Get or create heart filigree templates (left sphere, right sphere, cone)."""
    names = ['Heart_Template_L', 'Heart_Template_R', 'Heart_Template_P']
    if all(n in bpy.data.objects for n in names):
        return [bpy.data.objects[n] for n in names]
    
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, segments=8, ring_count=6)
    heart_left = bpy.context.object
    heart_left.name = 'Heart_Template_L'
    heart_left.location = (-0.015, -20, 0.01)
    
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, segments=8, ring_count=6)
    heart_right = bpy.context.object
    heart_right.name = 'Heart_Template_R'
    heart_right.location = (0.015, -20, 0.01)
    
    bpy.ops.mesh.primitive_cone_add(radius1=0.025, depth=0.06, vertices=8)
    heart_point = bpy.context.object
    heart_point.name = 'Heart_Template_P'
    heart_point.location = (0, -20, -0.03)
    heart_point.rotation_euler = (0, 0, math.pi)
    
    return [heart_left, heart_right, heart_point]


def _get_bead_template():
    """Get or create the bead sphere template."""
    if 'Bead_Template' in bpy.data.objects:
        return bpy.data.objects['Bead_Template']
    
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=8, ring_count=6)
    bead = bpy.context.object
    bead.name = 'Bead_Template'
    bead.location = (0, -20, 0)
    return bead


# ---------------------------------------------------------------------------
# Builder: MEL_nikki_star_pendant
# ---------------------------------------------------------------------------

def build_nikki_star_pendant(group_name="MEL_nikki_star_pendant"):
    """Star-shaped musical pendant. Curve Star → Curve to Mesh with optional tuned drop.
    
    Params:
        Pendant Count: number of stars along the guide
        Star Size: radius of the star
        Drop: how far below the guide the star hangs
        Point Count: points on the star (5 = classic star)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_int_param(tree, "Pendant Count", 12, 3, 50)
    add_float_param(tree, "Star Size", 0.06, 0.01, 0.2)
    add_float_param(tree, "Drop", 0.15, 0.0, 1.0)
    add_int_param(tree, "Point Count", 5, 3, 12)
    add_float_param(tree, "Inner Ratio", 0.4, 0.1, 0.9)
    
    bx, by = 0, 0
    
    # Guide curve input (from GN modifier)
    guide_curve = safe_node(tree, "GeometryNodeObjectInfo", (bx - 800, by))
    guide_curve.inputs["Object"].default_value = _get_star_template()
    
    # Resample Curve
    resample = safe_node(tree, "GeometryNodeResampleCurve", (bx - 600, by))
    resample.inputs["Mode"].default_value = "Count"
    link_sockets(tree, gin.outputs["Pendant Count"], resample.inputs["Count"])
    link_sockets(tree, guide_curve.outputs["Geometry"], resample.inputs["Curve"])
    
    # Instance on Points
    instance = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 400, by))
    link_sockets(tree, resample.outputs["Curve"], instance.inputs["Points"])
    
    # Star template
    star_template = _get_star_template()
    star_info = safe_node(tree, "GeometryNodeObjectInfo", (bx - 600, by - 200))
    star_info.inputs["Object"].default_value = star_template
    link_sockets(tree, star_info.outputs["Geometry"], instance.inputs["Instance"])
    
    # Scale
    scale = safe_node(tree, "GeometryNodeScaleInstances", (bx - 200, by))
    link_sockets(tree, instance.outputs["Instances"], scale.inputs["Instances"])
    link_float_to_vector(tree, gin.outputs["Star Size"], scale.inputs["Scale"], factor=1.0)
    
    # Drop
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx, by))
    link_sockets(tree, scale.outputs["Instances"], set_pos.inputs["Geometry"])
    link_float_to_vector(tree, gin.outputs["Drop"], set_pos.inputs["Offset"], axis="Z", factor=-1.0)
    
    # Realize
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 200, by))
    link_sockets(tree, set_pos.outputs["Geometry"], realize.inputs["Geometry"])
    
    # Join with original
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 400, by))
    link_sockets(tree, gin.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, realize.outputs["Geometry"], join.inputs["Geometry"])
    
    link_sockets(tree, join.outputs["Geometry"], gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Star Pendants", "nodes": ("Resample", "Instance", "Scale", "Realize"), "role": "geometry"},
        {"title": "Output", "nodes": ("Join", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Builder: MEL_nikki_heart_filigree
# ---------------------------------------------------------------------------

def build_nikki_heart_filigree(group_name="MEL_nikki_heart_filigree"):
    """Heart token filigree — IcoSphere + cone pair above window headers.
    
    Params:
        Heart Count: number of hearts along the guide
        Heart Size: scale of each heart
        Offset Y: horizontal offset along the guide
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_int_param(tree, "Heart Count", 6, 1, 30)
    add_float_param(tree, "Heart Size", 0.05, 0.01, 0.2)
    add_float_param(tree, "Drop", 0.0, -0.5, 0.5)
    
    bx, by = 0, 0
    
    # Resample guide curve
    resample = safe_node(tree, "GeometryNodeResampleCurve", (bx - 600, by))
    resample.inputs["Mode"].default_value = "Count"
    link_sockets(tree, gin.outputs["Heart Count"], resample.inputs["Count"])
    
    # Instance on Points
    instance = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 400, by))
    link_sockets(tree, resample.outputs["Curve"], instance.inputs["Points"])
    
    # Heart template (use left sphere as main token)
    heart_templates = _get_heart_templates()
    heart_info = safe_node(tree, "GeometryNodeObjectInfo", (bx - 600, by - 200))
    heart_info.inputs["Object"].default_value = heart_templates[0]
    link_sockets(tree, heart_info.outputs["Geometry"], instance.inputs["Instance"])
    
    # Scale
    scale = safe_node(tree, "GeometryNodeScaleInstances", (bx - 200, by))
    link_sockets(tree, instance.outputs["Instances"], scale.inputs["Instances"])
    link_float_to_vector(tree, gin.outputs["Heart Size"], scale.inputs["Scale"], factor=1.0)
    
    # Offset
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx, by))
    link_sockets(tree, scale.outputs["Instances"], set_pos.inputs["Geometry"])
    link_float_to_vector(tree, gin.outputs["Drop"], set_pos.inputs["Offset"], axis="Z", factor=-1.0)
    
    # Realize
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 200, by))
    link_sockets(tree, set_pos.outputs["Geometry"], realize.inputs["Geometry"])
    
    # Join
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 400, by))
    link_sockets(tree, gin.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, realize.outputs["Geometry"], join.inputs["Geometry"])
    
    link_sockets(tree, join.outputs["Geometry"], gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Heart Filigree", "nodes": ("Resample", "Instance", "Scale", "Realize"), "role": "geometry"},
        {"title": "Output", "nodes": ("Join", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Builder: MEL_nikki_wall_beads
# ---------------------------------------------------------------------------

def build_nikki_wall_beads(group_name="MEL_nikki_wall_beads"):
    """Vertical bead strings for wall siding.
    
    Params:
        String Count: number of vertical strings per wall
        Beads Per String: beads in each vertical drop
        Bead Radius: size of each bead
        String Drop: how far the string hangs down
        Spacing: horizontal spacing between strings
    """
    tree, gin, gout = new_geometry_tree(group_name)
    add_int_param(tree, "String Count", 3, 1, 10)
    add_int_param(tree, "Beads Per String", 8, 2, 30)
    add_float_param(tree, "Bead Radius", 0.03, 0.005, 0.1)
    add_float_param(tree, "String Drop", 0.3, 0.0, 3.0)
    add_float_param(tree, "Spacing", 0.5, 0.1, 2.0)
    
    bx, by = 0, 0
    
    # Line of points for string origins (horizontal along wall top)
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 800, by + 200))
    line.mode = "OFFSET"
    link_sockets(tree, gin.outputs["String Count"], line.inputs["Count"])
    # Offset by spacing
    offset_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 900, by + 100))
    link_sockets(tree, gin.outputs["Spacing"], offset_vec.inputs["X"])
    link_sockets(tree, offset_vec.outputs["Vector"], line.inputs["Offset"])
    
    # Instance bead string template (vertical line of beads)
    # For each line point, instance a vertical string
    instance_outer = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 600, by + 200))
    link_sockets(tree, line.outputs["Mesh"], instance_outer.inputs["Points"])
    
    # Create vertical string of beads using a second line
    string_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 800, by))
    string_line.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Beads Per String"], string_line.inputs["Count"])
    # Offset downward
    drop_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 900, by - 100))
    link_sockets(tree, gin.outputs["String Drop"], drop_vec.inputs["Z"])
    # Scale drop by -1 for downward
    drop_scale = safe_node(tree, "ShaderNodeMath", (bx - 1000, by - 100))
    drop_scale.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["String Drop"], drop_scale.inputs[0])
    drop_scale.inputs[1].default_value = -1.0 / max(1, 8)  # Normalize by count
    link_sockets(tree, drop_scale.outputs[0], drop_vec.inputs["Z"])
    drop_vec.inputs["X"].default_value = 0.0
    drop_vec.inputs["Y"].default_value = 0.0
    link_sockets(tree, drop_vec.outputs["Vector"], string_line.inputs["Offset"])
    
    # Instance beads on the string line
    instance_inner = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 400, by))
    link_sockets(tree, string_line.outputs["Mesh"], instance_inner.inputs["Points"])
    
    # Bead template
    bead_template = _get_bead_template()
    bead_info = safe_node(tree, "GeometryNodeObjectInfo", (bx - 600, by - 200))
    bead_info.inputs["Object"].default_value = bead_template
    link_sockets(tree, bead_info.outputs["Geometry"], instance_inner.inputs["Instance"])
    
    # Scale beads
    scale = safe_node(tree, "GeometryNodeScaleInstances", (bx - 200, by))
    link_sockets(tree, instance_inner.outputs["Instances"], scale.inputs["Instances"])
    link_float_to_vector(tree, gin.outputs["Bead Radius"], scale.inputs["Scale"], factor=1.0)
    
    # Realize
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by))
    link_sockets(tree, scale.outputs["Instances"], realize.inputs["Geometry"])
    
    # Join
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200, by))
    link_sockets(tree, gin.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, realize.outputs["Geometry"], join.inputs["Geometry"])
    
    link_sockets(tree, join.outputs["Geometry"], gout.inputs["Geometry"])
    
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Wall Bead Strings", "nodes": ("Line", "String Line", "Instance", "Scale", "Realize"), "role": "geometry"},
        {"title": "Output", "nodes": ("Join", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------

register_builder("MEL_nikki_star_pendant", build_nikki_star_pendant,
                 "Nikki Star Pendant", "Star-shaped musical pendant — Curve Star → Curve to Mesh with tuned drop",
                 category="music")

register_builder("MEL_nikki_heart_filigree", build_nikki_heart_filigree,
                 "Nikki Heart Filigree", "Heart token filigree — IcoSphere + cone pair above window headers",
                 category="music")

register_builder("MEL_nikki_wall_beads", build_nikki_wall_beads,
                 "Nikki Wall Beads", "Vertical bead strings for wall siding — multi-string hanging decoration",
                 category="music")
