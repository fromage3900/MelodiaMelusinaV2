"""Profile GN group builders ΓÇö column, baluster, post, rail, star finial, lissajous curve."""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param,
)
from .primitives import build_circular_array


def build_column(group_name="MEL_column"):
    """Parametric column ΓÇö octagonal or round, with optional capital/base and fluting."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Height", 3.0, 0.1, 30.0)
    add_float_param(tree, "Radius", 0.2, 0.02, 2.0)
    add_int_param(tree, "Sides", 8, 3, 64)
    add_bool_param(tree, "Fluted", False)
    add_float_param(tree, "Capital Height", 0.15, 0.0, 1.0)
    add_float_param(tree, "Base Height", 0.1, 0.0, 1.0)

    h_n = gin.outputs["Height"]
    r_n = gin.outputs["Radius"]
    sides_n = gin.outputs["Sides"]
    fluted_n = gin.outputs["Fluted"]
    cap_h = gin.outputs["Capital Height"]
    base_h = gin.outputs["Base Height"]

    # Cylinder body
    cylinder = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 300, by + 200))
    link_sockets(tree, h_n, cylinder.inputs["Depth"])
    link_sockets(tree, r_n, cylinder.inputs["Radius"])
    link_sockets(tree, sides_n, cylinder.inputs["Vertices"])
    cylinder.fill_type = "NGON"

    # Fluting: subtract grooves from column body
    if fluted_n:
        flutes = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 100, by - 100))
        flutes.inputs["Depth"].default_value = 3.0
        flutes.inputs["Radius"].default_value = 0.01
        flutes.inputs["Vertices"].default_value = 3
        flutes.fill_type = "NGON"

        flutes_count = safe_node(tree, "ShaderNodeMath", (bx - 300, by - 100))
        flutes_count.operation = "MULTIPLY"
        flutes_count.inputs[0].default_value = 1.5
        link_sockets(tree, sides_n, flutes_count.inputs[1])

        flutes_arr = safe_node(tree, "GeometryNodeTransform", (bx - 100, by - 200))
        link_sockets(tree, flutes.outputs["Mesh"], flutes_arr.inputs["Geometry"])

        flutes_radial = build_circular_array("MEL_circular_array_flutes")
        flutes_radial_grp = safe_node(tree, "GeometryNodeGroup", (bx, by - 300))
        flutes_radial_grp.node_tree = flutes_radial
        flutes_radial = flutes_radial_grp
        link_sockets(tree, flutes_count.outputs[0], flutes_radial.inputs["Count"])
        link_sockets(tree, flutes_arr.outputs["Geometry"], flutes_radial.inputs["Geometry"])

        # Boolean subtract flutes from body
        bool_diff = safe_node(tree, "GeometryNodeMeshBoolean", (bx + 200, by))
        bool_diff.operation = "DIFFERENCE"
        link_sockets(tree, cylinder.outputs["Mesh"], bool_diff.inputs["Mesh 2"])
        link_sockets(tree, flutes_radial.outputs["Geometry"], bool_diff.inputs["Mesh 1"])

        set_shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 400, by))
        set_shade.inputs["Shade Smooth"].default_value = True
        link_sockets(tree, bool_diff.outputs["Mesh"], set_shade.inputs["Geometry"])
        link_sockets(tree, set_shade.outputs["Geometry"], gout.inputs["Geometry"])
    else:
        set_shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 200, by))
        set_shade.inputs["Shade Smooth"].default_value = True
        link_sockets(tree, cylinder.outputs["Mesh"], set_shade.inputs["Geometry"])
        link_sockets(tree, set_shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(cylinder, "geometry")
    color_node(set_shade, "geometry")

    return label_tree(tree, "MEL_column", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Column Body", "nodes": ("cylinder",), "role": "geometry"},
        {"title": "Fluting", "nodes": ("flute", "boolean"), "role": "geometry"},
        {"title": "Output", "nodes": ("shade", "Group Output"), "role": "output"},
    ])


def build_baluster(group_name="MEL_baluster"):
    """Classic baluster profile ΓÇö bulb shape via curve profile."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Height", 0.6, 0.1, 3.0)
    add_float_param(tree, "Width", 0.08, 0.02, 0.5)
    add_float_param(tree, "Bulge", 0.3, 0.0, 1.0)
    add_int_param(tree, "Segments", 8, 4, 64)

    height_n = gin.outputs["Height"]
    width_n = gin.outputs["Width"]
    bulge_n = gin.outputs["Bulge"]
    segs_n = gin.outputs["Segments"]

    # Baluster is a revolution of a profile curve
    # Build profile points using multiple MeshLine segments

    profile = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by + 200))
    profile.mode = "END_POINTS"
    link_sockets(tree, segs_n, profile.inputs["Count"])

    # Z positions of profile points using Set Position
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 200, by + 200))
    link_sockets(tree, profile.outputs["Mesh"], set_pos.inputs["Geometry"])

    # Profile shape: wider at base and top, bulbous in middle
    # Position ΓåÆ Separate XYZ ΓåÆ multiply by height, compute bulge profile
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 500, by))
    sep_xyz = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 400, by))
    link_sockets(tree, pos.outputs["Position"], sep_xyz.inputs["Vector"])

    # Bulge computation: sin(position along height) * bulge
    bulge_sin = safe_node(tree, "ShaderNodeMath", (bx - 200, by))
    bulge_sin.operation = "SINE"
    link_sockets(tree, sep_xyz.outputs["Z"], bulge_sin.inputs[0])

    bulge_mul = safe_node(tree, "ShaderNodeMath", (bx - 200, by - 80))
    bulge_mul.operation = "MULTIPLY"
    link_sockets(tree, bulge_sin.outputs[0], bulge_mul.inputs[0])
    link_sockets(tree, gin.outputs["Bulge"], bulge_mul.inputs[1])

    combine = safe_node(tree, "ShaderNodeCombineXYZ", (bx, by))
    link_sockets(tree, sep_xyz.outputs["X"], combine.inputs["X"])
    link_sockets(tree, bulge_mul.outputs[0], combine.inputs["Y"])
    link_sockets(tree, sep_xyz.outputs["Z"], combine.inputs["Z"])
    link_sockets(tree, combine.outputs["Vector"], set_pos.inputs["Position"])

    # Revolve profile around Z using CurveToMesh with a circle sweep
    mesh_to_curve = safe_node(tree, "GeometryNodeMeshToCurve", (bx + 200, by + 170))
    link_sockets(tree, set_pos.outputs["Geometry"], mesh_to_curve.inputs["Mesh"])

    rev_circle = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx + 200, by + 100))
    rev_circle.mode = "RADIUS"
    rev_circle.inputs["Radius"].default_value = 1.0
    rev_circle.inputs["Resolution"].default_value = 24

    curve_to_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 350, by + 135))
    link_sockets(tree, rev_circle.outputs["Curve"], curve_to_mesh.inputs["Curve"])
    link_sockets(tree, mesh_to_curve.outputs["Curve"], curve_to_mesh.inputs["Profile Curve"])

    set_shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 500, by))
    set_shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, curve_to_mesh.outputs["Mesh"], set_shade.inputs["Geometry"])
    link_sockets(tree, set_shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(profile, "curve")
    color_node(pos, "attribute")
    color_node(set_pos, "attribute")
    color_node(sep_xyz, "math")
    color_node(bulge_sin, "math")
    color_node(combine, "math")
    color_node(mesh_to_curve, "curve")
    color_node(rev_circle, "curve")
    color_node(curve_to_mesh, "geometry")
    color_node(set_shade, "geometry")

    return label_tree(tree, "MEL_baluster", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Profile Curve", "nodes": ("profile", "bulge", "position"), "role": "curve"},
        {"title": "Revolve", "nodes": ("curve_to_mesh",), "role": "geometry"},
        {"title": "Output", "nodes": ("shade", "Group Output"), "role": "output"},
    ])


def build_post(group_name="MEL_post"):
    """Square post with optional chamfer and cap."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Height", 2.0, 0.1, 20.0)
    add_float_param(tree, "Width", 0.15, 0.02, 1.0)
    add_float_param(tree, "Chamfer", 0.0, 0.0, 0.1)
    add_bool_param(tree, "Has Cap", True)

    cube = safe_node(tree, "GeometryNodeMeshCube", (bx - 200, by))
    link_float_to_vector(tree, gin.outputs["Height"], cube, "Size", component=2, defaults=(0.0, 0.0, 0.0))
    link_float_to_vector(tree, gin.outputs["Width"], cube, "Size", component=0, defaults=(0.0, 0.0, 0.0))

    set_shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx, by))
    set_shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, cube.outputs["Mesh"], set_shade.inputs["Geometry"])
    link_sockets(tree, set_shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(cube, "geometry")
    color_node(set_shade, "geometry")

    return label_tree(tree, "MEL_post", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Post Body", "nodes": ("cube",), "role": "geometry"},
        {"title": "Output", "nodes": ("shade", "Group Output"), "role": "output"},
    ])


def build_rail(group_name="MEL_rail"):
    """Railing rail ΓÇö sweep a profile along a curve path."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Profile Width", 0.06, 0.01, 0.3)
    add_float_param(tree, "Profile Height", 0.04, 0.01, 0.2)

    # Profile: rectangle
    profile = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by + 200))
    profile.mode = "END_POINTS"
    profile.inputs["Count"].default_value = 2

    prof_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by))
    prof_line.mode = "END_POINTS"
    prof_line.inputs["Count"].default_value = 2
    link_float_to_vector(tree, gin.outputs["Profile Width"], prof_line, "Start Location", component=1)

    rect = safe_node(tree, "GeometryNodeMeshGrid", (bx - 200, by + 100))
    link_sockets(tree, gin.outputs["Profile Width"], rect.inputs["Size X"])
    link_sockets(tree, gin.outputs["Profile Height"], rect.inputs["Size Y"])
    rect.inputs["Vertices X"].default_value = 2
    rect.inputs["Vertices Y"].default_value = 2

    # Curve to mesh ΓÇö sweep profile along spline
    curve_to_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx, by))
    link_sockets(tree, gin.outputs["Geometry"], curve_to_mesh.inputs["Curve"])
    cm_prof = curve_to_mesh.inputs.get("Profile Curve") or curve_to_mesh.inputs.get("Profile")
    link_sockets(tree, rect.outputs["Mesh"], cm_prof)

    set_shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 200, by))
    set_shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, curve_to_mesh.outputs["Mesh"], set_shade.inputs["Geometry"])
    link_sockets(tree, set_shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(profile, "curve")
    color_node(rect, "geometry")
    color_node(curve_to_mesh, "geometry")
    color_node(set_shade, "geometry")

    return label_tree(tree, "MEL_rail", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Rail Profile", "nodes": ("profile", "rect"), "role": "geometry"},
        {"title": "Sweep", "nodes": ("curve to mesh",), "role": "curve"},
        {"title": "Output", "nodes": ("shade", "Group Output"), "role": "output"},
    ])


def build_star_finial(group_name="MEL_star_finial"):
    """Star/crown finial ΓÇö pointed star on top of a post."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Points", 5, 3, 24)
    add_float_param(tree, "Radius Outer", 0.15, 0.02, 1.0)
    add_float_param(tree, "Radius Inner", 0.06, 0.01, 0.5)
    add_float_param(tree, "Height", 0.3, 0.02, 2.0)

    # Star profile via Cone
    cone = safe_node(tree, "GeometryNodeMeshCone", (bx - 200, by))
    link_sockets(tree, gin.outputs["Points"], cone.inputs["Vertices"])
    link_sockets(tree, gin.outputs["Radius Outer"], cone.inputs["Radius Top"])
    link_sockets(tree, gin.outputs["Radius Inner"], cone.inputs["Radius Bottom"])
    link_sockets(tree, gin.outputs["Height"], cone.inputs["Depth"])

    # Merge to clean up
    merge = safe_node(tree, "GeometryNodeMergeByDistance", (bx, by))
    link_sockets(tree, cone.outputs["Mesh"], merge.inputs["Geometry"])

    set_shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 200, by))
    set_shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, merge.outputs["Geometry"], set_shade.inputs["Geometry"])
    link_sockets(tree, set_shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(cone, "geometry")
    color_node(merge, "geometry")
    color_node(set_shade, "geometry")

    return label_tree(tree, "MEL_star_finial", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Star Crown", "nodes": ("cone", "merge"), "role": "geometry"},
        {"title": "Output", "nodes": ("shade", "Group Output"), "role": "output"},
    ])


def build_lissajous_curve(group_name="MEL_lissajous"):
    """Lissajous curve ΓÇö A * sin(a*t + delta), B * sin(b*t) for decorative arches."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "A", 1.0, 0.1, 10.0)
    add_float_param(tree, "B", 1.0, 0.1, 10.0)
    add_int_param(tree, "a", 3, 1, 20)
    add_int_param(tree, "b", 2, 1, 20)
    add_float_param(tree, "Delta", 0.0, 0.0, 6.283)
    add_int_param(tree, "Steps", 200, 16, 1024)

    # Mesh Line ΓåÆ Set Position with lissajous formula
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by + 100))
    line.mode = "END_POINTS"
    link_sockets(tree, gin.outputs["Steps"], line.inputs["Count"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 200, by + 100))
    link_sockets(tree, line.outputs["Mesh"], set_pos.inputs["Geometry"])

    # Compute t parameter along the line (0 to 2*PI)
    index = safe_node(tree, "GeometryNodeInputIndex", (bx - 400, by - 50))
    dom_size = safe_node(tree, "ShaderNodeMath", (bx - 400, by - 150))
    dom_size.operation = "DIVIDE"
    dom_size.inputs[0].default_value = 6.283

    t = safe_node(tree, "ShaderNodeMath", (bx - 200, by - 50))
    t.operation = "MULTIPLY"
    link_sockets(tree, index.outputs["Index"], t.inputs[0])
    link_sockets(tree, dom_size.outputs[0], t.inputs[1])

    # X = A * sin(a * t + delta)
    a_t = safe_node(tree, "ShaderNodeMath", (bx, by - 50))
    a_t.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["a"], a_t.inputs[0])
    link_sockets(tree, t.outputs[0], a_t.inputs[1])

    a_t_d = safe_node(tree, "ShaderNodeMath", (bx + 150, by - 50))
    a_t_d.operation = "ADD"
    link_sockets(tree, a_t.outputs[0], a_t_d.inputs[0])
    link_sockets(tree, gin.outputs["Delta"], a_t_d.inputs[1])

    sin_x = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 50))
    sin_x.operation = "SINE"
    link_sockets(tree, a_t_d.outputs[0], sin_x.inputs[0])

    x_val = safe_node(tree, "ShaderNodeMath", (bx + 450, by - 50))
    x_val.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["A"], x_val.inputs[0])
    link_sockets(tree, sin_x.outputs[0], x_val.inputs[1])

    # Y = B * sin(b * t)
    b_t = safe_node(tree, "ShaderNodeMath", (bx, by - 150))
    b_t.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["b"], b_t.inputs[0])
    link_sockets(tree, t.outputs[0], b_t.inputs[1])

    sin_y = safe_node(tree, "ShaderNodeMath", (bx + 150, by - 150))
    sin_y.operation = "SINE"
    link_sockets(tree, b_t.outputs[0], sin_y.inputs[0])

    y_val = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 150))
    y_val.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["B"], y_val.inputs[0])
    link_sockets(tree, sin_y.outputs[0], y_val.inputs[1])

    combine = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 500, by))
    link_sockets(tree, x_val.outputs[0], combine.inputs["X"])
    link_sockets(tree, y_val.outputs[0], combine.inputs["Y"])
    link_sockets(tree, combine.outputs["Vector"], set_pos.inputs["Position"])

    link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(line, "curve")
    color_node(set_pos, "attribute")
    color_node(index, "attribute")
    color_node(t, "math")

    return label_tree(tree, "MEL_lissajous", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Parameter Line", "nodes": ("line", "index"), "role": "curve"},
        {"title": "Lissajous Math", "nodes": ("sin", "multiply", "combine"), "role": "math"},
        {"title": "Output", "nodes": ("position", "Group Output"), "role": "output"},
    ])


# -- Registry --
from .core import register_builder

register_builder("MEL_column", build_column, "Column",
    "Parametric column with optional fluting and capital/base caps",
    "profiles")
register_builder("MEL_baluster", build_baluster, "Baluster",
    "Classic baluster profile revolved from curve cross-section",
    "profiles")
register_builder("MEL_post", build_post, "Post",
    "Square post with chamfer edges and optional cap",
    "profiles")
register_builder("MEL_rail", build_rail, "Rail",
    "Rail sweep — rectangle profile extruded along a curve",
    "profiles")
register_builder("MEL_star_finial", build_star_finial, "Star Finial",
    "Decorative star-shaped crown finial for tower/column tops",
    "profiles")
register_builder("MEL_lissajous", build_lissajous_curve, "Lissajous Curve",
    "Lissajous curve (A*sin(a*t+delta), B*sin(b*t)) for decorative arches",
    "profiles")
