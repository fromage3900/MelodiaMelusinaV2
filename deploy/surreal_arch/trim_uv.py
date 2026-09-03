"""Trimsheet-oriented procedural UV inside Geometry Nodes."""

from __future__ import annotations

from .trim_color_bake import TRIM_ZONE_ATTR


def add_trim_sheet_uv_pass(monolith, tree, in_geom, props, x=14700):
    """
    BOX footprint UV scaled for modular trim sheets + atlas slots for trim-zone faces.
    Trim zones (surreal_trim_zone > 0) map to a grid in the 0-1 UV square; body uses center tile.
    """
    uv_name = getattr(props, "uv_map_name", "UVMap") or "UVMap"
    cols = max(2, min(8, int(getattr(props, "trim_sheet_atlas_cols", 4))))
    tile = 1.0 / float(cols)
    body_scale = max(0.05, min(1.0, float(getattr(props, "trim_sheet_body_scale", 0.85))))
    uv_scale = max(0.01, getattr(props, "uv_scale", 1.0))

    bbox = tree.nodes.new("GeometryNodeBoundBox")
    bbox.location = (x, 300)
    monolith.color_node(bbox, "cleanup")
    monolith._link(tree, in_geom, bbox.inputs["Geometry"])

    sep_min = tree.nodes.new("ShaderNodeSeparateXYZ")
    sep_min.location = (x + 200, 200)
    sep_max = tree.nodes.new("ShaderNodeSeparateXYZ")
    sep_max.location = (x + 200, 400)
    monolith._link(tree, bbox.outputs["Min"], sep_min.inputs["Vector"])
    monolith._link(tree, bbox.outputs["Max"], sep_max.inputs["Vector"])

    pos = tree.nodes.new("GeometryNodeInputPosition")
    pos.location = (x, 0)
    sep_p = tree.nodes.new("ShaderNodeSeparateXYZ")
    sep_p.location = (x + 200, 0)
    monolith._link(tree, pos.outputs["Position"], sep_p.inputs["Vector"])

    def _norm_axis(coord_out, min_out, max_out, loc_y):
        sub = tree.nodes.new("ShaderNodeMath")
        sub.location = (x + 400, loc_y)
        sub.operation = "SUBTRACT"
        monolith._link(tree, coord_out, sub.inputs[0])
        monolith._link(tree, min_out, sub.inputs[1])
        rng = tree.nodes.new("ShaderNodeMath")
        rng.location = (x + 580, loc_y)
        rng.operation = "SUBTRACT"
        monolith._link(tree, max_out, rng.inputs[0])
        monolith._link(tree, min_out, rng.inputs[1])
        div = tree.nodes.new("ShaderNodeMath")
        div.location = (x + 760, loc_y)
        div.operation = "DIVIDE"
        div.inputs[1].default_value = 1.0
        monolith._link(tree, sub.outputs[0], div.inputs[0])
        monolith._link(tree, rng.outputs[0], div.inputs[1])
        return div.outputs[0]

    nu = _norm_axis(sep_p.outputs["X"], sep_min.outputs["X"], sep_max.outputs["X"], 80)
    nv = _norm_axis(sep_p.outputs["Z"], sep_min.outputs["Z"], sep_max.outputs["Z"], -80)

    center = tree.nodes.new("ShaderNodeMath")
    center.location = (x + 940, 40)
    center.operation = "MULTIPLY"
    center.inputs[1].default_value = body_scale
    monolith._link(tree, nu, center.inputs[0])
    off_u = tree.nodes.new("ShaderNodeMath")
    off_u.location = (x + 1120, 40)
    off_u.operation = "ADD"
    off_u.inputs[1].default_value = (1.0 - body_scale) * 0.5
    monolith._link(tree, center.outputs[0], off_u.inputs[0])

    center_v = tree.nodes.new("ShaderNodeMath")
    center_v.location = (x + 940, -60)
    center_v.operation = "MULTIPLY"
    center_v.inputs[1].default_value = body_scale
    monolith._link(tree, nv, center_v.inputs[0])
    off_v = tree.nodes.new("ShaderNodeMath")
    off_v.location = (x + 1120, -60)
    off_v.operation = "ADD"
    off_v.inputs[1].default_value = (1.0 - body_scale) * 0.5
    monolith._link(tree, center_v.outputs[0], off_v.inputs[0])

    u_body, v_body = off_u.outputs[0], off_v.outputs[0]

    if abs(uv_scale - 1.0) > 0.001:
        us = tree.nodes.new("ShaderNodeMath")
        us.location = (x + 1280, 40)
        us.operation = "MULTIPLY"
        us.inputs[1].default_value = uv_scale
        monolith._link(tree, u_body, us.inputs[0])
        vs = tree.nodes.new("ShaderNodeMath")
        vs.location = (x + 1280, -60)
        vs.operation = "MULTIPLY"
        vs.inputs[1].default_value = uv_scale
        monolith._link(tree, v_body, vs.inputs[0])
        u_body, v_body = us.outputs[0], vs.outputs[0]

    zone_attr = tree.nodes.new("GeometryNodeInputNamedAttribute")
    zone_attr.location = (x + 400, -280)
    try:
        zone_attr.data_type = "FLOAT"
    except Exception:
        pass
    zone_attr.inputs["Name"].default_value = TRIM_ZONE_ATTR

    zone_idx = tree.nodes.new("ShaderNodeMath")
    zone_idx.location = (x + 600, -280)
    zone_idx.operation = "SUBTRACT"
    zone_idx.inputs[1].default_value = 1.0
    monolith._link(tree, zone_attr.outputs["Attribute"], zone_idx.inputs[0])

    col_f = tree.nodes.new("ShaderNodeMath")
    col_f.location = (x + 780, -320)
    col_f.operation = "MODULO"
    col_f.inputs[1].default_value = float(cols)
    monolith._link(tree, zone_idx.outputs[0], col_f.inputs[0])

    row_f = tree.nodes.new("ShaderNodeMath")
    row_f.location = (x + 780, -200)
    row_f.operation = "FLOOR"
    monolith._link(tree, zone_idx.outputs[0], row_f.inputs[0])
    row_div = tree.nodes.new("ShaderNodeMath")
    row_div.location = (x + 960, -200)
    row_div.operation = "DIVIDE"
    row_div.inputs[1].default_value = float(cols)
    monolith._link(tree, row_f.outputs[0], row_div.inputs[0])

    half_tile = tree.nodes.new("ShaderNodeMath")
    half_tile.location = (x + 1140, -260)
    half_tile.operation = "MULTIPLY"
    half_tile.inputs[0].default_value = tile
    half_tile.inputs[1].default_value = 0.5

    slot_u = tree.nodes.new("ShaderNodeMath")
    slot_u.location = (x + 1140, -320)
    slot_u.operation = "MULTIPLY"
    slot_u.inputs[1].default_value = tile
    monolith._link(tree, col_f.outputs[0], slot_u.inputs[0])

    slot_v = tree.nodes.new("ShaderNodeMath")
    slot_v.location = (x + 1140, -200)
    slot_v.operation = "MULTIPLY"
    slot_v.inputs[1].default_value = tile
    monolith._link(tree, row_div.outputs[0], slot_v.inputs[0])

    trim_u = tree.nodes.new("ShaderNodeMath")
    trim_u.location = (x + 1320, -320)
    trim_u.operation = "ADD"
    monolith._link(tree, slot_u.outputs[0], trim_u.inputs[0])
    monolith._link(tree, half_tile.outputs[0], trim_u.inputs[1])

    trim_v = tree.nodes.new("ShaderNodeMath")
    trim_v.location = (x + 1320, -200)
    trim_v.operation = "ADD"
    monolith._link(tree, slot_v.outputs[0], trim_v.inputs[0])
    monolith._link(tree, half_tile.outputs[0], trim_v.inputs[1])

    is_trim = tree.nodes.new("ShaderNodeMath")
    is_trim.location = (x + 600, -120)
    is_trim.operation = "GREATER_THAN"
    is_trim.inputs[1].default_value = 0.5
    monolith._link(tree, zone_attr.outputs["Attribute"], is_trim.inputs[0])

    mix_u = tree.nodes.new("ShaderNodeMix")
    mix_u.location = (x + 1500, 20)
    mix_u.data_type = "FLOAT"
    monolith._link(tree, is_trim.outputs[0], mix_u.inputs["Factor"])
    monolith._link(tree, u_body, mix_u.inputs.get("A", mix_u.inputs[6]))
    monolith._link(tree, trim_u.outputs[0], mix_u.inputs.get("B", mix_u.inputs[7]))

    mix_v = tree.nodes.new("ShaderNodeMix")
    mix_v.location = (x + 1500, -120)
    mix_v.data_type = "FLOAT"
    monolith._link(tree, is_trim.outputs[0], mix_v.inputs["Factor"])
    monolith._link(tree, v_body, mix_v.inputs.get("A", mix_v.inputs[6]))
    monolith._link(tree, trim_v.outputs[0], mix_v.inputs.get("B", mix_v.inputs[7]))

    u_out = mix_u.outputs.get("Result", mix_u.outputs[2])
    v_out = mix_v.outputs.get("Result", mix_v.outputs[2])

    uv_vec = tree.nodes.new("ShaderNodeCombineXYZ")
    uv_vec.location = (x + 1680, 0)
    monolith._link(tree, u_out, uv_vec.inputs["X"])
    monolith._link(tree, v_out, uv_vec.inputs["Y"])
    uv_vec.inputs["Z"].default_value = 0.0

    store = tree.nodes.new("GeometryNodeStoreNamedAttribute")
    store.location = (x + 1860, 0)
    monolith.color_node(store, "cleanup")
    store.domain = "CORNER"
    try:
        store.data_type = "FLOAT_VECTOR"
    except Exception:
        try:
            store.data_type = "FLOAT2"
        except Exception:
            pass
    store.inputs["Name"].default_value = uv_name
    monolith._link(tree, in_geom, store.inputs["Geometry"])
    monolith._link(tree, uv_vec.outputs["Vector"], store.inputs["Value"])
    return store.outputs["Geometry"]
