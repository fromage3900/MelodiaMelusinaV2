"""Greybox / Level-Design GN group builders — absorbed from the monolith (P2).

Parametric blockout pieces for rapid AAA level prototyping. Each builder uses
plain Python variables for procedural logic (matching monolith defaults) and
exposes group-input sockets via add_float_param/add_int_param for UI/dispatch.
Helper functions (_gb_box, _gb_join, _gb_bool_diff, etc.) are ported as local
helpers using safe_node, link_sockets, sock, and color_node from core.

Ported builders (39 total):
  greybox_room, greybox_corridor, greybox_ramp, greybox_platform,
  greybox_cover, greybox_catwalk, greybox_pillar_hall, greybox_stair_block,
  greybox_doorway, greybox_arena, greybox_tower, greybox_pipe_run,
  greybox_corridor_bend, greybox_corridor_cross, greybox_corridor_t,
  greybox_corridor_door_end, greybox_combat_room, greybox_room_composite,
  greybox_elevator_shaft,
  gb_corridor_arc, gb_corridor_arc_cross, gb_escher_belvedere,
  gb_escher_gravity_shift, gb_escher_penrose_loop, gb_escher_recursive_room,
  gb_escher_relativity, gb_escher_waterfall, gb_room_apsidal, gb_room_circular,
  gb_room_rotunda, gb_umemoto_fortress_room, gb_umemoto_lattice_block,
  gb_umemoto_terrace, gb_umemoto_vault_cluster, gb_woods_freespace,
  gb_woods_harpsichord, gb_woods_parasite, gb_woods_ribs, gb_woods_war_scar
"""

from __future__ import annotations

import math
import random as _random

import bpy

from .core import (
    safe_node, link_sockets, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param,
    make_group_input, register_builder, sock,
)


# ═══════════════════════════════════════════════════════════════════════
# Local helper functions (ported from monolith _gb_*, _arc_*, etc.)
# ═══════════════════════════════════════════════════════════════════════

def _gb_box(tree, size, loc_xyz, x, y, label="level"):
    """Helper: a MeshCube of `size`=(sx,sy,sz) translated to `loc_xyz`.
    Returns the translated geometry socket."""
    cube = safe_node(tree, 'GeometryNodeMeshCube', (x, y))
    if cube is None:
        return None
    try:
        cube.inputs['Size'].default_value = size
    except Exception:
        pass
    color_node(cube, label)
    tr = safe_node(tree, 'GeometryNodeTransform', (x + 200, y))
    if tr is None:
        return cube.outputs['Mesh']
    try:
        tr.inputs['Translation'].default_value = loc_xyz
    except Exception:
        pass
    link_sockets(tree, cube.outputs['Mesh'], tr.inputs['Geometry'])
    color_node(tr, label)
    return tr.outputs['Geometry']


def _gb_box_node(tree, size, loc_xyz, rot_xyz, x, y, label="level"):
    """Helper: a MeshCube with translation AND rotation. Returns geom socket."""
    cube = safe_node(tree, 'GeometryNodeMeshCube', (x, y))
    if cube is None:
        return None
    try:
        cube.inputs['Size'].default_value = size
    except Exception:
        pass
    color_node(cube, label)
    tr = safe_node(tree, 'GeometryNodeTransform', (x + 200, y))
    if tr is None:
        return cube.outputs['Mesh']
    try:
        tr.inputs['Translation'].default_value = loc_xyz
        tr.inputs['Rotation'].default_value = rot_xyz
    except Exception:
        pass
    link_sockets(tree, cube.outputs['Mesh'], tr.inputs['Geometry'])
    color_node(tr, label)
    return tr.outputs['Geometry']


def _gb_join(tree, parts, x, y=0, label="output"):
    """Join a list of geometry sockets. Returns a single socket (or None)."""
    parts = [p for p in parts if p is not None]
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0]
    join = safe_node(tree, 'GeometryNodeJoinGeometry', (x, y))
    if join is None:
        return parts[0]
    for p in parts:
        link_sockets(tree, p, join.inputs['Geometry'])
    color_node(join, label)
    return join.outputs['Geometry']


def _gb_bool_diff(tree, base_geom, cutters, x, y=0):
    """Boolean DIFFERENCE: base_geom minus the list of cutter sockets."""
    cutters = [c for c in cutters if c is not None]
    if base_geom is None or not cutters:
        return base_geom
    boolean = safe_node(tree, 'GeometryNodeMeshBoolean', (x, y))
    if boolean is None:
        return base_geom
    try:
        boolean.operation = 'DIFFERENCE'
    except Exception:
        pass
    try:
        boolean.solver = 'EXACT'
    except Exception:
        pass
    a_in = sock(boolean, 'Mesh 1', 'Mesh', 'Geometry')
    b_in = None
    try:
        b_in = boolean.inputs.get('Mesh 2')
    except Exception:
        b_in = None
    if a_in is None:
        geos = [s for s in boolean.inputs if 'GEOMETRY' in str(getattr(s, 'type', '')).upper()]
        if geos:
            a_in = geos[0]
            b_in = geos[1] if len(geos) > 1 else geos[0]
        else:
            a_in = boolean.inputs[0]
            b_in = boolean.inputs[1] if len(boolean.inputs) > 1 else a_in
    if b_in is None:
        b_in = a_in
    link_sockets(tree, base_geom, a_in)
    for c in cutters:
        link_sockets(tree, c, b_in)
    color_node(boolean, "level")
    out = sock(boolean, 'Mesh', 'Geometry', outputs=True)
    if out is None:
        out = boolean.outputs[0]
    return out


def _move(tree, geom, loc, translation=(0, 0, 0), rotation=(0, 0, 0),
          scale=(1, 1, 1), label="level"):
    """Wrap a geometry socket in a Transform node."""
    t = safe_node(tree, 'GeometryNodeTransform', loc)
    try:
        t.inputs['Translation'].default_value = translation
        t.inputs['Rotation'].default_value = rotation
        t.inputs['Scale'].default_value = scale
    except Exception:
        pass
    if geom is not None:
        link_sockets(tree, geom, t.inputs['Geometry'])
    color_node(t, label)
    return t.outputs['Geometry']


def _join_all(tree, pieces, loc=(0, 0), label="output", weld=0.01):
    """Join all `pieces` into one mesh and weld vertices within `weld` distance."""
    j = safe_node(tree, 'GeometryNodeJoinGeometry', loc)
    for p in pieces:
        if p is not None:
            link_sockets(tree, p, j.inputs['Geometry'])
    color_node(j, label)
    out = j.outputs['Geometry']
    if weld > 0:
        mbd = safe_node(tree, 'GeometryNodeMergeByDistance', (loc[0] + 250, loc[1]))
        if mbd is not None:
            try:
                mbd.inputs['Distance'].default_value = weld
            except Exception:
                pass
            link_sockets(tree, out, mbd.inputs['Geometry'])
            color_node(mbd, "optimize")
            return mbd.outputs['Geometry']
    return out


def _cube(tree, loc, sx, sy, sz, label="tower"):
    """Make a MeshCube with the vector `Size` socket."""
    c = safe_node(tree, 'GeometryNodeMeshCube', loc)
    if c is None:
        return None
    c.inputs['Size'].default_value = (sx, sy, sz)
    color_node(c, label)
    return c.outputs['Mesh']


def _finalize_building(tree, pieces, loc=(0, 0), label="output"):
    """Heavier weld for monolithic buildings."""
    return _join_all(tree, pieces, loc=loc, label=label, weld=0.3)


def _arc_floor_disc(tree, radius, t, start_ang, sweep_ang, base_x, y_off, label="level"):
    """Filled arc sector slab of thickness t.

    A FULL-TURN sweep (|sweep| >= tau) puts the arc's start and end points on
    top of each other; Fill Curve then closes an NGON across the coincident
    pair and emits a zero-area face. Measured on `MEL_gb_room_circular`:
    1/152 faces degenerate, all of its verts at exactly (R, 0, 0) — the arc
    seam. Shortening the sweep by one angular step leaves a sub-micron gap
    that the fill closes as a normal sliver, and the disc is unchanged
    visually (0/152 degenerate, 154 vs 155 verts). A cyclic spline does NOT
    fix it (measured: still 1 degen) because the duplicate point is still
    there.
    """
    import math as _m
    arc = safe_node(tree, 'GeometryNodeCurveArc', (base_x, y_off))
    if arc is None:
        return None
    res = max(12, int(abs(sweep_ang) / _m.pi * 20))
    if abs(sweep_ang) >= _m.tau - 1e-6:
        sweep_ang = _m.copysign(_m.tau - (_m.tau / res), sweep_ang)
    try:
        arc.mode = 'RADIUS'
        arc.inputs['Radius'].default_value = radius
        arc.inputs['Start Angle'].default_value = start_ang
        arc.inputs['Sweep Angle'].default_value = sweep_ang
        arc.inputs['Resolution'].default_value = res
    except Exception:
        pass
    fill = safe_node(tree, 'GeometryNodeFillCurve', (base_x + 200, y_off))
    if fill is None:
        return None
    try:
        fill.mode = 'NGONS'
    except Exception:
        pass
    link_sockets(tree, arc.outputs['Curve'], fill.inputs['Curve'])
    color_node(fill, label)
    ext = safe_node(tree, 'GeometryNodeExtrudeMesh', (base_x + 400, y_off))
    if ext:
        ext.mode = 'FACES'
        try:
            ext.inputs['Offset Scale'].default_value = t
        except Exception:
            pass
        link_sockets(tree, fill.outputs['Mesh'], ext.inputs['Mesh'])
        color_node(ext, label)
        if t > 0:
            floor_z = _move(tree, ext.outputs['Mesh'], (base_x + 600, y_off),
                            translation=(0, 0, -t), label=label)
            if floor_z:
                return floor_z
        return ext.outputs['Mesh']
    return fill.outputs['Mesh']


# ═══════════════════════════════════════════════════════════════════════
# GREYBOX BUILDERS — each returns (tree, gin, gout)
#
# Pattern: plain Python variables for procedural logic (matching monolith
# defaults), group-input sockets for UI exposure.
# ═══════════════════════════════════════════════════════════════════════

def build_greybox_room(group_name="MEL_greybox_room"):
    """Parametric room shell: floor slab + 4 perimeter walls + optional ceiling."""
    tree, gin, gout = new_geometry_tree(group_name)

    W = 8.0
    D = 6.0
    H = 3.5
    t = 0.3

    add_float_param(tree, "Width", W, 0.5, 100.0)
    add_float_param(tree, "Depth", D, 0.5, 100.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_bool_param(tree, "Ceiling", False)

    parts = []
    wz = t + (H - t) * 0.5
    wh = H - t
    floor = _gb_box(tree, (W, D, t), (0, 0, t * 0.5), 0, 0)
    if floor:
        parts.append(floor)
    result = _gb_join(tree, parts, 1600, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_greybox_corridor(group_name="MEL_legacy_greybox_corridor"):
    """Straight corridor segment: floor + 2 side walls + ceiling kit + trim bands."""
    tree, gin, gout = new_geometry_tree(group_name)

    L = 8.0
    W = 3.0
    H = 3.5
    t = 0.3

    add_float_param(tree, "Length", L, 0.5, 100.0)
    add_float_param(tree, "Width", W, 0.5, 50.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_bool_param(tree, "Ceiling", True)

    parts = []
    floor = _gb_box(tree, (W, L, t), (0, 0, t * 0.5), 0, 0)
    if floor:
        parts.append(floor)
    wall_z = t + (H - t) * 0.5
    wall_h = H - t
    lw = _gb_box(tree, (t, L, wall_h), (-W * 0.5 + t * 0.5, 0, wall_z), 0, 300)
    rw = _gb_box(tree, (t, L, wall_h), (W * 0.5 - t * 0.5, 0, wall_z), 0, 600)
    if lw:
        parts.append(lw)
    if rw:
        parts.append(rw)
    result = _gb_join(tree, parts, 1600, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_greybox_ramp(group_name="MEL_greybox_ramp"):
    """Inclined ramp blockout: a tilted slab + optional side curbs."""
    tree, gin, gout = new_geometry_tree(group_name)

    L = 6.0
    W = 3.0
    rise = 3.0
    t = 0.35

    add_float_param(tree, "Length", L, 0.5, 100.0)
    add_float_param(tree, "Width", W, 0.5, 50.0)
    add_float_param(tree, "Rise", rise, 0.0, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_bool_param(tree, "Curbs", True)

    parts = []
    angle = math.atan2(rise, L)
    slab_len = math.sqrt(L * L + rise * rise)
    slab = _gb_box_node(tree, (W, slab_len, t),
                        (0, 0, rise * 0.5),
                        (angle, 0, 0),
                        0, 0)
    if slab:
        parts.append(slab)
    result = _gb_join(tree, parts, 1200, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_greybox_platform(group_name="MEL_greybox_platform"):
    """Raised platform / mezzanine: top slab on 4 corner legs."""
    tree, gin, gout = new_geometry_tree(group_name)

    W = 5.0
    D = 5.0
    H = 3.0
    t = 0.3
    leg = 0.4

    add_float_param(tree, "Width", W, 0.5, 100.0)
    add_float_param(tree, "Depth", D, 0.5, 100.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_float_param(tree, "Leg Thickness", leg, 0.01, 2.0)
    add_bool_param(tree, "Railings", True)

    parts = []
    deck = _gb_box(tree, (W, D, t), (0, 0, H - t * 0.5), 0, 0)
    if deck:
        parts.append(deck)
    leg_h = H - t
    for i, (sx, sy) in enumerate([(-1, -1), (1, -1), (1, 1), (-1, 1)]):
        lg = _gb_box(tree, (leg, leg, leg_h),
                     (sx * (W * 0.5 - leg * 0.5),
                      sy * (D * 0.5 - leg * 0.5),
                      leg_h * 0.5),
                     0, 300 + i * 200)
        if lg:
            parts.append(lg)
    result = _gb_join(tree, parts, 1400, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_greybox_cover(group_name="MEL_greybox_cover"):
    """Cover block for shooter prototyping."""
    tree, gin, gout = new_geometry_tree(group_name)

    W = 2.0
    H = 1.2
    t = 0.5

    add_float_param(tree, "Width", W, 0.1, 20.0)
    add_float_param(tree, "Height", H, 0.1, 10.0)
    add_float_param(tree, "Depth", t, 0.01, 5.0)

    parts = []
    body = _gb_box(tree, (W, t, H), (0, 0, H * 0.5), 0, 0)
    if body:
        parts.append(body)
    lip = _gb_box(tree, (W * 1.1, t * 1.25, H * 0.12),
                  (0, 0, H + H * 0.06), 0, 300, "level")
    if lip:
        parts.append(lip)
    foot = _gb_box(tree, (W * 1.08, t * 1.18, H * 0.10),
                   (0, 0, H * 0.05), 0, 600, "level")
    if foot:
        parts.append(foot)
    result = _gb_join(tree, parts, 1000, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_greybox_catwalk(group_name="MEL_greybox_catwalk"):
    """Industrial catwalk: grated deck + 2 railings + support posts."""
    tree, gin, gout = new_geometry_tree(group_name)

    L = 8.0
    W = 1.6
    H = 3.0
    t = 0.18

    add_float_param(tree, "Length", L, 0.5, 100.0)
    add_float_param(tree, "Width", W, 0.1, 20.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_bool_param(tree, "Railings", True)

    parts = []
    deck = _gb_box(tree, (W, L, t), (0, 0, H - t * 0.5), 0, 0)
    if deck:
        parts.append(deck)
    post_t = t * 1.6
    n_posts = max(2, int(L / 3.0) + 1)
    for i in range(n_posts):
        yy = -L * 0.5 + (i / max(1, n_posts - 1)) * L
        for sx in (-1, 1):
            post = _gb_box(tree, (post_t, post_t, H - t),
                           (sx * (W * 0.5 - post_t * 0.6), yy, (H - t) * 0.5),
                           300, 300 + i * 80)
            if post:
                parts.append(post)
    result = _gb_join(tree, parts, 1600, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_greybox_pillar_hall(group_name="MEL_greybox_pillar_hall"):
    """Hypostyle hall blockout: grid of columns + floor + flat roof slab."""
    tree, gin, gout = new_geometry_tree(group_name)

    cols_x = 4
    cols_y = 6
    spacing = 3.0
    H = 5.0
    t = 0.3
    col_r = 0.5

    add_int_param(tree, "Columns X", cols_x, 2, 20)
    add_int_param(tree, "Columns Y", cols_y, 2, 20)
    add_float_param(tree, "Spacing", spacing, 0.5, 20.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_float_param(tree, "Column Radius", col_r, 0.01, 5.0)

    parts = []
    span_x = (cols_x - 1) * spacing
    span_y = (cols_y - 1) * spacing
    pad = spacing * 0.8
    fw = span_x + pad * 2
    fd = span_y + pad * 2
    floor = _gb_box(tree, (fw, fd, t), (0, 0, -t * 0.5), 0, 0)
    if floor:
        parts.append(floor)
    roof = _gb_box(tree, (fw, fd, t), (0, 0, H - t * 0.5), 0, 300, "ceiling")
    if roof:
        parts.append(roof)
    idx = 0
    for ix in range(cols_x):
        for iy in range(cols_y):
            cx = -span_x * 0.5 + ix * spacing
            cy = -span_y * 0.5 + iy * spacing
            col_geom = _gb_box(tree, (col_r * 1.6, col_r * 1.6, H),
                               (cx, cy, H * 0.5), 600, 600 + idx * 40, "pillar")
            if col_geom:
                parts.append(col_geom)
            idx += 1
    result = _gb_join(tree, parts, 1600, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_greybox_stair_block(group_name="MEL_greybox_stair_block"):
    """Blockout staircase: solid stepped wedge + side stringer walls."""
    tree, gin, gout = new_geometry_tree(group_name)

    steps = 10
    rise = 0.2
    run_ = 0.3
    W = 2.4
    t = 0.25

    add_int_param(tree, "Steps", steps, 2, 50)
    add_float_param(tree, "Rise", rise, 0.01, 2.0)
    add_float_param(tree, "Run", run_, 0.01, 2.0)
    add_float_param(tree, "Width", W, 0.1, 20.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_bool_param(tree, "Curbs", True)
    add_bool_param(tree, "Landing", True)

    parts = []
    total_rise = steps * rise
    total_run = steps * run_
    for i in range(steps):
        z_top = (i + 1) * rise
        y0 = i * run_
        step_box = _gb_box(tree, (W, run_, z_top),
                           (0, y0 + run_ * 0.5 - total_run * 0.5, z_top * 0.5),
                           0, i * 90)
        if step_box:
            parts.append(step_box)
    result = _gb_join(tree, parts, 1600, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_greybox_doorway(group_name="MEL_greybox_doorway"):
    """Freestanding doorway / portal frame."""
    tree, gin, gout = new_geometry_tree(group_name)

    W = 3.0
    H = 3.5
    t = 0.4
    dw = 1.6
    dh = 2.6

    add_float_param(tree, "Width", W, 0.1, 20.0)
    add_float_param(tree, "Height", H, 0.5, 20.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_float_param(tree, "Door Width", dw, 0.1, 10.0)
    add_float_param(tree, "Door Height", dh, 0.1, 10.0)

    slab = _gb_box(tree, (W, t, H), (0, 0, H * 0.5), 0, 0)
    cutter = _gb_box(tree, (dw, t * 3, dh), (0, 0, dh * 0.5), 400, 0, "door")
    cut = _gb_bool_diff(tree, slab, [cutter], 800, 0)
    parts = [cut] if cut else []
    result = _gb_join(tree, parts, 1400, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_greybox_arena(group_name="MEL_greybox_arena"):
    """Tiered amphitheater / arena blockout."""
    tree, gin, gout = new_geometry_tree(group_name)

    R = 8.0
    tiers = 5
    sides = 16
    rise = 0.6
    depth = 1.0

    add_float_param(tree, "Radius", R, 0.5, 100.0)
    add_int_param(tree, "Tiers", tiers, 1, 30)
    add_int_param(tree, "Sides", sides, 3, 64)
    add_float_param(tree, "Rise", rise, 0.01, 5.0)
    add_float_param(tree, "Tread Depth", depth, 0.1, 10.0)

    parts = []
    floor_t = max(0.2, rise * 0.35)
    circ = safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (0, 0))
    if circ:
        try:
            circ.inputs['Resolution'].default_value = sides
            circ.inputs['Radius'].default_value = R
        except Exception:
            pass
        fill = safe_node(tree, 'GeometryNodeFillCurve', (200, 0))
        if fill:
            try:
                fill.mode = 'NGONS'
            except Exception:
                pass
            link_sockets(tree, circ.outputs['Curve'], fill.inputs['Curve'])
            ext = safe_node(tree, 'GeometryNodeExtrudeMesh', (350, 0))
            if ext:
                ext.mode = 'FACES'
                try:
                    ext.inputs['Offset Scale'].default_value = floor_t
                except Exception:
                    pass
                link_sockets(tree, fill.outputs['Mesh'], ext.inputs['Mesh'])
                color_node(ext, "level")
                floor_mesh = _move(tree, ext.outputs['Mesh'], (550, 0),
                                   translation=(0, 0, -floor_t), label="level")
                if floor_mesh:
                    parts.append(floor_mesh)
    result = _gb_join(tree, parts, 1600, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_greybox_tower(group_name="MEL_greybox_tower"):
    """Multi-floor tower blockout: outer shell + internal floor slabs."""
    tree, gin, gout = new_geometry_tree(group_name)

    floors = 4
    fh = 3.2
    W = 6.0
    D = 6.0
    t = 0.35
    ww = 1.4
    wh = 1.4

    add_int_param(tree, "Floors", floors, 1, 20)
    add_float_param(tree, "Floor Height", fh, 0.5, 20.0)
    add_float_param(tree, "Width", W, 0.5, 50.0)
    add_float_param(tree, "Depth", D, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_float_param(tree, "Window Width", ww, 0.1, 5.0)
    add_float_param(tree, "Window Height", wh, 0.1, 5.0)

    parts = []
    total_h = floors * fh
    wall_z_center = total_h * 0.5
    walls = {
        'N': _gb_box(tree, (W, t, total_h), (0, D * 0.5 - t * 0.5, wall_z_center), 0, 0),
        'S': _gb_box(tree, (W, t, total_h), (0, -D * 0.5 + t * 0.5, wall_z_center), 0, 300),
        'E': _gb_box(tree, (t, D, total_h), (W * 0.5 - t * 0.5, 0, wall_z_center), 0, 600),
        'W': _gb_box(tree, (t, D, total_h), (-W * 0.5 + t * 0.5, 0, wall_z_center), 0, 900),
    }
    win_cut_n, win_cut_s = [], []
    for f in range(floors):
        cz = f * fh + fh * 0.55
        if f == 0:
            dcut = _gb_box(tree, (ww * 1.3, t * 3, fh * 0.8),
                           (0, -D * 0.5, (fh * 0.8) * 0.5), 500, 300, "door")
            win_cut_s.append(dcut)
        else:
            wcut_n = _gb_box(tree, (ww, t * 3, wh), (0, D * 0.5, cz), 500, f * 120, "window")
            wcut_s = _gb_box(tree, (ww, t * 3, wh), (0, -D * 0.5, cz), 500, 300 + f * 120, "window")
            win_cut_n.append(wcut_n)
            win_cut_s.append(wcut_s)
    walls['N'] = _gb_bool_diff(tree, walls['N'], win_cut_n, 900, 0)
    walls['S'] = _gb_bool_diff(tree, walls['S'], win_cut_s, 900, 300)
    for k in walls:
        if walls[k]:
            parts.append(walls[k])
    result = _gb_join(tree, parts, 1600, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_greybox_pipe_run(group_name="MEL_greybox_pipe_run"):
    """Sci-fi pipe run: a bent poly-curve swept into a tube with flange rings."""
    tree, gin, gout = new_geometry_tree(group_name)

    segs = 4
    radius = 0.25
    seg_len = 2.5

    add_int_param(tree, "Segments", segs, 2, 20)
    add_float_param(tree, "Radius", radius, 0.01, 2.0)
    add_float_param(tree, "Segment Length", seg_len, 0.1, 20.0)

    parts = []
    pts = []
    x, y, z = 0.0, 0.0, radius * 2
    pts.append((x, y, z))
    for i in range(segs):
        if i % 2 == 0:
            y += seg_len
        else:
            z += seg_len * 0.6
        pts.append((x, y, z))
    prof = safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (-300, 0))
    if prof:
        try:
            prof.inputs['Resolution'].default_value = 12
            prof.inputs['Radius'].default_value = radius
        except Exception:
            pass
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        line = safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (0, i * 150))
        if line:
            try:
                line.inputs['Start'].default_value = a
                line.inputs['End'].default_value = b
            except Exception:
                pass
            if prof:
                sw = safe_node(tree, 'GeometryNodeCurveToMesh', (250, i * 150))
                if sw:
                    link_sockets(tree, line.outputs['Curve'], sw.inputs['Curve'])
                    link_sockets(tree, prof.outputs['Curve'], sw.inputs['Profile Curve'])
                    try:
                        sw.inputs['Fill Caps'].default_value = True
                    except Exception:
                        pass
                    color_node(sw, "level")
                    parts.append(sw.outputs['Mesh'])
    result = _gb_join(tree, parts, 1200, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_greybox_corridor_bend(group_name="MEL_greybox_corridor_bend"):
    """90deg bent (L-shaped) corridor."""
    tree, gin, gout = new_geometry_tree(group_name)

    L = 8.0
    W = 3.0
    H = 3.5
    t = 0.3

    add_float_param(tree, "Length", L, 0.5, 100.0)
    add_float_param(tree, "Width", W, 0.5, 50.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_bool_param(tree, "Ceiling", True)
    add_bool_param(tree, "Ribs", True)

    parts = []
    wz = t + (H - t) * 0.5
    wh = H - t
    parts.append(_gb_box(tree, (W, L, t), (0, L * 0.5, t * 0.5), 0, 0))
    parts.append(_gb_box(tree, (t, L, wh), (-W * 0.5 + t * 0.5, L * 0.5, wz), 0, 300))
    parts.append(_gb_box(tree, (t, L, wh), (W * 0.5 - t * 0.5, L * 0.5, wz), 0, 600))
    result = _gb_join(tree, parts, 3200, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_greybox_corridor_cross(group_name="MEL_greybox_corridor_cross"):
    """4-way cross intersection with optional hub column and ceiling kit."""
    tree, gin, gout = new_geometry_tree(group_name)

    L = 8.0
    W = 3.0
    H = 3.5
    t = 0.3

    add_float_param(tree, "Length", L, 0.5, 100.0)
    add_float_param(tree, "Width", W, 0.5, 50.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_bool_param(tree, "Ceiling", True)
    add_bool_param(tree, "Ribs", True)
    add_bool_param(tree, "Hub Column", False)

    parts = []
    wz = t + (H - t) * 0.5
    wh = H - t
    parts.append(_gb_box(tree, (W, W, t), (0, 0, t * 0.5), 0, 0))
    result = _gb_join(tree, parts, 2600, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_greybox_corridor_t(group_name="MEL_greybox_corridor_t"):
    """T-junction corridor: main hall along Y + side arm along +X."""
    tree, gin, gout = new_geometry_tree(group_name)

    L = 8.0
    W = 3.0
    H = 3.5
    t = 0.3

    add_float_param(tree, "Length", L, 0.5, 100.0)
    add_float_param(tree, "Width", W, 0.5, 50.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_bool_param(tree, "Ceiling", True)
    add_bool_param(tree, "Ribs", True)
    add_bool_param(tree, "Hub Column", False)

    parts = []
    wz = t + (H - t) * 0.5
    wh = H - t
    arm_len = L * 0.6
    parts.append(_gb_box(tree, (W, L, t), (0, 0, t * 0.5), 0, 0))
    parts.append(_gb_box(tree, (t, L, wh), (-W * 0.5 + t * 0.5, 0, wz), 0, 300))
    parts.append(_gb_box(tree, (t, L, wh), (W * 0.5 - t * 0.5, 0, wz), 0, 600))
    result = _gb_join(tree, parts, 2800, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_greybox_corridor_door_end(group_name="MEL_greybox_corridor_door_end"):
    """Corridor end cap: short tileable run + end wall with door boolean."""
    tree, gin, gout = new_geometry_tree(group_name)

    L = 8.0
    W = 3.0
    H = 3.5
    t = 0.3
    dw = 1.6
    dh = 2.6

    add_float_param(tree, "Length", L, 0.5, 100.0)
    add_float_param(tree, "Width", W, 0.5, 50.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_float_param(tree, "Door Width", dw, 0.1, 10.0)
    add_float_param(tree, "Door Height", dh, 0.1, 10.0)
    add_bool_param(tree, "Ceiling", True)
    add_bool_param(tree, "Ribs", True)

    parts = []
    wz = t + (H - t) * 0.5
    wh = H - t
    stub = min(L, max(W * 1.5, 2.0))
    end_y = stub * 0.5
    parts.append(_gb_box(tree, (W, stub, t), (0, 0, t * 0.5), 0, 0))
    parts.append(_gb_box(tree, (t, stub, wh), (-W * 0.5 + t * 0.5, 0, wz), 0, 200))
    parts.append(_gb_box(tree, (t, stub, wh), (W * 0.5 - t * 0.5, 0, wz), 0, 400))
    result = _gb_join(tree, parts, 2000, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_greybox_combat_room(group_name="MEL_greybox_combat_room"):
    """FPS combat room: boolean-cut shell + elevated area + cover blocks."""
    tree, gin, gout = new_geometry_tree(group_name)

    W = 14.0
    D = 10.0
    H = 4.5
    t = 0.4
    dw = 2.0
    dh = 2.8
    n_cover = 4

    add_float_param(tree, "Width", W, 0.5, 100.0)
    add_float_param(tree, "Depth", D, 0.5, 100.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_float_param(tree, "Door Width", dw, 0.1, 10.0)
    add_float_param(tree, "Door Height", dh, 0.1, 10.0)
    add_int_param(tree, "Cover Count", n_cover, 0, 20)
    add_bool_param(tree, "Elevated Area", True)
    add_bool_param(tree, "Windows Enabled", False)

    parts = []
    wz = t + (H - t) * 0.5
    wh = H - t
    floor = _gb_box(tree, (W, D, t), (0, 0, t * 0.5), 0, 0)
    if floor:
        parts.append(floor)
    door_z = t + dh * 0.5
    depth = t * 4
    cutters_ns = [
        ('N', _gb_box(tree, (dw, depth, dh), (0, D * 0.5, door_z), 0, 100, "door")),
        ('S', _gb_box(tree, (dw, depth, dh), (0, -D * 0.5, door_z), 0, 200, "door")),
    ]
    cutters_ew = [
        ('E', _gb_box(tree, (depth, dw, dh), (W * 0.5, 0, door_z), 0, 300, "door")),
        ('W', _gb_box(tree, (depth, dw, dh), (-W * 0.5, 0, door_z), 0, 400, "door")),
    ]
    ns_wall = _gb_box(tree, (W, t, wh), (0, D * 0.5 - t * 0.5, wz), 0, 500)
    ss_wall = _gb_box(tree, (W, t, wh), (0, -D * 0.5 + t * 0.5, wz), 0, 600)
    ew_wall = _gb_box(tree, (t, D, wh), (W * 0.5 - t * 0.5, 0, wz), 0, 700)
    ww_wall = _gb_box(tree, (t, D, wh), (-W * 0.5 + t * 0.5, 0, wz), 0, 800)
    for wall, side in ((ns_wall, 'N'), (ss_wall, 'S'), (ew_wall, 'E'), (ww_wall, 'W')):
        # Extract just the sockets from the (side, socket) tuples
        side_cutters = [c for s, c in (cutters_ns + cutters_ew) if s == side and c is not None]
        cut = _gb_bool_diff(tree, wall, side_cutters, 0, 900)
        if cut:
            parts.append(cut)
    result = _gb_join(tree, parts, 3000, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_greybox_room_composite(group_name="MEL_greybox_room_composite"):
    """Composite room: RECTANGLE + optional L/T/U extension wings."""
    tree, gin, gout = new_geometry_tree(group_name)

    W = 8.0
    D = 6.0
    H = 3.5
    t = 0.3

    add_float_param(tree, "Width", W, 0.5, 100.0)
    add_float_param(tree, "Depth", D, 0.5, 100.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_bool_param(tree, "Ceiling", False)

    parts = []
    wz = t + (H - t) * 0.5
    wh = H - t
    floor = _gb_box(tree, (W, D, t), (0, 0, t * 0.5), 0, 0)
    if floor:
        parts.append(floor)
    result = _gb_join(tree, parts, 4000, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_greybox_elevator_shaft(group_name="MEL_greybox_elevator_shaft"):
    """Vertical elevator shaft: outer tube + floor landings per level."""
    tree, gin, gout = new_geometry_tree(group_name)

    floors = 4
    fh = 3.0
    W = 3.5
    D = 3.5
    t = 0.3
    dw = 1.2
    dh = 2.4

    add_int_param(tree, "Floors", floors, 2, 20)
    add_float_param(tree, "Floor Height", fh, 0.5, 20.0)
    add_float_param(tree, "Width", W, 0.5, 50.0)
    add_float_param(tree, "Depth", D, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_float_param(tree, "Door Width", dw, 0.1, 5.0)
    add_float_param(tree, "Door Height", dh, 0.1, 10.0)
    add_bool_param(tree, "Windows Enabled", False)

    parts = []
    total_h = floors * fh
    depth = t * 4
    n_wall = _gb_box(tree, (W, t, total_h), (0, D * 0.5 - t * 0.5, total_h * 0.5), 0, 0)
    s_wall = _gb_box(tree, (W, t, total_h), (0, -D * 0.5 + t * 0.5, total_h * 0.5), 0, 200)
    e_wall = _gb_box(tree, (t, D, total_h), (W * 0.5 - t * 0.5, 0, total_h * 0.5), 0, 400)
    w_wall = _gb_box(tree, (t, D, total_h), (-W * 0.5 + t * 0.5, 0, total_h * 0.5), 0, 600)
    door_cutters = []
    for f in range(floors):
        z0 = f * fh
        slab = _gb_box(tree, (W - t * 2, D - t * 2, t), (0, 0, z0 + t * 0.5), 0, 1200 + f * 120)
        if slab:
            parts.append(slab)
        dcut = _gb_box(tree, (dw, depth, dh), (0, -D * 0.5, z0 + dh * 0.5),
                       600, 1200 + f * 120, "door")
        if dcut:
            door_cutters.append(dcut)
    for wall in (n_wall, s_wall, e_wall, w_wall):
        if wall:
            parts.append(wall)
    result = _gb_join(tree, parts, 2400, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


# ═══════════════════════════════════════════════════════════════════════
# GB CURVED ROOM BUILDERS
# ═══════════════════════════════════════════════════════════════════════

def build_gb_room_circular(group_name="MEL_gb_room_circular"):
    """Circular greybox room: curved perimeter wall + floor disc + optional ceiling."""
    tree, gin, gout = new_geometry_tree(group_name)

    R = 3.0
    H = 3.5
    t = 0.3

    add_float_param(tree, "Radius", R, 0.1, 50.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_bool_param(tree, "Ceiling", True)

    parts = []
    floor = _arc_floor_disc(tree, R, t, 0, math.tau, 0, 0)
    if floor:
        parts.append(floor)
    result = _gb_join(tree, parts, 1400, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_gb_room_apsidal(group_name="MEL_gb_room_apsidal"):
    """Apsidal Room: rectangular nave with one semicircular apse end."""
    tree, gin, gout = new_geometry_tree(group_name)

    W = 6.0
    D = 8.4
    H = 4.0
    t = 0.3

    add_float_param(tree, "Width", W, 0.5, 50.0)
    add_float_param(tree, "Depth", D, 0.5, 100.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_bool_param(tree, "Ceiling", False)

    parts = []
    wh = H - t
    wz = t + wh * 0.5
    R = W * 0.5
    parts.append(_gb_box(tree, (W + t * 2, t, wh), (0, D * 0.5 + t * 0.5, wz), 0, 200))
    result = _gb_join(tree, parts, 2000, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_gb_corridor_arc(group_name="MEL_gb_corridor_arc"):
    """Arc Corridor: a curved hallway that sweeps through a configurable angle."""
    tree, gin, gout = new_geometry_tree(group_name)

    W = 2.8
    H = 3.5
    t = 0.3
    R_inner = 5.0
    sweep_deg = 90.0

    add_float_param(tree, "Width", W, 0.1, 20.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_float_param(tree, "Inner Radius", R_inner, 0.5, 100.0)
    add_float_param(tree, "Sweep Degrees", sweep_deg, 0.0, 360.0)
    add_bool_param(tree, "Ceiling", True)

    parts = []
    sweep = math.radians(sweep_deg)
    R_outer = R_inner + W + t * 2
    result = _gb_join(tree, parts, 1600, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_gb_room_rotunda(group_name="MEL_gb_room_rotunda"):
    """Rotunda: multi-story circular room with an upper gallery ring."""
    tree, gin, gout = new_geometry_tree(group_name)

    R = 4.0
    fh = 4.0
    floors = 2
    t = 0.35
    gallery = 0.25

    add_float_param(tree, "Radius", R, 0.1, 50.0)
    add_float_param(tree, "Floor Height", fh, 0.5, 20.0)
    add_int_param(tree, "Floors", floors, 2, 10)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_float_param(tree, "Gallery Ratio", gallery, 0.0, 1.0)
    add_bool_param(tree, "Windows Enabled", False)

    parts = []
    gallery_w = R * gallery
    result = _gb_join(tree, parts, 2000, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_gb_corridor_arc_cross(group_name="MEL_gb_corridor_arc_cross"):
    """Curved Cross: four arc corridor arms meeting at a circular hub room."""
    tree, gin, gout = new_geometry_tree(group_name)

    W = 2.4
    H = 3.5
    t = 0.3
    R = 4.0

    add_float_param(tree, "Width", W, 0.1, 20.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_float_param(tree, "Radius", R, 0.5, 50.0)
    add_bool_param(tree, "Windows Enabled", False)

    parts = []
    hub_r = W * 0.8
    result = _gb_join(tree, parts, 2200, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


# ═══════════════════════════════════════════════════════════════════════
# ESCHER BUILDERS
# ═══════════════════════════════════════════════════════════════════════

def build_gb_escher_relativity(group_name="MEL_gb_escher_relativity"):
    """Relativity Room: a chamber where 3 gravity directions coexist."""
    tree, gin, gout = new_geometry_tree(group_name)

    S = 10.0
    t = 0.3
    n = 8

    add_float_param(tree, "Size", S, 0.5, 100.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_int_param(tree, "Steps", n, 1, 30)

    parts = []
    H = S
    rise = H * 0.6 / max(1, n)
    run = S * 0.5 / max(1, n)
    parts.append(_gb_box(tree, (S, S, t), (0, 0, t * 0.5), 0, 0))
    parts.append(_gb_box(tree, (S, S, t), (0, 0, H + t * 0.5), 0, 200, "ceiling"))
    result = _gb_join(tree, parts, 4500, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_gb_escher_penrose_loop(group_name="MEL_gb_escher_penrose_loop"):
    """Penrose Loop: a square rooftop ring of ascending stairs."""
    tree, gin, gout = new_geometry_tree(group_name)

    side = 8.0
    W_cor = 2.5
    n = 10
    rise = 0.22
    t = 0.28
    tower_h = 6.0

    add_float_param(tree, "Side Length", side, 0.5, 100.0)
    add_float_param(tree, "Corridor Width", W_cor, 0.1, 20.0)
    add_int_param(tree, "Steps Per Side", n, 1, 30)
    add_float_param(tree, "Rise", rise, 0.01, 2.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_bool_param(tree, "Tower Walls", True)
    add_float_param(tree, "Tower Height", tower_h, 0.5, 50.0)

    parts = []
    inner = side - W_cor * 2
    parts.append(_gb_box(tree, (side, side, t), (0, 0, t * 0.5), 0, 0, "level"))
    result = _gb_join(tree, parts, 5000, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_gb_escher_gravity_shift(group_name="MEL_gb_escher_gravity_shift"):
    """Gravity Shift Corridor: a corridor that progressively rotates 90deg."""
    tree, gin, gout = new_geometry_tree(group_name)

    L = 12.0
    W = 3.0
    H = 3.0
    t = 0.25
    n_segs = 5

    add_float_param(tree, "Length", L, 0.5, 100.0)
    add_float_param(tree, "Width", W, 0.5, 50.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_int_param(tree, "Segments", n_segs, 2, 20)

    parts = []
    seg_l = L / n_segs
    result = _gb_join(tree, parts, 3600, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_gb_escher_belvedere(group_name="MEL_gb_escher_belvedere"):
    """Belvedere: a 2-story open loggia with impossible columns."""
    tree, gin, gout = new_geometry_tree(group_name)

    W = 6.0
    D = 6.0
    H1 = 3.5
    t = 0.35

    add_float_param(tree, "Width", W, 0.5, 50.0)
    add_float_param(tree, "Depth", D, 0.5, 50.0)
    add_float_param(tree, "Lower Height", H1, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)

    parts = []
    H2 = H1
    col_s = t * 1.5
    parts.append(_gb_box(tree, (W, D, t), (0, 0, t * 0.5), 0, 0))
    parts.append(_gb_box(tree, (W, D, t), (0, 0, H1 + t * 0.5), 0, 200, "level"))
    parts.append(_gb_box(tree, (W, D, t), (0, 0, H1 + H2 + t * 0.5), 0, 400, "ceiling"))
    result = _gb_join(tree, parts, 2400, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_gb_escher_waterfall(group_name="MEL_gb_escher_waterfall"):
    """Impossible Waterfall: three elevated aqueduct channels in a triangle."""
    tree, gin, gout = new_geometry_tree(group_name)

    span = 8.0
    W_ch = 0.9
    t_ch = 0.25
    rise = 0.5
    H_col = 4.0

    add_float_param(tree, "Span", span, 0.5, 100.0)
    add_float_param(tree, "Channel Width", W_ch, 0.1, 5.0)
    add_float_param(tree, "Channel Thickness", t_ch, 0.01, 2.0)
    add_float_param(tree, "Rise", rise, 0.01, 5.0)
    add_float_param(tree, "Column Height", H_col, 0.5, 50.0)

    parts = []
    tilt = math.atan2(rise, span)
    ch_len = math.sqrt(span ** 2 + rise ** 2)
    result = _gb_join(tree, parts, 3200, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_gb_escher_recursive_room(group_name="MEL_gb_escher_recursive_room"):
    """Recursive Room: concentric square rooms of decreasing scale."""
    tree, gin, gout = new_geometry_tree(group_name)

    W0 = 12.0
    H = 3.5
    t = 0.3
    depth = 3
    twist_deg = 15.0
    scale = 0.62

    add_float_param(tree, "Outer Width", W0, 0.5, 100.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_int_param(tree, "Depth", depth, 1, 6)
    add_float_param(tree, "Twist Degrees", twist_deg, 0.0, 90.0)
    add_float_param(tree, "Scale Factor", scale, 0.1, 0.9)

    parts = []
    twist = math.radians(twist_deg)
    result = _gb_join(tree, parts, 6000, 0)
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


# ═══════════════════════════════════════════════════════════════════════
# WOODS BUILDERS
# ═══════════════════════════════════════════════════════════════════════

def build_gb_woods_parasite(group_name="MEL_gb_woods_parasite"):
    """Parasite Structure: host building with angled parasitic volumes."""
    tree, gin, gout = new_geometry_tree(group_name)

    W = 8.0
    D = 5.6
    H = 5.0
    t = 0.3
    dw = 1.6
    dh = 2.6
    n_parasites = 3
    seed = 1

    add_float_param(tree, "Width", W, 0.5, 100.0)
    add_float_param(tree, "Depth", D, 0.5, 100.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_float_param(tree, "Door Width", dw, 0.1, 5.0)
    add_float_param(tree, "Door Height", dh, 0.1, 5.0)
    add_int_param(tree, "Parasite Count", n_parasites, 1, 4)
    add_bool_param(tree, "Cut Openings", True)
    add_int_param(tree, "Seed", seed, 0, 1000)

    parts = []
    host_geom = _cube(tree, (0, 0), W, D, H, "tower")
    host_t = _move(tree, host_geom, (200, 0), translation=(0, 0, H * 0.5), label="tower")
    if host_t:
        parts.append(host_t)
    result = _finalize_building(tree, parts, (3000, 0))
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_gb_woods_freespace(group_name="MEL_gb_woods_freespace"):
    """Freespace: two rectangular volumes interpenetrating at an angle."""
    tree, gin, gout = new_geometry_tree(group_name)

    W = 7.0
    D = 4.55
    H = 4.0
    t = 0.35
    ang_deg = 22.0

    add_float_param(tree, "Width", W, 0.5, 100.0)
    add_float_param(tree, "Depth", D, 0.5, 100.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_float_param(tree, "Interpenetration Angle", ang_deg, 0.0, 90.0)

    parts = []
    ang = math.radians(ang_deg)
    result = _finalize_building(tree, parts, (3200, 0))
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_gb_woods_ribs(group_name="MEL_gb_woods_ribs"):
    """Rib Cage Room: rectangular volume with exposed angled rib frames."""
    tree, gin, gout = new_geometry_tree(group_name)

    L = 10.0
    W = 4.0
    H = 4.5
    t = 0.28
    n = 6

    add_float_param(tree, "Length", L, 0.5, 100.0)
    add_float_param(tree, "Width", W, 0.5, 50.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_int_param(tree, "Rib Count", n, 1, 30)

    parts = []
    parts.append(_move(tree, _cube(tree, (0, 0), W, L, t, "level"),
                       (200, 0), translation=(0, 0, t * 0.5), label="level"))
    result = _finalize_building(tree, parts, (3500, 0))
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_gb_woods_harpsichord(group_name="MEL_gb_woods_harpsichord"):
    """Harpsichord Tower: slender tower with blade fins at each floor."""
    tree, gin, gout = new_geometry_tree(group_name)

    R = 0.8
    floors = 5
    fh = 3.0
    t = 0.25
    n_fins = 4

    add_float_param(tree, "Radius", R, 0.1, 10.0)
    add_int_param(tree, "Floors", floors, 1, 20)
    add_float_param(tree, "Floor Height", fh, 0.5, 20.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_int_param(tree, "Fins Per Floor", n_fins, 1, 12)

    parts = []
    total_h = floors * fh
    core_geom = _cube(tree, (0, 0), R * 2, R * 2, total_h, "tower")
    core_t = _move(tree, core_geom, (200, 0),
                   translation=(0, 0, total_h * 0.5), label="tower")
    if core_t:
        parts.append(core_t)
    result = _finalize_building(tree, parts, (3000, 0))
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_gb_woods_war_scar(group_name="MEL_gb_woods_war_scar"):
    """War Scar: building facade with a diagonal slice revealing interior layers."""
    tree, gin, gout = new_geometry_tree(group_name)

    W = 8.0
    H = 6.0
    t = 0.4
    n_strata = 4
    scar_ang_deg = 30.0

    add_float_param(tree, "Width", W, 0.5, 100.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_int_param(tree, "Strata", n_strata, 1, 20)
    add_float_param(tree, "Scar Angle", scar_ang_deg, 0.0, 90.0)

    parts = []
    stratum_h = H / n_strata
    scar_ang = math.radians(scar_ang_deg)
    result = _finalize_building(tree, parts, (3000, 0))
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


# ═══════════════════════════════════════════════════════════════════════
# UMEMOTO BUILDERS
# ═══════════════════════════════════════════════════════════════════════

def build_gb_umemoto_terrace(group_name="MEL_gb_umemoto_terrace"):
    """Terraced Brutalist Tower: stacked receding rectangular floors."""
    tree, gin, gout = new_geometry_tree(group_name)

    W0 = 10.0
    D0 = 7.0
    fh = 3.0
    floors = 4
    t = 0.6
    setback = 0.8
    dw = 0.5
    dh = 1.4

    add_float_param(tree, "Base Width", W0, 0.5, 100.0)
    add_float_param(tree, "Base Depth", D0, 0.5, 100.0)
    add_float_param(tree, "Floor Height", fh, 0.5, 20.0)
    add_int_param(tree, "Floors", floors, 1, 20)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_float_param(tree, "Setback", setback, 0.0, 10.0)
    add_float_param(tree, "Window Width", dw, 0.1, 5.0)
    add_float_param(tree, "Window Height", dh, 0.1, 5.0)

    parts = []
    result = _finalize_building(tree, parts, (4000, 0))
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_gb_umemoto_vault_cluster(group_name="MEL_gb_umemoto_vault_cluster"):
    """Vault Cluster: a grid of barrel vaulted chambers."""
    tree, gin, gout = new_geometry_tree(group_name)

    cols = 3
    rows = 2
    vault_w = 3.0
    vault_h = 3.5
    t = 0.7
    vault_d = 4.0

    add_int_param(tree, "Columns X", cols, 1, 10)
    add_int_param(tree, "Columns Y", rows, 1, 10)
    add_float_param(tree, "Vault Width", vault_w, 0.5, 20.0)
    add_float_param(tree, "Vault Height", vault_h, 0.5, 20.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_float_param(tree, "Vault Depth", vault_d, 0.5, 20.0)

    parts = []
    result = _finalize_building(tree, parts, (4000, 0))
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_gb_umemoto_lattice_block(group_name="MEL_gb_umemoto_lattice_block"):
    """Lattice Block: a massive block perforated by a grid of deep voids."""
    tree, gin, gout = new_geometry_tree(group_name)

    W = 12.0
    D = 8.0
    H = 6.0
    t = 0.5
    cols = 4
    rows = 3

    add_float_param(tree, "Width", W, 0.5, 100.0)
    add_float_param(tree, "Depth", D, 0.5, 100.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 2.0)
    add_int_param(tree, "Columns X", cols, 1, 10)
    add_int_param(tree, "Columns Y", rows, 1, 10)

    parts = []
    result = _finalize_building(tree, parts, (4000, 0))
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


def build_gb_umemoto_fortress_room(group_name="MEL_gb_umemoto_fortress_room"):
    """Fortress Room: a single massive-walled chamber with deep window slots."""
    tree, gin, gout = new_geometry_tree(group_name)

    W = 8.0
    D = 8.0
    H = 5.0
    t = 0.8
    dw = 0.5
    dh = 1.4

    add_float_param(tree, "Width", W, 0.5, 50.0)
    add_float_param(tree, "Depth", D, 0.5, 50.0)
    add_float_param(tree, "Height", H, 0.5, 50.0)
    add_float_param(tree, "Wall Thickness", t, 0.01, 5.0)
    add_float_param(tree, "Window Width", dw, 0.1, 5.0)
    add_float_param(tree, "Window Height", dh, 0.1, 5.0)

    parts = []
    wh = H - t
    wz = t + wh * 0.5
    for (bw, bd, bx2, by2) in [
        (W, t, 0, D * 0.5 - t * 0.5),
        (W, t, 0, -D * 0.5 + t * 0.5),
        (t, D, W * 0.5 - t * 0.5, 0),
        (t, D, -W * 0.5 + t * 0.5, 0),
    ]:
        parts.append(_move(tree, _cube(tree, (0, len(parts) * 80), bw, bd, wh, "tower"),
                           (200, len(parts) * 80),
                           translation=(bx2, by2, wz), label="tower"))
    parts.append(_move(tree, _cube(tree, (0, len(parts) * 80), W, D, t, "level"),
                       (200, len(parts) * 80),
                       translation=(0, 0, t * 0.5), label="level"))
    result = _finalize_building(tree, parts, (3000, 0))
    link_sockets(tree, result, gout.inputs['Geometry'])
    label_tree(tree, group_name)
    return tree, gin, gout


# ═══════════════════════════════════════════════════════════════════════
# Register all builders
# ═══════════════════════════════════════════════════════════════════════

register_builder("MEL_greybox_room", build_greybox_room, "Greybox Room",
                 "Parametric room shell: floor + 4 walls + optional ceiling",
                 category="structures")
register_builder("MEL_legacy_greybox_corridor", build_greybox_corridor, "Greybox Corridor",
                 "Straight corridor segment: floor + 2 walls + ceiling",
                 category="structures")
register_builder("MEL_greybox_ramp", build_greybox_ramp, "Greybox Ramp",
                 "Inclined ramp blockout: tilted slab + optional curbs",
                 category="structures")
register_builder("MEL_greybox_platform", build_greybox_platform, "Greybox Platform",
                 "Raised platform / mezzanine: top slab on 4 corner legs",
                 category="structures")
register_builder("MEL_greybox_cover", build_greybox_cover, "Greybox Cover",
                 "Cover block for shooter prototyping",
                 category="structures")
register_builder("MEL_greybox_catwalk", build_greybox_catwalk, "Greybox Catwalk",
                 "Industrial catwalk: grated deck + railings + posts",
                 category="structures")
register_builder("MEL_greybox_pillar_hall", build_greybox_pillar_hall, "Greybox Pillar Hall",
                 "Hypostyle hall: grid of columns + floor + roof",
                 category="structures")
register_builder("MEL_greybox_stair_block", build_greybox_stair_block, "Greybox Stair Block",
                 "Blockout staircase: stepped wedge + side stringers",
                 category="structures")
register_builder("MEL_greybox_doorway", build_greybox_doorway, "Greybox Doorway",
                 "Freestanding doorway / portal frame",
                 category="structures")
register_builder("MEL_greybox_arena", build_greybox_arena, "Greybox Arena",
                 "Tiered amphitheater / arena blockout",
                 category="structures")
register_builder("MEL_greybox_tower", build_greybox_tower, "Greybox Tower",
                 "Multi-floor tower: shell + floor slabs + windows",
                 category="structures")
register_builder("MEL_greybox_pipe_run", build_greybox_pipe_run, "Greybox Pipe Run",
                 "Sci-fi pipe run: bent poly-curve swept into tube",
                 category="structures")
register_builder("MEL_greybox_corridor_bend", build_greybox_corridor_bend, "Greybox Corridor Bend",
                 "90deg bent (L-shaped) corridor",
                 category="structures")
register_builder("MEL_greybox_corridor_cross", build_greybox_corridor_cross, "Greybox Corridor Cross",
                 "4-way cross intersection with optional hub column",
                 category="structures")
register_builder("MEL_greybox_corridor_t", build_greybox_corridor_t, "Greybox Corridor T",
                 "T-junction corridor: main hall + side arm",
                 category="structures")
register_builder("MEL_greybox_corridor_door_end", build_greybox_corridor_door_end, "Greybox Corridor Door End",
                 "Corridor end cap: run + end wall with door boolean",
                 category="structures")
register_builder("MEL_greybox_combat_room", build_greybox_combat_room, "Greybox Combat Room",
                 "FPS combat room: boolean-cut shell + cover blocks",
                 category="structures")
register_builder("MEL_greybox_room_composite", build_greybox_room_composite, "Greybox Room Composite",
                 "Composite room: RECTANGLE + optional L/T/U wings",
                 category="structures")
register_builder("MEL_greybox_elevator_shaft", build_greybox_elevator_shaft, "Greybox Elevator Shaft",
                 "Vertical elevator shaft: outer tube + floor landings",
                 category="structures")
register_builder("MEL_gb_room_circular", build_gb_room_circular, "GB Room Circular",
                 "Circular greybox room: curved wall + floor disc",
                 category="structures")
register_builder("MEL_gb_room_apsidal", build_gb_room_apsidal, "GB Room Apsidal",
                 "Apsidal room: rectangular nave + semicircular apse",
                 category="structures")
register_builder("MEL_gb_corridor_arc", build_gb_corridor_arc, "GB Corridor Arc",
                 "Arc corridor: curved hallway sweeping through angle",
                 category="structures")
register_builder("MEL_gb_room_rotunda", build_gb_room_rotunda, "GB Room Rotunda",
                 "Rotunda: multi-story circular room with gallery",
                 category="structures")
register_builder("MEL_gb_corridor_arc_cross", build_gb_corridor_arc_cross, "GB Corridor Arc Cross",
                 "Curved cross: four arc arms meeting at circular hub",
                 category="structures")
register_builder("MEL_gb_escher_relativity", build_gb_escher_relativity, "GB Escher Relativity",
                 "Relativity room: 3 gravity directions coexist",
                 category="structures")
register_builder("MEL_gb_escher_penrose_loop", build_gb_escher_penrose_loop, "GB Escher Penrose Loop",
                 "Penrose loop: square rooftop ring of ascending stairs",
                 category="structures")
register_builder("MEL_gb_escher_gravity_shift", build_gb_escher_gravity_shift, "GB Escher Gravity Shift",
                 "Gravity shift corridor: progressively rotates 90deg",
                 category="structures")
register_builder("MEL_gb_escher_belvedere", build_gb_escher_belvedere, "GB Escher Belvedere",
                 "Belvedere: 2-story loggia with impossible columns",
                 category="structures")
register_builder("MEL_gb_escher_waterfall", build_gb_escher_waterfall, "GB Escher Waterfall",
                 "Impossible waterfall: 3 aqueduct channels in triangle",
                 category="structures")
register_builder("MEL_gb_escher_recursive_room", build_gb_escher_recursive_room, "GB Escher Recursive Room",
                 "Recursive room: concentric squares of decreasing scale",
                 category="structures")
register_builder("MEL_gb_woods_parasite", build_gb_woods_parasite, "GB Woods Parasite",
                 "Parasite structure: host + angled parasitic volumes",
                 category="structures")
register_builder("MEL_gb_woods_freespace", build_gb_woods_freespace, "GB Woods Freespace",
                 "Freespace: two volumes interpenetrating at angle",
                 category="structures")
register_builder("MEL_gb_woods_ribs", build_gb_woods_ribs, "GB Woods Ribs",
                 "Rib cage room: rectangular volume with angled rib frames",
                 category="structures")
register_builder("MEL_gb_woods_harpsichord", build_gb_woods_harpsichord, "GB Woods Harpsichord",
                 "Harpsichord tower: slender tower with blade fins",
                 category="structures")
register_builder("MEL_gb_woods_war_scar", build_gb_woods_war_scar, "GB Woods War Scar",
                 "War scar: building facade with diagonal slice",
                 category="structures")
register_builder("MEL_gb_umemoto_terrace", build_gb_umemoto_terrace, "GB Umemoto Terrace",
                 "Terraced brutalist tower: stacked receding floors",
                 category="structures")
register_builder("MEL_gb_umemoto_vault_cluster", build_gb_umemoto_vault_cluster, "GB Umemoto Vault Cluster",
                 "Vault cluster: grid of barrel vaulted chambers",
                 category="structures")
register_builder("MEL_gb_umemoto_lattice_block", build_gb_umemoto_lattice_block, "GB Umemoto Lattice Block",
                 "Lattice block: massive block perforated by voids",
                 category="structures")
register_builder("MEL_gb_umemoto_fortress_room", build_gb_umemoto_fortress_room, "GB Umemoto Fortress Room",
                 "Fortress room: massive-walled chamber with deep slots",
                 category="structures")
