"""Melodia Wardrobe -- trim-sheet UV unwrapping GN builder.

Builds a trim-sheet UV projection for garments (Infinity Nikki style):
cylindrical projection for fabric regions (material_id < 2), planar
projection for trim borders (material_id >= 2), with consistent texel
density normalization. Stored as a named FLOAT2 attribute 'uv_garment'
on the FACE domain.

Builder (registered in the Melodia GN catalog):
  MEL_garment_trim_uv -- trim-sheet UV: cylindrical for fabric, planar for trim
"""
from __future__ import annotations
import math

from .core import (
    safe_node, link_sockets, color_node, label_tree,
    new_geometry_tree, sock,
    add_float_param, add_int_param, add_bool_param, register_builder,
)


def build_garment_trim_uv(group_name="MEL_garment_trim_uv"):
    """Trim-sheet UV: cylindrical for fabric, planar for trim, texel-normalized."""
    tree, gin, gout = new_geometry_tree(group_name)
    geo = gin.outputs["Geometry"]

    # --- parameters ---
    texel = add_float_param(tree, "Texel Density", 10.0, 0.0, 1000.0)
    pblend = add_float_param(tree, "Planar Blend", 1.0, 0.0, 1.0)
    seam = add_float_param(tree, "Seam Angle", 0.0, -math.pi, math.pi)

    # --- position + bounding box ---
    pos = safe_node(tree, "GeometryNodeInputPosition", (0, 0))
    bbox = safe_node(tree, "GeometryNodeBoundBox", (-300, -160))

    bbox_min_sock = sock(bbox, "Min", outputs=True)

    # separate bbox_min components (for normalization)
    min_sep = safe_node(tree, "ShaderNodeSeparateXYZ", (-120, -200))
    link_sockets(tree, bbox_min_sock, min_sep.inputs["Vector"])

    # separate position XYZ
    pos_sep = safe_node(tree, "ShaderNodeSeparateXYZ", (-180, 0))
    link_sockets(tree, pos.outputs["Position"], pos_sep.inputs["Vector"])

    # ============================
    # Cylindrical UV (all faces)
    # U = (atan2(x,z) + seam) / (2*pi) + 0.5
    # V = y - min_y (world meters)
    # ============================

    # atan2(x, z): inputs[0]=Y(=x), inputs[1]=X(=z) in Blender 5.2
    atan = safe_node(tree, "ShaderNodeMath", (180, -60))
    atan.operation = "ARCTAN2"
    link_sockets(tree, pos_sep.outputs["X"], atan.inputs[0])
    link_sockets(tree, pos_sep.outputs["Z"], atan.inputs[1])

    # add seam angle
    seam_add = safe_node(tree, "ShaderNodeMath", (360, -60))
    seam_add.operation = "ADD"
    link_sockets(tree, atan.outputs[0], seam_add.inputs[0])
    link_sockets(tree, gin.outputs.get("Seam Angle") or seam, seam_add.inputs[1])

    # U_cyl = seam_result / (2*pi) + 0.5
    u_cyl_scale = safe_node(tree, "ShaderNodeMath", (540, -60))
    u_cyl_scale.operation = "MULTIPLY"
    u_cyl_scale.inputs[1].default_value = 1.0 / (2.0 * math.pi)
    link_sockets(tree, seam_add.outputs[0], u_cyl_scale.inputs[0])

    u_cyl = safe_node(tree, "ShaderNodeMath", (720, -60))
    u_cyl.operation = "ADD"
    u_cyl.inputs[1].default_value = 0.5
    link_sockets(tree, u_cyl_scale.outputs[0], u_cyl.inputs[0])

    # V_cyl = y - min_y (meters)
    v_cyl = safe_node(tree, "ShaderNodeMath", (180, -220))
    v_cyl.operation = "SUBTRACT"
    link_sockets(tree, pos_sep.outputs["Y"], v_cyl.inputs[0])
    link_sockets(tree, min_sep.outputs["Y"], v_cyl.inputs[1])

    # clamp U_cyl to [0,1]
    u_cyl_clamp = safe_node(tree, "ShaderNodeClamp", (900, -60))
    u_cyl_clamp.inputs["Min"].default_value = 0.0
    u_cyl_clamp.inputs["Max"].default_value = 1.0
    link_sockets(tree, u_cyl.outputs[0], u_cyl_clamp.inputs["Value"])

    # combine cylindrical UV
    cyl_comb = safe_node(tree, "ShaderNodeCombineXYZ", (1080, -60))
    link_sockets(tree, u_cyl_clamp.outputs[0], cyl_comb.inputs["X"])
    link_sockets(tree, v_cyl.outputs[0], cyl_comb.inputs["Y"])

    # ============================
    # Planar UV (trim faces): X -> U, Z -> V
    # U = x - min_x (meters)
    # V = z - min_z (meters)
    # ============================

    u_plan = safe_node(tree, "ShaderNodeMath", (180, -420))
    u_plan.operation = "SUBTRACT"
    link_sockets(tree, pos_sep.outputs["X"], u_plan.inputs[0])
    link_sockets(tree, min_sep.outputs["X"], u_plan.inputs[1])

    v_plan = safe_node(tree, "ShaderNodeMath", (180, -580))
    v_plan.operation = "SUBTRACT"
    link_sockets(tree, pos_sep.outputs["Z"], v_plan.inputs[0])
    link_sockets(tree, min_sep.outputs["Z"], v_plan.inputs[1])

    # combine planar UV
    plan_comb = safe_node(tree, "ShaderNodeCombineXYZ", (360, -420))
    link_sockets(tree, u_plan.outputs[0], plan_comb.inputs["X"])
    link_sockets(tree, v_plan.outputs[0], plan_comb.inputs["Y"])

    # ============================
    # material_id attribute (INT, FACE domain)
    # ============================
    mat_attr = safe_node(tree, "GeometryNodeInputNamedAttribute", (-300, -460))
    try:
        mat_attr.inputs["Name"].default_value = "material_id"
    except Exception:
        try:
            mat_attr.inputs["Attribute"].default_value = "material_id"
        except Exception:
            pass
    try:
        mat_attr.data_type = "INT"
    except Exception:
        pass

    # factor = material_id >= 2
    compare = safe_node(tree, "FunctionNodeCompare", (-80, -480))
    try:
        compare.operation = "GREATER_EQUAL"
        compare.data_type = "INT"
    except Exception:
        pass
    link_sockets(tree, sock(mat_attr, "Attribute", "Value", outputs=True), compare.inputs["A"])
    compare.inputs["B"].default_value = 2

    # blend factor = compare_result * Planar Blend
    factor_mul = safe_node(tree, "ShaderNodeMath", (100, -480))
    factor_mul.operation = "MULTIPLY"
    link_sockets(tree, compare.outputs["Result"], factor_mul.inputs[0])
    link_sockets(tree, gin.outputs.get("Planar Blend") or pblend, factor_mul.inputs[1])

    # ============================
    # Blend cylindrical <-> planar via ShaderNodeMix (FLOAT2)
    # ============================
    mix = safe_node(tree, "ShaderNodeMix", (1260, -260))
    try:
        mix.data_type = "FLOAT2"
    except Exception:
        pass
    link_sockets(tree, cyl_comb.outputs["Vector"], mix.inputs["A"])
    link_sockets(tree, plan_comb.outputs["Vector"], mix.inputs["B"])
    link_sockets(tree, factor_mul.outputs[0], mix.inputs["Factor"])

    # ============================
    # Texel density: scale UV by texel_density
    # ============================
    texel_scale = safe_node(tree, "ShaderNodeVectorMath", (1440, -260))
    texel_scale.operation = "SCALE"
    link_sockets(tree, mix.outputs["Result"], texel_scale.inputs["Vector"])
    link_sockets(tree, gin.outputs.get("Texel Density") or texel, texel_scale.inputs["Scale"])

    # ============================
    # Store as named attribute (FACE domain, uv_garment, FLOAT2)
    # ============================
    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (1620, -260))
    try:
        store.data_type = "FLOAT2"
    except Exception:
        pass
    try:
        store.domain = "FACE"
    except Exception:
        pass
    link_sockets(tree, geo, store.inputs["Geometry"])
    try:
        store.inputs["Name"].default_value = "uv_garment"
    except Exception:
        try:
            store.inputs["Attribute"].default_value = "uv_garment"
        except Exception:
            pass
    link_sockets(tree, texel_scale.outputs["Vector"], store.inputs["Value"] if "Value" in store.inputs else store.inputs[2])

    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Position + BBox", "nodes": ("position", "bounding", "separate",), "role": "attribute"},
        {"title": "Cylindrical UV", "nodes": ("arctan", "scale", "clamp", "combine",), "role": "geometry"},
        {"title": "Planar UV (Trim)", "nodes": ("subtract", "planar",), "role": "geometry"},
        {"title": "Material Blend", "nodes": ("named attribute", "compare", "mix",), "role": "math"},
        {"title": "Texel Density + Output", "nodes": ("scale", "store",), "role": "output"},
    ])


# --------------------------------------------------------------------------- #
# register builder
# --------------------------------------------------------------------------- #
try:
    register_builder(
        "MEL_garment_trim_uv",
        build_garment_trim_uv,
        "Garment Trim UV",
        "Trim-sheet UV: cylindrical for fabric, planar for trim, texel-normalized",
        "Garment",
    )
except Exception:
    pass
