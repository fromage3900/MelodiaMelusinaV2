"""Advanced audio-reactive Geometry Nodes builders for Melodia Studio.

Five builders extending the audio reactivity system:
  MEL_audio_multiband_decomposition - Multi-band frequency decomposition with per-band displacement
  MEL_audio_waveform_deform       - Waveform-driven mesh deformation (spiral, not just vertical)
  MEL_audio_spectral_ripple       - Spectral ripple effect (radial waves from audio amplitude)
  MEL_audio_emission_pulse        - Audio-reactive material emission strength
  MEL_audio_beat_sync             - Beat-sync pulse (sharp attack, exponential decay)

All use Blender 5.2 native sound sampling via GeometryNodeSampleSoundFrequencies.
Offline authoring lane: Unreal remains the runtime rhythm authority.
"""

from __future__ import annotations

import bpy

from .audio_terrain import _add_sound_param, _sample_band, _store_float
from .core import (
    add_float_param,
    add_int_param,
    add_bool_param,
    add_material_param,
    add_music_influence_params,
    apply_universal_music_pass,
    color_node,
    label_tree,
    link_sockets,
    new_geometry_tree,
    register_builder,
    safe_node,
    sock,
)
from .time import add_time_to_phase, time_seconds


# ---------------------------------------------------------------------------
# Shared audio inputs
# ---------------------------------------------------------------------------

def _audio_inputs_v2(tree):
    """Audio input sockets for v2 builders."""
    _add_sound_param(tree)
    add_float_param(tree, "Time", 0.0, 0.0, 36000.0)
    add_float_param(tree, "Audio Gain", 6.0, 0.0, 100.0)
    add_music_influence_params(tree)


def _create_emission_material(name="MEL_audio_emission_mat"):
    """Create a material with emission driven by audio_amplitude attribute.

    The material uses a ShaderNodeAttribute (GEOMETRY type) to read the stored
    audio_amplitude and drives the Principled BSDF Emission Strength input.
    """
    mat = bpy.data.materials.get(name)
    if mat is not None:
        return mat
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for node in list(nt.nodes):
        nt.nodes.remove(node)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    out.location = (400, 0)
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (100, 0)
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.location = (-200, 100)
    attr.attribute_type = "GEOMETRY"
    attr.attribute_name = "audio_amplitude"
    math_node = nt.nodes.new("ShaderNodeMath")
    math_node.location = (0, 100)
    math_node.operation = "MULTIPLY"
    math_node.inputs[1].default_value = 10.0
    nt.links.new(attr.outputs["Fac"], math_node.inputs[0])
    nt.links.new(math_node.outputs[0], bsdf.inputs["Emission Strength"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


# ---------------------------------------------------------------------------
# 1. MEL_audio_multiband_decomposition
# ---------------------------------------------------------------------------

def build_audio_multiband_decomposition(group_name="MEL_audio_multiband_decomposition"):
    """Multi-band frequency decomposition with per-band displacement.

    Splits audio into low/mid/high bands. Bass (low) pushes vertically,
    mids push radially outward, highs add fine vertical ripple.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    _audio_inputs_v2(tree)

    add_float_param(tree, "Size X M", 40.0, 2.0, 500.0)
    add_float_param(tree, "Size Y M", 40.0, 2.0, 500.0)
    add_int_param(tree, "Resolution X", 129, 9, 513)
    add_int_param(tree, "Resolution Y", 129, 9, 513)
    add_float_param(tree, "Low Hz", 250.0, 20.0, 20000.0)
    add_float_param(tree, "Mid Hz", 2000.0, 100.0, 20000.0)
    add_float_param(tree, "High Hz", 8000.0, 1000.0, 24000.0)
    add_float_param(tree, "High Hz Max", 24000.0, 1000.0, 48000.0)
    add_float_param(tree, "Low Gain", 8.0, 0.0, 100.0)
    add_float_param(tree, "Mid Gain", 4.0, 0.0, 100.0)
    add_float_param(tree, "High Gain", 2.0, 0.0, 100.0)
    add_float_param(tree, "Displacement M", 10.0, 0.0, 200.0)

    # Grid
    grid = safe_node(tree, "GeometryNodeMeshGrid", (-1400, 200))
    link_sockets(tree, gin.outputs["Size X M"], grid.inputs["Size X"])
    link_sockets(tree, gin.outputs["Size Y M"], grid.inputs["Size Y"])
    link_sockets(tree, gin.outputs["Resolution X"], grid.inputs["Vertices X"])
    link_sockets(tree, gin.outputs["Resolution Y"], grid.inputs["Vertices Y"])

    pos = safe_node(tree, "GeometryNodeInputPosition", (-1200, -100))

    # --- Low band (bass) -> vertical displacement ---
    low_amp = _sample_band(tree, gin, (-1000, -300), gin.outputs["Low Hz"], gin.outputs["Mid Hz"],
                           use_scene_time=True)
    low_gain = safe_node(tree, "ShaderNodeMath", (-800, -300))
    low_gain.operation = "MULTIPLY"
    link_sockets(tree, low_amp, low_gain.inputs[0])
    link_sockets(tree, gin.outputs["Low Gain"], low_gain.inputs[1])
    low_disp = safe_node(tree, "ShaderNodeMath", (-600, -300))
    low_disp.operation = "MULTIPLY"
    link_sockets(tree, low_gain.outputs[0], low_disp.inputs[0])
    link_sockets(tree, gin.outputs["Displacement M"], low_disp.inputs[1])

    # --- Mid band -> radial displacement ---
    mid_amp = _sample_band(tree, gin, (-1000, -500), gin.outputs["Mid Hz"], gin.outputs["High Hz"],
                           use_scene_time=True)
    mid_gain = safe_node(tree, "ShaderNodeMath", (-800, -500))
    mid_gain.operation = "MULTIPLY"
    link_sockets(tree, mid_amp, mid_gain.inputs[0])
    link_sockets(tree, gin.outputs["Mid Gain"], mid_gain.inputs[1])
    mid_disp = safe_node(tree, "ShaderNodeMath", (-600, -500))
    mid_disp.operation = "MULTIPLY"
    link_sockets(tree, mid_gain.outputs[0], mid_disp.inputs[0])
    link_sockets(tree, gin.outputs["Displacement M"], mid_disp.inputs[1])

    # --- High band -> fine vertical ripple ---
    high_amp = _sample_band(tree, gin, (-1000, -700), gin.outputs["High Hz"], gin.outputs["High Hz Max"],
                            use_scene_time=True)
    high_gain = safe_node(tree, "ShaderNodeMath", (-800, -700))
    high_gain.operation = "MULTIPLY"
    link_sockets(tree, high_amp, high_gain.inputs[0])
    link_sockets(tree, gin.outputs["High Gain"], high_gain.inputs[1])
    high_disp = safe_node(tree, "ShaderNodeMath", (-600, -700))
    high_disp.operation = "MULTIPLY"
    link_sockets(tree, high_gain.outputs[0], high_disp.inputs[0])
    link_sockets(tree, gin.outputs["Displacement M"], high_disp.inputs[1])

    # --- Combine displacements ---
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (-1000, -900))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    center_x = safe_node(tree, "ShaderNodeMath", (-1200, -1000))
    center_x.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Size X M"], center_x.inputs[0])
    center_x.inputs[1].default_value = -0.5

    center_y = safe_node(tree, "ShaderNodeMath", (-1200, -1100))
    center_y.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Size Y M"], center_y.inputs[0])
    center_y.inputs[1].default_value = -0.5

    rel_x = safe_node(tree, "ShaderNodeMath", (-800, -1000))
    rel_x.operation = "ADD"
    link_sockets(tree, sep.outputs["X"], rel_x.inputs[0])
    link_sockets(tree, center_x.outputs[0], rel_x.inputs[1])

    rel_y = safe_node(tree, "ShaderNodeMath", (-800, -1100))
    rel_y.operation = "ADD"
    link_sockets(tree, sep.outputs["Y"], rel_y.inputs[0])
    link_sockets(tree, center_y.outputs[0], rel_y.inputs[1])

    radial_vec = safe_node(tree, "ShaderNodeCombineXYZ", (-600, -1050))
    link_sockets(tree, rel_x.outputs[0], radial_vec.inputs["X"])
    link_sockets(tree, rel_y.outputs[0], radial_vec.inputs["Y"])
    radial_vec.inputs["Z"].default_value = 0.0

    radial_norm = safe_node(tree, "ShaderNodeVectorMath", (-400, -1050))
    radial_norm.operation = "NORMALIZE"
    link_sockets(tree, radial_vec.outputs["Vector"], radial_norm.inputs[0])

    radial_scaled = safe_node(tree, "ShaderNodeVectorMath", (-200, -1050))
    radial_scaled.operation = "SCALE"
    link_sockets(tree, radial_norm.outputs["Vector"], radial_scaled.inputs[0])
    link_sockets(tree, mid_disp.outputs[0], radial_scaled.inputs["Scale"])

    radial_sep = safe_node(tree, "ShaderNodeSeparateXYZ", (0, -1050))
    link_sockets(tree, radial_scaled.outputs[0], radial_sep.inputs["Vector"])

    z_combined = safe_node(tree, "ShaderNodeMath", (-400, -300))
    z_combined.operation = "ADD"
    link_sockets(tree, low_disp.outputs[0], z_combined.inputs[0])
    link_sockets(tree, high_disp.outputs[0], z_combined.inputs[1])

    offset = safe_node(tree, "ShaderNodeCombineXYZ", (200, -500))
    link_sockets(tree, radial_sep.outputs["X"], offset.inputs["X"])
    link_sockets(tree, radial_sep.outputs["Y"], offset.inputs["Y"])
    link_sockets(tree, z_combined.outputs[0], offset.inputs["Z"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (600, 100))
    link_sockets(tree, grid.outputs["Mesh"], set_pos.inputs["Geometry"])
    link_sockets(tree, offset.outputs["Vector"], set_pos.inputs["Offset"])

    geom = _store_float(tree, set_pos.outputs["Geometry"], "audio_amplitude", low_gain.outputs[0], (800, 100))
    geom = _store_float(tree, geom, "audio_mid", mid_gain.outputs[0], (1000, 100))
    geom = _store_float(tree, geom, "audio_high", high_gain.outputs[0], (1200, 100))
    geom = apply_universal_music_pass(tree, gin, geom, (1400, 100))
    link_sockets(tree, geom, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Grid", "nodes": ("grid",), "role": "geometry"},
        {"title": "Low Band", "nodes": ("low",), "role": "attribute"},
        {"title": "Mid Band", "nodes": ("mid",), "role": "attribute"},
        {"title": "High Band", "nodes": ("high",), "role": "attribute"},
        {"title": "Displacement", "nodes": ("set position",), "role": "geometry"},
        {"title": "Export", "nodes": ("store", "music pass"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# 2. MEL_audio_waveform_deform
# ---------------------------------------------------------------------------

def build_audio_waveform_deform(group_name="MEL_audio_waveform_deform"):
    """Waveform-driven mesh deformation (spiral, not just vertical).

    Uses audio amplitude to drive a spiral deformation pattern.
    X/Y displacement follows cos/sin of angle, Z follows amplitude directly.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    _audio_inputs_v2(tree)

    add_float_param(tree, "Size X M", 40.0, 2.0, 500.0)
    add_float_param(tree, "Size Y M", 40.0, 2.0, 500.0)
    add_int_param(tree, "Resolution X", 129, 9, 513)
    add_int_param(tree, "Resolution Y", 129, 9, 513)
    add_float_param(tree, "Low Hz", 60.0, 20.0, 20000.0)
    add_float_param(tree, "High Hz", 12000.0, 100.0, 24000.0)
    add_float_param(tree, "Spiral Turns", 3.0, 0.0, 20.0)
    add_float_param(tree, "Displacement M", 5.0, 0.0, 100.0)

    # Grid
    grid = safe_node(tree, "GeometryNodeMeshGrid", (-1200, 200))
    link_sockets(tree, gin.outputs["Size X M"], grid.inputs["Size X"])
    link_sockets(tree, gin.outputs["Size Y M"], grid.inputs["Size Y"])
    link_sockets(tree, gin.outputs["Resolution X"], grid.inputs["Vertices X"])
    link_sockets(tree, gin.outputs["Resolution Y"], grid.inputs["Vertices Y"])

    pos = safe_node(tree, "GeometryNodeInputPosition", (-1000, -100))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (-800, -100))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    # Center offset
    center_x = safe_node(tree, "ShaderNodeMath", (-1000, -260))
    center_x.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Size X M"], center_x.inputs[0])
    center_x.inputs[1].default_value = -0.5

    center_y = safe_node(tree, "ShaderNodeMath", (-1000, -360))
    center_y.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Size Y M"], center_y.inputs[0])
    center_y.inputs[1].default_value = -0.5

    rel_x = safe_node(tree, "ShaderNodeMath", (-600, -260))
    rel_x.operation = "ADD"
    link_sockets(tree, sep.outputs["X"], rel_x.inputs[0])
    link_sockets(tree, center_x.outputs[0], rel_x.inputs[1])

    rel_y = safe_node(tree, "ShaderNodeMath", (-600, -360))
    rel_y.operation = "ADD"
    link_sockets(tree, sep.outputs["Y"], rel_y.inputs[0])
    link_sockets(tree, center_y.outputs[0], rel_y.inputs[1])

    # Angle from center
    angle = safe_node(tree, "ShaderNodeMath", (-400, -300))
    angle.operation = "ARCTAN2"
    link_sockets(tree, rel_y.outputs[0], angle.inputs[0])
    link_sockets(tree, rel_x.outputs[0], angle.inputs[1])

    # Spiral phase
    spiral = safe_node(tree, "ShaderNodeMath", (-200, -300))
    spiral.operation = "MULTIPLY"
    link_sockets(tree, angle.outputs[0], spiral.inputs[0])
    link_sockets(tree, gin.outputs["Spiral Turns"], spiral.inputs[1])

    # Audio amplitude
    amp = _sample_band(tree, gin, (-400, -500), gin.outputs["Low Hz"], gin.outputs["High Hz"],
                       use_scene_time=True)
    gain = safe_node(tree, "ShaderNodeMath", (-200, -500))
    gain.operation = "MULTIPLY"
    link_sockets(tree, amp, gain.inputs[0])
    link_sockets(tree, gin.outputs["Audio Gain"], gain.inputs[1])
    disp = safe_node(tree, "ShaderNodeMath", (0, -500))
    disp.operation = "MULTIPLY"
    link_sockets(tree, gain.outputs[0], disp.inputs[0])
    link_sockets(tree, gin.outputs["Displacement M"], disp.inputs[1])

    # Spiral displacement
    cos_a = safe_node(tree, "ShaderNodeMath", (0, -300))
    cos_a.operation = "COSINE"
    link_sockets(tree, spiral.outputs[0], cos_a.inputs[0])

    sin_a = safe_node(tree, "ShaderNodeMath", (0, -200))
    sin_a.operation = "SINE"
    link_sockets(tree, spiral.outputs[0], sin_a.inputs[0])

    x_disp = safe_node(tree, "ShaderNodeMath", (200, -300))
    x_disp.operation = "MULTIPLY"
    link_sockets(tree, cos_a.outputs[0], x_disp.inputs[0])
    link_sockets(tree, disp.outputs[0], x_disp.inputs[1])

    y_disp = safe_node(tree, "ShaderNodeMath", (200, -200))
    y_disp.operation = "MULTIPLY"
    link_sockets(tree, sin_a.outputs[0], y_disp.inputs[0])
    link_sockets(tree, disp.outputs[0], y_disp.inputs[1])

    offset = safe_node(tree, "ShaderNodeCombineXYZ", (400, -300))
    link_sockets(tree, x_disp.outputs[0], offset.inputs["X"])
    link_sockets(tree, y_disp.outputs[0], offset.inputs["Y"])
    link_sockets(tree, disp.outputs[0], offset.inputs["Z"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (600, 100))
    link_sockets(tree, grid.outputs["Mesh"], set_pos.inputs["Geometry"])
    link_sockets(tree, offset.outputs["Vector"], set_pos.inputs["Offset"])

    geom = _store_float(tree, set_pos.outputs["Geometry"], "audio_amplitude", gain.outputs[0], (800, 100))
    geom = apply_universal_music_pass(tree, gin, geom, (1000, 100))
    link_sockets(tree, geom, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Grid", "nodes": ("grid",), "role": "geometry"},
        {"title": "Spiral", "nodes": ("angle", "spiral"), "role": "math"},
        {"title": "Audio", "nodes": ("sample sound",), "role": "attribute"},
        {"title": "Displacement", "nodes": ("set position",), "role": "geometry"},
        {"title": "Export", "nodes": ("store", "music pass"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# 3. MEL_audio_spectral_ripple
# ---------------------------------------------------------------------------

def build_audio_spectral_ripple(group_name="MEL_audio_spectral_ripple"):
    """Spectral ripple effect (radial waves from audio amplitude).

    Creates concentric rings of displacement based on distance from center
    modulated by audio amplitude. The rings breathe with the music.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    _audio_inputs_v2(tree)

    add_float_param(tree, "Size X M", 60.0, 2.0, 500.0)
    add_float_param(tree, "Size Y M", 60.0, 2.0, 500.0)
    add_int_param(tree, "Resolution X", 192, 9, 513)
    add_int_param(tree, "Resolution Y", 192, 9, 513)
    add_float_param(tree, "Low Hz", 60.0, 20.0, 20000.0)
    add_float_param(tree, "High Hz", 12000.0, 100.0, 24000.0)
    add_float_param(tree, "Ripple Frequency", 8.0, 0.5, 50.0)
    add_float_param(tree, "Ripple Phase", 0.0, 0.0, 6.28318)
    add_float_param(tree, "Displacement M", 8.0, 0.0, 100.0)

    # Grid
    grid = safe_node(tree, "GeometryNodeMeshGrid", (-1200, 200))
    link_sockets(tree, gin.outputs["Size X M"], grid.inputs["Size X"])
    link_sockets(tree, gin.outputs["Size Y M"], grid.inputs["Size Y"])
    link_sockets(tree, gin.outputs["Resolution X"], grid.inputs["Vertices X"])
    link_sockets(tree, gin.outputs["Resolution Y"], grid.inputs["Vertices Y"])

    pos = safe_node(tree, "GeometryNodeInputPosition", (-1000, -100))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (-800, -100))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    # Center offset
    center_x = safe_node(tree, "ShaderNodeMath", (-1000, -260))
    center_x.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Size X M"], center_x.inputs[0])
    center_x.inputs[1].default_value = -0.5

    center_y = safe_node(tree, "ShaderNodeMath", (-1000, -360))
    center_y.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Size Y M"], center_y.inputs[0])
    center_y.inputs[1].default_value = -0.5

    rel_x = safe_node(tree, "ShaderNodeMath", (-600, -260))
    rel_x.operation = "ADD"
    link_sockets(tree, sep.outputs["X"], rel_x.inputs[0])
    link_sockets(tree, center_x.outputs[0], rel_x.inputs[1])

    rel_y = safe_node(tree, "ShaderNodeMath", (-600, -360))
    rel_y.operation = "ADD"
    link_sockets(tree, sep.outputs["Y"], rel_y.inputs[0])
    link_sockets(tree, center_y.outputs[0], rel_y.inputs[1])

    # Distance from center
    dist_sq = safe_node(tree, "ShaderNodeMath", (-400, -300))
    dist_sq.operation = "MULTIPLY"
    link_sockets(tree, rel_x.outputs[0], dist_sq.inputs[0])
    link_sockets(tree, rel_x.outputs[0], dist_sq.inputs[1])

    dist_sq2 = safe_node(tree, "ShaderNodeMath", (-400, -400))
    dist_sq2.operation = "MULTIPLY"
    link_sockets(tree, rel_y.outputs[0], dist_sq2.inputs[0])
    link_sockets(tree, rel_y.outputs[0], dist_sq2.inputs[1])

    dist_sum = safe_node(tree, "ShaderNodeMath", (-200, -350))
    dist_sum.operation = "ADD"
    link_sockets(tree, dist_sq.outputs[0], dist_sum.inputs[0])
    link_sockets(tree, dist_sq2.outputs[0], dist_sum.inputs[1])

    dist = safe_node(tree, "ShaderNodeMath", (0, -350))
    dist.operation = "SQRT"
    link_sockets(tree, dist_sum.outputs[0], dist.inputs[0])

    # Ripple phase = distance * frequency + time_phase
    ripple_phase = safe_node(tree, "ShaderNodeMath", (200, -350))
    ripple_phase.operation = "MULTIPLY"
    link_sockets(tree, dist.outputs[0], ripple_phase.inputs[0])
    link_sockets(tree, gin.outputs["Ripple Frequency"], ripple_phase.inputs[1])

    # Add time-based phase animation
    t_phase = add_time_to_phase(tree, gin, ripple_phase.outputs[0], (400, -350))

    # Sine wave
    sine_wave = safe_node(tree, "ShaderNodeMath", (600, -350))
    sine_wave.operation = "SINE"
    link_sockets(tree, t_phase, sine_wave.inputs[0])

    # Audio amplitude
    amp = _sample_band(tree, gin, (-400, -500), gin.outputs["Low Hz"], gin.outputs["High Hz"],
                       use_scene_time=True)
    gain = safe_node(tree, "ShaderNodeMath", (-200, -500))
    gain.operation = "MULTIPLY"
    link_sockets(tree, amp, gain.inputs[0])
    link_sockets(tree, gin.outputs["Audio Gain"], gain.inputs[1])

    # Displacement = sine_wave * amplitude * displacement
    disp = safe_node(tree, "ShaderNodeMath", (800, -400))
    disp.operation = "MULTIPLY"
    link_sockets(tree, sine_wave.outputs[0], disp.inputs[0])
    link_sockets(tree, gain.outputs[0], disp.inputs[1])

    disp2 = safe_node(tree, "ShaderNodeMath", (1000, -400))
    disp2.operation = "MULTIPLY"
    link_sockets(tree, disp.outputs[0], disp2.inputs[0])
    link_sockets(tree, gin.outputs["Displacement M"], disp2.inputs[1])

    offset = safe_node(tree, "ShaderNodeCombineXYZ", (1200, -300))
    offset.inputs["X"].default_value = 0.0
    offset.inputs["Y"].default_value = 0.0
    link_sockets(tree, disp2.outputs[0], offset.inputs["Z"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (1400, 100))
    link_sockets(tree, grid.outputs["Mesh"], set_pos.inputs["Geometry"])
    link_sockets(tree, offset.outputs["Vector"], set_pos.inputs["Offset"])

    geom = _store_float(tree, set_pos.outputs["Geometry"], "audio_amplitude", gain.outputs[0], (1600, 100))
    geom = _store_float(tree, geom, "ripple_phase", ripple_phase.outputs[0], (1800, 100))
    geom = apply_universal_music_pass(tree, gin, geom, (2000, 100))
    link_sockets(tree, geom, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Grid", "nodes": ("grid",), "role": "geometry"},
        {"title": "Distance", "nodes": ("dist",), "role": "math"},
        {"title": "Ripple", "nodes": ("sine", "phase"), "role": "math"},
        {"title": "Audio", "nodes": ("sample sound",), "role": "attribute"},
        {"title": "Displacement", "nodes": ("set position",), "role": "geometry"},
        {"title": "Export", "nodes": ("store", "music pass"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# 4. MEL_audio_emission_pulse
# ---------------------------------------------------------------------------

def build_audio_emission_pulse(group_name="MEL_audio_emission_pulse"):
    """Audio-reactive material emission strength.

    Creates a grid mesh with a material whose emission strength is driven
    by the stored audio_amplitude attribute. The material uses a Named
    Attribute node to read the amplitude and modulate emission.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    _audio_inputs_v2(tree)

    add_float_param(tree, "Size X M", 30.0, 2.0, 500.0)
    add_float_param(tree, "Size Y M", 30.0, 2.0, 500.0)
    add_int_param(tree, "Resolution X", 65, 9, 257)
    add_int_param(tree, "Resolution Y", 65, 9, 257)
    add_float_param(tree, "Low Hz", 60.0, 20.0, 20000.0)
    add_float_param(tree, "High Hz", 12000.0, 100.0, 24000.0)
    add_float_param(tree, "Emission Multiplier", 10.0, 0.0, 100.0)
    add_float_param(tree, "Base Emission", 0.1, 0.0, 10.0)
    add_float_param(tree, "Displacement M", 2.0, 0.0, 50.0)

    # Grid
    grid = safe_node(tree, "GeometryNodeMeshGrid", (-1200, 200))
    link_sockets(tree, gin.outputs["Size X M"], grid.inputs["Size X"])
    link_sockets(tree, gin.outputs["Size Y M"], grid.inputs["Size Y"])
    link_sockets(tree, gin.outputs["Resolution X"], grid.inputs["Vertices X"])
    link_sockets(tree, gin.outputs["Resolution Y"], grid.inputs["Vertices Y"])

    # Audio amplitude
    amp = _sample_band(tree, gin, (-1000, -300), gin.outputs["Low Hz"], gin.outputs["High Hz"],
                       use_scene_time=True)
    gain = safe_node(tree, "ShaderNodeMath", (-800, -300))
    gain.operation = "MULTIPLY"
    link_sockets(tree, amp, gain.inputs[0])
    link_sockets(tree, gin.outputs["Audio Gain"], gain.inputs[1])
    disp = safe_node(tree, "ShaderNodeMath", (-600, -300))
    disp.operation = "MULTIPLY"
    link_sockets(tree, gain.outputs[0], disp.inputs[0])
    link_sockets(tree, gin.outputs["Displacement M"], disp.inputs[1])

    offset = safe_node(tree, "ShaderNodeCombineXYZ", (-400, -300))
    offset.inputs["X"].default_value = 0.0
    offset.inputs["Y"].default_value = 0.0
    link_sockets(tree, disp.outputs[0], offset.inputs["Z"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (-200, 100))
    link_sockets(tree, grid.outputs["Mesh"], set_pos.inputs["Geometry"])
    link_sockets(tree, offset.outputs["Vector"], set_pos.inputs["Offset"])

    # Store audio amplitude as attribute for material to read
    geom = _store_float(tree, set_pos.outputs["Geometry"], "audio_amplitude", gain.outputs[0], (0, 100))

    # Create and assign emission material
    em_mat = _create_emission_material()
    set_mat = safe_node(tree, "GeometryNodeSetMaterial", (200, 100))
    color_node(set_mat, "material")
    link_sockets(tree, geom, set_mat.inputs["Geometry"])
    try:
        set_mat.inputs["Material"].default_value = em_mat
    except Exception:
        pass

    geom = apply_universal_music_pass(tree, gin, set_mat.outputs["Geometry"], (400, 100))
    link_sockets(tree, geom, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Grid", "nodes": ("grid",), "role": "geometry"},
        {"title": "Audio", "nodes": ("sample sound",), "role": "attribute"},
        {"title": "Displacement", "nodes": ("set position",), "role": "geometry"},
        {"title": "Material", "nodes": ("set material",), "role": "material"},
        {"title": "Export", "nodes": ("music pass",), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# 5. MEL_audio_beat_sync
# ---------------------------------------------------------------------------

def build_audio_beat_sync(group_name="MEL_audio_beat_sync"):
    """Beat-sync pulse (sharp attack, exponential decay).

    Uses a power function to sharpen the audio envelope into a pulse.
    The result has a sharp attack and decay that follows the beat.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    _audio_inputs_v2(tree)

    add_float_param(tree, "Size X M", 50.0, 2.0, 500.0)
    add_float_param(tree, "Size Y M", 50.0, 2.0, 500.0)
    add_int_param(tree, "Resolution X", 129, 9, 513)
    add_int_param(tree, "Resolution Y", 129, 9, 513)
    add_float_param(tree, "Low Hz", 60.0, 20.0, 20000.0)
    add_float_param(tree, "High Hz", 12000.0, 100.0, 24000.0)
    add_float_param(tree, "Beat Power", 3.0, 1.0, 10.0)
    add_float_param(tree, "Beat Threshold", 0.0, 0.0, 1.0)
    add_float_param(tree, "Displacement M", 15.0, 0.0, 200.0)

    # Grid
    grid = safe_node(tree, "GeometryNodeMeshGrid", (-1200, 200))
    link_sockets(tree, gin.outputs["Size X M"], grid.inputs["Size X"])
    link_sockets(tree, gin.outputs["Size Y M"], grid.inputs["Size Y"])
    link_sockets(tree, gin.outputs["Resolution X"], grid.inputs["Vertices X"])
    link_sockets(tree, gin.outputs["Resolution Y"], grid.inputs["Vertices Y"])

    # Audio amplitude
    amp = _sample_band(tree, gin, (-1000, -300), gin.outputs["Low Hz"], gin.outputs["High Hz"],
                       use_scene_time=True)
    gain = safe_node(tree, "ShaderNodeMath", (-800, -300))
    gain.operation = "MULTIPLY"
    link_sockets(tree, amp, gain.inputs[0])
    link_sockets(tree, gin.outputs["Audio Gain"], gain.inputs[1])

    # Apply power function to sharpen attack
    # pulse = amplitude^power
    power_node = safe_node(tree, "ShaderNodeMath", (-600, -300))
    power_node.operation = "POWER"
    link_sockets(tree, gain.outputs[0], power_node.inputs[0])
    link_sockets(tree, gin.outputs["Beat Power"], power_node.inputs[1])

    # Map range to control output
    map_range = safe_node(tree, "ShaderNodeMapRange", (-400, -300))
    map_range.clamp = True
    link_sockets(tree, power_node.outputs[0], map_range.inputs["Value"])
    link_sockets(tree, gin.outputs["Beat Threshold"], map_range.inputs["From Min"])
    map_range.inputs["From Max"].default_value = 1.0
    map_range.inputs["To Min"].default_value = 0.0
    map_range.inputs["To Max"].default_value = 1.0

    # Displacement
    disp = safe_node(tree, "ShaderNodeMath", (-200, -300))
    disp.operation = "MULTIPLY"
    link_sockets(tree, map_range.outputs["Result"], disp.inputs[0])
    link_sockets(tree, gin.outputs["Displacement M"], disp.inputs[1])

    offset = safe_node(tree, "ShaderNodeCombineXYZ", (0, -300))
    offset.inputs["X"].default_value = 0.0
    offset.inputs["Y"].default_value = 0.0
    link_sockets(tree, disp.outputs[0], offset.inputs["Z"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (200, 100))
    link_sockets(tree, grid.outputs["Mesh"], set_pos.inputs["Geometry"])
    link_sockets(tree, offset.outputs["Vector"], set_pos.inputs["Offset"])

    geom = _store_float(tree, set_pos.outputs["Geometry"], "audio_amplitude", gain.outputs[0], (400, 100))
    geom = _store_float(tree, geom, "beat_pulse", map_range.outputs["Result"], (600, 100))
    geom = apply_universal_music_pass(tree, gin, geom, (800, 100))
    link_sockets(tree, geom, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Grid", "nodes": ("grid",), "role": "geometry"},
        {"title": "Audio", "nodes": ("sample sound",), "role": "attribute"},
        {"title": "Beat Detect", "nodes": ("power", "map range"), "role": "math"},
        {"title": "Displacement", "nodes": ("set position",), "role": "geometry"},
        {"title": "Export", "nodes": ("store", "music pass"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder(
    "MEL_audio_multiband_decomposition",
    build_audio_multiband_decomposition,
    "Audio Multiband Decomposition",
    "Multi-band frequency decomposition with per-band displacement (low/mid/high)",
    "music",
)

register_builder(
    "MEL_audio_waveform_deform",
    build_audio_waveform_deform,
    "Audio Waveform Deform",
    "Waveform-driven mesh deformation with spiral pattern (not just vertical)",
    "music",
)

register_builder(
    "MEL_audio_spectral_ripple",
    build_audio_spectral_ripple,
    "Audio Spectral Ripple",
    "Spectral ripple effect with radial waves from audio amplitude",
    "music",
)

register_builder(
    "MEL_audio_emission_pulse",
    build_audio_emission_pulse,
    "Audio Emission Pulse",
    "Audio-reactive material emission strength driven by audio amplitude",
    "music",
)

register_builder(
    "MEL_audio_beat_sync",
    build_audio_beat_sync,
    "Audio Beat Sync",
    "Beat-sync pulse with sharp attack and exponential decay",
    "music",
)
