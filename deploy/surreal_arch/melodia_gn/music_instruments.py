"""Music instrument GN group builders - brass pipe, reed body, bell/chime."""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    make_group_input, register_builder,
)


def build_brass_pipe(group_name="MEL_brass_pipe"):
    """Brass instrument tube - trumpet (narrow bore) or trombone (wide bore).

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
    """Reed instrument body - clarinet (cylindrical) or oboe (conical).

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
    """Bell and chime body - spherical bell, cup bell, or tubular chime.

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


# ---------------------------------------------------------------------------
# MEL_tuning_fork
# ---------------------------------------------------------------------------

def build_tuning_fork(group_name="MEL_tuning_fork"):
    """U-shaped tines with resonance box. Pitch from tine length."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Tine Length", 0.35, 0.1, 1.0)
    add_float_param(tree, "Tine Radius", 0.008, 0.002, 0.04)
    add_float_param(tree, "Tine Gap", 0.04, 0.01, 0.2)
    add_float_param(tree, "Handle Length", 0.25, 0.1, 0.8)
    add_float_param(tree, "Handle Radius", 0.012, 0.005, 0.05)
    add_float_param(tree, "Box Width", 0.08, 0.02, 0.3)
    add_float_param(tree, "Box Height", 0.06, 0.02, 0.2)
    add_float_param(tree, "Box Depth", 0.04, 0.01, 0.15)
    add_float_param(tree, "Pitch", 440.0, 20.0, 2000.0)

    parts = []

    # Handle
    handle = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 600, by + 200))
    if handle:
        handle.inputs["Vertices"].default_value = 12
        link_sockets(tree, gin.outputs["Handle Length"], handle.inputs["Depth"])
        link_sockets(tree, gin.outputs["Handle Radius"], handle.inputs["Radius"])
        # Lift so bottom at z=0
        handle_xf = safe_node(tree, "GeometryNodeTransform", (bx - 400, by + 200))
        if handle_xf:
            link_sockets(tree, handle.outputs["Mesh"], handle_xf.inputs["Geometry"])
            half_h = safe_node(tree, "ShaderNodeMath", (bx - 600, by + 150))
            if half_h:
                half_h.operation = "MULTIPLY"
                link_sockets(tree, gin.outputs["Handle Length"], half_h.inputs[0])
                half_h.inputs[1].default_value = 0.5
                link_float_to_vector(tree, half_h.outputs[0], handle_xf, "Translation",
                                     component=2, defaults=(0.0, 0.0, 0.0))
            parts.append(handle_xf.outputs["Geometry"])

    # Two tines
    for side in (-1, 1):
        tine = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 600, by - side * 200))
        if tine:
            tine.inputs["Vertices"].default_value = 8
            link_sockets(tree, gin.outputs["Tine Length"], tine.inputs["Depth"])
            link_sockets(tree, gin.outputs["Tine Radius"], tine.inputs["Radius"])
            # Position tine at gap offset
            gap = safe_node(tree, "ShaderNodeMath", (bx - 400, by - side * 250))
            if gap:
                gap.operation = "MULTIPLY"
                link_sockets(tree, gin.outputs["Tine Gap"], gap.inputs[0])
                gap.inputs[1].default_value = side * 0.5
            tine_xf = safe_node(tree, "GeometryNodeTransform", (bx - 200, by - side * 200))
            if tine_xf:
                link_sockets(tree, tine.outputs["Mesh"], tine_xf.inputs["Geometry"])
                if gap:
                    link_float_to_vector(tree, gap.outputs[0], tine_xf, "Translation",
                                         component=0, defaults=(0.0, 0.0, 0.0))
                tine_half = safe_node(tree, "ShaderNodeMath", (bx - 600, by - side * 200 - 80))
                tine_base = safe_node(tree, "ShaderNodeMath", (bx - 420, by - side * 200 - 80))
                tine_lift = safe_node(tree, "ShaderNodeMath", (bx - 240, by - side * 200 - 80))
                if tine_half and tine_base and tine_lift:
                    tine_half.operation = "MULTIPLY"
                    link_sockets(tree, gin.outputs["Tine Length"], tine_half.inputs[0])
                    tine_half.inputs[1].default_value = 0.5
                    tine_base.operation = "ADD"
                    link_sockets(tree, gin.outputs["Handle Length"], tine_base.inputs[0])
                    link_sockets(tree, gin.outputs["Box Height"], tine_base.inputs[1])
                    tine_lift.operation = "ADD"
                    link_sockets(tree, tine_base.outputs[0], tine_lift.inputs[0])
                    link_sockets(tree, tine_half.outputs[0], tine_lift.inputs[1])
                    link_float_to_vector(
                        tree,
                        tine_lift.outputs[0],
                        tine_xf,
                        "Translation",
                        component=2,
                        defaults=(0.0, 0.0, 0.0),
                    )
                parts.append(tine_xf.outputs["Geometry"])

    # Resonance box (at top of handle)
    box = safe_node(tree, "GeometryNodeMeshCube", (bx - 600, by + 400))
    if box:
        box_size = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 800, by + 440))
        if box_size:
            link_sockets(tree, gin.outputs["Box Width"], box_size.inputs["X"])
            link_sockets(tree, gin.outputs["Box Depth"], box_size.inputs["Y"])
            link_sockets(tree, gin.outputs["Box Height"], box_size.inputs["Z"])
            link_sockets(tree, box_size.outputs["Vector"], box.inputs["Size"])
        box_xf = safe_node(tree, "GeometryNodeTransform", (bx - 400, by + 400))
        if box_xf:
            link_sockets(tree, box.outputs["Mesh"], box_xf.inputs["Geometry"])
            # Place the box directly above the handle.
            half_box = safe_node(tree, "ShaderNodeMath", (bx - 780, by + 350))
            lift = safe_node(tree, "ShaderNodeMath", (bx - 600, by + 350))
            if half_box and lift:
                half_box.operation = "MULTIPLY"
                link_sockets(tree, gin.outputs["Box Height"], half_box.inputs[0])
                half_box.inputs[1].default_value = 0.5
                lift.operation = "ADD"
                link_sockets(tree, gin.outputs["Handle Length"], lift.inputs[0])
                link_sockets(tree, half_box.outputs[0], lift.inputs[1])
                link_float_to_vector(tree, lift.outputs[0], box_xf, "Translation",
                                     component=2, defaults=(0.0, 0.0, 0.0))
            parts.append(box_xf.outputs["Geometry"])

    # Join all
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx, by))
    for p in parts:
        if p:
            link_sockets(tree, p, join.inputs["Geometry"])

    # Store pitch
    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 200, by))
    if store:
        store.data_type = "FLOAT"
        try:
            store.inputs["Name"].default_value = "pitch"
        except Exception:
            pass
        link_sockets(tree, join.outputs["Geometry"], store.inputs["Geometry"])
        link_sockets(tree, gin.outputs["Pitch"], store.inputs["Value"])
        result = store.outputs["Geometry"]
    else:
        result = join.outputs["Geometry"]

    link_sockets(tree, result, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Tines", "nodes": ("cylinder", "transform"), "role": "geometry"},
        {"title": "Handle + Box", "nodes": ("cylinder", "cube", "join"), "role": "geometry"},
        {"title": "Output", "nodes": ("store", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_singing_bowl
# ---------------------------------------------------------------------------

def build_singing_bowl(group_name="MEL_singing_bowl"):
    """Rim-resonant bowl with strike point. Harmonic overtones from wall profile."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Radius", 0.15, 0.05, 0.5)
    add_float_param(tree, "Wall Thickness", 0.004, 0.001, 0.02)
    add_float_param(tree, "Depth", 0.08, 0.02, 0.3)
    add_float_param(tree, "Rim Width", 0.02, 0.005, 0.1)
    add_float_param(tree, "Strike Point", 0.0, 0.0, 1.0)
    add_float_param(tree, "Pitch", 256.0, 20.0, 2000.0)

    # Bowl profile: shell a sphere, delete the upper hemisphere, then scale
    # the retained half to the requested depth.
    outer = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 400, by))
    if outer:
        link_sockets(tree, gin.outputs["Radius"], outer.inputs["Radius"])
        outer.inputs["Segments"].default_value = 32
        outer.inputs["Rings"].default_value = 16

    # Inner sphere (smaller)
    inner_r = safe_node(tree, "ShaderNodeMath", (bx - 600, by - 100))
    if inner_r:
        inner_r.operation = "SUBTRACT"
        link_sockets(tree, gin.outputs["Radius"], inner_r.inputs[0])
        link_sockets(tree, gin.outputs["Wall Thickness"], inner_r.inputs[1])
    inner = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 400, by - 200))
    if inner:
        if inner_r:
            link_sockets(tree, inner_r.outputs[0], inner.inputs["Radius"])
        inner.inputs["Segments"].default_value = 32
        inner.inputs["Rings"].default_value = 16

    # Boolean difference for shell
    boolean = safe_node(tree, "GeometryNodeMeshBoolean", (bx - 100, by))
    if boolean and outer and inner:
        boolean.operation = "DIFFERENCE"
        link_sockets(tree, outer.outputs["Mesh"], boolean.inputs[0])
        link_sockets(tree, inner.outputs["Mesh"], boolean.inputs[1])
        shell = boolean.outputs["Mesh"]
    else:
        shell = outer.outputs["Mesh"] if outer else None

    if shell:
        position = safe_node(tree, "GeometryNodeInputPosition", (bx - 120, by - 360))
        separate = safe_node(tree, "ShaderNodeSeparateXYZ", (bx + 60, by - 360))
        compare = safe_node(tree, "FunctionNodeCompare", (bx + 240, by - 360))
        delete = safe_node(tree, "GeometryNodeDeleteGeometry", (bx + 420, by - 160))
        if position and separate and compare and delete:
            compare.data_type = "FLOAT"
            compare.operation = "GREATER_THAN"
            compare.inputs[1].default_value = 0.0
            delete.domain = "FACE"
            link_sockets(tree, position.outputs["Position"], separate.inputs["Vector"])
            link_sockets(tree, separate.outputs["Z"], compare.inputs[0])
            link_sockets(tree, shell, delete.inputs["Geometry"])
            link_sockets(tree, compare.outputs["Result"], delete.inputs["Selection"])
            shell = delete.outputs["Geometry"]

        depth_ratio = safe_node(tree, "ShaderNodeMath", (bx + 240, by - 520))
        bowl_xf = safe_node(tree, "GeometryNodeTransform", (bx + 600, by - 160))
        if depth_ratio and bowl_xf:
            depth_ratio.operation = "DIVIDE"
            link_sockets(tree, gin.outputs["Depth"], depth_ratio.inputs[0])
            link_sockets(tree, gin.outputs["Radius"], depth_ratio.inputs[1])
            link_sockets(tree, shell, bowl_xf.inputs["Geometry"])
            link_float_to_vector(
                tree,
                depth_ratio.outputs[0],
                bowl_xf,
                "Scale",
                component=2,
                defaults=(1.0, 1.0, 1.0),
            )
            link_float_to_vector(
                tree,
                gin.outputs["Depth"],
                bowl_xf,
                "Translation",
                component=2,
                defaults=(0.0, 0.0, 0.0),
            )
            shell = bowl_xf.outputs["Geometry"]

    # Rim ring (torus-like) - torus not in 5.2, use tube instead
    rim = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 400, by + 200))
    if rim:
        # Set radius via the curve's radius input
        if rim.inputs.get("Radius"):
            link_sockets(tree, gin.outputs["Radius"], rim.inputs["Radius"])
        rim.inputs["Resolution"].default_value = 32
        rim_geo = rim.outputs["Curve"]
        # Sweep a small circle along the rim for thickness
        rim_profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 200, by + 100))
        if rim_profile:
            rim_profile.inputs["Resolution"].default_value = 8
            link_sockets(tree, gin.outputs["Rim Width"], rim_profile.inputs["Radius"])
        rim_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx, by + 200))
        if rim_mesh and rim_geo:
            link_sockets(tree, rim_geo, rim_mesh.inputs.get("Curve") or rim_mesh.inputs[0])
            if rim_profile:
                link_sockets(tree, rim_profile.outputs["Curve"],
                             rim_mesh.inputs.get("Profile Curve") or rim_mesh.inputs[1])
            rim_geo = rim_mesh.outputs["Mesh"]
    else:
        rim_geo = None

    # Join shell + rim
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 100, by))
    if shell:
        link_sockets(tree, shell, join.inputs["Geometry"])
    if rim_geo:
        link_sockets(tree, rim_geo, join.inputs["Geometry"])

    # Store pitch
    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 300, by))
    if store:
        store.data_type = "FLOAT"
        try:
            store.inputs["Name"].default_value = "pitch"
        except Exception:
            pass
        link_sockets(tree, join.outputs["Geometry"], store.inputs["Geometry"])
        link_sockets(tree, gin.outputs["Pitch"], store.inputs["Value"])
        strike_store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 500, by))
        if strike_store:
            strike_store.data_type = "FLOAT"
            strike_store.inputs["Name"].default_value = "strike_point"
            link_sockets(tree, store.outputs["Geometry"], strike_store.inputs["Geometry"])
            link_sockets(tree, gin.outputs["Strike Point"], strike_store.inputs["Value"])
            result = strike_store.outputs["Geometry"]
        else:
            result = store.outputs["Geometry"]
    else:
        result = join.outputs["Geometry"]

    link_sockets(tree, result, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Shell", "nodes": ("sphere", "boolean"), "role": "geometry"},
        {"title": "Rim", "nodes": ("torus", "join"), "role": "geometry"},
        {"title": "Output", "nodes": ("store", "Group Output"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_church_bell
# ---------------------------------------------------------------------------

def build_church_bell(group_name="MEL_church_bell"):
    """Inverted cup bell with crown, shoulder, and sound bow. Clapper swing."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Height", 0.6, 0.1, 2.0)
    add_float_param(tree, "Mouth Radius", 0.25, 0.05, 1.0)
    add_float_param(tree, "Wall Thickness", 0.01, 0.002, 0.05)
    add_float_param(tree, "Crown Width", 0.08, 0.02, 0.3)
    add_bool_param(tree, "Has Clapper", True)
    add_float_param(tree, "Clapper Swing", 0.0, -30.0, 30.0)
    add_float_param(tree, "Pitch", 128.0, 20.0, 2000.0)

    parts = []

    # Outer profile: cone (inverted)
    outer = safe_node(tree, "GeometryNodeMeshCone", (bx - 600, by))
    if outer:
        outer.inputs["Vertices"].default_value = 48
        link_sockets(tree, gin.outputs["Height"], outer.inputs["Depth"])
        link_sockets(tree, gin.outputs["Mouth Radius"], outer.inputs["Radius Bottom"])
        # Top radius = mouth - shoulder
        top_r = safe_node(tree, "ShaderNodeMath", (bx - 800, by - 100))
        if top_r:
            top_r.operation = "MULTIPLY"
            link_sockets(tree, gin.outputs["Mouth Radius"], top_r.inputs[0])
            top_r.inputs[1].default_value = 0.3
            link_sockets(tree, top_r.outputs[0], outer.inputs["Radius Top"])
        outer.fill_type = "NGON"

    # Inner cone (smaller)
    inner_h = safe_node(tree, "ShaderNodeMath", (bx - 800, by + 100))
    if inner_h:
        inner_h.operation = "SUBTRACT"
        link_sockets(tree, gin.outputs["Height"], inner_h.inputs[0])
        link_sockets(tree, gin.outputs["Wall Thickness"], inner_h.inputs[1])
    inner_mouth = safe_node(tree, "ShaderNodeMath", (bx - 800, by - 200))
    if inner_mouth:
        inner_mouth.operation = "SUBTRACT"
        link_sockets(tree, gin.outputs["Mouth Radius"], inner_mouth.inputs[0])
        link_sockets(tree, gin.outputs["Wall Thickness"], inner_mouth.inputs[1])
    inner = safe_node(tree, "GeometryNodeMeshCone", (bx - 600, by - 300))
    if inner:
        inner.inputs["Vertices"].default_value = 48
        if inner_h:
            link_sockets(tree, inner_h.outputs[0], inner.inputs["Depth"])
        if inner_mouth:
            link_sockets(tree, inner_mouth.outputs[0], inner.inputs["Radius Bottom"])
            inner_top = safe_node(tree, "ShaderNodeMath", (bx - 800, by - 400))
            if inner_top:
                inner_top.operation = "MULTIPLY"
                link_sockets(tree, inner_mouth.outputs[0], inner_top.inputs[0])
                inner_top.inputs[1].default_value = 0.3
                link_sockets(tree, inner_top.outputs[0], inner.inputs["Radius Top"])
        inner.fill_type = "NGON"

    # Boolean difference
    boolean = safe_node(tree, "GeometryNodeMeshBoolean", (bx - 300, by))
    if boolean and outer and inner:
        boolean.operation = "DIFFERENCE"
        link_sockets(tree, outer.outputs["Mesh"], boolean.inputs[0])
        link_sockets(tree, inner.outputs["Mesh"], boolean.inputs[1])
        shell = boolean.outputs["Mesh"]
    else:
        shell = outer.outputs["Mesh"] if outer else None

    if shell:
        parts.append(shell)

    # Crown (top cap)
    crown = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 600, by + 300))
    if crown:
        crown.inputs["Vertices"].default_value = 24
        link_sockets(tree, gin.outputs["Crown Width"], crown.inputs["Radius"])
        crown.inputs["Depth"].default_value = 0.05
        crown.fill_type = "NGON"
        # Position at top of bell
        crown_xf = safe_node(tree, "GeometryNodeTransform", (bx - 400, by + 300))
        if crown_xf:
            link_sockets(tree, crown.outputs["Mesh"], crown_xf.inputs["Geometry"])
            lift = safe_node(tree, "ShaderNodeMath", (bx - 600, by + 250))
            if lift:
                lift.operation = "SUBTRACT"
                link_sockets(tree, gin.outputs["Height"], lift.inputs[0])
                lift.inputs[1].default_value = 0.025
                link_float_to_vector(tree, lift.outputs[0], crown_xf, "Translation",
                                     component=2, defaults=(0.0, 0.0, 0.0))
            parts.append(crown_xf.outputs["Geometry"])
        else:
            parts.append(crown.outputs["Mesh"])

    # Clapper (optional) - use switch to toggle
    clapper_switch = safe_node(tree, "GeometryNodeSwitch", (bx - 200, by + 400))
    if clapper_switch:
        try:
            clapper_switch.input_type = "GEOMETRY"
        except Exception:
            pass
        link_sockets(tree, gin.outputs["Has Clapper"],
                     clapper_switch.inputs.get("Switch") or clapper_switch.inputs[0])

        clapper = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 600, by + 500))
        if clapper:
            clapper.inputs["Radius"].default_value = 0.04
            clapper.inputs["Segments"].default_value = 16
            clapper.inputs["Rings"].default_value = 8
            swing = safe_node(tree, "ShaderNodeMath", (bx - 400, by + 500))
            if swing:
                swing.operation = "DIVIDE"
                link_sockets(tree, gin.outputs["Clapper Swing"], swing.inputs[0])
                swing.inputs[1].default_value = 57.3
            clapper_xf = safe_node(tree, "GeometryNodeTransform", (bx - 200, by + 500))
            if clapper_xf:
                link_sockets(tree, clapper.outputs["Mesh"], clapper_xf.inputs["Geometry"])
                if swing:
                    link_float_to_vector(
                        tree,
                        swing.outputs[0],
                        clapper_xf,
                        "Rotation",
                        component=1,
                        defaults=(0.0, 0.0, 0.0),
                    )
                clapper_xf.inputs["Translation"].default_value = (0, 0, 0)
                true_in = clapper_switch.inputs.get("True")
                if true_in is None:
                    true_in = clapper_switch.inputs[1] if len(clapper_switch.inputs) > 1 else None
                if true_in:
                    link_sockets(tree, clapper_xf.outputs["Geometry"], true_in)
            else:
                true_in = clapper_switch.inputs.get("True")
                if true_in is None:
                    true_in = clapper_switch.inputs[1] if len(clapper_switch.inputs) > 1 else None
                if true_in:
                    link_sockets(tree, clapper.outputs["Mesh"], true_in)

        # Get output socket directly
        out_sock = clapper_switch.outputs.get("Output")
        if out_sock is None:
            out_sock = clapper_switch.outputs[0] if clapper_switch.outputs else None
        if out_sock:
            parts.append(out_sock)

    # Join all
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 100, by))
    for p in parts:
        if p:
            link_sockets(tree, p, join.inputs["Geometry"])

    # Store pitch
    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 300, by))
    if store:
        store.data_type = "FLOAT"
        try:
            store.inputs["Name"].default_value = "pitch"
        except Exception:
            pass
        link_sockets(tree, join.outputs["Geometry"], store.inputs["Geometry"])
        link_sockets(tree, gin.outputs["Pitch"], store.inputs["Value"])
        result = store.outputs["Geometry"]
    else:
        result = join.outputs["Geometry"]

    link_sockets(tree, result, gout.inputs["Geometry"])

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Shell", "nodes": ("cone", "boolean"), "role": "geometry"},
        {"title": "Crown + Clapper", "nodes": ("cylinder", "sphere", "switch"), "role": "geometry"},
        {"title": "Output", "nodes": ("store", "Group Output"), "role": "output"},
    ])


# -- Registry --
register_builder("MEL_brass_pipe", build_brass_pipe, "Brass Pipe",
    "Brass tube geometry - narrow trumpet bore or wide trombone bore with bell flare.",
    "music")
register_builder("MEL_reed_body", build_reed_body, "Reed Body",
    "Reed instrument body - clarinet (cylindrical) or oboe (conical) with tone holes.",
    "music")
register_builder("MEL_bell_chime", build_bell_chime, "Bell/Chime",
    "Spherical bell, cup bell, or tubular chime with partial control and clapper flag.",
    "music")
register_builder("MEL_tuning_fork", build_tuning_fork, "Tuning Fork",
    "U-shaped tines with resonance box - pitch from tine length.",
    "music")
register_builder("MEL_singing_bowl", build_singing_bowl, "Singing Bowl",
    "Rim-resonant bowl with strike point - harmonic overtones from wall profile.",
    "music")
register_builder("MEL_church_bell", build_church_bell, "Church Bell",
    "Inverted cup bell with crown, shoulder, and sound bow - clapper swing.",
    "music")
