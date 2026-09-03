"""Musical hero GN builders - life-size keys, piano-roll paths, walkable sheet rail, room shell, harp.

Period language: instance spacing = key / string width. Pitch is stored along
spline factor (or string index). Endless tiling uses curve length / period.
"""

from __future__ import annotations

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    make_group_input, register_builder, sock, sweep_profile, set_resample_count,
)


def _true_socket(node):
    return node.inputs.get("True") or node.inputs.get("TRUE") or node.inputs.get("A")


def _false_socket(node):
    return node.inputs.get("False") or node.inputs.get("FALSE") or node.inputs.get("B")


def _output_socket(node):
    return node.outputs.get("Output") or (node.outputs[0] if node and node.outputs else None)


def _ensure_group_node(tree, group_name, builder, loc):
    if group_name not in bpy.data.node_groups:
        builder(group_name)
    node = safe_node(tree, "GeometryNodeGroup", loc)
    if node:
        node.node_tree = bpy.data.node_groups.get(group_name)
    return node


def _math(tree, operation, loc, a=None, b=None):
    node = safe_node(tree, "ShaderNodeMath", loc)
    ops = (operation,)
    if operation == "FLOORMOD":
        ops = ("FLOORMOD", "MODULO")
    if node:
        for op in ops:
            try:
                node.operation = op
                break
            except Exception:
                continue
        if a is not None:
            if isinstance(a, (int, float)):
                node.inputs[0].default_value = float(a)
            else:
                link_sockets(tree, a, node.inputs[0])
        if b is not None:
            if isinstance(b, (int, float)):
                node.inputs[1].default_value = float(b)
            else:
                link_sockets(tree, b, node.inputs[1])
    return node


def _combine(tree, loc, x=None, y=None, z=None):
    node = safe_node(tree, "ShaderNodeCombineXYZ", loc)
    for name, val in (("X", x), ("Y", y), ("Z", z)):
        if val is None or node is None:
            continue
        if isinstance(val, (int, float)):
            try:
                node.inputs[name].default_value = float(val)
            except Exception:
                pass
        else:
            link_sockets(tree, val, node.inputs[name])
    return node


def _switch_geo(tree, loc, switch_sock, if_true, if_false):
    sw = safe_node(tree, "GeometryNodeSwitch", loc)
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, switch_sock, sw.inputs.get("Switch") or sw.inputs[0])
    if if_true is not None:
        link_sockets(tree, if_true, _true_socket(sw))
    if if_false is not None:
        link_sockets(tree, if_false, _false_socket(sw))
    return _output_socket(sw)


def _switch_typed(tree, loc, switch_sock, if_true, if_false, input_type="INT"):
    sw = safe_node(tree, "GeometryNodeSwitch", loc)
    try:
        sw.input_type = input_type
    except Exception:
        pass
    link_sockets(tree, switch_sock, sw.inputs.get("Switch") or sw.inputs[0])
    if isinstance(if_true, (int, float)) and _true_socket(sw) is not None:
        try:
            _true_socket(sw).default_value = if_true
        except Exception:
            pass
    else:
        link_sockets(tree, if_true, _true_socket(sw))
    if isinstance(if_false, (int, float)) and _false_socket(sw) is not None:
        try:
            _false_socket(sw).default_value = if_false
        except Exception:
            pass
    else:
        link_sockets(tree, if_false, _false_socket(sw))
    return _output_socket(sw)


def _compare(tree, loc, a_sock, b, *, data_type="FLOAT", operation="EQUAL"):
    node = safe_node(tree, "FunctionNodeCompare", loc)
    if node is None:
        return None
    try:
        node.data_type = data_type
    except Exception:
        pass
    try:
        node.operation = operation
    except Exception:
        pass
    a_in = sock(node, "A", "A_FLOAT", "A_INT")
    b_in = sock(node, "B", "B_FLOAT", "B_INT")
    if a_in is not None:
        if isinstance(a_sock, (int, float)):
            try:
                a_in.default_value = a_sock
            except Exception:
                pass
        else:
            link_sockets(tree, a_sock, a_in)
    if b_in is not None:
        if isinstance(b, (int, float)):
            try:
                b_in.default_value = b
            except Exception:
                pass
        else:
            link_sockets(tree, b, b_in)
    return node.outputs.get("Result") or _output_socket(node)


def _bool_or(tree, loc, a_sock, b_sock):
    node = safe_node(tree, "FunctionNodeBooleanMath", loc)
    if node is None:
        addn = _math(tree, "ADD", loc, a_sock, b_sock)
        return addn.outputs[0] if addn else a_sock
    try:
        node.operation = "OR"
    except Exception:
        pass
    link_sockets(tree, a_sock, node.inputs[0])
    link_sockets(tree, b_sock, node.inputs[1])
    return node.outputs.get("Boolean") or _output_socket(node)


def _bool_not(tree, loc, a_sock):
    node = safe_node(tree, "FunctionNodeBooleanMath", loc)
    if node is None:
        return a_sock
    try:
        node.operation = "NOT"
    except Exception:
        pass
    link_sockets(tree, a_sock, node.inputs[0])
    return node.outputs.get("Boolean") or _output_socket(node)


def _to_int(tree, loc, value_sock):
    node = safe_node(tree, "FunctionNodeFloatToInt", loc)
    if node is None:
        return value_sock
    try:
        node.rounding_mode = "FLOOR"
    except Exception:
        pass
    link_sockets(tree, value_sock, node.inputs[0] if node.inputs else None)
    return node.outputs[0] if node.outputs else value_sock


def _replace_output(tree, gout, geom):
    geo_in = gout.inputs.get("Geometry")
    if geo_in is not None:
        for link in list(tree.links):
            if link.to_socket == geo_in:
                try:
                    tree.links.remove(link)
                except Exception:
                    pass
    link_sockets(tree, geom, gout.inputs["Geometry"])


def _export_tail(tree, gin, gout, geom, loc):
    """Realize-for-export at the end only; live instances stay editable."""
    bx, by = loc
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by))
    link_sockets(tree, geom, realize.inputs["Geometry"])
    export_switch = safe_node(tree, "GeometryNodeSwitch", (bx + 220, by))
    try:
        export_switch.input_type = "GEOMETRY"
    except Exception:
        pass
    realize_sock = gin.outputs.get("Realize for export")
    if realize_sock is not None:
        link_sockets(tree, realize_sock, export_switch.inputs.get("Switch") or export_switch.inputs[0])
    link_sockets(tree, geom, _false_socket(export_switch))
    link_sockets(tree, realize.outputs["Geometry"], _true_socket(export_switch))
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 440, by))
    try:
        shade.inputs["Shade Smooth"].default_value = True
    except Exception:
        pass
    link_sockets(tree, _output_socket(export_switch), shade.inputs["Geometry"])
    _replace_output(tree, gout, shade.outputs["Geometry"])
    color_node(realize, "instance")
    color_node(export_switch, "instance")
    color_node(shade, "geometry")
    return shade.outputs["Geometry"]


def _store_named(tree, loc, geom, name, value_sock, data_type="FLOAT", domain=None):
    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", loc)
    store.data_type = data_type
    if domain:
        try:
            store.domain = domain
        except Exception:
            pass
    try:
        store.inputs["Name"].default_value = name
    except Exception:
        pass
    link_sockets(tree, geom, store.inputs["Geometry"])
    if value_sock is not None:
        val = store.inputs.get("Value") or store.inputs.get("Value_001")
        link_sockets(tree, value_sock, val)
    color_node(store, "attribute")
    return store.outputs["Geometry"]


def _sized_cube(tree, loc, size_x, size_y, size_z):
    cube = safe_node(tree, "GeometryNodeMeshCube", loc)
    link_float_to_vector(tree, size_x, cube, "Size", component=0, defaults=(1.0, 1.0, 1.0))
    link_float_to_vector(tree, size_y, cube, "Size", component=1, defaults=(1.0, 1.0, 1.0))
    link_float_to_vector(tree, size_z, cube, "Size", component=2, defaults=(1.0, 1.0, 1.0))
    color_node(cube, "geometry")
    return cube.outputs.get("Mesh") or cube.outputs[0]


def _translate(tree, loc, geom, translation_sock):
    node = safe_node(tree, "GeometryNodeTransform", loc)
    link_sockets(tree, geom, node.inputs["Geometry"])
    link_sockets(tree, translation_sock, node.inputs["Translation"])
    color_node(node, "instance")
    return node.outputs["Geometry"]


def _lift_z(tree, loc, geom, height_sock, factor=0.5):
    half = _math(tree, "MULTIPLY", (loc[0] - 160, loc[1]), height_sock, factor)
    vec = _combine(tree, (loc[0] - 40, loc[1]), 0.0, 0.0, half.outputs[0])
    return _translate(tree, loc, geom, vec.outputs["Vector"])


def _mesh_span_x(tree, node, length_sock, count_sock=None):
    """Span a Mesh Line along +X. Blender 5.2 dropped End Location in OFFSET mode."""
    if node is None:
        return
    if count_sock is not None:
        cin = sock(node, "Count")
        if cin is not None:
            link_sockets(tree, count_sock, cin)
    if sock(node, "End Location"):
        try:
            node.mode = "END_POINTS"
        except Exception:
            pass
        link_float_to_vector(tree, length_sock, node, "End Location", component=0)
        return
    try:
        node.mode = "OFFSET"
    except Exception:
        pass
    if sock(node, "Offset"):
        link_float_to_vector(tree, length_sock, node, "Offset", component=0)


def _curve_line(tree, loc, length_sock):
    line = safe_node(tree, "GeometryNodeCurvePrimitiveLine", loc)
    if line is not None:
        try:
            line.mode = "DIRECTION"
        except Exception:
            pass
        length_in = sock(line, "Length")
        if length_in is not None:
            link_sockets(tree, length_sock, length_in)
        else:
            end_in = sock(line, "End") or (line.inputs[1] if line.inputs else None)
            end = _combine(tree, (loc[0] - 160, loc[1] - 80), length_sock, 0.0, 0.0)
            link_sockets(tree, end.outputs["Vector"], end_in)
        color_node(line, "curve")
        return sock(line, "Curve", "Geometry", outputs=True) or line.outputs[0]
    mesh = safe_node(tree, "GeometryNodeMeshLine", loc)
    try:
        mesh.inputs["Count"].default_value = 2
    except Exception:
        pass
    _mesh_span_x(tree, mesh, length_sock)
    to_curve = safe_node(tree, "GeometryNodeMeshToCurve", (loc[0] + 180, loc[1]))
    link_sockets(tree, mesh.outputs["Mesh"], sock(to_curve, "Mesh") or to_curve.inputs[0])
    color_node(mesh, "curve")
    color_node(to_curve, "curve")
    return sock(to_curve, "Curve", "Geometry", outputs=True) or to_curve.outputs[0]


def _curve_length(tree, loc, curve_sock, fallback_sock):
    node = safe_node(tree, "GeometryNodeCurveLength", loc)
    if node is None:
        return fallback_sock
    link_sockets(tree, curve_sock, node.inputs.get("Curve") or node.inputs.get("Geometry") or node.inputs[0])
    return node.outputs.get("Length") or fallback_sock


def _default_spline(tree, gin, loc, length_sock):
    """Default seed curve along +X, or Mesh-to-Curve of incoming Geometry."""
    bx, by = loc
    add_bool_param(tree, "Use Default Seed", True)
    seed = _curve_line(tree, (bx, by + 80), length_sock)
    to_curve = safe_node(tree, "GeometryNodeMeshToCurve", (bx, by - 80))
    geo_in = gin.outputs.get("Geometry")
    if geo_in is not None and to_curve is not None:
        link_sockets(tree, geo_in, to_curve.inputs.get("Mesh") or to_curve.inputs[0])
        color_node(to_curve, "curve")
        incoming = to_curve.outputs.get("Curve") or to_curve.outputs[0]
    else:
        incoming = seed
    return _switch_geo(tree, (bx + 240, by), gin.outputs["Use Default Seed"], seed, incoming)


def _is_accidental_field(tree, loc, index_sock):
    """Piano accidental classes: 1, 3, 6, 8, 10 in 12-TET."""
    bx, by = loc
    pc = _math(tree, "FLOORMOD", (bx, by), index_sock, 12.0)
    flags = []
    for i, tone in enumerate((1.0, 3.0, 6.0, 8.0, 10.0)):
        flags.append(_compare(tree, (bx + 200, by - i * 70), pc.outputs[0], tone))
    acc = flags[0]
    for i, flag in enumerate(flags[1:], 1):
        acc = _bool_or(tree, (bx + 420, by - i * 70), acc, flag)
    color_node(pc, "math")
    return acc


def _instance_on_spline_group(tree, loc, proto, spline, count_sock):
    """Resample curve by count, then instance proto - same pattern as MEL_instance_on_spline.

    Inline on 5.2: nested GeometryNodeGroup Count/Spline sockets are unreliable.
    Still constructs MEL_instance_on_spline so the helper tree exists for reuse.
    """
    from .primitives import build_instance_on_spline
    _ensure_group_node(
        tree, "MEL_instance_on_spline", build_instance_on_spline, (loc[0], loc[1] + 240),
    )
    resample = safe_node(tree, "GeometryNodeResampleCurve", loc)
    set_resample_count(resample)
    curve_in = sock(resample, "Curve", "Geometry") or (resample.inputs[0] if resample and resample.inputs else None)
    link_sockets(tree, spline, curve_in)
    count_in = sock(resample, "Count", "Offset", "Length")
    if count_in is not None:
        link_sockets(tree, count_sock, count_in)
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (loc[0] + 220, loc[1]))
    pts = sock(inst, "Points") or (inst.inputs[0] if inst and inst.inputs else None)
    resample_out = sock(resample, "Curve", "Geometry", outputs=True) or (
        resample.outputs[0] if resample and resample.outputs else None
    )
    link_sockets(tree, resample_out, pts)
    inst_in = sock(inst, "Instance")
    link_sockets(tree, proto, inst_in)
    color_node(resample, "curve")
    color_node(inst, "instance")
    return sock(inst, "Instances", "Geometry", outputs=True) or inst.outputs[0]


def _count_from_period(tree, loc, endless_sock, key_count_sock, curve_len_sock, period_sock):
    bx, by = loc
    div = _math(tree, "DIVIDE", (bx, by + 40), curve_len_sock, period_sock)
    floored = _math(tree, "FLOOR", (bx + 160, by + 40), div.outputs[0], 0.0)
    clamped = _math(tree, "MAXIMUM", (bx + 320, by + 40), floored.outputs[0], 2.0)
    endless_int = _to_int(tree, (bx + 480, by + 40), clamped.outputs[0])
    return _switch_typed(
        tree, (bx + 640, by), endless_sock, endless_int, key_count_sock, input_type="INT",
    )


# ---------------------------------------------------------------------------
# MEL_music_key_unit
# ---------------------------------------------------------------------------

def build_music_key_unit(group_name="MEL_music_key_unit"):
    """One life-size keyboard key: box + front lip. Accidentals are shorter/raised."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Width", 0.0235, 0.008, 1.5)
    add_float_param(tree, "Length", 0.15, 0.04, 4.0)
    add_float_param(tree, "Height", 0.018, 0.004, 0.8)
    add_bool_param(tree, "Is Accidental", False)
    add_float_param(tree, "Pitch", 0.0, -24.0, 88.0)
    add_float_param(tree, "Lip Depth", 0.012, 0.0, 0.4)
    add_bool_param(tree, "Realize for export", False)

    white_body = _sized_cube(
        tree, (bx - 520, by + 220),
        gin.outputs["Width"], gin.outputs["Length"], gin.outputs["Height"],
    )
    white_lifted = _lift_z(tree, (bx - 280, by + 220), white_body, gin.outputs["Height"])

    lip_h = _math(tree, "MULTIPLY", (bx - 720, by + 40), gin.outputs["Height"], 0.38)
    lip = _sized_cube(
        tree, (bx - 520, by + 40),
        gin.outputs["Width"], gin.outputs["Lip Depth"], lip_h.outputs[0],
    )
    half_len = _math(tree, "MULTIPLY", (bx - 720, by - 40), gin.outputs["Length"], 0.5)
    half_lip = _math(tree, "MULTIPLY", (bx - 720, by - 120), gin.outputs["Lip Depth"], 0.5)
    lip_y = _math(tree, "ADD", (bx - 540, by - 80), half_len.outputs[0], half_lip.outputs[0])
    lip_y_neg = _math(tree, "MULTIPLY", (bx - 360, by - 80), lip_y.outputs[0], -1.0)
    lip_z = _math(tree, "MULTIPLY", (bx - 360, by - 160), lip_h.outputs[0], 0.5)
    lip_pos = _combine(tree, (bx - 200, by - 40), 0.0, lip_y_neg.outputs[0], lip_z.outputs[0])
    lip_moved = _translate(tree, (bx - 40, by + 40), lip, lip_pos.outputs["Vector"])

    white_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 80, by + 160))
    link_sockets(tree, white_lifted, white_join.inputs["Geometry"])
    link_sockets(tree, lip_moved, white_join.inputs["Geometry"])
    color_node(white_join, "geometry")

    acc_w = _math(tree, "MULTIPLY", (bx - 720, by - 280), gin.outputs["Width"], 0.52)
    acc_l = _math(tree, "MULTIPLY", (bx - 720, by - 360), gin.outputs["Length"], 0.62)
    acc_h = _math(tree, "MULTIPLY", (bx - 720, by - 440), gin.outputs["Height"], 1.15)
    acc_body = _sized_cube(tree, (bx - 520, by - 320), acc_w.outputs[0], acc_l.outputs[0], acc_h.outputs[0])
    raise_z = _math(tree, "MULTIPLY", (bx - 360, by - 480), gin.outputs["Height"], 0.55)
    acc_half = _math(tree, "MULTIPLY", (bx - 360, by - 560), acc_h.outputs[0], 0.5)
    acc_z = _math(tree, "ADD", (bx - 180, by - 520), raise_z.outputs[0], acc_half.outputs[0])
    acc_pos = _combine(tree, (bx - 40, by - 400), 0.0, 0.0, acc_z.outputs[0])
    acc_moved = _translate(tree, (bx + 80, by - 320), acc_body, acc_pos.outputs["Vector"])

    key_geo = _switch_geo(
        tree, (bx + 280, by + 40), gin.outputs["Is Accidental"],
        acc_moved, white_join.outputs["Geometry"],
    )
    keyed = _store_named(tree, (bx + 500, by + 40), key_geo, "pitch", gin.outputs["Pitch"])
    _export_tail(tree, gin, gout, keyed, (bx + 720, by + 40))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "White Key", "nodes": ("cube", "lip", "join"), "role": "geometry"},
        {"title": "Accidental", "nodes": ("accidental", "switch"), "role": "geometry"},
        {"title": "Pitch", "nodes": ("store",), "role": "attribute"},
        {"title": "Export", "nodes": ("realize", "switch", "shade", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_piano_roll
# ---------------------------------------------------------------------------

def build_music_piano_roll(group_name="MEL_music_piano_roll"):
    """Instance key_unit on a spline. Period = key width. Profile: bar vs lever."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Key Width", 0.08, 0.01, 2.0)
    add_float_param(tree, "Key Length", 0.22, 0.04, 4.0)
    add_float_param(tree, "Key Height", 0.04, 0.004, 1.0)
    add_int_param(tree, "Profile", 0, 0, 3)  # 0 PIANO / 1 XYLOPHONE / 2 MARIMBA / 3 GLOCK
    add_int_param(tree, "Key Count", 24, 2, 128)
    add_bool_param(tree, "Endless", True)
    add_float_param(tree, "Length", 4.0, 0.4, 80.0)
    add_float_param(tree, "Pitch Start", 0.0, -24.0, 88.0)
    add_float_param(tree, "Black Offset", 0.04, 0.0, 2.0)
    add_bool_param(tree, "Realize for export", False)

    spline = _default_spline(tree, gin, (bx - 900, by + 360), gin.outputs["Length"])
    curve_len = _curve_length(tree, (bx - 560, by + 520), spline, gin.outputs["Length"])
    count_sock = _count_from_period(
        tree, (bx - 520, by + 280),
        gin.outputs["Endless"], gin.outputs["Key Count"],
        curve_len, gin.outputs["Key Width"],
    )

    key_grp = _ensure_group_node(tree, "MEL_music_key_unit", build_music_key_unit, (bx - 520, by + 80))
    if key_grp and key_grp.node_tree:
        for name in ("Width", "Length", "Height"):
            src = {"Width": "Key Width", "Length": "Key Length", "Height": "Key Height"}[name]
            if key_grp.inputs.get(name):
                link_sockets(tree, gin.outputs[src], key_grp.inputs[name])
        if key_grp.inputs.get("Is Accidental"):
            try:
                key_grp.inputs["Is Accidental"].default_value = False
            except Exception:
                pass
        if key_grp.inputs.get("Lip Depth"):
            lip = _math(tree, "MULTIPLY", (bx - 720, by - 40), gin.outputs["Key Height"], 0.55)
            link_sockets(tree, lip.outputs[0], key_grp.inputs["Lip Depth"])
    lever = key_grp.outputs.get("Geometry") if key_grp and key_grp.node_tree else None

    # Bar prototypes: XYLO / MARIMBA / GLOCK scale the same box (no lip).
    xylo_l = _math(tree, "MULTIPLY", (bx - 720, by - 160), gin.outputs["Key Length"], 1.05)
    xylo_h = _math(tree, "MULTIPLY", (bx - 720, by - 240), gin.outputs["Key Height"], 0.55)
    mar_l = _math(tree, "MULTIPLY", (bx - 720, by - 320), gin.outputs["Key Length"], 1.45)
    mar_h = _math(tree, "MULTIPLY", (bx - 720, by - 400), gin.outputs["Key Height"], 0.7)
    glock_l = _math(tree, "MULTIPLY", (bx - 720, by - 480), gin.outputs["Key Length"], 0.55)
    glock_h = _math(tree, "MULTIPLY", (bx - 720, by - 560), gin.outputs["Key Height"], 0.38)
    bar_xylo = _lift_z(
        tree, (bx - 360, by - 200),
        _sized_cube(tree, (bx - 520, by - 200), gin.outputs["Key Width"], xylo_l.outputs[0], xylo_h.outputs[0]),
        xylo_h.outputs[0],
    )
    bar_mar = _lift_z(
        tree, (bx - 360, by - 360),
        _sized_cube(tree, (bx - 520, by - 360), gin.outputs["Key Width"], mar_l.outputs[0], mar_h.outputs[0]),
        mar_h.outputs[0],
    )
    bar_glock = _lift_z(
        tree, (bx - 360, by - 520),
        _sized_cube(tree, (bx - 520, by - 520), gin.outputs["Key Width"], glock_l.outputs[0], glock_h.outputs[0]),
        glock_h.outputs[0],
    )

    is_xylo = _compare(tree, (bx - 160, by - 80), gin.outputs["Profile"], 1, data_type="INT")
    is_mar = _compare(tree, (bx - 160, by - 200), gin.outputs["Profile"], 2, data_type="INT")
    is_glock = _compare(tree, (bx - 160, by - 320), gin.outputs["Profile"], 3, data_type="INT")
    proto_xylo = _switch_geo(tree, (bx + 40, by - 80), is_xylo, bar_xylo, lever)
    proto_mar = _switch_geo(tree, (bx + 40, by - 200), is_mar, bar_mar, proto_xylo)
    proto = _switch_geo(tree, (bx + 40, by - 320), is_glock, bar_glock, proto_mar)

    instanced = _instance_on_spline_group(
        tree, (bx + 280, by + 200), proto, spline, count_sock,
    )

    idx = safe_node(tree, "GeometryNodeInputIndex", (bx + 280, by - 40))
    color_node(idx, "attribute")
    accidental = _is_accidental_field(tree, (bx + 280, by - 160), idx.outputs["Index"])
    y_off = _switch_typed(
        tree, (bx + 720, by - 80), accidental,
        gin.outputs["Black Offset"], 0.0, input_type="FLOAT",
    )
    z_raise = _math(tree, "MULTIPLY", (bx + 520, by - 240), gin.outputs["Key Height"], 0.45)
    z_off = _switch_typed(
        tree, (bx + 720, by - 240), accidental, z_raise.outputs[0], 0.0, input_type="FLOAT",
    )
    offset_vec = _combine(tree, (bx + 900, by - 140), 0.0, y_off, z_off)
    translate_inst = safe_node(tree, "GeometryNodeTranslateInstances", (bx + 520, by + 80))
    if translate_inst:
        link_sockets(tree, instanced, translate_inst.inputs.get("Instances") or translate_inst.inputs[0])
        link_sockets(tree, offset_vec.outputs["Vector"], translate_inst.inputs.get("Translation"))
        sel = translate_inst.inputs.get("Selection")
        if sel is not None:
            link_sockets(tree, accidental, sel)
        color_node(translate_inst, "instance")
        moved = translate_inst.outputs.get("Instances") or translate_inst.outputs[0]
    else:
        moved = instanced

    y_scale = _switch_typed(
        tree, (bx + 720, by - 360), accidental, 0.68, 1.0, input_type="FLOAT",
    )
    scale_vec = _combine(tree, (bx + 900, by - 360), 1.0, y_scale, 1.0)
    scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 740, by + 80))
    if scale_inst:
        link_sockets(tree, moved, scale_inst.inputs.get("Instances") or scale_inst.inputs[0])
        link_sockets(tree, scale_vec.outputs["Vector"], scale_inst.inputs.get("Scale"))
        color_node(scale_inst, "instance")
        scaled = scale_inst.outputs.get("Instances") or scale_inst.outputs[0]
    else:
        scaled = moved

    pitch = _math(tree, "ADD", (bx + 740, by - 40), idx.outputs["Index"], gin.outputs["Pitch Start"])
    stored = _store_named(
        tree, (bx + 980, by + 80), scaled, "pitch", pitch.outputs[0],
        data_type="FLOAT", domain="INSTANCE",
    )
    _export_tail(tree, gin, gout, stored, (bx + 1200, by + 80))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Spline Period", "nodes": ("curve", "length", "count", "endless"), "role": "curve"},
        {"title": "Key Prototype", "nodes": ("key_unit", "bar", "profile"), "role": "geometry"},
        {"title": "Instance On Spline", "nodes": ("instance",), "role": "instance"},
        {"title": "Pitch And Accidentals", "nodes": ("index", "offset", "store"), "role": "attribute"},
        {"title": "Export", "nodes": ("realize", "switch", "shade", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_sheet_rail  (rewrite in place - same tree id)
# ---------------------------------------------------------------------------

def build_music_sheet_rail(group_name="MEL_music_sheet_rail"):
    """Walkable staff railing: posts + five swept staff lines + note heads at pitch-height."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Length", 8.0, 1.0, 40.0)
    add_float_param(tree, "Height", 1.05, 0.4, 3.0)
    add_float_param(tree, "Line Thickness", 0.04, 0.008, 0.2)
    add_float_param(tree, "Line Spacing", 0.12, 0.04, 0.4)
    add_int_param(tree, "Note Count", 12, 1, 96)
    add_float_param(tree, "Note Size", 0.18, 0.04, 1.2)
    add_int_param(tree, "Post Count", 5, 2, 32)
    add_bool_param(tree, "Show Clef", True)
    add_bool_param(tree, "Realize for export", False)

    # Five horizontal rails stacked in Z (balustrade staff, not a decal).
    rail_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 720, by + 420))
    try:
        rail_line.inputs["Count"].default_value = 2
    except Exception:
        pass
    _mesh_span_x(tree, rail_line, gin.outputs["Length"])
    color_node(rail_line, "curve")
    rail_mesh = sweep_profile(
        tree, (bx - 420, by + 420), rail_line.outputs["Mesh"], gin.outputs["Line Thickness"],
        profile_res=10, already_curve=False,
    )

    spacing_span = _math(tree, "MULTIPLY", (bx - 720, by + 620), gin.outputs["Line Spacing"], 4.0)
    staff_pts = safe_node(tree, "GeometryNodeMeshLine", (bx - 420, by + 620))
    offset_mode = False
    try:
        staff_pts.mode = "OFFSET"
        offset_mode = True
    except Exception:
        staff_pts.mode = "END_POINTS"
    staff_pts.inputs["Count"].default_value = 5
    if offset_mode:
        link_float_to_vector(tree, spacing_span.outputs[0], staff_pts, "Offset", component=2)
    else:
        link_float_to_vector(tree, spacing_span.outputs[0], staff_pts, "End Location", component=2)
    color_node(staff_pts, "curve")

    rail_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 160, by + 500))
    link_sockets(tree, staff_pts.outputs["Mesh"], rail_inst.inputs["Points"])
    link_sockets(tree, rail_mesh, rail_inst.inputs["Instance"])
    color_node(rail_inst, "instance")

    base_z = _math(tree, "SUBTRACT", (bx - 160, by + 680), gin.outputs["Height"], spacing_span.outputs[0])
    rail_lift = _math(tree, "MULTIPLY", (bx + 20, by + 680), gin.outputs["Line Spacing"], 0.0)
    rail_pos = safe_node(tree, "GeometryNodeTransform", (bx + 40, by + 500))
    link_sockets(tree, rail_inst.outputs["Instances"], rail_pos.inputs["Geometry"])
    lift_vec = _combine(tree, (bx + 40, by + 640), 0.0, 0.0, base_z.outputs[0])
    link_sockets(tree, lift_vec.outputs["Vector"], rail_pos.inputs["Translation"])
    color_node(rail_pos, "instance")
    _ = rail_lift  # spacing is encoded in the 5-point line Offset

    # Posts - walkable uprights, same period language as the piano roll.
    post_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 720, by + 80))
    _mesh_span_x(tree, post_line, gin.outputs["Length"], gin.outputs["Post Count"])
    color_node(post_line, "curve")

    try:
        from .profiles import build_post
        post_grp = _ensure_group_node(tree, "MEL_post", build_post, (bx - 420, by - 40))
    except Exception:
        post_grp = None
    if post_grp and post_grp.node_tree:
        if post_grp.inputs.get("Height"):
            link_sockets(tree, gin.outputs["Height"], post_grp.inputs["Height"])
        if post_grp.inputs.get("Width"):
            post_grp.inputs["Width"].default_value = 0.07
        post_geo = post_grp.outputs.get("Geometry")
        color_node(post_grp, "geometry")
    else:
        post_geo = _lift_z(
            tree, (bx - 420, by - 40),
            _sized_cube(tree, (bx - 560, by - 40), 0.07, 0.07, gin.outputs["Height"]),
            gin.outputs["Height"],
        )

    post_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 160, by + 80))
    link_sockets(tree, post_line.outputs["Mesh"], post_inst.inputs["Points"])
    if post_geo is not None:
        link_sockets(tree, post_geo, post_inst.inputs["Instance"])
    color_node(post_inst, "instance")

    # Notes sit at pitch-height on the staff (harmonic -> Z).
    from .music import build_music_harmonic, build_music_note_head, build_music_treble_clef

    note_pts = safe_node(tree, "GeometryNodeMeshLine", (bx - 720, by - 220))
    _mesh_span_x(tree, note_pts, gin.outputs["Length"], gin.outputs["Note Count"])
    color_node(note_pts, "curve")

    harmonic = _ensure_group_node(tree, "MEL_music_harmonic", build_music_harmonic, (bx - 420, by - 220))
    pitched = note_pts.outputs["Mesh"]
    if harmonic and harmonic.node_tree:
        if harmonic.inputs.get("Geometry"):
            link_sockets(tree, note_pts.outputs["Mesh"], harmonic.inputs["Geometry"])
        if harmonic.inputs.get("Note Count"):
            link_sockets(tree, gin.outputs["Note Count"], harmonic.inputs["Note Count"])
        pitched = harmonic.outputs.get("Geometry") or pitched
        color_node(harmonic, "attribute")

    attr = safe_node(tree, "GeometryNodeInputNamedAttribute", (bx - 200, by - 320))
    attr.data_type = "FLOAT"
    try:
        attr.inputs["Name"].default_value = "pitch"
    except Exception:
        pass
    color_node(attr, "attribute")
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 200, by - 400))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 40, by - 400))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])
    pitch_z = _math(tree, "MULTIPLY", (bx - 40, by - 280), attr.outputs.get("Attribute") or attr.outputs[0], 1.0)
    link_sockets(tree, gin.outputs["Line Spacing"], pitch_z.inputs[1])
    note_z = _math(tree, "ADD", (bx + 140, by - 280), base_z.outputs[0], pitch_z.outputs[0])
    combine = _combine(tree, (bx + 140, by - 380), sep.outputs["X"], sep.outputs["Y"], note_z.outputs[0])
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 320, by - 220))
    link_sockets(tree, pitched, set_pos.inputs["Geometry"])
    link_sockets(tree, combine.outputs["Vector"], set_pos.inputs["Position"])

    note_grp = _ensure_group_node(tree, "MEL_music_note_head", build_music_note_head, (bx - 40, by - 80))
    if note_grp and note_grp.node_tree and note_grp.inputs.get("Scale"):
        link_sockets(tree, gin.outputs["Note Size"], note_grp.inputs["Scale"])
        color_node(note_grp, "geometry")
    note_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 520, by - 220))
    link_sockets(tree, set_pos.outputs["Geometry"], note_inst.inputs["Points"])
    if note_grp and note_grp.node_tree:
        note_geo = note_grp.outputs.get("Geometry")
        if note_geo:
            link_sockets(tree, note_geo, note_inst.inputs["Instance"])
    color_node(note_inst, "instance")

    clef_grp = _ensure_group_node(tree, "MEL_music_treble_clef", build_music_treble_clef, (bx + 200, by + 80))
    if clef_grp and clef_grp.node_tree and clef_grp.inputs.get("Scale"):
        clef_scale = _math(tree, "MULTIPLY", (bx + 40, by + 20), gin.outputs["Height"], 0.85)
        link_sockets(tree, clef_scale.outputs[0], clef_grp.inputs["Scale"])
        color_node(clef_grp, "curve")
    clef_xf = safe_node(tree, "GeometryNodeTransform", (bx + 420, by + 80))
    if clef_grp and clef_grp.node_tree:
        link_sockets(tree, clef_grp.outputs.get("Geometry"), clef_xf.inputs["Geometry"])
    clef_z = _math(tree, "MULTIPLY", (bx + 260, by + 0), gin.outputs["Height"], 0.55)
    clef_pos = _combine(tree, (bx + 400, by + 0), 0.15, 0.0, clef_z.outputs[0])
    link_sockets(tree, clef_pos.outputs["Vector"], clef_xf.inputs["Translation"])
    clef_on = _switch_geo(
        tree, (bx + 620, by + 80), gin.outputs["Show Clef"],
        clef_xf.outputs["Geometry"], None,
    )

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 760, by + 200))
    link_sockets(tree, rail_pos.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, post_inst.outputs["Instances"], join.inputs["Geometry"])
    link_sockets(tree, note_inst.outputs["Instances"], join.inputs["Geometry"])
    if clef_on is not None:
        link_sockets(tree, clef_on, join.inputs["Geometry"])
    color_node(join, "geometry")

    _export_tail(tree, gin, gout, join.outputs["Geometry"], (bx + 980, by + 200))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Staff Rails", "nodes": ("sweep", "staff", "rail"), "role": "curve"},
        {"title": "Posts", "nodes": ("post",), "role": "instance"},
        {"title": "Notes", "nodes": ("note", "harmonic", "pitch"), "role": "instance"},
        {"title": "Clef", "nodes": ("clef", "switch"), "role": "curve"},
        {"title": "Export", "nodes": ("realize", "switch", "shade", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_room_shell  (Structures)
# ---------------------------------------------------------------------------

def build_music_room_shell(group_name="MEL_music_room_shell"):
    """Greybox hollow room + openings + optional dado staff band. Structures, not set dressing."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Room Length", 10.0, 2.0, 40.0)
    add_float_param(tree, "Room Width", 7.0, 2.0, 30.0)
    add_float_param(tree, "Room Height", 4.5, 2.0, 16.0)
    add_float_param(tree, "Wall Thickness", 0.28, 0.1, 1.5)
    add_bool_param(tree, "Ceiling", True)
    add_bool_param(tree, "Cut Door", True)
    add_bool_param(tree, "Cut Window", True)
    add_bool_param(tree, "Dado Staff Band", True)
    add_float_param(tree, "Dado Height", 1.05, 0.4, 3.0)
    add_float_param(tree, "Dado Thickness", 0.03, 0.008, 0.15)
    add_float_param(tree, "Line Spacing", 0.12, 0.04, 0.4)
    add_bool_param(tree, "Realize for export", False)

    from .polyhedra_gn import build_greybox_openings, build_greybox_room_kit

    room_grp = _ensure_group_node(tree, "MEL_greybox_room_kit", build_greybox_room_kit, (bx - 520, by + 280))
    if room_grp and room_grp.node_tree:
        mapping = {
            "Room Length": "Room Length",
            "Room Width": "Room Width",
            "Room Height": "Room Height",
            "Wall Thickness": "Wall Thickness",
            "Ceiling": "Ceiling",
        }
        for src, dst in mapping.items():
            if room_grp.inputs.get(dst):
                link_sockets(tree, gin.outputs[src], room_grp.inputs[dst])
        color_node(room_grp, "geometry")
        room_geo = room_grp.outputs.get("Geometry")
    else:
        room_geo = gin.outputs.get("Geometry")

    open_grp = _ensure_group_node(tree, "MEL_greybox_openings", build_greybox_openings, (bx - 160, by + 280))
    opened = room_geo
    if open_grp and open_grp.node_tree:
        if open_grp.inputs.get("Geometry") and room_geo is not None:
            link_sockets(tree, room_geo, open_grp.inputs["Geometry"])
        if open_grp.inputs.get("Cut Door"):
            link_sockets(tree, gin.outputs["Cut Door"], open_grp.inputs["Cut Door"])
        if open_grp.inputs.get("Cut Window"):
            link_sockets(tree, gin.outputs["Cut Window"], open_grp.inputs["Cut Window"])
        opened = open_grp.outputs.get("Geometry") or room_geo
        color_node(open_grp, "geometry")

    inner_l = _math(tree, "SUBTRACT", (bx - 520, by - 40), gin.outputs["Room Length"], gin.outputs["Wall Thickness"])
    inner_w = _math(tree, "SUBTRACT", (bx - 520, by - 120), gin.outputs["Room Width"], gin.outputs["Wall Thickness"])
    quad = safe_node(tree, "GeometryNodeCurvePrimitiveQuadrilateral", (bx - 280, by - 80))
    if quad is not None:
        link_sockets(tree, inner_l.outputs[0], quad.inputs.get("Width") or quad.inputs[0])
        height_in = quad.inputs.get("Height") or (quad.inputs[1] if len(quad.inputs) > 1 else None)
        if height_in is not None:
            link_sockets(tree, inner_w.outputs[0], height_in)
        color_node(quad, "curve")
        band_curve = quad.outputs.get("Curve") or quad.outputs[0]
    else:
        band_curve = _curve_line(tree, (bx - 280, by - 80), inner_l.outputs[0])

    dado_lift = _combine(tree, (bx - 80, by - 200), 0.0, 0.0, gin.outputs["Dado Height"])
    band_at = _translate(tree, (bx + 40, by - 80), band_curve, dado_lift.outputs["Vector"])
    band_mesh = sweep_profile(
        tree, (bx + 240, by - 80), band_at, gin.outputs["Dado Thickness"],
        profile_res=8, already_curve=True,
    )

    spacing_span = _math(tree, "MULTIPLY", (bx + 40, by - 280), gin.outputs["Line Spacing"], 4.0)
    band_pts = safe_node(tree, "GeometryNodeMeshLine", (bx + 240, by - 280))
    offset_mode = False
    try:
        band_pts.mode = "OFFSET"
        offset_mode = True
    except Exception:
        band_pts.mode = "END_POINTS"
    band_pts.inputs["Count"].default_value = 5
    if offset_mode:
        link_float_to_vector(tree, spacing_span.outputs[0], band_pts, "Offset", component=2)
    else:
        link_float_to_vector(tree, spacing_span.outputs[0], band_pts, "End Location", component=2)
    color_node(band_pts, "curve")
    band_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 460, by - 160))
    link_sockets(tree, band_pts.outputs["Mesh"], band_inst.inputs["Points"])
    link_sockets(tree, band_mesh, band_inst.inputs["Instance"])
    color_node(band_inst, "instance")

    empty = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 460, by - 360))
    dado_on = _switch_geo(
        tree, (bx + 680, by - 160), gin.outputs["Dado Staff Band"],
        band_inst.outputs["Instances"], empty.outputs["Geometry"],
    )

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 240, by + 200))
    if opened is not None:
        link_sockets(tree, opened, join.inputs["Geometry"])
    if dado_on is not None:
        link_sockets(tree, dado_on, join.inputs["Geometry"])
    color_node(join, "geometry")
    _export_tail(tree, gin, gout, join.outputs["Geometry"], (bx + 480, by + 200))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Greybox Room", "nodes": ("room", "openings"), "role": "geometry"},
        {"title": "Dado Staff Band", "nodes": ("quadrilateral", "sweep", "band"), "role": "curve"},
        {"title": "Export", "nodes": ("realize", "switch", "shade", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_music_harp
# ---------------------------------------------------------------------------

def build_music_harp(group_name="MEL_music_harp"):
    """Pillar + neck curve, strings instance_on_spline, pitch from string index, soundboard panel."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Height", 1.8, 0.4, 4.0)
    add_float_param(tree, "Depth", 0.55, 0.15, 2.0)
    add_float_param(tree, "Soundboard Width", 0.42, 0.12, 1.5)
    add_float_param(tree, "Soundboard Height", 0.95, 0.2, 2.5)
    add_int_param(tree, "String Count", 47, 4, 80)
    add_float_param(tree, "String Radius", 0.003, 0.001, 0.04)
    add_float_param(tree, "String Spacing", 0.012, 0.004, 0.12)
    add_bool_param(tree, "Endless", False)
    add_float_param(tree, "Pitch Start", 0.0, -12.0, 48.0)
    add_float_param(tree, "Pillar Radius", 0.045, 0.01, 0.2)
    add_bool_param(tree, "Realize for export", False)

    try:
        from .profiles import build_column
        pillar_grp = _ensure_group_node(tree, "MEL_column", build_column, (bx - 520, by + 360))
    except Exception:
        pillar_grp = None
    if pillar_grp and pillar_grp.node_tree:
        if pillar_grp.inputs.get("Height"):
            link_sockets(tree, gin.outputs["Height"], pillar_grp.inputs["Height"])
        if pillar_grp.inputs.get("Radius"):
            link_sockets(tree, gin.outputs["Pillar Radius"], pillar_grp.inputs["Radius"])
        pillar = pillar_grp.outputs.get("Geometry")
        color_node(pillar_grp, "geometry")
    else:
        cyl = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 520, by + 360))
        link_sockets(tree, gin.outputs["Height"], cyl.inputs["Depth"])
        link_sockets(tree, gin.outputs["Pillar Radius"], cyl.inputs["Radius"])
        cyl.inputs["Vertices"].default_value = 12
        pillar = _lift_z(tree, (bx - 300, by + 360), cyl.outputs["Mesh"], gin.outputs["Height"])

    board_thick = _math(tree, "MULTIPLY", (bx - 720, by + 80), gin.outputs["Pillar Radius"], 1.6)
    board = _sized_cube(
        tree, (bx - 520, by + 80),
        board_thick.outputs[0], gin.outputs["Soundboard Width"], gin.outputs["Soundboard Height"],
    )
    board_lifted = _lift_z(tree, (bx - 300, by + 80), board, gin.outputs["Soundboard Height"])
    board_pos = _combine(tree, (bx - 300, by - 40), gin.outputs["Depth"], 0.0, 0.0)
    board_moved = _translate(tree, (bx - 80, by + 80), board_lifted, board_pos.outputs["Vector"])

    neck = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx - 520, by - 200))
    start = _combine(tree, (bx - 720, by - 120), 0.0, 0.0, gin.outputs["Height"])
    end = _combine(tree, (bx - 720, by - 280), gin.outputs["Depth"], 0.0, gin.outputs["Soundboard Height"])
    handle_x = _math(tree, "MULTIPLY", (bx - 900, by - 200), gin.outputs["Depth"], 0.35)
    start_h = _combine(tree, (bx - 720, by - 200), handle_x.outputs[0], 0.0, gin.outputs["Height"])
    end_h_z = _math(tree, "MULTIPLY", (bx - 900, by - 360), gin.outputs["Height"], 0.82)
    end_h = _combine(tree, (bx - 720, by - 360), gin.outputs["Depth"], 0.0, end_h_z.outputs[0])
    if neck:
        link_sockets(tree, start.outputs["Vector"], neck.inputs.get("Start"))
        link_sockets(tree, end.outputs["Vector"], neck.inputs.get("End"))
        if neck.inputs.get("Start Handle"):
            link_sockets(tree, start_h.outputs["Vector"], neck.inputs["Start Handle"])
        if neck.inputs.get("End Handle"):
            link_sockets(tree, end_h.outputs["Vector"], neck.inputs["End Handle"])
        try:
            neck.inputs["Resolution"].default_value = 24
        except Exception:
            pass
        color_node(neck, "curve")
        neck_curve = neck.outputs.get("Curve") or neck.outputs[0]
    else:
        neck_curve = _curve_line(tree, (bx - 520, by - 200), gin.outputs["Depth"])

    neck_mesh = sweep_profile(
        tree, (bx - 240, by - 200), neck_curve, gin.outputs["Pillar Radius"],
        profile_res=8, already_curve=True,
    )

    neck_len = _curve_length(tree, (bx - 80, by - 80), neck_curve, gin.outputs["Depth"])
    count_sock = _count_from_period(
        tree, (bx - 80, by - 280),
        gin.outputs["Endless"], gin.outputs["String Count"],
        neck_len, gin.outputs["String Spacing"],
    )

    string_cyl = safe_node(tree, "GeometryNodeMeshCylinder", (bx + 40, by - 80))
    string_cyl.inputs["Vertices"].default_value = 6
    string_cyl.inputs["Depth"].default_value = 1.0
    link_sockets(tree, gin.outputs["String Radius"], string_cyl.inputs["Radius"])
    color_node(string_cyl, "geometry")

    strings = _instance_on_spline_group(
        tree, (bx + 240, by - 80),
        string_cyl.outputs["Mesh"], neck_curve, count_sock,
    )

    idx = safe_node(tree, "GeometryNodeInputIndex", (bx + 240, by - 280))
    color_node(idx, "attribute")
    count_f = _math(tree, "ADD", (bx + 400, by - 360), gin.outputs["String Count"], 0.0)
    # Guard divide-by-zero with max(count-1, 1)
    count_m1 = _math(tree, "SUBTRACT", (bx + 400, by - 440), count_f.outputs[0], 1.0)
    count_safe = _math(tree, "MAXIMUM", (bx + 560, by - 440), count_m1.outputs[0], 1.0)
    factor = _math(tree, "DIVIDE", (bx + 560, by - 280), idx.outputs["Index"], count_safe.outputs[0])
    long_s = _math(tree, "MULTIPLY", (bx + 400, by - 520), gin.outputs["Height"], 0.82)
    short_s = _math(tree, "MULTIPLY", (bx + 400, by - 600), gin.outputs["Soundboard Height"], 0.35)
    span = _math(tree, "SUBTRACT", (bx + 560, by - 560), long_s.outputs[0], short_s.outputs[0])
    drop = _math(tree, "MULTIPLY", (bx + 720, by - 360), span.outputs[0], factor.outputs[0])
    str_len = _math(tree, "SUBTRACT", (bx + 880, by - 280), long_s.outputs[0], drop.outputs[0])
    scale_vec = _combine(tree, (bx + 880, by - 160), 1.0, 1.0, str_len.outputs[0])
    scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 480, by - 40))
    if scale_inst:
        link_sockets(tree, strings, scale_inst.inputs.get("Instances") or scale_inst.inputs[0])
        link_sockets(tree, scale_vec.outputs["Vector"], scale_inst.inputs.get("Scale"))
        color_node(scale_inst, "instance")
        scaled = scale_inst.outputs.get("Instances") or scale_inst.outputs[0]
    else:
        scaled = strings
    half_len = _math(tree, "MULTIPLY", (bx + 880, by - 40), str_len.outputs[0], -0.5)
    down = _combine(tree, (bx + 1040, by - 40), 0.0, 0.0, half_len.outputs[0])
    drop_inst = safe_node(tree, "GeometryNodeTranslateInstances", (bx + 680, by - 40))
    if drop_inst:
        link_sockets(tree, scaled, drop_inst.inputs.get("Instances") or drop_inst.inputs[0])
        link_sockets(tree, down.outputs["Vector"], drop_inst.inputs.get("Translation"))
        color_node(drop_inst, "instance")
        hung = drop_inst.outputs.get("Instances") or drop_inst.outputs[0]
    else:
        hung = scaled

    pitch = _math(tree, "ADD", (bx + 680, by - 280), idx.outputs["Index"], gin.outputs["Pitch Start"])
    hung_p = _store_named(
        tree, (bx + 900, by + 40), hung, "pitch", pitch.outputs[0],
        data_type="FLOAT", domain="INSTANCE",
    )

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 160, by + 240))
    if pillar is not None:
        link_sockets(tree, pillar, join.inputs["Geometry"])
    link_sockets(tree, board_moved, join.inputs["Geometry"])
    link_sockets(tree, neck_mesh, join.inputs["Geometry"])
    link_sockets(tree, hung_p, join.inputs["Geometry"])
    color_node(join, "geometry")
    _export_tail(tree, gin, gout, join.outputs["Geometry"], (bx + 400, by + 240))

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Pillar And Soundboard", "nodes": ("column", "panel"), "role": "geometry"},
        {"title": "Neck Curve", "nodes": ("bezier", "sweep"), "role": "curve"},
        {"title": "Strings", "nodes": ("instance", "scale", "index"), "role": "instance"},
        {"title": "Pitch", "nodes": ("store",), "role": "attribute"},
        {"title": "Export", "nodes": ("realize", "switch", "shade", "Group Output"), "role": "output"},
    ])


# -- Registry --
register_builder(
    "MEL_music_key_unit", build_music_key_unit, "Music Key Unit",
    "Life-size piano key: box plus front lip, accidental switch, pitch attribute",
    "music",
)
register_builder(
    "MEL_music_piano_roll", build_music_piano_roll, "Music Piano Roll",
    "Instance keys on a spline; period = key width; PIANO/XYLO/MARIMBA/GLOCK profiles",
    "music",
)
register_builder(
    "MEL_music_sheet_rail", build_music_sheet_rail, "Sheet Music Rail",
    "Walkable staff railing: posts, five swept lines, note heads at pitch-height",
    "music",
)
register_builder(
    "MEL_music_room_shell", build_music_room_shell, "Music Room Shell",
    "Greybox hollow room with openings and optional dado staff band",
    "structures",
)
register_builder(
    "MEL_music_harp", build_music_harp, "Music Harp",
    "Pedal harp: pillar, neck curve, strings instance-on-spline, soundboard, pitch index",
    "music",
)
