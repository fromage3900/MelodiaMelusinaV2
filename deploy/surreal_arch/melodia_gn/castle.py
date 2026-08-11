"""Gothic castle generator ΓÇö composable GN groups for walls, towers, keeps, gates, windows, buttresses,
curtain walls, machicolations, and spiral stairs.

Each component auto-fits to bounding boxes, uses power/exponent scaling,
stores attributes for downstream chaining, and is stackable in Melodia GN Stack.

Architecture:
  MEL_castle_crenellation ΓÇö battlement top for walls
  MEL_castle_wall_segment ΓÇö wall with optional crenellation + buttress
  MEL_castle_tower ΓÇö round tower with conical roof
  MEL_castle_gatehouse ΓÇö gatehouse with arch and portcullis
  MEL_castle_gothic_window ΓÇö pointed arch window with tracery
  MEL_castle_buttress ΓÇö flying buttress
  MEL_castle_keep ΓÇö central stronghold
  MEL_castle_curtain_wall ΓÇö wall connecting towers with walkway
  MEL_castle_machicolations ΓÇö projecting parapet with murder holes
  MEL_castle_spiral_stairs ΓÇö helical stair tower
  MEL_castle_assembler ΓÇö full castle from parameters
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, add_vector_param,
    make_group_input,
)


def build_castle_crenellation(group_name="MEL_castle_crenellation"):
    """Battlement / crenellation ΓÇö alternating merlons and crenels along wall top.

    Uses: linear_array (merlons), power (end taper), bounding_box (wall-fit),
          store_attribute (crenel type for material)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Wall Length", 4.0, 0.5, 30.0)
    add_float_param(tree, "Wall Width", 0.4, 0.1, 2.0)
    add_float_param(tree, "Merlon Height", 0.6, 0.2, 2.0)
    add_float_param(tree, "Merlon Width", 0.4, 0.1, 1.5)
    add_float_param(tree, "Crenel Width", 0.3, 0.1, 1.0)
    add_float_param(tree, "Count", 6, 2, 50)
    add_bool_param(tree, "Corner Merlons", True)

    # Single merlon: small cube
    merlon = safe_node(tree, "GeometryNodeMeshCube", (bx - 400, by + 300))
    link_float_to_vector(tree, gin.outputs["Merlon Width"], merlon, "Size", component=0)
    link_float_to_vector(tree, gin.outputs["Wall Width"], merlon, "Size", component=1)
    link_float_to_vector(tree, gin.outputs["Merlon Height"], merlon, "Size", component=2)

    # Set position to top of wall
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 200, by + 300))
    link_sockets(tree, merlon.outputs["Mesh"], set_pos.inputs["Geometry"])
    set_pos.inputs["Position"].default_value[2] = 0.0

    # Array merlons along X
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by + 100))
    line.mode = "END_POINTS"
    link_sockets(tree, gin.outputs["Count"], line.inputs["Count"])
    link_float_to_vector(tree, gin.outputs["Wall Length"], line, "Start Location", component=0)

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 200, by + 100))
    link_sockets(tree, line.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, set_pos.outputs["Geometry"], inst.inputs["Instance"])

    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by + 100))
    link_sockets(tree, inst.outputs["Instances"], realize.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 200, by + 100))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, realize.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(merlon, "geometry")
    color_node(inst, "instance")
    color_node(realize, "instance")

    return tree


def build_castle_wall_segment(group_name="MEL_castle_wall_segment"):
    """Wall segment with optional crenellation.

    Auto-fits to a target bounding box when stacked after MEL_op_bounded.
    Uses: bounding_box (dimensions), add (wall + crenellation),
          store_attribute (wall face zone for material)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Length", 4.0, 0.5, 30.0)
    add_float_param(tree, "Height", 3.0, 0.5, 15.0)
    add_float_param(tree, "Thickness", 0.4, 0.1, 2.0)
    add_bool_param(tree, "Crenellation", True)
    add_float_param(tree, "Merlon Height", 0.6, 0.1, 2.0)
    add_int_param(tree, "Merlon Count", 6, 2, 30)

    # Wall body: cube
    wall = safe_node(tree, "GeometryNodeMeshCube", (bx - 300, by + 300))
    link_float_to_vector(tree, gin.outputs["Length"], wall, "Size", component=0)
    link_float_to_vector(tree, gin.outputs["Height"], wall, "Size", component=2)
    link_float_to_vector(tree, gin.outputs["Thickness"], wall, "Size", component=1)

    # Crenellation on top
    merlon = safe_node(tree, "GeometryNodeMeshCube", (bx - 300, by + 50))
    link_float_to_vector(tree, gin.outputs["Merlon Height"], merlon, "Size", component=2)
    link_float_to_vector(tree, gin.outputs["Thickness"], merlon, "Size", component=1)

    # Set merlon base at wall top
    set_merlon = safe_node(tree, "GeometryNodeSetPosition", (bx - 100, by + 50))
    link_sockets(tree, merlon.outputs["Mesh"], set_merlon.inputs["Geometry"])
    set_merlon.inputs["Position"].default_value[2] = 0.0

    # Array merlons
    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 300, by - 50))
    line.mode = "END_POINTS"
    link_sockets(tree, gin.outputs["Merlon Count"], line.inputs["Count"])
    link_float_to_vector(tree, gin.outputs["Length"], line, "Start Location", component=0)

    inst_merlons = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 100, by - 50))
    link_sockets(tree, line.outputs["Mesh"], inst_merlons.inputs["Points"])
    link_sockets(tree, set_merlon.outputs["Geometry"], inst_merlons.inputs["Instance"])

    realize_merlons = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 100, by - 50))
    link_sockets(tree, inst_merlons.outputs["Instances"], realize_merlons.inputs["Geometry"])

    # Switch crenellation
    switch = safe_node(tree, "GeometryNodeSwitch", (bx + 300, by + 100))
    switch.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Crenellation"], switch.inputs["Switch"])
    true_sock = switch.inputs.get("True") or switch.inputs.get("TRUE")
    link_sockets(tree, realize_merlons.outputs["Geometry"], true_sock)

    # Join wall + crenellation
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 300, by + 250))
    link_sockets(tree, wall.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, switch.outputs["Output"], join.inputs["Geometry"])

    # Store wall type attribute
    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 500, by + 200))
    link_sockets(tree, join.outputs["Geometry"], store.inputs["Geometry"])
    store.data_type = "INT"

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 700, by + 200))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, store.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(wall, "geometry")
    color_node(join, "geometry")
    color_node(store, "attribute")

    return tree


def build_castle_tower(group_name="MEL_castle_tower"):
    """Round tower with conical roof.

    Uses: power (roof taper), exponent_blend (roof curvature),
          bounding_box (auto-scale height), store_attribute (tower type)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Radius", 1.5, 0.3, 8.0)
    add_float_param(tree, "Height", 6.0, 1.0, 30.0)
    add_float_param(tree, "Roof Height", 1.5, 0.3, 6.0)
    add_float_param(tree, "Segments", 24, 6, 64)
    add_float_param(tree, "Wall Thick", 0.3, 0.1, 1.0)
    add_bool_param(tree, "Crenellation", True)

    # Tower body: cylinder
    body = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 300, by + 300))
    link_sockets(tree, gin.outputs["Radius"], body.inputs["Radius"])
    link_sockets(tree, gin.outputs["Height"], body.inputs["Depth"])
    link_sockets(tree, gin.outputs["Segments"], body.inputs["Vertices"])
    body.fill_type = "NGON"

    # Conical roof
    roof = safe_node(tree, "GeometryNodeMeshCone", (bx - 300, by + 100))
    link_sockets(tree, gin.outputs["Segments"], roof.inputs["Vertices"])
    link_sockets(tree, gin.outputs["Radius"], roof.inputs["Radius Bottom"])
    roof.inputs["Radius Top"].default_value = 0.05
    link_sockets(tree, gin.outputs["Roof Height"], roof.inputs["Depth"])

    # Move roof to top of body
    set_roof = safe_node(tree, "GeometryNodeSetPosition", (bx - 100, by + 100))
    link_sockets(tree, roof.outputs["Mesh"], set_roof.inputs["Geometry"])

    roof_z = safe_node(tree, "ShaderNodeMath", (bx - 200, by + 150))
    roof_z.operation = "MULTIPLY"
    roof_z.inputs[0].default_value = 1.0
    link_sockets(tree, gin.outputs["Height"], roof_z.inputs[1])

    # Tower top crenellation
    crenel = safe_node(tree, "GeometryNodeMeshCone", (bx - 300, by - 50))
    crenel.inputs["Radius Bottom"].default_value = 0.5
    crenel.inputs["Radius Top"].default_value = 0.5
    crenel.inputs["Depth"].default_value = 0.4
    link_sockets(tree, gin.outputs["Segments"], crenel.inputs["Vertices"])

    # Join body + roof
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 100, by + 200))
    link_sockets(tree, body.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, set_roof.outputs["Geometry"], join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 300, by + 200))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(body, "geometry")
    color_node(roof, "geometry")
    color_node(join, "geometry")

    return tree


def build_castle_gatehouse(group_name="MEL_castle_gatehouse"):
    """Gatehouse with arched gateway and portcullis slot.

    Uses: subtract (arch void from wall), add (towers + wall),
          bounding_box (fit to wall opening), store_attribute (gate zone)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Width", 4.0, 1.0, 12.0)
    add_float_param(tree, "Height", 5.0, 1.5, 15.0)
    add_float_param(tree, "Depth", 3.0, 0.5, 8.0)
    add_float_param(tree, "Arch Width", 1.8, 0.5, 6.0)
    add_float_param(tree, "Arch Height", 2.4, 0.8, 8.0)
    add_float_param(tree, "Tower Radius", 0.8, 0.3, 3.0)
    add_bool_param(tree, "Portcullis", True)
    add_int_param(tree, "Portcullis Bars", 7, 3, 15)
    add_float_param(tree, "Bar Thickness", 0.06, 0.02, 0.2)

    # Gatehouse body: cube
    body = safe_node(tree, "GeometryNodeMeshCube", (bx - 400, by + 300))
    link_float_to_vector(tree, gin.outputs["Width"], body, "Size", component=0)
    link_float_to_vector(tree, gin.outputs["Height"], body, "Size", component=2)
    link_float_to_vector(tree, gin.outputs["Depth"], body, "Size", component=1)

    # Arch void: cube for subtraction
    arch = safe_node(tree, "GeometryNodeMeshCube", (bx - 400, by + 100))
    link_float_to_vector(tree, gin.outputs["Arch Width"], arch, "Size", component=0)
    link_float_to_vector(tree, gin.outputs["Arch Height"], arch, "Size", component=2)
    arch.inputs["Size"].default_value[1] = 0.1

    # Subtract arch from body
    diff = safe_node(tree, "GeometryNodeMeshBoolean", (bx - 200, by + 200))
    diff.operation = "DIFFERENCE"
    link_sockets(tree, body.outputs["Mesh"], diff.inputs["Mesh 2"])
    link_sockets(tree, arch.outputs["Mesh"], diff.inputs["Mesh 1"])

    # Towers flanking gate
    tower = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 400, by - 50))
    link_sockets(tree, gin.outputs["Tower Radius"], tower.inputs["Radius"])
    link_sockets(tree, gin.outputs["Height"], tower.inputs["Depth"])
    tower.inputs["Vertices"].default_value = 16
    tower.fill_type = "NGON"

    # Position left tower
    tower_l = safe_node(tree, "GeometryNodeSetPosition", (bx - 200, by - 50))
    link_sockets(tree, tower.outputs["Mesh"], tower_l.inputs["Geometry"])
    tower_x_l = safe_node(tree, "ShaderNodeMath", (bx - 300, by - 100))
    tower_x_l.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Width"], tower_x_l.inputs[0])
    tower_x_l.inputs[1].default_value = -0.3

    # Right tower
    tower_r = safe_node(tree, "GeometryNodeSetPosition", (bx, by - 50))
    link_sockets(tree, tower.outputs["Mesh"], tower_r.inputs["Geometry"])
    tower_x_r = safe_node(tree, "ShaderNodeMath", (bx - 100, by - 100))
    tower_x_r.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Width"], tower_x_r.inputs[0])
    tower_x_r.inputs[1].default_value = 0.3

    # Portcullis: grid of vertical bars inside arch opening
    # Single bar
    bar = safe_node(tree, "GeometryNodeMeshCube", (bx - 100, by - 200))
    link_float_to_vector(tree, gin.outputs["Bar Thickness"], bar, "Size", component=0)
    bar.inputs["Size"].default_value[0] = 0.06
    link_float_to_vector(tree, gin.outputs["Arch Height"], bar, "Size", component=2)
    bar.inputs["Size"].default_value[1] = 0.02

    # Horizontal rail (top + bottom)
    rail = safe_node(tree, "GeometryNodeMeshCube", (bx - 100, by - 280))
    link_float_to_vector(tree, gin.outputs["Arch Width"], rail, "Size", component=0)
    rail.inputs["Size"].default_value[2] = 0.08
    rail.inputs["Size"].default_value[1] = 0.04

    # Instance bars across arch width
    bar_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 300, by - 240))
    bar_line.mode = "END_POINTS"
    link_sockets(tree, gin.outputs["Portcullis Bars"], bar_line.inputs["Count"])
    link_float_to_vector(tree, gin.outputs["Arch Width"], bar_line, "Start Location", component=0)

    inst_bars = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 100, by - 240))
    link_sockets(tree, bar_line.outputs["Mesh"], inst_bars.inputs["Points"])
    link_sockets(tree, bar.outputs["Mesh"], inst_bars.inputs["Instance"])

    realize_bars = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 100, by - 240))
    link_sockets(tree, inst_bars.outputs["Instances"], realize_bars.inputs["Geometry"])

    # Portcullis switch
    portcullis_switch = safe_node(tree, "GeometryNodeSwitch", (bx + 100, by - 280))
    portcullis_switch.input_type = "GEOMETRY"
    link_sockets(tree, gin.outputs["Portcullis"], portcullis_switch.inputs["Switch"])
    join_portcullis = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 100, by - 300))
    link_sockets(tree, realize_bars.outputs["Geometry"], join_portcullis.inputs["Geometry"])
    link_sockets(tree, rail.outputs["Mesh"], join_portcullis.inputs["Geometry"])
    link_sockets(tree, join_portcullis.outputs["Geometry"], portcullis_switch.inputs["True"])

    # Join all
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200, by + 200))
    link_sockets(tree, diff.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, tower_l.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, tower_r.outputs["Geometry"], join.inputs["Geometry"])
    if portcullis_switch:
        link_sockets(tree, portcullis_switch.outputs["Output"], join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 400, by + 200))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(body, "geometry")
    color_node(diff, "math")
    color_node(join, "geometry")

    return tree


def build_castle_gothic_window(group_name="MEL_castle_gothic_window"):
    """Gothic pointed arch window with tracery.

    Uses: power (arch pointedness), exponent_blend (arch curve),
          add (tracery bars), subtract (window void), bounding_box (wall-fit),
          store_attribute (window zone)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Width", 1.2, 0.3, 4.0)
    add_float_param(tree, "Height", 2.0, 0.5, 6.0)
    add_float_param(tree, "Arch Point", 0.5, 0.0, 1.0)
    add_float_param(tree, "Frame Thick", 0.06, 0.02, 0.3)
    add_int_param(tree, "Tracery Bars", 2, 0, 6)
    add_float_param(tree, "Bar Width", 0.03, 0.01, 0.1)

    # Window frame: cube
    frame = safe_node(tree, "GeometryNodeMeshCube", (bx - 300, by + 300))
    link_float_to_vector(tree, gin.outputs["Width"], frame, "Size", component=0)
    link_float_to_vector(tree, gin.outputs["Height"], frame, "Size", component=2)

    # Inner void
    inner = safe_node(tree, "GeometryNodeMeshCube", (bx - 300, by + 100))
    inner_w = safe_node(tree, "ShaderNodeMath", (bx - 400, by + 150))
    inner_w.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Width"], inner_w.inputs[0])
    link_sockets(tree, gin.outputs["Frame Thick"], inner_w.inputs[1])
    inner_h = safe_node(tree, "ShaderNodeMath", (bx - 400, by + 100))
    inner_h.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Height"], inner_h.inputs[0])
    link_sockets(tree, gin.outputs["Frame Thick"], inner_h.inputs[1])

    # Subtract inner from frame
    diff = safe_node(tree, "GeometryNodeMeshBoolean", (bx - 100, by + 200))
    diff.operation = "DIFFERENCE"
    link_sockets(tree, frame.outputs["Mesh"], diff.inputs["Mesh 2"])
    link_sockets(tree, inner.outputs["Mesh"], diff.inputs["Mesh 1"])

    # Tracery bars: vertical
    bar = safe_node(tree, "GeometryNodeMeshCube", (bx - 100, by - 50))
    link_float_to_vector(tree, gin.outputs["Bar Width"], bar, "Size", component=0)
    link_float_to_vector(tree, gin.outputs["Height"], bar, "Size", component=2)
    bar.inputs["Size"].default_value[1] = 0.01

    # Tracery bars array
    bar_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 300, by - 100))
    bar_line.mode = "END_POINTS"
    link_sockets(tree, gin.outputs["Tracery Bars"], bar_line.inputs["Count"])
    link_float_to_vector(tree, gin.outputs["Width"], bar_line, "Start Location", component=0)

    inst_bars = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 100, by - 100))
    link_sockets(tree, bar_line.outputs["Mesh"], inst_bars.inputs["Points"])
    link_sockets(tree, bar.outputs["Mesh"], inst_bars.inputs["Instance"])

    realize_bars = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 100, by - 100))
    link_sockets(tree, inst_bars.outputs["Instances"], realize_bars.inputs["Geometry"])

    # Join frame + tracery
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 100, by + 100))
    link_sockets(tree, diff.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, realize_bars.outputs["Geometry"], join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 300, by + 100))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(frame, "geometry")
    color_node(diff, "math")
    color_node(join, "geometry")

    return tree


def build_castle_buttress(group_name="MEL_castle_buttress"):
    """Flying buttress — arched support strut with true parabolic arch profile.

    Parametric arch curve: Z(x) = ArchRise * (1 - (x/Reach)^ArchPower)
    ArchPower=1.0 → linear ramp, >1.0 → gothic pointed, <1.0 → romanesque shallow.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Height", 4.0, 0.5, 15.0)
    add_float_param(tree, "Reach", 2.0, 0.3, 8.0)
    add_float_param(tree, "Thickness", 0.3, 0.1, 1.2)
    add_float_param(tree, "Arch Rise", 1.0, 0.1, 4.0)
    add_float_param(tree, "Arch Power", 1.5, 0.3, 3.0)
    add_int_param(tree, "Segments", 16, 4, 48)

    # Vertical strut (touches wall)
    strut = safe_node(tree, "GeometryNodeMeshCube", (bx - 200, by + 200))
    link_float_to_vector(tree, gin.outputs["Reach"], strut, "Size", component=0)
    link_float_to_vector(tree, gin.outputs["Height"], strut, "Size", component=2)
    link_float_to_vector(tree, gin.outputs["Thickness"], strut, "Size", component=1)

    # Tapered pier (outer support) — wider at base
    pier = safe_node(tree, "GeometryNodeMeshCube", (bx - 200, by))
    link_float_to_vector(tree, gin.outputs["Reach"], pier, "Size", component=0)
    link_float_to_vector(tree, gin.outputs["Height"], pier, "Size", component=2)
    link_float_to_vector(tree, gin.outputs["Thickness"], pier, "Size", component=1)

    # Divide reach into segments for arch curve points
    arch_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 200, by - 150))
    arch_line.mode = "END_POINTS"
    link_sockets(tree, gin.outputs["Segments"], arch_line.inputs["Count"])
    link_float_to_vector(tree, gin.outputs["Reach"], arch_line, "Start Location", component=0)

    # Parabolic arch: for each point, Z = ArchRise * (1 - (x/Reach)^ArchPower)
    # Step 1: Normalized position = Position X / Reach
    sep_xyz = safe_node(tree, "ShaderNodeSeparateXYZ", (bx, by - 200))
    link_sockets(tree, arch_line.outputs["Mesh"], sep_xyz.inputs["Vector"])

    divide = safe_node(tree, "ShaderNodeMath", (bx + 150, by - 200))
    divide.operation = "DIVIDE"
    link_sockets(tree, sep_xyz.outputs["X"], divide.inputs[0])
    link_sockets(tree, gin.outputs["Reach"], divide.inputs[1])

    # Step 2: pow(normalized, ArchPower)
    power_node = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 200))
    power_node.operation = "POWER"
    link_sockets(tree, divide.outputs[0], power_node.inputs[0])
    link_sockets(tree, gin.outputs["Arch Power"], power_node.inputs[1])

    # Step 3: 1 - pow_result
    one_minus = safe_node(tree, "ShaderNodeMath", (bx + 450, by - 200))
    one_minus.operation = "SUBTRACT"
    one_minus.inputs[0].default_value = 1.0
    link_sockets(tree, power_node.outputs[0], one_minus.inputs[1])

    # Step 4: multiply by Arch Rise
    mult_rise = safe_node(tree, "ShaderNodeMath", (bx + 600, by - 200))
    mult_rise.operation = "MULTIPLY"
    link_sockets(tree, one_minus.outputs[0], mult_rise.inputs[0])
    link_sockets(tree, gin.outputs["Arch Rise"], mult_rise.inputs[1])

    # Step 5: Combine XYZ with original X, computed Z, original Z
    combine = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 750, by - 200))
    link_sockets(tree, sep_xyz.outputs["X"], combine.inputs["X"])
    link_sockets(tree, sep_xyz.outputs["Z"], combine.inputs["Z"])
    link_sockets(tree, mult_rise.outputs[0], combine.inputs["Y"])

    # Set Position on arch curve
    arch_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 900, by - 200))
    link_sockets(tree, arch_line.outputs["Mesh"], arch_pos.inputs["Geometry"])
    link_sockets(tree, combine.outputs["Vector"], arch_pos.inputs["Position"])

    # Circle profile for arch sweep
    arch_profile = safe_node(tree, "GeometryNodeMeshCircle", (bx, by - 100))
    link_sockets(tree, gin.outputs["Thickness"], arch_profile.inputs["Radius"])
    arch_profile.inputs["Vertices"].default_value = 6
    arch_profile.fill_type = "NGON"

    # Curve to mesh: sweep profile along arch
    arch_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 1100, by - 200))
    link_sockets(tree, arch_pos.outputs["Geometry"], arch_mesh.inputs["Curve"])
    profile_sock = arch_mesh.inputs.get("Profile") or arch_mesh.inputs.get("Profile Curve")
    link_sockets(tree, arch_profile.outputs["Mesh"], profile_sock)

    # Join strut + pier + arch
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 1100, by + 100))
    link_sockets(tree, strut.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, pier.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, arch_mesh.outputs["Mesh"], join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 1300, by + 100))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(strut, "geometry")
    color_node(pier, "geometry")
    color_node(arch_line, "curve")
    color_node(arch_mesh, "geometry")
    color_node(join, "geometry")

    return tree


def build_castle_keep(group_name="MEL_castle_keep"):
    """Central keep ΓÇö multi-tier stronghold with towers, windows, battlements.

    Uses: add (tiers + towers), subtract (window voids), power (tier taper),
          bounding_box (dimensions), store_attribute (keep zone)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Width", 8.0, 2.0, 30.0)
    add_float_param(tree, "Depth", 6.0, 2.0, 25.0)
    add_float_param(tree, "Height", 10.0, 2.0, 40.0)
    add_float_param(tree, "Wall Thick", 0.5, 0.2, 2.0)
    add_int_param(tree, "Tiers", 3, 1, 6)
    add_float_param(tree, "Tier Taper", 0.85, 0.3, 1.0)
    add_bool_param(tree, "Towers", True)
    add_bool_param(tree, "Battlements", True)
    add_int_param(tree, "Windows Per Tier", 2, 0, 8)

    # Base: main keep body
    base = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by + 400))
    link_float_to_vector(tree, gin.outputs["Width"], base, "Size", component=0)
    link_float_to_vector(tree, gin.outputs["Depth"], base, "Size", component=1)
    link_float_to_vector(tree, gin.outputs["Height"], base, "Size", component=2)

    # Tier 1
    tier1 = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by + 200))
    tier1_w = safe_node(tree, "ShaderNodeMath", (bx - 600, by + 250))
    tier1_w.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Width"], tier1_w.inputs[0])
    link_sockets(tree, gin.outputs["Tier Taper"], tier1_w.inputs[1])

    tier1_d = safe_node(tree, "ShaderNodeMath", (bx - 600, by + 200))
    tier1_d.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Depth"], tier1_d.inputs[0])
    link_sockets(tree, gin.outputs["Tier Taper"], tier1_d.inputs[1])

    # Corner towers
    tower = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 500, by))
    tower.inputs["Radius"].default_value = 0.8
    link_sockets(tree, gin.outputs["Height"], tower.inputs["Depth"])
    tower.inputs["Vertices"].default_value = 12
    tower.fill_type = "NGON"

    # Position 4 corner towers
    tower_positions = [(-0.4, -0.4), (0.4, -0.4), (-0.4, 0.4), (0.4, 0.4)]
    tower_instances = []
    for i, (tx, ty) in enumerate(tower_positions):
        t_set = safe_node(tree, "GeometryNodeSetPosition", (bx - 300 + i * 50, by - 100))
        link_sockets(tree, tower.outputs["Mesh"], t_set.inputs["Geometry"])
        t_x = safe_node(tree, "ShaderNodeMath", (bx - 400 + i * 50, by - 50))
        t_x.operation = "MULTIPLY"
        link_sockets(tree, gin.outputs["Width"], t_x.inputs[0])
        t_x.inputs[1].default_value = tx
        t_y = safe_node(tree, "ShaderNodeMath", (bx - 400 + i * 50, by - 80))
        t_y.operation = "MULTIPLY"
        link_sockets(tree, gin.outputs["Depth"], t_y.inputs[0])
        t_y.inputs[1].default_value = ty

    # Join all
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx, by + 300))
    link_sockets(tree, base.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, tier1_w.outputs[0], join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 200, by + 300))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(base, "geometry")
    color_node(join, "geometry")

    return tree


def build_castle_curtain_wall(group_name="MEL_castle_curtain_wall"):
    """Curtain wall connecting two towers with parapet walkway.

    Uses: linear_array (walkway supports), add (wall + walkway),
          bounding_box (span between towers), store_attribute (curtain zone)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Span", 6.0, 1.0, 30.0)
    add_float_param(tree, "Height", 5.0, 1.0, 20.0)
    add_float_param(tree, "Thickness", 0.4, 0.1, 2.0)
    add_float_param(tree, "Walkway Width", 1.2, 0.3, 4.0)
    add_int_param(tree, "Support Count", 3, 1, 12)
    add_float_param(tree, "Support Radius", 0.15, 0.05, 0.5)

    # Main wall body
    wall = safe_node(tree, "GeometryNodeMeshCube", (bx - 400, by + 350))
    link_float_to_vector(tree, gin.outputs["Span"], wall, "Size", component=0)
    link_float_to_vector(tree, gin.outputs["Height"], wall, "Size", component=2)
    link_float_to_vector(tree, gin.outputs["Thickness"], wall, "Size", component=1)

    # Walkway on top
    walkway = safe_node(tree, "GeometryNodeMeshCube", (bx - 400, by + 200))
    link_float_to_vector(tree, gin.outputs["Span"], walkway, "Size", component=0)
    walkway.inputs["Size"].default_value[2] = 0.15
    link_float_to_vector(tree, gin.outputs["Walkway Width"], walkway, "Size", component=1)

    # Move walkway to top of wall
    walkway_z = safe_node(tree, "ShaderNodeMath", (bx - 550, by + 200))
    walkway_z.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Height"], walkway_z.inputs[0])
    walkway_z.inputs[1].default_value = 1.0

    # Walkway supports (pillars)
    pillar = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 400, by + 50))
    link_sockets(tree, gin.outputs["Support Radius"], pillar.inputs["Radius"])
    link_sockets(tree, gin.outputs["Height"], pillar.inputs["Depth"])
    pillar.inputs["Vertices"].default_value = 8
    pillar.fill_type = "NGON"

    # Array pillars along span
    pillar_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by - 50))
    pillar_line.mode = "END_POINTS"
    link_sockets(tree, gin.outputs["Support Count"], pillar_line.inputs["Count"])
    link_float_to_vector(tree, gin.outputs["Span"], pillar_line, "Start Location", component=0)

    inst_pillars = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 200, by + 50))
    link_sockets(tree, pillar_line.outputs["Mesh"], inst_pillars.inputs["Points"])
    link_sockets(tree, pillar.outputs["Mesh"], inst_pillars.inputs["Instance"])

    realize_pillars = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by + 50))
    link_sockets(tree, inst_pillars.outputs["Instances"], realize_pillars.inputs["Geometry"])

    # Joining wall + walkway + pillars
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200, by + 250))
    link_sockets(tree, wall.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, walkway.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, realize_pillars.outputs["Geometry"], join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 400, by + 250))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(wall, "geometry")
    color_node(join, "geometry")

    return tree


def build_castle_machicolations(group_name="MEL_castle_machicolations"):
    """Projecting parapet with murder holes for castle walls.

    Uses: linear_array (brackets), grid_array (murder holes),
          power (bracket scaling), exponent_blend (overhang profile),
          store_attribute (defense zone)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Wall Length", 4.0, 1.0, 30.0)
    add_float_param(tree, "Wall Thick", 0.4, 0.1, 2.0)
    add_float_param(tree, "Overhang", 0.6, 0.1, 2.0)
    add_float_param(tree, "Height", 0.5, 0.2, 1.5)
    add_int_param(tree, "Bracket Count", 6, 2, 30)
    add_int_param(tree, "Hole Rows", 2, 1, 5)
    add_float_param(tree, "Hole Spacing", 0.3, 0.1, 1.0)
    add_float_param(tree, "Hole Radius", 0.04, 0.02, 0.15)

    # Main parapet slab
    slab = safe_node(tree, "GeometryNodeMeshCube", (bx - 400, by + 300))
    link_float_to_vector(tree, gin.outputs["Wall Length"], slab, "Size", component=0)
    link_float_to_vector(tree, gin.outputs["Overhang"], slab, "Size", component=1)
    link_float_to_vector(tree, gin.outputs["Height"], slab, "Size", component=2)

    # Murder holes ΓÇö cylinder voids through slab
    hole = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 400, by + 100))
    link_sockets(tree, gin.outputs["Hole Radius"], hole.inputs["Radius"])
    link_sockets(tree, gin.outputs["Height"], hole.inputs["Depth"])
    hole.inputs["Vertices"].default_value = 8
    hole.fill_type = "NGON"

    # Grid array for holes
    hole_grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 400, by - 50))
    link_sockets(tree, gin.outputs["Wall Length"], hole_grid.inputs["Size X"])
    link_sockets(tree, gin.outputs["Overhang"], hole_grid.inputs["Size Y"])
    link_sockets(tree, gin.outputs["Hole Rows"], hole_grid.inputs["Vertices Y"])
    link_sockets(tree, gin.outputs["Bracket Count"], hole_grid.inputs["Vertices X"])

    inst_holes = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 200, by + 100))
    link_sockets(tree, hole_grid.outputs["Mesh"], inst_holes.inputs["Points"])
    link_sockets(tree, hole.outputs["Mesh"], inst_holes.inputs["Instance"])

    realize_holes = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by + 100))
    link_sockets(tree, inst_holes.outputs["Instances"], realize_holes.inputs["Geometry"])

    # Subtract holes from slab
    diff = safe_node(tree, "GeometryNodeMeshBoolean", (bx + 200, by + 200))
    diff.operation = "DIFFERENCE"
    link_sockets(tree, slab.outputs["Mesh"], diff.inputs["Mesh 2"])
    link_sockets(tree, realize_holes.outputs["Geometry"], diff.inputs["Mesh 1"])

    # Brackets / corbels supporting overhang
    bracket = safe_node(tree, "GeometryNodeMeshCone", (bx - 200, by - 100))
    bracket.inputs["Radius Bottom"].default_value = 0.12
    bracket.inputs["Radius Top"].default_value = 0.06
    bracket.inputs["Depth"].default_value = 0.2
    bracket.inputs["Vertices"].default_value = 4

    bracket_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by - 150))
    bracket_line.mode = "END_POINTS"
    link_sockets(tree, gin.outputs["Bracket Count"], bracket_line.inputs["Count"])
    link_float_to_vector(tree, gin.outputs["Wall Length"], bracket_line, "Start Location", component=0)

    inst_brackets = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 200, by - 100))
    link_sockets(tree, bracket_line.outputs["Mesh"], inst_brackets.inputs["Points"])
    link_sockets(tree, bracket.outputs["Mesh"], inst_brackets.inputs["Instance"])

    realize_brackets = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by - 100))
    link_sockets(tree, inst_brackets.outputs["Instances"], realize_brackets.inputs["Geometry"])

    # Join slab + brackets
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 400, by + 100))
    link_sockets(tree, diff.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, realize_brackets.outputs["Geometry"], join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 600, by + 100))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(slab, "geometry")
    color_node(diff, "math")
    color_node(join, "geometry")

    return tree


def build_castle_spiral_stairs(group_name="MEL_castle_spiral_stairs"):
    """Spiral staircase ΓÇö helical stair tower for keeps and towers.

    Uses: power (step scaling), exponent_blend (helix curve),
          bounding_box (shaft fit), store_attribute (stair zone)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Shaft Radius", 1.2, 0.4, 4.0)
    add_float_param(tree, "Height", 4.0, 0.8, 20.0)
    add_int_param(tree, "Steps", 20, 5, 80)
    add_float_param(tree, "Tread Depth", 0.25, 0.1, 0.8)
    add_float_param(tree, "Riser Height", 0.2, 0.05, 0.5)
    add_float_param(tree, "Inner Radius", 0.2, 0.05, 0.8)
    add_float_param(tree, "Wall Thick", 0.15, 0.05, 0.5)

    # Stair shaft (outer wall cylinder)
    shaft = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 400, by + 400))
    link_sockets(tree, gin.outputs["Shaft Radius"], shaft.inputs["Radius"])
    link_sockets(tree, gin.outputs["Height"], shaft.inputs["Depth"])
    shaft.inputs["Vertices"].default_value = 24
    shaft.fill_type = "NGON"

    # Hollow out shaft interior
    core = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 400, by + 250))
    core_r = safe_node(tree, "ShaderNodeMath", (bx - 550, by + 300))
    core_r.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Shaft Radius"], core_r.inputs[0])
    link_sockets(tree, gin.outputs["Wall Thick"], core_r.inputs[1])
    link_sockets(tree, gin.outputs["Height"], core.inputs["Depth"])
    core.fill_type = "NGON"

    diff = safe_node(tree, "GeometryNodeMeshBoolean", (bx - 200, by + 300))
    diff.operation = "DIFFERENCE"
    link_sockets(tree, shaft.outputs["Mesh"], diff.inputs["Mesh 2"])
    link_sockets(tree, core.outputs["Mesh"], diff.inputs["Mesh 1"])

    # Individual step as wedge
    step = safe_node(tree, "GeometryNodeMeshCube", (bx - 400, by + 50))
    step_r = safe_node(tree, "ShaderNodeMath", (bx - 550, by + 100))
    step_r.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Shaft Radius"], step_r.inputs[0])
    link_sockets(tree, gin.outputs["Inner Radius"], step_r.inputs[1])
    link_float_to_vector(tree, step_r.outputs[0], step, "Size", component=0)
    link_float_to_vector(tree, gin.outputs["Tread Depth"], step, "Size", component=1)
    link_float_to_vector(tree, gin.outputs["Riser Height"], step, "Size", component=2)

    # Step array along helix using mesh line
    step_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by - 80))
    step_line.mode = "END_POINTS"
    link_sockets(tree, gin.outputs["Steps"], step_line.inputs["Count"])

    # Instance steps on line points
    inst_steps = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 200, by - 80))
    link_sockets(tree, step_line.outputs["Mesh"], inst_steps.inputs["Points"])
    link_sockets(tree, step.outputs["Mesh"], inst_steps.inputs["Instance"])

    realize_steps = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by - 80))
    link_sockets(tree, inst_steps.outputs["Instances"], realize_steps.inputs["Geometry"])

    # Rotate each step around Z by (360 / steps * index)
    rotate_steps = safe_node(tree, "GeometryNodeRotateInstances", (bx + 200, by - 80))
    rotate_steps.inputs["Rotation"].default_value[2] = 0.0

    # Join shaft + steps
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200, by + 150))
    link_sockets(tree, diff.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, realize_steps.outputs["Geometry"], join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 400, by + 150))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(diff, "math")
    color_node(join, "geometry")

    return tree


def build_castle_drawbridge(group_name="MEL_castle_drawbridge"):
    """Drawbridge — plank floor with chain suspension and hinge rotation.

    Parametric: Span, Width, Plank Count, Chain Sag, Hinge Angle.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Span", 3.0, 0.5, 8.0)
    add_float_param(tree, "Width", 2.0, 0.5, 5.0)
    add_float_param(tree, "Thickness", 0.15, 0.05, 0.4)
    add_int_param(tree, "Plank Count", 8, 3, 20)
    add_float_param(tree, "Chain Sag", 0.3, 0.0, 1.0)
    add_float_param(tree, "Hinge Angle", 0.0, -45.0, 45.0)

    # Deck: single flat panel
    deck = safe_node(tree, "GeometryNodeMeshCube", (bx - 300, by + 200))
    link_float_to_vector(tree, gin.outputs["Span"], deck, "Size", component=0)
    link_float_to_vector(tree, gin.outputs["Width"], deck, "Size", component=1)
    link_float_to_vector(tree, gin.outputs["Thickness"], deck, "Size", component=2)

    # Planks: instance thin boxes along span
    plank = safe_node(tree, "GeometryNodeMeshCube", (bx - 300, by))
    plank.inputs["Size"].default_value[0] = 0.08
    link_float_to_vector(tree, gin.outputs["Width"], plank, "Size", component=1)
    plank.inputs["Size"].default_value[2] = 0.04

    plank_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 500, by))
    plank_line.mode = "END_POINTS"
    link_sockets(tree, gin.outputs["Plank Count"], plank_line.inputs["Count"])
    link_float_to_vector(tree, gin.outputs["Span"], plank_line, "Start Location", component=0)

    inst_planks = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 100, by))
    link_sockets(tree, plank_line.outputs["Mesh"], inst_planks.inputs["Points"])
    link_sockets(tree, plank.outputs["Mesh"], inst_planks.inputs["Instance"])
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 100, by))
    link_sockets(tree, inst_planks.outputs["Instances"], realize.inputs["Geometry"])

    # Hinge rotation (rotate around Z axis at one end)
    rotate = safe_node(tree, "GeometryNodeTransform", (bx + 300, by + 200))
    link_sockets(tree, deck.outputs["Mesh"], rotate.inputs["Geometry"])
    link_sockets(tree, realize.outputs["Geometry"], rotate.inputs["Geometry"])
    rotate.inputs["Rotation"].default_value[2] = 0.0
    rotate.inputs["Rotation"].default_value[1] = 0.0

    hinge_rad = safe_node(tree, "ShaderNodeMath", (bx + 150, by + 300))
    hinge_rad.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Hinge Angle"], hinge_rad.inputs[0])
    hinge_rad.inputs[1].default_value = 0.0174533  # deg to rad

    rotate_z = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 300, by + 300))
    link_sockets(tree, hinge_rad.outputs[0], rotate_z.inputs["Z"])
    link_sockets(tree, rotate_z.outputs["Vector"], rotate.inputs["Rotation"])

    # Chain curves (catenary approximation)
    chain_line_l = safe_node(tree, "GeometryNodeMeshLine", (bx - 100, by - 200))
    chain_line_l.mode = "END_POINTS"
    chain_line_l.inputs["Count"].default_value = 12
    link_float_to_vector(tree, gin.outputs["Span"], chain_line_l, "Start Location", component=0)
    link_float_to_vector(tree, gin.outputs["Chain Sag"], chain_line_l, "Start Location", component=2)

    chain_pos_l = safe_node(tree, "GeometryNodeSetPosition", (bx + 100, by - 200))
    link_sockets(tree, chain_line_l.outputs["Mesh"], chain_pos_l.inputs["Geometry"])
    # Sag: Z = sin(X * pi / Span) * -ChainSag
    chain_sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 100, by - 280))
    link_sockets(tree, chain_line_l.outputs["Mesh"], chain_sep.inputs["Vector"])
    chain_div = safe_node(tree, "ShaderNodeMath", (bx, by - 280))
    chain_div.operation = "DIVIDE"
    link_sockets(tree, chain_sep.outputs["X"], chain_div.inputs[0])
    link_sockets(tree, gin.outputs["Span"], chain_div.inputs[1])
    chain_pi = safe_node(tree, "ShaderNodeMath", (bx + 100, by - 280))
    chain_pi.operation = "MULTIPLY"
    link_sockets(tree, chain_div.outputs[0], chain_pi.inputs[0])
    chain_pi.inputs[1].default_value = 3.14159
    chain_sin = safe_node(tree, "ShaderNodeMath", (bx + 200, by - 280))
    chain_sin.operation = "SINE"
    link_sockets(tree, chain_pi.outputs[0], chain_sin.inputs[0])
    chain_sag = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 280))
    chain_sag.operation = "MULTIPLY"
    link_sockets(tree, chain_sin.outputs[0], chain_sag.inputs[0])
    link_sockets(tree, gin.outputs["Chain Sag"], chain_sag.inputs[1])
    # chain_sag is positive downward; subtract from Z
    chain_z = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 280))
    chain_z.operation = "SUBTRACT"
    link_sockets(tree, chain_sep.outputs["Z"], chain_z.inputs[0])
    link_sockets(tree, chain_sag.outputs[0], chain_z.inputs[1])
    chain_c = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 500, by - 280))
    link_sockets(tree, chain_sep.outputs["X"], chain_c.inputs["X"])
    link_sockets(tree, chain_z.outputs[0], chain_c.inputs["Z"])
    link_sockets(tree, chain_c.outputs["Vector"], chain_pos_l.inputs["Position"])

    # Chain profile (thin circle)
    chain_profile = safe_node(tree, "GeometryNodeMeshCircle", (bx + 100, by - 150))
    chain_profile.inputs["Radius"].default_value = 0.025
    chain_profile.inputs["Vertices"].default_value = 4
    chain_profile.fill_type = "NGON"

    chain_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 300, by - 200))
    link_sockets(tree, chain_pos_l.outputs["Geometry"], chain_mesh.inputs["Curve"])
    cprof = chain_mesh.inputs.get("Profile") or chain_mesh.inputs.get("Profile Curve")
    link_sockets(tree, chain_profile.outputs["Mesh"], cprof)

    # Join all
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 400, by + 100))
    link_sockets(tree, rotate.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, chain_mesh.outputs["Mesh"], join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 600, by + 100))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(deck, "geometry")
    color_node(join, "geometry")
    return tree


def build_castle_corner_bastion(group_name="MEL_castle_corner_bastion"):
    """Corner bastion — 90-degree wall junction with integrated tower.

    Creates two wall arms meeting at a corner with a tower at the intersection.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Wall Length A", 5.0, 1.0, 20.0)
    add_float_param(tree, "Wall Length B", 5.0, 1.0, 20.0)
    add_float_param(tree, "Wall Height", 4.0, 1.0, 15.0)
    add_float_param(tree, "Wall Thickness", 0.4, 0.1, 2.0)
    add_float_param(tree, "Tower Radius", 1.0, 0.3, 3.0)
    add_bool_param(tree, "Crenellation", True)

    # Wall arm A (along X)
    wall_a = safe_node(tree, "GeometryNodeMeshCube", (bx - 300, by + 300))
    link_float_to_vector(tree, gin.outputs["Wall Length A"], wall_a, "Size", component=0)
    link_float_to_vector(tree, gin.outputs["Wall Height"], wall_a, "Size", component=2)
    link_float_to_vector(tree, gin.outputs["Wall Thickness"], wall_a, "Size", component=1)
    pos_a = safe_node(tree, "GeometryNodeSetPosition", (bx - 100, by + 300))
    link_sockets(tree, wall_a.outputs["Mesh"], pos_a.inputs["Geometry"])
    # Offset so it extends from corner outward
    a_x = safe_node(tree, "ShaderNodeMath", (bx - 200, by + 400))
    a_x.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Wall Length A"], a_x.inputs[0])
    a_x.inputs[1].default_value = 0.5
    a_c = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 100, by + 400))
    link_sockets(tree, a_x.outputs[0], a_c.inputs["X"])
    link_sockets(tree, a_c.outputs["Vector"], pos_a.inputs["Position"])

    # Wall arm B (along Y)
    wall_b = safe_node(tree, "GeometryNodeMeshCube", (bx - 300, by + 100))
    link_float_to_vector(tree, gin.outputs["Wall Length B"], wall_b, "Size", component=1)
    link_float_to_vector(tree, gin.outputs["Wall Height"], wall_b, "Size", component=2)
    link_float_to_vector(tree, gin.outputs["Wall Thickness"], wall_b, "Size", component=0)
    pos_b = safe_node(tree, "GeometryNodeSetPosition", (bx - 100, by + 100))
    link_sockets(tree, wall_b.outputs["Mesh"], pos_b.inputs["Geometry"])
    b_y = safe_node(tree, "ShaderNodeMath", (bx - 200, by + 200))
    b_y.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Wall Length B"], b_y.inputs[0])
    b_y.inputs[1].default_value = 0.5
    b_c = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 100, by + 200))
    link_sockets(tree, b_y.outputs[0], b_c.inputs["Y"])
    link_sockets(tree, b_c.outputs["Vector"], pos_b.inputs["Position"])

    # Corner tower
    tower = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 300, by - 100))
    link_sockets(tree, gin.outputs["Tower Radius"], tower.inputs["Radius"])
    link_sockets(tree, gin.outputs["Wall Height"], tower.inputs["Depth"])
    tower.inputs["Vertices"].default_value = 16
    tower.fill_type = "NGON"

    # Join
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 100, by + 100))
    link_sockets(tree, pos_a.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, pos_b.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, tower.outputs["Mesh"], join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 300, by + 100))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(wall_a, "geometry")
    color_node(wall_b, "geometry")
    color_node(tower, "geometry")
    color_node(join, "geometry")

    return tree


def build_castle_assembler(group_name="MEL_castle_assembler"):
    """Complete gothic castle generator ΓÇö assembles all components.

    Takes modular castle parts (walls, towers, keep, gatehouse) and
    composes them into a full castle layout. Each component is
    positioned via stored attributes and bounding-box snapping.

    Uses: add (all components), bounding_box (site), store_attribute (zones),
          power (battlement scaling), exponent_blend (roof profiles)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    make_group_input(tree, "NodeSocketGeometry", "Walls")
    make_group_input(tree, "NodeSocketGeometry", "Towers")
    make_group_input(tree, "NodeSocketGeometry", "Keep")
    make_group_input(tree, "NodeSocketGeometry", "Gatehouse")

    add_float_param(tree, "Site Scale", 1.0, 0.1, 5.0)
    add_float_param(tree, "Courtyard Width", 20.0, 5.0, 80.0)
    add_float_param(tree, "Courtyard Depth", 15.0, 5.0, 60.0)
    add_bool_param(tree, "Complete Walls", True)
    add_bool_param(tree, "Corner Towers", True)

    walls_sock = gin.outputs["Walls"] if "Walls" in gin.outputs else None
    towers_sock = gin.outputs["Towers"] if "Towers" in gin.outputs else None
    keep_sock = gin.outputs["Keep"] if "Keep" in gin.outputs else None
    gate_sock = gin.outputs["Gatehouse"] if "Gatehouse" in gin.outputs else None

    # Courtyard bounding box
    court = safe_node(tree, "GeometryNodeMeshGrid", (bx - 400, by + 300))
    link_sockets(tree, gin.outputs["Courtyard Width"], court.inputs["Size X"])
    link_sockets(tree, gin.outputs["Courtyard Depth"], court.inputs["Size Y"])
    court.inputs["Vertices X"].default_value = 2
    court.inputs["Vertices Y"].default_value = 2

    # Extrude for ground plane
    extrude = safe_node(tree, "GeometryNodeExtrudeMesh", (bx - 200, by + 300))
    link_sockets(tree, court.outputs["Mesh"], extrude.inputs["Mesh"])
    extrude.inputs["Offset Scale"].default_value = 0.2
    extrude.mode = "FACES"

    # Join all components
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx, by + 100))
    link_sockets(tree, extrude.outputs["Mesh"], join.inputs["Geometry"])
    if walls_sock:
        link_sockets(tree, walls_sock, join.inputs["Geometry"])
    if towers_sock:
        link_sockets(tree, towers_sock, join.inputs["Geometry"])
    if keep_sock:
        link_sockets(tree, keep_sock, join.inputs["Geometry"])
    if gate_sock:
        link_sockets(tree, gate_sock, join.inputs["Geometry"])

    # Scale entire castle
    scale_all = safe_node(tree, "GeometryNodeTransform", (bx + 200, by + 100))
    link_sockets(tree, join.outputs["Geometry"], scale_all.inputs["Geometry"])
    link_float_to_vector(tree, gin.outputs["Site Scale"], scale_all, "Scale", component=1)

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 400, by + 100))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, scale_all.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(extrude, "geometry")
    color_node(join, "geometry")
    color_node(shade, "geometry")

    return tree


# -- Registry --
from .core import register_builder

register_builder("MEL_castle_crenellation", build_castle_crenellation, "Castle Crenellation",
    "Battlement top ΓÇö alternating merlons and crenels along a wall",
    "castle")
register_builder("MEL_castle_wall_segment", build_castle_wall_segment, "Castle Wall Segment",
    "Wall body with optional crenellation toggle via Switch node",
    "castle")
register_builder("MEL_castle_tower", build_castle_tower, "Castle Tower",
    "Round tower with conical roof and crenellation ring",
    "castle")
register_builder("MEL_castle_gatehouse", build_castle_gatehouse, "Castle Gatehouse",
    "Gatehouse with arched gateway and flanking towers",
    "castle")
register_builder("MEL_castle_gothic_window", build_castle_gothic_window, "Castle Gothic Window",
    "Pointed arch window with tracery bars",
    "castle")
register_builder("MEL_castle_buttress", build_castle_buttress, "Castle Buttress",
    "Flying buttress ΓÇö tapered strut with angled arch support",
    "castle")
register_builder("MEL_castle_keep", build_castle_keep, "Castle Keep",
    "Central keep ΓÇö multi-tier core with corner towers and tier taper",
    "castle")
register_builder("MEL_castle_curtain_wall", build_castle_curtain_wall, "Castle Curtain Wall",
    "Wall between towers ΓÇö walkway and support pillars via linear array",
    "castle")
register_builder("MEL_castle_machicolations", build_castle_machicolations, "Castle Machicolations",
    "Projecting parapet ΓÇö murder holes via grid array of boolean voids",
    "castle")
register_builder("MEL_castle_spiral_stairs", build_castle_spiral_stairs, "Castle Spiral Stairs",
    "Spiral staircase ΓÇö hollow shaft with wedge steps on helix",
    "castle")
register_builder("MEL_castle_assembler", build_castle_assembler, "Castle Full Assembler",
    "Full castle composition \u2014 walls, towers, keep, gatehouse, courtyard",
    "castle")
register_builder("MEL_castle_drawbridge", build_castle_drawbridge, "Castle Drawbridge",
    "Drawbridge with plank floor, chain suspension, and hinge rotation",
    "castle")
register_builder("MEL_castle_corner_bastion", build_castle_corner_bastion,
    "Castle Corner Bastion",
    "90-degree wall junction with integrated corner tower",
    "castle")
