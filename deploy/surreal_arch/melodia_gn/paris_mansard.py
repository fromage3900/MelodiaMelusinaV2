"""Parisian mansard roof band - the slate hat every Haussmann facade wears.

GN_PARIS_Mansard (build_paris_mansard)

The DayNightFacade stops at its cornice; this builder is the roof above it:
the two-slope mansard profile (steep lower pitch, shallow upper), zinc seam
ribs, gabled or oculus dormers, chimney stacks with pots, and the iron
cresting along the ridge.  Width is the facade's width - put a 5-bay facade
under an 11.5 m band and the eaves line up.

The profile is fully parametric: `Break Point` splits the half-depth between
the two slopes, and each slope carries its own rise/run.  Roof height is
DERIVED from depth x slopes, so the eaves can never float above the walls.

NOT a reimplementation of anything in the registry: no mansard/roof-band
builder exists (the ladder's "Mansard Landing" is a wedge above one landing,
not a roof).  The slate/zinc language matches GN_PARIS_WallDetail's palette
notes; materials land downstream.

Follows the paris_* family convention: helpers from paris_common,
register_builder() at import time, every parameter an editable named input.
"""

from __future__ import annotations

import math

import bpy

from .core import new_geometry_tree, add_float_param, add_int_param, add_bool_param
from .paris_common import (
    N, L, mathn, booln, combine, xform, cyl, sphere, cube_s,
    inst_realize, guard_off, out_name, HALF_PI,
)


def build_paris_mansard(group_name="GN_PARIS_Mansard"):
    """Haussmann mansard band: two-slope profile + dormers + zinc + chimneys."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    # ---- dials -----------------------------------------------------------
    add_float_param(tree, "Band Width", 11.5, 4.0, 24.0)
    add_float_param(tree, "Band Depth", 6.0, 2.0, 12.0)
    add_float_param(tree, "Lower Slope", 1.15, 0.5, 1.8)
    add_float_param(tree, "Upper Slope", 0.25, 0.05, 0.7)
    add_float_param(tree, "Break Point", 0.62, 0.30, 0.85)
    add_float_param(tree, "Cornice Lip", 0.16, 0.05, 0.4)
    add_int_param(tree, "Dormers", 4, 0, 8)
    add_float_param(tree, "Dormer Width", 0.85, 0.4, 1.6)
    add_float_param(tree, "Dormer Height", 0.95, 0.5, 1.8)
    add_bool_param(tree, "Oculus Dormers", True)
    add_int_param(tree, "Zinc Ribs", 14, 0, 40)
    add_float_param(tree, "Rib Size", 0.02, 0.008, 0.06)
    add_int_param(tree, "Chimneys", 2, 0, 6)
    add_float_param(tree, "Chimney Height", 1.10, 0.40, 2.5)
    add_int_param(tree, "Chimney Pots", 3, 0, 6)
    add_bool_param(tree, "Iron Cresting", True)
    add_int_param(tree, "Cresting", 16, 0, 40)

    W = gin.outputs['Band Width']
    D = gin.outputs['Band Depth']
    LS = gin.outputs['Lower Slope']
    US = gin.outputs['Upper Slope']
    BP = gin.outputs['Break Point']
    LIP = gin.outputs['Cornice Lip']
    DORW = gin.outputs['Dormer Width']
    DORH = gin.outputs['Dormer Height']

    # ---- profile math ----------------------------------------------------
    # run per side = D/2; split at Break Point; height is derived from slopes.
    half_d = mathn(tree, 'MULTIPLY', bx - 3000, by + 5000, D, 0.5)
    run_l = mathn(tree, 'MULTIPLY', bx - 3000, by + 4850, half_d.outputs[0], BP)
    one_m_bp = mathn(tree, 'SUBTRACT', bx - 3000, by + 4700, 1.0, BP)
    run_u = mathn(tree, 'MULTIPLY', bx - 3000, by + 4550, half_d.outputs[0],
                  one_m_bp.outputs[0])
    h_l = mathn(tree, 'MULTIPLY', bx - 3000, by + 4400, run_l.outputs[0], LS)
    h_u = mathn(tree, 'MULTIPLY', bx - 3000, by + 4250, run_u.outputs[0], US)
    roof_h = mathn(tree, 'ADD', bx - 3000, by + 4100, h_l.outputs[0],
                   h_u.outputs[0])
    ang_l = mathn(tree, 'ARCTANGENT', bx - 3000, by + 3950, LS)
    ang_u = mathn(tree, 'ARCTANGENT', bx - 3000, by + 3800, US)
    # panel lengths = sqrt(run^2 + rise^2)
    len_l = mathn(tree, 'SQRT', bx - 3000, by + 3650,
                  mathn(tree, 'ADD', bx - 3000, by + 3500,
                        mathn(tree, 'MULTIPLY', bx - 3000, by + 3350,
                              run_l.outputs[0], run_l.outputs[0]).outputs[0],
                        mathn(tree, 'MULTIPLY', bx - 3000, by + 3200,
                              h_l.outputs[0], h_l.outputs[0]).outputs[0]).outputs[0])
    len_u = mathn(tree, 'SQRT', bx - 3000, by + 3050,
                  mathn(tree, 'ADD', bx - 3000, by + 2900,
                        mathn(tree, 'MULTIPLY', bx - 3000, by + 2750,
                              run_u.outputs[0], run_u.outputs[0]).outputs[0],
                        mathn(tree, 'MULTIPLY', bx - 3000, by + 2600,
                              h_u.outputs[0], h_u.outputs[0]).outputs[0]).outputs[0])
    len_l_x = mathn(tree, 'ADD', bx - 3000, by + 2450, len_l.outputs[0], 0.08)
    len_u_x = mathn(tree, 'ADD', bx - 3000, by + 2300, len_u.outputs[0], 0.08)

    # ---- the four slope panels (front/back x lower/upper) ----------------
    # front eave at y=-D/2, ridge at y=0, back eave at +D/2.
    neg_half = mathn(tree, 'MULTIPLY', bx - 3000, by + 2150, half_d.outputs[0], -1.0)
    fl_y = mathn(tree, 'ADD', bx - 3000, by + 2000, neg_half.outputs[0],
                 mathn(tree, 'MULTIPLY', bx - 3000, by + 1850,
                       run_l.outputs[0], 0.5).outputs[0])
    fl_z = mathn(tree, 'MULTIPLY', bx - 3000, by + 1700, h_l.outputs[0], 0.5)
    fu_y = mathn(tree, 'ADD', bx - 3000, by + 1550, neg_half.outputs[0],
                 mathn(tree, 'ADD', bx - 3000, by + 1400, run_l.outputs[0],
                       mathn(tree, 'MULTIPLY', bx - 3000, by + 1250,
                             run_u.outputs[0], 0.5).outputs[0]).outputs[0])
    fu_z = mathn(tree, 'ADD', bx - 3000, by + 1100, h_l.outputs[0],
                 mathn(tree, 'MULTIPLY', bx - 3000, by + 950,
                       h_u.outputs[0], 0.5).outputs[0])
    bl_y = mathn(tree, 'SUBTRACT', bx - 3000, by + 800, half_d.outputs[0],
                 mathn(tree, 'MULTIPLY', bx - 3000, by + 650,
                       run_l.outputs[0], 0.5).outputs[0])
    bu_y = mathn(tree, 'SUBTRACT', bx - 3000, by + 500, half_d.outputs[0],
                 mathn(tree, 'ADD', bx - 3000, by + 350, run_l.outputs[0],
                       mathn(tree, 'MULTIPLY', bx - 3000, by + 200,
                             run_u.outputs[0], 0.5).outputs[0]).outputs[0])

    panels = []
    for pi, (py, pz, ang, ln, sgn) in enumerate((
            (fl_y, fl_z, ang_l, len_l_x, 1.0),
            (fu_y, fu_z, ang_u, len_u_x, 1.0),
            (bl_y, fl_z, ang_l, len_l_x, -1.0),
            (bu_y, fu_z, ang_u, len_u_x, -1.0))):
        rot = mathn(tree, 'MULTIPLY', bx - 3000 + pi * 10, by - 900,
                    ang.outputs[0], sgn)
        rot_v = combine(tree, bx - 2800, by - 900, rot.outputs[0], 0.0, 0.0)
        slab = cube_s(tree, bx - 2600, by - 900, W, ln.outputs[0], 0.10)
        slab_x = xform(tree, bx - 2400, by - 900, slab,
                       trans=combine(tree, bx - 2600, by - 1050, 0.0,
                                     py.outputs[0], pz.outputs[0]).outputs['Vector'],
                       rot=rot_v.outputs['Vector'])
        panels.append(slab_x)
        # side cap: the same profile as a thin end wall, at x = +/- (W/2 - 0.05)
        cap = cube_s(tree, bx - 2600, by - 1200, 0.10, ln.outputs[0], 0.14)
        for side, sx in (("a", -1.0), ("b", 1.0)):
            cap_dx = mathn(tree, 'MULTIPLY', bx - 2600, by - 1350 - pi * 10,
                           W, 0.45 * sx)
            cap_tr = combine(tree, bx - 2600, by - 1500 - pi * 10,
                             cap_dx.outputs[0], py.outputs[0], pz.outputs[0])
            cap_x = xform(tree, bx - 2400, by - 1200, cap,
                          trans=cap_tr.outputs['Vector'],
                          rot=rot_v.outputs['Vector'])
            panels.append(cap_x)

    # ---- eave lip + ridge cap -------------------------------------------
    lip_w = mathn(tree, 'ADD', bx - 3000, by - 1800, W, 0.12)
    lip_d = mathn(tree, 'ADD', bx - 3000, by - 1950, D, 0.12)
    lip = cube_s(tree, bx - 3000, by - 2100, lip_w.outputs[0], lip_d.outputs[0],
                 LIP)
    lip_z = mathn(tree, 'MULTIPLY', bx - 3000, by - 2250, LIP, -0.5)
    lip_x = xform(tree, bx - 2800, by - 2100, lip,
                  trans=combine(tree, bx - 2800, by - 2250, 0.0, 0.0,
                                lip_z.outputs[0]).outputs['Vector'])
    ridge_w = mathn(tree, 'ADD', bx - 3000, by - 2400, W, 0.06)
    ridge = cube_s(tree, bx - 3000, by - 2550, ridge_w.outputs[0], 0.18, 0.08)
    ridge_z = mathn(tree, 'ADD', bx - 3000, by - 2700, roof_h.outputs[0], 0.02)
    ridge_x = xform(tree, bx - 2800, by - 2550, ridge,
                    trans=combine(tree, bx - 2800, by - 2700, 0.0, 0.0,
                                  ridge_z.outputs[0]).outputs['Vector'])

    # ---- zinc seam ribs on both lower slopes -----------------------------
    # The rib template is ROTATED about its own origin first, then instanced
    # along a line and translated onto the slope (rotating a realized stream
    # would swing the whole row around the world origin).
    rib_h = mathn(tree, 'MULTIPLY', bx - 3000, by - 2850,
                  gin.outputs['Rib Size'], 8.0)
    rib_tpl = cube_s(tree, bx - 3000, by - 3000, gin.outputs['Rib Size'],
                     mathn(tree, 'ADD', bx - 3000, by - 3150,
                           len_l.outputs[0], 0.10).outputs[0],
                     rib_h.outputs[0])
    ribs = []
    for ri, (py, pz, sgn) in enumerate(((fl_y, fl_z, 1.0), (bl_y, fl_z, -1.0))):
        rib_rot = mathn(tree, 'MULTIPLY', bx - 3000, by - 3300 - ri * 10,
                        ang_l.outputs[0], sgn)
        rib_tpl_r = xform(tree, bx - 2800, by - 3300 - ri * 10, rib_tpl,
                          rot=combine(tree, bx - 2900, by - 3300 - ri * 10,
                                      rib_rot.outputs[0], 0.0,
                                      0.0).outputs['Vector'])
        rib_line = N(tree, 'GeometryNodeMeshLine', bx - 2600, by - 3300 - ri * 10)
        try:
            rib_line.mode = 'OFFSET'
        except Exception:
            pass
        L(tree, gin, 'Zinc Ribs', rib_line, 'Count')
        rib_pitch = mathn(tree, 'DIVIDE', bx - 3000, by - 3450 - ri * 10, W,
                          mathn(tree, 'ADD', bx - 3000, by - 3600 - ri * 10,
                                gin.outputs['Zinc Ribs'], 1.0).outputs[0])
        rib_off = combine(tree, bx - 2600, by - 3450 - ri * 10,
                          rib_pitch.outputs[0], 0.0, 0.0)
        L(tree, rib_off, 'Vector', rib_line, 'Offset')
        rib_so = combine(tree, bx - 2600, by - 3600 - ri * 10,
                         mathn(tree, 'MULTIPLY', bx - 3000, by - 3750 - ri * 10,
                               W, -0.5).outputs[0], 0.0, 0.0)
        L(tree, rib_so, 'Vector', rib_line, 'Start Location')
        rib_tr = combine(tree, bx - 2600, by - 3900 - ri * 10, 0.0,
                         py.outputs[0], pz.outputs[0])
        rib_real = inst_realize(tree, bx - 2200, by - 3300 - ri * 10, rib_line,
                                rib_tpl_r, sname='Geometry',
                                trans=rib_tr.outputs['Vector'])
        ribs.append(rib_real)

    # ---- dormers on the front lower slope --------------------------------
    # The dormer sits ON the slope: z_base up the lower panel, y = y_slope(z).
    z_base = mathn(tree, 'MULTIPLY', bx - 3000, by - 4200, h_l.outputs[0], 0.35)
    y_slope = mathn(tree, 'ADD', bx - 3000, by - 4350, neg_half.outputs[0],
                    mathn(tree, 'DIVIDE', bx - 3000, by - 4500,
                          z_base.outputs[0], LS).outputs[0])
    y_dorm = mathn(tree, 'SUBTRACT', bx - 3000, by - 4800, y_slope.outputs[0],
                   0.15)
    z_dorm = mathn(tree, 'ADD', bx - 3000, by - 4950, z_base.outputs[0],
                   mathn(tree, 'MULTIPLY', bx - 3000, by - 5100,
                         DORH, 0.5).outputs[0])

    body = cube_s(tree, bx - 2600, by - 4200, DORW, 0.50, DORH)
    # rect window + frame
    win_w = mathn(tree, 'MULTIPLY', bx - 3000, by - 5250, DORW, 0.55)
    win_h = mathn(tree, 'MULTIPLY', bx - 3000, by - 5400, DORH, 0.50)
    win = cube_s(tree, bx - 2600, by - 5250, win_w.outputs[0], 0.08,
                 win_h.outputs[0])
    win_x = xform(tree, bx - 2400, by - 5250, win, trans=(0.0, -0.28, 0.0))
    frame_w = mathn(tree, 'MULTIPLY', bx - 3000, by - 5550, DORW, 0.68)
    frame_h = mathn(tree, 'MULTIPLY', bx - 3000, by - 5700, DORH, 0.62)
    frame = cube_s(tree, bx - 2600, by - 5550, frame_w.outputs[0], 0.10,
                   frame_h.outputs[0])
    frame_x = xform(tree, bx - 2400, by - 5550, frame, trans=(0.0, -0.26, 0.0))
    rect_join = N(tree, 'GeometryNodeJoinGeometry', bx - 2200, by - 5250)
    L(tree, win_x, 'Geometry', rect_join, 'Geometry')
    L(tree, frame_x, 'Geometry', rect_join, 'Geometry')
    # oculus window (disc facing the street)
    oc_r = mathn(tree, 'MULTIPLY', bx - 3000, by - 5850, DORW, 0.30)
    oc = cyl(tree, bx - 2600, by - 5850, oc_r.outputs[0], 0.08, 20)
    oc_x = xform(tree, bx - 2400, by - 5850, oc, trans=(0.0, -0.28, 0.05),
                 rot=(HALF_PI, 0.0, 0.0))
    oc_g = guard_off(tree, bx - 2200, by - 5850,
                     gin.outputs['Oculus Dormers'], oc_x)
    rect_g = guard_off(tree, bx - 2000, by - 5250,
                       gin.outputs['Oculus Dormers'], rect_join)
    # gabled roof: two panels rotated about Y
    g_ang = 0.62
    g_len = mathn(tree, 'DIVIDE', bx - 3000, by - 6000,
                  mathn(tree, 'MULTIPLY', bx - 3000, by - 6150,
                        DORW, 0.55).outputs[0], math.cos(g_ang))
    g_z = mathn(tree, 'ADD', bx - 3000, by - 6300,
                mathn(tree, 'MULTIPLY', bx - 3000, by - 6450,
                      DORH, 0.5).outputs[0], 0.10)
    g_off = mathn(tree, 'MULTIPLY', bx - 3000, by - 6600, DORW, 0.25)
    gables = []
    for gs in (-1.0, 1.0):
        gp = cube_s(tree, bx - 2600, by - 6000, g_len.outputs[0], 0.55, 0.06)
        g_dx = mathn(tree, 'MULTIPLY', bx - 3000, by - 6750,
                     g_off.outputs[0], gs)
        gp_x = xform(tree, bx - 2400, by - 6000, gp,
                     trans=combine(tree, bx - 2600, by - 6750,
                                   g_dx.outputs[0], 0.0, g_z.outputs[0]).outputs['Vector'],
                     rot=(0.0, g_ang * gs, 0.0))
        gables.append(gp_x)
    dorm_join = N(tree, 'GeometryNodeJoinGeometry', bx - 2000, by - 4500)
    for node in (body, oc_g, rect_g, gables[0], gables[1]):
        L(tree, node, out_name(node, 'Geometry', 'Mesh'), dorm_join, 'Geometry')
    dorm_line = N(tree, 'GeometryNodeMeshLine', bx - 1800, by - 4500)
    try:
        dorm_line.mode = 'OFFSET'
    except Exception:
        pass
    L(tree, gin, 'Dormers', dorm_line, 'Count')
    dorm_span = mathn(tree, 'SUBTRACT', bx - 3000, by - 6900, W, 1.2)
    dorm_pitch = mathn(tree, 'DIVIDE', bx - 3000, by - 7050, dorm_span.outputs[0],
                       mathn(tree, 'MAXIMUM', bx - 3000, by - 7200,
                             gin.outputs['Dormers'], 1.0).outputs[0])
    dorm_off = combine(tree, bx - 1800, by - 7050, dorm_pitch.outputs[0], 0.0, 0.0)
    L(tree, dorm_off, 'Vector', dorm_line, 'Offset')
    dorm_so = combine(tree, bx - 1800, by - 7200,
                      mathn(tree, 'ADD', bx - 3000, by - 7350,
                            mathn(tree, 'MULTIPLY', bx - 3000, by - 7500,
                                  dorm_span.outputs[0], -0.5).outputs[0],
                            mathn(tree, 'MULTIPLY', bx - 3000, by - 7650,
                                  dorm_pitch.outputs[0], 0.5).outputs[0]).outputs[0],
                      0.0, 0.0)
    L(tree, dorm_so, 'Vector', dorm_line, 'Start Location')
    dorm_tr = combine(tree, bx - 1800, by - 7800, 0.0, y_dorm.outputs[0],
                      z_dorm.outputs[0])
    dorm_real = inst_realize(tree, bx - 1400, by - 4500, dorm_line, dorm_join,
                             sname='Geometry', trans=dorm_tr.outputs['Vector'])

    # ---- chimney stacks with pots ----------------------------------------
    stack = cube_s(tree, bx + 1400, by - 4200, 0.55, 0.55, gin.outputs['Chimney Height'])
    cap = cube_s(tree, bx + 1400, by - 4350, 0.65, 0.65, 0.08)
    cap_z = mathn(tree, 'MULTIPLY', bx + 1200, by - 4500,
                  gin.outputs['Chimney Height'], 0.5)
    cap_x = xform(tree, bx + 1600, by - 4350, cap,
                  trans=combine(tree, bx + 1400, by - 4500, 0.0, 0.0,
                                cap_z.outputs[0]).outputs['Vector'])
    pot_tpl = cyl(tree, bx + 1400, by - 4650, 0.09, 0.34, 10)
    pot_line = N(tree, 'GeometryNodeMeshLine', bx + 1400, by - 4800)
    try:
        pot_line.mode = 'OFFSET'
    except Exception:
        pass
    L(tree, gin, 'Chimney Pots', pot_line, 'Count')
    pot_pitch = 0.17
    pot_off = combine(tree, bx + 1400, by - 4950, pot_pitch, 0.0, 0.0)
    L(tree, pot_off, 'Vector', pot_line, 'Offset')
    pot_so = combine(tree, bx + 1400, by - 5100,
                     mathn(tree, 'MULTIPLY', bx + 1200, by - 5250,
                           gin.outputs['Chimney Pots'], -0.5 * pot_pitch).outputs[0],
                     0.0, 0.0)
    L(tree, pot_so, 'Vector', pot_line, 'Start Location')
    pot_z = mathn(tree, 'ADD', bx + 1200, by - 5400, cap_z.outputs[0], 0.21)
    pot_tr = combine(tree, bx + 1400, by - 5550, 0.0, 0.0, pot_z.outputs[0])
    pot_real = inst_realize(tree, bx + 1800, by - 4800, pot_line, pot_tpl,
                            trans=pot_tr.outputs['Vector'])
    chim_join = N(tree, 'GeometryNodeJoinGeometry', bx + 2200, by - 4500)
    for node in (stack, cap_x, pot_real):
        L(tree, node, out_name(node, 'Geometry', 'Mesh'), chim_join, 'Geometry')
    chim_line = N(tree, 'GeometryNodeMeshLine', bx + 2400, by - 4500)
    try:
        chim_line.mode = 'OFFSET'
    except Exception:
        pass
    L(tree, gin, 'Chimneys', chim_line, 'Count')
    chim_pitch = mathn(tree, 'DIVIDE', bx + 1200, by - 5700,
                       mathn(tree, 'MULTIPLY', bx + 1200, by - 5850,
                             W, 0.55).outputs[0],
                       mathn(tree, 'MAXIMUM', bx + 1200, by - 6000,
                             gin.outputs['Chimneys'], 1.0).outputs[0])
    chim_off = combine(tree, bx + 2400, by - 5700, chim_pitch.outputs[0], 0.0, 0.0)
    L(tree, chim_off, 'Vector', chim_line, 'Offset')
    chim_so = combine(tree, bx + 2400, by - 5850,
                      mathn(tree, 'MULTIPLY', bx + 1200, by - 6150,
                            chim_pitch.outputs[0], -0.5).outputs[0], 0.0, 0.0)
    L(tree, chim_so, 'Vector', chim_line, 'Start Location')
    chim_z = mathn(tree, 'SUBTRACT', bx + 1200, by - 6300,
                   mathn(tree, 'ADD', bx + 1200, by - 6450, roof_h.outputs[0],
                         mathn(tree, 'MULTIPLY', bx + 1200, by - 6600,
                               gin.outputs['Chimney Height'], 0.5).outputs[0]).outputs[0],
                   0.45)
    chim_tr = combine(tree, bx + 2400, by - 6600, 0.0, 0.15, chim_z.outputs[0])
    chim_real = inst_realize(tree, bx + 2800, by - 4500, chim_line, chim_join,
                             sname='Geometry', trans=chim_tr.outputs['Vector'])

    # ---- iron cresting along the ridge -----------------------------------
    crest_tpl_join = N(tree, 'GeometryNodeJoinGeometry', bx + 1400, by + 0)
    c_mid = cube_s(tree, bx + 1400, by - 150, 0.025, 0.035, 0.24)
    c_mid_x = xform(tree, bx + 1600, by - 150, c_mid, trans=(0.0, 0.0, 0.12))
    L(tree, c_mid_x, 'Geometry', crest_tpl_join, 'Geometry')
    for cs in (-1.0, 1.0):
        c_wing = cube_s(tree, bx + 1400, by - 300 - (cs + 1) * 200,
                        0.025, 0.035, 0.18)
        c_wing_x = xform(tree, bx + 1600, by - 300 - (cs + 1) * 200, c_wing,
                         trans=(0.07 * cs, 0.0, 0.07),
                         rot=(0.0, 0.75 * cs, 0.0))
        L(tree, c_wing_x, 'Geometry', crest_tpl_join, 'Geometry')
    crest_line = N(tree, 'GeometryNodeMeshLine', bx + 2400, by + 0)
    try:
        crest_line.mode = 'OFFSET'
    except Exception:
        pass
    L(tree, gin, 'Cresting', crest_line, 'Count')
    crest_span = mathn(tree, 'SUBTRACT', bx + 1200, by + 150, W, 0.4)
    crest_pitch = mathn(tree, 'DIVIDE', bx + 1200, by + 300, crest_span.outputs[0],
                        mathn(tree, 'MAXIMUM', bx + 1200, by + 450,
                              gin.outputs['Cresting'], 1.0).outputs[0])
    crest_off = combine(tree, bx + 2400, by + 300, crest_pitch.outputs[0], 0.0, 0.0)
    L(tree, crest_off, 'Vector', crest_line, 'Offset')
    crest_so = combine(tree, bx + 2400, by + 150,
                       mathn(tree, 'ADD', bx + 1200, by + 600,
                             mathn(tree, 'MULTIPLY', bx + 1200, by + 750,
                                   crest_span.outputs[0], -0.5).outputs[0],
                             mathn(tree, 'MULTIPLY', bx + 1200, by + 900,
                                   crest_pitch.outputs[0], 0.5).outputs[0]).outputs[0],
                       0.0, 0.0)
    L(tree, crest_so, 'Vector', crest_line, 'Start Location')
    crest_z = mathn(tree, 'ADD', bx + 1200, by + 1050, roof_h.outputs[0], 0.06)
    crest_tr = combine(tree, bx + 2400, by + 1050, 0.0, 0.0, crest_z.outputs[0])
    crest_real = inst_realize(tree, bx + 2800, by + 0, crest_line,
                              crest_tpl_join, sname='Geometry',
                              trans=crest_tr.outputs['Vector'])
    crest_g = guard_off(tree, bx + 3000, by + 0, gin.outputs['Iron Cresting'],
                        crest_real)

    # ---- join ------------------------------------------------------------
    j1 = N(tree, 'GeometryNodeJoinGeometry', bx + 4200, by + 4000)
    for node in (lip_x, ridge_x):
        L(tree, node, 'Geometry', j1, 'Geometry')
    for node in panels:
        L(tree, node, 'Geometry', j1, 'Geometry')
    for node in ribs:
        L(tree, node, 'Geometry', j1, 'Geometry')
    j2 = N(tree, 'GeometryNodeJoinGeometry', bx + 4400, by + 3800)
    for node in (j1, dorm_real, chim_real, crest_g):
        L(tree, node, 'Geometry', j2, 'Geometry')
    L(tree, j2, 'Geometry', gout, 'Geometry')

    return tree, gin, gout


# ------------------------------------------------- addon registration

try:
    from .core import register_builder  # noqa: E402
    register_builder(
        'GN_PARIS_Mansard', build_paris_mansard,
        'PARIS Mansard',
        'Haussmann mansard roof band: two-slope profile (Break Point + both '
        'slopes), zinc seam ribs, gabled or oculus dormers, chimney stacks '
        'with pots, iron cresting. Roof height is derived - eaves cannot '
        'float.',
        category='escher',
    )
    print('[paris_mansard] registered GN_PARIS_Mansard')
except ImportError:
    print('[paris_mansard] standalone mode (no core registry)')


if __name__ == '__main__':
    build_paris_mansard()
