"""GN chime family - port of chime_row's physical tuning into Geometry Nodes.

Physics carried over from deploy/surreal_arch/chime_row.py:
  f(semitone) = root_hz * 2^((semitone - 9) / 12)      (A4 = 440 anchored)
  free-free beam: L = longest_m * sqrt(f_ref / f)       (longer = lower pitch)
  hang node at 22.4% L; shimmer bands at L/2.756 and L/5.404

Builders (registered, category "music"):
  MEL_chime_tube          - one tuned tube prototype (length from semitone)
  MEL_chime_field_scatter - poisson-ish scatter of tuned tubes on a plane
  MEL_chime_mark_tree     - graduated hanging-rod curtain (stage edge)
  MEL_chime_carillon_tier - ring tier for carillon towers
  MEL_chime_aeolian_wall  - walkable harp wall with wind-phase strings
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    register_builder, sock,
)

# --- helpers local to this module (mirroring music_heroes private style) ---

def _math(tree, operation, loc, a=None, b=None):
    node = safe_node(tree, "ShaderNodeMath", loc)
    if node:
        try:
            node.operation = operation
        except Exception:
            pass
        if a is not None:
            if isinstance(a, (int, float)):
                node.inputs[0].default_value = float(a)
            else:
                link_sockets(tree, a, node.inputs[0])
        if b is not None:
            if isinstance(b, (int, float)):
                node.inputs[1].default_value = float(b)
            else:
                link_sockets(tree, b, node.inputs[1])
    return node


def _combine(tree, loc, x=None, y=None, z=None):
    node = safe_node(tree, "ShaderNodeCombineXYZ", loc)
    for name, val in (("X", x), ("Y", y), ("Z", z)):
        if val is None or node is None:
            continue
        if isinstance(val, (int, float)):
            try:
                node.inputs[name].default_value = float(val)
            except Exception:
                pass
        else:
            link_sockets(tree, val, node.inputs[name])
    return node


def _true_socket(n): return n.inputs.get("True") or n.inputs.get("A")
def _false_socket(n): return n.inputs.get("False") or n.inputs.get("B")
def _out_socket(n): return n.outputs.get("Output") or (n.outputs[0] if n and n.outputs else None)


def _switch_geo(tree, loc, switch_sock, if_true, if_false):
    sw = safe_node(tree, "GeometryNodeSwitch", loc)
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    link_sockets(tree, switch_sock, sw.inputs.get("Switch") or sw.inputs[0])
    if if_true is not None:
        link_sockets(tree, if_true, _true_socket(sw))
    if if_false is not None:
        link_sockets(tree, if_false, _false_socket(sw))
    return _out_socket(sw)


def _replace_output(tree, gout, geom):
    geo_in = gout.inputs.get("Geometry")
    if geo_in is not None:
        for lk in list(tree.links):
            if lk.to_socket == geo_in:
                tree.links.remove(lk)
    link_sockets(tree, geom, gout.inputs["Geometry"])


def _export_tail(tree, gin, gout, geom, loc):
    realize = safe_node(tree, "GeometryNodeRealizeInstances", loc)
    link_sockets(tree, geom, realize.inputs["Geometry"])
    sw = safe_node(tree, "GeometryNodeSwitch", (loc[0] + 220, loc[1]))
    try:
        sw.input_type = "GEOMETRY"
    except Exception:
        pass
    rs = gin.outputs.get("Realize for export")
    if rs is not None:
        link_sockets(tree, rs, sw.inputs.get("Switch") or sw.inputs[0])
    link_sockets(tree, geom, _false_socket(sw))
    link_sockets(tree, realize.outputs["Geometry"], _true_socket(sw))
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (loc[0] + 440, loc[1]))
    try:
        shade.inputs["Shade Smooth"].default_value = True
    except Exception:
        pass
    link_sockets(tree, _out_socket(sw), shade.inputs["Geometry"])
    _replace_output(tree, gout, shade.outputs["Geometry"])
    return shade.outputs["Geometry"]


def _store_named(tree, loc, geom, name, value_sock, data_type="FLOAT"):
    st = safe_node(tree, "GeometryNodeStoreNamedAttribute", loc)
    try:
        st.data_type = data_type
    except Exception:
        pass
    try:
        st.inputs["Name"].default_value = name
    except Exception:
        pass
    link_sockets(tree, geom, st.inputs["Geometry"])
    if value_sock is not None:
        v = st.inputs.get("Value") or st.inputs.get("Value_001")
        if v is not None:
            link_sockets(tree, value_sock, v)
    color_node(st, "attribute")
    return st.outputs["Geometry"]


def _cylinder_along_z(tree, loc, radius_sock, length_sock, verts=12):
    """UV sphere-free tube: cone/cylinder primitive along +Z centered at half length."""
    cyl = safe_node(tree, "GeometryNodeMeshCylinder", loc)
    try:
        cyl.inputs["Vertices"].default_value = verts
    except Exception:
        pass
    r_in = sock(cyl, "Radius")
    if r_in is not None:
        if isinstance(radius_sock, (int, float)):
            r_in.default_value = float(radius_sock)
        else:
            link_sockets(tree, radius_sock, r_in)
    depth_in = sock(cyl, "Depth")
    if depth_in is not None:
        if isinstance(length_sock, (int, float)):
            depth_in.default_value = float(length_sock)
        else:
            link_sockets(tree, length_sock, depth_in)
    fill = sock(cyl, "Fill Type")
    color_node(cyl, "geometry")
    return cyl.outputs.get("Mesh") or cyl.outputs[0]


# ---------------------------------------------------------------------------
# MEL_chime_tube - one physically-proportioned tube
# ---------------------------------------------------------------------------

def build_chime_tube(group_name="MEL_chime_tube"):
    """Tuned tube: Length driven by semitone via free-free beam law.

    Inputs: Semitone (0..36 relative to root), Root Hz, Longest M, Radius M.
    Output carries stored attributes: chime_semitone (float), chime_len (float).
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Semitone", 0.0, 0.0, 48.0)
    add_float_param(tree, "Root Hz", 261.63, 55.0, 880.0)
    add_float_param(tree, "Longest M", 1.25, 0.2, 6.0)
    add_float_param(tree, "Radius M", 0.019, 0.004, 0.15)
    add_bool_param(tree, "Realize for export", False)

    # f = root * 2^((semi-9)/12); L = longest * sqrt(f_ref / f), f_ref at semi=9
    # pow2 = 2^((semi-9)/12)
    off = _math(tree, "SUBTRACT", (bx - 900, by + 200), gin.outputs["Semitone"], 9.0)
    div12 = _math(tree, "DIVIDE", (bx - 760, by + 200), off.outputs[0], 12.0)
    # ShaderNodeMath has no POW; use Arithmetic via "POWER" op name in Blender = POWER
    powr = _math(tree, "POWER", (bx - 600, by + 200))
    if powr is not None:
        # inputs already linked a=div12; set b=2 and swap so base=2 exp=div12
        try:
            powr.operation = "POWER"
        except Exception:
            pass
        b_in = powr.inputs[1]
        # relink: input0 = 2.0 (base), input1 = div12 (exponent)
        for lk in list(tree.links):
            if lk.to_socket == powr.inputs[0]:
                tree.links.remove(lk)
        powr.inputs[0].default_value = 2.0
        link_sockets(tree, div12.outputs[0], b_in)
    freq = _math(tree, "MULTIPLY", (bx - 420, by + 200),
                 gin.outputs["Root Hz"], powr.outputs[0] if powr else 1.0)

    # f_ref = root * 2^0 = root (semitone 9 reference). ratio = root / f
    inv = safe_node(tree, "ShaderNodeMath", (bx - 240, by + 200))
    if inv is not None:
        inv.operation = "DIVIDE"
        link_sockets(tree, gin.outputs["Root Hz"], inv.inputs[0])
        link_sockets(tree, freq.outputs[0], inv.inputs[1])
    sq = _math(tree, "SQRT", (bx - 80, by + 200), inv.outputs[0] if inv else 1.0)
    length = _math(tree, "MULTIPLY", (bx + 80, by + 200),
                   gin.outputs["Longest M"], sq.outputs[0])

    tube = _cylinder_along_z(tree, (bx + 260, by + 120), gin.outputs["Radius M"], length.outputs[0])
    # lift so top sits at z=0 (hang point), tube extends downward
    half = _math(tree, "MULTIPLY", (bx + 80, by + 60), length.outputs[0], 0.5)
    negh = _math(tree, "MULTIPLY", (bx + 180, by + 60), half.outputs[0], -1.0)
    posv = _combine(tree, (bx + 300, by + 60), 0.0, 0.0, negh.outputs[0])
    xf = safe_node(tree, "GeometryNodeTransform", (bx + 440, by + 120))
    link_sockets(tree, tube, xf.inputs["Geometry"])
    link_sockets(tree, posv.outputs["Vector"], xf.inputs["Translation"])

    stored = _store_named(tree, (bx + 620, by + 120), xf.outputs["Geometry"],
                          "chime_semitone", gin.outputs["Semitone"])
    stored = _store_named(tree, (bx + 780, by + 120), stored,
                          "chime_len", length.outputs[0])
    _export_tail(tree, gin, gout, stored, (bx + 960, by + 120))

    return label_tree(tree, group_name, [
        {"title": "Tuning", "nodes": ("tuning math",), "role": "input"},
        {"title": "Tube", "nodes": ("cylinder", "transform"), "role": "geometry"},
        {"title": "Attributes", "nodes": ("store",), "role": "attribute"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Shared tuning-table helper: instance N semitones along a line/grid
# ---------------------------------------------------------------------------

def _refresh_group_refs(tree, group_name):
    """Re-point Group nodes after dependency-tree rebuilds.

    new_geometry_tree removes+recreates datablocks, orphaning earlier
    Group node references (node_tree becomes None). Call before returning
    from any builder that embeds another builder's tree.
    """
    changed = 0
    ng = bpy.data.node_groups.get(group_name)
    if ng is None:
        return 0
    for n in tree.nodes:
        if n.type == "GROUP" and getattr(n, "node_tree", None) is None:
            n.node_tree = ng
            changed += 1
    return changed



def _ensure_tube_group(tree, loc):
    def _b(gn="MEL_chime_tube"):
        build_chime_tube(gn)
    node = safe_node(tree, "GeometryNodeGroup", loc)
    if "MEL_chime_tube" not in bpy.data.node_groups:
        _b()
    node.node_tree = bpy.data.node_groups.get("MEL_chime_tube")
    return node


def _scatter_instances(tree, loc, proto_group, count_sock, spacing_sock, cols_sock,
                       semitone_start=0, jitter=0.0, seed=11):
    """Grid-scatter proto with per-instance Semitone = index (row-major)."""
    bx, by = loc
    mesh_line = safe_node(tree, "GeometryNodeMeshLine", (bx, by + 160))
    try:
        mesh_line.inputs["Count"].default_value = 64
    except Exception:
        pass
    cnt_in = sock(mesh_line, "Count")
    if cnt_in is not None:
        link_sockets(tree, count_sock, cnt_in)
    try:
        mesh_line.mode = "END_POINTS"
    except Exception:
        pass
    total_len = _math(tree, "MULTIPLY", (bx - 200, by + 240), spacing_sock, count_sock)
    link_float_to_vector(tree, total_len.outputs[0], mesh_line, "End Location", component=0)
    to_pts = safe_node(tree, "GeometryNodeMeshToPoints", (bx + 200, by + 160))
    link_sockets(tree, mesh_line.outputs["Mesh"], sock(to_pts, "Mesh") or to_pts.inputs[0])

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 420, by + 120))
    link_sockets(tree, to_pts.outputs["Points"], sock(inst, "Points") or inst.inputs[0])
    link_sockets(tree, proto_group.outputs.get("Geometry"), sock(inst, "Instance"))

    idx = safe_node(tree, "GeometryNodeInputIndex", (bx + 420, by - 80))
    # per-instance semitone -> group input
    if proto_group.inputs.get("Semitone") is not None:
        link_sockets(tree, idx.outputs["Index"], proto_group.inputs["Semitone"])

    if jitter > 0.0:
        rand = safe_node(tree, "FunctionNodeRandomValue", (bx + 420, by - 220))
        try:
            rand.data_type = "FLOAT_VECTOR"
        except Exception:
            pass
        try:
            rand.inputs[1].default_value = (-jitter, -jitter, 0.0)
            rand.inputs[2].default_value = (jitter, jitter, 0.0)
        except Exception:
            pass
        try:
            rand.inputs["Seed"].default_value = seed
        except Exception:
            pass
        tr = safe_node(tree, "GeometryNodeTranslateInstances", (bx + 700, by + 120))
        link_sockets(tree, inst.outputs["Instances"], tr.inputs["Instances"])
        link_sockets(tree, rand.outputs[0], sock(tr, "Translation") or tr.inputs[1])
        return tr.outputs["Instances"]
    return inst.outputs["Instances"]


# ---------------------------------------------------------------------------
# MEL_chime_field_scatter
# ---------------------------------------------------------------------------

def build_chime_field_scatter(group_name="MEL_chime_field_scatter"):
    """Scatter field of tuned hanging tubes; semitone = instance index mod range."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Count", 16, 3, 128)
    add_float_param(tree, "Spacing M", 0.35, 0.05, 4.0)
    add_int_param(tree, "Columns", 8, 1, 32)
    add_float_param(tree, "Jitter M", 0.06, 0.0, 0.5)
    add_float_param(tree, "Root Hz", 261.63, 55.0, 880.0)
    add_float_param(tree, "Longest M", 1.25, 0.2, 6.0)
    add_float_param(tree, "Radius M", 0.019, 0.004, 0.15)
    add_bool_param(tree, "Realize for export", False)

    proto = _ensure_tube_group(tree, (bx - 500, by + 80))
    if proto:
        for src, dst in (("Root Hz", "Root Hz"), ("Longest M", "Longest M"),
                         ("Radius M", "Radius M")):
            if proto.inputs.get(src) is not None:
                link_sockets(tree, gin.outputs[dst], proto.inputs[src])

    rows = _math(tree, "DIVIDE", (bx - 700, by - 80), gin.outputs["Count"], gin.outputs["Columns"])
    rows_i = safe_node(tree, "FunctionNodeFloatToInt", (bx - 560, by - 80))
    link_sockets(tree, rows.outputs[0], rows_i.inputs[0])
    count = _math(tree, "MULTIPLY", (bx - 400, by - 80), rows_i.outputs[0], gin.outputs["Columns"])

    instanced = _scatter_instances(
        tree, (bx - 100, by + 40), proto, count.outputs[0],
        gin.outputs["Spacing M"], gin.outputs["Columns"],
        jitter=0.06, seed=11,
    )
    # store velocity-style attribute for UE emission hookup
    stored = _store_named(tree, (bx + 900, by + 40), instanced, "chime_field", 1.0)
    _export_tail(tree, gin, gout, stored, (bx + 1100, by + 40))

    _refresh_group_refs(tree, "MEL_chime_tube")
    return label_tree(tree, group_name, [
        {"title": "Layout", "nodes": ("count",), "role": "input"},
        {"title": "Scatter", "nodes": ("line", "points", "instance"), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_chime_mark_tree - graduated rod curtain
# ---------------------------------------------------------------------------

def build_chime_mark_tree(group_name="MEL_chime_mark_tree"):
    """Hanging curtain of rods, lengths descending across the row."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Rod Count", 24, 4, 96)
    add_float_param(tree, "Row Width M", 3.0, 0.5, 20.0)
    add_float_param(tree, "Longest M", 1.4, 0.2, 6.0)
    add_float_param(tree, "Shortest M", 0.45, 0.05, 3.0)
    add_float_param(tree, "Rod Radius M", 0.008, 0.002, 0.08)
    add_bool_param(tree, "Realize for export", False)

    proto = _ensure_tube_group(tree, (bx - 520, by + 80))
    if proto:
        if proto.inputs.get("Root Hz") is not None:
            try:
                proto.inputs["Root Hz"].default_value = 523.25  # C5 anchor
            except Exception:
                pass
        if proto.inputs.get("Radius M") is not None:
            link_sockets(tree, gin.outputs["Rod Radius M"], proto.inputs["Radius M"])
        # Longest fixed at tree param; per-instance scale handles graduation below.

    mesh_line = safe_node(tree, "GeometryNodeMeshLine", (bx - 320, by + 200))
    try:
        mesh_line.mode = "END_POINTS"
    except Exception:
        pass
    cnt = sock(mesh_line, "Count")
    if cnt is not None:
        link_sockets(tree, gin.outputs["Rod Count"], cnt)
    link_float_to_vector(tree, gin.outputs["Row Width M"], mesh_line, "End Location", component=0)
    pts = safe_node(tree, "GeometryNodeMeshToPoints", (bx - 120, by + 200))
    link_sockets(tree, mesh_line.outputs["Mesh"], sock(pts, "Mesh") or pts.inputs[0])

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 100, by + 140))
    link_sockets(tree, pts.outputs["Points"], sock(inst, "Points"))
    if proto:
        link_sockets(tree, proto.outputs.get("Geometry"), sock(inst, "Instance"))

    # Graduation factor t = index/(n-1); len = lerp(longest, shortest, t)
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx + 100, by - 120))
    nm1 = _math(tree, "SUBTRACT", (bx + 100, by - 200), gin.outputs["Rod Count"], 1.0)
    t = _math(tree, "DIVIDE", (bx + 260, by - 160), idx.outputs["Index"], nm1.outputs[0])
    span = _math(tree, "SUBTRACT", (bx + 260, by - 280), gin.outputs["Shortest M"], gin.outputs["Longest M"])
    scaled = _math(tree, "MULTIPLY", (bx + 420, by - 220), span.outputs[0], t.outputs[0])
    length = _math(tree, "ADD", (bx + 580, by - 200), gin.outputs["Longest M"], scaled.outputs[0])
    # uniform Z scale approximates length change for the tube prototype
    sv = _combine(tree, (bx + 740, by - 200), 1.0, 1.0, length.outputs[0])
    scale_inst = safe_node(tree, "GeometryNodeScaleInstances", (bx + 900, by + 140))
    link_sockets(tree, inst.outputs["Instances"], scale_inst.inputs["Instances"])
    link_sockets(tree, sv.outputs["Vector"], sock(scale_inst, "Scale") or scale_inst.inputs[2])

    _export_tail(tree, gin, gout, scale_inst.outputs["Instances"], (bx + 1100, by + 140))

    _refresh_group_refs(tree, "MEL_chime_tube")
    return label_tree(tree, group_name, [
        {"title": "Curtain", "nodes": ("line", "points", "instance"), "role": "instance"},
        {"title": "Graduation", "nodes": ("lerp",), "role": "math"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_chime_carillon_tier - one ring tier for towers
# ---------------------------------------------------------------------------

def build_chime_carillon_tier(group_name="MEL_chime_carillon_tier"):
    """Ring of tuned tubes around a circle; semitone steps around the ring."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Tube Count", 12, 3, 36)
    add_float_param(tree, "Ring Radius M", 1.6, 0.4, 12.0)
    add_float_param(tree, "Root Hz", 196.0, 55.0, 880.0)
    add_float_param(tree, "Longest M", 1.8, 0.2, 6.0)
    add_float_param(tree, "Radius M", 0.03, 0.004, 0.2)
    add_bool_param(tree, "Realize for export", False)

    circ = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 420, by + 200))
    if circ is not None:
        try:
            circ.inputs["Resolution"].default_value = 48
        except Exception:
            pass
        r_in = sock(circ, "Radius")
        if r_in is not None:
            link_sockets(tree, gin.outputs["Ring Radius M"], r_in)
    resample = safe_node(tree, "GeometryNodeResampleCurve", (bx - 200, by + 200))
    curve_in = sock(resample, "Curve", "Geometry")
    if circ is not None:
        link_sockets(tree, circ.outputs.get("Curve") or circ.outputs[0], curve_in)
    c_in = sock(resample, "Count", "Offset", "Length")
    if c_in is not None:
        link_sockets(tree, gin.outputs["Tube Count"], c_in)
    pts = safe_node(tree, "GeometryNodeCurveToPoints", (bx + 20, by + 200))
    link_sockets(tree, resample.outputs.get("Curve") or resample.outputs[0],
                 sock(pts, "Curve") or pts.inputs[0])

    proto = _ensure_tube_group(tree, (bx - 420, by - 120))
    if proto:
        for s, d in (("Root Hz", "Root Hz"), ("Longest M", "Longest M"),
                     ("Radius M", "Radius M")):
            if proto.inputs.get(s) is not None:
                link_sockets(tree, gin.outputs[d], proto.inputs[s])

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 240, by + 120))
    link_sockets(tree, pts.outputs["Points"], sock(inst, "Points"))
    if proto:
        link_sockets(tree, proto.outputs.get("Geometry"), sock(inst, "Instance"))
        if proto.inputs.get("Semitone") is not None:
            idx = safe_node(tree, "GeometryNodeInputIndex", (bx + 240, by - 80))
            link_sockets(tree, idx.outputs["Index"], proto.inputs["Semitone"])

    _export_tail(tree, gin, gout, inst.outputs["Instances"], (bx + 460, by + 120))

    _refresh_group_refs(tree, "MEL_chime_tube")
    return label_tree(tree, group_name, [
        {"title": "Ring", "nodes": ("circle", "resample", "to points"), "role": "curve"},
        {"title": "Instance", "nodes": ("instance",), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_chime_aeolian_wall - walkable harp wall with wind-phase strings
# ---------------------------------------------------------------------------

def build_chime_aeolian_wall(group_name="MEL_chime_aeolian_wall"):
    """Wall of vertical 'wind' strings; sine phase offsets make it playable/walkable."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Width M", 6.0, 1.0, 30.0)
    add_float_param(tree, "Height M", 3.2, 0.5, 14.0)
    add_int_param(tree, "String Count", 28, 4, 128)
    add_float_param(tree, "String Radius M", 0.006, 0.001, 0.05)
    add_float_param(tree, "Wind Phase", 0.0, 0.0, 1.0)
    add_float_param(tree, "Wind Amplitude M", 0.08, 0.0, 0.6)
    add_bool_param(tree, "Realize for export", False)

    # Strings as thin cylinders spanning height, arrayed across width
    str_cyl = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 600, by + 200))
    try:
        str_cyl.inputs["Vertices"].default_value = 8
    except Exception:
        pass
    try:
        str_cyl.inputs["Radius"].default_value = 0.006
    except Exception:
        pass
    r_in = sock(str_cyl, "Radius")
    if r_in is not None:
        link_sockets(tree, gin.outputs["String Radius M"], r_in)
    d_in = sock(str_cyl, "Depth")
    if d_in is not None:
        link_sockets(tree, gin.outputs["Height M"], d_in)

    line = safe_node(tree, "GeometryNodeMeshLine", (bx - 380, by + 260))
    try:
        line.mode = "END_POINTS"
    except Exception:
        pass
    c_in = sock(line, "Count")
    if c_in is not None:
        link_sockets(tree, gin.outputs["String Count"], c_in)
    link_float_to_vector(tree, gin.outputs["Width M"], line, "End Location", component=0)
    pts = safe_node(tree, "GeometryNodeMeshToPoints", (bx - 180, by + 260))
    link_sockets(tree, line.outputs["Mesh"], sock(pts, "Mesh") or pts.inputs[0])

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 60, by + 200))
    link_sockets(tree, pts.outputs["Points"], sock(inst, "Points"))
    link_sockets(tree, str_cyl.outputs["Mesh"], sock(inst, "Instance"))

    # Wind displacement: sine(index * k + phase) * amplitude on Y
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx + 60, by - 120))
    k = _math(tree, "MULTIPLY", (bx + 60, by - 200), idx.outputs["Index"], 0.7)
    phased = _math(tree, "ADD", (bx + 220, by - 200), k.outputs[0], gin.outputs["Wind Phase"])
    sine = safe_node(tree, "ShaderNodeMath", (bx + 380, by - 200))
    if sine is not None:
        sine.operation = "SINE"
        link_sockets(tree, phased.outputs[0], sine.inputs[0])
    amp = _math(tree, "MULTIPLY", (bx + 540, by - 200), sine.outputs[0], gin.outputs["Wind Amplitude M"])
    disp = _combine(tree, (bx + 700, by - 200), 0.0, amp.outputs[0], 0.0)
    tr = safe_node(tree, "GeometryNodeTranslateInstances", (bx + 860, by + 200))
    link_sockets(tree, inst.outputs["Instances"], tr.inputs["Instances"])
    link_sockets(tree, disp.outputs["Vector"], sock(tr, "Translation") or tr.inputs[1])

    stored = _store_named(tree, (bx + 1040, by + 200), tr.outputs["Instances"],
                          "aeolian_phase", gin.outputs["Wind Phase"])
    _export_tail(tree, gin, gout, stored, (bx + 1220, by + 200))

    _refresh_group_refs(tree, "MEL_chime_tube")
    return label_tree(tree, group_name, [
        {"title": "Wall", "nodes": ("line", "points", "instance"), "role": "instance"},
        {"title": "Wind", "nodes": ("sine", "translate instances"), "role": "effect"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder(
    "MEL_chime_tube", build_chime_tube, "Chime Tube (Tuned)",
    "Free-free beam tube; length from ET semitone via L = Lmax*sqrt(f_ref/f)",
    "music",
)
register_builder(
    "MEL_chime_field_scatter", build_chime_field_scatter, "Chime Field Scatter",
    "Grid scatter of tuned tubes; semitone = index, jittered like wind groves",
    "music",
)
register_builder(
    "MEL_chime_mark_tree", build_chime_mark_tree, "Mark Tree Curtain",
    "Graduated hanging rods descending across the row; stage-edge shimmer",
    "music",
)
register_builder(
    "MEL_chime_carillon_tier", build_chime_carillon_tier, "Carillon Ring Tier",
    "Ring of tuned tubes stepping semitones around the circle",
    "music",
)
register_builder(
    "MEL_chime_aeolian_wall", build_chime_aeolian_wall, "Aeolian Harp Wall",
    "Walkable wall of wind strings with sine phase sway (Wind Phase param)",
    "music",
)
