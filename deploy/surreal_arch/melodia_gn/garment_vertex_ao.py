"""Garment vertex AO — bakes fold-depth ambient occlusion into vertex colors."""

from __future__ import annotations
import bpy
from .core import (
    add_float_param, add_int_param, label_tree,
    link_sockets, new_geometry_tree, register_builder, safe_node, sock,
)


def _math(tree, op, loc):
    n = safe_node(tree, "ShaderNodeMath", loc)
    n.operation = op
    return n


def build_garment_vertex_ao(group_name="MEL_garment_vertex_ao"):
    """Bake garment fold AO into vertex colors (simplified)."""
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "AO Strength", 1.0, 0.0, 5.0)
    add_float_param(tree, "Base Color", 1.0, 0.0, 1.0)

    geo = sock(gin, "Geometry", outputs=True)
    bx, by = 0, 0

    # 1. Read tension_fold (FLOAT)
    tension_attr = safe_node(tree, "GeometryNodeInputNamedAttribute", (bx, by))
    tension_attr.data_type = "FLOAT"
    tension_attr.inputs["Name"].default_value = "tension_fold"
    tension_val = sock(tension_attr, "Attribute", outputs=True)
    tension_exists = sock(tension_attr, "Exists", outputs=True)

    # 2. Rest-deviation proxy
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx, by - 200))
    rest_attr = safe_node(tree, "GeometryNodeInputNamedAttribute", (bx, by - 200))
    rest_attr.data_type = "FLOAT_VECTOR"
    rest_attr.inputs["Name"].default_value = "rest_position"
    rest_pos = sock(rest_attr, "Attribute", outputs=True)

    diff = safe_node(tree, "ShaderNodeVectorMath", (bx + 200, by - 200))
    diff.operation = "SUBTRACT"
    link_sockets(tree, sock(pos, "Position", outputs=True), sock(diff, "Vector"))
    link_sockets(tree, rest_pos, sock(diff, "Vector 1"))

    proxy_len = safe_node(tree, "ShaderNodeVectorMath", (bx + 400, by - 200))
    proxy_len.operation = "LENGTH"
    link_sockets(tree, sock(diff, "Vector", outputs=True), sock(proxy_len, "Vector"))
    proxy_val = sock(proxy_len, "Value", outputs=True)

    # 3. Select fold depth
    fold_sw = safe_node(tree, "GeometryNodeSwitch", (bx + 600, by))
    fold_sw.input_type = "FLOAT"
    link_sockets(tree, tension_exists, sock(fold_sw, "Switch"))
    link_sockets(tree, proxy_val, sock(fold_sw, "False"))
    link_sockets(tree, tension_val, sock(fold_sw, "True"))
    fold_depth = sock(fold_sw, "Output", outputs=True)

    # 4. AO = clamp(depth * strength, 0, 1)
    ao_mul = _math(tree, "MULTIPLY", (bx + 800, by))
    link_sockets(tree, fold_depth, ao_mul.inputs[0])
    link_sockets(tree, sock(gin, "AO Strength", outputs=True), ao_mul.inputs[1])
    ao_clamp = safe_node(tree, "ShaderNodeClamp", (bx + 1000, by))
    sock(ao_clamp, "Min").default_value = 0.0
    sock(ao_clamp, "Max").default_value = 1.0
    link_sockets(tree, ao_mul.outputs[0], sock(ao_clamp, "Value"))

    # 5. final = base * (1 - ao * 0.6)
    ao_dark = _math(tree, "MULTIPLY", (bx + 1200, by))
    link_sockets(tree, ao_clamp.outputs[0], ao_dark.inputs[0])
    ao_dark.inputs[1].default_value = 0.6
    factor = _math(tree, "SUBTRACT", (bx + 1400, by))
    factor.inputs[0].default_value = 1.0
    link_sockets(tree, ao_dark.outputs[0], factor.inputs[1])
    combined = _math(tree, "MULTIPLY", (bx + 1600, by))
    link_sockets(tree, sock(gin, "Base Color", outputs=True), combined.inputs[0])
    link_sockets(tree, factor.outputs[0], combined.inputs[1])

    # 6. Store as 'Color' (FLOAT_COLOR, CORNER)
    # Convert scalar to color via CombineXYZ then store
    to_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 1800, by))
    link_sockets(tree, combined.outputs[0], sock(to_vec, "X"))
    link_sockets(tree, combined.outputs[0], sock(to_vec, "Y"))
    link_sockets(tree, combined.outputs[0], sock(to_vec, "Z"))

    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 2000, by))
    store.data_type = "FLOAT_COLOR"
    store.domain = "CORNER"
    store.inputs["Name"].default_value = "Color"
    link_sockets(tree, geo, sock(store, "Geometry"))
    link_sockets(tree, sock(to_vec, "Vector", outputs=True), sock(store, "Value"))
    link_sockets(tree, sock(store, "Geometry", outputs=True), sock(gout, "Geometry"))

    return label_tree(tree, group_name, [
        {"title": "Fold Depth", "nodes": ("attribute", "position", "vector math", "switch"), "role": "attribute"},
        {"title": "AO Combine", "nodes": ("clamp", "subtract", "multiply"), "role": "math"},
        {"title": "Store Color", "nodes": ("combine", "store"), "role": "output"},
    ])


register_builder(
    "MEL_garment_vertex_ao",
    build_garment_vertex_ao,
    "Garment Vertex AO",
    "Bakes fold AO into vertex colors from tension_fold or rest deviation",
    "Garment",
)
