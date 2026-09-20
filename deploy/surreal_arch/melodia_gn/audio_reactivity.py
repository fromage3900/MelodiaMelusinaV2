"""Shared audio reactivity helpers for Melodia Studio GN builders."""
from __future__ import annotations

from .core import add_float_param, link_sockets, safe_node
from .audio_terrain import _add_sound_param, _sample_band


def add_audio_reactivity(tree, gin, geo_socket, loc=(0, 0)):
    """Add audio-reactive vertical displacement to geometry.

    Adds Sound, Time, Low Hz, High Hz, Audio Gain inputs and offsets
    the geometry vertically based on the sampled audio amplitude.
    Returns the SetPosition geometry output.
    """
    _add_sound_param(tree)
    add_float_param(tree, "Time", 0.0, 0.0, 36000.0)
    add_float_param(tree, "Low Hz", 20.0, 0.0, 20000.0)
    add_float_param(tree, "High Hz", 20000.0, 1.0, 20000.0)
    add_float_param(tree, "Audio Gain", 4.0, 0.0, 50.0)

    amp = _sample_band(tree, gin, loc, gin.outputs["Low Hz"], gin.outputs["High Hz"])
    gain = safe_node(tree, "ShaderNodeMath", (loc[0] + 100, loc[1]))
    gain.operation = "MULTIPLY"
    link_sockets(tree, amp, gain.inputs[0])
    link_sockets(tree, gin.outputs["Audio Gain"], gain.inputs[1])

    offset = safe_node(tree, "ShaderNodeCombineXYZ", (loc[0] + 200, loc[1]))
    offset.inputs["X"].default_value = 0.0
    offset.inputs["Y"].default_value = 0.0
    link_sockets(tree, gain.outputs[0], offset.inputs["Z"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (loc[0] + 400, loc[1]))
    link_sockets(tree, geo_socket, set_pos.inputs["Geometry"])
    link_sockets(tree, offset.outputs["Vector"], set_pos.inputs["Offset"])
    return set_pos.outputs["Geometry"]
