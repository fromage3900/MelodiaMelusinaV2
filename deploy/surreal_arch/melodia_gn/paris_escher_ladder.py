"""Parisian Escher ladder - the Belvedere ladder as a standalone device.

GN_PARIS_EscherLadder (build_paris_escher_ladder)

Escher's *Belvedere* hangs on one device: a straight staircase that visibly
fails to meet the upper floor. Inside MEL_escher_belvedere that device exists
only as an inseparable part of the loggia (see its own comment, "floating
ladder extension: only when the upper level is rotated"). This module extracts
it into a reusable Parisian service ladder: a stone stringer and treads, a
mansard landing, a wrought-iron handrail (the Guimard line), and the
impossibility exposed as a DIAL.

The impossibility is `Join Error`:

    0.0   the top rung meets the landing exactly - an honest working ladder;
    +     the ladder overshoots the landing surface (it arrives above it);
    -     the ladder falls short (it arrives below it).

The landing stays where the building says it should be, so any non-zero Join
Error is a visible join failure - the Belvedere read - and it is parametric
rather than baked. One device can be a working ladder in one shot and an
impossibility in the next.

`Floating Steps` deepens the read: the stringer is given its OWN length while
the rungs keep going, so the top N treads are unsupported and hang in the air.
That is done purely with math on the existing sockets - no second geometry
chain, no switch, no duplicated rung line.

NOT a reimplementation of MEL_escher_penrose_stairs: that builder closes N runs
into a Penrose loop (Runs / Run Length / Loop Offset / Second Loop). This one is
a single OPEN flight whose TOP JOIN is wrong. Different device, different defect.

Follows the escher_*.py family convention: package-relative core imports,
register_builder() at import time, every parameter an editable named input.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param,
)


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


def cube(t, x, y):
    """MeshCube whose Size is left for the caller to drive (socket or float)."""
    return N(t, 'GeometryNodeMeshCube', x, y)


def xform(t, x, y, src, sname='Mesh', trans=None, rot=None):
    n = N(t, 'GeometryNodeTransform', x, y)
    link_sockets(t, src.outputs[sname], n.inputs['Geometry'])
    for key, val in (('Translation', trans), ('Rotation', rot)):
        if val is None:
            continue
        if isinstance(val, (tuple, list)):
            n.inputs[key].default_value = tuple(val)
        else:
            link_sockets(t, val, n.inputs[key])
    return n


# ------------------------------------------------------------------- builder

def build_paris_escher_ladder(group_name="GN_PARIS_EscherLadder"):
    """Belvedere ladder: stone flight + mansard landing, join error as a dial."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Ladder Height", 3.2, 1.0, 8.0)
    add_float_param(tree, "Ladder Lean", 0.18, 0.0, 0.6)
    add_int_param(tree, "Rung Count", 12, 4, 40)
    add_float_param(tree, "Ladder Width", 0.75, 0.4, 2.0)
    add_float_param(tree, "Rung Depth", 0.30, 0.10, 0.80)
    add_float_param(tree, "Rung Thickness", 0.05, 0.02, 0.15)
    add_float_param(tree, "Join Error", 0.30, -0.80, 0.80)
    add_int_param(tree, "Floating Steps", 3, 0, 12)
    add_float_param(tree, "Landing Depth", 1.6, 0.5, 4.0)
    add_float_param(tree, "Landing Thickness", 0.18, 0.05, 0.5)
    add_bool_param(tree, "Mansard Landing", True)
    add_bool_param(tree, "Railing", True)
    add_float_param(tree, "Rail Height", 0.95, 0.5, 1.5)

    # ---- flight math -----------------------------------------------------
    # rise = nominal height + join error. The horizontal run follows the
    # NOMINAL height only, so changing Join Error slides the top of the ladder
    # off the landing instead of also moving it - that is what makes the
    # mismatch read as an impossibility rather than a resize.
    rise = mathn(tree, 'ADD', bx - 1700, by + 500,
                 gin.outputs['Ladder Height'], gin.outputs['Join Error'])
    nm1 = mathn(tree, 'SUBTRACT', bx - 1700, by + 380,
                gin.outputs['Rung Count'], 1.0)
    nm1c = mathn(tree, 'MAXIMUM', bx - 1500, by + 380, nm1.outputs[0], 1.0)
    dz = mathn(tree, 'DIVIDE', bx - 1300, by + 500, rise.outputs[0], nm1c.outputs[0])
    run = mathn(tree, 'MULTIPLY', bx - 1700, by + 260,
                gin.outputs['Ladder Height'], gin.outputs['Ladder Lean'])
    dy = mathn(tree, 'DIVIDE', bx - 1300, by + 380, run.outputs[0], nm1c.outputs[0])

    # ---- rungs: one template, instanced along the step vector ------------
    rung = cube(tree, bx - 1300, by + 1200)
    rung_sz = combine(tree, bx - 1300, by + 1320, gin.outputs['Ladder Width'],
                      gin.outputs['Rung Depth'], gin.outputs['Rung Thickness'])
    L(tree, rung_sz, 'Vector', rung, 'Size')
    rung_drop = mathn(tree, 'MULTIPLY', bx - 1500, by + 1200,
                      gin.outputs['Rung Thickness'], -0.5)
    rung_off = combine(tree, bx - 1300, by + 1440, 0.0, 0.0, rung_drop.outputs[0])
    rung_xf = xform(tree, bx - 1100, by + 1200, rung, trans=rung_off.outputs['Vector'])

    line = N(tree, 'GeometryNodeMeshLine', bx - 1300, by + 900)
    line.mode = 'OFFSET'
    L(tree, gin, 'Rung Count', line, 'Count')
    line_off = combine(tree, bx - 1300, by + 1020, 0.0, dy.outputs[0], dz.outputs[0])
    L(tree, line_off, 'Vector', line, 'Offset')

    inst = N(tree, 'GeometryNodeInstanceOnPoints', bx - 900, by + 1200)
    L(tree, line, 'Mesh', inst, 'Points')
    L(tree, rung_xf, 'Geometry', inst, 'Instance')
    rungs_real = N(tree, 'GeometryNodeRealizeInstances', bx - 700, by + 1200)
    L(tree, inst, 'Instances', rungs_real, 'Geometry')

    # ---- stringer: sized to cover only (Rung Count - Floating Steps) -----
    # The rungs keep the full length; the stringer stops early. The top
    # `Floating Steps` treads are therefore unsupported - the floating ladder
    # read - without a second geometry chain or a switch.
    covered = mathn(tree, 'SUBTRACT', bx - 1700, by + 140,
                    gin.outputs['Rung Count'], gin.outputs['Floating Steps'])
    covc = mathn(tree, 'MAXIMUM', bx - 1500, by + 140, covered.outputs[0], 1.0)
    cov_n = mathn(tree, 'SUBTRACT', bx - 1300, by + 140, covc.outputs[0], 1.0)
    cov_n = mathn(tree, 'MAXIMUM', bx - 1150, by + 140, cov_n.outputs[0], 1.0)
    srun = mathn(tree, 'MULTIPLY', bx - 900, by + 140, dy.outputs[0], cov_n.outputs[0])
    srise = mathn(tree, 'MULTIPLY', bx - 900, by + 20, dz.outputs[0], cov_n.outputs[0])
    s2 = mathn(tree, 'MULTIPLY', bx - 700, by + 140, srun.outputs[0], srun.outputs[0])
    r2 = mathn(tree, 'MULTIPLY', bx - 700, by + 20, srise.outputs[0], srise.outputs[0])
    tot = mathn(tree, 'ADD', bx - 550, by + 80, s2.outputs[0], r2.outputs[0])
    slen = mathn(tree, 'SQRT', bx - 400, by + 80, tot.outputs[0])
    ang = mathn(tree, 'ARCTAN2', bx - 550, by - 80, srise.outputs[0], srun.outputs[0])

    spine = cube(tree, bx - 700, by - 320)
    spine_w = mathn(tree, 'ADD', bx - 900, by - 320, gin.outputs['Ladder Width'], 0.10)
    spine_sz = combine(tree, bx - 700, by - 200, spine_w.outputs[0],
                       slen.outputs[0], 0.10)
    L(tree, spine_sz, 'Vector', spine, 'Size')
    spine_rot = combine(tree, bx - 700, by - 80, ang.outputs[0], 0.0, 0.0)
    half_run = mathn(tree, 'MULTIPLY', bx - 900, by - 440, srun.outputs[0], 0.5)
    half_rise = mathn(tree, 'MULTIPLY', bx - 900, by - 560, srise.outputs[0], 0.5)
    spine_z = mathn(tree, 'SUBTRACT', bx - 700, by - 560, half_rise.outputs[0], 0.09)
    spine_tr = combine(tree, bx - 550, by - 440, 0.0,
                       half_run.outputs[0], spine_z.outputs[0])
    spine_xf = xform(tree, bx - 400, by - 320, spine,
                     trans=spine_tr.outputs['Vector'], rot=spine_rot.outputs['Vector'])

    # ---- mansard landing: the honest destination -------------------------
    # The landing sits where the BUILDING says it should: top surface exactly at
    # Ladder Height. The ladder's top is at Ladder Height + Join Error, so any
    # non-zero Join Error is a visible join failure.
    lw = mathn(tree, 'ADD', bx - 1700, by - 800, gin.outputs['Ladder Width'], 0.60)
    land = cube(tree, bx - 1300, by - 800)
    land_sz = combine(tree, bx - 1300, by - 680, lw.outputs[0],
                      gin.outputs['Landing Depth'], gin.outputs['Landing Thickness'])
    L(tree, land_sz, 'Vector', land, 'Size')
    land_half = mathn(tree, 'MULTIPLY', bx - 1500, by - 800,
                      gin.outputs['Landing Thickness'], 0.5)
    land_z = mathn(tree, 'SUBTRACT', bx - 1300, by - 920,
                   gin.outputs['Ladder Height'], land_half.outputs[0])
    land_tr = combine(tree, bx - 1100, by - 800, 0.0,
                      run.outputs[0], land_z.outputs[0])
    land_xf = xform(tree, bx - 900, by - 800, land, trans=land_tr.outputs['Vector'])

    # ---- mansard wedge above the landing (optional) ----------------------
    man = cube(tree, bx - 1500, by - 1400)
    man_sz = combine(tree, bx - 1500, by - 1280, lw.outputs[0],
                     gin.outputs['Landing Depth'], 0.10)
    L(tree, man_sz, 'Vector', man, 'Size')
    man_rot = combine(tree, bx - 1500, by - 1160, math.radians(58.0), 0.0, 0.0)
    man_up = mathn(tree, 'ADD', bx - 1700, by - 1400,
                   gin.outputs['Ladder Height'], 0.42)
    man_tr = combine(tree, bx - 1300, by - 1400, 0.0,
                     run.outputs[0], man_up.outputs[0])
    man_xf = xform(tree, bx - 1100, by - 1400, man,
                   trans=man_tr.outputs['Vector'], rot=man_rot.outputs['Vector'])
    # Optional geometry, house pattern: DeleteGeometry on NOT <toggle>, so an
    # off toggle yields genuinely empty geometry rather than a hidden stub.
    not_man = booln(tree, 'NOT', bx - 1100, by - 1560, gin.outputs['Mansard Landing'])
    man_del = N(tree, 'GeometryNodeDeleteGeometry', bx - 900, by - 1400)
    L(tree, man_xf, 'Geometry', man_del, 'Geometry')
    L(tree, not_man, 0, man_del, 'Selection')

    # ---- wrought-iron handrail (the Guimard line), optional --------------
    rail_z = mathn(tree, 'ADD', bx - 1700, by + 1500,
                   rise.outputs[0], gin.outputs['Rail Height'])
    rail_line = N(tree, 'GeometryNodeCurvePrimitiveLine', bx - 1500, by + 1700)
    rail_start = combine(tree, bx - 1700, by + 1800, 0.0, 0.0,
                         gin.outputs['Rail Height'])
    L(tree, rail_start, 'Vector', rail_line, 'Start')
    rail_end = combine(tree, bx - 1300, by + 1800, 0.0,
                       run.outputs[0], rail_z.outputs[0])
    L(tree, rail_end, 'Vector', rail_line, 'End')
    # Profile must be a CURVE, not a mesh. The house pattern (aesthetic_fx.py)
    # feeds `circle.outputs['Curve']`; a Mesh Circle links without complaint and
    # then Curve to Mesh yields a 2-vertex "rail" with no tube at all. Caught by
    # the vert-count delta in _melodia_health_paris_ladder.py, not by the link
    # recorder - the link really is made, the geometry is just degenerate.
    prof = N(tree, 'GeometryNodeCurvePrimitiveCircle', bx - 1500, by + 1950)
    prof.inputs['Radius'].default_value = 0.03
    try:
        prof.inputs['Resolution'].default_value = 8
    except Exception:
        pass
    c2m = N(tree, 'GeometryNodeCurveToMesh', bx - 1100, by + 1800)
    L(tree, rail_line, 'Curve', c2m, 'Curve')
    L(tree, prof, 'Curve', c2m, 'Profile Curve')
    try:
        c2m.inputs['Fill Caps'].default_value = True
    except Exception:
        pass
    # The line already carries the tilt; only the +/- X offset differs per
    # side, so one instance along a 2-point line makes both rails.
    rail_pts = N(tree, 'GeometryNodeMeshLine', bx - 1500, by + 2150)
    rail_pts.mode = 'OFFSET'
    rail_pts.inputs['Count'].default_value = 2
    rail_gap = mathn(tree, 'ADD', bx - 1700, by + 2150,
                     gin.outputs['Ladder Width'], 0.12)
    rail_off = combine(tree, bx - 1500, by + 2250, rail_gap.outputs[0], 0.0, 0.0)
    L(tree, rail_off, 'Vector', rail_pts, 'Offset')
    rail_inst = N(tree, 'GeometryNodeInstanceOnPoints', bx - 900, by + 2000)
    L(tree, rail_pts, 'Mesh', rail_inst, 'Points')
    L(tree, c2m, 'Mesh', rail_inst, 'Instance')
    rail_real = N(tree, 'GeometryNodeRealizeInstances', bx - 700, by + 2000)
    L(tree, rail_inst, 'Instances', rail_real, 'Geometry')
    # re-centre the pair on the ladder: -(Width/2) - 0.06
    rail_half = mathn(tree, 'MULTIPLY', bx - 900, by + 2200,
                      gin.outputs['Ladder Width'], -0.5)
    rail_dx = mathn(tree, 'SUBTRACT', bx - 700, by + 2200,
                    rail_half.outputs[0], 0.06)
    rail_tr = combine(tree, bx - 500, by + 2200, rail_dx.outputs[0], 0.0, 0.0)
    rail_xf = xform(tree, bx - 300, by + 2000, rail_real, sname='Geometry',
                    trans=rail_tr.outputs['Vector'])
    not_rail = booln(tree, 'NOT', bx - 300, by - 2300, gin.outputs['Railing'])
    rail_del = N(tree, 'GeometryNodeDeleteGeometry', bx - 100, by + 2000)
    L(tree, rail_xf, 'Geometry', rail_del, 'Geometry')
    L(tree, not_rail, 0, rail_del, 'Selection')

    # ---- join ------------------------------------------------------------
    j1 = N(tree, 'GeometryNodeJoinGeometry', bx + 150, by + 400)
    L(tree, rungs_real, 'Geometry', j1, 'Geometry')
    L(tree, spine_xf, 'Geometry', j1, 'Geometry')
    L(tree, land_xf, 'Geometry', j1, 'Geometry')
    j2 = N(tree, 'GeometryNodeJoinGeometry', bx + 300, by + 200)
    L(tree, j1, 'Geometry', j2, 'Geometry')
    L(tree, man_del, 'Geometry', j2, 'Geometry')
    L(tree, rail_del, 'Geometry', j2, 'Geometry')
    L(tree, j2, 'Geometry', gout, 'Geometry')

    return tree, gin, gout


# ------------------------------------------------- addon registration

try:
    from .core import register_builder  # noqa: E402
    register_builder(
        'GN_PARIS_EscherLadder', build_paris_escher_ladder,
        'PARIS Escher Ladder',
        'Belvedere ladder: stone flight + mansard landing. Join Error dials the '
        'impossibility; Floating Steps hang the top treads.',
        category='escher',
    )
    print('[paris_escher_ladder] registered GN_PARIS_EscherLadder')
except ImportError:
    print('[paris_escher_ladder] standalone mode (no core registry)')


if __name__ == '__main__':
    build_paris_escher_ladder()
