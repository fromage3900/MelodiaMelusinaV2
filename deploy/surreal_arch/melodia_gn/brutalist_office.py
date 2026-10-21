"""Brutalist office block - beton brut, deep reveals, pilotis, board marks.

GN_BRUTALIST_OfficeBlock (build_brutalist_office_block)

The Parisian family dressed its stone; this one shows its concrete.  The
device is honest structure at civic scale: full-height piers at every bay
line, flush spandrel bands carrying board-form shadow lines, glass sunk a
full reveal behind both, and - when the ground floor is given over to
Pilotis - a recessed glazed lobby standing on square columns.

Layout contract (what the health script asserts):
  * piers run the FULL height of the stacked floors at every bay line on all
    four faces (front/back by Bay Count, sides by the aspect ratio);
  * bands are flush with the facade and the glass is inset by Window Reveal,
    so the reveal is a real depth, not a texture;
  * Pilotis off deletes the columns and the lobby glass (NOT +
    DeleteGeometry, house pattern) and the floors drop to the ground;
  * Formwork grooves live INSIDE the band template, so every band at every
    floor carries them;
  * the stair tower's slot windows sit on the tower's own face line.

Front face is +Y (same convention as the PARIS family).
"""

from __future__ import annotations

from .core import (new_geometry_tree, add_float_param, add_int_param,
                   add_bool_param)
from .paris_common import (
    N, L, mathn, combine, xform, cyl, cube_s, inst_realize, guard_off,
    out_name, gn_line,
)


def build_brutalist_office_block(group_name="GN_BRUTALIST_OfficeBlock"):
    tree, gin, gout = new_geometry_tree(group_name)

    # ---- dials -----------------------------------------------------------
    W = add_float_param(tree, "Block Width", 18.0, 6.0, 40.0)
    D = add_float_param(tree, "Block Depth", 12.0, 5.0, 30.0)
    FLOORS = add_int_param(tree, "Floors", 6, 1, 24)
    FH = add_float_param(tree, "Floor Height", 3.2, 2.4, 5.0)
    BC = add_int_param(tree, "Bay Count", 8, 2, 20)
    PW = add_float_param(tree, "Pier Width", 0.5, 0.2, 1.5)
    BH = add_float_param(tree, "Band Height", 0.9, 0.3, 2.0)
    REV = add_float_param(tree, "Window Reveal", 0.35, 0.05, 1.2)
    PIL = add_bool_param(tree, "Pilotis", True)
    PH = add_float_param(tree, "Pilotis Height", 4.2, 2.5, 8.0)
    TOW = add_bool_param(tree, "Stair Tower", True)
    TW = add_float_param(tree, "Tower Width", 3.2, 1.5, 6.0)
    SLOTS = add_int_param(tree, "Slot Count", 6, 2, 16)
    PARH = add_float_param(tree, "Parapet Height", 0.9, 0.0, 2.0)
    PLANT = add_bool_param(tree, "Roof Plant", True)
    PLH = add_float_param(tree, "Plant Height", 2.2, 0.5, 5.0)
    FORM = add_int_param(tree, "Formwork", 3, 0, 8)

    bx, by = -3000, 0
    g = gin.outputs

    # ---- derived ---------------------------------------------------------
    z0 = mathn(tree, 'MULTIPLY', bx, by - 100, PH, g['Pilotis'])
    win_h = mathn(tree, 'SUBTRACT', bx, by - 300, FH, BH)
    stack_h = mathn(tree, 'MULTIPLY', bx, by - 500, FH, g['Floors'])
    h_total = mathn(tree, 'ADD', bx, by - 700, z0.outputs[0],
                    stack_h.outputs[0])
    bay_pitch = mathn(tree, 'DIVIDE', bx, by - 900, W, g['Bay Count'])
    side_bays = mathn(
        tree, 'MAXIMUM', bx, by - 1100,
        mathn(tree, 'ROUND', bx - 200, by - 1100,
              mathn(tree, 'DIVIDE', bx - 400, by - 1100,
                    mathn(tree, 'MULTIPLY', bx - 600, by - 1100,
                          g['Bay Count'], D).outputs[0],
                    W).outputs[0]).outputs[0],
        2.0)
    side_pitch = mathn(tree, 'DIVIDE', bx, by - 1300, D, side_bays.outputs[0])
    pier_d = mathn(tree, 'ADD', bx, by - 1500, REV, 0.30)
    pier_z = mathn(tree, 'ADD', bx, by - 1700, z0.outputs[0],
                   mathn(tree, 'MULTIPLY', bx - 200, by - 1700,
                         stack_h.outputs[0], 0.5).outputs[0])
    n_fb = mathn(tree, 'ADD', bx, by - 1900, g['Bay Count'], 1)
    n_lr = mathn(tree, 'ADD', bx, by - 2000, side_bays.outputs[0], 1)
    half_w = mathn(tree, 'MULTIPLY', bx, by - 2100, W, -0.5)
    half_d = mathn(tree, 'MULTIPLY', bx, by - 2200, D, -0.5)
    half_pd = mathn(tree, 'MULTIPLY', bx, by - 2300, pier_d.outputs[0], 0.5)

    parts = []

    # ---- piers: four full-height bay lines -------------------------------
    pier_fb = cube_s(tree, bx, by - 2400, PW, pier_d.outputs[0],
                     stack_h.outputs[0])                      # front/back
    pier_lr = cube_s(tree, bx, by - 2600, pier_d.outputs[0], PW,
                     stack_h.outputs[0])                      # left/right

    py_front = mathn(tree, 'SUBTRACT', bx, by - 2800,
                     mathn(tree, 'MULTIPLY', bx - 200, by - 2800, D,
                           0.5).outputs[0], half_pd.outputs[0])
    py_back = mathn(tree, 'ADD', bx, by - 2900, half_d.outputs[0],
                    half_pd.outputs[0])
    px_left = mathn(tree, 'ADD', bx, by - 3000, half_w.outputs[0],
                    half_pd.outputs[0])
    px_right = mathn(tree, 'SUBTRACT', bx, by - 3100,
                     mathn(tree, 'MULTIPLY', bx - 200, by - 3100, W,
                           0.5).outputs[0], half_pd.outputs[0])

    for tag, count, start, offset, trans in (
            ("front", n_fb,
             combine(tree, bx - 2400, by - 3200, half_w.outputs[0], 0.0, 0.0),
             combine(tree, bx - 2400, by - 3350, bay_pitch.outputs[0],
                     0.0, 0.0),
             combine(tree, bx - 2400, by - 3500, 0.0, py_front.outputs[0],
                     pier_z.outputs[0])),
            ("back", n_fb,
             combine(tree, bx - 2300, by - 3200, half_w.outputs[0], 0.0, 0.0),
             combine(tree, bx - 2300, by - 3350, bay_pitch.outputs[0],
                     0.0, 0.0),
             combine(tree, bx - 2300, by - 3500, 0.0, py_back.outputs[0],
                     pier_z.outputs[0])),
            ("left", n_lr,
             combine(tree, bx - 2200, by - 3200, px_left.outputs[0],
                     half_d.outputs[0], 0.0),
             combine(tree, bx - 2200, by - 3350, 0.0,
                     side_pitch.outputs[0], 0.0),
             combine(tree, bx - 2200, by - 3500, 0.0, 0.0,
                     pier_z.outputs[0])),
            ("right", n_lr,
             combine(tree, bx - 2100, by - 3200, px_right.outputs[0],
                     half_d.outputs[0], 0.0),
             combine(tree, bx - 2100, by - 3350, 0.0,
                     side_pitch.outputs[0], 0.0),
             combine(tree, bx - 2100, by - 3500, 0.0, 0.0,
                     pier_z.outputs[0])),
    ):
        line = gn_line(tree, gin, bx + 600, by - 3200, count, start, offset)
        tpl = pier_fb if tag in ('front', 'back') else pier_lr
        parts.append(inst_realize(
            tree, bx + 900, by - 3200, line, tpl,
            sname=out_name(tpl, 'Mesh', 'Geometry'), trans=trans))

    # ---- bands with board-form shadow lines ------------------------------
    band_box = cube_s(tree, bx, by - 3900, W, D, BH)
    gro_pitch = mathn(tree, 'DIVIDE', bx, by - 4100, BH,
                      mathn(tree, 'ADD', bx - 200, by - 4100, g['Formwork'],
                            1.0).outputs[0])
    gro_box = cube_s(tree, bx + 400, by - 3900,
                     mathn(tree, 'ADD', bx + 200, by - 3900, W, 0.06),
                     mathn(tree, 'ADD', bx + 200, by - 4000, D, 0.06),
                     0.05)
    gro_tr = xform(tree, bx + 700, by - 3900, gro_box,
                   sname=out_name(gro_box, 'Mesh', 'Geometry'),
                   trans=combine(tree, bx + 550, by - 4050, 0.0, 0.0,
                                 mathn(tree, 'SUBTRACT', bx + 400, by - 4050,
                                       mathn(tree, 'MULTIPLY', bx + 250,
                                             by - 4050, BH, -0.5).outputs[0],
                                       gro_pitch.outputs[0]).outputs[0]))
    gro_line = gn_line(tree, gin, bx + 600, by - 4200, 'Formwork',
                       combine(tree, bx + 450, by - 4350, 0.0, 0.0, 0.0),
                       combine(tree, bx + 450, by - 4500, 0.0, 0.0,
                               gro_pitch.outputs[0]))
    gro_real = inst_realize(tree, bx + 1000, by - 3900, gro_line, gro_tr,
                            sname='Geometry')
    band_tpl = N(tree, 'GeometryNodeJoinGeometry', bx + 1300, by - 3900)
    for node in (band_box, gro_real):
        L(tree, node, out_name(node, 'Geometry', 'Mesh'), band_tpl, 'Geometry')

    band_z = mathn(tree, 'ADD', bx, by - 4700,
                   mathn(tree, 'ADD', bx - 200, by - 4700, z0.outputs[0],
                         win_h.outputs[0]).outputs[0],
                   mathn(tree, 'MULTIPLY', bx - 400, by - 4700, BH,
                         0.5).outputs[0])
    band_line = gn_line(tree, gin, bx + 600, by - 4800, 'Floors',
                        combine(tree, bx + 450, by - 4950, 0.0, 0.0, 0.0),
                        combine(tree, bx + 450, by - 5100, 0.0, 0.0, FH))
    band_real = inst_realize(
        tree, bx + 1500, by - 4800, band_line, band_tpl, sname='Geometry',
        trans=combine(tree, bx + 1350, by - 4950, 0.0, 0.0,
                      band_z.outputs[0]))
    parts.append(band_real)

    # ---- recessed glass per floor ----------------------------------------
    glass_box = cube_s(tree, bx, by - 5400,
                       mathn(tree, 'SUBTRACT', bx + 200, by - 5400, W,
                             mathn(tree, 'MULTIPLY', bx + 400, by - 5400,
                                   REV, 2.0).outputs[0]),
                       mathn(tree, 'SUBTRACT', bx + 200, by - 5500, D,
                             mathn(tree, 'MULTIPLY', bx + 400, by - 5500,
                                   REV, 2.0).outputs[0]),
                       mathn(tree, 'SUBTRACT', bx + 200, by - 5600,
                             win_h.outputs[0], 0.10))
    glass_z = mathn(tree, 'ADD', bx, by - 5800, z0.outputs[0],
                    mathn(tree, 'MULTIPLY', bx - 200, by - 5800,
                          win_h.outputs[0], 0.5).outputs[0])
    glass_line = gn_line(tree, gin, bx + 600, by - 5900, 'Floors',
                         combine(tree, bx + 450, by - 6050, 0.0, 0.0, 0.0),
                         combine(tree, bx + 450, by - 6200, 0.0, 0.0, FH))
    glass_real = inst_realize(
        tree, bx + 900, by - 5900, glass_line, glass_box,
        sname=out_name(glass_box, 'Mesh', 'Geometry'),
        trans=combine(tree, bx + 750, by - 6050, 0.0, 0.0,
                      glass_z.outputs[0]))
    parts.append(glass_real)

    # ---- pilotis: columns + lobby glass + ground beam ---------------------
    pil_col = cube_s(tree, bx + 1700, by - 6500, 0.55, 0.55, PH)
    col_z = mathn(tree, 'MULTIPLY', bx + 1700, by - 6600, PH, 0.5)
    for tag, count, start, offset, trans in (
            ("pf", n_fb,
             combine(tree, bx + 1500, by - 6800, half_w.outputs[0], 0.0, 0.0),
             combine(tree, bx + 1500, by - 6950, bay_pitch.outputs[0],
                     0.0, 0.0),
             combine(tree, bx + 1500, by - 7100, 0.0,
                     mathn(tree, 'SUBTRACT', bx + 1300, by - 7100,
                           mathn(tree, 'MULTIPLY', bx + 1100, by - 7100,
                                 D, 0.5).outputs[0], 0.275).outputs[0],
                     col_z.outputs[0])),
            ("pb", n_fb,
             combine(tree, bx + 1400, by - 6800, half_w.outputs[0], 0.0, 0.0),
             combine(tree, bx + 1400, by - 6950, bay_pitch.outputs[0],
                     0.0, 0.0),
             combine(tree, bx + 1400, by - 7100, 0.0,
                     mathn(tree, 'ADD', bx + 1300, by - 7100,
                           half_d.outputs[0], 0.275).outputs[0],
                     col_z.outputs[0])),
            ("pl", n_lr,
             combine(tree, bx + 1300, by - 6800,
                     mathn(tree, 'SUBTRACT', bx + 1100, by - 6800,
                           half_w.outputs[0], -0.275).outputs[0],
                     half_d.outputs[0], 0.0),
             combine(tree, bx + 1300, by - 6950, 0.0,
                     side_pitch.outputs[0], 0.0),
             combine(tree, bx + 1300, by - 7100, 0.0, 0.0,
                     col_z.outputs[0])),
            ("pr", n_lr,
             combine(tree, bx + 1200, by - 6800,
                     mathn(tree, 'SUBTRACT', bx + 1000, by - 6800,
                           mathn(tree, 'MULTIPLY', bx + 800, by - 6800,
                                 W, 0.5).outputs[0], 0.275).outputs[0],
                     half_d.outputs[0], 0.0),
             combine(tree, bx + 1200, by - 6950, 0.0,
                     side_pitch.outputs[0], 0.0),
             combine(tree, bx + 1200, by - 7100, 0.0, 0.0,
                     col_z.outputs[0])),
    ):
        line = gn_line(tree, gin, bx + 2000, by - 6800, count, start, offset)
        real = inst_realize(tree, bx + 2300, by - 6800, line, pil_col,
                            sname=out_name(pil_col, 'Mesh', 'Geometry'),
                            trans=trans)
        parts.append(guard_off(tree, bx + 2700, by - 6800, PIL, real))

    lobby = cube_s(tree, bx + 1700, by - 7400,
                   mathn(tree, 'SUBTRACT', bx + 1900, by - 7400, W, 1.4),
                   mathn(tree, 'SUBTRACT', bx + 1900, by - 7500, D, 1.4),
                   mathn(tree, 'SUBTRACT', bx + 1900, by - 7600, PH, 0.6))
    lobby_tr = xform(tree, bx + 2100, by - 7400, lobby,
                     sname=out_name(lobby, 'Mesh', 'Geometry'),
                     trans=combine(tree, bx + 1950, by - 7550, 0.0, 0.0,
                                   col_z.outputs[0]))
    parts.append(guard_off(tree, bx + 2700, by - 7400, PIL, lobby_tr,
                           sname='Geometry'))

    ground_beam = cube_s(tree, bx + 1700, by - 7800,
                         mathn(tree, 'ADD', bx + 1900, by - 7800, W, 0.2),
                         mathn(tree, 'ADD', bx + 1900, by - 7900, D, 0.2),
                         0.5)
    parts.append(xform(tree, bx + 2100, by - 7800, ground_beam,
                       sname=out_name(ground_beam, 'Mesh', 'Geometry'),
                       trans=combine(tree, bx + 1950, by - 7950, 0.0, 0.0,
                                     mathn(tree, 'SUBTRACT', bx + 1800,
                                           by - 7950, z0.outputs[0],
                                           0.25).outputs[0])))

    # ---- stair tower with slot windows ------------------------------------
    tow_h = mathn(tree, 'ADD', bx + 1700, by - 8200, h_total.outputs[0], 1.4)
    tow_x = mathn(tree, 'SUBTRACT', bx + 1700, by - 8300,
                  mathn(tree, 'ADD', bx + 1500, by - 8300,
                        half_w.outputs[0], 0.35).outputs[0],
                  mathn(tree, 'MULTIPLY', bx + 1100, by - 8300,
                        TW, 0.5).outputs[0])
    tow_d = mathn(tree, 'MULTIPLY', bx + 1700, by - 8400, D, 0.55)
    tow_box = cube_s(tree, bx + 1700, by - 8500, TW, tow_d.outputs[0],
                     tow_h.outputs[0])
    tow_tr = xform(tree, bx + 2100, by - 8500, tow_box,
                   sname=out_name(tow_box, 'Mesh', 'Geometry'),
                   trans=combine(tree, bx + 1950, by - 8650,
                                 tow_x.outputs[0], 0.0,
                                 mathn(tree, 'MULTIPLY', bx + 1800, by - 8650,
                                       tow_h.outputs[0], 0.5).outputs[0]))
    slot_box = cube_s(tree, bx + 1700, by - 8800,
                      mathn(tree, 'MULTIPLY', bx + 1900, by - 8800, TW, 0.60),
                      0.18, 0.42)
    slot_line = gn_line(
        tree, gin, bx + 1700, by - 9000, 'Slot Count',
        combine(tree, bx + 1550, by - 9150, 0.0, 0.0, 1.2),
        combine(tree, bx + 1550, by - 9300, 0.0, 0.0,
                mathn(tree, 'DIVIDE', bx + 1350, by - 9300,
                      mathn(tree, 'SUBTRACT', bx + 1150, by - 9300,
                            tow_h.outputs[0], 2.4).outputs[0],
                      g['Slot Count']).outputs[0]))
    slot_real = inst_realize(
        tree, bx + 2100, by - 8800, slot_line, slot_box,
        sname=out_name(slot_box, 'Mesh', 'Geometry'),
        trans=combine(tree, bx + 1950, by - 8950, tow_x.outputs[0],
                      mathn(tree, 'SUBTRACT', bx + 1800, by - 8950,
                            mathn(tree, 'MULTIPLY', bx + 1600, by - 8950,
                                  D, 0.275).outputs[0],
                            0.06).outputs[0],
                      0.0))
    tow_join = N(tree, 'GeometryNodeJoinGeometry', bx + 2500, by - 8500)
    for node in (tow_tr, slot_real):
        L(tree, node, out_name(node, 'Geometry', 'Mesh'), tow_join, 'Geometry')
    parts.append(guard_off(tree, bx + 2700, by - 8500, TOW, tow_join,
                           sname='Geometry'))

    # ---- parapet, roof plant, stacks --------------------------------------
    par_box = cube_s(tree, bx, by - 9600,
                     mathn(tree, 'ADD', bx + 200, by - 9600, W, 0.3),
                     mathn(tree, 'ADD', bx + 200, by - 9700, D, 0.3), PARH)
    par_z = mathn(tree, 'ADD', bx, by - 9800, h_total.outputs[0],
                  mathn(tree, 'MULTIPLY', bx - 200, by - 9800, PARH,
                        0.5).outputs[0])
    parts.append(xform(tree, bx + 400, by - 9600, par_box,
                       sname=out_name(par_box, 'Mesh', 'Geometry'),
                       trans=combine(tree, bx + 250, by - 9750, 0.0, 0.0,
                                     par_z.outputs[0])))

    plant_box = cube_s(tree, bx + 1700, by - 10100,
                       mathn(tree, 'MULTIPLY', bx + 1900, by - 10100, W,
                             0.35),
                       mathn(tree, 'MULTIPLY', bx + 1900, by - 10200, D,
                             0.35),
                       PLH)
    plant_z = mathn(tree, 'ADD', bx + 1700, by - 10300, h_total.outputs[0],
                    mathn(tree, 'MULTIPLY', bx + 1500, by - 10300, PLH,
                          0.5).outputs[0])
    plant_tr = xform(tree, bx + 2100, by - 10100, plant_box,
                     sname=out_name(plant_box, 'Mesh', 'Geometry'),
                     trans=combine(tree, bx + 1950, by - 10250,
                                   mathn(tree, 'MULTIPLY', bx + 1750,
                                         by - 10250, W, 0.12),
                                   0.0, plant_z.outputs[0]))
    stack_a = cyl(tree, bx + 1700, by - 10600, 0.35,
                  mathn(tree, 'MULTIPLY', bx + 1900, by - 10600, PLH, 0.6))
    stack_a_tr = xform(tree, bx + 2100, by - 10600, stack_a,
                       sname=out_name(stack_a, 'Mesh', 'Geometry'),
                       trans=combine(tree, bx + 1950, by - 10750,
                                     mathn(tree, 'MULTIPLY', bx + 1750,
                                           by - 10750, W, 0.30),
                                     mathn(tree, 'MULTIPLY', bx + 1750,
                                           by - 10850, D, 0.10),
                                     mathn(tree, 'ADD', bx + 1750, by - 10950,
                                           h_total.outputs[0],
                                           mathn(tree, 'MULTIPLY', bx + 1550,
                                                 by - 10950, PLH, 0.3
                                                 ).outputs[0]).outputs[0]))
    stack_b = cyl(tree, bx + 1700, by - 11100, 0.35,
                  mathn(tree, 'MULTIPLY', bx + 1900, by - 11100, PLH, 0.45))
    stack_b_tr = xform(tree, bx + 2100, by - 11100, stack_b,
                       sname=out_name(stack_b, 'Mesh', 'Geometry'),
                       trans=combine(tree, bx + 1950, by - 11250,
                                     mathn(tree, 'MULTIPLY', bx + 1750,
                                           by - 11250, W, 0.30),
                                     mathn(tree, 'MULTIPLY', bx + 1750,
                                           by - 11350, D, -0.10),
                                     mathn(tree, 'ADD', bx + 1750, by - 11450,
                                           h_total.outputs[0],
                                           mathn(tree, 'MULTIPLY', bx + 1550,
                                                 by - 11450, PLH, 0.225
                                                 ).outputs[0]).outputs[0]))
    plant_join = N(tree, 'GeometryNodeJoinGeometry', bx + 2500, by - 10100)
    for node in (plant_tr, stack_a_tr, stack_b_tr):
        L(tree, node, out_name(node, 'Geometry', 'Mesh'), plant_join,
          'Geometry')
    parts.append(guard_off(tree, bx + 2700, by - 10100, PLANT, plant_join,
                           sname='Geometry'))

    # ---- join all ---------------------------------------------------------
    out = N(tree, 'GeometryNodeJoinGeometry', bx + 3600, by - 3000)
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
        "GN_BRUTALIST_OfficeBlock", build_brutalist_office_block,
        "BRUTALIST Office Block",
        "Beton brut office slab: full-height piers, flush board-marked "
        "spandrels, deep reveals, pilotis lobby, stair tower, roof plant.",
        category='city_gen',
    )
    print('[brutalist_office] registered GN_BRUTALIST_OfficeBlock')
except ImportError:
    print('[brutalist_office] standalone mode (no core registry)')


if __name__ == '__main__':
    build_brutalist_office_block()
