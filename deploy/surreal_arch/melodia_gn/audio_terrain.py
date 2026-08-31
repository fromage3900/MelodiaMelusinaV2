"""Blender 5.2 native-audio Geometry Nodes builders for Melodia Studio.

These builders use GeometryNodeSampleSoundFrequencies directly.  They are an
offline authoring/bake lane: Unreal remains the runtime rhythm authority.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    add_float_param,
    add_music_influence_params,
    apply_universal_music_pass,
    add_int_param,
    color_node,
    label_tree,
    link_sockets,
    new_geometry_tree,
    register_builder,
    safe_node,
    sock,
)


def _add_sound_param(tree, name="Sound"):
    """Add a Blender 5.2 Sound interface socket and return its identifier."""
    for item in tree.interface.items_tree:
        if getattr(item, "item_type", "") == "SOCKET" and item.name == name:
            return item
    return tree.interface.new_socket(name=name, in_out="INPUT", socket_type="NodeSocketSound")


def _sample_band(tree, gin, loc, low, high):
    sample = safe_node(tree, "GeometryNodeSampleSoundFrequencies", loc)
    if sample is None:
        raise RuntimeError("Blender 5.2 Sample Sound Frequencies node is unavailable")
    link_sockets(tree, gin.outputs["Sound"], sample.inputs["Sound"])
    link_sockets(tree, gin.outputs["Time"], sample.inputs["Time"])
    link_sockets(tree, low, sample.inputs["Low"])
    link_sockets(tree, high, sample.inputs["High"])
    sample.inputs["All Channels"].default_value = True
    return sample.outputs["Amplitude"]


def _map_frequency(tree, gin, position, loc):
    separate = safe_node(tree, "ShaderNodeSeparateXYZ", loc)
    link_sockets(tree, position, separate.inputs["Vector"])
    map_range = safe_node(tree, "ShaderNodeMapRange", (loc[0] + 190, loc[1]))
    map_range.clamp = True
    link_sockets(tree, separate.outputs["X"], map_range.inputs["Value"])
    half = safe_node(tree, "ShaderNodeMath", (loc[0], loc[1] - 170))
    half.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Size X M"], half.inputs[0])
    half.inputs[1].default_value = 0.5
    neg = safe_node(tree, "ShaderNodeMath", (loc[0] + 190, loc[1] - 170))
    neg.operation = "MULTIPLY"
    link_sockets(tree, half.outputs[0], neg.inputs[0])
    neg.inputs[1].default_value = -1.0
    link_sockets(tree, neg.outputs[0], map_range.inputs["From Min"])
    link_sockets(tree, half.outputs[0], map_range.inputs["From Max"])
    link_sockets(tree, gin.outputs["Low Hz"], map_range.inputs["To Min"])
    link_sockets(tree, gin.outputs["High Hz"], map_range.inputs["To Max"])
    width = safe_node(tree, "ShaderNodeMath", (loc[0] + 390, loc[1] - 120))
    width.operation = "MULTIPLY"
    link_sockets(tree, map_range.outputs["Result"], width.inputs[0])
    link_sockets(tree, gin.outputs["Band Width"], width.inputs[1])
    high = safe_node(tree, "ShaderNodeMath", (loc[0] + 570, loc[1] - 30))
    high.operation = "ADD"
    link_sockets(tree, map_range.outputs["Result"], high.inputs[0])
    link_sockets(tree, width.outputs[0], high.inputs[1])
    return map_range.outputs["Result"], high.outputs[0]


def _audio_inputs(tree):
    _add_sound_param(tree)
    add_float_param(tree, "Time", 0.0, 0.0, 36000.0)
    add_float_param(tree, "Low Hz", 30.0, 0.0, 20000.0)
    add_float_param(tree, "High Hz", 12000.0, 1.0, 24000.0)
    add_float_param(tree, "Band Width", 0.08, 0.001, 1.0)
    add_float_param(tree, "Audio Gain", 8.0, 0.0, 100.0)
    add_music_influence_params(tree)


def _store_float(tree, geometry, name, value, loc):
    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", loc)
    store.data_type = "FLOAT"
    store.domain = "POINT"
    link_sockets(tree, geometry, store.inputs["Geometry"])
    store.inputs["Name"].default_value = name
    link_sockets(tree, value, store.inputs["Value"])
    return store.outputs["Geometry"]


def build_audio_spectrum_terrain(group_name="MEL_audio_spectrum_terrain"):
    """Continuous walkable terrain displaced by sampled frequency energy."""
    tree, gin, gout = new_geometry_tree(group_name)
    _audio_inputs(tree)
    add_float_param(tree, "Size X M", 80.0, 2.0, 2000.0)
    add_float_param(tree, "Size Y M", 48.0, 2.0, 2000.0)
    add_int_param(tree, "Resolution X", 192, 8, 1024)
    add_int_param(tree, "Resolution Y", 96, 8, 1024)
    add_float_param(tree, "Height M", 18.0, 0.0, 500.0)

    grid = safe_node(tree, "GeometryNodeMeshGrid", (-900, 120))
    link_sockets(tree, gin.outputs["Size X M"], grid.inputs["Size X"])
    link_sockets(tree, gin.outputs["Size Y M"], grid.inputs["Size Y"])
    link_sockets(tree, gin.outputs["Resolution X"], grid.inputs["Vertices X"])
    link_sockets(tree, gin.outputs["Resolution Y"], grid.inputs["Vertices Y"])
    pos = safe_node(tree, "GeometryNodeInputPosition", (-700, -130))
    low, high = _map_frequency(tree, gin, pos.outputs["Position"], (-500, -100))
    amp = _sample_band(tree, gin, (-80, -80), low, high)
    gain = safe_node(tree, "ShaderNodeMath", (120, -80)); gain.operation = "MULTIPLY"
    link_sockets(tree, amp, gain.inputs[0]); link_sockets(tree, gin.outputs["Audio Gain"], gain.inputs[1])
    height = safe_node(tree, "ShaderNodeMath", (300, -80)); height.operation = "MULTIPLY"
    link_sockets(tree, gain.outputs[0], height.inputs[0]); link_sockets(tree, gin.outputs["Height M"], height.inputs[1])
    offset = safe_node(tree, "ShaderNodeCombineXYZ", (480, -80))
    link_sockets(tree, height.outputs[0], offset.inputs["Z"])
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (670, 100))
    link_sockets(tree, grid.outputs["Mesh"], set_pos.inputs["Geometry"])
    link_sockets(tree, offset.outputs["Vector"], set_pos.inputs["Offset"])
    geom = _store_float(tree, set_pos.outputs["Geometry"], "audio_amplitude", gain.outputs[0], (870, 100))
    geom = _store_float(tree, geom, "frequency_hz", low, (1070, 100))
    geom = apply_universal_music_pass(tree, gin, geom, (1280, 100))
    link_sockets(tree, geom, gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Audio Spectrum", "nodes": ("sample sound", "map frequency"), "role": "attribute"},
        {"title": "Terrain", "nodes": ("grid", "set position"), "role": "geometry"},
        {"title": "Export Attributes", "nodes": ("store",), "role": "output"},
    ])


def build_audio_spectrum_towers(group_name="MEL_audio_spectrum_towers"):
    """Large-scale frequency-bin mesh generator for cities, walls, and reefs."""
    tree, gin, gout = new_geometry_tree(group_name)
    _audio_inputs(tree)
    add_float_param(tree, "Size X M", 120.0, 2.0, 4000.0)
    add_int_param(tree, "Frequency Bins", 128, 8, 2048)
    add_float_param(tree, "Tower Width M", 0.7, 0.02, 40.0)
    add_float_param(tree, "Tower Depth M", 3.0, 0.02, 200.0)
    add_float_param(tree, "Height M", 32.0, 0.0, 1000.0)

    line = safe_node(tree, "GeometryNodeMeshLine", (-900, 100)); line.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Frequency Bins"], line.inputs["Count"])
    bins_minus_one = safe_node(tree, "ShaderNodeMath", (-1120, -220)); bins_minus_one.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Frequency Bins"], bins_minus_one.inputs[0]); bins_minus_one.inputs[1].default_value = 1.0
    step = safe_node(tree, "ShaderNodeMath", (-920, -220)); step.operation = "DIVIDE"
    link_sockets(tree, gin.outputs["Size X M"], step.inputs[0]); link_sockets(tree, bins_minus_one.outputs[0], step.inputs[1])
    offset = safe_node(tree, "ShaderNodeCombineXYZ", (-700, -240)); link_sockets(tree, step.outputs[0], offset.inputs["X"])
    link_sockets(tree, offset.outputs["Vector"], line.inputs["Offset"])
    half = safe_node(tree, "ShaderNodeMath", (-1120, -80)); half.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Size X M"], half.inputs[0]); half.inputs[1].default_value = -0.5
    start = safe_node(tree, "ShaderNodeCombineXYZ", (-900, -80)); link_sockets(tree, half.outputs[0], start.inputs["X"])
    link_sockets(tree, start.outputs["Vector"], line.inputs["Start Location"])
    points = safe_node(tree, "GeometryNodeMeshToPoints", (-700, 100))
    link_sockets(tree, line.outputs["Mesh"], points.inputs["Mesh"])
    pos = safe_node(tree, "GeometryNodeInputPosition", (-700, -160))
    low, high = _map_frequency(tree, gin, pos.outputs["Position"], (-500, -140))
    amp = _sample_band(tree, gin, (-60, -120), low, high)
    gain = safe_node(tree, "ShaderNodeMath", (130, -120)); gain.operation = "MULTIPLY"
    link_sockets(tree, amp, gain.inputs[0]); link_sockets(tree, gin.outputs["Audio Gain"], gain.inputs[1])
    h = safe_node(tree, "ShaderNodeMath", (310, -120)); h.operation = "MULTIPLY"
    link_sockets(tree, gain.outputs[0], h.inputs[0]); link_sockets(tree, gin.outputs["Height M"], h.inputs[1])
    cube = safe_node(tree, "GeometryNodeMeshCube", (-80, 220))
    size = safe_node(tree, "ShaderNodeCombineXYZ", (140, 220))
    link_sockets(tree, gin.outputs["Tower Width M"], size.inputs["X"])
    link_sockets(tree, gin.outputs["Tower Depth M"], size.inputs["Y"])
    link_sockets(tree, h.outputs[0], size.inputs["Z"])
    link_sockets(tree, size.outputs["Vector"], cube.inputs["Size"])
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (430, 100))
    link_sockets(tree, points.outputs["Points"], inst.inputs["Points"])
    link_sockets(tree, cube.outputs["Mesh"], inst.inputs["Instance"])
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (650, 100))
    link_sockets(tree, inst.outputs["Instances"], realize.inputs["Geometry"])
    geom = _store_float(tree, realize.outputs["Geometry"], "audio_amplitude", gain.outputs[0], (850, 100))
    geom = _store_float(tree, geom, "frequency_hz", low, (1050, 100))
    geom = apply_universal_music_pass(tree, gin, geom, (1260, 100))
    link_sockets(tree, geom, gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Frequency Bins", "nodes": ("mesh line", "sample sound"), "role": "attribute"},
        {"title": "Tower Instances", "nodes": ("cube", "instance", "realize"), "role": "instance"},
        {"title": "Export Attributes", "nodes": ("store",), "role": "output"},
    ])


def build_audio_radial_field(group_name="MEL_audio_radial_field"):
    """Concentric terrain membrane driven by low-to-high radial frequency bands."""
    tree, gin, gout = new_geometry_tree(group_name)
    _audio_inputs(tree)
    add_float_param(tree, "Size X M", 100.0, 2.0, 4000.0)
    add_int_param(tree, "Radial Segments", 256, 16, 2048)
    add_float_param(tree, "Height M", 24.0, 0.0, 1000.0)
    add_float_param(tree, "Radius M", 50.0, 1.0, 2000.0)

    grid = safe_node(tree, "GeometryNodeMeshGrid", (-850, 120))
    link_sockets(tree, gin.outputs["Radial Segments"], grid.inputs["Vertices X"])
    link_sockets(tree, gin.outputs["Radial Segments"], grid.inputs["Vertices Y"])
    link_sockets(tree, gin.outputs["Size X M"], grid.inputs["Size X"])
    link_sockets(tree, gin.outputs["Size X M"], grid.inputs["Size Y"])
    pos = safe_node(tree, "GeometryNodeInputPosition", (-680, -140))
    length = safe_node(tree, "ShaderNodeVectorMath", (-500, -140)); length.operation = "LENGTH"
    link_sockets(tree, pos.outputs["Position"], length.inputs[0])
    mapped = safe_node(tree, "ShaderNodeMapRange", (-300, -140)); mapped.clamp = True
    link_sockets(tree, length.outputs["Value"], mapped.inputs["Value"])
    link_sockets(tree, gin.outputs["Radius M"], mapped.inputs["From Max"])
    link_sockets(tree, gin.outputs["Low Hz"], mapped.inputs["To Min"])
    link_sockets(tree, gin.outputs["High Hz"], mapped.inputs["To Max"])
    bw = safe_node(tree, "ShaderNodeMath", (-100, -260)); bw.operation = "MULTIPLY"
    link_sockets(tree, mapped.outputs["Result"], bw.inputs[0]); link_sockets(tree, gin.outputs["Band Width"], bw.inputs[1])
    hi = safe_node(tree, "ShaderNodeMath", (80, -180)); hi.operation = "ADD"
    link_sockets(tree, mapped.outputs["Result"], hi.inputs[0]); link_sockets(tree, bw.outputs[0], hi.inputs[1])
    amp = _sample_band(tree, gin, (260, -150), mapped.outputs["Result"], hi.outputs[0])
    gain = safe_node(tree, "ShaderNodeMath", (450, -150)); gain.operation = "MULTIPLY"
    link_sockets(tree, amp, gain.inputs[0]); link_sockets(tree, gin.outputs["Audio Gain"], gain.inputs[1])
    height = safe_node(tree, "ShaderNodeMath", (630, -150)); height.operation = "MULTIPLY"
    link_sockets(tree, gain.outputs[0], height.inputs[0]); link_sockets(tree, gin.outputs["Height M"], height.inputs[1])
    offset = safe_node(tree, "ShaderNodeCombineXYZ", (810, -150)); link_sockets(tree, height.outputs[0], offset.inputs["Z"])
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (810, 100))
    link_sockets(tree, grid.outputs["Mesh"], set_pos.inputs["Geometry"]); link_sockets(tree, offset.outputs["Vector"], set_pos.inputs["Offset"])
    geom = _store_float(tree, set_pos.outputs["Geometry"], "audio_amplitude", gain.outputs[0], (1030, 100))
    geom = apply_universal_music_pass(tree, gin, geom, (1230, 100))
    link_sockets(tree, geom, gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Radial Spectrum", "nodes": ("position", "length", "sample sound"), "role": "attribute"},
        {"title": "Pulse Membrane", "nodes": ("grid", "set position"), "role": "geometry"},
    ])


register_builder("MEL_audio_spectrum_terrain", build_audio_spectrum_terrain,
                 "Audio Spectrum Terrain", "Blender 5.2 native sound-frequency terrain with export attributes", "music")
register_builder("MEL_audio_spectrum_towers", build_audio_spectrum_towers,
                 "Audio Spectrum Towers", "Frequency-bin mesh city/wall generator driven by native sound sampling", "music")
register_builder("MEL_audio_radial_field", build_audio_radial_field,
                 "Audio Radial Field", "Concentric audio-reactive terrain membrane for arenas and monolith fields", "music")
