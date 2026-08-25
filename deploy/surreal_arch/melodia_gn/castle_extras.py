"""Castle kit & structure GN group builders - turrets, portcullis, slits, siege gear.

Seven new pieces for the CASTLE + STRUCTURES lane. Castle pieces follow the
castle.py convention: primitives + instance arrays + store_attribute for
downstream chaining. Each builder exposes only editable named inputs and
ends with Melodia label frames.
"""

from __future__ import annotations

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    register_builder,
)


def _math(tree, operation, loc, a=None, b=None):
    """Local shorthand for ShaderNodeMath (keeps graphs legible)."""
    n = safe_node(tree, "ShaderNodeMath", loc)
    try:
        n.operation = operation
    except Exception:
        pass
    if a is not None:
        if isinstance(a, (int, float)):
            n.inputs[0].default_value = a
        else:
            link_sockets(tree, a, n.inputs[0])
    if b is not None:
        if isinstance(b, (int, float)):
            n.inputs[1].default_value = b
        else:
            link_sockets(tree, b, n.inputs[1])
    return n


def _combine(tree, loc, x=None, y=None, z=None):
    """Local shorthand for CombineXYZ with socket-or-scalar components."""
    n = safe_node(tree, "ShaderNodeCombineXYZ", loc)
    for comp, val in (("X", x), ("Y", y), ("Z", z)):
        if val is None:
            continue
        if isinstance(val, (int, float)):
            try:
                n.inputs[comp].default_value = val
            except Exception:
                pass
        else:
            link_sockets(tree, val, n.inputs[comp])
    return n


def _place(tree, loc, geometry_sock, x=None, y=None, z=None):
    """Translate a piece to its final spot (primitives are origin-centered)."""
    t = safe_node(tree, "GeometryNodeTransform", loc)
    link_sockets(tree, geometry_sock, t.inputs["Geometry"])
    if x is not None or y is not None or z is not None:
        pos = _combine(tree, (loc[0] - 200, loc[1] - 140), x, y, z)
        link_sockets(tree, pos.outputs["Vector"], t.inputs["Translation"])
    return t.outputs["Geometry"]


def _instance(tree, loc, points_sock, instance_sock):
    """Instance `instance` on `points` and realize (keeps graphs compact)."""
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", loc)
    link_sockets(tree, points_sock, inst.inputs["Points"])
    link_sockets(tree, instance_sock, inst.inputs["Instance"])
    real = safe_node(tree, "GeometryNodeRealizeInstances", (loc[0] + 240, loc[1]))
    link_sockets(tree, inst.outputs["Instances"], real.inputs["Geometry"])
    return real.outputs["Geometry"]


def build_castle_corner_turret(group_name="MEL_castle_corner_turret"):
    """Corner turret - round body, conical roof, merlon ring.

    Stores turret_height (FLOAT) on the output for stack chaining.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Turret Radius", 0.8, 0.3, 3.0)
    add_float_param(tree, "Turret Height", 5.0, 1.0, 20.0)
    add_float_param(tree, "Roof Height", 1.2, 0.3, 4.0)
    add_int_param(tree, "Segments", 16, 6, 48)
    add_int_param(tree, "Merlon Count", 8, 3, 24)
    add_float_param(tree, "Merlon Width", 0.25, 0.1, 0.8)

    body = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 500, by + 400))
    link_sockets(tree, gin.outputs["Turret Radius"], body.inputs["Radius"])
    link_sockets(tree, gin.outputs["Turret Height"], body.inputs["Depth"])
    link_sockets(tree, gin.outputs["Segments"], body.inputs["Vertices"])
    body.fill_type = "NGON"

    roof = safe_node(tree, "GeometryNodeMeshCone", (bx - 500, by + 200))
    roof_r = _math(tree, "MULTIPLY", (bx - 700, by + 200), gin.outputs["Turret Radius"], 1.08)
    link_sockets(tree, roof_r.outputs[0], roof.inputs["Radius Bottom"])
    roof.inputs["Radius Top"].default_value = 0.05
    link_sockets(tree, gin.outputs["Roof Height"], roof.inputs["Depth"])
    link_sockets(tree, gin.outputs["Segments"], roof.inputs["Vertices"])
    roof_z = _math(tree, "ADD", (bx - 700, by + 140),
                   _math(tree, "MULTIPLY", (bx - 820, by + 140), gin.outputs["Turret Height"], 0.5).outputs[0],
                   _math(tree, "MULTIPLY", (bx - 820, by + 100), gin.outputs["Roof Height"], 0.5).outputs[0])
    roof_out = _place(tree, (bx - 300, by + 200), roof.outputs["Mesh"], z=roof_z.outputs[0])

    ring = safe_node(tree, "GeometryNodeMeshCircle", (bx - 500, by))
    ring_r = _math(tree, "MULTIPLY", (bx - 700, by), gin.outputs["Turret Radius"], 1.04)
    link_sockets(tree, ring_r.outputs[0], ring.inputs["Radius"])
    link_sockets(tree, gin.outputs["Merlon Count"], ring.inputs["Vertices"])
    ring.fill_type = "NONE"
    ring_z = _math(tree, "MULTIPLY", (bx - 700, by - 60), gin.outputs["Turret Height"], 1.0)
    ring_out = _place(tree, (bx - 300, by), ring.outputs["Mesh"], z=ring_z.outputs[0])

    merlon = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by - 200))
    merlon_s = _combine(tree, (bx - 700, by - 260), gin.outputs["Merlon Width"], gin.outputs["Merlon Width"],
                        _math(tree, "MULTIPLY", (bx - 820, by - 260), gin.outputs["Merlon Width"], 2.0).outputs[0])
    link_sockets(tree, merlon_s.outputs["Vector"], merlon.inputs["Size"])
    merlon_z = _math(tree, "MULTIPLY", (bx - 700, by - 320),
                     _math(tree, "MULTIPLY", (bx - 820, by - 320), gin.outputs["Merlon Width"], 2.0).outputs[0], 0.5)
    merlon_up = _place(tree, (bx - 300, by - 200), merlon.outputs["Mesh"], z=merlon_z.outputs[0])
    merlons = _instance(tree, (bx - 100, by), ring_out, merlon_up)

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 100, by + 300))
    link_sockets(tree, body.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, roof_out, join.inputs["Geometry"])
    link_sockets(tree, merlons, join.inputs["Geometry"])

    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 300, by + 300))
    store.data_type = "FLOAT"
    store.inputs["Name"].default_value = "turret_height"
    link_sockets(tree, gin.outputs["Turret Height"], store.inputs["Value"])
    link_sockets(tree, join.outputs["Geometry"], store.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 500, by + 300))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, store.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(body, "geometry")
    color_node(roof, "geometry")
    color_node(ring, "curve")
    color_node(merlon, "geometry")
    color_node(store, "attribute")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Turret Body", "nodes": ("turret", "cylinder", "roof"), "role": "geometry"},
        {"title": "Merlon Ring", "nodes": ("ring", "merlon", "circle", "instance"), "role": "instance"},
        {"title": "Output", "nodes": ("store", "shade", "join", "Group Output"), "role": "output"},
    ])


def build_castle_portcullis(group_name="MEL_castle_portcullis"):
    """Portcullis - vertical bar lattice, frame, head beam, optional cross braces.

    Stores portcullis_open (BOOLEAN) and bar_count (INT) on the output.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Width", 1.6, 0.6, 5.0)
    add_float_param(tree, "Height", 2.2, 0.8, 8.0)
    add_int_param(tree, "Bar Count", 7, 3, 20)
    add_float_param(tree, "Bar Thickness", 0.06, 0.02, 0.2)
    add_bool_param(tree, "Cross Bars", True)
    add_bool_param(tree, "Open", False)

    w_half = _math(tree, "MULTIPLY", (bx - 900, by + 300), gin.outputs["Width"], -0.5)
    gap = _math(tree, "MULTIPLY", (bx - 900, by + 240), gin.outputs["Bar Thickness"], 2.0)
    step = _math(tree, "DIVIDE", (bx - 900, by + 180), gin.outputs["Width"], gin.outputs["Bar Count"])

    bar_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 700, by + 400))
    bar_line.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Bar Count"], bar_line.inputs["Count"])
    link_sockets(tree, _combine(tree, (bx - 900, by + 520), w_half.outputs[0], 0.0, 0.0).outputs["Vector"], bar_line.inputs["Start Location"])
    link_sockets(tree, _combine(tree, (bx - 900, by + 440), step.outputs[0], 0.0, 0.0).outputs["Vector"], bar_line.inputs["Offset"])

    bar = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 700, by + 200))
    link_sockets(tree, gin.outputs["Bar Thickness"], bar.inputs["Radius"])
    link_sockets(tree, gin.outputs["Height"], bar.inputs["Depth"])
    bar.inputs["Vertices"].default_value = 8
    bar.fill_type = "NGON"
    bars = _instance(tree, (bx - 400, by + 400), bar_line.outputs["Mesh"], bar.outputs["Mesh"])

    frame_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 700, by + 100))
    frame_line.mode = "OFFSET"
    frame_line.inputs["Count"].default_value = 2
    link_sockets(tree, _combine(tree, (bx - 900, by + 160),
                                _math(tree, "SUBTRACT", (bx - 1000, by + 160), w_half.outputs[0], gap.outputs[0]).outputs[0],
                                0.0, 0.0).outputs["Vector"], frame_line.inputs["Start Location"])
    link_sockets(tree, _combine(tree, (bx - 900, by + 100),
                                _math(tree, "ADD", (bx - 1000, by + 100), gin.outputs["Width"],
                                      _math(tree, "MULTIPLY", (bx - 1100, by + 100), gap.outputs[0], 2.0).outputs[0]).outputs[0],
                                0.0, 0.0).outputs["Vector"], frame_line.inputs["Offset"])

    frame = safe_node(tree, "GeometryNodeMeshCube", (bx - 700, by - 100))
    link_sockets(tree, _combine(tree, (bx - 900, by - 160),
                                _math(tree, "MULTIPLY", (bx - 1000, by - 160), gin.outputs["Bar Thickness"], 2.5).outputs[0],
                                _math(tree, "MULTIPLY", (bx - 1000, by - 200), gin.outputs["Bar Thickness"], 2.5).outputs[0],
                                gin.outputs["Height"]).outputs["Vector"], frame.inputs["Size"])
    frame_up = _place(tree, (bx - 500, by - 100), frame.outputs["Mesh"], z=_math(tree, "MULTIPLY", (bx - 700, by - 160), gin.outputs["Height"], 0.5).outputs[0])
    frames = _instance(tree, (bx - 300, by + 100), frame_line.outputs["Mesh"], frame_up)

    beam = safe_node(tree, "GeometryNodeMeshCube", (bx - 700, by - 300))
    link_sockets(tree, _combine(tree, (bx - 900, by - 360),
                                _math(tree, "ADD", (bx - 1000, by - 360), gin.outputs["Width"],
                                      _math(tree, "MULTIPLY", (bx - 1100, by - 360), gin.outputs["Bar Thickness"], 6.0).outputs[0]).outputs[0],
                                _math(tree, "MULTIPLY", (bx - 1000, by - 400), gin.outputs["Bar Thickness"], 3.0).outputs[0],
                                _math(tree, "MULTIPLY", (bx - 1000, by - 440), gin.outputs["Bar Thickness"], 2.0).outputs[0]).outputs["Vector"], beam.inputs["Size"])
    beam_z = _math(tree, "ADD", (bx - 900, by - 480),
                   _math(tree, "MULTIPLY", (bx - 1000, by - 480), gin.outputs["Height"], 0.5).outputs[0],
                   _math(tree, "MULTIPLY", (bx - 1000, by - 520), gin.outputs["Bar Thickness"], 1.0).outputs[0])
    beam_out = _place(tree, (bx - 500, by - 300), beam.outputs["Mesh"], z=beam_z.outputs[0])

    cross_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 700, by - 500))
    cross_line.mode = "OFFSET"
    cross_line.inputs["Count"].default_value = 2
    h_third = _math(tree, "MULTIPLY", (bx - 900, by - 580), gin.outputs["Height"], 0.33)
    link_sockets(tree, _combine(tree, (bx - 900, by - 440), w_half.outputs[0], 0.0, h_third.outputs[0]).outputs["Vector"], cross_line.inputs["Start Location"])
    link_sockets(tree, _combine(tree, (bx - 900, by - 500), _math(tree, "MULTIPLY", (bx - 1000, by - 500), gin.outputs["Width"], 1.0).outputs[0],
                                0.0, h_third.outputs[0]).outputs["Vector"], cross_line.inputs["Offset"])

    cross = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by - 700))
    link_sockets(tree, _combine(tree, (bx - 700, by - 760), gin.outputs["Width"], gin.outputs["Bar Thickness"], gin.outputs["Bar Thickness"]).outputs["Vector"], cross.inputs["Size"])
    crosses = _instance(tree, (bx - 300, by - 500), cross_line.outputs["Mesh"], cross.outputs["Mesh"])

    switch = safe_node(tree, "GeometryNodeSwitch", (bx - 100, by - 500))
    switch.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Cross Bars"], switch.inputs["Switch"])
    link_sockets(tree, crosses, switch.inputs["True"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 100, by + 200))
    link_sockets(tree, bars, join.inputs["Geometry"])
    link_sockets(tree, frames, join.inputs["Geometry"])
    link_sockets(tree, beam_out, join.inputs["Geometry"])
    link_sockets(tree, switch.outputs["Output"], join.inputs["Geometry"])

    store_o = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 300, by + 300))
    store_o.data_type = "BOOLEAN"
    store_o.inputs["Name"].default_value = "portcullis_open"
    link_sockets(tree, gin.outputs["Open"], store_o.inputs["Value"])
    link_sockets(tree, join.outputs["Geometry"], store_o.inputs["Geometry"])

    store_b = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 500, by + 300))
    store_b.data_type = "INT"
    store_b.inputs["Name"].default_value = "bar_count"
    link_sockets(tree, gin.outputs["Bar Count"], store_b.inputs["Value"])
    link_sockets(tree, store_o.outputs["Geometry"], store_b.inputs["Geometry"])
    link_sockets(tree, store_b.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(bar_line, "curve")
    color_node(bar, "geometry")
    color_node(cross_line, "curve")
    color_node(switch, "instance")
    color_node(store_o, "attribute")
    color_node(store_b, "attribute")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bar Lattice", "nodes": ("bar", "line", "instance"), "role": "instance"},
        {"title": "Frame & Beam", "nodes": ("frame", "beam", "cube"), "role": "geometry"},
        {"title": "Cross Braces", "nodes": ("cross", "switch", "line"), "role": "instance"},
        {"title": "Portcullis Attributes", "nodes": ("store",), "role": "attribute"},
        {"title": "Output", "nodes": ("join", "Group Output"), "role": "output"},
    ])


def build_castle_arrow_slit(group_name="MEL_castle_arrow_slit"):
    """Arrow-slit wall - defensive wall patch with instanced slit openings.

    Stores slit_count (INT) on the output for PCG reads.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Wall Length", 4.0, 1.0, 12.0)
    add_float_param(tree, "Wall Height", 3.0, 1.0, 8.0)
    add_float_param(tree, "Wall Thickness", 0.5, 0.2, 1.5)
    add_float_param(tree, "Slit Height", 1.2, 0.4, 3.0)
    add_float_param(tree, "Slit Width", 0.14, 0.06, 0.6)
    add_int_param(tree, "Slit Count", 3, 1, 12)

    wall = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by + 400))
    wall_s = _combine(tree, (bx - 700, by + 340), gin.outputs["Wall Length"], gin.outputs["Wall Thickness"], gin.outputs["Wall Height"])
    link_sockets(tree, wall_s.outputs["Vector"], wall.inputs["Size"])
    wall_z = _math(tree, "MULTIPLY", (bx - 700, by + 280), gin.outputs["Wall Height"], 0.5)
    wall_out = _place(tree, (bx - 300, by + 400), wall.outputs["Mesh"], z=wall_z.outputs[0])

    frame = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by + 200))
    frame_s = _combine(tree, (bx - 700, by + 140),
                       _math(tree, "MULTIPLY", (bx - 820, by + 140), gin.outputs["Slit Width"], 3.0).outputs[0],
                       _math(tree, "MULTIPLY", (bx - 820, by + 100), gin.outputs["Wall Thickness"], 1.1).outputs[0],
                       _math(tree, "ADD", (bx - 820, by + 60), gin.outputs["Slit Height"], 0.6).outputs[0])
    link_sockets(tree, frame_s.outputs["Vector"], frame.inputs["Size"])

    slit = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by))
    slit_s = _combine(tree, (bx - 700, by - 60), gin.outputs["Slit Width"],
                      _math(tree, "MULTIPLY", (bx - 820, by - 60), gin.outputs["Wall Thickness"], 1.3).outputs[0],
                      gin.outputs["Slit Height"])
    link_sockets(tree, slit_s.outputs["Vector"], slit.inputs["Size"])

    notch = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by - 200))
    notch_s = _combine(tree, (bx - 700, by - 260),
                       _math(tree, "MULTIPLY", (bx - 820, by - 260), gin.outputs["Slit Width"], 0.6).outputs[0],
                       _math(tree, "MULTIPLY", (bx - 820, by - 300), gin.outputs["Wall Thickness"], 1.2).outputs[0], 0.1)
    link_sockets(tree, notch_s.outputs["Vector"], notch.inputs["Size"])

    slit_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 200, by))
    link_sockets(tree, frame.outputs["Mesh"], slit_join.inputs["Geometry"])
    link_sockets(tree, slit.outputs["Mesh"], slit_join.inputs["Geometry"])
    link_sockets(tree, notch.outputs["Mesh"], slit_join.inputs["Geometry"])

    slit_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 500, by - 400))
    slit_line.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Slit Count"], slit_line.inputs["Count"])
    slit_step = _math(tree, "DIVIDE", (bx - 700, by - 460),
                      _math(tree, "MULTIPLY", (bx - 820, by - 460), gin.outputs["Wall Length"], 0.8).outputs[0],
                      gin.outputs["Slit Count"])
    slit_start = _combine(tree, (bx - 700, by - 340),
                          _math(tree, "MULTIPLY", (bx - 820, by - 340), gin.outputs["Wall Length"], -0.4).outputs[0],
                          0.0, _math(tree, "MULTIPLY", (bx - 820, by - 380), gin.outputs["Wall Height"], 0.55).outputs[0])
    link_sockets(tree, slit_start.outputs["Vector"], slit_line.inputs["Start Location"])
    slit_off = _combine(tree, (bx - 700, by - 400), slit_step.outputs[0], 0.0, 0.0)
    link_sockets(tree, slit_off.outputs["Vector"], slit_line.inputs["Offset"])
    slits = _instance(tree, (bx - 200, by - 400), slit_line.outputs["Mesh"], slit_join.outputs["Geometry"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx, by + 200))
    link_sockets(tree, wall_out, join.inputs["Geometry"])
    link_sockets(tree, slits, join.inputs["Geometry"])

    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 200, by + 300))
    store.data_type = "INT"
    store.inputs["Name"].default_value = "slit_count"
    link_sockets(tree, gin.outputs["Slit Count"], store.inputs["Value"])
    link_sockets(tree, join.outputs["Geometry"], store.inputs["Geometry"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(wall, "geometry")
    color_node(frame, "geometry")
    color_node(slit, "geometry")
    color_node(slit_line, "curve")
    color_node(store, "attribute")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Wall Patch", "nodes": ("wall", "cube"), "role": "geometry"},
        {"title": "Slit Openings", "nodes": ("slit", "frame", "notch", "join"), "role": "geometry"},
        {"title": "Slit Instances", "nodes": ("slit", "line", "instance"), "role": "instance"},
        {"title": "Output", "nodes": ("store", "join", "Group Output"), "role": "output"},
    ])


def build_castle_hoarding(group_name="MEL_castle_hoarding"):
    """Hoarding - projecting wooden gallery: floor, posts, wall plate, canopy.

    Stores gallery_level (INT) and has_canopy (BOOLEAN) on the output.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Length", 3.0, 1.0, 10.0)
    add_float_param(tree, "Width", 1.2, 0.5, 3.0)
    add_float_param(tree, "Wall Height", 4.0, 1.0, 10.0)
    add_float_param(tree, "Floor Thickness", 0.12, 0.05, 0.3)
    add_int_param(tree, "Post Count", 4, 2, 8)
    add_int_param(tree, "Gallery Level", 2, 1, 5)
    add_bool_param(tree, "Has Canopy", True)

    floor = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by + 400))
    link_sockets(tree, _combine(tree, (bx - 700, by + 340), gin.outputs["Length"], gin.outputs["Width"], gin.outputs["Floor Thickness"]).outputs["Vector"], floor.inputs["Size"])
    floor_z = _math(tree, "ADD", (bx - 700, by + 280),
                    _math(tree, "MULTIPLY", (bx - 820, by + 280), gin.outputs["Wall Height"], 0.75).outputs[0],
                    _math(tree, "MULTIPLY", (bx - 820, by + 240), gin.outputs["Floor Thickness"], 0.5).outputs[0])
    floor_out = _place(tree, (bx - 300, by + 400), floor.outputs["Mesh"], z=floor_z.outputs[0])

    post_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 500, by + 200))
    post_line.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Post Count"], post_line.inputs["Count"])
    post_step = _math(tree, "DIVIDE", (bx - 700, by + 140), gin.outputs["Length"], gin.outputs["Post Count"])
    link_sockets(tree, _combine(tree, (bx - 700, by + 260),
                                _math(tree, "MULTIPLY", (bx - 820, by + 260), gin.outputs["Length"], -0.5).outputs[0],
                                _math(tree, "MULTIPLY", (bx - 820, by + 220), gin.outputs["Width"], 0.3).outputs[0],
                                _math(tree, "MULTIPLY", (bx - 820, by + 180), gin.outputs["Wall Height"], 0.72).outputs[0]).outputs["Vector"],
                post_line.inputs["Start Location"])
    link_sockets(tree, _combine(tree, (bx - 700, by + 200), post_step.outputs[0], 0.0, 0.0).outputs["Vector"], post_line.inputs["Offset"])

    post = safe_node(tree, "GeometryNodeMeshCube", (bx - 300, by))
    link_sockets(tree, _combine(tree, (bx - 500, by - 60), 0.1, 0.1,
                                _math(tree, "MULTIPLY", (bx - 620, by - 60), gin.outputs["Wall Height"], 0.28).outputs[0]).outputs["Vector"], post.inputs["Size"])
    post_up = _place(tree, (bx - 100, by), post.outputs["Mesh"], z=_math(tree, "MULTIPLY", (bx - 500, by - 100), gin.outputs["Wall Height"], 0.86).outputs[0])
    posts = _instance(tree, (bx + 100, by + 200), post_line.outputs["Mesh"], post_up)

    plate = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by - 200))
    link_sockets(tree, _combine(tree, (bx - 700, by - 260), gin.outputs["Length"], 0.18, gin.outputs["Wall Height"]).outputs["Vector"], plate.inputs["Size"])
    plate_y = _math(tree, "MULTIPLY", (bx - 700, by - 300),
                    _math(tree, "ADD", (bx - 820, by - 300), gin.outputs["Width"], 0.18).outputs[0], -0.5)
    plate_out = _place(tree, (bx - 300, by - 200), plate.outputs["Mesh"], y=plate_y.outputs[0],
                       z=_math(tree, "MULTIPLY", (bx - 700, by - 340), gin.outputs["Wall Height"], 0.5).outputs[0])

    canopy = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by - 400))
    link_sockets(tree, _combine(tree, (bx - 700, by - 460),
                                _math(tree, "MULTIPLY", (bx - 820, by - 460), gin.outputs["Length"], 1.1).outputs[0],
                                _math(tree, "MULTIPLY", (bx - 820, by - 500), gin.outputs["Width"], 1.15).outputs[0], 0.16).outputs["Vector"], canopy.inputs["Size"])
    canopy_z = _math(tree, "ADD", (bx - 700, by - 540),
                     _math(tree, "MULTIPLY", (bx - 820, by - 540), gin.outputs["Wall Height"], 0.98).outputs[0], 0.08)
    canopy_out = _place(tree, (bx - 300, by - 400), canopy.outputs["Mesh"], z=canopy_z.outputs[0])

    switch = safe_node(tree, "GeometryNodeSwitch", (bx - 100, by - 400))
    switch.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Has Canopy"], switch.inputs["Switch"])
    link_sockets(tree, canopy_out, switch.inputs["True"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 100, by + 300))
    link_sockets(tree, floor_out, join.inputs["Geometry"])
    link_sockets(tree, posts, join.inputs["Geometry"])
    link_sockets(tree, plate_out, join.inputs["Geometry"])
    link_sockets(tree, switch.outputs["Output"], join.inputs["Geometry"])

    store_l = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 300, by + 400))
    store_l.data_type = "INT"
    store_l.inputs["Name"].default_value = "gallery_level"
    link_sockets(tree, gin.outputs["Gallery Level"], store_l.inputs["Value"])
    link_sockets(tree, join.outputs["Geometry"], store_l.inputs["Geometry"])

    store_c = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 500, by + 400))
    store_c.data_type = "BOOLEAN"
    store_c.inputs["Name"].default_value = "has_canopy"
    link_sockets(tree, gin.outputs["Has Canopy"], store_c.inputs["Value"])
    link_sockets(tree, store_l.outputs["Geometry"], store_c.inputs["Geometry"])
    link_sockets(tree, store_c.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(floor, "geometry")
    color_node(post_line, "curve")
    color_node(post, "geometry")
    color_node(plate, "geometry")
    color_node(switch, "instance")
    color_node(store_l, "attribute")
    color_node(store_c, "attribute")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Gallery Floor", "nodes": ("floor", "plate", "cube"), "role": "geometry"},
        {"title": "Gallery Posts", "nodes": ("post", "line", "instance"), "role": "instance"},
        {"title": "Canopy", "nodes": ("canopy", "switch"), "role": "geometry"},
        {"title": "Hoarding Attributes", "nodes": ("store",), "role": "attribute"},
        {"title": "Output", "nodes": ("join", "Group Output"), "role": "output"},
    ])


def build_castle_siege_tower(group_name="MEL_castle_siege_tower"):
    """Siege tower - four corner posts, stacked decks, optional roof cap.

    Stores tower_levels (INT) on the output for PCG reads.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Width", 3.0, 1.5, 6.0)
    add_float_param(tree, "Height", 8.0, 3.0, 20.0)
    add_float_param(tree, "Deck Thickness", 0.15, 0.06, 0.4)
    add_int_param(tree, "Deck Count", 3, 1, 6)
    add_float_param(tree, "Post Thickness", 0.18, 0.08, 0.5)
    add_float_param(tree, "Roof Height", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Has Roof", True)

    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 600, by + 400))
    grid.inputs["Vertices X"].default_value = 2
    grid.inputs["Vertices Y"].default_value = 2
    link_sockets(tree, gin.outputs["Width"], grid.inputs["Size X"])
    link_sockets(tree, gin.outputs["Width"], grid.inputs["Size Y"])

    post = safe_node(tree, "GeometryNodeMeshCube", (bx - 600, by + 200))
    post_s = _combine(tree, (bx - 800, by + 140), gin.outputs["Post Thickness"], gin.outputs["Post Thickness"], gin.outputs["Height"])
    link_sockets(tree, post_s.outputs["Vector"], post.inputs["Size"])
    post_z = _math(tree, "MULTIPLY", (bx - 800, by + 80), gin.outputs["Height"], 0.5)
    post_up = _place(tree, (bx - 400, by + 200), post.outputs["Mesh"], z=post_z.outputs[0])
    posts = _instance(tree, (bx - 200, by + 400), grid.outputs["Mesh"], post_up)

    decks = []
    deck_i = safe_node(tree, "ShaderNodeMath", (bx - 900, by - 100))
    deck_i.operation = "DIVIDE"
    deck_i.inputs[0].default_value = 1.0
    link_sockets(tree, gin.outputs["Deck Count"], deck_i.inputs[1])
    for i in range(6):
        deck = safe_node(tree, "GeometryNodeMeshCube", (bx - 800 + i * 60, by - 100))
        deck_s = _combine(tree, (bx - 1000 + i * 60, by - 160),
                          _math(tree, "MULTIPLY", (bx - 1100 + i * 60, by - 160), gin.outputs["Width"], 0.9).outputs[0],
                          _math(tree, "MULTIPLY", (bx - 1100 + i * 60, by - 200), gin.outputs["Width"], 0.9).outputs[0],
                          gin.outputs["Deck Thickness"])
        link_sockets(tree, deck_s.outputs["Vector"], deck.inputs["Size"])
        level = _math(tree, "MULTIPLY", (bx - 900 + i * 60, by - 240),
                      _math(tree, "MULTIPLY", (bx - 1020 + i * 60, by - 240),
                            _math(tree, "ADD", (bx - 1140 + i * 60, by - 240), float(i + 1), 0.0).outputs[0],
                            deck_i.outputs[0]).outputs[0],
                      gin.outputs["Height"])
        deck_z = _math(tree, "ADD", (bx - 900 + i * 60, by - 280), level.outputs[0],
                       _math(tree, "MULTIPLY", (bx - 1020 + i * 60, by - 280), gin.outputs["Deck Thickness"], 0.5).outputs[0])
        deck_out = _place(tree, (bx - 600 + i * 60, by - 100), deck.outputs["Mesh"], z=deck_z.outputs[0])
        decks.append(deck_out)

    roof = safe_node(tree, "GeometryNodeMeshCone", (bx - 600, by - 400))
    roof_r = _math(tree, "MULTIPLY", (bx - 800, by - 400), gin.outputs["Width"], 0.75)
    link_sockets(tree, roof_r.outputs[0], roof.inputs["Radius Bottom"])
    roof.inputs["Radius Top"].default_value = 0.0
    link_sockets(tree, gin.outputs["Roof Height"], roof.inputs["Depth"])
    roof.inputs["Vertices"].default_value = 8
    roof_z = _math(tree, "ADD", (bx - 800, by - 460),
                   _math(tree, "MULTIPLY", (bx - 920, by - 460), gin.outputs["Height"], 0.5).outputs[0],
                   _math(tree, "MULTIPLY", (bx - 920, by - 500), gin.outputs["Roof Height"], 0.5).outputs[0])
    roof_out = _place(tree, (bx - 400, by - 400), roof.outputs["Mesh"], z=roof_z.outputs[0])

    switch_roof = safe_node(tree, "GeometryNodeSwitch", (bx - 100, by - 400))
    switch_roof.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Has Roof"], switch_roof.inputs["Switch"])
    link_sockets(tree, roof_out, switch_roof.inputs["True"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 100, by + 200))
    link_sockets(tree, posts, join.inputs["Geometry"])
    for deck in decks:
        link_sockets(tree, deck, join.inputs["Geometry"])
    link_sockets(tree, switch_roof.outputs["Output"], join.inputs["Geometry"])

    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 300, by + 300))
    store.data_type = "INT"
    store.inputs["Name"].default_value = "tower_levels"
    link_sockets(tree, gin.outputs["Deck Count"], store.inputs["Value"])
    link_sockets(tree, join.outputs["Geometry"], store.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 500, by + 300))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, store.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(grid, "curve")
    color_node(post, "geometry")
    color_node(deck, "geometry")
    color_node(roof, "geometry")
    color_node(store, "attribute")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Corner Posts", "nodes": ("grid", "post", "instance"), "role": "instance"},
        {"title": "Decks", "nodes": ("deck", "cube", "divide"), "role": "geometry"},
        {"title": "Roof Cap", "nodes": ("roof", "cone", "switch"), "role": "geometry"},
        {"title": "Output", "nodes": ("store", "shade", "join", "Group Output"), "role": "output"},
    ])


def build_castle_barbican(group_name="MEL_castle_barbican"):
    """Barbican gate - flanking pillars, lintel, turrets, portcullis slot.

    Stores gate_mode (INT) on the output for PCG gate-state reads.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Passage Width", 1.8, 0.8, 4.0)
    add_float_param(tree, "Passage Height", 2.6, 1.2, 5.0)
    add_float_param(tree, "Wall Depth", 1.2, 0.5, 3.0)
    add_float_param(tree, "Turret Radius", 0.7, 0.3, 2.0)
    add_float_param(tree, "Turret Height", 4.0, 1.0, 10.0)
    add_int_param(tree, "Gate Mode", 0, 0, 2)

    half_w = _math(tree, "MULTIPLY", (bx - 900, by + 400), gin.outputs["Passage Width"], 0.5)
    pillar_off = _math(tree, "ADD", (bx - 900, by + 340), half_w.outputs[0], 0.3)
    turret_off = _math(tree, "ADD", (bx - 900, by + 280),
                       _math(tree, "ADD", (bx - 1000, by + 280), pillar_off.outputs[0], gin.outputs["Turret Radius"]).outputs[0], 0.3)

    pillar_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 700, by + 400))
    pillar_line.mode = "OFFSET"
    pillar_line.inputs["Count"].default_value = 2
    link_sockets(tree, _combine(tree, (bx - 900, by + 520),
                                _math(tree, "MULTIPLY", (bx - 1000, by + 520), pillar_off.outputs[0], -1.0).outputs[0], 0.0,
                                _math(tree, "MULTIPLY", (bx - 1000, by + 480), gin.outputs["Passage Height"], 0.5).outputs[0]).outputs["Vector"],
                pillar_line.inputs["Start Location"])
    link_sockets(tree, _combine(tree, (bx - 900, by + 440), _math(tree, "MULTIPLY", (bx - 1000, by + 440), pillar_off.outputs[0], 2.0).outputs[0], 0.0, 0.0).outputs["Vector"],
                pillar_line.inputs["Offset"])

    pillar = safe_node(tree, "GeometryNodeMeshCube", (bx - 700, by + 200))
    link_sockets(tree, _combine(tree, (bx - 900, by + 140), gin.outputs["Wall Depth"], 0.6, gin.outputs["Passage Height"]).outputs["Vector"], pillar.inputs["Size"])
    pillars = _instance(tree, (bx - 400, by + 400), pillar_line.outputs["Mesh"], pillar.outputs["Mesh"])

    lintel = safe_node(tree, "GeometryNodeMeshCube", (bx - 700, by))
    link_sockets(tree, _combine(tree, (bx - 900, by - 60),
                                _math(tree, "ADD", (bx - 1000, by - 60), gin.outputs["Passage Width"], 1.2).outputs[0],
                                gin.outputs["Wall Depth"], 0.6).outputs["Vector"], lintel.inputs["Size"])
    lintel_out = _place(tree, (bx - 500, by), lintel.outputs["Mesh"], z=_math(tree, "ADD", (bx - 900, by - 120), gin.outputs["Passage Height"], 0.3).outputs[0])

    slot = safe_node(tree, "GeometryNodeMeshCube", (bx - 700, by - 200))
    link_sockets(tree, _combine(tree, (bx - 900, by - 260),
                                _math(tree, "MULTIPLY", (bx - 1000, by - 260), gin.outputs["Passage Width"], 0.75).outputs[0],
                                _math(tree, "MULTIPLY", (bx - 1000, by - 300), gin.outputs["Wall Depth"], 1.05).outputs[0], 0.2).outputs["Vector"], slot.inputs["Size"])
    slot_out = _place(tree, (bx - 500, by - 200), slot.outputs["Mesh"], z=_math(tree, "SUBTRACT", (bx - 900, by - 340), gin.outputs["Passage Height"], 0.3).outputs[0])

    turret_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 700, by - 400))
    turret_line.mode = "OFFSET"
    turret_line.inputs["Count"].default_value = 2
    link_sockets(tree, _combine(tree, (bx - 900, by - 280),
                                _math(tree, "MULTIPLY", (bx - 1000, by - 280), turret_off.outputs[0], -1.0).outputs[0], 0.0,
                                _math(tree, "MULTIPLY", (bx - 1000, by - 320), gin.outputs["Turret Height"], 0.5).outputs[0]).outputs["Vector"],
                turret_line.inputs["Start Location"])
    link_sockets(tree, _combine(tree, (bx - 900, by - 400), _math(tree, "MULTIPLY", (bx - 1000, by - 400), turret_off.outputs[0], 2.0).outputs[0], 0.0, 0.0).outputs["Vector"],
                turret_line.inputs["Offset"])

    turret = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 700, by - 600))
    link_sockets(tree, gin.outputs["Turret Radius"], turret.inputs["Radius"])
    link_sockets(tree, gin.outputs["Turret Height"], turret.inputs["Depth"])
    turret.inputs["Vertices"].default_value = 16
    turret.fill_type = "NGON"
    turrets = _instance(tree, (bx - 400, by - 400), turret_line.outputs["Mesh"], turret.outputs["Mesh"])

    cap = safe_node(tree, "GeometryNodeMeshCone", (bx - 700, by - 800))
    link_sockets(tree, _math(tree, "MULTIPLY", (bx - 900, by - 800), gin.outputs["Turret Radius"], 1.1).outputs[0], cap.inputs["Radius Bottom"])
    cap.inputs["Radius Top"].default_value = 0.03
    cap_d = _math(tree, "MULTIPLY", (bx - 900, by - 860), gin.outputs["Turret Radius"], 1.3)
    link_sockets(tree, cap_d.outputs[0], cap.inputs["Depth"])
    cap.inputs["Vertices"].default_value = 16
    cap_z = _math(tree, "ADD", (bx - 900, by - 920),
                  _math(tree, "MULTIPLY", (bx - 1000, by - 920), gin.outputs["Turret Height"], 0.5).outputs[0],
                  _math(tree, "MULTIPLY", (bx - 1000, by - 960), cap_d.outputs[0], 0.5).outputs[0])
    cap_up = _place(tree, (bx - 400, by - 800), cap.outputs["Mesh"], z=cap_z.outputs[0])
    caps = _instance(tree, (bx - 200, by - 400), turret_line.outputs["Mesh"], cap_up)

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 100, by))
    link_sockets(tree, pillars, join.inputs["Geometry"])
    link_sockets(tree, lintel_out, join.inputs["Geometry"])
    link_sockets(tree, slot_out, join.inputs["Geometry"])
    link_sockets(tree, turrets, join.inputs["Geometry"])
    link_sockets(tree, caps, join.inputs["Geometry"])

    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 300, by + 100))
    store.data_type = "INT"
    store.inputs["Name"].default_value = "gate_mode"
    link_sockets(tree, gin.outputs["Gate Mode"], store.inputs["Value"])
    link_sockets(tree, join.outputs["Geometry"], store.inputs["Geometry"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(pillar_line, "curve")
    color_node(pillar, "geometry")
    color_node(turret_line, "curve")
    color_node(turret, "geometry")
    color_node(cap, "geometry")
    color_node(store, "attribute")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Gate Pillars", "nodes": ("pillar", "line", "instance"), "role": "instance"},
        {"title": "Lintel & Slot", "nodes": ("lintel", "slot", "cube"), "role": "geometry"},
        {"title": "Flanking Turrets", "nodes": ("turret", "cap", "line", "instance"), "role": "instance"},
        {"title": "Output", "nodes": ("store", "join", "Group Output"), "role": "output"},
    ])


def build_pergola_walkway(group_name="MEL_pergola_walkway"):
    """Pergola walkway - twin post lines, top beams, cross rafters.

    Stores post_count (INT) on the output for PCG reads.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Length", 6.0, 2.0, 30.0)
    add_float_param(tree, "Width", 2.4, 1.0, 6.0)
    add_float_param(tree, "Post Height", 2.4, 1.0, 4.5)
    add_int_param(tree, "Post Count", 5, 2, 20)
    add_float_param(tree, "Beam Thickness", 0.12, 0.05, 0.3)

    start_x = _math(tree, "MULTIPLY", (bx - 900, by + 400), gin.outputs["Length"], -0.5)
    step_x = _math(tree, "DIVIDE", (bx - 900, by + 320), gin.outputs["Length"], gin.outputs["Post Count"])
    w_half = _math(tree, "MULTIPLY", (bx - 900, by + 240), gin.outputs["Width"], 0.5)
    w_neg = _math(tree, "MULTIPLY", (bx - 900, by + 160), gin.outputs["Width"], -0.5)

    line_a = safe_node(tree, "GeometryNodeMeshLine", (bx - 700, by + 400))
    line_a.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Post Count"], line_a.inputs["Count"])
    link_sockets(tree, _combine(tree, (bx - 900, by + 520), start_x.outputs[0], w_half.outputs[0], 0.0).outputs["Vector"], line_a.inputs["Start Location"])
    link_sockets(tree, _combine(tree, (bx - 900, by + 440), step_x.outputs[0], 0.0, 0.0).outputs["Vector"], line_a.inputs["Offset"])

    line_b = safe_node(tree, "GeometryNodeMeshLine", (bx - 700, by + 100))
    line_b.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Post Count"], line_b.inputs["Count"])
    link_sockets(tree, _combine(tree, (bx - 900, by + 220), start_x.outputs[0], w_neg.outputs[0], 0.0).outputs["Vector"], line_b.inputs["Start Location"])
    link_sockets(tree, _combine(tree, (bx - 900, by + 140), step_x.outputs[0], 0.0, 0.0).outputs["Vector"], line_b.inputs["Offset"])

    post = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by + 300))
    link_sockets(tree, _combine(tree, (bx - 700, by + 240), gin.outputs["Beam Thickness"], gin.outputs["Beam Thickness"], gin.outputs["Post Height"]).outputs["Vector"], post.inputs["Size"])
    post_up = _place(tree, (bx - 300, by + 300), post.outputs["Mesh"], z=_math(tree, "MULTIPLY", (bx - 700, by + 180), gin.outputs["Post Height"], 0.5).outputs[0])
    posts_a = _instance(tree, (bx - 100, by + 400), line_a.outputs["Mesh"], post_up)
    posts_b = _instance(tree, (bx - 100, by + 100), line_b.outputs["Mesh"], post_up)

    beam = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by))
    link_sockets(tree, _combine(tree, (bx - 700, by - 60), gin.outputs["Length"], gin.outputs["Beam Thickness"], gin.outputs["Beam Thickness"]).outputs["Vector"], beam.inputs["Size"])
    beam_z = _math(tree, "ADD", (bx - 700, by - 120), gin.outputs["Post Height"],
                   _math(tree, "MULTIPLY", (bx - 820, by - 120), gin.outputs["Beam Thickness"], 0.5).outputs[0])
    beam_a = _place(tree, (bx - 300, by), beam.outputs["Mesh"], y=w_half.outputs[0], z=beam_z.outputs[0])
    beam_b = _place(tree, (bx - 100, by), beam.outputs["Mesh"], y=w_neg.outputs[0], z=beam_z.outputs[0])

    rafter_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 500, by - 200))
    rafter_line.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Post Count"], rafter_line.inputs["Count"])
    link_sockets(tree, _combine(tree, (bx - 700, by - 120), start_x.outputs[0], 0.0, 0.0).outputs["Vector"], rafter_line.inputs["Start Location"])
    link_sockets(tree, _combine(tree, (bx - 700, by - 200), step_x.outputs[0], 0.0, 0.0).outputs["Vector"], rafter_line.inputs["Offset"])

    rafter = safe_node(tree, "GeometryNodeMeshCube", (bx - 300, by - 400))
    link_sockets(tree, _combine(tree, (bx - 500, by - 460), gin.outputs["Beam Thickness"], gin.outputs["Width"], gin.outputs["Beam Thickness"]).outputs["Vector"], rafter.inputs["Size"])
    rafter_z = _math(tree, "ADD", (bx - 500, by - 500), gin.outputs["Post Height"],
                     _math(tree, "MULTIPLY", (bx - 620, by - 500), gin.outputs["Beam Thickness"], 1.5).outputs[0])
    rafter_up = _place(tree, (bx - 100, by - 400), rafter.outputs["Mesh"], z=rafter_z.outputs[0])
    rafters = _instance(tree, (bx + 100, by - 200), rafter_line.outputs["Mesh"], rafter_up)

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 300, by + 200))
    link_sockets(tree, posts_a, join.inputs["Geometry"])
    link_sockets(tree, posts_b, join.inputs["Geometry"])
    link_sockets(tree, beam_a, join.inputs["Geometry"])
    link_sockets(tree, beam_b, join.inputs["Geometry"])
    link_sockets(tree, rafters, join.inputs["Geometry"])

    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 500, by + 300))
    store.data_type = "INT"
    store.inputs["Name"].default_value = "post_count"
    link_sockets(tree, gin.outputs["Post Count"], store.inputs["Value"])
    link_sockets(tree, join.outputs["Geometry"], store.inputs["Geometry"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(line_a, "curve")
    color_node(line_b, "curve")
    color_node(post, "geometry")
    color_node(beam, "geometry")
    color_node(rafter_line, "curve")
    color_node(rafter, "geometry")
    color_node(store, "attribute")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Post Lines", "nodes": ("line", "post", "instance"), "role": "instance"},
        {"title": "Top Beams", "nodes": ("beam", "transform"), "role": "geometry"},
        {"title": "Cross Rafters", "nodes": ("rafter", "line", "instance"), "role": "instance"},
        {"title": "Output", "nodes": ("store", "join", "Group Output"), "role": "output"},
    ])


# -- Registry --
register_builder("MEL_castle_corner_turret", build_castle_corner_turret, "Castle Corner Turret",
    "Corner turret with conical roof and merlon ring; turret_height attribute.",
    "castle")
register_builder("MEL_castle_portcullis", build_castle_portcullis, "Castle Portcullis",
    "Bar lattice portcullis with frame, head beam and cross braces.",
    "castle")
register_builder("MEL_castle_arrow_slit", build_castle_arrow_slit, "Castle Arrow-Slit Wall",
    "Defensive wall patch with instanced arrow-slit openings.",
    "castle")
register_builder("MEL_castle_hoarding", build_castle_hoarding, "Castle Hoarding",
    "Projecting wooden gallery with posts, floor, wall plate and canopy.",
    "castle")
register_builder("MEL_castle_siege_tower", build_castle_siege_tower, "Castle Siege Tower",
    "Siege tower blank - corner posts, stacked decks, optional roof cap.",
    "castle")
register_builder("MEL_castle_barbican", build_castle_barbican, "Castle Barbican",
    "Barbican gate - pillars, lintel, portcullis slot and flanking turrets.",
    "castle")
register_builder("MEL_pergola_walkway", build_pergola_walkway, "Pergola Walkway",
    "Garden pergola - twin post lines, top beams and cross rafters.",
    "structures")