"""MEL core forms port — tower, organic, hybrid, curved_wall, building.

Ported from monolith surreal_architecture_gen.py (P2).
Params-as-values port. Regenerable.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, add_string_param,
    register_builder, sock,
)


def _node(tree, bl_idname, loc=(0, 0), **kwargs):
    """Create a node with optional attribute/input defaults."""
    n = tree.nodes.new(bl_idname)
    n.location = loc
    for k, v in kwargs.items():
        try:
            if hasattr(n, k):
                setattr(n, k, v)
            elif k in n.inputs:
                n.inputs[k].default_value = v
        except Exception:
            pass
    return n


def _link(tree, src, dst):
    """Link two sockets, ignoring errors."""
    try:
        tree.links.new(src, dst)
    except Exception:
        pass


def _is_socket(obj):
    """Check if obj is a Blender socket (has id_data)."""
    return hasattr(obj, 'id_data')


def _math(tree, op, a, b, loc):
    """Create a Math node. a and b can be sockets or float values."""
    node = safe_node(tree, 'ShaderNodeMath', loc)
    node.operation = op
    if _is_socket(a):
        link_sockets(tree, a, node.inputs[0])
    else:
        node.inputs[0].default_value = a
    if _is_socket(b):
        link_sockets(tree, b, node.inputs[1])
    else:
        node.inputs[1].default_value = b
    return node


def _float_to_int(tree, float_sock, loc):
    """Convert a float socket to an int socket using FloatToInt node.
    Returns an Int socket, or None if conversion fails."""
    try:
        node = tree.nodes.new('FunctionNodeFloatToInt')
        node.location = loc
        link_sockets(tree, float_sock, node.inputs[0])
        return node.outputs[0]
    except Exception:
        # If conversion fails, return None - caller should use default_value
        try:
            tree.nodes.remove(node)
        except Exception:
            pass
        return None


def _mul(tree, a, b, loc):
    """Create a Multiply node. a and b can be sockets or values."""
    return _math(tree, 'MULTIPLY', a, b, loc).outputs['Value']


def _add(tree, a, b, loc):
    """Create an Add node. a and b can be sockets or values."""
    return _math(tree, 'ADD', a, b, loc).outputs['Value']


def _sub(tree, a, b, loc):
    """Create a Subtract node. a and b can be sockets or values."""
    return _math(tree, 'SUBTRACT', a, b, loc).outputs['Value']


def _max(tree, a, b, loc):
    """Create a Maximum node. a and b can be sockets or values."""
    return _math(tree, 'MAXIMUM', a, b, loc).outputs['Value']


# ──────────────────────────────────────────────────────────────────────
# Helper functions (ported from monolith)
# ──────────────────────────────────────────────────────────────────────

def _add_taper_chain(tree, in_geom, height_sock, taper_sock, x=0, y=-300):
    """Port of add_taper_chain. height_sock and taper_sock are sockets."""
    pos = safe_node(tree, 'GeometryNodeInputPosition', (x, y))
    color_node(pos, "input")
    sep = safe_node(tree, 'ShaderNodeSeparateXYZ', (x+200, y))
    link_sockets(tree, pos.outputs['Position'], sep.inputs['Vector'])

    map_range = safe_node(tree, 'ShaderNodeMapRange', (x+400, y))
    neg_half = _mul(tree, height_sock, -0.5, (x+200, y-200))
    pos_half = _mul(tree, height_sock, 0.5, (x+200, y-400))
    link_sockets(tree, neg_half, map_range.inputs['From Min'])
    link_sockets(tree, pos_half, map_range.inputs['From Max'])
    map_range.inputs['To Min'].default_value = 1.0
    one_minus_taper = _sub(tree, 1.0, taper_sock, (x+200, y-600))
    to_max = _max(tree, one_minus_taper, 0.05, (x+400, y-600))
    link_sockets(tree, to_max, map_range.inputs['To Max'])
    link_sockets(tree, sep.outputs['Z'], map_range.inputs['Value'])
    color_node(map_range, "tower")

    combine = safe_node(tree, 'ShaderNodeCombineXYZ', (x+600, y))
    link_sockets(tree, map_range.outputs['Result'], combine.inputs['X'])
    link_sockets(tree, map_range.outputs['Result'], combine.inputs['Y'])
    combine.inputs['Z'].default_value = 1.0

    mul = safe_node(tree, 'ShaderNodeVectorMath', (x+800, y+100))
    mul.operation = 'MULTIPLY'
    link_sockets(tree, pos.outputs['Position'], mul.inputs[0])
    link_sockets(tree, combine.outputs['Vector'], mul.inputs[1])

    sub = safe_node(tree, 'ShaderNodeVectorMath', (x+1000, y+100))
    sub.operation = 'SUBTRACT'
    link_sockets(tree, mul.outputs['Vector'], sub.inputs[0])
    link_sockets(tree, pos.outputs['Position'], sub.inputs[1])

    set_pos = safe_node(tree, 'GeometryNodeSetPosition', (x+1200, 0))
    color_node(set_pos, "deform")
    link_sockets(tree, in_geom, set_pos.inputs['Geometry'])
    link_sockets(tree, sub.outputs['Vector'], set_pos.inputs['Offset'])
    return set_pos.outputs['Geometry']


def _add_noise_displace(tree, in_geom, scale, detail, strength, seed_sock, x=0, y=300):
    """Port of add_noise_displace. seed_sock is a socket. scale can be socket or float."""
    pos = safe_node(tree, 'GeometryNodeInputPosition', (x, y))
    color_node(pos, "input")
    noise = safe_node(tree, 'ShaderNodeTexNoise', (x+200, y))
    noise.noise_dimensions = '4D'
    # seed_sock * 0.1 for W
    w_val = _mul(tree, seed_sock, 0.1, (x, y-200))
    link_sockets(tree, w_val, noise.inputs['W'])
    if _is_socket(scale):
        link_sockets(tree, scale, noise.inputs['Scale'])
    else:
        noise.inputs['Scale'].default_value = scale
    noise.inputs['Detail'].default_value = detail
    noise.inputs['Roughness'].default_value = 0.55
    noise.inputs['Distortion'].default_value = 0.4
    link_sockets(tree, pos.outputs['Position'], noise.inputs['Vector'])
    color_node(noise, "noise")

    center = safe_node(tree, 'ShaderNodeVectorMath', (x+450, y))
    center.operation = 'SUBTRACT'
    center.inputs[1].default_value = (0.5, 0.5, 0.5)
    link_sockets(tree, noise.outputs['Color'], center.inputs[0])

    sc = safe_node(tree, 'ShaderNodeVectorMath', (x+650, y))
    sc.operation = 'SCALE'
    if _is_socket(strength):
        link_sockets(tree, strength, sc.inputs['Scale'])
    else:
        sc.inputs['Scale'].default_value = strength
    link_sockets(tree, center.outputs['Vector'], sc.inputs[0])

    set_pos = safe_node(tree, 'GeometryNodeSetPosition', (x+850, 0))
    color_node(set_pos, "deform")
    link_sockets(tree, in_geom, set_pos.inputs['Geometry'])
    link_sockets(tree, sc.outputs['Vector'], set_pos.inputs['Offset'])
    return set_pos.outputs['Geometry']


def _add_wave_bulge(tree, in_geom, frequency, flow, bulge, x=0, y=300):
    """Port of add_wave_bulge. frequency, flow, bulge are float values."""
    pos = safe_node(tree, 'GeometryNodeInputPosition', (x, y))
    color_node(pos, "input")
    sep = safe_node(tree, 'ShaderNodeSeparateXYZ', (x+200, y))
    link_sockets(tree, pos.outputs['Position'], sep.inputs['Vector'])

    z_freq = safe_node(tree, 'ShaderNodeMath', (x+400, y))
    z_freq.operation = 'MULTIPLY'
    z_freq.inputs[1].default_value = frequency
    link_sockets(tree, sep.outputs['Z'], z_freq.inputs[0])

    sine = safe_node(tree, 'ShaderNodeMath', (x+600, y))
    sine.operation = 'SINE'
    link_sockets(tree, z_freq.outputs['Value'], sine.inputs[0])
    color_node(sine, "organic")

    flow_mult = safe_node(tree, 'ShaderNodeMath', (x+800, y))
    flow_mult.operation = 'MULTIPLY'
    flow_mult.inputs[1].default_value = flow + bulge
    link_sockets(tree, sine.outputs['Value'], flow_mult.inputs[0])

    bvec = safe_node(tree, 'ShaderNodeCombineXYZ', (x+1000, y))
    link_sockets(tree, flow_mult.outputs['Value'], bvec.inputs['X'])
    link_sockets(tree, flow_mult.outputs['Value'], bvec.inputs['Y'])
    bvec.inputs['Z'].default_value = 0.0

    pos_xy = safe_node(tree, 'ShaderNodeCombineXYZ', (x+600, y-200))
    link_sockets(tree, sep.outputs['X'], pos_xy.inputs['X'])
    link_sockets(tree, sep.outputs['Y'], pos_xy.inputs['Y'])
    pos_xy.inputs['Z'].default_value = 0.0

    apply_b = safe_node(tree, 'ShaderNodeVectorMath', (x+1200, y-100))
    apply_b.operation = 'MULTIPLY'
    link_sockets(tree, pos_xy.outputs['Vector'], apply_b.inputs[0])
    link_sockets(tree, bvec.outputs['Vector'], apply_b.inputs[1])

    set_pos = safe_node(tree, 'GeometryNodeSetPosition', (x+1400, 0))
    color_node(set_pos, "deform")
    link_sockets(tree, in_geom, set_pos.inputs['Geometry'])
    link_sockets(tree, apply_b.outputs['Vector'], set_pos.inputs['Offset'])
    return set_pos.outputs['Geometry']


def _add_twist(tree, in_geom, twist_angle_sock, height_sock, x=0, y=300):
    """Port of add_twist. twist_angle_sock and height_sock are sockets."""
    pos = safe_node(tree, 'GeometryNodeInputPosition', (x, y))
    color_node(pos, "input")
    sep = safe_node(tree, 'ShaderNodeSeparateXYZ', (x+200, y))
    link_sockets(tree, pos.outputs['Position'], sep.inputs['Vector'])

    map_range = safe_node(tree, 'ShaderNodeMapRange', (x+400, y))
    neg_half = _mul(tree, height_sock, -0.5, (x+200, y-200))
    pos_half = _mul(tree, height_sock, 0.5, (x+200, y-400))
    link_sockets(tree, neg_half, map_range.inputs['From Min'])
    link_sockets(tree, pos_half, map_range.inputs['From Max'])
    map_range.inputs['To Min'].default_value = 0.0
    link_sockets(tree, twist_angle_sock, map_range.inputs['To Max'])
    link_sockets(tree, sep.outputs['Z'], map_range.inputs['Value'])

    rvec = safe_node(tree, 'ShaderNodeCombineXYZ', (x+600, y))
    rvec.inputs['X'].default_value = 0.0
    rvec.inputs['Y'].default_value = 0.0
    link_sockets(tree, map_range.outputs['Result'], rvec.inputs['Z'])

    rotate = safe_node(tree, 'ShaderNodeVectorRotate', (x+800, y))
    rotate.rotation_type = 'EULER_XYZ'
    link_sockets(tree, pos.outputs['Position'], rotate.inputs['Vector'])
    link_sockets(tree, rvec.outputs['Vector'], rotate.inputs['Rotation'])
    color_node(rotate, "organic")

    sub = safe_node(tree, 'ShaderNodeVectorMath', (x+1000, y))
    sub.operation = 'SUBTRACT'
    link_sockets(tree, rotate.outputs['Vector'], sub.inputs[0])
    link_sockets(tree, pos.outputs['Position'], sub.inputs[1])

    set_pos = safe_node(tree, 'GeometryNodeSetPosition', (x+1200, 0))
    color_node(set_pos, "deform")
    link_sockets(tree, in_geom, set_pos.inputs['Geometry'])
    link_sockets(tree, sub.outputs['Vector'], set_pos.inputs['Offset'])
    return set_pos.outputs['Geometry']


def _make_harmonic_value(tree, index_socket, freq_a, freq_b, layers, x, y):
    """Port of make_harmonic_value. freq_a, freq_b are floats, layers is int."""
    m1 = safe_node(tree, 'ShaderNodeMath', (x, y))
    m1.operation = 'MULTIPLY'
    m1.inputs[1].default_value = freq_a
    link_sockets(tree, index_socket, m1.inputs[0])
    s1 = safe_node(tree, 'ShaderNodeMath', (x+200, y))
    s1.operation = 'SINE'
    link_sockets(tree, m1.outputs['Value'], s1.inputs[0])
    color_node(s1, "ornament")

    if layers <= 1:
        return s1.outputs['Value']

    m2 = safe_node(tree, 'ShaderNodeMath', (x, y-200))
    m2.operation = 'MULTIPLY'
    m2.inputs[1].default_value = freq_b
    link_sockets(tree, index_socket, m2.inputs[0])
    s2 = safe_node(tree, 'ShaderNodeMath', (x+200, y-200))
    s2.operation = 'SINE'
    link_sockets(tree, m2.outputs['Value'], s2.inputs[0])
    color_node(s2, "ornament")

    add = safe_node(tree, 'ShaderNodeMath', (x+400, y-100))
    add.operation = 'ADD'
    link_sockets(tree, s1.outputs['Value'], add.inputs[0])
    link_sockets(tree, s2.outputs['Value'], add.inputs[1])

    if layers <= 2:
        return add.outputs['Value']

    m3 = safe_node(tree, 'ShaderNodeMath', (x, y-400))
    m3.operation = 'MULTIPLY'
    m3.inputs[1].default_value = freq_a * 2.0
    link_sockets(tree, index_socket, m3.inputs[0])
    s3 = safe_node(tree, 'ShaderNodeMath', (x+200, y-400))
    s3.operation = 'SINE'
    link_sockets(tree, m3.outputs['Value'], s3.inputs[0])
    color_node(s3, "ornament")
    add2 = safe_node(tree, 'ShaderNodeMath', (x+400, y-300))
    add2.operation = 'ADD'
    link_sockets(tree, add.outputs['Value'], add2.inputs[0])
    link_sockets(tree, s3.outputs['Value'], add2.inputs[1])
    final = add2

    for i, fmul in enumerate([3.0, 5.0][:layers-3], start=4):
        mn = safe_node(tree, 'ShaderNodeMath', (x, y-200*i-200))
        mn.operation = 'MULTIPLY'
        mn.inputs[1].default_value = freq_b * fmul / 3.0
        link_sockets(tree, index_socket, mn.inputs[0])
        sn = safe_node(tree, 'ShaderNodeMath', (x+200, y-200*i-200))
        sn.operation = 'SINE'
        link_sockets(tree, mn.outputs['Value'], sn.inputs[0])
        addn = safe_node(tree, 'ShaderNodeMath', (x+400, y-200*i-100))
        addn.operation = 'ADD'
        link_sockets(tree, final.outputs['Value'], addn.inputs[0])
        link_sockets(tree, sn.outputs['Value'], addn.inputs[1])
        final = addn

    return final.outputs['Value']


# ──────────────────────────────────────────────────────────────────────
# Sub-builders (ported from monolith, used by build_building)
# ──────────────────────────────────────────────────────────────────────

def _impl_build_tower(tree, gin, base_x=-1400):
    """Port of build_tower. Reads params from gin.outputs."""
    cyl = safe_node(tree, 'GeometryNodeMeshCylinder', (base_x, 0))
    color_node(cyl, "tower")
    # Vertices = max(8, complexity_level * 8)
    complexity_mul = _mul(tree, gin.outputs["Complexity Level"], 8, (base_x-400, 200))
    verts_max = _max(tree, complexity_mul, 8, (base_x-200, 200))
    link_sockets(tree, _float_to_int(tree, verts_max, (base_x-100, 200)), cyl.inputs['Vertices'])
    # Side Segments = max(2, recursion_depth * 4)
    recursion_mul = _mul(tree, gin.outputs["Recursion Depth"], 4, (base_x-400, 400))
    sides_max = _max(tree, recursion_mul, 2, (base_x-200, 400))
    link_sockets(tree, _float_to_int(tree, sides_max, (base_x-100, 400)), cyl.inputs['Side Segments'])
    cyl.inputs['Fill Segments'].default_value = 1
    link_sockets(tree, gin.outputs["Base Radius"], cyl.inputs['Radius'])
    link_sockets(tree, gin.outputs["Height"], cyl.inputs['Depth'])

    geom = cyl.outputs['Mesh']
    geom = _add_taper_chain(tree, geom, gin.outputs["Height"], gin.outputs["Taper Ratio"], x=base_x+300, y=-400)
    geom = _add_twist(tree, geom, gin.outputs["Twist Angle"], gin.outputs["Height"], x=base_x+1600, y=-400)
    # strength = variation_intensity * 0.5 + symmetry_break * 0.3
    var_mul = _mul(tree, gin.outputs["Variation Intensity"], 0.5, (base_x+2400, 600))
    sym_mul = _mul(tree, gin.outputs["Symmetry Break"], 0.3, (base_x+2400, 800))
    strength = _add(tree, var_mul, sym_mul, (base_x+2600, 700))
    # scale = 1.5 + complexity_level * 0.5
    scale_val = _add(tree, 1.5, _mul(tree, gin.outputs["Complexity Level"], 0.5, (base_x+2400, 1000)), (base_x+2600, 1000))
    # detail = float(complexity_level)
    detail_val = gin.outputs["Complexity Level"]
    geom = _add_noise_displace(tree, geom, scale_val, 3.0, strength, gin.outputs["Seed"], x=base_x+2900, y=400)
    return geom


def _impl_build_organic(tree, gin, base_x=-1400):
    """Port of build_organic. Reads params from gin.outputs."""
    sphere = safe_node(tree, 'GeometryNodeMeshUVSphere', (base_x, 0))
    color_node(sphere, "organic")
    # Segments = max(16, complexity_level * 8)
    comp_mul = _mul(tree, gin.outputs["Complexity Level"], 8, (base_x-400, 200))
    segs_max = _max(tree, comp_mul, 16, (base_x-200, 200))
    link_sockets(tree, _float_to_int(tree, segs_max, (base_x-100, 200)), sphere.inputs['Segments'])
    # Rings = max(8, complexity_level * 4)
    comp_mul2 = _mul(tree, gin.outputs["Complexity Level"], 4, (base_x-400, 400))
    rings_max = _max(tree, comp_mul2, 8, (base_x-200, 400))
    link_sockets(tree, _float_to_int(tree, rings_max, (base_x-100, 400)), sphere.inputs['Rings'])
    link_sockets(tree, gin.outputs["Base Radius"], sphere.inputs['Radius'])

    geom = sphere.outputs['Mesh']

    # Stretch sphere to height
    pos = safe_node(tree, 'GeometryNodeInputPosition', (base_x+300, -400))
    color_node(pos, "input")
    sep = safe_node(tree, 'ShaderNodeSeparateXYZ', (base_x+500, -400))
    link_sockets(tree, pos.outputs['Position'], sep.inputs['Vector'])
    # z_str = height / max(0.1, base_radius * 2)
    radius_mul = _mul(tree, gin.outputs["Base Radius"], 2, (base_x+500, -600))
    radius_max = _max(tree, radius_mul, 0.1, (base_x+700, -600))
    z_str = _math(tree, 'DIVIDE', gin.outputs["Height"], radius_max, (base_x+900, -600))
    link_sockets(tree, sep.outputs['Z'], z_str.inputs[0])

    new_pos = safe_node(tree, 'ShaderNodeCombineXYZ', (base_x+900, -400))
    link_sockets(tree, sep.outputs['X'], new_pos.inputs['X'])
    link_sockets(tree, sep.outputs['Y'], new_pos.inputs['Y'])
    link_sockets(tree, z_str.outputs['Value'], new_pos.inputs['Z'])
    delta = safe_node(tree, 'ShaderNodeVectorMath', (base_x+1100, -400))
    delta.operation = 'SUBTRACT'
    link_sockets(tree, new_pos.outputs['Vector'], delta.inputs[0])
    link_sockets(tree, pos.outputs['Position'], delta.inputs[1])
    set_str = safe_node(tree, 'GeometryNodeSetPosition', (base_x+1300, 0))
    color_node(set_str, "deform")
    link_sockets(tree, geom, set_str.inputs['Geometry'])
    link_sockets(tree, delta.outputs['Vector'], set_str.inputs['Offset'])
    geom = set_str.outputs['Geometry']

    geom = _add_wave_bulge(tree, geom, 2.0, 0.3, 0.2, x=base_x+1600, y=400)
    geom = _add_twist(tree, geom, gin.outputs["Twist Angle"], gin.outputs["Height"], x=base_x+3100, y=400)
    # strength = flow_amount * 0.3 + variation_intensity * 0.2
    flow_mul = _mul(tree, gin.outputs["Flow Amount"], 0.3, (base_x+3800, 600))
    var_mul = _mul(tree, gin.outputs["Variation Intensity"], 0.2, (base_x+3800, 800))
    strength = _add(tree, flow_mul, var_mul, (base_x+4000, 700))
    geom = _add_noise_displace(tree, geom, 2.0, 3.0, strength, gin.outputs["Seed"], x=base_x+4400, y=400)
    return geom


def _impl_build_railing(tree, gin, x_offset=0, y_offset=0, length=None, height=None):
    """Port of build_railing. Reads params from gin.outputs."""
    L = length if length is not None else gin.outputs["Rail Length"]
    H = height if height is not None else gin.outputs["Rail Height"]
    bx = -1400 + x_offset
    parts = []

    bal_prof = safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (bx - 300, -300))
    if bal_prof:
        bal_prof.inputs['Resolution'].default_value = 10
        link_sockets(tree, gin.outputs["Rail Baluster Radius"], bal_prof.inputs['Radius'])
        color_node(bal_prof, "railing")

    rail_prof = safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (bx - 300, -600))
    if rail_prof:
        rail_prof.inputs['Resolution'].default_value = 10
        link_sockets(tree, gin.outputs["Rail Top Size"], rail_prof.inputs['Radius'])
        color_node(rail_prof, "railing")

    bal_line = safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (bx, 0))
    if bal_line:
        bal_line.inputs['Start'].default_value = (0, 0, 0)
        bal_line.inputs['End'].default_value = (0, 0, 1.0)
        color_node(bal_line, "railing")

    if bal_line and bal_prof:
        bal_sweep = safe_node(tree, 'GeometryNodeCurveToMesh', (bx + 250, 0))
        if bal_sweep:
            link_sockets(tree, bal_line.outputs['Curve'], bal_sweep.inputs['Curve'])
            link_sockets(tree, bal_prof.outputs['Curve'], bal_sweep.inputs['Profile Curve'])
            bal_sweep.inputs['Fill Caps'].default_value = True
            color_node(bal_sweep, "railing")
            bal_geom_out = bal_sweep.outputs['Mesh']
        else:
            bal_geom_out = None
    else:
        bal_geom_out = None

    pt_line = safe_node(tree, 'GeometryNodeMeshLine', (bx, 400))
    if pt_line:
        try:
            pt_line.mode = 'END_POINTS'
        except Exception:
            pass
        link_sockets(tree, gin.outputs["Rail Baluster Count"], pt_line.inputs['Count'])
        pt_line.inputs['Start Location'].default_value = (-1.5, 0, 0)
        pt_line.inputs['Offset'].default_value = (3.0, 0, 0)
        color_node(pt_line, "railing")

    if pt_line and bal_geom_out is not None:
        iop = safe_node(tree, 'GeometryNodeInstanceOnPoints', (bx + 500, 300))
        if iop:
            link_sockets(tree, pt_line.outputs['Mesh'], iop.inputs['Points'])
            link_sockets(tree, bal_geom_out, iop.inputs['Instance'])
            color_node(iop, "railing")
            parts.append(iop.outputs['Instances'])

    if parts:
        realize = safe_node(tree, 'GeometryNodeRealizeInstances', (bx + 800, 300))
        if realize:
            link_sockets(tree, parts[0], realize.inputs['Geometry'])
            return realize.outputs['Geometry']
    return parts[0] if parts else None


def _impl_build_arch(tree, gin, base_x=-1400):
    """Port of build_arch. Reads params from gin.outputs."""
    curve = safe_node(tree, 'GeometryNodeCurveArc', (base_x, 200))
    color_node(curve, "arch")
    curve.mode = 'RADIUS'
    curve.inputs['Resolution'].default_value = 32
    link_sockets(tree, gin.outputs["Arch Radius"], curve.inputs['Radius'])
    link_sockets(tree, gin.outputs["Arch Sweep Deg"], curve.inputs['Sweep Angle'])

    profile = safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x, -200))
    color_node(profile, "arch")
    profile.mode = 'RADIUS'
    profile.inputs['Resolution'].default_value = 8
    link_sockets(tree, gin.outputs["Arch Thickness"], profile.inputs['Radius'])

    sweep_node = safe_node(tree, 'GeometryNodeCurveToMesh', (base_x+300, 0))
    color_node(sweep_node, "arch")
    link_sockets(tree, curve.outputs['Curve'], sweep_node.inputs['Curve'])
    link_sockets(tree, profile.outputs['Curve'], sweep_node.inputs['Profile Curve'])
    sweep_node.inputs['Fill Caps'].default_value = True

    idx = safe_node(tree, 'GeometryNodeInputIndex', (base_x, -500))
    harmonic = _make_harmonic_value(tree, idx.outputs['Index'],
                                    0.6, 1.2, 2, base_x+200, -500)
    sc = safe_node(tree, 'ShaderNodeMath', (base_x+1000, -500))
    sc.operation = 'MULTIPLY'
    sc.inputs[1].default_value = 0.05
    link_sockets(tree, harmonic, sc.inputs[0])

    ovec = safe_node(tree, 'ShaderNodeCombineXYZ', (base_x+1200, -500))
    ovec.inputs['X'].default_value = 0
    ovec.inputs['Y'].default_value = 0
    link_sockets(tree, sc.outputs['Value'], ovec.inputs['Z'])

    set_pos = safe_node(tree, 'GeometryNodeSetPosition', (base_x+1400, 0))
    color_node(set_pos, "deform")
    link_sockets(tree, sweep_node.outputs['Mesh'], set_pos.inputs['Geometry'])
    link_sockets(tree, ovec.outputs['Vector'], set_pos.inputs['Offset'])

    geom = set_pos.outputs['Geometry']
    return geom


def _impl_build_buttress(tree, gin, base_x=-1400):
    """Port of build_buttress. Reads params from gin.outputs."""
    line = safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (base_x, 200))
    color_node(line, "buttress")
    line.mode = 'POINTS'
    line.inputs['Start'].default_value = (0, 0, 0)
    link_sockets(tree, gin.outputs["Buttress Span"], line.inputs['End'])

    sample = safe_node(tree, 'GeometryNodeResampleCurve', (base_x+300, 200))
    color_node(sample, "buttress")
    try:
        sample.inputs['Mode'].default_value = 'Count'
    except Exception:
        pass
    sample.inputs['Count'].default_value = 32
    link_sockets(tree, line.outputs['Curve'], sample.inputs['Curve'])

    param = safe_node(tree, 'GeometryNodeSplineParameter', (base_x+300, -200))
    mul_pi = safe_node(tree, 'ShaderNodeMath', (base_x+500, -200))
    mul_pi.operation = 'MULTIPLY'
    mul_pi.inputs[1].default_value = math.pi
    link_sockets(tree, param.outputs['Factor'], mul_pi.inputs[0])
    sine = safe_node(tree, 'ShaderNodeMath', (base_x+700, -200))
    sine.operation = 'SINE'
    link_sockets(tree, mul_pi.outputs['Value'], sine.inputs[0])
    bow_h = safe_node(tree, 'ShaderNodeMath', (base_x+900, -200))
    bow_h.operation = 'MULTIPLY'
    link_sockets(tree, gin.outputs["Buttress Arch Bow"], bow_h.inputs[1])
    link_sockets(tree, sine.outputs['Value'], bow_h.inputs[0])

    ovec = safe_node(tree, 'ShaderNodeCombineXYZ', (base_x+1100, -200))
    ovec.inputs['X'].default_value = 0
    ovec.inputs['Y'].default_value = 0
    link_sockets(tree, bow_h.outputs['Value'], ovec.inputs['Z'])

    set_arch = safe_node(tree, 'GeometryNodeSetPosition', (base_x+600, 200))
    color_node(set_arch, "deform")
    link_sockets(tree, sample.outputs['Curve'], set_arch.inputs['Geometry'])
    link_sockets(tree, ovec.outputs['Vector'], set_arch.inputs['Offset'])

    profile = safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x, -500))
    color_node(profile, "buttress")
    profile.mode = 'RADIUS'
    profile.inputs['Resolution'].default_value = 6
    profile.inputs['Radius'].default_value = 0.15

    sweep = safe_node(tree, 'GeometryNodeCurveToMesh', (base_x+1300, 0))
    color_node(sweep, "buttress")
    link_sockets(tree, set_arch.outputs['Geometry'], sweep.inputs['Curve'])
    link_sockets(tree, profile.outputs['Curve'], sweep.inputs['Profile Curve'])
    sweep.inputs['Fill Caps'].default_value = True

    geom = sweep.outputs['Mesh']
    return geom


# ──────────────────────────────────────────────────────────────────────
# GROUP BUILDERS (ported from monolith)
# ──────────────────────────────────────────────────────────────────────

def build_tower_group(group_name="MEL_tower"):
    """Port of build_tower as a group builder."""
    tree, gin, gout = new_geometry_tree(group_name)
    add_int_param(tree, "Complexity Level", 3, 1, 5)
    add_int_param(tree, "Recursion Depth", 3, 1, 6)
    add_float_param(tree, "Base Radius", 1.2, 0.1, 10.0)
    add_float_param(tree, "Height", 5.0, 0.5, 30.0)
    add_float_param(tree, "Taper Ratio", 0.6, 0.0, 1.0)
    add_float_param(tree, "Twist Angle", 0.0, -6.283, 6.283)
    add_float_param(tree, "Variation Intensity", 0.5, 0.0, 1.0)
    add_float_param(tree, "Symmetry Break", 0.3, 0.0, 1.0)
    add_int_param(tree, "Seed", 42, 0, 9999)

    geom = _impl_build_tower(tree, gin, base_x=-1400)
    if geom is not None:
        link_sockets(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_tower")
    return tree, gin, gout


register_builder(
    "MEL_tower", build_tower_group,
    "Tower", "Core form builder (absorbed from monolith build_tower).",
    category="structures")


def build_organic_group(group_name="MEL_organic"):
    """Port of build_organic as a group builder."""
    tree, gin, gout = new_geometry_tree(group_name)
    add_int_param(tree, "Complexity Level", 3, 1, 5)
    add_float_param(tree, "Base Radius", 1.2, 0.1, 10.0)
    add_float_param(tree, "Height", 5.0, 0.5, 30.0)
    add_float_param(tree, "Wave Frequency", 2.0, 0.5, 10.0)
    add_float_param(tree, "Flow Amount", 0.3, 0.0, 2.0)
    add_float_param(tree, "Bulge Amount", 0.2, 0.0, 2.0)
    add_float_param(tree, "Twist Angle", 0.0, -6.283, 6.283)
    add_float_param(tree, "Variation Intensity", 0.5, 0.0, 1.0)
    add_int_param(tree, "Seed", 42, 0, 9999)

    geom = _impl_build_organic(tree, gin, base_x=-1400)
    if geom is not None:
        link_sockets(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_organic")
    return tree, gin, gout


register_builder(
    "MEL_organic", build_organic_group,
    "Organic", "Core form builder (absorbed from monolith build_organic).",
    category="structures")


def build_hybrid_group(group_name="MEL_hybrid"):
    """Port of build_hybrid as a group builder."""
    tree, gin, gout = new_geometry_tree(group_name)
    add_int_param(tree, "Complexity Level", 3, 1, 5)
    add_int_param(tree, "Recursion Depth", 3, 1, 6)
    add_float_param(tree, "Base Radius", 1.2, 0.1, 10.0)
    add_float_param(tree, "Height", 5.0, 0.5, 30.0)
    add_float_param(tree, "Taper Ratio", 0.6, 0.0, 1.0)
    add_float_param(tree, "Twist Angle", 0.0, -6.283, 6.283)
    add_float_param(tree, "Variation Intensity", 0.5, 0.0, 1.0)
    add_float_param(tree, "Symmetry Break", 0.3, 0.0, 1.0)
    add_float_param(tree, "Wave Frequency", 2.0, 0.5, 10.0)
    add_float_param(tree, "Flow Amount", 0.3, 0.0, 2.0)
    add_float_param(tree, "Bulge Amount", 0.2, 0.0, 2.0)
    add_int_param(tree, "Seed", 42, 0, 9999)

    tower_geom = _impl_build_tower(tree, gin, base_x=-2400)
    organic_geom = _impl_build_organic(tree, gin, base_x=2200)

    join = safe_node(tree, 'GeometryNodeJoinGeometry', (5800, 0))
    color_node(join, "output")
    link_sockets(tree, tower_geom, join.inputs['Geometry'])
    link_sockets(tree, organic_geom, join.inputs['Geometry'])

    geom = join.outputs['Geometry']
    if geom is not None:
        link_sockets(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_hybrid")
    return tree, gin, gout


register_builder(
    "MEL_hybrid", build_hybrid_group,
    "Hybrid", "Core form builder (absorbed from monolith build_hybrid).",
    category="structures")


def build_curved_wall_group(group_name="MEL_curved_wall"):
    """Port of build_curved_wall as a group builder."""
    tree, gin, gout = new_geometry_tree(group_name)
    add_float_param(tree, "Wall Arc Angle", 90.0, 0.0, 360.0)
    add_float_param(tree, "Wall Thickness", 0.4, 0.02, 2.0)
    add_float_param(tree, "Wall Height", 3.0, 0.5, 10.0)
    add_float_param(tree, "Wall Arc Radius", 5.0, 0.3, 20.0)
    add_int_param(tree, "Crenel Merlon Count", 8, 0, 60)

    base_x = -1400

    arc_deg = gin.outputs["Wall Arc Angle"]
    thickness = gin.outputs["Wall Thickness"]
    h = gin.outputs["Wall Height"]
    radius = gin.outputs["Wall Arc Radius"]
    crenels = gin.outputs["Crenel Merlon Count"]

    # Compute arc radians from degrees
    arc_rad = _mul(tree, arc_deg, math.pi / 180.0, (base_x-600, 200))
    half_ang = _mul(tree, arc_rad, 0.5, (base_x-400, 200))

    # tan_len = (4/3) * tan(arc/4) * radius
    quarter_arc = _mul(tree, arc_rad, 0.25, (base_x-600, 400))
    tan_node = safe_node(tree, 'ShaderNodeMath', (base_x-400, 400))
    tan_node.operation = 'TANGENT'
    link_sockets(tree, quarter_arc, tan_node.inputs[0])
    tan_len = _mul(tree, _mul(tree, tan_node.outputs['Value'], 4/3, (base_x-200, 400)), radius, (base_x, 400))

    # Compute start/end points using sin/cos of half_ang
    neg_half = _mul(tree, half_ang, -1, (base_x-600, 600))
    sin_neg = safe_node(tree, 'ShaderNodeMath', (base_x-400, 600))
    sin_neg.operation = 'SINE'
    link_sockets(tree, neg_half, sin_neg.inputs[0])
    cos_neg = safe_node(tree, 'ShaderNodeMath', (base_x-400, 800))
    cos_neg.operation = 'COSINE'
    link_sockets(tree, neg_half, cos_neg.inputs[0])
    sin_pos = safe_node(tree, 'ShaderNodeMath', (base_x-400, 1000))
    sin_pos.operation = 'SINE'
    link_sockets(tree, half_ang, sin_pos.inputs[0])
    cos_pos = safe_node(tree, 'ShaderNodeMath', (base_x-400, 1200))
    cos_pos.operation = 'COSINE'
    link_sockets(tree, half_ang, cos_pos.inputs[0])

    sx = _mul(tree, cos_neg.outputs['Value'], radius, (base_x-200, 600))
    sy = _mul(tree, sin_neg.outputs['Value'], radius, (base_x-200, 800))
    ex = _mul(tree, cos_pos.outputs['Value'], radius, (base_x-200, 1000))
    ey = _mul(tree, sin_pos.outputs['Value'], radius, (base_x-200, 1200))

    # Tangent directions
    stx = _mul(tree, _mul(tree, sin_neg.outputs['Value'], -1, (base_x, 1400)), tan_len, (base_x+200, 600))
    sty = _mul(tree, cos_neg.outputs['Value'], tan_len, (base_x+200, 800))
    etx = _mul(tree, _mul(tree, sin_pos.outputs['Value'], -1, (base_x, 1600)), tan_len, (base_x+200, 1000))
    ety = _mul(tree, cos_pos.outputs['Value'], tan_len, (base_x+200, 1200))

    # Build bezier segment
    spine = safe_node(tree, 'GeometryNodeCurvePrimitiveBezierSegment', (base_x, 0))
    if spine:
        spine.inputs['Resolution'].default_value = 32
        start_comb = safe_node(tree, 'ShaderNodeCombineXYZ', (base_x-200, -200))
        link_sockets(tree, sx, start_comb.inputs['X'])
        link_sockets(tree, sy, start_comb.inputs['Y'])
        start_comb.inputs['Z'].default_value = 0
        link_sockets(tree, start_comb.outputs['Vector'], spine.inputs['Start'])

        sh_comb = safe_node(tree, 'ShaderNodeCombineXYZ', (base_x-200, -400))
        link_sockets(tree, _add(tree, sx, stx, (base_x+400, 600)), sh_comb.inputs['X'])
        link_sockets(tree, _add(tree, sy, sty, (base_x+400, 800)), sh_comb.inputs['Y'])
        sh_comb.inputs['Z'].default_value = 0
        link_sockets(tree, sh_comb.outputs['Vector'], spine.inputs['Start Handle'])

        eh_comb = safe_node(tree, 'ShaderNodeCombineXYZ', (base_x-200, -600))
        link_sockets(tree, _sub(tree, ex, etx, (base_x+400, 1000)), eh_comb.inputs['X'])
        link_sockets(tree, _sub(tree, ey, ety, (base_x+400, 1200)), eh_comb.inputs['Y'])
        eh_comb.inputs['Z'].default_value = 0
        link_sockets(tree, eh_comb.outputs['Vector'], spine.inputs['End Handle'])

        end_comb = safe_node(tree, 'ShaderNodeCombineXYZ', (base_x-200, -800))
        link_sockets(tree, ex, end_comb.inputs['X'])
        link_sockets(tree, ey, end_comb.inputs['Y'])
        end_comb.inputs['Z'].default_value = 0
        link_sockets(tree, end_comb.outputs['Vector'], spine.inputs['End'])
        color_node(spine, "wall")

    # Rectangular profile
    rect_prof = safe_node(tree, 'GeometryNodeCurvePrimitiveQuadrilateral', (base_x - 300, -200))
    if rect_prof:
        rect_prof.mode = 'RECTANGLE'
        link_sockets(tree, thickness, rect_prof.inputs['Width'])
        link_sockets(tree, h, rect_prof.inputs['Height'])

    parts = []
    if spine and rect_prof:
        wall_sweep = safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 300, 0))
        if wall_sweep:
            link_sockets(tree, spine.outputs['Curve'], wall_sweep.inputs['Curve'])
            link_sockets(tree, rect_prof.outputs['Curve'], wall_sweep.inputs['Profile Curve'])
            wall_sweep.inputs['Fill Caps'].default_value = True
            color_node(wall_sweep, "wall")
            parts.append(wall_sweep.outputs['Mesh'])

    # Crenellations
    if spine and crenels:
        resample = safe_node(tree, 'GeometryNodeResampleCurve', (base_x + 300, -400))
        if resample:
            try:
                resample.mode = 'COUNT'
            except Exception:
                pass
            count_val = _add(tree, _mul(tree, crenels, 2, (base_x+100, -600)), 1, (base_x+300, -600))
            link_sockets(tree, _float_to_int(tree, count_val, (base_x+400, -600)), resample.inputs['Count'])
            link_sockets(tree, spine.outputs['Curve'], resample.inputs['Curve'])
            color_node(resample, "ornament")

            crv_to_pts = safe_node(tree, 'GeometryNodeCurveToPoints', (base_x + 500, -400))
            if crv_to_pts:
                try:
                    crv_to_pts.mode = 'EVALUATED'
                except Exception:
                    pass
                link_sockets(tree, resample.outputs['Curve'], crv_to_pts.inputs['Curve'])
                color_node(crv_to_pts, "ornament")

                merlon = safe_node(tree, 'GeometryNodeMeshCube', (base_x - 200, -600))
                if merlon:
                    thick_mul = _mul(tree, thickness, 1.2, (base_x-400, -800))
                    h_mul = _mul(tree, h, 0.18, (base_x-400, -1000))
                    size_comb = safe_node(tree, 'ShaderNodeCombineXYZ', (base_x-400, -600))
                    link_sockets(tree, thick_mul, size_comb.inputs['X'])
                    link_sockets(tree, thick_mul, size_comb.inputs['Y'])
                    link_sockets(tree, h_mul, size_comb.inputs['Z'])
                    link_sockets(tree, size_comb.outputs['Vector'], merlon.inputs['Size'])
                    color_node(merlon, "ornament")

                    iop = safe_node(tree, 'GeometryNodeInstanceOnPoints', (base_x + 700, -400))
                    if iop:
                        link_sockets(tree, crv_to_pts.outputs['Points'], iop.inputs['Points'])
                        link_sockets(tree, merlon.outputs['Mesh'], iop.inputs['Instance'])
                        link_sockets(tree, crv_to_pts.outputs['Rotation'], iop.inputs['Rotation'])

                        tr_up = safe_node(tree, 'GeometryNodeTranslateInstances', (base_x + 900, -400))
                        if tr_up:
                            z_offset = _add(tree, _mul(tree, h, 0.5, (base_x+700, -600)), _mul(tree, h, 0.09, (base_x+700, -800)), (base_x+900, -600))
                            t_comb = safe_node(tree, 'ShaderNodeCombineXYZ', (base_x+700, -700))
                            t_comb.inputs['X'].default_value = 0
                            t_comb.inputs['Y'].default_value = 0
                            link_sockets(tree, z_offset, t_comb.inputs['Z'])
                            link_sockets(tree, t_comb.outputs['Vector'], tr_up.inputs['Translation'])
                            link_sockets(tree, iop.outputs['Instances'], tr_up.inputs['Instances'])
                            rea = safe_node(tree, 'GeometryNodeRealizeInstances', (base_x + 1100, -400))
                            if rea:
                                link_sockets(tree, tr_up.outputs['Instances'], rea.inputs['Geometry'])
                                parts.append(rea.outputs['Geometry'])

    if not parts:
        return None
    if len(parts) == 1:
        geom = parts[0]
    else:
        join = safe_node(tree, 'GeometryNodeJoinGeometry', (base_x + 1400, 0))
        if join:
            for p in parts:
                link_sockets(tree, p, join.inputs['Geometry'])
            color_node(join, "output")
            geom = join.outputs['Geometry']
        else:
            geom = parts[0]

    if geom is not None:
        link_sockets(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_curved_wall")
    return tree, gin, gout


register_builder(
    "MEL_curved_wall", build_curved_wall_group,
    "Curved Wall", "Core form builder (absorbed from monolith build_curved_wall).",
    category="structures")


def build_building_group(group_name="MEL_building"):
    """Port of build_building as a group builder."""
    tree, gin, gout = new_geometry_tree(group_name)
    # Tower params
    add_int_param(tree, "Complexity Level", 3, 1, 5)
    add_int_param(tree, "Recursion Depth", 3, 1, 6)
    add_float_param(tree, "Base Radius", 1.2, 0.1, 10.0)
    add_float_param(tree, "Height", 5.0, 0.5, 30.0)
    add_float_param(tree, "Taper Ratio", 0.6, 0.0, 1.0)
    add_float_param(tree, "Twist Angle", 0.0, -6.283, 6.283)
    add_float_param(tree, "Variation Intensity", 0.5, 0.0, 1.0)
    add_float_param(tree, "Symmetry Break", 0.3, 0.0, 1.0)
    add_int_param(tree, "Seed", 42, 0, 9999)
    # Building params
    add_int_param(tree, "Building Floors", 3, 1, 10)
    add_float_param(tree, "Building Floor Height", 2.5, 1.0, 8.0)
    add_bool_param(tree, "Building With Railings", True)
    add_bool_param(tree, "Building With Arches", True)
    add_bool_param(tree, "Building With Buttress", True)
    add_int_param(tree, "Building Arches Per Face", 2, 1, 8)
    add_bool_param(tree, "Building Align To Radius", True)
    # Railing params
    add_float_param(tree, "Rail Height", 1.0, 0.2, 5.0)
    add_float_param(tree, "Rail Length", 6.0, 1.0, 30.0)
    add_float_param(tree, "Rail Baluster Radius", 0.06, 0.01, 0.5)
    add_float_param(tree, "Rail Top Size", 0.1, 0.02, 0.5)
    add_int_param(tree, "Rail Baluster Count", 24, 4, 200)
    # Arch params
    add_float_param(tree, "Arch Radius", 1.5, 0.3, 10.0)
    add_float_param(tree, "Arch Sweep Deg", 180.0, 30.0, 360.0)
    add_float_param(tree, "Arch Thickness", 0.18, 0.02, 1.0)
    # Buttress params
    add_float_param(tree, "Buttress Span", 2.0, 0.5, 10.0)
    add_float_param(tree, "Buttress Height", 4.0, 0.5, 15.0)
    add_float_param(tree, "Buttress Arch Bow", 0.5, 0.0, 2.0)

    parts = []

    # 1. Tower body with overridden height = floors * floor_height
    total_h = _mul(tree, gin.outputs["Building Floors"], gin.outputs["Building Floor Height"], (-3700, 200))
    # taper_override = max(0.1, taper_ratio * 0.6)
    taper_override = _max(tree, _mul(tree, gin.outputs["Taper Ratio"], 0.6, (-3700, 400)), 0.1, (-3500, 400))

    # Build tower with overridden height/taper
    cyl = safe_node(tree, 'GeometryNodeMeshCylinder', (-3500, 0))
    color_node(cyl, "tower")
    complexity_mul = _mul(tree, gin.outputs["Complexity Level"], 8, (-3900, 200))
    verts_max = _max(tree, complexity_mul, 8, (-3700, 200))
    link_sockets(tree, _float_to_int(tree, verts_max, (-3600, 200)), cyl.inputs['Vertices'])
    recursion_mul = _mul(tree, gin.outputs["Recursion Depth"], 4, (-3900, 400))
    sides_max = _max(tree, recursion_mul, 2, (-3700, 400))
    link_sockets(tree, _float_to_int(tree, sides_max, (-3600, 400)), cyl.inputs['Side Segments'])
    cyl.inputs['Fill Segments'].default_value = 1
    link_sockets(tree, gin.outputs["Base Radius"], cyl.inputs['Radius'])
    link_sockets(tree, total_h, cyl.inputs['Depth'])

    tower_geom = cyl.outputs['Mesh']
    tower_geom = _add_taper_chain(tree, tower_geom, total_h, taper_override, x=-3200, y=-400)
    tower_geom = _add_twist(tree, tower_geom, gin.outputs["Twist Angle"], total_h, x=-1600, y=-400)
    var_mul = _mul(tree, gin.outputs["Variation Intensity"], 0.5, (-300, 600))
    sym_mul = _mul(tree, gin.outputs["Symmetry Break"], 0.3, (-300, 800))
    strength = _add(tree, var_mul, sym_mul, (-100, 700))
    scale_val = _add(tree, 1.5, _mul(tree, gin.outputs["Complexity Level"], 0.5, (-300, 1000)), (-100, 1000))
    tower_geom = _add_noise_displace(tree, tower_geom, scale_val, 3.0, strength, gin.outputs["Seed"], x=0, y=400)
    parts.append(tower_geom)

    # 2. Top railing
    # top_radius = base_radius * max(0.05, 1.0 - taper * 0.6)
    top_taper = _max(tree, _sub(tree, 1.0, taper_override, (4300, 200)), 0.05, (4500, 200))
    top_radius = _mul(tree, gin.outputs["Base Radius"], top_taper, (4700, 200))
    # rail_len = max(1.0, top_radius * 2 * 1.05)
    rail_len_raw = _mul(tree, _mul(tree, top_radius, 2, (4700, 400)), 1.05, (4900, 400))
    rail_len = _max(tree, rail_len_raw, 1.0, (5100, 400))

    rail_geom = _impl_build_railing(tree, gin, x_offset=4500, y_offset=0,
                                     length=rail_len, height=gin.outputs["Rail Height"])
    if rail_geom is not None:
        trans = safe_node(tree, 'GeometryNodeTransform', (5500, 1500))
        color_node(trans, "railing")
        t_comb = safe_node(tree, 'ShaderNodeCombineXYZ', (5300, 1700))
        t_comb.inputs['X'].default_value = 0
        t_comb.inputs['Y'].default_value = 0
        link_sockets(tree, _mul(tree, total_h, 0.5, (5300, 1900)), t_comb.inputs['Z'])
        link_sockets(tree, t_comb.outputs['Vector'], trans.inputs['Translation'])
        link_sockets(tree, rail_geom, trans.inputs['Geometry'])
        parts.append(trans.outputs['Geometry'])

    # 3. Side arches
    arch_geom = _impl_build_arch(tree, gin, base_x=4500)
    if arch_geom is not None:
        per_face = gin.outputs["Building Arches Per Face"]
        for floor in range(3):  # default floors
            floor_t = (floor + 0.5) / 3.0
            taper_factor = 1.0 - max(0.05, 0.6) * floor_t
            radius_at_floor = 1.2 * taper_factor * 1.05
            z = -2.5 + 2.5 * (floor + 0.5)
            for face in range(4):
                face_angle = math.radians(face * 90)
                for slot in range(2):
                    slot_t = (slot + 0.5) / 2 - 0.5
                    cx = math.cos(face_angle) * radius_at_floor + math.sin(face_angle) * slot_t * radius_at_floor * 1.4
                    cy = math.sin(face_angle) * radius_at_floor - math.cos(face_angle) * slot_t * radius_at_floor * 1.4
                    trans = safe_node(tree, 'GeometryNodeTransform', (8000, 800 + (floor*4 + face)*120))
                    color_node(trans, "arch")
                    t_comb = safe_node(tree, 'ShaderNodeCombineXYZ', (7800, 1000 + (floor*4 + face)*120))
                    t_comb.inputs['X'].default_value = cx
                    t_comb.inputs['Y'].default_value = cy
                    t_comb.inputs['Z'].default_value = z
                    link_sockets(tree, t_comb.outputs['Vector'], trans.inputs['Translation'])
                    r_comb = safe_node(tree, 'ShaderNodeCombineXYZ', (7800, 1200 + (floor*4 + face)*120))
                    r_comb.inputs['X'].default_value = 0
                    r_comb.inputs['Y'].default_value = 0
                    r_comb.inputs['Z'].default_value = face_angle
                    link_sockets(tree, r_comb.outputs['Vector'], trans.inputs['Rotation'])
                    link_sockets(tree, arch_geom, trans.inputs['Geometry'])
                    parts.append(trans.outputs['Geometry'])

    # 4. Flying buttress
    but_geom = _impl_build_buttress(tree, gin, base_x=8500)
    if but_geom is not None:
        trans_b = safe_node(tree, 'GeometryNodeTransform', (12000, -1000))
        color_node(trans_b, "buttress")
        t_comb = safe_node(tree, 'ShaderNodeCombineXYZ', (11800, -800))
        t_comb.inputs['X'].default_value = -1.2 - 2.0
        t_comb.inputs['Y'].default_value = 0
        link_sockets(tree, _mul(tree, total_h, -0.5, (11800, -600)), t_comb.inputs['Z'])
        link_sockets(tree, t_comb.outputs['Vector'], trans_b.inputs['Translation'])
        link_sockets(tree, but_geom, trans_b.inputs['Geometry'])
        parts.append(trans_b.outputs['Geometry'])

    # Join everything
    if len(parts) == 1:
        geom = parts[0]
    else:
        join = safe_node(tree, 'GeometryNodeJoinGeometry', (13000, 0))
        color_node(join, "output")
        for p in parts:
            link_sockets(tree, p, join.inputs['Geometry'])
        geom = join.outputs['Geometry']

    if geom is not None:
        link_sockets(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_building")
    return tree, gin, gout


register_builder(
    "MEL_building", build_building_group,
    "Building", "Core form builder (absorbed from monolith build_building).",
    category="structures")
