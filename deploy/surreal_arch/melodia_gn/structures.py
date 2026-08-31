"""Structure GN group builders — gazebo, column, arch, roof assemblies.

Composes primitives and profiles into reusable architectural structures.
"""

from __future__ import annotations

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param,
    make_group_input, add_music_influence_params, apply_universal_music_pass,
)


def build_gazebo(group_name="MEL_gazebo"):
    """Composable gazebo: circular array of columns + beam ring + roof + star finial.

    Inputs:
      Column Profile — geometry input to instance as columns
      Roof Profile — geometry input for roof panels
      Radius, Column Count, Roof Pitch, Height
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    make_group_input(tree, "NodeSocketGeometry", "Column Profile")
    make_group_input(tree, "NodeSocketGeometry", "Roof Profile")

    add_float_param(tree, "Radius", 1.5, 0.2, 20.0)
    add_int_param(tree, "Column Count", 8, 3, 64)
    add_float_param(tree, "Column Height", 2.4, 0.2, 20.0)
    add_float_param(tree, "Roof Pitch", 0.8, 0.1, 3.0)
    add_float_param(tree, "Beam Radius", 0.04, 0.01, 0.2)
    add_bool_param(tree, "Has Finial", True)
    add_bool_param(tree, "Has Engawa", True)
    add_float_param(tree, "Engawa Depth", 0.45, 0.0, 2.0)
    add_bool_param(tree, "Has Irimoya", False)
    add_bool_param(tree, "Use Default Column", True)
    add_music_influence_params(tree)

    col_profile = gin.outputs["Column Profile"] if "Column Profile" in gin.outputs else None
    roof_profile = gin.outputs["Roof Profile"] if "Roof Profile" in gin.outputs else None

    # ── Circular array of columns ──
    circle_col = safe_node(tree, "GeometryNodeMeshCircle", (bx - 200, by + 600))
    link_sockets(tree, gin.outputs["Radius"], circle_col.inputs["Radius"])
    link_sockets(tree, gin.outputs["Column Count"], circle_col.inputs["Vertices"])
    circle_col.fill_type = "NONE"

    # Default cylinder when Column Profile is empty (RQ seed)
    def_col = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 400, by + 720))
    def_col.inputs["Vertices"].default_value = 12
    def_col.inputs["Radius"].default_value = 0.08
    def_col.inputs["Depth"].default_value = 1.0
    col_sw = safe_node(tree, "GeometryNodeSwitch", (bx - 200, by + 720))
    try:
        col_sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Use Default Column"], col_sw.inputs["Switch"])
    true_in = col_sw.inputs.get("True") or col_sw.inputs.get("TRUE")
    false_in = col_sw.inputs.get("False") or col_sw.inputs.get("FALSE")
    link_sockets(tree, def_col.outputs["Mesh"], true_in)
    if col_profile:
        link_sockets(tree, col_profile, false_in)
    col_instance = col_sw.outputs.get("Output") or col_sw.outputs.get("Geometry")

    # Instance column profile on circle points
    inst_col = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx, by + 600))
    link_sockets(tree, circle_col.outputs["Mesh"], inst_col.inputs["Points"])
    link_sockets(tree, col_instance, inst_col.inputs["Instance"])

    # Scale column instances by height
    scale_col = safe_node(tree, "GeometryNodeScaleInstances", (bx + 200, by + 600))
    link_sockets(tree, inst_col.outputs["Instances"], scale_col.inputs["Instances"])
    link_float_to_vector(tree, gin.outputs["Column Height"], scale_col, "Scale", component=2, defaults=(1.0, 1.0, 0.0))

    # Realize
    realize_col = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 400, by + 600))
    link_sockets(tree, scale_col.outputs["Instances"], realize_col.inputs["Geometry"])

    # ── Beam ring on top of columns ──
    circle_beam = safe_node(tree, "GeometryNodeMeshCircle", (bx - 200, by + 300))
    link_sockets(tree, gin.outputs["Radius"], circle_beam.inputs["Radius"])
    link_sockets(tree, gin.outputs["Column Count"], circle_beam.inputs["Vertices"])
    circle_beam.fill_type = "NONE"

    # Extrude the beam circle into a ring
    extrude_beam = safe_node(tree, "GeometryNodeExtrudeMesh", (bx, by + 300))
    link_sockets(tree, circle_beam.outputs["Mesh"], extrude_beam.inputs["Mesh"])
    link_sockets(tree, gin.outputs["Beam Radius"], extrude_beam.inputs["Offset Scale"])
    extrude_beam.mode = "EDGES"

    # Set beam position at column height
    set_pos_beam = safe_node(tree, "GeometryNodeSetPosition", (bx + 200, by + 300))
    link_sockets(tree, extrude_beam.outputs["Mesh"], set_pos_beam.inputs["Geometry"])
    beam_z = safe_node(tree, "ShaderNodeMath", (bx + 100, by + 300))
    beam_z.operation = "MULTIPLY"
    beam_z.inputs[0].default_value = 1.0
    link_sockets(tree, gin.outputs["Column Height"], beam_z.inputs[1])

    beam_pos_in = safe_node(tree, "GeometryNodeInputPosition", (bx - 100, by + 200))
    sep_z = safe_node(tree, "ShaderNodeSeparateXYZ", (bx, by + 200))
    link_sockets(tree, beam_pos_in.outputs["Position"], sep_z.inputs["Vector"])

    combine_beam = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 200, by + 200))
    link_sockets(tree, sep_z.outputs["X"], combine_beam.inputs["X"])
    link_sockets(tree, sep_z.outputs["Y"], combine_beam.inputs["Y"])
    link_sockets(tree, beam_z.outputs[0], combine_beam.inputs["Z"])
    link_sockets(tree, combine_beam.outputs["Vector"], set_pos_beam.inputs["Position"])

    # ── Roof ──
    # Cone at top of columns
    roof_cone = safe_node(tree, "GeometryNodeMeshCone", (bx - 200, by))
    link_sockets(tree, gin.outputs["Column Count"], roof_cone.inputs["Vertices"])
    link_sockets(tree, gin.outputs["Radius"], roof_cone.inputs["Radius Bottom"])
    roof_cone.inputs["Radius Top"].default_value = 0.05
    roof_height = safe_node(tree, "ShaderNodeMath", (bx - 300, by))
    roof_height.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Radius"], roof_height.inputs[0])
    link_sockets(tree, gin.outputs["Roof Pitch"], roof_height.inputs[1])
    link_sockets(tree, roof_height.outputs[0], roof_cone.inputs["Depth"])

    # Move roof to top of columns
    set_pos_roof = safe_node(tree, "GeometryNodeSetPosition", (bx, by))
    link_sockets(tree, roof_cone.outputs["Mesh"], set_pos_roof.inputs["Geometry"])
    roof_z = safe_node(tree, "ShaderNodeMath", (bx - 100, by - 100))
    roof_z.operation = "ADD"
    link_sockets(tree, beam_z.outputs[0], roof_z.inputs[0])
    link_sockets(tree, roof_height.outputs[0], roof_z.inputs[1])

    roof_pos_in = safe_node(tree, "GeometryNodeInputPosition", (bx - 200, by - 200))
    sep_z_roof = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 100, by - 200))
    link_sockets(tree, roof_pos_in.outputs["Position"], sep_z_roof.inputs["Vector"])

    combine_roof = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 100, by - 200))
    link_sockets(tree, sep_z_roof.outputs["X"], combine_roof.inputs["X"])
    link_sockets(tree, sep_z_roof.outputs["Y"], combine_roof.inputs["Y"])
    link_sockets(tree, roof_z.outputs[0], combine_roof.inputs["Z"])
    link_sockets(tree, combine_roof.outputs["Vector"], set_pos_roof.inputs["Position"])

    # Roof thickness via extrude
    solid_roof = safe_node(tree, "GeometryNodeExtrudeMesh", (bx + 200, by))
    link_sockets(tree, set_pos_roof.outputs["Geometry"], solid_roof.inputs["Mesh"])
    solid_roof.inputs["Offset Scale"].default_value = 0.02
    solid_roof.mode = "FACES"

    # ── Star finial on top ──
    finial_cone = safe_node(tree, "GeometryNodeMeshCone", (bx + 400, by + 100))
    finial_cone.inputs["Vertices"].default_value = 5
    finial_cone.inputs["Radius Top"].default_value = 0.0
    finial_cone.inputs["Radius Bottom"].default_value = 0.08
    finial_cone.inputs["Depth"].default_value = 0.15

    switch_finial = safe_node(tree, "GeometryNodeSwitch", (bx + 600, by + 100))
    link_sockets(tree, gin.outputs["Has Finial"], switch_finial.inputs["Switch"])

    # Set finial position
    set_pos_fin = safe_node(tree, "GeometryNodeSetPosition", (bx + 500, by + 200))
    link_sockets(tree, finial_cone.outputs["Mesh"], set_pos_fin.inputs["Geometry"])
    fin_z = safe_node(tree, "ShaderNodeMath", (bx + 400, by + 300))
    fin_z.operation = "ADD"
    fin_z_extra = safe_node(tree, "ShaderNodeMath", (bx + 300, by + 300))
    fin_z_extra.operation = "ADD"
    link_sockets(tree, roof_z.outputs[0], fin_z_extra.inputs[0])
    fin_z_extra.inputs[1].default_value = 0.15
    link_sockets(tree, fin_z_extra.outputs[0], fin_z.inputs[0])
    fin_z.inputs[1].default_value = 0.0

    fin_pos_in = safe_node(tree, "GeometryNodeInputPosition", (bx + 300, by + 400))
    sep_z_fin = safe_node(tree, "ShaderNodeSeparateXYZ", (bx + 400, by + 400))
    link_sockets(tree, fin_pos_in.outputs["Position"], sep_z_fin.inputs["Vector"])
    combine_fin = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 500, by + 400))
    link_sockets(tree, sep_z_fin.outputs["X"], combine_fin.inputs["X"])
    link_sockets(tree, sep_z_fin.outputs["Y"], combine_fin.inputs["Y"])
    link_sockets(tree, fin_z.outputs[0], combine_fin.inputs["Z"])
    link_sockets(tree, combine_fin.outputs["Vector"], set_pos_fin.inputs["Position"])

    try:
        switch_finial.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, set_pos_fin.outputs["Geometry"], switch_finial.inputs.get("True") or switch_finial.inputs.get("TRUE"))

    # Engawa veranda (zen teahouse language) - annular deck around the posts
    engawa_r = safe_node(tree, "ShaderNodeMath", (bx - 300, by - 360))
    engawa_r.operation = "ADD"
    link_sockets(tree, gin.outputs["Radius"], engawa_r.inputs[0])
    link_sockets(tree, gin.outputs["Engawa Depth"], engawa_r.inputs[1])
    engawa = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 100, by - 360))
    engawa.inputs["Vertices"].default_value = 24
    engawa.inputs["Depth"].default_value = 0.08
    link_sockets(tree, engawa_r.outputs[0], engawa.inputs["Radius"])
    engawa_sw = safe_node(tree, "GeometryNodeSwitch", (bx + 120, by - 360))
    try:
        engawa_sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Has Engawa"], engawa_sw.inputs["Switch"])
    link_sockets(tree, engawa.outputs["Mesh"], engawa_sw.inputs.get("True") or engawa_sw.inputs.get("TRUE"))

    # Optional irimoya overlay - shallower second hip (teahouse concave roof)
    iri = safe_node(tree, "GeometryNodeMeshCone", (bx + 200, by - 480))
    iri.inputs["Vertices"].default_value = 12
    link_sockets(tree, gin.outputs["Radius"], iri.inputs["Radius Bottom"])
    iri_top = safe_node(tree, "ShaderNodeMath", (bx + 40, by - 480))
    iri_top.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Radius"], iri_top.inputs[0])
    iri_top.inputs[1].default_value = 0.55
    link_sockets(tree, iri_top.outputs[0], iri.inputs["Radius Top"])
    iri_h = safe_node(tree, "ShaderNodeMath", (bx + 40, by - 540))
    iri_h.operation = "MULTIPLY"
    link_sockets(tree, roof_height.outputs[0], iri_h.inputs[0])
    iri_h.inputs[1].default_value = 0.45
    link_sockets(tree, iri_h.outputs[0], iri.inputs["Depth"])
    iri_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 360, by - 480))
    link_sockets(tree, iri.outputs["Mesh"], iri_pos.inputs["Geometry"])
    iri_z = safe_node(tree, "ShaderNodeMath", (bx + 200, by - 560))
    iri_z.operation = "ADD"
    link_sockets(tree, beam_z.outputs[0], iri_z.inputs[0])
    iri_z.inputs[1].default_value = 0.12
    iri_combine = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 280, by - 560))
    link_sockets(tree, iri_z.outputs[0], iri_combine.inputs["Z"])
    link_sockets(tree, iri_combine.outputs["Vector"], iri_pos.inputs["Offset"])
    iri_sw = safe_node(tree, "GeometryNodeSwitch", (bx + 520, by - 480))
    try:
        iri_sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Has Irimoya"], iri_sw.inputs["Switch"])
    link_sockets(tree, iri_pos.outputs["Geometry"], iri_sw.inputs.get("True") or iri_sw.inputs.get("TRUE"))

    # ── Join everything ──
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 600, by - 100))
    link_sockets(tree, realize_col.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, set_pos_beam.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, solid_roof.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, switch_finial.outputs["Output"], join.inputs["Geometry"])
    link_sockets(tree, engawa_sw.outputs.get("Output") or engawa_sw.outputs[0], join.inputs["Geometry"])
    link_sockets(tree, iri_sw.outputs.get("Output") or iri_sw.outputs[0], join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 800, by - 100))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    music_geo = apply_universal_music_pass(tree, gin, shade.outputs["Geometry"], (bx + 1000, by - 100))
    link_sockets(tree, music_geo, gout.inputs["Geometry"])

    color_node(circle_col, "curve")
    color_node(inst_col, "instance")
    color_node(scale_col, "instance")
    color_node(realize_col, "instance")
    color_node(circle_beam, "curve")
    color_node(extrude_beam, "geometry")
    color_node(set_pos_beam, "attribute")
    color_node(roof_cone, "geometry")
    color_node(set_pos_roof, "attribute")
    color_node(solid_roof, "geometry")
    color_node(finial_cone, "geometry")
    color_node(switch_finial, "instance")
    color_node(join, "geometry")
    color_node(shade, "geometry")

    return label_tree(tree, "MEL_gazebo", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Columns", "nodes": ("column", "circle", "instance", "scale"), "role": "instance"},
        {"title": "Beam Ring", "nodes": ("beam",), "role": "curve"},
        {"title": "Roof", "nodes": ("roof",), "role": "geometry"},
        {"title": "Finial", "nodes": ("finial", "switch"), "role": "geometry"},
        {"title": "Output", "nodes": ("join", "shade", "Group Output"), "role": "output"},
    ])


def build_arch(group_name="MEL_arch"):
    """Arch structure: two uprights plus a swept crown arc."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Span", 2.0, 0.2, 20.0)
    add_float_param(tree, "Height", 3.0, 0.2, 20.0)
    add_float_param(tree, "Arch Rise", 1.0, 0.1, 5.0)
    add_float_param(tree, "Thickness", 0.1, 0.01, 0.5)
    add_int_param(tree, "Segments", 16, 4, 64)

    # Shared upright mesh.
    col = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by + 250))
    col_size = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 700, by + 250))
    link_sockets(tree, gin.outputs["Thickness"], col_size.inputs["X"])
    link_sockets(tree, gin.outputs["Thickness"], col_size.inputs["Y"])
    link_sockets(tree, gin.outputs["Height"], col_size.inputs["Z"])
    link_sockets(tree, col_size.outputs["Vector"], col.inputs["Size"])

    half_span_l = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 80))
    half_span_l.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Span"], half_span_l.inputs[0])
    half_span_l.inputs[1].default_value = -0.5
    half_span_r = safe_node(tree, "ShaderNodeMath", (bx - 700, by - 80))
    half_span_r.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Span"], half_span_r.inputs[0])
    half_span_r.inputs[1].default_value = 0.5

    left_pos = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 500, by + 80))
    right_pos = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 500, by - 80))
    link_sockets(tree, half_span_l.outputs[0], left_pos.inputs["X"])
    link_sockets(tree, half_span_r.outputs[0], right_pos.inputs["X"])

    set_left = safe_node(tree, "GeometryNodeTransform", (bx - 250, by + 180))
    set_right = safe_node(tree, "GeometryNodeTransform", (bx - 250, by))
    link_sockets(tree, col.outputs["Mesh"], set_left.inputs["Geometry"])
    link_sockets(tree, col.outputs["Mesh"], set_right.inputs["Geometry"])
    link_sockets(tree, left_pos.outputs["Vector"], set_left.inputs["Translation"])
    link_sockets(tree, right_pos.outputs["Vector"], set_right.inputs["Translation"])

    # Crown arc: circle mesh, scaled by span/rise and lifted to the column top.
    arc = safe_node(tree, "GeometryNodeMeshCircle", (bx - 500, by - 260))
    link_sockets(tree, gin.outputs["Segments"], arc.inputs["Vertices"])
    arc.fill_type = "NONE"
    arc.inputs["Radius"].default_value = 0.5

    arc_scale = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 700, by - 260))
    link_sockets(tree, gin.outputs["Span"], arc_scale.inputs["X"])
    link_sockets(tree, gin.outputs["Thickness"], arc_scale.inputs["Y"])
    link_sockets(tree, gin.outputs["Arch Rise"], arc_scale.inputs["Z"])
    arc_pos = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 500, by - 420))
    link_sockets(tree, gin.outputs["Height"], arc_pos.inputs["Z"])
    arc_tx = safe_node(tree, "GeometryNodeTransform", (bx - 250, by - 260))
    link_sockets(tree, arc.outputs["Mesh"], arc_tx.inputs["Geometry"])
    link_sockets(tree, arc_scale.outputs["Vector"], arc_tx.inputs["Scale"])
    link_sockets(tree, arc_pos.outputs["Vector"], arc_tx.inputs["Translation"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 100, by))
    link_sockets(tree, set_left.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, set_right.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, arc_tx.outputs["Geometry"], join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 350, by))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(col, "geometry")
    color_node(arc, "curve")
    color_node(join, "geometry")
    color_node(shade, "geometry")

    return label_tree(tree, "MEL_arch", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Uprights", "nodes": ("column", "left", "right"), "role": "geometry"},
        {"title": "Crown Arc", "nodes": ("arc",), "role": "curve"},
        {"title": "Output", "nodes": ("join", "shade", "Group Output"), "role": "output"},
    ])


def build_portico(group_name="MEL_portico"):
    """Portico / pediment — triangle gable roof over columns."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Width", 3.0, 0.5, 20.0)
    add_float_param(tree, "Depth", 1.5, 0.3, 10.0)
    add_float_param(tree, "Column Height", 2.4, 0.3, 20.0)
    add_int_param(tree, "Column Count", 4, 2, 20)

    # Simple box pediment
    cube = safe_node(tree, "GeometryNodeMeshCube", (bx - 200, by + 100))
    link_float_to_vector(tree, gin.outputs["Width"], cube, "Size", component=0, defaults=(0.0, 0.0, 0.0))
    link_float_to_vector(tree, gin.outputs["Depth"], cube, "Size", component=1, defaults=(0.0, 0.0, 0.0))
    cube.inputs["Size"].default_value[2] = 0.3

    set_pos_ped = safe_node(tree, "GeometryNodeSetPosition", (bx, by + 100))
    link_sockets(tree, cube.outputs["Mesh"], set_pos_ped.inputs["Geometry"])
    ped_z = safe_node(tree, "ShaderNodeMath", (bx - 100, by))
    ped_z.operation = "ADD"
    link_sockets(tree, gin.outputs["Column Height"], ped_z.inputs[0])
    ped_z.inputs[1].default_value = 0.3

    # Columns grid.
    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 200, by - 200))
    link_sockets(tree, gin.outputs["Column Count"], grid.inputs["Vertices X"])
    grid.inputs["Vertices Y"].default_value = 2
    link_sockets(tree, gin.outputs["Width"], grid.inputs["Size X"])
    link_sockets(tree, gin.outputs["Depth"], grid.inputs["Size Y"])

    column = safe_node(tree, "GeometryNodeMeshCylinder", (bx, by - 250))
    column.inputs["Radius"].default_value = 0.08
    link_sockets(tree, gin.outputs["Column Height"], column.inputs["Depth"])
    column.inputs["Vertices"].default_value = 12
    column.fill_type = "NGON"

    inst_cols = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 200, by - 200))
    link_sockets(tree, grid.outputs["Mesh"], inst_cols.inputs["Points"])
    link_sockets(tree, column.outputs["Mesh"], inst_cols.inputs["Instance"])

    realize_cols = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 400, by - 200))
    link_sockets(tree, inst_cols.outputs["Instances"], realize_cols.inputs["Geometry"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 600, by))
    link_sockets(tree, set_pos_ped.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, realize_cols.outputs["Geometry"], join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 800, by))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(cube, "geometry")
    color_node(grid, "curve")
    color_node(inst_cols, "instance")
    color_node(set_pos_ped, "attribute")
    color_node(join, "geometry")
    color_node(shade, "geometry")

    return label_tree(tree, "MEL_portico", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Pediment", "nodes": ("pediment", "cube"), "role": "geometry"},
        {"title": "Columns", "nodes": ("grid", "column", "instance"), "role": "instance"},
        {"title": "Output", "nodes": ("join", "shade", "Group Output"), "role": "output"},
    ])


# -- Registry --
from .core import register_builder

register_builder("MEL_gazebo", build_gazebo, "Gazebo",
    "Full gazebo - columns, beam ring, conical roof, star finial",
    "structures")
register_builder("MEL_arch", build_arch, "Arch",
    "Simple arch structure - column pair with arc span",
    "structures")
register_builder("MEL_portico", build_portico, "Portico",
    "Portico assembly - column grid with triangular pediment gable",
    "structures")
