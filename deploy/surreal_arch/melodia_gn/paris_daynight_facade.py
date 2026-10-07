"""Parisian day-and-night facade - the light/dark duality, as a slider.

GN_PARIS_DayNightFacade (build_paris_daynight_facade)

Escher's *Day and Night* works because two readings share one cut: day birds and
night birds interlock along a seam, and neither can be pulled out without
damaging the other.  This builder puts that logic on a Haussmann bay wall:

  * `Night Mix` is the seam.  0.0 is the full-day read (every window dark,
    recessed, shuttered-open); 1.0 is full night (every window lit, panes
    pushed proud, brass trim).  In between, the light climbs DOWN from the top
    floor - one window at a time - which is what dusk actually looks like on a
    facade.
  * `Lit Pop` and `Window Recess` are the same pane at two depths: a lit window
    leans out toward the street, a dark window sits back in its reveal.
  * The roofline carries the actual Escher device: two interlocking flocks of
    birds (wings-up and wings-down), `Bird Lock` controlling how deep the two
    flocks mesh.

Everything else is the Parisian dress, every piece a dial: shutters that swing
through their full 180 degree arc (`Shutter Open`), iron balcony bands with a
bar-count dial, dentils under the cornice, geranium boxes under every sill
(`Bloom Count` on a seed), a portal with an oculus.

NOT a reimplementation of GN_PARIS_WallDetail: that builder details ONE wall
surface (bands, panels, wainscot, reveals) at bay scale.  This is the whole
facade body - grid, windows, lighting state, roofline - that the wall detail
pass then dresses.  Different device, different defect: no windows, no grid,
no lighting state in any other builder in the family.

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
HALF_PI = math.pi * 0.5


# ------------------------------------------------------------------ shorthand

def N(t, bl, x=0, y=0):
    return safe_node(t, bl, (x, y))


def L(t, a, sa, b, sb):
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


def cube_s(t, x, y, sx=None, sy=None, sz=None, base=(0.1, 0.1, 0.1)):
    """Cube whose Size components may be numbers or SOCKETS.  A vector input
    socket cannot be linked per-component, so socket components route through
    a CombineXYZ and the whole vector is linked to Size."""
    n = N(t, 'GeometryNodeMeshCube', x, y)
    vals = (sx, sy, sz)
    if any(v is not None and not isinstance(v, (int, float)) for v in vals):
        comb = N(t, 'ShaderNodeCombineXYZ', x - 220, y)
        for comp, bval, val in zip(('X', 'Y', 'Z'), base, vals):
            if val is None:
                comb.inputs[comp].default_value = float(bval)
            elif isinstance(val, (int, float)):
                comb.inputs[comp].default_value = float(val)
            else:
                link_sockets(t, val, comb.inputs[comp])
        link_sockets(t, comb.outputs['Vector'], n.inputs['Size'])
    else:
        n.inputs['Size'].default_value = base
        for i, val in enumerate(vals):
            if val is not None:
                n.inputs['Size'].default_value[i] = val
    return n


def cyl(t, x, y, radius, depth, verts=12):
    n = N(t, 'GeometryNodeMeshCylinder', x, y)
    for key, val in (('Radius', radius), ('Depth', depth)):
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
    n.inputs['Segments'].default_value = 10
    n.inputs['Rings'].default_value = 6
    return n


def out_name(node, *names):
    """First existing output socket name on `node` (bpy collections raise
    KeyError on `in`, so probe with .get())."""
    for nm in names:
        try:
            if node.outputs.get(nm) is not None:
                return nm
        except Exception:
            pass
    return names[0]


def inst_realize(t, x, y, points, template, sname='Mesh', rot=None, scale=None,
                 trans=None):
    inst = N(t, 'GeometryNodeInstanceOnPoints', x, y)
    L(t, points, out_name(points, 'Geometry', 'Mesh', 'Points'), inst, 'Points')
    L(t, template, sname, inst, 'Instance')
    for key, val in (('Rotation', rot), ('Scale', scale)):
        if val is None:
            continue
        if isinstance(val, (tuple, list)):
            inst.inputs[key].default_value = tuple(val)
        else:
            link_sockets(t, val, inst.inputs[key])
    out = inst
    if trans is not None:
        tr = N(t, 'GeometryNodeTranslateInstances', x + 140, y - 160)
        L(t, inst, 'Instances', tr, 'Instances')
        if isinstance(trans, (tuple, list)):
            tr.inputs['Translation'].default_value = tuple(trans)
        else:
            link_sockets(t, trans, tr.inputs['Translation'])
        out = tr
    real = N(t, 'GeometryNodeRealizeInstances', x + 300, y)
    L(t, out, 'Instances', real, 'Geometry')
    return real


def grid_points(t, x, y, count, offset, bays, bayw, floorh, base, whalf):
    """Window grid positions from a line index.

    Global index g = i + offset; col = g - floor(g/Bays)*Bays; row = floor(g/Bays).
    Position = ((col - (Bays-1)/2) * BayW, 0, row*FloorH + WindowBase + winH/2).
    count, offset, bays, bayw, floorh, base, whalf may be numbers or sockets.
    Returns the SetPosition node (points output via 'Geometry').
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

    idx = N(t, 'GeometryNodeInputIndex', x, y + 260)
    gi = mathn(t, 'ADD', x + 180, y + 260, idx.outputs['Index'], offset)
    colf = mathn(t, 'DIVIDE', x + 340, y + 340, gi.outputs[0], bays)
    fl = mathn(t, 'FLOOR', x + 500, y + 340, colf.outputs[0])
    col = mathn(t, 'SUBTRACT', x + 660, y + 260, gi.outputs[0],
                mathn(t, 'MULTIPLY', x + 500, y + 160, fl.outputs[0],
                      bays).outputs[0])
    half_b = mathn(t, 'SUBTRACT', x + 660, y + 420, bays, 1.0)
    half_b2 = mathn(t, 'MULTIPLY', x + 820, y + 420, half_b.outputs[0], 0.5)
    col_c = mathn(t, 'SUBTRACT', x + 820, y + 260, col.outputs[0],
                  half_b2.outputs[0])
    wx = mathn(t, 'MULTIPLY', x + 980, y + 260, col_c.outputs[0], bayw)
    rowz = mathn(t, 'MULTIPLY', x + 660, y + 100, fl.outputs[0], floorh)
    wz0 = mathn(t, 'ADD', x + 980, y + 100, rowz.outputs[0], base)
    wz = mathn(t, 'ADD', x + 1140, y + 100, wz0.outputs[0], whalf)
    off = combine(t, x + 1300, y + 160, wx.outputs[0], 0.0, wz.outputs[0])
    sp = N(t, 'GeometryNodeSetPosition', x + 1460, y + 160)
    L(t, line, 'Mesh', sp, 'Geometry')
    L(t, off, 'Vector', sp, 'Offset')
    return sp


def guard_off(t, x, y, toggle_socket, geom_node, sname='Geometry'):
    """Optional-geometry house pattern: DeleteGeometry on NOT <toggle>."""
    not_t = booln(t, 'NOT', x, y, toggle_socket)
    d = N(t, 'GeometryNodeDeleteGeometry', x + 160, y - 140)
    L(t, geom_node, sname, d, 'Geometry')
    L(t, not_t, 0, d, 'Selection')
    return d


# ------------------------------------------------------------------- builder

def build_paris_daynight_facade(group_name="GN_PARIS_DayNightFacade"):
    """Haussmann bay wall whose windows slide day -> night, with an
    interlocking bird frieze on the roofline."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    # ---- dials (Infinity-Nikki pass: everything is a dial) ----------------
    add_int_param(tree, "Bay Count", 5, 2, 9)
    add_int_param(tree, "Floor Count", 3, 1, 5)
    add_float_param(tree, "Bay Width", 2.30, 1.4, 3.2)
    add_float_param(tree, "Floor Height", 2.75, 2.0, 3.8)
    add_float_param(tree, "Wall Depth", 0.45, 0.25, 1.0)
    add_float_param(tree, "Plinth Height", 0.45, 0.15, 1.0)
    add_float_param(tree, "Window Width", 0.52, 0.30, 0.85)
    add_float_param(tree, "Window Height", 0.60, 0.35, 0.85)
    add_float_param(tree, "Window Base", 0.85, 0.30, 1.40)
    add_float_param(tree, "Window Recess", 0.05, 0.01, 0.15)
    add_bool_param(tree, "Muntins", True)
    add_int_param(tree, "Muntin Bars", 2, 0, 4)
    add_float_param(tree, "Night Mix", 0.0, 0.0, 1.0)
    add_float_param(tree, "Lit Pop", 0.14, 0.03, 0.30)
    add_bool_param(tree, "Brass Trim", True)
    add_bool_param(tree, "Shutters", True)
    add_float_param(tree, "Shutter Open", 0.0, 0.0, 1.0)
    add_bool_param(tree, "Balconies", True)
    add_int_param(tree, "Balcony Bars", 12, 0, 32)
    add_float_param(tree, "Rail Height", 0.95, 0.60, 1.4)
    add_int_param(tree, "Dentils", 28, 0, 48)
    add_float_param(tree, "Dentil Size", 0.14, 0.05, 0.28)
    add_bool_param(tree, "Flower Boxes", True)
    add_int_param(tree, "Bloom Count", 10, 0, 24)
    add_float_param(tree, "Bloom Size", 0.075, 0.03, 0.2)
    add_float_param(tree, "Portal Width", 1.15, 0.5, 2.4)
    add_bool_param(tree, "Oculus", True)
    add_int_param(tree, "Birds", 14, 0, 24)
    add_float_param(tree, "Bird Size", 0.55, 0.15, 1.2)
    add_float_param(tree, "Bird Lock", 0.50, 0.0, 1.0)
    add_int_param(tree, "Seed", 7, 0, 99)

    BAYS = gin.outputs['Bay Count']
    FLOORS = gin.outputs['Floor Count']
    BW = gin.outputs['Bay Width']
    FH = gin.outputs['Floor Height']
    WD = gin.outputs['Wall Depth']
    PM = gin.outputs['Plinth Height']
    WR = gin.outputs['Window Width']
    WH = gin.outputs['Window Height']
    WB = gin.outputs['Window Base']
    RC = gin.outputs['Window Recess']
    NM = gin.outputs['Night Mix']
    LP = gin.outputs['Lit Pop']
    SO = gin.outputs['Shutter Open']

    # shared derived values
    W = mathn(tree, 'MULTIPLY', bx - 3600, by + 5000, BAYS, BW)       # facade width
    H = mathn(tree, 'MULTIPLY', bx - 3600, by + 4850, FLOORS, FH)     # facade height
    HALF_W = mathn(tree, 'MULTIPLY', bx - 3600, by + 4700, W.outputs[0], 0.5)
    HALF_D = mathn(tree, 'MULTIPLY', bx - 3600, by + 4550, WD, 0.5)
    winW = mathn(tree, 'MULTIPLY', bx - 3600, by + 4400, BW, WR)
    winH = mathn(tree, 'MULTIPLY', bx - 3600, by + 4250, FH, WH)
    winH_h = mathn(tree, 'MULTIPLY', bx - 3600, by + 4100, winH.outputs[0], 0.5)
    winW_h = mathn(tree, 'MULTIPLY', bx - 3600, by + 3950, winW.outputs[0], 0.5)
    total = mathn(tree, 'MULTIPLY', bx - 3600, by + 3800, BAYS, FLOORS)
    litN0 = mathn(tree, 'MULTIPLY', bx - 3600, by + 3650, NM, total.outputs[0])
    litN = mathn(tree, 'ROUND', bx - 3600, by + 3500, litN0.outputs[0])
    darkN = mathn(tree, 'SUBTRACT', bx - 3600, by + 3350, total.outputs[0],
                  litN.outputs[0])

    # ---- wall body -------------------------------------------------------
    wall = cube_s(tree, bx - 3000, by + 3000, W.outputs[0], WD, H.outputs[0])
    wall_tr = combine(tree, bx - 2800, by + 3000, 0.0, 0.0,
                      mathn(tree, 'MULTIPLY', bx - 3000, by + 2850,
                            H.outputs[0], 0.5).outputs[0])
    wall_x = xform(tree, bx - 2600, by + 3000, wall,
                   trans=wall_tr.outputs['Vector'])
    plinth_w = mathn(tree, 'ADD', bx - 3000, by + 2650, W.outputs[0], 0.30)
    plinth_d = mathn(tree, 'ADD', bx - 3000, by + 2500, WD, 0.22)
    plinth = cube_s(tree, bx - 3000, by + 2350, plinth_w.outputs[0],
                    plinth_d.outputs[0], PM)
    plinth_tr = combine(tree, bx - 2800, by + 2350, 0.0, 0.0,
                        mathn(tree, 'MULTIPLY', bx - 3000, by + 2200,
                              PM, 0.5).outputs[0])
    plinth_x = xform(tree, bx - 2600, by + 2350, plinth,
                     trans=plinth_tr.outputs['Vector'])

    # cornice: two stacked slabs
    cor1_w = mathn(tree, 'ADD', bx - 3000, by + 2050, W.outputs[0], 0.34)
    cor1_d = mathn(tree, 'ADD', bx - 3000, by + 1900, WD, 0.28)
    cor1 = cube_s(tree, bx - 3000, by + 1750, cor1_w.outputs[0],
                  cor1_d.outputs[0], 0.14)
    cor1_z = mathn(tree, 'ADD', bx - 3000, by + 1600, H.outputs[0], 0.10)
    cor1_x = xform(tree, bx - 2600, by + 1750, cor1,
                   trans=combine(tree, bx - 2800, by + 1600, 0.0, 0.0,
                                 cor1_z.outputs[0]).outputs['Vector'])
    cor2_w = mathn(tree, 'ADD', bx - 3000, by + 1450, W.outputs[0], 0.18)
    cor2_d = mathn(tree, 'ADD', bx - 3000, by + 1300, WD, 0.12)
    cor2 = cube_s(tree, bx - 3000, by + 1150, cor2_w.outputs[0],
                  cor2_d.outputs[0], 0.10)
    cor2_z = mathn(tree, 'SUBTRACT', bx - 3000, by + 1000, H.outputs[0], 0.04)
    cor2_x = xform(tree, bx - 2600, by + 1150, cor2,
                   trans=combine(tree, bx - 2800, by + 1000, 0.0, 0.0,
                                 cor2_z.outputs[0]).outputs['Vector'])

    # dentils under the cornice
    den_w = mathn(tree, 'ADD', bx - 3000, by + 850, W.outputs[0], 0.24)
    den_pitch = mathn(tree, 'DIVIDE', bx - 3000, by + 700, den_w.outputs[0],
                      mathn(tree, 'ADD', bx - 3000, by + 550,
                            gin.outputs['Dentils'], 1.0).outputs[0])
    den_start = mathn(tree, 'SUBTRACT', bx - 3000, by + 400,
                      mathn(tree, 'MULTIPLY', bx - 3000, by + 250,
                            HALF_W.outputs[0], -1.0).outputs[0],
                      mathn(tree, 'MULTIPLY', bx - 3000, by + 100,
                            0.12, 1.0).outputs[0])
    den_line = N(tree, 'GeometryNodeMeshLine', bx - 2800, by + 700)
    try:
        den_line.mode = 'OFFSET'
    except Exception:
        pass
    L(tree, gin, 'Dentils', den_line, 'Count')
    den_off = combine(tree, bx - 2800, by + 550, den_pitch.outputs[0], 0.0, 0.0)
    L(tree, den_off, 'Vector', den_line, 'Offset')
    den_sx = mathn(tree, 'ADD', bx - 2800, by + 400, den_start.outputs[0],
                   den_pitch.outputs[0])
    den_so = combine(tree, bx - 2800, by + 250, den_sx.outputs[0], 0.0, 0.0)
    L(tree, den_so, 'Vector', den_line, 'Start Location')
    den_h = mathn(tree, 'MULTIPLY', bx - 2800, by + 100,
                  gin.outputs['Dentil Size'], 1.20)
    den_tpl = cube_s(tree, bx - 2800, by - 50, gin.outputs['Dentil Size'],
                     mathn(tree, 'MULTIPLY', bx - 3000, by - 200,
                           WD, 0.60).outputs[0], den_h.outputs[0])
    den_z = mathn(tree, 'ADD', bx - 2800, by - 350, H.outputs[0], 0.04)
    den_tr = combine(tree, bx - 2800, by - 500, 0.0, 0.0, den_z.outputs[0])
    den_real = inst_realize(tree, bx - 2400, by + 700, den_line, den_tpl,
                            trans=den_tr.outputs['Vector'])

    # portal: door + frame + oculus, centered
    pw = gin.outputs['Portal Width']
    doorH = mathn(tree, 'MULTIPLY', bx - 3000, by - 700, pw, 1.9)
    door = cube_s(tree, bx - 3000, by - 850, pw, 0.12, doorH.outputs[0])
    door_y = mathn(tree, 'SUBTRACT', bx - 3000, by - 1000, HALF_D.outputs[0], 0.02)
    door_z = mathn(tree, 'MULTIPLY', bx - 3000, by - 1150, doorH.outputs[0], 0.5)
    door_tr = combine(tree, bx - 2800, by - 1000, 0.0, door_y.outputs[0],
                      door_z.outputs[0])
    door_x = xform(tree, bx - 2600, by - 850, door,
                   trans=door_tr.outputs['Vector'])
    jamb = cube_s(tree, bx - 3000, by - 1300, 0.10,
                  mathn(tree, 'MULTIPLY', bx - 3000, by - 1450,
                        WD, 0.36).outputs[0],
                  mathn(tree, 'ADD', bx - 3000, by - 1600, doorH.outputs[0],
                        0.14).outputs[0])
    jamb_dx = mathn(tree, 'ADD', bx - 3000, by - 1750,
                    mathn(tree, 'MULTIPLY', bx - 3000, by - 1900,
                          pw, 0.5).outputs[0], 0.05)
    jamb_a_tr = combine(tree, bx - 2800, by - 1750, jamb_dx.outputs[0],
                        door_y.outputs[0], door_z.outputs[0])
    jamb_a = xform(tree, bx - 2600, by - 1300, jamb,
                   trans=jamb_a_tr.outputs['Vector'])
    jamb_neg = mathn(tree, 'MULTIPLY', bx - 3000, by - 2050, jamb_dx.outputs[0],
                     -1.0)
    jamb_b_tr = combine(tree, bx - 2800, by - 2050, jamb_neg.outputs[0],
                        door_y.outputs[0], door_z.outputs[0])
    jamb_b = xform(tree, bx - 2600, by - 2200, jamb, trans=jamb_b_tr.outputs['Vector'])
    lintel_w = mathn(tree, 'ADD', bx - 3000, by - 2350, pw, 0.30)
    lintel = cube_s(tree, bx - 3000, by - 2500, lintel_w.outputs[0],
                    mathn(tree, 'MULTIPLY', bx - 3000, by - 2650,
                          WD, 0.40).outputs[0], 0.14)
    lintel_z = mathn(tree, 'ADD', bx - 3000, by - 2800, doorH.outputs[0], 0.07)
    lintel_tr = combine(tree, bx - 2800, by - 2800, 0.0, door_y.outputs[0],
                        lintel_z.outputs[0])
    lintel_x = xform(tree, bx - 2600, by - 2500, lintel,
                     trans=lintel_tr.outputs['Vector'])
    oc_r = mathn(tree, 'MULTIPLY', bx - 3000, by - 2950, pw, 0.42)
    oculus = cyl(tree, bx - 3000, by - 3100, oc_r.outputs[0], 0.07, 24)
    oc_z = mathn(tree, 'ADD', bx - 3000, by - 3250, lintel_z.outputs[0],
                 mathn(tree, 'ADD', bx - 3000, by - 3400,
                       oc_r.outputs[0], 0.16).outputs[0])
    oc_tr = combine(tree, bx - 2800, by - 3250, 0.0, door_y.outputs[0],
                    oc_z.outputs[0])
    oc_x = xform(tree, bx - 2600, by - 3100, oculus,
                 trans=oc_tr.outputs['Vector'],
                 rot=(HALF_PI, 0.0, 0.0))
    oc_g = guard_off(tree, bx - 2400, by - 3100, gin.outputs['Oculus'], oc_x)

    # ---- window templates (authored in window-local space) ----------------
    # DARK (day read): recessed pane in a proud stone surround.
    dk_frame = cube_s(tree, bx - 3000, by + 6200,
                      mathn(tree, 'ADD', bx - 3000, by + 6050,
                            winW.outputs[0], 0.14).outputs[0],
                      mathn(tree, 'MULTIPLY', bx - 3000, by + 5900, WD, 0.20).outputs[0],
                      mathn(tree, 'ADD', bx - 3000, by + 5750,
                            winH.outputs[0], 0.14).outputs[0])
    # frame y = +WallDepth/2 (sits flush at the wall face, proud by half its depth)
    dkf_y = HALF_D.outputs[0]
    dkf_tr = combine(tree, bx - 2800, by + 6050, 0.0, dkf_y, 0.0)
    dk_frame_x = xform(tree, bx - 2800, by + 6200, dk_frame,
                       trans=dkf_tr.outputs['Vector'])
    # pane: pushed IN by Window Recess
    dk_pane = cube_s(tree, bx - 3000, by + 5450, winW.outputs[0], 0.03,
                     winH.outputs[0])
    dkp_y = mathn(tree, 'SUBTRACT', bx - 3000, by + 5300, HALF_D.outputs[0],
                  RC)
    dkp_depth = mathn(tree, 'MULTIPLY', bx - 3000, by + 5150, WD, 0.20)
    dkp_y2 = mathn(tree, 'SUBTRACT', bx - 3000, by + 5000, dkp_y.outputs[0],
                   dkp_depth.outputs[0])
    dk_pane_x = xform(tree, bx - 2800, by + 5450, dk_pane,
                      trans=combine(tree, bx - 2800, by + 5300, 0.0,
                                    dkp_y2.outputs[0], 0.0).outputs['Vector'])
    # sill under the frame
    dk_sill = cube_s(tree, bx - 3000, by + 4850,
                     mathn(tree, 'ADD', bx - 3000, by + 4700,
                           winW.outputs[0], 0.26).outputs[0],
                     mathn(tree, 'MULTIPLY', bx - 3000, by + 4550, WD, 0.40).outputs[0],
                     0.07)
    dks_z = mathn(tree, 'SUBTRACT', bx - 3000, by + 4400, winH_h.outputs[0],
                  mathn(tree, 'MULTIPLY', bx - 3000, by + 4250,
                        0.07, 0.5).outputs[0])
    dk_sill_x = xform(tree, bx - 2800, by + 4850, dk_sill,
                      trans=combine(tree, bx - 2800, by + 4400, 0.0, dkf_y,
                                    dks_z.outputs[0]).outputs['Vector'])
    # muntins: vertical bars on a socket-count line + one horizontal bar
    mn_pitch = mathn(tree, 'DIVIDE', bx - 3000, by + 4100, winW.outputs[0],
                     mathn(tree, 'ADD', bx - 3000, by + 3950,
                           gin.outputs['Muntin Bars'], 1.0).outputs[0])
    mn_start = mathn(tree, 'ADD', bx - 3000, by + 3800,
                     mathn(tree, 'MULTIPLY', bx - 3000, by + 3650,
                           winW_h.outputs[0], -1.0).outputs[0],
                     mn_pitch.outputs[0])
    mn_line = N(tree, 'GeometryNodeMeshLine', bx - 2800, by + 4100)
    try:
        mn_line.mode = 'OFFSET'
    except Exception:
        pass
    L(tree, gin, 'Muntin Bars', mn_line, 'Count')
    mn_off = combine(tree, bx - 2800, by + 3950, mn_pitch.outputs[0], 0.0, 0.0)
    L(tree, mn_off, 'Vector', mn_line, 'Offset')
    mn_so = combine(tree, bx - 2800, by + 3800, mn_start.outputs[0], 0.0, 0.0)
    L(tree, mn_so, 'Vector', mn_line, 'Start Location')
    mn_bar_h = mathn(tree, 'SUBTRACT', bx - 3000, by + 3650,
                     winH.outputs[0], 0.06)
    mn_tpl = cube_s(tree, bx - 2800, by + 3500, 0.022, 0.03, mn_bar_h.outputs[0])
    mnp_y = mathn(tree, 'ADD', bx - 3000, by + 3350, dkp_y2.outputs[0], 0.02)
    mn_tr = combine(tree, bx - 2800, by + 3200, 0.0, mnp_y.outputs[0], 0.0)
    mn_real = inst_realize(tree, bx - 2400, by + 4100, mn_line, mn_tpl,
                           trans=mn_tr.outputs['Vector'])
    mn_hbar = cube_s(tree, bx - 2800, by + 2900, winW.outputs[0], 0.03, 0.02)
    mn_hbar_x = xform(tree, bx - 2600, by + 2900, mn_hbar,
                      trans=combine(tree, bx - 2800, by + 2750, 0.0,
                                    mnp_y.outputs[0], 0.0).outputs['Vector'])
    mn_join = N(tree, 'GeometryNodeJoinGeometry', bx - 2200, by + 3500)
    L(tree, mn_real, 'Geometry', mn_join, 'Geometry')
    L(tree, mn_hbar_x, 'Geometry', mn_join, 'Geometry')
    mn_g = guard_off(tree, bx - 2000, by + 3500, gin.outputs['Muntins'], mn_join)

    dk_join = N(tree, 'GeometryNodeJoinGeometry', bx - 1600, by + 5200)
    for node in (dk_frame_x, dk_pane_x, dk_sill_x, mn_g):
        L(tree, node, 'Geometry', dk_join, 'Geometry')
    dk_tpl = dk_join

    # LIT (night read): pane pushed proud + brass trim; sill shared.
    lt_pane = cube_s(tree, bx - 3000, by + 2300, winW.outputs[0], 0.06,
                     winH.outputs[0])
    ltp_y = mathn(tree, 'ADD', bx - 3000, by + 2150, HALF_D.outputs[0],
                  mathn(tree, 'MULTIPLY', bx - 3000, by + 2000,
                        LP, 0.5).outputs[0])
    lt_pane_x = xform(tree, bx - 2800, by + 2300, lt_pane,
                      trans=combine(tree, bx - 2800, by + 2150, 0.0,
                                    ltp_y.outputs[0], 0.0).outputs['Vector'])
    # brass trim: top, bottom, two sides around the pane
    trim_d = mathn(tree, 'MULTIPLY', bx - 3000, by + 1850, WD, 0.30)
    ltp_face = mathn(tree, 'ADD', bx - 3000, by + 1700, ltp_y.outputs[0], 0.03)
    tr_top = cube_s(tree, bx - 3000, by + 1550,
                    mathn(tree, 'ADD', bx - 3000, by + 1400,
                          winW.outputs[0], 0.10).outputs[0],
                    trim_d.outputs[0], 0.05)
    trt_z = mathn(tree, 'ADD', bx - 3000, by + 1250, winH_h.outputs[0], 0.025)
    tr_top_x = xform(tree, bx - 2800, by + 1550, tr_top,
                     trans=combine(tree, bx - 2800, by + 1250, 0.0,
                                   ltp_face.outputs[0], trt_z.outputs[0]).outputs['Vector'])
    tr_bot = cube_s(tree, bx - 3000, by + 1100,
                    mathn(tree, 'ADD', bx - 3000, by + 950,
                          winW.outputs[0], 0.10).outputs[0],
                    trim_d.outputs[0], 0.05)
    trb_z = mathn(tree, 'SUBTRACT', bx - 3000, by + 800, winH_h.outputs[0], -0.025)
    tr_bot_x = xform(tree, bx - 2800, by + 1100, tr_bot,
                     trans=combine(tree, bx - 2800, by + 800, 0.0,
                                   ltp_face.outputs[0], trb_z.outputs[0]).outputs['Vector'])
    tr_side = cube_s(tree, bx - 3000, by + 650, 0.05, trim_d.outputs[0],
                     mathn(tree, 'ADD', bx - 3000, by + 500,
                           winH.outputs[0], 0.10).outputs[0])
    trs_dx = mathn(tree, 'ADD', bx - 3000, by + 350, winW_h.outputs[0], 0.025)
    trs_a_tr = combine(tree, bx - 2800, by + 350, trs_dx.outputs[0],
                       ltp_face.outputs[0], 0.0)
    tr_side_a = xform(tree, bx - 2600, by + 650, tr_side,
                      trans=trs_a_tr.outputs['Vector'])
    trs_neg = mathn(tree, 'MULTIPLY', bx - 3000, by + 200, trs_dx.outputs[0], -1.0)
    trs_b_tr = combine(tree, bx - 2800, by + 200, trs_neg.outputs[0],
                       ltp_face.outputs[0], 0.0)
    tr_side_b = xform(tree, bx - 2600, by + 50, tr_side, trans=trs_b_tr.outputs['Vector'])
    tr_join = N(tree, 'GeometryNodeJoinGeometry', bx - 2200, by + 1100)
    for node in (tr_top_x, tr_bot_x, tr_side_a, tr_side_b):
        L(tree, node, 'Geometry', tr_join, 'Geometry')
    tr_g = guard_off(tree, bx - 2000, by + 1100, gin.outputs['Brass Trim'], tr_join)
    lt_sill = cube_s(tree, bx - 3000, by - 150,
                     mathn(tree, 'ADD', bx - 3000, by - 300,
                           winW.outputs[0], 0.26).outputs[0],
                     mathn(tree, 'MULTIPLY', bx - 3000, by - 450, WD, 0.40).outputs[0],
                     0.07)
    lt_sill_x = xform(tree, bx - 2800, by - 150, lt_sill,
                      trans=combine(tree, bx - 2800, by - 600, 0.0, dkf_y,
                                    dks_z.outputs[0]).outputs['Vector'])
    lt_join = N(tree, 'GeometryNodeJoinGeometry', bx - 1600, by + 1700)
    for node in (dk_frame_x, lt_pane_x, tr_g, lt_sill_x):
        L(tree, node, 'Geometry', lt_join, 'Geometry')
    lt_tpl = lt_join

    # ---- window streams: dark (bottom-up) and lit (top-down) --------------
    dk_pts = grid_points(tree, bx - 1200, by + 5200, darkN.outputs[0], 0.0,
                         BAYS, BW, FH, WB, winH_h.outputs[0])
    dk_win = inst_realize(tree, bx - 200, by + 5200, dk_pts, dk_tpl,
                          sname='Geometry')
    lt_pts = grid_points(tree, bx - 1200, by + 4300, litN.outputs[0],
                         darkN.outputs[0], BAYS, BW, FH, WB, winH_h.outputs[0])
    lt_win = inst_realize(tree, bx - 200, by + 4300, lt_pts, lt_tpl,
                          sname='Geometry')

    # ---- shutters over every window (all-grid stream) ---------------------
    panel_w = mathn(tree, 'MULTIPLY', bx - 3000, by - 900, winW.outputs[0], 0.52)
    panel_h = mathn(tree, 'ADD', bx - 3000, by - 1050, winH.outputs[0], 0.06)
    sh_bar = cube_s(tree, bx - 3000, by - 1200, panel_w.outputs[0], 0.035,
                    panel_h.outputs[0])
    theta = mathn(tree, 'MULTIPLY', bx - 3000, by - 1350, SO, math.pi)
    pan_off = mathn(tree, 'MULTIPLY', bx - 3000, by - 1500, panel_w.outputs[0], 0.5)
    # right panel: authored left-of-hinge (closed), rotated -theta, moved to +winW/2
    pr_neg = mathn(tree, 'MULTIPLY', bx - 3000, by - 1650, pan_off.outputs[0], -1.0)
    pr_a_tr = combine(tree, bx - 2800, by - 1500, pr_neg.outputs[0], 0.0, 0.0)
    pr_a = xform(tree, bx - 2800, by - 1200, sh_bar,
                 trans=pr_a_tr.outputs['Vector'])
    th_neg = mathn(tree, 'MULTIPLY', bx - 3000, by - 1800, theta.outputs[0], -1.0)
    pr_rot = combine(tree, bx - 2800, by - 1800, 0.0, 0.0, th_neg.outputs[0])
    pr_b = xform(tree, bx - 2600, by - 1200, pr_a, sname='Geometry',
                 rot=pr_rot.outputs['Vector'])
    sh_y = mathn(tree, 'ADD', bx - 3000, by - 1950, dkf_y, 0.035)
    pr_dx = mathn(tree, 'ADD', bx - 3000, by - 2100, winW_h.outputs[0], 0.02)
    pr_c = xform(tree, bx - 2400, by - 1200, pr_b, sname='Geometry',
                 trans=combine(tree, bx - 2400, by - 2100, pr_dx.outputs[0],
                               sh_y.outputs[0], 0.0).outputs['Vector'])
    # left panel: authored right-of-hinge, rotated +theta, moved to -winW/2
    pl_a_tr = combine(tree, bx - 2800, by - 2700, pan_off.outputs[0], 0.0, 0.0)
    pl_a = xform(tree, bx - 2800, by - 2400, sh_bar,
                 trans=pl_a_tr.outputs['Vector'])
    pl_rot = combine(tree, bx - 2800, by - 2850, 0.0, 0.0, theta.outputs[0])
    pl_b = xform(tree, bx - 2600, by - 2400, pl_a, sname='Geometry',
                 rot=pl_rot.outputs['Vector'])
    pl_dx = mathn(tree, 'MULTIPLY', bx - 3000, by - 3000, pr_dx.outputs[0], -1.0)
    pl_c = xform(tree, bx - 2400, by - 2400, pl_b, sname='Geometry',
                 trans=combine(tree, bx - 2400, by - 3150, pl_dx.outputs[0],
                               sh_y.outputs[0], 0.0).outputs['Vector'])
    sh_tpl = N(tree, 'GeometryNodeJoinGeometry', bx - 2000, by - 1800)
    L(tree, pr_c, 'Geometry', sh_tpl, 'Geometry')
    L(tree, pl_c, 'Geometry', sh_tpl, 'Geometry')
    sh_pts = grid_points(tree, bx - 1400, by - 1800, total.outputs[0], 0.0,
                         BAYS, BW, FH, WB, winH_h.outputs[0])
    sh_real = inst_realize(tree, bx - 100, by - 1800, sh_pts, sh_tpl,
                           sname='Geometry')
    sh_g = guard_off(tree, bx + 100, by - 1800, gin.outputs['Shutters'], sh_real)

    # ---- flower boxes under every window ----------------------------------
    fb_box = cube_s(tree, bx - 3000, by + 60,
                    mathn(tree, 'MULTIPLY', bx - 3000, by - 90,
                          winW.outputs[0], 0.92).outputs[0],
                    0.20, 0.14)
    fb_y = mathn(tree, 'ADD', bx - 3000, by - 240, HALF_D.outputs[0], 0.10)
    neg_hh = mathn(tree, 'MULTIPLY', bx - 3000, by - 540, winH_h.outputs[0], -1.0)
    fb_z = mathn(tree, 'SUBTRACT', bx - 3000, by - 390, neg_hh.outputs[0], 0.115)
    fb_box_x = xform(tree, bx - 2800, by + 60, fb_box,
                     trans=combine(tree, bx - 2800, by - 240, 0.0,
                                   fb_y.outputs[0], fb_z.outputs[0]).outputs['Vector'])
    # blooms: socket-count line with seeded jitter + scale
    bl_span = mathn(tree, 'MULTIPLY', bx - 3000, by - 690, winW.outputs[0], 0.78)
    bl_pitch = mathn(tree, 'DIVIDE', bx - 3000, by - 840, bl_span.outputs[0],
                     mathn(tree, 'MAXIMUM', bx - 3000, by - 990,
                           gin.outputs['Bloom Count'], 1.0).outputs[0])
    bl_start = mathn(tree, 'SUBTRACT', bx - 3000, by - 1140,
                     mathn(tree, 'MULTIPLY', bx - 3000, by - 1290,
                           bl_span.outputs[0], -0.5).outputs[0],
                     mathn(tree, 'MULTIPLY', bx - 3000, by - 1440,
                           bl_pitch.outputs[0], -0.5).outputs[0])
    bl_line = N(tree, 'GeometryNodeMeshLine', bx - 2800, by - 690)
    try:
        bl_line.mode = 'OFFSET'
    except Exception:
        pass
    L(tree, gin, 'Bloom Count', bl_line, 'Count')
    bl_off = combine(tree, bx - 2800, by - 840, bl_pitch.outputs[0], 0.0, 0.0)
    L(tree, bl_off, 'Vector', bl_line, 'Offset')
    bl_so = combine(tree, bx - 2800, by - 990, bl_start.outputs[0], 0.0, 0.0)
    L(tree, bl_so, 'Vector', bl_line, 'Start Location')
    bl_tpl = sphere(tree, bx - 2800, by - 1140, gin.outputs['Bloom Size'])
    rv_t = N(tree, 'FunctionNodeRandomValue', bx - 2800, by - 1340)
    try:
        rv_t.data_type = 'FLOAT_VECTOR'
    except Exception:
        pass
    try:
        rv_t.inputs['Min'].default_value = (-0.03, -0.02, 0.01)
        rv_t.inputs['Max'].default_value = (0.03, 0.02, 0.045)
    except Exception:
        pass
    try:
        rv_t.inputs['Seed'].default_value = 31
        link_sockets(tree, gin.outputs['Seed'], rv_t.inputs['Seed'])
    except Exception:
        pass
    rv_s = N(tree, 'FunctionNodeRandomValue', bx - 2600, by - 1540)
    try:
        rv_s.data_type = 'FLOAT'
    except Exception:
        pass
    try:
        rv_s.inputs['Min'].default_value = 0.75
        rv_s.inputs['Max'].default_value = 1.30
    except Exception:
        pass
    try:
        rv_s.inputs['Seed'].default_value = 32
        link_sockets(tree, gin.outputs['Seed'], rv_s.inputs['Seed'])
    except Exception:
        pass
    bl_base_tr = combine(tree, bx - 2800, by - 1740, 0.0, fb_y.outputs[0],
                         mathn(tree, 'ADD', bx - 3000, by - 1890,
                               fb_z.outputs[0], 0.065).outputs[0])
    # bloom offset/scale are FIELDS: wire them onto the instance stream before
    # realize (seeded jitter in X/Z + a per-bloom size wobble).
    bl_inst = N(tree, 'GeometryNodeInstanceOnPoints', bx - 2400, by - 690)
    L(tree, bl_line, 'Mesh', bl_inst, 'Points')
    L(tree, bl_tpl, 'Mesh', bl_inst, 'Instance')
    L(tree, rv_s, 0, bl_inst, 'Scale')
    bl_tr = N(tree, 'GeometryNodeTranslateInstances', bx - 2200, by - 900)
    L(tree, bl_inst, 'Instances', bl_tr, 'Instances')
    L(tree, rv_t, 0, bl_tr, 'Translation')
    bl_tr2 = N(tree, 'GeometryNodeTranslateInstances', bx - 2000, by - 1100)
    L(tree, bl_tr, 'Instances', bl_tr2, 'Instances')
    L(tree, bl_base_tr, 'Vector', bl_tr2, 'Translation')
    bl_real2 = N(tree, 'GeometryNodeRealizeInstances', bx - 1800, by - 950)
    L(tree, bl_tr2, 'Instances', bl_real2, 'Geometry')
    fb_join = N(tree, 'GeometryNodeJoinGeometry', bx - 1600, by - 300)
    L(tree, fb_box_x, 'Geometry', fb_join, 'Geometry')
    L(tree, bl_real2, 'Geometry', fb_join, 'Geometry')
    fb_pts = grid_points(tree, bx - 1400, by - 300, total.outputs[0], 0.0,
                         BAYS, BW, FH, WB, winH_h.outputs[0])
    fb_real = inst_realize(tree, bx - 100, by - 300, fb_pts, fb_join,
                           sname='Geometry')
    fb_g = guard_off(tree, bx + 100, by - 300, gin.outputs['Flower Boxes'], fb_real)

    # ---- balcony bands on the upper floors --------------------------------
    fl_m1 = mathn(tree, 'SUBTRACT', bx - 3000, by - 3600, FLOORS, 1.0)
    bd_slab_w = mathn(tree, 'ADD', bx - 3000, by - 3750, W.outputs[0], 0.20)
    bal_slab = cube_s(tree, bx - 3000, by - 3900, bd_slab_w.outputs[0], 0.55, 0.10)
    bal_slab_x = xform(tree, bx - 2800, by - 3900, bal_slab,
                       trans=(0.0, 0.0, 0.05))
    bal_bars_pitch = mathn(tree, 'DIVIDE', bx - 3000, by - 4050,
                           bd_slab_w.outputs[0],
                           mathn(tree, 'MAXIMUM', bx - 3000, by - 4200,
                                 gin.outputs['Balcony Bars'], 1.0).outputs[0])
    bal_bars_line = N(tree, 'GeometryNodeMeshLine', bx - 2800, by - 4050)
    try:
        bal_bars_line.mode = 'OFFSET'
    except Exception:
        pass
    L(tree, gin, 'Balcony Bars', bal_bars_line, 'Count')
    bbl_off = combine(tree, bx - 2800, by - 4200, bal_bars_pitch.outputs[0],
                      0.0, 0.0)
    L(tree, bbl_off, 'Vector', bal_bars_line, 'Offset')
    bbl_so = combine(tree, bx - 2800, by - 4350,
                     mathn(tree, 'MULTIPLY', bx - 3000, by - 4500,
                           bd_slab_w.outputs[0], -0.5).outputs[0], 0.0, 0.0)
    L(tree, bbl_so, 'Vector', bal_bars_line, 'Start Location')
    bal_bar_tpl = cyl(tree, bx - 2800, by - 4650, 0.013,
                      mathn(tree, 'ADD', bx - 3000, by - 4800,
                            gin.outputs['Rail Height'], 0.10).outputs[0], 8)
    bal_bars_z = mathn(tree, 'MULTIPLY', bx - 3000, by - 4950,
                       gin.outputs['Rail Height'], 0.5)
    bal_bars_tr = combine(tree, bx - 2800, by - 5100, 0.0, 0.0,
                          bal_bars_z.outputs[0])
    bal_bars_real = inst_realize(tree, bx - 2400, by - 4050, bal_bars_line,
                                 bal_bar_tpl, trans=bal_bars_tr.outputs['Vector'])
    bal_top = cube_s(tree, bx - 3000, by - 5250, bd_slab_w.outputs[0], 0.05, 0.04)
    bal_top_x = xform(tree, bx - 2800, by - 5250, bal_top,
                      trans=combine(tree, bx - 2800, by - 5400, 0.0, 0.0,
                                    gin.outputs['Rail Height']).outputs['Vector'])
    bal_join = N(tree, 'GeometryNodeJoinGeometry', bx - 2200, by - 4200)
    for node in (bal_slab_x, bal_bars_real, bal_top_x):
        L(tree, node, 'Geometry', bal_join, 'Geometry')
    bal_line = N(tree, 'GeometryNodeMeshLine', bx - 2000, by - 4200)
    try:
        bal_line.mode = 'OFFSET'
    except Exception:
        pass
    L(tree, fl_m1, 0, bal_line, 'Count')
    bal_off_z = combine(tree, bx - 2000, by - 4350, 0.0, 0.0, FH)
    L(tree, bal_off_z, 'Vector', bal_line, 'Offset')
    bal_start_z = combine(tree, bx - 2000, by - 4500, 0.0, 0.0, FH)
    L(tree, bal_start_z, 'Vector', bal_line, 'Start Location')
    bal_real = inst_realize(tree, bx - 1600, by - 4200, bal_line, bal_join,
                            sname='Geometry')
    bal_g = guard_off(tree, bx - 1400, by - 4200, gin.outputs['Balconies'], bal_real)

    # ---- bird frieze: two interlocking flocks on the roofline -------------
    BS = gin.outputs['Bird Size']

    def bird_template(t, x, y):
        body = cube_s(t, x, y, 0.10, 0.06, 0.16)
        tail = cube_s(t, x, y - 140, 0.08, 0.05, 0.12)
        tail_x = xform(t, x + 200, y - 140, tail, trans=(0.0, 0.0, -0.14))
        wing_l = cube_s(t, x, y - 300, 0.42, 0.05, 0.10)
        wing_l_x = xform(t, x + 200, y - 300, wing_l,
                         trans=(-0.20, 0.0, 0.05), rot=(0.0, 0.60, 0.0))
        wing_r = cube_s(t, x, y - 460, 0.42, 0.05, 0.10)
        wing_r_x = xform(t, x + 200, y - 460, wing_r,
                         trans=(0.20, 0.0, 0.05), rot=(0.0, -0.60, 0.0))
        j = N(t, 'GeometryNodeJoinGeometry', x + 400, y - 230)
        for node in (body, tail_x, wing_l_x, wing_r_x):
            L(t, node, out_name(node, 'Geometry', 'Mesh'), j, 'Geometry')
        return xform(t, x + 600, y - 230, j, sname='Geometry', scale=BS)

    birds_up = bird_template(tree, bx + 2400, by + 4000)
    birds_dn_j = bird_template(tree, bx + 2400, by + 3600)
    birds_dn = xform(tree, bx + 2600, by + 3600, birds_dn_j, sname='Geometry',
                     rot=(math.pi, 0.0, 0.0))
    bird_z0 = mathn(tree, 'ADD', bx - 3000, by + 3200, H.outputs[0], 0.55)
    bird_pitch = mathn(tree, 'DIVIDE', bx - 3000, by + 3050, W.outputs[0],
                       mathn(tree, 'ADD', bx - 3000, by + 2900,
                             gin.outputs['Birds'], 1.0).outputs[0])
    bird_start = mathn(tree, 'SUBTRACT', bx - 3000, by + 2750,
                       mathn(tree, 'MULTIPLY', bx - 3000, by + 2600,
                             HALF_W.outputs[0], -1.0).outputs[0],
                       mathn(tree, 'MULTIPLY', bx - 3000, by + 2450,
                             bird_pitch.outputs[0], -0.5).outputs[0])
    # flock A: wings up, on the roofline
    ba_line = N(tree, 'GeometryNodeMeshLine', bx + 2400, by + 3400)
    try:
        ba_line.mode = 'OFFSET'
    except Exception:
        pass
    L(tree, gin, 'Birds', ba_line, 'Count')
    ba_off = combine(tree, bx + 2400, by + 3250, bird_pitch.outputs[0], 0.0, 0.0)
    L(tree, ba_off, 'Vector', ba_line, 'Offset')
    ba_so = combine(tree, bx + 2400, by + 3100, bird_start.outputs[0], 0.0, 0.0)
    L(tree, ba_so, 'Vector', ba_line, 'Start Location')
    ba_tr = combine(tree, bx + 2400, by + 2950, 0.0, 0.0, bird_z0.outputs[0])
    ba_real = inst_realize(tree, bx + 2800, by + 3400, ba_line, birds_up,
                           sname='Geometry', trans=ba_tr.outputs['Vector'])
    # flock B: wings down, offset half a pitch and dropped by Bird Lock
    bb_line = N(tree, 'GeometryNodeMeshLine', bx + 2400, by + 2500)
    try:
        bb_line.mode = 'OFFSET'
    except Exception:
        pass
    L(tree, gin, 'Birds', bb_line, 'Count')
    bb_off = combine(tree, bx + 2400, by + 2350, bird_pitch.outputs[0], 0.0, 0.0)
    L(tree, bb_off, 'Vector', bb_line, 'Offset')
    bb_shift = mathn(tree, 'ADD', bx - 3000, by + 2200, bird_start.outputs[0],
                     mathn(tree, 'MULTIPLY', bx - 3000, by + 2050,
                           bird_pitch.outputs[0], 0.5).outputs[0])
    bb_so = combine(tree, bx + 2400, by + 1900, bb_shift.outputs[0], 0.0, 0.0)
    L(tree, bb_so, 'Vector', bb_line, 'Start Location')
    lock_drop = mathn(tree, 'MULTIPLY', bx - 3000, by + 1750,
                      gin.outputs['Bird Lock'],
                      mathn(tree, 'MULTIPLY', bx - 3000, by + 1600,
                            BS, 0.85).outputs[0])
    bb_z = mathn(tree, 'SUBTRACT', bx + 2400, by + 1450, bird_z0.outputs[0],
                 lock_drop.outputs[0])
    bb_tr = combine(tree, bx + 2400, by + 1300, 0.0, 0.0, bb_z.outputs[0])
    bb_real = inst_realize(tree, bx + 2800, by + 2500, bb_line, birds_dn,
                           sname='Geometry', trans=bb_tr.outputs['Vector'])

    # ---- join ------------------------------------------------------------
    j1 = N(tree, 'GeometryNodeJoinGeometry', bx + 5000, by + 400)
    for node in (wall_x, plinth_x, cor1_x, cor2_x, den_real, door_x,
                 jamb_a, jamb_b, lintel_x, oc_g):
        L(tree, node, 'Geometry', j1, 'Geometry')
    j2 = N(tree, 'GeometryNodeJoinGeometry', bx + 5200, by + 200)
    L(tree, j1, 'Geometry', j2, 'Geometry')
    for node in (dk_win, lt_win, sh_g, fb_g, bal_g, ba_real, bb_real):
        L(tree, node, 'Geometry', j2, 'Geometry')
    j3 = N(tree, 'GeometryNodeJoinGeometry', bx + 5400, by + 0)
    L(tree, j2, 'Geometry', j3, 'Geometry')
    L(tree, j3, 'Geometry', gout, 'Geometry')

    return tree, gin, gout


# ------------------------------------------------- addon registration

try:
    from .core import register_builder  # noqa: E402
    register_builder(
        'GN_PARIS_DayNightFacade', build_paris_daynight_facade,
        'PARIS Day-Night Facade',
        'Haussmann bay wall with a Night Mix slider: lit windows climb down '
        'from the top floor, panes pop proud, brass trim on. Shutters, '
        'balcony bands, dentils, geranium boxes and an interlocking bird '
        'frieze (Bird Lock) are all dials.',
        category='escher',
    )
    print('[paris_daynight_facade] registered GN_PARIS_DayNightFacade')
except ImportError:
    print('[paris_daynight_facade] standalone mode (no core registry)')


if __name__ == '__main__':
    build_paris_daynight_facade()
