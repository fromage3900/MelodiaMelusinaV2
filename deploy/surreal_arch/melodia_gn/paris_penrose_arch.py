"""Parisian Penrose arch - the tribar join as a doorway.

GN_PARIS_PenroseArch (build_paris_penrose_arch)

The Penrose triangle's trick is a join that cannot exist: one beam passes IN
FRONT of a column at one end and BEHIND it at the other.  This builder puts
that join on a doorway: the lintel is honest, but its two END BLOCKS slide in
opposite directions out of the wall plane.

The impossibility is `Impossibility`:

    0.0    an honest arch - both join blocks flush with the jambs;
    + / -  the LEFT block steps toward the street and the RIGHT block steps
           back (or vice versa): the lintel visibly passes in front of one
           jamb and behind the other, which no real lintel can do.

`Swap Offset` is how far the blocks travel at full impossibility - the dial
lets one arch be a working doorway in one shot and a paradox in the next.

NOT a reimplementation of MEL_penrose_triangle (a decorative tribar of beams):
that is a motif; this is the architectural doorway device, with jambs, plinths,
keystone, brackets, crown and an optional panelled door.

Follows the paris_* family convention: helpers from paris_common,
register_builder() at import time, every parameter an editable named input.
"""

from __future__ import annotations

import math

import bpy

from .core import new_geometry_tree, add_float_param, add_int_param, add_bool_param
from .paris_common import (
    N, L, mathn, booln, combine, xform, cyl, sphere, cube_s,
    inst_realize, guard_off, out_name,
)


def build_paris_penrose_arch(group_name="GN_PARIS_PenroseArch"):
    """Penrose doorway: honest jambs, a lintel whose joins swap sides."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    # ---- dials -----------------------------------------------------------
    add_float_param(tree, "Arch Width", 1.6, 0.8, 3.0)
    add_float_param(tree, "Arch Height", 2.6, 1.4, 4.0)
    add_float_param(tree, "Jamb Width", 0.36, 0.15, 0.8)
    add_float_param(tree, "Jamb Depth", 0.45, 0.2, 1.0)
    add_float_param(tree, "Lintel Height", 0.45, 0.2, 0.9)
    add_float_param(tree, "Impossibility", 0.0, -1.0, 1.0)
    add_float_param(tree, "Swap Offset", 0.22, 0.05, 0.40)
    add_bool_param(tree, "Keystone", True)
    add_float_param(tree, "Keystone Size", 0.36, 0.15, 0.8)
    add_bool_param(tree, "Plinths", True)
    add_float_param(tree, "Plinth Height", 0.22, 0.08, 0.5)
    add_bool_param(tree, "Brackets", True)
    add_float_param(tree, "Bracket Size", 0.16, 0.06, 0.35)
    add_bool_param(tree, "Crown", True)
    add_float_param(tree, "Crown Size", 0.22, 0.08, 0.5)
    add_bool_param(tree, "Panel", True)
    add_float_param(tree, "Panel Size", 0.50, 0.20, 1.0)
    add_bool_param(tree, "Door", True)
    add_int_param(tree, "Door Panels", 2, 0, 4)

    AW = gin.outputs['Arch Width']
    AH = gin.outputs['Arch Height']
    JW = gin.outputs['Jamb Width']
    JD = gin.outputs['Jamb Depth']
    LH = gin.outputs['Lintel Height']
    IMP = gin.outputs['Impossibility']
    SO = gin.outputs['Swap Offset']
    PH = gin.outputs['Plinth Height']

    # ---- jambs (street side = +Y, same convention as the facade) ---------
    jamb_x = mathn(tree, 'ADD', bx - 3000, by + 5000, AW,
                   mathn(tree, 'MULTIPLY', bx - 3000, by + 4850,
                         JW, 0.5).outputs[0])
    jamb_z = mathn(tree, 'ADD', bx - 3000, by + 4700, PH,
                   mathn(tree, 'MULTIPLY', bx - 3000, by + 4550,
                         AH, 0.5).outputs[0])
    jambs = []
    for js in (-1.0, 1.0):
        jamb = cube_s(tree, bx - 3000, by + 4400 + js * 10, JW, JD, AH)
        jx = mathn(tree, 'MULTIPLY', bx - 3000, by + 4250 + js * 10,
                   jamb_x.outputs[0], js)
        jamb_tr = combine(tree, bx - 2800, by + 4250 + js * 10, jx.outputs[0],
                          0.0, jamb_z.outputs[0])
        jambs.append(xform(tree, bx - 2600, by + 4400 + js * 10, jamb,
                           trans=jamb_tr.outputs['Vector']))
    # inner reveal liners (thin, make the opening read as a doorway)
    reveal = cube_s(tree, bx - 3000, by + 4200, 0.05,
                    mathn(tree, 'MULTIPLY', bx - 3000, by + 4050,
                          JD, 0.92).outputs[0], AH)
    reveals = []
    for rs in (-1.0, 1.0):
        rx2 = mathn(tree, 'MULTIPLY', bx - 3000, by + 3900, AW, 0.5 * rs)
        # pull each liner 0.025 INSIDE the opening
        rx3 = mathn(tree, 'SUBTRACT', bx - 3000, by + 3750, rx2.outputs[0],
                    0.025 * rs)
        rev_tr = combine(tree, bx - 2800, by + 3750, rx3.outputs[0], 0.0,
                         jamb_z.outputs[0])
        reveals.append(xform(tree, bx - 2600, by + 4200, reveal,
                             trans=rev_tr.outputs['Vector']))

    # ---- lintel + the two join blocks (the device) -----------------------
    lintel_w = mathn(tree, 'ADD', bx - 3000, by + 3450, AW,
                     mathn(tree, 'MULTIPLY', bx - 3000, by + 3300,
                           JW, 0.70).outputs[0])
    lintel_z = mathn(tree, 'ADD', bx - 3000, by + 3150, PH,
                     mathn(tree, 'ADD', bx - 3000, by + 3000, AH,
                           mathn(tree, 'MULTIPLY', bx - 3000, by + 2850,
                                 LH, 0.5).outputs[0]).outputs[0])
    lintel = cube_s(tree, bx - 3000, by + 2700, lintel_w.outputs[0],
                    mathn(tree, 'MULTIPLY', bx - 3000, by + 2550,
                          JD, 0.90).outputs[0], LH)
    lintel_x = xform(tree, bx - 2800, by + 2700, lintel,
                     trans=combine(tree, bx - 2800, by + 2550, 0.0, 0.0,
                                   lintel_z.outputs[0]).outputs['Vector'])
    # join blocks: left and right, sliding in OPPOSITE y directions
    block = cube_s(tree, bx - 3000, by + 2400,
                   mathn(tree, 'MULTIPLY', bx - 3000, by + 2250,
                         JW, 0.85).outputs[0],
                   mathn(tree, 'MULTIPLY', bx - 3000, by + 2100,
                         JD, 1.05).outputs[0], LH)
    blocks = []
    for bs in (-1.0, 1.0):
        # left block slides -Y at +Impossibility, right block +Y (sign flips)
        bslide = mathn(tree, 'MULTIPLY', bx - 3000, by + 1950 + bs * 10,
                       mathn(tree, 'MULTIPLY', bx - 3000, by + 1800 + bs * 10,
                             IMP, SO).outputs[0], -1.0 * bs)
        bx_pos = mathn(tree, 'MULTIPLY', bx - 3000, by + 1650 + bs * 10,
                       jamb_x.outputs[0], bs)
        b_tr = combine(tree, bx - 2800, by + 1650 + bs * 10, bx_pos.outputs[0],
                       bslide.outputs[0], lintel_z.outputs[0])
        blocks.append(xform(tree, bx - 2600, by + 2400 + bs * 10, block,
                            trans=b_tr.outputs['Vector']))

    # ---- keystone --------------------------------------------------------
    ks = gin.outputs['Keystone Size']
    ks_w = mathn(tree, 'MULTIPLY', bx - 3000, by + 1350, ks, 0.75)
    ks_d = mathn(tree, 'MULTIPLY', bx - 3000, by + 1200, JD, 1.15)
    ks_h = mathn(tree, 'MULTIPLY', bx - 3000, by + 1050, LH, 1.10)
    key = cube_s(tree, bx - 3000, by + 900, ks_w.outputs[0], ks_d.outputs[0],
                 ks_h.outputs[0])
    key_x = xform(tree, bx - 2800, by + 900, key,
                  trans=combine(tree, bx - 2800, by + 750, 0.0, 0.0,
                                lintel_z.outputs[0]).outputs['Vector'])
    key_g = guard_off(tree, bx - 2600, by + 900, gin.outputs['Keystone'], key_x)

    # ---- plinths ---------------------------------------------------------
    plinth = cube_s(tree, bx - 3000, by + 450,
                    mathn(tree, 'ADD', bx - 3000, by + 300, JW, 0.16).outputs[0],
                    mathn(tree, 'ADD', bx - 3000, by + 150, JD, 0.12).outputs[0],
                    PH)
    plinths = []
    for ps in (-1.0, 1.0):
        px = mathn(tree, 'MULTIPLY', bx - 3000, by + 0, jamb_x.outputs[0], ps)
        p_tr = combine(tree, bx - 2800, by + 0, px.outputs[0], 0.0,
                       mathn(tree, 'MULTIPLY', bx - 3000, by - 150,
                             PH, 0.5).outputs[0])
        plinths.append(xform(tree, bx - 2600, by + 450 + ps * 10, plinth,
                             trans=p_tr.outputs['Vector']))
    plinth_join = N(tree, 'GeometryNodeJoinGeometry', bx - 2200, by + 300)
    for node in plinths:
        L(tree, node, 'Geometry', plinth_join, 'Geometry')
    plinth_g = guard_off(tree, bx - 2000, by + 300, gin.outputs['Plinths'],
                         plinth_join)

    # ---- brackets under the lintel ends ----------------------------------
    BS = gin.outputs['Bracket Size']
    bracket = cube_s(tree, bx - 3000, by - 600, BS,
                     mathn(tree, 'MULTIPLY', bx - 3000, by - 750,
                           JD, 0.90).outputs[0], BS)
    brackets = []
    for bs2 in (-1.0, 1.0):
        bdx = mathn(tree, 'MULTIPLY', bx - 3000, by - 900 + bs2 * 10,
                    jamb_x.outputs[0], bs2 * 0.82)
        b_z = mathn(tree, 'SUBTRACT', bx - 3000, by - 1050 + bs2 * 10,
                    lintel_z.outputs[0],
                    mathn(tree, 'ADD', bx - 3000, by - 1200 + bs2 * 10,
                          mathn(tree, 'MULTIPLY', bx - 3000, by - 1350 + bs2 * 10,
                                LH, 0.5).outputs[0],
                          mathn(tree, 'MULTIPLY', bx - 3000, by - 1500 + bs2 * 10,
                                BS, 0.5).outputs[0]).outputs[0])
        b_tr = combine(tree, bx - 2800, by - 1050 + bs2 * 10, bdx.outputs[0],
                       0.0, b_z.outputs[0])
        brackets.append(xform(tree, bx - 2600, by - 600 + bs2 * 10, bracket,
                              trans=b_tr.outputs['Vector']))
    bracket_join = N(tree, 'GeometryNodeJoinGeometry', bx - 2200, by - 900)
    for node in brackets:
        L(tree, node, 'Geometry', bracket_join, 'Geometry')
    bracket_g = guard_off(tree, bx - 2000, by - 900, gin.outputs['Brackets'],
                          bracket_join)

    # ---- crown over the lintel -------------------------------------------
    CS = gin.outputs['Crown Size']
    crown1 = cube_s(tree, bx - 3000, by - 1800,
                    mathn(tree, 'ADD', bx - 3000, by - 1950,
                          lintel_w.outputs[0], 0.24).outputs[0],
                    mathn(tree, 'MULTIPLY', bx - 3000, by - 2100,
                          JD, 1.25).outputs[0],
                    mathn(tree, 'MULTIPLY', bx - 3000, by - 2250,
                          CS, 0.5).outputs[0])
    crown1_z = mathn(tree, 'ADD', bx - 3000, by - 2400, lintel_z.outputs[0],
                     mathn(tree, 'ADD', bx - 3000, by - 2550,
                           mathn(tree, 'MULTIPLY', bx - 3000, by - 2700,
                                 LH, 0.5).outputs[0],
                           mathn(tree, 'MULTIPLY', bx - 3000, by - 2850,
                                 CS, 0.25).outputs[0]).outputs[0])
    crown1_x = xform(tree, bx - 2800, by - 1800, crown1,
                     trans=combine(tree, bx - 2800, by - 2400, 0.0, 0.0,
                                   crown1_z.outputs[0]).outputs['Vector'])
    crown2 = cube_s(tree, bx - 3000, by - 3000,
                    mathn(tree, 'ADD', bx - 3000, by - 3150,
                          lintel_w.outputs[0], 0.10).outputs[0],
                    mathn(tree, 'MULTIPLY', bx - 3000, by - 3300,
                          JD, 1.05).outputs[0],
                    mathn(tree, 'MULTIPLY', bx - 3000, by - 3450,
                          CS, 0.28).outputs[0])
    crown2_z = mathn(tree, 'ADD', bx - 3000, by - 3600, crown1_z.outputs[0],
                     mathn(tree, 'MULTIPLY', bx - 3000, by - 3750,
                           CS, 0.39).outputs[0])
    crown2_x = xform(tree, bx - 2800, by - 3000, crown2,
                     trans=combine(tree, bx - 2800, by - 3600, 0.0, 0.0,
                                   crown2_z.outputs[0]).outputs['Vector'])
    crown_join = N(tree, 'GeometryNodeJoinGeometry', bx - 2200, by - 3000)
    L(tree, crown1_x, 'Geometry', crown_join, 'Geometry')
    L(tree, crown2_x, 'Geometry', crown_join, 'Geometry')
    crown_g = guard_off(tree, bx - 2000, by - 3000, gin.outputs['Crown'],
                        crown_join)

    # ---- inscription panel (cartouche) -----------------------------------
    PS = gin.outputs['Panel Size']
    panel = cube_s(tree, bx - 3000, by - 4200,
                   mathn(tree, 'MULTIPLY', bx - 3000, by - 4350,
                         PS, 1.40).outputs[0], 0.08, PS)
    panel_y = mathn(tree, 'ADD', bx - 3000, by - 4500,
                    mathn(tree, 'MULTIPLY', bx - 3000, by - 4650,
                          JD, 0.5).outputs[0], 0.04)
    panel_z = mathn(tree, 'ADD', bx - 3000, by - 4800, crown2_z.outputs[0],
                    mathn(tree, 'ADD', bx - 3000, by - 4950,
                          mathn(tree, 'MULTIPLY', bx - 3000, by - 5100,
                                CS, 0.14).outputs[0],
                          mathn(tree, 'MULTIPLY', bx - 3000, by - 5250,
                                PS, 0.5).outputs[0]).outputs[0])
    panel_x = xform(tree, bx - 2800, by - 4200, panel,
                    trans=combine(tree, bx - 2800, by - 4800, 0.0,
                                  panel_y.outputs[0], panel_z.outputs[0]).outputs['Vector'])
    panel_g = guard_off(tree, bx - 2600, by - 4200, gin.outputs['Panel'], panel_x)

    # ---- door leaf with raised panels ------------------------------------
    door_w = mathn(tree, 'SUBTRACT', bx - 3000, by - 5400, AW, 0.06)
    door_h = mathn(tree, 'SUBTRACT', bx - 3000, by - 5550, AH, 0.04)
    door = cube_s(tree, bx - 3000, by - 5700, door_w.outputs[0], 0.08,
                  door_h.outputs[0])
    door_z = mathn(tree, 'ADD', bx - 3000, by - 5850, PH,
                   mathn(tree, 'MULTIPLY', bx - 3000, by - 6000,
                         AH, 0.5).outputs[0])
    door_x = xform(tree, bx - 2800, by - 5700, door,
                   trans=combine(tree, bx - 2800, by - 5850, 0.0, 0.0,
                                 door_z.outputs[0]).outputs['Vector'])
    dp_w = mathn(tree, 'MULTIPLY', bx - 3000, by - 6150, AW, 0.55)
    dp_h = mathn(tree, 'DIVIDE', bx - 3000, by - 6300,
                 mathn(tree, 'MULTIPLY', bx - 3000, by - 6450,
                       AH, 0.60).outputs[0],
                 mathn(tree, 'MAXIMUM', bx - 3000, by - 6600,
                       gin.outputs['Door Panels'], 1.0).outputs[0])
    dp_tpl = cube_s(tree, bx - 3000, by - 6750, dp_w.outputs[0], 0.03,
                    dp_h.outputs[0])
    dp_line = N(tree, 'GeometryNodeMeshLine', bx - 2800, by - 6750)
    try:
        dp_line.mode = 'OFFSET'
    except Exception:
        pass
    L(tree, gin, 'Door Panels', dp_line, 'Count')
    dp_off = combine(tree, bx - 2800, by - 6900, 0.0, 0.0, dp_h.outputs[0])
    L(tree, dp_off, 'Vector', dp_line, 'Offset')
    dp_so = combine(tree, bx - 2800, by - 7050, 0.0, 0.0,
                    mathn(tree, 'ADD', bx - 3000, by - 7200, PH,
                          mathn(tree, 'MULTIPLY', bx - 3000, by - 7350,
                                dp_h.outputs[0], 0.5).outputs[0]).outputs[0])
    L(tree, dp_so, 'Vector', dp_line, 'Start Location')
    dp_tr = combine(tree, bx - 2800, by - 7500, 0.0, 0.055, 0.0)
    dp_real = inst_realize(tree, bx - 2400, by - 6750, dp_line, dp_tpl,
                           trans=dp_tr.outputs['Vector'])
    door_join = N(tree, 'GeometryNodeJoinGeometry', bx - 2000, by - 5700)
    L(tree, door_x, 'Geometry', door_join, 'Geometry')
    L(tree, dp_real, 'Geometry', door_join, 'Geometry')
    door_g = guard_off(tree, bx - 1800, by - 5700, gin.outputs['Door'],
                       door_join)

    # ---- join ------------------------------------------------------------
    j1 = N(tree, 'GeometryNodeJoinGeometry', bx + 4000, by + 2000)
    for node in jambs:
        L(tree, node, 'Geometry', j1, 'Geometry')
    for node in reveals:
        L(tree, node, 'Geometry', j1, 'Geometry')
    for node in (lintel_x, blocks[0], blocks[1], key_g, plinth_g, bracket_g,
                 crown_g, panel_g, door_g):
        L(tree, node, 'Geometry', j1, 'Geometry')
    L(tree, j1, 'Geometry', gout, 'Geometry')

    return tree, gin, gout


# ------------------------------------------------- addon registration

try:
    from .core import register_builder  # noqa: E402
    register_builder(
        'GN_PARIS_PenroseArch', build_paris_penrose_arch,
        'PARIS Penrose Arch',
        'Doorway with the tribar join: Impossibility slides the two lintel '
        'join blocks in opposite directions - in front of one jamb, behind '
        'the other. Keystone, plinths, brackets, crown, cartouche, door.',
        category='escher',
    )
    print('[paris_penrose_arch] registered GN_PARIS_PenroseArch')
except ImportError:
    print('[paris_penrose_arch] standalone mode (no core registry)')


if __name__ == '__main__':
    build_paris_penrose_arch()
