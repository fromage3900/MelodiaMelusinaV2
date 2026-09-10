"""Garment smart bevel — material-aware edge bevel for garments.

Fabric edges get soft rounded bevels; trim/border edges stay sharp.
Infinity Nikki style: crisp trim lines, soft fabric rolls.
"""

from __future__ import annotations
import bpy

from .core import (
    add_float_param, add_int_param, add_bool_param, label_tree,
    link_sockets, new_geometry_tree, register_builder,
    require_node, safe_node, sock,
)


def _math(tree, op, loc):
    n = safe_node(tree, "ShaderNodeMath", loc)
    n.operation = op
    return n


def build_garment_smart_bevel(group_name="MEL_garment_smart_bevel"):
    """Material-aware bevel: fabric edges rounded, trim edges sharp."""
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Base Width", 0.03, 0.0, 2.0)
    add_int_param(tree, "Segments", 3, 1, 8)
    add_float_param(tree, "Profile", 0.5, 0.0, 1.0)
    add_float_param(tree, "Trim Bevel Factor", 0.3, 0.0, 1.0)
    add_bool_param(tree, "Use Bevel Weight", True)
    add_float_param(tree, "Auto Angle Threshold", 30.0, 5.0, 90.0)

    bx, by = 0, 0

    # 1. Auto bevel_weight from edge angle (when no manual weight)
    edge_angle = safe_node(tree, "GeometryNodeInputMeshEdgeAngle", (bx - 500, by + 120))
    thresh_rad = _math(tree, "MULTIPLY", (bx - 350, by + 120))
    link_sockets(tree, sock(gin, "Auto Angle Threshold", outputs=True), thresh_rad.inputs[0])
    thresh_rad.inputs[1].default_value = 0.01745329252  # deg->rad
    cmp = safe_node(tree, "FunctionNodeCompare", (bx - 200, by + 80))
    auto_weight = None
    if edge_angle and thresh_rad and cmp:
        cmp.data_type = "FLOAT"
        cmp.operation = "GREATER_THAN"
        link_sockets(tree, sock(edge_angle, "Unsigned Angle", outputs=True), sock(cmp, "A"))
        link_sockets(tree, thresh_rad.outputs[0], sock(cmp, "B"))
        auto_store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx - 50, by + 80))
        if auto_store:
            auto_store.data_type = "FLOAT"
            auto_store.domain = "EDGE"
            auto_store.inputs["Name"].default_value = "bevel_weight_auto"
            link_sockets(tree, sock(gin, "Geometry", outputs=True), sock(auto_store, "Geometry"))
            link_sockets(tree, sock(cmp, "Result", outputs=True), sock(auto_store, "Value"))
            auto_weight = sock(auto_store, "Geometry", outputs=True)

    # 2. Read material_id (INT, FACE domain)
    mat_attr = safe_node(tree, "GeometryNodeInputNamedAttribute", (bx - 500, by - 50))
    mat_attr.data_type = "INT"
    mat_attr.inputs["Name"].default_value = "material_id"
    mat_val = sock(mat_attr, "Attribute", outputs=True)

    # 3. Convert material_id to bevel factor:
    #    id=1 (fabric) -> 1.0 (full bevel)
    #    id>=2 (trim)  -> Trim Bevel Factor (reduced bevel)
    # For edges, we need to check adjacent face material_id.
    # Simpler: use the material_id from the edge's faces via a trick —
    # use a NamedAttribute on FACE domain, then for edges, Blender
    # automatically interpolates face attributes to edges.
    is_trim = safe_node(tree, "FunctionNodeCompare", (bx - 200, by - 50))
    if is_trim:
        is_trim.data_type = "INT"
        is_trim.operation = "GREATER_EQUAL"
        link_sockets(tree, mat_val, sock(is_trim, "A"))
        sock(is_trim, "B").default_value = 2

    # 4. bevel_weight = auto_weight * material_factor
    #    material_factor = if trim: Trim_Bevel_Factor, else: 1.0
    mat_factor = safe_node(tree, "ShaderNodeMix", (bx + 100, by - 50))
    if mat_factor:
        mat_factor.data_type = "FLOAT"
        link_sockets(tree, sock(is_trim, "Result", outputs=True), sock(mat_factor, "Factor"))
        mat_factor.inputs["A"].default_value = 1.0
        link_sockets(tree, sock(gin, "Trim Bevel Factor", outputs=True), sock(mat_factor, "B"))

    # 5. Read manual bevel_weight (EDGE domain)
    named = safe_node(tree, "GeometryNodeInputNamedAttribute", (bx - 300, by - 150))
    if named:
        named.data_type = "FLOAT"
        named.inputs["Name"].default_value = "bevel_weight"
    named_auto = safe_node(tree, "GeometryNodeInputNamedAttribute", (bx - 300, by - 250))
    if named_auto:
        named_auto.data_type = "FLOAT"
        named_auto.inputs["Name"].default_value = "bevel_weight_auto"

    # 6. Pick weight source: manual > auto > 1.0
    use_manual = safe_node(tree, "ShaderNodeMix", (bx + 50, by - 100))
    if use_manual:
        use_manual.data_type = "FLOAT"
        use_manual.clamp_result = True
        link_sockets(tree, sock(gin, "Use Bevel Weight", outputs=True), sock(use_manual, "Factor"))
        use_manual.inputs["A"].default_value = 1.0
        if named:
            link_sockets(tree, sock(named, "Attribute", outputs=True), sock(use_manual, "B"))

    use_auto = safe_node(tree, "ShaderNodeMix", (bx + 200, by - 180))
    if use_auto and named_auto:
        use_auto.data_type = "FLOAT"
        gt = safe_node(tree, "FunctionNodeCompare", (bx + 100, by - 200))
        if gt:
            gt.data_type = "FLOAT"
            gt.operation = "GREATER_THAN"
            if use_manual:
                link_sockets(tree, use_manual.outputs[0], sock(gt, "A"))
            sock(gt, "B").default_value = 0.01
            link_sockets(tree, sock(gt, "Result", outputs=True), sock(use_auto, "Factor"))
            use_auto.inputs["A"].default_value = 0.0
            link_sockets(tree, sock(named_auto, "Attribute", outputs=True), sock(use_auto, "B"))
            weight_src = use_auto.outputs[0]
        else:
            weight_src = use_manual.outputs[0] if use_manual else None
    else:
        weight_src = use_manual.outputs[0] if use_manual else None

    # 7. Apply material factor to weight
    weighted = _math(tree, "MULTIPLY", (bx + 400, by))
    if weight_src:
        link_sockets(tree, weight_src, weighted.inputs[0])
    link_sockets(tree, mat_factor.outputs[0] if mat_factor else sock(gin, "Trim Bevel Factor", outputs=True), weighted.inputs[1])

    # 8. Final width = Base Weight * weighted
    final_width = _math(tree, "MULTIPLY", (bx + 600, by))
    link_sockets(tree, sock(gin, "Base Width", outputs=True), final_width.inputs[0])
    link_sockets(tree, weighted.outputs[0], final_width.inputs[1])

    # 9. Bevel
    bevel = require_node(tree, "GeometryNodeMeshBevel", (bx + 800, by), "GeometryNodeBevelMesh")
    bevel_input = auto_weight if auto_weight is not None else sock(gin, "Geometry", outputs=True)
    link_sockets(tree, bevel_input, sock(bevel, "Mesh", "Geometry"))
    link_sockets(tree, final_width.outputs[0], sock(bevel, "Offset", "Width"))
    link_sockets(tree, sock(gin, "Segments", outputs=True), sock(bevel, "Segments"))
    link_sockets(tree, sock(gin, "Profile", outputs=True), sock(bevel, "Shape"))
    link_sockets(tree, sock(bevel, "Mesh", "Geometry", outputs=True), sock(gout, "Geometry"))

    return label_tree(tree, group_name, [
        {"title": "Auto Weight (edge angle)", "nodes": ("edge", "compare", "auto"), "role": "attribute"},
        {"title": "Material Factor", "nodes": ("named attribute", "compare", "mix"), "role": "material"},
        {"title": "Weighted Bevel", "nodes": ("bevel",), "role": "geometry"},
    ])


register_builder(
    "MEL_garment_smart_bevel",
    build_garment_smart_bevel,
    "Garment Smart Bevel",
    "Material-aware bevel: fabric edges rounded, trim edges sharp",
    "Garment",
)
