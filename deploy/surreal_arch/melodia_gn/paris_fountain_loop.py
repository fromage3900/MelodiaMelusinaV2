"""Parisian courtyard fountain - the self-feeding basin loop.

GN_PARIS_FountainLoop (build_paris_fountain_loop)

The Maison Impossible courtyard needs a fountain, and the fountain carries the
Escher device: a water channel that leaves the basin, climbs, and arrives back
at its own spout.  Nothing pumps it.  The impossibility is `Loop Error` - the
vertical distance by which the channel's mouth misses the spout it feeds:

    0.0   the mouth meets the spout exactly - a working recirculating fountain
    +     the channel arrives ABOVE its own mouth (it would spill past it)
    -     the channel arrives BELOW it (the Piranesi read: it never gets there)

`Feed Rise` is the channel's own height above the water surface, so the two
dials are independent: how tall the impossible arch stands, and whether its
mouth meets the source.  The spout itself stays where the building says it is
(sitting over the top bowl) - the channel is what moves.  Both dials are pure
math on existing sockets, the same trick as GN_PARIS_EscherLadder's Join Error.

NOT a reimplementation of MEL_public_fountain (civic): that builder makes a
generic plaza fountain - basin, tiered cups, finial - with no circulation logic
and no water.  This is the curated courtyard piece with the self-feeding loop
as a socket-level dial, a full Parisian dress (flutes, scallop bosses, bead
rim, Guimard-channel), and live water (rippled disc, falling streams, sparkle
droplets).  Different device, different defect.

Infinity-Nikki lens: every ornament is a dial - Shell Count, Rim Beads,
Flutes, Crown Spikes, Droplets - so one builder is a maid's courtyard basin or
a palace centerpiece without a rebuild.

Follows the paris_* family convention: package-relative core imports,
register_builder() at import time, every parameter an editable named input.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param,
)

TAU = math.pi * 2.0


# ------------------------------------------------------------------ shorthand

def N(t, bl, x=0, y=0):
    return safe_node(t, bl, (x, y))


def L(t, a, sa, b, sb):
    """Link node output `sa` to node input `sb` (name or index, house style)."""
    link_sockets(t, a.outputs[sa], b.inputs[sb])


def mathn(t, op, x, y, a=None, b=None):
    n = N(t, 'ShaderNodeMath', x, y)
    try:
        n.operation = op
    except Exception:
        pass
    for idx, val in ((0, a), (1, b)):
        if val is None:
            continue
        if isinstance(val, (int, float)):
            n.inputs[idx].default_value = val
        else:
            link_sockets(t, val, n.inputs[idx])
    return n


def booln(t, op, x, y, a=None):
    n = N(t, 'FunctionNodeBooleanMath', x, y)
    try:
        n.operation = op
    except Exception:
        pass
    if a is not None:
        if isinstance(a, bool):
            n.inputs[0].default_value = a
        else:
            link_sockets(t, a, n.inputs[0])
    return n


def combine(t, x, y, a=None, b=None, c=None):
    n = N(t, 'ShaderNodeCombineXYZ', x, y)
    for comp, val in (('X', a), ('Y', b), ('Z', c)):
        if val is None:
            continue
        if isinstance(val, (int, float)):
            n.inputs[comp].default_value = val
        else:
            link_sockets(t, val, n.inputs[comp])
    return n


def xform(t, x, y, src, sname='Mesh', trans=None, rot=None, scale=None):
    """Transform node. trans/rot/scale: number-tuple or SOCKET."""
    n = N(t, 'GeometryNodeTransform', x, y)
    link_sockets(t, src.outputs[sname], n.inputs['Geometry'])
    for key, val in (('Translation', trans), ('Rotation', rot), ('Scale', scale)):
        if val is None:
            continue
        if isinstance(val, (tuple, list)):
            n.inputs[key].default_value = tuple(val)
        else:
            link_sockets(t, val, n.inputs[key])
    return n


def cyl(t, x, y, radius, depth, verts=24):
    """Mesh cylinder; radius/depth may be numbers or SOCKETS."""
    n = N(t, 'GeometryNodeMeshCylinder', x, y)
    for key, val in (('Radius', radius), ('Depth', depth)):
        if isinstance(val, (int, float)):
            n.inputs[key].default_value = float(val)
        else:
            link_sockets(t, val, n.inputs[key])
    n.inputs['Vertices'].default_value = verts
    return n


def cone(t, x, y, r_bottom, r_top, depth, verts=24):
    """Mesh cone, centred on origin (translate +depth/2 to sit its base at z=0).
    Socket names verified against aesthetic_fx.py usage in this addon."""
    n = N(t, 'GeometryNodeMeshCone', x, y)
    for key, val in (('Radius Bottom', r_bottom), ('Radius Top', r_top),
                     ('Depth', depth)):
        if isinstance(val, (int, float)):
            n.inputs[key].default_value = float(val)
        else:
            link_sockets(t, val, n.inputs[key])
    n.inputs['Vertices'].default_value = verts
    return n


def sphere(t, x, y, radius):
    n = N(t, 'GeometryNodeMeshUVSphere', x, y)
    if isinstance(radius, (int, float)):
        n.inputs['Radius'].default_value = float(radius)
    else:
        link_sockets(t, radius, n.inputs['Radius'])
    n.inputs['Segments'].default_value = 12
    n.inputs['Rings'].default_value = 8
    return n


def ring_points(t, x, y, count, radius, zpos):
    """Points evenly around a circle, count from a SOCKET.

    MeshLine (zero offset) gives `count` points at the origin; a SetPosition
    OFFSET then places point `i` at angle i * (TAU/count) on the circle:
    (cos*r, sin*r, z).  count / radius / z may each be number or socket.
    Returns (set_position_node, angle_socket) - shells reuse the angle chain
    for per-instance orientation.
    """
    line = N(t, 'GeometryNodeMeshLine', x, y)
    try:
        line.mode = 'OFFSET'
    except Exception:
        pass
    if isinstance(count, (int, float)):
        line.inputs['Count'].default_value = int(count)
    else:
        link_sockets(t, count, line.inputs['Count'])
    line.inputs['Offset'].default_value = (0.0, 0.0, 0.0)

    idx = N(t, 'GeometryNodeInputIndex', x, y + 140)
    step = mathn(t, 'DIVIDE', x + 200, y + 140, TAU, count)
    ang = mathn(t, 'MULTIPLY', x + 340, y + 140, idx.outputs['Index'],
                step.outputs[0])
    cosn = mathn(t, 'COSINE', x + 480, y + 200, ang.outputs[0])
    sinn = mathn(t, 'SINE', x + 480, y + 60, ang.outputs[0])
    rx = mathn(t, 'MULTIPLY', x + 620, y + 200, cosn.outputs[0], radius)
    ry = mathn(t, 'MULTIPLY', x + 620, y + 60, sinn.outputs[0], radius)
    off = combine(t, x + 760, y + 140, rx.outputs[0], ry.outputs[0], zpos)
    sp = N(t, 'GeometryNodeSetPosition', x + 900, y + 140)
    L(t, line, 'Mesh', sp, 'Geometry')
    L(t, off, 'Vector', sp, 'Offset')
    return sp, ang.outputs[0]


def inst_realize(t, x, y, points, template, sname='Mesh', rot=None, scale=None):
    """Instance `template` on points and realize. rot/scale: number-tuple,
    socket, or None."""
    inst = N(t, 'GeometryNodeInstanceOnPoints', x, y)
    L(t, points, 'Geometry', inst, 'Points')
    L(t, template, sname, inst, 'Instance')
    for key, val in (('Rotation', rot), ('Scale', scale)):
        if val is None:
            continue
        if isinstance(val, (tuple, list)):
            inst.inputs[key].default_value = tuple(val)
        else:
            link_sockets(t, val, inst.inputs[key])
    real = N(t, 'GeometryNodeRealizeInstances', x + 180, y)
    L(t, inst, 'Instances', real, 'Geometry')
    return real


def not_less(t, x, y, const_k, socket):
    """True when the socket is <= const_k (slot const_k is OUT of range).
    LESS_THAN + NOT - both proven ops in this house."""
    lt = mathn(t, 'LESS_THAN', x, y, const_k, socket)
    return booln(t, 'NOT', x + 140, y, lt.outputs[0])


def vmath(t, op, x, y, a=None, b=None):
    n = N(t, 'ShaderNodeVectorMath', x, y)
    try:
        n.operation = op
    except Exception:
        pass
    for idx, val in ((0, a), (1, b)):
        if val is None:
            continue
        if isinstance(val, (tuple, list)):
            n.inputs[idx].default_value = tuple(val)
        else:
            link_sockets(t, val, n.inputs[idx])
    return n


# ------------------------------------------------------------------- builder

def build_paris_fountain_loop(group_name="GN_PARIS_FountainLoop"):
    """Courtyard fountain: stone basin, tiered bowls, ornament, water, and the
    self-feeding return channel with Loop Error as the impossibility dial."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    # ---- dials -----------------------------------------------------------
    add_float_param(tree, "Basin Radius", 1.6, 0.8, 3.0)
    add_float_param(tree, "Basin Height", 0.72, 0.30, 1.5)
    add_int_param(tree, "Flutes", 24, 0, 64)
    add_int_param(tree, "Shell Count", 4, 0, 12)
    add_float_param(tree, "Shell Size", 0.34, 0.12, 0.8)
    add_int_param(tree, "Rim Beads", 120, 0, 240)
    add_float_param(tree, "Bead Size", 0.022, 0.006, 0.06)
    add_int_param(tree, "Tiers", 2, 1, 4)
    add_float_param(tree, "Tier Rise", 0.46, 0.20, 1.2)
    add_float_param(tree, "Tier Shrink", 0.62, 0.35, 0.8)
    add_int_param(tree, "Crown Spikes", 8, 0, 24)
    add_float_param(tree, "Crown Size", 0.16, 0.05, 0.5)
    add_float_param(tree, "Water Level", 0.80, 0.40, 0.98)
    add_float_param(tree, "Ripple Amp", 0.025, 0.0, 0.15)
    add_float_param(tree, "Ripple Count", 6.0, 1.0, 16.0)
    add_int_param(tree, "Streams", 6, 0, 16)
    add_float_param(tree, "Stream Radius", 0.022, 0.008, 0.08)
    add_int_param(tree, "Droplets", 24, 0, 96)
    add_float_param(tree, "Droplet Size", 0.020, 0.006, 0.05)
    add_bool_param(tree, "Self Feed", True)
    add_float_param(tree, "Feed Rise", 1.35, 0.20, 2.5)
    add_float_param(tree, "Loop Error", 0.0, -0.50, 0.50)
    add_float_param(tree, "Channel Radius", 0.055, 0.020, 0.15)

    R = gin.outputs['Basin Radius']
    BH = gin.outputs['Basin Height']

    # ---- stone basin -----------------------------------------------------
    plinth = cyl(tree, bx - 2600, by + 2200, 1.0, 0.14, 48)
    plinth_r = mathn(tree, 'ADD', bx - 2500, by + 2200, R, 0.18)
    L(tree, plinth_r, 0, plinth, 'Radius')
    plinth_z = xform(tree, bx - 2300, by + 2200, plinth, trans=(0.0, 0.0, 0.07))

    drum = cyl(tree, bx - 2600, by + 1900, R, BH, 48)
    drum_half = mathn(tree, 'MULTIPLY', bx - 2500, by + 1900, BH, 0.5)
    drum_tr = combine(tree, bx - 2400, by + 1900, 0.0, 0.0, drum_half.outputs[0])
    drum_z = xform(tree, bx - 2300, by + 1900, drum,
                   trans=drum_tr.outputs['Vector'])

    lip = cyl(tree, bx - 2600, by + 1600, 1.0, 0.10, 48)
    lip_r = mathn(tree, 'ADD', bx - 2500, by + 1600, R, 0.055)
    L(tree, lip_r, 0, lip, 'Radius')
    lip_tr = combine(tree, bx - 2400, by + 1600, 0.0, 0.0, BH)
    lip_z = xform(tree, bx - 2300, by + 1600, lip, trans=lip_tr.outputs['Vector'])

    # ---- flutes: vertical reeds around the drum --------------------------
    fl_r = mathn(tree, 'ADD', bx - 2500, by + 1300, R, 0.012)
    fl_z = mathn(tree, 'MULTIPLY', bx - 2500, by + 1150, BH, 0.45)
    fl_pts, _ = ring_points(tree, bx - 2600, by + 1000,
                            gin.outputs['Flutes'], fl_r.outputs[0],
                            fl_z.outputs[0])
    fl_h = mathn(tree, 'MULTIPLY', bx - 2500, by + 850, BH, 0.62)
    fl_tpl = cyl(tree, bx - 2600, by + 700, 0.016, fl_h.outputs[0], 6)
    fl_real = inst_realize(tree, bx - 2200, by + 1000, fl_pts, fl_tpl)

    # ---- scallop bosses around the drum ----------------------------------
    sh_r = mathn(tree, 'ADD', bx - 2500, by + 400, R, 0.02)
    sh_z = mathn(tree, 'MULTIPLY', bx - 2500, by + 250, BH, 0.62)
    sh_pts, sh_ang = ring_points(tree, bx - 2600, by + 100,
                                 gin.outputs['Shell Count'],
                                 sh_r.outputs[0], sh_z.outputs[0])
    # template: squashed dome + three fan fins, authored facing +Y
    dome = sphere(tree, bx - 2600, by - 500, 1.0)
    dome_s = xform(tree, bx - 2300, by - 500, dome, scale=(0.55, 0.30, 0.42))
    sh_tpl_join = N(tree, 'GeometryNodeJoinGeometry', bx - 1800, by - 500)
    L(tree, dome_s, 'Geometry', sh_tpl_join, 'Geometry')
    for si, (dx, tilt) in enumerate(((-0.24, 0.42), (0.0, 0.0), (0.24, -0.42))):
        fin = N(tree, 'GeometryNodeMeshCube', bx - 2600, by - 800 - si * 220)
        fin.inputs['Size'].default_value = (0.09, 0.16, 0.52)
        fin_x = xform(tree, bx - 2300, by - 800 - si * 220, fin,
                      trans=(dx, 0.0, 0.0), rot=(0.0, tilt, 0.0))
        L(tree, fin_x, 'Geometry', sh_tpl_join, 'Geometry')
    sh_sz = combine(tree, bx - 1900, by - 900,
                    gin.outputs['Shell Size'], gin.outputs['Shell Size'],
                    gin.outputs['Shell Size'])
    sh_tpl = xform(tree, bx - 1600, by - 500, sh_tpl_join, sname='Geometry',
                   scale=sh_sz.outputs['Vector'])
    # orient each boss outward: rotation Z = ring angle - 90deg
    sh_rot_ang = mathn(tree, 'SUBTRACT', bx - 2200, by + 100,
                       sh_ang, TAU * 0.25)
    sh_rot = combine(tree, bx - 2000, by + 100, 0.0, 0.0, sh_rot_ang.outputs[0])
    sh_real = inst_realize(tree, bx - 1400, by + 100, sh_pts, sh_tpl,
                           sname='Geometry', rot=sh_rot.outputs['Vector'])

    # ---- rim beads -------------------------------------------------------
    bd_r = mathn(tree, 'ADD', bx - 2500, by - 1400, R, 0.055)
    bd_z0 = mathn(tree, 'ADD', bx - 2500, by - 1550, BH, 0.05)
    bd_z = mathn(tree, 'ADD', bx - 2500, by - 1700, bd_z0.outputs[0],
                 gin.outputs['Bead Size'])
    bd_pts, _ = ring_points(tree, bx - 2600, by - 1850,
                            gin.outputs['Rim Beads'], bd_r.outputs[0],
                            bd_z.outputs[0])
    bd_tpl = sphere(tree, bx - 2600, by - 2050, gin.outputs['Bead Size'])
    bd_real = inst_realize(tree, bx - 2200, by - 1850, bd_pts, bd_tpl)

    # ---- water: rippled disc ---------------------------------------------
    # The drum is solid, so the water surface sits in the basin MOUTH: the
    # lip ring rises 0.10 above the drum top, and Water Level is the fraction
    # of that lip height the water fills (0.8 = just under the lip).
    wt = cyl(tree, bx - 2600, by - 2400, 1.0, 0.03, 64)
    wt_r = mathn(tree, 'SUBTRACT', bx - 2500, by - 2400, R, 0.07)
    L(tree, wt_r, 0, wt, 'Radius')
    wt_lift = mathn(tree, 'MULTIPLY', bx - 2500, by - 2550,
                    gin.outputs['Water Level'], 0.085)
    wt_z = mathn(tree, 'ADD', bx - 2500, by - 2700, BH, wt_lift.outputs[0])
    wt_tr = combine(tree, bx - 2400, by - 2550, 0.0, 0.0, wt_z.outputs[0])
    wt_x = xform(tree, bx - 2300, by - 2400, wt, trans=wt_tr.outputs['Vector'])
    # ripple: z += sin(len(xy) * Ripple Count) * Ripple Amp
    pos = N(tree, 'GeometryNodeInputPosition', bx - 2600, by - 2900)
    xy = vmath(tree, 'MULTIPLY', bx - 2400, by - 2900, pos.outputs['Position'],
               (1.0, 1.0, 0.0))
    ln = vmath(tree, 'LENGTH', bx - 2200, by - 2900, xy.outputs['Vector'])
    freq = mathn(tree, 'MULTIPLY', bx - 2000, by - 2900, ln.outputs['Value'],
                 gin.outputs['Ripple Count'])
    wave = mathn(tree, 'SINE', bx - 1800, by - 2900, freq.outputs[0])
    amp = mathn(tree, 'MULTIPLY', bx - 1600, by - 2900, wave.outputs[0],
                gin.outputs['Ripple Amp'])
    rip_off = combine(tree, bx - 1400, by - 2900, 0.0, 0.0, amp.outputs[0])
    rip_sp = N(tree, 'GeometryNodeSetPosition', bx - 1200, by - 2400)
    L(tree, wt_x, 'Geometry', rip_sp, 'Geometry')
    L(tree, rip_off, 'Vector', rip_sp, 'Offset')

    # ---- tiers: four slots, Tiers picks how many exist -------------------
    tier_geoms = []
    for k in range(4):
        kx = bx - 2600 + k * 950
        ky = by + 3400
        rk = mathn(tree, 'MULTIPLY', kx, ky + 300, R,
                   mathn(tree, 'POWER', kx - 150, ky + 300,
                         gin.outputs['Tier Shrink'], float(k + 1)).outputs[0])
        zk = mathn(tree, 'ADD', kx, ky + 150, BH,
                   mathn(tree, 'MULTIPLY', kx - 150, ky + 0,
                         gin.outputs['Tier Rise'], float(k + 1)).outputs[0])
        zprev = mathn(tree, 'ADD', kx, ky - 150, BH,
                      mathn(tree, 'MULTIPLY', kx - 150, ky - 300,
                            gin.outputs['Tier Rise'], float(k)).outputs[0])
        # bowl: truncated cone, base at zk, flaring upward
        r_bot = mathn(tree, 'MULTIPLY', kx, ky + 450, rk.outputs[0], 0.34)
        bowl = cone(tree, kx, ky + 600, r_bot.outputs[0], rk.outputs[0], 0.20, 32)
        bowl_cz = mathn(tree, 'ADD', kx, ky + 450, zk.outputs[0], 0.10)
        bowl_tr = combine(tree, kx, ky + 750, 0.0, 0.0, bowl_cz.outputs[0])
        bowl_x = xform(tree, kx + 200, ky + 600, bowl,
                       trans=bowl_tr.outputs['Vector'])
        # water disc inside the bowl
        disc_r = mathn(tree, 'MULTIPLY', kx, ky + 900, rk.outputs[0], 0.78)
        disc = cyl(tree, kx, ky + 1050, disc_r.outputs[0], 0.02)
        disc_cz = mathn(tree, 'ADD', kx, ky + 900, zk.outputs[0], 0.16)
        disc_tr = combine(tree, kx, ky + 1200, 0.0, 0.0, disc_cz.outputs[0])
        disc_x = xform(tree, kx + 200, ky + 1050, disc,
                       trans=disc_tr.outputs['Vector'])
        # stem from the previous level up to this bowl
        st_h = mathn(tree, 'SUBTRACT', kx, ky + 1350, zk.outputs[0],
                     zprev.outputs[0])
        st_r = mathn(tree, 'MULTIPLY', kx, ky + 1500, rk.outputs[0], 0.12)
        st_max = mathn(tree, 'MAXIMUM', kx, ky + 1650, st_r.outputs[0], 0.035)
        stem = cyl(tree, kx, ky + 1800, st_max.outputs[0], st_h.outputs[0])
        st_sum = mathn(tree, 'ADD', kx, ky + 1350, zk.outputs[0],
                       zprev.outputs[0])
        st_cz = mathn(tree, 'MULTIPLY', kx, ky + 1950, st_sum.outputs[0], 0.5)
        st_tr = combine(tree, kx, ky + 2100, 0.0, 0.0, st_cz.outputs[0])
        stem_x = xform(tree, kx + 200, ky + 1800, stem,
                       trans=st_tr.outputs['Vector'])
        # falling streams: from this bowl's rim down to the level below
        sr_r = mathn(tree, 'MULTIPLY', kx, ky + 2250, rk.outputs[0], 0.86)
        sr_sum = mathn(tree, 'ADD', kx, ky + 2250, zk.outputs[0],
                       zprev.outputs[0])
        sr_cz = mathn(tree, 'MULTIPLY', kx, ky + 2400, sr_sum.outputs[0], 0.5)
        sr_pts, _ = ring_points(tree, kx, ky + 2550, gin.outputs['Streams'],
                                sr_r.outputs[0], sr_cz.outputs[0])
        sr_h = mathn(tree, 'ADD', kx, ky + 2250, st_h.outputs[0], 0.10)
        sr_tpl = cyl(tree, kx, ky + 2700, gin.outputs['Stream Radius'],
                     sr_h.outputs[0], 8)
        sr_real = inst_realize(tree, kx + 200, ky + 2550, sr_pts, sr_tpl)

        slot_join = N(tree, 'GeometryNodeJoinGeometry', kx + 500, ky + 900)
        for node in (bowl_x, disc_x, stem_x, sr_real):
            L(tree, node, 'Geometry', slot_join, 'Geometry')
        # slots beyond Tiers vanish entirely (DeleteGeometry, no stub)
        sel_off = not_less(tree, kx + 500, ky + 560, float(k),
                           gin.outputs['Tiers'])
        slot_del = N(tree, 'GeometryNodeDeleteGeometry', kx + 700, ky + 900)
        L(tree, slot_join, 'Geometry', slot_del, 'Geometry')
        L(tree, sel_off, 0, slot_del, 'Selection')
        tier_geoms.append(slot_del)

    # ---- crown on the top of the stack -----------------------------------
    z_top = mathn(tree, 'ADD', bx - 2600, by + 4900, BH,
                  mathn(tree, 'MULTIPLY', bx - 2750, by + 4900,
                        gin.outputs['Tier Rise'],
                        gin.outputs['Tiers']).outputs[0])
    col_r = mathn(tree, 'MULTIPLY', bx - 2600, by + 5050,
                  gin.outputs['Crown Size'], 0.70)
    collar = cyl(tree, bx - 2600, by + 5200, col_r.outputs[0], 0.04)
    col_cz = mathn(tree, 'ADD', bx - 2600, by + 5050, z_top.outputs[0], 0.14)
    col_tr = combine(tree, bx - 2400, by + 5050, 0.0, 0.0, col_cz.outputs[0])
    collar_x = xform(tree, bx - 2300, by + 5200, collar,
                     trans=col_tr.outputs['Vector'])
    fin_r = mathn(tree, 'MULTIPLY', bx - 2600, by + 5350,
                  gin.outputs['Crown Size'], 0.55)
    finial = sphere(tree, bx - 2600, by + 5500, fin_r.outputs[0])
    fin_cz = mathn(tree, 'ADD', bx - 2600, by + 5350, z_top.outputs[0], 0.30)
    fin_tr = combine(tree, bx - 2400, by + 5350, 0.0, 0.0, fin_cz.outputs[0])
    finial_x = xform(tree, bx - 2300, by + 5500, finial,
                     trans=fin_tr.outputs['Vector'])
    spk_r = mathn(tree, 'MULTIPLY', bx - 2600, by + 5650,
                  gin.outputs['Crown Size'], 1.05)
    spk_z = mathn(tree, 'ADD', bx - 2600, by + 5800, z_top.outputs[0], 0.22)
    spk_pts, _ = ring_points(tree, bx - 2600, by + 5950,
                             gin.outputs['Crown Spikes'], spk_r.outputs[0],
                             spk_z.outputs[0])
    spk_rr = mathn(tree, 'MULTIPLY', bx - 2600, by + 6100,
                   gin.outputs['Crown Size'], 0.10)
    spk_h = mathn(tree, 'MULTIPLY', bx - 2600, by + 6250,
                  gin.outputs['Crown Size'], 0.60)
    spk_tpl = cone(tree, bx - 2600, by + 6400, spk_rr.outputs[0], 0.0,
                   spk_h.outputs[0], 8)
    spk_real = inst_realize(tree, bx - 2200, by + 5950, spk_pts, spk_tpl)

    # ---- sparkle droplets hanging over the basin water -------------------
    # base = basin top + a little of the first tier rise (above the water)
    dr_r = mathn(tree, 'MULTIPLY', bx, by + 6100, R,
                 mathn(tree, 'MULTIPLY', bx - 200, by + 6250,
                       gin.outputs['Tier Shrink'], 0.86).outputs[0])
    dr_base = mathn(tree, 'ADD', bx, by + 6400, BH,
                    mathn(tree, 'MULTIPLY', bx - 200, by + 6700,
                          gin.outputs['Tier Rise'], 0.55).outputs[0])
    dr_pts, _ = ring_points(tree, bx, by + 6850,
                            gin.outputs['Droplets'], dr_r.outputs[0],
                            dr_base.outputs[0])
    # stagger every third droplet a little lower - a falling read
    idx2 = N(tree, 'GeometryNodeInputIndex', bx + 200, by + 7000)
    mod3 = mathn(tree, 'MODULO', bx + 400, by + 7000, idx2.outputs['Index'], 3.0)
    drop = mathn(tree, 'MULTIPLY', bx + 600, by + 7000, mod3.outputs[0], 0.075)
    drop_n = mathn(tree, 'MULTIPLY', bx + 800, by + 7000, drop.outputs[0], -1.0)
    dr_off = combine(tree, bx + 1000, by + 7000, 0.0, 0.0, drop_n.outputs[0])
    dr_sp = N(tree, 'GeometryNodeSetPosition', bx + 1200, by + 6850)
    L(tree, dr_pts, 'Geometry', dr_sp, 'Geometry')
    L(tree, dr_off, 'Vector', dr_sp, 'Offset')
    dr_tpl = sphere(tree, bx + 200, by + 7200, gin.outputs['Droplet Size'])
    dr_real = inst_realize(tree, bx + 600, by + 6850, dr_sp, dr_tpl)

    # ---- the self-feeding channel (the device) ---------------------------
    # Fixed by the building: the spout sits over the top bowl.
    z_spout = mathn(tree, 'ADD', bx + 3600, by + 5600, z_top.outputs[0], 0.30)
    z_water = mathn(tree, 'MULTIPLY', bx + 3600, by + 5450, BH,
                    gin.outputs['Water Level'])
    # The channel's own height: water + Feed Rise, then Loop Error shifts it.
    z_rise = mathn(tree, 'ADD', bx + 3600, by + 5750, z_water.outputs[0],
                   gin.outputs['Feed Rise'])
    z_rise2 = mathn(tree, 'ADD', bx + 3600, by + 5900, z_rise.outputs[0],
                    gin.outputs['Loop Error'])
    z_foot = mathn(tree, 'SUBTRACT', bx + 3600, by + 6050,
                   z_water.outputs[0], 0.06)
    xr = mathn(tree, 'MULTIPLY', bx + 3600, by + 6200, R, 0.70)
    xr2 = mathn(tree, 'ADD', bx + 3600, by + 6350, xr.outputs[0], 0.12)
    x_end = 0.22  # the spout's own x - fixed by the building

    riser_h = mathn(tree, 'SUBTRACT', bx + 3600, by + 6500,
                    z_rise2.outputs[0], z_foot.outputs[0])
    riser = cyl(tree, bx + 3600, by + 6650,
                gin.outputs['Channel Radius'], riser_h.outputs[0], 10)
    riser_sum = mathn(tree, 'ADD', bx + 3600, by + 6500,
                      z_rise2.outputs[0], z_foot.outputs[0])
    riser_cz = mathn(tree, 'MULTIPLY', bx + 3600, by + 6800,
                     riser_sum.outputs[0], 0.5)
    riser_tr = combine(tree, bx + 3800, by + 6800, xr2.outputs[0], 0.0,
                       riser_cz.outputs[0])
    riser_x = xform(tree, bx + 4000, by + 6650, riser,
                    trans=riser_tr.outputs['Vector'])

    arm_len = mathn(tree, 'SUBTRACT', bx + 3600, by + 6950,
                    xr2.outputs[0], x_end)
    arm = cyl(tree, bx + 3600, by + 7100, gin.outputs['Channel Radius'],
              arm_len.outputs[0], 10)
    arm_sum = mathn(tree, 'ADD', bx + 3600, by + 6950, xr2.outputs[0], x_end)
    arm_cx = mathn(tree, 'MULTIPLY', bx + 3600, by + 7250,
                   arm_sum.outputs[0], 0.5)
    arm_tr = combine(tree, bx + 3800, by + 7250, arm_cx.outputs[0], 0.0,
                     z_rise2.outputs[0])
    arm_x = xform(tree, bx + 4000, by + 7100, arm,
                  trans=arm_tr.outputs['Vector'],
                  rot=(0.0, math.pi * 0.5, 0.0))

    elb_r = mathn(tree, 'MULTIPLY', bx + 3600, by + 7400,
                  gin.outputs['Channel Radius'], 1.35)
    elbow = sphere(tree, bx + 3600, by + 7550, elb_r.outputs[0])
    elb_tr = combine(tree, bx + 3800, by + 7400, xr2.outputs[0], 0.0,
                     z_rise2.outputs[0])
    elbow_x = xform(tree, bx + 4000, by + 7550, elbow,
                    trans=elb_tr.outputs['Vector'])

    foot_r = mathn(tree, 'MULTIPLY', bx + 3600, by + 7700,
                   gin.outputs['Channel Radius'], 1.60)
    foot = sphere(tree, bx + 3600, by + 7850, foot_r.outputs[0])
    foot_tr = combine(tree, bx + 3800, by + 7700, xr2.outputs[0], 0.0,
                      z_foot.outputs[0])
    foot_x = xform(tree, bx + 4000, by + 7850, foot,
                   trans=foot_tr.outputs['Vector'])

    # spout cup: fixed to the building, mouth at z_spout over the top bowl
    sp_w = mathn(tree, 'MULTIPLY', bx + 3600, by + 8000,
                 gin.outputs['Channel Radius'], 1.00)
    sp_t = mathn(tree, 'MULTIPLY', bx + 3600, by + 8150,
                 gin.outputs['Channel Radius'], 0.36)
    spout = cone(tree, bx + 3600, by + 8300, sp_t.outputs[0], sp_w.outputs[0],
                 0.12, 12)
    sp_tr = combine(tree, bx + 3800, by + 8300, x_end, 0.0, z_spout.outputs[0])
    spout_x = xform(tree, bx + 4000, by + 8300, spout,
                    trans=sp_tr.outputs['Vector'])

    channel_join = N(tree, 'GeometryNodeJoinGeometry', bx + 4400, by + 7000)
    for node in (riser_x, arm_x, elbow_x, foot_x, spout_x):
        L(tree, node, 'Geometry', channel_join, 'Geometry')
    not_feed = booln(tree, 'NOT', bx + 4400, by + 6600,
                     gin.outputs['Self Feed'])
    channel_del = N(tree, 'GeometryNodeDeleteGeometry', bx + 4600, by + 7000)
    L(tree, channel_join, 'Geometry', channel_del, 'Geometry')
    L(tree, not_feed, 0, channel_del, 'Selection')

    # ---- join ------------------------------------------------------------
    j1 = N(tree, 'GeometryNodeJoinGeometry', bx + 5000, by + 4000)
    for node in (plinth_z, drum_z, lip_z, fl_real, sh_real, bd_real, rip_sp):
        L(tree, node, 'Geometry', j1, 'Geometry')
    for node in tier_geoms:
        L(tree, node, 'Geometry', j1, 'Geometry')
    for node in (collar_x, finial_x, spk_real, dr_real):
        L(tree, node, 'Geometry', j1, 'Geometry')
    j2 = N(tree, 'GeometryNodeJoinGeometry', bx + 5200, by + 3800)
    L(tree, j1, 'Geometry', j2, 'Geometry')
    L(tree, channel_del, 'Geometry', j2, 'Geometry')
    L(tree, j2, 'Geometry', gout, 'Geometry')

    return tree, gin, gout


# ------------------------------------------------- addon registration

try:
    from .core import register_builder  # noqa: E402
    register_builder(
        'GN_PARIS_FountainLoop', build_paris_fountain_loop,
        'PARIS Fountain Loop',
        'Courtyard fountain with the self-feeding water channel. Loop Error '
        'dials the impossibility; Feed Rise sets the arch height. Flutes, '
        'scallop bosses, bead rim, crown spikes, streams and droplets are '
        'all dials.',
        category='escher',
    )
    print('[paris_fountain_loop] registered GN_PARIS_FountainLoop')
except ImportError:
    print('[paris_fountain_loop] standalone mode (no core registry)')


if __name__ == '__main__':
    build_paris_fountain_loop()
