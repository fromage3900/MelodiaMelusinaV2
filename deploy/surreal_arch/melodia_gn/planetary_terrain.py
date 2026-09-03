"""Deterministic planetary musical terrain for Melodia Studio v3.

The builder is an offline authoring system.  Tile coordinates affect the noise
sampling domain, not object transforms, so neighbouring exports share edges and
remain world-origin safe.  Unreal's existing presentation subsystem remains the
runtime music authority.
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


NAMED_ATTRIBUTES = (
    "mel_height",
    "mel_slope",
    "mel_cavity",
    "mel_shoreline",
    "mel_biome",
    "mel_traversal",
    "audio_amplitude",
)


def _math(tree, operation, a, b, loc):
    node = safe_node(tree, "ShaderNodeMath", loc)
    node.operation = operation
    if hasattr(a, "id_data"):
        link_sockets(tree, a, node.inputs[0])
    else:
        node.inputs[0].default_value = a
    if hasattr(b, "id_data"):
        link_sockets(tree, b, node.inputs[1])
    else:
        node.inputs[1].default_value = b
    return node.outputs[0]


def _terrain_inputs(tree):
    _add_sound_param(tree)
    add_float_param(tree, "Time", 0.0, 0.0, 36000.0)
    add_int_param(tree, "Seed", 1337, 0, 1000000)
    add_int_param(tree, "Tile X", 0, -4096, 4096)
    add_int_param(tree, "Tile Y", 0, -4096, 4096)
    add_int_param(tree, "Terrain Mode", 0, 0, 9)
    add_float_param(tree, "Size X M", 256.0, 8.0, 8192.0)
    add_float_param(tree, "Size Y M", 256.0, 8.0, 8192.0)
    add_int_param(tree, "Resolution X", 129, 9, 1025)
    add_int_param(tree, "Resolution Y", 129, 9, 1025)
    add_float_param(tree, "Base Height M", 0.0, -1000.0, 1000.0)
    add_float_param(tree, "Macro Height M", 64.0, 0.0, 2000.0)
    add_float_param(tree, "Macro Scale M", 420.0, 1.0, 10000.0)
    add_float_param(tree, "Mid Height M", 18.0, 0.0, 500.0)
    add_float_param(tree, "Mid Scale M", 96.0, 0.2, 4000.0)
    add_float_param(tree, "Micro Height M", 3.0, 0.0, 100.0)
    add_float_param(tree, "Micro Scale M", 18.0, 0.1, 500.0)
    add_float_param(tree, "Island Radius", 0.82, 0.05, 2.0)
    add_float_param(tree, "Shore Height M", 4.0, -500.0, 500.0)
    add_float_param(tree, "Reserved Path M", 8.0, 0.0, 200.0)
    add_float_param(tree, "Low Hz", 30.0, 0.0, 20000.0)
    add_float_param(tree, "High Hz", 900.0, 1.0, 24000.0)
    add_float_param(tree, "Audio Gain", 1.0, 0.0, 100.0)
    add_float_param(tree, "Audio Height M", 12.0, 0.0, 500.0)
    add_music_influence_params(tree)


def _noise(tree, vector, scale_socket, detail, roughness, loc):
    reciprocal = safe_node(tree, "ShaderNodeMath", (loc[0] - 200, loc[1] - 80))
    reciprocal.operation = "DIVIDE"
    reciprocal.inputs[0].default_value = 1.0
    link_sockets(tree, scale_socket, reciprocal.inputs[1])
    noise = safe_node(tree, "ShaderNodeTexNoise", loc)
    noise.noise_dimensions = "3D"
    link_sockets(tree, vector, noise.inputs["Vector"])
    link_sockets(tree, reciprocal.outputs[0], noise.inputs["Scale"])
    noise.inputs["Detail"].default_value = detail
    noise.inputs["Roughness"].default_value = roughness
    return noise.outputs["Fac"]


def build_planetary_musical_terrain(group_name="MEL_planetary_musical_terrain"):
    """Tile-continuous planetary terrain with export-ready semantic masks."""
    tree, gin, gout = new_geometry_tree(group_name)
    _terrain_inputs(tree)

    grid = safe_node(tree, "GeometryNodeMeshGrid", (-1500, 260))
    for source, target in (("Size X M", "Size X"), ("Size Y M", "Size Y"),
                           ("Resolution X", "Vertices X"), ("Resolution Y", "Vertices Y")):
        link_sockets(tree, gin.outputs[source], grid.inputs[target])

    pos = safe_node(tree, "GeometryNodeInputPosition", (-1500, -100))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (-1300, -100))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    tile_x = _math(tree, "MULTIPLY", gin.outputs["Tile X"], gin.outputs["Size X M"], (-1300, -340))
    tile_y = _math(tree, "MULTIPLY", gin.outputs["Tile Y"], gin.outputs["Size Y M"], (-1300, -500))
    world_x = _math(tree, "ADD", sep.outputs["X"], tile_x, (-1080, -300))
    world_y = _math(tree, "ADD", sep.outputs["Y"], tile_y, (-1080, -460))
    seeded = _math(tree, "MULTIPLY", gin.outputs["Seed"], 0.013579, (-1080, -620))
    vector = safe_node(tree, "ShaderNodeCombineXYZ", (-860, -300))
    link_sockets(tree, world_x, vector.inputs["X"])
    link_sockets(tree, world_y, vector.inputs["Y"])
    link_sockets(tree, seeded, vector.inputs["Z"])

    macro = _noise(tree, vector.outputs["Vector"], gin.outputs["Macro Scale M"], 3.0, 0.58, (-600, -180))
    mid = _noise(tree, vector.outputs["Vector"], gin.outputs["Mid Scale M"], 5.0, 0.63, (-600, -400))
    micro = _noise(tree, vector.outputs["Vector"], gin.outputs["Micro Scale M"], 2.0, 0.7, (-600, -620))
    macro_h = _math(tree, "MULTIPLY", macro, gin.outputs["Macro Height M"], (-340, -180))
    mid_h = _math(tree, "MULTIPLY", mid, gin.outputs["Mid Height M"], (-340, -400))
    micro_h = _math(tree, "MULTIPLY", micro, gin.outputs["Micro Height M"], (-340, -620))
    terrain_h = _math(tree, "ADD", macro_h, mid_h, (-100, -250))
    terrain_h = _math(tree, "ADD", terrain_h, micro_h, (100, -250))

    # Broad-band music adds authored relief but defaults to zero through Audio Height.
    amp = _sample_band(tree, gin, (-80, -760), gin.outputs["Low Hz"], gin.outputs["High Hz"])
    amp = _math(tree, "MULTIPLY", amp, gin.outputs["Audio Gain"], (160, -760))
    audio_h = _math(tree, "MULTIPLY", amp, gin.outputs["Audio Height M"], (360, -700))
    terrain_h = _math(tree, "ADD", terrain_h, audio_h, (360, -250))
    terrain_h = _math(tree, "ADD", terrain_h, gin.outputs["Base Height M"], (560, -250))

    # Island falloff is mixed by Terrain Mode / 9, giving modes a stable shared shape vocabulary.
    length = safe_node(tree, "ShaderNodeVectorMath", (-820, 40)); length.operation = "LENGTH"
    link_sockets(tree, pos.outputs["Position"], length.inputs[0])
    radius = _math(tree, "MULTIPLY", gin.outputs["Size X M"], gin.outputs["Island Radius"], (-600, 40))
    falloff = safe_node(tree, "ShaderNodeMapRange", (-340, 40)); falloff.clamp = True
    link_sockets(tree, length.outputs["Value"], falloff.inputs["Value"])
    link_sockets(tree, radius, falloff.inputs["From Max"])
    falloff.inputs["To Min"].default_value = 1.0
    falloff.inputs["To Max"].default_value = 0.0
    island_cut = _math(tree, "MULTIPLY", falloff.outputs["Result"], terrain_h, (120, 20))
    mode_mix = _math(tree, "DIVIDE", gin.outputs["Terrain Mode"], 9.0, (120, -80))
    mix = safe_node(tree, "ShaderNodeMix", (560, 0)); mix.data_type = "FLOAT"
    link_sockets(tree, mode_mix, mix.inputs["Factor"])
    link_sockets(tree, terrain_h, mix.inputs["A"])
    link_sockets(tree, island_cut, mix.inputs["B"])

    offset = safe_node(tree, "ShaderNodeCombineXYZ", (760, -80))
    link_sockets(tree, mix.outputs["Result"], offset.inputs["Z"])
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (960, 220))
    link_sockets(tree, grid.outputs["Mesh"], set_pos.inputs["Geometry"])
    link_sockets(tree, offset.outputs["Vector"], set_pos.inputs["Offset"])

    normal = safe_node(tree, "GeometryNodeInputNormal", (760, -360))
    nsep = safe_node(tree, "ShaderNodeSeparateXYZ", (960, -360))
    link_sockets(tree, normal.outputs["Normal"], nsep.inputs["Vector"])
    slope = _math(tree, "SUBTRACT", 1.0, nsep.outputs["Z"], (1160, -360))
    cavity = _math(tree, "SUBTRACT", mid, micro, (1160, -500))
    shore_delta = _math(tree, "SUBTRACT", mix.outputs["Result"], gin.outputs["Shore Height M"], (1160, -640))
    shore_abs = safe_node(tree, "ShaderNodeMath", (1360, -640)); shore_abs.operation = "ABSOLUTE"
    link_sockets(tree, shore_delta, shore_abs.inputs[0])
    shoreline = safe_node(tree, "ShaderNodeMapRange", (1560, -640)); shoreline.clamp = True
    link_sockets(tree, shore_abs.outputs[0], shoreline.inputs["Value"])
    shoreline.inputs["From Max"].default_value = 12.0
    shoreline.inputs["To Min"].default_value = 1.0
    shoreline.inputs["To Max"].default_value = 0.0
    path_abs = safe_node(tree, "ShaderNodeMath", (1160, -780)); path_abs.operation = "ABSOLUTE"
    link_sockets(tree, sep.outputs["Y"], path_abs.inputs[0])
    traversal = safe_node(tree, "ShaderNodeMapRange", (1360, -780)); traversal.clamp = True
    link_sockets(tree, path_abs.outputs[0], traversal.inputs["Value"])
    link_sockets(tree, gin.outputs["Reserved Path M"], traversal.inputs["From Max"])
    traversal.inputs["To Min"].default_value = 1.0
    traversal.inputs["To Max"].default_value = 0.0

    geom = set_pos.outputs["Geometry"]
    for name, value in (
        ("mel_height", mix.outputs["Result"]), ("mel_slope", slope),
        ("mel_cavity", cavity), ("mel_shoreline", shoreline.outputs["Result"]),
        ("mel_biome", macro), ("mel_traversal", traversal.outputs["Result"]),
        ("audio_amplitude", amp),
    ):
        geom = _store_float(tree, geom, name, value, (1220 + 190 * NAMED_ATTRIBUTES.index(name), 220))
    geom = apply_universal_music_pass(tree, gin, geom, (2700, 220))
    link_sockets(tree, geom, gout.inputs["Geometry"])
    return label_tree(tree, group_name, [
        {"title": "Planet Coordinates", "nodes": ("position", "combine xyz"), "role": "input"},
        {"title": "Macro Mid Micro", "nodes": ("noise", "map range"), "role": "geometry"},
        {"title": "Music Relief", "nodes": ("sample sound",), "role": "attribute"},
        {"title": "UE Semantic Masks", "nodes": ("store named",), "role": "output"},
    ])


register_builder(
    "MEL_planetary_musical_terrain",
    build_planetary_musical_terrain,
    "Planetary Musical Terrain",
    "Deterministic tile-continuous continents, islands, reefs, ruins, and traversal fields.",
    "music",
)
