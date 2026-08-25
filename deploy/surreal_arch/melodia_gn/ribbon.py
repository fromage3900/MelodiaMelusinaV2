"""Ribbon GN group builders - swept ribbons, lissajous, closed loops, violin bow."""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    make_group_input, register_builder,
)


def _build_ribbon_common(group_name, mode="wave"):
    """Shared ribbon graph. `mode` selects the centerline shape.

    wave      - sine centerline (default ribbon)
    lissajous - x = sin(a*t), z = sin(b*t) closed curve
    closed    - circle loop on XZ
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Segments", 64, 8, 256)
    add_float_param(tree, "Length", 6.0, 0.5, 20.0)
    add_float_param(tree, "Ribbon Width", 0.3, 0.01, 2.0)
    add_float_param(tree, "Amplitude", 0.5, 0.0, 3.0)
    add_float_param(tree, "Frequency", 2.0, 0.1, 10.0)
    add_float_param(tree, "Twist", 0.0, 0.0, 6.283)
    add_bool_param(tree, "Closed Loop", mode == "closed")

    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 600, by))
    line.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Segments"], line.inputs["Count"])
    seg_len = safe_node(tree, "ShaderNodeMath", (bx - 800, by))
    seg_len.operation = "DIVIDE"
    link_sockets(tree, gin.outputs["Length"], seg_len.inputs[0])
    link_sockets(tree, gin.outputs["Segments"], seg_len.inputs[1])
    line.inputs["Start Location"].default_value = (-3.0, 0.0, 0.0)
    link_float_to_vector(tree, seg_len.outputs[0], line, "Offset", component=0, defaults=(1.0, 0.0, 0.0))

    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 800, by - 240))
    phi_frac = safe_node(tree, "ShaderNodeMath", (bx - 620, by - 240))
    phi_frac.operation = "DIVIDE"
    link_sockets(tree, idx.outputs["Index"], phi_frac.inputs[0])
    link_sockets(tree, gin.outputs["Segments"], phi_frac.inputs[1])
    two_pi = safe_node(tree, "ShaderNodeMath", (bx - 450, by - 240))
    two_pi.operation = "MULTIPLY"
    two_pi.inputs[0].default_value = math.pi * 2.0
    link_sockets(tree, phi_frac.outputs[0], two_pi.inputs[1])
    phase = safe_node(tree, "ShaderNodeMath", (bx - 280, by - 240))
    phase.operation = "MULTIPLY"
    link_sockets(tree, two_pi.outputs[0], phase.inputs[0])
    link_sockets(tree, gin.outputs["Frequency"], phase.inputs[1])

    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 800, by - 420))
    pos_x = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 620, by - 420))
    link_sockets(tree, pos.outputs["Position"], pos_x.inputs["Vector"])

    if mode == "lissajous":
        y_sin = safe_node(tree, "ShaderNodeMath", (bx - 280, by - 420))
        y_sin.operation = "SINE"
        link_sockets(tree, phase.outputs[0], y_sin.inputs[0])
        y_amp = safe_node(tree, "ShaderNodeMath", (bx - 110, by - 420))
        y_amp.operation = "MULTIPLY"
        link_sockets(tree, y_sin.outputs[0], y_amp.inputs[0])
        link_sockets(tree, gin.outputs["Amplitude"], y_amp.inputs[1])
        z_sin = safe_node(tree, "ShaderNodeMath", (bx - 280, by - 560))
        z_sin.operation = "SINE"
        phase_z = safe_node(tree, "ShaderNodeMath", (bx - 450, by - 560))
        phase_z.operation = "ADD"
        link_sockets(tree, phase.outputs[0], phase_z.inputs[0])
        phase_z.inputs[1].default_value = math.pi / 2.0
        link_sockets(tree, phase_z.outputs[0], z_sin.inputs[0])
        z_amp = safe_node(tree, "ShaderNodeMath", (bx - 110, by - 560))
        z_amp.operation = "MULTIPLY"
        link_sockets(tree, z_sin.outputs[0], z_amp.inputs[0])
        link_sockets(tree, gin.outputs["Amplitude"], z_amp.inputs[1])
    elif mode == "closed":
        c_theta = safe_node(tree, "ShaderNodeMath", (bx - 450, by - 320))
        c_theta.operation = "MULTIPLY"
        link_sockets(tree, phi_frac.outputs[0], c_theta.inputs[0])
        c_theta.inputs[1].default_value = math.pi * 2.0
        cos_t = safe_node(tree, "ShaderNodeMath", (bx - 280, by - 320))
        cos_t.operation = "COSINE"
        link_sockets(tree, c_theta.outputs[0], cos_t.inputs[0])
        sin_t = safe_node(tree, "ShaderNodeMath", (bx - 280, by - 400))
        sin_t.operation = "SINE"
        link_sockets(tree, c_theta.outputs[0], sin_t.inputs[0])
        rad = safe_node(tree, "ShaderNodeMath", (bx - 450, by - 480))
        rad.operation = "MULTIPLY"
        link_sockets(tree, gin.outputs["Length"], rad.inputs[0])
        rad.inputs[1].default_value = 0.5
        y_amp = safe_node(tree, "ShaderNodeMath", (bx - 110, by - 320))
        y_amp.operation = "MULTIPLY"
        link_sockets(tree, cos_t.outputs[0], y_amp.inputs[0])
        link_sockets(tree, rad.outputs[0], y_amp.inputs[1])
        z_amp = safe_node(tree, "ShaderNodeMath", (bx - 110, by - 400))
        z_amp.operation = "MULTIPLY"
        link_sockets(tree, sin_t.outputs[0], z_amp.inputs[0])
        link_sockets(tree, rad.outputs[0], z_amp.inputs[1])
    else:  # wave
        y_sin = safe_node(tree, "ShaderNodeMath", (bx - 280, by - 420))
        y_sin.operation = "SINE"
        link_sockets(tree, phase.outputs[0], y_sin.inputs[0])
        y_amp = safe_node(tree, "ShaderNodeMath", (bx - 110, by - 420))
        y_amp.operation = "MULTIPLY"
        link_sockets(tree, y_sin.outputs[0], y_amp.inputs[0])
        link_sockets(tree, gin.outputs["Amplitude"], y_amp.inputs[1])
        z_amp = safe_node(tree, "ShaderNodeMath", (bx - 110, by - 520))
        z_amp.operation = "ADD"
        z_amp.inputs[0].default_value = 0.0
        z_amp.inputs[1].default_value = 0.0

    y_off = safe_node(tree, "ShaderNodeMath", (bx + 60, by - 300))
    y_off.operation = "ADD"
    link_sockets(tree, pos_x.outputs["Y"], y_off.inputs[0])
    link_sockets(tree, y_amp.outputs[0], y_off.inputs[1])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 110, by))
    link_sockets(tree, line.outputs["Mesh"], set_pos.inputs["Geometry"])
    combine = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 280, by - 200))
    link_sockets(tree, pos_x.outputs["X"], combine.inputs["X"])
    link_sockets(tree, y_off.outputs[0], combine.inputs["Y"])
    link_sockets(tree, z_amp.outputs[0], combine.inputs["Z"])
    link_sockets(tree, combine.outputs["Vector"], set_pos.inputs["Position"])

    extrude = safe_node(tree, "GeometryNodeExtrudeMesh", (bx + 100, by))
    link_sockets(tree, set_pos.outputs["Geometry"], extrude.inputs["Mesh"])
    extrude.mode = "EDGES"
    link_float_to_vector(tree, gin.outputs["Ribbon Width"], extrude, "Offset Scale", component=2, defaults=(0.0, 0.0, 1.0))

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 280, by))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, extrude.outputs["Mesh"], shade.inputs["Geometry"])

    store_w = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 440, by))
    store_w.data_type = "FLOAT"
    store_w.inputs["Name"].default_value = "ribbon_width"
    link_sockets(tree, gin.outputs["Ribbon Width"], store_w.inputs["Value"])
    link_sockets(tree, shade.outputs["Geometry"], store_w.inputs["Geometry"])

    store_t = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 440, by - 200))
    store_t.data_type = "FLOAT"
    store_t.inputs["Name"].default_value = "ribbon_twist"
    link_sockets(tree, gin.outputs["Twist"], store_t.inputs["Value"])
    link_sockets(tree, store_w.outputs["Geometry"], store_t.inputs["Geometry"])
    link_sockets(tree, store_t.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(line, "curve")
    color_node(set_pos, "attribute")
    color_node(extrude, "geometry")
    color_node(store_w, "attribute")
    color_node(store_t, "attribute")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Centerline", "nodes": ("mesh line", "sine", "combine", "set position"), "role": "curve"},
        {"title": "Ribbon", "nodes": ("extrude", "shade"), "role": "geometry"},
        {"title": "Attributes", "nodes": ("store",), "role": "attribute"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_ribbon_curve(group_name="MEL_ribbon_curve"):
    """Wave-shaped ribbon strip with width, amplitude, and twist attributes."""
    return _build_ribbon_common(group_name, mode="wave")


def build_lissajous_ribbon(group_name="MEL_lissajous_ribbon"):
    """Lissajous figure ribbon - sin/cos cross path with configurable frequency."""
    return _build_ribbon_common(group_name, mode="lissajous")


def build_closed_ribbon(group_name="MEL_closed_ribbon"):
    """Seamless circular ribbon loop for UI borders and decorative rings."""
    return _build_ribbon_common(group_name, mode="closed")


def build_violin_bow(group_name="MEL_violin_bow"):
    """Violin bow - tapered stick with a sagging horsehair ribbon curve."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Bow Length", 25.0, 10.0, 50.0)
    add_float_param(tree, "Stick Taper", 0.5, 0.1, 1.0)
    add_float_param(tree, "Hair Curve Height", 2.0, 0.5, 5.0)
    add_int_param(tree, "Hair Resolution", 32, 8, 128)
    add_float_param(tree, "Rosin Zone Length", 8.0, 2.0, 15.0)
    add_bool_param(tree, "Curved Stick", True)

    stick = safe_node(tree, "GeometryNodeMeshCone", (bx - 500, by))
    link_sockets(tree, gin.outputs["Bow Length"], stick.inputs["Depth"])
    stick.inputs["Radius Bottom"].default_value = 0.06
    stick_r = safe_node(tree, "ShaderNodeMath", (bx - 700, by - 200))
    stick_r.operation = "MULTIPLY"
    stick_r.inputs[0].default_value = 0.06
    link_sockets(tree, gin.outputs["Stick Taper"], stick_r.inputs[1])
    link_sockets(tree, stick_r.outputs[0], stick.inputs["Radius Top"])
    stick.inputs["Vertices"].default_value = 16
    stick.fill_type = "NGON"

    hair = safe_node(tree, "GeometryNodeMeshLine", (bx - 300, by - 300))
    hair.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Hair Resolution"], hair.inputs["Count"])
    hair.inputs["Start Location"].default_value = (-12.5, 0.0, 0.0)
    hair.inputs["Offset"].default_value = (0.8, 0.0, 0.0)

    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 300, by - 480))
    frac = safe_node(tree, "ShaderNodeMath", (bx - 150, by - 480))
    frac.operation = "DIVIDE"
    link_sockets(tree, idx.outputs["Index"], frac.inputs[0])
    link_sockets(tree, gin.outputs["Hair Resolution"], frac.inputs[1])
    sag_t = safe_node(tree, "ShaderNodeMath", (bx, by - 480))
    sag_t.operation = "MULTIPLY"
    link_sockets(tree, frac.outputs[0], sag_t.inputs[0])
    sag_t.inputs[1].default_value = math.pi * 2.0
    sag = safe_node(tree, "ShaderNodeMath", (bx + 150, by - 480))
    sag.operation = "SINE"
    link_sockets(tree, sag_t.outputs[0], sag.inputs[0])
    sag_amp = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 480))
    sag_amp.operation = "MULTIPLY"
    link_sockets(tree, sag.outputs[0], sag_amp.inputs[0])
    sag_amp.inputs[1].default_value = -0.5
    hair_z = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 560))
    hair_z.operation = "MULTIPLY"
    link_sockets(tree, sag_amp.outputs[0], hair_z.inputs[0])
    link_sockets(tree, gin.outputs["Hair Curve Height"], hair_z.inputs[1])

    hair_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 150, by - 300))
    link_sockets(tree, hair.outputs["Mesh"], hair_pos.inputs["Geometry"])
    hair_comb = safe_node(tree, "ShaderNodeCombineXYZ", (bx, by - 380))
    place = safe_node(tree, "GeometryNodeInputPosition", (bx - 320, by - 360))
    place_sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 160, by - 360))
    link_sockets(tree, place.outputs["Position"], place_sep.inputs["Vector"])
    link_sockets(tree, place_sep.outputs["X"], hair_comb.inputs["X"])
    link_sockets(tree, place_sep.outputs["Y"], hair_comb.inputs["Y"])
    link_sockets(tree, hair_z.outputs[0], hair_comb.inputs["Z"])
    link_sockets(tree, hair_comb.outputs["Vector"], hair_pos.inputs["Position"])

    to_curve = safe_node(tree, "GeometryNodeMeshToCurve", (bx, by - 300))
    link_sockets(tree, hair_pos.outputs["Geometry"], to_curve.inputs["Mesh"])
    curve = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 150, by - 300))
    link_sockets(tree, to_curve.outputs["Curve"], curve.inputs["Curve"])
    profile = safe_node(tree, "GeometryNodeMeshCircle", (bx + 100, by - 380))
    profile.inputs["Radius"].default_value = 0.01
    profile.inputs["Vertices"].default_value = 6
    profile.fill_type = "NONE"
    link_sockets(tree, profile.outputs["Mesh"], curve.inputs["Profile Curve"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 300, by))
    link_sockets(tree, stick.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, curve.outputs["Mesh"], join.inputs["Geometry"])

    store_len = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 480, by))
    store_len.data_type = "FLOAT"
    store_len.inputs["Name"].default_value = "bow_length"
    link_sockets(tree, gin.outputs["Bow Length"], store_len.inputs["Value"])
    link_sockets(tree, join.outputs["Geometry"], store_len.inputs["Geometry"])

    store_rosin = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 480, by - 200))
    store_rosin.data_type = "FLOAT"
    store_rosin.inputs["Name"].default_value = "rosin_zone_length"
    link_sockets(tree, gin.outputs["Rosin Zone Length"], store_rosin.inputs["Value"])
    link_sockets(tree, store_len.outputs["Geometry"], store_rosin.inputs["Geometry"])
    link_sockets(tree, store_rosin.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(stick, "geometry")
    color_node(hair_pos, "curve")
    color_node(curve, "geometry")
    color_node(join, "geometry")
    color_node(store_len, "attribute")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Stick", "nodes": ("cylinder",), "role": "geometry"},
        {"title": "Hair", "nodes": ("mesh line", "sine", "curve to mesh"), "role": "curve"},
        {"title": "Attributes", "nodes": ("store",), "role": "attribute"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# -- Registry --
register_builder("MEL_ribbon_curve", build_ribbon_curve, "Ribbon Curve",
    "Sine centerline ribbon strip - width, amplitude, frequency, twist attributes.",
    "effects")
register_builder("MEL_lissajous_ribbon", build_lissajous_ribbon, "Lissajous Ribbon",
    "Lissajous figure ribbon - sin/cos cross path with frequency ratio control.",
    "effects")
register_builder("MEL_closed_ribbon", build_closed_ribbon, "Closed Ribbon",
    "Seamless circular ribbon loop for UI borders and decorative rings.",
    "effects")
register_builder("MEL_violin_bow", build_violin_bow, "Violin Bow",
    "Tapered bow stick with sagging horsehair ribbon and rosin-zone attribute.",
    "music")