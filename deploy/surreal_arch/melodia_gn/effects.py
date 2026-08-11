"""Magic effect GN group builders ΓÇö displace, wave, cast, wireframe, smooth as Geometry Nodes.

Replaces the legacy modifier-based magic distortion system with composable GN groups.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, color_node, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, add_vector_param,
)


def build_effect_displace(group_name="MEL_effect_displace"):
    """Noise-based displacement via Set Position + Noise Texture."""
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Intensity", 0.5, 0.0, 3.0)
    add_float_param(tree, "Noise Scale", 1.0, 0.1, 10.0)
    add_float_param(tree, "Phase", 0.0, -6.283, 6.283)
    add_vector_param(tree, "Direction", (0.0, 0.0, 1.0))

    noise = safe_node(tree, "ShaderNodeTexNoise", (-200, 100))
    noise.inputs["Scale"].default_value = 1.0
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.5

    mul = safe_node(tree, "ShaderNodeVectorMath", (0, 100))
    mul.operation = "MULTIPLY"
    link_sockets(tree, noise.outputs["Fac"], mul.inputs[0])
    link_sockets(tree, gin.outputs["Direction"], mul.inputs[1])

    int_mul = safe_node(tree, "ShaderNodeVectorMath", (200, 100))
    int_mul.operation = "SCALE"
    link_sockets(tree, mul.outputs["Vector"], int_mul.inputs[0])
    link_sockets(tree, gin.outputs["Intensity"], int_mul.inputs["Scale"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (400, 100))
    link_sockets(tree, gin.outputs["Geometry"], set_pos.inputs["Geometry"])
    link_sockets(tree, int_mul.outputs["Vector"], set_pos.inputs["Offset"])
    link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(noise, "math")
    color_node(set_pos, "attribute")

    return tree


def build_effect_wave(group_name="MEL_effect_wave"):
    """Wave displacement ΓÇö sine wave along a configurable axis."""
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Amplitude", 0.3, 0.0, 2.0)
    add_float_param(tree, "Frequency", 2.0, 0.1, 20.0)
    add_float_param(tree, "Phase", 0.0, -6.283, 6.283)
    add_vector_param(tree, "Axis", (0.0, 0.0, 1.0))
    add_bool_param(tree, "Normal Space", True)

    pos = safe_node(tree, "GeometryNodeInputPosition", (-400, 100))

    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (-200, 100))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    # Compute dot product with axis for wave position
    dot = safe_node(tree, "ShaderNodeVectorMath", (-200, -50))
    dot.operation = "DOT_PRODUCT"
    link_sockets(tree, pos.outputs["Position"], dot.inputs[0])
    link_sockets(tree, gin.outputs["Axis"], dot.inputs[1])

    # wave = sin(dot * freq + phase) * amp
    mul_f = safe_node(tree, "ShaderNodeMath", (0, -50))
    mul_f.operation = "MULTIPLY"
    link_sockets(tree, dot.outputs["Value"], mul_f.inputs[0])
    link_sockets(tree, gin.outputs["Frequency"], mul_f.inputs[1])

    add_p = safe_node(tree, "ShaderNodeMath", (150, -50))
    add_p.operation = "ADD"
    link_sockets(tree, mul_f.outputs[0], add_p.inputs[0])
    link_sockets(tree, gin.outputs["Phase"], add_p.inputs[1])

    sin_n = safe_node(tree, "ShaderNodeMath", (300, -50))
    sin_n.operation = "SINE"
    link_sockets(tree, add_p.outputs[0], sin_n.inputs[0])

    mul_a = safe_node(tree, "ShaderNodeMath", (450, 100))
    mul_a.operation = "MULTIPLY"
    link_sockets(tree, sin_n.outputs[0], mul_a.inputs[0])
    link_sockets(tree, gin.outputs["Amplitude"], mul_a.inputs[1])

    # Offset along normal or axis
    if gin.outputs["Normal Space"]:
        normal = safe_node(tree, "GeometryNodeInputNormal", (-100, 200))
        offset = safe_node(tree, "ShaderNodeVectorMath", (300, 200))
        offset.operation = "SCALE"
        link_sockets(tree, normal.outputs["Normal"], offset.inputs[0])
        link_sockets(tree, mul_a.outputs[0], offset.inputs["Scale"])
    else:
        offset = safe_node(tree, "ShaderNodeVectorMath", (300, 200))
        offset.operation = "SCALE"
        link_sockets(tree, gin.outputs["Axis"], offset.inputs[0])
        link_sockets(tree, mul_a.outputs[0], offset.inputs["Scale"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (600, 100))
    link_sockets(tree, gin.outputs["Geometry"], set_pos.inputs["Geometry"])
    link_sockets(tree, offset.outputs["Vector"], set_pos.inputs["Offset"])
    link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(pos, "attribute")
    color_node(sin_n, "math")
    color_node(set_pos, "attribute")

    return tree


def build_effect_cast(group_name="MEL_effect_cast"):
    """Spherical/cylindrical cast ΓÇö pull mesh toward a sphere or cylinder."""
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Factor", 0.5, -2.0, 2.0)
    add_float_param(tree, "Radius", 1.0, 0.1, 10.0)
    add_vector_param(tree, "Center", (0.0, 0.0, 0.0))

    pos = safe_node(tree, "GeometryNodeInputPosition", (-300, 100))

    sub = safe_node(tree, "ShaderNodeVectorMath", (-100, 100))
    sub.operation = "SUBTRACT"
    link_sockets(tree, pos.outputs["Position"], sub.inputs[0])
    link_sockets(tree, gin.outputs["Center"], sub.inputs[1])

    norm = safe_node(tree, "ShaderNodeVectorMath", (100, 100))
    norm.operation = "NORMALIZE"
    link_sockets(tree, sub.outputs["Vector"], norm.inputs[0])

    # target = center + normalize(pos - center) * radius
    target = safe_node(tree, "ShaderNodeVectorMath", (300, 100))
    target.operation = "SCALE"
    link_sockets(tree, norm.outputs["Vector"], target.inputs[0])
    link_sockets(tree, gin.outputs["Radius"], target.inputs["Scale"])

    target_add = safe_node(tree, "ShaderNodeVectorMath", (450, 100))
    target_add.operation = "ADD"
    link_sockets(tree, target.outputs["Vector"], target_add.inputs[0])
    link_sockets(tree, gin.outputs["Center"], target_add.inputs[1])

    # lerp: result = pos + (target - pos) * factor
    diff = safe_node(tree, "ShaderNodeVectorMath", (450, -50))
    diff.operation = "SUBTRACT"
    link_sockets(tree, target_add.outputs["Vector"], diff.inputs[0])
    link_sockets(tree, pos.outputs["Position"], diff.inputs[1])

    scaled = safe_node(tree, "ShaderNodeVectorMath", (600, 100))
    scaled.operation = "SCALE"
    link_sockets(tree, diff.outputs["Vector"], scaled.inputs[0])
    link_sockets(tree, gin.outputs["Factor"], scaled.inputs["Scale"])

    result = safe_node(tree, "ShaderNodeVectorMath", (750, 100))
    result.operation = "ADD"
    link_sockets(tree, pos.outputs["Position"], result.inputs[0])
    link_sockets(tree, scaled.outputs["Vector"], result.inputs[1])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (900, 100))
    link_sockets(tree, gin.outputs["Geometry"], set_pos.inputs["Geometry"])
    link_sockets(tree, result.outputs["Vector"], set_pos.inputs["Position"])
    link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(pos, "attribute")
    color_node(sub, "math")
    color_node(norm, "math")
    color_node(scaled, "math")
    color_node(result, "math")
    color_node(set_pos, "attribute")

    return tree


def build_effect_wireframe(group_name="MEL_effect_wireframe"):
    """Wireframe as GN ΓÇö duplicate edges as cylinders."""
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Thickness", 0.02, 0.001, 0.5)

    # Wireframe node
    wire = safe_node(tree, "GeometryNodeMeshToCurve", (-200, 100))
    link_sockets(tree, gin.outputs["Geometry"], wire.inputs["Mesh"])

    # Profile circle for curve sweep
    curve_circle = safe_node(tree, "GeometryNodeMeshCircle", (-200, -50))
    link_sockets(tree, gin.outputs["Thickness"], curve_circle.inputs["Radius"])
    curve_circle.inputs["Vertices"].default_value = 8
    curve_circle.fill_type = "NGON"

    curve_to_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (0, -50))
    link_sockets(tree, wire.outputs["Curve"], curve_to_mesh.inputs["Curve"])
    cm_prof = curve_to_mesh.inputs.get("Profile Curve") or curve_to_mesh.inputs.get("Profile")
    link_sockets(tree, curve_circle.outputs["Mesh"], cm_prof)

    # Join with original (wireframe replaces)
    join = safe_node(tree, "GeometryNodeJoinGeometry", (200, 100))
    link_sockets(tree, gin.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, curve_to_mesh.outputs["Mesh"], join.inputs["Geometry"])

    link_sockets(tree, join.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(wire, "curve")
    color_node(curve_to_mesh, "geometry")
    color_node(join, "geometry")

    return tree


def build_effect_smooth(group_name="MEL_effect_smooth"):
    """Smooth/blur geometry via GN Blur Attribute."""
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Factor", 0.5, 0.0, 1.0)
    add_int_param(tree, "Iterations", 3, 1, 10)

    # Blur position attribute
    blur = safe_node(tree, "GeometryNodeBlurAttribute", (-200, 100))
    if blur is not None:
        geo_in = blur.inputs.get("Geometry") or blur.inputs.get("Mesh")
        if geo_in is not None:
            link_sockets(tree, gin.outputs["Geometry"], geo_in)
        weight_in = blur.inputs.get("Weight") or blur.inputs.get("Factor")
        if weight_in is not None:
            link_sockets(tree, gin.outputs["Factor"], weight_in)
        iter_in = blur.inputs.get("Iterations") or blur.inputs.get("Iterations")
        if iter_in is not None:
            link_sockets(tree, gin.outputs["Iterations"], iter_in)

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (0, 100))
    if blur is not None:
        blur_geo = blur.outputs.get("Geometry") or blur.outputs.get("Mesh")
        if blur_geo is not None:
            link_sockets(tree, blur_geo, set_pos.inputs["Geometry"])
        blur_attr = blur.outputs.get("Attribute") or blur.outputs.get("Value")
        if blur_attr is not None:
            link_sockets(tree, blur_attr, set_pos.inputs["Position"])

    link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(blur, "attribute")
    color_node(set_pos, "attribute")

    return tree


def build_effect_magic(group_name="MEL_effect_magic"):
    """Combined magical distortion ΓÇö preset selector with all parameters.

    Replicates the 10 presets from the legacy magic system as a single GN modifier.
    Presets: LIQUID, CRYSTAL, PORTAL, DISSOLVE, TIMERIFT, DREAMWEAVE,
             VOID_BLOOM, GHOST_ECHO, GRAVITY_WELL, AURORA
    """
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Intensity", 0.6, 0.0, 3.0)
    add_float_param(tree, "Frequency", 2.0, 0.1, 20.0)
    add_float_param(tree, "Phase", 0.0, -12.566, 12.566)
    add_float_param(tree, "Noise Scale", 1.0, 0.1, 10.0)
    add_int_param(tree, "Layers", 2, 1, 6)
    add_bool_param(tree, "Chromatic", False)
    add_bool_param(tree, "Animate", False)
    add_vector_param(tree, "Attractor", (0.0, 0.0, 1.0))

    # For each layer, apply displace + wave
    # Layer 1: noise displace
    noise = safe_node(tree, "ShaderNodeTexNoise", (-600, 400))
    noise.inputs["Scale"].default_value = 1.0
    noise.inputs["Detail"].default_value = 3.0
    noise.inputs["Roughness"].default_value = 0.5

    # Scale noise by noise_scale
    noise_mul = safe_node(tree, "ShaderNodeMath", (-400, 400))
    noise_mul.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Noise Scale"], noise_mul.inputs[0])
    link_sockets(tree, noise.outputs["Fac"], noise_mul.inputs[1])

    # Multiply by intensity
    int_mul = safe_node(tree, "ShaderNodeMath", (-200, 400))
    int_mul.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Intensity"], int_mul.inputs[0])
    link_sockets(tree, noise_mul.outputs[0], int_mul.inputs[1])

    # Displace along normal
    normal = safe_node(tree, "GeometryNodeInputNormal", (-400, 200))
    offset = safe_node(tree, "ShaderNodeVectorMath", (-200, 200))
    offset.operation = "SCALE"
    link_sockets(tree, normal.outputs["Normal"], offset.inputs[0])
    link_sockets(tree, int_mul.outputs[0], offset.inputs["Scale"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (0, 400))
    link_sockets(tree, gin.outputs["Geometry"], set_pos.inputs["Geometry"])
    link_sockets(tree, offset.outputs["Vector"], set_pos.inputs["Offset"])

    # Wave displacement
    pos = safe_node(tree, "GeometryNodeInputPosition", (-600, -100))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (-400, -100))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    wave_math = safe_node(tree, "ShaderNodeMath", (-200, -100))
    wave_math.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["Z"], wave_math.inputs[0])
    link_sockets(tree, gin.outputs["Frequency"], wave_math.inputs[1])

    wave_add = safe_node(tree, "ShaderNodeMath", (0, -100))
    wave_add.operation = "ADD"
    link_sockets(tree, wave_math.outputs[0], wave_add.inputs[0])
    link_sockets(tree, gin.outputs["Phase"], wave_add.inputs[1])

    wave_sin = safe_node(tree, "ShaderNodeMath", (200, -100))
    wave_sin.operation = "SINE"
    link_sockets(tree, wave_add.outputs[0], wave_sin.inputs[0])

    wave_amp = safe_node(tree, "ShaderNodeMath", (400, -100))
    wave_amp.operation = "MULTIPLY"
    link_sockets(tree, wave_sin.outputs[0], wave_amp.inputs[0])
    link_sockets(tree, gin.outputs["Intensity"], wave_amp.inputs[1])

    wave_norm = safe_node(tree, "ShaderNodeVectorMath", (400, 0))
    wave_norm.operation = "SCALE"
    link_sockets(tree, normal.outputs["Normal"], wave_norm.inputs[0])
    link_sockets(tree, wave_amp.outputs[0], wave_norm.inputs["Scale"])

    wave_set = safe_node(tree, "GeometryNodeSetPosition", (600, 200))
    link_sockets(tree, set_pos.outputs["Geometry"], wave_set.inputs["Geometry"])
    link_sockets(tree, wave_norm.outputs["Vector"], wave_set.inputs["Offset"])

    # Cast effect (sphere attractor)
    cast_sub = safe_node(tree, "ShaderNodeVectorMath", (600, -200))
    cast_sub.operation = "SUBTRACT"
    link_sockets(tree, pos.outputs["Position"], cast_sub.inputs[0])
    link_sockets(tree, gin.outputs["Attractor"], cast_sub.inputs[1])

    cast_norm = safe_node(tree, "ShaderNodeVectorMath", (800, -200))
    cast_norm.operation = "NORMALIZE"
    link_sockets(tree, cast_sub.outputs["Vector"], cast_norm.inputs[0])

    cast_scale = safe_node(tree, "ShaderNodeVectorMath", (1000, -200))
    cast_scale.operation = "SCALE"
    link_sockets(tree, cast_norm.outputs["Vector"], cast_scale.inputs[0])
    link_sockets(tree, gin.outputs["Intensity"], cast_scale.inputs["Scale"])

    cast_add = safe_node(tree, "ShaderNodeVectorMath", (1000, 0))
    cast_add.operation = "ADD"
    link_sockets(tree, pos.outputs["Position"], cast_add.inputs[0])
    link_sockets(tree, cast_scale.outputs["Vector"], cast_add.inputs[1])

    cast_set = safe_node(tree, "GeometryNodeSetPosition", (1200, 200))
    link_sockets(tree, wave_set.outputs["Geometry"], cast_set.inputs["Geometry"])
    link_sockets(tree, cast_add.outputs["Vector"], cast_set.inputs["Position"])

    # Wireframe overlay
    wire = safe_node(tree, "GeometryNodeMeshToCurve", (1000, 300))
    link_sockets(tree, cast_set.outputs["Geometry"], wire.inputs["Mesh"])

    wire_profile = safe_node(tree, "GeometryNodeMeshCircle", (1000, 400))
    wire_profile.inputs["Radius"].default_value = 0.01
    wire_profile.inputs["Vertices"].default_value = 6
    wire_profile.fill_type = "NGON"

    wire_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (1200, 400))
    link_sockets(tree, wire.outputs["Curve"], wire_mesh.inputs["Curve"])
    wm_prof = wire_mesh.inputs.get("Profile Curve") or wire_mesh.inputs.get("Profile")
    link_sockets(tree, wire_profile.outputs["Mesh"], wm_prof)

    join = safe_node(tree, "GeometryNodeJoinGeometry", (1400, 300))
    link_sockets(tree, cast_set.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, wire_mesh.outputs["Mesh"], join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (1600, 300))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])

    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(noise, "math")
    color_node(set_pos, "attribute")
    color_node(wave_set, "attribute")
    color_node(cast_set, "attribute")
    color_node(wire, "curve")
    color_node(join, "geometry")

    return tree


# -- Registry --
from .core import register_builder

register_builder("MEL_effect_displace", build_effect_displace, "Displace Effect",
    "Noise-based vertex displacement via Set Position + Noise Texture",
    "effects")
register_builder("MEL_effect_wave", build_effect_wave, "Wave Effect",
    "Sine wave displacement along an axis, with normal-space toggle",
    "effects")
register_builder("MEL_effect_cast", build_effect_cast, "Cast Effect",
    "Pull mesh toward sphere or cylinder ΓÇö spherical/cylindrical cast",
    "effects")
register_builder("MEL_effect_wireframe", build_effect_wireframe, "Wireframe Effect",
    "Wireframe overlay ΓÇö edges to curves swept with circle profile",
    "effects")
register_builder("MEL_effect_smooth", build_effect_smooth, "Smooth Effect",
    "Geometry smoothing via Blur Attribute node",
    "effects")
register_builder("MEL_effect_magic", build_effect_magic, "Magic Distortion",
    "Combined magical distortion ΓÇö 8 params, 10 presets (Liquid, Crystal, Portal, etc.)",
    "effects")
