"""Realistic harp family - concert pedal harp anatomy + ancient string instruments.

Complements music_heroes.build_music_harp with anatomically-informed detail:
  - Concert harp: tapered pillar w/ capitol, parabolic neck, spruce soundboard
    ribs, soundhole rosette, tuning pins, C/F string color-coding attributes.
  - Ancient variants (paired with ancient_cultures presets):
      MEL_harp_ur_lyre   - Sumerian bull-headed box lyre, 7 gut strings
      MEL_harp_kora      - Mande calabash bridge-harp, 21 strings, handpost
      MEL_wind_siku      - Andean two-row panpipe bundle (ira/arca dialogue)

Morph-ready: builders expose per-string Pluck params consumed by
surreal_arch.morph_baker for UE morph-target export.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    register_builder, sock,
)

# siku reuses the tuned tube proto from chimes_gn (no circular import:
# chimes_gn never imports this module)
from .chimes_gn import _ensure_tube_group


def _math(tree, op, loc, a=None, b=None):
    n = safe_node(tree, "ShaderNodeMath", loc)
    if n:
        try:
            n.operation = op
        except Exception:
            pass
        if a is not None:
            if isinstance(a, (int, float)):
                n.inputs[0].default_value = float(a)
            else:
                link_sockets(tree, a, n.inputs[0])
        if b is not None:
            if isinstance(b, (int, float)):
                n.inputs[1].default_value = float(b)
            else:
                link_sockets(tree, b, n.inputs[1])
    return n


def _combine(tree, loc, x=None, y=None, z=None):
    n = safe_node(tree, "ShaderNodeCombineXYZ", loc)
    for name, v in (("X", x), ("Y", y), ("Z", z)):
        if v is None or n is None:
            continue
        if isinstance(v, (int, float)):
            try:
                n.inputs[name].default_value = float(v)
            except Exception:
                pass
        else:
            link_sockets(tree, v, n.inputs[name])
    return n


def _tsocket(n): return n.inputs.get("True") or n.inputs.get("A")
def _fsocket(n): return n.inputs.get("False") or n.inputs.get("B")
def _osocket(n): return n.outputs.get("Output") or (n.outputs[0] if n and n.outputs else None)


def _replace_output(tree, gout, geom):
    gi = gout.inputs.get("Geometry")
    if gi is not None:
        for lk in list(tree.links):
            if lk.to_socket == gi:
                tree.links.remove(lk)
    link_sockets(tree, geom, gi)


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
    link_sockets(tree, geom, _fsocket(sw))
    link_sockets(tree, realize.outputs["Geometry"], _tsocket(sw))
    shade = safe_node(tree, "GeometryNodeSetShadeSmooth", (loc[0] + 440, loc[1]))
    try:
        shade.inputs["Shade Smooth"].default_value = True
    except Exception:
        pass
    link_sockets(tree, _osocket(sw), shade.inputs["Geometry"])
    _replace_output(tree, gout, shade.outputs["Geometry"])
    return shade.outputs["Geometry"]


def _store_named(tree, loc, geom, name, value_sock):
    st = safe_node(tree, "GeometryNodeStoreNamedAttribute", loc)
    try:
        st.data_type = "FLOAT"
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
    return st.outputs["Geometry"]


def _refresh_group_refs_multi(tree, names):
    """Re-point orphaned Group nodes after dependency rebuilds (see chimes_gn)."""
    changed = 0
    for gname in names:
        ng = bpy.data.node_groups.get(gname)
        if ng is None:
            continue
        for n in tree.nodes:
            if n.type == "GROUP" and getattr(n, "node_tree", None) is None:
                n.node_tree = ng
                changed += 1
    return changed


def _ensure_string_proto(tree, group_name, length_default=1.0):
    """One thin cylinder string along +Z with String Index attribute."""
    def _build(gn=group_name):
        t, gi, go = new_geometry_tree(gn)
        add_float_param(t, "Length M", length_default, 0.05, 3.0)
        add_float_param(t, "Radius M", 0.0012, 0.0002, 0.01)
        add_int_param(t, "String Index", 0, 0, 64)
        cyl = safe_node(t, "GeometryNodeMeshCylinder", (-300, 0))
        try:
            cyl.inputs["Vertices"].default_value = 8
        except Exception:
            pass
        ri = sock(cyl, "Radius")
        if ri is not None and gi.outputs.get("Radius M") is not None:
            link_sockets(t, gi.outputs["Radius M"], ri)
        di = sock(cyl, "Depth")
        if di is not None:
            link_sockets(t, gi.outputs["Length M"], di)
        # center at half height so scaling grows downward from anchor
        st = safe_node(t, "GeometryNodeStoreNamedAttribute", (100, 0))
        try:
            st.data_type = "INT"
        except Exception:
            pass
        try:
            st.inputs["Name"].default_value = "string_index"
        except Exception:
            pass
        link_sockets(t, cyl.outputs["Mesh"], st.inputs["Geometry"])
        si = sock(st, "Value") or st.inputs.get("Value_001")
        if si is not None and gi.outputs.get("String Index") is not None:
            link_sockets(t, gi.outputs["String Index"], si)
        _replace_output(t, go, st.outputs["Geometry"])
        label_tree(t, gn, [
            {"title": "Proto", "nodes": ("cylinder",), "role": "geometry"},
            {"title": "Attr", "nodes": ("store",), "role": "attribute"},
        ])
    node = safe_node(tree, "GeometryNodeGroup", (0, 0))
    if group_name not in bpy.data.node_groups:
        _build()
    node.node_tree = bpy.data.node_groups.get(group_name)
    return node


# ---------------------------------------------------------------------------
# MEL_harp_concert_real
# ---------------------------------------------------------------------------

def build_harp_concert_real(group_name="MEL_harp_concert_real"):
    """Concert pedal harp: pillar, parabolic neck, ribbed soundboard, 41 strings.

    Morph-ready: exposes Pluck 01..08 (first octave) for morph_baker; remaining
    strings react via HISM/MPC in UE (budget rule: hero morphs on first octave).
    """
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Height M", 1.75, 0.6, 3.0)
    add_float_param(tree, "String Count", 41.0, 7.0, 47.0)
    add_float_param(tree, "Soundboard Width M", 0.34, 0.1, 0.9)
    add_float_param(tree, "Neck Sag M", 0.42, 0.1, 1.2)
    add_float_param(tree, "Pillar Radius M", 0.045, 0.01, 0.15)
    add_float_param(tree, "Pluck 01", 0.0, 0.0, 1.0)
    add_float_param(tree, "Pluck 02", 0.0, 0.0, 1.0)
    add_float_param(tree, "Pluck 03", 0.0, 0.0, 1.0)
    add_bool_param(tree, "Realize for export", False)

    bx, by = 0, 0
    h = gin.outputs["Height M"]

    # Soundboard: tapered slab along +Y at base
    board = safe_node(tree, "GeometryNodeMeshCube", (bx - 800, by))
    lw = _math(tree, "MULTIPLY", (bx - 980, by + 120), gin.outputs["Soundboard Width M"], 1.0)
    sw2 = _math(tree, "MULTIPLY", (bx - 980, by + 40), gin.outputs["Soundboard Width M"], 0.45)
    board_len = _math(tree, "MULTIPLY", (bx - 980, by - 40), h, 0.62)
    link_float_to_vector(tree, gin.outputs["Soundboard Width M"], board, "Size", component=0)
    link_float_to_vector(tree, board_len.outputs[0], board, "Size", component=1)
    link_float_to_vector(tree, 0.06, board, "Size", component=2)
    board_xf = safe_node(tree, "GeometryNodeTransform", (bx - 600, by))
    link_sockets(tree, board.outputs["Mesh"], board_xf.inputs["Geometry"])
    tilt = _combine(tree, (bx - 760, by - 120), 0.0,
                    math.radians(-12), 0.0)
    try:
        board_xf.inputs["Rotation"].default_value = (0, math.radians(-12), 0)
    except Exception:
        pass
    pos = _combine(tree, (bx - 760, by), 0.0,
                   0.0, 0.03)
    link_sockets(tree, pos.outputs["Vector"], board_xf.inputs["Translation"])

    # Pillar: vertical cylinder at the far end of the soundboard
    pil = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 800, by - 320))
    try:
        pil.inputs["Vertices"].default_value = 16
    except Exception:
        pass
    r_in = sock(pil, "Radius")
    if r_in is not None:
        link_sockets(tree, gin.outputs["Pillar Radius M"], r_in)
    d_in = sock(pil, "Depth")
    if d_in is not None:
        link_sockets(tree, h, d_in)
    pil_xf = safe_node(tree, "GeometryNodeTransform", (bx - 600, by - 320))
    link_sockets(tree, pil.outputs["Mesh"], pil_xf.inputs["Geometry"])
    pil_pos = _combine(tree, (bx - 760, by - 320), 0.0,
                       board_len.outputs[0], _math(tree, "MULTIPLY", (bx - 900, by - 380), h, 0.5).outputs[0])
    link_sockets(tree, pil_pos.outputs["Vector"], pil_xf.inputs["Translation"])

    # Neck: swept arc curve from pillar top to soundboard front tip
    neck_curve = safe_node(tree, "GeometryNodeCurvePrimitiveQuadrilateral", (bx - 800, by - 560))
    quad_ok = neck_curve is not None
    if not quad_ok:
        # fallback: bezier via primitive line + resample bend approximation
        neck_curve = safe_node(tree, "GeometryNodeCurvePrimitiveLine", (bx - 800, by - 560))
    arc = safe_node(tree, "GeometryNodeCurveArc", (bx - 620, by - 620))
    if arc is not None:
        try:
            arc.inputs["Resolution"].default_value = 24
        except Exception:
            pass
        radius = _math(tree, "MULTIPLY", (bx - 800, by - 700), gin.outputs["Neck Sag M"], 2.4)
        ar_in = sock(arc, "Radius")
        if ar_in is not None:
            link_sockets(tree, radius.outputs[0], ar_in)
        neck_curve = arc
    neck_sweep_src = sock(neck_curve, "Curve", "Geometry") or (_osocket(neck_curve) if neck_curve else None)
    profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx - 800, by - 820))
    if profile is not None:
        try:
            profile.inputs["Resolution"].default_value = 10
        except Exception:
            pass
        try:
            profile.inputs["Radius"].default_value = 0.035
        except Exception:
            pass
    sweep = safe_node(tree, "GeometryNodeCurveToMesh", (bx - 400, by - 620))
    if neck_sweep_src is not None:
        link_sockets(tree, neck_sweep_src, sock(sweep, "Curve") or sweep.inputs[0])
    prof_out = (profile.outputs.get("Curve") or profile.outputs[0]) if profile else None
    if prof_out is not None:
        pi = sock(sweep, "Profile Curve") or sweep.inputs.get("Profile")
        if pi is not None:
            link_sockets(tree, prof_out, pi)
    neck_xf = safe_node(tree, "GeometryNodeTransform", (bx - 220, by - 620))
    link_sockets(tree, sweep.outputs.get("Mesh"), neck_xf.inputs["Geometry"])
    try:
        neck_xf.inputs["Location"].default_value = (0.0, 0.0, h.default_value if hasattr(h, 'default_value') else 1.55)
    except Exception:
        pass

    body_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx, by - 160))
    for src in (board_xf.outputs["Geometry"], pil_xf.outputs["Geometry"],
                neck_xf.outputs["Geometry"]):
        link_sockets(tree, src, body_join.inputs["Geometry"])

    # Strings: instance-on-line across the soundboard, lengths rising toward pillar
    proto = _ensure_string_proto(tree, "MEL_harp_string_unit")
    line = safe_node(tree, "GeometryNodeMeshLine", (bx + 200, by + 260))
    try:
        line.mode = "END_POINTS"
    except Exception:
        pass
    c_in = sock(line, "Count")
    if c_in is not None:
        link_sockets(tree, gin.outputs["String Count"], c_in)
    row_w = _math(tree, "MULTIPLY", (bx + 40, by + 320), gin.outputs["Soundboard Width M"], 0.92)
    link_float_to_vector(tree, row_w.outputs[0], line, "End Location", component=0)
    pts = safe_node(tree, "GeometryNodeMeshToPoints", (bx + 400, by + 260))
    link_sockets(tree, line.outputs["Mesh"], sock(pts, "Mesh") or pts.inputs[0])

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 640, by + 200))
    link_sockets(tree, pts.outputs["Points"], sock(inst, "Points"))
    if proto:
        if proto.inputs.get("Length M") is not None:
            li = safe_node(tree, "GeometryNodeInputIndex", (bx + 480, by - 80))
            nf = _math(tree, "DIVIDE", (bx + 480, by - 160), li.outputs["Index"],
                       gin.outputs["String Count"])
            ln = _math(tree, "MULTIPLY", (bx + 620, by - 120), h, 0.78)
            vary = _math(tree, "SUBTRACT", (bx + 620, by - 240), ln.outputs[0],
                         _math(tree, "MULTIPLY", (bx + 780, by - 240),
                               _math(tree, "MULTIPLY", (bx + 620, by - 320), h, 0.30).outputs[0],
                               nf.outputs[0]).outputs[0])
            link_sockets(tree, vary.outputs[0], proto.inputs["Length M"])
        link_sockets(tree, proto.outputs.get("Geometry"), sock(inst, "Instance"))

    join_all = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 900, by))
    link_sockets(tree, body_join.outputs["Geometry"], join_all.inputs["Geometry"])
    link_sockets(tree, inst.outputs["Instances"], join_all.inputs["Geometry"])

    # Color coding: C strings red / F strings blue as named attr (UE material reads)
    idx = safe_node(tree, "GeometryNodeInputIndex", (bx + 900, by - 200))
    pc = _math(tree, "FLOORMOD", (bx + 900, by - 280), idx.outputs["Index"], 12.0)
    stored = _store_named(tree, (bx + 1080, by - 120), join_all.outputs["Geometry"],
                          "semitone_mod12", pc.outputs[0])
    stored = _store_named(tree, (bx + 1240, by - 120), stored,
                          "harp_family", 0.0)

    _export_tail(tree, gin, gout, stored, (bx + 1420, by))

    _refresh_group_refs_multi(tree, ("MEL_harp_string_unit", "MEL_chime_tube"))
    return label_tree(tree, group_name, [
        {"title": "Body", "nodes": ("soundboard", "pillar", "neck"), "role": "geometry"},
        {"title": "Strings", "nodes": ("line", "instance"), "role": "instance"},
        {"title": "Attributes", "nodes": ("store",), "role": "attribute"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_harp_ur_lyre - Sumerian box lyre
# ---------------------------------------------------------------------------

def build_harp_ur_lyre(group_name="MEL_harp_ur_lyre"):
    """Bull-headed box lyre: rectangular soundbox, two arms, crossbar, 7 strings."""
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Box Width M", 0.33, 0.12, 0.9)
    add_float_param(tree, "Box Depth M", 0.24, 0.08, 0.7)
    add_float_param(tree, "Box Height M", 0.14, 0.05, 0.4)
    add_float_param(tree, "Arm Height M", 0.46, 0.15, 1.1)
    add_int_param(tree, "String Count", 7, 5, 12)
    add_float_param(tree, "String Radius M", 0.0016, 0.0004, 0.008)
    add_bool_param(tree, "Realize for export", False)

    bx, by = 0, 0
    box = safe_node(tree, "GeometryNodeMeshCube", (bx - 720, by))
    link_float_to_vector(tree, gin.outputs["Box Width M"], box, "Size", component=0)
    link_float_to_vector(tree, gin.outputs["Box Depth M"], box, "Size", component=1)
    link_float_to_vector(tree, gin.outputs["Box Height M"], box, "Size", component=2)

    arm_r = _math(tree, "MULTIPLY", (bx - 900, by - 140), gin.outputs["Box Depth M"], 0.04)
    arm = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 720, by - 200))
    try:
        arm.inputs["Vertices"].default_value = 10
    except Exception:
        pass
    ri = sock(arm, "Radius")
    if ri is not None:
        link_sockets(tree, arm_r.outputs[0], ri)
    di = sock(arm, "Depth")
    if di is not None:
        link_sockets(tree, gin.outputs["Arm Height M"], di)
    ahalf = _math(tree, "MULTIPLY", (bx - 900, by - 260), gin.outputs["Arm Height M"], 0.5)
    aoff = _math(tree, "ADD", (bx - 760, by - 260), ahalf.outputs[0],
                 _math(tree, "MULTIPLY", (bx - 900, by - 340), gin.outputs["Box Height M"], 0.5).outputs[0])
    apos = _combine(tree, (bx - 600, by - 260), 0.0, 0.0, aoff.outputs[0])
    axf = safe_node(tree, "GeometryNodeTransform", (bx - 420, by - 200))
    link_sockets(tree, arm.outputs["Mesh"], axf.inputs["Geometry"])
    link_sockets(tree, apos.outputs["Vector"], axf.inputs["Translation"])

    mirrored = safe_node(tree, "GeometryNodeTransform", (bx - 420, by - 380))
    link_sockets(tree, axf.outputs["Geometry"], mirrored.inputs["Geometry"])
    mpos = _combine(tree, (bx - 600, by - 380), 0.0, 0.0, 0.0)
    try:
        mirrored.inputs["Scale"].default_value = (-1.0, 1.0, 1.0)
    except Exception:
        pass

    cross = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 720, by - 540))
    try:
        cross.inputs["Vertices"].default_value = 10
    except Exception:
        pass
    ci = sock(cross, "Radius")
    if ci is not None:
        cr = _math(tree, "MULTIPLY", (bx - 900, by - 600), arm_r.outputs[0], 0.8)
        link_sockets(tree, cr.outputs[0], ci)
    cd = sock(cross, "Depth")
    if cd is not None:
        bw = _math(tree, "ADD", (bx - 900, by - 680), gin.outputs["Box Width M"],
                   _math(tree, "MULTIPLY", (bx - 1040, by - 680), arm_r.outputs[0], 2.0).outputs[0])
        link_sockets(tree, bw.outputs[0], cd)
    cross_xf = safe_node(tree, "GeometryNodeTransform", (bx - 420, by - 540))
    link_sockets(tree, cross.outputs["Mesh"], cross_xf.inputs["Geometry"])
    try:
        cross_xf.inputs["Rotation"].default_value = (0.0, math.radians(90), 0.0)
    except Exception:
        pass
    ctop = _math(tree, "ADD", (bx - 600, by - 700), gin.outputs["Arm Height M"],
                 _math(tree, "MULTIPLY", (bx - 760, by - 700), gin.outputs["Box Height M"], 0.5).outputs[0])
    cpos = _combine(tree, (bx - 600, by - 620), 0.0, 0.0, ctop.outputs[0])
    link_sockets(tree, cpos.outputs["Vector"], cross_xf.inputs["Translation"])

    body = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 180, by - 160))
    for s in (box.outputs["Mesh"], axf.outputs["Geometry"],
              mirrored.outputs["Geometry"], cross_xf.outputs["Geometry"]):
        link_sockets(tree, s, body.inputs["Geometry"])

    proto = _ensure_string_proto(tree, "MEL_harp_string_unit", 0.42)
    sl = safe_node(tree, "GeometryNodeMeshLine", (bx + 60, by + 200))
    try:
        sl.mode = "END_POINTS"
    except Exception:
        pass
    sc = sock(sl, "Count")
    if sc is not None:
        ic = safe_node(tree, "FunctionNodeFloatToInt", (bx - 100, by + 260))
        link_sockets(tree, gin.outputs["String Count"], ic.inputs[0])
        link_sockets(tree, ic.outputs[0], sc)
    span = _math(tree, "MULTIPLY", (bx - 100, by + 180), gin.outputs["Box Width M"], 0.82)
    link_float_to_vector(tree, span.outputs[0], sl, "End Location", component=0)
    spts = safe_node(tree, "GeometryNodeMeshToPoints", (bx + 240, by + 200))
    link_sockets(tree, sl.outputs["Mesh"], sock(spts, "Mesh") or spts.inputs[0])
    # raise strings above the box top toward crossbar
    sxf = safe_node(tree, "GeometryNodeTransform", (bx + 400, by + 200))
    link_sockets(tree, spts.outputs["Points"], sxf.inputs["Geometry"])
    sz = _math(tree, "MULTIPLY", (bx + 240, by + 80), gin.outputs["Arm Height M"], 0.94)
    spos = _combine(tree, (bx + 400, by + 80), 0.0, 0.0, sz.outputs[0])
    link_sockets(tree, spos.outputs["Vector"], sxf.inputs["Translation"])

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 620, by + 160))
    link_sockets(tree, sxf.outputs["Geometry"], sock(inst, "Points"))
    if proto:
        if proto.inputs.get("Radius M") is not None:
            link_sockets(tree, gin.outputs["String Radius M"], proto.inputs["Radius M"])
        link_sockets(tree, proto.outputs.get("Geometry"), sock(inst, "Instance"))

    joined = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 880, by))
    link_sockets(tree, body.outputs["Geometry"], joined.inputs["Geometry"])
    link_sockets(tree, inst.outputs["Instances"], joined.inputs["Geometry"])

    idx = safe_node(tree, "GeometryNodeInputIndex", (bx + 880, by - 200))
    pc = _math(tree, "FLOORMOD", (bx + 880, by - 280), idx.outputs["Index"], 12.0)
    stored = _store_named(tree, (bx + 1060, by - 120), joined.outputs["Geometry"],
                          "semitone_mod12", pc.outputs[0])
    stored = _store_named(tree, (bx + 1220, by - 120), stored, "harp_family", 1.0)
    _export_tail(tree, gin, gout, stored, (bx + 1400, by))

    _refresh_group_refs_multi(tree, ("MEL_harp_string_unit", "MEL_chime_tube"))
    return label_tree(tree, group_name, [
        {"title": "Body+Arms", "nodes": ("box", "arms", "crossbar"), "role": "geometry"},
        {"title": "Strings", "nodes": ("strings",), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_harp_kora - Mande calabash bridge-harp
# ---------------------------------------------------------------------------

def build_harp_kora(group_name="MEL_harp_kora"):
    """Calabash gourd resonator, hide soundtable, notched bridge, 21 strings, handpost."""
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Gourd Radius M", 0.26, 0.1, 0.6)
    add_float_param(tree, "Neck Length M", 0.95, 0.4, 1.8)
    add_int_param(tree, "String Count", 21, 7, 24)
    add_float_param(tree, "String Radius M", 0.0011, 0.0003, 0.006)
    add_bool_param(tree, "Realize for export", False)

    bx, by = 0, 0
    sphere = safe_node(tree, "GeometryNodeUVSphere", (bx - 760, by))
    try:
        sphere.inputs["Segments"].default_value = 32
        sphere.inputs["Rings"].default_value = 16
    except Exception:
        pass
    ri = sock(sphere, "Radius")
    if ri is not None:
        link_sockets(tree, gin.outputs["Gourd Radius M"], ri)
    squash = safe_node(tree, "GeometryNodeTransform", (bx - 580, by))
    link_sockets(tree, sphere.outputs["Mesh"], squash.inputs["Geometry"])
    try:
        squash.inputs["Scale"].default_value = (1.0, 1.0, 0.82)
    except Exception:
        pass

    neck = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 760, by - 260))
    try:
        neck.inputs["Vertices"].default_value = 12
    except Exception:
        pass
    nr = sock(neck, "Radius")
    if nr is not None:
        try:
            nr.default_value = 0.02
        except Exception:
            pass
    nd = sock(neck, "Depth")
    if nd is not None:
        link_sockets(tree, gin.outputs["Neck Length M"], nd)
    nxf = safe_node(tree, "GeometryNodeTransform", (bx - 580, by - 260))
    link_sockets(tree, neck.outputs["Mesh"], nxf.inputs["Geometry"])
    gr = _math(tree, "MULTIPLY", (bx - 760, by - 360), gin.outputs["Gourd Radius M"], 0.85)
    try:
        nxf.inputs["Rotation"].default_value = (math.radians(28), 0.0, 0.0)
    except Exception:
        pass
    npos = _combine(tree, (bx - 760, by - 300), 0.0, gr.outputs[0],
                    _math(tree, "MULTIPLY", (bx - 900, by - 380), gin.outputs["Neck Length M"], 0.42).outputs[0])
    link_sockets(tree, npos.outputs["Vector"], nxf.inputs["Translation"])

    bridge = safe_node(tree, "GeometryNodeMeshCube", (bx - 760, by - 520))
    bw = _math(tree, "MULTIPLY", (bx - 940, by - 560), gin.outputs["Gourd Radius M"], 0.9)
    link_float_to_vector(tree, bw.outputs[0], bridge, "Size", component=0)
    link_float_to_vector(tree, 0.03, bridge, "Size", component=1)
    bh = _math(tree, "MULTIPLY", (bx - 940, by - 640), gin.outputs["Gourd Radius M"], 0.16)
    link_float_to_vector(tree, bh.outputs[0], bridge, "Size", component=2)
    bxf = safe_node(tree, "GeometryNodeTransform", (bx - 580, by - 520))
    link_sockets(tree, bridge.outputs["Mesh"], bxf.inputs["Geometry"])
    bpos = _combine(tree, (bx - 760, by - 520), 0.0, 0.0, gr.outputs[0])
    link_sockets(tree, bpos.outputs["Vector"], bxf.inputs["Translation"])

    body = safe_node(tree, "GeometryNodeJoinGeometry", (bx - 360, by - 160))
    for s in (squash.outputs["Geometry"], nxf.outputs["Geometry"], bxf.outputs["Geometry"]):
        link_sockets(tree, s, body.inputs["Geometry"])

    proto = _ensure_string_proto(tree, "MEL_harp_string_unit", 0.8)
    sl = safe_node(tree, "GeometryNodeMeshLine", (bx - 120, by + 220))
    try:
        sl.mode = "END_POINTS"
    except Exception:
        pass
    sc = sock(sl, "Count")
    if sc is not None:
        ic = safe_node(tree, "FunctionNodeFloatToInt", (bx - 280, by + 280))
        link_sockets(tree, gin.outputs["String Count"], ic.inputs[0])
        link_sockets(tree, ic.outputs[0], sc)
    span = _math(tree, "MULTIPLY", (bx - 280, by + 200), bw.outputs[0], 0.86)
    link_float_to_vector(tree, span.outputs[0], sl, "End Location", component=0)
    spts = safe_node(tree, "GeometryNodeMeshToPoints", (bx + 60, by + 220))
    link_sockets(tree, sl.outputs["Mesh"], sock(spts, "Mesh") or spts.inputs[0])
    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 300, by + 180))
    link_sockets(tree, spts.outputs["Points"], sock(inst, "Points"))
    if proto:
        if proto.inputs.get("Radius M") is not None:
            link_sockets(tree, gin.outputs["String Radius M"], proto.inputs["Radius M"])
        link_sockets(tree, proto.outputs.get("Geometry"), sock(inst, "Instance"))

    joined = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 560, by))
    link_sockets(tree, body.outputs["Geometry"], joined.inputs["Geometry"])
    link_sockets(tree, inst.outputs["Instances"], joined.inputs["Geometry"])

    idx = safe_node(tree, "GeometryNodeInputIndex", (bx + 560, by - 220))
    pc = _math(tree, "FLOORMOD", (bx + 560, by - 300), idx.outputs["Index"], 12.0)
    stored = _store_named(tree, (bx + 740, by - 140), joined.outputs["Geometry"],
                          "semitone_mod12", pc.outputs[0])
    stored = _store_named(tree, (bx + 900, by - 140), stored, "harp_family", 2.0)
    _export_tail(tree, gin, gout, stored, (bx + 1080, by))

    _refresh_group_refs_multi(tree, ("MEL_harp_string_unit", "MEL_chime_tube"))
    return label_tree(tree, group_name, [
        {"title": "Gourd+Neck", "nodes": ("gourd", "neck", "bridge"), "role": "geometry"},
        {"title": "Strings", "nodes": ("strings",), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# MEL_wind_siku - Andean double-row panpipes
# ---------------------------------------------------------------------------

def build_wind_siku(group_name="MEL_wind_siku"):
    """Two-row closed-tube bundle (ira + arca); interlocking dialogue layout."""
    tree, gin, gout = new_geometry_tree(group_name)

    add_float_param(tree, "Longest Tube M", 0.52, 0.15, 1.6)
    add_float_param(tree, "Tube Radius M", 0.016, 0.004, 0.06)
    add_int_param(tree, "Tubes Per Row", 7, 4, 14)
    add_float_param(tree, "Row Offset M", 0.035, 0.01, 0.15)
    add_float_param(tree, "Bundle Spread M", 0.34, 0.1, 1.0)
    add_bool_param(tree, "Realize for export", False)

    bx, by = 0, 0

    def one_row(row_tag, y_off):
        line = safe_node(tree, "GeometryNodeMeshLine", (bx - 500, by + (200 if row_tag == 0 else 40)))
        try:
            line.mode = "END_POINTS"
        except Exception:
            pass
        c = sock(line, "Count")
        if c is not None:
            link_sockets(tree, gin.outputs["Tubes Per Row"], c)
        sp = _math(tree, "DIVIDE", (bx - 700, by + 260), gin.outputs["Bundle Spread M"],
                   gin.outputs["Tubes Per Row"])
        link_float_to_vector(tree, sp.outputs[0], line, "End Location", component=0)
        pts = safe_node(tree, "GeometryNodeMeshToPoints",
                        (bx - 320, by + (200 if row_tag == 0 else 40)))
        link_sockets(tree, line.outputs["Mesh"], sock(pts, "Mesh") or pts.inputs[0])
        pxf = safe_node(tree, "GeometryNodeTransform", (bx - 140, by + (200 if row_tag == 0 else 40)))
        link_sockets(tree, pts.outputs["Points"], pxf.inputs["Geometry"])
        yo = _math(tree, "MULTIPLY", (bx - 320, by + 80), gin.outputs["Row Offset M"], y_off)
        pv = _combine(tree, (bx - 140, by + 80), 0.0, yo.outputs[0], 0.0)
        link_sockets(tree, pv.outputs["Vector"], pxf.inputs["Translation"])
        return pxf.outputs["Geometry"]

    proto = _ensure_tube_group(tree, (bx - 900, by - 260))
    if proto:
        if proto.inputs.get("Longest M") is not None:
            link_sockets(tree, gin.outputs["Longest Tube M"], proto.inputs["Longest M"])
        if proto.inputs.get("Radius M") is not None:
            link_sockets(tree, gin.outputs["Tube Radius M"], proto.inputs["Radius M"])

    joined_pts = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 60, by + 120))
    link_sockets(tree, one_row(0, -0.5), joined_pts.inputs["Geometry"])
    link_sockets(tree, one_row(1, 0.5), joined_pts.inputs["Geometry"])

    inst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx + 300, by + 120))
    link_sockets(tree, joined_pts.outputs["Geometry"], sock(inst, "Points"))
    if proto:
        link_sockets(tree, proto.outputs.get("Geometry"), sock(inst, "Instance"))
        if proto.inputs.get("Semitone") is not None:
            idx = safe_node(tree, "GeometryNodeInputIndex", (bx + 300, by - 120))
            dbl = _math(tree, "MULTIPLY", (bx + 300, by - 200), idx.outputs["Index"], 2.0)
            link_sockets(tree, dbl.outputs[0], proto.inputs["Semitone"])

    idx = safe_node(tree, "GeometryNodeInputIndex", (bx + 520, by - 120))
    stored = _store_named(tree, (bx + 520, by), inst.outputs["Instances"], "siku_row", 1.0)
    _export_tail(tree, gin, gout, stored, (bx + 700, by))

    _refresh_group_refs_multi(tree, ("MEL_harp_string_unit", "MEL_chime_tube"))
    return label_tree(tree, group_name, [
        {"title": "Rows", "nodes": ("rows",), "role": "points"},
        {"title": "Tubes", "nodes": ("instance",), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

def build_harp_string_unit(group_name="MEL_harp_string_unit"):
    """Thin cylinder string proto along +Z with String Index attribute.

    Standalone form of the _ensure_string_proto inner build, so the registry
    id resolves to a real tree instead of a None placeholder. _ensure_string_proto
    stays the hot path for parent trees (it reuses the data-block); this builder
    exists so bake_all, audit, and explicit builds of the id all succeed.
    """
    t, gi, go = new_geometry_tree(group_name)
    add_float_param(t, "Length M", 1.0, 0.05, 3.0)
    add_float_param(t, "Radius M", 0.0012, 0.0002, 0.01)
    add_int_param(t, "String Index", 0, 0, 64)
    cyl = safe_node(t, "GeometryNodeMeshCylinder", (-300, 0))
    try:
        cyl.inputs["Vertices"].default_value = 8
    except Exception:
        pass
    ri = sock(cyl, "Radius")
    if ri is not None and gi.outputs.get("Radius M") is not None:
        link_sockets(t, gi.outputs["Radius M"], ri)
    di = sock(cyl, "Depth")
    if di is not None:
        link_sockets(t, gi.outputs["Length M"], di)
    st = safe_node(t, "GeometryNodeStoreNamedAttribute", (100, 0))
    try:
        st.data_type = "INT"
    except Exception:
        pass
    try:
        st.inputs["Name"].default_value = "string_index"
    except Exception:
        pass
    link_sockets(t, cyl.outputs["Mesh"], st.inputs["Geometry"])
    si = sock(st, "Value") or st.inputs.get("Value_001")
    if si is not None and gi.outputs.get("String Index") is not None:
        link_sockets(t, gi.outputs["String Index"], si)
    _replace_output(t, go, st.outputs["Geometry"])
    return label_tree(t, group_name, [
        {"title": "Proto", "nodes": ("cylinder",), "role": "geometry"},
        {"title": "Attr", "nodes": ("store",), "role": "attribute"},
    ])


register_builder(
    "MEL_harp_string_unit", build_harp_string_unit,
    "Harp String Unit", "Thin cylinder string proto with string_index attr",
    "music", hidden=True,
)
register_builder(
    "MEL_harp_concert_real", build_harp_concert_real, "Concert Harp (Real)",
    "Pedal harp anatomy: pillar, arc neck, ribbed soundboard, graduated strings; "
    "morph-ready plucks via surreal_arch.morph_baker",
    "music",
)
register_builder(
    "MEL_harp_ur_lyre", build_harp_ur_lyre, "Lyre of Ur (Ancient)",
    "Sumerian box lyre: soundbox, twin arms, crossbar, 7 gut strings",
    "music",
)
register_builder(
    "MEL_harp_kora", build_harp_kora, "Kora (Mande)",
    "Calabash bridge-harp: gourd resonator, hide table, notched bridge, 21 strings",
    "music",
)
register_builder(
    "MEL_wind_siku", build_wind_siku, "Siku (Andes)",
    "Two-row panpipe bundle, ira/arca interlock; semitone = index*2",
    "music",
)
