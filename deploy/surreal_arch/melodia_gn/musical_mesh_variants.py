"""Musical mesh variants — procedural variant framework for any mesh.

Four builders that take ANY input mesh and create musical-parameter-driven
variants on the fly. Each builder exposes a Variant Count and Variant Seed
so artists can sweep through deterministic permutations instantly.

Offline authoring/bake lane: Unreal remains runtime rhythm authority.
"""

from __future__ import annotations
import math
import bpy
from .core import (
    add_float_param, add_int_param, add_bool_param,
    add_music_influence_params, apply_universal_music_pass,
    color_node, label_tree, link_sockets, new_geometry_tree,
    register_builder, safe_node, sock,
)


# --------------------------------------------------------------------------- #
# Shared: variant-seed permutation
# --------------------------------------------------------------------------- #
def _variant_seed_param(tree):
    add_int_param(tree, "Variant Seed", 0, 0, 999999)
    add_float_param(tree, "Variant Morph", 0.5, 0.0, 1.0)


def _variant_hash(tree, gin, loc):
    """Deterministic 0-1 hash from Variant Seed."""
    seed = sock(gin, "Variant Seed", outputs=True)
    n = safe_node(tree, "ShaderNodeMath", loc)
    if n:
        n.operation = "MULTIPLY"
        link_sockets(tree, seed, n.inputs[0])
        n.inputs[1].default_value = 0.61803398875  # golden ratio hash
    n2 = safe_node(tree, "ShaderNodeMath", (loc[0] + 180, loc[1]))
    if n2:
        n2.operation = "WRAP"
        n2.inputs[1].default_value = 0.0
        n2.inputs[2].default_value = 1.0
        if n:
            link_sockets(tree, n.outputs[0], n2.inputs[0])
    return n2


# --------------------------------------------------------------------------- #
# 1. Wave variant — sine/triangle/sawtooth displacement
# --------------------------------------------------------------------------- #
def build_musical_wave_variant(group_name="MEL_musical_wave_variant"):
    """Displace mesh along a musical waveform (sine/triangle/saw/pulse)."""
    tree, gin, gout = new_geometry_tree(group_name)
    add_int_param(tree, "Waveform", 0, 0, 3)  # 0=sine, 1=tri, 2=saw, 3=pulse
    add_float_param(tree, "Frequency", 2.0, 0.1, 20.0)
    add_float_param(tree, "Amplitude", 0.3, 0.0, 10.0)
    add_int_param(tree, "Axis", 2, 0, 2)  # 0=X, 1=Y, 2=Z
    _variant_seed_param(tree)

    bx, by = 0, 0
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx, by))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx + 200, by))
    link_sockets(tree, sock(pos, "Position", outputs=True), sock(sep, "Vector"))

    # Select axis component based on Axis parameter
    # Use a simple approach: math on each axis, then pick
    phase = _math_chain_phase(tree, gin, sep, (bx + 400, by))

    # Waveform shapes
    sine = _math_sine(tree, phase.outputs[0], (bx + 600, by))
    triangle = _math_triangle(tree, phase.outputs[0], (bx + 600, by - 150))
    saw = _math_saw(tree, phase.outputs[0], (bx + 600, by - 300))
    pulse = _math_pulse(tree, phase.outputs[0], (bx + 600, by - 450))

    # Select waveform by int
    wsel = _int_select_4(tree, gin, sine.outputs[0], triangle.outputs[0],
                          saw.outputs[0], pulse.outputs[0],
                          (bx + 850, by - 200))

    # Scale by amplitude
    scaled = safe_node(tree, "ShaderNodeMath", (bx + 1050, by))
    scaled.operation = "MULTIPLY"
    link_sockets(tree, wsel, scaled.inputs[0])
    link_sockets(tree, sock(gin, "Amplitude", outputs=True), scaled.inputs[1])

    # Build offset vector (select axis)
    zero = safe_node(tree, "ShaderNodeMath", (bx + 850, by + 100))
    zero.operation = "MULTIPLY"
    if zero:
        link_sockets(tree, sock(sep, "X", outputs=True), zero.inputs[0])
        zero.inputs[1].default_value = 0.0  # zero out for now; axis switch below

    offset = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 1200, by))
    # For simplicity: displace along Z (can be extended with axis switch)
    link_sockets(tree, scaled.outputs[0], sock(offset, "Z"))

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 1400, by))
    link_sockets(tree, sock(gin, "Geometry", outputs=True), sock(set_pos, "Geometry"))
    link_sockets(tree, sock(offset, "Vector", outputs=True), sock(set_pos, "Offset"))

    geom = apply_universal_music_pass(tree, gin, sock(set_pos, "Geometry", outputs=True), (bx + 1600, by))
    link_sockets(tree, geom, sock(gout, "Geometry"))

    return label_tree(tree, group_name, [
        {"title": "Position", "nodes": ("position", "separate"), "role": "input"},
        {"title": "Waveform Math", "nodes": ("sine", "triangle", "saw", "pulse"), "role": "math"},
        {"title": "Displace", "nodes": ("scale", "set position"), "role": "geometry"},
    ])


# --------------------------------------------------------------------------- #
# 2. Harmonic variant — multi-frequency harmonic叠加
# --------------------------------------------------------------------------- #
def build_musical_harmonic_variant(group_name="MEL_musical_harmonic_variant"):
    """Multi-frequency harmonic displacement creating complex surface variants."""
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Harmony 1", 1.0, 0.1, 12.0)
    add_float_param(tree, "Harmony 2", 1.5, 0.1, 12.0)
    add_float_param(tree, "Harmony 3", 2.0, 0.1, 12.0)
    add_float_param(tree, "Mix 1", 1.0, 0.0, 1.0)
    add_float_param(tree, "Mix 2", 0.5, 0.0, 1.0)
    add_float_param(tree, "Mix 3", 0.25, 0.0, 1.0)
    add_float_param(tree, "Amplitude", 0.3, 0.0, 10.0)
    _variant_seed_param(tree)

    bx, by = 0, 0
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx, by))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx + 200, by))
    link_sockets(tree, sock(pos, "Position", outputs=True), sock(sep, "Vector"))

    # Phase from position
    phase = safe_node(tree, "ShaderNodeMath", (bx + 400, by))
    phase.operation = "ADD"
    link_sockets(tree, sock(sep, "X", outputs=True), phase.inputs[0])
    link_sockets(tree, sock(sep, "Z", outputs=True), phase.inputs[1])

    # Three harmonics
    h1 = _math_sine_scaled(tree, phase.outputs[0], "Harmony 1", gin, (bx + 600, by))
    h2 = _math_sine_scaled(tree, phase.outputs[0], "Harmony 2", gin, (bx + 600, by - 120))
    h3 = _math_sine_scaled(tree, phase.outputs[0], "Harmony 3", gin, (bx + 600, by - 240))

    # Mix
    mix1 = safe_node(tree, "ShaderNodeMath", (bx + 850, by))
    mix1.operation = "MULTIPLY"
    link_sockets(tree, h1, mix1.inputs[0])
    link_sockets(tree, sock(gin, "Mix 1", outputs=True), mix1.inputs[1])

    mix2 = safe_node(tree, "ShaderNodeMath", (bx + 850, by - 120))
    mix2.operation = "MULTIPLY"
    link_sockets(tree, h2, mix2.inputs[0])
    link_sockets(tree, sock(gin, "Mix 2", outputs=True), mix2.inputs[1])

    mix3 = safe_node(tree, "ShaderNodeMath", (bx + 850, by - 240))
    mix3.operation = "MULTIPLY"
    link_sockets(tree, h3, mix3.inputs[0])
    link_sockets(tree, sock(gin, "Mix 3", outputs=True), mix3.inputs[1])

    # Sum harmonics
    sum1 = safe_node(tree, "ShaderNodeMath", (bx + 1050, by - 60))
    sum1.operation = "ADD"
    link_sockets(tree, mix1.outputs[0], sum1.inputs[0])
    link_sockets(tree, mix2.outputs[0], sum1.inputs[1])

    sum2 = safe_node(tree, "ShaderNodeMath", (bx + 1200, by - 60))
    sum2.operation = "ADD"
    link_sockets(tree, sum1.outputs[0], sum2.inputs[0])
    link_sockets(tree, mix3.outputs[0], sum2.inputs[1])

    # Scale by amplitude
    scaled = safe_node(tree, "ShaderNodeMath", (bx + 1400, by))
    scaled.operation = "MULTIPLY"
    link_sockets(tree, sum2.outputs[0], scaled.inputs[0])
    link_sockets(tree, sock(gin, "Amplitude", outputs=True), scaled.inputs[1])

    # Normal displacement
    normal = safe_node(tree, "GeometryNodeInputNormal", (bx + 1400, by + 150))
    n_scale = safe_node(tree, "ShaderNodeVectorMath", (bx + 1600, by))
    n_scale.operation = "SCALE"
    link_sockets(tree, sock(normal, "Normal", outputs=True), sock(n_scale, "Vector"))
    link_sockets(tree, scaled.outputs[0], sock(n_scale, "Scale"))

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 1800, by))
    link_sockets(tree, sock(gin, "Geometry", outputs=True), sock(set_pos, "Geometry"))
    link_sockets(tree, sock(n_scale, "Vector", outputs=True), sock(set_pos, "Offset"))

    geom = apply_universal_music_pass(tree, gin, sock(set_pos, "Geometry", outputs=True), (bx + 2000, by))
    link_sockets(tree, geom, sock(gout, "Geometry"))

    return label_tree(tree, group_name, [
        {"title": "Position", "nodes": ("position", "separate"), "role": "input"},
        {"title": "Harmonics", "nodes": ("sine", "multiply", "add"), "role": "math"},
        {"title": "Displace", "nodes": ("normal", "scale", "set position"), "role": "geometry"},
    ])


# --------------------------------------------------------------------------- #
# 3. Pulse variant — radial pulse driven by audio envelope
# --------------------------------------------------------------------------- #
def build_musical_pulse_variant(group_name="MEL_musical_pulse_variant"):
    """Radial pulse from mesh centroid, gated by audio amplitude."""
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Pulse Speed", 1.0, 0.1, 10.0)
    add_float_param(tree, "Pulse Width", 0.3, 0.01, 1.0)
    add_float_param(tree, "Amplitude", 0.5, 0.0, 10.0)
    add_float_param(tree, "Decay", 2.0, 0.1, 10.0)
    _variant_seed_param(tree)

    bx, by = 0, 0
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx, by))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx + 200, by))
    link_sockets(tree, sock(pos, "Position", outputs=True), sock(sep, "Vector"))

    # Radial distance from origin (mesh approximate center)
    # For variant on the fly: use bounding box center via InputBoundingBox
    bbox = safe_node(tree, "GeometryNodeBoundBox", (bx, by - 200))
    link_sockets(tree, sock(gin, "Geometry", outputs=True), sock(bbox, "Geometry"))
    bbox_center = safe_node(tree, "ShaderNodeSeparateXYZ", (bx + 200, by - 200))
    link_sockets(tree, sock(bbox, "Center", outputs=True), sock(bbox_center, "Vector"))

    # Delta = position - center
    delta = safe_node(tree, "ShaderNodeVectorMath", (bx + 400, by - 100))
    delta.operation = "SUBTRACT"
    link_sockets(tree, sock(pos, "Position", outputs=True), sock(delta, "Vector"))
    link_sockets(tree, sock(bbox_center, "Vector", outputs=True), sock(delta, "Vector 1"))

    dist = safe_node(tree, "ShaderNodeVectorMath", (bx + 600, by - 100))
    dist.operation = "LENGTH"
    link_sockets(tree, sock(delta, "Vector", outputs=True), sock(dist, "Vector"))

    # Pulse = exp(-decay * |dist - speed*time|)
    # Variant Morph is the phase OFFSET in seconds; scene time is added BEFORE
    # the multiply, so at t = 0 the phase is Variant Morph * Pulse Speed exactly
    # as it was before time existed - Animated off reproduces the old geometry,
    # and the travelling wave the comment above describes actually travels.
    from .time import add_time_to_phase
    phase_offset = add_time_to_phase(
        tree, gin, sock(gin, "Variant Morph", outputs=True), (bx + 700, by - 240))
    pulse_phase = safe_node(tree, "ShaderNodeMath", (bx + 800, by))
    pulse_phase.operation = "MULTIPLY"
    link_sockets(tree, phase_offset, pulse_phase.inputs[0])
    link_sockets(tree, sock(gin, "Pulse Speed", outputs=True), pulse_phase.inputs[1])

    diff = safe_node(tree, "ShaderNodeMath", (bx + 1000, by))
    diff.operation = "SUBTRACT"
    link_sockets(tree, sock(dist, "Value", outputs=True), diff.inputs[0])
    link_sockets(tree, pulse_phase.outputs[0], diff.inputs[1])

    abs_diff = safe_node(tree, "ShaderNodeMath", (bx + 1200, by))
    abs_diff.operation = "ABSOLUTE"
    link_sockets(tree, diff.outputs[0], abs_diff.inputs[0])

    decay = safe_node(tree, "ShaderNodeMath", (bx + 1400, by))
    decay.operation = "MULTIPLY"
    link_sockets(tree, abs_diff.outputs[0], decay.inputs[0])
    link_sockets(tree, sock(gin, "Decay", outputs=True), decay.inputs[1])

    neg = safe_node(tree, "ShaderNodeMath", (bx + 1600, by))
    neg.operation = "MULTIPLY"
    link_sockets(tree, decay.outputs[0], neg.inputs[0])
    neg.inputs[1].default_value = -1.0

    # exp(x) via power(e, x): use POWER with base e
    exp = safe_node(tree, "ShaderNodeMath", (bx + 1800, by))
    exp.operation = "POWER"
    exp.inputs[0].default_value = 2.71828182846
    link_sockets(tree, neg.outputs[0], exp.inputs[1])

    # Scale by amplitude
    scaled = safe_node(tree, "ShaderNodeMath", (bx + 2000, by))
    scaled.operation = "MULTIPLY"
    link_sockets(tree, exp.outputs[0], scaled.inputs[0])
    link_sockets(tree, sock(gin, "Amplitude", outputs=True), scaled.inputs[1])

    # Normal displacement
    normal = safe_node(tree, "GeometryNodeInputNormal", (bx + 1800, by + 150))
    n_scale = safe_node(tree, "ShaderNodeVectorMath", (bx + 2200, by))
    n_scale.operation = "SCALE"
    link_sockets(tree, sock(normal, "Normal", outputs=True), sock(n_scale, "Vector"))
    link_sockets(tree, scaled.outputs[0], sock(n_scale, "Scale"))

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 2400, by))
    link_sockets(tree, sock(gin, "Geometry", outputs=True), sock(set_pos, "Geometry"))
    link_sockets(tree, sock(n_scale, "Vector", outputs=True), sock(set_pos, "Offset"))

    geom = apply_universal_music_pass(tree, gin, sock(set_pos, "Geometry", outputs=True), (bx + 2600, by))
    link_sockets(tree, geom, sock(gout, "Geometry"))

    return label_tree(tree, group_name, [
        {"title": "Radial Distance", "nodes": ("bbox", "position", "subtract", "length"), "role": "attribute"},
        {"title": "Pulse Math", "nodes": ("abs", "decay", "exp"), "role": "math"},
        {"title": "Displace", "nodes": ("normal", "scale", "set position"), "role": "geometry"},
    ])


# --------------------------------------------------------------------------- #
# 4. Seeded variant — deterministic variant sweep ranked by musical params
# --------------------------------------------------------------------------- #
def build_musical_seeded_variant(group_name="MEL_musical_seeded_variant"):
    """Deterministic variant generator: sweep Variant Seed for instant permutations."""
    tree, gin, gout = new_geometry_tree(group_name)
    add_int_param(tree, "Variant Count", 8, 2, 64)
    _variant_seed_param(tree)
    add_float_param(tree, "Displace Amplitude", 0.5, 0.0, 10.0)
    add_float_param(tree, "Twist Amplitude", 0.3, 0.0, 6.28)
    add_float_param(tree, "Noise Scale", 3.0, 0.1, 20.0)

    bx, by = 0, 0
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx, by))

    # Hash for deterministic per-variant randomization
    hash_n = _variant_hash(tree, gin, (bx + 200, by))

    # Three displacement axes from variant hash
    hx = safe_node(tree, "ShaderNodeMath", (bx + 400, by + 50))
    hx.operation = "MULTIPLY"
    if hash_n:
        link_sockets(tree, hash_n.outputs[0], hx.inputs[0])
    hx.inputs[1].default_value = 2.0  # -1 to 1 range
    hx_shift = safe_node(tree, "ShaderNodeMath", (bx + 550, by + 50))
    hx_shift.operation = "ADD"
    link_sockets(tree, hx.outputs[0], hx_shift.inputs[0])
    hx_shift.inputs[1].default_value = -1.0

    hy = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 50))
    hy.operation = "MULTIPLY"
    if hash_n:
        link_sockets(tree, hash_n.outputs[0], hy.inputs[0])
    hy.inputs[1].default_value = 1.7
    hy_shift = safe_node(tree, "ShaderNodeMath", (bx + 550, by - 50))
    hy_shift.operation = "ADD"
    link_sockets(tree, hy.outputs[0], hy_shift.inputs[0])
    hy_shift.inputs[1].default_value = -0.85

    hz = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 150))
    hz.operation = "MULTIPLY"
    if hash_n:
        link_sockets(tree, hash_n.outputs[0], hz.inputs[0])
    hz.inputs[1].default_value = 1.4
    hz_shift = safe_node(tree, "ShaderNodeMath", (bx + 550, by - 150))
    hz_shift.operation = "ADD"
    link_sockets(tree, hz.outputs[0], hz_shift.inputs[0])
    hz_shift.inputs[1].default_value = -0.7

    # Twist: rotate position around Y by hash-driven angle
    angle = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 250))
    angle.operation = "MULTIPLY"
    if hash_n:
        link_sockets(tree, hash_n.outputs[0], angle.inputs[0])
    link_sockets(tree, sock(gin, "Twist Amplitude", outputs=True), angle.inputs[1])

    # Build displacement vector
    offset = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 750, by))
    link_sockets(tree, hx_shift.outputs[0], sock(offset, "X"))
    link_sockets(tree, hy_shift.outputs[0], sock(offset, "Y"))
    link_sockets(tree, hz_shift.outputs[0], sock(offset, "Z"))

    # Scale by amplitude
    scaled = safe_node(tree, "ShaderNodeVectorMath", (bx + 950, by))
    scaled.operation = "SCALE"
    link_sockets(tree, sock(offset, "Vector", outputs=True), sock(scaled, "Vector"))
    link_sockets(tree, sock(gin, "Displace Amplitude", outputs=True), sock(scaled, "Scale"))

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 1150, by))
    link_sockets(tree, sock(gin, "Geometry", outputs=True), sock(set_pos, "Geometry"))
    link_sockets(tree, sock(scaled, "Vector", outputs=True), sock(set_pos, "Offset"))

    geom = apply_universal_music_pass(tree, gin, sock(set_pos, "Geometry", outputs=True), (bx + 1350, by))
    link_sockets(tree, geom, sock(gout, "Geometry"))

    return label_tree(tree, group_name, [
        {"title": "Variant Hash", "nodes": ("hash",), "role": "attribute"},
        {"title": "Displacement Vector", "nodes": ("math", "combine"), "role": "math"},
        {"title": "Apply", "nodes": ("scale", "set position"), "role": "geometry"},
    ])


# --------------------------------------------------------------------------- #
# Math helpers
# --------------------------------------------------------------------------- #
def _math_chain_phase(tree, gin, sep, loc):
    """Compute phase = (X + Z) * Frequency."""
    phase_add = safe_node(tree, "ShaderNodeMath", loc)
    phase_add.operation = "ADD"
    link_sockets(tree, sock(sep, "X", outputs=True), phase_add.inputs[0])
    link_sockets(tree, sock(sep, "Z", outputs=True), phase_add.inputs[1])
    phase = safe_node(tree, "ShaderNodeMath", (loc[0] + 180, loc[1]))
    phase.operation = "MULTIPLY"
    link_sockets(tree, phase_add.outputs[0], phase.inputs[0])
    link_sockets(tree, sock(gin, "Frequency", outputs=True), phase.inputs[1])
    return phase


def _math_sine(tree, input_sock, loc):
    n = safe_node(tree, "ShaderNodeMath", loc)
    n.operation = "SINE"
    if input_sock:
        link_sockets(tree, input_sock, n.inputs[0])
    return n


def _math_sine_scaled(tree, input_sock, param_name, gin, loc):
    """sine(input * param)."""
    mul = safe_node(tree, "ShaderNodeMath", loc)
    mul.operation = "MULTIPLY"
    if input_sock:
        link_sockets(tree, input_sock, mul.inputs[0])
    link_sockets(tree, sock(gin, param_name, outputs=True), mul.inputs[1])
    sine = safe_node(tree, "ShaderNodeMath", (loc[0] + 180, loc[1]))
    sine.operation = "SINE"
    link_sockets(tree, mul.outputs[0], sine.inputs[0])
    return sine


def _math_triangle(tree, input_sock, loc):
    """Triangle wave: abs(2 * (x - floor(x + 0.5)))."""
    floored = safe_node(tree, "ShaderNodeMath", loc)
    floored.operation = "FLOOR"
    if input_sock:
        link_sockets(tree, input_sock, floored.inputs[0])
    add_half = safe_node(tree, "ShaderNodeMath", (loc[0], loc[1] - 80))
    add_half.operation = "ADD"
    if input_sock:
        link_sockets(tree, input_sock, add_half.inputs[0])
    add_half.inputs[1].default_value = 0.5
    diff = safe_node(tree, "ShaderNodeMath", (loc[0] + 150, loc[1] - 40))
    diff.operation = "SUBTRACT"
    link_sockets(tree, input_sock, diff.inputs[0])
    link_sockets(tree, floored.outputs[0], diff.inputs[1])
    mul2 = safe_node(tree, "ShaderNodeMath", (loc[0] + 300, loc[1] - 40))
    mul2.operation = "MULTIPLY"
    link_sockets(tree, diff.outputs[0], mul2.inputs[0])
    mul2.inputs[1].default_value = 2.0
    abs_n = safe_node(tree, "ShaderNodeMath", (loc[0] + 450, loc[1] - 40))
    abs_n.operation = "ABSOLUTE"
    link_sockets(tree, mul2.outputs[0], abs_n.inputs[0])
    return abs_n


def _math_saw(tree, input_sock, loc):
    """Sawtooth: 2 * (x - floor(x + 0.5))."""
    floored = safe_node(tree, "ShaderNodeMath", loc)
    floored.operation = "FLOOR"
    if input_sock:
        link_sockets(tree, input_sock, floored.inputs[0])
    diff = safe_node(tree, "ShaderNodeMath", (loc[0] + 150, loc[1]))
    diff.operation = "SUBTRACT"
    link_sockets(tree, input_sock, diff.inputs[0])
    link_sockets(tree, floored.outputs[0], diff.inputs[1])
    mul2 = safe_node(tree, "ShaderNodeMath", (loc[0] + 300, loc[1]))
    mul2.operation = "MULTIPLY"
    link_sockets(tree, diff.outputs[0], mul2.inputs[0])
    mul2.inputs[1].default_value = 2.0
    return mul2


def _math_pulse(tree, input_sock, loc):
    """Pulse: 1 if sin(x) > 0 else 0."""
    sine = safe_node(tree, "ShaderNodeMath", loc)
    sine.operation = "SINE"
    if input_sock:
        link_sockets(tree, input_sock, sine.inputs[0])
    cmp = safe_node(tree, "FunctionNodeCompare", (loc[0] + 180, loc[1]))
    if cmp:
        cmp.data_type = "FLOAT"
        cmp.operation = "GREATER_THAN"
        link_sockets(tree, sine.outputs[0], sock(cmp, "A"))
        sock(cmp, "B").default_value = 0.0
    return cmp


def _int_select_4(tree, gin, val0, val1, val2, val3, loc):
    """Select one of 4 float values based on Waveform int parameter."""
    sw1 = safe_node(tree, "GeometryNodeSwitch", loc)
    sw1.input_type = "FLOAT"
    cmp0 = safe_node(tree, "FunctionNodeCompare", (loc[0] - 200, loc[1] + 100))
    if cmp0:
        cmp0.data_type = "INT"
        cmp0.operation = "EQUAL"
        link_sockets(tree, sock(gin, "Waveform", outputs=True), sock(cmp0, "A"))
        sock(cmp0, "B").default_value = 0
        link_sockets(tree, sock(cmp0, "Result", outputs=True), sock(sw1, "Switch"))
    if val2:
        link_sockets(tree, val2, sock(sw1, "False"))
    if val0:
        link_sockets(tree, val0, sock(sw1, "True"))

    sw2 = safe_node(tree, "GeometryNodeSwitch", (loc[0], loc[1] - 150))
    sw2.input_type = "FLOAT"
    cmp1 = safe_node(tree, "FunctionNodeCompare", (loc[0] - 200, loc[1] - 50))
    if cmp1:
        cmp1.data_type = "INT"
        cmp1.operation = "EQUAL"
        link_sockets(tree, sock(gin, "Waveform", outputs=True), sock(cmp1, "A"))
        sock(cmp1, "B").default_value = 1
        link_sockets(tree, sock(cmp1, "Result", outputs=True), sock(sw2, "Switch"))
    if val3:
        link_sockets(tree, val3, sock(sw2, "False"))
    if val1:
        link_sockets(tree, val1, sock(sw2, "True"))

    # Combine: if 0/1 use sw1, if 2/3 use sw2
    sw_final = safe_node(tree, "GeometryNodeSwitch", (loc[0] + 200, loc[1] - 75))
    sw_final.input_type = "FLOAT"
    # Use Waveform < 2 as selector
    lt2 = safe_node(tree, "FunctionNodeCompare", (loc[0], loc[1] - 200))
    if lt2:
        lt2.data_type = "INT"
        lt2.operation = "LESS_THAN"
        link_sockets(tree, sock(gin, "Waveform", outputs=True), sock(lt2, "A"))
        sock(lt2, "B").default_value = 2
        link_sockets(tree, sock(lt2, "Result", outputs=True), sock(sw_final, "Switch"))
    link_sockets(tree, sock(sw2, "Output", outputs=True), sock(sw_final, "False"))
    link_sockets(tree, sock(sw1, "Output", outputs=True), sock(sw_final, "True"))

    return sock(sw_final, "Output", outputs=True)


# --------------------------------------------------------------------------- #
# Registration
# --------------------------------------------------------------------------- #
register_builder("MEL_musical_wave_variant", build_musical_wave_variant,
                 "Musical Wave Variant", "Sine/triangle/saw/pulse displacement along axis", "music")
register_builder("MEL_musical_harmonic_variant", build_musical_harmonic_variant,
                 "Musical Harmonic Variant", "Multi-frequency harmonic surface displacement", "music")
register_builder("MEL_musical_pulse_variant", build_musical_pulse_variant,
                 "Musical Pulse Variant", "Radial pulse from mesh centroid", "music")
register_builder("MEL_musical_seeded_variant", build_musical_seeded_variant,
                 "Musical Seeded Variant", "Deterministic variant sweep for instant permutations", "music")
