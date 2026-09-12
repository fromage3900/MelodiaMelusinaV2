"""Music + Euro remainder builders — ported from the monolith (P2 final batch).

MUSIC: note_head, treble_clef, staff, sheet_music_railing, cascading_beams
EURO/ORNAMENT: gothic_bay, gothic_portal, gothic_buttress_kit, gothic_tracery_panel,
               romanesque_apse, romanesque_arcade_bay, venetian_loggia_bay,
               palazzo, lancet, rose_window

Stubs route to existing package builders via _ensure_group_node.
Full builders port the monolith body with props.X → add_*_param + gin.outputs["X"].
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, add_string_param,
    make_group_input, sweep_profile, mesh_boolean_node,
    register_builder, sock,
)


# ---------------------------------------------------------------------------
# Helpers (ported from monolith / music.py)
# ---------------------------------------------------------------------------

def _ensure_group_node(tree, group_name, builder, loc):
    """Create a group node referencing an existing registered builder."""
    if group_name not in bpy.data.node_groups:
        builder(group_name)
    node = safe_node(tree, "GeometryNodeGroup", loc)
    if node:
        node.node_tree = bpy.data.node_groups.get(group_name)
    return node


def _switch_geo(tree, loc, switch_sock, true_geo, false_geo):
    """Geometry switch node helper."""
    sw = safe_node(tree, "GeometryNodeSwitch", loc)
    if sw:
        try:
            sw.input_type = "GEOMETRY"
        except Exception:
            pass
        link_sockets(tree, switch_sock, sw.inputs["Switch"])
        true_in = sw.inputs.get("True") or sw.inputs.get("TRUE")
        false_in = sw.inputs.get("False") or sw.inputs.get("FALSE")
        if true_geo is not None and true_in is not None:
            link_sockets(tree, true_geo, true_in)
        if false_geo is not None and false_in is not None:
            link_sockets(tree, false_geo, false_in)
    return sw


def _make_harmonic_value(tree, index_socket, freq_a, freq_b, layers, x, y):
    """Ported from monolith make_harmonic_value. Returns a value socket."""
    m1 = safe_node(tree, 'ShaderNodeMath', (x, y))
    if m1:
        m1.operation = 'MULTIPLY'
        m1.inputs[1].default_value = freq_a
        link_sockets(tree, index_socket, m1.inputs[0])
    s1 = safe_node(tree, 'ShaderNodeMath', (x + 200, y))
    if s1:
        s1.operation = 'SINE'
        link_sockets(tree, m1.outputs['Value'], s1.inputs[0])
    color_node(s1, "ornament")

    if layers <= 1:
        return s1.outputs['Value']

    m2 = safe_node(tree, 'ShaderNodeMath', (x, y - 200))
    if m2:
        m2.operation = 'MULTIPLY'
        m2.inputs[1].default_value = freq_b
        link_sockets(tree, index_socket, m2.inputs[0])
    s2 = safe_node(tree, 'ShaderNodeMath', (x + 200, y - 200))
    if s2:
        s2.operation = 'SINE'
        link_sockets(tree, m2.outputs['Value'], s2.inputs[0])
    color_node(s2, "ornament")

    add = safe_node(tree, 'ShaderNodeMath', (x + 400, y - 100))
    if add:
        add.operation = 'ADD'
        link_sockets(tree, s1.outputs['Value'], add.inputs[0])
        link_sockets(tree, s2.outputs['Value'], add.inputs[1])

    if layers <= 2:
        return add.outputs['Value']

    m3 = safe_node(tree, 'ShaderNodeMath', (x, y - 400))
    if m3:
        m3.operation = 'MULTIPLY'
        m3.inputs[1].default_value = freq_a * 2.0
        link_sockets(tree, index_socket, m3.inputs[0])
    s3 = safe_node(tree, 'ShaderNodeMath', (x + 200, y - 400))
    if s3:
        s3.operation = 'SINE'
        link_sockets(tree, m3.outputs['Value'], s3.inputs[0])
    color_node(s3, "ornament")

    add2 = safe_node(tree, 'ShaderNodeMath', (x + 400, y - 300))
    if add2:
        add2.operation = 'ADD'
        link_sockets(tree, add.outputs['Value'], add2.inputs[0])
        link_sockets(tree, s3.outputs['Value'], add2.inputs[1])
    final = add2

    for i, fmul in enumerate([3.0, 5.0][:layers - 3], start=4):
        mn = safe_node(tree, 'ShaderNodeMath', (x, y - 200 * i - 200))
        if mn:
            mn.operation = 'MULTIPLY'
            mn.inputs[1].default_value = freq_b * fmul / 3.0
            link_sockets(tree, index_socket, mn.inputs[0])
        sn = safe_node(tree, 'ShaderNodeMath', (x + 200, y - 200 * i - 200))
        if sn:
            sn.operation = 'SINE'
            link_sockets(tree, mn.outputs['Value'], sn.inputs[0])
        addn = safe_node(tree, 'ShaderNodeMath', (x + 400, y - 200 * i - 100))
        if addn:
            addn.operation = 'ADD'
            link_sockets(tree, final.outputs['Value'], addn.inputs[0])
            link_sockets(tree, sn.outputs['Value'], addn.inputs[1])
        final = addn

    return final.outputs['Value']


# ---------------------------------------------------------------------------
# MUSIC: NOTE HEAD
# ---------------------------------------------------------------------------

def build_note_head_group(group_name="MEL_music_note_head_mp"):
    """Elliptical note head with optional stem and flag (monolith port)."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Note Size", 0.18, 0.04, 1.0)
    add_string_param(tree, "Note Kind", "QUARTER")
    add_float_param(tree, "Stem Length", 1.2, 0.2, 4.0)
    add_bool_param(tree, "Has Stem", True)
    add_bool_param(tree, "Has Flag", False)

    # Note head - flattened oval
    head = safe_node(tree, "GeometryNodeMeshUVSphere", (bx, by))
    if head:
        head.inputs['Radius'].default_value = 0.09
        head.inputs['Segments'].default_value = 24
        head.inputs['Rings'].default_value = 12

    head_t = safe_node(tree, "GeometryNodeTransform", (bx + 300, by))
    if head_t:
        head_t.inputs['Scale'].default_value = (1.2, 0.85, 0.45)
        head_t.inputs['Rotation'].default_value = (0, math.radians(-15), 0)
        link_sockets(tree, sock(head, "Mesh", outputs=True), head_t.inputs['Geometry'])

    parts = [sock(head_t, "Geometry", outputs=True)]

    # Stem
    stem = safe_node(tree, "GeometryNodeMeshCube", (bx, by + 300))
    if stem:
        stem.inputs['Size'].default_value = (0.05, 0.05, 1.2)

    stem_t = safe_node(tree, "GeometryNodeTransform", (bx + 300, by + 300))
    if stem_t:
        stem_t.inputs['Translation'].default_value = (0.05, 0, 0.6)
        link_sockets(tree, sock(stem, "Mesh", outputs=True), stem_t.inputs['Geometry'])

    stem_switch = _switch_geo(tree, (bx + 500, by + 200),
                               gin.outputs["Has Stem"],
                               sock(stem_t, "Geometry", outputs=True), None)
    if stem_switch:
        parts.append(sock(stem_switch, "Output", outputs=True))

    # Flag
    flag_curve = safe_node(tree, "GeometryNodeCurveArc", (bx, by + 600))
    if flag_curve:
        try:
            flag_curve.mode = 'RADIUS'
        except Exception:
            pass
        flag_curve.inputs['Resolution'].default_value = 16
        flag_curve.inputs['Radius'].default_value = 0.054
        flag_curve.inputs['Sweep Angle'].default_value = math.radians(120)

    flag_profile = safe_node(tree, "GeometryNodeCurvePrimitiveCircle", (bx, by + 800))
    if flag_profile:
        try:
            flag_profile.mode = 'RADIUS'
        except Exception:
            pass
        flag_profile.inputs['Resolution'].default_value = 6
        flag_profile.inputs['Radius'].default_value = 0.007

    flag_sweep = safe_node(tree, "GeometryNodeCurveToMesh", (bx + 300, by + 600))
    if flag_sweep:
        link_sockets(tree, sock(flag_curve, "Curve", outputs=True), flag_sweep.inputs['Curve'])
        link_sockets(tree, sock(flag_profile, "Curve", outputs=True), flag_sweep.inputs.get('Profile Curve') or flag_sweep.inputs.get('Profile'))

    flag_t = safe_node(tree, "GeometryNodeTransform", (bx + 600, by + 600))
    if flag_t:
        flag_t.inputs['Translation'].default_value = (0.05, 0, 1.2)
        flag_t.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
        link_sockets(tree, sock(flag_sweep, "Mesh", outputs=True), flag_t.inputs['Geometry'])

    flag_switch = _switch_geo(tree, (bx + 800, by + 400),
                               gin.outputs["Has Flag"],
                               sock(flag_t, "Geometry", outputs=True), None)
    if flag_switch:
        parts.append(sock(flag_switch, "Output", outputs=True))

    # Join
    join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 1000, by))
    for p in parts:
        if p is not None:
            link_sockets(tree, p, join.inputs['Geometry'])

    link_sockets(tree, sock(join, "Geometry", outputs=True), gout.inputs['Geometry'])

    color_node(head, "geometry")
    color_node(join, "output")

    return tree, gin, gout


# ---------------------------------------------------------------------------
# MUSIC: TREBLE CLEF
# ---------------------------------------------------------------------------

def build_treble_clef_group(group_name="MEL_music_treble_clef_mp"):
    """G-clef ornament (monolith port): flat spiral + S-curve stem + tail + finials."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Clef Size", 2.0, 0.4, 6.0)
    add_float_param(tree, "Clef Thickness", 0.04, 0.008, 0.15)
    add_float_param(tree, "Clef Curls", 1.8, 0.5, 3.0)

    # Profile circle
    profile = safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (bx, by - 300))
    if profile:
        try:
            profile.mode = 'RADIUS'
        except Exception:
            pass
        profile.inputs['Resolution'].default_value = 8
        link_sockets(tree, gin.outputs["Clef Thickness"], profile.inputs['Radius'])
    color_node(profile, "music")

    # Belly spiral - FLAT 2D curl
    spiral = safe_node(tree, 'GeometryNodeCurveSpiral', (bx, by))
    if spiral:
        spiral.inputs['Resolution'].default_value = 96
        link_sockets(tree, gin.outputs["Clef Curls"], spiral.inputs['Rotations'])
        spiral.inputs['Start Radius'].default_value = 0.04
        spiral.inputs['End Radius'].default_value = 0.225
        spiral.inputs['Height'].default_value = 0.0
    color_node(spiral, "music")

    spiral_t = safe_node(tree, 'GeometryNodeTransform', (bx + 300, by))
    if spiral_t:
        spiral_t.inputs['Translation'].default_value = (0, 0, -0.025)
        spiral_t.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
        link_sockets(tree, sock(spiral, "Curve", outputs=True), spiral_t.inputs['Geometry'])

    spiral_sweep = safe_node(tree, 'GeometryNodeCurveToMesh', (bx + 600, by))
    if spiral_sweep:
        link_sockets(tree, sock(spiral_t, "Geometry", outputs=True), spiral_sweep.inputs['Curve'])
        link_sockets(tree, sock(profile, "Curve", outputs=True), spiral_sweep.inputs.get('Profile Curve') or spiral_sweep.inputs.get('Profile'))
        try:
            spiral_sweep.inputs['Fill Caps'].default_value = True
        except Exception:
            pass
    color_node(spiral_sweep, "music")

    # Stem - Bezier S-curve
    stem = safe_node(tree, 'GeometryNodeCurvePrimitiveBezierSegment', (bx, by + 600))
    if stem:
        stem.inputs['Resolution'].default_value = 48
        stem.inputs['Start'].default_value = (0.0, 0.225, 0)
        stem.inputs['Start Handle'].default_value = (0.2, 0.475, 0)
        stem.inputs['End Handle'].default_value = (0.075, 0.775, 0)
        stem.inputs['End'].default_value = (-0.075, 0.825, 0)
    color_node(stem, "music")

    stem_t = safe_node(tree, 'GeometryNodeTransform', (bx + 300, by + 600))
    if stem_t:
        stem_t.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
        link_sockets(tree, sock(stem, "Curve", outputs=True), stem_t.inputs['Geometry'])

    stem_sweep = safe_node(tree, 'GeometryNodeCurveToMesh', (bx + 600, by + 600))
    if stem_sweep:
        link_sockets(tree, sock(stem_t, "Geometry", outputs=True), stem_sweep.inputs['Curve'])
        link_sockets(tree, sock(profile, "Curve", outputs=True), stem_sweep.inputs.get('Profile Curve') or stem_sweep.inputs.get('Profile'))
        try:
            stem_sweep.inputs['Fill Caps'].default_value = True
        except Exception:
            pass
    color_node(stem_sweep, "music")

    # Tail - Bezier S-curve below spiral
    tail = safe_node(tree, 'GeometryNodeCurvePrimitiveBezierSegment', (bx, by - 600))
    if tail:
        tail.inputs['Resolution'].default_value = 32
        tail.inputs['Start'].default_value = (0.0, -0.225, 0)
        tail.inputs['Start Handle'].default_value = (-0.15, -0.425, 0)
        tail.inputs['End Handle'].default_value = (-0.05, -0.525, 0)
        tail.inputs['End'].default_value = (0.025, -0.55, 0)
    color_node(tail, "music")

    tail_t = safe_node(tree, 'GeometryNodeTransform', (bx + 300, by - 600))
    if tail_t:
        tail_t.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
        link_sockets(tree, sock(tail, "Curve", outputs=True), tail_t.inputs['Geometry'])

    tail_sweep = safe_node(tree, 'GeometryNodeCurveToMesh', (bx + 600, by - 600))
    if tail_sweep:
        link_sockets(tree, sock(tail_t, "Geometry", outputs=True), tail_sweep.inputs['Curve'])
        link_sockets(tree, sock(profile, "Curve", outputs=True), tail_sweep.inputs.get('Profile Curve') or tail_sweep.inputs.get('Profile'))
        try:
            tail_sweep.inputs['Fill Caps'].default_value = True
        except Exception:
            pass
    color_node(tail_sweep, "music")

    # Top finial
    finial = safe_node(tree, 'GeometryNodeMeshUVSphere', (bx, by + 1000))
    if finial:
        finial.inputs['Radius'].default_value = 0.088
        finial.inputs['Segments'].default_value = 16
        finial.inputs['Rings'].default_value = 12
    color_node(finial, "ornament")

    finial_t = safe_node(tree, 'GeometryNodeTransform', (bx + 300, by + 1000))
    if finial_t:
        finial_t.inputs['Translation'].default_value = (-0.075, 0, 0.825)
        link_sockets(tree, sock(finial, "Mesh", outputs=True), finial_t.inputs['Geometry'])
    color_node(finial_t, "ornament")

    # Bottom dot
    bd = safe_node(tree, 'GeometryNodeMeshUVSphere', (bx, by - 1000))
    if bd:
        bd.inputs['Radius'].default_value = 0.08
        bd.inputs['Segments'].default_value = 16
        bd.inputs['Rings'].default_value = 12
    color_node(bd, "ornament")

    bd_t = safe_node(tree, 'GeometryNodeTransform', (bx + 300, by - 1000))
    if bd_t:
        bd_t.inputs['Translation'].default_value = (0.025, 0, -0.55)
        link_sockets(tree, sock(bd, "Mesh", outputs=True), bd_t.inputs['Geometry'])
    color_node(bd_t, "ornament")

    # Join all
    join = safe_node(tree, 'GeometryNodeJoinGeometry', (bx + 900, by))
    for p in [sock(spiral_sweep, "Mesh", outputs=True),
              sock(stem_sweep, "Mesh", outputs=True),
              sock(tail_sweep, "Mesh", outputs=True),
              sock(finial_t, "Geometry", outputs=True),
              sock(bd_t, "Geometry", outputs=True)]:
        if p is not None:
            link_sockets(tree, p, join.inputs['Geometry'])
    color_node(join, "output")

    link_sockets(tree, sock(join, "Geometry", outputs=True), gout.inputs['Geometry'])

    return tree, gin, gout


# ---------------------------------------------------------------------------
# MUSIC: STAFF
# ---------------------------------------------------------------------------

def build_staff_group(group_name="MEL_music_staff_mp"):
    """Five-line staff with arrayed note heads (monolith port)."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Staff Length", 4.0, 0.5, 20.0)
    add_int_param(tree, "Staff Note Count", 8, 1, 64)
    add_float_param(tree, "Staff Line Thickness", 0.008, 0.002, 0.03)
    add_float_param(tree, "Musical Freq A", 2.0, 0.1, 12.0)
    add_float_param(tree, "Musical Freq B", 3.0, 0.1, 12.0)
    add_int_param(tree, "Harmonic Layers", 3, 1, 5)

    parts = []

    # Five horizontal staff lines
    for i in range(5):
        z = (i - 2) * 0.25
        ln = safe_node(tree, 'GeometryNodeMeshCube', (bx, i * 100))
        if ln:
            ln.inputs['Size'].default_value = (4.0, 0.008, 0.008)
        lt = safe_node(tree, 'GeometryNodeTransform', (bx + 200, i * 100))
        if lt:
            lt.inputs['Translation'].default_value = (0, 0, z)
            link_sockets(tree, sock(ln, "Mesh", outputs=True), lt.inputs['Geometry'])
        parts.append(sock(lt, "Geometry", outputs=True))

    # Note positions along the staff
    note_line = safe_node(tree, 'GeometryNodeMeshLine', (bx, by + 700))
    if note_line:
        try:
            note_line.mode = 'END_POINTS'
        except Exception:
            pass
        link_sockets(tree, gin.outputs["Staff Note Count"], note_line.inputs['Count'])
        note_line.inputs['Start Location'].default_value = (-1.6, 0, 0)
        note_line.inputs['Offset'].default_value = (3.2, 0, 0)
    color_node(note_line, "music")

    # Note head primitive
    note_head = safe_node(tree, 'GeometryNodeMeshUVSphere', (bx, by + 900))
    if note_head:
        note_head.inputs['Radius'].default_value = 0.18
        note_head.inputs['Segments'].default_value = 16
        note_head.inputs['Rings'].default_value = 12
    color_node(note_head, "music")

    # Flatten note
    note_flat = safe_node(tree, 'GeometryNodeTransform', (bx + 200, by + 900))
    if note_flat:
        note_flat.inputs['Scale'].default_value = (1.2, 0.6, 0.5)
        link_sockets(tree, sock(note_head, "Mesh", outputs=True), note_flat.inputs['Geometry'])

    inst = safe_node(tree, 'GeometryNodeInstanceOnPoints', (bx + 500, by + 700))
    if inst:
        link_sockets(tree, sock(note_line, "Mesh", outputs=True), inst.inputs['Points'])
        link_sockets(tree, sock(note_flat, "Geometry", outputs=True), inst.inputs['Instance'])

    # Vary note Z position using harmonic
    idx = safe_node(tree, 'GeometryNodeInputIndex', (bx, by + 1100))
    h = _make_harmonic_value(tree, sock(idx, "Index", outputs=True),
                             2.0, 3.0, 3, bx + 200, 1100)

    map_z = safe_node(tree, 'ShaderNodeMapRange', (bx + 1000, by + 1100))
    if map_z:
        map_z.inputs['From Min'].default_value = -2
        map_z.inputs['From Max'].default_value = 2
        map_z.inputs['To Min'].default_value = -0.5
        map_z.inputs['To Max'].default_value = 0.5
        link_sockets(tree, h, map_z.inputs['Value'])

    note_offset = safe_node(tree, 'ShaderNodeCombineXYZ', (bx + 1200, by + 1100))
    if note_offset:
        note_offset.inputs['X'].default_value = 0
        note_offset.inputs['Y'].default_value = 0
        link_sockets(tree, sock(map_z, "Result", outputs=True), note_offset.inputs['Z'])
    color_node(note_offset, "ornament")

    trans_inst = safe_node(tree, 'GeometryNodeTranslateInstances', (bx + 1400, by + 700))
    if trans_inst:
        link_sockets(tree, sock(inst, "Instances", outputs=True), trans_inst.inputs['Instances'])
        link_sockets(tree, sock(note_offset, "Vector", outputs=True), trans_inst.inputs['Translation'])

    # Add stems
    stem = safe_node(tree, 'GeometryNodeMeshCube', (bx, by + 1500))
    if stem:
        stem.inputs['Size'].default_value = (0.04, 0.04, 1.2)
    color_node(stem, "music")

    stem_t = safe_node(tree, 'GeometryNodeTransform', (bx + 200, by + 1500))
    if stem_t:
        stem_t.inputs['Translation'].default_value = (0.18, 0, 0.6)
        link_sockets(tree, sock(stem, "Mesh", outputs=True), stem_t.inputs['Geometry'])

    inst_stems = safe_node(tree, 'GeometryNodeInstanceOnPoints', (bx + 500, by + 1500))
    if inst_stems:
        link_sockets(tree, sock(note_line, "Mesh", outputs=True), inst_stems.inputs['Points'])
        link_sockets(tree, sock(stem_t, "Geometry", outputs=True), inst_stems.inputs['Instance'])

    trans_stems = safe_node(tree, 'GeometryNodeTranslateInstances', (bx + 1400, by + 1500))
    if trans_stems:
        link_sockets(tree, sock(inst_stems, "Instances", outputs=True), trans_stems.inputs['Instances'])
        link_sockets(tree, sock(note_offset, "Vector", outputs=True), trans_stems.inputs['Translation'])

    realize_n = safe_node(tree, 'GeometryNodeRealizeInstances', (bx + 1700, by + 700))
    if realize_n:
        link_sockets(tree, sock(trans_inst, "Instances", outputs=True), realize_n.inputs['Geometry'])

    realize_s = safe_node(tree, 'GeometryNodeRealizeInstances', (bx + 1700, by + 1500))
    if realize_s:
        link_sockets(tree, sock(trans_stems, "Instances", outputs=True), realize_s.inputs['Geometry'])

    parts.append(sock(realize_n, "Geometry", outputs=True))
    parts.append(sock(realize_s, "Geometry", outputs=True))

    join = safe_node(tree, 'GeometryNodeJoinGeometry', (bx + 2000, by))
    for p in parts:
        if p is not None:
            link_sockets(tree, p, join.inputs['Geometry'])
    color_node(join, "output")

    link_sockets(tree, sock(join, "Geometry", outputs=True), gout.inputs['Geometry'])

    return tree, gin, gout


# ---------------------------------------------------------------------------
# MUSIC: SHEET MUSIC RAILING
# ---------------------------------------------------------------------------

def build_sheet_music_railing_group(group_name="MEL_music_sheet_rail_mp"):
    """Walkable staff railing (monolith port): 5 lines + bar lines + notes + clef + posts."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Sheet Length", 8.0, 1.0, 40.0)
    add_float_param(tree, "Sheet Height", 1.0, 0.2, 4.0)
    add_float_param(tree, "Sheet Line Thickness", 0.02, 0.004, 0.1)
    add_int_param(tree, "Sheet Note Count", 12, 1, 96)
    add_float_param(tree, "Sheet Note Size", 0.18, 0.04, 1.2)
    add_int_param(tree, "Sheet Bar Count", 4, 0, 16)
    add_bool_param(tree, "Sheet With Clef", True)
    add_bool_param(tree, "Sheet With Stems", True)
    add_bool_param(tree, "Sheet Pitch Driven", True)
    add_int_param(tree, "Sheet Post Count", 5, 0, 32)
    add_float_param(tree, "Sheet Post Radius", 0.05, 0.01, 0.3)
    add_float_param(tree, "Musical Freq A", 2.0, 0.1, 12.0)
    add_float_param(tree, "Musical Freq B", 3.0, 0.1, 12.0)
    add_int_param(tree, "Harmonic Layers", 3, 1, 5)
    add_float_param(tree, "Clef Size", 2.0, 0.4, 6.0)
    add_float_param(tree, "Clef Thickness", 0.04, 0.008, 0.15)
    add_float_param(tree, "Clef Curls", 1.5, 0.5, 3.0)

    parts = []
    line_spacing = 0.25  # H / 4 for default H=1.0

    # 5 horizontal staff lines (cylinders along X)
    for i in range(5):
        z = (i - 2) * line_spacing
        ln = safe_node(tree, 'GeometryNodeMeshCylinder', (bx, i * 100))
        if ln:
            ln.inputs['Vertices'].default_value = 8
            link_sockets(tree, gin.outputs["Sheet Line Thickness"], ln.inputs['Radius'])
            link_sockets(tree, gin.outputs["Sheet Length"], ln.inputs['Depth'])
        lt = safe_node(tree, 'GeometryNodeTransform', (bx + 200, i * 100))
        if lt:
            lt.inputs['Translation'].default_value = (0, 0, z)
            lt.inputs['Rotation'].default_value = (0, math.radians(90), 0)
            link_sockets(tree, sock(ln, "Mesh", outputs=True), lt.inputs['Geometry'])
        parts.append(sock(lt, "Geometry", outputs=True))

    # Bar lines
    bl = safe_node(tree, 'GeometryNodeMeshLine', (bx, by + 600))
    if bl:
        try:
            bl.mode = 'OFFSET'
        except Exception:
            pass
        link_sockets(tree, gin.outputs["Sheet Bar Count"], bl.inputs['Count'])
        bl.inputs['Start Location'].default_value = (-2.0, 0, 0)
        bl.inputs['Offset'].default_value = (1.0, 0, 0)
    color_node(bl, "sheet_music")

    bar = safe_node(tree, 'GeometryNodeMeshCube', (bx, by + 800))
    if bar:
        bar.inputs['Size'].default_value = (0.03, 0.03, 1.0)
    color_node(bar, "sheet_music")

    bi = safe_node(tree, 'GeometryNodeInstanceOnPoints', (bx + 300, by + 600))
    if bi:
        link_sockets(tree, sock(bl, "Mesh", outputs=True), bi.inputs['Points'])
        link_sockets(tree, sock(bar, "Mesh", outputs=True), bi.inputs['Instance'])

    br = safe_node(tree, 'GeometryNodeRealizeInstances', (bx + 600, by + 600))
    if br:
        link_sockets(tree, sock(bi, "Instances", outputs=True), br.inputs['Geometry'])
    parts.append(sock(br, "Geometry", outputs=True))

    # Note heads
    note_line = safe_node(tree, 'GeometryNodeMeshLine', (bx, by + 1000))
    if note_line:
        try:
            note_line.mode = 'END_POINTS'
        except Exception:
            pass
        link_sockets(tree, gin.outputs["Sheet Note Count"], note_line.inputs['Count'])
        note_line.inputs['Start Location'].default_value = (-2.8, 0, 0)
        note_line.inputs['Offset'].default_value = (5.1, 0, 0)
    color_node(note_line, "sheet_music")

    head = safe_node(tree, 'GeometryNodeMeshUVSphere', (bx, by + 1200))
    if head:
        link_sockets(tree, gin.outputs["Sheet Note Size"], head.inputs['Radius'])
        head.inputs['Segments'].default_value = 18
        head.inputs['Rings'].default_value = 12
    color_node(head, "sheet_music")

    flat = safe_node(tree, 'GeometryNodeTransform', (bx + 200, by + 1200))
    if flat:
        flat.inputs['Scale'].default_value = (1.3, 0.6, 0.85)
        flat.inputs['Rotation'].default_value = (0, math.radians(-15), 0)
        link_sockets(tree, sock(head, "Mesh", outputs=True), flat.inputs['Geometry'])

    inst = safe_node(tree, 'GeometryNodeInstanceOnPoints', (bx + 500, by + 1000))
    if inst:
        link_sockets(tree, sock(note_line, "Mesh", outputs=True), inst.inputs['Points'])
        link_sockets(tree, sock(flat, "Geometry", outputs=True), inst.inputs['Instance'])

    # Pitch-driven Z displacement
    idx = safe_node(tree, 'GeometryNodeInputIndex', (bx, by + 1500))
    h_val = _make_harmonic_value(tree, sock(idx, "Index", outputs=True),
                                 2.0, 3.0, 3, bx + 200, 1500)

    map_z = safe_node(tree, 'ShaderNodeMapRange', (bx + 1000, by + 1500))
    if map_z:
        map_z.inputs['From Min'].default_value = -2
        map_z.inputs['From Max'].default_value = 2
        map_z.inputs['To Min'].default_value = -0.5
        map_z.inputs['To Max'].default_value = 0.5
        link_sockets(tree, h_val, map_z.inputs['Value'])

    ovec = safe_node(tree, 'ShaderNodeCombineXYZ', (bx + 1200, by + 1500))
    if ovec:
        ovec.inputs['X'].default_value = 0
        ovec.inputs['Y'].default_value = 0
        link_sockets(tree, sock(map_z, "Result", outputs=True), ovec.inputs['Z'])
    color_node(ovec, "sheet_music")

    ti = safe_node(tree, 'GeometryNodeTranslateInstances', (bx + 1500, by + 1000))
    if ti:
        link_sockets(tree, sock(inst, "Instances", outputs=True), ti.inputs['Instances'])
        link_sockets(tree, sock(ovec, "Vector", outputs=True), ti.inputs['Translation'])
    notes_inst = sock(ti, "Instances", outputs=True)

    notes_real = safe_node(tree, 'GeometryNodeRealizeInstances', (bx + 1800, by + 1000))
    if notes_real:
        link_sockets(tree, notes_inst, notes_real.inputs['Geometry'])
    parts.append(sock(notes_real, "Geometry", outputs=True))

    # Note stems
    stem = safe_node(tree, 'GeometryNodeMeshCube', (bx, by + 1900))
    if stem:
        stem.inputs['Size'].default_value = (0.03, 0.03, 0.9)
    color_node(stem, "sheet_music")

    stem_t = safe_node(tree, 'GeometryNodeTransform', (bx + 200, by + 1900))
    if stem_t:
        stem_t.inputs['Translation'].default_value = (0.18, 0, 0.45)
        link_sockets(tree, sock(stem, "Mesh", outputs=True), stem_t.inputs['Geometry'])

    si = safe_node(tree, 'GeometryNodeInstanceOnPoints', (bx + 500, by + 1900))
    if si:
        link_sockets(tree, sock(note_line, "Mesh", outputs=True), si.inputs['Points'])
        link_sockets(tree, sock(stem_t, "Geometry", outputs=True), si.inputs['Instance'])

    ti2 = safe_node(tree, 'GeometryNodeTranslateInstances', (bx + 1500, by + 1900))
    if ti2:
        link_sockets(tree, sock(si, "Instances", outputs=True), ti2.inputs['Instances'])
        link_sockets(tree, sock(ovec, "Vector", outputs=True), ti2.inputs['Translation'])

    sr = safe_node(tree, 'GeometryNodeRealizeInstances', (bx + 1800, by + 1900))
    if sr:
        link_sockets(tree, sock(ti2, "Instances", outputs=True), sr.inputs['Geometry'])
    parts.append(sock(sr, "Geometry", outputs=True))

    # Treble clef at start
    clef_grp = _ensure_group_node(tree, "MEL_music_treble_clef", build_treble_clef_group, (bx + 2200, by))
    if clef_grp and clef_grp.node_tree:
        if clef_grp.inputs.get("Clef Size"):
            link_sockets(tree, gin.outputs["Sheet Height"], clef_grp.inputs["Clef Size"])
        if clef_grp.inputs.get("Clef Thickness"):
            link_sockets(tree, gin.outputs["Sheet Line Thickness"], clef_grp.inputs["Clef Thickness"])
        if clef_grp.inputs.get("Clef Curls"):
            clef_grp.inputs["Clef Curls"].default_value = 1.5

    clef_t = safe_node(tree, 'GeometryNodeTransform', (bx + 3500, by))
    if clef_t:
        clef_t.inputs['Translation'].default_value = (-3.0, 0, -0.1)
        clef_t.inputs['Scale'].default_value = (0.6, 0.6, 0.6)
        if clef_grp and clef_grp.node_tree:
            link_sockets(tree, sock(clef_grp, "Geometry", outputs=True), clef_t.inputs['Geometry'])
    parts.append(sock(clef_t, "Geometry", outputs=True))

    # Support posts
    pl = safe_node(tree, 'GeometryNodeMeshLine', (bx, by + 2300))
    if pl:
        try:
            pl.mode = 'OFFSET'
        except Exception:
            pass
        link_sockets(tree, gin.outputs["Sheet Post Count"], pl.inputs['Count'])
        pl.inputs['Start Location'].default_value = (-3.0, 0, -0.5)
        pl.inputs['Offset'].default_value = (1.5, 0, 0)
    color_node(pl, "sheet_music")

    post = safe_node(tree, 'GeometryNodeMeshCylinder', (bx, by + 2500))
    if post:
        post.inputs['Vertices'].default_value = 8
        link_sockets(tree, gin.outputs["Sheet Post Radius"], post.inputs['Radius'])
        post.inputs['Depth'].default_value = 1.0
    color_node(post, "sheet_music")

    pi = safe_node(tree, 'GeometryNodeInstanceOnPoints', (bx + 300, by + 2300))
    if pi:
        link_sockets(tree, sock(pl, "Mesh", outputs=True), pi.inputs['Points'])
        link_sockets(tree, sock(post, "Mesh", outputs=True), pi.inputs['Instance'])

    pr = safe_node(tree, 'GeometryNodeRealizeInstances', (bx + 600, by + 2300))
    if pr:
        link_sockets(tree, sock(pi, "Instances", outputs=True), pr.inputs['Geometry'])
    parts.append(sock(pr, "Geometry", outputs=True))

    # Join all
    join = safe_node(tree, 'GeometryNodeJoinGeometry', (bx + 4000, by))
    for p in parts:
        if p is not None:
            link_sockets(tree, p, join.inputs['Geometry'])
    color_node(join, "output")

    link_sockets(tree, sock(join, "Geometry", outputs=True), gout.inputs['Geometry'])

    return tree, gin, gout


# ---------------------------------------------------------------------------
# MUSIC: CASCADING BEAMS
# ---------------------------------------------------------------------------

def build_cascading_beams_group(group_name="MEL_cascading_beams"):
    """Erindale-style cascading beams (monolith port)."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Beams Count", 8, 1, 64)
    add_float_param(tree, "Beams Length", 4.0, 0.5, 20.0)
    add_float_param(tree, "Beams Thickness", 0.1, 0.01, 1.0)
    add_float_param(tree, "Beams Spacing", 0.6, 0.1, 4.0)
    add_float_param(tree, "Beams Z Cascade", 0.15, -1.0, 1.0)
    add_float_param(tree, "Beams X Cascade", 0.05, -1.0, 1.0)
    add_float_param(tree, "Beams Twist", 0.0, -1.0, 1.0)
    add_bool_param(tree, "Has Twist", False)

    # Line of N points along Y axis
    line = safe_node(tree, 'GeometryNodeMeshLine', (bx, by))
    if line:
        try:
            line.mode = 'OFFSET'
        except Exception:
            pass
        link_sockets(tree, gin.outputs["Beams Count"], line.inputs['Count'])
        line.inputs['Start Location'].default_value = (0, -3.0, 0)
        line.inputs['Offset'].default_value = (0, 0.6, 0)
    color_node(line, "beams")

    # Beam prototype
    beam = safe_node(tree, 'GeometryNodeMeshCube', (bx, by + 200))
    if beam:
        beam.inputs['Size'].default_value = (4.0, 0.1, 0.1)
    color_node(beam, "beams")

    inst = safe_node(tree, 'GeometryNodeInstanceOnPoints', (bx + 300, by))
    if inst:
        link_sockets(tree, sock(line, "Mesh", outputs=True), inst.inputs['Points'])
        link_sockets(tree, sock(beam, "Mesh", outputs=True), inst.inputs['Instance'])
    color_node(inst, "beams")

    # Per-beam Z + X cascade
    idx = safe_node(tree, 'GeometryNodeInputIndex', (bx, by + 400))

    z_step = safe_node(tree, 'ShaderNodeMath', (bx + 200, by + 400))
    if z_step:
        z_step.operation = 'MULTIPLY'
        link_sockets(tree, sock(idx, "Index", outputs=True), z_step.inputs[0])
        link_sockets(tree, gin.outputs["Beams Z Cascade"], z_step.inputs[1])

    x_step = safe_node(tree, 'ShaderNodeMath', (bx + 200, by + 600))
    if x_step:
        x_step.operation = 'MULTIPLY'
        link_sockets(tree, sock(idx, "Index", outputs=True), x_step.inputs[0])
        link_sockets(tree, gin.outputs["Beams X Cascade"], x_step.inputs[1])

    ovec = safe_node(tree, 'ShaderNodeCombineXYZ', (bx + 450, by + 500))
    if ovec:
        link_sockets(tree, sock(x_step, "Value", outputs=True), ovec.inputs['X'])
        ovec.inputs['Y'].default_value = 0
        link_sockets(tree, sock(z_step, "Value", outputs=True), ovec.inputs['Z'])
    color_node(ovec, "beams")

    ti = safe_node(tree, 'GeometryNodeTranslateInstances', (bx + 700, by))
    if ti:
        link_sockets(tree, sock(inst, "Instances", outputs=True), ti.inputs['Instances'])
        link_sockets(tree, sock(ovec, "Vector", outputs=True), ti.inputs['Translation'])
    color_node(ti, "beams")

    # Per-beam twist
    rot_step = safe_node(tree, 'ShaderNodeMath', (bx + 200, by + 800))
    if rot_step:
        rot_step.operation = 'MULTIPLY'
        link_sockets(tree, sock(idx, "Index", outputs=True), rot_step.inputs[0])
        link_sockets(tree, gin.outputs["Beams Twist"], rot_step.inputs[1])

    rvec = safe_node(tree, 'ShaderNodeCombineXYZ', (bx + 450, by + 800))
    if rvec:
        link_sockets(tree, sock(rot_step, "Value", outputs=True), rvec.inputs['X'])
        rvec.inputs['Y'].default_value = 0
        rvec.inputs['Z'].default_value = 0
    color_node(rvec, "beams")

    ri = safe_node(tree, 'GeometryNodeRotateInstances', (bx + 900, by))
    if ri:
        link_sockets(tree, sock(ti, "Instances", outputs=True), ri.inputs['Instances'])
        link_sockets(tree, sock(rvec, "Vector", outputs=True), ri.inputs['Rotation'])

    out_inst = sock(ri, "Instances", outputs=True)

    realize = safe_node(tree, 'GeometryNodeRealizeInstances', (bx + 1200, by))
    if realize:
        link_sockets(tree, out_inst, realize.inputs['Geometry'])
    color_node(realize, "output")

    link_sockets(tree, sock(realize, "Geometry", outputs=True), gout.inputs['Geometry'])

    return tree, gin, gout


# ---------------------------------------------------------------------------
# EURO STUBS — route to existing package builders
# ---------------------------------------------------------------------------

def build_gothic_portal(group_name="MEL_gothic_portal"):
    """Stub: routes to MEL_greybox_room_kit (monolith override)."""
    tree, gin, gout = new_geometry_tree(group_name)
    from .polyhedra_gn import build_greybox_room_kit
    portal = _ensure_group_node(tree, "MEL_greybox_room_kit", build_greybox_room_kit, (0, 0))
    if portal and portal.node_tree:
        geo_out = sock(portal, "Geometry", outputs=True)
        if geo_out:
            link_sockets(tree, geo_out, gout.inputs['Geometry'])
    return tree, gin, gout


def build_gothic_bay(group_name="MEL_gothic_bay"):
    """Stub: routes to MEL_greybox_room_kit (monolith override)."""
    tree, gin, gout = new_geometry_tree(group_name)
    from .polyhedra_gn import build_greybox_room_kit
    bay = _ensure_group_node(tree, "MEL_greybox_room_kit", build_greybox_room_kit, (0, 0))
    if bay and bay.node_tree:
        geo_out = sock(bay, "Geometry", outputs=True)
        if geo_out:
            link_sockets(tree, geo_out, gout.inputs['Geometry'])
    return tree, gin, gout


def build_gothic_buttress_kit(group_name="MEL_gothic_buttress_kit"):
    """Stub: routes to MEL_buttress (monolith override)."""
    tree, gin, gout = new_geometry_tree(group_name)
    from .euro_kit import build_buttress_group
    buttress = _ensure_group_node(tree, "MEL_buttress", build_buttress_group, (0, 0))
    if buttress and buttress.node_tree:
        geo_out = sock(buttress, "Geometry", outputs=True)
        if geo_out:
            link_sockets(tree, geo_out, gout.inputs['Geometry'])
    return tree, gin, gout


def build_gothic_tracery_panel(group_name="MEL_gothic_tracery_panel"):
    """Stub: routes to MEL_trefoil (monolith override)."""
    tree, gin, gout = new_geometry_tree(group_name)
    from .euro_kit import build_trefoil_group
    trefoil = _ensure_group_node(tree, "MEL_trefoil", build_trefoil_group, (0, 0))
    if trefoil and trefoil.node_tree:
        geo_out = sock(trefoil, "Geometry", outputs=True)
        if geo_out:
            link_sockets(tree, geo_out, gout.inputs['Geometry'])
    return tree, gin, gout


def build_romanesque_apse(group_name="MEL_romanesque_apse"):
    """Stub: routes to MEL_greybox_room_kit (monolith override)."""
    tree, gin, gout = new_geometry_tree(group_name)
    from .polyhedra_gn import build_greybox_room_kit
    apse = _ensure_group_node(tree, "MEL_greybox_room_kit", build_greybox_room_kit, (0, 0))
    if apse and apse.node_tree:
        geo_out = sock(apse, "Geometry", outputs=True)
        if geo_out:
            link_sockets(tree, geo_out, gout.inputs['Geometry'])
    return tree, gin, gout


def build_romanesque_arcade_bay(group_name="MEL_romanesque_arcade_bay"):
    """Stub: routes to MEL_greybox_room_kit (monolith override)."""
    tree, gin, gout = new_geometry_tree(group_name)
    from .polyhedra_gn import build_greybox_room_kit
    arcade = _ensure_group_node(tree, "MEL_greybox_room_kit", build_greybox_room_kit, (0, 0))
    if arcade and arcade.node_tree:
        geo_out = sock(arcade, "Geometry", outputs=True)
        if geo_out:
            link_sockets(tree, geo_out, gout.inputs['Geometry'])
    return tree, gin, gout


def build_venetian_loggia_bay(group_name="MEL_venetian_loggia_bay"):
    """Stub: routes to MEL_bifora (monolith override)."""
    tree, gin, gout = new_geometry_tree(group_name)
    from .euro_kit import build_bifora_group
    bifora = _ensure_group_node(tree, "MEL_bifora", build_bifora_group, (0, 0))
    if bifora and bifora.node_tree:
        geo_out = sock(bifora, "Geometry", outputs=True)
        if geo_out:
            link_sockets(tree, geo_out, gout.inputs['Geometry'])
    return tree, gin, gout


# ---------------------------------------------------------------------------
# EURO FULL: ROSE WINDOW
# ---------------------------------------------------------------------------

def build_rose_window_group(group_name="MEL_rose_window"):
    """Radial Gothic rose window (monolith port)."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Rose Outer Radius", 1.5, 0.3, 6.0)
    add_float_param(tree, "Rose Inner Radius", 0.8, 0.2, 4.0)
    add_int_param(tree, "Rose Petal Count", 12, 3, 32)
    add_int_param(tree, "Rose Spoke Count", 8, 0, 24)
    add_float_param(tree, "Rose Petal Radius", 0.25, 0.05, 1.0)
    add_float_param(tree, "Gothic Thickness", 0.04, 0.008, 0.15)
    add_bool_param(tree, "Has Spokes", True)

    # Profile
    profile = safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (bx, by - 500))
    if profile:
        try:
            profile.mode = 'RADIUS'
        except Exception:
            pass
        profile.inputs['Resolution'].default_value = 6
        link_sockets(tree, gin.outputs["Gothic Thickness"], profile.inputs['Radius'])
    color_node(profile, "tracery")

    # Outer ring
    outer = safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (bx, by + 200))
    if outer:
        try:
            outer.mode = 'RADIUS'
        except Exception:
            pass
        outer.inputs['Resolution'].default_value = 64
        link_sockets(tree, gin.outputs["Rose Outer Radius"], outer.inputs['Radius'])
    color_node(outer, "gothic")

    outer_t = safe_node(tree, 'GeometryNodeTransform', (bx + 200, by + 200))
    if outer_t:
        outer_t.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
        link_sockets(tree, sock(outer, "Curve", outputs=True), outer_t.inputs['Geometry'])

    outer_sweep = safe_node(tree, 'GeometryNodeCurveToMesh', (bx + 500, by + 200))
    if outer_sweep:
        link_sockets(tree, sock(outer_t, "Geometry", outputs=True), outer_sweep.inputs['Curve'])
        link_sockets(tree, sock(profile, "Curve", outputs=True), outer_sweep.inputs.get('Profile Curve') or outer_sweep.inputs.get('Profile'))

    # Inner ring
    inner = safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (bx, by))
    if inner:
        try:
            inner.mode = 'RADIUS'
        except Exception:
            pass
        inner.inputs['Resolution'].default_value = 24
        link_sockets(tree, gin.outputs["Rose Inner Radius"], inner.inputs['Radius'])
    color_node(inner, "gothic")

    inner_t = safe_node(tree, 'GeometryNodeTransform', (bx + 200, by))
    if inner_t:
        inner_t.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
        link_sockets(tree, sock(inner, "Curve", outputs=True), inner_t.inputs['Geometry'])

    inner_sweep = safe_node(tree, 'GeometryNodeCurveToMesh', (bx + 500, by))
    if inner_sweep:
        link_sockets(tree, sock(inner_t, "Geometry", outputs=True), inner_sweep.inputs['Curve'])
        link_sockets(tree, sock(profile, "Curve", outputs=True), inner_sweep.inputs.get('Profile Curve') or inner_sweep.inputs.get('Profile'))

    # Petals
    petal = safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (bx, by - 200))
    if petal:
        try:
            petal.mode = 'RADIUS'
        except Exception:
            pass
        petal.inputs['Resolution'].default_value = 24
        link_sockets(tree, gin.outputs["Rose Petal Radius"], petal.inputs['Radius'])
    color_node(petal, "tracery")

    petal_t = safe_node(tree, 'GeometryNodeTransform', (bx + 200, by - 200))
    if petal_t:
        petal_t.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
        link_sockets(tree, sock(petal, "Curve", outputs=True), petal_t.inputs['Geometry'])

    petal_sweep = safe_node(tree, 'GeometryNodeCurveToMesh', (bx + 500, by - 200))
    if petal_sweep:
        link_sockets(tree, sock(petal_t, "Geometry", outputs=True), petal_sweep.inputs['Curve'])
        link_sockets(tree, sock(profile, "Curve", outputs=True), petal_sweep.inputs.get('Profile Curve') or petal_sweep.inputs.get('Profile'))

    # Place petals on circle
    petal_dist = 1.2
    pc = safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (bx, by + 500))
    if pc:
        try:
            pc.mode = 'RADIUS'
        except Exception:
            pass
        link_sockets(tree, gin.outputs["Rose Petal Count"], pc.inputs['Resolution'])
        pc.inputs['Radius'].default_value = petal_dist

    pc_t = safe_node(tree, 'GeometryNodeTransform', (bx + 200, by + 500))
    if pc_t:
        pc_t.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
        link_sockets(tree, sock(pc, "Curve", outputs=True), pc_t.inputs['Geometry'])

    pc2p = safe_node(tree, 'GeometryNodeCurveToPoints', (bx + 500, by + 500))
    if pc2p:
        try:
            pc2p.mode = 'EVALUATED'
        except Exception:
            pass
        link_sockets(tree, sock(pc_t, "Geometry", outputs=True), pc2p.inputs['Curve'])

    inst = safe_node(tree, 'GeometryNodeInstanceOnPoints', (bx + 800, by - 200))
    if inst:
        link_sockets(tree, sock(pc2p, "Points", outputs=True), inst.inputs['Points'])
        link_sockets(tree, sock(petal_sweep, "Mesh", outputs=True), inst.inputs['Instance'])

    realize_p = safe_node(tree, 'GeometryNodeRealizeInstances', (bx + 1100, by - 200))
    if realize_p:
        link_sockets(tree, sock(inst, "Instances", outputs=True), realize_p.inputs['Geometry'])

    parts = [sock(outer_sweep, "Mesh", outputs=True),
             sock(inner_sweep, "Mesh", outputs=True),
             sock(realize_p, "Geometry", outputs=True)]

    # Spokes
    sp = safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (bx, by + 800))
    if sp:
        try:
            sp.mode = 'RADIUS'
        except Exception:
            pass
        link_sockets(tree, gin.outputs["Rose Spoke Count"], sp.inputs['Resolution'])
        sp.inputs['Radius'].default_value = 1.15
    color_node(sp, "tracery")

    sp_t = safe_node(tree, 'GeometryNodeTransform', (bx + 200, by + 800))
    if sp_t:
        sp_t.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
        link_sockets(tree, sock(sp, "Curve", outputs=True), sp_t.inputs['Geometry'])

    sp2p = safe_node(tree, 'GeometryNodeCurveToPoints', (bx + 500, by + 800))
    if sp2p:
        try:
            sp2p.mode = 'EVALUATED'
        except Exception:
            pass
        link_sockets(tree, sock(sp_t, "Geometry", outputs=True), sp2p.inputs['Curve'])

    spoke = safe_node(tree, 'GeometryNodeMeshCylinder', (bx, by + 1100))
    if spoke:
        spoke.inputs['Vertices'].default_value = 6
        spoke.inputs['Radius'].default_value = 0.016
        spoke.inputs['Depth'].default_value = 0.7
    color_node(spoke, "tracery")

    sp_inst = safe_node(tree, 'GeometryNodeInstanceOnPoints', (bx + 800, by + 800))
    if sp_inst:
        link_sockets(tree, sock(sp2p, "Points", outputs=True), sp_inst.inputs['Points'])
        link_sockets(tree, sock(spoke, "Mesh", outputs=True), sp_inst.inputs['Instance'])
        link_sockets(tree, sock(sp2p, "Rotation", outputs=True), sp_inst.inputs['Rotation'])

    sp_realize = safe_node(tree, 'GeometryNodeRealizeInstances', (bx + 1100, by + 800))
    if sp_realize:
        link_sockets(tree, sock(sp_inst, "Instances", outputs=True), sp_realize.inputs['Geometry'])

    spokes_switch = _switch_geo(tree, (bx + 1400, by + 400),
                                gin.outputs["Has Spokes"],
                                sock(sp_realize, "Geometry", outputs=True), None)

    join = safe_node(tree, 'GeometryNodeJoinGeometry', (bx + 1700, by))
    for p in parts:
        if p is not None:
            link_sockets(tree, p, join.inputs['Geometry'])
    if spokes_switch:
        link_sockets(tree, sock(spokes_switch, "Output", outputs=True), join.inputs['Geometry'])
    color_node(join, "output")

    link_sockets(tree, sock(join, "Geometry", outputs=True), gout.inputs['Geometry'])

    return tree, gin, gout


# ---------------------------------------------------------------------------
# EURO FULL: LANCET WINDOW
# ---------------------------------------------------------------------------

def build_lancet_group(group_name="MEL_lancet"):
    """Tall slender Gothic pointed window (monolith port)."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Lancet Width", 0.6, 0.1, 3.0)
    add_float_param(tree, "Lancet Height", 3.0, 0.5, 12.0)
    add_float_param(tree, "Lancet Pointiness", 0.6, 0.1, 1.0)
    add_int_param(tree, "Lancet Count", 1, 1, 8)
    add_float_param(tree, "Gothic Thickness", 0.04, 0.008, 0.15)
    add_float_param(tree, "Musical Freq A", 2.0, 0.1, 12.0)
    add_float_param(tree, "Musical Freq B", 3.0, 0.1, 12.0)
    add_int_param(tree, "Harmonic Layers", 3, 1, 5)
    add_float_param(tree, "Ornament Density", 0.5, 0.0, 1.0)
    add_bool_param(tree, "Multi Lancet", False)

    half_W = 0.3
    R = 0.18
    peak_angle = math.acos(min(1.0, max(-1.0, (R - half_W) / R)))

    # Profile
    profile = safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (bx, by - 500))
    if profile:
        try:
            profile.mode = 'RADIUS'
        except Exception:
            pass
        profile.inputs['Resolution'].default_value = 8
        link_sockets(tree, gin.outputs["Gothic Thickness"], profile.inputs['Radius'])
    color_node(profile, "gothic")

    # Right side
    r_side = safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (bx, by + 200))
    if r_side:
        try:
            r_side.mode = 'POINTS'
        except Exception:
            pass
        r_side.inputs['Start'].default_value = (0.3, 0, 0)
        r_side.inputs['End'].default_value = (0.3, 0, 1.5)
    color_node(r_side, "gothic")

    # Left side
    l_side = safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (bx, by))
    if l_side:
        try:
            l_side.mode = 'POINTS'
        except Exception:
            pass
        l_side.inputs['Start'].default_value = (-0.3, 0, 0)
        l_side.inputs['End'].default_value = (-0.3, 0, 1.5)
    color_node(l_side, "gothic")

    # Bottom sill
    sill = safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (bx, by - 200))
    if sill:
        try:
            sill.mode = 'POINTS'
        except Exception:
            pass
        sill.inputs['Start'].default_value = (-0.3, 0, 0)
        sill.inputs['End'].default_value = (0.3, 0, 0)
    color_node(sill, "gothic")

    # Right arc
    r_arc = safe_node(tree, 'GeometryNodeCurveArc', (bx, by + 500))
    if r_arc:
        try:
            r_arc.mode = 'RADIUS'
        except Exception:
            pass
        r_arc.inputs['Resolution'].default_value = 24
        r_arc.inputs['Radius'].default_value = 0.18
        r_arc.inputs['Start Angle'].default_value = math.pi - peak_angle
        r_arc.inputs['Sweep Angle'].default_value = peak_angle
    color_node(r_arc, "gothic")

    r_arc_t = safe_node(tree, 'GeometryNodeTransform', (bx + 200, by + 500))
    if r_arc_t:
        r_arc_t.inputs['Translation'].default_value = (0.12, 0, 1.35)
        r_arc_t.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
        link_sockets(tree, sock(r_arc, "Curve", outputs=True), r_arc_t.inputs['Geometry'])

    # Left arc
    l_arc = safe_node(tree, 'GeometryNodeCurveArc', (bx, by + 700))
    if l_arc:
        try:
            l_arc.mode = 'RADIUS'
        except Exception:
            pass
        l_arc.inputs['Resolution'].default_value = 24
        l_arc.inputs['Radius'].default_value = 0.18
        l_arc.inputs['Start Angle'].default_value = 0
        l_arc.inputs['Sweep Angle'].default_value = peak_angle
    color_node(l_arc, "gothic")

    l_arc_t = safe_node(tree, 'GeometryNodeTransform', (bx + 200, by + 700))
    if l_arc_t:
        l_arc_t.inputs['Translation'].default_value = (-0.48, 0, 1.35)
        l_arc_t.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
        link_sockets(tree, sock(l_arc, "Curve", outputs=True), l_arc_t.inputs['Geometry'])

    # Sweep all curves
    parts = []
    for curve_out, y in [(sock(r_side, "Curve", outputs=True), 200),
                          (sock(l_side, "Curve", outputs=True), 0),
                          (sock(sill, "Curve", outputs=True), -200),
                          (sock(r_arc_t, "Geometry", outputs=True), 500),
                          (sock(l_arc_t, "Geometry", outputs=True), 700)]:
        sw = safe_node(tree, 'GeometryNodeCurveToMesh', (bx + 500, y))
        if sw and curve_out is not None:
            link_sockets(tree, curve_out, sw.inputs['Curve'])
            link_sockets(tree, sock(profile, "Curve", outputs=True), sw.inputs.get('Profile Curve') or sw.inputs.get('Profile'))
            try:
                sw.inputs['Fill Caps'].default_value = True
            except Exception:
                pass
            parts.append(sock(sw, "Mesh", outputs=True))

    join_one = safe_node(tree, 'GeometryNodeJoinGeometry', (bx + 800, by))
    for p in parts:
        if p is not None:
            link_sockets(tree, p, join_one.inputs['Geometry'])
    color_node(join_one, "output")

    geom = sock(join_one, "Geometry", outputs=True)

    # Multi-lancet
    line = safe_node(tree, 'GeometryNodeMeshLine', (bx + 800, by + 1000))
    if line:
        try:
            line.mode = 'OFFSET'
        except Exception:
            pass
        link_sockets(tree, gin.outputs["Lancet Count"], line.inputs['Count'])
        line.inputs['Start Location'].default_value = (-0.3, 0, 0)
        line.inputs['Offset'].default_value = (0.66, 0, 0)
    color_node(line, "gothic")

    ml_inst = safe_node(tree, 'GeometryNodeInstanceOnPoints', (bx + 1100, by))
    if ml_inst:
        link_sockets(tree, sock(line, "Mesh", outputs=True), ml_inst.inputs['Points'])
        link_sockets(tree, geom, ml_inst.inputs['Instance'])

    idx = safe_node(tree, 'GeometryNodeInputIndex', (bx + 800, by + 1300))
    h = _make_harmonic_value(tree, sock(idx, "Index", outputs=True),
                             2.0, 3.0, 3, bx + 1000, 1300)

    mr = safe_node(tree, 'ShaderNodeMapRange', (bx + 1700, by + 1300))
    if mr:
        mr.inputs['From Min'].default_value = -2
        mr.inputs['From Max'].default_value = 2
        mr.inputs['To Min'].default_value = 0.85
        mr.inputs['To Max'].default_value = 1.15
        link_sockets(tree, h, mr.inputs['Value'])

    sv = safe_node(tree, 'ShaderNodeCombineXYZ', (bx + 1900, by + 1300))
    if sv:
        sv.inputs['X'].default_value = 1
        sv.inputs['Y'].default_value = 1
        link_sockets(tree, sock(mr, "Result", outputs=True), sv.inputs['Z'])
    color_node(sv, "ornament")

    scale_inst = safe_node(tree, 'GeometryNodeScaleInstances', (bx + 2100, by))
    if scale_inst:
        link_sockets(tree, sock(ml_inst, "Instances", outputs=True), scale_inst.inputs['Instances'])
        link_sockets(tree, sock(sv, "Vector", outputs=True), scale_inst.inputs['Scale'])

    realize = safe_node(tree, 'GeometryNodeRealizeInstances', (bx + 2400, by))
    if realize:
        link_sockets(tree, sock(scale_inst, "Instances", outputs=True), realize.inputs['Geometry'])

    multi_switch = _switch_geo(tree, (bx + 2700, by),
                                gin.outputs["Multi Lancet"],
                                sock(realize, "Geometry", outputs=True),
                                geom)

    link_sockets(tree, sock(multi_switch, "Output", outputs=True), gout.inputs['Geometry'])

    return tree, gin, gout


# ---------------------------------------------------------------------------
# EURO FULL: PALAZZO
# ---------------------------------------------------------------------------

def build_palazzo_group(group_name="MEL_palazzo"):
    """Venetian palazzo (monolith port): arcade ground floor + bifora piano nobile + upper floors."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_int_param(tree, "Palazzo Floors", 3, 1, 8)
    add_float_param(tree, "Palazzo Width", 12.0, 3.0, 40.0)
    add_float_param(tree, "Palazzo Floor H", 4.0, 2.0, 8.0)
    add_int_param(tree, "Palazzo Arches Per Floor", 4, 1, 12)
    add_string_param(tree, "Palazzo Arch Style", "GOTHIC")
    add_bool_param(tree, "Palazzo String Courses", True)
    add_bool_param(tree, "Palazzo Back Wall", False)

    parts = []
    base_x = -3500
    total_h = 12.0

    # Back wall
    bw = safe_node(tree, 'GeometryNodeMeshCube', (base_x, by))
    if bw:
        bw.inputs['Size'].default_value = (12.0, 0.15, 12.0)
    color_node(bw, "palazzo")

    bwt = safe_node(tree, 'GeometryNodeTransform', (base_x + 300, by))
    if bwt:
        bwt.inputs['Translation'].default_value = (0, -0.075, 6.0)
        link_sockets(tree, sock(bw, "Mesh", outputs=True), bwt.inputs['Geometry'])

    bw_switch = _switch_geo(tree, (base_x + 600, by),
                             gin.outputs["Palazzo Back Wall"],
                             sock(bwt, "Geometry", outputs=True), None)
    if bw_switch:
        parts.append(sock(bw_switch, "Output", outputs=True))

    # Create arch variants via package builders
    from .euro_kit import build_ogee_arch_group, build_bifora_group, build_cusped_arch_group, build_gothic_arch_group

    arch_ogee = _ensure_group_node(tree, "MEL_ogee_arch", build_ogee_arch_group, (base_x + 1500, by))
    arch_bifora = _ensure_group_node(tree, "MEL_bifora", build_bifora_group, (base_x + 1500, by + 300))
    arch_cusped = _ensure_group_node(tree, "MEL_cusped_arch", build_cusped_arch_group, (base_x + 1500, by + 600))
    arch_gothic = _ensure_group_node(tree, "MEL_gothic_arch", build_gothic_arch_group, (base_x + 1500, by + 900))

    # Use gothic arch as default (style selection would need runtime switch)
    arch_geo = sock(arch_gothic, "Geometry", outputs=True) if arch_gothic and arch_gothic.node_tree else None

    # Instance arches across floor
    arch_W = 3.0
    line = safe_node(tree, 'GeometryNodeMeshLine', (base_x + 5000, by))
    if line:
        try:
            line.mode = 'OFFSET'
        except Exception:
            pass
        link_sockets(tree, gin.outputs["Palazzo Arches Per Floor"], line.inputs['Count'])
        line.inputs['Start Location'].default_value = (-4.5, 0, 2.0)
        line.inputs['Offset'].default_value = (3.0, 0, 0)
    color_node(line, "palazzo")

    inst = safe_node(tree, 'GeometryNodeInstanceOnPoints', (base_x + 5300, by))
    if inst:
        link_sockets(tree, sock(line, "Mesh", outputs=True), inst.inputs['Points'])
        if arch_geo:
            link_sockets(tree, arch_geo, inst.inputs['Instance'])

    realize = safe_node(tree, 'GeometryNodeRealizeInstances', (base_x + 5600, by))
    if realize:
        link_sockets(tree, sock(inst, "Instances", outputs=True), realize.inputs['Geometry'])
    parts.append(sock(realize, "Geometry", outputs=True))

    # String courses
    sc = safe_node(tree, 'GeometryNodeMeshCube', (base_x + 200, by + 1500))
    if sc:
        sc.inputs['Size'].default_value = (12.6, 0.6, 0.15)
    color_node(sc, "palazzo")

    sct = safe_node(tree, 'GeometryNodeTransform', (base_x + 500, by + 1500))
    if sct:
        sct.inputs['Translation'].default_value = (0, 0, 4.0)
        link_sockets(tree, sock(sc, "Mesh", outputs=True), sct.inputs['Geometry'])

    sc_switch = _switch_geo(tree, (base_x + 800, by + 1500),
                             gin.outputs["Palazzo String Courses"],
                             sock(sct, "Geometry", outputs=True), None)
    if sc_switch:
        parts.append(sock(sc_switch, "Output", outputs=True))

    # Join
    join = safe_node(tree, 'GeometryNodeJoinGeometry', (base_x + 6500, by))
    for p in parts:
        if p is not None:
            link_sockets(tree, p, join.inputs['Geometry'])
    color_node(join, "output")

    link_sockets(tree, sock(join, "Geometry", outputs=True), gout.inputs['Geometry'])

    return tree, gin, gout


# ---------------------------------------------------------------------------
# REGISTRY
# ---------------------------------------------------------------------------

register_builder("MEL_music_note_head_mp", build_note_head_group,
    "Music Note Head (MP)", "Elliptical note head with stem and flag (monolith port)",
    "music")
register_builder("MEL_music_treble_clef_mp", build_treble_clef_group,
    "Music Treble Clef (MP)", "G-clef ornament - spiral + stem + tail + finials (monolith port)",
    "music")
register_builder("MEL_music_staff_mp", build_staff_group,
    "Music Staff (MP)", "Five-line staff with arrayed note heads (monolith port)",
    "music")
register_builder("MEL_music_sheet_rail_mp", build_sheet_music_railing_group,
    "Sheet Music Rail (MP)", "Walkable staff railing - 5 lines + bars + notes + clef + posts (monolith port)",
    "music")
register_builder("MEL_cascading_beams", build_cascading_beams_group,
    "Cascading Beams", "Erindale-style cascading beams with per-step offsets",
    "music")

register_builder("MEL_gothic_portal", build_gothic_portal,
    "Gothic Portal", "Stub: routes to MEL_greybox_room_kit (monolith override)",
    "ornament")
register_builder("MEL_gothic_bay", build_gothic_bay,
    "Gothic Bay", "Stub: routes to MEL_greybox_room_kit (monolith override)",
    "ornament")
register_builder("MEL_gothic_buttress_kit", build_gothic_buttress_kit,
    "Gothic Buttress Kit", "Stub: routes to MEL_buttress (monolith override)",
    "ornament")
register_builder("MEL_gothic_tracery_panel", build_gothic_tracery_panel,
    "Gothic Tracery Panel", "Stub: routes to MEL_trefoil (monolith override)",
    "ornament")
register_builder("MEL_romanesque_apse", build_romanesque_apse,
    "Romanesque Apse", "Stub: routes to MEL_greybox_room_kit (monolith override)",
    "ornament")
register_builder("MEL_romanesque_arcade_bay", build_romanesque_arcade_bay,
    "Romanesque Arcade Bay", "Stub: routes to MEL_greybox_room_kit (monolith override)",
    "ornament")
register_builder("MEL_venetian_loggia_bay", build_venetian_loggia_bay,
    "Venetian Loggia Bay", "Stub: routes to MEL_bifora (monolith override)",
    "ornament")

register_builder("MEL_rose_window", build_rose_window_group,
    "Rose Window", "Radial Gothic rose window - petal count = musical time signature top",
    "ornament")
register_builder("MEL_lancet", build_lancet_group,
    "Lancet Window", "Tall slender Gothic pointed window, 1+ side-by-side",
    "ornament")
register_builder("MEL_palazzo", build_palazzo_group,
    "Palazzo", "Venetian palazzo: arcade ground floor + bifora piano nobile + upper floors",
    "ornament")
