"""Brutalist cubicle farm - the open plan as a maze of half-walls.

GN_BRUTALIST_CubicleFarm (build_brutalist_cubicle_farm)

The office block's interior system: a grid of cubicles under a waffle
ceiling.  Each cell is a back wall + one desk + (optionally) a monitor, a
chair and an overhead bin; partitions are shared - the left wall of every
cell plus one closing wall at the right edge, so no doubled panels anywhere.

Dials that matter:
  * Rows / Columns - the grid.  Rows are built as reusable row templates and
    guarded by index (the slots pattern): dialing Rows down to 2 leaves no
    hidden geometry behind, it deletes the extra rows;
  * Drift - each row slides sideways by row x Drift x cell width.  At 0 the
    grid is a corporate lattice; pushed up the cubicle maze shears into the
    Escher read without ever rebuilding;
  * Ceiling Grid - waffle beams + light strips + ceiling slab, deletable.

Front face is -Y (the occupant faces out of the cell, toward the viewer).
"""

from __future__ import annotations

from .core import (new_geometry_tree, add_float_param, add_int_param,
                   add_bool_param)
from .paris_common import (
    N, L, mathn, combine, xform, cyl, sphere, cube_s, inst_realize, guard_off,
    out_name, gn_line,
)

ROWS_MAX = 8


def build_brutalist_cubicle_farm(group_name="GN_BRUTALIST_CubicleFarm"):
    tree, gin, gout = new_geometry_tree(group_name)

    # ---- dials -----------------------------------------------------------
    ROWS = add_int_param(tree, "Rows", 3, 1, ROWS_MAX)
    COLS = add_int_param(tree, "Columns", 4, 1, 12)
    CW = add_float_param(tree, "Cell Width", 2.4, 1.4, 4.0)
    CD = add_float_param(tree, "Cell Depth", 2.0, 1.2, 3.5)
    PH = add_float_param(tree, "Partition Height", 1.65, 1.0, 2.4)
    PT = add_float_param(tree, "Partition Thickness", 0.06, 0.02, 0.2)
    DH = add_float_param(tree, "Desk Height", 0.74, 0.6, 0.95)
    DD = add_float_param(tree, "Desk Depth", 0.6, 0.4, 1.0)
    MON = add_bool_param(tree, "Monitor", True)
    MS = add_float_param(tree, "Monitor Size", 0.5, 0.2, 0.8)
    CHAIR = add_bool_param(tree, "Chair", True)
    BIN = add_bool_param(tree, "Overhead Bin", True)
    DRIFT = add_float_param(tree, "Drift", 0.0, 0.0, 1.0)
    CEIL = add_bool_param(tree, "Ceiling Grid", True)
    BEAMS = add_int_param(tree, "Grid Beams", 8, 2, 20)
    CH = add_float_param(tree, "Ceiling Height", 2.9, 2.4, 4.5)
    LIGHTS = add_int_param(tree, "Lights", 8, 0, 24)
    PLANTS = add_int_param(tree, "Plants", 3, 0, 10)

    bx, by = -3000, 0
    g = gin.outputs

    # ---- derived ---------------------------------------------------------
    w_tot = mathn(tree, 'MULTIPLY', bx, by - 100, CW, g['Columns'])
    d_tot = mathn(tree, 'MULTIPLY', bx, by - 300, CD, g['Rows'])
    half_w = mathn(tree, 'MULTIPLY', bx, by - 500, w_tot.outputs[0], -0.5)
    half_d = mathn(tree, 'MULTIPLY', bx, by - 700, d_tot.outputs[0], -0.5)
    cell_x = mathn(tree, 'ADD', bx, by - 900, half_w.outputs[0],
                   mathn(tree, 'MULTIPLY', bx - 200, by - 900, CW,
                         0.5).outputs[0])                      # first cell centre
    desk_y = mathn(tree, 'SUBTRACT', bx, by - 1100,
                   mathn(tree, 'SUBTRACT', bx - 200, by - 1100,
                         mathn(tree, 'MULTIPLY', bx - 400, by - 1100, CD,
                               0.5).outputs[0], PT).outputs[0],
                   mathn(tree, 'MULTIPLY', bx - 600, by - 1100, DD,
                         0.5).outputs[0])                      # desk centre y
    drift_unit = mathn(tree, 'MULTIPLY', bx, by - 1300, DRIFT, CW)
    n_cols_p1 = mathn(tree, 'ADD', bx, by - 1500, g['Columns'], 1)

    parts = []

    # ---- row template ----------------------------------------------------
    row_line = gn_line(tree, gin, bx + 600, by - 1800, n_cols_p1,
                       combine(tree, bx + 450, by - 1950,
                               half_w.outputs[0], 0.0, 0.0),
                       combine(tree, bx + 450, by - 2100, CW, 0.0, 0.0))
    wall_tpl = cube_s(tree, bx + 600, by - 2300, PT, CD, PH)
    wall_real = inst_realize(
        tree, bx + 1000, by - 1800, row_line, wall_tpl,
        sname=out_name(wall_tpl, 'Mesh', 'Geometry'),
        trans=combine(tree, bx + 850, by - 1950, 0.0, 0.0,
                      mathn(tree, 'MULTIPLY', bx + 700, by - 1950, PH,
                            0.5).outputs[0]))

    cell_line = gn_line(tree, gin, bx + 600, by - 2600, g['Columns'],
                        combine(tree, bx + 450, by - 2750, cell_x.outputs[0],
                                0.0, 0.0),
                        combine(tree, bx + 450, by - 2900, CW, 0.0, 0.0))
    back_tpl = cube_s(tree, bx + 600, by - 3100, CW, PT, PH)
    back_real = inst_realize(
        tree, bx + 1000, by - 2600, cell_line, back_tpl,
        sname=out_name(back_tpl, 'Mesh', 'Geometry'),
        trans=combine(tree, bx + 850, by - 2750, 0.0,
                      mathn(tree, 'SUBTRACT', bx + 700, by - 2750,
                            mathn(tree, 'MULTIPLY', bx + 500, by - 2750,
                                  CD, 0.5).outputs[0],
                            mathn(tree, 'MULTIPLY', bx + 300, by - 2750,
                                  PT, 0.5).outputs[0]).outputs[0],
                      mathn(tree, 'MULTIPLY', bx + 300, by - 2900, PH,
                            0.5).outputs[0]))

    desk_top = cube_s(tree, bx + 600, by - 3400,
                      mathn(tree, 'SUBTRACT', bx + 800, by - 3400, CW, 0.30),
                      DD, 0.05)
    desk_top_tr = xform(tree, bx + 850, by - 3400, desk_top,
                        sname=out_name(desk_top, 'Mesh', 'Geometry'),
                        trans=combine(tree, bx + 700, by - 3550, 0.0, 0.0, DH))
    desk_ped = cube_s(tree, bx + 600, by - 3700,
                      mathn(tree, 'SUBTRACT', bx + 800, by - 3700, CW, 0.70),
                      mathn(tree, 'SUBTRACT', bx + 800, by - 3800, DD, 0.15),
                      DH)
    desk_ped_tr = xform(tree, bx + 850, by - 3700, desk_ped,
                        sname=out_name(desk_ped, 'Mesh', 'Geometry'),
                        trans=combine(tree, bx + 700, by - 3850, 0.0, 0.0,
                                      mathn(tree, 'MULTIPLY', bx + 550,
                                            by - 3850, DH, 0.5).outputs[0]))
    desk_tpl = N(tree, 'GeometryNodeJoinGeometry', bx + 1100, by - 3400)
    for node in (desk_top_tr, desk_ped_tr):
        L(tree, node, out_name(node, 'Geometry', 'Mesh'), desk_tpl, 'Geometry')
    desk_real = inst_realize(tree, bx + 1400, by - 2600, cell_line, desk_tpl,
                             sname='Geometry',
                             trans=combine(tree, bx + 1250, by - 2750, 0.0,
                                           desk_y.outputs[0], 0.0))

    # monitor: panel + base, sitting on the desk against the back wall
    mon_panel = cube_s(tree, bx + 600, by - 4200,
                       mathn(tree, 'MULTIPLY', bx + 800, by - 4200, MS, 0.55),
                       0.06,
                       mathn(tree, 'MULTIPLY', bx + 800, by - 4300, MS, 0.36))
    mon_panel_tr = xform(
        tree, bx + 850, by - 4200, mon_panel,
        sname=out_name(mon_panel, 'Mesh', 'Geometry'),
        trans=combine(tree, bx + 700, by - 4350, 0.0, 0.0,
                      mathn(tree, 'ADD', bx + 550, by - 4350, DH,
                            mathn(tree, 'MULTIPLY', bx + 400, by - 4350,
                                  MS, 0.20).outputs[0]).outputs[0]))
    mon_base = cube_s(tree, bx + 600, by - 4600,
                      mathn(tree, 'MULTIPLY', bx + 800, by - 4600, MS, 0.18),
                      mathn(tree, 'MULTIPLY', bx + 800, by - 4700, MS, 0.16),
                      0.035)
    mon_base_tr = xform(tree, bx + 850, by - 4600, mon_base,
                        sname=out_name(mon_base, 'Mesh', 'Geometry'),
                        trans=combine(tree, bx + 700, by - 4750, 0.0, 0.0,
                                      mathn(tree, 'ADD', bx + 550, by - 4750,
                                            DH, 0.02).outputs[0]))
    mon_tpl = N(tree, 'GeometryNodeJoinGeometry', bx + 1100, by - 4200)
    for node in (mon_panel_tr, mon_base_tr):
        L(tree, node, out_name(node, 'Geometry', 'Mesh'), mon_tpl, 'Geometry')
    mon_real = inst_realize(
        tree, bx + 1400, by - 4200, cell_line, mon_tpl, sname='Geometry',
        trans=combine(tree, bx + 1250, by - 4350, 0.0,
                      mathn(tree, 'SUBTRACT', bx + 1100, by - 4350,
                            mathn(tree, 'SUBTRACT', bx + 900, by - 4350,
                                  mathn(tree, 'MULTIPLY', bx + 700,
                                        by - 4350, CD, 0.5).outputs[0],
                                  PT).outputs[0],
                            0.14).outputs[0],
                      0.0))
    mon_g = guard_off(tree, bx + 1700, by - 4200, MON, mon_real)

    # chair: seat + back + post + base, in front of the desk
    seat = cube_s(tree, bx + 600, by - 5000, 0.42, 0.42, 0.06)
    seat_tr = xform(tree, bx + 850, by - 5000, seat,
                    sname=out_name(seat, 'Mesh', 'Geometry'),
                    trans=combine(tree, bx + 700, by - 5150, 0.0, 0.0, 0.45))
    back = cube_s(tree, bx + 600, by - 5300, 0.42, 0.06, 0.50)
    back_tr = xform(tree, bx + 850, by - 5300, back,
                    sname=out_name(back, 'Mesh', 'Geometry'),
                    trans=combine(tree, bx + 700, by - 5450, 0.0, -0.18, 0.72))
    post = cyl(tree, bx + 600, by - 5600, 0.05, 0.42)
    post_tr = xform(tree, bx + 850, by - 5600, post,
                    sname=out_name(post, 'Mesh', 'Geometry'),
                    trans=combine(tree, bx + 700, by - 5750, 0.0, 0.0, 0.21))
    cbase = cube_s(tree, bx + 600, by - 5900, 0.40, 0.40, 0.04)
    cbase_tr = xform(tree, bx + 850, by - 5900, cbase,
                     sname=out_name(cbase, 'Mesh', 'Geometry'),
                     trans=combine(tree, bx + 700, by - 6050, 0.0, 0.0, 0.02))
    chair_tpl = N(tree, 'GeometryNodeJoinGeometry', bx + 1100, by - 5300)
    for node in (seat_tr, back_tr, post_tr, cbase_tr):
        L(tree, node, out_name(node, 'Geometry', 'Mesh'), chair_tpl,
          'Geometry')
    chair_real = inst_realize(
        tree, bx + 1400, by - 5000, cell_line, chair_tpl, sname='Geometry',
        trans=combine(tree, bx + 1250, by - 5150, 0.0,
                      mathn(tree, 'SUBTRACT', bx + 1100, by - 5150,
                            desk_y.outputs[0],
                            mathn(tree, 'SUBTRACT', bx + 900, by - 5150,
                                  mathn(tree, 'MULTIPLY', bx + 700,
                                        by - 5150, DD, 0.5).outputs[0],
                                  0.35).outputs[0]).outputs[0],
                      0.0))
    chair_g = guard_off(tree, bx + 1700, by - 5000, CHAIR, chair_real)

    # overhead bin above the back wall
    bin_box = cube_s(tree, bx + 600, by - 6400,
                     mathn(tree, 'SUBTRACT', bx + 800, by - 6400, CW, 0.25),
                     0.35, 0.40)
    bin_tr = xform(tree, bx + 850, by - 6400, bin_box,
                   sname=out_name(bin_box, 'Mesh', 'Geometry'),
                   trans=combine(tree, bx + 700, by - 6550, 0.0,
                                 mathn(tree, 'SUBTRACT', bx + 500, by - 6550,
                                       mathn(tree, 'MULTIPLY', bx + 300,
                                             by - 6550, CD, 0.5).outputs[0],
                                       0.20).outputs[0],
                                 mathn(tree, 'ADD', bx + 500, by - 6700, PH,
                                       0.22).outputs[0]))
    bin_g = guard_off(tree, bx + 1700, by - 6400, BIN, bin_tr)

    row_tpl = N(tree, 'GeometryNodeJoinGeometry', bx + 2000, by - 3000)
    for node in (wall_real, back_real, desk_real, mon_g, chair_g, bin_g):
        L(tree, node, out_name(node, 'Geometry', 'Mesh'), row_tpl, 'Geometry')

    # ---- rows: guarded instances of the row template ---------------------
    for r in range(ROWS_MAX):
        keep = mathn(tree, 'LESS_THAN', bx + 2300, by - 3400 - r * 40,
                     float(r), g['Rows'])
        one = gn_line(tree, gin, bx + 2500, by - 3400 - r * 40, 1,
                      combine(tree, bx + 2350, by - 3550 - r * 40, 0.0, 0.0,
                              0.0),
                      combine(tree, bx + 2350, by - 3700 - r * 40, 0.0, 0.0,
                              0.0))
        row_tr = combine(
            tree, bx + 2500, by - 3400 - r * 40,
            mathn(tree, 'MULTIPLY', bx + 2300, by - 3550 - r * 40,
                  drift_unit.outputs[0], float(r)).outputs[0],
            mathn(tree, 'SUBTRACT', bx + 2300, by - 3700 - r * 40,
                  mathn(tree, 'MULTIPLY', bx + 2100, by - 3700 - r * 40,
                        CD, float(r) + 0.5).outputs[0],
                  mathn(tree, 'MULTIPLY', bx + 1900, by - 3700 - r * 40,
                        d_tot.outputs[0], 0.5).outputs[0]).outputs[0],
            0.0)
        real = inst_realize(tree, bx + 2800, by - 3400 - r * 40, one, row_tpl,
                            sname='Geometry', trans=row_tr)
        parts.append(guard_off(tree, bx + 3100, by - 3400 - r * 40, keep, real))

    # ---- ceiling grid + lights (one guard) --------------------------------
    beam_x_line = gn_line(
        tree, gin, bx + 3400, by - 4200, g['Grid Beams'],
        combine(tree, bx + 3250, by - 4350, 0.0, half_d.outputs[0], 0.0),
        combine(tree, bx + 3250, by - 4500, 0.0,
                mathn(tree, 'DIVIDE', bx + 3050, by - 4500,
                      d_tot.outputs[0], g['Grid Beams']).outputs[0], 0.0))
    beam_x_tpl = cube_s(tree, bx + 3400, by - 4700, w_tot.outputs[0], 0.22, 0.4)
    beam_x = inst_realize(
        tree, bx + 3800, by - 4200, beam_x_line, beam_x_tpl,
        sname=out_name(beam_x_tpl, 'Mesh', 'Geometry'),
        trans=combine(tree, bx + 3650, by - 4350, 0.0, 0.0,
                      mathn(tree, 'SUBTRACT', bx + 3450, by - 4350, CH,
                            0.2).outputs[0]))
    beam_y_line = gn_line(
        tree, gin, bx + 3400, by - 5000, g['Grid Beams'],
        combine(tree, bx + 3250, by - 5150, half_w.outputs[0], 0.0, 0.0),
        combine(tree, bx + 3250, by - 5300,
                mathn(tree, 'DIVIDE', bx + 3050, by - 5300,
                      w_tot.outputs[0], g['Grid Beams']).outputs[0], 0.0,
                0.0))
    beam_y_tpl = cube_s(tree, bx + 3400, by - 5500, 0.22, d_tot.outputs[0], 0.4)
    beam_y = inst_realize(
        tree, bx + 3800, by - 5000, beam_y_line, beam_y_tpl,
        sname=out_name(beam_y_tpl, 'Mesh', 'Geometry'),
        trans=combine(tree, bx + 3650, by - 5150, 0.0, 0.0,
                      mathn(tree, 'SUBTRACT', bx + 3450, by - 5150, CH,
                            0.2).outputs[0]))
    light_line = gn_line(
        tree, gin, bx + 3400, by - 5800, g['Lights'],
        combine(tree, bx + 3250, by - 5950,
                mathn(tree, 'ADD', bx + 3050, by - 5950,
                      half_w.outputs[0], 0.5).outputs[0], 0.0, 0.0),
        combine(tree, bx + 3250, by - 6100,
                mathn(tree, 'DIVIDE', bx + 3050, by - 6100,
                      mathn(tree, 'MAXIMUM', bx + 2850, by - 6100,
                            mathn(tree, 'SUBTRACT', bx + 2650, by - 6100,
                                  w_tot.outputs[0], 1.0).outputs[0],
                            1.0).outputs[0],
                      mathn(tree, 'MAXIMUM', bx + 2850, by - 6250,
                            g['Lights'], 1.0).outputs[0]).outputs[0],
                0.0, 0.0))
    light_tpl = cube_s(tree, bx + 3400, by - 6500, 1.1, 0.14, 0.07)
    light_real = inst_realize(
        tree, bx + 3800, by - 5800, light_line, light_tpl,
        sname=out_name(light_tpl, 'Mesh', 'Geometry'),
        trans=combine(tree, bx + 3650, by - 5950, 0.0, 0.0,
                      mathn(tree, 'SUBTRACT', bx + 3450, by - 5950, CH,
                            0.45).outputs[0]))
    ceil_slab = cube_s(tree, bx + 3400, by - 6800,
                       mathn(tree, 'ADD', bx + 3600, by - 6800,
                             w_tot.outputs[0], 0.3),
                       mathn(tree, 'ADD', bx + 3600, by - 6900,
                             d_tot.outputs[0], 0.3),
                       0.10)
    ceil_tr = xform(tree, bx + 3800, by - 6800, ceil_slab,
                    sname=out_name(ceil_slab, 'Mesh', 'Geometry'),
                    trans=combine(tree, bx + 3650, by - 6950, 0.0, 0.0,
                                  mathn(tree, 'ADD', bx + 3450, by - 6950,
                                        CH, 0.15).outputs[0]))
    ceil_join = N(tree, 'GeometryNodeJoinGeometry', bx + 4200, by - 5500)
    for node in (beam_x, beam_y, light_real, ceil_tr):
        L(tree, node, out_name(node, 'Geometry', 'Mesh'), ceil_join,
          'Geometry')
    parts.append(guard_off(tree, bx + 4400, by - 5500, CEIL, ceil_join,
                           sname='Geometry'))

    # ---- plants along the front edge --------------------------------------
    plant_line = gn_line(
        tree, gin, bx + 3400, by - 7400, g['Plants'],
        combine(tree, bx + 3250, by - 7550,
                mathn(tree, 'ADD', bx + 3050, by - 7550,
                      half_w.outputs[0], 0.4).outputs[0],
                mathn(tree, 'ADD', bx + 3050, by - 7700,
                      half_d.outputs[0], 0.45).outputs[0], 0.0),
        combine(tree, bx + 3250, by - 7850,
                mathn(tree, 'DIVIDE', bx + 3050, by - 7850,
                      mathn(tree, 'SUBTRACT', bx + 2850, by - 7850,
                            w_tot.outputs[0], 0.8).outputs[0],
                      mathn(tree, 'MAXIMUM', bx + 2850, by - 8000,
                            g['Plants'], 1.0).outputs[0]).outputs[0],
                0.0, 0.0))
    pot = cyl(tree, bx + 3400, by - 8300, 0.11, 0.22)
    pot_tr = xform(tree, bx + 3600, by - 8300, pot,
                   sname=out_name(pot, 'Mesh', 'Geometry'),
                   trans=combine(tree, bx + 3450, by - 8450, 0.0, 0.0, 0.11))
    foliage = sphere(tree, bx + 3400, by - 8700, 0.20)
    fol_tr = xform(tree, bx + 3600, by - 8700, foliage,
                   sname=out_name(foliage, 'Mesh', 'Geometry'),
                   trans=combine(tree, bx + 3450, by - 8850, 0.0, 0.0, 0.42))
    plant_tpl = N(tree, 'GeometryNodeJoinGeometry', bx + 3800, by - 8500)
    for node in (pot_tr, fol_tr):
        L(tree, node, out_name(node, 'Geometry', 'Mesh'), plant_tpl,
          'Geometry')
    parts.append(inst_realize(tree, bx + 4200, by - 7400, plant_line,
                              plant_tpl, sname='Geometry'))

    # ---- floor slab -------------------------------------------------------
    floor = cube_s(tree, bx + 3400, by - 9200,
                   mathn(tree, 'ADD', bx + 3600, by - 9200,
                         w_tot.outputs[0], 0.6),
                   mathn(tree, 'ADD', bx + 3600, by - 9300,
                         d_tot.outputs[0], 0.6),
                   0.12)
    parts.append(xform(tree, bx + 3800, by - 9200, floor,
                       sname=out_name(floor, 'Mesh', 'Geometry'),
                       trans=combine(tree, bx + 3650, by - 9350, 0.0, 0.0,
                                     -0.06)))

    # ---- join all ---------------------------------------------------------
    out = N(tree, 'GeometryNodeJoinGeometry', bx + 5200, by - 3000)
    for node in parts:
        L(tree, node, out_name(node, 'Geometry', 'Mesh'), out, 'Geometry')
    # UV CHANNEL - see brutalist_city.py for the full rationale. The two
    # projection OPERATORS are unavailable in 5.2 (unregistered / active-object
    # only), but a UV is just a CORNER-domain FLOAT2 named "UVMap" attribute,
    # and StoreNamedAttribute writes it from inside the group.
    from . import brutalist_uv as _buv
    if _buv.add_box_uv(tree, out.outputs[0], gout) is None:
        L(tree, out, 'Geometry', gout, 'Geometry')

    return tree, gin, gout


try:
    from .core import register_builder
    register_builder(
        "GN_BRUTALIST_CubicleFarm", build_brutalist_cubicle_farm,
        "BRUTALIST Cubicle Farm",
        "Open-plan cubicle grid: shared partitions, pedestal desks, "
        "monitors, chairs, overhead bins, drift shear, waffle ceiling.",
        category='city_gen',
    )
    print('[brutalist_cubicles] registered GN_BRUTALIST_CubicleFarm')
except ImportError:
    print('[brutalist_cubicles] standalone mode (no core registry)')


if __name__ == '__main__':
    build_brutalist_cubicle_farm()
