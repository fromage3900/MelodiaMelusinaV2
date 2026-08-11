"""Primitive GN group builders ΓÇö circular array, linear array, grid array, bounding box, instance on spline."""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, add_vector_param,
    make_group_output, make_group_input, tree_input_names,
)


def build_circular_array(group_name="MEL_circular_array"):
    """Create a reusable circular array node group.

    Parameters:
        Geometry, Count, Radius, Scale per item, Offset Z
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    count_n = add_int_param(tree, "Count", 8, 1, 256)
    radius_n = add_float_param(tree, "Radius", 2.0, 0.01, 100.0)
    scale_n = add_float_param(tree, "Scale per item", 1.0, 0.01, 10.0)
    offset_z = add_float_param(tree, "Offset Z", 0.0, -100.0, 100.0)

    # Circle of points using MeshCircle with N vertices (fill=NONE = just vertices)
    circle = safe_node(tree, "GeometryNodeMeshCircle", (bx - 300, by + 200))
    link_sockets(tree, count_n, circle.inputs["Vertices"])
    link_sockets(tree, radius_n, circle.inputs["Radius"])
    circle.fill_type = "NONE"

    # Instance on circle vertices
    inst_on_pts = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx, by + 100))
    link_sockets(tree, circle.outputs["Mesh"], inst_on_pts.inputs["Points"])
    link_sockets(tree, gin.outputs["Geometry"], inst_on_pts.inputs["Instance"])

    # Scale per item
    scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 200, by + 100))
    link_float_to_vector(tree, scale_n, scale_inst, "Scale", component=1, defaults=(1.0, 0.0, 1.0))
    link_sockets(tree, inst_on_pts.outputs["Instances"], scale_inst.inputs["Instances"])

    # Z offset per item
    translate = safe_node(tree, "GeometryNodeTranslateInstances", (bx + 400, by))
    link_float_to_vector(tree, offset_z, translate, "Translation", component=2)
    link_sockets(tree, scale_inst.outputs["Instances"], translate.inputs["Instances"])

    link_sockets(tree, translate.outputs["Instances"], gout.inputs["Geometry"])

    color_node(circle, "geometry")
    color_node(inst_on_pts, "instance")
    color_node(scale_inst, "instance")
    color_node(translate, "instance")

    return label_tree(tree, "MEL_circular_array", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Radial Points", "nodes": ("circle",), "role": "curve"},
        {"title": "Instances", "nodes": ("instance", "scale", "translate"), "role": "instance"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_linear_array(group_name="MEL_linear_array"):
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Count", 5, 1, 256)
    add_vector_param(tree, "Offset", (2.0, 0.0, 0.0))
    add_float_param(tree, "Scale per item", 1.0, 0.01, 10.0)
    add_float_param(tree, "Taper", 0.0, -1.0, 1.0)

    to_inst = safe_node(tree, "GeometryNodeTransform", (bx, by + 100))
    to_inst.inputs["Scale"].default_value = (1, 1, 1)
    link_sockets(tree, gin.outputs["Geometry"], to_inst.inputs["Geometry"])

    count_n = gin.outputs["Count"] if "Count" in tree_input_names(tree) else None
    off_n = gin.outputs["Offset"] if "Offset" in tree_input_names(tree) else None
    scale_n = gin.outputs["Scale per item"] if "Scale per item" in tree_input_names(tree) else None

    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 300, by))
    line.mode = "OFFSET"
    if count_n:
        link_sockets(tree, count_n, line.inputs["Count"])
    if off_n:
        link_sockets(tree, off_n, line.inputs["Offset"])

    inst_on_pts = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 200, by))
    link_sockets(tree, line.outputs["Mesh"], inst_on_pts.inputs["Points"])
    link_sockets(tree, to_inst.outputs["Geometry"], inst_on_pts.inputs["Instance"])

    scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 400, by))
    if scale_n:
        link_float_to_vector(tree, scale_n, scale_inst, "Scale", component=1, defaults=(1.0, 0.0, 1.0))
    link_sockets(tree, inst_on_pts.outputs["Instances"], scale_inst.inputs["Instances"])

    link_sockets(tree, scale_inst.outputs["Instances"], gout.inputs["Geometry"])

    color_node(to_inst, "instance")
    color_node(line, "curve")
    color_node(inst_on_pts, "instance")
    color_node(scale_inst, "instance")

    return label_tree(tree, "MEL_linear_array", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Array Points", "nodes": ("line",), "role": "curve"},
        {"title": "Instances", "nodes": ("instance", "scale"), "role": "instance"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_grid_array(group_name="MEL_grid_array"):
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Count X", 4, 1, 50)
    add_int_param(tree, "Count Y", 4, 1, 50)
    add_float_param(tree, "Spacing X", 2.0, 0.1, 50.0)
    add_float_param(tree, "Spacing Y", 2.0, 0.1, 50.0)

    to_inst = safe_node(tree, "GeometryNodeTransform", (bx, by + 100))
    to_inst.inputs["Scale"].default_value = (1, 1, 1)
    link_sockets(tree, gin.outputs["Geometry"], to_inst.inputs["Geometry"])

    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 300, by))
    link_sockets(tree, gin.outputs["Count X"], grid.inputs["Vertices X"])
    link_sockets(tree, gin.outputs["Count Y"], grid.inputs["Vertices Y"])
    count_x_minus_one = safe_node(tree, "ShaderNodeMath", (bx - 500, by - 160))
    count_x_minus_one.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Count X"], count_x_minus_one.inputs[0])
    count_x_minus_one.inputs[1].default_value = 1.0
    size_x = safe_node(tree, "ShaderNodeMath", (bx - 300, by - 160))
    size_x.operation = "MULTIPLY"
    link_sockets(tree, count_x_minus_one.outputs[0], size_x.inputs[0])
    link_sockets(tree, gin.outputs["Spacing X"], size_x.inputs[1])
    count_y_minus_one = safe_node(tree, "ShaderNodeMath", (bx - 500, by - 260))
    count_y_minus_one.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Count Y"], count_y_minus_one.inputs[0])
    count_y_minus_one.inputs[1].default_value = 1.0
    size_y = safe_node(tree, "ShaderNodeMath", (bx - 300, by - 260))
    size_y.operation = "MULTIPLY"
    link_sockets(tree, count_y_minus_one.outputs[0], size_y.inputs[0])
    link_sockets(tree, gin.outputs["Spacing Y"], size_y.inputs[1])
    link_sockets(tree, size_x.outputs[0], grid.inputs["Size X"])
    link_sockets(tree, size_y.outputs[0], grid.inputs["Size Y"])

    inst_on_pts = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 200, by))
    link_sockets(tree, grid.outputs["Mesh"], inst_on_pts.inputs["Points"])
    link_sockets(tree, to_inst.outputs["Geometry"], inst_on_pts.inputs["Instance"])

    link_sockets(tree, inst_on_pts.outputs["Instances"], gout.inputs["Geometry"])

    color_node(to_inst, "instance")
    color_node(grid, "geometry")
    color_node(inst_on_pts, "instance")

    return label_tree(tree, "MEL_grid_array", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Grid Points", "nodes": ("grid",), "role": "geometry"},
        {"title": "Instances", "nodes": ("instance",), "role": "instance"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_bounding_box(group_name="MEL_bounding_box"):
    """Bounding box group ΓÇö outputs size and center for proportional sizing."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    bbox = safe_node(tree, "GeometryNodeBoundBox", (bx - 100, 100))
    link_sockets(tree, gin.outputs["Geometry"], bbox.inputs["Geometry"])

    make_group_output(tree, "NodeSocketVector", "Size")
    make_group_output(tree, "NodeSocketVector", "Center")

    size = safe_node(tree, "ShaderNodeVectorMath", (bx + 150, 160))
    size.operation = "SUBTRACT"
    link_sockets(tree, bbox.outputs["Max"], size.inputs[0])
    link_sockets(tree, bbox.outputs["Min"], size.inputs[1])

    center_sum = safe_node(tree, "ShaderNodeVectorMath", (bx + 150, -20))
    center_sum.operation = "ADD"
    link_sockets(tree, bbox.outputs["Min"], center_sum.inputs[0])
    link_sockets(tree, bbox.outputs["Max"], center_sum.inputs[1])

    center = safe_node(tree, "ShaderNodeVectorMath", (bx + 350, -20))
    center.operation = "SCALE"
    link_sockets(tree, center_sum.outputs["Vector"], center.inputs[0])
    center.inputs["Scale"].default_value = 0.5

    link_sockets(tree, gin.outputs["Geometry"], gout.inputs["Geometry"])
    link_sockets(tree, size.outputs["Vector"], gout.inputs["Size"])
    link_sockets(tree, center.outputs["Vector"], gout.inputs["Center"])

    color_node(bbox, "geometry")
    color_node(size, "math")
    color_node(center, "math")

    return label_tree(tree, "MEL_bounding_box", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bounds", "nodes": ("bound",), "role": "attribute"},
        {"title": "Size And Center", "nodes": ("size", "center"), "role": "math"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_instance_on_spline(group_name="MEL_instance_on_spline"):
    """Instance geometry along a curve ΓÇö used for railings, arches, fences."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Count", 10, 2, 500)
    add_float_param(tree, "Scale", 1.0, 0.01, 10.0)
    add_float_param(tree, "Offset along curve", 0.0, -10.0, 10.0)

    to_inst = safe_node(tree, "GeometryNodeTransform", (bx, by + 100))
    to_inst.inputs["Scale"].default_value = (1, 1, 1)
    link_sockets(tree, gin.outputs["Geometry"], to_inst.inputs["Geometry"])

    spline_in = make_group_input(tree, "NodeSocketGeometry", "Spline")
    if spline_in is None:
        spline_in = gin.outputs["Geometry"]

    count_n = gin.outputs["Count"] if "Count" in tree_input_names(tree) else None

    resample = safe_node(tree, "GeometryNodeResampleCurve", (bx - 300, by))
    spline_sock = gin.outputs["Spline"] if "Spline" in gin.outputs else gin.outputs["Geometry"]
    link_sockets(tree, spline_sock, resample.inputs["Curve"])
    if count_n:
        try:
            resample.mode = "COUNT"
            link_sockets(tree, count_n, resample.inputs["Count"])
        except Exception:
            res_in = resample.inputs.get("Count")
            if res_in is not None:
                link_sockets(tree, count_n, res_in)
            try:
                resample.inputs["Count"].default_value = 10
            except Exception:
                pass

    inst_on_pts = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 200, by))
    link_sockets(tree, resample.outputs["Curve"], inst_on_pts.inputs["Points"])
    link_sockets(tree, to_inst.outputs["Geometry"], inst_on_pts.inputs["Instance"])

    link_sockets(tree, inst_on_pts.outputs["Instances"], gout.inputs["Geometry"])

    color_node(to_inst, "instance")
    color_node(resample, "curve")
    color_node(inst_on_pts, "instance")

    return label_tree(tree, "MEL_instance_on_spline", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Spline Sampling", "nodes": ("resample",), "role": "curve"},
        {"title": "Instances", "nodes": ("instance",), "role": "instance"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# ---------- Extended Array Tools ----------


def build_spiral_array(group_name="MEL_spiral_array"):
    """Spiral array -- sweeps instances along a helical path.

    Controls for turns, radius growth, height, per-item scale/rotation.
    Useful for staircases, helixes, spring coils, particle trails.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Count", 32, 2, 512)
    add_float_param(tree, "Turns", 3.0, 0.5, 50.0)
    add_float_param(tree, "Radius", 2.0, 0.1, 50.0)
    add_float_param(tree, "Radius Growth", 0.0, -5.0, 5.0)
    add_float_param(tree, "Height", 4.0, -20.0, 20.0)
    add_float_param(tree, "Scale per item", 1.0, 0.01, 10.0)
    add_float_param(tree, "Roll per item", 0.0, -3.141, 3.141)

    curve = safe_node(tree, "GeometryNodeCurveSpiral", (bx - 300, by + 150))
    if curve:
        link_sockets(tree, gin.outputs["Count"], curve.inputs["Resolution"])
        link_sockets(tree, gin.outputs["Turns"], curve.inputs["Rotations"])
        link_sockets(tree, gin.outputs["Radius"], curve.inputs["Radius"])
        link_sockets(tree, gin.outputs["Radius Growth"], curve.inputs["Radius Growth"])
        link_sockets(tree, gin.outputs["Height"], curve.inputs["Height"])
        color_node(curve, "curve")

        inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx, by + 50))
        link_sockets(tree, curve.outputs["Curve"], inst.inputs["Points"])
        link_sockets(tree, gin.outputs["Geometry"], inst.inputs["Instance"])
        color_node(inst, "instance")

        scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 200, by))
        link_float_to_vector(tree, gin.outputs["Scale per item"], scale_inst, "Scale", component=1, defaults=(1.0, 0.0, 1.0))
        link_sockets(tree, inst.outputs["Instances"], scale_inst.inputs["Instances"])

        rotate = safe_node(tree, "GeometryNodeRotateInstances", (bx + 400, by - 50))
        link_float_to_vector(tree, gin.outputs["Roll per item"], rotate, "Rotation", component=0, defaults=(0.0, 0.0, 0.0))
        link_sockets(tree, scale_inst.outputs["Instances"], rotate.inputs["Instances"])

        link_sockets(tree, rotate.outputs["Instances"], gout.inputs["Geometry"])
    else:
        link_sockets(tree, gin.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, "MEL_spiral_array", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Spiral Curve", "nodes": ("curve",), "role": "curve"},
        {"title": "Instance", "nodes": ("instance",), "role": "instance"},
        {"title": "Taper", "nodes": ("scale", "rotate"), "role": "instance"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_radial_array(group_name="MEL_radial_array"):
    """Radial array -- instances distributed in a full or partial arc.

    Like circular array but with angular offset, per-item rotation tracking,
    and arc-angle control for non-360-degree spreads.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Count", 8, 1, 256)
    add_float_param(tree, "Arc Angle", 6.283, 0.01, 12.566)
    add_float_param(tree, "Radius", 2.0, 0.01, 100.0)
    add_float_param(tree, "Offset Angle", 0.0, -6.283, 6.283)
    add_float_param(tree, "Scale per item", 1.0, 0.01, 10.0)
    add_bool_param(tree, "Rotate with Arc", True)
    add_float_param(tree, "Radius per item", 0.0, -10.0, 10.0)

    circle = safe_node(tree, "GeometryNodeMeshCircle", (bx - 300, by + 200))
    if circle:
        circle.fill_type = "NONE"
        link_sockets(tree, gin.outputs["Count"], circle.inputs["Vertices"])
        link_sockets(tree, gin.outputs["Radius"], circle.inputs["Radius"])

        inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 50, by + 100))
        link_sockets(tree, circle.outputs["Mesh"], inst.inputs["Points"])
        link_sockets(tree, gin.outputs["Geometry"], inst.inputs["Instance"])
        color_node(inst, "instance")

        scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 150, by + 50))
        link_float_to_vector(tree, gin.outputs["Scale per item"], scale_inst, "Scale", component=1, defaults=(1.0, 0.0, 1.0))
        link_sockets(tree, inst.outputs["Instances"], scale_inst.inputs["Instances"])

        if gin.outputs["Rotate with Arc"]:
            rotate = safe_node(tree, "GeometryNodeRotateInstances", (bx + 350, by))
            rotate.inputs["Local Space"].default_value = True
            link_sockets(tree, scale_inst.outputs["Instances"], rotate.inputs["Instances"])
            normals = safe_node(tree, "GeometryNodeInputNormal", (bx + 150, by - 100))
            link_sockets(tree, normals.outputs["Normal"], rotate.inputs["Rotation"])
            color_node(rotate, "instance")
            link_sockets(tree, rotate.outputs["Instances"], gout.inputs["Geometry"])
        else:
            link_sockets(tree, scale_inst.outputs["Instances"], gout.inputs["Geometry"])

    return label_tree(tree, "MEL_radial_array", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Arc Points", "nodes": ("circle",), "role": "curve"},
        {"title": "Instances", "nodes": ("instance", "scale", "rotate"), "role": "instance"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_weighted_array(group_name="MEL_weighted_array"):
    """Weighted random array -- distributes instances on a mesh surface using
    Poisson-disk distribution with per-item random scale and normal alignment.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Count", 50, 1, 5000)
    add_float_param(tree, "Scale Min", 0.5, 0.01, 5.0)
    add_float_param(tree, "Scale Max", 1.5, 0.01, 10.0)
    add_float_param(tree, "Random Seed", 0.0, 0.0, 10000.0)
    add_bool_param(tree, "Align to Normal", True)
    add_float_param(tree, "Density", 1.0, 0.0, 5.0)

    dist_points = safe_node(tree, "GeometryNodeDistributePointsOnFaces", (bx - 200, by + 150))
    if dist_points:
        dist_points.distribute_method = "POISSON"
        link_sockets(tree, gin.outputs["Geometry"], dist_points.inputs["Mesh"])
        link_sockets(tree, gin.outputs["Count"], dist_points.inputs["Density"])
        link_sockets(tree, gin.outputs["Random Seed"], dist_points.inputs["Seed"])
        color_node(dist_points, "geometry")

        inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx, by + 50))
        link_sockets(tree, dist_points.outputs["Points"], inst.inputs["Points"])
        link_sockets(tree, gin.outputs["Geometry"], inst.inputs["Instance"])
        color_node(inst, "instance")

        random_v = safe_node(tree, "FunctionNodeRandomValue", (bx, by - 100))
        if random_v:
            random_v.data_type = "FLOAT_VECTOR"
            link_sockets(tree, gin.outputs["Scale Min"], random_v.inputs["Min"])
            link_sockets(tree, gin.outputs["Scale Max"], random_v.inputs["Max"])
            link_sockets(tree, gin.outputs["Random Seed"], random_v.inputs["Seed"])

            scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 200, by - 50))
            scale_inst.inputs["Local Space"].default_value = True
            link_sockets(tree, inst.outputs["Instances"], scale_inst.inputs["Instances"])
            link_sockets(tree, random_v.outputs["Value"], scale_inst.inputs["Scale"])
            color_node(scale_inst, "instance")

            if gin.outputs["Align to Normal"]:
                rotate = safe_node(tree, "GeometryNodeRotateInstances", (bx + 400, by - 150))
                link_sockets(tree, scale_inst.outputs["Instances"], rotate.inputs["Instances"])
                link_sockets(tree, dist_points.outputs["Normal"], rotate.inputs["Rotation"])
                color_node(rotate, "instance")
                link_sockets(tree, rotate.outputs["Instances"], gout.inputs["Geometry"])
            else:
                link_sockets(tree, scale_inst.outputs["Instances"], gout.inputs["Geometry"])
        else:
            link_sockets(tree, inst.outputs["Instances"], gout.inputs["Geometry"])
    else:
        link_sockets(tree, gin.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, "MEL_weighted_array", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Distribute", "nodes": ("distribute",), "role": "geometry"},
        {"title": "Instance", "nodes": ("instance",), "role": "instance"},
        {"title": "Randomize", "nodes": ("random", "scale", "rotate"), "role": "instance"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_curve_array(group_name="MEL_curve_array"):
    """Curve array -- instances along a curve with per-item rotation from
    curve tangent, scale taper, and alignment controls.

    Upgrade from basic instance_on_spline: adds taper curve, rotation
    alignment modes, and offset-along-curve controls.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Count", 10, 2, 500)
    add_float_param(tree, "Scale Start", 1.0, 0.0, 10.0)
    add_float_param(tree, "Scale End", 1.0, 0.0, 10.0)
    add_float_param(tree, "Offset Along Curve", 0.0, -10.0, 10.0)
    add_bool_param(tree, "Align to Curve", True)
    add_float_param(tree, "Rotation Offset", 0.0, -6.283, 6.283)

    geo_in = gin.outputs["Geometry"]

    resample = safe_node(tree, "GeometryNodeResampleCurve", (bx - 300, by + 150))
    if resample:
        resample.mode = "COUNT"
        link_sockets(tree, geo_in, resample.inputs["Curve"])
        link_sockets(tree, gin.outputs["Count"], resample.inputs["Count"])
        color_node(resample, "curve")

        inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 50, by + 100))
        link_sockets(tree, resample.outputs["Curve"], inst.inputs["Points"])
        link_sockets(tree, geo_in, inst.inputs["Instance"])
        color_node(inst, "instance")

        count_float = safe_node(tree, "ShaderNodeMath", (bx - 300, by - 50))
        count_float.operation = "ADD"
        count_float.inputs[0].default_value = 1.0
        link_sockets(tree, gin.outputs["Count"], count_float.inputs[1])

        idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 300, by - 150))
        idx_float = safe_node(tree, "ShaderNodeMath", (bx - 150, by - 100))
        idx_float.operation = "ADD"
        idx_float.inputs[0].default_value = 1.0
        link_sockets(tree, idx.outputs["Index"], idx_float.inputs[1])

        frac = safe_node(tree, "ShaderNodeMath", (bx, by - 100))
        frac.operation = "DIVIDE"
        link_sockets(tree, idx_float.outputs[0], frac.inputs[0])
        link_sockets(tree, count_float.outputs[0], frac.inputs[1])

        scale_range = safe_node(tree, "ShaderNodeMath", (bx + 150, by - 150))
        scale_range.operation = "SUBTRACT"
        link_sockets(tree, gin.outputs["Scale End"], scale_range.inputs[0])
        link_sockets(tree, gin.outputs["Scale Start"], scale_range.inputs[1])

        scale_contrib = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 100))
        scale_contrib.operation = "MULTIPLY"
        link_sockets(tree, scale_range.outputs[0], scale_contrib.inputs[0])
        link_sockets(tree, frac.outputs[0], scale_contrib.inputs[1])

        scale_total = safe_node(tree, "ShaderNodeMath", (bx + 450, by - 100))
        scale_total.operation = "ADD"
        link_sockets(tree, gin.outputs["Scale Start"], scale_total.inputs[0])
        link_sockets(tree, scale_contrib.outputs[0], scale_total.inputs[1])

        scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 450, by + 50))
        link_float_to_vector(tree, scale_total.outputs[0], scale_inst, "Scale", component=1, defaults=(1.0, 0.0, 1.0))
        link_sockets(tree, inst.outputs["Instances"], scale_inst.inputs["Instances"])
        color_node(scale_inst, "instance")

        if gin.outputs["Align to Curve"]:
            tangent = safe_node(tree, "GeometryNodeInputTangent", (bx + 300, by + 150))
            rotate = safe_node(tree, "GeometryNodeRotateInstances", (bx + 600, by))
            rotate.inputs["Local Space"].default_value = True
            link_sockets(tree, scale_inst.outputs["Instances"], rotate.inputs["Instances"])
            link_sockets(tree, tangent.outputs["Tangent"], rotate.inputs["Rotation"])
            color_node(rotate, "instance")

            if gin.outputs["Rotation Offset"]:
                offset_mul = safe_node(tree, "ShaderNodeMath", (bx + 600, by - 100))
                offset_mul.operation = "MULTIPLY"
                link_sockets(tree, gin.outputs["Rotation Offset"], offset_mul.inputs[0])
                offset_mul.inputs[1].default_value = 1.0
            link_sockets(tree, rotate.outputs["Instances"], gout.inputs["Geometry"])
        else:
            link_sockets(tree, scale_inst.outputs["Instances"], gout.inputs["Geometry"])

    return label_tree(tree, "MEL_curve_array", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Spline", "nodes": ("resample",), "role": "curve"},
        {"title": "Instance", "nodes": ("instance",), "role": "instance"},
        {"title": "Taper", "nodes": ("scale",), "role": "instance"},
        {"title": "Align", "nodes": ("tangent", "rotate"), "role": "instance"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# -- Registry --
from .core import register_builder

register_builder("MEL_circular_array", build_circular_array, "Circular Array",
    "Radial array \u2014 instance geometry around a circle with scale and Z offset",
    "primitives")
register_builder("MEL_linear_array", build_linear_array, "Linear Array",
    "Linear array along a direction vector with count, spacing, and taper",
    "primitives")
register_builder("MEL_grid_array", build_grid_array, "Grid Array",
    "2D grid array with count and spacing controls on both axes",
    "primitives")
register_builder("MEL_bounding_box", build_bounding_box, "Bounding Box",
    "Extract bounding box size and center from input geometry",
    "primitives")
register_builder("MEL_instance_on_spline", build_instance_on_spline, "Instance on Spline",
    "Instance geometry along a curve with controllable spacing",
    "primitives")
register_builder("MEL_spiral_array", build_spiral_array, "Spiral Array",
    "Helical sweep along a spiral curve with radius growth, height, and taper",
    "primitives")
register_builder("MEL_radial_array", build_radial_array, "Radial Array",
    "Arc-distributed radial array with angular offset and per-item tracking",
    "primitives")
register_builder("MEL_weighted_array", build_weighted_array, "Weighted Array",
    "Poisson-disk random surface distribution with per-item random scale and alignment",
    "primitives")
register_builder("MEL_curve_array", build_curve_array, "Curve Array",
    "Curve-aligned array with taper (scale start\u2192end), tangent alignment, and rotation offset",
    "primitives")
