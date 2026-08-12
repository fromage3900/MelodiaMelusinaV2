"""Water GN group builders — Gerstner waves, ripples, foam, current markers."""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    add_vector_param, make_group_input, register_builder, tree_input_names,
)


def build_water_gerstner(group_name="MEL_water_gerstner"):
    """Multi-layer Gerstner wave displacement for ocean surfaces.

    Sums four fixed wave trains (phase, frequency, direction) into a float
    `water_displacement` attribute on the input geometry. Animated adds scene
    time to the phase of every wave.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Wave Count", 5, 1, 12)
    add_float_param(tree, "Wind Direction X", 1.0, -1.0, 1.0)
    add_float_param(tree, "Wind Direction Z", 0.0, -1.0, 1.0)
    add_float_param(tree, "Scale", 1.0, 0.1, 10.0)
    add_float_param(tree, "Amplitude", 1.0, 0.1, 5.0)
    add_float_param(tree, "Base Frequency", 0.5, 0.01, 10.0)
    add_float_param(tree, "Speed", 1.0, 0.1, 10.0)
    add_bool_param(tree, "Animated", True)

    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 1200, by))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 1000, by))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    time_node = safe_node(tree, "ShaderNodeTime", (bx - 1000, by - 300))
    time_sec = safe_node(tree, "ShaderNodeMath", (bx - 900, by - 300))
    time_sec.operation = "MULTIPLY"
    time_sec.inputs[1].default_value = 1.0
    link_sockets(tree, time_node.outputs["Seconds"], time_sec.inputs[0])

    sum_node = None
    for i in range(4):
        # k dot p — wave number times position along the wind direction
        kx = safe_node(tree, "ShaderNodeMath", (bx - 800 + i * 320, by + i * 40))
        kx.operation = "MULTIPLY"
        kx.inputs[0].default_value = 1.0 / (2.0 + i * 1.5)
        link_sockets(tree, gin.outputs["Base Frequency"], kx.inputs[1])
        x_terms = safe_node(tree, "ShaderNodeMath", (bx - 600 + i * 320, by + i * 40))
        x_terms.operation = "MULTIPLY"
        link_sockets(tree, kx.outputs[0], x_terms.inputs[0])
        link_sockets(tree, sep.outputs["X"], x_terms.inputs[1])

        kz = safe_node(tree, "ShaderNodeMath", (bx - 800 + i * 320, by - 120 + i * 40))
        kz.operation = "MULTIPLY"
        kz.inputs[0].default_value = 1.0 / (3.0 + i * 1.5)
        link_sockets(tree, gin.outputs["Base Frequency"], kz.inputs[1])
        z_terms = safe_node(tree, "ShaderNodeMath", (bx - 600 + i * 320, by - 120 + i * 40))
        z_terms.operation = "MULTIPLY"
        link_sockets(tree, kz.outputs[0], z_terms.inputs[0])
        link_sockets(tree, sep.outputs["Z"], z_terms.inputs[1])

        dot = safe_node(tree, "ShaderNodeMath", (bx - 400 + i * 320, by + i * 40))
        dot.operation = "ADD"
        link_sockets(tree, x_terms.outputs[0], dot.inputs[0])
        link_sockets(tree, z_terms.outputs[0], dot.inputs[1])

        # phase = k dot p + wave offset + speed * time
        phase = safe_node(tree, "ShaderNodeMath", (bx - 200 + i * 320, by + i * 40))
        phase.operation = "ADD"
        phase.inputs[1].default_value = i * 2.1
        link_sockets(tree, dot.outputs[0], phase.inputs[0])

        drift = safe_node(tree, "ShaderNodeMath", (bx - 300 + i * 320, by - 240 + i * 40))
        drift.operation = "MULTIPLY"
        link_sockets(tree, gin.outputs["Speed"], drift.inputs[0])
        link_sockets(tree, time_sec.outputs[0], drift.inputs[1])

        wave = safe_node(tree, "ShaderNodeMath", (bx, by + i * 40))
        wave.operation = "ADD"
        link_sockets(tree, phase.outputs[0], wave.inputs[0])
        link_sockets(tree, drift.outputs[0], wave.inputs[1])

        sine = safe_node(tree, "ShaderNodeMath", (bx + 200, by + i * 40))
        sine.operation = "SINE"
        link_sockets(tree, wave.outputs[0], sine.inputs[0])

        amp = safe_node(tree, "ShaderNodeMath", (bx + 400, by + i * 40))
        amp.operation = "MULTIPLY"
        amp.inputs[0].default_value = 1.0 / (i + 1.0)
        link_sockets(tree, gin.outputs["Amplitude"], amp.inputs[0])
        scaled = safe_node(tree, "ShaderNodeMath", (bx + 600, by + i * 40))
        scaled.operation = "MULTIPLY"
        link_sockets(tree, sine.outputs[0], scaled.inputs[0])
        link_sockets(tree, amp.outputs[0], scaled.inputs[1])

        if sum_node is None:
            sum_node = scaled
        else:
            acc = safe_node(tree, "ShaderNodeMath", (bx + 600, by + i * 40 - 60))
            acc.operation = "ADD"
            link_sockets(tree, sum_node.outputs[0], acc.inputs[0])
            link_sockets(tree, scaled.outputs[0], acc.inputs[1])
            sum_node = acc

    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 900, by))
    store.data_type = "FLOAT"
    store.inputs["Name"].default_value = "water_displacement"
    link_sockets(tree, sum_node.outputs[0], store.inputs["Value"])
    link_sockets(tree, gin.outputs["Geometry"], store.inputs["Geometry"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(pos, "attribute")
    color_node(sep, "math")
    color_node(sine, "math")
    color_node(sum_node, "math")
    color_node(store, "attribute")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Wave Math", "nodes": ("position", "separate", "sine", "add", "multiply"), "role": "math"},
        {"title": "Output", "nodes": ("store", "Group Output"), "role": "output"},
    ])


def build_water_ripples(group_name="MEL_water_ripples"):
    """Expanding ripple rings around an impact point, with decay.

    Stores `ripple_height` on the input geometry. Radius grows with the
    Growth Speed; amplitude decays per ring with Decay Rate.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Ripple Count", 4, 1, 16)
    add_float_param(tree, "Initial Radius", 2.0, 0.1, 20.0)
    add_float_param(tree, "Decay Rate", 0.85, 0.01, 0.99)
    add_float_param(tree, "Growth Speed", 0.5, 0.01, 5.0)
    add_float_param(tree, "Height Amplitude", 0.1, 0.001, 1.0)
    add_int_param(tree, "Segments", 32, 6, 256)

    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 1000, by))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 800, by))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    dist_x = safe_node(tree, "ShaderNodeMath", (bx - 600, by))
    dist_x.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], dist_x.inputs[0])
    link_sockets(tree, sep.outputs["X"], dist_x.inputs[1])
    dist_z = safe_node(tree, "ShaderNodeMath", (bx - 600, by - 200))
    dist_z.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["Z"], dist_z.inputs[0])
    link_sockets(tree, sep.outputs["Z"], dist_z.inputs[1])
    dist = safe_node(tree, "ShaderNodeMath", (bx - 400, by - 100))
    dist.operation = "ADD"
    link_sockets(tree, dist_x.outputs[0], dist.inputs[0])
    link_sockets(tree, dist_z.outputs[0], dist.inputs[1])
    dist_root = safe_node(tree, "ShaderNodeMath", (bx - 200, by - 100))
    dist_root.operation = "SQRT"
    link_sockets(tree, dist.outputs[0], dist_root.inputs[0])

    time_node = safe_node(tree, "ShaderNodeTime", (bx - 1000, by - 400))
    time_sec = safe_node(tree, "ShaderNodeMath", (bx - 800, by - 400))
    time_sec.operation = "MULTIPLY"
    time_sec.inputs[1].default_value = 1.0
    link_sockets(tree, time_node.outputs["Seconds"], time_sec.inputs[0])

    sum_node = None
    for i in range(4):
        ring_r = safe_node(tree, "ShaderNodeMath", (bx - 200, by - 300 - i * 60))
        ring_r.operation = "MULTIPLY"
        ring_r.inputs[0].default_value = float(i)
        link_sockets(tree, gin.outputs["Growth Speed"], ring_r.inputs[0])
        ring_r2 = safe_node(tree, "ShaderNodeMath", (bx - 50, by - 300 - i * 60))
        ring_r2.operation = "MULTIPLY"
        ring_r2.inputs[1].default_value = 1.0
        link_sockets(tree, time_sec.outputs[0], ring_r2.inputs[1])
        ring_r3 = safe_node(tree, "ShaderNodeMath", (bx + 100, by - 300 - i * 60))
        ring_r3.operation = "ADD"
        link_sockets(tree, gin.outputs["Initial Radius"], ring_r3.inputs[0])
        link_sockets(tree, ring_r.outputs[0], ring_r3.inputs[1])

        offset = safe_node(tree, "ShaderNodeMath", (bx + 250, by - 200 - i * 60))
        offset.operation = "SUBTRACT"
        link_sockets(tree, dist_root.outputs[0], offset.inputs[0])
        link_sockets(tree, ring_r3.outputs[0], offset.inputs[1])
        offset_abs = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 200 - i * 60))
        offset_abs.operation = "ABS"
        link_sockets(tree, offset.outputs[0], offset_abs.inputs[0])

        width = safe_node(tree, "ShaderNodeMath", (bx + 550, by - 200 - i * 60))
        width.operation = "DIVIDE"
        width.inputs[0].default_value = 1.0
        width.inputs[1].default_value = 0.6
        pulse = safe_node(tree, "ShaderNodeMath", (bx + 700, by - 200 - i * 60))
        pulse.operation = "MULTIPLY"
        link_sockets(tree, offset_abs.outputs[0], pulse.inputs[0])
        link_sockets(tree, width.outputs[0], pulse.inputs[1])
        falloff = safe_node(tree, "ShaderNodeMath", (bx + 850, by - 200 - i * 60))
        falloff.operation = "SUBTRACT"
        falloff.inputs[0].default_value = 1.0
        link_sockets(tree, pulse.outputs[0], falloff.inputs[1])

        decay = safe_node(tree, "ShaderNodeMath", (bx + 1000, by - 200 - i * 60))
        decay.operation = "POWER"
        decay.inputs[1].default_value = float(i + 1)
        link_sockets(tree, gin.outputs["Decay Rate"], decay.inputs[0])

        hgt = safe_node(tree, "ShaderNodeMath", (bx + 1150, by - 200 - i * 60))
        hgt.operation = "MULTIPLY"
        link_sockets(tree, falloff.outputs[0], hgt.inputs[0])
        link_sockets(tree, decay.outputs[0], hgt.inputs[1])
        final = safe_node(tree, "ShaderNodeMath", (bx + 1300, by - 200 - i * 60))
        final.operation = "MULTIPLY"
        link_sockets(tree, hgt.outputs[0], final.inputs[0])
        link_sockets(tree, gin.outputs["Height Amplitude"], final.inputs[1])

        if sum_node is None:
            sum_node = final
        else:
            acc = safe_node(tree, "ShaderNodeMath", (bx + 1300, by - 260 - i * 60))
            acc.operation = "ADD"
            link_sockets(tree, sum_node.outputs[0], acc.inputs[0])
            link_sockets(tree, final.outputs[0], acc.inputs[1])
            sum_node = acc

    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 1600, by))
    store.data_type = "FLOAT"
    store.inputs["Name"].default_value = "ripple_height"
    link_sockets(tree, sum_node.outputs[0], store.inputs["Value"])
    link_sockets(tree, gin.outputs["Geometry"], store.inputs["Geometry"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(sep, "math")
    color_node(dist_root, "math")
    color_node(store, "attribute")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Ripple Math", "nodes": ("separate", "distance", "falloff", "decay"), "role": "math"},
        {"title": "Output", "nodes": ("store", "Group Output"), "role": "output"},
    ])


def build_water_foam(group_name="MEL_water_foam"):
    """Foam patch instances on a grid, tagged with lifetime.

    Instances small UV spheres over a MeshGrid; stores `foam_lifetime`
    (default Lifetime seconds) on the instanced geometry.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Foam Count", 100, 10, 1000)
    add_float_param(tree, "Velocity Threshold", 2.0, 0.1, 10.0)
    add_float_param(tree, "Foam Density", 0.3, 0.01, 1.0)
    add_float_param(tree, "Foam Size", 0.1, 0.001, 1.0)
    add_float_param(tree, "Lifetime", 10.0, 0.1, 60.0)
    add_bool_param(tree, "Animated Foam", True)

    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 800, by))
    grid_verts = safe_node(tree, "ShaderNodeMath", (bx - 1000, by))
    grid_verts.operation = "SQRT"
    link_sockets(tree, gin.outputs["Foam Count"], grid_verts.inputs[0])
    grid_verts_int = safe_node(tree, "ShaderNodeMath", (bx - 900, by))
    grid_verts_int.operation = "CEIL"
    link_sockets(tree, grid_verts.outputs[0], grid_verts_int.inputs[0])
    link_sockets(tree, grid_verts_int.outputs[0], grid.inputs["Vertices X"])
    link_sockets(tree, grid_verts_int.outputs[0], grid.inputs["Vertices Y"])
    grid.inputs["Size X"].default_value = 4.0
    grid.inputs["Size Y"].default_value = 4.0

    foam = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 600, by - 300))
    foam.inputs["Radius"].default_value = 0.05
    foam.inputs["Segments"].default_value = 8
    foam.inputs["Rings"].default_value = 6

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 400, by))
    link_sockets(tree, grid.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, foam.outputs["Mesh"], inst.inputs["Instance"])

    scale = safe_node(tree, "GeometryNodeScaleInstances", (bx - 200, by))
    link_sockets(tree, inst.outputs["Instances"], scale.inputs["Instances"])
    link_float_to_vector(tree, gin.outputs["Foam Size"], scale, "Scale", component=0, defaults=(1.0, 1.0, 1.0))
    link_float_to_vector(tree, gin.outputs["Foam Size"], scale, "Scale", component=1, defaults=(1.0, 1.0, 1.0))
    link_float_to_vector(tree, gin.outputs["Foam Size"], scale, "Scale", component=2, defaults=(1.0, 1.0, 1.0))

    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by))
    link_sockets(tree, scale.outputs["Instances"], realize.inputs["Geometry"])

    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 200, by))
    store.data_type = "FLOAT"
    store.inputs["Name"].default_value = "foam_lifetime"
    link_sockets(tree, gin.outputs["Lifetime"], store.inputs["Value"])
    link_sockets(tree, realize.outputs["Geometry"], store.inputs["Geometry"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(grid, "geometry")
    color_node(inst, "instance")
    color_node(realize, "geometry")
    color_node(store, "attribute")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Foam Instances", "nodes": ("grid", "uv sphere", "instance", "scale"), "role": "instance"},
        {"title": "Output", "nodes": ("store", "Group Output"), "role": "output"},
    ])


def build_water_current_markers(group_name="MEL_water_current_markers"):
    """Flow direction arrow instances along the current vector.

    Builds a MeshLine along Current Direction * Current Speed and instances
    small cones on it. Stores `current_dir` as a vector attribute.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Segment Count", 20, 5, 100)
    add_float_param(tree, "Segment Length", 1.0, 0.1, 10.0)
    add_float_param(tree, "Arrow Size", 0.2, 0.01, 1.0)
    add_vector_param(tree, "Current Direction", (1.0, 0.0, 0.0))
    add_float_param(tree, "Current Speed", 1.0, 0.01, 10.0)

    dir_norm = safe_node(tree, "ShaderNodeVectorMath", (bx - 800, by))
    dir_norm.operation = "NORMALIZE"
    link_sockets(tree, gin.outputs["Current Direction"], dir_norm.inputs[0])

    length = safe_node(tree, "ShaderNodeMath", (bx - 800, by - 200))
    length.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Segment Length"], length.inputs[0])
    link_sockets(tree, gin.outputs["Current Speed"], length.inputs[1])

    offset = safe_node(tree, "ShaderNodeVectorMath", (bx - 600, by))
    offset.operation = "SCALE"
    link_sockets(tree, dir_norm.outputs[0], offset.inputs[0])
    link_sockets(tree, length.outputs[0], offset.inputs["Scale"])

    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by))
    line.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Segment Count"], line.inputs["Count"])
    line.inputs["Start Location"].default_value = (-5.0, 0.0, 0.0)
    link_sockets(tree, offset.outputs[0], line.inputs["Offset"])

    arrow = safe_node(tree, "GeometryNodeMeshCone", (bx - 200, by - 300))
    arrow.inputs["Radius Bottom"].default_value = 0.05
    arrow.inputs["Depth"].default_value = 0.15
    arrow.inputs["Vertices"].default_value = 8

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx, by))
    link_sockets(tree, line.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, arrow.outputs["Mesh"], inst.inputs["Instance"])

    align = safe_node(tree, "FunctionNodeAlignEulerToVector", (bx, by - 100))
    align.inputs["Vector"].default_value = (1.0, 0.0, 0.0)
    link_sockets(tree, dir_norm.outputs[0], align.inputs["Vector"])
    link_sockets(tree, align.outputs["Rotation"], inst.inputs["Rotation"])

    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 200, by))
    link_sockets(tree, inst.outputs["Instances"], realize.inputs["Geometry"])

    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 400, by))
    store.data_type = "FLOAT_VECTOR"
    store.inputs["Name"].default_value = "current_dir"
    link_sockets(tree, dir_norm.outputs[0], store.inputs["Value"])
    link_sockets(tree, realize.outputs["Geometry"], store.inputs["Geometry"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(dir_norm, "math")
    color_node(line, "curve")
    color_node(inst, "instance")
    color_node(store, "attribute")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Current Math", "nodes": ("normalize", "scale", "mesh line"), "role": "curve"},
        {"title": "Arrow Instances", "nodes": ("cone", "instance", "align"), "role": "instance"},
        {"title": "Output", "nodes": ("store", "Group Output"), "role": "output"},
    ])


# -- Registry --
register_builder("MEL_water_gerstner", build_water_gerstner, "Gerstner Waves",
    "Multi-layer Gerstner wave displacement — wind direction, speed, amplitude, animated.",
    "effects")
register_builder("MEL_water_ripples", build_water_ripples, "Water Ripples",
    "Expanding ripple rings from an impact point with per-ring decay.",
    "effects")
register_builder("MEL_water_foam", build_water_foam, "Water Foam",
    "Foam patch instances with lifetime — velocity-threshold wake and impact foam.",
    "effects")
register_builder("MEL_water_current_markers", build_water_current_markers, "Current Markers",
    "Flow-direction arrow instances with current_dir attribute for navigation reads.",
    "effects")
