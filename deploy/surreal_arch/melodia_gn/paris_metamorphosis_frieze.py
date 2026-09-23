"""Parisian metamorphosis frieze - one species becoming another along a wall.

GN_PARIS_MetamorphosisFrieze (build_paris_metamorphosis_frieze)

Escher's *Metamorphosis* runs a band in which birds become fish become birds,
with no seam you can point at.  This builder puts that band on a wall: a row
of motif cells where `Morph` slides the species boundary along the frieze and
`Seam Width` says how many cells the transition takes.

In the seam the two species are INSTANCED ON THE SAME CELLS, offset apart by
`Interlock` - so the transition is not a cut but a zone where bird and fish
mesh, the same interlock idea as the Day-Night facade's roofline flocks.

Dials: Cells, Morph (0 = all birds, 1 = all fish), Seam Width, Interlock,
Motif Scale, Bird Wing Spread, Fin Count (the fish's dorsal ribs), Fish Flip,
plus a bead rail along both edges and a Reveal that lifts the motifs off the
plate.

NOT a reimplementation of MEL_escher_tessellation (a 2D tiling grid fill):
this is a linear band with a moving species boundary and an interlock zone.

Follows the paris_* family convention: helpers from paris_common,
register_builder() at import time, every parameter an editable named input.
"""

from __future__ import annotations

import math

import bpy

from .core import (new_geometry_tree, add_float_param, add_int_param,
                   add_bool_param, link_sockets)
from .paris_common import (
    N, L, mathn, booln, combine, xform, cyl, sphere, cube_s,
    inst_realize, guard_off, out_name,
)


def build_paris_metamorphosis_frieze(group_name="GN_PARIS_MetamorphosisFrieze"):
    """Morph band: bird cells, a meshing seam, fish cells - Morph slides it."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    # ---- dials -----------------------------------------------------------
    add_float_param(tree, "Band Length", 8.0, 3.0, 20.0)
    add_float_param(tree, "Band Height", 0.9, 0.4, 2.0)
    add_float_param(tree, "Band Depth", 0.12, 0.05, 0.4)
    add_int_param(tree, "Cells", 16, 4, 48)
    add_float_param(tree, "Morph", 0.5, 0.0, 1.0)
    add_int_param(tree, "Seam Width", 3, 0, 8)
    add_float_param(tree, "Interlock", 0.5, 0.0, 1.0)
    add_float_param(tree, "Motif Scale", 0.36, 0.15, 0.9)
    add_float_param(tree, "Bird Wing Spread", 0.6, 0.2, 1.2)
    add_int_param(tree, "Fin Count", 4, 2, 8)
    add_bool_param(tree, "Fish Flip", True)
    add_bool_param(tree, "Bead Rail", True)
    add_int_param(tree, "Rail Beads", 60, 0, 160)
    add_float_param(tree, "Bead Size", 0.02, 0.008, 0.05)
    add_float_param(tree, "Reveal", 0.06, 0.0, 0.2)

    LEN = gin.outputs['Band Length']
    BH = gin.outputs['Band Height']
    BD = gin.outputs['Band Depth']
    CELLS = gin.outputs['Cells']
    MORPH = gin.outputs['Morph']
    SEAM = gin.outputs['Seam Width']
    ILOCK = gin.outputs['Interlock']
    MS = gin.outputs['Motif Scale']

    # ---- plate -----------------------------------------------------------
    plate = cube_s(tree, bx - 3000, by + 5000, LEN, BD, BH)

    # ---- cell windows: birds / seam / fish -------------------------------
    # birdN = round((1 - Morph) * Cells); seamN = min(SeamWidth, birdN,
    # Cells - birdN); pure birds = birdN - seamN; seam = [birdN-seamN, birdN);
    # pure fish = [birdN, Cells).
    one_m = mathn(tree, 'SUBTRACT', bx - 3000, by + 4700, 1.0, MORPH)
    birdN0 = mathn(tree, 'MULTIPLY', bx - 3000, by + 4550, one_m.outputs[0], CELLS)
    birdN = mathn(tree, 'ROUND', bx - 3000, by + 4400, birdN0.outputs[0])
    fishN = mathn(tree, 'SUBTRACT', bx - 3000, by + 4250, CELLS, birdN.outputs[0])
    seam_a = mathn(tree, 'MINIMUM', bx - 3000, by + 4100, SEAM, birdN.outputs[0])
    seamN = mathn(tree, 'MINIMUM', bx - 3000, by + 3950, seam_a.outputs[0],
                  fishN.outputs[0])
    # the seam STRADDLES the boundary: [birdN - floor(seamN/2), +seamN)
    halfS = mathn(tree, 'FLOOR', bx - 3000, by + 3725,
                  mathn(tree, 'MULTIPLY', bx - 3000, by + 3790,
                        seamN.outputs[0], 0.5).outputs[0])
    bird_pure = mathn(tree, 'SUBTRACT', bx - 3000, by + 3800, birdN.outputs[0],
                      halfS.outputs[0])
    seam_start = mathn(tree, 'SUBTRACT', bx - 3000, by + 3650, birdN.outputs[0],
                       halfS.outputs[0])
    seam_end = mathn(tree, 'ADD', bx - 3000, by + 3580, seam_start.outputs[0],
                     seamN.outputs[0])
    pitch = mathn(tree, 'DIVIDE', bx - 3000, by + 3500, LEN, CELLS)

    def cell_line(x, y, count, offset):
        """Points at cell centres: x_i = (g + 0.5) * pitch - L/2, g = i + offset."""
        line = N(tree, 'GeometryNodeMeshLine', x, y)
        try:
            line.mode = 'OFFSET'
        except Exception:
            pass
        if isinstance(count, (int, float)):
            line.inputs['Count'].default_value = int(count)
        elif hasattr(count, 'outputs'):
            link_sockets(tree, count.outputs[0], line.inputs['Count'])
        else:
            link_sockets(tree, count, line.inputs['Count'])
        line.inputs['Offset'].default_value = (0.0, 0.0, 0.0)
        idx = N(tree, 'GeometryNodeInputIndex', x, y + 140)
        gi = mathn(tree, 'ADD', x + 180, y + 140, idx.outputs['Index'], offset)
        gp = mathn(tree, 'ADD', x + 340, y + 140, gi.outputs[0], 0.5)
        px = mathn(tree, 'MULTIPLY', x + 500, y + 140, gp.outputs[0],
                   pitch.outputs[0])
        px2 = mathn(tree, 'SUBTRACT', x + 660, y + 140, px.outputs[0],
                    mathn(tree, 'MULTIPLY', x + 500, y + 0,
                          LEN, 0.5).outputs[0])
        off = combine(tree, x + 820, y + 140, px2.outputs[0], 0.0, 0.0)
        sp = N(tree, 'GeometryNodeSetPosition', x + 960, y + 140)
        L(tree, line, 'Mesh', sp, 'Geometry')
        L(tree, off, 'Vector', sp, 'Offset')
        return sp

    # ---- bird template (front-facing, wings spread) ----------------------
    body = cube_s(tree, bx - 3000, by + 3200, 0.30, 0.10, 0.16)
    tail = cube_s(tree, bx - 3000, by + 3050, 0.12, 0.08, 0.16)
    tail_x = xform(tree, bx - 2800, by + 3050, tail, trans=(-0.30, 0.0, -0.02))
    bird_join = N(tree, 'GeometryNodeJoinGeometry', bx - 2600, by + 3200)
    L(tree, body, 'Mesh', bird_join, 'Geometry')
    L(tree, tail_x, 'Geometry', bird_join, 'Geometry')
    for ws in (-1.0, 1.0):
        wing = cube_s(tree, bx - 3000, by + 2900 + ws * 10, 0.55, 0.06, 0.10)
        # outer ends UP: rotation sign flips per side (see facade bird)
        wing_ang = mathn(tree, 'MULTIPLY', bx - 3000, by + 3050 + ws * 10,
                         gin.outputs['Bird Wing Spread'], -ws)
        wing_x = xform(tree, bx - 2800, by + 2900 + ws * 10, wing,
                       trans=(0.24 * ws, 0.0, 0.06),
                       rot=combine(tree, bx - 2900, by + 3050 + ws * 10,
                                   0.0, wing_ang.outputs[0], 0.0).outputs['Vector'])
        L(tree, wing_x, 'Geometry', bird_join, 'Geometry')
    bird_tpl = xform(tree, bx - 2400, by + 3200, bird_join, sname='Geometry',
                     scale=combine(tree, bx - 2600, by + 3350, MS, MS, MS).outputs['Vector'])

    # ---- fish template (profile, dorsal fin ribs) ------------------------
    f_body = cube_s(tree, bx - 3000, by + 2600, 0.42, 0.10, 0.18)
    f_join = N(tree, 'GeometryNodeJoinGeometry', bx - 2600, by + 2600)
    L(tree, f_body, 'Mesh', f_join, 'Geometry')
    for ts in (-1.0, 1.0):
        fin = cube_s(tree, bx - 3000, by + 2450 + ts * 10, 0.18, 0.08, 0.26)
        fin_x = xform(tree, bx - 2800, by + 2450 + ts * 10, fin,
                      trans=(0.28, 0.0, 0.0),
                      rot=(0.0, ts * math.radians(28.0), 0.0))
        L(tree, fin_x, 'Geometry', f_join, 'Geometry')
    # dorsal ribs: socket-count line along the back
    rib_tpl = cube_s(tree, bx - 3000, by + 2250, 0.035, 0.06, 0.17)
    rib_line = N(tree, 'GeometryNodeMeshLine', bx - 2800, by + 2250)
    try:
        rib_line.mode = 'OFFSET'
    except Exception:
        pass
    link_sockets(tree, gin.outputs['Fin Count'], rib_line.inputs['Count'])
    rib_off = combine(tree, bx - 2800, by + 2100, 0.075, 0.0, 0.0)
    L(tree, rib_off, 'Vector', rib_line, 'Offset')
    rib_so = combine(tree, bx - 2800, by + 1950, -0.14, 0.0, 0.0)
    L(tree, rib_so, 'Vector', rib_line, 'Start Location')
    rib_tr = combine(tree, bx - 2800, by + 1800, 0.0, 0.0, 0.09)
    rib_real = inst_realize(tree, bx - 2400, by + 2250, rib_line, rib_tpl,
                            trans=rib_tr.outputs['Vector'])
    L(tree, rib_real, 'Geometry', f_join, 'Geometry')
    # Fish Flip: rotate the whole fish about Z by 0 or pi (bool * pi)
    flip = mathn(tree, 'MULTIPLY', bx - 3000, by + 1650, gin.outputs['Fish Flip'],
                 math.pi)
    f_rot = combine(tree, bx - 2800, by + 1650, 0.0, 0.0, flip.outputs[0])
    fish_tpl0 = xform(tree, bx - 2400, by + 2600, f_join, sname='Geometry',
                      rot=f_rot.outputs['Vector'])
    fish_tpl = xform(tree, bx - 2200, by + 2600, fish_tpl0, sname='Geometry',
                     scale=combine(tree, bx - 2400, by + 2750, MS, MS, MS).outputs['Vector'])

    # ---- the three streams -----------------------------------------------
    lift = mathn(tree, 'ADD', bx - 3000, by + 1500,
                 mathn(tree, 'MULTIPLY', bx - 3000, by + 1350,
                       BD, 0.5).outputs[0], gin.outputs['Reveal'])
    ilock_z = mathn(tree, 'MULTIPLY', bx - 3000, by + 1200,
                    mathn(tree, 'MULTIPLY', bx - 3000, by + 1050,
                          ILOCK, BH).outputs[0], 0.22)
    b_lift = combine(tree, bx - 2800, by + 1200, 0.0, lift.outputs[0],
                     ilock_z.outputs[0])
    f_lift = combine(tree, bx - 2800, by + 900, 0.0, lift.outputs[0],
                     mathn(tree, 'MULTIPLY', bx - 3000, by + 750,
                           ilock_z.outputs[0], -1.0).outputs[0])

    birds_line = cell_line(bx - 2200, by + 4200, bird_pure, 0.0)
    birds_real = inst_realize(tree, bx - 1000, by + 4200, birds_line, bird_tpl,
                              sname='Geometry', trans=b_lift.outputs['Vector'])
    fish_line = cell_line(bx - 2200, by + 3400,
                          mathn(tree, 'SUBTRACT', bx - 3000, by + 3300,
                                CELLS, seam_end.outputs[0]),
                          seam_end.outputs[0])
    fish_real = inst_realize(tree, bx - 1000, by + 3400, fish_line, fish_tpl,
                             sname='Geometry', trans=f_lift.outputs['Vector'])
    # seam: BOTH species on the same cells (they mesh)
    seam_line = cell_line(bx - 2200, by + 2600, seamN, seam_start.outputs[0])
    seam_b = inst_realize(tree, bx - 1000, by + 2600, seam_line, bird_tpl,
                          sname='Geometry', trans=b_lift.outputs['Vector'])
    seam_f = inst_realize(tree, bx - 800, by + 2600, seam_line, fish_tpl,
                          sname='Geometry', trans=f_lift.outputs['Vector'])

    # ---- bead rails along both edges -------------------------------------
    bead_tpl = sphere(tree, bx + 1400, by + 4200, gin.outputs['Bead Size'])
    rail_pitch = mathn(tree, 'DIVIDE', bx - 3000, by + 600, LEN,
                       mathn(tree, 'MAXIMUM', bx - 3000, by + 450,
                             gin.outputs['Rail Beads'], 1.0).outputs[0])
    rail_z = mathn(tree, 'SUBTRACT', bx - 3000, by + 300,
                   mathn(tree, 'MULTIPLY', bx - 3000, by + 150,
                         BH, 0.5).outputs[0],
                   mathn(tree, 'MULTIPLY', bx - 3000, by + 0,
                         gin.outputs['Bead Size'], 1.5).outputs[0])
    rails = []
    for rz_s, rz in (("t", rail_z), ("b", mathn(tree, 'MULTIPLY',
                                                bx - 3000, by - 150,
                                                rail_z.outputs[0], -1.0))):
        r_line = N(tree, 'GeometryNodeMeshLine', bx + 1400, by - 300)
        try:
            r_line.mode = 'OFFSET'
        except Exception:
            pass
        link_sockets(tree, gin.outputs['Rail Beads'], r_line.inputs['Count'])
        r_off = combine(tree, bx + 1400, by - 450, rail_pitch.outputs[0], 0.0, 0.0)
        L(tree, r_off, 'Vector', r_line, 'Offset')
        r_so = combine(tree, bx + 1400, by - 600,
                       mathn(tree, 'ADD', bx - 3000, by - 750,
                             mathn(tree, 'MULTIPLY', bx - 3000, by - 900,
                                   LEN, -0.5).outputs[0],
                             mathn(tree, 'MULTIPLY', bx - 3000, by - 1050,
                                   rail_pitch.outputs[0], 0.5).outputs[0]).outputs[0],
                       0.0, 0.0)
        L(tree, r_so, 'Vector', r_line, 'Start Location')
        r_real = inst_realize(tree, bx + 1800, by - 300, r_line, bead_tpl,
                              trans=combine(tree, bx + 1600, by - 1200,
                                            mathn(tree, 'MULTIPLY', bx - 3000,
                                                  by - 1500, BD, 0.5).outputs[0],
                                            0.0, rz.outputs[0]).outputs['Vector'])
        rails.append(r_real)
    rail_join = N(tree, 'GeometryNodeJoinGeometry', bx + 2400, by - 300)
    for node in rails:
        L(tree, node, 'Geometry', rail_join, 'Geometry')
    rail_g = guard_off(tree, bx + 2600, by - 300, gin.outputs['Bead Rail'],
                       rail_join)

    # ---- join ------------------------------------------------------------
    j1 = N(tree, 'GeometryNodeJoinGeometry', bx + 4000, by + 1500)
    for node in (plate, birds_real, fish_real, seam_b, seam_f, rail_g):
        L(tree, node, out_name(node, 'Geometry', 'Mesh'), j1, 'Geometry')
    L(tree, j1, 'Geometry', gout, 'Geometry')

    return tree, gin, gout


# ------------------------------------------------- addon registration

try:
    from .core import register_builder  # noqa: E402
    register_builder(
        'GN_PARIS_MetamorphosisFrieze', build_paris_metamorphosis_frieze,
        'PARIS Metamorphosis Frieze',
        'Band where one species becomes another: Morph slides the boundary, '
        'Seam Width sets the transition, Interlock meshes bird and fish on '
        'shared cells. Bead rails + reveal.',
        category='escher',
    )
    print('[paris_metamorphosis_frieze] registered GN_PARIS_MetamorphosisFrieze')
except ImportError:
    print('[paris_metamorphosis_frieze] standalone mode (no core registry)')


if __name__ == '__main__':
    build_paris_metamorphosis_frieze()
