"""Garment audio drape — offline bake-lane audio-reactive fold/drape modifier.

Blender 5.2 native-audio Geometry Node builder. Offline authoring/bake lane
only: Unreal remains the runtime rhythm authority. Never add an audio writer.
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


def _store_float(tree, geometry, name, value, loc):
    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", loc)
    store.data_type = "FLOAT"
    store.domain = "POINT"
    link_sockets(tree, geometry, store.inputs["Geometry"])
    store.inputs["Name"].default_value = name
    link_sockets(tree, value, store.inputs["Value"])
    return store.outputs["Geometry"]


def build_garment_audio_drape(group_name="MEL_garment_audio_drape"):
    """Audio-reactive fold + noise drape over an incoming garment shell."""
    tree, gin, gout = new_geometry_tree(group_name)
    _add_sound_param(tree)
    add_float_param(tree, "Time", 0.0, 0.0, 36000.0)
    add_float_param(tree, "Low Hz", 40.0, 0.0, 20000.0)
    add_float_param(tree, "High Hz", 4000.0, 1.0, 24000.0)
    add_float_param(tree, "Band Width", 0.08, 0.001, 1.0)
    add_float_param(tree, "Audio Gain", 1.0, 0.0, 100.0)
    add_int_param(tree, "Seed", 0, 0, 9999)
    add_float_param(tree, "Fold", 2.0, 0.0, 32.0)
    add_float_param(tree, "Drape", 0.15, 0.0, 5.0)

    # Band: high = Low + (High - Low) * Band Width
    span = safe_node(tree, "ShaderNodeMath", (-640, -220))
    span.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["High Hz"], span.inputs[0])
    link_sockets(tree, gin.outputs["Low Hz"], span.inputs[1])
    scaled_span = safe_node(tree, "ShaderNodeMath", (-450, -220))
    scaled_span.operation = "MULTIPLY"
    link_sockets(tree, span.outputs[0], scaled_span.inputs[0])
    link_sockets(tree, gin.outputs["Band Width"], scaled_span.inputs[1])
    band_high = safe_node(tree, "ShaderNodeMath", (-260, -180))
    band_high.operation = "ADD"
    link_sockets(tree, gin.outputs["Low Hz"], band_high.inputs[0])
    link_sockets(tree, scaled_span.outputs[0], band_high.inputs[1])

    amp = _sample_band(tree, gin, (-60, -140), gin.outputs["Low Hz"], band_high.outputs[0])
    scaled = safe_node(tree, "ShaderNodeMath", (130, -140))
    scaled.operation = "MULTIPLY"
    link_sockets(tree, amp, scaled.inputs[0])
    link_sockets(tree, gin.outputs["Audio Gain"], scaled.inputs[1])

    # Position-based fold: sin(Y * Fold + Seed) * scaled * Drape
    pos = safe_node(tree, "GeometryNodeInputPosition", (-640, 60))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (-450, 60))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])
    fold_freq = safe_node(tree, "ShaderNodeMath", (-260, 60))
    fold_freq.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["Y"], fold_freq.inputs[0])
    link_sockets(tree, gin.outputs["Fold"], fold_freq.inputs[1])
    fold_phase = safe_node(tree, "ShaderNodeMath", (-70, 60))
    fold_phase.operation = "ADD"
    link_sockets(tree, fold_freq.outputs[0], fold_phase.inputs[0])
    link_sockets(tree, gin.outputs["Seed"], fold_phase.inputs[1])
    fold_sin = safe_node(tree, "ShaderNodeMath", (120, 60))
    fold_sin.operation = "SINE"
    link_sockets(tree, fold_phase.outputs[0], fold_sin.inputs[0])
    fold_amp = safe_node(tree, "ShaderNodeMath", (310, 60))
    fold_amp.operation = "MULTIPLY"
    link_sockets(tree, fold_sin.outputs[0], fold_amp.inputs[0])
    link_sockets(tree, scaled.outputs[0], fold_amp.inputs[1])
    fold_disp = safe_node(tree, "ShaderNodeMath", (500, 60))
    fold_disp.operation = "MULTIPLY"
    link_sockets(tree, fold_amp.outputs[0], fold_disp.inputs[0])
    link_sockets(tree, gin.outputs["Drape"], fold_disp.inputs[1])

    # Noise drape: (Noise(Position, W=Seed).Fac - 0.5) * 2 * scaled * Drape
    noise = safe_node(tree, "ShaderNodeTexNoise", (-260, -60))
    link_sockets(tree, pos.outputs["Position"], noise.inputs["Vector"])
    link_sockets(tree, gin.outputs["Seed"], sock(noise, "W"))
    noise_center = safe_node(tree, "ShaderNodeMath", (-70, -60))
    noise_center.operation = "SUBTRACT"
    link_sockets(tree, noise.outputs["Fac"], noise_center.inputs[0])
    noise_center.inputs[1].default_value = 0.5
    noise_bipolar = safe_node(tree, "ShaderNodeMath", (120, -60))
    noise_bipolar.operation = "MULTIPLY"
    link_sockets(tree, noise_center.outputs[0], noise_bipolar.inputs[0])
    noise_bipolar.inputs[1].default_value = 2.0
    noise_amp = safe_node(tree, "ShaderNodeMath", (310, -60))
    noise_amp.operation = "MULTIPLY"
    link_sockets(tree, noise_bipolar.outputs[0], noise_amp.inputs[0])
    link_sockets(tree, scaled.outputs[0], noise_amp.inputs[1])
    noise_disp = safe_node(tree, "ShaderNodeMath", (500, -60))
    noise_disp.operation = "MULTIPLY"
    link_sockets(tree, noise_amp.outputs[0], noise_disp.inputs[0])
    link_sockets(tree, gin.outputs["Drape"], noise_disp.inputs[1])

    total = safe_node(tree, "ShaderNodeMath", (690, 0))
    total.operation = "ADD"
    link_sockets(tree, fold_disp.outputs[0], total.inputs[0])
    link_sockets(tree, noise_disp.outputs[0], total.inputs[1])

    # Displace along normal via Set Position.
    normal = safe_node(tree, "GeometryNodeInputNormal", (690, 220))
    offset = safe_node(tree, "ShaderNodeVectorMath", (880, 100))
    offset.operation = "SCALE"
    link_sockets(tree, normal.outputs["Normal"], offset.inputs["Vector"])
    link_sockets(tree, total.outputs[0], offset.inputs["Scale"])
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (1070, 100))
    link_sockets(tree, gin.outputs["Geometry"], set_pos.inputs["Geometry"])
    link_sockets(tree, offset.outputs["Vector"], set_pos.inputs["Offset"])
    geom = _store_float(tree, set_pos.outputs["Geometry"], "audio_amplitude",
                        scaled.outputs[0], (1270, 100))
    link_sockets(tree, geom, gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Audio Band", "nodes": ("sample sound",), "role": "attribute"},
        {"title": "Fold + Drape", "nodes": ("noise", "sine", "set position"), "role": "geometry"},
        {"title": "Export Attributes", "nodes": ("store",), "role": "output"},
    ])


register_builder("MEL_garment_audio_drape", build_garment_audio_drape,
                 "Garment Audio Drape", "Offline audio-reactive fold+drape over a garment shell", "Garment")
