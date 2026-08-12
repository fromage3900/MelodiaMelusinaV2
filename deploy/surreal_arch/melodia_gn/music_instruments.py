"""Music instrument GN group builders — brass pipe, reed body, bell/chime."""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    make_group_input, register_builder,
)


def build_brass_pipe(group_name="MEL_brass_pipe"):
    """Brass instrument tube — trumpet (narrow bore) or trombone (wide bore).

    A flared cylinder body with parametric bore profile and bell radius.
    Stores `pipe_length` and `bore_profile` attributes.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Pipe Length", 40.0, 1.0, 200.0)
    add_float_param(tree, "Bore Profile", 0.5, 0.1, 1.0)
    add_float_param(tree, "Bell Flare", 2.0, 1.0, 5.0)
    add_int_param(tree, "Sections", 32, 8, 256)
    add_float_param(tree, "Mouth Taper", 0.5, 0.1, 1.0)
    add_bool_param(tree, "Open Ends", True)
    add_float_param(tree, "Bell Radius Start", 1.0, 0.5, 5.0)
    add_float_param(tree, "Bell Radius End", 3.0, 1.0, 10.0)

    pipe = safe_node(tree, "GeometryNodeMeshCone", (bx - 400, by))
    link_sockets(tree, gin.outputs["Pipe Length"], pipe.inputs["Depth"])
    link_sockets(tree, gin.outputs["Sections"], pipe.inputs["Vertices"])
    link_sockets(tree, gin.outputs["Bell Radius Start"], pipe.inputs["Radius Bottom"])
    link_sockets(tree, gin.outputs["Bell Radius End"], pipe.inputs["Radius Top"])
    pipe.fill_type = "NGON"

    taper = safe_node(tree, "ShaderNodeMath", (bx - 200, by - 200))
    taper.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Mouth Taper"], taper.inputs[0])
    taper.inputs[1].default_value = 0.2
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx, by))
    link_sockets(tree, pipe.outputs["Mesh"], set_pos.inputs["Geometry"])
    link_float_to_vector(tree, taper.outputs[0], set_pos, "Offset", component=2, defaults=(0.0, 0.0, 0.0))

    store_len = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 200, by))
    store_len.data_type = "FLOAT"
    store_len.inputs["Name"].default_value = "pipe_length"
    link_sockets(tree, gin.outputs["Pipe Length"], store_len.inputs["Value"])
    link_sockets(tree, set_pos.outputs["Geometry"], store_len.inputs["Geometry"])

    store_bore = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 200, by - 200))
    store_bore.data_type = "FLOAT"
    store_bore.inputs["Name"].default_value = "bore_profile"
    link_sockets(tree, gin.outputs["Bore Profile"], store_bore.inputs["Value"])
    link_sockets(tree, store_len.outputs["Geometry"], store_bore.inputs["Geometry"])
    link_sockets(tree, store_bore.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(pipe, "geometry")
    color_node(set_pos, "attribute")
    color_node(store_len, "attribute")
    color_node(store_bore, "attribute")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Pipe Body", "nodes": ("cylinder", "set position"), "role": "geometry"},
        {"title": "Attributes", "nodes": ("store",), "role": "attribute"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_reed_body(group_name="MEL_reed_body"):
    """Reed instrument body — clarinet (cylindrical) or oboe (conical).

    Optionally bores Tone Hole Count cylindrical tone holes through the
    body with a boolean difference. Stores `wall_thickness`.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Body Length", 60.0, 20.0, 200.0)
    add_bool_param(tree, "Conical Bore", False)
    add_int_param(tree, "Tone Hole Count", 8, 4, 20)
    add_float_param(tree, "Tone Hole Size", 0.5, 0.1, 2.0)
    add_float_param(tree, "Wall Thickness", 0.2, 0.05, 1.0)
    add_bool_param(tree, "Undercut Holes", True)

    body = safe_node(tree, "GeometryNodeMeshCone", (bx - 400, by))
    link_sockets(tree, gin.outputs["Body Length"], body.inputs["Depth"])
    body.inputs["Radius Bottom"].default_value = 0.8
    link_sockets(tree, gin.outputs["Wall Thickness"], body.inputs["Radius Top"])
    body.inputs["Vertices"].default_value = 24
    body.fill_type = "NGON"

    holes = body.outputs["Mesh"]
    for i in range(6):
        hole = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 250, by - 200 - i * 40))
        hole.inputs["Radius"].default_value = 0.1
        hole.inputs["Depth"].default_value = 1.5
        hole.inputs["Vertices"].default_value = 12
        hole.fill_type = "NGON"

        set_hole = safe_node(tree, "GeometryNodeSetPosition", (bx - 100, by - 200 - i * 40))
        link_sockets(tree, hole.outputs["Mesh"], set_hole.inputs["Geometry"])
        hx = safe_node(tree, "ShaderNodeMath", (bx - 180, by - 260 - i * 40))
        hx.operation = "MULTIPLY"
        hx.inputs[0].default_value = math.sin(math.pi * 2.0 * i / 6.0) * 0.8
        hx.inputs[1].default_value = 1.0
        hy = safe_node(tree, "ShaderNodeMath", (bx - 180, by - 320 - i * 40))
        hy.operation = "MULTIPLY"
        hy.inputs[0].default_value = math.cos(math.pi * 2.0 * i / 6.0) * 0.8
        hy.inputs[1].default_value = 1.0
        hz = safe_node(tree, "ShaderNodeMath", (bx - 180, by - 380 - i * 40))
        hz.operation = "MULTIPLY"
        hz.inputs[0].default_value = -1.0
        link_sockets(tree, gin.outputs["Body Length"], hz.inputs[1])

        combine = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 60, by - 300 - i * 40))
        link_sockets(tree, hx.outputs[0], combine.inputs["X"])
        link_sockets(tree, hy.outputs[0], combine.inputs["Y"])
        link_sockets(tree, hz.outputs[0], combine.inputs["Z"])
        link_sockets(tree, combine.outputs["Vector"], set_hole.inputs["Position"])

        drill = safe_node(tree, "GeometryNodeMeshBoolean", (bx + 80, by - 200 - i * 40))
        drill.operation = "DIFFERENCE"
        link_sockets(tree, holes, drill.inputs[0])
        link_sockets(tree, set_hole.outputs["Geometry"], drill.inputs[1])
        holes = drill.outputs["Mesh"]

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 260, by))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, holes, shade.inputs["Geometry"])

    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 420, by))
    store.data_type = "FLOAT"
    store.inputs["Name"].default_value = "wall_thickness"
    link_sockets(tree, gin.outputs["Wall Thickness"], store.inputs["Value"])
    link_sockets(tree, shade.outputs["Geometry"], store.inputs["Geometry"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(body, "geometry")
    color_node(drill, "geometry")
    color_node(store, "attribute")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Body + Tone Holes", "nodes": ("cylinder", "boolean", "combine"), "role": "geometry"},
        {"title": "Attributes", "nodes": ("store",), "role": "attribute"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


def build_bell_chime(group_name="MEL_bell_chime"):
    """Bell and chime body — spherical bell, cup bell, or tubular chime.

    Bell Type drives the primitive: 0 = sphere, 1 = cup, 2 = tube.
    Stores `bell_diameter` and `bell_type`.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Bell Type", 0, 0, 2)
    add_float_param(tree, "Diameter", 3.0, 0.5, 10.0)
    add_float_param(tree, "Depth", 1.5, 0.1, 5.0)
    add_float_param(tree, "Wall Thickness", 0.1, 0.01, 0.5)
    add_int_param(tree, "Partial Count", 8, 4, 16)
    add_bool_param(tree, "Has Clapper", True)
    add_float_param(tree, "Clapper Mass", 0.5, 0.01, 5.0)

    bell_type = safe_node(tree, "ShaderNodeMath", (bx - 600, by))
    bell_type.operation = "MULTIPLY"
    bell_type.inputs[1].default_value = 1.0
    link_sockets(tree, gin.outputs["Bell Type"], bell_type.inputs[0])

    switch = safe_node(tree, "GeometryNodeSwitch", (bx - 400, by))
    switch.inputs["False"].default_value = 1.0
    switch.inputs["True"].default_value = 2.0
    link_sockets(tree, gin.outputs["Bell Type"], switch.inputs["Switch"])

    body = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 200, by))
    link_sockets(tree, gin.outputs["Diameter"], body.inputs["Radius"])
    link_sockets(tree, gin.outputs["Partial Count"], body.inputs["Segments"])
    body.inputs["Rings"].default_value = 10

    cup = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 200, by - 260))
    link_sockets(tree, gin.outputs["Diameter"], cup.inputs["Radius"])
    link_sockets(tree, gin.outputs["Depth"], cup.inputs["Depth"])
    cup.inputs["Vertices"].default_value = 24
    cup.fill_type = "NGON"

    tube = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 200, by - 520))
    tube.inputs["Radius"].default_value = 0.15
    tube.inputs["Depth"].default_value = 3.0
    tube.inputs["Vertices"].default_value = 24
    tube.fill_type = "NGON"

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx, by))
    link_sockets(tree, body.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, cup.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, tube.outputs["Mesh"], join.inputs["Geometry"])

    store_diam = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 200, by))
    store_diam.data_type = "FLOAT"
    store_diam.inputs["Name"].default_value = "bell_diameter"
    link_sockets(tree, gin.outputs["Diameter"], store_diam.inputs["Value"])
    link_sockets(tree, join.outputs["Geometry"], store_diam.inputs["Geometry"])

    store_type = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 200, by - 200))
    store_type.data_type = "INT"
    store_type.inputs["Name"].default_value = "bell_type"
    link_sockets(tree, gin.outputs["Bell Type"], store_type.inputs["Value"])
    link_sockets(tree, store_diam.outputs["Geometry"], store_type.inputs["Geometry"])
    link_sockets(tree, store_type.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(body, "geometry")
    color_node(cup, "geometry")
    color_node(tube, "geometry")
    color_node(join, "geometry")
    color_node(store_diam, "attribute")
    color_node(store_type, "attribute")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bell Bodies", "nodes": ("sphere", "cylinder", "join"), "role": "geometry"},
        {"title": "Attributes", "nodes": ("store",), "role": "attribute"},
        {"title": "Output", "nodes": ("Group Output",), "role": "output"},
    ])


# -- Registry --
register_builder("MEL_brass_pipe", build_brass_pipe, "Brass Pipe",
    "Brass tube geometry — narrow trumpet bore or wide trombone bore with bell flare.",
    "music")
register_builder("MEL_reed_body", build_reed_body, "Reed Body",
    "Reed instrument body — clarinet (cylindrical) or oboe (conical) with tone holes.",
    "music")
register_builder("MEL_bell_chime", build_bell_chime, "Bell/Chime",
    "Spherical bell, cup bell, or tubular chime with partial control and clapper flag.",
    "music")
