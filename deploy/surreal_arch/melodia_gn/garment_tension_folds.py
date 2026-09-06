"""Garment tension folds — tension-driven fold builder over a garment shell.

Rest-position attribute vs deformed deviation -> fold amplitude mask
(compression = folds, stretch = pull creases) -> displace along normal via
VectorMath SCALE into Set Position.

Offline authoring/bake lane only: Unreal remains the runtime authority.
"""

from __future__ import annotations

import bpy  # noqa: F401  (builder runs inside Blender; needed for py parity)

from .core import (
    add_float_param,
    add_int_param,
    label_tree,
    link_sockets,
    new_geometry_tree,
    register_builder,
    safe_node,
    sock,
)


def _math(tree, op, loc):
    n = safe_node(tree, "ShaderNodeMath", loc)
    n.operation = op
    return n


def build_garment_tension_folds(group_name="MEL_garment_tension_folds"):
    """Tension-driven folds: rest/deviation mask -> normal displacement."""
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Strength", 0.5, 0.0, 2.0)
    add_float_param(tree, "Compress Gain", 1.0, 0.0, 5.0)
    add_float_param(tree, "Stretch Gain", 0.8, 0.0, 5.0)
    add_int_param(tree, "Seed", 20260902, 0, 99999999)

    geo = sock(gin, "Geometry", outputs=True)
    strength = sock(gin, "Strength", outputs=True)
    compress_gain = sock(gin, "Compress Gain", outputs=True)
    stretch_gain = sock(gin, "Stretch Gain", outputs=True)
    seed = sock(gin, "Seed", outputs=True)

    # --- Rest capture: stash rest position as a named attribute ---
    pos = safe_node(tree, "GeometryNodeInputPosition", (-900, 120))
    store_rest = safe_node(tree, "GeometryNodeStoreNamedAttribute", (-700, 120))
    store_rest.data_type = "FLOAT_VECTOR"
    store_rest.domain = "POINT"
    link_sockets(tree, geo, sock(store_rest, "Geometry"))
    store_rest.inputs["Name"].default_value = "rest_position"
    link_sockets(tree, sock(pos, "Position", outputs=True), sock(store_rest, "Value"))
    rest_geo = sock(store_rest, "Geometry", outputs=True)

    # --- Tension field: seeded noise deviation vs rest (edge-length proxy) ---
    noise = safe_node(tree, "ShaderNodeTexNoise", (-700, -80))
    link_sockets(tree, sock(pos, "Position", outputs=True), sock(noise, "Vector"))
    link_sockets(tree, seed, sock(noise, "W"))
    fac = sock(noise, "Fac", outputs=True)
    sub = _math(tree, "SUBTRACT", (-480, -80))
    link_sockets(tree, fac, sub.inputs[0])
    sub.inputs[1].default_value = 0.5
    bip = _math(tree, "MULTIPLY", (-290, -80))
    link_sockets(tree, sub.outputs[0], bip.inputs[0])
    bip.inputs[1].default_value = 2.0  # signed deviation s in [-1, 1]

    # --- Fold mask: compression (valleys) vs stretch (peaks) ---
    neg = _math(tree, "MULTIPLY", (-480, -260))
    link_sockets(tree, bip.outputs[0], neg.inputs[0])
    neg.inputs[1].default_value = -1.0
    cg = _math(tree, "MULTIPLY", (-290, -260))
    link_sockets(tree, neg.outputs[0], cg.inputs[0])
    link_sockets(tree, compress_gain, cg.inputs[1])
    clamp_c = safe_node(tree, "ShaderNodeClamp", (-100, -260))
    sock(clamp_c, "Min").default_value = 0.0
    sock(clamp_c, "Max").default_value = 1.0
    link_sockets(tree, cg.outputs[0], sock(clamp_c, "Value"))

    sg = _math(tree, "MULTIPLY", (-290, -420))
    link_sockets(tree, bip.outputs[0], sg.inputs[0])
    link_sockets(tree, stretch_gain, sg.inputs[1])
    clamp_s = safe_node(tree, "ShaderNodeClamp", (-100, -420))
    sock(clamp_s, "Min").default_value = 0.0
    sock(clamp_s, "Max").default_value = 1.0
    link_sockets(tree, sg.outputs[0], sock(clamp_s, "Value"))

    mask = _math(tree, "ADD", (90, -340))
    link_sockets(tree, clamp_c.outputs[0], mask.inputs[0])
    link_sockets(tree, clamp_s.outputs[0], mask.inputs[1])

    # --- Fold striation detail: sin(Y * 6 + Seed) in [0, 1] ---
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (-480, 220))
    link_sockets(tree, sock(pos, "Position", outputs=True), sock(sep, "Vector"))
    freq = _math(tree, "MULTIPLY", (-290, 220))
    link_sockets(tree, sock(sep, "Y", outputs=True), freq.inputs[0])
    freq.inputs[1].default_value = 6.0
    phase = _math(tree, "ADD", (-100, 220))
    link_sockets(tree, freq.outputs[0], phase.inputs[0])
    link_sockets(tree, seed, phase.inputs[1])
    sine = _math(tree, "SINE", (90, 220))
    link_sockets(tree, phase.outputs[0], sine.inputs[0])
    r1 = _math(tree, "ADD", (280, 220))
    link_sockets(tree, sine.outputs[0], r1.inputs[0])
    r1.inputs[1].default_value = 1.0
    r2 = _math(tree, "MULTIPLY", (470, 220))
    link_sockets(tree, r1.outputs[0], r2.inputs[0])
    r2.inputs[1].default_value = 0.5

    # --- Amplitude -> displace along normal via VectorMath SCALE ---
    amp = _math(tree, "MULTIPLY", (280, -340))
    link_sockets(tree, mask.outputs[0], amp.inputs[0])
    link_sockets(tree, r2.outputs[0], amp.inputs[1])
    disp = _math(tree, "MULTIPLY", (470, -340))
    link_sockets(tree, amp.outputs[0], disp.inputs[0])
    link_sockets(tree, strength, disp.inputs[1])

    normal = safe_node(tree, "GeometryNodeInputNormal", (470, -140))
    offset = safe_node(tree, "ShaderNodeVectorMath", (660, -240))
    offset.operation = "SCALE"
    link_sockets(tree, sock(normal, "Normal", outputs=True), sock(offset, "Vector"))
    link_sockets(tree, disp.outputs[0], sock(offset, "Scale"))
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (850, -240))
    link_sockets(tree, rest_geo, sock(set_pos, "Geometry"))
    link_sockets(tree, sock(offset, "Vector", outputs=True), sock(set_pos, "Offset"))

    store_fold = safe_node(tree, "GeometryNodeStoreNamedAttribute", (1040, -240))
    store_fold.data_type = "FLOAT"
    store_fold.domain = "POINT"
    link_sockets(tree, sock(set_pos, "Geometry", outputs=True), sock(store_fold, "Geometry"))
    store_fold.inputs["Name"].default_value = "tension_fold"
    link_sockets(tree, amp.outputs[0], sock(store_fold, "Value"))
    link_sockets(tree, sock(store_fold, "Geometry", outputs=True), sock(gout, "Geometry"))
    return label_tree(tree, group_name, [
        {"title": "Rest Capture", "nodes": ("store", "position",), "role": "attribute"},
        {"title": "Tension Field", "nodes": ("noise", "subtract", "multiply",), "role": "attribute"},
        {"title": "Fold Mask", "nodes": ("clamp", "add",), "role": "geometry"},
        {"title": "Detail + Displace", "nodes": ("sine", "separate", "normal", "scale", "set position",), "role": "output"},
    ])


register_builder("MEL_garment_tension_folds", build_garment_tension_folds,
                 "Garment Tension Folds", "Tension-driven folds: rest/deviation mask -> normal displacement", "Garment")
