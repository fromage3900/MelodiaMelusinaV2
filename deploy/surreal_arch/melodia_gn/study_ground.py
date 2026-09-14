"""Study ground — audio-reactive ground plane for Melusina's Study."""
from __future__ import annotations

from .audio_terrain import _add_sound_param, _sample_band
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


def build_study_ground(group_name="MEL_study_ground"):
    """Audio-reactive ground plane for Melusina's Study.

    A flat grid that displaces vertically based on audio amplitude.
    Bass frequencies push the ground up, treble adds fine ripple.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    _add_sound_param(tree)
    add_float_param(tree, "Time", 0.0, 0.0, 36000.0)
    add_float_param(tree, "Low Hz", 20.0, 0.0, 20000.0)
    add_float_param(tree, "High Hz", 20000.0, 1.0, 20000.0)
    add_float_param(tree, "Audio Gain", 2.0, 0.0, 50.0)
    add_float_param(tree, "Ground Size M", 20.0, 2.0, 100.0)
    add_int_param(tree, "Resolution", 64, 8, 256)
    add_float_param(tree, "Ripple Scale M", 5.0, 0.5, 50.0)
    add_float_param(tree, "Ripple Height M", 0.3, 0.0, 5.0)

    # Grid
    grid = safe_node(tree, "GeometryNodeMeshGrid", (-800, 200))
    link_sockets(tree, gin.outputs["Ground Size M"], grid.inputs["Size X"])
    link_sockets(tree, gin.outputs["Ground Size M"], grid.inputs["Size Y"])
    link_sockets(tree, gin.outputs["Resolution"], grid.inputs["Vertices X"])
    link_sockets(tree, gin.outputs["Resolution"], grid.inputs["Vertices Y"])

    # Position for noise
    pos = safe_node(tree, "GeometryNodeInputPosition", (-600, -100))

    # Noise ripple
    noise = safe_node(tree, "ShaderNodeTexNoise", (-400, 0))
    noise.noise_dimensions = "3D"
    link_sockets(tree, pos.outputs["Position"], noise.inputs["Vector"])
    recip = safe_node(tree, "ShaderNodeMath", (-600, -200))
    recip.operation = "DIVIDE"
    recip.inputs[0].default_value = 1.0
    link_sockets(tree, gin.outputs["Ripple Scale M"], recip.inputs[1])
    link_sockets(tree, recip.outputs[0], noise.inputs["Scale"])
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.6

    ripple_h = safe_node(tree, "ShaderNodeMath", (-200, 0))
    ripple_h.operation = "MULTIPLY"
    link_sockets(tree, noise.outputs["Fac"], ripple_h.inputs[0])
    link_sockets(tree, gin.outputs["Ripple Height M"], ripple_h.inputs[1])

    # Audio displacement
    amp = _sample_band(tree, gin, (0, -300), gin.outputs["Low Hz"], gin.outputs["High Hz"])
    gain = safe_node(tree, "ShaderNodeMath", (200, -300))
    gain.operation = "MULTIPLY"
    link_sockets(tree, amp, gain.inputs[0])
    link_sockets(tree, gin.outputs["Audio Gain"], gain.inputs[1])

    total_h = safe_node(tree, "ShaderNodeMath", (400, -100))
    total_h.operation = "ADD"
    link_sockets(tree, ripple_h.outputs[0], total_h.inputs[0])
    link_sockets(tree, gain.outputs[0], total_h.inputs[1])

    offset = safe_node(tree, "ShaderNodeCombineXYZ", (600, 0))
    link_sockets(tree, total_h.outputs[0], offset.inputs["Z"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (800, 100))
    link_sockets(tree, grid.outputs["Mesh"], set_pos.inputs["Geometry"])
    link_sockets(tree, offset.outputs["Vector"], set_pos.inputs["Offset"])

    geom = apply_universal_music_pass(tree, gin, set_pos.outputs["Geometry"], (1000, 100))
    link_sockets(tree, geom, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Ground Grid", "nodes": ("grid",), "role": "geometry"},
        {"title": "Audio Displace", "nodes": ("sample sound", "set position"), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


register_builder(
    "MEL_study_ground",
    build_study_ground,
    "Study Ground",
    "Audio-reactive ground plane for Melusina's Study — bass pushes ground up, treble adds ripple",
    "music",
)
