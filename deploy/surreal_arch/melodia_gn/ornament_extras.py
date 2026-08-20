"""Ornament and filigree extras — six-petal rosette, scallop band, keyhole frame,
corner volute, finial cross, and wreath ring.

Follows the ornament.py / filigree.py conventions: instanced radial arrays with
per-item rotation fields, tube-swept curves, and 1-2 named attributes per piece.

Uses: circular_array (petals/leaves), add (join parts), power (volute taper),
      store_attribute (piece metadata), bounding_box (auto-fit via Scale)
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    add_mesh_torus_linked, make_group_input, register_builder,
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
    """Sweep a curve path with a curve profile (AAA railing).

    Do not MeshToCurve first — scallop/keyhole/time-signature paths are already
    bezier curves; MeshToCurve on those yields empty geometry.
    """
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
    """Uniform Scale applied to a whole piece before shading."""
    tx = safe_node(tree, "GeometryNodeTransform", (bx, by))
    link_sockets(tree, geo_sock, tx.inputs["Geometry"])
    vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 140, by - 80))
    link_sockets(tree, gin.outputs["Scale"], vec.inputs["X"])
    link_sockets(tree, gin.outputs["Scale"], vec.inputs["Y"])
    link_sockets(tree, gin.outputs["Scale"], vec.inputs["Z"])
    link_sockets(tree, vec.outputs["Vector"], tx.inputs["Scale"])
    return tx


def _scale_all(tree, gin, bx, by, geo_sock):
    """Uniform Scale applied to a whole piece before shading."""
    tx = safe_node(tree, "GeometryNodeTransform", (bx, by))
    link_sockets(tree, geo_sock, tx.inputs["Geometry"])
    vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 140, by - 80))
    link_sockets(tree, gin.outputs["Scale"], vec.inputs["X"])
    link_sockets(tree, gin.outputs["Scale"], vec.inputs["Y"])
    link_sockets(tree, gin.outputs["Scale"], vec.inputs["Z"])
    link_sockets(tree, vec.outputs["Vector"], tx.inputs["Scale"])
    return tx


def _rotate_radial(tree, inst_sock, count_sock, bx, by, tilt_sock=None):
    """Rotate each instance in place about Z by its index angle, optional X tilt."""
    rotate = safe_node(tree, "GeometryNodeRotateInstances", (bx, by))
    rotate.inputs["Local Space"].default_value = True
    link_sockets(tree, inst_sock, rotate.inputs["Instances"])
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 260, by))
    frac = safe_node(tree, "ShaderNodeMath", (bx - 260, by - 120))
    frac.operation = "DIVIDE"
    link_sockets(tree, idx.outputs["Index"], frac.inputs[0])
    link_sockets(tree, count_sock, frac.inputs[1])
    ang = safe_node(tree, "ShaderNodeMath", (bx - 120, by - 120))
    ang.operation = "MULTIPLY"
    link_sockets(tree, frac.outputs[0], ang.inputs[0])
    ang.inputs[1].default_value = math.tau
    comb = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 120, by))
    link_sockets(tree, ang.outputs[0], comb.inputs["Z"])
    if tilt_sock is not None:
        tilt = safe_node(tree, "ShaderNodeMath", (bx - 260, by + 120))
        tilt.operation = "MULTIPLY"
        link_sockets(tree, tilt_sock, tilt.inputs[0])
        tilt.inputs[1].default_value = math.pi / 180.0
        link_sockets(tree, tilt.outputs[0], comb.inputs["X"])
    link_sockets(tree, comb.outputs["Vector"], rotate.inputs["Rotation"])
    return rotate


def build_ornament_rosette_sixpetal(group_name="MEL_ornament_rosette_sixpetal"):
    """Six-petal (or N-petal) rosette — radial petal ellipses around a domed medallion.

    Uses: circular_array (petals), add (join), store_attribute (rosette_petals)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Outer Radius", 1.0, 0.3, 3.0)
    add_int_param(tree, "Petal Count", 6, 4, 16)
    add_float_param(tree, "Petal Length", 0.5, 0.2, 1.2)
    add_float_param(tree, "Petal Width", 0.22, 0.1, 0.8)
    add_float_param(tree, "Center Dome Scale", 0.4, 0.1, 1.5)

    # Petal: flattened ellipsoid, long axis along X
    petal = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 500, by + 300))
    petal.inputs["Segments"].default_value = 12
    petal.inputs["Rings"].default_value = 8
    pz = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 300))
    pz.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Petal Width"], pz.inputs[0])
    pz.inputs[1].default_value = 0.2
    p_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 520, by + 300))
    link_sockets(tree, gin.outputs["Petal Length"], p_vec.inputs["X"])
    link_sockets(tree, gin.outputs["Petal Width"], p_vec.inputs["Y"])
    link_sockets(tree, pz.outputs[0], p_vec.inputs["Z"])
    petal_x = safe_node(tree, "GeometryNodeTransform", (bx - 320, by + 300))
    link_sockets(tree, petal.outputs["Mesh"], petal_x.inputs["Geometry"])
    link_sockets(tree, p_vec.outputs["Vector"], petal_x.inputs["Scale"])

    # Ring placement radius: petal centers sit just inside the outer rim
    r_in = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 100))
    r_in.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Outer Radius"], r_in.inputs[0])
    half_len = safe_node(tree, "ShaderNodeMath", (bx - 700, by))
    half_len.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Petal Length"], half_len.inputs[0])
    half_len.inputs[1].default_value = 0.5
    link_sockets(tree, half_len.outputs[0], r_in.inputs[1])

    ring = safe_node(tree, "GeometryNodeMeshCircle", (bx - 500, by - 100))
    link_sockets(tree, gin.outputs["Petal Count"], ring.inputs["Vertices"])
    link_sockets(tree, r_in.outputs[0], ring.inputs["Radius"])
    ring.fill_type = "NONE"

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 300, by - 100))
    link_sockets(tree, ring.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, petal_x.outputs["Geometry"], inst.inputs["Instance"])
    rotated = _rotate_radial(tree, inst.outputs["Instances"], gin.outputs["Petal Count"], bx - 80, by - 100)

    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx + 120, by - 100))
    link_sockets(tree, rotated.outputs["Instances"], realize.inputs["Geometry"])

    # Center medallion dome
    dome = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 300, by - 300))
    dome.inputs["Segments"].default_value = 24
    dome.inputs["Rings"].default_value = 12
    link_sockets(tree, gin.outputs["Center Dome Scale"], dome.inputs["Radius"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 300, by))
    link_sockets(tree, realize.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, dome.outputs["Mesh"], join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 460, by))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    store = _store_float(tree, bx + 560, by, shade.outputs["Geometry"], "rosette_petals", gin.outputs["Petal Count"], "INT")
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(petal, "geometry")
    color_node(ring, "curve")
    color_node(inst, "instance")
    color_node(rotated, "instance")
    color_node(realize, "instance")
    color_node(dome, "geometry")
    color_node(join, "geometry")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Radial Petals", "nodes": ("petal", "ring", "rotate", "instance"), "role": "instance"},
        {"title": "Center Medallion", "nodes": ("dome", "sphere"), "role": "geometry"},
        {"title": "Attribute And Output", "nodes": ("store", "shade", "Group Output"), "role": "output"},
    ])


def build_ornament_scallop_band(group_name="MEL_ornament_scallop_band"):
    """Scallop band — repeated semicircular arcs instanced along a baseline.

    Uses: linear_array (arcs), add (join), store_attribute (scallop_radius)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Width", 4.0, 1.0, 12.0)
    add_int_param(tree, "Scallop Count", 6, 2, 32)
    add_float_param(tree, "Scallop Radius", 0.25, 0.05, 1.5)
    add_float_param(tree, "Scallop Height", 1.0, 0.3, 1.5)
    add_float_param(tree, "Thickness", 0.02, 0.005, 0.1)

    # Semicircular arc: single cubic with handles at 4/3 the arc height
    h_y = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 300))
    h_y.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Scallop Radius"], h_y.inputs[0])
    link_sockets(tree, gin.outputs["Scallop Height"], h_y.inputs[1])
    h_scale = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 200))
    h_scale.operation = "MULTIPLY"
    link_sockets(tree, h_y.outputs[0], h_scale.inputs[0])
    h_scale.inputs[1].default_value = 1.3333
    r_neg = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 100))
    r_neg.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Scallop Radius"], r_neg.inputs[0])
    r_neg.inputs[1].default_value = -1.0

    arc_s = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 520, by + 300))
    link_sockets(tree, r_neg.outputs[0], arc_s.inputs["X"])
    arc_e = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 520, by + 200))
    link_sockets(tree, gin.outputs["Scallop Radius"], arc_e.inputs["X"])
    arc_h1 = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 340, by + 300))
    link_sockets(tree, r_neg.outputs[0], arc_h1.inputs["X"])
    link_sockets(tree, h_scale.outputs[0], arc_h1.inputs["Y"])
    arc_h2 = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 340, by + 200))
    link_sockets(tree, gin.outputs["Scallop Radius"], arc_h2.inputs["X"])
    link_sockets(tree, h_scale.outputs[0], arc_h2.inputs["Y"])

    arc = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx - 180, by + 250))
    link_sockets(tree, arc_s.outputs["Vector"], arc.inputs["Start"])
    link_sockets(tree, arc_h1.outputs["Vector"], arc.inputs["Start Handle"])
    link_sockets(tree, arc_e.outputs["Vector"], arc.inputs["End"])
    link_sockets(tree, arc_h2.outputs["Vector"], arc.inputs["End Handle"])
    arc.inputs["Resolution"].default_value = 10

    # Baseline points: evenly spaced scallop centers
    spacing = safe_node(tree, "ShaderNodeMath", (bx - 700, by))
    spacing.operation = "DIVIDE"
    link_sockets(tree, gin.outputs["Width"], spacing.inputs[0])
    link_sockets(tree, gin.outputs["Scallop Count"], spacing.inputs[1])
    half_w = safe_node(tree, "ShaderNodeMath", (bx - 700, by - 100))
    half_w.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Width"], half_w.inputs[0])
    half_w.inputs[1].default_value = -0.5
    base = safe_node(tree, "GeometryNodeMeshLine", (bx - 520, by))
    base.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Scallop Count"], base.inputs["Count"])
    link_float_to_vector(tree, half_w.outputs[0], base, "Start Location", component=0, defaults=(0.0, 0.0, 0.0))
    link_float_to_vector(tree, spacing.outputs[0], base, "Offset", component=0, defaults=(0.0, 0.0, 0.0))

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 320, by))
    link_sockets(tree, base.outputs["Mesh"], inst.inputs["Points"])
    link_sockets(tree, arc.outputs["Curve"], inst.inputs["Instance"])
    realize = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 120, by))
    link_sockets(tree, inst.outputs["Instances"], realize.inputs["Geometry"])

    profile = _profile_circle(tree, bx - 300, by - 250, gin.outputs["Thickness"])
    band_mesh = _sweep(tree, bx + 80, by, realize.outputs["Geometry"], _profile_out(profile))

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 240, by))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, band_mesh.outputs["Mesh"], shade.inputs["Geometry"])
    store = _store_float(tree, bx + 340, by, shade.outputs["Geometry"], "scallop_radius", gin.outputs["Scallop Radius"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(arc, "curve")
    color_node(base, "curve")
    color_node(inst, "instance")
    color_node(realize, "instance")
    color_node(band_mesh, "geometry")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Scallop Arcs", "nodes": ("arc", "bezier", "base", "instance"), "role": "curve"},
        {"title": "Sweep And Output", "nodes": ("curve to mesh", "store", "shade", "Group Output"), "role": "output"},
    ])


def build_ornament_keyhole_frame(group_name="MEL_ornament_keyhole_frame"):
    """Keyhole frame — rounded rectangle outline with a circular ring on top.

    Uses: add (join ring + rect), merge (corner weld), store_attribute (frame_width)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Ring Radius", 0.4, 0.15, 2.0)
    add_float_param(tree, "Body Height", 0.9, 0.3, 3.0)
    add_float_param(tree, "Thickness", 0.02, 0.005, 0.1)
    add_float_param(tree, "Scale", 1.0, 0.3, 3.0)
    add_int_param(tree, "Profile Vertices", 8, 4, 24)

    # Ring circle lifted to sit on top of the body
    ring = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 660, by + 300))
    link_sockets(tree, gin.outputs["Ring Radius"], ring.inputs["Radius"])
    ring.inputs["Resolution"].default_value = 40
    ring_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 460, by + 300))
    link_sockets(tree, ring.outputs["Curve"], ring_pos.inputs["Geometry"])
    link_float_to_vector(tree, gin.outputs["Ring Radius"], ring_pos, "Position", component=1, defaults=(0.0, 0.0, 0.0))

    # Corner math: half widths and handle fractions
    r_neg = safe_node(tree, "ShaderNodeMath", (bx - 800, by + 500))
    r_neg.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Ring Radius"], r_neg.inputs[0])
    r_neg.inputs[1].default_value = -1.0
    h_neg = safe_node(tree, "ShaderNodeMath", (bx - 800, by + 400))
    h_neg.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Body Height"], h_neg.inputs[0])
    h_neg.inputs[1].default_value = -1.0
    hx = safe_node(tree, "ShaderNodeMath", (bx - 800, by + 300))
    hx.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Ring Radius"], hx.inputs[0])
    hx.inputs[1].default_value = 0.6
    hxn = safe_node(tree, "ShaderNodeMath", (bx - 800, by + 200))
    hxn.operation = "MULTIPLY"
    link_sockets(tree, hx.outputs[0], hxn.inputs[0])
    hxn.inputs[1].default_value = -1.0
    hy = safe_node(tree, "ShaderNodeMath", (bx - 800, by + 100))
    hy.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Body Height"], hy.inputs[0])
    hy.inputs[1].default_value = 0.35
    hyn = safe_node(tree, "ShaderNodeMath", (bx - 800, by))
    hyn.operation = "MULTIPLY"
    link_sockets(tree, hy.outputs[0], hyn.inputs[0])
    hyn.inputs[1].default_value = -1.0

    # Corner points
    c_tl = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 620, by + 500))
    link_sockets(tree, r_neg.outputs[0], c_tl.inputs["X"])
    c_tr = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 620, by + 420))
    link_sockets(tree, gin.outputs["Ring Radius"], c_tr.inputs["X"])
    c_bl = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 620, by + 340))
    link_sockets(tree, r_neg.outputs[0], c_bl.inputs["X"])
    link_sockets(tree, h_neg.outputs[0], c_bl.inputs["Y"])
    c_br = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 620, by + 260))
    link_sockets(tree, gin.outputs["Ring Radius"], c_br.inputs["X"])
    link_sockets(tree, h_neg.outputs[0], c_br.inputs["Y"])

    # Handle points
    ht_l = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 620, by + 180))
    link_sockets(tree, hxn.outputs[0], ht_l.inputs["X"])
    ht_r = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 620, by + 100))
    link_sockets(tree, hx.outputs[0], ht_r.inputs["X"])
    hb_l = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 620, by + 20))
    link_sockets(tree, hxn.outputs[0], hb_l.inputs["X"])
    link_sockets(tree, h_neg.outputs[0], hb_l.inputs["Y"])
    hb_r = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 620, by - 60))
    link_sockets(tree, hx.outputs[0], hb_r.inputs["X"])
    link_sockets(tree, h_neg.outputs[0], hb_r.inputs["Y"])
    vl_t = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 620, by - 140))
    link_sockets(tree, r_neg.outputs[0], vl_t.inputs["X"])
    link_sockets(tree, hyn.outputs[0], vl_t.inputs["Y"])
    vr_t = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 620, by - 220))
    link_sockets(tree, gin.outputs["Ring Radius"], vr_t.inputs["X"])
    link_sockets(tree, hyn.outputs[0], vr_t.inputs["Y"])
    vl_b = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 620, by - 300))
    link_sockets(tree, r_neg.outputs[0], vl_b.inputs["X"])
    link_sockets(tree, hy.outputs[0], vl_b.inputs["Y"])
    vr_b = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 620, by - 380))
    link_sockets(tree, gin.outputs["Ring Radius"], vr_b.inputs["X"])
    link_sockets(tree, hy.outputs[0], vr_b.inputs["Y"])

    # Four bezier sides
    side_top = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx - 440, by + 500))
    link_sockets(tree, c_tl.outputs["Vector"], side_top.inputs["Start"])
    link_sockets(tree, ht_l.outputs["Vector"], side_top.inputs["Start Handle"])
    link_sockets(tree, c_tr.outputs["Vector"], side_top.inputs["End"])
    link_sockets(tree, ht_r.outputs["Vector"], side_top.inputs["End Handle"])
    side_top.inputs["Resolution"].default_value = 8

    side_right = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx - 440, by + 400))
    link_sockets(tree, c_tr.outputs["Vector"], side_right.inputs["Start"])
    link_sockets(tree, vr_t.outputs["Vector"], side_right.inputs["Start Handle"])
    link_sockets(tree, c_br.outputs["Vector"], side_right.inputs["End"])
    link_sockets(tree, vr_b.outputs["Vector"], side_right.inputs["End Handle"])
    side_right.inputs["Resolution"].default_value = 8

    side_bottom = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx - 440, by + 300))
    link_sockets(tree, c_br.outputs["Vector"], side_bottom.inputs["Start"])
    link_sockets(tree, hb_r.outputs["Vector"], side_bottom.inputs["Start Handle"])
    link_sockets(tree, c_bl.outputs["Vector"], side_bottom.inputs["End"])
    link_sockets(tree, hb_l.outputs["Vector"], side_bottom.inputs["End Handle"])
    side_bottom.inputs["Resolution"].default_value = 8

    side_left = safe_node(tree, "GeometryNodeCurvePrimitiveBezierSegment", (bx - 440, by + 200))
    link_sockets(tree, c_bl.outputs["Vector"], side_left.inputs["Start"])
    link_sockets(tree, vl_b.outputs["Vector"], side_left.inputs["Start Handle"])
    link_sockets(tree, c_tl.outputs["Vector"], side_left.inputs["End"])
    link_sockets(tree, vl_t.outputs["Vector"], side_left.inputs["End Handle"])
    side_left.inputs["Resolution"].default_value = 8

    join_c = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 260, by + 300))
    link_sockets(tree, ring_pos.outputs["Geometry"], join_c.inputs["Geometry"])
    link_sockets(tree, side_top.outputs["Curve"], join_c.inputs["Geometry"])
    link_sockets(tree, side_right.outputs["Curve"], join_c.inputs["Geometry"])
    link_sockets(tree, side_bottom.outputs["Curve"], join_c.inputs["Geometry"])
    link_sockets(tree, side_left.outputs["Curve"], join_c.inputs["Geometry"])
    merge = safe_node(tree, "GeometryNodeMergeByDistance", (bx - 80, by + 300))
    link_sockets(tree, join_c.outputs["Geometry"], merge.inputs["Geometry"])
    merge.inputs["Distance"].default_value = 0.002

    profile = _profile_circle(tree, bx - 200, by + 100, gin.outputs["Thickness"], gin.outputs["Profile Vertices"])
    frame_mesh = _sweep(tree, bx + 120, by + 300, merge.outputs["Geometry"], _profile_out(profile))
    scaled = _scale_all(tree, gin, bx + 280, by + 300, frame_mesh.outputs["Mesh"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 440, by + 300))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, scaled.outputs["Geometry"], shade.inputs["Geometry"])
    store = _store_float(tree, bx + 540, by + 300, shade.outputs["Geometry"], "frame_width", gin.outputs["Thickness"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(ring, "curve")
    color_node(ring_pos, "curve")
    color_node(side_top, "curve")
    color_node(side_right, "curve")
    color_node(side_bottom, "curve")
    color_node(side_left, "curve")
    color_node(join_c, "curve")
    color_node(merge, "math")
    color_node(frame_mesh, "geometry")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Ring And Outline", "nodes": ("ring", "side", "bezier", "join"), "role": "curve"},
        {"title": "Sweep And Output", "nodes": ("curve to mesh", "merge", "store", "shade", "Group Output"), "role": "output"},
    ])


def build_filigree_corner_volute(group_name="MEL_filigree_corner_volute"):
    """Corner volute — Archimedean spiral arm with a taper and finial dot.

    Uses: power (spiral taper), add (join arm + finial), store_attribute (FiligreePhase)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Outer Radius", 0.5, 0.15, 2.0)
    add_float_param(tree, "Inner Radius", 0.06, 0.02, 0.5)
    add_float_param(tree, "Turns", 1.5, 0.5, 5.0)
    add_float_param(tree, "Taper Power", 1.2, 0.1, 4.0)
    add_float_param(tree, "Profile Radius", 0.012, 0.004, 0.05)
    add_int_param(tree, "Resolution", 128, 16, 512)
    add_float_param(tree, "Finial Size", 0.03, 0.01, 0.2)

    # Points along the spiral: radius lerps Inner -> Outer, angle = Turns * 2pi
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx - 880, by + 300))
    count_minus = safe_node(tree, "ShaderNodeMath", (bx - 880, by + 200))
    count_minus.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Resolution"], count_minus.inputs[0])
    count_minus.inputs[1].default_value = 1.0
    factor = safe_node(tree, "ShaderNodeMath", (bx - 880, by + 100))
    factor.operation = "DIVIDE"
    link_sockets(tree, idx.outputs["Index"], factor.inputs[0])
    link_sockets(tree, count_minus.outputs[0], factor.inputs[1])

    r_range = safe_node(tree, "ShaderNodeMath", (bx - 880, by))
    r_range.operation = "SUBTRACT"
    link_sockets(tree, gin.outputs["Outer Radius"], r_range.inputs[0])
    link_sockets(tree, gin.outputs["Inner Radius"], r_range.inputs[1])
    r_lerp = safe_node(tree, "ShaderNodeMath", (bx - 880, by - 100))
    r_lerp.operation = "MULTIPLY"
    link_sockets(tree, factor.outputs[0], r_lerp.inputs[0])
    link_sockets(tree, r_range.outputs[0], r_lerp.inputs[1])
    radius = safe_node(tree, "ShaderNodeMath", (bx - 880, by - 200))
    radius.operation = "ADD"
    link_sockets(tree, gin.outputs["Inner Radius"], radius.inputs[0])
    link_sockets(tree, r_lerp.outputs[0], radius.inputs[1])

    tau_node = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 200))
    tau_node.operation = "MULTIPLY"
    link_sockets(tree, factor.outputs[0], tau_node.inputs[0])
    tau_node.inputs[1].default_value = math.tau
    angle = safe_node(tree, "ShaderNodeMath", (bx - 700, by + 100))
    angle.operation = "MULTIPLY"
    link_sockets(tree, tau_node.outputs[0], angle.inputs[0])
    link_sockets(tree, gin.outputs["Turns"], angle.inputs[1])

    cos_n = safe_node(tree, "ShaderNodeMath", (bx - 700, by))
    cos_n.operation = "COSINE"
    sin_n = safe_node(tree, "ShaderNodeMath", (bx - 700, by - 100))
    sin_n.operation = "SINE"
    link_sockets(tree, angle.outputs[0], cos_n.inputs[0])
    link_sockets(tree, angle.outputs[0], sin_n.inputs[0])
    pos_x = safe_node(tree, "ShaderNodeMath", (bx - 700, by - 200))
    pos_x.operation = "MULTIPLY"
    link_sockets(tree, cos_n.outputs[0], pos_x.inputs[0])
    link_sockets(tree, radius.outputs[0], pos_x.inputs[1])
    pos_y = safe_node(tree, "ShaderNodeMath", (bx - 700, by - 300))
    pos_y.operation = "MULTIPLY"
    link_sockets(tree, sin_n.outputs[0], pos_y.inputs[0])
    link_sockets(tree, radius.outputs[0], pos_y.inputs[1])
    pos = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 520, by - 200))
    link_sockets(tree, pos_x.outputs[0], pos.inputs["X"])
    link_sockets(tree, pos_y.outputs[0], pos.inputs["Y"])

    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 880, by + 400))
    line.mode = "OFFSET"
    link_sockets(tree, gin.outputs["Resolution"], line.inputs["Count"])
    line.inputs["Start Location"].default_value = (0.0, 0.0, 0.0)
    line.inputs["Offset"].default_value = (0.001, 0.0, 0.0)

    set_pos = safe_node(tree, "GeometryNodeSetPosition", (bx - 700, by + 400))
    link_sockets(tree, line.outputs["Mesh"], set_pos.inputs["Geometry"])
    link_sockets(tree, pos.outputs["Vector"], set_pos.inputs["Position"])

    # FiligreePhase attribute = progress along the spiral
    phase = _store_float(tree, bx - 520, by + 400, set_pos.outputs["Geometry"], "FiligreePhase", factor.outputs[0])

    curve = safe_node(tree, "GeometryNodeMeshToCurve", (bx - 340, by + 400))
    link_sockets(tree, phase.outputs["Geometry"], curve.inputs["Mesh"])

    # Taper: radius = (1 - phase^TaperPower) * Profile Radius
    taper = safe_node(tree, "ShaderNodeMath", (bx - 520, by + 200))
    taper.operation = "POWER"
    link_sockets(tree, factor.outputs[0], taper.inputs[0])
    link_sockets(tree, gin.outputs["Taper Power"], taper.inputs[1])
    inv = safe_node(tree, "ShaderNodeMath", (bx - 520, by + 100))
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    link_sockets(tree, taper.outputs[0], inv.inputs[1])

    set_radius = safe_node(tree, "GeometryNodeSetCurveRadius", (bx - 340, by + 200))
    link_sockets(tree, curve.outputs["Curve"], set_radius.inputs["Curve"])
    link_sockets(tree, inv.outputs[0], set_radius.inputs["Radius"])

    profile = _profile_circle(tree, bx - 700, by - 500, gin.outputs["Profile Radius"], 8)
    arm = _sweep(tree, bx - 140, by + 300, set_radius.outputs["Curve"], _profile_out(profile))

    finial = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 340, by - 200))
    finial.inputs["Segments"].default_value = 16
    finial.inputs["Rings"].default_value = 8
    link_sockets(tree, gin.outputs["Finial Size"], finial.inputs["Radius"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 60, by + 300))
    link_sockets(tree, arm.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, finial.outputs["Mesh"], join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 220, by + 300))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    store = _store_float(tree, bx + 320, by + 300, shade.outputs["Geometry"], "filigree_turns", gin.outputs["Turns"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(line, "curve")
    color_node(set_pos, "geometry")
    color_node(curve, "curve")
    color_node(set_radius, "curve")
    color_node(arm, "geometry")
    color_node(finial, "geometry")
    color_node(join, "geometry")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Spiral", "nodes": ("line", "spiral", "set position", "phase"), "role": "curve"},
        {"title": "Taper", "nodes": ("taper", "power", "set curve radius"), "role": "curve"},
        {"title": "Finial And Output", "nodes": ("finial", "sphere", "join", "store", "shade", "Group Output"), "role": "output"},
    ])


def build_filigree_finial_cross(group_name="MEL_filigree_finial_cross"):
    """Finial cross — bar-and-ball cross with four domed tips and optional center ball.

    Uses: add (join bars), switch (center ball), store_attribute (finial_height)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Height", 0.7, 0.3, 2.5)
    add_float_param(tree, "Arm Width", 0.4, 0.15, 1.5)
    add_float_param(tree, "Bar Thickness", 0.05, 0.02, 0.2)
    add_float_param(tree, "Tip Size", 0.09, 0.03, 0.35)
    add_float_param(tree, "Center Ball Size", 0.09, 0.03, 0.35)
    add_bool_param(tree, "Has Center Ball", True)

    # Vertical bar sits on the base, horizontal arm crosses above its center
    hx_cross = safe_node(tree, "ShaderNodeMath", (bx - 760, by + 160))
    hx_cross.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Height"], hx_cross.inputs[0])
    hx_cross.inputs[1].default_value = 0.5
    v_center = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 580, by + 200))
    link_sockets(tree, hx_cross.outputs[0], v_center.inputs["Y"])
    vbar = safe_node(tree, "GeometryNodeMeshCube", (bx - 400, by + 200))
    link_float_to_vector(tree, gin.outputs["Bar Thickness"], vbar, "Size", component=0, defaults=(0.0, 0.0, 0.0))
    link_float_to_vector(tree, gin.outputs["Height"], vbar, "Size", component=1, defaults=(0.0, 0.0, 0.0))
    link_float_to_vector(tree, gin.outputs["Bar Thickness"], vbar, "Size", component=2, defaults=(0.0, 0.0, 0.0))
    h_center = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 580, by + 350))
    link_sockets(tree, hx_cross.outputs[0], h_center.inputs["Y"])
    hbar = safe_node(tree, "GeometryNodeMeshCube", (bx - 400, by + 350))
    link_float_to_vector(tree, gin.outputs["Arm Width"], hbar, "Size", component=0, defaults=(0.0, 0.0, 0.0))
    link_float_to_vector(tree, gin.outputs["Bar Thickness"], hbar, "Size", component=1, defaults=(0.0, 0.0, 0.0))
    link_float_to_vector(tree, gin.outputs["Bar Thickness"], hbar, "Size", component=2, defaults=(0.0, 0.0, 0.0))

    v_trans = safe_node(tree, "GeometryNodeTransform", (bx - 240, by + 200))
    link_sockets(tree, vbar.outputs["Mesh"], v_trans.inputs["Geometry"])
    link_sockets(tree, v_center.outputs["Vector"], v_trans.inputs["Translation"])
    h_trans = safe_node(tree, "GeometryNodeTransform", (bx - 240, by + 350))
    link_sockets(tree, hbar.outputs["Mesh"], h_trans.inputs["Geometry"])
    link_sockets(tree, h_center.outputs["Vector"], h_trans.inputs["Translation"])

    # Tip studs on all four ends: two endpoint lines to instance the globe on
    arm_neg = safe_node(tree, "ShaderNodeMath", (bx - 860, by + 520))
    arm_neg.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Arm Width"], arm_neg.inputs[0])
    arm_neg.inputs[1].default_value = -0.5

    x_start = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 860, by + 420))
    link_sockets(tree, arm_neg.outputs[0], x_start.inputs["X"])
    link_sockets(tree, hx_cross.outputs[0], x_start.inputs["Y"])
    x_delta = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 860, by + 320))
    link_sockets(tree, gin.outputs["Arm Width"], x_delta.inputs["X"])
    tip_line_x = safe_node(tree, "GeometryNodeMeshLine", (bx - 680, by + 420))
    tip_line_x.mode = "OFFSET"
    tip_line_x.inputs["Count"].default_value = 2
    link_sockets(tree, x_start.outputs["Vector"], tip_line_x.inputs["Start Location"])
    link_sockets(tree, x_delta.outputs["Vector"], tip_line_x.inputs["Offset"])

    y_delta = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 860, by + 220))
    link_sockets(tree, gin.outputs["Height"], y_delta.inputs["Y"])
    tip_line_y = safe_node(tree, "GeometryNodeMeshLine", (bx - 680, by + 320))
    tip_line_y.mode = "OFFSET"
    tip_line_y.inputs["Count"].default_value = 2
    link_sockets(tree, y_delta.outputs["Vector"], tip_line_y.inputs["Offset"])

    tip_globe = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 860, by + 100))
    tip_globe.inputs["Segments"].default_value = 12
    tip_globe.inputs["Rings"].default_value = 6
    tip_x_ball = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 680, by + 100))
    link_sockets(tree, tip_line_x.outputs["Mesh"], tip_x_ball.inputs["Points"])
    link_sockets(tree, tip_globe.outputs["Mesh"], tip_x_ball.inputs["Instance"])
    tip_y_ball = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 520, by + 100))
    link_sockets(tree, tip_line_y.outputs["Mesh"], tip_y_ball.inputs["Points"])
    link_sockets(tree, tip_globe.outputs["Mesh"], tip_y_ball.inputs["Instance"])

    tips = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 340, by + 300))
    tip_all = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 500, by + 300))
    link_sockets(tree, tip_x_ball.outputs["Instances"], tip_all.inputs["Geometry"])
    link_sockets(tree, tip_y_ball.outputs["Instances"], tip_all.inputs["Geometry"])
    link_sockets(tree, tip_all.outputs["Geometry"], tips.inputs["Geometry"])

    ball = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 440, by + 100))
    ball.inputs["Segments"].default_value = 16
    ball.inputs["Rings"].default_value = 8
    ball_move = safe_node(tree, "GeometryNodeTransform", (bx - 260, by + 100))
    link_sockets(tree, ball.outputs["Mesh"], ball_move.inputs["Geometry"])
    link_sockets(tree, h_center.outputs["Vector"], ball_move.inputs["Translation"])
    ball_sw = safe_node(tree, "GeometryNodeSwitch", (bx - 80, by + 100))
    try:
        ball_sw.input_type = "GEOMETRY"
    except Exception:
        pass
    ball_sw.inputs["Switch"].default_value = False
    link_sockets(tree, ball_move.outputs["Geometry"], _true_socket(ball_sw))
    link_sockets(tree, gin.outputs["Has Center Ball"], ball_sw.inputs["Switch"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 80, by + 300))
    link_sockets(tree, v_trans.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, h_trans.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, tips.outputs["Geometry"], join.inputs["Geometry"])
    link_sockets(tree, _output_socket(ball_sw), join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 240, by + 300))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    store = _store_float(tree, bx + 340, by + 300, shade.outputs["Geometry"], "finial_height", gin.outputs["Height"])
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(v_trans, "geometry")
    color_node(h_trans, "geometry")
    color_node(tip_y_ball, "instance")
    color_node(tips, "instance")
    color_node(ball_sw, "instance")
    color_node(join, "geometry")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Bars", "nodes": ("cube", "transform", "vbar", "hbar"), "role": "geometry"},
        {"title": "Tip Studs", "nodes": ("line", "instance", "sphere"), "role": "instance"},
        {"title": "Center Ball", "nodes": ("ball", "switch", "sphere"), "role": "instance"},
        {"title": "Attribute And Output", "nodes": ("store", "shade", "Group Output"), "role": "output"},
    ])


def build_filigree_wreath_ring(group_name="MEL_filigree_wreath_ring"):
    """Wreath ring — torus band ringed with tilted laurel leaves.

    Uses: circular_array (leaves), add (join), store_attribute (wreath_leaves)
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Radius", 0.3, 0.1, 1.5)
    add_float_param(tree, "Tube Radius", 0.02, 0.005, 0.12)
    add_int_param(tree, "Leaf Count", 8, 4, 24)
    add_float_param(tree, "Leaf Length", 0.18, 0.05, 0.6)
    add_float_param(tree, "Leaf Width", 0.08, 0.03, 0.3)
    add_float_param(tree, "Leaf Tilt", 25.0, -60.0, 60.0)

    band = add_mesh_torus_linked(tree, (bx - 460, by + 300),
                                 gin.outputs["Radius"], gin.outputs["Tube Radius"])

    # Leaf: flattened ellipsoid oriented radially outward
    leaf = safe_node(tree, "GeometryNodeMeshUVSphere", (bx - 660, by - 100))
    leaf.inputs["Segments"].default_value = 12
    leaf.inputs["Rings"].default_value = 8
    leaf_z = safe_node(tree, "ShaderNodeMath", (bx - 820, by + 80))
    leaf_z.operation = "MULTIPLY"
    link_sockets(tree, gin.outputs["Leaf Width"], leaf_z.inputs[0])
    leaf_z.inputs[1].default_value = 0.18
    leaf_vec = safe_node(tree, "ShaderNodeCombineXYZ", (bx - 660, by + 80))
    link_sockets(tree, gin.outputs["Leaf Length"], leaf_vec.inputs["X"])
    link_sockets(tree, gin.outputs["Leaf Width"], leaf_vec.inputs["Y"])
    link_sockets(tree, leaf_z.outputs[0], leaf_vec.inputs["Z"])
    leaf_x = safe_node(tree, "GeometryNodeTransform", (bx - 480, by - 100))
    link_sockets(tree, leaf.outputs["Mesh"], leaf_x.inputs["Geometry"])
    link_sockets(tree, leaf_vec.outputs["Vector"], leaf_x.inputs["Scale"])

    leaf_circle = safe_node(tree, "GeometryNodeMeshCircle", (bx - 660, by - 260))
    link_sockets(tree, gin.outputs["Leaf Count"], leaf_circle.inputs["Vertices"])
    link_sockets(tree, gin.outputs["Radius"], leaf_circle.inputs["Radius"])
    leaf_circle.fill_type = "NONE"

    leaf_inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 480, by - 260))
    link_sockets(tree, leaf_circle.outputs["Mesh"], leaf_inst.inputs["Points"])
    link_sockets(tree, leaf_x.outputs["Geometry"], leaf_inst.inputs["Instance"])
    leaf_rot = _rotate_radial(tree, leaf_inst.outputs["Instances"], gin.outputs["Leaf Count"], bx - 260, by - 260, gin.outputs["Leaf Tilt"])
    leaves = safe_node(tree, "GeometryNodeRealizeInstances", (bx - 80, by - 260))
    link_sockets(tree, leaf_rot.outputs["Instances"], leaves.inputs["Geometry"])

    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 60, by + 100))
    link_sockets(tree, band.outputs["Mesh"], join.inputs["Geometry"])
    link_sockets(tree, leaves.outputs["Geometry"], join.inputs["Geometry"])

    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (bx + 220, by + 100))
    shade.inputs["Shade Smooth"].default_value = True
    link_sockets(tree, join.outputs["Geometry"], shade.inputs["Geometry"])
    store = _store_float(tree, bx + 320, by + 100, shade.outputs["Geometry"], "wreath_leaves", gin.outputs["Leaf Count"], "INT")
    link_sockets(tree, store.outputs["Geometry"], gout.inputs["Geometry"])

    color_node(band, "geometry")
    color_node(leaf, "geometry")
    color_node(leaf_circle, "curve")
    color_node(leaf_inst, "instance")
    color_node(leaf_rot, "instance")
    color_node(leaves, "instance")
    color_node(join, "geometry")

    return label_tree(tree, group_name, [
        {"title": "Inputs", "nodes": ("Group Input",), "role": "input"},
        {"title": "Band", "nodes": ("torus", "band"), "role": "geometry"},
        {"title": "Leaves", "nodes": ("leaf", "circle", "rotate", "instance"), "role": "instance"},
        {"title": "Attribute And Output", "nodes": ("store", "shade", "Group Output"), "role": "output"},
    ])


# -- Registry --
register_builder("MEL_ornament_rosette_sixpetal", build_ornament_rosette_sixpetal, "Ornament Rosette Sixpetal",
    "Six-petal (or N-petal) rosette — radial petal ellipses around a domed medallion",
    "ornament")
register_builder("MEL_ornament_scallop_band", build_ornament_scallop_band, "Ornament Scallop Band",
    "Scallop band — repeated semicircular arcs instanced along a baseline",
    "ornament")
register_builder("MEL_ornament_keyhole_frame", build_ornament_keyhole_frame, "Ornament Keyhole Frame",
    "Keyhole frame — rounded rectangle outline with a circular ring on top",
    "ornament")
register_builder("MEL_filigree_corner_volute", build_filigree_corner_volute, "Filigree Corner Volute",
    "Corner volute — Archimedean spiral arm with a taper and finial dot",
    "filigree")
register_builder("MEL_filigree_finial_cross", build_filigree_finial_cross, "Filigree Finial Cross",
    "Finial cross — bar-and-ball cross with four domed tips and optional center ball",
    "filigree")
register_builder("MEL_filigree_wreath_ring", build_filigree_wreath_ring, "Filigree Wreath Ring",
    "Wreath ring — torus band ringed with tilted laurel leaves",
    "filigree")

