"""Paris Track A builders - the two pending Maison Impossible pack slots.

GN_PARIS_FountainLoop   (MI_COUR_D_HONNEUR pack, preset MI_COURTYARD_DAY)
GN_PARIS_DayNightFacade (MI_MAISON_NUIT pack, preset MI_NUIT)

FountainLoop is the courtyard's self-feeding basin: a stone cylinder, a water
disc, a central spout, and the Escher read - a closed water ring that rises
from the spout and falls back into itself. `Wobble` is the only effect dial
and is neutral at 0.0 (multiply wiring through SINE of the ring angle); every
other dial is structural.

DayNightFacade is the duality plate as a standing facade grid. Each tile face
takes its parity ((col + row) mod 2) and pops by

    light tiles:  Relief * (1 - Duality)
    dark  tiles:  Relief * Duality

so Duality 0.0 is the day plate (light tiles forward), 1.0 the night plate
(dark tiles forward, the Maison Nuit read), and 0.5 the flat Escher plate.
Pure per-face math - no Switch node, no second geometry chain.

Follows the paris_* family convention: package-relative core imports,
register_builder() at import time, every parameter an editable named input.
"""

from __future__ import annotations

import math

from .core import (
    safe_node, link_sockets, sock, new_geometry_tree,
    add_float_param, add_int_param,
)


# ------------------------------------------------------------------ shorthand

def N(t, bl, x=0, y=0):
    return safe_node(t, bl, (x, y))


def L(t, a, sa, b, sb):
    """Link node output `sa` to node input `sb` (name or index, house style)."""
    link_sockets(t, a.outputs[sa], b.inputs[sb])


def mathn(t, op, x, y, a=None, b=None):
    m = N(t, 'ShaderNodeMath', x, y)
    m.operation = op
    if a is not None:
        link_sockets(t, a, m.inputs[0])
    if b is not None:
        link_sockets(t, b, m.inputs[1])
    return m


def num(t, value, x, y):
    v = N(t, 'ShaderNodeValue', x, y)
    v.outputs['Value'].default_value = value
    return v.outputs['Value']


def xform(t, x, y, geo, trans=None, rot=None):
    tr = N(t, 'GeometryNodeTransform', x, y)
    link_sockets(t, geo, tr.inputs['Geometry'])
    if trans is not None:
        link_sockets(t, trans, sock(tr, 'Translation'))
    if rot is not None:
        tr.inputs['Rotation'].default_value = rot
    return tr


def combine(t, x, y, vx=0.0, vy=0.0, vz=0.0):
    c = N(t, 'ShaderNodeCombineXYZ', x, y)
    c.inputs['X'].default_value = vx
    c.inputs['Y'].default_value = vy
    c.inputs['Z'].default_value = vz
    return c


# ------------------------------------------------------- GN_PARIS_FountainLoop

def build_paris_fountain_loop():
    tree, gin, gout = new_geometry_tree('GN_PARIS_FountainLoop')

    add_float_param(tree, 'Basin Radius', 0.9, 0.2, 3.0,
                    'Outer radius of the stone basin.')
    add_float_param(tree, 'Basin Depth', 0.35, 0.1, 1.5,
                    'Height of the basin wall.')
    add_float_param(tree, 'Loop Rise', 0.85, 0.2, 3.0,
                    'Height of the self-feeding ring above the basin rim.')
    add_float_param(tree, 'Stream Radius', 0.06, 0.01, 0.2,
                    'Thickness of the spout and the water ring.')
    add_float_param(tree, 'Wobble', 0.0, 0.0, 0.25,
                    'Radial breathing of the water ring. 0.0 is still water.')
    add_int_param(tree, 'Basin Segments', 48, 8, 128,
                  'Radial resolution of basin and ring.')

    r_basin = gin.outputs['Basin Radius']
    d_basin = gin.outputs['Basin Depth']
    rise = gin.outputs['Loop Rise']
    r_stream = gin.outputs['Stream Radius']
    wobble = gin.outputs['Wobble']
    segs = gin.outputs['Basin Segments']

    # basin: filled stone cylinder
    basin = N(tree, 'GeometryNodeMeshCylinder', -900, 400)
    link_sockets(tree, segs, sock(basin, 'Vertices'))
    link_sockets(tree, r_basin, sock(basin, 'Radius'))
    link_sockets(tree, d_basin, sock(basin, 'Depth'))

    # water disc: slightly inset cylinder sitting near the rim
    r_water = mathn(tree, 'MULTIPLY', -650, 150, r_basin, num(tree, 0.92, -800, 150))
    z_water = mathn(tree, 'MULTIPLY', -650, 0, d_basin, num(tree, 0.9, -800, 0))
    water = N(tree, 'GeometryNodeMeshCylinder', -400, 150)
    link_sockets(tree, segs, sock(water, 'Vertices'))
    link_sockets(tree, r_water.outputs[0], sock(water, 'Radius'))
    water.inputs['Depth'].default_value = 0.04
    water_xf = xform(tree, -150, 150, water.outputs['Mesh'])
    # (Translation Z arrives as a float; feed it through CombineXYZ)
    c_water = combine(tree, -50, 0)
    link_sockets(tree, z_water.outputs[0], c_water.inputs['Z'])
    link_sockets(tree, c_water.outputs['Vector'], sock(water_xf, 'Translation'))

    # spout column: from basin floor up through the ring
    h_col = mathn(tree, 'ADD', -650, -200, d_basin, rise)
    h_half = mathn(tree, 'MULTIPLY', -450, -300, h_col.outputs[0], num(tree, 0.5, -600, -350))
    column = N(tree, 'GeometryNodeMeshCylinder', -400, -250)
    link_sockets(tree, r_stream, sock(column, 'Radius'))
    link_sockets(tree, h_col.outputs[0], sock(column, 'Depth'))
    c_col = combine(tree, -150, -350)
    link_sockets(tree, h_half.outputs[0], c_col.inputs['Z'])
    column_xf = xform(tree, 50, -250, column.outputs['Mesh'],
                      trans=c_col.outputs['Vector'])

    # the self-feeding ring: swept-circle torus (5.2 GN has no torus primitive)
    r_major = mathn(tree, 'MULTIPLY', -650, -550, r_basin, num(tree, 0.55, -800, -600))
    path = N(tree, 'GeometryNodeCurvePrimitiveCircle', -400, -550)
    if hasattr(path, 'mode'):
        path.mode = 'RADIUS'
    link_sockets(tree, segs, sock(path, 'Resolution'))
    link_sockets(tree, r_major.outputs[0], sock(path, 'Radius'))
    prof = N(tree, 'GeometryNodeCurvePrimitiveCircle', -400, -700)
    if hasattr(prof, 'mode'):
        prof.mode = 'RADIUS'
    link_sockets(tree, r_stream, sock(prof, 'Radius'))
    prof.inputs['Resolution'].default_value = 12
    sweep = N(tree, 'GeometryNodeCurveToMesh', 100, -600)
    link_sockets(tree, path.outputs['Curve'], sock(sweep, 'Curve'))
    link_sockets(tree, prof.outputs['Curve'], sock(sweep, 'Profile Curve'))
    sweep.inputs['Fill Caps'].default_value = True
    z_ring = mathn(tree, 'ADD', -650, -750, d_basin, rise)
    c_ring = combine(tree, -150, -750)
    link_sockets(tree, z_ring.outputs[0], c_ring.inputs['Z'])
    ring_xf = xform(tree, 250, -550, sweep.outputs['Mesh'],
                    trans=c_ring.outputs['Vector'])

    # wobble: radial SINE breathing of the ring, neutral at 0.0
    pos = N(tree, 'GeometryNodeInputPosition', 200, -900)
    xy = N(tree, 'ShaderNodeSeparateXYZ', 350, -900)
    link_sockets(tree, pos.outputs['Position'], xy.inputs['Vector'])
    ang = mathn(tree, 'ARCTAN2', 500, -900, xy.outputs['Y'], xy.outputs['X'])
    ang6 = mathn(tree, 'MULTIPLY', 650, -900, ang.outputs[0], num(tree, 6.0, 550, -1000))
    sine = mathn(tree, 'SINE', 800, -900, ang6.outputs[0])
    cosn = mathn(tree, 'COSINE', 800, -1050, ang6.outputs[0])
    amp = mathn(tree, 'MULTIPLY', 950, -900, sine.outputs[0], wobble)
    ax = mathn(tree, 'MULTIPLY', 1100, -850, cosn.outputs[0], amp.outputs[0])
    ay = mathn(tree, 'MULTIPLY', 1100, -1000, sine.outputs[0], amp.outputs[0])
    off = combine(tree, 1250, -950)
    link_sockets(tree, ax.outputs[0], off.inputs['X'])
    link_sockets(tree, ay.outputs[0], off.inputs['Y'])
    wob = N(tree, 'GeometryNodeSetPosition', 1400, -700)
    link_sockets(tree, ring_xf.outputs['Geometry'], sock(wob, 'Geometry'))
    link_sockets(tree, off.outputs['Vector'], sock(wob, 'Offset'))

    # join: basin + water + column + (wobbled) ring
    j1 = N(tree, 'GeometryNodeJoinGeometry', 1650, 200)
    link_sockets(tree, basin.outputs['Mesh'], sock(j1, 'Geometry'))
    link_sockets(tree, water_xf.outputs['Geometry'], sock(j1, 'Geometry'))
    j2 = N(tree, 'GeometryNodeJoinGeometry', 1800, 200)
    link_sockets(tree, j1.outputs['Geometry'], sock(j2, 'Geometry'))
    link_sockets(tree, column_xf.outputs['Geometry'], sock(j2, 'Geometry'))
    j3 = N(tree, 'GeometryNodeJoinGeometry', 1950, 200)
    link_sockets(tree, j2.outputs['Geometry'], sock(j3, 'Geometry'))
    link_sockets(tree, wob.outputs['Geometry'], sock(j3, 'Geometry'))
    link_sockets(tree, j3.outputs['Geometry'], gout.inputs['Geometry'])

    return tree, gin, gout


# ---------------------------------------------------- GN_PARIS_DayNightFacade

def build_paris_day_night_facade():
    tree, gin, gout = new_geometry_tree('GN_PARIS_DayNightFacade')

    add_float_param(tree, 'Facade Width', 3.0, 0.5, 12.0,
                    'Total width of the facade grid.')
    add_float_param(tree, 'Facade Height', 3.2, 0.5, 12.0,
                    'Total height of the facade grid.')
    add_int_param(tree, 'Tiles X', 12, 2, 96,
                  'Tile columns across the width.')
    add_int_param(tree, 'Tiles Y', 14, 2, 96,
                  'Tile rows up the height.')
    add_float_param(tree, 'Relief', 0.06, 0.0, 0.3,
                    'How far the winning tiles stand proud of the plate.')
    add_float_param(tree, 'Duality', 0.5, 0.0, 1.0,
                    '0.0 day plate (light tiles forward), 1.0 night plate '
                    '(dark tiles forward), 0.5 flat Escher plate.')

    width = gin.outputs['Facade Width']
    height = gin.outputs['Facade Height']
    tiles_x = gin.outputs['Tiles X']
    tiles_y = gin.outputs['Tiles Y']
    relief = gin.outputs['Relief']
    duality = gin.outputs['Duality']

    # standing grid: authored flat, stood up 90 degrees about X
    grid = N(tree, 'GeometryNodeMeshGrid', -900, 300)
    link_sockets(tree, width, sock(grid, 'Size X'))
    link_sockets(tree, height, sock(grid, 'Size Y'))
    vx = mathn(tree, 'ADD', -650, 150, tiles_x, num(tree, 1.0, -800, 100))
    vy = mathn(tree, 'ADD', -650, 0, tiles_y, num(tree, 1.0, -800, -50))
    link_sockets(tree, vx.outputs[0], sock(grid, 'Vertices X'))
    link_sockets(tree, vy.outputs[0], sock(grid, 'Vertices Y'))
    stood = xform(tree, -400, 300, grid.outputs['Mesh'],
                  rot=(math.radians(90.0), 0.0, 0.0))

    # per-face tile parity on the STOOD grid (x across, z up)
    pos = N(tree, 'GeometryNodeInputPosition', -150, 300)
    sep = N(tree, 'ShaderNodeSeparateXYZ', 0, 300)
    link_sockets(tree, pos.outputs['Position'], sep.inputs['Vector'])
    half_w = mathn(tree, 'MULTIPLY', 150, 450, width, num(tree, 0.5, 50, 500))
    half_h = mathn(tree, 'MULTIPLY', 150, -150, height, num(tree, 0.5, 50, -100))
    tw = mathn(tree, 'DIVIDE', 300, 450, width, tiles_x)
    th = mathn(tree, 'DIVIDE', 300, -150, height, tiles_y)
    u = mathn(tree, 'ADD', 450, 450, sep.outputs['X'], half_w.outputs[0])
    v = mathn(tree, 'ADD', 450, -150, sep.outputs['Z'], half_h.outputs[0])
    div_u = mathn(tree, 'DIVIDE', 600, 500, u.outputs[0], tw.outputs[0])
    div_v = mathn(tree, 'DIVIDE', 600, -200, v.outputs[0], th.outputs[0])
    cu = mathn(tree, 'FLOOR', 750, 500, div_u.outputs[0])
    cv = mathn(tree, 'FLOOR', 750, -200, div_v.outputs[0])
    colrow = mathn(tree, 'ADD', 900, 150, cu.outputs[0], cv.outputs[0])
    parity = mathn(tree, 'MODULO', 1050, 150, colrow.outputs[0], num(tree, 2.0, 950, 50))

    # winning-tile offsets: A = Relief*(1-Duality), B = Relief*Duality
    one_minus = mathn(tree, 'SUBTRACT', 300, -400, num(tree, 1.0, 200, -450), duality)
    a_off = mathn(tree, 'MULTIPLY', 450, -400, relief, one_minus.outputs[0])
    b_off = mathn(tree, 'MULTIPLY', 450, -550, relief, duality)
    delta = mathn(tree, 'SUBTRACT', 600, -500, b_off.outputs[0], a_off.outputs[0])
    scaled = mathn(tree, 'MULTIPLY', 750, -500, delta.outputs[0], parity.outputs[0])
    mag = mathn(tree, 'ADD', 900, -450, a_off.outputs[0], scaled.outputs[0])

    # offset each face along its own normal
    nrm = N(tree, 'GeometryNodeInputNormal', 1050, -450)
    scaled_v = N(tree, 'ShaderNodeVectorMath', 1200, -450)
    scaled_v.operation = 'SCALE'
    link_sockets(tree, nrm.outputs['Normal'], scaled_v.inputs[0])
    link_sockets(tree, mag.outputs[0], sock(scaled_v, 'Scale'))
    sp = N(tree, 'GeometryNodeSetPosition', 1350, 300)
    link_sockets(tree, stood.outputs['Geometry'], sock(sp, 'Geometry'))
    link_sockets(tree, scaled_v.outputs['Vector'], sock(sp, 'Offset'))

    link_sockets(tree, sp.outputs['Geometry'], gout.inputs['Geometry'])

    return tree, gin, gout


# ------------------------------------------------- addon registration

try:
    from .core import register_builder  # noqa: E402
    register_builder(
        'GN_PARIS_FountainLoop', build_paris_fountain_loop,
        'PARIS Fountain Loop',
        'Courtyard self-feeding basin: stone cylinder, water disc, spout, and '
        'a closed water ring - the Escher waterfall read in the round. '
        'Wobble breathes the ring; 0.0 is still water.',
        category='structures',
    )
    register_builder(
        'GN_PARIS_DayNightFacade', build_paris_day_night_facade,
        'PARIS Day-Night Facade',
        'Duality plate as a standing facade grid. Per-tile parity pops light '
        'or dark tiles; Duality slides the day plate to the night plate '
        'through the flat Escher read.',
        category='structures',
    )
    print('[paris_track_a] registered GN_PARIS_FountainLoop + GN_PARIS_DayNightFacade')
except ImportError:
    print('[paris_track_a] standalone mode (no core registry)')


if __name__ == '__main__':
    build_paris_fountain_loop()
    build_paris_day_night_facade()
