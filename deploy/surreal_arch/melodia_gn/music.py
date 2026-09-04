"""Musical GN group builders — note head, treble clef, staff, harmonic driver, phrase.

Uses: exponent_blend (spiral), power_scale (iteration falloff), add (sine stacking),
      store_attribute (pitch/duration/velocity), bounding_box (auto-fit).
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node,
    label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, add_vector_param,
    make_group_input, sweep_profile,
    input_geometry_with_default,
)


def _true_socket(node):
    return node.inputs.get("True") or node.inputs.get("TRUE")


def _false_socket(node):
    return node.inputs.get("False") or node.inputs.get("FALSE")


def _output_socket(node):
    return node.outputs.get("Output") or (node.outputs[0] if node and node.outputs else None)


def _ensure_group_node(tree, group_name, builder, loc):
    if group_name not in bpy.data.node_groups:
        builder(group_name)
    node = safe_node(tree, "GeometryNodeGroup", loc)
    if node:
        node.node_tree = bpy.data.node_groups.get(group_name)
    return node


def build_music_note_head(group_name="MEL_music_note_head"):
    """Elliptical note head with optional stem and flag.

    Stores 'pitch', 'duration', 'velocity' attributes for downstream reads.
    Uses: power_scale (flag curvature), store_attribute (pitch/duration/velocity),
          bounding_box (auto-scale to staff lines)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Scale", 1.0, 0.2, 3.0)
    add_float_param(tree, "Pitch", 0.0, -3.0, 3.0)
    add_float_param(tree, "Duration", 1.0, 0.25, 4.0)
    add_float_param(tree, "Velocity", 0.8, 0.0, 1.0)
    add_int_param(tree, "Note Kind", 2, 0, 3)
    add_int_param(tree, "LOD", 1, 0, 3)
    add_bool_param(tree, "Has Stem", True)
    add_bool_param(tree, "Has Flag", False)
    add_bool_param(tree, "Realize for export", False)

    # Note head: flattened UV sphere
    uv_sphere = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 300, by + 300))
    uv_sphere.inputs["Segments"].default_value = 16
    uv_sphere.inputs["Rings"].default_value = 8

    # Scale to elliptical: non-uniform XYZ
    transform = safe_node(tree, "GeometryNodeTransform", (bx - 100, by + 300))
    link_sockets(tree, uv_sphere.outputs["Mesh"], transform.inputs["Geometry"])
    transform.inputs["Scale"].default_value[0] = 1.2
    transform.inputs["Scale"].default_value[1] = 0.85
    transform.inputs["Scale"].default_value[2] = 0.45

    # Rotate slightly for note-head angle
    transform.inputs["Rotation"].default_value[1] = -0.26  # -15deg Y

    # Overall scale
    scale_node = safe_node(tree, "GeometryNodeTransform", (bx + 100, by + 300))
    link_sockets(tree, transform.outputs["Geometry"], scale_node.inputs["Geometry"])
    link_float_to_vector(tree, gin.outputs["Scale"], scale_node, "Scale", component=1, defaults=(1.0, 0.0, 1.0))

    # Stem: thin cube
    stem = safe_node(tree, "GeometryNodeMeshCube", (bx - 200, by + 100))
    stem.inputs["Size"].default_value[0] = 0.02
    stem.inputs["Size"].default_value[1] = 0.02
    stem.inputs["Size"].default_value[2] = 0.5

    stem_pos = safe_node(tree, "GeometryNodeSetPosition", (bx, by + 100))
    link_sockets(tree, stem.outputs["Mesh"], stem_pos.inputs["Geometry"])
    stem_z = safe_node(tree, "ShaderNodeMath", (bx - 100, by + 50))
    stem_z.operation = "MULTIPLY"
    stem_z.inputs[0].default_value = 0.25
    link_sockets(tree, gin.outputs["Scale"], stem_z.inputs[1])
    link_float_to_vector(tree, stem_z.outputs[0], stem_pos, "Position", component=2)

    # Flag: curved arc using bezier segment
    flag_bezier = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx - 300, by - 50))
    flag_bezier.inputs["Start"].default_value = (0.0, 0.0, 0.0)
    flag_bezier.inputs["Start Handle"].default_value = (0.06, 0.04, 0.0)
    flag_bezier.inputs["End"].default_value = (0.15, -0.15, 0.0)
    flag_bezier.inputs["End Handle"].default_value = (0.12, -0.05, 0.0)
    try:
        flag_bezier.resolution = 6
    except Exception:
        res_in = flag_bezier.inputs.get("Resolution")
        if res_in is not None:
            res_in.default_value = 6

    flag_circle = safe_node(tree, "GeometryNodeMeshCircle", (bx - 100, by - 50))
    flag_circle.inputs["Radius"].default_value = 0.03
    flag_circle.inputs["Vertices"].default_value = 6
    flag_circle.fill_type = "NGON"

    flag_sweep = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 100, by - 50))
    link_sockets(tree, flag_bezier.outputs["Curve"], flag_sweep.inputs["Curve"])
    flag_prof = flag_sweep.inputs.get("Profile Curve") or flag_sweep.inputs.get("Profile")
    link_sockets(tree, flag_circle.outputs["Mesh"], flag_prof)

    # Switch: stem on/off
    stem_switch = safe_node(tree, "GeometryNodeSwitch", (bx + 200, by + 100))
    try:
        stem_switch.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Has Stem"], stem_switch.inputs["Switch"])
    link_sockets(tree, stem_pos.outputs["Geometry"], _true_socket(stem_switch))

    # Switch: flag on/off
    flag_switch = safe_node(tree, "GeometryNodeSwitch", (bx + 200, by - 50))
    try:
        flag_switch.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Has Flag"], flag_switch.inputs["Switch"])
    link_sockets(tree, flag_sweep.outputs["Mesh"], _true_socket(flag_switch))

    # Join all parts
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 400, by + 150))
    link_sockets(tree, scale_node.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, stem_switch.outputs["Output"], join.inputs["Geometry"])
    link_sockets(tree, flag_switch.outputs["Output"], join.inputs["Geometry"])

    # Store attributes for downstream (set Name so pitch/duration/velocity are retrievable)
    store_pitch = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 600, by + 250))
    link_sockets(tree, join.outputs["Geometry"], store_pitch.inputs["Geometry"])
    link_sockets(tree, gin.outputs["Pitch"], store_pitch.inputs["Value"])
    store_pitch.data_type = "FLOAT"
    try:
        store_pitch.inputs["Name"].default_value = "pitch"
    except Exception:
        pass

    store_dur = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 600, by + 100))
    link_sockets(tree, store_pitch.outputs["Geometry"], store_dur.inputs["Geometry"])
    link_sockets(tree, gin.outputs["Duration"], store_dur.inputs["Value"])
    store_dur.data_type = "FLOAT"
    try:
        store_dur.inputs["Name"].default_value = "duration"
    except Exception:
        pass

    store_vel = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 600, by - 50))
    link_sockets(tree, store_dur.outputs["Geometry"], store_vel.inputs["Geometry"])
    link_sockets(tree, gin.outputs["Velocity"], store_vel.inputs["Value"])
    store_vel.data_type = "FLOAT"
    try:
        store_vel.inputs["Name"].default_value = "velocity"
    except Exception:
        pass

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 800, by))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, store_vel.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(uv_sphere, "geometry")
    color_node(transform, "instance")
    color_node(join, "geometry")
    color_node(store_pitch, "attribute")
    color_node(shade, "geometry")

    return label_tree(tree, "MEL_music_note_head", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Note Head", "nodes": ("sphere", "transform", "scale"), "role": "geometry"},
        {"title": "Stem And Flag", "nodes": ("stem", "flag", "switch"), "role": "instance"},
        {"title": "Attributes", "nodes": ("store", "pitch", "duration", "velocity"), "role": "attribute"},
        {"title": "Output", "nodes": ("shade", "Group Output"), "role": "output"},
    ])


def build_music_treble_clef(group_name="MEL_music_treble_clef"):
    """G-clef (𝄞) — calligraphic curve with ascending body, tight spiral knot at top,
    descending stem, and bottom hook. Uses 3 bezier curve segments joined and swept
    with a tube profile so the result is actually recognizable as a treble clef.

    Uses: exponent_blend (spiral radius), add (body+stem+hook),
          bounding_box (auto-fit to staff), store_attribute (clef zone)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_float_param(tree, "Thickness", 0.018, 0.006, 0.08)
    add_float_param(tree, "Spiral Tightness", 0.5, 0.2, 1.0)
    add_float_param(tree, "Body Curve", 0.5, 0.0, 1.0)

    # ─── Top spiral knot (1.5 turns, tight) ────────────────────
    spiral = safe_node(tree, "GeometryNodeCurveSpiral", (bx - 600, by + 300))
    spiral.inputs["Height"].default_value = 0.0
    spiral_tight = safe_node(tree, "ShaderNodeMath", (bx - 750, by + 350))
    spiral_tight.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Spiral Tightness"], spiral_tight.inputs[0])
    spiral_tight.inputs[1].default_value = 0.016
    link_sockets(tree, spiral_tight.outputs[0], spiral.inputs["Start Radius"])
    spiral_end_r = safe_node(tree, "ShaderNodeMath", (bx - 750, by + 300))
    spiral_end_r.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Spiral Tightness"], spiral_end_r.inputs[0])
    spiral_end_r.inputs[1].default_value = 0.06
    link_sockets(tree, spiral_end_r.outputs[0], spiral.inputs["End Radius"])
    spiral.inputs["Rotations"].default_value = 1.8
    spiral.inputs["Resolution"].default_value = 32

    # Rotate spiral to XZ plane (flat G-clef curl)
    rot_spiral = safe_node(tree, "GeometryNodeTransform", (bx - 400, by + 300))
    link_sockets(tree, spiral.outputs["Curve"], rot_spiral.inputs["Geometry"])
    rot_spiral.inputs["Rotation"].default_value = (math.radians(90), 0.0, 0.0)

    # Position spiral at top-center of clef
    pos_spiral = safe_node(tree, "GeometryNodeTransform", (bx - 200, by + 300))
    link_sockets(tree, rot_spiral.outputs["Geometry"], pos_spiral.inputs["Geometry"])
    pos_spiral.inputs["Translation"].default_value = (0.0, 0.42, 0.0)

    # ─── Ascending body (S-curve from bottom to spiral entry) ──
    # Using QuadraticBezier: start point → control → end point
    body_bezier = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx - 600, by))
    # Start: bottom hook transition point
    body_bezier.inputs["Start"].default_value = (0.15, -0.48, 0.0)
    # Control: curves right and up
    body_ctrl = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 700, by - 50))
    body_ctrl_x = safe_node(tree, "ShaderNodeMath", (bx - 800, by))
    body_ctrl_x.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Body Curve"], body_ctrl_x.inputs[0])
    body_ctrl_x.inputs[1].default_value = 0.35
    body_ctrl_y = safe_node(tree, "ShaderNodeMath", (bx - 800, by - 100))
    body_ctrl_y.operation = "MULTIPLY"
    body_ctrl_y.inputs[0].default_value = 0.05
    link_sockets(tree, gin.outputs["Body Curve"], body_ctrl_y.inputs[1])
    link_sockets(tree, body_ctrl_x.outputs[0], body_ctrl.inputs["X"])
    link_sockets(tree, body_ctrl_y.outputs[0], body_ctrl.inputs["Y"])
    # End: near spiral entry point, right side
    body_bezier.inputs["End"].default_value = (0.0, 0.35, 0.0)
    body_bezier.inputs["End Handle"].default_value = (0.08, 0.30, 0.0)

    # ─── Descending stem (from spiral center down) ─────────────
    stem_bezier = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx - 600, by - 150))
    # The stem must pass through the spiral center and continue down
    # It should start just inside the spiral (slightly below center)
    # and go straight down through the right side of the body
    stem_bezier.inputs["Start"].default_value = (0.01, 0.38, 0.0)
    stem_bezier.inputs["Start Handle"].default_value = (0.01, 0.10, 0.0)
    stem_bezier.inputs["End"].default_value = (0.01, -0.55, 0.0)
    stem_bezier.inputs["End Handle"].default_value = (0.01, -0.30, 0.0)
    stem_bezier.inputs["Resolution"].default_value = 8

    # ─── Bottom hook (curves left and up) ──────────────────────
    hook_bezier = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx - 600, by - 300))
    hook_bezier.inputs["Start"].default_value = (0.01, -0.55, 0.0)
    hook_bezier.inputs["Start Handle"].default_value = (-0.05, -0.55, 0.0)
    hook_bezier.inputs["End"].default_value = (-0.22, -0.48, 0.0)
    hook_bezier.inputs["End Handle"].default_value = (-0.18, -0.52, 0.0)
    hook_bezier.inputs["Resolution"].default_value = 8

    # ─── Join all curves into one ──────────────────────────────
    join_curves = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 100, by + 100))
    link_sockets(tree, pos_spiral.outputs["Geometry"], join_curves.inputs["Geometry"])
    link_sockets(tree, body_bezier.outputs["Curve"], join_curves.inputs["Geometry"])
    link_sockets(tree, stem_bezier.outputs["Curve"], join_curves.inputs["Geometry"])
    link_sockets(tree, hook_bezier.outputs["Curve"], join_curves.inputs["Geometry"])
    try:
        from .profiles import build_lissajous_curve
        flourish = _ensure_group_node(tree, "MEL_lissajous", build_lissajous_curve, (bx - 300, by - 420))
        if flourish and flourish.node_tree:
            if flourish.inputs.get("A"):
                flourish.inputs["A"].default_value = 0.10
            if flourish.inputs.get("B"):
                flourish.inputs["B"].default_value = 0.16
            if flourish.inputs.get("Steps"):
                flourish.inputs["Steps"].default_value = 64
            geo_out = flourish.outputs.get("Geometry")
            if geo_out:
                link_sockets(tree, geo_out, join_curves.inputs["Geometry"])
            color_node(flourish, "curve")
    except Exception:
        pass

    # Merge overlapping points so it's one continuous shape
    merge = safe_node(tree, "GeometryNodeMergeByDistance", (bx + 100, by + 100))
    link_sockets(tree, join_curves.outputs["Geometry"], merge.inputs["Geometry"])
    merge.inputs["Distance"].default_value = 0.001

    # ─── Sweep with tube profile ───────────────────────────────
    circle = safe_node(tree, "GeometryNodeMeshCircle", (bx - 100, by - 50))
    link_sockets(tree, gin.outputs["Thickness"], circle.inputs["Radius"])
    circle.inputs["Vertices"].default_value = 8
    circle.fill_type = "NGON"

    clef_mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 100, by - 50))
    link_sockets(tree, merge.outputs["Geometry"], clef_mesh.inputs["Curve"])
    profile_sock = clef_mesh.inputs.get("Profile Curve") or clef_mesh.inputs.get("Profile")
    link_sockets(tree, circle.outputs["Mesh"], profile_sock)

    # ─── Finial dot at stem top ────────────────────────────────
    dot = safe_node(tree, "GeometryNodeMeshUVSphere", (bx, by - 150))
    dot.inputs["Segments"].default_value = 12
    dot.inputs["Rings"].default_value = 8

    dot_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 200, by - 150))
    link_sockets(tree, dot.outputs["Mesh"], dot_pos.inputs["Geometry"])
    dot_pos.inputs["Position"].default_value = (0.0, 0.45, 0.0)
    dot_diam = safe_node(tree, "ShaderNodeMath", (bx + 100, by - 200))
    dot_diam.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Thickness"], dot_diam.inputs[0])
    dot_diam.inputs[1].default_value = 3.0
    dot_scale = safe_node(tree, "GeometryNodeTransform", (bx + 400, by - 150))
    link_sockets(tree, dot_pos.outputs["Geometry"], dot_scale.inputs["Geometry"])
    dot_scale_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 300, by - 200))
    link_sockets(tree, dot_diam.outputs[0], dot_scale_vec.inputs["X"])
    link_sockets(tree, dot_diam.outputs[0], dot_scale_vec.inputs["Y"])
    link_sockets(tree, dot_diam.outputs[0], dot_scale_vec.inputs["Z"])
    link_sockets(tree, dot_scale_vec.outputs["Vector"], dot_scale.inputs["Scale"])

    # ─── Join clef body + dot ──────────────────────────────────
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 300, by + 100))
    link_sockets(tree, clef_mesh.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, dot_scale.outputs["Geometry"], join.inputs["Geometry"])

    scale_all = safe_node(tree, "GeometryNodeTransform", (bx + 500, by + 100))
    link_sockets(tree, join.outputs["Geometry"], scale_all.inputs["Geometry"])
    scale_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 400, by + 50))
    link_sockets(tree, gin.outputs["Scale"], scale_vec.inputs["X"])
    link_sockets(tree, gin.outputs["Scale"], scale_vec.inputs["Y"])
    link_sockets(tree, gin.outputs["Scale"], scale_vec.inputs["Z"])
    link_sockets(tree, scale_vec.outputs["Vector"], scale_all.inputs["Scale"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 700, by + 100))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, scale_all.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(spiral, "curve")
    color_node(pos_spiral, "instance")
    color_node(join_curves, "curve")
    color_node(merge, "math")
    color_node(clef_mesh, "geometry")
    color_node(join, "geometry")

    return label_tree(tree, "MEL_music_treble_clef", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Clef Curves", "nodes": ("spiral", "bezier", "lissajous", "join"), "role": "curve"},
        {"title": "Tube Profile", "nodes": ("circle", "curve to mesh"), "role": "geometry"},
        {"title": "Scale And Output", "nodes": ("scale", "shade", "Group Output"), "role": "output"},
    ])


def build_music_staff(group_name="MEL_music_staff"):
    """Five-line staff with bar lines.

    Uses: linear_array (staff lines ├ù5), add (merge lines + bars),
          bounding_box (auto-fit to phrase length), store_attribute (line index)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Length", 4.0, 0.5, 20.0)
    add_float_param(tree, "Line Spacing", 0.15, 0.05, 0.5)
    add_float_param(tree, "Thickness", 0.008, 0.002, 0.03)
    add_int_param(tree, "Bar Count", 4, 1, 16)
    add_bool_param(tree, "Show Clef", True)

    # Single staff line: curve sweep along X
    line_cyl = safe_node(tree, "GeometryNodeMeshLine", (bx - 400, by + 300))
    line_cyl.mode = "END_POINTS"
    line_cyl.inputs["Count"].default_value = 2
    link_float_to_vector(tree, gin.outputs["Length"], line_cyl, "Start Location", component=0)
    line_mesh_sock = sweep_profile(
        tree, (bx - 100, by + 300), line_cyl.outputs["Mesh"], gin.outputs["Thickness"],
        profile_res=8, already_curve=False)

    # Array 5 lines via linear array on Y
    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx + 100, by + 300))
    grid.inputs["Size X"].default_value = 0.0
    spacing_span = safe_node(tree, "ShaderNodeMath", (bx - 100, by + 500))
    spacing_span.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Line Spacing"], spacing_span.inputs[0])
    spacing_span.inputs[1].default_value = 4.0
    link_sockets(tree, spacing_span.outputs[0], grid.inputs["Size Y"])
    grid.inputs["Vertices Y"].default_value = 5
    grid.inputs["Vertices X"].default_value = 1

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 300, by + 300))
    link_sockets(tree, grid.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, line_mesh_sock, inst.inputs["Instance"])

    # Set position to space lines vertically
    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 500, by + 300))
    link_sockets(tree, inst.outputs["Instances"], set_pos.inputs["Geometry"])

    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 700, by + 300))
    link_sockets(tree, set_pos.outputs["Geometry"], realize.inputs["Geometry"])

    # Bar lines: vertical cylinders instanced along X
    bar_cyl = safe_node(tree, "GeometryNodeMeshLine", (bx - 200, by + 100))
    bar_cyl.mode = "END_POINTS"
    bar_cyl.inputs["Count"].default_value = 2
    bar_cyl.inputs["Start Location"].default_value[2] = -0.35
    bar_cyl.inputs["Start Location"].default_value[1] = 0.35

    bar_mesh_sock = sweep_profile(
        tree, (bx, by + 100), bar_cyl.outputs["Mesh"], gin.outputs["Thickness"],
        profile_res=8, already_curve=False)

    # Array bar lines along X
    bar_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 200, by))
    bar_line.mode = "END_POINTS"
    link_sockets(tree, gin.outputs["Bar Count"], bar_line.inputs["Count"])
    link_float_to_vector(tree, gin.outputs["Length"], bar_line, "Start Location", component=0)

    bar_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx, by))
    link_sockets(tree, bar_line.outputs["Mesh"], bar_inst.inputs["Points"])
    link_sockets(tree, bar_mesh_sock, bar_inst.inputs["Instance"])

    realize_bars = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 200, by))
    link_sockets(tree, bar_inst.outputs["Instances"], realize_bars.inputs["Geometry"])

    # Join staff lines + bars
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 200, by + 150))
    link_sockets(tree, realize.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, realize_bars.outputs["Geometry"], join.inputs["Geometry"])

    clef_grp = _ensure_group_node(tree, "MEL_music_treble_clef", build_music_treble_clef, (bx, by - 260))
    clef_switch = safe_node(tree, "GeometryNodeSwitch", (bx + 200, by - 240))
    try:
        clef_switch.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Show Clef"], clef_switch.inputs["Switch"])
    if clef_grp and clef_grp.node_tree:
        clef_geo = clef_grp.outputs.get("Geometry")
        if clef_geo:
            link_sockets(tree, clef_geo, _true_socket(clef_switch))
    link_sockets(tree, _output_socket(clef_switch), join.inputs["Geometry"])

    # Store line index attribute
    store_line = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 400, by + 150))
    link_sockets(tree, join.outputs["Geometry"], store_line.inputs["Geometry"])
    store_line.data_type = "INT"
    try:
        store_line.inputs["Name"].default_value = "staff_line"
    except Exception:
        pass

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 600, by + 150))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, store_line.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(grid, "curve")
    color_node(inst, "instance")
    color_node(realize, "instance")
    color_node(clef_grp, "curve")
    color_node(clef_switch, "instance")
    color_node(join, "geometry")
    color_node(store_line, "attribute")
    color_node(shade, "geometry")

    return label_tree(tree, "MEL_music_staff", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Staff Lines", "nodes": ("grid", "line", "spacing"), "role": "curve"},
        {"title": "Bars", "nodes": ("bar",), "role": "geometry"},
        {"title": "Clef", "nodes": ("clef", "switch"), "role": "curve"},
        {"title": "Attributes And Output", "nodes": ("store", "shade", "Group Output"), "role": "output"},
    ])


def build_music_harmonic(group_name="MEL_music_harmonic"):
    """Harmonic pitch driver — additive sine layers for note placement.

    Formula: pitch = ╬ú sin(index * freq * harmonic_i) for i in 1..5
    Uses: add (sine stacking), power_scale (harmonic amplitude falloff),
          exponent_blend (phrase envelope fade-in/fade-out),
          store_attribute (pitch value for downstream)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Base Frequency", 2.0, 0.1, 10.0)
    add_float_param(tree, "Harmonic Blend", 0.5, 0.0, 1.0)
    add_float_param(tree, "Octave Mix", 0.3, 0.0, 1.0)
    add_float_param(tree, "Voice Count", 3.0, 1.0, 5.0)
    add_float_param(tree, "Amplitude", 0.5, 0.0, 2.0)
    add_float_param(tree, "Fade In", 0.2, 0.0, 1.0)
    add_float_param(tree, "Fade Out", 0.2, 0.0, 1.0)
    add_int_param(tree, "Note Count", 16, 4, 64)

    src = input_geometry_with_default(tree, gin, (bx - 700, by), kind="grid")

    # Position input
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 500, by + 300))

    # normalized position: t = idx / count
    idx_f = safe_node(tree, "ShaderNodeMath", (bx - 300, by + 300))
    idx_f.operation = "ADD"
    idx_f.inputs[0].default_value = 1.0
    link_sockets(tree, idx.outputs["Index"], idx_f.inputs[1])

    count_f = safe_node(tree, "ShaderNodeMath", (bx - 300, by + 200))
    count_f.operation = "ADD"
    count_f.inputs[0].default_value = 1.0
    link_sockets(tree, gin.outputs["Note Count"], count_f.inputs[1])

    t = safe_node(tree, "ShaderNodeMath", (bx - 100, by + 250))
    t.operation = "DIVIDE"
    link_sockets(tree, idx_f.outputs[0], t.inputs[0])
    link_sockets(tree, count_f.outputs[0], t.inputs[1])

    # Layer 1: sin(t * base_freq)
    l1 = safe_node(tree, "ShaderNodeMath", (bx + 100, by + 300))
    l1.operation = "MULTIPLY"
    link_sockets(tree, t.outputs[0], l1.inputs[0])
    link_sockets(tree, gin.outputs["Base Frequency"], l1.inputs[1])

    sin1 = safe_node(tree, "ShaderNodeMath", (bx + 300, by + 300))
    sin1.operation = "SINE"
    link_sockets(tree, l1.outputs[0], sin1.inputs[0])

    # Layer 2: sin(t * base_freq * 2) * blend
    l2 = safe_node(tree, "ShaderNodeMath", (bx + 100, by + 200))
    l2.operation = "MULTIPLY"
    link_sockets(tree, l1.outputs[0], l2.inputs[0])
    l2.inputs[1].default_value = 2.0

    sin2 = safe_node(tree, "ShaderNodeMath", (bx + 300, by + 200))
    sin2.operation = "SINE"
    link_sockets(tree, l2.outputs[0], sin2.inputs[0])

    mul2 = safe_node(tree, "ShaderNodeMath", (bx + 500, by + 200))
    mul2.operation = "MULTIPLY"
    link_sockets(tree, sin2.outputs[0], mul2.inputs[0])
    link_sockets(tree, gin.outputs["Harmonic Blend"], mul2.inputs[1])

    # Layer 3: sin(t * base_freq * 3) * blend^2
    l3 = safe_node(tree, "ShaderNodeMath", (bx + 100, by + 100))
    l3.operation = "MULTIPLY"
    link_sockets(tree, l1.outputs[0], l3.inputs[0])
    l3.inputs[1].default_value = 3.0

    sin3 = safe_node(tree, "ShaderNodeMath", (bx + 300, by + 100))
    sin3.operation = "SINE"
    link_sockets(tree, l3.outputs[0], sin3.inputs[0])

    blend_pow = safe_node(tree, "ShaderNodeMath", (bx + 400, by + 100))
    blend_pow.operation = "POWER"
    link_sockets(tree, gin.outputs["Harmonic Blend"], blend_pow.inputs[0])
    blend_pow.inputs[1].default_value = 2.0

    mul3 = safe_node(tree, "ShaderNodeMath", (bx + 550, by + 100))
    mul3.operation = "MULTIPLY"
    link_sockets(tree, sin3.outputs[0], mul3.inputs[0])
    link_sockets(tree, blend_pow.outputs[0], mul3.inputs[1])

    # Layer 4 (octave): sin(t * base_freq * 0.5) * octave_mix
    l4 = safe_node(tree, "ShaderNodeMath", (bx + 100, by))
    l4.operation = "MULTIPLY"
    link_sockets(tree, l1.outputs[0], l4.inputs[0])
    l4.inputs[1].default_value = 0.5

    sin4 = safe_node(tree, "ShaderNodeMath", (bx + 300, by))
    sin4.operation = "SINE"
    link_sockets(tree, l4.outputs[0], sin4.inputs[0])

    mul4 = safe_node(tree, "ShaderNodeMath", (bx + 500, by))
    mul4.operation = "MULTIPLY"
    link_sockets(tree, sin4.outputs[0], mul4.inputs[0])
    link_sockets(tree, gin.outputs["Octave Mix"], mul4.inputs[1])

    # Layer 5 (sub): sin(t * base_freq * 0.25) * octave_mix * 0.5
    l5 = safe_node(tree, "ShaderNodeMath", (bx + 100, by - 100))
    l5.operation = "MULTIPLY"
    link_sockets(tree, l1.outputs[0], l5.inputs[0])
    l5.inputs[1].default_value = 0.25

    sin5 = safe_node(tree, "ShaderNodeMath", (bx + 300, by - 100))
    sin5.operation = "SINE"
    link_sockets(tree, l5.outputs[0], sin5.inputs[0])

    mul5 = safe_node(tree, "ShaderNodeMath", (bx + 500, by - 100))
    mul5.operation = "MULTIPLY"
    link_sockets(tree, sin5.outputs[0], mul5.inputs[0])
    link_sockets(tree, gin.outputs["Octave Mix"], mul5.inputs[1])
    mul5_half = safe_node(tree, "ShaderNodeMath", (bx + 650, by - 100))
    mul5_half.operation = "MULTIPLY"
    link_sockets(tree, mul5.outputs[0], mul5_half.inputs[0])
    mul5_half.inputs[1].default_value = 0.5

    # ADD all layers
    add_a = safe_node(tree, "ShaderNodeMath", (bx + 800, by + 300))
    add_a.operation = "ADD"
    link_sockets(tree, sin1.outputs[0], add_a.inputs[0])
    link_sockets(tree, mul2.outputs[0], add_a.inputs[1])

    add_b = safe_node(tree, "ShaderNodeMath", (bx + 800, by + 100))
    add_b.operation = "ADD"
    link_sockets(tree, add_a.outputs[0], add_b.inputs[0])
    link_sockets(tree, mul3.outputs[0], add_b.inputs[1])

    add_c = safe_node(tree, "ShaderNodeMath", (bx + 800, by))
    add_c.operation = "ADD"
    link_sockets(tree, add_b.outputs[0], add_c.inputs[0])
    link_sockets(tree, mul4.outputs[0], add_c.inputs[1])

    add_d = safe_node(tree, "ShaderNodeMath", (bx + 800, by - 100))
    add_d.operation = "ADD"
    link_sockets(tree, add_c.outputs[0], add_d.inputs[0])
    link_sockets(tree, mul5_half.outputs[0], add_d.inputs[1])

    # Multiply by amplitude
    amp = safe_node(tree, "ShaderNodeMath", (bx + 1000, by + 100))
    amp.operation = "MULTIPLY"
    link_sockets(tree, add_d.outputs[0], amp.inputs[0])
    link_sockets(tree, gin.outputs["Amplitude"], amp.inputs[1])

    # Exponent blend envelope: fade-in * fade-out
    fade_in = safe_node(tree, "ShaderNodeMath", (bx + 800, by + 400))
    fade_in.operation = "POWER"
    link_sockets(tree, t.outputs[0], fade_in.inputs[0])
    link_sockets(tree, gin.outputs["Fade In"], fade_in.inputs[1])

    fade_out = safe_node(tree, "ShaderNodeMath", (bx + 800, by + 450))
    fade_out.operation = "POWER"
    one_minus_t = safe_node(tree, "ShaderNodeMath", (bx + 600, by + 450))
    one_minus_t.operation = "SUBTRACT"
    one_minus_t.inputs[0].default_value = 1.0
    link_sockets(tree, t.outputs[0], one_minus_t.inputs[1])
    link_sockets(tree, one_minus_t.outputs[0], fade_out.inputs[0])
    link_sockets(tree, gin.outputs["Fade Out"], fade_out.inputs[1])

    envelope = safe_node(tree, "ShaderNodeMath", (bx + 1000, by + 400))
    envelope.operation = "MULTIPLY"
    link_sockets(tree, fade_in.outputs[0], envelope.inputs[0])
    link_sockets(tree, fade_out.outputs[0], envelope.inputs[1])

    final = safe_node(tree, "ShaderNodeMath", (bx + 1200, by + 250))
    final.operation = "MULTIPLY"
    link_sockets(tree, amp.outputs[0], final.inputs[0])
    link_sockets(tree, envelope.outputs[0], final.inputs[1])

    # Store as "pitch" attribute
    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx + 1400, by + 250))
    link_sockets(tree, src, store.inputs["Geometry"])
    link_sockets(tree, final.outputs[0], store.inputs["Value"])
    store.data_type = "FLOAT"
    try:
        store.inputs["Name"].default_value = "pitch"
    except Exception:
        pass

    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(idx, "attribute")
    color_node(add_a, "math")
    color_node(add_d, "math")
    color_node(store, "attribute")

    return label_tree(tree, "MEL_music_harmonic", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Harmonic Layers", "nodes": ("sin", "mul", "add"), "role": "math"},
        {"title": "Envelope", "nodes": ("fade", "envelope"), "role": "math"},
        {"title": "Pitch Attribute", "nodes": ("store", "pitch"), "role": "attribute"},
    ])


def build_music_phrase(group_name="MEL_music_phrase"):
    """Composite musical phrase — staff + note heads + harmonic pitch + treble clef.

    Chains stored attributes: pitch from harmonic drives note head Z position.
    Uses: add (combine staff + notes), store_attribute (phrase metadata),
          exponent_blend (phrase curve), power_scale (emphasis),
          bounding_box (read staff bounds for note placement)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Length", 4.0, 0.5, 20.0)
    add_float_param(tree, "Note Count", 16, 4, 64)
    add_float_param(tree, "Staff Scale", 1.0, 0.3, 3.0)
    add_float_param(tree, "Note Size", 1.0, 0.3, 2.0)
    add_bool_param(tree, "Show Clef", True)

    # Staff
    staff_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 500, by + 400))
    staff_line.mode = "END_POINTS"
    staff_line.inputs["Count"].default_value = 2
    link_float_to_vector(tree, gin.outputs["Length"], staff_line, "Start Location", component=0)
    staff_mesh_sock = sweep_profile(
        tree, (bx - 400, by + 350), staff_line.outputs["Mesh"], None,
        profile_res=6, already_curve=False)

    # 5 staff lines arrayed on Y
    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 400, by + 500))
    grid.inputs["Size X"].default_value = 0.0
    grid.inputs["Size Y"].default_value = 0.0
    grid.inputs["Vertices Y"].default_value = 5
    grid.inputs["Vertices X"].default_value = 1

    inst_staff = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 200, by + 500))
    link_sockets(tree, grid.outputs["Mesh"], inst_staff.inputs["Points"])
    link_sockets(tree, staff_mesh_sock, inst_staff.inputs["Instance"])

    realize_staff = safe_node(tree, "GeometryNodeRealizeInstances", (bx, by + 500))
    link_sockets(tree, inst_staff.outputs["Instances"], realize_staff.inputs["Geometry"])

    # Note points along X
    note_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 300, by + 200))
    note_line.mode = "END_POINTS"
    link_sockets(tree, gin.outputs["Note Count"], note_line.inputs["Count"])
    link_float_to_vector(tree, gin.outputs["Length"], note_line, "Start Location", component=0)

    harmonic_grp = _ensure_group_node(tree, "MEL_music_harmonic", build_music_harmonic, (bx - 100, by + 320))
    harmonic_geo = note_line.outputs["Mesh"]
    if harmonic_grp and harmonic_grp.node_tree:
        if harmonic_grp.inputs.get("Geometry"):
            link_sockets(tree, note_line.outputs["Mesh"], harmonic_grp.inputs["Geometry"])
        if harmonic_grp.inputs.get("Note Count"):
            link_sockets(tree, gin.outputs["Note Count"], harmonic_grp.inputs["Note Count"])
        harmonic_geo = harmonic_grp.outputs.get("Geometry") or harmonic_geo

    # Pitch attribute may come from Harmonic Input stack (socket declared above)
    attr = safe_node(tree, "GeometryNodeInputNamedAttribute", (bx - 100, by + 200))
    attr.data_type = "FLOAT"
    try:
        attr.inputs["Name"].default_value = "pitch"
    except Exception:
        pass

    # Position notes: X along line, Z from pitch attribute
    pos = safe_node(tree, "GeometryNodeInputPosition", (bx - 300, by + 100))
    sep = safe_node(tree, "ShaderNodeSeparateXYZ", (bx - 100, by + 100))
    link_sockets(tree, pos.outputs["Position"], sep.inputs["Vector"])

    pitch_mul = safe_node(tree, "ShaderNodeMath", (bx + 100, by + 200))
    pitch_mul.operation = "MULTIPLY"
    link_sockets(tree, attr.outputs["Attribute"], pitch_mul.inputs[0])
    pitch_mul.inputs[1].default_value = 0.15

    combine = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 100, by + 100))
    link_sockets(tree, sep.outputs["X"], combine.inputs["X"])
    link_sockets(tree, pitch_mul.outputs[0], combine.inputs["Z"])

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx + 300, by + 200))
    link_sockets(tree, harmonic_geo, set_pos.inputs["Geometry"])
    link_sockets(tree, combine.outputs["Vector"], set_pos.inputs["Position"])

    # Instance note heads on positioned points (use MEL_music_note_head for proper shape)
    note_head_grp = _ensure_group_node(tree, "MEL_music_note_head", build_music_note_head, (bx - 200, by + 50))
    if note_head_grp and note_head_grp.node_tree:
        try:
            note_head_grp.inputs["Has Stem"].default_value = True
            note_head_grp.inputs["Pitch"].default_value = 0.0
            note_head_grp.inputs["Duration"].default_value = 1.0
            note_head_grp.inputs["Velocity"].default_value = 0.8
        except Exception:
            pass
        # Connect Note Size → Scale
        for sock_name in ("Scale", "size", "scale"):
            scale_in = note_head_grp.inputs.get(sock_name)
            if scale_in:
                link_sockets(tree, gin.outputs["Note Size"], scale_in)
                break

    inst_notes = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 300, by + 50))
    link_sockets(tree, set_pos.outputs["Geometry"], inst_notes.inputs["Points"])
    if note_head_grp and note_head_grp.node_tree:
        geo_out = note_head_grp.outputs.get("Geometry")
        if geo_out:
            link_sockets(tree, geo_out, inst_notes.inputs["Instance"])

    realize_notes = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 500, by + 50))
    link_sockets(tree, inst_notes.outputs["Instances"], realize_notes.inputs["Geometry"])

    # Join staff + notes
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 400, by + 300))
    link_sockets(tree, realize_staff.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, realize_notes.outputs["Geometry"], join.inputs["Geometry"])

    clef_grp = _ensure_group_node(tree, "MEL_music_treble_clef", build_music_treble_clef, (bx + 100, by - 180))
    clef_switch = safe_node(tree, "GeometryNodeSwitch", (bx + 360, by - 180))
    try:
        clef_switch.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Show Clef"], clef_switch.inputs["Switch"])
    if clef_grp and clef_grp.node_tree:
        clef_geo = clef_grp.outputs.get("Geometry")
        if clef_geo:
            link_sockets(tree, clef_geo, _true_socket(clef_switch))
    link_sockets(tree, _output_socket(clef_switch), join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 600, by + 300))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    link_sockets(tree, shade.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(grid, "curve")
    color_node(inst_staff, "instance")
    color_node(realize_staff, "instance")
    color_node(harmonic_grp, "attribute")
    color_node(attr, "attribute")
    color_node(inst_notes, "instance")
    color_node(clef_grp, "curve")
    color_node(clef_switch, "instance")
    color_node(join, "geometry")

    return label_tree(tree, "MEL_music_phrase", [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Staff", "nodes": ("staff", "grid"), "role": "curve"},
        {"title": "Harmonic Pitch", "nodes": ("harmonic", "attribute", "pitch"), "role": "attribute"},
        {"title": "Notes", "nodes": ("note", "instance"), "role": "instance"},
        {"title": "Clef And Output", "nodes": ("clef", "join", "shade", "Group Output"), "role": "output"},
    ])


def build_music_sheet_rail(group_name="MEL_music_sheet_rail"):
    """Walkable staff railing - back-compat alias, canonical build lives in music_heroes.

    Registration for MEL_music_sheet_rail lives in music_heroes.py; do not
    re-register here (register_builder overwrites silently, last import wins).
    """
    from .music_heroes import build_music_sheet_rail as _impl
    return _impl(group_name)


# -- Registry --
from .core import register_builder

register_builder("MEL_music_note_head", build_music_note_head, "Music Note Head",
    "Elliptical note head with stem, flag, and pitch/duration/velocity attributes",
    "music")
register_builder("MEL_music_treble_clef", build_music_treble_clef, "Music Treble Clef",
    "Treble clef glyph - 4 bezier segments merged and tube-swept",
    "music")
register_builder("MEL_music_staff", build_music_staff, "Music Staff",
    "Five-line staff with bar lines and line-index attribute storage",
    "music")
register_builder("MEL_music_harmonic", build_music_harmonic, "Music Harmonic Driver",
    "5-layer additive harmonic pitch driver with fade envelope",
    "music", role="modifier")
register_builder("MEL_music_phrase", build_music_phrase, "Music Phrase (Composite)",
    "Composite musical phrase - staff + note heads + harmonic + clef",
    "music")
