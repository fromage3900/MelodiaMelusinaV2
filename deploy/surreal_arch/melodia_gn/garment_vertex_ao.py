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
    """Bake garment fold AO into vertex colors."""
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "AO Strength", 1.0, 0.0, 5.0)
    add_float_param(tree, "Curvature AO", 0.5, 0.0, 2.0)
    add_float_param(tree, "Base Color", 1.0, 0.0, 1.0)
    add_int_param(tree, "Blend Mode", 0, 0, 2)

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

    # 5. Curvature: dot(vertex_normal, blurred_normal)
    normal_node = safe_node(tree, "GeometryNodeInputNormal", (bx, by - 400))
    normal = sock(normal_node, "Normal", outputs=True)

    blur_normal = safe_node(tree, "GeometryNodeBlurAttribute", (bx + 200, by - 400))
    blur_normal.data_type = "FLOAT_VECTOR"
    link_sockets(tree, normal, sock(blur_normal, "Value"))
    sock(blur_normal, "Iterations").default_value = 3
    blurred = sock(blur_normal, "Value", outputs=True)

    dot_n = safe_node(tree, "ShaderNodeVectorMath", (bx + 400, by - 400))
    dot_n.operation = "DOT_PRODUCT"
    link_sockets(tree, normal, sock(dot_n, "Vector"))
    link_sockets(tree, blurred, sock(dot_n, "Vector 1"))

    curvature = _math(tree, "SUBTRACT", (bx + 600, by - 400))
    curvature.inputs[0].default_value = 1.0
    link_sockets(tree, sock(dot_n, "Value", outputs=True), curvature.inputs[1])

    curv_scaled = _math(tree, "MULTIPLY", (bx + 800, by - 400))
    link_sockets(tree, curvature.outputs[0], curv_scaled.inputs[0])
    link_sockets(tree, sock(gin, "Curvature AO", outputs=True), curv_scaled.inputs[1])

    # 6. Combine: final = base * (1 - fold_ao*0.5) * (1 - curv_ao*0.3)
    fold_dark = _math(tree, "MULTIPLY", (bx + 1000, by))
    link_sockets(tree, ao_clamp.outputs[0], fold_dark.inputs[0])
    fold_dark.inputs[1].default_value = 0.5
    fold_factor = _math(tree, "SUBTRACT", (bx + 1200, by))
    fold_factor.inputs[0].default_value = 1.0
    link_sockets(tree, fold_dark.outputs[0], fold_factor.inputs[1])

    curv_dark = _math(tree, "MULTIPLY", (bx + 1000, by - 200))
    link_sockets(tree, curv_scaled.outputs[0], curv_dark.inputs[0])
    curv_dark.inputs[1].default_value = 0.3
    curv_factor = _math(tree, "SUBTRACT", (bx + 1200, by - 200))
    curv_factor.inputs[0].default_value = 1.0
    link_sockets(tree, curv_dark.outputs[0], curv_factor.inputs[1])

    combined = _math(tree, "MULTIPLY", (bx + 1400, by - 100))
    link_sockets(tree, sock(gin, "Base Color", outputs=True), combined.inputs[0])
    link_sockets(tree, fold_factor.outputs[0], combined.inputs[1])
    combined2 = _math(tree, "MULTIPLY", (bx + 1600, by - 100))
    link_sockets(tree, combined.outputs[0], combined2.inputs[0])
    link_sockets(tree, curv_factor.outputs[0], combined2.inputs[1])

    final_clamp = safe_node(tree, "ShaderNodeClamp", (bx + 1800, by - 100))
    sock(final_clamp, "Min").default_value = 0.0
    sock(final_clamp, "Max").default_value = 1.0
    link_sockets(tree, combined2.outputs[0], sock(final_clamp, "Value"))

    # 7. Read existing Color (FLOAT_COLOR, CORNER) for blending
    existing_attr = safe_node(tree, "GeometryNodeInputNamedAttribute", (bx + 1800, by - 300))
    existing_attr.data_type = "RGBA"

    # Convert scalar AO to grayscale FLOAT_COLOR
    to_color = safe_node(tree, "FunctionNodeCombineColor", (bx + 2000, by - 100))
    link_sockets(tree, final_clamp.outputs[0], sock(to_color, "Red"))
    link_sockets(tree, final_clamp.outputs[0], sock(to_color, "Green"))
    link_sockets(tree, final_clamp.outputs[0], sock(to_color, "Blue"))
    new_color = sock(to_color, "Color", outputs=True)

    # 8. Blend: Multiply = existing * new
    mul_scale = safe_node(tree, "ShaderNodeVectorMath", (bx + 2200, by))
    mul_scale.operation = "SCALE"
    link_sockets(tree, existing_val, sock(mul_scale, "Vector"))
    link_sockets(tree, final_clamp.outputs[0], sock(mul_scale, "Scale"))
    mul_result = sock(mul_scale, "Vector", outputs=True)

    # 9. Blend: Add = existing + new
    add_scalar = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 2200, by - 200))
    link_sockets(tree, final_clamp.outputs[0], sock(add_scalar, "X"))
    link_sockets(tree, final_clamp.outputs[0], sock(add_scalar, "Y"))
    link_sockets(tree, final_clamp.outputs[0], sock(add_scalar, "Z"))
    add_vec = safe_node(tree, "ShaderNodeVectorMath", (bx + 2400, by - 150))
    add_vec.operation = "ADD"
    link_sockets(tree, existing_val, sock(add_vec, "Vector"))
    link_sockets(tree, sock(add_scalar, "Vector", outputs=True), sock(add_vec, "Vector 1"))
    add_result = sock(add_vec, "Vector", outputs=True)

    # 10. Select blend by int: 0=Multiply, 1=Add, 2=Override
    blend_sw1 = safe_node(tree, "GeometryNodeSwitch", (bx + 2600, by))
    blend_sw1.input_type = "FLOAT_COLOR"
    cmp_mul = safe_node(tree, "FunctionNodeCompare", (bx + 2400, by + 100))
    cmp_mul.data_type = "INT"
    cmp_mul.operation = "EQUAL"
    link_sockets(tree, sock(gin, "Blend Mode", outputs=True), sock(cmp_mul, "A"))
    sock(cmp_mul, "B").default_value = 0
    link_sockets(tree, sock(cmp_mul, "Result", outputs=True), sock(blend_sw1, "Switch"))
    link_sockets(tree, add_result, sock(blend_sw1, "False"))
    link_sockets(tree, mul_result, sock(blend_sw1, "True"))

    blend_sw2 = safe_node(tree, "GeometryNodeSwitch", (bx + 2600, by - 150))
    blend_sw2.input_type = "FLOAT_COLOR"
    cmp_add = safe_node(tree, "FunctionNodeCompare", (bx + 2400, by - 250))
    cmp_add.data_type = "INT"
    cmp_add.operation = "EQUAL"
    link_sockets(tree, sock(gin, "Blend Mode", outputs=True), sock(cmp_add, "A"))
    sock(cmp_add, "B").default_value = 1
    link_sockets(tree, sock(cmp_add, "Result", outputs=True), sock(blend_sw2, "Switch"))
    link_sockets(tree, new_color, sock(blend_sw2, "False"))
    link_sockets(tree, sock(blend_sw1, "Output", outputs=True), sock(blend_sw2, "True"))

    # 11. If no existing color, use new_color
    final_sw = safe_node(tree, "GeometryNodeSwitch", (bx + 2800, by - 100))
    final_sw.input_type = "FLOAT_COLOR"
    link_sockets(tree, existing_exists, sock(final_sw, "Switch"))
    link_sockets(tree, new_color, sock(final_sw, "False"))
    link_sockets(tree, sock(blend_sw2, "Output", outputs=True), sock(final_sw, "True"))
    final_color = sock(final_sw, "Output", outputs=True)

    # 12. Store as 'Color' (RGBA, CORNER)
    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 3000, by - 100))
    store.data_type = "RGBA"
    store.domain = "CORNER"
    store.inputs["Name"].default_value = "Color"
    link_sockets(tree, geo, sock(store, "Geometry"))
    link_sockets(tree, final_color, sock(store, "Value"))
    link_sockets(tree, sock(store, "Geometry", outputs=True), sock(gout, "Geometry"))

    return label_tree(tree, group_name, [
        {"title": "Fold Depth", "nodes": ("attribute", "position", "vector math", "switch"), "role": "attribute"},
        {"title": "Curvature", "nodes": ("blur", "dot", "normal", "subtract"), "role": "attribute"},
        {"title": "AO Combine", "nodes": ("clamp", "subtract", "multiply"), "role": "math"},
        {"title": "Color Blend", "nodes": ("combine", "compare", "switch", "store"), "role": "output"},
    ])


register_builder(
    "MEL_garment_vertex_ao",
    build_garment_vertex_ao,
    "Garment Vertex AO",
    "Bakes fold AO into vertex colors from tension_fold or rest deviation",
    "Garment",
)
