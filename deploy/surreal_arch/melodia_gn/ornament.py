"""Ornamental GN group builders — vine, radial, grid, frame, panel with power/add/subtract/bbox/attr operations."""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, add_vector_param,
    make_group_input, mesh_line_to_curve, sweep_profile,
)


def _ensure_group_node(tree, group_name, builder, loc):
    if group_name not in bpy.data.node_groups:
        builder(group_name)
    node = safe_node(tree, "GeometryNodeGroup", loc)
    if node:
        node.node_tree = bpy.data.node_groups.get(group_name)
    return node


def build_ornament_vine(group_name="MEL_ornament_vine"):
    """Art Nouveau vine — sinusoidal S-curve sweep with power-tapered thickness.

    Uses: power (taper), store_attribute (thickness along vine), bounding_box (auto-fit)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Panel Width", 1.6, 0.2, 5.0)
    add_float_param(tree, "Panel Height", 2.0, 0.2, 5.0)
    add_float_param(tree, "Branch Count", 3.0, 1.0, 8.0)
    add_float_param(tree, "Density", 0.5, 0.1, 1.0)
    add_float_param(tree, "Taper Power", 0.7, 0.1, 2.0)
    add_float_param(tree, "Thickness", 0.02, 0.005, 0.1)
    add_float_param(tree, "Wave Amp", 0.15, 0.0, 0.5)
    add_float_param(tree, "Wave Freq", 2.0, 0.5, 5.0)
    add_int_param(tree, "Segments", 48, 8, 128)

    # Base curve: Mesh Line along X
    base_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 600, by + 400))
    base_line.mode = "END_POINTS"
    link_sockets(tree, gin.outputs["Segments"], base_line.inputs["Count"])
    link_float_to_vector(tree, gin.outputs["Panel Width"], base_line, "Start Location", component=0)

    # Set Position: Z = sin(x * freq) * amp, with taper
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 600, by + 100))
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 600, by))

    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 400, by + 100))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    # Taper: pow((idx / count), taper_power) for thickness scaling
    count = safe_node(tree, "ShaderNodeMath", (bx - 400, by))
    count.operation = "ADD"
    count.inputs[0].default_value = 1.0
    link_sockets(tree, gin.outputs["Segments"], count.inputs[1])

    norm = safe_node(tree, "ShaderNodeMath", (bx - 200, by))
    norm.operation = "DIVIDE"
    link_sockets(tree, idx.outputs["Index"], norm.inputs[0])
    link_sockets(tree, count.outputs[0], norm.inputs[1])

    taper = safe_node(tree, "ShaderNodeMath", (bx, by))
    taper.operation = "POWER"
    link_sockets(tree, norm.outputs[0], taper.inputs[0])
    link_sockets(tree, gin.outputs["Taper Power"], taper.inputs[1])

    # Sine wave Z displacement
    wave = safe_node(tree, "ShaderNodeMath", (bx - 200, by + 200))
    wave.operation = "MULTIPLY"
    link_sockets(tree, sep.outputs["X"], wave.inputs[0])
    link_sockets(tree, gin.outputs["Wave Freq"], wave.inputs[1])

    sin_wave = safe_node(tree, "ShaderNodeMath", (bx, by + 200))
    sin_wave.operation = "SINE"
    link_sockets(tree, wave.outputs[0], sin_wave.inputs[0])

    wave_z = safe_node(tree, "ShaderNodeMath", (bx + 200, by + 200))
    wave_z.operation = "MULTIPLY"
    link_sockets(tree, sin_wave.outputs[0], wave_z.inputs[0])
    link_sockets(tree, gin.outputs["Wave Amp"], wave_z.inputs[1])

    # Set position: Y = wave_z for horizontal vine
    combine = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 400, by + 200))
    link_sockets(tree, sep.outputs["X"], combine.inputs["X"])
    link_sockets(tree, wave_z.outputs[0], combine.inputs["Y"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 400, by + 50))
    link_sockets(tree, base_line.outputs["Mesh"], set_pos.inputs["Geometry"])
    link_sockets(tree, combine.outputs["Vector"], set_pos.inputs["Position"])

    vine_curve = mesh_line_to_curve(tree, (bx + 600, by + 50), set_pos.outputs["Geometry"])
    rad_mul = safe_node(tree, "ShaderNodeMath", (bx + 600, by - 80))
    rad_mul.operation = "MULTIPLY"
    link_sockets(tree, taper.outputs[0], rad_mul.inputs[0])
    link_sockets(tree, gin.outputs["Thickness"], rad_mul.inputs[1])
    set_rad = safe_node(tree, "GeometryNodeSetCurveRadius", (bx + 800, by + 50))
    if set_rad is None:
        set_rad = safe_node(tree, "GeometryNodeSetRadius", (bx + 800, by + 50))
    if set_rad is not None:
        rad_geo_in = set_rad.inputs.get("Curve") or set_rad.inputs.get("Geometry")
        if rad_geo_in is not None:
            link_sockets(tree, vine_curve, rad_geo_in)
        rad_in = set_rad.inputs.get("Radius")
        if rad_in is not None:
            link_sockets(tree, rad_mul.outputs[0], rad_in)
        vine_curve = set_rad.outputs.get("Curve") or set_rad.outputs.get("Geometry") or vine_curve

    swept = sweep_profile(tree, (bx + 1100, by + 50), vine_curve, gin.outputs["Thickness"],
                          profile_res=10, already_curve=True)

    store_thick = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 1300, by))
    link_sockets(tree, swept, store_thick.inputs["Geometry"])
    link_sockets(tree, taper.outputs[0], store_thick.inputs["Value"])
    store_thick.data_type = "FLOAT"
    try:
        store_thick.inputs["Name"].default_value = "vine_thickness"
    except Exception:
        pass

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 1500, by + 100))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, store_thick.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(base_line, "curve")
    color_node(set_pos, "attribute")
    color_node(store_thick, "attribute")
    color_node(set_rad, "attribute")
    color_node(shade, "geometry")

    return label_tree(tree, "MEL_ornament_vine", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Vine Curve", "nodes": ("line", "wave", "position"), "role": "curve"},
        {"title": "Thickness", "nodes": ("taper", "thick", "radius"), "role": "attribute"},
        {"title": "Mesh Output", "nodes": ("curve to mesh", "shade", "Group Output"), "role": "output"},
    ])


def build_ornament_radial(group_name="MEL_ornament_radial"):
    """Gothic radial — circular array of spokes + concentric rings, with subtract for voids.

    Uses: circular_array (spokes), add (rings), subtract (voids), bounding_box (center/radius)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Radius", 0.8, 0.1, 3.0)
    add_int_param(tree, "Spoke Count", 8, 3, 32)
    add_int_param(tree, "Ring Count", 3, 1, 8)
    add_float_param(tree, "Profile Radius", 0.015, 0.005, 0.08)
    add_float_param(tree, "Center Void", 0.0, 0.0, 0.5)

    # Spokes: linear array rotated by circular_array
    spoke_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by + 400))
    spoke_line.mode = "END_POINTS"
    spoke_line.inputs["Count"].default_value = 2
    link_float_to_vector(tree, gin.outputs["Radius"], spoke_line, "Start Location", component=0)

    spoke_mesh_sock = sweep_profile(
        tree, (bx, by + 400), spoke_line.outputs["Mesh"], gin.outputs["Profile Radius"],
        profile_res=8, already_curve=False)

    # Circular array of spokes -- use the shared Melodia primitive before export realization.
    try:
        from .primitives import build_circular_array
        spoke_radial = _ensure_group_node(tree, "MEL_circular_array", build_circular_array, (bx + 200, by + 400))
    except Exception:
        spoke_radial = None
    radial_spokes = None
    if spoke_radial and spoke_radial.node_tree:
        if spoke_radial.inputs.get("Geometry"):
            link_sockets(tree, spoke_mesh_sock, spoke_radial.inputs["Geometry"])
        if spoke_radial.inputs.get("Count"):
            link_sockets(tree, gin.outputs["Spoke Count"], spoke_radial.inputs["Count"])
        if spoke_radial.inputs.get("Radius"):
            link_sockets(tree, gin.outputs["Radius"], spoke_radial.inputs["Radius"])
        radial_spokes = spoke_radial.outputs.get("Geometry")

    # Fallback instance-on-circle points for Blender builds missing the helper.
    circle_pts = safe_node(tree, "GeometryNodeMeshCircle", (bx - 200, by + 200))
    link_sockets(tree, gin.outputs["Radius"], circle_pts.inputs["Radius"])
    link_sockets(tree, gin.outputs["Spoke Count"], circle_pts.inputs["Vertices"])
    circle_pts.fill_type = "NONE"

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx, by + 200))
    link_sockets(tree, circle_pts.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, spoke_mesh_sock, inst.inputs["Instance"])

    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 200, by + 200))
    link_sockets(tree, inst.outputs["Instances"], realize.inputs["Geometry"])

    # Rings: concentric circles
    ring_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by))
    ring_line.mode = "END_POINTS"
    ring_line.inputs["Count"].default_value = 2
    link_sockets(tree, gin.outputs["Ring Count"], ring_line.inputs["Count"])
    link_float_to_vector(tree, gin.outputs["Radius"], ring_line, "Start Location", component=0)

    ring_path = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 200, by - 100))
    link_sockets(tree, gin.outputs["Radius"], ring_path.inputs["Radius"])
    ring_path.inputs["Resolution"].default_value = 32
    ring_mesh_sock = sweep_profile(
        tree, (bx, by - 100), ring_path.outputs.get("Curve") or ring_path.outputs[0],
        gin.outputs["Profile Radius"], profile_res=8, already_curve=True)

    ring_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 80, by - 100))
    link_sockets(tree, ring_line.outputs["Mesh"], ring_inst.inputs["Points"])
    link_sockets(tree, ring_mesh_sock, ring_inst.inputs["Instance"])

    realize_rings = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 200, by - 100))
    link_sockets(tree, ring_inst.outputs["Instances"], realize_rings.inputs["Geometry"])

    # Add spokes + rings
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 400, by + 100))
    link_sockets(tree, radial_spokes or realize.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, realize_rings.outputs["Geometry"], join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 600, by + 100))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(circle_pts, "curve")
    color_node(spoke_radial, "instance")
    color_node(inst, "instance")
    color_node(realize, "instance")
    color_node(join, "geometry")
    color_node(shade, "geometry")

    return label_tree(tree, "MEL_ornament_radial", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Gothic Spokes", "nodes": ("spoke", "circular"), "role": "instance"},
        {"title": "Rings", "nodes": ("ring",), "role": "curve"},
        {"title": "Center Void", "nodes": ("void", "boolean"), "role": "geometry"},
        {"title": "Output", "nodes": ("join", "shade", "Group Output"), "role": "output"},
    ])


def build_ornament_grid(group_name="MEL_ornament_grid"):
    """Geometric grid — cells arranged in rows/cols with power-scale falloff and subtract voids.

    Uses: grid_array (cells), add (merge), subtract (checkerboard), power (edge falloff)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Panel Width", 1.6, 0.2, 5.0)
    add_float_param(tree, "Panel Height", 2.0, 0.2, 5.0)
    add_int_param(tree, "Cols", 6, 2, 20)
    add_int_param(tree, "Rows", 8, 2, 20)
    add_float_param(tree, "Cell Radius", 0.04, 0.01, 0.2)
    add_float_param(tree, "Edge Falloff", 0.5, 0.0, 2.0)
    add_bool_param(tree, "Checkerboard", True)

    # Grid of points
    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 300, by + 300))
    link_sockets(tree, gin.outputs["Cols"], grid.inputs["Vertices X"])
    link_sockets(tree, gin.outputs["Rows"], grid.inputs["Vertices Y"])
    link_sockets(tree, gin.outputs["Panel Width"], grid.inputs["Size X"])
    link_sockets(tree, gin.outputs["Panel Height"], grid.inputs["Size Y"])

    # Instance circle at each grid point
    cell = safe_node(tree, "GeometryNodeMeshCircle", (bx - 100, by + 300))
    link_sockets(tree, gin.outputs["Cell Radius"], cell.inputs["Radius"])
    cell.inputs["Vertices"].default_value = 8
    cell.fill_type = "NGON"

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 100, by + 300))
    link_sockets(tree, grid.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, cell.outputs["Mesh"], inst.inputs["Instance"])

    # Power falloff toward edges
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx, by + 100))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx + 150, by + 100))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    # Normalize X distance from center
    abs_x = safe_node(tree, "ShaderNodeMath", (bx + 300, by + 100))
    abs_x.operation = "ABSOLUTE"
    link_sockets(tree, sep.outputs["X"], abs_x.inputs[0])

    norm_x = safe_node(tree, "ShaderNodeMath", (bx + 450, by + 100))
    norm_x.operation = "DIVIDE"
    link_sockets(tree, abs_x.outputs[0], norm_x.inputs[0])
    link_sockets(tree, gin.outputs["Panel Width"], norm_x.inputs[1])

    power_n = safe_node(tree, "ShaderNodeMath", (bx + 600, by + 100))
    power_n.operation = "POWER"
    link_sockets(tree, norm_x.outputs[0], power_n.inputs[0])
    link_sockets(tree, gin.outputs["Edge Falloff"], power_n.inputs[1])

    # Scale instances by power falloff
    scale = safe_node(tree, "GeometryNodeScaleInstances", (bx + 300, by + 300))
    link_sockets(tree, inst.outputs["Instances"], scale.inputs["Instances"])
    link_float_to_vector(tree, power_n.outputs[0], scale, "Scale", component=1, defaults=(1.0, 0.0, 1.0))

    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 600, by + 250))
    link_sockets(tree, scale.outputs["Instances"], realize.inputs["Geometry"])

    # Checkerboard subtraction
    if gin.outputs["Checkerboard"]:
        idx = safe_node(tree, "GeometryNodeInputIndex", (bx + 300, by - 100))
        checker = safe_node(tree, "ShaderNodeMath", (bx + 450, by - 100))
        checker.operation = "MODULO"
        link_sockets(tree, idx.outputs["Index"], checker.inputs[0])
        checker.inputs[1].default_value = 2

        # Selection: keep only even indices — currently unused pending selector implementation

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 800, by + 200))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, realize.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(grid, "geometry")
    color_node(inst, "instance")
    color_node(realize, "instance")
    color_node(shade, "geometry")

    return label_tree(tree, "MEL_ornament_grid", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Grid Cells", "nodes": ("grid", "cell", "instance"), "role": "instance"},
        {"title": "Falloff", "nodes": ("power", "scale"), "role": "math"},
        {"title": "Output", "nodes": ("shade", "Group Output"), "role": "output"},
    ])


def build_ornament_frame(group_name="MEL_ornament_frame"):
    """Rectangular frame — extruded edges from bounding box, with corner taper.

    Uses: bounding_box (dimensions), power (corner taper)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Frame Width", 0.05, 0.01, 0.2)
    add_float_param(tree, "Corner Taper", 1.0, 0.0, 2.0)
    add_float_param(tree, "Smooth", True)

    # Bounding box
    bbox = safe_node(tree, "GeometryNodeBoundBox", (bx - 200, by + 200))
    link_sockets(tree, gin.outputs["Geometry"], bbox.inputs["Geometry"])

    # Extrude edges
    extrude = safe_node(tree, "GeometryNodeExtrudeMesh", (bx, by + 200))
    bbox_out = bbox.outputs.get("Bounding Box") or bbox.outputs.get("Mesh")
    link_sockets(tree, bbox_out, extrude.inputs["Mesh"])
    link_sockets(tree, gin.outputs["Frame Width"], extrude.inputs["Offset Scale"])
    extrude.mode = "EDGES"

    # Corner taper via power scale on vertices
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 200, by + 200))
    link_sockets(tree, extrude.outputs["Mesh"], set_pos.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 400, by + 200))
    link_sockets(tree, set_pos.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, gin.outputs["Smooth"], shade.inputs["Shade Smooth"])

    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(bbox, "attribute")
    color_node(extrude, "geometry")
    color_node(shade, "geometry")

    return label_tree(tree, "MEL_ornament_frame", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bounds", "nodes": ("bbox", "bound"), "role": "attribute"},
        {"title": "Frame Mesh", "nodes": ("extrude", "position"), "role": "geometry"},
        {"title": "Output", "nodes": ("shade", "Group Output"), "role": "output"},
    ])


def build_ornament_panel(group_name="MEL_ornament_panel"):
    """Composite ornamental panel — selects vine/radial/grid, adds frame, stores material zone attr.

    Uses: add (combine frame + interior), store_attribute (material zone), switch (style selector)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    make_group_input(tree, "NodeSocketGeometry", "Interior Ornament")

    add_float_param(tree, "Panel Width", 1.6, 0.2, 5.0)
    add_float_param(tree, "Panel Height", 2.0, 0.2, 5.0)
    add_float_param(tree, "Frame Width", 0.04, 0.01, 0.15)
    add_int_param(tree, "Style", 1, 0, 3)
    add_bool_param(tree, "Show Frame", True)

    # Frame from bounding box
    bbox = safe_node(tree, "GeometryNodeBoundBox", (bx - 400, by + 300))
    link_sockets(tree, gin.outputs["Geometry"], bbox.inputs["Geometry"])

    extrude = safe_node(tree, "GeometryNodeExtrudeMesh", (bx - 200, by + 300))
    bbox_out = bbox.outputs.get("Bounding Box") or bbox.outputs.get("Mesh")
    link_sockets(tree, bbox_out, extrude.inputs["Mesh"])
    link_sockets(tree, gin.outputs["Frame Width"], extrude.inputs["Offset Scale"])
    extrude.mode = "EDGES"

    # Switch frame on/off
    frame_switch = safe_node(tree, "GeometryNodeSwitch", (bx, by + 300))
    try:
        frame_switch.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Show Frame"], frame_switch.inputs["Switch"])
    fs_true = frame_switch.inputs.get("True") or frame_switch.inputs.get("TRUE")
    link_sockets(tree, extrude.outputs["Mesh"], fs_true)

    try:
        radial_grp = _ensure_group_node(tree, "MEL_ornament_radial", build_ornament_radial, (bx - 200, by - 80))
    except Exception:
        radial_grp = None
    style_compare = safe_node(tree, "FunctionNodeCompare", (bx, by - 80))
    style_out = None
    if style_compare is not None:
        try:
            style_compare.data_type = "INT"
            style_compare.operation = "GREATER_THAN"
        except Exception:
            pass
        if style_compare.inputs.get("A"):
            link_sockets(tree, gin.outputs["Style"], style_compare.inputs["A"])
        if style_compare.inputs.get("B"):
            style_compare.inputs["B"].default_value = 0
        style_out = style_compare.outputs.get("Result")
    ornament_switch = safe_node(tree, "GeometryNodeSwitch", (bx + 120, by - 80))
    try:
        ornament_switch.input_type = "GEOMETRY"
    except Exception:
        pass
    if style_out is not None:
        link_sockets(tree, style_out, ornament_switch.inputs["Switch"])
    if "Interior Ornament" in gin.outputs:
        link_sockets(tree, gin.outputs["Interior Ornament"], ornament_switch.inputs.get("False") or ornament_switch.inputs.get("FALSE"))
    if radial_grp and radial_grp.node_tree:
        radial_geo = radial_grp.outputs.get("Geometry")
        if radial_geo:
            link_sockets(tree, radial_geo, ornament_switch.inputs.get("True") or ornament_switch.inputs.get("TRUE"))

    # Join frame with interior ornament
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200, by + 200))
    link_sockets(tree, (ornament_switch.outputs.get("Output") if ornament_switch else None), join.inputs["Geometry"])
    link_sockets(tree, frame_switch.outputs["Output"], join.inputs["Geometry"])

    # Store material zone attribute
    store_zone = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 400, by + 100))
    link_sockets(tree, join.outputs["Geometry"], store_zone.inputs["Geometry"])
    try:
        store_zone.inputs["Name"].default_value = "material_zone"
    except Exception:
        pass

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 600, by + 100))
    link_sockets(tree, store_zone.outputs["Geometry"], shade.inputs["Geometry"])
    shade.inputs["Shade Smooth"].default_value = True

    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(bbox, "attribute")
    color_node(extrude, "geometry")
    color_node(radial_grp, "instance")
    color_node(style_compare, "math")
    color_node(ornament_switch, "instance")
    color_node(join, "geometry")
    color_node(shade, "geometry")

    return label_tree(tree, "MEL_ornament_panel", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Panel Style", "nodes": ("style", "radial", "switch"), "role": "instance"},
        {"title": "Frame", "nodes": ("bbox", "extrude", "frame"), "role": "geometry"},
        {"title": "Material And Output", "nodes": ("store", "shade", "Group Output"), "role": "output"},
    ])


# -- Registry --
from .core import register_builder

register_builder("MEL_ornament_vine", build_ornament_vine, "Ornament Vine (Art Nouveau)",
    "Art Nouveau vine - sinusoidal S-curve sweep with power-tapered thickness",
    "ornament")
register_builder("MEL_ornament_radial", build_ornament_radial, "Ornament Radial (Gothic)",
    "Gothic radial - circular spoke array with concentric rings",
    "ornament")
register_builder("MEL_ornament_grid", build_ornament_grid, "Ornament Grid (Arabesque)",
    "Arabesque geometric grid - cells with edge power falloff",
    "ornament")
register_builder("MEL_ornament_frame", build_ornament_frame, "Ornament Frame",
    "Rectangular picture frame - bounding-box edges with corner taper",
    "ornament")
register_builder("MEL_ornament_panel", build_ornament_panel, "Ornament Panel (Composite)",
    "Composite panel - interior ornament + frame, material zone attribute",
    "ornament")
