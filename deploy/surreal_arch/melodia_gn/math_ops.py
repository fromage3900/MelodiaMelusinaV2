"""Math operation GN group builders ΓÇö add, subtract, power scale, exponent blend, named attributes."""

from __future__ import annotations

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, new_geometry_tree,
    add_float_param, add_bool_param, add_vector_param,
    make_group_input,
)


def build_add_geometry(group_name="MEL_add_geometry"):
    """Union-merge two geometry inputs."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    make_group_input(tree, "NodeSocketGeometry", "Geometry B")
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx, by))
    link_sockets(tree, gin.outputs["Geometry"], join.inputs["Geometry"])
    if "Geometry B" in gin.outputs:
        link_sockets(tree, gin.outputs["Geometry B"], join.inputs["Geometry"])
    link_sockets(tree, join.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(join, "geometry")
    return tree


def build_subtract_geometry(group_name="MEL_subtract_geometry"):
    """Boolean difference between two geometry inputs."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    make_group_input(tree, "NodeSocketGeometry", "Geometry B")
    bool_node = safe_node(tree, "GeometryNodeMeshBoolean", (bx, by))
    bool_node.operation = "DIFFERENCE"
    link_sockets(tree, gin.outputs["Geometry"], bool_node.inputs["Mesh 2"])
    if "Geometry B" in gin.outputs:
        link_sockets(tree, gin.outputs["Geometry B"], bool_node.inputs["Mesh 1"])
    link_sockets(tree, bool_node.outputs["Mesh"], gout.inputs["Geometry"])

    color_node(bool_node, "math")
    return tree


def build_power_scale(group_name="MEL_power_scale"):
    """Scale instances with exponential power falloff along an axis.

    Useful for tapering columns, creating diminishing returns on arrays.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Base Scale", 1.0, 0.01, 10.0)
    add_float_param(tree, "Power", 0.8, 0.01, 5.0)

    index = safe_node(tree, "GeometryNodeInputIndex", (bx - 300, by + 100))

    # Power formula: base * (index+1) ^ -power
    idx_f = safe_node(tree, "ShaderNodeMath", (bx - 100, by + 100))
    idx_f.operation = "ADD"
    idx_f.inputs[0].default_value = 1.0
    link_sockets(tree, index.outputs["Index"], idx_f.inputs[1])

    exp = safe_node(tree, "ShaderNodeMath", (bx + 100, by + 100))
    exp.operation = "POWER"
    link_sockets(tree, idx_f.outputs[0], exp.inputs[0])
    link_sockets(tree, gin.outputs["Power"], exp.inputs[1])

    # Multiply by base scale
    mul = safe_node(tree, "ShaderNodeMath", (bx + 300, by + 100))
    mul.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Base Scale"], mul.inputs[0])
    link_sockets(tree, exp.outputs[0], mul.inputs[1])

    # Scale instances (uniform power scale on all axes)
    scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 200, by - 100))
    link_sockets(tree, gin.outputs["Geometry"], scale_inst.inputs["Instances"])
    combine = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 100, by - 200))
    link_sockets(tree, mul.outputs[0], combine.inputs["X"])
    link_sockets(tree, mul.outputs[0], combine.inputs["Y"])
    link_sockets(tree, mul.outputs[0], combine.inputs["Z"])
    link_sockets(tree, combine.outputs["Vector"], scale_inst.inputs["Scale"])

    link_sockets(tree, scale_inst.outputs["Instances"], gout.inputs["Geometry"])

    color_node(index, "attribute")
    color_node(exp, "math")
    color_node(mul, "math")
    color_node(scale_inst, "instance")

    return tree


def build_exponent_blend(group_name="MEL_exponent_blend"):
    """Blend between two positions using an exponent curve ΓÇö smooth transitions."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Blend Factor", 0.5, 0.0, 1.0)
    add_float_param(tree, "Exponent", 1.0, 0.1, 5.0)
    add_vector_param(tree, "Start Position", (0.0, 0.0, 0.0))
    add_vector_param(tree, "End Position", (1.0, 1.0, 1.0))

    # Blend = factor ^ exponent
    exp_n = safe_node(tree, "ShaderNodeMath", (bx - 100, by + 100))
    exp_n.operation = "POWER"
    link_sockets(tree, gin.outputs["Blend Factor"], exp_n.inputs[0])
    link_sockets(tree, gin.outputs["Exponent"], exp_n.inputs[1])

    # Lerp: start + (end - start) * blend
    sub = safe_node(tree, "ShaderNodeVectorMath", (bx + 100, by))
    sub.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["End Position"], sub.inputs[0])
    link_sockets(tree, gin.outputs["Start Position"], sub.inputs[1])

    mul = safe_node(tree, "ShaderNodeVectorMath", (bx + 300, by))
    mul.operation = "MULTIPLY"
    link_sockets(tree, sub.outputs["Vector"], mul.inputs[0])
    link_sockets(tree, exp_n.outputs[0], mul.inputs[1])

    add = safe_node(tree, "ShaderNodeVectorMath", (bx + 500, by))
    add.operation = "ADD"
    link_sockets(tree, gin.outputs["Start Position"], add.inputs[0])
    link_sockets(tree, mul.outputs["Vector"], add.inputs[1])

    # Set Position on geometry
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 200, by - 200))
    link_sockets(tree, gin.outputs["Geometry"], set_pos.inputs["Geometry"])
    link_sockets(tree, add.outputs["Vector"], set_pos.inputs["Position"])
    link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(exp_n, "math")
    color_node(set_pos, "attribute")

    return tree


def build_store_named_attr(group_name="MEL_store_named_attr"):
    """Store a named attribute ΓÇö enables data passing between stacked modifiers."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    # Custom socket for attribute name
    make_group_input(tree, "NodeSocketString", "Attribute Name")
    add_float_param(tree, "Value", 0.0)
    add_vector_param(tree, "Vector Value", (0.0, 0.0, 0.0))

    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx, by))
    link_sockets(tree, gin.outputs["Geometry"], store.inputs["Geometry"])
    if "Attribute Name" in gin.outputs:
        link_sockets(tree, gin.outputs["Attribute Name"], store.inputs["Name"])

    # Float value
    link_sockets(tree, gin.outputs["Value"], store.inputs["Value"])

    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(store, "attribute")
    return tree


def build_attribute_math(group_name="MEL_attribute_math"):
    """Do math on a named attribute: add, multiply, power."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    make_group_input(tree, "NodeSocketString", "Attribute Name")
    add_float_param(tree, "Factor", 1.0, -10.0, 10.0)
    make_group_input(tree, "NodeSocketInt", "Operation", default=0)

    # Named attribute
    attr = safe_node(tree, "GeometryNodeInputNamedAttribute", (bx - 300, by + 100))
    attr.data_type = "FLOAT"
    if "Attribute Name" in gin.outputs:
        link_sockets(tree, gin.outputs["Attribute Name"], attr.inputs["Name"])

    # Math node
    math_n = safe_node(tree, "ShaderNodeMath", (bx - 100, by))
    link_sockets(tree, attr.outputs["Attribute"], math_n.inputs[0])
    link_sockets(tree, gin.outputs["Factor"], math_n.inputs[1])

    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 300, by))
    link_sockets(tree, gin.outputs["Geometry"], store.inputs["Geometry"])
    attr_name_sock = store.inputs.get("Name") if "Attribute Name" in gin.outputs else None
    if attr_name_sock:
        link_sockets(tree, gin.outputs["Attribute Name"], attr_name_sock)
    link_sockets(tree, math_n.outputs[0], store.inputs["Value"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(attr, "attribute")
    color_node(math_n, "math")
    color_node(store, "attribute")

    return tree


# -- Registry --
from .core import register_builder

register_builder("MEL_add_geometry", build_add_geometry, "Add (Union)",
    "Boolean union ΓÇö merge two geometry inputs",
    "math_attrs")
register_builder("MEL_subtract_geometry", build_subtract_geometry, "Subtract (Difference)",
    "Boolean difference ΓÇö subtract second geometry from first",
    "math_attrs")
register_builder("MEL_power_scale", build_power_scale, "Power Scale",
    "Exponential power falloff scale along an axis for tapering",
    "math_attrs")
register_builder("MEL_exponent_blend", build_exponent_blend, "Exponent Blend",
    "Blend between two position sets using exponent curve",
    "math_attrs")
register_builder("MEL_store_named_attr", build_store_named_attr, "Store Named Attribute",
    "Store a named float/vector attribute on geometry for downstream mods",
    "math_attrs")
register_builder("MEL_attribute_math", build_attribute_math, "Attribute Math",
    "Read named attribute, apply math op, store result back",
    "math_attrs")
