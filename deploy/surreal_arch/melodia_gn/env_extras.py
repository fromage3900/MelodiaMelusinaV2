"""Environment & set-dressing GN group builders — ponds, paths, buoys, stalls, fires.

Ten new pieces for the water/environment lane. Water pieces (lily pond, buoy
line, waterfall pool) reuse the set_dressing water contract: they store
water_level / current_speed / ripple_carve FLOAT attributes on the output so
PCG and material lanes can read them. Dry pieces store their own FLOAT / INT /
BOOLEAN themed attributes.
"""

from __future__ import annotations

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    add_mesh_torus_linked, register_builder,
)


def _math(tree, operation, loc, a=None, b=None):
    """Local shorthand for ShaderNodeMath (keeps graphs legible)."""
    n = safe_node(tree, "ShaderNodeMath", loc)
    try:
        n.operation = operation
    except Exception:
        pass
    if a is not None:
        if isinstance(a, (int, float)):
            n.inputs[0].default_value = a
        else:
            link_sockets(tree, a, n.inputs[0])
    if b is not None:
        if isinstance(b, (int, float)):
            n.inputs[1].default_value = b
        else:
            link_sockets(tree, b, n.inputs[1])
    return n


def _combine(tree, loc, x=None, y=None, z=None):
    """Local shorthand for CombineXYZ with socket-or-scalar components."""
    n = safe_node(tree, "ShaderNodeCombineXYZ", loc)
    for comp, val in (("X", x), ("Y", y), ("Z", z)):
        if val is None:
            continue
        if isinstance(val, (int, float)):
            try:
                n.inputs[comp].default_value = val
            except Exception:
                pass
        else:
            link_sockets(tree, val, n.inputs[comp])
    return n


def _place(tree, loc, geometry_sock, x=None, y=None, z=None):
    """Translate a piece to its final spot (primitives are origin-centered)."""
    t = safe_node(tree, "GeometryNodeTransform", loc)
    link_sockets(tree, geometry_sock, t.inputs["Geometry"])
    if x is not None or y is not None or z is not None:
        pos = _combine(tree, (loc[0] - 200, loc[1] - 140), x, y, z)
        link_sockets(tree, pos.outputs["Vector"], t.inputs["Translation"])
    return t.outputs["Geometry"]


def _instance(tree, loc, points_sock, instance_sock):
    """Instance `instance` on `points` and realize (keeps graphs compact)."""
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", loc)
    link_sockets(tree, points_sock, inst.inputs["Points"])
    link_sockets(tree, instance_sock, inst.inputs["Instance"])
    real = safe_node(tree, "GeometryNodeRealizeInstances", (loc[0] + 240, loc[1]))
    link_sockets(tree, inst.outputs["Instances"], real.inputs["Geometry"])
    return real.outputs["Geometry"]


def _water_disc(tree, loc, radius_sock, depth_sock, z_sock):
    """Flattened water cylinder disc whose center sits at z_sock."""
    w = safe_node(tree, "GeometryNodeMeshCylinder", loc)
    link_sockets(tree, radius_sock, w.inputs["Radius"])
    if depth_sock is not None:
        link_sockets(tree, depth_sock, w.inputs["Depth"])
    else:
        w.inputs["Depth"].default_value = 0.08
    w.inputs["Vertices"].default_value = 24
    w.fill_type = "NGON"
    return _place(tree, (loc[0] + 200, loc[1]), w.outputs["Mesh"], z=z_sock)


def _water_attrs(tree, gin, gout, geom):
    """Store the water-theme attribute contract (set_dressing convention)."""
    bx = geom.node.location.x + 240
    by = geom.node.location.y
    store_wl = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx, by))
    store_wl.data_type = "FLOAT"
    store_wl.inputs["Name"].default_value = "water_level"
    link_sockets(tree, gin.outputs["Water Level"], store_wl.inputs["Value"])
    link_sockets(tree, geom, store_wl.inputs["Geometry"])
    store_cs = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx, by - 180))
    store_cs.data_type = "FLOAT"
    store_cs.inputs["Name"].default_value = "current_speed"
    link_sockets(tree, gin.outputs["Current Speed"], store_cs.inputs["Value"])
    link_sockets(tree, store_wl.outputs["Geometry"], store_cs.inputs["Geometry"])
    store_rc = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx, by - 360))
    store_rc.data_type = "FLOAT"
    store_rc.inputs["Name"].default_value = "ripple_carve"
    link_sockets(tree, gin.outputs["Ripple Carve"], store_rc.inputs["Value"])
    link_sockets(tree, store_cs.outputs["Geometry"], store_rc.inputs["Geometry"])
    link_sockets(tree, store_rc.outputs["Geometry"], gout.inputs["Geometry"])
    color_node(store_wl, "attribute")
    color_node(store_cs, "attribute")
    color_node(store_rc, "attribute")


def build_env_lily_pond(group_name="MEL_env_lily_pond"):
    """Lily pond — basin, water disc, floating lily pads, lotus blooms.

    Water contract attributes: water_level, current_speed, ripple_carve.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_float_param(tree, "Pond Radius", 2.0, 0.5, 12.0)
    add_float_param(tree, "Panel Depth", 0.3, 0.05, 1.0)
    add_float_param(tree, "Water Level", 0.15, 0.0, 0.6)
    add_int_param(tree, "Pad Count", 8, 0, 48)
    add_float_param(tree, "Pad Size", 0.35, 0.1, 1.2)
    add_int_param(tree, "Lotus Count", 3, 0, 16)
    add_float_param(tree, "Current Speed", 0.5, 0.01, 10.0)
    add_float_param(tree, "Ripple Carve", 0.5, 0.0, 2.0)

    basin = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 500, by + 500))
    link_sockets(tree, gin.outputs["Pond Radius"], basin.inputs["Radius"])
    link_sockets(tree, gin.outputs["Panel Depth"], basin.inputs["Depth"])
    basin.inputs["Vertices"].default_value = 32
    basin.fill_type = "NGON"

    water_z = _math(tree, "MULTIPLY", (bx - 700, by + 260),
                    _math(tree, "SUBTRACT", (bx - 820, by + 260),
                          gin.outputs["Panel Depth"], gin.outputs["Water Level"]).outputs[0], 0.5)
    water_out = _water_disc(tree, (bx - 500, by + 320),
                            _math(tree, "MULTIPLY", (bx - 700, by + 320), gin.outputs["Pond Radius"], 0.92).outputs[0],
                            gin.outputs["Water Level"], water_z.outputs[0])

    pad_ring = safe_node(tree, "GeometryNodeMeshCircle", (bx - 500, by))
    link_sockets(tree, _math(tree, "MULTIPLY", (bx - 700, by), gin.outputs["Pond Radius"], 0.7).outputs[0], pad_ring.inputs["Radius"])
    link_sockets(tree, gin.outputs["Pad Count"], pad_ring.inputs["Vertices"])
    pad_ring.fill_type = "NONE"
    pad = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 500, by - 160))
    link_sockets(tree, gin.outputs["Pad Size"], pad.inputs["Radius"])
    pad.inputs["Depth"].default_value = 0.05
    pad.inputs["Vertices"].default_value = 10
    pad.fill_type = "NGON"
    pad_up = _place(tree, (bx - 300, by - 160), pad.outputs["Mesh"], z=0.02)
    pads = _instance(tree, (bx - 100, by), pad_ring.outputs["Mesh"], pad_up)

    lotus = safe_node(tree, "GeometryNodeMeshCone", (bx - 500, by - 320))
    lotus.inputs["Radius Bottom"].default_value = 0.07
    lotus.inputs["Radius Top"].default_value = 0.0
    lotus.inputs["Depth"].default_value = 0.14
    lotus.inputs["Vertices"].default_value = 8
    lotus_up = _place(tree, (bx - 300, by - 320), lotus.outputs["Mesh"],
                      z=_math(tree, "ADD", (bx - 700, by - 320), gin.outputs["Water Level"], 0.08).outputs[0])
    bloom_ring = safe_node(tree, "GeometryNodeMeshCircle", (bx - 500, by - 480))
    link_sockets(tree, _math(tree, "MULTIPLY", (bx - 700, by - 480), gin.outputs["Pond Radius"], 0.6).outputs[0], bloom_ring.inputs["Radius"])
    link_sockets(tree, gin.outputs["Lotus Count"], bloom_ring.inputs["Vertices"])
    bloom_ring.fill_type = "NONE"
    blooms = _instance(tree, (bx - 100, by - 480), bloom_ring.outputs["Mesh"], lotus_up)

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200, by + 200))
    link_sockets(tree, basin.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, water_out, join.inputs["Geometry"])
    link_sockets(tree, pads, join.inputs["Geometry"])
    link_sockets(tree, blooms, join.inputs["Geometry"])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 400, by + 200))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    _water_attrs(tree, gin, gout, shade.outputs["Geometry"])

    color_node(basin, "geometry")
    color_node(pad_ring, "curve")
    color_node(join, "geometry")
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Pond Basin", "nodes": ("cylinder",), "role": "geometry"},
        {"title": "Water Disc", "nodes": ("water", "transform", "subtract", "multiply"), "role": "math"},
        {"title": "Lily Pads", "nodes": ("circle", "pad", "instance"), "role": "instance"},
        {"title": "Lotus Blooms", "nodes": ("bloom", "cone", "instance"), "role": "instance"},
        {"title": "Water Attributes", "nodes": ("store",), "role": "attribute"},
        {"title": "Output", "nodes": ("join", "shade", "Group Output"), "role": "output"},
    ])


def build_env_stepping_stones(group_name="MEL_env_stepping_stones"):
    """Stepping-stone path — twin meander lines of flattened stones.

    Stores stone_count (INT) and path_width (FLOAT) on the output.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_int_param(tree, "Stone Count", 7, 2, 32)
    add_float_param(tree, "Stone Size", 0.4, 0.15, 1.5)
    add_float_param(tree, "Stone Height", 0.18, 0.05, 0.8)
    add_float_param(tree, "Path Width", 1.2, 0.4, 6.0)
    add_float_param(tree, "Path Length", 6.0, 1.0, 30.0)

    start_x = _math(tree, "MULTIPLY", (bx - 900, by + 300), gin.outputs["Path Length"], -0.5)
    step_x = _math(tree, "DIVIDE", (bx - 900, by + 200), gin.outputs["Path Length"], gin.outputs["Stone Count"])
    w_half = _math(tree, "MULTIPLY", (bx - 900, by + 100), gin.outputs["Path Width"], 0.5)
    w_neg = _math(tree, "MULTIPLY", (bx - 900, by), gin.outputs["Path Width"], -0.5)

    line_a = safe_node(tree, "GeometryNodeMeshLine", (bx - 700, by + 300))
    line_a.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Stone Count"], line_a.inputs["Count"])
    link_sockets(tree, _combine(tree, (bx - 900, by + 420), start_x.outputs[0], w_half.outputs[0], 0.0).outputs["Vector"], line_a.inputs["Start Location"])
    link_sockets(tree, _combine(tree, (bx - 900, by + 340), step_x.outputs[0], w_half.outputs[0], 0.0).outputs["Vector"], line_a.inputs["Offset"])

    line_b = safe_node(tree, "GeometryNodeMeshLine", (bx - 700, by - 100))
    line_b.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Stone Count"], line_b.inputs["Count"])
    link_sockets(tree, _combine(tree, (bx - 900, by + 20), start_x.outputs[0], w_neg.outputs[0], 0.0).outputs["Vector"], line_b.inputs["Start Location"])
    link_sockets(tree, _combine(tree, (bx - 900, by - 60), step_x.outputs[0], w_neg.outputs[0], 0.0).outputs["Vector"], line_b.inputs["Offset"])

    stone = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 500, by + 400))
    link_sockets(tree, gin.outputs["Stone Size"], stone.inputs["Radius"])
    link_sockets(tree, gin.outputs["Stone Height"], stone.inputs["Depth"])
    stone.inputs["Vertices"].default_value = 10
    stone.fill_type = "NGON"
    stone_up = _place(tree, (bx - 300, by + 400), stone.outputs["Mesh"],
                      z=_math(tree, "MULTIPLY", (bx - 700, by + 400), gin.outputs["Stone Height"], 0.5).outputs[0])
    stones_a = _instance(tree, (bx - 300, by + 300), line_a.outputs["Mesh"], stone_up)
    stones_b = _instance(tree, (bx - 300, by - 100), line_b.outputs["Mesh"], stone_up)

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 100, by + 100))
    link_sockets(tree, stones_a, join.inputs["Geometry"])
    link_sockets(tree, stones_b, join.inputs["Geometry"])
    store_n = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 300, by + 160))
    store_n.data_type = "INT"
    store_n.inputs["Name"].default_value = "stone_count"
    link_sockets(tree, gin.outputs["Stone Count"], store_n.inputs["Value"])
    link_sockets(tree, join.outputs["Geometry"], store_n.inputs["Geometry"])
    store_w = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 500, by + 160))
    store_w.data_type = "FLOAT"
    store_w.inputs["Name"].default_value = "path_width"
    link_sockets(tree, gin.outputs["Path Width"], store_w.inputs["Value"])
    link_sockets(tree, store_n.outputs["Geometry"], store_w.inputs["Geometry"])
    link_sockets(tree, store_w.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(line_a, "curve")
    color_node(line_b, "curve")
    color_node(stone, "geometry")
    color_node(store_n, "attribute")
    color_node(store_w, "attribute")
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Path Lines", "nodes": ("line", "divide", "multiply"), "role": "curve"},
        {"title": "Stones", "nodes": ("stone", "transform", "instance"), "role": "instance"},
        {"title": "Path Attributes", "nodes": ("store",), "role": "attribute"},
        {"title": "Output", "nodes": ("join", "Group Output"), "role": "output"},
    ])


def build_env_reeds_patch(group_name="MEL_env_reeds_patch"):
    """Reeds patch — clustered reed stems with height jitter.

    Stores reed_density (FLOAT) on the output for PCG material reads.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_int_param(tree, "Reed Count", 60, 10, 400)
    add_float_param(tree, "Patch Size", 3.0, 0.5, 12.0)
    add_float_param(tree, "Reed Height", 1.2, 0.3, 4.0)
    add_float_param(tree, "Reed Radius", 0.03, 0.01, 0.2)
    add_float_param(tree, "Density", 0.5, 0.01, 2.0)
    add_float_param(tree, "Height Jitter", 0.35, 0.0, 1.0)
    add_float_param(tree, "Clump", 0.4, 0.0, 1.0)

    verts = _math(tree, "CEIL", (bx - 900, by + 200),
                  _math(tree, "SQRT", (bx - 1000, by + 200), gin.outputs["Reed Count"]).outputs[0])
    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 700, by + 200))
    link_sockets(tree, gin.outputs["Patch Size"], grid.inputs["Size X"])
    link_sockets(tree, gin.outputs["Patch Size"], grid.inputs["Size Y"])
    link_sockets(tree, verts.outputs[0], grid.inputs["Vertices X"])
    link_sockets(tree, verts.outputs[0], grid.inputs["Vertices Y"])

    # Clump: mix XY toward a 3x3 cell grid so stems gather instead of a uniform lattice.
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 900, by + 40))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 720, by + 40))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])
    cell = _math(tree, "DIVIDE", (bx - 900, by - 80), gin.outputs["Patch Size"], 3.0)
    qx = _math(tree, "MULTIPLY", (bx - 520, by + 80),
               _math(tree, "FLOOR", (bx - 680, by + 80),
                     _math(tree, "DIVIDE", (bx - 840, by + 80), sep.outputs["X"], cell.outputs[0]).outputs[0]).outputs[0],
               cell.outputs[0])
    qy = _math(tree, "MULTIPLY", (bx - 520, by - 40),
               _math(tree, "FLOOR", (bx - 680, by - 40),
                     _math(tree, "DIVIDE", (bx - 840, by - 40), sep.outputs["Y"], cell.outputs[0]).outputs[0]).outputs[0],
               cell.outputs[0])
    mix_x = _math(tree, "MULTIPLY", (bx - 340, by + 80), qx.outputs[0], gin.outputs["Clump"])
    keep_x = _math(tree, "MULTIPLY", (bx - 340, by + 160), sep.outputs["X"],
                   _math(tree, "SUBTRACT", (bx - 500, by + 200), 1.0, gin.outputs["Clump"]).outputs[0])
    mix_y = _math(tree, "MULTIPLY", (bx - 340, by - 40), qy.outputs[0], gin.outputs["Clump"])
    keep_y = _math(tree, "MULTIPLY", (bx - 340, by - 120), sep.outputs["Y"],
                   _math(tree, "SUBTRACT", (bx - 500, by - 160), 1.0, gin.outputs["Clump"]).outputs[0])
    clump_pos = _combine(
        tree, (bx - 160, by + 40),
        _math(tree, "ADD", (bx - 220, by + 80), keep_x.outputs[0], mix_x.outputs[0]).outputs[0],
        _math(tree, "ADD", (bx - 220, by - 40), keep_y.outputs[0], mix_y.outputs[0]).outputs[0],
        sep.outputs["Z"],
    )
    set_clump = safe_node(tree, "GeometryNodeSetPosition", (bx - 40, by + 200))
    link_sockets(tree, grid.outputs["Mesh"], set_clump.inputs["Geometry"])
    link_sockets(tree, clump_pos.outputs["Vector"], set_clump.inputs["Position"])

    reed = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 500, by - 280))
    link_sockets(tree, gin.outputs["Reed Radius"], reed.inputs["Radius"])
    link_sockets(tree, gin.outputs["Reed Height"], reed.inputs["Depth"])
    reed.inputs["Vertices"].default_value = 6
    reed.fill_type = "NGON"

    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 200, by - 200))
    rand = safe_node(tree, "FunctionNodeRandomValue", (bx, by - 200))
    if rand is None:
        rand = safe_node(tree, "GeometryNodeRandomValue", (bx, by - 200))
    try:
        rand.data_type = "FLOAT"
    except Exception:
        pass
    jitter_lo = _math(tree, "SUBTRACT", (bx - 200, by - 320), 1.0, gin.outputs["Height Jitter"])
    jitter_hi = _math(tree, "ADD", (bx - 200, by - 400), 1.0, gin.outputs["Height Jitter"])
    if rand:
        min_in = rand.inputs.get("Min") or (rand.inputs[0] if len(rand.inputs) else None)
        max_in = rand.inputs.get("Max") or (rand.inputs[1] if len(rand.inputs) > 1 else None)
        id_in = rand.inputs.get("ID") or rand.inputs.get("Id")
        if min_in is not None:
            link_sockets(tree, jitter_lo.outputs[0], min_in)
        if max_in is not None:
            link_sockets(tree, jitter_hi.outputs[0], max_in)
        if id_in is not None:
            link_sockets(tree, idx.outputs["Index"], id_in)
        rand_out = rand.outputs.get("Value") or rand.outputs[0]
    else:
        rand_out = jitter_hi.outputs[0]

    scale = _combine(tree, (bx + 160, by - 200), 1.0, 1.0, rand_out)
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 160, by + 80))
    link_sockets(tree, set_clump.outputs["Geometry"], inst.inputs["Points"])
    link_sockets(tree, reed.outputs["Mesh"], inst.inputs["Instance"])
    if "Scale" in inst.inputs:
        link_sockets(tree, scale.outputs["Vector"], inst.inputs["Scale"])
    real = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 380, by + 80))
    link_sockets(tree, inst.outputs["Instances"], real.inputs["Geometry"])

    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 580, by + 80))
    store.data_type = "FLOAT"
    store.inputs["Name"].default_value = "reed_density"
    link_sockets(tree, gin.outputs["Density"], store.inputs["Value"])
    link_sockets(tree, real.outputs["Geometry"], store.inputs["Geometry"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(grid, "curve")
    color_node(reed, "geometry")
    color_node(inst, "instance")
    color_node(store, "attribute")
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Scatter Grid", "nodes": ("grid", "sqrt", "ceil"), "role": "curve"},
        {"title": "Clump and Jitter", "nodes": ("floor", "random", "set position"), "role": "attribute"},
        {"title": "Reed Stems", "nodes": ("reed", "instance"), "role": "instance"},
        {"title": "Output", "nodes": ("store", "Group Output"), "role": "output"},
    ])


def build_env_buoy_line(group_name="MEL_env_buoy_line"):
    """Buoy line — moored buoy floats with anchor drop lines along a row.

    Water contract attributes: water_level, current_speed, ripple_carve.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_int_param(tree, "Buoy Count", 8, 2, 64)
    add_float_param(tree, "Line Length", 10.0, 1.0, 60.0)
    add_float_param(tree, "Buoy Scale", 0.25, 0.08, 1.0)
    add_float_param(tree, "Anchor Depth", 0.4, 0.1, 2.0)
    add_float_param(tree, "Water Level", 0.5, 0.1, 2.0)
    add_float_param(tree, "Current Speed", 1.0, 0.01, 10.0)
    add_float_param(tree, "Ripple Carve", 0.5, 0.0, 2.0)

    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 700, by + 300))
    line.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Buoy Count"], line.inputs["Count"])
    link_sockets(tree, _combine(tree, (bx - 900, by + 420),
                                _math(tree, "MULTIPLY", (bx - 1000, by + 420), gin.outputs["Line Length"], -0.5).outputs[0],
                                0.0, gin.outputs["Water Level"]).outputs["Vector"], line.inputs["Start Location"])
    link_sockets(tree, _combine(tree, (bx - 900, by + 340),
                                _math(tree, "DIVIDE", (bx - 1000, by + 340), gin.outputs["Line Length"], gin.outputs["Buoy Count"]).outputs[0],
                                0.0, 0.0).outputs["Vector"], line.inputs["Offset"])

    body = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 500, by))
    link_sockets(tree, _math(tree, "MULTIPLY", (bx - 700, by), gin.outputs["Buoy Scale"], 0.34).outputs[0], body.inputs["Radius"])
    link_sockets(tree, _math(tree, "MULTIPLY", (bx - 700, by - 100), gin.outputs["Buoy Scale"], 0.6).outputs[0], body.inputs["Depth"])
    body.inputs["Vertices"].default_value = 12
    body.fill_type = "NGON"

    cap = safe_node(tree, "GeometryNodeMeshCone", (bx - 500, by - 200))
    cap_d = _math(tree, "MULTIPLY", (bx - 700, by - 300), gin.outputs["Buoy Scale"], 0.35)
    link_sockets(tree, _math(tree, "MULTIPLY", (bx - 700, by - 200), gin.outputs["Buoy Scale"], 0.32).outputs[0], cap.inputs["Radius Bottom"])
    cap.inputs["Radius Top"].default_value = 0.0
    link_sockets(tree, cap_d.outputs[0], cap.inputs["Depth"])
    cap.inputs["Vertices"].default_value = 12
    cap_up = _place(tree, (bx - 300, by - 200), cap.outputs["Mesh"], z=cap_d.outputs[0])

    buoy_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 100, by))
    link_sockets(tree, body.outputs["Mesh"], buoy_join.inputs["Geometry"])
    link_sockets(tree, cap_up, buoy_join.inputs["Geometry"])
    buoys = _instance(tree, (bx + 100, by + 300), line.outputs["Mesh"], buoy_join.outputs["Geometry"])

    anchor = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 500, by - 400))
    link_sockets(tree, _math(tree, "MULTIPLY", (bx - 700, by - 400), gin.outputs["Buoy Scale"], 0.08).outputs[0], anchor.inputs["Radius"])
    link_sockets(tree, gin.outputs["Anchor Depth"], anchor.inputs["Depth"])
    anchor.inputs["Vertices"].default_value = 8
    anchor.fill_type = "NGON"
    anchor_up = _place(tree, (bx - 300, by - 400), anchor.outputs["Mesh"],
                       z=_math(tree, "MULTIPLY", (bx - 700, by - 500), gin.outputs["Anchor Depth"], -0.5).outputs[0])
    anchors = _instance(tree, (bx - 100, by - 400), line.outputs["Mesh"], anchor_up)

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 300, by + 200))
    link_sockets(tree, buoys, join.inputs["Geometry"])
    link_sockets(tree, anchors, join.inputs["Geometry"])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 500, by + 200))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    _water_attrs(tree, gin, gout, shade.outputs["Geometry"])

    color_node(line, "curve")
    color_node(body, "geometry")
    color_node(cap, "geometry")
    color_node(join, "geometry")
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Mooring Line", "nodes": ("line", "divide", "multiply"), "role": "curve"},
        {"title": "Buoys", "nodes": ("buoy", "body", "cap", "instance"), "role": "instance"},
        {"title": "Anchors", "nodes": ("anchor", "instance"), "role": "instance"},
        {"title": "Water Attributes", "nodes": ("store",), "role": "attribute"},
        {"title": "Output", "nodes": ("join", "shade", "Group Output"), "role": "output"},
    ])


def build_env_market_stall(group_name="MEL_env_market_stall"):
    """Market stall — corner posts, flat canopy, front counter and awning skirt.

    Stores stall_type (INT) and has_stock (BOOLEAN) on the output.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_float_param(tree, "Stall Width", 2.4, 0.8, 6.0)
    add_float_param(tree, "Stall Depth", 1.6, 0.6, 4.0)
    add_float_param(tree, "Post Height", 2.2, 0.8, 4.0)
    add_float_param(tree, "Awning Drop", 0.6, 0.1, 1.5)
    add_float_param(tree, "Counter Height", 0.9, 0.3, 1.5)
    add_int_param(tree, "Stall Type", 2, 0, 3)
    add_bool_param(tree, "Has Stock", True)

    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 600, by + 200))
    grid.inputs["Vertices X"].default_value = 2
    grid.inputs["Vertices Y"].default_value = 2
    link_sockets(tree, gin.outputs["Stall Width"], grid.inputs["Size X"])
    link_sockets(tree, gin.outputs["Stall Depth"], grid.inputs["Size Y"])

    post = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 600, by))
    post.inputs["Radius"].default_value = 0.05
    link_sockets(tree, gin.outputs["Post Height"], post.inputs["Depth"])
    post.inputs["Vertices"].default_value = 8
    post.fill_type = "NGON"
    post_up = _place(tree, (bx - 400, by), post.outputs["Mesh"],
                     z=_math(tree, "MULTIPLY", (bx - 800, by), gin.outputs["Post Height"], 0.5).outputs[0])
    posts = _instance(tree, (bx - 200, by + 200), grid.outputs["Mesh"], post_up)

    canopy = safe_node(tree, "GeometryNodeMeshCube", (bx - 600, by - 200))
    link_sockets(tree, _combine(tree, (bx - 800, by - 260),
                                _math(tree, "MULTIPLY", (bx - 900, by - 260), gin.outputs["Stall Width"], 1.1).outputs[0],
                                gin.outputs["Stall Depth"], 0.06).outputs["Vector"], canopy.inputs["Size"])
    canopy_out = _place(tree, (bx - 400, by - 200), canopy.outputs["Mesh"],
                        z=_math(tree, "ADD", (bx - 800, by - 320), gin.outputs["Post Height"], 0.03).outputs[0])

    skirt = safe_node(tree, "GeometryNodeMeshCube", (bx - 600, by - 400))
    link_sockets(tree, _combine(tree, (bx - 800, by - 460),
                                _math(tree, "MULTIPLY", (bx - 900, by - 460), gin.outputs["Stall Width"], 1.05).outputs[0],
                                _math(tree, "MULTIPLY", (bx - 900, by - 480), gin.outputs["Stall Depth"], 0.3).outputs[0],
                                gin.outputs["Awning Drop"]).outputs["Vector"], skirt.inputs["Size"])
    skirt_out = _place(tree, (bx - 400, by - 400), skirt.outputs["Mesh"],
                       y=_math(tree, "MULTIPLY", (bx - 800, by - 520), gin.outputs["Stall Depth"], -0.34).outputs[0],
                       z=_math(tree, "SUBTRACT", (bx - 800, by - 560), gin.outputs["Post Height"], 0.5).outputs[0])

    counter = safe_node(tree, "GeometryNodeMeshCube", (bx - 200, by - 300))
    link_sockets(tree, _combine(tree, (bx - 400, by - 360),
                                _math(tree, "MULTIPLY", (bx - 500, by - 360), gin.outputs["Stall Width"], 0.8).outputs[0],
                                _math(tree, "MULTIPLY", (bx - 500, by - 380), gin.outputs["Stall Depth"], 0.4).outputs[0],
                                gin.outputs["Counter Height"]).outputs["Vector"], counter.inputs["Size"])
    counter_out = _place(tree, (bx, by - 300), counter.outputs["Mesh"],
                         y=_math(tree, "MULTIPLY", (bx - 400, by - 420), gin.outputs["Stall Depth"], -0.2).outputs[0],
                         z=_math(tree, "MULTIPLY", (bx - 400, by - 440), gin.outputs["Counter Height"], 0.5).outputs[0])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200, by))
    link_sockets(tree, posts, join.inputs["Geometry"])
    link_sockets(tree, canopy_out, join.inputs["Geometry"])
    link_sockets(tree, skirt_out, join.inputs["Geometry"])
    link_sockets(tree, counter_out, join.inputs["Geometry"])

    store_t = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 400, by + 100))
    store_t.data_type = "INT"
    store_t.inputs["Name"].default_value = "stall_type"
    link_sockets(tree, gin.outputs["Stall Type"], store_t.inputs["Value"])
    link_sockets(tree, join.outputs["Geometry"], store_t.inputs["Geometry"])
    store_s = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 600, by + 100))
    store_s.data_type = "BOOLEAN"
    store_s.inputs["Name"].default_value = "has_stock"
    link_sockets(tree, gin.outputs["Has Stock"], store_s.inputs["Value"])
    link_sockets(tree, store_t.outputs["Geometry"], store_s.inputs["Geometry"])
    link_sockets(tree, store_s.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(grid, "curve")
    color_node(post, "geometry")
    color_node(join, "geometry")
    color_node(store_t, "attribute")
    color_node(store_s, "attribute")
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Post Frame", "nodes": ("grid", "post", "instance"), "role": "instance"},
        {"title": "Canopy", "nodes": ("canopy", "combine"), "role": "geometry"},
        {"title": "Awning & Counter", "nodes": ("skirt", "counter", "transform"), "role": "geometry"},
        {"title": "Stall Attributes", "nodes": ("store",), "role": "attribute"},
        {"title": "Output", "nodes": ("join", "Group Output"), "role": "output"},
    ])


def build_env_campfire_ring(group_name="MEL_env_campfire_ring"):
    """Campfire ring — stone ring, log pile, inner and outer flames.

    Stores fire_intensity (FLOAT) on the output for FX lanes.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_float_param(tree, "Ring Radius", 0.8, 0.3, 3.0)
    add_int_param(tree, "Stone Count", 8, 4, 24)
    add_int_param(tree, "Log Count", 5, 2, 12)
    add_float_param(tree, "Fire Scale", 0.4, 0.1, 1.5)

    ring = safe_node(tree, "GeometryNodeMeshCircle", (bx - 600, by + 300))
    link_sockets(tree, gin.outputs["Ring Radius"], ring.inputs["Radius"])
    link_sockets(tree, gin.outputs["Stone Count"], ring.inputs["Vertices"])
    ring.fill_type = "NONE"
    stone = safe_node(tree, "GeometryNodeMeshCube", (bx - 600, by + 100))
    stone.inputs["Size"].default_value = (0.22, 0.14, 0.18)
    stones = _instance(tree, (bx - 200, by + 300), ring.outputs["Mesh"], _place(tree, (bx - 400, by + 100), stone.outputs["Mesh"], z=0.09))

    log_spread = _math(tree, "MULTIPLY", (bx - 900, by - 100), gin.outputs["Ring Radius"], 1.1)
    log_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 700, by - 100))
    log_line.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Log Count"], log_line.inputs["Count"])
    link_sockets(tree, _combine(tree, (bx - 900, by + 20),
                                _math(tree, "MULTIPLY", (bx - 1000, by + 20), log_spread.outputs[0], -0.5).outputs[0], 0.0, 0.0).outputs["Vector"], log_line.inputs["Start Location"])
    link_sockets(tree, _combine(tree, (bx - 900, by - 60),
                                _math(tree, "DIVIDE", (bx - 1000, by - 60), log_spread.outputs[0], gin.outputs["Log Count"]).outputs[0], 0.0, 0.0).outputs["Vector"], log_line.inputs["Offset"])

    log = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by - 300))
    link_sockets(tree, _combine(tree, (bx - 700, by - 360), 0.05,
                                _math(tree, "MULTIPLY", (bx - 800, by - 360), gin.outputs["Ring Radius"], 0.7).outputs[0], 0.08).outputs["Vector"], log.inputs["Size"])
    logs = _instance(tree, (bx - 100, by - 100), log_line.outputs["Mesh"], _place(tree, (bx - 300, by - 300), log.outputs["Mesh"], z=0.04))

    flame_outer = safe_node(tree, "GeometryNodeMeshCone", (bx - 500, by - 500))
    fo_d = _math(tree, "MULTIPLY", (bx - 700, by - 580), gin.outputs["Fire Scale"], 0.5)
    link_sockets(tree, _math(tree, "MULTIPLY", (bx - 700, by - 500), gin.outputs["Fire Scale"], 0.18).outputs[0], flame_outer.inputs["Radius Bottom"])
    flame_outer.inputs["Radius Top"].default_value = 0.0
    link_sockets(tree, fo_d.outputs[0], flame_outer.inputs["Depth"])
    flame_outer.inputs["Vertices"].default_value = 8
    flame_outer_up = _place(tree, (bx - 300, by - 500), flame_outer.outputs["Mesh"],
                            z=_math(tree, "MULTIPLY", (bx - 700, by - 620), fo_d.outputs[0], 0.5).outputs[0])

    flame_inner = safe_node(tree, "GeometryNodeMeshCone", (bx - 500, by - 700))
    fi_d = _math(tree, "MULTIPLY", (bx - 700, by - 780), gin.outputs["Fire Scale"], 0.32)
    link_sockets(tree, _math(tree, "MULTIPLY", (bx - 700, by - 700), gin.outputs["Fire Scale"], 0.09).outputs[0], flame_inner.inputs["Radius Bottom"])
    flame_inner.inputs["Radius Top"].default_value = 0.0
    link_sockets(tree, fi_d.outputs[0], flame_inner.inputs["Depth"])
    flame_inner.inputs["Vertices"].default_value = 6
    flame_inner_up = _place(tree, (bx - 300, by - 700), flame_inner.outputs["Mesh"],
                            z=_math(tree, "ADD", (bx - 700, by - 820), fi_d.outputs[0], 0.1).outputs[0])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 100, by))
    link_sockets(tree, stones, join.inputs["Geometry"])
    link_sockets(tree, logs, join.inputs["Geometry"])
    link_sockets(tree, flame_outer_up, join.inputs["Geometry"])
    link_sockets(tree, flame_inner_up, join.inputs["Geometry"])
    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 300, by + 100))
    store.data_type = "FLOAT"
    store.inputs["Name"].default_value = "fire_intensity"
    link_sockets(tree, gin.outputs["Fire Scale"], store.inputs["Value"])
    link_sockets(tree, join.outputs["Geometry"], store.inputs["Geometry"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(ring, "curve")
    color_node(stone, "geometry")
    color_node(log_line, "curve")
    color_node(flame_outer, "geometry")
    color_node(store, "attribute")
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Stone Ring", "nodes": ("ring", "stone", "instance"), "role": "instance"},
        {"title": "Log Pile", "nodes": ("log", "line", "instance"), "role": "instance"},
        {"title": "Flames", "nodes": ("flame", "cone", "transform"), "role": "geometry"},
        {"title": "Output", "nodes": ("store", "join", "Group Output"), "role": "output"},
    ])


def build_env_village_well(group_name="MEL_env_village_well"):
    """Village well — stone well base, twin posts, crossbar, conical roof, water.

    Stores water_level (FLOAT) and well_depth (FLOAT) on the output.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_float_param(tree, "Well Radius", 0.7, 0.3, 2.0)
    add_float_param(tree, "Wall Height", 0.9, 0.3, 2.0)
    add_float_param(tree, "Post Height", 1.4, 0.6, 3.0)
    add_float_param(tree, "Roof Height", 0.5, 0.2, 1.5)
    add_float_param(tree, "Water Level", 0.5, 0.0, 1.5)
    add_float_param(tree, "Well Depth", 0.8, 0.1, 3.0)

    base = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 500, by + 400))
    link_sockets(tree, gin.outputs["Well Radius"], base.inputs["Radius"])
    link_sockets(tree, gin.outputs["Wall Height"], base.inputs["Depth"])
    base.inputs["Vertices"].default_value = 24
    base.fill_type = "NGON"

    wall_half = _math(tree, "MULTIPLY", (bx - 700, by + 220), gin.outputs["Wall Height"], 0.5)
    water_out = _water_disc(tree, (bx - 500, by + 220),
                            _math(tree, "MULTIPLY", (bx - 700, by + 280), gin.outputs["Well Radius"], 0.82).outputs[0],
                            None,
                            _math(tree, "SUBTRACT", (bx - 700, by + 160), wall_half.outputs[0], gin.outputs["Water Level"]).outputs[0])

    post_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 500, by + 20))
    post_line.mode = "OFFSET"
    post_line.inputs["Count"].default_value = 2
    spread = _math(tree, "MULTIPLY", (bx - 700, by + 20), gin.outputs["Well Radius"], 1.3)
    link_sockets(tree, _combine(tree, (bx - 700, by + 140),
                                _math(tree, "MULTIPLY", (bx - 820, by + 140), spread.outputs[0], -1.0).outputs[0],
                                0.0, wall_half.outputs[0]).outputs["Vector"], post_line.inputs["Start Location"])
    link_sockets(tree, _combine(tree, (bx - 700, by + 60),
                                _math(tree, "MULTIPLY", (bx - 820, by + 60), spread.outputs[0], 2.0).outputs[0],
                                0.0, 0.0).outputs["Vector"], post_line.inputs["Offset"])

    post = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 300, by - 140))
    post.inputs["Radius"].default_value = 0.045
    link_sockets(tree, gin.outputs["Post Height"], post.inputs["Depth"])
    post.inputs["Vertices"].default_value = 8
    post.fill_type = "NGON"
    posts = _instance(tree, (bx - 100, by + 20), post_line.outputs["Mesh"], post.outputs["Mesh"])

    bar = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by - 320))
    link_sockets(tree, _combine(tree, (bx - 700, by - 380),
                                _math(tree, "MULTIPLY", (bx - 800, by - 380), gin.outputs["Well Radius"], 2.6).outputs[0],
                                0.06, 0.06).outputs["Vector"], bar.inputs["Size"])
    bar_out = _place(tree, (bx - 300, by - 320), bar.outputs["Mesh"],
                     z=_math(tree, "ADD", (bx - 700, by - 420), wall_half.outputs[0],
                             _math(tree, "MULTIPLY", (bx - 820, by - 420), gin.outputs["Post Height"], 0.5).outputs[0]).outputs[0])

    roof = safe_node(tree, "GeometryNodeMeshCone", (bx - 500, by - 500))
    link_sockets(tree, _math(tree, "MULTIPLY", (bx - 700, by - 500), gin.outputs["Well Radius"], 1.35).outputs[0], roof.inputs["Radius Bottom"])
    roof.inputs["Radius Top"].default_value = 0.03
    link_sockets(tree, gin.outputs["Roof Height"], roof.inputs["Depth"])
    roof.inputs["Vertices"].default_value = 24
    roof_out = _place(tree, (bx - 300, by - 500), roof.outputs["Mesh"],
                      z=_math(tree, "ADD", (bx - 700, by - 560), wall_half.outputs[0],
                              _math(tree, "ADD", (bx - 820, by - 560),
                                    _math(tree, "MULTIPLY", (bx - 920, by - 560), gin.outputs["Post Height"], 0.5).outputs[0],
                                    _math(tree, "MULTIPLY", (bx - 920, by - 600), gin.outputs["Roof Height"], 0.5).outputs[0]).outputs[0]).outputs[0])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 100, by))
    link_sockets(tree, base.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, water_out, join.inputs["Geometry"])
    link_sockets(tree, posts, join.inputs["Geometry"])
    link_sockets(tree, bar_out, join.inputs["Geometry"])
    link_sockets(tree, roof_out, join.inputs["Geometry"])

    store_w = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 300, by + 100))
    store_w.data_type = "FLOAT"
    store_w.inputs["Name"].default_value = "water_level"
    link_sockets(tree, gin.outputs["Water Level"], store_w.inputs["Value"])
    link_sockets(tree, join.outputs["Geometry"], store_w.inputs["Geometry"])
    store_d = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 500, by + 100))
    store_d.data_type = "FLOAT"
    store_d.inputs["Name"].default_value = "well_depth"
    link_sockets(tree, gin.outputs["Well Depth"], store_d.inputs["Value"])
    link_sockets(tree, store_w.outputs["Geometry"], store_d.inputs["Geometry"])
    link_sockets(tree, store_d.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(base, "geometry")
    color_node(post_line, "curve")
    color_node(post, "geometry")
    color_node(roof, "geometry")
    color_node(store_w, "attribute")
    color_node(store_d, "attribute")
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Well Base", "nodes": ("well", "base", "water"), "role": "geometry"},
        {"title": "Post & Roof", "nodes": ("post", "roof", "bar", "line"), "role": "instance"},
        {"title": "Well Attributes", "nodes": ("store",), "role": "attribute"},
        {"title": "Output", "nodes": ("join", "Group Output"), "role": "output"},
    ])


def build_env_lantern_post(group_name="MEL_env_lantern_post"):
    """Lantern post — pole, arm, glass lantern, cone cap.

    Stores lantern_lit (BOOLEAN) and lantern_height (FLOAT) on the output.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_float_param(tree, "Post Height", 2.4, 0.8, 5.0)
    add_float_param(tree, "Post Radius", 0.06, 0.02, 0.2)
    add_float_param(tree, "Lantern Size", 0.25, 0.1, 0.6)
    add_float_param(tree, "Arm Length", 0.6, 0.2, 1.5)
    add_bool_param(tree, "Lit", True)

    post = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 500, by + 300))
    link_sockets(tree, gin.outputs["Post Radius"], post.inputs["Radius"])
    link_sockets(tree, gin.outputs["Post Height"], post.inputs["Depth"])
    post.inputs["Vertices"].default_value = 10
    post.fill_type = "NGON"
    post_out = _place(tree, (bx - 300, by + 300), post.outputs["Mesh"],
                      z=_math(tree, "MULTIPLY", (bx - 700, by + 300), gin.outputs["Post Height"], 0.5).outputs[0])

    arm = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by + 100))
    link_sockets(tree, _combine(tree, (bx - 700, by + 60), gin.outputs["Arm Length"], 0.05, 0.05).outputs["Vector"], arm.inputs["Size"])
    arm_out = _place(tree, (bx - 300, by + 100), arm.outputs["Mesh"],
                     x=_math(tree, "MULTIPLY", (bx - 700, by + 20), gin.outputs["Arm Length"], 0.5).outputs[0],
                     z=_math(tree, "ADD", (bx - 700, by - 20), gin.outputs["Post Height"], 0.03).outputs[0])

    lantern = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by - 100))
    link_sockets(tree, _combine(tree, (bx - 700, by - 140), gin.outputs["Lantern Size"],
                                _math(tree, "MULTIPLY", (bx - 820, by - 140), gin.outputs["Lantern Size"], 0.8).outputs[0],
                                gin.outputs["Lantern Size"]).outputs["Vector"], lantern.inputs["Size"])
    lantern_out = _place(tree, (bx - 300, by - 100), lantern.outputs["Mesh"],
                         x=_math(tree, "MULTIPLY", (bx - 700, by - 180), gin.outputs["Arm Length"], 0.98).outputs[0],
                         z=_math(tree, "ADD", (bx - 700, by - 220), gin.outputs["Post Height"], 0.05).outputs[0])

    cap = safe_node(tree, "GeometryNodeMeshCone", (bx - 500, by - 300))
    cap_d = _math(tree, "MULTIPLY", (bx - 700, by - 340), gin.outputs["Lantern Size"], 0.35)
    link_sockets(tree, _math(tree, "MULTIPLY", (bx - 700, by - 300), gin.outputs["Lantern Size"], 0.45).outputs[0], cap.inputs["Radius Bottom"])
    cap.inputs["Radius Top"].default_value = 0.0
    link_sockets(tree, cap_d.outputs[0], cap.inputs["Depth"])
    cap.inputs["Vertices"].default_value = 10
    cap_out = _place(tree, (bx - 300, by - 300), cap.outputs["Mesh"],
                     x=_math(tree, "MULTIPLY", (bx - 700, by - 380), gin.outputs["Arm Length"], 0.98).outputs[0],
                     z=_math(tree, "ADD", (bx - 700, by - 420),
                             _math(tree, "ADD", (bx - 820, by - 420), gin.outputs["Post Height"], 0.05).outputs[0],
                             _math(tree, "ADD", (bx - 820, by - 460),
                                   _math(tree, "MULTIPLY", (bx - 920, by - 460), gin.outputs["Lantern Size"], 0.5).outputs[0],
                                   _math(tree, "MULTIPLY", (bx - 920, by - 500), cap_d.outputs[0], 0.5).outputs[0]).outputs[0]).outputs[0])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 100, by + 100))
    link_sockets(tree, post_out, join.inputs["Geometry"])
    link_sockets(tree, arm_out, join.inputs["Geometry"])
    link_sockets(tree, lantern_out, join.inputs["Geometry"])
    link_sockets(tree, cap_out, join.inputs["Geometry"])

    store_l = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 300, by + 200))
    store_l.data_type = "BOOLEAN"
    store_l.inputs["Name"].default_value = "lantern_lit"
    link_sockets(tree, gin.outputs["Lit"], store_l.inputs["Value"])
    link_sockets(tree, join.outputs["Geometry"], store_l.inputs["Geometry"])
    store_h = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 500, by + 200))
    store_h.data_type = "FLOAT"
    store_h.inputs["Name"].default_value = "lantern_height"
    link_sockets(tree, gin.outputs["Post Height"], store_h.inputs["Value"])
    link_sockets(tree, store_l.outputs["Geometry"], store_h.inputs["Geometry"])
    link_sockets(tree, store_h.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(post, "geometry")
    color_node(lantern, "geometry")
    color_node(cap, "geometry")
    color_node(store_l, "attribute")
    color_node(store_h, "attribute")
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Pole & Arm", "nodes": ("pole", "arm", "transform"), "role": "geometry"},
        {"title": "Lantern", "nodes": ("lantern", "cap", "cone"), "role": "geometry"},
        {"title": "Lantern Attributes", "nodes": ("store",), "role": "attribute"},
        {"title": "Output", "nodes": ("join", "Group Output"), "role": "output"},
    ])


def build_env_hedgerow(group_name="MEL_env_hedgerow"):
    """Hedgerow — trimmed row body with rounded bush topknots.

    Stores hedge_height (FLOAT) on the output for PCG height reads.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_float_param(tree, "Row Length", 8.0, 1.0, 40.0)
    add_float_param(tree, "Row Width", 1.2, 0.4, 4.0)
    add_float_param(tree, "Row Height", 1.5, 0.4, 4.0)
    add_int_param(tree, "Bush Count", 12, 2, 60)

    body = safe_node(tree, "GeometryNodeMeshCube", (bx - 600, by + 300))
    link_sockets(tree, _combine(tree, (bx - 800, by + 240), gin.outputs["Row Length"], gin.outputs["Row Width"],
                                _math(tree, "MULTIPLY", (bx - 900, by + 240), gin.outputs["Row Height"], 0.55).outputs[0]).outputs["Vector"], body.inputs["Size"])
    body_out = _place(tree, (bx - 400, by + 300), body.outputs["Mesh"],
                      z=_math(tree, "MULTIPLY", (bx - 800, by + 180), gin.outputs["Row Height"], 0.275).outputs[0])

    bush_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 600, by))
    bush_line.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Bush Count"], bush_line.inputs["Count"])
    link_sockets(tree, _combine(tree, (bx - 800, by + 120),
                                _math(tree, "MULTIPLY", (bx - 920, by + 120), gin.outputs["Row Length"], -0.5).outputs[0],
                                0.0, _math(tree, "MULTIPLY", (bx - 920, by + 80), gin.outputs["Row Height"], 0.55).outputs[0]).outputs["Vector"], bush_line.inputs["Start Location"])
    link_sockets(tree, _combine(tree, (bx - 800, by + 40),
                                _math(tree, "DIVIDE", (bx - 920, by + 40), gin.outputs["Row Length"], gin.outputs["Bush Count"]).outputs[0],
                                0.0, 0.0).outputs["Vector"], bush_line.inputs["Offset"])

    bush = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 400, by - 200))
    link_sockets(tree, _math(tree, "MULTIPLY", (bx - 600, by - 200), gin.outputs["Row Width"], 0.38).outputs[0], bush.inputs["Radius"])
    bush.inputs["Segments"].default_value = 12
    bush.inputs["Rings"].default_value = 8
    bushes = _instance(tree, (bx - 200, by), bush_line.outputs["Mesh"], bush.outputs["Mesh"])
    bush_up = _place(tree, (bx + 40, by - 200), bushes,
                     z=_math(tree, "MULTIPLY", (bx - 160, by - 240), gin.outputs["Row Height"], 0.3).outputs[0])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200, by + 200))
    link_sockets(tree, body_out, join.inputs["Geometry"])
    link_sockets(tree, bush_up, join.inputs["Geometry"])
    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 400, by + 300))
    store.data_type = "FLOAT"
    store.inputs["Name"].default_value = "hedge_height"
    link_sockets(tree, gin.outputs["Row Height"], store.inputs["Value"])
    link_sockets(tree, join.outputs["Geometry"], store.inputs["Geometry"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(body, "geometry")
    color_node(bush_line, "curve")
    color_node(bush, "geometry")
    color_node(store, "attribute")
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Row Body", "nodes": ("row", "body", "transform"), "role": "geometry"},
        {"title": "Bush Topknots", "nodes": ("bush", "line", "sphere", "instance"), "role": "instance"},
        {"title": "Output", "nodes": ("store", "join", "Group Output"), "role": "output"},
    ])


def build_env_waterfall_pool(group_name="MEL_env_waterfall_pool"):
    """Waterfall pool — basin, water disc, cascade sheet, splash ring.

    Water contract attributes: water_level, current_speed, ripple_carve.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0
    add_float_param(tree, "Pool Radius", 2.0, 0.6, 8.0)
    add_float_param(tree, "Pool Depth", 0.4, 0.1, 1.5)
    add_float_param(tree, "Water Level", 0.15, 0.05, 0.6)
    add_float_param(tree, "Sheet Width", 1.6, 0.5, 5.0)
    add_float_param(tree, "Sheet Height", 2.5, 0.5, 8.0)
    add_float_param(tree, "Splash Strength", 0.5, 0.0, 2.0)
    add_float_param(tree, "Current Speed", 1.0, 0.01, 10.0)
    add_float_param(tree, "Ripple Carve", 0.5, 0.0, 2.0)

    basin = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 500, by + 400))
    link_sockets(tree, gin.outputs["Pool Radius"], basin.inputs["Radius"])
    link_sockets(tree, gin.outputs["Pool Depth"], basin.inputs["Depth"])
    basin.inputs["Vertices"].default_value = 32
    basin.fill_type = "NGON"

    water_out = _water_disc(tree, (bx - 500, by + 220),
                            _math(tree, "MULTIPLY", (bx - 700, by + 280), gin.outputs["Pool Radius"], 0.94).outputs[0],
                            gin.outputs["Water Level"],
                            _math(tree, "MULTIPLY", (bx - 700, by + 160),
                                  _math(tree, "SUBTRACT", (bx - 820, by + 160), gin.outputs["Pool Depth"], gin.outputs["Water Level"]).outputs[0], 0.5).outputs[0])

    sheet = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by + 20))
    link_sockets(tree, _combine(tree, (bx - 700, by - 40), gin.outputs["Sheet Width"], 0.15, gin.outputs["Sheet Height"]).outputs["Vector"], sheet.inputs["Size"])
    sheet_out = _place(tree, (bx - 300, by + 20), sheet.outputs["Mesh"],
                       x=_math(tree, "MULTIPLY", (bx - 700, by - 100), gin.outputs["Pool Radius"], 0.55).outputs[0],
                       z=_math(tree, "MULTIPLY", (bx - 700, by - 160), gin.outputs["Sheet Height"], 0.5).outputs[0])

    splash = add_mesh_torus_linked(
        tree, (bx - 500, by - 220),
        _math(tree, "MULTIPLY", (bx - 700, by - 220), gin.outputs["Sheet Width"], 0.5).outputs[0],
        _math(tree, "ADD", (bx - 700, by - 280),
              _math(tree, "MULTIPLY", (bx - 820, by - 280), gin.outputs["Splash Strength"], 0.05).outputs[0], 0.07).outputs[0],
        major_segments=40, minor_segments=8,
    )
    splash_out = _place(tree, (bx - 300, by - 220), splash.outputs["Mesh"],
                        x=_math(tree, "MULTIPLY", (bx - 700, by - 340), gin.outputs["Pool Radius"], 0.6).outputs[0], z=0.06)

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 100, by + 200))
    link_sockets(tree, basin.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, water_out, join.inputs["Geometry"])
    link_sockets(tree, sheet_out, join.inputs["Geometry"])
    link_sockets(tree, splash_out, join.inputs["Geometry"])
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 300, by + 200))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    _water_attrs(tree, gin, gout, shade.outputs["Geometry"])

    color_node(basin, "geometry")
    color_node(sheet, "geometry")
    color_node(splash, "curve")
    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Pool Basin", "nodes": ("pool", "basin", "water"), "role": "geometry"},
        {"title": "Cascade Sheet", "nodes": ("sheet", "transform"), "role": "geometry"},
        {"title": "Splash Ring", "nodes": ("splash", "torus", "add"), "role": "curve"},
        {"title": "Water Attributes", "nodes": ("store",), "role": "attribute"},
        {"title": "Output", "nodes": ("join", "shade", "Group Output"), "role": "output"},
    ])


# -- Registry --
register_builder("MEL_env_lily_pond", build_env_lily_pond, "Lily Pond",
    "Lily pond — basin, water disc, floating pads, lotus blooms with water attribute contract.",
    "set_dressing")
register_builder("MEL_env_stepping_stones", build_env_stepping_stones, "Stepping Stones",
    "Twin meander path of flattened stones with stone_count and path_width attributes.",
    "set_dressing")
register_builder("MEL_env_reeds_patch", build_env_reeds_patch, "Reeds Patch",
    "Clustered reed stems on a scatter grid with reed_density attribute.",
    "set_dressing")
register_builder("MEL_env_buoy_line", build_env_buoy_line, "Buoy Line",
    "Mooring buoy row with anchor drops and water attribute contract.",
    "set_dressing")
register_builder("MEL_env_market_stall", build_env_market_stall, "Market Stall",
    "Stall with post frame, canopy, awning skirt and counter; stall_type and has_stock attributes.",
    "set_dressing")
register_builder("MEL_env_campfire_ring", build_env_campfire_ring, "Campfire Ring",
    "Stone ring, log pile and twin flames with fire_intensity attribute.",
    "set_dressing")
register_builder("MEL_env_village_well", build_env_village_well, "Village Well",
    "Well base, posts, crossbar and roof with water_level and well_depth attributes.",
    "set_dressing")
register_builder("MEL_env_lantern_post", build_env_lantern_post, "Lantern Post",
    "Pole, arm, lantern and cap with lantern_lit and lantern_height attributes.",
    "set_dressing")
register_builder("MEL_env_hedgerow", build_env_hedgerow, "Hedgerow",
    "Trimmed hedge row with bush topknots and hedge_height attribute.",
    "set_dressing")
register_builder("MEL_env_waterfall_pool", build_env_waterfall_pool, "Waterfall Pool",
    "Pool, cascade sheet and splash ring with water attribute contract.",
    "effects")