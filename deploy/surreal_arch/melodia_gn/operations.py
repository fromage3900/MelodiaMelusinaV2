"""Composite operations  --  multi-iteration power falloff and bounded auto-fit content.

MEL_op_iterate: instance geometry N times with power-scale falloff along axis
MEL_op_bounded: auto-scale content to fit a target bounding box

Composes: circular_array, power_scale, bounding_box, exponent_blend, store_attribute
"""

from __future__ import annotations

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, add_vector_param,
    make_group_input,
)


def build_op_iterate(group_name="MEL_op_iterate"):
    """Multi-iteration instancer with power-scale falloff.

    Takes any geometry, instances it N times along an axis with
    exponential power falloff on scale. Each instance stores its
    iteration index as a named attribute.

    Uses: power (falloff curve), circular_array (positioning),
          store_attribute (iteration index for downstream)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Count", 8, 1, 256)
    add_float_param(tree, "Spacing", 1.0, 0.01, 20.0)
    add_float_param(tree, "Base Scale", 1.0, 0.01, 5.0)
    add_float_param(tree, "Power Falloff", 0.5, 0.0, 3.0)
    add_vector_param(tree, "Direction", (1.0, 0.0, 0.0))
    add_bool_param(tree, "Even Spacing", True)

    # Build array points along direction
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 300, by + 300))
    line.mode = "END_POINTS"
    link_sockets(tree, gin.outputs["Count"], line.inputs["Count"])
    link_float_to_vector(tree, gin.outputs["Spacing"], line, "Start Location", component=0)

    # Instance input geometry on each point
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 100, by + 300))
    link_sockets(tree, line.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, gin.outputs["Geometry"], inst.inputs["Instance"])

    # Power scale: base * ( (idx+1) / count ) ^ power
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 300, by + 100))

    idx_f = safe_node(tree, "ShaderNodeMath", (bx - 100, by + 100))
    idx_f.operation = "ADD"
    idx_f.inputs[0].default_value = 1.0
    link_sockets(tree, idx.outputs["Index"], idx_f.inputs[1])

    count_f = safe_node(tree, "ShaderNodeMath", (bx - 100, by))
    count_f.operation = "ADD"
    count_f.inputs[0].default_value = 1.0
    link_sockets(tree, gin.outputs["Count"], count_f.inputs[1])

    norm = safe_node(tree, "ShaderNodeMath", (bx + 100, by + 100))
    norm.operation = "DIVIDE"
    link_sockets(tree, idx_f.outputs[0], norm.inputs[0])
    link_sockets(tree, count_f.outputs[0], norm.inputs[1])

    power_n = safe_node(tree, "ShaderNodeMath", (bx + 300, by + 100))
    power_n.operation = "POWER"
    link_sockets(tree, norm.outputs[0], power_n.inputs[0])
    link_sockets(tree, gin.outputs["Power Falloff"], power_n.inputs[1])

    final_scale = safe_node(tree, "ShaderNodeMath", (bx + 500, by + 100))
    final_scale.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Base Scale"], final_scale.inputs[0])
    link_sockets(tree, power_n.outputs[0], final_scale.inputs[1])

    # Direction vector
    scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 500, by + 300))
    link_sockets(tree, inst.outputs["Instances"], scale_inst.inputs["Instances"])
    dir_sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx + 300, by + 200))
    link_sockets(tree, gin.outputs["Direction"], dir_sep.inputs["Vector"])
    scale_combine = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 500, by + 200))
    link_sockets(tree, dir_sep.outputs["X"], scale_combine.inputs["X"])
    link_sockets(tree, final_scale.outputs[0], scale_combine.inputs["Y"])
    link_sockets(tree, scale_combine.outputs["Vector"], scale_inst.inputs["Scale"])

    # Store iteration index attribute
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 700, by + 300))
    link_sockets(tree, scale_inst.outputs["Instances"], realize.inputs["Geometry"])

    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 900, by + 300))
    link_sockets(tree, realize.outputs["Geometry"], store.inputs["Geometry"])
    link_sockets(tree, idx.outputs["Index"], store.inputs["Value"])
    store.data_type = "INT"
    store.domain = "FACE"

    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(line, "curve")
    color_node(inst, "instance")
    color_node(scale_inst, "instance")
    color_node(power_n, "math")
    color_node(store, "attribute")

    return label_tree(tree, "MEL_op_iterate", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Array Points", "nodes": ("line",), "role": "curve"},
        {"title": "Power Scale", "nodes": ("power", "scale"), "role": "math"},
        {"title": "Iteration Attribute", "nodes": ("store", "index"), "role": "attribute"},
    ])


def build_op_bounded(group_name="MEL_op_bounded"):
    """Auto-fit content to a target bounding box.

    Reads bounding box of input geometry, scales and translates content
    to exactly fill the target dimensions. Useful for fitting ornamental
    panels, windows, doors into wall openings.

    Uses: bounding_box (source + target), exponent_blend (fit curve),
          store_attribute (orig size for downstream)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    make_group_input(tree, "NodeSocketGeometry", "Content")
    make_group_input(tree, "NodeSocketGeometry", "Target Bounds")

    add_float_param(tree, "Padding", 0.02, 0.0, 0.5)
    add_float_param(tree, "Fit Exponent", 1.0, 0.1, 3.0)
    add_bool_param(tree, "Uniform Scale", True)
    add_bool_param(tree, "Center", True)

    # Bounding box of content
    bbox_content = safe_node(tree, "GeometryNodeBoundBox", (bx - 400, by + 400))
    if "Content" in gin.outputs:
        link_sockets(tree, gin.outputs["Content"], bbox_content.inputs["Geometry"])

    # Bounding box of target
    bbox_target = safe_node(tree, "GeometryNodeBoundBox", (bx - 400, by + 200))
    if "Target Bounds" in gin.outputs:
        link_sockets(tree, gin.outputs["Target Bounds"], bbox_target.inputs["Geometry"])

    # Get sizes from bounding boxes
    # Content size
    sep_min_c = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 200, by + 400))
    link_sockets(tree, bbox_content.outputs["Min"], sep_min_c.inputs["Vector"])
    sep_max_c = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 200, by + 300))
    link_sockets(tree, bbox_content.outputs["Max"], sep_max_c.inputs["Vector"])

    size_c_x = safe_node(tree, "ShaderNodeMath", (bx, by + 400))
    size_c_x.operation = "SUBTRACT"
    link_sockets(tree, sep_max_c.outputs["X"], size_c_x.inputs[0])
    link_sockets(tree, sep_min_c.outputs["X"], size_c_x.inputs[1])

    size_c_y = safe_node(tree, "ShaderNodeMath", (bx, by + 300))
    size_c_y.operation = "SUBTRACT"
    link_sockets(tree, sep_max_c.outputs["Y"], size_c_y.inputs[0])
    link_sockets(tree, sep_min_c.outputs["Y"], size_c_y.inputs[1])

    size_c_z = safe_node(tree, "ShaderNodeMath", (bx, by + 200))
    size_c_z.operation = "SUBTRACT"
    link_sockets(tree, sep_max_c.outputs["Z"], size_c_z.inputs[0])
    link_sockets(tree, sep_min_c.outputs["Z"], size_c_z.inputs[1])

    # Target size
    sep_min_t = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 200, by + 100))
    link_sockets(tree, bbox_target.outputs["Min"], sep_min_t.inputs["Vector"])
    sep_max_t = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 200, by))
    link_sockets(tree, bbox_target.outputs["Max"], sep_max_t.inputs["Vector"])

    size_t_x = safe_node(tree, "ShaderNodeMath", (bx, by + 100))
    size_t_x.operation = "SUBTRACT"
    link_sockets(tree, sep_max_t.outputs["X"], size_t_x.inputs[0])
    link_sockets(tree, sep_min_t.outputs["X"], size_t_x.inputs[1])

    size_t_y = safe_node(tree, "ShaderNodeMath", (bx, by))
    size_t_y.operation = "SUBTRACT"
    link_sockets(tree, sep_max_t.outputs["Y"], size_t_y.inputs[0])
    link_sockets(tree, sep_min_t.outputs["Y"], size_t_y.inputs[1])

    size_t_z = safe_node(tree, "ShaderNodeMath", (bx, by - 100))
    size_t_z.operation = "SUBTRACT"
    link_sockets(tree, sep_max_t.outputs["Z"], size_t_z.inputs[0])
    link_sockets(tree, sep_min_t.outputs["Z"], size_t_z.inputs[1])

    # Scale ratios: target / content (with padding)
    pad = safe_node(tree, "ShaderNodeMath", (bx + 200, by + 400))
    pad.operation = "SUBTRACT"
    pad.inputs[0].default_value = 1.0
    link_sockets(tree, gin.outputs["Padding"], pad.inputs[1])

    ratio_x = safe_node(tree, "ShaderNodeMath", (bx + 200, by + 300))
    ratio_x.operation = "DIVIDE"
    link_sockets(tree, size_t_x.outputs[0], ratio_x.inputs[0])
    link_sockets(tree, size_c_x.outputs[0], ratio_x.inputs[1])
    link_sockets(tree, pad.outputs[0], ratio_x.inputs[1])

    ratio_y = safe_node(tree, "ShaderNodeMath", (bx + 200, by + 200))
    ratio_y.operation = "DIVIDE"
    link_sockets(tree, size_t_y.outputs[0], ratio_y.inputs[0])
    link_sockets(tree, size_c_y.outputs[0], ratio_y.inputs[1])
    link_sockets(tree, pad.outputs[0], ratio_y.inputs[1])

    ratio_z = safe_node(tree, "ShaderNodeMath", (bx + 200, by + 100))
    ratio_z.operation = "DIVIDE"
    link_sockets(tree, size_t_z.outputs[0], ratio_z.inputs[0])
    link_sockets(tree, size_c_z.outputs[0], ratio_z.inputs[1])
    link_sockets(tree, pad.outputs[0], ratio_z.inputs[1])

    # Uniform or per-axis scale
    if gin.outputs["Uniform Scale"]:
        min_xyz = safe_node(tree, "ShaderNodeMath", (bx + 400, by + 250))
        min_xyz.operation = "MINIMUM"
        link_sockets(tree, ratio_x.outputs[0], min_xyz.inputs[0])
        link_sockets(tree, ratio_y.outputs[0], min_xyz.inputs[1])

        unif_scale = safe_node(tree, "ShaderNodeMath", (bx + 600, by + 250))
        unif_scale.operation = "MINIMUM"
        link_sockets(tree, min_xyz.outputs[0], unif_scale.inputs[0])
        link_sockets(tree, ratio_z.outputs[0], unif_scale.inputs[1])

        combine = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 800, by + 250))
        link_sockets(tree, unif_scale.outputs[0], combine.inputs["X"])
        link_sockets(tree, unif_scale.outputs[0], combine.inputs["Y"])
        link_sockets(tree, unif_scale.outputs[0], combine.inputs["Z"])
    else:
        combine = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 400, by + 250))
        link_sockets(tree, ratio_x.outputs[0], combine.inputs["X"])
        link_sockets(tree, ratio_y.outputs[0], combine.inputs["Y"])
        link_sockets(tree, ratio_z.outputs[0], combine.inputs["Z"])

    # Transform content
    transform = safe_node(tree, "GeometryNodeTransform", (bx + 1000, by + 300))
    content_sock = gin.outputs.get("Content")
    if content_sock is not None:
        link_sockets(tree, content_sock, transform.inputs["Geometry"])
    link_sockets(tree, combine.outputs["Vector"], transform.inputs["Scale"])

    # Center in target bounds
    if gin.outputs["Center"]:
        center_add = safe_node(tree, "ShaderNodeVectorMath", (bx + 800, by))
        center_add.operation = "ADD"
        link_sockets(tree, bbox_target.outputs["Min"], center_add.inputs[0])
        link_sockets(tree, bbox_target.outputs["Max"], center_add.inputs[1])
        center_target = safe_node(tree, "ShaderNodeVectorMath", (bx + 1000, by))
        center_target.operation = "SCALE"
        link_sockets(tree, center_add.outputs["Vector"], center_target.inputs[0])
        center_target.inputs["Scale"].default_value = 0.5

        set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 1000, by + 100))
        link_sockets(tree, transform.outputs["Geometry"], set_pos.inputs["Geometry"])
        link_sockets(tree, center_target.outputs["Vector"], set_pos.inputs["Position"])

        link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])
    else:
        link_sockets(tree, transform.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(bbox_content, "attribute")
    color_node(bbox_target, "attribute")
    color_node(transform, "instance")

    return label_tree(tree, "MEL_op_bounded", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bounds", "nodes": ("bbox", "target"), "role": "attribute"},
        {"title": "Fit Math", "nodes": ("ratio", "scale", "min"), "role": "math"},
        {"title": "Output", "nodes": ("transform", "Group Output"), "role": "output"},
    ])


# -- Registry --
from .core import register_builder

register_builder("MEL_op_iterate", build_op_iterate, "Iterate + Power Falloff",
    "Multi-iteration instancer with power-scale falloff along a direction",
    "operations")
register_builder("MEL_op_bounded", build_op_bounded, "Bounded Auto-Fit",
    "Auto-fit - scale source to match target bounding box (uniform or per-axis)",
    "operations")
