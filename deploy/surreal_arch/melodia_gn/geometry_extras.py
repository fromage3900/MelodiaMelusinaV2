"""Geometry toolkit extras -- vortex twist, radial wave, mesh tools, attribute math, primitives, profiles, operations.

Composable GN group builders that extend the core toolkit lanes with
proven node/socket patterns only: Set Position, Extrude, Boolean,
Merge By Distance, Blur Attribute, Named Attribute, Switch, Compare.

Every builder follows the melodia_gn convention: `register_builder`
at module end, MEL_ tree ids as default group names, label_tree frames.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, add_vector_param,
    add_mesh_torus_linked, make_group_input,
)


# ---------------------------------------------------------------- effects


def build_vortex_twist(group_name="MEL_vortex_twist"):
    """Twist displacement around the Z axis.

    Angle of rotation at any vertex is (Z - Center) * Twist, so the mesh
    spirals with height. Stores the per-vertex twist angle as a float
    named attribute for downstream shading.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Twist", 0.5, -3.141, 3.141)
    add_float_param(tree, "Center", 0.0, -100.0, 100.0)

    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 500, by + 100))
    color_node(pos, "attribute")

    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 300, by + 100))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    z_off = safe_node(tree, "ShaderNodeMath", (bx - 150, by + 150))
    z_off.operation = "SUBTRACT"
    link_sockets(tree, sep.outputs["Z"], z_off.inputs[0])
    link_sockets(tree, gin.outputs["Center"], z_off.inputs[1])

    ang = safe_node(tree, "ShaderNodeMath", (bx, by + 150))
    ang.operation = "MULTIPLY"
    link_sockets(tree, z_off.outputs[0], ang.inputs[0])
    link_sockets(tree, gin.outputs["Twist"], ang.inputs[1])

    cos_a = safe_node(tree, "ShaderNodeMath", (bx + 150, by + 200))
    cos_a.operation = "COSINE"
    link_sockets(tree, ang.outputs[0], cos_a.inputs[0])

    sin_a = safe_node(tree, "ShaderNodeMath", (bx + 150, by + 100))
    sin_a.operation = "SINE"
    link_sockets(tree, ang.outputs[0], sin_a.inputs[0])

    x_cos = safe_node(tree, "ShaderNodeMath", (bx + 300, by + 200))
    x_cos.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], x_cos.inputs[0])
    link_sockets(tree, cos_a.outputs[0], x_cos.inputs[1])

    y_sin = safe_node(tree, "ShaderNodeMath", (bx + 300, by + 150))
    y_sin.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["Y"], y_sin.inputs[0])
    link_sockets(tree, sin_a.outputs[0], y_sin.inputs[1])

    x_rot = safe_node(tree, "ShaderNodeMath", (bx + 450, by + 180))
    x_rot.operation = "SUBTRACT"
    link_sockets(tree, x_cos.outputs[0], x_rot.inputs[0])
    link_sockets(tree, y_sin.outputs[0], x_rot.inputs[1])

    x_sin = safe_node(tree, "ShaderNodeMath", (bx + 300, by + 50))
    x_sin.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], x_sin.inputs[0])
    link_sockets(tree, sin_a.outputs[0], x_sin.inputs[1])

    y_cos = safe_node(tree, "ShaderNodeMath", (bx + 300, by))
    y_cos.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["Y"], y_cos.inputs[0])
    link_sockets(tree, cos_a.outputs[0], y_cos.inputs[1])

    y_rot = safe_node(tree, "ShaderNodeMath", (bx + 450, by + 30))
    y_rot.operation = "ADD"
    link_sockets(tree, x_sin.outputs[0], y_rot.inputs[0])
    link_sockets(tree, y_cos.outputs[0], y_rot.inputs[1])

    combine = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 600, by + 100))
    link_sockets(tree, x_rot.outputs[0], combine.inputs["X"])
    link_sockets(tree, y_rot.outputs[0], combine.inputs["Y"])
    link_sockets(tree, sep.outputs["Z"], combine.inputs["Z"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 800, by + 100))
    link_sockets(tree, gin.outputs["Geometry"], set_pos.inputs["Geometry"])
    link_sockets(tree, combine.outputs["Vector"], set_pos.inputs["Position"])

    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 1000, by + 100))
    store.data_type = "FLOAT"
    store.domain = "POINT"
    store.inputs["Name"].default_value = "twist"
    link_sockets(tree, set_pos.outputs["Geometry"], store.inputs["Geometry"])
    link_sockets(tree, ang.outputs[0], store.inputs["Value"])

    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(sep, "math")
    color_node(sin_a, "math")
    color_node(combine, "math")
    color_node(set_pos, "attribute")
    color_node(store, "attribute")

    return label_tree(tree, "MEL_vortex_twist", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Twist Math", "nodes": ("sine", "cosine", "multiply", "subtract"), "role": "math"},
        {"title": "Displace", "nodes": ("set", "position"), "role": "attribute"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_radial_wave(group_name="MEL_radial_wave"):
    """Radial gradient wave -- concentric ripple displacement along normals.

    Offset is sin(distance * Frequency + Phase) * Amplitude along the
    face normal, so flat grids become target-like ripples.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Amplitude", 0.2, 0.0, 2.0)
    add_float_param(tree, "Frequency", 4.0, 0.1, 40.0)
    add_float_param(tree, "Phase", 0.0, -6.283, 6.283)

    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 500, by + 100))
    color_node(pos, "attribute")

    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 300, by + 100))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    x2 = safe_node(tree, "ShaderNodeMath", (bx - 150, by + 150))
    x2.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], x2.inputs[0])
    link_sockets(tree, sep.outputs["X"], x2.inputs[1])

    y2 = safe_node(tree, "ShaderNodeMath", (bx - 150, by + 50))
    y2.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["Y"], y2.inputs[0])
    link_sockets(tree, sep.outputs["Y"], y2.inputs[1])

    r2 = safe_node(tree, "ShaderNodeMath", (bx, by + 100))
    r2.operation = "ADD"
    link_sockets(tree, x2.outputs[0], r2.inputs[0])
    link_sockets(tree, y2.outputs[0], r2.inputs[1])

    rad = safe_node(tree, "ShaderNodeMath", (bx + 150, by + 100))
    rad.operation = "SQRT"
    link_sockets(tree, r2.outputs[0], rad.inputs[0])

    ph = safe_node(tree, "ShaderNodeMath", (bx + 300, by + 150))
    ph.operation = "MULTIPLY"
    link_sockets(tree, rad.outputs[0], ph.inputs[0])
    link_sockets(tree, gin.outputs["Frequency"], ph.inputs[1])

    ph2 = safe_node(tree, "ShaderNodeMath", (bx + 450, by + 150))
    ph2.operation = "ADD"
    link_sockets(tree, ph.outputs[0], ph2.inputs[0])
    link_sockets(tree, gin.outputs["Phase"], ph2.inputs[1])

    wave = safe_node(tree, "ShaderNodeMath", (bx + 600, by + 150))
    wave.operation = "SINE"
    link_sockets(tree, ph2.outputs[0], wave.inputs[0])

    amp = safe_node(tree, "ShaderNodeMath", (bx + 750, by + 150))
    amp.operation = "MULTIPLY"
    link_sockets(tree, wave.outputs[0], amp.inputs[0])
    link_sockets(tree, gin.outputs["Amplitude"], amp.inputs[1])

    normal = safe_node(tree, "GeometryNodeInputNormal", (bx + 600, by - 50))
    color_node(normal, "geometry")

    offset = safe_node(tree, "ShaderNodeVectorMath", (bx + 900, by + 100))
    offset.operation = "SCALE"
    link_sockets(tree, normal.outputs["Normal"], offset.inputs[0])
    link_sockets(tree, amp.outputs[0], offset.inputs["Scale"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 1100, by + 100))
    link_sockets(tree, gin.outputs["Geometry"], set_pos.inputs["Geometry"])
    link_sockets(tree, offset.outputs["Vector"], set_pos.inputs["Offset"])
    link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(sep, "math")
    color_node(rad, "math")
    color_node(wave, "math")
    color_node(offset, "math")
    color_node(set_pos, "attribute")

    return label_tree(tree, "MEL_radial_wave", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Radial Math", "nodes": ("sqrt", "sine", "multiply", "add"), "role": "math"},
        {"title": "Displace", "nodes": ("offset", "set", "position"), "role": "attribute"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# ---------------------------------------------------------------- mesh_tools


def build_shell_thicken(group_name="MEL_shell_thicken"):
    """Shell thicken -- offset every face along its normal by Thickness.

    With Solid enabled the original surface is joined back, producing a
    closed shell; with Solid off you get a pure offset surface.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Thickness", 0.05, 0.0, 2.0)
    add_bool_param(tree, "Solid", True)

    extrude = safe_node(tree, "GeometryNodeExtrudeMesh", (bx, by))
    extrude.mode = "FACES"
    link_sockets(tree, gin.outputs["Geometry"], extrude.inputs["Mesh"])
    link_sockets(tree, gin.outputs["Thickness"], extrude.inputs["Offset Scale"])

    if gin.outputs["Solid"]:
        join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200, by))
        link_sockets(tree, gin.outputs["Geometry"], join.inputs["Geometry"])
        link_sockets(tree, extrude.outputs["Mesh"], join.inputs["Geometry"])
        shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 400, by))
        link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    else:
        shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 200, by))
        link_sockets(tree, extrude.outputs["Mesh"], shade.inputs["Geometry"])
    shade.inputs["Shade Smooth"].default_value = True

    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(extrude, "geometry")
    color_node(shade, "geometry")

    return label_tree(tree, "MEL_shell_thicken", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Thicken", "nodes": ("extrude",), "role": "geometry"},
        {"title": "Output", "nodes": ("shade", "Group Output"), "role": "output"},
    ])


def build_edge_ring_inset(group_name="MEL_edge_ring_inset"):
    """Edge-ring inset -- extrude every edge by Width to carve inset rings.

    On closed meshes (cubes, cylinders) this creates the classic inset
    edge-loop look without touching faces.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Width", 0.05, 0.0, 2.0)

    extrude = safe_node(tree, "GeometryNodeExtrudeMesh", (bx, by))
    extrude.mode = "EDGES"
    link_sockets(tree, gin.outputs["Geometry"], extrude.inputs["Mesh"])
    link_sockets(tree, gin.outputs["Width"], extrude.inputs["Offset Scale"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 200, by))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, extrude.outputs["Mesh"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(extrude, "geometry")
    color_node(shade, "geometry")

    return label_tree(tree, "MEL_edge_ring_inset", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Edge Extrude", "nodes": ("extrude",), "role": "geometry"},
        {"title": "Output", "nodes": ("shade", "Group Output"), "role": "output"},
    ])


def build_symmetry_weld(group_name="MEL_symmetry_weld"):
    """Symmetry weld -- mirror geometry across an axis and weld the seam.

    Mirrors about the selected axis (0=X, 1=Y, 2=Z), joins with the
    original, and merges coincident vertices by Weld Distance.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Axis", 0, 0, 2)
    add_float_param(tree, "Weld Distance", 0.001, 0.0, 1.0)

    mirror_x = safe_node(tree, "GeometryNodeTransform", (bx - 300, by + 300))
    mirror_x.inputs["Scale"].default_value = (-1.0, 1.0, 1.0)
    link_sockets(tree, gin.outputs["Geometry"], mirror_x.inputs["Geometry"])

    mirror_y = safe_node(tree, "GeometryNodeTransform", (bx - 300, by + 150))
    mirror_y.inputs["Scale"].default_value = (1.0, -1.0, 1.0)
    link_sockets(tree, gin.outputs["Geometry"], mirror_y.inputs["Geometry"])

    mirror_z = safe_node(tree, "GeometryNodeTransform", (bx - 300, by))
    mirror_z.inputs["Scale"].default_value = (1.0, 1.0, -1.0)
    link_sockets(tree, gin.outputs["Geometry"], mirror_z.inputs["Geometry"])

    cmp_1 = safe_node(tree, "FunctionNodeCompare", (bx - 100, by + 220))
    cmp_1.data_type = "INT"
    cmp_1.operation = "GREATER_THAN"
    link_sockets(tree, gin.outputs["Axis"], cmp_1.inputs["A"])
    cmp_1.inputs["B"].default_value = 0

    sw_1 = safe_node(tree, "GeometryNodeSwitch", (bx + 100, by + 220))
    sw_1.input_type = "GEOMETRY"
    link_sockets(tree, mirror_x.outputs["Geometry"], sw_1.inputs["False"])
    link_sockets(tree, mirror_y.outputs["Geometry"], sw_1.inputs["True"])
    link_sockets(tree, cmp_1.outputs["Result"], sw_1.inputs["Switch"])

    cmp_2 = safe_node(tree, "FunctionNodeCompare", (bx + 100, by + 100))
    cmp_2.data_type = "INT"
    cmp_2.operation = "GREATER_THAN"
    link_sockets(tree, gin.outputs["Axis"], cmp_2.inputs["A"])
    cmp_2.inputs["B"].default_value = 1

    sw_2 = safe_node(tree, "GeometryNodeSwitch", (bx + 300, by + 160))
    sw_2.input_type = "GEOMETRY"
    link_sockets(tree, sw_1.outputs["Output"], sw_2.inputs["False"])
    link_sockets(tree, mirror_z.outputs["Geometry"], sw_2.inputs["True"])
    link_sockets(tree, cmp_2.outputs["Result"], sw_2.inputs["Switch"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 500, by + 200))
    link_sockets(tree, gin.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, sw_2.outputs["Output"], join.inputs["Geometry"])

    weld = safe_node(tree, "GeometryNodeMergeByDistance", (bx + 700, by + 200))
    link_sockets(tree, join.outputs["Geometry"], weld.inputs["Geometry"])
    link_sockets(tree, gin.outputs["Weld Distance"], weld.inputs["Distance"])

    link_sockets(tree, weld.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(mirror_x, "instance")
    color_node(mirror_y, "instance")
    color_node(mirror_z, "instance")
    color_node(join, "geometry")
    color_node(weld, "geometry")

    return label_tree(tree, "MEL_symmetry_weld", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Mirror", "nodes": ("transform", "mirror", "switch"), "role": "instance"},
        {"title": "Weld", "nodes": ("merge", "weld"), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_vertex_relax(group_name="MEL_vertex_relax"):
    """Vertex cluster relax -- blur positions with per-vertex noise jitter.

    Smooths vertex clusters toward the local average while Jitter mixes
    in a noise field so dense clusters relax without collapsing flat.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Factor", 0.5, 0.0, 1.0)
    add_int_param(tree, "Iterations", 2, 1, 10)
    add_float_param(tree, "Jitter", 0.0, 0.0, 1.0)
    add_float_param(tree, "Jitter Scale", 2.0, 0.1, 20.0)

    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 500, by + 100))
    color_node(pos, "attribute")

    blur = safe_node(tree, "GeometryNodeBlurAttribute", (bx - 300, by + 100))
    blur.data_type = "FLOAT_VECTOR"
    link_sockets(tree, pos.outputs["Position"], blur.inputs["Value"])
    link_sockets(tree, gin.outputs["Iterations"], blur.inputs["Iterations"])
    link_sockets(tree, gin.outputs["Factor"], blur.inputs["Weight"])

    noise = safe_node(tree, "ShaderNodeTexNoise", (bx - 300, by - 100))
    noise.inputs["Detail"].default_value = 1.0
    noise.inputs["Roughness"].default_value = 0.5
    link_sockets(tree, pos.outputs["Position"], noise.inputs["Vector"])
    link_sockets(tree, gin.outputs["Jitter Scale"], noise.inputs["Scale"])

    jit_mul = safe_node(tree, "ShaderNodeMath", (bx - 100, by - 100))
    jit_mul.operation = "MULTIPLY"
    link_sockets(tree, noise.outputs["Fac"], jit_mul.inputs[0])
    link_sockets(tree, gin.outputs["Jitter"], jit_mul.inputs[1])

    mix = safe_node(tree, "ShaderNodeMix", (bx - 100, by + 50))
    mix.data_type = "VECTOR"
    mix.clamp_result = True
    link_sockets(tree, pos.outputs["Position"], mix.inputs["A"])
    link_sockets(tree, blur.outputs["Value"], mix.inputs["B"])
    link_sockets(tree, jit_mul.outputs[0], mix.inputs["Factor"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 100, by + 100))
    link_sockets(tree, gin.outputs["Geometry"], set_pos.inputs["Geometry"])
    link_sockets(tree, mix.outputs[0], set_pos.inputs["Position"])
    link_sockets(tree, set_pos.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(blur, "attribute")
    color_node(noise, "math")
    color_node(mix, "math")
    color_node(set_pos, "attribute")

    return label_tree(tree, "MEL_vertex_relax", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Blur Position", "nodes": ("blur", "position"), "role": "attribute"},
        {"title": "Jitter Mix", "nodes": ("noise", "mix"), "role": "math"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# ---------------------------------------------------------------- math_attrs


def build_attr_ramp_mix(group_name="MEL_attr_ramp_mix"):
    """Three-stop ramp blend from a float attribute.

    Reads a float attribute (default name 'ramp_t'), maps it through a
    Start / Middle / End ramp with a smooth crossfade at Mid Point, and
    stores the result back as 'ramp_out'.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Start", 0.0, 0.0, 10.0)
    add_float_param(tree, "Middle", 0.5, 0.0, 10.0)
    add_float_param(tree, "End", 1.0, 0.0, 10.0)
    add_float_param(tree, "Mid Point", 0.5, 0.01, 0.99)

    attr = safe_node(tree, "GeometryNodeInputNamedAttribute", (bx - 500, by + 150))
    attr.data_type = "FLOAT"
    attr.inputs["Name"].default_value = "ramp_t"
    color_node(attr, "attribute")

    # First half: t in [0, Mid] maps Start -> Middle
    t1 = safe_node(tree, "ShaderNodeMath", (bx - 300, by + 200))
    t1.operation = "DIVIDE"
    link_sockets(tree, attr.outputs["Attribute"], t1.inputs[0])
    link_sockets(tree, gin.outputs["Mid Point"], t1.inputs[1])

    mix_01 = safe_node(tree, "ShaderNodeMix", (bx - 100, by + 200))
    mix_01.data_type = "FLOAT"
    mix_01.clamp_result = True
    link_sockets(tree, gin.outputs["Start"], mix_01.inputs["A"])
    link_sockets(tree, gin.outputs["Middle"], mix_01.inputs["B"])
    link_sockets(tree, t1.outputs[0], mix_01.inputs["Factor"])

    # Second half: t in [Mid, 1] maps Middle -> End
    t2 = safe_node(tree, "ShaderNodeMath", (bx - 300, by + 50))
    t2.operation = "SUBTRACT"
    link_sockets(tree, attr.outputs["Attribute"], t2.inputs[0])
    link_sockets(tree, gin.outputs["Mid Point"], t2.inputs[1])

    t2b = safe_node(tree, "ShaderNodeMath", (bx - 150, by + 50))
    t2b.operation = "DIVIDE"
    link_sockets(tree, t2.outputs[0], t2b.inputs[0])
    t2_den = safe_node(tree, "ShaderNodeMath", (bx - 300, by))
    t2_den.operation = "SUBTRACT"
    t2_den.inputs[0].default_value = 1.0
    link_sockets(tree, gin.outputs["Mid Point"], t2_den.inputs[1])
    link_sockets(tree, t2_den.outputs[0], t2b.inputs[1])

    mix_12 = safe_node(tree, "ShaderNodeMix", (bx + 50, by + 50))
    mix_12.data_type = "FLOAT"
    mix_12.clamp_result = True
    link_sockets(tree, gin.outputs["Middle"], mix_12.inputs["A"])
    link_sockets(tree, gin.outputs["End"], mix_12.inputs["B"])
    link_sockets(tree, t2b.outputs[0], mix_12.inputs["Factor"])

    # Crossfade weight: 0 before Mid, ramps to 1 after
    h_off = safe_node(tree, "ShaderNodeMath", (bx + 350, by + 100))
    h_off.operation = "SUBTRACT"
    link_sockets(tree, t1.outputs[0], h_off.inputs[0])
    h_off.inputs[1].default_value = 1.0

    h_clamp = safe_node(tree, "ShaderNodeMath", (bx + 500, by + 100))
    h_clamp.operation = "MAXIMUM"
    link_sockets(tree, h_off.outputs[0], h_clamp.inputs[0])
    h_clamp.inputs[1].default_value = 0.0

    mix_final = safe_node(tree, "ShaderNodeMix", (bx + 650, by + 150))
    mix_final.data_type = "FLOAT"
    mix_final.clamp_result = True
    link_sockets(tree, mix_01.outputs[0], mix_final.inputs["A"])
    link_sockets(tree, mix_12.outputs[0], mix_final.inputs["B"])
    link_sockets(tree, h_clamp.outputs[0], mix_final.inputs["Factor"])

    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 850, by + 150))
    store.data_type = "FLOAT"
    store.domain = "POINT"
    store.inputs["Name"].default_value = "ramp_out"
    link_sockets(tree, gin.outputs["Geometry"], store.inputs["Geometry"])
    link_sockets(tree, mix_final.outputs[0], store.inputs["Value"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(mix_01, "math")
    color_node(mix_12, "math")
    color_node(mix_final, "math")
    color_node(store, "attribute")

    return label_tree(tree, "MEL_attr_ramp_mix", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Ramp Blend", "nodes": ("mix", "attribute"), "role": "math"},
        {"title": "Store", "nodes": ("store",), "role": "attribute"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_attr_vector_rotate(group_name="MEL_attr_vector_rotate"):
    """Rotate a named vector attribute around the Z axis.

    Reads a FLOAT_VECTOR attribute (default name 'vec'), applies the
    rotation by Angle, and stores the result as 'rotated_vec'.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Angle", 1.5708, -6.283, 6.283)

    attr = safe_node(tree, "GeometryNodeInputNamedAttribute", (bx - 400, by + 100))
    attr.data_type = "FLOAT_VECTOR"
    attr.inputs["Name"].default_value = "vec"
    color_node(attr, "attribute")

    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 200, by + 100))
    link_sockets(tree, attr.outputs["Attribute"], sep.inputs["Vector"])

    cos_a = safe_node(tree, "ShaderNodeMath", (bx, by + 150))
    cos_a.operation = "COSINE"
    link_sockets(tree, gin.outputs["Angle"], cos_a.inputs[0])

    sin_a = safe_node(tree, "ShaderNodeMath", (bx, by + 50))
    sin_a.operation = "SINE"
    link_sockets(tree, gin.outputs["Angle"], sin_a.inputs[0])

    x_cos = safe_node(tree, "ShaderNodeMath", (bx + 150, by + 150))
    x_cos.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], x_cos.inputs[0])
    link_sockets(tree, cos_a.outputs[0], x_cos.inputs[1])

    y_sin = safe_node(tree, "ShaderNodeMath", (bx + 150, by + 100))
    y_sin.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["Y"], y_sin.inputs[0])
    link_sockets(tree, sin_a.outputs[0], y_sin.inputs[1])

    x_rot = safe_node(tree, "ShaderNodeMath", (bx + 300, by + 130))
    x_rot.operation = "SUBTRACT"
    link_sockets(tree, x_cos.outputs[0], x_rot.inputs[0])
    link_sockets(tree, y_sin.outputs[0], x_rot.inputs[1])

    x_sin = safe_node(tree, "ShaderNodeMath", (bx + 150, by))
    x_sin.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], x_sin.inputs[0])
    link_sockets(tree, sin_a.outputs[0], x_sin.inputs[1])

    y_cos = safe_node(tree, "ShaderNodeMath", (bx + 150, by - 50))
    y_cos.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["Y"], y_cos.inputs[0])
    link_sockets(tree, cos_a.outputs[0], y_cos.inputs[1])

    y_rot = safe_node(tree, "ShaderNodeMath", (bx + 300, by + 30))
    y_rot.operation = "ADD"
    link_sockets(tree, x_sin.outputs[0], y_rot.inputs[0])
    link_sockets(tree, y_cos.outputs[0], y_rot.inputs[1])

    combine = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 450, by + 80))
    link_sockets(tree, x_rot.outputs[0], combine.inputs["X"])
    link_sockets(tree, y_rot.outputs[0], combine.inputs["Y"])
    link_sockets(tree, sep.outputs["Z"], combine.inputs["Z"])

    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 650, by + 100))
    store.data_type = "FLOAT_VECTOR"
    store.domain = "POINT"
    store.inputs["Name"].default_value = "rotated_vec"
    link_sockets(tree, gin.outputs["Geometry"], store.inputs["Geometry"])
    link_sockets(tree, combine.outputs["Vector"], store.inputs["Value"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(sep, "math")
    color_node(sin_a, "math")
    color_node(combine, "math")
    color_node(store, "attribute")

    return label_tree(tree, "MEL_attr_vector_rotate", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Rotate Math", "nodes": ("sine", "cosine", "multiply"), "role": "math"},
        {"title": "Store", "nodes": ("store",), "role": "attribute"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_edge_band_weight(group_name="MEL_edge_band_weight"):
    """Per-edge banded falloff weight.

    Walks edges in bands of Band Width and writes weight = power(frac,
    Curve) inside each band (optionally inverted) as the 'edge_falloff'
    float attribute on the EDGE domain.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Band Width", 8, 1, 64)
    add_float_param(tree, "Curve", 1.0, 0.1, 5.0)
    add_bool_param(tree, "Invert", False)

    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 400, by + 100))
    color_node(idx, "attribute")

    band = safe_node(tree, "ShaderNodeMath", (bx - 200, by + 100))
    band.operation = "MODULO"
    link_sockets(tree, idx.outputs["Index"], band.inputs[0])
    link_sockets(tree, gin.outputs["Band Width"], band.inputs[1])

    frac = safe_node(tree, "ShaderNodeMath", (bx - 50, by + 100))
    frac.operation = "DIVIDE"
    link_sockets(tree, band.outputs[0], frac.inputs[0])
    link_sockets(tree, gin.outputs["Band Width"], frac.inputs[1])

    weight = safe_node(tree, "ShaderNodeMath", (bx + 100, by + 100))
    weight.operation = "POWER"
    link_sockets(tree, frac.outputs[0], weight.inputs[0])
    link_sockets(tree, gin.outputs["Curve"], weight.inputs[1])

    if gin.outputs["Invert"]:
        inv = safe_node(tree, "ShaderNodeMath", (bx + 250, by + 100))
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        link_sockets(tree, weight.outputs[0], inv.inputs[1])
        weight_out = inv.outputs[0]
    else:
        weight_out = weight.outputs[0]

    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 400, by + 100))
    store.data_type = "FLOAT"
    store.domain = "EDGE"
    store.inputs["Name"].default_value = "edge_falloff"
    link_sockets(tree, gin.outputs["Geometry"], store.inputs["Geometry"])
    link_sockets(tree, weight_out, store.inputs["Value"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(band, "math")
    color_node(weight, "math")
    color_node(store, "attribute")

    return label_tree(tree, "MEL_edge_band_weight", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Band Math", "nodes": ("modulo", "power", "divide"), "role": "math"},
        {"title": "Store", "nodes": ("store",), "role": "attribute"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# ---------------------------------------------------------------- primitives


def build_gear(group_name="MEL_gear"):
    """Star gear -- central disc with radially aligned tooth blocks.

    Teeth are instanced on a circle with Align-Euler-To-Vector so every
    tooth points outward, realized, and unioned with the disc.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Teeth", 12, 4, 64)
    add_float_param(tree, "Radius", 1.0, 0.1, 10.0)
    add_float_param(tree, "Tooth Width", 0.3, 0.01, 5.0)
    add_float_param(tree, "Tooth Depth", 0.35, 0.01, 5.0)
    add_float_param(tree, "Thickness", 0.2, 0.01, 2.0)

    disc = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 400, by + 200))
    link_sockets(tree, gin.outputs["Teeth"], disc.inputs["Vertices"])
    link_sockets(tree, gin.outputs["Radius"], disc.inputs["Radius"])
    link_sockets(tree, gin.outputs["Thickness"], disc.inputs["Depth"])
    disc.fill_type = "NGON"
    color_node(disc, "geometry")

    circle = safe_node(tree, "GeometryNodeMeshCircle", (bx - 400, by))
    link_sockets(tree, gin.outputs["Teeth"], circle.inputs["Vertices"])
    link_sockets(tree, gin.outputs["Radius"], circle.inputs["Radius"])
    circle.fill_type = "NONE"
    color_node(circle, "curve")

    tooth = safe_node(tree, "GeometryNodeMeshCube", (bx - 400, by - 150))
    link_float_to_vector(tree, gin.outputs["Tooth Width"], tooth, "Size", component=0, defaults=(0.0, 0.0, 0.0))
    link_float_to_vector(tree, gin.outputs["Tooth Depth"], tooth, "Size", component=1, defaults=(0.0, 0.0, 0.0))
    link_float_to_vector(tree, gin.outputs["Thickness"], tooth, "Size", component=2, defaults=(0.0, 0.0, 0.0))
    color_node(tooth, "geometry")

    align = safe_node(tree, "FunctionNodeAlignEulerToVector", (bx - 200, by - 150))
    align_pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 300, by - 200))
    link_sockets(tree, align_pos.outputs["Position"], align.inputs["Vector"])
    color_node(align, "math")

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 200, by))
    link_sockets(tree, circle.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, tooth.outputs["Mesh"], inst.inputs["Instance"])
    link_sockets(tree, align.outputs["Rotation"], inst.inputs["Rotation"])
    color_node(inst, "instance")

    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by))
    link_sockets(tree, inst.outputs["Instances"], realize.inputs["Geometry"])

    union = safe_node(tree, "GeometryNodeMeshBoolean", (bx + 200, by))
    link_sockets(tree, realize.outputs["Geometry"], union.inputs[0])
    link_sockets(tree, disc.outputs["Mesh"], union.inputs[1])
    union.operation = "UNION"
    color_node(union, "math")

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 400, by))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, union.outputs["Mesh"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(shade, "geometry")

    return label_tree(tree, "MEL_gear", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Disc", "nodes": ("cylinder", "disc"), "role": "geometry"},
        {"title": "Teeth", "nodes": ("circle", "instance", "align"), "role": "instance"},
        {"title": "Union", "nodes": ("boolean", "union"), "role": "math"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_stepped_pyramid(group_name="MEL_stepped_pyramid"):
    """Stepped pyramid -- stacked shrinking cubes with step gating.

    Up to eight steps are unrolled; each step is only included when
    Steps is greater than the step index, so the pyramid grows and
    shrinks cleanly.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Steps", 5, 1, 8)
    add_float_param(tree, "Base Size", 4.0, 0.5, 20.0)
    add_float_param(tree, "Step Height", 0.4, 0.05, 2.0)
    add_float_param(tree, "Shrink", 0.75, 0.5, 0.98)

    empty = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 600, by))
    color_node(empty, "geometry")

    parts = []
    for i in range(8):
        cube = safe_node(tree, "GeometryNodeMeshCube", (bx - 600, by + 120 - i * 160))
        try:
            cube.inputs["Size"].default_value = (4.0, 4.0, 0.4)
            cube.inputs["Vertices X"].default_value = 4
            cube.inputs["Vertices Y"].default_value = 4
            cube.inputs["Vertices Z"].default_value = 2
        except Exception:
            pass
        shrink_pow = safe_node(tree, "ShaderNodeMath", (bx - 900, by + 120 - i * 160))
        shrink_pow.operation = "POWER"
        shrink_pow.inputs[0].default_value = 0.75
        shrink_pow.inputs[1].default_value = float(i)
        link_sockets(tree, gin.outputs["Shrink"], shrink_pow.inputs[0])
        xy = safe_node(tree, "ShaderNodeMath", (bx - 750, by + 120 - i * 160))
        xy.operation = "MULTIPLY"
        xy.inputs[0].default_value = 4.0
        xy.inputs[1].default_value = 1.0
        link_sockets(tree, gin.outputs["Base Size"], xy.inputs[0])
        link_sockets(tree, shrink_pow.outputs[0], xy.inputs[1])
        size_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 620, by + 80 - i * 160))
        size_vec.inputs["X"].default_value = 4.0
        size_vec.inputs["Y"].default_value = 4.0
        size_vec.inputs["Z"].default_value = 0.4
        link_sockets(tree, xy.outputs[0], size_vec.inputs["X"])
        link_sockets(tree, xy.outputs[0], size_vec.inputs["Y"])
        link_sockets(tree, gin.outputs["Step Height"], size_vec.inputs["Z"])
        link_sockets(tree, size_vec.outputs["Vector"], cube.inputs["Size"])
        color_node(cube, "geometry")

        z_off = safe_node(tree, "ShaderNodeMath", (bx - 750, by + 40 - i * 160))
        z_off.operation = "MULTIPLY"
        z_off.inputs[1].default_value = i
        link_sockets(tree, gin.outputs["Step Height"], z_off.inputs[0])

        z_center = safe_node(tree, "ShaderNodeMath", (bx - 600, by + 40 - i * 160))
        z_center.operation = "MULTIPLY"
        z_center.inputs[0].default_value = 0.5
        link_sockets(tree, z_off.outputs[0], z_center.inputs[1])

        z_pos = safe_node(tree, "ShaderNodeMath", (bx - 450, by + 40 - i * 160))
        z_pos.operation = "ADD"
        link_sockets(tree, z_off.outputs[0], z_pos.inputs[0])
        link_sockets(tree, z_center.outputs[0], z_pos.inputs[1])

        combine = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 450, by + 90 - i * 160))
        combine.inputs["X"].default_value = 0.0
        combine.inputs["Y"].default_value = 0.0
        link_sockets(tree, z_pos.outputs[0], combine.inputs["Z"])

        set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 300, by + 120 - i * 160))
        link_sockets(tree, cube.outputs["Mesh"], set_pos.inputs["Geometry"])
        link_sockets(tree, combine.outputs["Vector"], set_pos.inputs["Offset"])

        gate = safe_node(tree, "FunctionNodeCompare", (bx - 450, by - 20 - i * 160))
        gate.data_type = "INT"
        gate.operation = "GREATER_THAN"
        link_sockets(tree, gin.outputs["Steps"], gate.inputs["A"])
        gate.inputs["B"].default_value = i

        sw = safe_node(tree, "GeometryNodeSwitch", (bx - 300, by - 20 - i * 160))
        sw.input_type = "GEOMETRY"
        link_sockets(tree, empty.outputs["Geometry"], sw.inputs["False"])
        link_sockets(tree, set_pos.outputs["Geometry"], sw.inputs["True"])
        link_sockets(tree, gate.outputs["Result"], sw.inputs["Switch"])
        parts.append(sw.outputs["Output"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 100, by))
    for part in parts:
        link_sockets(tree, part, join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 100, by))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(join, "geometry")
    color_node(shade, "geometry")

    return label_tree(tree, "MEL_stepped_pyramid", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Steps", "nodes": ("cube", "switch", "compare"), "role": "geometry"},
        {"title": "Join", "nodes": ("join",), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_torus_cross(group_name="MEL_torus_cross"):
    """Two-torus cross -- primary torus plus a rotated secondary ring.

    With Cross Rings enabled the second torus is rotated 90 degrees
    about X, producing a figure-8 / gyroscope silhouette.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Major Radius", 1.0, 0.1, 10.0)
    add_float_param(tree, "Minor Radius", 0.15, 0.01, 2.0)
    add_int_param(tree, "Major Segments", 48, 8, 128)
    add_int_param(tree, "Minor Segments", 12, 4, 32)
    add_bool_param(tree, "Cross Rings", True)

    t1 = add_mesh_torus_linked(tree, (bx - 300, by + 100),
                               gin.outputs["Major Radius"], gin.outputs["Minor Radius"],
                               gin.outputs["Major Segments"], gin.outputs["Minor Segments"])
    color_node(t1, "geometry")

    t2 = add_mesh_torus_linked(tree, (bx - 300, by - 100),
                               gin.outputs["Major Radius"], gin.outputs["Minor Radius"],
                               gin.outputs["Major Segments"], gin.outputs["Minor Segments"])
    color_node(t2, "geometry")

    rot = safe_node(tree, "GeometryNodeTransform", (bx - 100, by - 100))
    rot.inputs["Rotation"].default_value = (1.5708, 0.0, 0.0)
    link_sockets(tree, t2.outputs["Mesh"], rot.inputs["Geometry"])
    color_node(rot, "instance")

    empty = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 100, by - 200))
    color_node(empty, "geometry")

    sw = safe_node(tree, "GeometryNodeSwitch", (bx + 100, by - 100))
    sw.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Cross Rings"], sw.inputs["Switch"])
    link_sockets(tree, empty.outputs["Geometry"], sw.inputs["False"])
    link_sockets(tree, rot.outputs["Geometry"], sw.inputs["True"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 300, by + 100))
    link_sockets(tree, t1.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, sw.outputs["Output"], join.inputs["Geometry"])
    color_node(join, "geometry")

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 500, by + 100))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(shade, "geometry")

    return label_tree(tree, "MEL_torus_cross", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Primary Ring", "nodes": ("torus",), "role": "geometry"},
        {"title": "Cross Ring", "nodes": ("transform", "switch"), "role": "instance"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# ---------------------------------------------------------------- profiles


def build_egg_dart_rail(group_name="MEL_egg_dart_rail"):
    """Egg-and-dart rail -- ornamented sweep along a curve.

    A rectangle rail profile is swept along the input curve; egg (scaled
    UV sphere) and dart (cone) ornaments alternate by index parity along
    a resampled copy of the curve. The whole assembly is scaled by Scale.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Profile Width", 0.06, 0.01, 0.3)
    add_float_param(tree, "Profile Height", 0.04, 0.01, 0.2)
    add_int_param(tree, "Ornament Count", 12, 2, 64)
    add_float_param(tree, "Ornament Scale", 1.0, 0.1, 3.0)
    add_float_param(tree, "Scale", 1.0, 0.01, 10.0)

    rect = safe_node(tree, "GeometryNodeMeshGrid", (bx - 500, by + 300))
    link_sockets(tree, gin.outputs["Profile Width"], rect.inputs["Size X"])
    link_sockets(tree, gin.outputs["Profile Height"], rect.inputs["Size Y"])
    rect.inputs["Vertices X"].default_value = 2
    rect.inputs["Vertices Y"].default_value = 2
    color_node(rect, "geometry")

    sweep = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 300, by + 300))
    link_sockets(tree, gin.outputs["Geometry"], sweep.inputs["Curve"])
    cm_prof = sweep.inputs.get("Profile Curve") or sweep.inputs.get("Profile")
    link_sockets(tree, rect.outputs["Mesh"], cm_prof)
    color_node(sweep, "curve")

    resample = safe_node(tree, "GeometryNodeResampleCurve", (bx - 500, by + 100))
    link_sockets(tree, gin.outputs["Geometry"], resample.inputs["Curve"])
    link_sockets(tree, gin.outputs["Ornament Count"], resample.inputs["Count"])
    color_node(resample, "curve")

    egg = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 500, by - 100))
    egg.inputs["Radius"].default_value = 0.03
    egg.inputs["Segments"].default_value = 10
    egg.inputs["Rings"].default_value = 8
    egg_scale = safe_node(tree, "GeometryNodeTransform", (bx - 300, by - 100))
    egg_scale.inputs["Scale"].default_value = (1.0, 1.0, 1.4)
    link_sockets(tree, egg.outputs["Mesh"], egg_scale.inputs["Geometry"])
    color_node(egg, "geometry")

    dart = safe_node(tree, "GeometryNodeMeshCone", (bx - 500, by - 250))
    dart.inputs["Radius Bottom"].default_value = 0.035
    dart.inputs["Depth"].default_value = 0.07
    dart.inputs["Vertices"].default_value = 6
    color_node(dart, "geometry")

    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 500, by - 350))
    color_node(idx, "attribute")

    parity = safe_node(tree, "ShaderNodeMath", (bx - 350, by - 350))
    parity.operation = "MODULO"
    parity.inputs[1].default_value = 2.0
    link_sockets(tree, idx.outputs["Index"], parity.inputs[0])

    cmp = safe_node(tree, "FunctionNodeCompare", (bx - 200, by - 350))
    cmp.data_type = "FLOAT"
    cmp.operation = "GREATER_THAN"
    link_sockets(tree, parity.outputs[0], cmp.inputs["A"])
    cmp.inputs["B"].default_value = 0.5

    inv = safe_node(tree, "ShaderNodeMath", (bx - 200, by - 450))
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    link_sockets(tree, parity.outputs[0], inv.inputs[1])

    cmp_inv = safe_node(tree, "FunctionNodeCompare", (bx, by - 450))
    cmp_inv.data_type = "FLOAT"
    cmp_inv.operation = "GREATER_THAN"
    link_sockets(tree, inv.outputs[0], cmp_inv.inputs["A"])
    cmp_inv.inputs["B"].default_value = 0.5

    eggs_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 100, by + 100))
    link_sockets(tree, resample.outputs["Curve"], eggs_inst.inputs["Points"])
    link_sockets(tree, egg_scale.outputs["Geometry"], eggs_inst.inputs["Instance"])
    link_sockets(tree, cmp_inv.outputs["Result"], eggs_inst.inputs["Selection"])
    color_node(eggs_inst, "instance")

    darts_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 100, by + 100))
    link_sockets(tree, resample.outputs["Curve"], darts_inst.inputs["Points"])
    link_sockets(tree, dart.outputs["Mesh"], darts_inst.inputs["Instance"])
    link_sockets(tree, cmp.outputs["Result"], darts_inst.inputs["Selection"])
    color_node(darts_inst, "instance")

    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 300, by + 100))
    link_sockets(tree, eggs_inst.outputs["Instances"], realize.inputs["Geometry"])
    realize_2 = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 300, by))
    link_sockets(tree, darts_inst.outputs["Instances"], realize_2.inputs["Geometry"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 500, by + 150))
    link_sockets(tree, sweep.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, realize.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, realize_2.outputs["Geometry"], join.inputs["Geometry"])

    orn_scale = safe_node(tree, "ShaderNodeMath", (bx + 500, by - 100))
    orn_scale.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Ornament Scale"], orn_scale.inputs[0])
    orn_scale.inputs[1].default_value = 1.0

    transform = safe_node(tree, "GeometryNodeTransform", (bx + 700, by + 150))
    transform.inputs["Translation"].default_value = (0.0, 0.0, 0.0)
    link_sockets(tree, join.outputs["Geometry"], transform.inputs["Geometry"])
    link_float_to_vector(tree, gin.outputs["Scale"], transform, "Scale", component=0, defaults=(1.0, 1.0, 1.0))

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 900, by + 150))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, transform.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(shade, "geometry")

    return label_tree(tree, "MEL_egg_dart_rail", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Rail Sweep", "nodes": ("grid", "sweep"), "role": "curve"},
        {"title": "Ornaments", "nodes": ("sphere", "cone", "instance"), "role": "instance"},
        {"title": "Assembly", "nodes": ("join", "transform"), "role": "instance"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_baluster_collar(group_name="MEL_baluster_collar"):
    """Baluster with collar steps -- shaft plus stepped collar rings.

    A polygonal shaft with up to four collar rings unioned into it.
    Collars sit at 20/40/60/80 percent of the shaft height and are
    gated by Collar Count.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Height", 0.8, 0.1, 3.0)
    add_float_param(tree, "Radius", 0.05, 0.01, 0.5)
    add_int_param(tree, "Sides", 8, 4, 32)
    add_int_param(tree, "Collar Count", 3, 0, 4)
    add_float_param(tree, "Collar Scale", 1.5, 1.0, 3.0)

    shaft = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 500, by + 200))
    link_sockets(tree, gin.outputs["Radius"], shaft.inputs["Radius"])
    link_sockets(tree, gin.outputs["Height"], shaft.inputs["Depth"])
    link_sockets(tree, gin.outputs["Sides"], shaft.inputs["Vertices"])
    shaft.fill_type = "NGON"
    color_node(shaft, "geometry")

    empty = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 700, by))
    color_node(empty, "geometry")

    collar_geo = shaft.outputs["Mesh"]
    for i in range(4):
        frac = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 120 - i * 180))
        frac.operation = "MULTIPLY"
        frac.inputs[0].default_value = 0.2 * (i + 1)
        link_sockets(tree, gin.outputs["Height"], frac.inputs[1])

        z_center = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 60 - i * 180))
        z_center.operation = "SUBTRACT"
        link_sockets(tree, frac.outputs[0], z_center.inputs[0])
        half_h = safe_node(tree, "ShaderNodeMath", (bx - 800, by + 60 - i * 180))
        half_h.operation = "MULTIPLY"
        half_h.inputs[0].default_value = 0.5
        link_sockets(tree, gin.outputs["Height"], half_h.inputs[1])
        link_sockets(tree, half_h.outputs[0], z_center.inputs[1])

        collar = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 500, by + 120 - i * 180))
        collar.inputs["Depth"].default_value = 0.04
        link_sockets(tree, gin.outputs["Sides"], collar.inputs["Vertices"])
        collar_r = safe_node(tree, "ShaderNodeMath", (bx - 650, by + 120 - i * 180))
        collar_r.operation = "MULTIPLY"
        link_sockets(tree, gin.outputs["Radius"], collar_r.inputs[0])
        link_sockets(tree, gin.outputs["Collar Scale"], collar_r.inputs[1])
        link_sockets(tree, collar_r.outputs[0], collar.inputs["Radius"])
        collar.fill_type = "NGON"
        color_node(collar, "geometry")

        combine = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 650, by + 60 - i * 180))
        combine.inputs["X"].default_value = 0.0
        combine.inputs["Y"].default_value = 0.0
        link_sockets(tree, z_center.outputs[0], combine.inputs["Z"])

        set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 500, by + 60 - i * 180))
        link_sockets(tree, collar.outputs["Mesh"], set_pos.inputs["Geometry"])
        link_sockets(tree, combine.outputs["Vector"], set_pos.inputs["Position"])

        gate = safe_node(tree, "FunctionNodeCompare", (bx - 500, by - 40 - i * 180))
        gate.data_type = "INT"
        gate.operation = "GREATER_THAN"
        link_sockets(tree, gin.outputs["Collar Count"], gate.inputs["A"])
        gate.inputs["B"].default_value = i

        sw = safe_node(tree, "GeometryNodeSwitch", (bx - 350, by - 40 - i * 180))
        sw.input_type = "GEOMETRY"
        link_sockets(tree, empty.outputs["Geometry"], sw.inputs["False"])
        link_sockets(tree, set_pos.outputs["Geometry"], sw.inputs["True"])
        link_sockets(tree, gate.outputs["Result"], sw.inputs["Switch"])

        union = safe_node(tree, "GeometryNodeMeshBoolean", (bx - 150, by + 100 - i * 180))
        link_sockets(tree, collar_geo, union.inputs[0])
        link_sockets(tree, sw.outputs["Output"], union.inputs[1])
        union.operation = "UNION"
        collar_geo = union.outputs["Mesh"]
        color_node(union, "math")

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 50, by))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, collar_geo, shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(shade, "geometry")

    return label_tree(tree, "MEL_baluster_collar", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Shaft", "nodes": ("cylinder", "shaft"), "role": "geometry"},
        {"title": "Collars", "nodes": ("collar", "switch", "union"), "role": "geometry"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# ---------------------------------------------------------------- operations


def build_op_power_clamp(group_name="MEL_op_power_clamp"):
    """Clamped power scale -- instance falloff scale with hard min/max.

    Scale = clamp(Base * (idx+1) ^ -Power, Min, Max) applied uniformly
    to all instances. Unlike Power Scale, extremes are capped so arrays
    never collapse to zero or blow past Max.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Base Scale", 1.0, 0.01, 10.0)
    add_float_param(tree, "Power", 0.8, 0.01, 5.0)
    add_float_param(tree, "Min", 0.05, 0.001, 10.0)
    add_float_param(tree, "Max", 10.0, 0.01, 100.0)

    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 400, by + 100))
    color_node(idx, "attribute")

    idx_f = safe_node(tree, "ShaderNodeMath", (bx - 200, by + 150))
    idx_f.operation = "ADD"
    idx_f.inputs[0].default_value = 1.0
    link_sockets(tree, idx.outputs["Index"], idx_f.inputs[1])

    exp = safe_node(tree, "ShaderNodeMath", (bx, by + 150))
    exp.operation = "POWER"
    link_sockets(tree, idx_f.outputs[0], exp.inputs[0])
    link_sockets(tree, gin.outputs["Power"], exp.inputs[1])

    inv = safe_node(tree, "ShaderNodeMath", (bx + 150, by + 150))
    inv.operation = "DIVIDE"
    inv.inputs[0].default_value = 1.0
    link_sockets(tree, exp.outputs[0], inv.inputs[1])

    base = safe_node(tree, "ShaderNodeMath", (bx + 300, by + 150))
    base.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Base Scale"], base.inputs[0])
    link_sockets(tree, inv.outputs[0], base.inputs[1])

    clamp_low = safe_node(tree, "ShaderNodeMath", (bx + 450, by + 150))
    clamp_low.operation = "MAXIMUM"
    link_sockets(tree, base.outputs[0], clamp_low.inputs[0])
    link_sockets(tree, gin.outputs["Min"], clamp_low.inputs[1])

    clamp_high = safe_node(tree, "ShaderNodeMath", (bx + 600, by + 150))
    clamp_high.operation = "MINIMUM"
    link_sockets(tree, clamp_low.outputs[0], clamp_high.inputs[0])
    link_sockets(tree, gin.outputs["Max"], clamp_high.inputs[1])

    scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 600, by - 50))
    link_sockets(tree, gin.outputs["Geometry"], scale_inst.inputs["Instances"])
    combine = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 450, by - 100))
    link_sockets(tree, clamp_high.outputs[0], combine.inputs["X"])
    link_sockets(tree, clamp_high.outputs[0], combine.inputs["Y"])
    link_sockets(tree, clamp_high.outputs[0], combine.inputs["Z"])
    link_sockets(tree, combine.outputs["Vector"], scale_inst.inputs["Scale"])

    link_sockets(tree, scale_inst.outputs["Instances"], gout.inputs["Geometry"])

    color_node(exp, "math")
    color_node(clamp_low, "math")
    color_node(clamp_high, "math")
    color_node(scale_inst, "instance")

    return label_tree(tree, "MEL_op_power_clamp", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Power Math", "nodes": ("power", "multiply", "index"), "role": "math"},
        {"title": "Clamp", "nodes": ("minimum", "maximum"), "role": "math"},
        {"title": "Scale", "nodes": ("scale",), "role": "instance"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# -- Registry --
from .core import register_builder

register_builder("MEL_vortex_twist", build_vortex_twist, "Vortex Twist",
    "Twist displacement around the Z axis with stored per-vertex twist angle",
    "effects")
register_builder("MEL_radial_wave", build_radial_wave, "Radial Wave",
    "Concentric radial ripple displacement along face normals",
    "effects")
register_builder("MEL_shell_thicken", build_shell_thicken, "Shell Thicken",
    "Face-offset shell thicken with solid toggle",
    "mesh_tools")
register_builder("MEL_edge_ring_inset", build_edge_ring_inset, "Edge Ring Inset",
    "Extrude every edge to carve inset edge rings",
    "mesh_tools")
register_builder("MEL_symmetry_weld", build_symmetry_weld, "Symmetry Weld",
    "Mirror across an axis and weld the seam with Merge By Distance",
    "mesh_tools")
register_builder("MEL_vertex_relax", build_vertex_relax, "Vertex Cluster Relax",
    "Position blur with noise jitter for relaxing dense vertex clusters",
    "mesh_tools")
register_builder("MEL_attr_ramp_mix", build_attr_ramp_mix, "Attribute Ramp Mix",
    "Three-stop Start/Middle/End ramp blend read from and stored to named attributes",
    "math_attrs")
register_builder("MEL_attr_vector_rotate", build_attr_vector_rotate, "Attribute Vector Rotate",
    "Rotate a named vector attribute around Z and store the result",
    "math_attrs")
register_builder("MEL_edge_band_weight", build_edge_band_weight, "Edge Band Weight",
    "Per-edge banded falloff weight stored as 'edge_falloff' on the EDGE domain",
    "math_attrs")
register_builder("MEL_gear", build_gear, "Gear",
    "Star gear -- radial tooth blocks unioned into a disc",
    "primitives")
register_builder("MEL_stepped_pyramid", build_stepped_pyramid, "Stepped Pyramid",
    "Stacked shrinking cubes forming a stepped pyramid with step gating",
    "primitives")
register_builder("MEL_torus_cross", build_torus_cross, "Torus Cross",
    "Two-torus gyroscope cross with toggle for the rotated ring",
    "primitives")
register_builder("MEL_egg_dart_rail", build_egg_dart_rail, "Egg and Dart Rail",
    "Classical egg-and-dart ornament rail swept along a curve",
    "profiles")
register_builder("MEL_baluster_collar", build_baluster_collar, "Baluster with Collar",
    "Baluster shaft with stepped collar rings unioned in",
    "profiles")
register_builder("MEL_op_power_clamp", build_op_power_clamp, "Clamped Power Scale",
    "Instance power-falloff scale with hard min/max clamping",
    "operations")
