"""MEL misc props & structures — absorbed from the monolith (P2 family 8b).

17 builders. Params-as-values port. Regenerable.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, add_string_param,
    register_builder,
)

def _node(tree, bl_idname, loc=(0, 0), **kwargs):
    n = tree.nodes.new(bl_idname)
    n.location = loc
    for k, v in kwargs.items():
        try:
            if hasattr(n, k):
                setattr(n, k, v)
            elif k in n.inputs:
                n.inputs[k].default_value = v
        except Exception:
            pass
    return n


# ──────────────────────────────────────────────────────────────────────
# ADVANCED BUILDER: RAYCAST FACADE
# Uses Raycast node to project panel windows onto a curved surface,
# creating a parametric glass curtain-wall facade.
# ──────────────────────────────────────────────────────────────────────
def _safe_node(tree, bl_idname, loc=(0, 0)):
    """Create a node, returning None (not crashing) if the type doesn't exist."""
    try:
        n = tree.nodes.new(bl_idname)
        n.location = loc
        return n
    except Exception:
        return None


def _link(tree, src, dst):
    try:
        tree.links.new(src, dst)
    except Exception:
        pass


def _cube(tree, loc, sx, sy, sz, label="tower"):
    """Make a MeshCube with the vector `Size` socket (Blender 5.1 correct API)."""
    c = _node(tree, 'GeometryNodeMeshCube', loc)
    c.inputs['Size'].default_value = (sx, sy, sz)
    color_node(c, label)
    return c.outputs['Mesh']


# ─── TOWN HOUSE (Tudor) ─────────────────────────────────────────────
def _move(tree, geom, loc, translation=(0, 0, 0), rotation=(0, 0, 0),
          scale=(1, 1, 1), label="tower"):
    """Wrap a geometry socket in a Transform node."""
    t = _node(tree, 'GeometryNodeTransform', loc)
    t.inputs['Translation'].default_value = translation
    t.inputs['Rotation'].default_value = rotation
    t.inputs['Scale'].default_value = scale
    if geom is not None:
        _link(tree, geom, t.inputs['Geometry'])
    color_node(t, label)
    return t.outputs['Geometry']


def _join_all(tree, pieces, loc=(0, 0), label="output", weld=0.01):
    """Join all `pieces` into one mesh and weld vertices within `weld` distance.
    Set weld=0 to skip merging."""
    j = _node(tree, 'GeometryNodeJoinGeometry', loc)
    for p in pieces:
        if p is not None:
            _link(tree, p, j.inputs['Geometry'])
    color_node(j, label)
    out = j.outputs['Geometry']
    if weld > 0:
        mbd = _safe_node(tree, 'GeometryNodeMergeByDistance', (loc[0] + 250, loc[1]))
        if mbd is not None:
            try:
                mbd.inputs['Distance'].default_value = weld
            except Exception:
                pass
            _link(tree, out, mbd.inputs['Geometry'])
            color_node(mbd, "optimize")
            return mbd.outputs['Geometry']
    return out


def _finalize_building(tree, pieces, loc=(0, 0), label="output"):
    """Heavier weld for monolithic buildings - fuses touching tops/finials
    to their bodies (weld=0.3). Use as the last step of a building builder."""
    return _join_all(tree, pieces, loc=loc, label=label, weld=0.3)


def _cv_circle(tree, loc, radius, resolution=32):
    """Helper: a closed circle curve."""
    c = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', loc)
    if c is None:
        return None
    try:
        c.inputs['Resolution'].default_value = resolution
        c.inputs['Radius'].default_value = radius
    except Exception:
        return None
    return c


def _fill_extrude(tree, curve_out, loc_fill, loc_ext, height, label="tower"):
    """Curve -> Fill -> Extrude -> returns extruded mesh socket."""
    f = _safe_node(tree, 'GeometryNodeFillCurve', loc_fill)
    if f is None or curve_out is None:
        return None
    try:
        f.mode = 'NGONS'
    except Exception:
        pass
    _link(tree, curve_out, f.inputs['Curve'])
    e = _safe_node(tree, 'GeometryNodeExtrudeMesh', loc_ext)
    if e is None:
        return f.outputs['Mesh']
    e.mode = 'FACES'
    e.inputs['Offset Scale'].default_value = height
    _link(tree, f.outputs['Mesh'], e.inputs['Mesh'])
    color_node(f, label); color_node(e, label)
    return e.outputs['Mesh']


def _rect_profile(tree, loc, width, height, label="arch"):
    """Quadrilateral RECTANGLE profile: Width maps to world-Y (depth),
    Height maps to radial (band thickness) for curves in the X-Z plane."""
    q = _safe_node(tree, 'GeometryNodeCurvePrimitiveQuadrilateral', loc)
    if q is None:
        return None
    try:
        q.mode = 'RECTANGLE'
        q.inputs['Width'].default_value  = width
        q.inputs['Height'].default_value = height
    except Exception:
        pass
    color_node(q, label)
    return q.outputs['Curve']


def _curved_roof(tree, loc, size_x, size_y, ridge_h, base_z=0.0,
                 pitch=1.6, hip=True, eave_flip=0.16, thickness=-0.1,
                 label="roof", res=24):
    """Reusable East-Asian curved roof built from a deformed Grid.

    hip=True  -> 4-way hip/pyramid roof (square level-sets, Chebyshev),
                tips sweep up uniformly (Japanese/Chinese irimoya feel).
    hip=False -> gable roof: ridge runs along X, slopes fall off in Y,
                the four corners flip up (Korean cheoma / Chinese pailou).

    The (1-n)^pitch profile is concave when pitch>1 so the eaves sweep.
    Returns a geometry output socket (extruded shell with `thickness`).
    """
    bx, by = loc
    half_x = size_x / 2.0
    half_y = size_y / 2.0
    grid = tree.nodes.new('GeometryNodeMeshGrid'); grid.location = (bx, by); color_node(grid, label)
    grid.inputs['Size X'].default_value = size_x
    grid.inputs['Size Y'].default_value = size_y
    grid.inputs['Vertices X'].default_value = res
    grid.inputs['Vertices Y'].default_value = res
    pos = tree.nodes.new('GeometryNodeInputPosition'); pos.location = (bx, by + 250)
    sep = tree.nodes.new('ShaderNodeSeparateXYZ'); sep.location = (bx + 180, by + 250)
    tree.links.new(pos.outputs['Position'], sep.inputs['Vector'])
    axn = tree.nodes.new('ShaderNodeMath'); axn.location = (bx + 360, by + 320); axn.operation = 'ABSOLUTE'
    tree.links.new(sep.outputs['X'], axn.inputs[0])
    ayn = tree.nodes.new('ShaderNodeMath'); ayn.location = (bx + 360, by + 200); ayn.operation = 'ABSOLUTE'
    tree.links.new(sep.outputs['Y'], ayn.inputs[0])
    # normalized x,y in [0..1]
    nxd = tree.nodes.new('ShaderNodeMath'); nxd.location = (bx + 540, by + 320); nxd.operation = 'DIVIDE'
    nxd.inputs[1].default_value = max(0.001, half_x); tree.links.new(axn.outputs[0], nxd.inputs[0])
    nyd = tree.nodes.new('ShaderNodeMath'); nyd.location = (bx + 540, by + 200); nyd.operation = 'DIVIDE'
    nyd.inputs[1].default_value = max(0.001, half_y); tree.links.new(ayn.outputs[0], nyd.inputs[0])
    if hip:
        m = tree.nodes.new('ShaderNodeMath'); m.location = (bx + 720, by + 260); m.operation = 'MAXIMUM'
        tree.links.new(nxd.outputs[0], m.inputs[0]); tree.links.new(nyd.outputs[0], m.inputs[1])
        m_out = m.outputs[0]
    else:
        m_out = nyd.outputs[0]   # gable falls off in Y only
    inv = tree.nodes.new('ShaderNodeMath'); inv.location = (bx + 900, by + 320); inv.operation = 'SUBTRACT'
    inv.inputs[0].default_value = 1.0; tree.links.new(m_out, inv.inputs[1])
    powr = tree.nodes.new('ShaderNodeMath'); powr.location = (bx + 1080, by + 320); powr.operation = 'POWER'
    powr.inputs[1].default_value = max(0.4, pitch); tree.links.new(inv.outputs[0], powr.inputs[0])
    zmul = tree.nodes.new('ShaderNodeMath'); zmul.location = (bx + 1260, by + 320); zmul.operation = 'MULTIPLY'
    zmul.inputs[1].default_value = ridge_h; tree.links.new(powr.outputs[0], zmul.inputs[0])
    # corner / eave upturn
    if hip:
        ef = tree.nodes.new('ShaderNodeMath'); ef.location = (bx + 900, by + 140); ef.operation = 'POWER'
        ef.inputs[1].default_value = 6.0; tree.links.new(m_out, ef.inputs[0])
        flip_src = ef.outputs[0]
    else:
        exp = tree.nodes.new('ShaderNodeMath'); exp.location = (bx + 720, by + 60); exp.operation = 'POWER'
        exp.inputs[1].default_value = 5.0; tree.links.new(nxd.outputs[0], exp.inputs[0])
        eyp = tree.nodes.new('ShaderNodeMath'); eyp.location = (bx + 720, by - 60); eyp.operation = 'POWER'
        eyp.inputs[1].default_value = 4.0; tree.links.new(nyd.outputs[0], eyp.inputs[0])
        cm = tree.nodes.new('ShaderNodeMath'); cm.location = (bx + 900, by + 0); cm.operation = 'MULTIPLY'
        tree.links.new(exp.outputs[0], cm.inputs[0]); tree.links.new(eyp.outputs[0], cm.inputs[1])
        flip_src = cm.outputs[0]
    eamp = tree.nodes.new('ShaderNodeMath'); eamp.location = (bx + 1080, by + 140); eamp.operation = 'MULTIPLY'
    eamp.inputs[1].default_value = ridge_h * eave_flip; tree.links.new(flip_src, eamp.inputs[0])
    zsum = tree.nodes.new('ShaderNodeMath'); zsum.location = (bx + 1440, by + 260); zsum.operation = 'ADD'
    tree.links.new(zmul.outputs[0], zsum.inputs[0]); tree.links.new(eamp.outputs[0], zsum.inputs[1])
    zvec = tree.nodes.new('ShaderNodeCombineXYZ'); zvec.location = (bx + 1620, by + 260)
    tree.links.new(zsum.outputs[0], zvec.inputs['Z'])
    setp = tree.nodes.new('GeometryNodeSetPosition'); setp.location = (bx + 1800, by); color_node(setp, label)
    tree.links.new(grid.outputs['Mesh'], setp.inputs['Geometry'])
    tree.links.new(zvec.outputs['Vector'], setp.inputs['Offset'])
    out = setp.outputs['Geometry']
    if thickness:
        ext = _safe_node(tree, 'GeometryNodeExtrudeMesh', (bx + 1980, by))
        if ext:
            ext.mode = 'FACES'
            try: ext.inputs['Offset Scale'].default_value = thickness
            except Exception: pass
            tree.links.new(setp.outputs['Geometry'], ext.inputs['Mesh'])
            out = ext.outputs['Mesh']
    if base_z:
        tr = tree.nodes.new('GeometryNodeTransform'); tr.location = (bx + 2160, by)
        tr.inputs['Translation'].default_value = (0, 0, base_z)
        tree.links.new(out, tr.inputs['Geometry'])
        out = tr.outputs['Geometry']
    return out


def _arch_spine(tree, style, hw, spring_z, loc, base_x):
    """Return list of curve output sockets forming the arch-head centreline
    in the X-Z plane, springing at (±hw, 0, spring_z).
    Each curve socket is positioned/rotated into world space already."""
    curves = []
    bx, by = loc

    if style == 'ROMAN':
        # True semicircle via CurveArc - rotate into X-Z plane
        a = _safe_node(tree, 'GeometryNodeCurveArc', (bx, by))
        if a:
            a.mode = 'RADIUS'
            a.inputs['Resolution'].default_value  = 48
            a.inputs['Radius'].default_value       = hw
            a.inputs['Start Angle'].default_value  = 0.0
            a.inputs['Sweep Angle'].default_value  = math.pi
            color_node(a, "arch")
            t = _move(tree, a.outputs['Curve'], (bx + 240, by),
                      translation=(0, 0, spring_z),
                      rotation=(math.radians(90), 0, 0), label="arch")
            curves.append(t)

    elif style == 'SEGMENTAL':
        # Shallow bezier arc - rise ≈ 42% of half-width
        rise = hw * 0.42
        bz = _safe_node(tree, 'GeometryNodeCurvePrimitiveBezierSegment', (bx, by))
        if bz:
            bz.inputs['Resolution'].default_value    = 32
            bz.inputs['Start'].default_value         = (-hw, 0, spring_z)
            bz.inputs['Start Handle'].default_value  = (-hw * 0.35, 0, spring_z + rise * 1.35)
            bz.inputs['End Handle'].default_value    = ( hw * 0.35, 0, spring_z + rise * 1.35)
            bz.inputs['End'].default_value           = ( hw, 0, spring_z)
            color_node(bz, "arch"); curves.append(bz.outputs['Curve'])

    elif style == 'HORSESHOE':
        # Moorish / Islamic horseshoe - arc exceeds 180deg, legs tuck inward
        a = _safe_node(tree, 'GeometryNodeCurveArc', (bx, by))
        if a:
            a.mode = 'RADIUS'
            a.inputs['Resolution'].default_value  = 56
            a.inputs['Radius'].default_value       = hw
            a.inputs['Start Angle'].default_value  = math.radians(-38)
            a.inputs['Sweep Angle'].default_value  = math.pi + math.radians(76)
            color_node(a, "arch")
            t = _move(tree, a.outputs['Curve'], (bx + 240, by),
                      translation=(0, 0, spring_z),
                      rotation=(math.radians(90), 0, 0), label="arch")
            curves.append(t)

    elif style == 'GOTHIC':
        # Two bezier arcs meeting at pointed apex (≈1.4 × hw above spring)
        apex_z = spring_z + hw * 1.4
        for i, sgn in enumerate((-1, 1)):
            bz = _safe_node(tree, 'GeometryNodeCurvePrimitiveBezierSegment',
                             (bx, by + i * 160))
            if bz:
                bz.inputs['Resolution'].default_value    = 24
                bz.inputs['Start'].default_value         = (sgn * hw, 0, spring_z)
                bz.inputs['Start Handle'].default_value  = (sgn * hw, 0, spring_z + hw * 0.9)
                bz.inputs['End Handle'].default_value    = (sgn * hw * 0.18, 0, apex_z)
                bz.inputs['End'].default_value           = (0, 0, apex_z)
                color_node(bz, "gothic"); curves.append(bz.outputs['Curve'])

    elif style == 'TUDOR':
        # Four-centred Tudor arch - low pointed apex, flat-topped silhouette
        apex_z = spring_z + hw * 0.62
        for i, sgn in enumerate((-1, 1)):
            bz = _safe_node(tree, 'GeometryNodeCurvePrimitiveBezierSegment',
                             (bx, by + i * 160))
            if bz:
                bz.inputs['Resolution'].default_value    = 24
                bz.inputs['Start'].default_value         = (sgn * hw, 0, spring_z)
                bz.inputs['Start Handle'].default_value  = (sgn * hw,       0, spring_z + hw * 0.5)
                bz.inputs['End Handle'].default_value    = (sgn * hw * 0.5, 0, apex_z)
                bz.inputs['End'].default_value           = (0, 0, apex_z)
                color_node(bz, "arch"); curves.append(bz.outputs['Curve'])

    elif style == 'OGEE':
        # S-curve ogee - convex below, concave above, meeting at tall apex
        apex_z = spring_z + hw * 1.55
        midz   = spring_z + hw * 0.75
        for i, sgn in enumerate((-1, 1)):
            bz = _safe_node(tree, 'GeometryNodeCurvePrimitiveBezierSegment',
                             (bx, by + i * 160))
            if bz:
                bz.inputs['Resolution'].default_value    = 28
                bz.inputs['Start'].default_value         = (sgn * hw,        0, spring_z)
                bz.inputs['Start Handle'].default_value  = (sgn * hw,        0, midz)
                bz.inputs['End Handle'].default_value    = (sgn * hw * 0.55, 0, midz)
                bz.inputs['End'].default_value           = (0, 0, apex_z)
                color_node(bz, "ogee"); curves.append(bz.outputs['Curve'])

    else:  # LINTEL - flat horizontal head
        ln = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (bx, by))
        if ln:
            ln.inputs['Start'].default_value = (-hw, 0, spring_z)
            ln.inputs['End'].default_value   = ( hw, 0, spring_z)
            color_node(ln, "arch"); curves.append(ln.outputs['Curve'])

    return curves




BUILDER_PARAM_DEFAULTS = {
    "arch_radius": {"type": "FloatProperty", "default": 1.5, "min": 0.3, "max": 10.0},
    "arch_thickness": {"type": "FloatProperty", "default": 0.18, "min": 0.02, "max": 1.0},
    "archway_depth": {"type": "FloatProperty", "default": 0.6, "min": 0.1, "max": 4.0},
    "archway_height": {"type": "FloatProperty", "default": 2.6, "min": 0.3, "max": 10.0},
    "archway_keystone": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "archway_pier_width": {"type": "FloatProperty", "default": 0.5, "min": 0.05, "max": 3.0},
    "archway_piers": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "archway_style": {"type": "EnumProperty", "default": 'ROMAN', "min": None, "max": None},
    "archway_thickness": {"type": "FloatProperty", "default": 0.35, "min": 0.04, "max": 2.0},
    "archway_voussoirs": {"type": "IntProperty", "default": 0, "min": 0, "max": 24},
    "archway_width": {"type": "FloatProperty", "default": 2.4, "min": 0.4, "max": 12.0},
    "base_radius": {"type": "FloatProperty", "default": 1.2, "min": 0.1, "max": 10.0},
    "bridge_arches": {"type": "IntProperty", "default": 3, "min": 1, "max": 12},
    "bridge_deck_thick": {"type": "FloatProperty", "default": 0.25, "min": 0.05, "max": 1.5},
    "bridge_railings": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "bridge_rise": {"type": "FloatProperty", "default": 2.5, "min": 0.3, "max": 20.0},
    "bridge_span": {"type": "FloatProperty", "default": 12.0, "min": 2.0, "max": 80.0},
    "bridge_style": {"type": "EnumProperty", "default": 'STONE_ARCH', "min": None, "max": None},
    "bridge_width": {"type": "FloatProperty", "default": 3.0, "min": 0.5, "max": 12.0},
    "bulge_amount": {"type": "FloatProperty", "default": 0.2, "min": 0.0, "max": 2.0},
    "complexity_level": {"type": "IntProperty", "default": 3, "min": 1, "max": 5},
    "door_height": {"type": "FloatProperty", "default": 2.4, "min": 1.5, "max": 5.0},
    "door_width": {"type": "FloatProperty", "default": 1.2, "min": 0.4, "max": 4.0},
    "fence_height": {"type": "FloatProperty", "default": 1.2, "min": 0.2, "max": 6.0},
    "fence_length": {"type": "FloatProperty", "default": 6.0, "min": 0.5, "max": 50.0},
    "fence_picket_gap": {"type": "FloatProperty", "default": 0.06, "min": 0.01, "max": 0.5},
    "fence_post_spacing": {"type": "FloatProperty", "default": 1.5, "min": 0.2, "max": 6.0},
    "fence_rails": {"type": "IntProperty", "default": 2, "min": 1, "max": 6},
    "fence_style": {"type": "EnumProperty", "default": 'PICKET', "min": None, "max": None},
    "flow_amount": {"type": "FloatProperty", "default": 0.3, "min": 0.0, "max": 2.0},
    "frame_arch_cap": {"type": "EnumProperty", "default": 'ROMAN', "min": None, "max": None},
    "frame_with_shutters": {"type": "BoolProperty", "default": False, "min": None, "max": None},
    "height": {"type": "FloatProperty", "default": 5.0, "min": 0.5, "max": 30.0},
    "prop_count": {"type": "IntProperty", "default": 3, "min": 1, "max": 8},
    "prop_scatter": {"type": "FloatProperty", "default": 0.35, "min": 0.0, "max": 2.0},
    "recursion_depth": {"type": "IntProperty", "default": 3, "min": 1, "max": 6},
    "ruin_damage": {"type": "FloatProperty", "default": 0.6, "min": 0.0, "max": 1.0},
    "ruin_style": {"type": "EnumProperty", "default": 'CRUMBLED', "min": None, "max": None},
    "seed": {"type": "IntProperty", "default": 42, "min": 0, "max": 9999},
    "unit_size": {"type": "FloatProperty", "default": 2.0, "min": 0.5, "max": 10.0},
    "variation_intensity": {"type": "FloatProperty", "default": 0.5, "min": 0.0, "max": 1.0},
    "wall_height": {"type": "FloatProperty", "default": 3.0, "min": 1.0, "max": 10.0},
    "wall_segments": {"type": "IntProperty", "default": 1, "min": 1, "max": 10},
    "wall_thickness": {"type": "FloatProperty", "default": 0.25, "min": 0.05, "max": 2.0},
    "wave_frequency": {"type": "FloatProperty", "default": 2.0, "min": 0.5, "max": 10.0},
    "window_height": {"type": "FloatProperty", "default": 1.1, "min": 0.2, "max": 4.0},
    "window_width": {"type": "FloatProperty", "default": 0.7, "min": 0.1, "max": 4.0},
}

import types as _types

def _make_props():
    kv = {k: (v["default"] if v["default"] is not None else 0.0)
         for k, v in BUILDER_PARAM_DEFAULTS.items()}
    return _types.SimpleNamespace(**kv)


def build_street_lamp_group(group_name="MEL_street_lamp"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0) if spec['default'] is not None else 0, int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t in ('StringProperty', 'EnumProperty'):
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    PROPS = _make_props()
    base_x = -1400
    def _impl():
        """Period street lamp: tapered post + bracket + glass lantern + finial."""
        H = max(2.5, getattr(PROPS, 'height', 3.5) * 1.0)
        pieces = []
        # Plinth base
        pieces.append(_move(tree, _cube(tree, (base_x, 200), 0.35, 0.35, 0.25, "tower"),
                             (base_x + 200, 200), translation=(0, 0, 0.125), label="tower"))
        # Tapered post (cylinder)
        post = _node(tree, 'GeometryNodeMeshCylinder', (base_x, -100))
        post.inputs['Radius'].default_value = 0.07
        post.inputs['Depth'].default_value = H
        post.inputs['Vertices'].default_value = 12
        pieces.append(_move(tree, post.outputs['Mesh'], (base_x + 200, -100),
                             translation=(0, 0, H / 2 + 0.25), label="tower"))
        color_node(post, "tower")
        # Lantern housing (octagonal extruded square)
        lh = _cv_circle(tree, (base_x, -500), 0.18, 8)
        lhx = _fill_extrude(tree, lh.outputs['Curve'] if lh else None,
                             (base_x + 200, -500), (base_x + 400, -500), 0.35, "ornament")
        pieces.append(_move(tree, lhx, (base_x + 600, -500),
                             translation=(0, 0, H + 0.25), label="ornament"))
        # Pointed cap
        cap = _safe_node(tree, 'GeometryNodeMeshCone', (base_x, -900))
        if cap:
            cap.inputs['Radius Bottom'].default_value = 0.2
            cap.inputs['Radius Top'].default_value = 0
            cap.inputs['Depth'].default_value = 0.3
            cap.inputs['Vertices'].default_value = 8
            pieces.append(_move(tree, cap.outputs['Mesh'], (base_x + 200, -900),
                                 translation=(0, 0, H + 0.75), label="ornament"))
            color_node(cap, "ornament")
        # Finial ball
        fin = _safe_node(tree, 'GeometryNodeMeshIcoSphere', (base_x, -1200))
        if fin:
            fin.inputs['Radius'].default_value = 0.07
            fin.inputs['Subdivisions'].default_value = 3
            pieces.append(_move(tree, fin.outputs['Mesh'], (base_x + 200, -1200),
                                 translation=(0, 0, H + 1.0), label="ornament"))
            color_node(fin, "ornament")
        return _join_all(tree, pieces, (base_x + 1100, 0))


    # ─── PUBLIC FOUNTAIN ────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_street_lamp")
    return tree, gin, gout

register_builder(
    "MEL_street_lamp", build_street_lamp_group,
    "Street Lamp", "Misc prop (absorbed from monolith build_street_lamp).",
    category="set_dressing")


def build_stylized_tree_group(group_name="MEL_stylized_tree"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0) if spec['default'] is not None else 0, int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t in ('StringProperty', 'EnumProperty'):
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    PROPS = _make_props()
    base_x = -1400
    def _impl():
        """Stylized low-poly tree: trunk + 3 foliage icosphere clumps."""
        H = max(2.0, getattr(PROPS, 'height', 4.0))
        r_trunk = max(0.1, getattr(PROPS, 'base_radius', 1.0) * 0.18)
        pieces = []
        # Trunk
        trunk = _node(tree, 'GeometryNodeMeshCylinder', (base_x, 200))
        trunk.inputs['Radius'].default_value = r_trunk
        trunk.inputs['Depth'].default_value = H * 0.6
        trunk.inputs['Vertices'].default_value = 8
        pieces.append(_move(tree, trunk.outputs['Mesh'], (base_x + 200, 200),
                             translation=(0, 0, H * 0.3), label="tower"))
        color_node(trunk, "tower")
        # 3 foliage clumps (icosphere) overlapping at top
        import math
        for i, (dx, dy, sc) in enumerate([(0, 0, 1.0), (0.4, 0.2, 0.7), (-0.3, -0.3, 0.8)]):
            leaf = _safe_node(tree, 'GeometryNodeMeshIcoSphere', (base_x, -200 - i * 100))
            if leaf is None: continue
            leaf.inputs['Radius'].default_value = r_trunk * 5
            leaf.inputs['Subdivisions'].default_value = 2
            pieces.append(_move(tree, leaf.outputs['Mesh'], (base_x + 200, -200 - i * 100),
                                 translation=(dx * H * 0.2, dy * H * 0.2, H * 0.7 + i * H * 0.1),
                                 scale=(sc, sc, sc * 0.85), label="organic"))
            color_node(leaf, "organic")
        return _join_all(tree, pieces, (base_x + 1100, 0))


    # ─── BOULDER PILE ───────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_stylized_tree")
    return tree, gin, gout

register_builder(
    "MEL_stylized_tree", build_stylized_tree_group,
    "Stylized Tree", "Misc prop (absorbed from monolith build_stylized_tree).",
    category="set_dressing")


def build_boulder_pile_group(group_name="MEL_boulder_pile"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0) if spec['default'] is not None else 0, int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t in ('StringProperty', 'EnumProperty'):
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    PROPS = _make_props()
    base_x = -1400
    def _impl():
        """Cluster of weathered boulders (5 irregular icospheres)."""
        R = max(0.4, getattr(PROPS, 'base_radius', 1.0) * 0.7)
        pieces = []
        import random as _rnd, math
        _rnd.seed(getattr(PROPS, 'seed', 7))
        for i in range(6):
            rad = R * _rnd.uniform(0.7, 1.3)
            boulder = _safe_node(tree, 'GeometryNodeMeshIcoSphere', (base_x, 200 - i * 120))
            if boulder is None: continue
            boulder.inputs['Radius'].default_value = rad
            boulder.inputs['Subdivisions'].default_value = 2
            dx = _rnd.uniform(-R * 1.4, R * 1.4)
            dy = _rnd.uniform(-R * 1.4, R * 1.4)
            dz = abs(_rnd.uniform(0, R * 0.6))
            sx = _rnd.uniform(0.7, 1.4)
            sy = _rnd.uniform(0.7, 1.4)
            sz = _rnd.uniform(0.6, 1.2)
            pieces.append(_move(tree, boulder.outputs['Mesh'], (base_x + 220, 200 - i * 120),
                                 translation=(dx, dy, dz + rad * 0.6),
                                 rotation=(_rnd.uniform(-1, 1), _rnd.uniform(-1, 1), _rnd.uniform(-1, 1)),
                                 scale=(sx, sy, sz), label="tower"))
            color_node(boulder, "tower")
        return _join_all(tree, pieces, (base_x + 1100, 0))


    # ─── HERALDIC BANNER ────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_boulder_pile")
    return tree, gin, gout

register_builder(
    "MEL_boulder_pile", build_boulder_pile_group,
    "Boulder Pile", "Misc prop (absorbed from monolith build_boulder_pile).",
    category="set_dressing")


def build_heraldic_banner_group(group_name="MEL_heraldic_banner"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0) if spec['default'] is not None else 0, int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t in ('StringProperty', 'EnumProperty'):
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    PROPS = _make_props()
    base_x = -1400
    def _impl():
        """Hanging vertical banner on a horizontal pole with bracket."""
        H = max(1.5, getattr(PROPS, 'height', 2.5))
        W = max(0.5, getattr(PROPS, 'base_radius', 1.0) * 0.7)
        pieces = []
        # Mounting block (assumes hangs from wall behind)
        pieces.append(_move(tree, _cube(tree, (base_x, 200), 0.15, 0.15, 0.3, "tower"),
                             (base_x + 200, 200), translation=(0, W * 0.5, H + 0.15),
                             label="tower"))
        # Horizontal pole sticking out
        pole = _node(tree, 'GeometryNodeMeshCylinder', (base_x, -100))
        pole.inputs['Radius'].default_value = 0.04
        pole.inputs['Depth'].default_value = W * 1.4
        pole.inputs['Vertices'].default_value = 10
        pieces.append(_move(tree, pole.outputs['Mesh'], (base_x + 200, -100),
                             translation=(0, 0, H + 0.05),
                             rotation=(1.5708, 0, 0), label="ornament"))
        color_node(pole, "ornament")
        # Banner cloth (thin tall cube hanging from pole)
        pieces.append(_move(tree, _cube(tree, (base_x, -400), W, 0.03, H, "ornament"),
                             (base_x + 200, -400), translation=(0, 0, H * 0.5),
                             label="ornament"))
        # Bottom fringe (3 small triangles via small cubes)
        for i in range(3):
            x = -W * 0.3 + i * (W * 0.3)
            pieces.append(_move(tree, _cube(tree, (base_x, -700 - i * 60),
                                              W * 0.18, 0.03, 0.1, "ornament"),
                                 (base_x + 220, -700 - i * 60),
                                 translation=(x, 0, -0.05), label="ornament"))
        return _join_all(tree, pieces, (base_x + 1100, 0))


    # ─── TORCH SCONCE ───────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_heraldic_banner")
    return tree, gin, gout

register_builder(
    "MEL_heraldic_banner", build_heraldic_banner_group,
    "Heraldic Banner", "Misc prop (absorbed from monolith build_heraldic_banner).",
    category="set_dressing")


def build_torch_sconce_group(group_name="MEL_torch_sconce"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0) if spec['default'] is not None else 0, int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t in ('StringProperty', 'EnumProperty'):
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    PROPS = _make_props()
    base_x = -1400
    def _impl():
        """Wall-mounted iron torch with brazier-cup + curved bracket + flame."""
        H = max(1.0, getattr(PROPS, 'height', 1.5))
        pieces = []
        # Mounting plate (against wall)
        pieces.append(_move(tree, _cube(tree, (base_x, 200), 0.15, 0.04, 0.25, "ornament"),
                             (base_x + 200, 200), translation=(0, 0, H), label="ornament"))
        # Curved bracket arm (bezier swept thin)
        arm = _safe_node(tree, 'GeometryNodeCurveQuadraticBezier', (base_x, -100))
        if arm:
            try:
                arm.inputs['Resolution'].default_value = 16
                arm.inputs['Start'].default_value = (0, 0, H + 0.05)
                arm.inputs['Middle'].default_value = (0, -0.15, H + 0.05)
                arm.inputs['End'].default_value = (0, -0.25, H + 0.15)
            except Exception:
                pass
            prof = _cv_circle(tree, (base_x, -300), 0.025, 8)
            sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 250, -100))
            if sw and prof:
                _link(tree, arm.outputs['Curve'], sw.inputs['Curve'])
                _link(tree, prof.outputs['Curve'], sw.inputs['Profile Curve'])
                color_node(sw, "ornament")
                pieces.append(sw.outputs['Mesh'])
        # Brazier cup (small cylinder)
        cup = _node(tree, 'GeometryNodeMeshCylinder', (base_x, -600))
        cup.inputs['Radius'].default_value = 0.07
        cup.inputs['Depth'].default_value = 0.1
        cup.inputs['Vertices'].default_value = 10
        pieces.append(_move(tree, cup.outputs['Mesh'], (base_x + 200, -600),
                             translation=(0, -0.25, H + 0.2), label="ornament"))
        color_node(cup, "ornament")
        # Flame (cone pointing up)
        flame = _safe_node(tree, 'GeometryNodeMeshCone', (base_x, -900))
        if flame:
            flame.inputs['Radius Bottom'].default_value = 0.06
            flame.inputs['Radius Top'].default_value = 0
            flame.inputs['Depth'].default_value = 0.18
            flame.inputs['Vertices'].default_value = 8
            pieces.append(_move(tree, flame.outputs['Mesh'], (base_x + 200, -900),
                                 translation=(0, -0.25, H + 0.34), label="ornament"))
            color_node(flame, "ornament")
        return _join_all(tree, pieces, (base_x + 1000, 0))


    # ==============================================================================
    # *  RUINS / DESTRUCTION  (v2.51)
    # ==============================================================================

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_torch_sconce")
    return tree, gin, gout

register_builder(
    "MEL_torch_sconce", build_torch_sconce_group,
    "Torch Sconce", "Misc prop (absorbed from monolith build_torch_sconce).",
    category="set_dressing")


def build_wall_ruined_group(group_name="MEL_wall_ruined"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0) if spec['default'] is not None else 0, int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t in ('StringProperty', 'EnumProperty'):
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    PROPS = _make_props()
    base_x = -1400
    def _impl():
        """Stone wall with crumbled top, random tumbled chunks and rubble at base."""
        import math, random
        W       = getattr(PROPS, 'wall_segments', 3) * getattr(PROPS, 'unit_size', 1.0) * 2.0
        H       = getattr(PROPS, 'wall_height', 3.0)
        T       = getattr(PROPS, 'wall_thickness', 0.35)
        damage  = getattr(PROPS, 'ruin_damage', 0.6)
        seed_v  = getattr(PROPS, 'seed', 1)
        style   = getattr(PROPS, 'ruin_style', 'CRUMBLED')
        rng     = random.Random(seed_v + 7)
        pieces  = []

        # Surviving wall body (height drops with damage)
        survive_h = max(0.3, H * (1.0 - damage * 0.55))
        pieces.append(_move(tree, _cube(tree, (base_x, 200), W, T, survive_h, "tower"),
                            (base_x + 200, 200), translation=(0, 0, survive_h / 2), label="tower"))

        # Tumbled chunk ledge at top edge
        for i in range(max(2, int(8 * damage))):
            cx  = rng.uniform(-W * 0.45, W * 0.45)
            cz  = survive_h + rng.uniform(0.0, H * 0.3)
            cw  = rng.uniform(T * 0.8, T * 1.6)
            ch  = rng.uniform(T * 0.4, T * 1.0)
            cd  = rng.uniform(T * 0.6, T * 1.2)
            ang = rng.uniform(-0.4, 0.4)
            pieces.append(_move(tree, _cube(tree, (base_x, -400 - i * 120), cw, cd, ch, "tower"),
                                (base_x + 200, -400 - i * 120),
                                translation=(cx, 0, cz), rotation=(0, 0, ang), label="tower"))

        # Ground rubble scatter
        for i in range(max(3, int(10 * damage))):
            rx  = rng.uniform(-W * 0.4, W * 0.4)
            ry  = rng.uniform(-T * 0.8, T * 0.8)
            rw  = rng.uniform(0.15, 0.4)
            rh  = rng.uniform(0.08, 0.25)
            ang_r = rng.uniform(0, math.tau)
            ang_p = rng.uniform(-0.5, 0.5)
            pieces.append(_move(tree, _cube(tree, (base_x, -2000 - i * 100), rw, rw * 0.9, rh, "wall"),
                                (base_x + 200, -2000 - i * 100),
                                translation=(rx, ry, rh / 2),
                                rotation=(ang_p, ang_p * 0.5, ang_r), label="wall"))

        # Overgrown: torus vine lumps along surviving top
        if style == 'OVERGROWN':
            for i in range(6):
                tor = _safe_node(tree, 'GeometryNodeMeshTorus', (base_x, -4000 - i * 80))
                if tor:
                    try:
                        tor.inputs['Major Radius'].default_value = 0.12
                        tor.inputs['Minor Radius'].default_value = 0.06
                        tor.inputs['Major Segments'].default_value = 16
                        tor.inputs['Minor Segments'].default_value = 6
                    except Exception: pass
                    color_node(tor, "ornament")
                    pieces.append(_move(tree, tor.outputs['Mesh'],
                                        (base_x + 200, -4000 - i * 80),
                                        translation=(rng.uniform(-W * 0.4, W * 0.4), 0,
                                                     survive_h + rng.uniform(-0.1, 0.2)),
                                        label="ornament"))

        return _finalize_building(tree, pieces, (base_x + 1200, 0))


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_wall_ruined")
    return tree, gin, gout

register_builder(
    "MEL_wall_ruined", build_wall_ruined_group,
    "Wall Ruined", "Misc prop (absorbed from monolith build_wall_ruined).",
    category="set_dressing")


def build_arch_broken_group(group_name="MEL_arch_broken"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0) if spec['default'] is not None else 0, int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t in ('StringProperty', 'EnumProperty'):
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    PROPS = _make_props()
    base_x = -1400
    def _impl():
        """Arch with broken ring: left side survives, right pier shorter, keystone fallen."""
        import math, random
        hw       = getattr(PROPS, 'arch_radius', 1.2)
        thickness= getattr(PROPS, 'arch_thickness', 0.35)
        depth    = 0.6
        damage   = getattr(PROPS, 'ruin_damage', 0.55)
        rng      = random.Random(getattr(PROPS, 'seed', 1) + 13)
        spring_z = hw * 0.25
        pieces   = []

        pier_w = thickness * 1.4
        pier_h = spring_z + hw * 0.8

        # Left pier (full height)
        pieces.append(_move(tree, _cube(tree, (base_x, 200), pier_w, depth, pier_h, "tower"),
                            (base_x + 200, 200),
                            translation=(-hw - pier_w / 2, 0, pier_h / 2), label="tower"))
        # Right pier (shortened by damage)
        r_pier_h = max(0.4, pier_h * (1.0 - damage * 0.35))
        pieces.append(_move(tree, _cube(tree, (base_x, -100), pier_w, depth, r_pier_h, "tower"),
                            (base_x + 200, -100),
                            translation=(hw + pier_w / 2, 0, r_pier_h / 2), label="tower"))

        # Arch voussoir ring - only surviving portion (left side)
        n_vouss = 8
        survive_count = max(3, int(n_vouss * (1.0 - damage * 0.5)))
        for i in range(survive_count):
            ang = math.pi * (i + 0.5) / n_vouss
            cx  = -math.cos(ang) * hw
            cz  = spring_z + math.sin(ang) * hw
            vw  = (math.pi * hw / n_vouss) * 1.05
            rot_a = math.pi / 2 - ang
            pieces.append(_move(tree, _cube(tree, (base_x, -600 - i * 80), vw, depth, thickness, "wall"),
                                (base_x + 200, -600 - i * 80),
                                translation=(cx, 0, cz), rotation=(0, rot_a, 0), label="wall"))

        # Fallen keystone on ground
        pieces.append(_move(tree, _cube(tree, (base_x, -2000), thickness * 1.2, depth, thickness * 0.9, "wall"),
                            (base_x + 200, -2000),
                            translation=(rng.uniform(-0.3, 0.5), 0, thickness * 0.45),
                            rotation=(0, rng.uniform(0.2, 0.6), 0), label="wall"))

        # Rubble scatter
        for i in range(6):
            rx = rng.uniform(-hw * 1.2, hw * 1.2)
            rs = rng.uniform(0.1, 0.28)
            pieces.append(_move(tree, _cube(tree, (base_x, -2400 - i * 80), rs, rs * 0.85, rs * 0.6, "tower"),
                                (base_x + 200, -2400 - i * 80),
                                translation=(rx, rng.uniform(-depth * 0.4, depth * 0.4), rs * 0.3),
                                rotation=(rng.uniform(-0.4, 0.4), rng.uniform(-0.3, 0.3),
                                          rng.uniform(0, math.tau)), label="tower"))

        return _finalize_building(tree, pieces, (base_x + 1200, 0))


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_arch_broken")
    return tree, gin, gout

register_builder(
    "MEL_arch_broken", build_arch_broken_group,
    "Arch Broken", "Misc prop (absorbed from monolith build_arch_broken).",
    category="set_dressing")


def build_collapsed_floor_group(group_name="MEL_collapsed_floor"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0) if spec['default'] is not None else 0, int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t in ('StringProperty', 'EnumProperty'):
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    PROPS = _make_props()
    base_x = -1400
    def _impl():
        """Angled/broken floor slab with exposed I-beams and a rubble slide."""
        import math, random
        W      = max(3.0, getattr(PROPS, 'wall_segments', 3) * getattr(PROPS, 'unit_size', 1.0) * 1.5)
        D      = W * 0.65
        damage = getattr(PROPS, 'ruin_damage', 0.6)
        rng    = random.Random(getattr(PROPS, 'seed', 1) + 17)
        tilt_y = damage * 0.35
        pieces = []

        # Main slab pitched to simulate partial collapse
        pieces.append(_move(tree, _cube(tree, (base_x, 200), W, D, 0.22, "wall"),
                            (base_x + 200, 200),
                            translation=(0, 0, 2.0), rotation=(tilt_y, 0, 0), label="wall"))

        # Exposed I-beams (web + top flange per beam)
        for bi in range(3):
            bx = (bi - 1) * (W / 4)
            pieces.append(_move(tree, _cube(tree, (base_x, -400 - bi * 200), 0.06, D + 0.4, 0.28, "ornament"),
                                (base_x + 200, -400 - bi * 200),
                                translation=(bx, 0, 1.88), rotation=(tilt_y, 0, 0), label="ornament"))
            pieces.append(_move(tree, _cube(tree, (base_x, -600 - bi * 200), 0.22, D + 0.4, 0.05, "ornament"),
                                (base_x + 200, -600 - bi * 200),
                                translation=(bx, 0, 2.03), rotation=(tilt_y, 0, 0), label="ornament"))

        # Rubble slide at low end
        for i in range(7):
            rs = rng.uniform(0.1, 0.3)
            pieces.append(_move(tree, _cube(tree, (base_x, -1800 - i * 80), rs, rs * 0.85, rs * 0.55, "tower"),
                                (base_x + 200, -1800 - i * 80),
                                translation=(rng.uniform(-W * 0.4, W * 0.4),
                                             D * 0.45 + i * 0.05,
                                             rng.uniform(0.05, 0.5) * damage),
                                rotation=(rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3),
                                          rng.uniform(0, 6.28)), label="tower"))

        return _finalize_building(tree, pieces, (base_x + 1200, 0))


    # ==============================================================================
    # *  MODULAR FRAMES & STRUCTURAL GAP-FILL  (v2.51)
    # ==============================================================================

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_collapsed_floor")
    return tree, gin, gout

register_builder(
    "MEL_collapsed_floor", build_collapsed_floor_group,
    "Collapsed Floor", "Misc prop (absorbed from monolith build_collapsed_floor).",
    category="set_dressing")


def build_door_frame_group(group_name="MEL_door_frame"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0) if spec['default'] is not None else 0, int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t in ('StringProperty', 'EnumProperty'):
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    PROPS = _make_props()
    base_x = -1400
    def _impl():
        """Standalone door frame: two jambs + lintel + sill + optional arch cap.
        Place into a matching wall cutout for a complete door opening."""
        import math
        FW    = getattr(PROPS, 'door_width', 1.0) if hasattr(PROPS, 'door_width') else 1.0
        FH    = getattr(PROPS, 'door_height', 2.2) if hasattr(PROPS, 'door_height') else 2.2
        T     = getattr(PROPS, 'wall_thickness', 0.35)
        reveal= T * 0.4
        jw    = 0.18
        cap   = getattr(PROPS, 'frame_arch_cap', 'ROMAN')
        pieces= []

        # Side jambs
        for sx in (-1, 1):
            pieces.append(_move(tree, _cube(tree, (base_x, 200 + sx * 100), jw, T + reveal * 2, FH, "wall"),
                                (base_x + 200, 200 + sx * 100),
                                translation=(sx * (FW / 2 + jw / 2), 0, FH / 2), label="wall"))
        # Lintel
        pieces.append(_move(tree, _cube(tree, (base_x, 600), FW + jw * 2, T + reveal * 2, 0.2, "wall"),
                            (base_x + 200, 600), translation=(0, 0, FH + 0.1), label="wall"))
        # Sill
        pieces.append(_move(tree, _cube(tree, (base_x, 900), FW + jw * 2.4, T + reveal * 3, 0.08, "wall"),
                            (base_x + 200, 900), translation=(0, 0, 0.04), label="wall"))

        # Arch cap
        if cap == 'ROMAN':
            arc = _safe_node(tree, 'GeometryNodeCurveArc', (base_x, -400))
            if arc:
                try:
                    arc.mode = 'RADIUS'
                    arc.inputs['Radius'].default_value      = FW / 2
                    arc.inputs['Start Angle'].default_value = 0.0
                    arc.inputs['Sweep Angle'].default_value = math.pi
                    arc.inputs['Resolution'].default_value  = 20
                except Exception: pass
                rot_n = _safe_node(tree, 'GeometryNodeTransform', (base_x + 200, -400))
                if rot_n:
                    rot_n.inputs['Rotation'].default_value    = (math.radians(90), 0, 0)
                    rot_n.inputs['Translation'].default_value = (0, 0, FH + FW / 2)
                    _link(tree, arc.outputs['Curve'], rot_n.inputs['Geometry'])
                    prof = _rect_profile(tree, (base_x, -600), T + reveal * 2, 0.16, "wall")
                    c2m  = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 400, -400))
                    if c2m and prof:
                        _link(tree, rot_n.outputs['Geometry'], c2m.inputs['Curve'])
                        _link(tree, prof,     c2m.inputs['Profile Curve'])   # prof is already a socket
                        color_node(c2m, "wall"); pieces.append(c2m.outputs['Mesh'])
        elif cap == 'GOTHIC':
            apex_z = FH + FW * 0.8
            for sx in (-1, 1):
                seg = _safe_node(tree, 'GeometryNodeCurvePrimitiveBezierSegment',
                                 (base_x, -800 + sx * 100))
                if seg:
                    try:
                        seg.inputs['Resolution'].default_value   = 16
                        seg.inputs['Start'].default_value        = (sx * FW / 2, 0, FH)
                        seg.inputs['Start Handle'].default_value = (sx * FW / 2, 0, FH + FW * 0.5)
                        seg.inputs['End Handle'].default_value   = (0, 0, apex_z - 0.1)
                        seg.inputs['End'].default_value          = (0, 0, apex_z)
                    except Exception: pass
                    prof = _rect_profile(tree, (base_x, -1000 + sx * 100), T + reveal * 2, 0.16, "wall")
                    c2m  = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 250, -800 + sx * 100))
                    if c2m and prof:
                        _link(tree, seg.outputs['Curve'], c2m.inputs['Curve'])
                        _link(tree, prof, c2m.inputs['Profile Curve'])   # prof is already a socket
                        color_node(c2m, "wall"); pieces.append(c2m.outputs['Mesh'])

        return _join_all(tree, pieces, (base_x + 1000, 0))


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_door_frame")
    return tree, gin, gout

register_builder(
    "MEL_door_frame", build_door_frame_group,
    "Door Frame", "Misc prop (absorbed from monolith build_door_frame).",
    category="set_dressing")


def build_window_frame_group(group_name="MEL_window_frame"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0) if spec['default'] is not None else 0, int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t in ('StringProperty', 'EnumProperty'):
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    PROPS = _make_props()
    base_x = -1400
    def _impl():
        """Standalone window frame: sill + jambs + head rail + mullion or shutters."""
        FW    = getattr(PROPS, 'window_width', 0.9) if hasattr(PROPS, 'window_width') else 0.9
        FH    = getattr(PROPS, 'window_height', 1.4) if hasattr(PROPS, 'window_height') else 1.4
        T     = getattr(PROPS, 'wall_thickness', 0.35)
        reveal= T * 0.35
        jw    = 0.14
        pieces= []

        # Jambs
        for sx in (-1, 1):
            pieces.append(_move(tree, _cube(tree, (base_x, 200 + sx * 80), jw, T + reveal * 2, FH, "wall"),
                                (base_x + 200, 200 + sx * 80),
                                translation=(sx * (FW / 2 + jw / 2), 0, FH / 2), label="wall"))
        # Head
        pieces.append(_move(tree, _cube(tree, (base_x, 500), FW + jw * 2, T + reveal * 2, 0.14, "wall"),
                            (base_x + 200, 500), translation=(0, 0, FH + 0.07), label="wall"))
        # Sill with drip edge
        sill_d = T + reveal * 2.8
        pieces.append(_move(tree, _cube(tree, (base_x, 800), FW + jw * 2.6, sill_d, 0.1, "wall"),
                            (base_x + 200, 800), translation=(0, 0, 0.05), label="wall"))
        pieces.append(_move(tree, _cube(tree, (base_x, 1000), FW + jw * 2.8, 0.07, 0.07, "wall"),
                            (base_x + 200, 1000), translation=(0, sill_d / 2, -0.035), label="wall"))

        if getattr(PROPS, 'frame_with_shutters', False):
            for sx in (-1, 1):
                pieces.append(_move(tree, _cube(tree, (base_x, -600 + sx * 60),
                                                FW / 2 * 0.9, 0.04, FH * 0.92, "ornament"),
                                    (base_x + 200, -600 + sx * 60),
                                    translation=(sx * FW * 0.24, -(T / 2 + 0.06), FH / 2), label="ornament"))
        else:
            # Central mullion
            pieces.append(_move(tree, _cube(tree, (base_x, -300), 0.05, T + reveal * 2, FH, "wall"),
                                (base_x + 200, -300), translation=(0, 0, FH / 2), label="wall"))

        return _join_all(tree, pieces, (base_x + 900, 0))


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_window_frame")
    return tree, gin, gout

register_builder(
    "MEL_window_frame", build_window_frame_group,
    "Window Frame", "Misc prop (absorbed from monolith build_window_frame).",
    category="set_dressing")


def build_barrel_stack_group(group_name="MEL_barrel_stack"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0) if spec['default'] is not None else 0, int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t in ('StringProperty', 'EnumProperty'):
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    PROPS = _make_props()
    base_x = -1400
    def _impl():
        """Stack of 2-3 wooden barrels: swept-cylinder staves + hoop rings."""
        import math, random
        n    = min(4, max(1, getattr(PROPS, 'prop_count', 3)))
        rng  = random.Random(getattr(PROPS, 'seed', 1) + 31)
        br   = getattr(PROPS, 'base_radius', 0.3) * 0.55
        bh   = max(0.4, getattr(PROPS, 'height', 0.8) * 0.5)
        scat = getattr(PROPS, 'prop_scatter', 0.3) * 0.1
        pieces = []

        positions = ([(0,0,0)] if n==1
                     else [(-br*1.1,0,0),(br*1.1,0,0)] if n==2
                     else [(-br*1.1,0,0),(br*1.1,0,0),(0,0,bh)] if n==3
                     else [(-br*1.3,-br*.8,0),(br*1.3,-br*.8,0),(0,br*.8,0),(0,0,bh)])

        for bi, (bx, by, bz) in enumerate(positions):
            ox    = rng.uniform(-scat, scat)
            tilt  = rng.uniform(-0.05, 0.05)
            # Body
            cyl = _node(tree, 'GeometryNodeMeshCylinder', (base_x, 200 - bi * 200))
            cyl.inputs['Radius'].default_value   = br
            cyl.inputs['Depth'].default_value    = bh
            cyl.inputs['Vertices'].default_value = 16
            color_node(cyl, "house")
            pieces.append(_move(tree, cyl.outputs['Mesh'], (base_x + 200, 200 - bi * 200),
                                translation=(bx + ox, by, bz + bh / 2),
                                rotation=(tilt, tilt * 0.5, 0), label="house"))
            # 3 hoop rings
            for ri, frac in enumerate([0.2, 0.5, 0.8]):
                tor = _safe_node(tree, 'GeometryNodeMeshTorus', (base_x, -400 - bi * 200 - ri * 60))
                if tor:
                    try:
                        tor.inputs['Major Radius'].default_value = br * 1.04
                        tor.inputs['Minor Radius'].default_value = 0.025
                        tor.inputs['Major Segments'].default_value = 24
                        tor.inputs['Minor Segments'].default_value = 6
                    except Exception: pass
                    color_node(tor, "ornament")
                    pieces.append(_move(tree, tor.outputs['Mesh'],
                                        (base_x + 200, -400 - bi * 200 - ri * 60),
                                        translation=(bx + ox, by, bz + bh * frac), label="ornament"))

        return _join_all(tree, pieces, (base_x + 1000, 0))


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_barrel_stack")
    return tree, gin, gout

register_builder(
    "MEL_barrel_stack", build_barrel_stack_group,
    "Barrel Stack", "Misc prop (absorbed from monolith build_barrel_stack).",
    category="set_dressing")


def build_crate_pile_group(group_name="MEL_crate_pile"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0) if spec['default'] is not None else 0, int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t in ('StringProperty', 'EnumProperty'):
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    PROPS = _make_props()
    base_x = -1400
    def _impl():
        """Pile of wooden crates with random scatter, tilts, and plank lines."""
        import random
        n    = min(6, max(1, getattr(PROPS, 'prop_count', 4)))
        scat = getattr(PROPS, 'prop_scatter', 0.35)
        rng  = random.Random(getattr(PROPS, 'seed', 1) + 43)
        cs   = max(0.3, getattr(PROPS, 'base_radius', 0.5) * 0.7)
        pieces = []

        for i in range(n):
            row = i // 2;  col = i % 2
            cx  = (col - 0.5) * cs * 1.08 + rng.uniform(-scat * 0.15, scat * 0.15)
            cy  = rng.uniform(-scat * 0.1, scat * 0.1)
            cz  = row * cs * 1.02
            cw  = cs * rng.uniform(0.85, 1.1)
            cd  = cs * rng.uniform(0.85, 1.05)
            ch  = cs * rng.uniform(0.7,  1.0)
            tlt = rng.uniform(-0.07, 0.07) * scat
            pieces.append(_move(tree, _cube(tree, (base_x, 200 - i * 150), cw, cd, ch, "house"),
                                (base_x + 200, 200 - i * 150),
                                translation=(cx, cy, cz + ch / 2),
                                rotation=(tlt, tlt * 0.6, rng.uniform(-0.1, 0.1) * scat), label="house"))
            # Plank seam lines on top
            for li in range(3):
                lx = (li - 1) * cw * 0.28
                pieces.append(_move(tree, _cube(tree, (base_x, -800 - i*150 - li*40),
                                                0.03, cd * 0.92, ch * 0.02, "ornament"),
                                    (base_x + 200, -800 - i*150 - li*40),
                                    translation=(cx + lx, cy, cz + ch + ch * 0.01),
                                    rotation=(tlt, tlt * 0.6, 0), label="ornament"))

        return _join_all(tree, pieces, (base_x + 900, 0))


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_crate_pile")
    return tree, gin, gout

register_builder(
    "MEL_crate_pile", build_crate_pile_group,
    "Crate Pile", "Misc prop (absorbed from monolith build_crate_pile).",
    category="set_dressing")


def build_campfire_group(group_name="MEL_campfire"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0) if spec['default'] is not None else 0, int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t in ('StringProperty', 'EnumProperty'):
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    PROPS = _make_props()
    base_x = -1400
    def _impl():
        """6-log radial campfire with stone/ash ring and two-cone flame stand-in."""
        import math, random
        r_logs = max(0.3, getattr(PROPS, 'base_radius', 0.4) * 0.55)
        rng    = random.Random(getattr(PROPS, 'seed', 1) + 61)
        pieces = []

        for li in range(6):
            ang    = li * math.tau / 6 + rng.uniform(-0.1, 0.1)
            tilt   = math.radians(rng.uniform(8, 18))
            log    = _node(tree, 'GeometryNodeMeshCylinder', (base_x, 200 - li * 120))
            log.inputs['Radius'].default_value   = 0.065
            log.inputs['Depth'].default_value    = r_logs * 2.2
            log.inputs['Vertices'].default_value = 8
            color_node(log, "house")
            pieces.append(_move(tree, log.outputs['Mesh'], (base_x + 200, 200 - li * 120),
                                translation=(math.cos(ang) * r_logs * 0.35,
                                             math.sin(ang) * r_logs * 0.35,
                                             0.065 + rng.uniform(-0.02, 0.04)),
                                rotation=(math.pi / 2 - tilt, 0, ang), label="house"))

        # Stone/ash ring
        tor = _safe_node(tree, 'GeometryNodeMeshTorus', (base_x, -1200))
        if tor:
            try:
                tor.inputs['Major Radius'].default_value = r_logs * 1.2
                tor.inputs['Minor Radius'].default_value = r_logs * 0.25
                tor.inputs['Major Segments'].default_value = 24
                tor.inputs['Minor Segments'].default_value = 6
            except Exception: pass
            color_node(tor, "ornament"); pieces.append(tor.outputs['Mesh'])

        # Two-cone flame (outer + inner)
        for fi, (fr, fh, fz) in enumerate([(r_logs * 0.5, r_logs * 2.2, 0.15),
                                            (r_logs * 0.28, r_logs * 1.4, 0.35)]):
            flame = _safe_node(tree, 'GeometryNodeMeshCone', (base_x, -1600 - fi * 100))
            if flame:
                flame.inputs['Radius Bottom'].default_value = fr
                flame.inputs['Radius Top'].default_value    = 0
                flame.inputs['Depth'].default_value         = fh
                flame.inputs['Vertices'].default_value      = 10
                color_node(flame, "ornament")
                pieces.append(_move(tree, flame.outputs['Mesh'],
                                    (base_x + 200, -1600 - fi * 100),
                                    translation=(0, 0, fz + fh / 2), label="ornament"))

        return _join_all(tree, pieces, (base_x + 1000, 0))


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_campfire")
    return tree, gin, gout

register_builder(
    "MEL_campfire", build_campfire_group,
    "Campfire", "Misc prop (absorbed from monolith build_campfire).",
    category="set_dressing")


def build_archway_group(group_name="MEL_archway"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0) if spec['default'] is not None else 0, int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t in ('StringProperty', 'EnumProperty'):
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    PROPS = _make_props()
    base_x = -1400
    def _impl():
        """Advanced multi-style archway generator (v2.50).

        Styles: ROMAN - SEGMENTAL - HORSESHOE - GOTHIC - TUDOR - OGEE - LINTEL
        Anatomy: arch ring (swept rect profile) + piers + impost bands +
                 optional keystone + optional voussoir lines.
        """
        import math
        style    = getattr(PROPS, 'archway_style',      'ROMAN')
        W        = max(0.6,  getattr(PROPS, 'archway_width',      2.4))
        spring_z = max(0.5,  getattr(PROPS, 'archway_height',     2.6))
        depth    = max(0.2,  getattr(PROPS, 'archway_depth',      0.6))
        band     = max(0.08, getattr(PROPS, 'archway_thickness',  0.35))
        pier_w   = max(0.1,  getattr(PROPS, 'archway_pier_width', 0.5))
        want_ks  = getattr(PROPS, 'archway_keystone', True)
        want_piers = getattr(PROPS, 'archway_piers',  True)
        n_vouss  = int(getattr(PROPS, 'archway_voussoirs', 0))
        hw = W / 2.0
        parts = []

        # ── arch ring (spine + rectangular sweep) ──────────────────────────
        spine_curves = _arch_spine(tree, style, hw, spring_z, (base_x, 200), base_x)
        prof = _rect_profile(tree, (base_x, -250), depth, band, "arch")

        spine_join = _node(tree, 'GeometryNodeJoinGeometry', (base_x + 500, 200))
        color_node(spine_join, "arch")
        for c in spine_curves:
            _link(tree, c, spine_join.inputs['Geometry'])

        sweep = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 760, 200))
        if sweep is not None:
            _link(tree, spine_join.outputs['Geometry'], sweep.inputs['Curve'])
            if prof is not None:
                _link(tree, prof, sweep.inputs['Profile Curve'])
            try:
                sweep.inputs['Fill Caps'].default_value = True
            except Exception:
                pass
            color_node(sweep, "arch")
            parts.append(sweep.outputs['Mesh'])

        # ── piers / legs ───────────────────────────────────────────────────
        if want_piers:
            for i, sgn in enumerate((-1, 1)):
                pier = _cube(tree, (base_x, -700 + i * 60), pier_w, depth, spring_z, "pillar")
                parts.append(_move(tree, pier, (base_x + 230, -700 + i * 60),
                                   translation=(sgn * (hw + pier_w * 0.5), 0, spring_z * 0.5),
                                   label="pillar"))
            # impost bands at the springing line
            for i, sgn in enumerate((-1, 1)):
                imp = _cube(tree, (base_x, -1050 + i * 60),
                            pier_w + band * 1.2, depth * 1.15, band * 0.55, "ornament")
                parts.append(_move(tree, imp, (base_x + 230, -1050 + i * 60),
                                   translation=(sgn * (hw + pier_w * 0.5), 0, spring_z),
                                   label="ornament"))

        # ── keystone at apex ───────────────────────────────────────────────
        if want_ks and style != 'LINTEL':
            apex_lifts = {
                'ROMAN': hw, 'SEGMENTAL': hw * 0.42, 'HORSESHOE': hw * 1.15,
                'GOTHIC': hw * 1.4, 'TUDOR': hw * 0.62, 'OGEE': hw * 1.55,
            }
            lift = apex_lifts.get(style, hw)
            ks = _cube(tree, (base_x, -1350), band * 1.5, depth * 1.2, band * 2.1, "ornament")
            parts.append(_move(tree, ks, (base_x + 230, -1350),
                               translation=(0, 0, spring_z + lift), label="ornament"))

        # ── voussoir joint lines (instanced thin slabs along the arch ring) ─
        if n_vouss >= 3 and sweep is not None and len(spine_curves) > 0:
            rs = _safe_node(tree, 'GeometryNodeResampleCurve', (base_x + 520, 600))
            if rs is not None:
                try:
                    rs.mode = 'COUNT'
                except Exception:
                    pass
                rs.inputs['Count'].default_value = n_vouss
                _link(tree, spine_join.outputs['Geometry'], rs.inputs['Curve'])
                c2p = _safe_node(tree, 'GeometryNodeCurveToPoints', (base_x + 740, 600))
                if c2p is not None:
                    try:
                        c2p.mode = 'EVALUATED'
                    except Exception:
                        pass
                    _link(tree, rs.outputs['Curve'], c2p.inputs['Curve'])
                    vb = _cube(tree, (base_x + 520, 820), band * 0.14, depth * 1.06,
                               band * 1.2, "ornament")
                    voi = _node(tree, 'GeometryNodeInstanceOnPoints', (base_x + 960, 600))
                    _link(tree, c2p.outputs['Points'], voi.inputs['Points'])
                    _link(tree, vb, voi.inputs['Instance'])
                    try:
                        _link(tree, c2p.outputs['Rotation'], voi.inputs['Rotation'])
                    except Exception:
                        pass
                    vrz = _node(tree, 'GeometryNodeRealizeInstances', (base_x + 1180, 600))
                    _link(tree, voi.outputs['Instances'], vrz.inputs['Geometry'])
                    parts.append(vrz.outputs['Geometry'])

        return _join_all(tree, parts, (base_x + 1600, 0), weld=0.0)


    # ==============================================================================
    # *  ADVANCED BRIDGE GENERATOR  (v2.50)
    # ==============================================================================

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_archway")
    return tree, gin, gout

register_builder(
    "MEL_archway", build_archway_group,
    "Archway", "Misc prop (absorbed from monolith build_archway).",
    category="set_dressing")


def build_bridge_advanced_group(group_name="MEL_bridge_advanced"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0) if spec['default'] is not None else 0, int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t in ('StringProperty', 'EnumProperty'):
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    PROPS = _make_props()
    base_x = -1400
    def _impl():
        """Advanced multi-style parametric bridge generator (v2.50).

        Styles:
          STONE_ARCH     - N semicircular masonry arches + spandrel walls + parapet
          ROMAN_AQUEDUCT - Two-tier stone arch bridge with water channel on top
          SUSPENSION     - Two pylons + catenary main cables + vertical hangers + deck
          TRUSS          - Deck + triangular truss frames on each side
          BEAM           - Simple I-beam/girder deck on cylinder piers
          COVERED        - Timber deck + side walls + curved roof
        """
        import math
        style       = getattr(PROPS, 'bridge_style',         'STONE_ARCH')
        span        = max(4.0,  getattr(PROPS, 'bridge_span',        12.0))
        bw          = max(1.0,  getattr(PROPS, 'bridge_width',        3.0))
        rise        = max(0.5,  getattr(PROPS, 'bridge_rise',         2.5))
        n_arches    = max(1,    getattr(PROPS, 'bridge_arches',        3))
        deck_thick  = max(0.1,  getattr(PROPS, 'bridge_deck_thick',   0.25))
        has_rail    = getattr(PROPS, 'bridge_railings',  True)
        base_z      = 0.0
        parts       = []

        # ── helpers ────────────────────────────────────────────────────────
        def _swept_circle(radius, loc_arc, loc_sweep, y_off=0.0):
            """Tube arch: circle arc swept with a round profile."""
            a = _safe_node(tree, 'GeometryNodeCurveArc', loc_arc)
            if a is None:
                return None
            a.mode = 'RADIUS'
            a.inputs['Resolution'].default_value = 48
            a.inputs['Radius'].default_value     = radius
            a.inputs['Start Angle'].default_value = 0.0
            a.inputs['Sweep Angle'].default_value = math.pi
            color_node(a, "bridge")
            t = _move(tree, a.outputs['Curve'], (loc_arc[0] + 260, loc_arc[1]),
                      translation=(0, y_off, rise),
                      rotation=(math.radians(90), 0, 0), label="bridge")
            prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', loc_sweep)
            if prof is None:
                return None
            prof.mode = 'RADIUS'
            prof.inputs['Resolution'].default_value = 10
            prof.inputs['Radius'].default_value     = 0.2
            sw = _safe_node(tree, 'GeometryNodeCurveToMesh',
                            (loc_sweep[0] + 240, loc_sweep[1]))
            if sw is None:
                return None
            _link(tree, t, sw.inputs['Curve'])
            _link(tree, prof.outputs['Curve'], sw.inputs['Profile Curve'])
            try:
                sw.inputs['Fill Caps'].default_value = True
            except Exception:
                pass
            color_node(sw, "bridge")
            return sw.outputs['Mesh']

        # ── deck slab (shared by most styles) ──────────────────────────────
        def _deck_slab(y_off=0.0, z_off=0.0):
            """Flat deck: a box spanning the full length, width, deck_thick."""
            d = _cube(tree, (base_x, -400 + int(y_off * 10)),
                      span + 0.4, bw, deck_thick, "bridge")
            return _move(tree, d, (base_x + 230, -400 + int(y_off * 10)),
                         translation=(0, y_off, z_off + deck_thick * 0.5), label="bridge")

        # ── railing helper ──────────────────────────────────────────────────
        def _side_railing(y_edge, z_base, label="railing"):
            """Low parapet: a thin box along the deck edge."""
            r = _cube(tree, (base_x, -2200 + int(y_edge * 20)),
                      span + 0.5, 0.15, 0.55, label)
            return _move(tree, r, (base_x + 230, -2200 + int(y_edge * 20)),
                         translation=(0, y_edge, z_base + 0.28), label=label)

        # ══════════════════════════════════════════════════════════════════
        if style == 'STONE_ARCH':
            arch_span = span / n_arches
            hw = arch_span / 2.0
            for ai in range(n_arches):
                ax = -span / 2 + arch_span * ai + hw
                g = _swept_circle(hw, (base_x, -ai * 300), (base_x + 500, -ai * 300))
                if g is not None:
                    parts.append(_move(tree, g, (base_x + 800, -ai * 300),
                                       translation=(ax, 0, base_z), label="bridge"))
            # spandrel fill walls (thin boxes, one per bay between arches)
            for ai in range(n_arches):
                ax = -span / 2 + (arch_span * ai) + arch_span / 2
                sp = _cube(tree, (base_x, -1500 - ai * 80),
                           arch_span, deck_thick * 1.5, rise * 1.05, "wall")
                parts.append(_move(tree, sp, (base_x + 230, -1500 - ai * 80),
                                   translation=(ax, 0, rise * 0.5), label="wall"))
            # deck on top
            parts.append(_deck_slab(z_off=rise * 2 + deck_thick * 0.5))
            if has_rail:
                for sgn in (-1, 1):
                    parts.append(_side_railing(sgn * (bw / 2 + 0.05),
                                               rise * 2 + deck_thick))

        elif style == 'ROMAN_AQUEDUCT':
            # Lower tier: arches (same as stone arch)
            arch_span = span / max(1, n_arches)
            hw = arch_span / 2.0
            for ai in range(n_arches):
                ax = -span / 2 + arch_span * ai + hw
                g = _swept_circle(hw, (base_x, -ai * 300), (base_x + 500, -ai * 300))
                if g is not None:
                    parts.append(_move(tree, g, (base_x + 800, -ai * 300),
                                       translation=(ax, 0, base_z), label="bridge"))
            pier_h = rise * 1.8
            # Upper tier piers (narrower)
            for ai in range(n_arches + 1):
                ax = -span / 2 + arch_span * ai
                pp = _cube(tree, (base_x, -1800 - ai * 80),
                           arch_span * 0.22, bw * 0.7, rise, "pillar")
                parts.append(_move(tree, pp, (base_x + 230, -1800 - ai * 80),
                                   translation=(ax, 0, rise * 2 + rise * 0.5), label="pillar"))
            # Upper tier arches
            for ai in range(n_arches):
                ax = -span / 2 + arch_span * ai + hw
                g2 = _swept_circle(hw * 0.75, (base_x, -2400 - ai * 300),
                                    (base_x + 500, -2400 - ai * 300))
                if g2 is not None:
                    parts.append(_move(tree, g2, (base_x + 800, -2400 - ai * 300),
                                       translation=(ax, 0, rise * 2), label="bridge"))
            # Water channel on top (U-section slab pair)
            ch_z = rise * 4 + deck_thick
            channel_outer = _cube(tree, (base_x, -3200), span + 0.4, bw, 0.3, "bridge")
            parts.append(_move(tree, channel_outer, (base_x + 230, -3200),
                               translation=(0, 0, ch_z), label="bridge"))
            for sgn in (-1, 1):
                cw = _cube(tree, (base_x, -3400 + sgn * 40),
                           span + 0.4, 0.18, 0.45, "bridge")
                parts.append(_move(tree, cw, (base_x + 230, -3400 + sgn * 40),
                                   translation=(0, sgn * (bw / 2 - 0.09), ch_z + 0.38), label="bridge"))

        elif style == 'SUSPENSION':
            deck_z = rise * 0.7
            # Deck
            parts.append(_deck_slab(z_off=deck_z))
            # Two towers
            tower_h = rise * 2.5
            for sgn in (-1, 1):
                tw = _cube(tree, (base_x, -1000 + sgn * 40),
                           0.35, bw * 0.8, tower_h, "pillar")
                parts.append(_move(tree, tw, (base_x + 230, -1000 + sgn * 40),
                                   translation=(sgn * span * 0.45, 0, tower_h / 2), label="pillar"))
                # Tower cross bar
                cb = _cube(tree, (base_x, -1200 + sgn * 40),
                           0.35, bw * 1.1, 0.25, "pillar")
                parts.append(_move(tree, cb, (base_x + 230, -1200 + sgn * 40),
                                   translation=(sgn * span * 0.45, 0, tower_h * 0.85), label="pillar"))
            # Main catenary cables (bezier sweep)
            cable_prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x, -1600))
            if cable_prof:
                cable_prof.mode = 'RADIUS'
                cable_prof.inputs['Radius'].default_value      = 0.05
                cable_prof.inputs['Resolution'].default_value  = 8
                color_node(cable_prof, "railing")
                for y_c in (-bw * 0.35, bw * 0.35):
                    cat = _safe_node(tree, 'GeometryNodeCurvePrimitiveBezierSegment',
                                     (base_x, -1800))
                    if cat:
                        top_z = tower_h * 0.85
                        cat.inputs['Start'].default_value        = (-span * 0.45, y_c, top_z)
                        cat.inputs['Start Handle'].default_value = (-span * 0.1,  y_c, top_z - rise * 0.5)
                        cat.inputs['End Handle'].default_value   = ( span * 0.1,  y_c, top_z - rise * 0.5)
                        cat.inputs['End'].default_value          = ( span * 0.45, y_c, top_z)
                        cat.inputs['Resolution'].default_value   = 32
                        color_node(cat, "railing")
                        csw = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 280, -1800))
                        if csw:
                            _link(tree, cat.outputs['Curve'], csw.inputs['Curve'])
                            _link(tree, cable_prof.outputs['Curve'], csw.inputs['Profile Curve'])
                            color_node(csw, "railing")
                            parts.append(csw.outputs['Mesh'])
                            # Vertical hangers (instanced along cable)
                            rs = _safe_node(tree, 'GeometryNodeResampleCurve', (base_x + 480, -2000))
                            if rs:
                                try: rs.mode = 'COUNT'
                                except Exception: pass
                                rs.inputs['Count'].default_value = 12
                                _link(tree, cat.outputs['Curve'], rs.inputs['Curve'])
                                cp = _safe_node(tree, 'GeometryNodeCurveToPoints', (base_x + 680, -2000))
                                if cp:
                                    try: cp.mode = 'EVALUATED'
                                    except Exception: pass
                                    _link(tree, rs.outputs['Curve'], cp.inputs['Curve'])
                                    hng = _cube(tree, (base_x + 480, -2200), 0.04, 0.04,
                                                tower_h * 0.85 - deck_z, "railing")
                                    hi = _node(tree, 'GeometryNodeInstanceOnPoints',
                                                (base_x + 880, -2000))
                                    _link(tree, cp.outputs['Points'], hi.inputs['Points'])
                                    _link(tree, hng, hi.inputs['Instance'])
                                    hrz = _node(tree, 'GeometryNodeRealizeInstances',
                                                 (base_x + 1080, -2000))
                                    _link(tree, hi.outputs['Instances'], hrz.inputs['Geometry'])
                                    parts.append(hrz.outputs['Geometry'])
            if has_rail:
                for sgn in (-1, 1):
                    parts.append(_side_railing(sgn * bw * 0.5, deck_z + deck_thick))

        elif style == 'TRUSS':
            deck_z = 0.0
            parts.append(_deck_slab(z_off=deck_z))
            # Triangulated side trusses
            for sgn_y in (-1, 1):
                y_pos = sgn_y * (bw * 0.5 + 0.05)
                n_panels = max(4, n_arches * 2)
                panel_w = span / n_panels
                truss_h = rise
                for pi in range(n_panels):
                    x_l = -span / 2 + panel_w * pi
                    x_r = x_l + panel_w
                    x_m = (x_l + x_r) / 2
                    # bottom chord segment
                    bc = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine',
                                     (base_x, -1000 - pi * 60))
                    if bc:
                        bc.inputs['Start'].default_value = (x_l, y_pos, deck_z + deck_thick)
                        bc.inputs['End'].default_value   = (x_r, y_pos, deck_z + deck_thick)
                        color_node(bc, "bridge")
                        tp = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle',
                                        (base_x + 220, -1000 - pi * 60))
                        if tp:
                            tp.mode = 'RADIUS'; tp.inputs['Radius'].default_value = 0.06
                            tp.inputs['Resolution'].default_value = 8
                            tsw = _safe_node(tree, 'GeometryNodeCurveToMesh',
                                              (base_x + 460, -1000 - pi * 60))
                            if tsw:
                                _link(tree, bc.outputs['Curve'], tsw.inputs['Curve'])
                                _link(tree, tp.outputs['Curve'], tsw.inputs['Profile Curve'])
                                color_node(tsw, "bridge"); parts.append(tsw.outputs['Mesh'])
                    # diagonal web member
                    for (xa, za, xb, zb) in [
                        (x_l, deck_z + deck_thick, x_m, deck_z + truss_h),
                        (x_m, deck_z + truss_h,   x_r, deck_z + deck_thick),
                    ]:
                        dm = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine',
                                        (base_x, -3000 - pi * 30))
                        if dm:
                            dm.inputs['Start'].default_value = (xa, y_pos, za)
                            dm.inputs['End'].default_value   = (xb, y_pos, zb)
                            color_node(dm, "bridge")
                            dp = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle',
                                            (base_x + 220, -3000 - pi * 30))
                            if dp:
                                dp.mode = 'RADIUS'; dp.inputs['Radius'].default_value = 0.045
                                dp.inputs['Resolution'].default_value = 8
                                dsw = _safe_node(tree, 'GeometryNodeCurveToMesh',
                                                  (base_x + 460, -3000 - pi * 30))
                                if dsw:
                                    _link(tree, dm.outputs['Curve'], dsw.inputs['Curve'])
                                    _link(tree, dp.outputs['Curve'], dsw.inputs['Profile Curve'])
                                    color_node(dsw, "bridge"); parts.append(dsw.outputs['Mesh'])
            if has_rail:
                for sgn in (-1, 1):
                    parts.append(_side_railing(sgn * bw * 0.5, deck_z + deck_thick + rise))

        elif style == 'COVERED':
            deck_z = rise * 0.5
            # Deck
            parts.append(_deck_slab(z_off=deck_z))
            # Side walls
            wall_h = rise
            for sgn in (-1, 1):
                wd = _cube(tree, (base_x, -700 + sgn * 40), span, 0.2, wall_h, "wall")
                parts.append(_move(tree, wd, (base_x + 230, -700 + sgn * 40),
                                   translation=(0, sgn * bw * 0.5, deck_z + wall_h * 0.5),
                                   label="wall"))
            # Gable roof using the _curved_roof helper (gentle pitch, hip=False)
            roof_g = _curved_roof(tree, (base_x, -1200),
                                  size_x=span + 0.6, size_y=bw + 0.5,
                                  ridge_h=rise * 0.55, base_z=deck_z + wall_h,
                                  pitch=1.2, hip=False, eave_flip=0.05,
                                  thickness=-0.1, label="roof")
            parts.append(roof_g)

        else:  # BEAM - simple girder on piers
            deck_z = rise
            n_piers = max(0, n_arches - 1)
            # Piers
            for pi in range(n_piers):
                px = -span / 2 + span * (pi + 1) / (n_piers + 1)
                pc = _safe_node(tree, 'GeometryNodeMeshCylinder',
                                 (base_x, -500 - pi * 120))
                if pc:
                    pc.inputs['Radius'].default_value   = 0.35
                    pc.inputs['Depth'].default_value    = deck_z
                    pc.inputs['Vertices'].default_value = 12
                    color_node(pc, "pillar")
                    parts.append(_move(tree, pc.outputs['Mesh'],
                                       (base_x + 230, -500 - pi * 120),
                                       translation=(px, 0, deck_z * 0.5), label="pillar"))
            # Girder (two I-beam flanges + web)
            for fz in (deck_z, deck_z + deck_thick * 0.5, deck_z + deck_thick):
                fl = _cube(tree, (base_x, -1500 + int(fz * 10)), span, bw,
                           deck_thick * 0.2, "bridge")
                parts.append(_move(tree, fl, (base_x + 230, -1500 + int(fz * 10)),
                                   translation=(0, 0, fz), label="bridge"))
            if has_rail:
                for sgn in (-1, 1):
                    parts.append(_side_railing(sgn * bw * 0.5, deck_z + deck_thick))

        return _join_all(tree, parts, (base_x + 2200, 0), weld=0.01)


    # ==============================================================================
    #  ADVANCED FENCE GENERATOR  (v2.50)
    # ==============================================================================

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_bridge_advanced")
    return tree, gin, gout

register_builder(
    "MEL_bridge_advanced", build_bridge_advanced_group,
    "Bridge Advanced", "Misc prop (absorbed from monolith build_bridge_advanced).",
    category="set_dressing")


def build_fence_group(group_name="MEL_fence"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0) if spec['default'] is not None else 0, int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t in ('StringProperty', 'EnumProperty'):
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    PROPS = _make_props()
    base_x = -1400
    def _impl():
        """Advanced multi-style fence / barrier generator (v2.50).

        Styles:
          PICKET   - pointed picket fence, posts + 2 rails + vertical pickets
          IRON     - wrought-iron posts + rails + spear-tipped balusters
          RANCH    - 3-rail ranch / post-and-rail fence (thick timber)
          STONE    - low dry-stone wall with coping cap
          LATTICE  - diagonal crisscross slats in a perimeter frame
          BAMBOO   - vertical bamboo poles + horizontal lashings
          MODERN   - steel post + horizontal slat panels
        """
        import math
        style    = getattr(PROPS, 'fence_style',        'PICKET')
        length   = max(1.0,  getattr(PROPS, 'fence_length',       6.0))
        fh       = max(0.3,  getattr(PROPS, 'fence_height',       1.2))
        spacing  = max(0.2,  getattr(PROPS, 'fence_post_spacing', 1.5))
        n_rails  = max(1,    getattr(PROPS, 'fence_rails',         2))
        gap      = max(0.02, getattr(PROPS, 'fence_picket_gap',   0.06))
        parts    = []

        n_posts = max(2, int(length / spacing) + 1)
        actual_spacing = length / max(1, n_posts - 1)

        # ── shared post helper (CurveLine swept with a circle profile) ──────
        def _post_tube(radius, height, loc, tx, label="fence"):
            ln = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', loc)
            if ln is None:
                return None
            ln.inputs['Start'].default_value = (tx, 0, 0)
            ln.inputs['End'].default_value   = (tx, 0, height)
            color_node(ln, label)
            pr = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (loc[0], loc[1] - 120))
            if pr is None:
                return None
            pr.mode = 'RADIUS'
            pr.inputs['Radius'].default_value     = radius
            pr.inputs['Resolution'].default_value = 8
            color_node(pr, label)
            sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (loc[0] + 240, loc[1]))
            if sw is None:
                return None
            _link(tree, ln.outputs['Curve'], sw.inputs['Curve'])
            _link(tree, pr.outputs['Curve'], sw.inputs['Profile Curve'])
            try:
                sw.inputs['Fill Caps'].default_value = True
            except Exception:
                pass
            color_node(sw, label)
            return sw.outputs['Mesh']

        # ── shared horizontal rail helper ────────────────────────────────────
        def _rail_bar(y_thick, z_thick, z_pos, loc, label="fence"):
            r = _cube(tree, loc, length, y_thick, z_thick, label)
            return _move(tree, r, (loc[0] + 230, loc[1]),
                         translation=(0, 0, z_pos), label=label)

        # ══════════════════════════════════════════════════════════════════
        if style == 'PICKET':
            post_r   = 0.045
            rail_t   = 0.04
            pick_w   = 0.065
            pick_gap = max(0.02, gap)

            # Posts
            for pi in range(n_posts):
                x = -length / 2 + actual_spacing * pi
                g = _post_tube(post_r, fh + 0.08, (base_x, pi * 80), x, "fence")
                if g is not None:
                    parts.append(g)

            # Horizontal rails
            for ri in range(n_rails):
                z_r = fh * 0.2 + ri * (fh * 0.55 / max(1, n_rails - 1))
                parts.append(_rail_bar(0.05, rail_t, z_r, (base_x, -200 - ri * 60), "fence"))

            # Pickets (instanced along a MeshLine)
            n_picks = max(2, int(length / (pick_w + pick_gap)))
            actual_pw = length / n_picks
            for pi in range(n_picks):
                px = -length / 2 + actual_pw * pi + actual_pw * 0.5
                # picket body
                pk = _cube(tree, (base_x, -500 - pi * 40), pick_w, 0.028, fh, "fence")
                parts.append(_move(tree, pk, (base_x + 230, -500 - pi * 40),
                                   translation=(px, 0, fh * 0.5), label="fence"))
                # pointed top: small rotated cube
                pt = _cube(tree, (base_x, -520 - pi * 40), pick_w, 0.028, pick_w, "fence")
                parts.append(_move(tree, pt, (base_x + 230, -520 - pi * 40),
                                   translation=(px, 0, fh + pick_w * 0.35),
                                   rotation=(0, math.radians(45), 0), label="fence"))

        elif style == 'IRON':
            post_r  = 0.05
            bal_r   = 0.018
            rail_r  = 0.022

            # Posts (octagonal, via swept 8-circle)
            for pi in range(n_posts):
                x = -length / 2 + actual_spacing * pi
                g = _post_tube(post_r, fh, (base_x, pi * 80), x, "fence")
                if g is not None:
                    parts.append(g)
                # decorative scroll cap (small torus)
                sc = _safe_node(tree, 'GeometryNodeMeshTorus',
                                 (base_x, -200 + pi * 30))
                if sc:
                    try:
                        sc.inputs['Major Radius'].default_value  = post_r * 1.5
                        sc.inputs['Minor Radius'].default_value  = post_r * 0.3
                        sc.inputs['Major Segments'].default_value = 16
                        sc.inputs['Minor Segments'].default_value = 6
                    except Exception:
                        pass
                    color_node(sc, "ornament")
                    parts.append(_move(tree, sc.outputs['Mesh'],
                                       (base_x + 230, -200 + pi * 30),
                                       translation=(x, 0, fh + post_r * 1.5),
                                       rotation=(math.radians(90), 0, 0), label="ornament"))

            # Horizontal rails (swept thin circle)
            for ri in range(n_rails):
                z_r = fh * 0.1 + ri * (fh * 0.8 / max(1, n_rails - 1))
                rl = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (base_x, -500 - ri * 60))
                if rl:
                    rl.inputs['Start'].default_value = (-length / 2, 0, z_r)
                    rl.inputs['End'].default_value   = ( length / 2, 0, z_r)
                    color_node(rl, "fence")
                    rp = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle',
                                     (base_x, -560 - ri * 60))
                    if rp:
                        rp.mode = 'RADIUS'
                        rp.inputs['Radius'].default_value     = rail_r
                        rp.inputs['Resolution'].default_value = 8
                        rsw = _safe_node(tree, 'GeometryNodeCurveToMesh',
                                          (base_x + 220, -500 - ri * 60))
                        if rsw:
                            _link(tree, rl.outputs['Curve'], rsw.inputs['Curve'])
                            _link(tree, rp.outputs['Curve'], rsw.inputs['Profile Curve'])
                            color_node(rsw, "fence"); parts.append(rsw.outputs['Mesh'])

            # Balusters with spear tip (instanced)
            n_bals = max(2, int(length / (gap + bal_r * 2)))
            bsp = length / n_bals
            for bi in range(n_bals):
                bx2 = -length / 2 + bsp * bi + bsp * 0.5
                bg = _post_tube(bal_r, fh * 0.88, (base_x, -1200 - bi * 30), bx2, "fence")
                if bg is not None:
                    parts.append(bg)
                # spear cone tip
                sp = _safe_node(tree, 'GeometryNodeMeshCone', (base_x, -1280 - bi * 30))
                if sp:
                    sp.inputs['Radius Bottom'].default_value = bal_r * 2.0
                    sp.inputs['Radius Top'].default_value    = 0.0
                    sp.inputs['Depth'].default_value         = bal_r * 5.0
                    sp.inputs['Vertices'].default_value      = 8
                    color_node(sp, "ornament")
                    parts.append(_move(tree, sp.outputs['Mesh'],
                                       (base_x + 230, -1280 - bi * 30),
                                       translation=(bx2, 0, fh * 0.88 + bal_r * 2.5),
                                       label="ornament"))

        elif style == 'RANCH':
            post_r = 0.09
            # Thick square posts
            for pi in range(n_posts):
                x = -length / 2 + actual_spacing * pi
                p = _cube(tree, (base_x, pi * 80),
                          post_r * 2, post_r * 2, fh + 0.1, "fence")
                parts.append(_move(tree, p, (base_x + 230, pi * 80),
                                   translation=(x, 0, (fh + 0.1) * 0.5), label="fence"))
            # 3 horizontal rails (thick)
            for ri in range(n_rails):
                zr = fh * 0.15 + ri * (fh * 0.68 / max(1, n_rails - 1))
                parts.append(_rail_bar(0.09, 0.065, zr, (base_x, -400 - ri * 60), "fence"))

        elif style == 'STONE':
            # Dry-stone wall: thick rectangular base + coping cap
            wall_w = max(0.25, gap + 0.1)
            base_h = fh * 0.85
            # Wall body
            wb = _cube(tree, (base_x, 200), length, wall_w, base_h, "wall")
            parts.append(_move(tree, wb, (base_x + 230, 200),
                               translation=(0, 0, base_h * 0.5), label="wall"))
            # Coping (slightly wider, rounded-ish via cube)
            cp = _cube(tree, (base_x, -100), length + 0.1, wall_w + 0.06, 0.1, "ornament")
            parts.append(_move(tree, cp, (base_x + 230, -100),
                               translation=(0, 0, base_h + 0.05), label="ornament"))
            # Stone texture suggestion: a grid of instanced small boxes as individual stones
            stone_l = 0.35
            stone_rows = max(1, int(base_h / 0.18))
            stones_per_row = max(2, int(length / stone_l))
            for row in range(stone_rows):
                z_stone = row * (base_h / stone_rows) + base_h / (2 * stone_rows)
                offset_x = (row % 2) * (stone_l * 0.5)
                for si in range(stones_per_row):
                    xs = -length / 2 + stone_l * si + offset_x
                    s = _cube(tree, (base_x, -300 - row * 40 - si * 20),
                              stone_l * 0.95, wall_w * 1.02, base_h / stone_rows * 0.92, "wall")
                    parts.append(_move(tree, s, (base_x + 230, -300 - row * 40 - si * 20),
                                       translation=(xs, 0, z_stone), label="wall"))

        elif style == 'LATTICE':
            slat_r = 0.018
            frame_r = 0.04
            # Perimeter frame
            for (sx, sz, ex, ez) in [
                (-length/2, 0, length/2, 0),         # bottom
                (-length/2, fh, length/2, fh),        # top
                (-length/2, 0, -length/2, fh),        # left post
                (length/2, 0, length/2, fh),           # right post
            ]:
                ln = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (base_x, -700))
                if ln:
                    ln.inputs['Start'].default_value = (sx, 0, sz)
                    ln.inputs['End'].default_value   = (ex, 0, ez)
                    fp = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x, -800))
                    if fp:
                        fp.mode = 'RADIUS'; fp.inputs['Radius'].default_value = frame_r
                        fp.inputs['Resolution'].default_value = 8
                        fsw = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 200, -700))
                        if fsw:
                            _link(tree, ln.outputs['Curve'], fsw.inputs['Curve'])
                            _link(tree, fp.outputs['Curve'], fsw.inputs['Profile Curve'])
                            color_node(fsw, "fence"); parts.append(fsw.outputs['Mesh'])
            # Diagonal slats
            cell = fh * 0.28
            n_diags = max(3, int(length / cell))
            for di in range(-n_diags, n_diags + 1):
                for sgn in (-1, 1):
                    x0 = di * cell; x1 = x0 + sgn * fh
                    dln = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine',
                                      (base_x, -1000 - di * 20 - int(sgn * 10)))
                    if dln:
                        dln.inputs['Start'].default_value = (
                            max(-length/2, min(length/2, x0)), 0, 0 if sgn == 1 else fh)
                        dln.inputs['End'].default_value   = (
                            max(-length/2, min(length/2, x1)), 0, fh if sgn == 1 else 0)
                        dp = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle',
                                        (base_x, -1080 - di * 20))
                        if dp:
                            dp.mode = 'RADIUS'; dp.inputs['Radius'].default_value = slat_r
                            dp.inputs['Resolution'].default_value = 8
                            dsw = _safe_node(tree, 'GeometryNodeCurveToMesh',
                                              (base_x + 200, -1000 - di * 20))
                            if dsw:
                                _link(tree, dln.outputs['Curve'], dsw.inputs['Curve'])
                                _link(tree, dp.outputs['Curve'], dsw.inputs['Profile Curve'])
                                color_node(dsw, "fence"); parts.append(dsw.outputs['Mesh'])

        elif style == 'BAMBOO':
            pole_r = 0.04
            # Vertical bamboo poles (CurveLine+circle sweep)
            n_poles = max(3, int(length / (pole_r * 3 + gap)))
            ps = length / n_poles
            for pi in range(n_poles):
                px = -length / 2 + ps * pi + ps * 0.5
                bg = _post_tube(pole_r, fh + 0.06, (base_x, pi * 60), px, "fence")
                if bg is not None:
                    parts.append(bg)
                # Node rings (bamboo joints)
                n_nodes = max(2, int(fh / 0.35))
                for ni in range(n_nodes):
                    nz = ni * (fh / n_nodes) + 0.12
                    nr = _safe_node(tree, 'GeometryNodeMeshTorus',
                                     (base_x, -300 - pi * 40 - ni * 20))
                    if nr:
                        try:
                            nr.inputs['Major Radius'].default_value  = pole_r * 1.25
                            nr.inputs['Minor Radius'].default_value  = pole_r * 0.35
                            nr.inputs['Major Segments'].default_value = 16
                            nr.inputs['Minor Segments'].default_value = 6
                        except Exception:
                            pass
                        color_node(nr, "fence")
                        parts.append(_move(tree, nr.outputs['Mesh'],
                                           (base_x + 230, -300 - pi * 40 - ni * 20),
                                           translation=(px, 0, nz),
                                           rotation=(math.radians(90), 0, 0), label="fence"))
            # Horizontal lashing rails (swept round tubes)
            for ri in range(n_rails):
                zr = fh * 0.15 + ri * (fh * 0.6 / max(1, n_rails - 1))
                rl = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (base_x, -1800 - ri * 60))
                if rl:
                    rl.inputs['Start'].default_value = (-length / 2, 0, zr)
                    rl.inputs['End'].default_value   = ( length / 2, 0, zr)
                    rp = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle',
                                     (base_x, -1860 - ri * 60))
                    if rp:
                        rp.mode = 'RADIUS'
                        rp.inputs['Radius'].default_value     = 0.025
                        rp.inputs['Resolution'].default_value = 8
                        rsw = _safe_node(tree, 'GeometryNodeCurveToMesh',
                                          (base_x + 220, -1800 - ri * 60))
                        if rsw:
                            _link(tree, rl.outputs['Curve'], rsw.inputs['Curve'])
                            _link(tree, rp.outputs['Curve'], rsw.inputs['Profile Curve'])
                            color_node(rsw, "fence"); parts.append(rsw.outputs['Mesh'])

        else:  # MODERN - steel post + horizontal slat panels
            post_r = 0.04
            slat_h = fh / max(1, n_rails + 1)
            for pi in range(n_posts):
                x = -length / 2 + actual_spacing * pi
                g = _post_tube(post_r, fh + 0.04, (base_x, pi * 80), x, "fence")
                if g is not None:
                    parts.append(g)
            for ri in range(n_rails):
                zr = slat_h * (ri + 0.5)
                parts.append(_rail_bar(slat_h * 0.7, 0.03, zr, (base_x, -400 - ri * 60), "fence"))

        return _join_all(tree, parts, (base_x + 2500, 0), weld=0.0)


    # ----------------------------------------------------------------------
    # APPLY
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_fence")
    return tree, gin, gout

register_builder(
    "MEL_fence", build_fence_group,
    "Fence", "Misc prop (absorbed from monolith build_fence).",
    category="set_dressing")


def build_volume_cloud_group(group_name="MEL_volume_cloud"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0) if spec['default'] is not None else 0, int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t in ('StringProperty', 'EnumProperty'):
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    PROPS = _make_props()
    base_x = -1400
    def _impl():
        """
        Cloud palace: inflate base mesh through Mesh-to-Volume,
        threshold, then Volume-to-Mesh for a bubbly organic topology.
        """
        x = -200
        # Base icosphere
        ico = _node(tree, 'GeometryNodeMeshIcoSphere', (x, 0))
        ico.inputs['Radius'].default_value     = PROPS.base_radius
        ico.inputs['Subdivisions'].default_value = min(4, PROPS.complexity_level)
        color_node(ico, "organic")

        # Subdivide for detail
        subd = _node(tree, 'GeometryNodeSubdivisionSurface', (x+300, 0))
        subd.inputs['Level'].default_value = min(3, PROPS.recursion_depth - 1)
        _link(tree, ico.outputs['Mesh'], subd.inputs['Mesh'])

        # Noise displacement before volumization
        noise = _node(tree, 'ShaderNodeTexNoise', (x+300, -400))
        noise.inputs['Scale'].default_value    = 3.0 * PROPS.wave_frequency
        noise.inputs['Detail'].default_value   = 6.0
        noise.inputs['Roughness'].default_value= 0.65
        noise.inputs['Distortion'].default_value = PROPS.flow_amount

        set_pos_n = _node(tree, 'GeometryNodeSetPosition', (x+600, 0))
        _link(tree, subd.outputs['Mesh'], set_pos_n.inputs['Geometry'])
        # Build offset vector from noise
        sub_noise = _node(tree, 'ShaderNodeVectorMath', (x+550, -300))
        sub_noise.operation = 'MULTIPLY'
        sub_noise.inputs[1].default_value = (PROPS.bulge_amount, PROPS.bulge_amount, PROPS.bulge_amount * 1.4)
        _link(tree, noise.outputs['Color'], sub_noise.inputs[0])
        _link(tree, sub_noise.outputs['Vector'], set_pos_n.inputs['Offset'])
        color_node(set_pos_n, "deform")

        # Mesh to Volume
        m2v = _node(tree, 'GeometryNodeMeshToVolume', (x+900, 0))
        try: m2v.resolution_mode = 'VOXEL_SIZE'
        except (AttributeError, TypeError): pass
        m2v.inputs['Voxel Size'].default_value   = 0.15 / max(0.5, PROPS.complexity_level * 0.5)
        m2v.inputs['Density'].default_value      = 1.0
        # `Exterior Band Width` was removed in newer Blender - try both names
        for w_name, w_val in (('Interior Band Width', PROPS.base_radius * 0.35),
                              ('Exterior Band Width', PROPS.bulge_amount * 0.4 + 0.1)):
            try:
                m2v.inputs[w_name].default_value = w_val
            except (KeyError, AttributeError):
                pass
        _link(tree, set_pos_n.outputs['Geometry'], m2v.inputs['Mesh'])
        color_node(m2v, "organic")

        # Volume to Mesh
        v2m = _node(tree, 'GeometryNodeVolumeToMesh', (x+1200, 0))
        try: v2m.resolution_mode = 'VOXEL_SIZE'
        except (AttributeError, TypeError): pass
        v2m.inputs['Voxel Size'].default_value = 0.12 / max(0.5, PROPS.complexity_level * 0.5)
        v2m.inputs['Threshold'].default_value  = 0.1 + PROPS.variation_intensity * 0.3
        v2m.inputs['Adaptivity'].default_value = 0.02
        _link(tree, m2v.outputs['Volume'], v2m.inputs['Volume'])
        color_node(v2m, "organic")

        # Add floating crystal shards via distributed points
        pts2 = _node(tree, 'GeometryNodeDistributePointsOnFaces', (x+1500, -400))
        pts2.distribute_method = 'POISSON'
        pts2.inputs['Distance Min'].default_value = 0.25
        pts2.inputs['Density Max'].default_value  = PROPS.complexity_level * 0.3
        pts2.inputs['Seed'].default_value         = PROPS.seed + 77
        _link(tree, v2m.outputs['Mesh'], pts2.inputs['Mesh'])

        ico2 = _node(tree, 'GeometryNodeMeshIcoSphere', (x+1500, -700))
        ico2.inputs['Radius'].default_value       = 0.08
        ico2.inputs['Subdivisions'].default_value  = 3

        inst2 = _node(tree, 'GeometryNodeInstanceOnPoints', (x+1800, -400))
        _link(tree, pts2.outputs['Points'],        inst2.inputs['Points'])
        _link(tree, ico2.outputs['Mesh'],          inst2.inputs['Instance'])
        real2 = _node(tree, 'GeometryNodeRealizeInstances', (x+2100, -400))
        _link(tree, inst2.outputs['Instances'],    real2.inputs['Geometry'])

        join2 = _node(tree, 'GeometryNodeJoinGeometry', (x+2400, 0))
        _link(tree, v2m.outputs['Mesh'],       join2.inputs['Geometry'])
        _link(tree, real2.outputs['Geometry'], join2.inputs['Geometry'])
        color_node(join2, "output")

        return join2.outputs['Geometry']


    # ──────────────────────────────────────────────────────────────────────
    # ADVANCED BUILDER: GEODESIC VORONOI DOME
    # Uses Edge Angle node for structural analysis, Named Attribute for
    # per-edge thickness, Distribute Points on Faces for rivet decoration.
    # ──────────────────────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_volume_cloud")
    return tree, gin, gout

register_builder(
    "MEL_volume_cloud", build_volume_cloud_group,
    "Volume Cloud", "Misc prop (absorbed from monolith build_volume_cloud).",
    category="set_dressing")


# 17 builders registered
