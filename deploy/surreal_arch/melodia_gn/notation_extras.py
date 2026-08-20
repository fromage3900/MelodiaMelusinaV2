"""Musical notation extras — bass clef, beam cluster, triplet, chord stack, fermata,
repeat bar, meter sign, and music stand.

Follows the music.py conventions: XY-plane glyphs swept with a tube profile, uniform
scale applied last, and 1-2 named attributes stored per glyph.

Uses: linear_array (stems/heads/ticks), add (join parts),
      store_attribute (glyph metadata), bounding_box (auto-fit via Scale)
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    make_group_input, register_builder,
)


def _true_socket(node):
    return node.inputs.get("True") or node.inputs.get("TRUE")


def _false_socket(node):
    return node.inputs.get("False") or node.inputs.get("FALSE")


def _output_socket(node):
    return node.outputs.get("Output") or (node.outputs[0] if node and node.outputs else None)


def _profile_circle(tree, bx, by, radius_sock, vertices=8):
    """Tube sweep profile: curve circle (AAA railing) driven by a float socket."""
    circle = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx, by))
    if circle is None:
        circle = safe_node(tree, "GeometryNodeMeshCircle", (bx, by))
        if radius_sock is not None:
            link_sockets(tree, radius_sock, circle.inputs["Radius"])
        try:
            circle.inputs["Vertices"].default_value = vertices
        except Exception:
            pass
        try:
            circle.fill_type = "NGON"
        except Exception:
            pass
        return circle
    if radius_sock is not None:
        link_sockets(tree, radius_sock, circle.inputs["Radius"])
    try:
        if isinstance(vertices, bpy.types.NodeSocket):
            link_sockets(tree, vertices, circle.inputs["Resolution"])
        else:
            circle.inputs["Resolution"].default_value = vertices
    except Exception:
        try:
            if isinstance(vertices, bpy.types.NodeSocket):
                link_sockets(tree, vertices, circle.inputs["Vertices"])
            else:
                circle.inputs["Vertices"].default_value = vertices
        except Exception:
            pass
    return circle


def _profile_out(node):
    return node.outputs.get("Curve") or node.outputs.get("Mesh") or node.outputs[0]


def _sweep(tree, bx, by, curve_sock, profile_sock):
    """Sweep a curve path with a curve profile (AAA railing)."""
    mesh = safe_node(tree, "GeometryNodeCurveToMesh", (bx, by))
    link_sockets(tree, curve_sock, mesh.inputs.get("Curve") or mesh.inputs[0])
    prof = mesh.inputs.get("Profile Curve") or mesh.inputs.get("Profile")
    link_sockets(tree, profile_sock, prof)
    return mesh


def _store_float(tree, bx, by, geo_sock, name, value_sock, data_type="FLOAT"):
    """Store a named attribute with a linked value socket."""
    store = safe_node(tree, "GeometryNodeStoreNamedAttribute", (bx, by))
    link_sockets(tree, geo_sock, store.inputs["Geometry"])
    if value_sock is not None:
        link_sockets(tree, value_sock, store.inputs["Value"])
    store.data_type = data_type
    try:
        store.inputs["Name"].default_value = name
    except Exception:
        pass
    color_node(store, "attribute")
    return store


def _scale_all(tree, gin, bx, by, geo_sock):
    """Uniform Scale applied to a whole glyph before shading."""
    tx = safe_node(tree, "GeometryNodeTransform", (bx, by))
    link_sockets(tree, geo_sock, tx.inputs["Geometry"])
    vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 140, by - 80))
    link_sockets(tree, gin.outputs["Scale"], vec.inputs["X"])
    link_sockets(tree, gin.outputs["Scale"], vec.inputs["Y"])
    link_sockets(tree, gin.outputs["Scale"], vec.inputs["Z"])
    link_sockets(tree, vec.outputs["Vector"], tx.inputs["Scale"])
    return tx


def _note_head(tree, gin, bx, by, scale_sock=None):
    """Flattened, slightly tilted note-head ellipsoid driven by a scale socket."""
    sphere = safe_node(tree, "GeometryNodeMeshUVSphere", (bx, by))
    sphere.inputs["Segments"].default_value = 12
    sphere.inputs["Rings"].default_value = 8
    src = scale_sock if scale_sock is not None else gin.outputs["Scale"]
    sx = safe_node(tree, "ShaderNodeMath", (bx - 140, by + 90))
    sx.operation = "MULTIPLY"
    sx.inputs[1].default_value = 1.2
    link_sockets(tree, src, sx.inputs[0])
    sy = safe_node(tree, "ShaderNodeMath", (bx - 140, by))
    sy.operation = "MULTIPLY"
    sy.inputs[1].default_value = 0.85
    link_sockets(tree, src, sy.inputs[0])
    sz = safe_node(tree, "ShaderNodeMath", (bx - 140, by - 90))
    sz.operation = "MULTIPLY"
    sz.inputs[1].default_value = 0.45
    link_sockets(tree, src, sz.inputs[0])
    vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 40, by - 30))
    link_sockets(tree, sx.outputs[0], vec.inputs["X"])
    link_sockets(tree, sy.outputs[0], vec.inputs["Y"])
    link_sockets(tree, sz.outputs[0], vec.inputs["Z"])
    tx = safe_node(tree, "GeometryNodeTransform", (bx + 160, by))
    link_sockets(tree, sphere.outputs["Mesh"], tx.inputs["Geometry"])
    link_sockets(tree, vec.outputs["Vector"], tx.inputs["Scale"])
    tx.inputs["Rotation"].default_value = (0.0, -0.26, 0.0)
    return tx


def build_music_bass_clef(group_name="MEL_music_bass_clef"):
    """Bass (F) clef glyph — sweeping C-body, bottom curl, vertical tail, two dots.

    Uses: add (join strokes), store_attribute (clef_family)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_float_param(tree, "Thickness", 0.02, 0.006, 0.08)
    add_float_param(tree, "Curl Depth", 0.5, 0.0, 1.0)
    add_float_param(tree, "Dot Size", 0.09, 0.03, 0.25)
    add_float_param(tree, "Tail Length", 1.0, 0.5, 1.5)

    # Body stroke: down through the middle to the curl entry
    body = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx - 500, by + 300))
    body.inputs["Start"].default_value = (-0.16, 0.5, 0.0)
    body.inputs["Start Handle"].default_value = (-0.16, 0.3, 0.0)
    body.inputs["End"].default_value = (0.34, 0.1, 0.0)
    body.inputs["End Handle"].default_value = (0.36, 0.2, 0.0)
    body.inputs["Resolution"].default_value = 12

    # Bottom curl, depth driven by Curl Depth
    curl = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx - 500, by + 100))
    curl.inputs["Start"].default_value = (0.34, 0.1, 0.0)
    curl.inputs["Start Handle"].default_value = (0.48, -0.02, 0.0)
    curl.inputs["End"].default_value = (-0.3, -0.18, 0.0)
    curl_h = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 100))
    curl_h.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Curl Depth"], curl_h.inputs[0])
    curl_h.inputs[1].default_value = 0.25
    curl_neg = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 150))
    curl_neg.operation = "SUBTRACT"
    curl_neg.inputs[0].default_value = -0.2
    link_sockets(tree, curl_h.outputs[0], curl_neg.inputs[1])
    curl_hx = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 520, by + 150))
    link_sockets(tree, curl_neg.outputs[0], curl_hx.inputs["X"])
    curl_hx.inputs["Y"].default_value = -0.32
    link_sockets(tree, curl_hx.outputs["Vector"], curl.inputs["End Handle"])
    curl.inputs["Resolution"].default_value = 12

    # Vertical tail under the curl
    tail = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx - 500, by - 100))
    tail.inputs["Start"].default_value = (-0.3, -0.18, 0.0)
    tail.inputs["Start Handle"].default_value = (-0.3, -0.36, 0.0)
    tail_end_y = safe_node(tree, "ShaderNodeMath", (bx - 700, by - 100))
    tail_end_y.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Tail Length"], tail_end_y.inputs[0])
    tail_end_y.inputs[1].default_value = -0.55
    tail_end = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 520, by - 100))
    tail_end.inputs["X"].default_value = -0.3
    link_sockets(tree, tail_end_y.outputs[0], tail_end.inputs["Y"])
    link_sockets(tree, tail_end.outputs["Vector"], tail.inputs["End"])
    tail_h_y = safe_node(tree, "ShaderNodeMath", (bx - 700, by - 160))
    tail_h_y.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Tail Length"], tail_h_y.inputs[0])
    tail_h_y.inputs[1].default_value = -0.42
    tail_h = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 520, by - 160))
    tail_h.inputs["X"].default_value = -0.3
    link_sockets(tree, tail_h_y.outputs[0], tail_h.inputs["Y"])
    link_sockets(tree, tail_h.outputs["Vector"], tail.inputs["End Handle"])
    tail.inputs["Resolution"].default_value = 8

    # Join strokes, fuse shared endpoints
    join_curves = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 200, by + 200))
    link_sockets(tree, body.outputs["Curve"], join_curves.inputs["Geometry"])
    link_sockets(tree, curl.outputs["Curve"], join_curves.inputs["Geometry"])
    link_sockets(tree, tail.outputs["Curve"], join_curves.inputs["Geometry"])
    merge = safe_node(tree, "GeometryNodeMergeByDistance", (bx, by + 200))
    link_sockets(tree, join_curves.outputs["Geometry"], merge.inputs["Geometry"])
    merge.inputs["Distance"].default_value = 0.001

    profile = _profile_circle(tree, bx - 100, by - 100, gin.outputs["Thickness"])
    clef_mesh = _sweep(tree, bx + 100, by + 200, merge.outputs["Geometry"], _profile_out(profile))

    # Two dots right of the curl
    dot1 = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 300, by - 280))
    dot1.inputs["Segments"].default_value = 10
    dot1.inputs["Rings"].default_value = 6
    link_sockets(tree, gin.outputs["Dot Size"], dot1.inputs["Radius"])
    dot1_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 120, by - 280))
    link_sockets(tree, dot1.outputs["Mesh"], dot1_pos.inputs["Geometry"])
    dot1_pos.inputs["Position"].default_value = (0.46, 0.04, 0.0)
    dot2 = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 300, by - 380))
    dot2.inputs["Segments"].default_value = 10
    dot2.inputs["Rings"].default_value = 6
    link_sockets(tree, gin.outputs["Dot Size"], dot2.inputs["Radius"])
    dot2_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 120, by - 380))
    link_sockets(tree, dot2.outputs["Mesh"], dot2_pos.inputs["Geometry"])
    dot2_pos.inputs["Position"].default_value = (0.46, -0.3, 0.0)

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 300, by + 100))
    link_sockets(tree, clef_mesh.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, dot1_pos.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, dot2_pos.outputs["Geometry"], join.inputs["Geometry"])
    scaled = _scale_all(tree, gin, bx + 420, by + 100, join.outputs["Geometry"])

    family = safe_node(tree, "ShaderNodeMath", (bx + 400, by - 100))
    family.operation = "ADD"
    family.inputs[0].default_value = 2.0
    family.inputs[1].default_value = 0.0

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 600, by + 100))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, scaled.outputs["Geometry"], shade.inputs["Geometry"])
    store = _store_float(tree, bx + 700, by + 100, shade.outputs["Geometry"], "clef_family", family.outputs[0])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(join_curves, "curve")
    color_node(merge, "math")
    color_node(clef_mesh, "geometry")
    color_node(join, "geometry")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "F-Clef Strokes", "nodes": ("bezier", "curl", "tail", "join"), "role": "curve"},
        {"title": "Clef Dots", "nodes": ("dot", "sphere"), "role": "geometry"},
        {"title": "Attribute And Output", "nodes": ("store", "clef_family", "shade", "Group Output"), "role": "output"},
    ])


def build_music_beam_cluster(group_name="MEL_music_beam_cluster"):
    """Eighth-note beam cluster — N note heads on stems joined by a slanted beam.

    Uses: linear_array (stems/heads), add (join parts), store_attribute (beam_span)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Note Count", 4, 2, 8)
    add_float_param(tree, "Spacing", 0.18, 0.05, 0.5)
    add_float_param(tree, "Stem Length", 0.6, 0.2, 1.5)
    add_float_param(tree, "Beam Thickness", 0.035, 0.01, 0.12)
    add_float_param(tree, "Slant", 0.0, -30.0, 30.0)
    add_float_param(tree, "Note Size", 1.0, 0.5, 2.0)

    # Stem placement points along X
    stem_pts = safe_node(tree, "GeometryNodeMeshLine", (bx - 500, by + 400))
    stem_pts.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Note Count"], stem_pts.inputs["Count"])
    link_float_to_vector(tree, gin.outputs["Spacing"], stem_pts, "Offset", component=0, defaults=(0.0, 0.0, 0.0))

    # Stem cylinder rotated to lie along Y
    stem = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 500, by + 200))
    stem.inputs["Radius"].default_value = 0.014
    link_sockets(tree, gin.outputs["Stem Length"], stem.inputs["Depth"])
    stem.inputs["Vertices"].default_value = 8
    stem.fill_type = "NGON"
    stem_rot = safe_node(tree, "GeometryNodeTransform", (bx - 320, by + 200))
    link_sockets(tree, stem.outputs["Mesh"], stem_rot.inputs["Geometry"])
    stem_rot.inputs["Rotation"].default_value = (-math.pi / 2.0, 0.0, 0.0)

    stems = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 140, by + 400))
    link_sockets(tree, stem_pts.outputs["Mesh"], stems.inputs["Points"])
    link_sockets(tree, stem_rot.outputs["Geometry"], stems.inputs["Instance"])

    # Lower stems so their tops meet the beam
    half = safe_node(tree, "ShaderNodeMath", (bx - 320, by + 500))
    half.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Stem Length"], half.inputs[0])
    half.inputs[1].default_value = -0.5
    stem_low = safe_node(tree, "GeometryNodeSetPosition", (bx - 140, by + 560))
    link_sockets(tree, stems.outputs["Instances"], stem_low.inputs["Geometry"])
    link_float_to_vector(tree, half.outputs[0], stem_low, "Offset", component=1, defaults=(0.0, 0.0, 0.0))

    # Note heads at the bottom of the stems
    head_pts = safe_node(tree, "GeometryNodeMeshLine", (bx - 500, by))
    head_pts.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Note Count"], head_pts.inputs["Count"])
    head_y = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 100))
    head_y.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Stem Length"], head_y.inputs[0])
    head_y.inputs[1].default_value = -1.0
    link_float_to_vector(tree, head_y.outputs[0], head_pts, "Start Location", component=1, defaults=(0.0, 0.0, 0.0))
    link_float_to_vector(tree, gin.outputs["Spacing"], head_pts, "Offset", component=0, defaults=(0.0, 0.0, 0.0))

    head = _note_head(tree, gin, bx - 220, by - 120, gin.outputs["Note Size"])
    heads = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 140, by))
    link_sockets(tree, head_pts.outputs["Mesh"], heads.inputs["Points"])
    link_sockets(tree, head.outputs["Geometry"], heads.inputs["Instance"])

    # Beam: flat box spanning the stems, slanted about Z
    count_m1 = safe_node(tree, "ShaderNodeMath", (bx - 400, by - 300))
    count_m1.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Note Count"], count_m1.inputs[0])
    count_m1.inputs[1].default_value = 1.0
    span = safe_node(tree, "ShaderNodeMath", (bx - 200, by - 300))
    span.operation = "MULTIPLY"
    link_sockets(tree, count_m1.outputs[0], span.inputs[0])
    link_sockets(tree, gin.outputs["Spacing"], span.inputs[1])

    beam_z = safe_node(tree, "ShaderNodeMath", (bx - 360, by - 420))
    beam_z.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Beam Thickness"], beam_z.inputs[0])
    beam_z.inputs[1].default_value = 3.0
    beam_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 200, by - 420))
    link_sockets(tree, span.outputs[0], beam_vec.inputs["X"])
    link_sockets(tree, gin.outputs["Beam Thickness"], beam_vec.inputs["Y"])
    link_sockets(tree, beam_z.outputs[0], beam_vec.inputs["Z"])

    beam = safe_node(tree, "GeometryNodeMeshCube", (bx - 320, by - 520))
    link_sockets(tree, beam_vec.outputs["Vector"], beam.inputs["Size"])

    span_half = safe_node(tree, "ShaderNodeMath", (bx - 320, by - 600))
    span_half.operation = "MULTIPLY"
    link_sockets(tree, span.outputs[0], span_half.inputs[0])
    span_half.inputs[1].default_value = 0.5
    beam_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 120, by - 520))
    link_sockets(tree, beam.outputs["Mesh"], beam_pos.inputs["Geometry"])
    link_float_to_vector(tree, span_half.outputs[0], beam_pos, "Position", component=0, defaults=(0.0, 0.0, 0.0))

    slant_rad = safe_node(tree, "ShaderNodeMath", (bx - 40, by - 620))
    slant_rad.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Slant"], slant_rad.inputs[0])
    slant_rad.inputs[1].default_value = math.pi / 180.0
    beam_slant = safe_node(tree, "GeometryNodeTransform", (bx + 80, by - 520))
    link_sockets(tree, beam_pos.outputs["Geometry"], beam_slant.inputs["Geometry"])
    link_float_to_vector(tree, slant_rad.outputs[0], beam_slant, "Rotation", component=2, defaults=(0.0, 0.0, 0.0))

    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 260, by + 400))
    link_sockets(tree, stem_low.outputs["Geometry"], realize.inputs["Geometry"])
    heads_real = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 260, by + 200))
    link_sockets(tree, heads.outputs["Instances"], heads_real.inputs["Geometry"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 440, by + 300))
    link_sockets(tree, realize.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, heads_real.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, beam_slant.outputs["Geometry"], join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 620, by + 300))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    store = _store_float(tree, bx + 720, by + 300, shade.outputs["Geometry"], "beam_span", span.outputs[0])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(stem_pts, "curve")
    color_node(stems, "instance")
    color_node(heads, "instance")
    color_node(beam, "geometry")
    color_node(realize, "instance")
    color_node(join, "geometry")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Stems And Heads", "nodes": ("mesh line", "cylinder", "instance"), "role": "instance"},
        {"title": "Beam", "nodes": ("beam", "span", "slant"), "role": "geometry"},
        {"title": "Attribute And Output", "nodes": ("store", "shade", "Group Output"), "role": "output"},
    ])


def build_music_triplet_note(group_name="MEL_music_triplet_note"):
    """Triplet note — three beamed eighth notes with an optional double beam.

    Uses: linear_array (three stems/heads), add (join parts), store_attribute (tuplet_value)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Spacing", 0.22, 0.05, 0.5)
    add_float_param(tree, "Stem Length", 0.6, 0.2, 1.5)
    add_float_param(tree, "Beam Thickness", 0.035, 0.01, 0.12)
    add_float_param(tree, "Slant", 0.0, -30.0, 30.0)
    add_float_param(tree, "Note Size", 1.0, 0.5, 2.0)
    add_bool_param(tree, "Double Beam", True)

    # Three stems along X
    stem_pts = safe_node(tree, "GeometryNodeMeshLine", (bx - 500, by + 400))
    stem_pts.mode = "OFFSET"
    stem_pts.inputs["Count"].default_value = 3
    link_float_to_vector(tree, gin.outputs["Spacing"], stem_pts, "Offset", component=0, defaults=(0.0, 0.0, 0.0))

    stem = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 500, by + 200))
    stem.inputs["Radius"].default_value = 0.014
    link_sockets(tree, gin.outputs["Stem Length"], stem.inputs["Depth"])
    stem.inputs["Vertices"].default_value = 8
    stem.fill_type = "NGON"
    stem_rot = safe_node(tree, "GeometryNodeTransform", (bx - 320, by + 200))
    link_sockets(tree, stem.outputs["Mesh"], stem_rot.inputs["Geometry"])
    stem_rot.inputs["Rotation"].default_value = (-math.pi / 2.0, 0.0, 0.0)

    stems = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 140, by + 400))
    link_sockets(tree, stem_pts.outputs["Mesh"], stems.inputs["Points"])
    link_sockets(tree, stem_rot.outputs["Geometry"], stems.inputs["Instance"])

    half = safe_node(tree, "ShaderNodeMath", (bx - 320, by + 500))
    half.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Stem Length"], half.inputs[0])
    half.inputs[1].default_value = -0.5
    stem_low = safe_node(tree, "GeometryNodeSetPosition", (bx - 140, by + 560))
    link_sockets(tree, stems.outputs["Instances"], stem_low.inputs["Geometry"])
    link_float_to_vector(tree, half.outputs[0], stem_low, "Offset", component=1, defaults=(0.0, 0.0, 0.0))

    head_pts = safe_node(tree, "GeometryNodeMeshLine", (bx - 500, by))
    head_pts.mode = "OFFSET"
    head_pts.inputs["Count"].default_value = 3
    head_y = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 100))
    head_y.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Stem Length"], head_y.inputs[0])
    head_y.inputs[1].default_value = -1.0
    link_float_to_vector(tree, head_y.outputs[0], head_pts, "Start Location", component=1, defaults=(0.0, 0.0, 0.0))
    link_float_to_vector(tree, gin.outputs["Spacing"], head_pts, "Offset", component=0, defaults=(0.0, 0.0, 0.0))

    head = _note_head(tree, gin, bx - 220, by - 120, gin.outputs["Note Size"])
    heads = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 140, by))
    link_sockets(tree, head_pts.outputs["Mesh"], heads.inputs["Points"])
    link_sockets(tree, head.outputs["Geometry"], heads.inputs["Instance"])

    # Main beam
    span_two = safe_node(tree, "ShaderNodeMath", (bx - 300, by - 300))
    span_two.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Spacing"], span_two.inputs[0])
    span_two.inputs[1].default_value = 2.0
    beam_z = safe_node(tree, "ShaderNodeMath", (bx - 380, by - 420))
    beam_z.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Beam Thickness"], beam_z.inputs[0])
    beam_z.inputs[1].default_value = 3.0
    beam_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 200, by - 420))
    link_sockets(tree, span_two.outputs[0], beam_vec.inputs["X"])
    link_sockets(tree, gin.outputs["Beam Thickness"], beam_vec.inputs["Y"])
    link_sockets(tree, beam_z.outputs[0], beam_vec.inputs["Z"])

    beam = safe_node(tree, "GeometryNodeMeshCube", (bx - 320, by - 520))
    link_sockets(tree, beam_vec.outputs["Vector"], beam.inputs["Size"])
    beam_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 120, by - 520))
    link_sockets(tree, beam.outputs["Mesh"], beam_pos.inputs["Geometry"])
    link_float_to_vector(tree, gin.outputs["Spacing"], beam_pos, "Position", component=0, defaults=(0.0, 0.0, 0.0))

    slant_rad = safe_node(tree, "ShaderNodeMath", (bx - 40, by - 620))
    slant_rad.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Slant"], slant_rad.inputs[0])
    slant_rad.inputs[1].default_value = math.pi / 180.0
    beam_slant = safe_node(tree, "GeometryNodeTransform", (bx + 80, by - 520))
    link_sockets(tree, beam_pos.outputs["Geometry"], beam_slant.inputs["Geometry"])
    link_float_to_vector(tree, slant_rad.outputs[0], beam_slant, "Rotation", component=2, defaults=(0.0, 0.0, 0.0))

    # Optional second beam stacked above
    beam2_y = safe_node(tree, "ShaderNodeMath", (bx - 100, by - 700))
    beam2_y.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Beam Thickness"], beam2_y.inputs[0])
    beam2_y.inputs[1].default_value = 1.8
    beam2_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx + 60, by - 700))
    link_sockets(tree, span_two.outputs[0], beam2_vec.inputs["X"])
    link_sockets(tree, beam2_y.outputs[0], beam2_vec.inputs["Y"])
    link_sockets(tree, beam_z.outputs[0], beam2_vec.inputs["Z"])
    beam2 = safe_node(tree, "GeometryNodeMeshCube", (bx + 60, by - 800))
    link_sockets(tree, beam2_vec.outputs["Vector"], beam2.inputs["Size"])
    beam2_sw = safe_node(tree, "GeometryNodeSwitch", (bx + 220, by - 800))
    try:
        beam2_sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Double Beam"], beam2_sw.inputs["Switch"])
    link_sockets(tree, beam2.outputs["Mesh"], _true_socket(beam2_sw))

    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 260, by + 400))
    link_sockets(tree, stem_low.outputs["Geometry"], realize.inputs["Geometry"])
    heads_real = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 260, by + 200))
    link_sockets(tree, heads.outputs["Instances"], heads_real.inputs["Geometry"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 440, by + 300))
    link_sockets(tree, realize.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, heads_real.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, beam_slant.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, _output_socket(beam2_sw), join.inputs["Geometry"])

    tuplet = safe_node(tree, "ShaderNodeMath", (bx + 520, by + 500))
    tuplet.operation = "ADD"
    tuplet.inputs[0].default_value = 3.0
    tuplet.inputs[1].default_value = 0.0

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 620, by + 300))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    store = _store_float(tree, bx + 720, by + 300, shade.outputs["Geometry"], "tuplet_value", tuplet.outputs[0])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(stem_pts, "curve")
    color_node(stems, "instance")
    color_node(heads, "instance")
    color_node(beam, "geometry")
    color_node(beam2_sw, "instance")
    color_node(join, "geometry")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Triplet Stems And Heads", "nodes": ("mesh line", "cylinder", "instance"), "role": "instance"},
        {"title": "Beams", "nodes": ("beam", "slant", "switch"), "role": "geometry"},
        {"title": "Attribute And Output", "nodes": ("store", "tuplet", "shade", "Group Output"), "role": "output"},
    ])


def build_music_chord_stack(group_name="MEL_music_chord_stack"):
    """Chord stack — note heads piled vertically on a shared stem.

    Uses: linear_array (stacked heads), add (join), store_attribute (chord_size)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Chord Size", 3, 2, 8)
    add_float_param(tree, "Spread", 0.14, 0.05, 0.4)
    add_float_param(tree, "Note Size", 1.0, 0.5, 2.0)
    add_float_param(tree, "Stem Length", 0.8, 0.2, 2.0)
    add_float_param(tree, "Stem Offset", 0.45, 0.2, 1.0)

    count_m1 = safe_node(tree, "ShaderNodeMath", (bx - 500, by + 300))
    count_m1.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Chord Size"], count_m1.inputs[0])
    count_m1.inputs[1].default_value = 1.0
    half_span = safe_node(tree, "ShaderNodeMath", (bx - 320, by + 300))
    half_span.operation = "MULTIPLY"
    link_sockets(tree, count_m1.outputs[0], half_span.inputs[0])
    link_sockets(tree, gin.outputs["Spread"], half_span.inputs[1])
    neg_half = safe_node(tree, "ShaderNodeMath", (bx - 500, by + 200))
    neg_half.operation = "MULTIPLY"
    link_sockets(tree, half_span.outputs[0], neg_half.inputs[0])
    neg_half.inputs[1].default_value = -0.5

    stack_pts = safe_node(tree, "GeometryNodeMeshLine", (bx - 500, by + 100))
    stack_pts.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Chord Size"], stack_pts.inputs["Count"])
    link_float_to_vector(tree, neg_half.outputs[0], stack_pts, "Start Location", component=1, defaults=(0.0, 0.0, 0.0))
    link_float_to_vector(tree, gin.outputs["Spread"], stack_pts, "Offset", component=1, defaults=(0.0, 0.0, 0.0))

    head = _note_head(tree, gin, bx - 320, by - 100, gin.outputs["Note Size"])
    heads = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 140, by + 100))
    link_sockets(tree, stack_pts.outputs["Mesh"], heads.inputs["Points"])
    link_sockets(tree, head.outputs["Geometry"], heads.inputs["Instance"])

    stem_z = safe_node(tree, "ShaderNodeMath", (bx - 380, by - 200))
    stem_z.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Note Size"], stem_z.inputs[0])
    stem_z.inputs[1].default_value = 0.4
    stem_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 200, by - 200))
    stem_vec.inputs["X"].default_value = 0.035
    link_sockets(tree, gin.outputs["Stem Length"], stem_vec.inputs["Y"])
    link_sockets(tree, stem_z.outputs[0], stem_vec.inputs["Z"])
    stem = safe_node(tree, "GeometryNodeMeshCube", (bx - 320, by - 300))
    link_sockets(tree, stem_vec.outputs["Vector"], stem.inputs["Size"])
    stem_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 120, by - 300))
    link_sockets(tree, stem.outputs["Mesh"], stem_pos.inputs["Geometry"])
    link_float_to_vector(tree, gin.outputs["Stem Offset"], stem_pos, "Position", component=0, defaults=(0.0, 0.0, 0.0))

    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 120, by + 100))
    link_sockets(tree, heads.outputs["Instances"], realize.inputs["Geometry"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 320, by + 100))
    link_sockets(tree, realize.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, stem_pos.outputs["Geometry"], join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 500, by + 100))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    store = _store_float(tree, bx + 600, by + 100, shade.outputs["Geometry"], "chord_size", gin.outputs["Chord Size"], "INT")
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(stack_pts, "curve")
    color_node(heads, "instance")
    color_node(stem, "geometry")
    color_node(realize, "instance")
    color_node(join, "geometry")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Stacked Heads", "nodes": ("stack", "mesh line", "instance"), "role": "instance"},
        {"title": "Shared Stem", "nodes": ("stem", "cube"), "role": "geometry"},
        {"title": "Attribute And Output", "nodes": ("store", "shade", "Group Output"), "role": "output"},
    ])


def build_music_fermata(group_name="MEL_music_fermata"):
    """Fermata (hold) mark — arc over a short base line with an optional center dot.

    Uses: add (join strokes), store_attribute (fermata_span)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_float_param(tree, "Radius", 0.55, 0.2, 1.5)
    add_float_param(tree, "Arc Height", 1.0, 0.5, 1.5)
    add_float_param(tree, "Thickness", 0.02, 0.006, 0.08)
    add_float_param(tree, "Dot Size", 0.1, 0.03, 0.3)
    add_bool_param(tree, "Has Dot", True)

    # Semicircular arc with handles at 4/3 the arc height
    r_neg = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 300))
    r_neg.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Radius"], r_neg.inputs[0])
    r_neg.inputs[1].default_value = -1.0
    h_r = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 200))
    h_r.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Radius"], h_r.inputs[0])
    link_sockets(tree, gin.outputs["Arc Height"], h_r.inputs[1])
    h_scale = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 100))
    h_scale.operation = "MULTIPLY"
    link_sockets(tree, h_r.outputs[0], h_scale.inputs[0])
    h_scale.inputs[1].default_value = 1.3333

    arc_start = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 500, by + 300))
    link_sockets(tree, r_neg.outputs[0], arc_start.inputs["X"])
    arc_end = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 500, by + 200))
    link_sockets(tree, gin.outputs["Radius"], arc_end.inputs["X"])
    hx_neg = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 320, by + 300))
    link_sockets(tree, r_neg.outputs[0], hx_neg.inputs["X"])
    link_sockets(tree, h_scale.outputs[0], hx_neg.inputs["Y"])
    hx_pos = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 320, by + 200))
    link_sockets(tree, gin.outputs["Radius"], hx_pos.inputs["X"])
    link_sockets(tree, h_scale.outputs[0], hx_pos.inputs["Y"])

    arc = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx - 160, by + 250))
    link_sockets(tree, arc_start.outputs["Vector"], arc.inputs["Start"])
    link_sockets(tree, hx_neg.outputs["Vector"], arc.inputs["Start Handle"])
    link_sockets(tree, arc_end.outputs["Vector"], arc.inputs["End"])
    link_sockets(tree, hx_pos.outputs["Vector"], arc.inputs["End Handle"])
    arc.inputs["Resolution"].default_value = 12

    # Short base line below the arc
    b_neg = safe_node(tree, "ShaderNodeMath", (bx - 560, by))
    b_neg.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Radius"], b_neg.inputs[0])
    b_neg.inputs[1].default_value = -1.15
    b_pos = safe_node(tree, "ShaderNodeMath", (bx - 560, by - 100))
    b_pos.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Radius"], b_pos.inputs[0])
    b_pos.inputs[1].default_value = 1.15
    b_y = safe_node(tree, "ShaderNodeMath", (bx - 560, by - 200))
    b_y.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Radius"], b_y.inputs[0])
    b_y.inputs[1].default_value = -0.15
    base_s = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 380, by))
    link_sockets(tree, b_neg.outputs[0], base_s.inputs["X"])
    link_sockets(tree, b_y.outputs[0], base_s.inputs["Y"])
    base_e = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 380, by - 100))
    link_sockets(tree, b_pos.outputs[0], base_e.inputs["X"])
    link_sockets(tree, b_y.outputs[0], base_e.inputs["Y"])
    base = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx - 200, by - 50))
    link_sockets(tree, base_s.outputs["Vector"], base.inputs["Start"])
    link_sockets(tree, base_e.outputs["Vector"], base.inputs["End"])
    base.inputs["Resolution"].default_value = 4

    join_curves = safe_node(tree, "GeometryNodeJoinGeometry", (bx, by + 150))
    link_sockets(tree, arc.outputs["Curve"], join_curves.inputs["Geometry"])
    link_sockets(tree, base.outputs["Curve"], join_curves.inputs["Geometry"])
    merge = safe_node(tree, "GeometryNodeMergeByDistance", (bx + 160, by + 150))
    link_sockets(tree, join_curves.outputs["Geometry"], merge.inputs["Geometry"])
    merge.inputs["Distance"].default_value = 0.001

    profile = _profile_circle(tree, bx - 100, by - 300, gin.outputs["Thickness"])
    fer_mesh = _sweep(tree, bx + 260, by + 150, merge.outputs["Geometry"], _profile_out(profile))

    # Center dot
    dot = safe_node(tree, "GeometryNodeMeshUVSphere", (bx, by - 320))
    dot.inputs["Segments"].default_value = 10
    dot.inputs["Rings"].default_value = 6
    link_sockets(tree, gin.outputs["Dot Size"], dot.inputs["Radius"])
    dot_y = safe_node(tree, "ShaderNodeMath", (bx - 200, by - 320))
    dot_y.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Radius"], dot_y.inputs[0])
    dot_y.inputs[1].default_value = -0.55
    dot_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 60, by - 320))
    link_sockets(tree, dot.outputs["Mesh"], dot_pos.inputs["Geometry"])
    link_float_to_vector(tree, dot_y.outputs[0], dot_pos, "Position", component=1, defaults=(0.0, 0.0, 0.0))
    dot_sw = safe_node(tree, "GeometryNodeSwitch", (bx + 100, by - 320))
    try:
        dot_sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Has Dot"], dot_sw.inputs["Switch"])
    link_sockets(tree, dot_pos.outputs["Geometry"], _true_socket(dot_sw))

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 420, by + 100))
    link_sockets(tree, fer_mesh.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, _output_socket(dot_sw), join.inputs["Geometry"])
    scaled = _scale_all(tree, gin, bx + 540, by + 100, join.outputs["Geometry"])

    span = safe_node(tree, "ShaderNodeMath", (bx + 520, by - 100))
    span.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Radius"], span.inputs[0])
    span.inputs[1].default_value = 2.0

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 700, by + 100))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, scaled.outputs["Geometry"], shade.inputs["Geometry"])
    store = _store_float(tree, bx + 800, by + 100, shade.outputs["Geometry"], "fermata_span", span.outputs[0])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(join_curves, "curve")
    color_node(merge, "math")
    color_node(fer_mesh, "geometry")
    color_node(dot_sw, "instance")
    color_node(join, "geometry")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Fermata Arc", "nodes": ("bezier", "arc", "base", "join"), "role": "curve"},
        {"title": "Dot", "nodes": ("dot", "sphere", "switch"), "role": "geometry"},
        {"title": "Attribute And Output", "nodes": ("store", "shade", "Group Output"), "role": "output"},
    ])


def build_music_repeat_bar(group_name="MEL_music_repeat_bar"):
    """Repeat-bar sign — double thick bars with two dots beside them.

    Uses: add (join bars + dots), store_attribute (repeat_count)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_float_param(tree, "Height", 1.2, 0.4, 2.5)
    add_float_param(tree, "Bar Thickness", 0.09, 0.03, 0.3)
    add_float_param(tree, "Gap", 0.12, 0.04, 0.5)
    add_float_param(tree, "Dot Size", 0.1, 0.03, 0.35)

    # Left and right thick bars
    bar_z = safe_node(tree, "ShaderNodeMath", (bx - 580, by + 300))
    bar_z.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Height"], bar_z.inputs[0])
    bar_z.inputs[1].default_value = 0.12
    bar_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 400, by + 300))
    link_sockets(tree, gin.outputs["Bar Thickness"], bar_vec.inputs["X"])
    link_sockets(tree, gin.outputs["Height"], bar_vec.inputs["Y"])
    link_sockets(tree, bar_z.outputs[0], bar_vec.inputs["Z"])

    bar1 = safe_node(tree, "GeometryNodeMeshCube", (bx - 300, by + 200))
    link_sockets(tree, bar_vec.outputs["Vector"], bar1.inputs["Size"])
    bar2 = safe_node(tree, "GeometryNodeMeshCube", (bx - 300, by + 100))
    link_sockets(tree, bar_vec.outputs["Vector"], bar2.inputs["Size"])

    off = safe_node(tree, "ShaderNodeMath", (bx - 480, by + 100))
    off.operation = "ADD"
    link_sockets(tree, gin.outputs["Gap"], off.inputs[0])
    link_sockets(tree, gin.outputs["Bar Thickness"], off.inputs[1])
    off_neg = safe_node(tree, "ShaderNodeMath", (bx - 480, by))
    off_neg.operation = "MULTIPLY"
    link_sockets(tree, off.outputs[0], off_neg.inputs[0])
    off_neg.inputs[1].default_value = -0.5
    pos1 = safe_node(tree, "GeometryNodeSetPosition", (bx - 140, by + 200))
    link_sockets(tree, bar1.outputs["Mesh"], pos1.inputs["Geometry"])
    link_float_to_vector(tree, off_neg.outputs[0], pos1, "Position", component=0, defaults=(0.0, 0.0, 0.0))
    pos2 = safe_node(tree, "GeometryNodeSetPosition", (bx - 140, by + 100))
    link_sockets(tree, bar2.outputs["Mesh"], pos2.inputs["Geometry"])
    link_float_to_vector(tree, off.outputs[0], pos2, "Position", component=0, defaults=(0.0, 0.0, 0.0))

    # Two dots beside the bars
    dot_off = safe_node(tree, "ShaderNodeMath", (bx - 480, by - 200))
    dot_off.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Gap"], dot_off.inputs[0])
    dot_off.inputs[1].default_value = -1.7
    dot_y = safe_node(tree, "ShaderNodeMath", (bx - 480, by - 300))
    dot_y.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Height"], dot_y.inputs[0])
    dot_y.inputs[1].default_value = 0.28
    dot_ny = safe_node(tree, "ShaderNodeMath", (bx - 480, by - 400))
    dot_ny.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Height"], dot_ny.inputs[0])
    dot_ny.inputs[1].default_value = -0.28
    dot_geo = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 320, by - 250))
    dot_geo.inputs["Segments"].default_value = 10
    dot_geo.inputs["Rings"].default_value = 6
    link_sockets(tree, gin.outputs["Dot Size"], dot_geo.inputs["Radius"])
    dot1 = safe_node(tree, "GeometryNodeSetPosition", (bx - 160, by - 250))
    link_sockets(tree, dot_geo.outputs["Mesh"], dot1.inputs["Geometry"])
    link_float_to_vector(tree, dot_off.outputs[0], dot1, "Position", component=0, defaults=(0.0, 0.0, 0.0))
    link_float_to_vector(tree, dot_y.outputs[0], dot1, "Position", component=1, defaults=(0.0, 0.0, 0.0))
    dot2 = safe_node(tree, "GeometryNodeSetPosition", (bx - 160, by - 350))
    link_sockets(tree, dot_geo.outputs["Mesh"], dot2.inputs["Geometry"])
    link_float_to_vector(tree, dot_off.outputs[0], dot2, "Position", component=0, defaults=(0.0, 0.0, 0.0))
    link_float_to_vector(tree, dot_ny.outputs[0], dot2, "Position", component=1, defaults=(0.0, 0.0, 0.0))

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 120, by + 100))
    link_sockets(tree, pos1.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, pos2.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, dot1.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, dot2.outputs["Geometry"], join.inputs["Geometry"])
    scaled = _scale_all(tree, gin, bx + 260, by + 100, join.outputs["Geometry"])

    count = safe_node(tree, "ShaderNodeMath", (bx + 240, by - 100))
    count.operation = "ADD"
    count.inputs[0].default_value = 2.0
    count.inputs[1].default_value = 0.0

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 420, by + 100))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, scaled.outputs["Geometry"], shade.inputs["Geometry"])
    store = _store_float(tree, bx + 520, by + 100, shade.outputs["Geometry"], "repeat_count", count.outputs[0])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(bar1, "geometry")
    color_node(bar2, "geometry")
    color_node(dot_geo, "geometry")
    color_node(join, "geometry")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Double Bars", "nodes": ("cube", "bar", "position"), "role": "geometry"},
        {"title": "Repeat Dots", "nodes": ("dot", "sphere"), "role": "geometry"},
        {"title": "Attribute And Output", "nodes": ("store", "shade", "Group Output"), "role": "output"},
    ])


def build_music_time_signature(group_name="MEL_music_time_signature"):
    """Meter sign — bold C (common time), optionally struck by a slash (cut time).

    Uses: add (join arc halves), store_attribute (meter_beats)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Radius", 0.5, 0.2, 1.2)
    add_float_param(tree, "Thickness", 0.02, 0.006, 0.08)
    add_float_param(tree, "Beats", 4.0, 1.0, 16.0)
    add_bool_param(tree, "Cut Time", False)
    add_int_param(tree, "Resolution", 12, 4, 32)

    # Arc halves of the C glyph (right half of a circle)
    r_neg = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 300))
    r_neg.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Radius"], r_neg.inputs[0])
    r_neg.inputs[1].default_value = -1.0
    k_neg = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 200))
    k_neg.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Radius"], k_neg.inputs[0])
    k_neg.inputs[1].default_value = -0.5523
    k_pos = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 100))
    k_pos.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Radius"], k_pos.inputs[0])
    k_pos.inputs[1].default_value = 0.5523

    a1s = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 500, by + 300))
    a1s.inputs["Y"].default_value = 0.0
    link_sockets(tree, gin.outputs["Radius"], a1s.inputs["Y"])
    a1e = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 500, by + 200))
    link_sockets(tree, gin.outputs["Radius"], a1e.inputs["X"])
    a1h1 = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 320, by + 300))
    link_sockets(tree, k_neg.outputs[0], a1h1.inputs["X"])
    link_sockets(tree, gin.outputs["Radius"], a1h1.inputs["Y"])
    a1h2 = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 320, by + 200))
    link_sockets(tree, gin.outputs["Radius"], a1h2.inputs["X"])
    link_sockets(tree, k_pos.outputs[0], a1h2.inputs["Y"])

    arc1 = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx - 160, by + 250))
    link_sockets(tree, a1s.outputs["Vector"], arc1.inputs["Start"])
    link_sockets(tree, a1h1.outputs["Vector"], arc1.inputs["Start Handle"])
    link_sockets(tree, a1e.outputs["Vector"], arc1.inputs["End"])
    link_sockets(tree, a1h2.outputs["Vector"], arc1.inputs["End Handle"])
    arc1.inputs["Resolution"].default_value = 12

    a2e = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 500, by))
    a2e.inputs["Y"].default_value = 0.0
    link_sockets(tree, r_neg.outputs[0], a2e.inputs["Y"])
    a2h1 = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 320, by))
    link_sockets(tree, gin.outputs["Radius"], a2h1.inputs["X"])
    link_sockets(tree, k_pos.outputs[0], a2h1.inputs["Y"])
    a2h2 = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 320, by - 100))
    link_sockets(tree, k_pos.outputs[0], a2h2.inputs["X"])
    link_sockets(tree, r_neg.outputs[0], a2h2.inputs["Y"])

    arc2 = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx - 160, by + 100))
    link_sockets(tree, a1e.outputs["Vector"], arc2.inputs["Start"])
    link_sockets(tree, a2h1.outputs["Vector"], arc2.inputs["Start Handle"])
    link_sockets(tree, a2e.outputs["Vector"], arc2.inputs["End"])
    link_sockets(tree, a2h2.outputs["Vector"], arc2.inputs["End Handle"])
    arc2.inputs["Resolution"].default_value = 12

    # Optional diagonal slash for cut time
    s_s = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 500, by - 200))
    s_s_x = safe_node(tree, "ShaderNodeMath", (bx - 680, by - 200))
    s_s_x.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Radius"], s_s_x.inputs[0])
    s_s_x.inputs[1].default_value = -0.5
    s_s_y = safe_node(tree, "ShaderNodeMath", (bx - 680, by - 280))
    s_s_y.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Radius"], s_s_y.inputs[0])
    s_s_y.inputs[1].default_value = 0.55
    link_sockets(tree, s_s_x.outputs[0], s_s.inputs["X"])
    link_sockets(tree, s_s_y.outputs[0], s_s.inputs["Y"])
    s_e = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 500, by - 320))
    s_e_x = safe_node(tree, "ShaderNodeMath", (bx - 680, by - 380))
    s_e_x.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Radius"], s_e_x.inputs[0])
    s_e_x.inputs[1].default_value = 0.5
    s_e_y = safe_node(tree, "ShaderNodeMath", (bx - 680, by - 460))
    s_e_y.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Radius"], s_e_y.inputs[0])
    s_e_y.inputs[1].default_value = -0.55
    link_sockets(tree, s_e_x.outputs[0], s_e.inputs["X"])
    link_sockets(tree, s_e_y.outputs[0], s_e.inputs["Y"])
    slash = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx - 300, by - 250))
    link_sockets(tree, s_s.outputs["Vector"], slash.inputs["Start"])
    link_sockets(tree, s_e.outputs["Vector"], slash.inputs["End"])
    slash.inputs["Resolution"].default_value = 8
    slash_sw = safe_node(tree, "GeometryNodeSwitch", (bx - 120, by - 250))
    try:
        slash_sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, gin.outputs["Cut Time"], slash_sw.inputs["Switch"])
    link_sockets(tree, slash.outputs["Curve"], _true_socket(slash_sw))

    join_curves = safe_node(tree, "GeometryNodeJoinGeometry", (bx, by + 200))
    link_sockets(tree, arc1.outputs["Curve"], join_curves.inputs["Geometry"])
    link_sockets(tree, arc2.outputs["Curve"], join_curves.inputs["Geometry"])
    link_sockets(tree, _output_socket(slash_sw), join_curves.inputs["Geometry"])
    merge = safe_node(tree, "GeometryNodeMergeByDistance", (bx + 160, by + 200))
    link_sockets(tree, join_curves.outputs["Geometry"], merge.inputs["Geometry"])
    merge.inputs["Distance"].default_value = 0.001

    profile = _profile_circle(tree, bx - 100, by - 500, gin.outputs["Thickness"])
    meter_mesh = _sweep(tree, bx + 260, by + 200, merge.outputs["Geometry"], _profile_out(profile))

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 420, by + 200))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, meter_mesh.outputs["Mesh"], shade.inputs["Geometry"])
    store = _store_float(tree, bx + 520, by + 200, shade.outputs["Geometry"], "meter_beats", gin.outputs["Beats"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(join_curves, "curve")
    color_node(merge, "math")
    color_node(meter_mesh, "geometry")
    color_node(slash_sw, "instance")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Meter Arc", "nodes": ("arc", "bezier", "merge"), "role": "curve"},
        {"title": "Cut Slash", "nodes": ("slash", "switch"), "role": "geometry"},
        {"title": "Attribute And Output", "nodes": ("store", "shade", "Group Output"), "role": "output"},
    ])


def build_music_stand(group_name="MEL_music_stand"):
    """Music stand — angled panel, center pole, and two splayed legs.

    Uses: add (join parts), store_attribute (stand_height)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Panel Width", 1.4, 0.4, 3.0)
    add_float_param(tree, "Panel Height", 0.9, 0.3, 2.0)
    add_float_param(tree, "Panel Thickness", 0.05, 0.01, 0.2)
    add_float_param(tree, "Stand Height", 1.2, 0.5, 2.5)
    add_float_param(tree, "Lean", 60.0, 0.0, 80.0)
    add_float_param(tree, "Leg Spread", 35.0, 5.0, 70.0)
    add_float_param(tree, "Scale", 1.0, 0.5, 2.0)

    # Panel: thin box tilted back about X
    panel = safe_node(tree, "GeometryNodeMeshCube", (bx - 500, by + 300))
    panel_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 700, by + 300))
    link_sockets(tree, gin.outputs["Panel Width"], panel_vec.inputs["X"])
    link_sockets(tree, gin.outputs["Panel Height"], panel_vec.inputs["Y"])
    link_sockets(tree, gin.outputs["Panel Thickness"], panel_vec.inputs["Z"])
    link_sockets(tree, panel_vec.outputs["Vector"], panel.inputs["Size"])
    panel_y = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 200))
    panel_y.operation = "ADD"
    link_sockets(tree, gin.outputs["Stand Height"], panel_y.inputs[0])
    panel_half = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 120))
    panel_half.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Panel Height"], panel_half.inputs[0])
    panel_half.inputs[1].default_value = 0.45
    link_sockets(tree, panel_half.outputs[0], panel_y.inputs[1])
    lean_rad = safe_node(tree, "ShaderNodeMath", (bx - 700, by))
    lean_rad.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Lean"], lean_rad.inputs[0])
    lean_rad.inputs[1].default_value = math.pi / 180.0
    panel_rot = safe_node(tree, "GeometryNodeTransform", (bx - 320, by + 300))
    link_sockets(tree, panel.outputs["Mesh"], panel_rot.inputs["Geometry"])
    link_float_to_vector(tree, lean_rad.outputs[0], panel_rot, "Rotation", component=0, defaults=(0.0, 0.0, 0.0))
    link_float_to_vector(tree, panel_y.outputs[0], panel_rot, "Translation", component=1, defaults=(0.0, 0.0, 0.0))

    # Center pole
    pole = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 500, by))
    pole.inputs["Radius"].default_value = 0.045
    link_sockets(tree, gin.outputs["Stand Height"], pole.inputs["Depth"])
    pole.inputs["Vertices"].default_value = 12
    pole.fill_type = "NGON"
    pole_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 320, by))
    link_sockets(tree, pole.outputs["Mesh"], pole_pos.inputs["Geometry"])
    pole_y = safe_node(tree, "ShaderNodeMath", (bx - 480, by - 120))
    pole_y.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Stand Height"], pole_y.inputs[0])
    pole_y.inputs[1].default_value = 0.5
    link_float_to_vector(tree, pole_y.outputs[0], pole_pos, "Position", component=1, defaults=(0.0, 0.0, 0.0))

    # Two splayed legs
    spread_rad = safe_node(tree, "ShaderNodeMath", (bx - 480, by - 240))
    spread_rad.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Leg Spread"], spread_rad.inputs[0])
    spread_rad.inputs[1].default_value = math.pi / 180.0
    leg = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 500, by - 360))
    leg.inputs["Radius"].default_value = 0.03
    leg_len = safe_node(tree, "ShaderNodeMath", (bx - 700, by - 360))
    leg_len.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Stand Height"], leg_len.inputs[0])
    leg_len.inputs[1].default_value = 0.55
    link_sockets(tree, leg_len.outputs[0], leg.inputs["Depth"])
    leg.inputs["Vertices"].default_value = 10
    leg.fill_type = "NGON"
    leg_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 320, by - 360))
    link_sockets(tree, leg.outputs["Mesh"], leg_pos.inputs["Geometry"])
    leg_y = safe_node(tree, "ShaderNodeMath", (bx - 480, by - 460))
    leg_y.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Stand Height"], leg_y.inputs[0])
    leg_y.inputs[1].default_value = 0.22
    link_float_to_vector(tree, leg_y.outputs[0], leg_pos, "Position", component=1, defaults=(0.0, 0.0, 0.0))
    leg_neg = safe_node(tree, "GeometryNodeTransform", (bx - 140, by - 360))
    link_sockets(tree, leg_pos.outputs["Geometry"], leg_neg.inputs["Geometry"])
    link_float_to_vector(tree, spread_rad.outputs[0], leg_neg, "Rotation", component=2, defaults=(0.0, 0.0, 0.0))
    leg_mirror = safe_node(tree, "GeometryNodeTransform", (bx + 160, by - 360))
    link_sockets(tree, leg_pos.outputs["Geometry"], leg_mirror.inputs["Geometry"])
    leg_mirror_rot = safe_node(tree, "ShaderNodeMath", (bx, by - 460))
    leg_mirror_rot.operation = "MULTIPLY"
    link_sockets(tree, spread_rad.outputs[0], leg_mirror_rot.inputs[0])
    leg_mirror_rot.inputs[1].default_value = -1.0
    link_float_to_vector(tree, leg_mirror_rot.outputs[0], leg_mirror, "Rotation", component=2, defaults=(0.0, 0.0, 0.0))

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 320, by + 200))
    link_sockets(tree, panel_rot.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, pole_pos.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, leg_neg.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, leg_mirror.outputs["Geometry"], join.inputs["Geometry"])
    scaled = _scale_all(tree, gin, bx + 460, by + 200, join.outputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 620, by + 200))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, scaled.outputs["Geometry"], shade.inputs["Geometry"])
    store = _store_float(tree, bx + 720, by + 200, shade.outputs["Geometry"], "stand_height", gin.outputs["Stand Height"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(panel, "geometry")
    color_node(pole, "geometry")
    color_node(leg, "geometry")
    color_node(join, "geometry")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Panel", "nodes": ("panel", "lean"), "role": "geometry"},
        {"title": "Pole And Legs", "nodes": ("pole", "leg", "mirror"), "role": "geometry"},
        {"title": "Attribute And Output", "nodes": ("store", "shade", "Group Output"), "role": "output"},
    ])


# -- Registry --
register_builder("MEL_music_bass_clef", build_music_bass_clef, "Music Bass Clef",
    "Bass (F) clef glyph — sweeping body, bottom curl, tail, and two dots",
    "music")
register_builder("MEL_music_beam_cluster", build_music_beam_cluster, "Music Beam Cluster",
    "Eighth-note beam cluster — note heads on stems under a slanted beam",
    "music")
register_builder("MEL_music_triplet_note", build_music_triplet_note, "Music Triplet Note",
    "Three beamed eighth notes with optional double beam and tuplet attribute",
    "music")
register_builder("MEL_music_chord_stack", build_music_chord_stack, "Music Chord Stack",
    "Vertical chord stack of note heads on a shared stem",
    "music")
register_builder("MEL_music_fermata", build_music_fermata, "Music Fermata",
    "Fermata (hold) mark — arc, base line, and optional center dot",
    "music")
register_builder("MEL_music_repeat_bar", build_music_repeat_bar, "Music Repeat Bar",
    "Repeat-bar sign — double thick bars with two dots",
    "music")
register_builder("MEL_music_time_signature", build_music_time_signature, "Music Time Signature",
    "Common-time C meter sign with optional cut-time slash and beats attribute",
    "music")
register_builder("MEL_music_stand", build_music_stand, "Music Stand",
    "Music stand — angled panel, center pole, and splayed legs",
    "music")


