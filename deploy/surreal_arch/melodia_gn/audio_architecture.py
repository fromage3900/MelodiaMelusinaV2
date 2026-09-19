"""Blender 5.2 audio-reactive architecture for Meludia Studio.

Two builders for Melusina's study context:
  MEL_audio_facade   - building facade with window panels that displace by frequency band
  MEL_audio_landscape - terrain that displaces based on audio, reusing planetary schema

Both reuse the existing audio schema from audio_terrain.py (_sample_band, _store_float,
_add_sound_param). Offline authoring lane: Unreal remains runtime rhythm authority.
"""

from __future__ import annotations

from .audio_terrain import _add_sound_param, _sample_band, _store_float
from .core import (
    add_float_param,
    add_int_param,
    add_music_influence_params,
    apply_universal_music_pass,
    label_tree,
    link_sockets,
    new_geometry_tree,
    register_builder,
    safe_node,
)


# ---------------------------------------------------------------------------
# Shared audio inputs (same schema as audio_terrain.py)
# ---------------------------------------------------------------------------

def _audio_inputs(tree):
    _add_sound_param(tree)
    add_float_param(tree, "Time", 0.0, 0.0, 36000.0)
    add_float_param(tree, "Low Hz", 60.0, 0.0, 20000.0)
    add_float_param(tree, "High Hz", 8000.0, 1.0, 24000.0)
    add_float_param(tree, "Band Width", 0.1, 0.001, 1.0)
    add_float_param(tree, "Audio Gain", 12.0, 0.0, 100.0)
    add_music_influence_params(tree)


# ---------------------------------------------------------------------------
# MEL_audio_facade
# ---------------------------------------------------------------------------

def build_audio_facade(group_name="MEL_audio_facade"):
    """Building facade with window panels that displace by frequency band.

    Grid of floors x bays. Each window panel pushes outward based on the
    amplitude of its mapped frequency band. Mullions stay fixed; only the
    glass breathes with the music.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    _audio_inputs(tree)

    add_float_param(tree, "Facade Width M", 12.0, 2.0, 60.0)
    add_float_param(tree, "Facade Height M", 6.0, 2.0, 30.0)
    add_int_param(tree, "Floors", 3, 1, 12)
    add_int_param(tree, "Bays", 4, 1, 20)
    add_float_param(tree, "Mullion Width M", 0.08, 0.02, 0.4)
    add_float_param(tree, "Wall Thickness M", 0.15, 0.05, 0.6)
    add_float_param(tree, "Window Displace M", 0.35, 0.0, 2.0)

    # --- Base wall: grid of floors x bays ---
    grid = safe_node(tree, "GeometryNodeMeshGrid", (-1200, 200))
    link_sockets(tree, gin.outputs["Bays"], grid.inputs["Vertices X"])
    link_sockets(tree, gin.outputs["Floors"], grid.inputs["Vertices Y"])

    cell_w = safe_node(tree, "ShaderNodeMath", (-1400, 300))
    cell_w.operation = "DIVIDE"
    link_sockets(tree, gin.outputs["Facade Width M"], cell_w.inputs[0])
    link_sockets(tree, gin.outputs["Bays"], cell_w.inputs[1])

    cell_h = safe_node(tree, "ShaderNodeMath", (-1400, 180))
    cell_h.operation = "DIVIDE"
    link_sockets(tree, gin.outputs["Facade Height M"], cell_h.inputs[0])
    link_sockets(tree, gin.outputs["Floors"], cell_h.inputs[1])

    cell_vec = safe_node(tree, "ShaderNodeCombineXYZ", (-1200, 340))
    link_sockets(tree, cell_w.outputs[0], cell_vec.inputs["X"])
    link_sockets(tree, cell_h.outputs[0], cell_vec.inputs["Y"])
    link_sockets(tree, cell_w.outputs[0], grid.inputs["Size X"])
    link_sockets(tree, cell_h.outputs[0], grid.inputs["Size Y"])

    # --- Position for frequency mapping ---
    pos = safe_node(tree, "GeometryNodeInputPosition", (-1000, -100))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (-800, -100))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    # Map X position to frequency band
    span_x = safe_node(tree, "ShaderNodeMath", (-1000, -260))
    span_x.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Facade Width M"], span_x.inputs[0])
    span_x.inputs[1].default_value = 0.5
    neg_span = safe_node(tree, "ShaderNodeMath", (-800, -260))
    neg_span.operation = "MULTIPLY"
    link_sockets(tree, span_x.outputs[0], neg_span.inputs[0])
    neg_span.inputs[1].default_value = -1.0

    map_low = safe_node(tree, "ShaderNodeMapRange", (-600, -180))
    map_low.clamp = True
    link_sockets(tree, sep.outputs["X"], map_low.inputs["Value"])
    link_sockets(tree, neg_span.outputs[0], map_low.inputs["From Min"])
    link_sockets(tree, span_x.outputs[0], map_low.inputs["From Max"])
    link_sockets(tree, gin.outputs["Low Hz"], map_low.inputs["To Min"])
    link_sockets(tree, gin.outputs["High Hz"], map_low.inputs["To Max"])

    bw = safe_node(tree, "ShaderNodeMath", (-400, -260))
    bw.operation = "MULTIPLY"
    link_sockets(tree, map_low.outputs["Result"], bw.inputs[0])
    link_sockets(tree, gin.outputs["Band Width"], bw.inputs[1])
    band_high = safe_node(tree, "ShaderNodeMath", (-200, -180))
    band_high.operation = "ADD"
    link_sockets(tree, map_low.outputs["Result"], band_high.inputs[0])
    link_sockets(tree, bw.outputs[0], band_high.inputs[1])

    # Sample the band
    amp = _sample_band(tree, gin, (0, -120), map_low.outputs["Result"], band_high.outputs[0],
                       use_scene_time=True)
    gain = safe_node(tree, "ShaderNodeMath", (200, -120))
    gain.operation = "MULTIPLY"
    link_sockets(tree, amp, gain.inputs[0])
    link_sockets(tree, gin.outputs["Audio Gain"], gain.inputs[1])

    # Displacement = amp * gain * Window Displace
    disp = safe_node(tree, "ShaderNodeMath", (400, -120))
    disp.operation = "MULTIPLY"
    link_sockets(tree, gain.outputs[0], disp.inputs[0])
    link_sockets(tree, gin.outputs["Window Displace M"], disp.inputs[1])

    # Offset along Z (outward from wall)
    offset = safe_node(tree, "ShaderNodeCombineXYZ", (600, -120))
    link_sockets(tree, disp.outputs[0], offset.inputs["Z"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (800, 100))
    link_sockets(tree, grid.outputs["Mesh"], set_pos.inputs["Geometry"])
    link_sockets(tree, offset.outputs["Vector"], set_pos.inputs["Offset"])

    # Store audio amplitude attribute for UE materials
    geom = _store_float(tree, set_pos.outputs["Geometry"], "audio_amplitude", gain.outputs[0], (1000, 100))
    geom = _store_float(tree, geom, "frequency_hz", map_low.outputs["Result"], (1200, 100))
    geom = apply_universal_music_pass(tree, gin, geom, (1400, 100))
    link_sockets(tree, geom, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Facade Grid", "nodes": ("grid", "cell size"), "role": "geometry"},
        {"title": "Frequency Map", "nodes": ("map range", "band width"), "role": "attribute"},
        {"title": "Audio Displace", "nodes": ("sample sound", "set position"), "role": "geometry"},
        {"title": "Export", "nodes": ("store", "music pass"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_audio_landscape
# ---------------------------------------------------------------------------

def build_audio_landscape(group_name="MEL_audio_landscape"):
    """Terrain that displaces based on audio amplitude.

    Reuses the planetary terrain noise-layer schema (macro/mid/micro) but
    adds a broad-band audio displacement term. The terrain breathes with
    the music — bass pushes the ground up, treble adds fine ripple.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    _audio_inputs(tree)

    add_float_param(tree, "Size X M", 40.0, 4.0, 500.0)
    add_float_param(tree, "Size Y M", 40.0, 4.0, 500.0)
    add_int_param(tree, "Resolution X", 129, 9, 513)
    add_int_param(tree, "Resolution Y", 129, 9, 513)
    add_float_param(tree, "Macro Height M", 8.0, 0.0, 200.0)
    add_float_param(tree, "Macro Scale M", 120.0, 1.0, 2000.0)
    add_float_param(tree, "Mid Height M", 3.0, 0.0, 100.0)
    add_float_param(tree, "Mid Scale M", 30.0, 0.2, 500.0)
    add_float_param(tree, "Micro Height M", 0.8, 0.0, 50.0)
    add_float_param(tree, "Micro Scale M", 6.0, 0.1, 100.0)
    add_float_param(tree, "Audio Height M", 4.0, 0.0, 200.0)

    # --- Grid ---
    grid = safe_node(tree, "GeometryNodeMeshGrid", (-1400, 200))
    for src, dst in (("Size X M", "Size X"), ("Size Y M", "Size Y"),
                     ("Resolution X", "Vertices X"), ("Resolution Y", "Vertices Y")):
        link_sockets(tree, gin.outputs[src], grid.inputs[dst])

    pos = safe_node(tree, "GeometryNodeInputPosition", (-1200, -100))

    # --- Noise layers ---
    def _noise(loc, scale_socket, detail, roughness):
        noise = safe_node(tree, "ShaderNodeTexNoise", loc)
        noise.noise_dimensions = "3D"
        link_sockets(tree, pos.outputs["Position"], noise.inputs["Vector"])
        recip = safe_node(tree, "ShaderNodeMath", (loc[0] - 200, loc[1] - 80))
        recip.operation = "DIVIDE"
        recip.inputs[0].default_value = 1.0
        link_sockets(tree, scale_socket, recip.inputs[1])
        link_sockets(tree, recip.outputs[0], noise.inputs["Scale"])
        noise.inputs["Detail"].default_value = detail
        noise.inputs["Roughness"].default_value = roughness
        return noise.outputs["Fac"]

    macro = _noise((-900, 0), gin.outputs["Macro Scale M"], 3.0, 0.58)
    mid = _noise((-900, -200), gin.outputs["Mid Scale M"], 5.0, 0.63)
    micro = _noise((-900, -400), gin.outputs["Micro Scale M"], 2.0, 0.7)

    macro_h = safe_node(tree, "ShaderNodeMath", (-600, 0))
    macro_h.operation = "MULTIPLY"
    link_sockets(tree, macro, macro_h.inputs[0])
    link_sockets(tree, gin.outputs["Macro Height M"], macro_h.inputs[1])

    mid_h = safe_node(tree, "ShaderNodeMath", (-600, -200))
    mid_h.operation = "MULTIPLY"
    link_sockets(tree, mid, mid_h.inputs[0])
    link_sockets(tree, gin.outputs["Mid Height M"], mid_h.inputs[1])

    micro_h = safe_node(tree, "ShaderNodeMath", (-600, -400))
    micro_h.operation = "MULTIPLY"
    link_sockets(tree, micro, micro_h.inputs[0])
    link_sockets(tree, gin.outputs["Micro Height M"], micro_h.inputs[1])

    terrain_h = safe_node(tree, "ShaderNodeMath", (-350, -100))
    terrain_h.operation = "ADD"
    link_sockets(tree, macro_h.outputs[0], terrain_h.inputs[0])
    link_sockets(tree, mid_h.outputs[0], terrain_h.inputs[1])

    terrain_h2 = safe_node(tree, "ShaderNodeMath", (-150, -100))
    terrain_h2.operation = "ADD"
    link_sockets(tree, terrain_h.outputs[0], terrain_h2.inputs[0])
    link_sockets(tree, micro_h.outputs[0], terrain_h2.inputs[1])

    # --- Audio displacement ---
    amp = _sample_band(tree, gin, (-100, -500), gin.outputs["Low Hz"], gin.outputs["High Hz"],
                       use_scene_time=True)
    gain = safe_node(tree, "ShaderNodeMath", (100, -500))
    gain.operation = "MULTIPLY"
    link_sockets(tree, amp, gain.inputs[0])
    link_sockets(tree, gin.outputs["Audio Gain"], gain.inputs[1])
    audio_h = safe_node(tree, "ShaderNodeMath", (300, -500))
    audio_h.operation = "MULTIPLY"
    link_sockets(tree, gain.outputs[0], audio_h.inputs[0])
    link_sockets(tree, gin.outputs["Audio Height M"], audio_h.inputs[1])

    total_h = safe_node(tree, "ShaderNodeMath", (500, -200))
    total_h.operation = "ADD"
    link_sockets(tree, terrain_h2.outputs[0], total_h.inputs[0])
    link_sockets(tree, audio_h.outputs[0], total_h.inputs[1])

    offset = safe_node(tree, "ShaderNodeCombineXYZ", (700, -100))
    link_sockets(tree, total_h.outputs[0], offset.inputs["Z"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (900, 100))
    link_sockets(tree, grid.outputs["Mesh"], set_pos.inputs["Geometry"])
    link_sockets(tree, offset.outputs["Vector"], set_pos.inputs["Offset"])

    geom = _store_float(tree, set_pos.outputs["Geometry"], "audio_amplitude", gain.outputs[0], (1100, 100))
    geom = _store_float(tree, geom, "mel_height", total_h.outputs[0], (1300, 100))
    geom = apply_universal_music_pass(tree, gin, geom, (1500, 100))
    link_sockets(tree, geom, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Terrain Grid", "nodes": ("grid",), "role": "geometry"},
        {"title": "Noise Layers", "nodes": ("macro", "mid", "micro"), "role": "geometry"},
        {"title": "Audio Relief", "nodes": ("sample sound",), "role": "attribute"},
        {"title": "Export", "nodes": ("store", "music pass"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder(
    "MEL_audio_facade",
    build_audio_facade,
    "Audio Facade",
    "Building facade with window panels that displace by frequency band",
    "music",
)

register_builder(
    "MEL_audio_landscape",
    build_audio_landscape,
    "Audio Landscape",
    "Terrain that displaces based on audio amplitude — bass pushes ground up, treble adds ripple",
    "music",
)
