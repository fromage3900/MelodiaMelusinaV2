"""MEL Zen builders — absorbed from the monolith (P2 family 3).

7 generator builders. Params-as-values port: each builder reads its
props via getattr(...) defaults -> P dict pre-filled from the monolith's
bpy.props defaults. Group sockets expose the same params for UI/dispatch.
Regenerable.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, add_string_param,
    register_builder,
)

SLUGS = {
    "build_zen_pagoda": "zen_pagoda",
    "build_zen_torii": "zen_torii",
    "build_zen_shoji": "zen_shoji",
    "build_zen_lantern": "zen_lantern",
    "build_zen_teahouse": "zen_teahouse",
    "build_zen_bridge": "zen_bridge",
    "build_zen_stone_garden": "zen_stone_garden",
}


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



def _crenel_top(tree, length, width, height, n_merlons, gap_ratio,
                 loc=(-700, -1700), label="ornament"):
    """Build a crenellated cap (merlons + gaps) along Y axis as a single mesh.
    Returns the mesh socket; caller translates it into place."""
    pieces = []
    if n_merlons < 2:
        n_merlons = 2
    full_span = length
    period = full_span / n_merlons
    merlon_w = period * (1.0 - gap_ratio)
    for i in range(n_merlons):
        m = _node(tree, 'GeometryNodeMeshCube', (loc[0], loc[1] - i * 80))
        m.inputs['Size'].default_value = (merlon_w, width, height)
        x = -full_span / 2 + period * i + period / 2
        t = _move(tree, m.outputs['Mesh'],
                  (loc[0] + 220, loc[1] - i * 80),
                  translation=(x, 0, height / 2),
                  label=label)
        color_node(m, label)
        pieces.append(t)
    return _join_all(tree, pieces, (loc[0] + 480, loc[1]), label=label)



def _finalize_building(tree, pieces, loc=(0, 0), label="output"):
    """Heavier weld for monolithic buildings - fuses touching tops/finials
    to their bodies (weld=0.3). Use as the last step of a building builder."""
    return _join_all(tree, pieces, loc=loc, label=label, weld=0.3)



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



def _make_circle_profile(tree, radius, resolution=8, loc=(-400, -600), P=None):
    """Build the user-selected sweep profile and return a stub object whose
    `.outputs['Curve']` is the profile curve socket.

    Backwards-compatible wrapper: callers that pass no `P` get a circle.
    With `P`, picks from `P.aest_profile`."""
    order = ["CIRCLE", "SQUARE", "FLUTE"]
    kind = order[P.get("profile", 0)] if isinstance(P, dict) else "CIRCLE"

    class _ProfileStub:
        def __init__(self, sock):
            self.outputs = {'Curve': sock}

    # CIRCLE - default round tube
    if kind == 'CIRCLE':
        prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', loc)
        if prof is None:
            return None
        try:
            prof.inputs['Resolution'].default_value = resolution
            prof.inputs['Radius'].default_value     = radius
        except Exception:
            return None
        color_node(prof, "input")
        return prof

    # SQUARE - quadrilateral via 4-resolution circle (gives a diamond,
    # but a Curve Line ring of 4 points is closer)
    if kind == 'SQUARE':
        # Build a quad as a small bezier closed curve via Curve Line w/4 segments
        # Easiest: a circle with 4 verts (rotated 45deg gives diamond - fine).
        prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', loc)
        if prof is None:
            return None
        try:
            prof.inputs['Resolution'].default_value = 4
            prof.inputs['Radius'].default_value     = radius * 1.2
        except Exception:
            return None
        color_node(prof, "input")
        return prof

    # FLUTE - multi-lobed circle: build by Set Position on a high-res circle
    # using radial sin to perturb the radius
    if kind == 'FLUTE':
        base = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', loc)
        if base is None:
            return None
        try:
            base.inputs['Resolution'].default_value = 48
            base.inputs['Radius'].default_value     = radius
        except Exception:
            return None
        # Per-point radial perturbation: sin(angle * 8) * radius * 0.25
        pos = _node(tree, 'GeometryNodeInputPosition', (loc[0] - 200, loc[1] - 200))
        sep = _node(tree, 'ShaderNodeSeparateXYZ', (loc[0] - 50, loc[1] - 200))
        _link(tree, pos.outputs['Position'], sep.inputs['Vector'])
        atan = _node(tree, 'ShaderNodeMath', (loc[0] + 100, loc[1] - 200))
        atan.operation = 'ARCTAN2'
        _link(tree, sep.outputs['Y'], atan.inputs[0])
        _link(tree, sep.outputs['X'], atan.inputs[1])
        mul = _node(tree, 'ShaderNodeMath', (loc[0] + 250, loc[1] - 200))
        mul.operation = 'MULTIPLY'
        _link(tree, atan.outputs['Value'], mul.inputs[0])
        mul.inputs[1].default_value = 8.0   # 8 flutes
        sn = _node(tree, 'ShaderNodeMath', (loc[0] + 400, loc[1] - 200))
        sn.operation = 'SINE'
        _link(tree, mul.outputs['Value'], sn.inputs[0])
        amp = _node(tree, 'ShaderNodeMath', (loc[0] + 550, loc[1] - 200))
        amp.operation = 'MULTIPLY'
        _link(tree, sn.outputs['Value'], amp.inputs[0])
        amp.inputs[1].default_value = radius * 0.3
        # Push verts outward along their own direction (just X,Y scaled)
        scale_n = _node(tree, 'ShaderNodeVectorMath', (loc[0] + 700, loc[1] - 100))
        scale_n.operation = 'SCALE'
        _link(tree, pos.outputs['Position'], scale_n.inputs[0])
        # normalize-ish: we'll use the position itself; small offset is fine
        norm_div = _node(tree, 'ShaderNodeMath', (loc[0] + 550, loc[1] - 300))
        norm_div.operation = 'DIVIDE'
        _link(tree, amp.outputs['Value'], norm_div.inputs[0])
        norm_div.inputs[1].default_value = max(0.001, radius)
        _link(tree, norm_div.outputs['Value'], scale_n.inputs['Scale'])
        sp = _safe_node(tree, 'GeometryNodeSetPosition', (loc[0] + 900, loc[1]))
        if sp:
            _link(tree, base.outputs['Curve'], sp.inputs['Geometry'])
            _link(tree, scale_n.outputs['Vector'], sp.inputs['Offset'])
            color_node(base, "input"); color_node(sp, "input")
            return _ProfileStub(sp.outputs['Geometry'])
        return base

    # OGEE - S-curve: two quadratic beziers stitched. Approximate with
    # a thin tall oval (circle scaled along Y) for now.
    if kind == 'OGEE':
        prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', loc)
        if prof is None:
            return None
        try:
            prof.inputs['Resolution'].default_value = 16
            prof.inputs['Radius'].default_value     = radius
        except Exception:
            return None
        # Scale the circle into an oval via Transform
        tr = _node(tree, 'GeometryNodeTransform', (loc[0] + 250, loc[1]))
        tr.inputs['Scale'].default_value = (0.5, 1.4, 1.0)
        _link(tree, prof.outputs['Curve'], tr.inputs['Geometry'])
        color_node(prof, "input"); color_node(tr, "input")
        return _ProfileStub(tr.outputs['Geometry'])

    # LOTUS - pointed-petal cross-section (5-pointed)
    if kind == 'LOTUS':
        base = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', loc)
        if base is None:
            return None
        try:
            base.inputs['Resolution'].default_value = 60
            base.inputs['Radius'].default_value     = radius
        except Exception:
            return None
        pos = _node(tree, 'GeometryNodeInputPosition', (loc[0] - 200, loc[1] - 200))
        sep = _node(tree, 'ShaderNodeSeparateXYZ', (loc[0] - 50, loc[1] - 200))
        _link(tree, pos.outputs['Position'], sep.inputs['Vector'])
        atan = _node(tree, 'ShaderNodeMath', (loc[0] + 100, loc[1] - 200))
        atan.operation = 'ARCTAN2'
        _link(tree, sep.outputs['Y'], atan.inputs[0])
        _link(tree, sep.outputs['X'], atan.inputs[1])
        mul = _node(tree, 'ShaderNodeMath', (loc[0] + 250, loc[1] - 200))
        mul.operation = 'MULTIPLY'
        _link(tree, atan.outputs['Value'], mul.inputs[0])
        mul.inputs[1].default_value = 5.0   # 5 petals
        sn = _node(tree, 'ShaderNodeMath', (loc[0] + 400, loc[1] - 200))
        sn.operation = 'COSINE'
        _link(tree, mul.outputs['Value'], sn.inputs[0])
        abs_n = _node(tree, 'ShaderNodeMath', (loc[0] + 550, loc[1] - 200))
        abs_n.operation = 'ABSOLUTE'
        _link(tree, sn.outputs['Value'], abs_n.inputs[0])
        amp = _node(tree, 'ShaderNodeMath', (loc[0] + 700, loc[1] - 200))
        amp.operation = 'MULTIPLY'
        _link(tree, abs_n.outputs['Value'], amp.inputs[0])
        amp.inputs[1].default_value = radius * 0.6
        scale_n = _node(tree, 'ShaderNodeVectorMath', (loc[0] + 700, loc[1] - 50))
        scale_n.operation = 'SCALE'
        _link(tree, pos.outputs['Position'], scale_n.inputs[0])
        norm_div = _node(tree, 'ShaderNodeMath', (loc[0] + 550, loc[1] - 350))
        norm_div.operation = 'DIVIDE'
        _link(tree, amp.outputs['Value'], norm_div.inputs[0])
        norm_div.inputs[1].default_value = max(0.001, radius)
        _link(tree, norm_div.outputs['Value'], scale_n.inputs['Scale'])
        sp = _safe_node(tree, 'GeometryNodeSetPosition', (loc[0] + 900, loc[1]))
        if sp:
            _link(tree, base.outputs['Curve'], sp.inputs['Geometry'])
            _link(tree, scale_n.outputs['Vector'], sp.inputs['Offset'])
            color_node(base, "input"); color_node(sp, "input")
            return _ProfileStub(sp.outputs['Geometry'])
        return base

    # Fallback: circle
    prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', loc)
    if prof is None:
        return None
    try:
        prof.inputs['Resolution'].default_value = resolution
        prof.inputs['Radius'].default_value     = radius
    except Exception:
        return None
    color_node(prof, "input")
    return prof




def _defaults_for(names):
    P = {}
    for nm in names:
        d = BUILDER_PARAM_DEFAULTS.get(nm, {})
        P[nm] = d.get("default", 0.0)
    return P

BUILDER_PARAM_DEFAULTS = {
    "pagoda_base_radius": {"type": "FloatProperty", "default": 1.2, "min": 0.3, "max": 8.0},
    "pagoda_roof_overhang": {"type": "FloatProperty", "default": 0.45, "min": 0.1, "max": 1.5},
    "pagoda_show_mokoshi": {"type": "BoolProperty", "default": False, "min": None, "max": None},
    "pagoda_show_shinbashira": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "pagoda_sorin_rings": {"type": "IntProperty", "default": 9, "min": 0, "max": 13},
    "pagoda_taper": {"type": "FloatProperty", "default": 0.85, "min": 0.5, "max": 0.99},
    "pagoda_tier_height": {"type": "FloatProperty", "default": 1.0, "min": 0.4, "max": 3.0},
    "pagoda_tiers": {"type": "IntProperty", "default": 3, "min": 2, "max": 7},
    "shoji_frame_depth": {"type": "FloatProperty", "default": 0.06, "min": 0.02, "max": 0.2},
    "shoji_grid_x": {"type": "IntProperty", "default": 4, "min": 1, "max": 12},
    "shoji_grid_y": {"type": "IntProperty", "default": 5, "min": 1, "max": 12},
    "shoji_height": {"type": "FloatProperty", "default": 2.4, "min": 0.6, "max": 6.0},
    "shoji_kumiko": {"type": "EnumProperty", "default": 'GRID', "min": None, "max": None},
    "shoji_mullion": {"type": "FloatProperty", "default": 0.035, "min": 0.005, "max": 0.15},
    "shoji_width": {"type": "FloatProperty", "default": 2.0, "min": 0.5, "max": 6.0},
    "stone_garden_ripples": {"type": "IntProperty", "default": 8, "min": 0, "max": 24},
    "stone_garden_sansonseki": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "stone_garden_size": {"type": "FloatProperty", "default": 3.0, "min": 1.0, "max": 10.0},
    "stone_garden_stones": {"type": "IntProperty", "default": 5, "min": 1, "max": 20},
    "stone_garden_tsukubai": {"type": "BoolProperty", "default": False, "min": None, "max": None},
    "sv_seed": {"type": "IntProperty", "default": 42, "min": 0, "max": 99999},
    "teahouse_chumon": {"type": "BoolProperty", "default": False, "min": None, "max": None},
    "teahouse_depth": {"type": "FloatProperty", "default": 3.0, "min": 1.5, "max": 8.0},
    "teahouse_engawa": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "teahouse_engawa_width": {"type": "FloatProperty", "default": 0.6, "min": 0.2, "max": 2.0},
    "teahouse_height": {"type": "FloatProperty", "default": 2.5, "min": 1.5, "max": 6.0},
    "teahouse_nijiriguchi": {"type": "BoolProperty", "default": False, "min": None, "max": None},
    "teahouse_pitch_factor": {"type": "FloatProperty", "default": 0.6, "min": 0.2, "max": 1.5},
    "teahouse_ro": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "teahouse_tokonoma": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "teahouse_width": {"type": "FloatProperty", "default": 3.0, "min": 1.5, "max": 8.0},
    "torii_height": {"type": "FloatProperty", "default": 3.5, "min": 1.0, "max": 10.0},
    "torii_nuki_height": {"type": "FloatProperty", "default": 0.70, "min": 0.45, "max": 0.85},
    "torii_post_radius": {"type": "FloatProperty", "default": 0.18, "min": 0.05, "max": 0.6},
    "torii_show_gakuzuka": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "torii_show_kusabi": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "torii_show_shimenawa": {"type": "BoolProperty", "default": False, "min": None, "max": None},
    "torii_style": {"type": "EnumProperty", "default": 'MYOJIN', "min": None, "max": None},
    "torii_top_curve": {"type": "FloatProperty", "default": 0.25, "min": 0.0, "max": 1.0},
    "torii_width": {"type": "FloatProperty", "default": 3.0, "min": 1.0, "max": 8.0},
    "zen_bridge_giboshi": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "zen_bridge_planks": {"type": "IntProperty", "default": 20, "min": 6, "max": 80},
    "zen_bridge_railings": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "zen_bridge_rise": {"type": "FloatProperty", "default": 0.8, "min": 0.1, "max": 3.0},
    "zen_bridge_span": {"type": "FloatProperty", "default": 4.0, "min": 1.5, "max": 12.0},
    "zen_bridge_style": {"type": "EnumProperty", "default": 'TAIKOBASHI', "min": None, "max": None},
    "zen_bridge_width": {"type": "FloatProperty", "default": 1.2, "min": 0.4, "max": 4.0},
    "zen_lantern_height": {"type": "FloatProperty", "default": 1.6, "min": 0.4, "max": 4.0},
    "zen_lantern_higuchi": {"type": "EnumProperty", "default": 'ROUND', "min": None, "max": None},
    "zen_lantern_hoju_scale": {"type": "FloatProperty", "default": 1.0, "min": 0.3, "max": 2.5},
    "zen_lantern_kasa_overhang": {"type": "FloatProperty", "default": 1.0, "min": 0.6, "max": 1.8},
    "zen_lantern_layers": {"type": "IntProperty", "default": 6, "min": 2, "max": 8},
    "zen_lantern_radius": {"type": "FloatProperty", "default": 0.4, "min": 0.1, "max": 1.5},
    "zen_lantern_show_kidan": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "zen_lantern_show_ukebana": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "zen_lantern_style": {"type": "EnumProperty", "default": 'KASUGA', "min": None, "max": None},
    "zen_lantern_warabide": {"type": "FloatProperty", "default": 0.35, "min": 0.0, "max": 1.0},
}


def _zen_lantern_element_mask(layers, show_kidan, show_ukebana):
    """Return active element keys bottom->top for a tōrō stack."""
    full = ['kidan', 'kiso', 'sao', 'chudai', 'hibukuro', 'kasa', 'ukebana', 'hoju']
    if not show_kidan and 'kidan' in full:
        full.remove('kidan')
    if not show_ukebana and 'ukebana' in full:
        full.remove('ukebana')
    n = max(2, min(8, layers))
    if n >= len(full):
        return full
    # Keep bottom (foundation) + top (finial); trim middle if needed
    if n <= 3:
        return full[:max(1, n - 1)] + ['hoju']
    return full[:n]



def build_zen_pagoda_group(group_name="MEL_zen_pagoda"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        """Multi-tier pagoda following Japanese pagoda principles:
           * Each tier ~85% of the previous (yon-juu = 4-tier rule)
           * Overhanging eaves on each tier (deep noki)
           * Curved Bezier roof beams for kibana (corner upturn)
           * Crowning sōrin (ringed spire) of 9 rings.
        """
        tiers = PROPS.pagoda_tiers
        R = PROPS.pagoda_base_radius
        th = PROPS.pagoda_tier_height
        overhang = PROPS.pagoda_roof_overhang
        taper = PROPS.pagoda_taper
        kurin_n = max(0, min(13, getattr(PROPS, 'pagoda_sorin_rings', 9)))
        show_mokoshi = getattr(PROPS, 'pagoda_show_mokoshi', False)
        show_shinbashira = getattr(PROPS, 'pagoda_show_shinbashira', True)
        parts = []
        cur_R = R
        cur_z = 0

        # Mokoshi (裳階) - decorative skirt story at pagoda base
        if show_mokoshi:
            mok_r = R * 1.35
            mok_circ = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x - 200, -200))
            if mok_circ:
                try:
                    mok_circ.inputs['Resolution'].default_value = 8
                    mok_circ.inputs['Radius'].default_value = mok_r
                except Exception:
                    pass
                mok_fill = _safe_node(tree, 'GeometryNodeFillCurve', (base_x, -200))
                if mok_fill and mok_circ:
                    try:
                        mok_fill.mode = 'NGONS'
                    except Exception:
                        pass
                    _link(tree, mok_circ.outputs['Curve'], mok_fill.inputs['Curve'])
                    mok_ext = _safe_node(tree, 'GeometryNodeExtrudeMesh', (base_x + 200, -200))
                    if mok_ext:
                        mok_ext.mode = 'FACES'
                        try:
                            mok_ext.inputs['Offset Scale'].default_value = th * 0.22
                        except Exception:
                            pass
                        _link(tree, mok_fill.outputs['Mesh'], mok_ext.inputs['Mesh'])
                        color_node(mok_ext, "roof")
                        parts.append(mok_ext.outputs['Mesh'])

        for i in range(tiers):
            # ── Body: octagonal column via CurvePrimitiveCircle(8) + FillCurve + ExtrudeMesh ──
            body_h = th * 0.72
            body_circ = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x, i * 400))
            if body_circ:
                try:
                    body_circ.inputs['Resolution'].default_value = 8    # octagonal plan
                    body_circ.inputs['Radius'].default_value     = cur_R * 0.90
                except Exception: pass
                color_node(body_circ, "house")
            body_fill = _safe_node(tree, 'GeometryNodeFillCurve', (base_x + 200, i * 400))
            if body_fill and body_circ:
                try: body_fill.mode = 'NGONS'
                except Exception: pass
                _link(tree, body_circ.outputs['Curve'], body_fill.inputs['Curve'])
            body_ext = _safe_node(tree, 'GeometryNodeExtrudeMesh', (base_x + 400, i * 400))
            if body_ext and body_fill:
                body_ext.mode = 'FACES'
                try: body_ext.inputs['Offset Scale'].default_value = body_h
                except Exception: pass
                _link(tree, body_fill.outputs['Mesh'], body_ext.inputs['Mesh'])
            body_tr = _safe_node(tree, 'GeometryNodeTransform', (base_x + 600, i * 400))
            if body_tr:
                try: body_tr.inputs['Translation'].default_value = (0, 0, cur_z)
                except Exception: pass
                if body_ext: _link(tree, body_ext.outputs['Mesh'], body_tr.inputs['Geometry'])
                color_node(body_tr, "house")
                parts.append(body_tr.outputs['Geometry'])

            # ── Roof: octagonal eave disc (FillCurve + ExtrudeMesh thin) ──────
            roof_h  = th * 0.40
            eave_r  = cur_R + overhang
            eave_z  = cur_z + body_h
            eave_circ = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle',
                                   (base_x, i * 400 + 100))
            if eave_circ:
                try:
                    eave_circ.inputs['Resolution'].default_value = 8
                    eave_circ.inputs['Radius'].default_value     = eave_r
                except Exception: pass
                color_node(eave_circ, "roof")
            eave_fill = _safe_node(tree, 'GeometryNodeFillCurve', (base_x + 200, i * 400 + 100))
            if eave_fill and eave_circ:
                try: eave_fill.mode = 'NGONS'
                except Exception: pass
                _link(tree, eave_circ.outputs['Curve'], eave_fill.inputs['Curve'])
            eave_ext = _safe_node(tree, 'GeometryNodeExtrudeMesh', (base_x + 400, i * 400 + 100))
            if eave_ext and eave_fill:
                eave_ext.mode = 'FACES'
                try: eave_ext.inputs['Offset Scale'].default_value = 0.06
                except Exception: pass
                _link(tree, eave_fill.outputs['Mesh'], eave_ext.inputs['Mesh'])
            eave_tr = _safe_node(tree, 'GeometryNodeTransform', (base_x + 600, i * 400 + 100))
            if eave_tr:
                try:
                    eave_tr.inputs['Translation'].default_value = (0, 0, eave_z - 0.03)
                    eave_tr.inputs['Rotation'].default_value    = (0, 0, math.radians(22.5))
                except Exception: pass
                if eave_ext: _link(tree, eave_ext.outputs['Mesh'], eave_tr.inputs['Geometry'])
                color_node(eave_tr, "roof")
                parts.append(eave_tr.outputs['Geometry'])

            # Eave rim torus (adds a rounded edge to the eave disc)
            eave_rim = _safe_node(tree, 'GeometryNodeMeshTorus', (base_x, i * 400 + 200))
            if eave_rim:
                try:
                    eave_rim.inputs['Major Radius'].default_value   = eave_r * 0.95
                    eave_rim.inputs['Minor Radius'].default_value   = 0.055
                    eave_rim.inputs['Major Segments'].default_value = 48
                    eave_rim.inputs['Minor Segments'].default_value = 6
                except Exception: pass
                eave_rim_tr = _safe_node(tree, 'GeometryNodeTransform',
                                         (base_x + 200, i * 400 + 200))
                if eave_rim_tr:
                    try: eave_rim_tr.inputs['Translation'].default_value = (0, 0, eave_z)
                    except Exception: pass
                    _link(tree, eave_rim.outputs['Mesh'], eave_rim_tr.inputs['Geometry'])
                    color_node(eave_rim, "roof"); color_node(eave_rim_tr, "roof")
                    parts.append(eave_rim_tr.outputs['Geometry'])

            # ── 8 curved corner kibana beams - bezier swept with thin tube ──────
            # Start at octagonal body edge, curve outward+upward to eave tip (upturn)
            body_edge_r = cur_R * 0.90   # match the octagonal body radius
            beam_prof_pag = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle',
                                       (base_x - 250, i * 400 + 300))
            if beam_prof_pag:
                try:
                    beam_prof_pag.inputs['Resolution'].default_value = 6
                    beam_prof_pag.inputs['Radius'].default_value     = 0.035
                except Exception: pass

            for corner in range(8):
                ang = corner * math.pi / 4.0 + math.pi / 8.0
                cos_a = math.cos(ang)
                sin_a = math.sin(ang)
                x0 = cos_a * body_edge_r
                y0 = sin_a * body_edge_r
                x1 = cos_a * (eave_r * 1.05)
                y1 = sin_a * (eave_r * 1.05)
                kib = _safe_node(tree, 'GeometryNodeCurvePrimitiveBezierSegment',
                                 (base_x + corner * 80, i * 400 + 300))
                if kib:
                    try:
                        kib.inputs['Resolution'].default_value    = 12
                        kib.inputs['Start'].default_value         = (x0, y0, eave_z - 0.02)
                        kib.inputs['Start Handle'].default_value  = ((x0 + x1) * 0.55,
                                                                      (y0 + y1) * 0.55,
                                                                      eave_z + 0.05)
                        kib.inputs['End Handle'].default_value    = (x1 * 1.03, y1 * 1.03,
                                                                      eave_z + 0.12)
                        kib.inputs['End'].default_value           = (x1 * 1.08, y1 * 1.08,
                                                                      eave_z + 0.28)
                    except Exception: pass
                    color_node(kib, "ornament")
                    if beam_prof_pag:
                        kib_sw = _safe_node(tree, 'GeometryNodeCurveToMesh',
                                            (base_x + corner * 80, i * 400 + 350))
                        if kib_sw:
                            _link(tree, kib.outputs['Curve'], kib_sw.inputs['Curve'])
                            _link(tree, beam_prof_pag.outputs['Curve'], kib_sw.inputs['Profile Curve'])
                            try: kib_sw.inputs['Fill Caps'].default_value = True
                            except Exception: pass
                            color_node(kib_sw, "ornament")
                            parts.append(kib_sw.outputs['Mesh'])

            cur_z += th
            cur_R *= taper

        # Shinbashira (心柱) - central heart column through all tiers
        if show_shinbashira:
            col_h = cur_z * 0.92
            shin_line = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (base_x - 400, tiers * 400 + 50))
            if shin_line:
                try:
                    shin_line.inputs['Start'].default_value = (0, 0, 0.05)
                    shin_line.inputs['End'].default_value = (0, 0, col_h)
                except Exception:
                    pass
                shin_prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x - 650, tiers * 400 + 50))
                if shin_prof:
                    try:
                        shin_prof.inputs['Resolution'].default_value = 10
                        shin_prof.inputs['Radius'].default_value = R * 0.08
                    except Exception:
                        pass
                    shin_sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x - 150, tiers * 400 + 50))
                    if shin_sw:
                        _link(tree, shin_line.outputs['Curve'], shin_sw.inputs['Curve'])
                        _link(tree, shin_prof.outputs['Curve'], shin_sw.inputs['Profile Curve'])
                        try:
                            shin_sw.inputs['Fill Caps'].default_value = True
                        except Exception:
                            pass
                        color_node(shin_sw, "house")
                        _g = shin_sw.outputs.get('Mesh') or shin_sw.outputs.get('Geometry')
                        if _g:
                            parts.append(_g)

        # ── Sōrin (crowning spire) - thin swept rod + kurin rings ─────
        spire_h = th * 1.25
        spire_line = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine',
                                (base_x, tiers * 400 + 100))
        if spire_line:
            try:
                spire_line.inputs['Start'].default_value = (0, 0, cur_z)
                spire_line.inputs['End'].default_value   = (0, 0, cur_z + spire_h)
            except Exception: pass
            spire_prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle',
                                    (base_x - 250, tiers * 400 + 100))
            if spire_prof:
                try:
                    spire_prof.inputs['Resolution'].default_value = 10
                    spire_prof.inputs['Radius'].default_value     = 0.055
                except Exception: pass
                spire_sw = _safe_node(tree, 'GeometryNodeCurveToMesh',
                                      (base_x + 250, tiers * 400 + 100))
                if spire_sw:
                    _link(tree, spire_line.outputs['Curve'], spire_sw.inputs['Curve'])
                    _link(tree, spire_prof.outputs['Curve'], spire_sw.inputs['Profile Curve'])
                    try: spire_sw.inputs['Fill Caps'].default_value = True
                    except Exception: pass
                    color_node(spire_sw, "ornament")
                    parts.append(spire_sw.outputs['Mesh'])

        # Kurin (九輪) rings + fukubachi dome + hōju jewel on sōrin spire
        fukubachi = _safe_node(tree, 'GeometryNodeMeshUVSphere', (base_x, tiers * 400 + 80))
        if fukubachi:
            try:
                fukubachi.inputs['Radius'].default_value = 0.14
            except Exception:
                pass
            fb_tr = _safe_node(tree, 'GeometryNodeTransform', (base_x + 200, tiers * 400 + 80))
            if fb_tr:
                try:
                    fb_tr.inputs['Translation'].default_value = (0, 0, cur_z + 0.05)
                    fb_tr.inputs['Scale'].default_value = (1.0, 1.0, 0.45)
                except Exception:
                    pass
                _link(tree, fukubachi.outputs['Mesh'], fb_tr.inputs['Geometry'])
                color_node(fb_tr, "ornament")
                parts.append(fb_tr.outputs['Geometry'])

        for r in range(kurin_n):
            k_ring = _safe_node(tree, 'GeometryNodeMeshTorus',
                                (base_x, tiers * 400 + 200 + r * 60))
            if k_ring:
                try:
                    k_ring.inputs['Major Radius'].default_value   = 0.12 - r * 0.008
                    k_ring.inputs['Minor Radius'].default_value   = 0.022 - r * 0.001
                    k_ring.inputs['Major Segments'].default_value = 24
                    k_ring.inputs['Minor Segments'].default_value = 6
                except Exception: pass
                k_tr = _safe_node(tree, 'GeometryNodeTransform',
                                  (base_x + 200, tiers * 400 + 200 + r * 60))
                if k_tr:
                    try: k_tr.inputs['Translation'].default_value = (
                        0, 0, cur_z + 0.22 + r * (spire_h * 0.085 / max(1, kurin_n)))
                    except Exception: pass
                    _link(tree, k_ring.outputs['Mesh'], k_tr.inputs['Geometry'])
                    color_node(k_ring, "ornament"); color_node(k_tr, "ornament")
                    parts.append(k_tr.outputs['Geometry'])

        # Hōju (宝珠) - wish-granting jewel at sōrin apex
        hoju = _safe_node(tree, 'GeometryNodeMeshUVSphere', (base_x, tiers * 400 + 800))
        if hoju:
            try:
                hoju.inputs['Radius'].default_value = 0.08
            except Exception:
                pass
            hj_tr = _safe_node(tree, 'GeometryNodeTransform', (base_x + 200, tiers * 400 + 800))
            if hj_tr:
                try:
                    hj_tr.inputs['Translation'].default_value = (0, 0, cur_z + spire_h + 0.12)
                except Exception:
                    pass
                _link(tree, hoju.outputs['Mesh'], hj_tr.inputs['Geometry'])
                color_node(hj_tr, "ornament")
                parts.append(hj_tr.outputs['Geometry'])

        join = _safe_node(tree, 'GeometryNodeJoinGeometry', (base_x + 800, 0))
        if join:
            for p in parts: _link(tree, p, join.inputs['Geometry'])
            color_node(join, "output")
            return join.outputs['Geometry']
        return parts[0] if parts else None


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_zen_pagoda")
    return tree, gin, gout

register_builder(
    "MEL_zen_pagoda", build_zen_pagoda_group,
    "Zen Pagoda", "Zen builder (absorbed from monolith build_zen_pagoda).",
    category="zen_kit")


def build_zen_torii_group(group_name="MEL_zen_torii"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        """Japanese Myōjin torii gate - v2.49 AAA overhaul.

        All beams are swept curve profiles; posts are fluted sweep tubes.
        * 2 vertical posts: CurvePrimitiveLine + round/fluted profile sweep
        * Nuki (tie beam): horizontal CurvePrimitiveLine + rect-oval profile sweep
        * Shimaki (straight upper beam): horizontal sweep, wider and taller than nuki
        * Kasagi (curved top beam): BezierSegment + round profile sweep (already AAA)
        * Gakuzuka (center vertical brace): line sweep
        * Post caps (kibashira cap rings): small torus at top of each post
        """
        W     = PROPS.torii_width
        H     = PROPS.torii_height
        pr    = PROPS.torii_post_radius
        curve = PROPS.torii_top_curve
        style = getattr(PROPS, 'torii_style', 'MYOJIN')
        nuki_frac = getattr(PROPS, 'torii_nuki_height', 0.70)
        show_gz = getattr(PROPS, 'torii_show_gakuzuka', True)
        show_kusabi = getattr(PROPS, 'torii_show_kusabi', True)
        show_shimenawa = getattr(PROPS, 'torii_show_shimenawa', False)
        is_shinmei = style in ('SHINMEI', 'ISE')
        parts = []

        # ── Shared post profile (round, 16-vert) ────────────────────────────
        post_prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x - 300, 0))
        if post_prof:
            try:
                post_prof.inputs['Resolution'].default_value = 16
                post_prof.inputs['Radius'].default_value     = pr
            except Exception: pass
            color_node(post_prof, "house")

        # ── 2 vertical posts - CurvePrimitiveLine swept with post_prof ───────
        for i, x_off in enumerate((-W / 2, W / 2)):
            post_line = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (base_x, i * 200))
            if post_line:
                try:
                    post_line.inputs['Start'].default_value = (x_off, 0, 0)
                    post_line.inputs['End'].default_value   = (x_off, 0, H * 1.04)  # slight overshoot
                except Exception: pass
                color_node(post_line, "house")
                if post_prof:
                    sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 250, i * 200))
                    if sw:
                        _link(tree, post_line.outputs['Curve'], sw.inputs['Curve'])
                        _link(tree, post_prof.outputs['Curve'], sw.inputs['Profile Curve'])
                        try: sw.inputs['Fill Caps'].default_value = True
                        except Exception: pass
                        color_node(sw, "house")
                        parts.append(sw.outputs['Mesh'])

            # Post cap ring (kibashira cap) - torus at top of post
            cap_ring = _safe_node(tree, 'GeometryNodeMeshTorus', (base_x, 500 + i * 100))
            if cap_ring:
                try:
                    cap_ring.inputs['Major Radius'].default_value = pr * 1.35
                    cap_ring.inputs['Minor Radius'].default_value = pr * 0.28
                    cap_ring.inputs['Major Segments'].default_value = 24
                    cap_ring.inputs['Minor Segments'].default_value = 8
                except Exception: pass
                cap_tr = _safe_node(tree, 'GeometryNodeTransform', (base_x + 200, 500 + i * 100))
                if cap_tr:
                    try: cap_tr.inputs['Translation'].default_value = (x_off, 0, H)
                    except Exception: pass
                    _link(tree, cap_ring.outputs['Mesh'], cap_tr.inputs['Geometry'])
                    color_node(cap_ring, "ornament"); color_node(cap_tr, "ornament")
                    parts.append(cap_tr.outputs['Geometry'])

        # ── Shared horizontal beam profile (oval/rectangle cross-section) ────
        beam_prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveQuadrilateral', (base_x - 300, -400))
        if beam_prof:
            try:
                beam_prof.mode = 'RECTANGLE'
                beam_prof.inputs['Width'].default_value  = pr * 1.8   # depth (front-back)
                beam_prof.inputs['Height'].default_value = pr * 1.3   # height
            except Exception:
                beam_prof = None
        color_node(beam_prof, "house") if beam_prof else None

        # ── Nuki (horizontal tie beam at 70% height) ─────────────────────────
        nuki_span = W + pr * 2.4
        nuki_line = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (base_x, 800))
        if nuki_line:
            try:
                nuki_line.inputs['Start'].default_value = (-nuki_span / 2, 0, H * nuki_frac)
                nuki_line.inputs['End'].default_value   = ( nuki_span / 2, 0, H * nuki_frac)
            except Exception: pass
            color_node(nuki_line, "house")
            if beam_prof:
                nuki_sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 250, 800))
                if nuki_sw:
                    _link(tree, nuki_line.outputs['Curve'], nuki_sw.inputs['Curve'])
                    _link(tree, beam_prof.outputs['Curve'], nuki_sw.inputs['Profile Curve'])
                    try: nuki_sw.inputs['Fill Caps'].default_value = True
                    except Exception: pass
                    color_node(nuki_sw, "house")
                    parts.append(nuki_sw.outputs['Mesh'])

        # ── Shimaki (島杨) - secondary lintel; myōjin / ise only ─────────────
        if not is_shinmei:
            shimaki_span = W + pr * 3.2
            shimaki_prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveQuadrilateral', (base_x - 300, -700))
            if shimaki_prof:
                try:
                    shimaki_prof.mode = 'RECTANGLE'
                    shimaki_prof.inputs['Width'].default_value  = pr * 2.0
                    shimaki_prof.inputs['Height'].default_value = pr * 1.6
                except Exception:
                    shimaki_prof = beam_prof
            color_node(shimaki_prof, "house") if shimaki_prof else None

            shim_line = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (base_x, 1000))
            if shim_line:
                try:
                    shim_line.inputs['Start'].default_value = (-shimaki_span / 2, 0, H - pr * 0.5)
                    shim_line.inputs['End'].default_value   = ( shimaki_span / 2, 0, H - pr * 0.5)
                except Exception: pass
                color_node(shim_line, "house")
                prof_to_use = shimaki_prof if shimaki_prof else beam_prof
                if prof_to_use:
                    shim_sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 250, 1000))
                    if shim_sw:
                        _link(tree, shim_line.outputs['Curve'], shim_sw.inputs['Curve'])
                        _link(tree, prof_to_use.outputs['Curve'], shim_sw.inputs['Profile Curve'])
                        try: shim_sw.inputs['Fill Caps'].default_value = True
                        except Exception: pass
                        color_node(shim_sw, "house")
                        parts.append(shim_sw.outputs['Mesh'])

        # ── Kasagi (笠杨) - top lintel; straight on shinmei, curved on myōjin ─
        overhang = W * (0.12 if is_shinmei else 0.20)
        kas_z = H + pr * (0.6 if is_shinmei else 0.9)
        bez = _safe_node(tree, 'GeometryNodeCurvePrimitiveBezierSegment', (base_x, 1300))
        if bez:
            try:
                bez.inputs['Resolution'].default_value    = 32
                bez.inputs['Start'].default_value         = (-W / 2 - overhang, 0, kas_z)
                curve_lift = 0.0 if is_shinmei else curve * 0.5
                bez.inputs['Start Handle'].default_value  = (-W / 2 - overhang * 0.4, 0, H - curve_lift + pr * 0.9)
                bez.inputs['End Handle'].default_value    = ( W / 2 + overhang * 0.4, 0, H - curve_lift + pr * 0.9)
                bez.inputs['End'].default_value           = ( W / 2 + overhang, 0, kas_z)
            except Exception: pass
            color_node(bez, "ornament")

            kas_prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x - 300, 1100))
            if kas_prof:
                try:
                    kas_prof.inputs['Resolution'].default_value = 12
                    kas_prof.inputs['Radius'].default_value     = pr * 1.35
                except Exception: pass
                color_node(kas_prof, "ornament")
                kas_sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 250, 1300))
                if kas_sw:
                    _link(tree, bez.outputs['Curve'], kas_sw.inputs['Curve'])
                    _link(tree, kas_prof.outputs['Curve'], kas_sw.inputs['Profile Curve'])
                    try: kas_sw.inputs['Fill Caps'].default_value = True
                    except Exception: pass
                    color_node(kas_sw, "ornament")
                    parts.append(kas_sw.outputs['Mesh'])

        # ── Gakuzuka (額束) - center tablet strut ─────────────────────────────
        if show_gz and not is_shinmei:
            gz_line = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (base_x, 1500))
            if gz_line:
                try:
                    gz_line.inputs['Start'].default_value = (0, 0, H * nuki_frac + pr * 0.15)
                    gz_line.inputs['End'].default_value   = (0, 0, H - pr * 0.5)
                except Exception: pass
                color_node(gz_line, "ornament")
                gz_prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x - 300, 1500))
                if gz_prof:
                    try:
                        gz_prof.inputs['Resolution'].default_value = 8
                        gz_prof.inputs['Radius'].default_value     = pr * 0.55
                    except Exception: pass
                    gz_sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 250, 1500))
                    if gz_sw:
                        _link(tree, gz_line.outputs['Curve'], gz_sw.inputs['Curve'])
                        _link(tree, gz_prof.outputs['Curve'], gz_sw.inputs['Profile Curve'])
                        try: gz_sw.inputs['Fill Caps'].default_value = True
                        except Exception: pass
                        color_node(gz_sw, "ornament")
                        parts.append(gz_sw.outputs['Mesh'])

        # ── Kusabi (楔) - wedges at hashira/nuki junction ───────────────────
        if show_kusabi:
            for x_off in (-W / 2, W / 2):
                wedge = _safe_node(tree, 'GeometryNodeMeshCube', (base_x, 1700))
                if wedge:
                    try:
                        wedge.inputs['Size'].default_value = (pr * 0.9, pr * 1.4, pr * 0.7)
                    except Exception: pass
                    wtr = _safe_node(tree, 'GeometryNodeTransform', (base_x + 200, 1700))
                    if wtr:
                        try:
                            wtr.inputs['Translation'].default_value = (x_off, 0, H * nuki_frac)
                            wtr.inputs['Rotation'].default_value = (0, 0, math.radians(18 if x_off < 0 else -18))
                        except Exception: pass
                        _link(tree, wedge.outputs['Mesh'], wtr.inputs['Geometry'])
                        color_node(wtr, "ornament")
                        parts.append(wtr.outputs['Geometry'])

        # Shimenawa (注連縄) - sacred rope between hashira
        if show_shimenawa:
            rope_y = 0.0
            for seg in range(5):
                t = seg / 4.0
                rx = -W / 2 + t * W
                seg_line = _safe_node(tree, 'GeometryNodeCurvePrimitiveBezierSegment', (base_x, 1900 + seg * 40))
                if seg_line:
                    sag = H * 0.04
                    try:
                        seg_line.inputs['Start'].default_value = (rx, rope_y, H * 0.55)
                        seg_line.inputs['End'].default_value = (rx + W / 4, rope_y, H * 0.55 - sag)
                        seg_line.inputs['Start Handle'].default_value = (rx + W / 16, rope_y, H * 0.55)
                        seg_line.inputs['End Handle'].default_value = (rx + W / 5, rope_y, H * 0.55 - sag * 0.6)
                    except Exception:
                        pass
                    rprof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x - 200, 1900 + seg * 40))
                    if rprof:
                        try:
                            rprof.inputs['Radius'].default_value = pr * 0.35
                            rprof.inputs['Resolution'].default_value = 8
                        except Exception:
                            pass
                        rsw = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 220, 1900 + seg * 40))
                        if rsw:
                            _link(tree, seg_line.outputs['Curve'], rsw.inputs['Curve'])
                            _link(tree, rprof.outputs['Curve'], rsw.inputs['Profile Curve'])
                            color_node(rsw, "ornament")
                            parts.append(rsw.outputs['Mesh'])

        if not parts:
            return None
        join = _safe_node(tree, 'GeometryNodeJoinGeometry', (base_x + 800, 0))
        if join:
            for p in parts: _link(tree, p, join.inputs['Geometry'])
            color_node(join, "output")
            return join.outputs['Geometry']
        return parts[0]


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_zen_torii")
    return tree, gin, gout

register_builder(
    "MEL_zen_torii", build_zen_torii_group,
    "Zen Torii", "Zen builder (absorbed from monolith build_zen_torii).",
    category="zen_kit")


def build_zen_shoji_group(group_name="MEL_zen_shoji"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        """Shōji (隝子) - shamoji frame + kumiko lattice + paper panel."""
        W = PROPS.shoji_width
        H = PROPS.shoji_height
        nx = PROPS.shoji_grid_x
        ny = PROPS.shoji_grid_y
        m = PROPS.shoji_mullion
        frame_thick = max(m * 2.5, getattr(PROPS, 'shoji_frame_depth', 0.06))
        kumiko = getattr(PROPS, 'shoji_kumiko', 'GRID')
        parts = []
        for cx, cy, cz, sx, sy, sz in [
            (0, 0, H - frame_thick/2, W, frame_thick, frame_thick),  # top
            (0, 0, frame_thick/2,     W, frame_thick, frame_thick),  # bottom
            (-W/2 + frame_thick/2, 0, H/2, frame_thick, frame_thick, H),  # left
            ( W/2 - frame_thick/2, 0, H/2, frame_thick, frame_thick, H),  # right
        ]:
            bar = tree.nodes.new('GeometryNodeMeshCube'); bar.location = (base_x, len(parts) * 100); color_node(bar, "house")
            bar.inputs['Size'].default_value = (sx, sy, sz)
            bt = tree.nodes.new('GeometryNodeTransform'); bt.location = (base_x+200, len(parts) * 100)
            bt.inputs['Translation'].default_value = (cx, cy, cz)
            tree.links.new(bar.outputs['Mesh'], bt.inputs['Geometry'])
            parts.append(bt.outputs['Geometry'])

        # Kumiko (組子) diagonal motifs inside each cell
        if kumiko in ('ASANOHA', 'YUKITSUBAKI'):
            inner_W = W - frame_thick * 2
            inner_H = H - frame_thick * 2
            cell_w = inner_W / max(1, nx)
            cell_h = inner_H / max(1, ny)
            for ci in range(nx):
                for ri in range(ny):
                    cx = -W / 2 + frame_thick + (ci + 0.5) * cell_w
                    cz = frame_thick + (ri + 0.5) * cell_h
                    diag_len = math.hypot(cell_w, cell_h) * 0.92
                    for sign in (1, -1):
                        dline = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (base_x, 900 + ci * 40 + ri * 10))
                        if dline:
                            try:
                                dline.inputs['Start'].default_value = (cx - cell_w * 0.42 * sign, 0, cz - cell_h * 0.42)
                                dline.inputs['End'].default_value = (cx + cell_w * 0.42 * sign, 0, cz + cell_h * 0.42)
                            except Exception:
                                pass
                            dprof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x - 200, 900 + ci * 40))
                            if dprof:
                                try:
                                    dprof.inputs['Radius'].default_value = m * 0.55
                                    dprof.inputs['Resolution'].default_value = 6
                                except Exception:
                                    pass
                                dsw = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 200, 900 + ci * 40))
                                if dsw:
                                    _link(tree, dline.outputs['Curve'], dsw.inputs['Curve'])
                                    _link(tree, dprof.outputs['Curve'], dsw.inputs['Profile Curve'])
                                    color_node(dsw, "house")
                                    parts.append(dsw.outputs['Mesh'])

        # Vertical mullions
        inner_W = W - frame_thick * 2
        for i in range(1, nx):
            x = -W/2 + frame_thick + (i / nx) * inner_W
            bar = tree.nodes.new('GeometryNodeMeshCube'); bar.location = (base_x, 600); color_node(bar, "house")
            bar.inputs['Size'].default_value = (m, m, H - frame_thick * 2)
            bt = tree.nodes.new('GeometryNodeTransform'); bt.location = (base_x+200, 600)
            bt.inputs['Translation'].default_value = (x, 0, H/2)
            tree.links.new(bar.outputs['Mesh'], bt.inputs['Geometry'])
            parts.append(bt.outputs['Geometry'])

        # Horizontal mullions
        inner_H = H - frame_thick * 2
        for j in range(1, ny):
            z = frame_thick + (j / ny) * inner_H
            bar = tree.nodes.new('GeometryNodeMeshCube'); bar.location = (base_x, 800); color_node(bar, "house")
            bar.inputs['Size'].default_value = (W - frame_thick * 2, m, m)
            bt = tree.nodes.new('GeometryNodeTransform'); bt.location = (base_x+200, 800)
            bt.inputs['Translation'].default_value = (0, 0, z)
            tree.links.new(bar.outputs['Mesh'], bt.inputs['Geometry'])
            parts.append(bt.outputs['Geometry'])

        # Paper backing - a thin plane recessed slightly
        paper = tree.nodes.new('GeometryNodeMeshCube'); paper.location = (base_x, 1000); color_node(paper, "ornament")
        paper.inputs['Size'].default_value = (W - frame_thick * 2, m * 0.5, H - frame_thick * 2)
        pt = tree.nodes.new('GeometryNodeTransform'); pt.location = (base_x+200, 1000)
        pt.inputs['Translation'].default_value = (0, m * 0.5, H/2)
        tree.links.new(paper.outputs['Mesh'], pt.inputs['Geometry'])
        parts.append(pt.outputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+500, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_zen_shoji")
    return tree, gin, gout

register_builder(
    "MEL_zen_shoji", build_zen_shoji_group,
    "Zen Shoji", "Zen builder (absorbed from monolith build_zen_shoji).",
    category="zen_kit")


def build_zen_lantern_group(group_name="MEL_zen_lantern"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        """Ishi-dōrō (石灯籠) - v2.56 research-backed tōrō assembly.

        Eight named elements (bottom -> top), per JAANUS / NAJGA / Wikipedia:
          kidan 基壇, kiso 基礎, sao 竿, chūdai 中台, hibukuro 火袋,
          kasa 笠 (+ warabide 蕨手), ukebana 請花, hōju 宝珠
        Geometry only - assign stone/wood materials in UE.
        """
        import math
        H = getattr(PROPS, 'zen_lantern_height', 2.0)
        R = getattr(PROPS, 'zen_lantern_radius', 0.35)
        style = getattr(PROPS, 'zen_lantern_style', 'KASUGA')
        layers = getattr(PROPS, 'zen_lantern_layers', 6)
        warabide = getattr(PROPS, 'zen_lantern_warabide', 0.35)
        higuchi = getattr(PROPS, 'zen_lantern_higuchi', 'ROUND')
        hoju_s = getattr(PROPS, 'zen_lantern_hoju_scale', 1.0)
        kasa_oh = getattr(PROPS, 'zen_lantern_kasa_overhang', 1.0)
        show_kidan = getattr(PROPS, 'zen_lantern_show_kidan', True)
        show_uke = getattr(PROPS, 'zen_lantern_show_ukebana', True)

        sao_mul = {'KASUGA': 1.0, 'YUKIMI': 0.35, 'ORIBE': 0.7, 'MISAKI': 0.15}.get(style, 1.0)
        kasa_mul = {'KASUGA': 1.0, 'YUKIMI': 1.45, 'ORIBE': 0.95, 'MISAKI': 1.55}.get(style, 1.0) * kasa_oh
        hib_verts = {'KASUGA': 6, 'YUKIMI': 6, 'ORIBE': 4, 'MISAKI': 8}.get(style, 6)

        active = _zen_lantern_element_mask(layers, show_kidan, show_uke)
        h_fracs = {
            'kidan': 0.06, 'kiso': 0.10, 'sao': 0.28 * sao_mul, 'chudai': 0.07,
            'hibukuro': 0.20, 'kasa': 0.16 * kasa_mul, 'ukebana': 0.05, 'hoju': 0.08 * hoju_s,
        }
        total_f = sum(h_fracs[k] for k in active) or 1.0
        parts = []
        cur_z = 0.0
        y_slot = 0

        def _ring_disc(major_r, minor_r, flat_z, y_offset, verts=32, segs=8, label="lantern", squash=0.30):
            nd = _safe_node(tree, 'GeometryNodeMeshTorus', (base_x, y_offset))
            if nd is None:
                return None
            try:
                nd.inputs['Major Radius'].default_value = major_r
                nd.inputs['Minor Radius'].default_value = minor_r
                nd.inputs['Major Segments'].default_value = verts
                nd.inputs['Minor Segments'].default_value = segs
            except Exception:
                return None
            tr = _safe_node(tree, 'GeometryNodeTransform', (base_x + 200, y_offset))
            if tr is None:
                return None
            try:
                tr.inputs['Translation'].default_value = (0, 0, flat_z)
                tr.inputs['Scale'].default_value = (1.0, 1.0, squash)
            except Exception:
                pass
            _link(tree, nd.outputs['Mesh'], tr.inputs['Geometry'])
            color_node(nd, label)
            color_node(tr, label)
            return tr.outputs['Geometry']

        def _poly_col(verts_n, radius, extrude_h, z_base, y_offset, label="lantern"):
            circ = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x, y_offset))
            if circ is None:
                return None
            try:
                circ.inputs['Resolution'].default_value = verts_n
                circ.inputs['Radius'].default_value = radius
            except Exception:
                return None
            fill = _safe_node(tree, 'GeometryNodeFillCurve', (base_x + 200, y_offset))
            if fill:
                try:
                    fill.mode = 'NGONS'
                except Exception:
                    pass
                _link(tree, circ.outputs['Curve'], fill.inputs['Curve'])
            ext = _safe_node(tree, 'GeometryNodeExtrudeMesh', (base_x + 400, y_offset))
            if ext and fill:
                ext.mode = 'FACES'
                try:
                    ext.inputs['Offset Scale'].default_value = extrude_h
                except Exception:
                    pass
                _link(tree, fill.outputs['Mesh'], ext.inputs['Mesh'])
            tr = _safe_node(tree, 'GeometryNodeTransform', (base_x + 600, y_offset))
            if tr:
                try:
                    tr.inputs['Translation'].default_value = (0, 0, z_base)
                except Exception:
                    pass
                if ext:
                    _link(tree, ext.outputs['Mesh'], tr.inputs['Geometry'])
                color_node(circ, label)
                color_node(tr, label)
                return tr.outputs['Geometry']
            return None

        def _tube(radius, z_start, z_end, verts_n, y_offset, label="lantern"):
            line = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (base_x, y_offset))
            if line is None:
                return None
            try:
                line.inputs['Start'].default_value = (0, 0, z_start)
                line.inputs['End'].default_value = (0, 0, z_end)
            except Exception:
                return None
            prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x - 250, y_offset))
            if prof is None:
                return None
            try:
                prof.inputs['Resolution'].default_value = verts_n
                prof.inputs['Radius'].default_value = radius
            except Exception:
                return None
            sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 250, y_offset))
            if sw is None:
                return None
            _link(tree, line.outputs['Curve'], sw.inputs['Curve'])
            _link(tree, prof.outputs['Curve'], sw.inputs['Profile Curve'])
            try:
                sw.inputs['Fill Caps'].default_value = True
            except Exception:
                pass
            color_node(sw, label)
            return sw.outputs['Mesh']

        def _hibukuro_higuchi(z_base, h_this, y_offset):
            for face_i, ang in enumerate((0.0, math.pi / 2.0)):
                cx = math.cos(ang) * R * 0.55
                cy = math.sin(ang) * R * 0.55
                opening = max(R * 0.22, 0.04)
                if higuchi == 'MOON':
                    arc = _safe_node(tree, 'GeometryNodeCurvePrimitiveArc', (base_x, y_offset - face_i * 80))
                    if arc:
                        try:
                            arc.inputs['Radius'].default_value = opening
                            arc.inputs['Start Angle'].default_value = math.radians(-60)
                            arc.inputs['Sweep Angle'].default_value = math.radians(120)
                        except Exception:
                            pass
                        atr = _safe_node(tree, 'GeometryNodeTransform', (base_x + 180, y_offset - face_i * 80))
                        if atr:
                            try:
                                atr.inputs['Translation'].default_value = (cx, cy, z_base + h_this * 0.5)
                                atr.inputs['Rotation'].default_value = (math.pi / 2, 0, ang)
                            except Exception:
                                pass
                            _link(tree, arc.outputs['Curve'], atr.inputs['Geometry'])
                            sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 360, y_offset - face_i * 80))
                            if sw:
                                prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x + 120, y_offset - face_i * 80))
                                if prof:
                                    try:
                                        prof.inputs['Radius'].default_value = R * 0.025
                                        prof.inputs['Resolution'].default_value = 6
                                    except Exception:
                                        pass
                                    _link(tree, atr.outputs['Geometry'], sw.inputs['Curve'])
                                    _link(tree, prof.outputs['Curve'], sw.inputs['Profile Curve'])
                                    color_node(sw, "ornament")
                                    parts.append(sw.outputs['Mesh'])
                else:
                    w = opening
                    d = opening
                    frame = _safe_node(tree, 'GeometryNodeMeshCube', (base_x, y_offset - face_i * 80))
                    if frame:
                        try:
                            frame.inputs['Size'].default_value = (w, R * 0.04, d)
                        except Exception:
                            pass
                        ftr = _safe_node(tree, 'GeometryNodeTransform', (base_x + 200, y_offset - face_i * 80))
                        if ftr:
                            try:
                                ftr.inputs['Translation'].default_value = (cx, cy, z_base + h_this * 0.5)
                                ftr.inputs['Rotation'].default_value = (0, 0, ang)
                            except Exception:
                                pass
                            _link(tree, frame.outputs['Mesh'], ftr.inputs['Geometry'])
                            color_node(ftr, "ornament")
                            parts.append(ftr.outputs['Geometry'])

        def _kasa_warabide(z_base, h_this, y_offset):
            if warabide <= 0.01:
                return
            for k in range(hib_verts):
                ang = k * math.tau / hib_verts
                tip_x = math.cos(ang) * R * 1.15 * kasa_mul
                tip_y = math.sin(ang) * R * 1.15 * kasa_mul
                bez = _safe_node(tree, 'GeometryNodeCurvePrimitiveBezierSegment', (base_x, y_offset - k * 50))
                if bez:
                    try:
                        bez.inputs['Start'].default_value = (tip_x * 0.92, tip_y * 0.92, z_base + h_this * 0.12)
                        bez.inputs['End'].default_value = (tip_x, tip_y, z_base + h_this * (0.12 + warabide * 0.35))
                        bez.inputs['Start Handle'].default_value = (tip_x * 0.95, tip_y * 0.95, z_base + h_this * 0.18)
                        bez.inputs['End Handle'].default_value = (tip_x, tip_y, z_base + h_this * (0.08 + warabide * 0.2))
                    except Exception:
                        pass
                    prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x - 200, y_offset - k * 50))
                    if prof:
                        try:
                            prof.inputs['Radius'].default_value = R * 0.04
                            prof.inputs['Resolution'].default_value = 6
                        except Exception:
                            pass
                        sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 220, y_offset - k * 50))
                        if sw:
                            _link(tree, bez.outputs['Curve'], sw.inputs['Curve'])
                            _link(tree, prof.outputs['Curve'], sw.inputs['Profile Curve'])
                            color_node(sw, "ornament")
                            parts.append(sw.outputs['Mesh'])

        for elem in active:
            h_this = H * (h_fracs.get(elem, 0.1) / total_f)

            if elem == 'kidan':
                disc = _ring_disc(R * 1.35, R * 0.32, cur_z + h_this * 0.5, y_slot, squash=0.22)
                if disc:
                    parts.append(disc)

            elif elem == 'kiso':
                disc = _ring_disc(R * 1.12, R * 0.28, cur_z + h_this * 0.5, y_slot)
                if disc:
                    parts.append(disc)
                core = _tube(R * 0.48, cur_z, cur_z + h_this, 12, y_slot - 120)
                if core:
                    parts.append(core)

            elif elem == 'sao':
                if sao_mul > 0.12:
                    shaft = _tube(R * 0.26, cur_z, cur_z + h_this, 12, y_slot)
                    if shaft:
                        parts.append(shaft)
                    fushi = _ring_disc(R * 0.38, R * 0.10, cur_z + h_this * 0.5, y_slot - 180, verts=20, segs=8)
                    if fushi:
                        parts.append(fushi)

            elif elem == 'chudai':
                col = _poly_col(8, R * 0.82, h_this, cur_z, y_slot)
                if col:
                    parts.append(col)
                rim = _ring_disc(R * 0.92, R * 0.12, cur_z + h_this, y_slot - 160, verts=32, segs=6)
                if rim:
                    parts.append(rim)

            elif elem == 'hibukuro':
                col = _poly_col(hib_verts, R * 0.74, h_this, cur_z, y_slot, label="ornament")
                if col:
                    parts.append(col)
                _hibukuro_higuchi(cur_z, h_this, y_slot - 300)

            elif elem == 'kasa':
                col = _poly_col(hib_verts, R * 1.18 * kasa_mul, h_this * 0.28, cur_z, y_slot, label="ornament")
                if col:
                    parts.append(col)
                kasa_rim = _safe_node(tree, 'GeometryNodeMeshTorus', (base_x, y_slot - 200))
                if kasa_rim:
                    try:
                        kasa_rim.inputs['Major Radius'].default_value = R * 1.12 * kasa_mul
                        kasa_rim.inputs['Minor Radius'].default_value = R * 0.18
                        kasa_rim.inputs['Major Segments'].default_value = 48
                        kasa_rim.inputs['Minor Segments'].default_value = 8
                    except Exception:
                        pass
                    kasa_tr = _safe_node(tree, 'GeometryNodeTransform', (base_x + 200, y_slot - 200))
                    if kasa_tr:
                        try:
                            kasa_tr.inputs['Translation'].default_value = (0, 0, cur_z + h_this * 0.2)
                            kasa_tr.inputs['Scale'].default_value = (1.0, 1.0, 0.45)
                        except Exception:
                            pass
                        _link(tree, kasa_rim.outputs['Mesh'], kasa_tr.inputs['Geometry'])
                        color_node(kasa_rim, "ornament")
                        parts.append(kasa_tr.outputs['Geometry'])
                _kasa_warabide(cur_z, h_this, y_slot - 400)

            elif elem == 'ukebana':
                lotus = _poly_col(12, R * 0.32, h_this * 0.55, cur_z, y_slot, label="ornament")
                if lotus:
                    parts.append(lotus)
                petal = _ring_disc(R * 0.28, R * 0.14, cur_z + h_this * 0.35, y_slot - 120, verts=24, segs=10, squash=0.55)
                if petal:
                    parts.append(petal)

            elif elem == 'hoju':
                for k, (maj, mino, z_frac) in enumerate([
                    (R * 0.22 * hoju_s, R * 0.20 * hoju_s, 0.12),
                    (R * 0.16 * hoju_s, R * 0.14 * hoju_s, 0.42),
                    (R * 0.08 * hoju_s, R * 0.07 * hoju_s, 0.72),
                ]):
                    ring = _safe_node(tree, 'GeometryNodeMeshTorus', (base_x, y_slot - 500 - k * 120))
                    if ring:
                        try:
                            ring.inputs['Major Radius'].default_value = maj
                            ring.inputs['Minor Radius'].default_value = mino
                            ring.inputs['Major Segments'].default_value = 20
                            ring.inputs['Minor Segments'].default_value = 8
                        except Exception:
                            pass
                        rtr = _safe_node(tree, 'GeometryNodeTransform', (base_x + 200, y_slot - 500 - k * 120))
                        if rtr:
                            try:
                                rtr.inputs['Translation'].default_value = (0, 0, cur_z + h_this * z_frac)
                            except Exception:
                                pass
                            _link(tree, ring.outputs['Mesh'], rtr.inputs['Geometry'])
                            color_node(ring, "ornament")
                            parts.append(rtr.outputs['Geometry'])

            cur_z += h_this
            y_slot -= 650

        if not parts:
            return None
        join = _safe_node(tree, 'GeometryNodeJoinGeometry', (base_x + 900, 0))
        if join:
            for p in parts:
                _link(tree, p, join.inputs['Geometry'])
            color_node(join, "output")
            return join.outputs['Geometry']
        return parts[0]


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_zen_lantern")
    return tree, gin, gout

register_builder(
    "MEL_zen_lantern", build_zen_lantern_group,
    "Zen Lantern", "Zen builder (absorbed from monolith build_zen_lantern).",
    category="zen_kit")


def build_zen_teahouse_group(group_name="MEL_zen_teahouse"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        """Tea house - square pavilion with steeply-pitched curved roof + raised platform."""
        W = PROPS.teahouse_width
        D = PROPS.teahouse_depth
        H = PROPS.teahouse_height
        pitch = PROPS.teahouse_pitch_factor
        parts = []

        # Raised platform - extended outward for engawa if enabled
        engawa_width = PROPS.teahouse_engawa_width if PROPS.teahouse_engawa else 0.0
        platform_W = W + engawa_width * 2
        platform_D = D + engawa_width * 2
        platform = tree.nodes.new('GeometryNodeMeshCube'); platform.location = (base_x, 0); color_node(platform, "house")
        platform.inputs['Size'].default_value = (platform_W, platform_D, 0.25)
        pt = tree.nodes.new('GeometryNodeTransform'); pt.location = (base_x+200, 0)
        pt.inputs['Translation'].default_value = (0, 0, 0.125)
        tree.links.new(platform.outputs['Mesh'], pt.inputs['Geometry'])
        parts.append(pt.outputs['Geometry'])

        # Engawa railing posts (small) along the platform edge
        if PROPS.teahouse_engawa:
            n_posts_side = 4
            for side_x, side_y in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                if side_x != 0:  # left/right side
                    for i in range(n_posts_side):
                        y = -platform_D/2 + (i + 0.5) * (platform_D / n_posts_side)
                        post = tree.nodes.new('GeometryNodeMeshCylinder'); post.location = (base_x, 100 + i * 50); color_node(post, "ornament")
                        post.inputs['Vertices'].default_value = 6
                        post.inputs['Radius'].default_value = 0.025
                        post.inputs['Depth'].default_value = 0.5
                        pot = tree.nodes.new('GeometryNodeTransform'); pot.location = (base_x+200, 100 + i * 50)
                        pot.inputs['Translation'].default_value = (side_x * (platform_W/2 - 0.04), y, 0.25 + 0.25)
                        tree.links.new(post.outputs['Mesh'], pot.inputs['Geometry'])
                        parts.append(pot.outputs['Geometry'])
                else:  # front/back side
                    for i in range(n_posts_side):
                        x = -platform_W/2 + (i + 0.5) * (platform_W / n_posts_side)
                        post = tree.nodes.new('GeometryNodeMeshCylinder'); post.location = (base_x, 100 + (i + n_posts_side) * 50); color_node(post, "ornament")
                        post.inputs['Vertices'].default_value = 6
                        post.inputs['Radius'].default_value = 0.025
                        post.inputs['Depth'].default_value = 0.5
                        pot = tree.nodes.new('GeometryNodeTransform'); pot.location = (base_x+200, 100 + (i + n_posts_side) * 50)
                        pot.inputs['Translation'].default_value = (x, side_y * (platform_D/2 - 0.04), 0.25 + 0.25)
                        tree.links.new(post.outputs['Mesh'], pot.inputs['Geometry'])
                        parts.append(pot.outputs['Geometry'])

        # 4 corner posts
        pr = 0.08
        post_h = H * 0.6
        for x_s, y_s in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
            post = tree.nodes.new('GeometryNodeMeshCylinder'); post.location = (base_x, 200); color_node(post, "house")
            post.inputs['Vertices'].default_value = 12
            post.inputs['Radius'].default_value = pr
            post.inputs['Depth'].default_value = post_h
            ppt = tree.nodes.new('GeometryNodeTransform'); ppt.location = (base_x+200, 200)
            ppt.inputs['Translation'].default_value = (x_s * (W/2 - pr * 2), y_s * (D/2 - pr * 2), 0.25 + post_h/2)
            tree.links.new(post.outputs['Mesh'], ppt.inputs['Geometry'])
            parts.append(ppt.outputs['Geometry'])

        # Floor mat (tatami area)
        mat = tree.nodes.new('GeometryNodeMeshCube'); mat.location = (base_x, 400); color_node(mat, "house")
        mat.inputs['Size'].default_value = (W * 0.9, D * 0.9, 0.05)
        mt = tree.nodes.new('GeometryNodeTransform'); mt.location = (base_x+200, 400)
        mt.inputs['Translation'].default_value = (0, 0, 0.27)
        tree.links.new(mat.outputs['Mesh'], mt.inputs['Geometry'])
        parts.append(mt.outputs['Geometry'])

        # ---- Curved hip roof (irimoya-style sweeping eaves) ----------------
        # Built from a flat Grid deformed by a concave Japanese roof curve.
        # Square level-sets (Chebyshev distance) give a proper 4-sided hip;
        # the (1-m)^pitch profile is concave so the eaves sweep outward.
        roof_h = H * pitch
        overhang = W * 0.28
        eave_span = W + overhang * 2          # full footprint of the eave
        half_span = eave_span / 2.0
        roof_base_z = 0.25 + post_h           # eave height sits on the posts
        res = 24

        grid = tree.nodes.new('GeometryNodeMeshGrid'); grid.location = (base_x, 600); color_node(grid, "roof")
        grid.inputs['Size X'].default_value = eave_span
        grid.inputs['Size Y'].default_value = eave_span
        grid.inputs['Vertices X'].default_value = res
        grid.inputs['Vertices Y'].default_value = res

        gpos = tree.nodes.new('GeometryNodeInputPosition'); gpos.location = (base_x, 850)
        gsep = tree.nodes.new('ShaderNodeSeparateXYZ'); gsep.location = (base_x+200, 850)
        tree.links.new(gpos.outputs['Position'], gsep.inputs['Vector'])
        ax = tree.nodes.new('ShaderNodeMath'); ax.location = (base_x+380, 920); ax.operation = 'ABSOLUTE'
        tree.links.new(gsep.outputs['X'], ax.inputs[0])
        ay = tree.nodes.new('ShaderNodeMath'); ay.location = (base_x+380, 800); ay.operation = 'ABSOLUTE'
        tree.links.new(gsep.outputs['Y'], ay.inputs[0])
        cheb = tree.nodes.new('ShaderNodeMath'); cheb.location = (base_x+560, 860); cheb.operation = 'MAXIMUM'
        tree.links.new(ax.outputs[0], cheb.inputs[0]); tree.links.new(ay.outputs[0], cheb.inputs[1])
        mnorm = tree.nodes.new('ShaderNodeMath'); mnorm.location = (base_x+740, 860); mnorm.operation = 'DIVIDE'
        mnorm.inputs[1].default_value = max(0.001, half_span)
        tree.links.new(cheb.outputs[0], mnorm.inputs[0])      # m in [0..1]
        inv = tree.nodes.new('ShaderNodeMath'); inv.location = (base_x+920, 920); inv.operation = 'SUBTRACT'
        inv.inputs[0].default_value = 1.0
        tree.links.new(mnorm.outputs[0], inv.inputs[1])       # 1 - m
        powr = tree.nodes.new('ShaderNodeMath'); powr.location = (base_x+1100, 920); powr.operation = 'POWER'
        powr.inputs[1].default_value = max(0.4, pitch * 1.2)  # concave when >1
        tree.links.new(inv.outputs[0], powr.inputs[0])
        zmul = tree.nodes.new('ShaderNodeMath'); zmul.location = (base_x+1280, 920); zmul.operation = 'MULTIPLY'
        zmul.inputs[1].default_value = roof_h
        tree.links.new(powr.outputs[0], zmul.inputs[0])
        # Upturned eave flip: lift the outer tips (m^6 spikes only at the very edge)
        eflip = tree.nodes.new('ShaderNodeMath'); eflip.location = (base_x+920, 760); eflip.operation = 'POWER'
        eflip.inputs[1].default_value = 6.0
        tree.links.new(mnorm.outputs[0], eflip.inputs[0])
        eamp = tree.nodes.new('ShaderNodeMath'); eamp.location = (base_x+1100, 760); eamp.operation = 'MULTIPLY'
        eamp.inputs[1].default_value = roof_h * 0.16
        tree.links.new(eflip.outputs[0], eamp.inputs[0])
        zsum = tree.nodes.new('ShaderNodeMath'); zsum.location = (base_x+1460, 880); zsum.operation = 'ADD'
        tree.links.new(zmul.outputs[0], zsum.inputs[0]); tree.links.new(eamp.outputs[0], zsum.inputs[1])
        zvec = tree.nodes.new('ShaderNodeCombineXYZ'); zvec.location = (base_x+1640, 880)
        tree.links.new(zsum.outputs[0], zvec.inputs['Z'])
        setp = tree.nodes.new('GeometryNodeSetPosition'); setp.location = (base_x+1820, 600); color_node(setp, "roof")
        tree.links.new(grid.outputs['Mesh'], setp.inputs['Geometry'])
        tree.links.new(zvec.outputs['Vector'], setp.inputs['Offset'])
        # Give the shell thickness so it reads as a solid roof
        rthick = tree.nodes.new('GeometryNodeExtrudeMesh'); rthick.location = (base_x+2020, 600); color_node(rthick, "roof")
        rthick.mode = 'FACES'
        try: rthick.inputs['Offset Scale'].default_value = -0.12
        except Exception: pass
        tree.links.new(setp.outputs['Geometry'], rthick.inputs['Mesh'])
        rt = tree.nodes.new('GeometryNodeTransform'); rt.location = (base_x+2220, 600)
        rt.inputs['Translation'].default_value = (0, 0, roof_base_z)
        tree.links.new(rthick.outputs['Mesh'], rt.inputs['Geometry'])
        parts.append(rt.outputs['Geometry'])

        # Corner hip ridge beams - bezier sweeps from apex down to each eave tip
        ridge_prof = _make_circle_profile(tree, 0.05, 6, (base_x, 1100), PROPS)
        apex_z = roof_base_z + roof_h + roof_h * 0.16
        for x_s, y_s in [(-1, -1), (1, -1), (1, 1), (-1, 1)]:
            rb = tree.nodes.new('GeometryNodeCurvePrimitiveBezierSegment'); rb.location = (base_x+200, 1100 + (x_s+y_s) * 40)
            rb.inputs['Start'].default_value = (0, 0, apex_z)
            rb.inputs['End'].default_value = (x_s * half_span, y_s * half_span, roof_base_z + roof_h * 0.16)
            rb.inputs['Start Handle'].default_value = (x_s * half_span * 0.35, y_s * half_span * 0.35, apex_z)
            rb.inputs['End Handle'].default_value = (x_s * half_span * 0.75, y_s * half_span * 0.75, roof_base_z + roof_h * 0.55)
            rsw = tree.nodes.new('GeometryNodeCurveToMesh'); rsw.location = (base_x+420, 1100 + (x_s+y_s) * 40); color_node(rsw, "roof")
            tree.links.new(rb.outputs['Curve'], rsw.inputs['Curve'])
            if ridge_prof is not None:
                tree.links.new(ridge_prof.outputs['Curve'], rsw.inputs['Profile Curve'])
            rsw.inputs['Fill Caps'].default_value = True
            parts.append(rsw.outputs['Mesh'])

        # Finial (hōju) at apex
        fin = tree.nodes.new('GeometryNodeMeshUVSphere'); fin.location = (base_x+200, 1400); color_node(fin, "ornament")
        fin.inputs['Radius'].default_value = 0.10
        fint = tree.nodes.new('GeometryNodeTransform'); fint.location = (base_x+420, 1400)
        fint.inputs['Translation'].default_value = (0, 0, apex_z + 0.05)
        tree.links.new(fin.outputs['Mesh'], fint.inputs['Geometry'])
        parts.append(fint.outputs['Geometry'])

        # Tokonoma (床の間) - recessed alcove with tokobashira pillar
        if getattr(PROPS, 'teahouse_tokonoma', True):
            alcove_w = W * 0.28
            alcove_d = 0.18
            alcove_h = H * 0.55
            alc = tree.nodes.new('GeometryNodeMeshCube'); alc.location = (base_x, 1500); color_node(alc, "house")
            alc.inputs['Size'].default_value = (alcove_w, alcove_d, alcove_h)
            alct = tree.nodes.new('GeometryNodeTransform'); alct.location = (base_x+200, 1500)
            alct.inputs['Translation'].default_value = (-W * 0.22, D / 2 - alcove_d * 0.6, 0.27 + alcove_h / 2)
            tree.links.new(alc.outputs['Mesh'], alct.inputs['Geometry'])
            parts.append(alct.outputs['Geometry'])
            # Tokobashira (床柱) - alcove pillar
            tbp = tree.nodes.new('GeometryNodeMeshCylinder'); tbp.location = (base_x, 1600); color_node(tbp, "ornament")
            tbp.inputs['Vertices'].default_value = 8
            tbp.inputs['Radius'].default_value = 0.045
            tbp.inputs['Depth'].default_value = alcove_h
            tbpt = tree.nodes.new('GeometryNodeTransform'); tbpt.location = (base_x+200, 1600)
            tbpt.inputs['Translation'].default_value = (-W * 0.22 + alcove_w * 0.35, D / 2 - alcove_d * 0.3, 0.27 + alcove_h / 2)
            tree.links.new(tbp.outputs['Mesh'], tbpt.inputs['Geometry'])
            parts.append(tbpt.outputs['Geometry'])

        # Ro (炉) - sunken hearth in tatami floor
        if getattr(PROPS, 'teahouse_ro', True):
            ro = tree.nodes.new('GeometryNodeMeshCube'); ro.location = (base_x, 1700); color_node(ro, "house")
            ro.inputs['Size'].default_value = (W * 0.22, D * 0.22, 0.08)
            rot = tree.nodes.new('GeometryNodeTransform'); rot.location = (base_x+200, 1700)
            rot.inputs['Translation'].default_value = (W * 0.12, -D * 0.08, 0.22)
            tree.links.new(ro.outputs['Mesh'], rot.inputs['Geometry'])
            parts.append(rot.outputs['Geometry'])

        # Nijiriguchi (躙口) - low crawl entrance opening
        if getattr(PROPS, 'teahouse_nijiriguchi', False):
            niw = W * 0.35
            nih = H * 0.38
            niche = tree.nodes.new('GeometryNodeMeshCube'); niche.location = (base_x, 1800); color_node(niche, "house")
            niche.inputs['Size'].default_value = (niw, 0.12, nih)
            nit = tree.nodes.new('GeometryNodeTransform'); nit.location = (base_x+200, 1800)
            nit.inputs['Translation'].default_value = (0, -D / 2 + 0.08, 0.27 + nih / 2)
            tree.links.new(niche.outputs['Mesh'], nit.inputs['Geometry'])
            parts.append(nit.outputs['Geometry'])

        # Chumon (中門) - roji inner gate posts on engawa approach
        if getattr(PROPS, 'teahouse_chumon', False) and PROPS.teahouse_engawa:
            gate_w = platform_W * 0.55
            for gx in (-gate_w / 2, gate_w / 2):
                gp = tree.nodes.new('GeometryNodeMeshCylinder'); gp.location = (base_x, 1900); color_node(gp, "ornament")
                gp.inputs['Vertices'].default_value = 8
                gp.inputs['Radius'].default_value = 0.05
                gp.inputs['Depth'].default_value = 1.1
                gpt = tree.nodes.new('GeometryNodeTransform'); gpt.location = (base_x+200, 1900)
                gpt.inputs['Translation'].default_value = (gx, -platform_D / 2 - 0.15, 0.25 + 0.55)
                tree.links.new(gp.outputs['Mesh'], gpt.inputs['Geometry'])
                parts.append(gpt.outputs['Geometry'])
            lintel = tree.nodes.new('GeometryNodeMeshCube'); lintel.location = (base_x, 2000); color_node(lintel, "ornament")
            lintel.inputs['Size'].default_value = (gate_w + 0.2, 0.08, 0.08)
            lt = tree.nodes.new('GeometryNodeTransform'); lt.location = (base_x+200, 2000)
            lt.inputs['Translation'].default_value = (0, -platform_D / 2 - 0.15, 0.25 + 1.05)
            tree.links.new(lintel.outputs['Mesh'], lt.inputs['Geometry'])
            parts.append(lt.outputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+2600, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_zen_teahouse")
    return tree, gin, gout

register_builder(
    "MEL_zen_teahouse", build_zen_teahouse_group,
    "Zen Teahouse", "Zen builder (absorbed from monolith build_zen_teahouse).",
    category="zen_kit")


def build_zen_bridge_group(group_name="MEL_zen_bridge"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        """Taikobashi / soribashi (太鼓橋 / 反橋) - moon drum garden bridge."""
        span = PROPS.zen_bridge_span
        rise = PROPS.zen_bridge_rise
        width = PROPS.zen_bridge_width
        n_planks = PROPS.zen_bridge_planks
        style = getattr(PROPS, 'zen_bridge_style', 'TAIKOBASHI')
        show_giboshi = getattr(PROPS, 'zen_bridge_giboshi', True)
        rise_mul = 2.0 if style == 'TAIKOBASHI' else 1.25
        arc_lift = rise * rise_mul
        parts = []

        # Build the bridge arc as a curve
        arc = tree.nodes.new('GeometryNodeCurvePrimitiveBezierSegment'); arc.location = (base_x, 0); color_node(arc, "house")
        arc.inputs['Resolution'].default_value = 32
        arc.inputs['Start'].default_value         = (-span/2, 0, 0)
        arc.inputs['Start Handle'].default_value  = (-span/4, 0, arc_lift)
        arc.inputs['End Handle'].default_value    = ( span/4, 0, arc_lift)
        arc.inputs['End'].default_value           = ( span/2, 0, 0)

        # Rectangle profile for the walkway
        rect = tree.nodes.new('GeometryNodeCurvePrimitiveQuadrilateral'); rect.location = (base_x, -300); color_node(rect, "house")
        try:
            rect.mode = 'RECTANGLE'
            rect.inputs['Width'].default_value = width
            rect.inputs['Height'].default_value = 0.08
        except Exception: pass

        # Sweep deck
        deck = tree.nodes.new('GeometryNodeCurveToMesh'); deck.location = (base_x+300, 0)
        tree.links.new(arc.outputs['Curve'], deck.inputs['Curve'])
        tree.links.new(rect.outputs['Curve'], deck.inputs['Profile Curve'])
        deck.inputs['Fill Caps'].default_value = True
        parts.append(deck.outputs['Mesh'])

        # Plank cross-pieces - resampled ALONG the arc so they ride the curve,
        # rotation-aligned to the tangent so each plank tilts with the slope.
        plank_arc = tree.nodes.new('GeometryNodeCurvePrimitiveBezierSegment'); plank_arc.location = (base_x, 300); color_node(plank_arc, "house")
        plank_arc.inputs['Resolution'].default_value = 32
        plank_arc.inputs['Start'].default_value        = (-span/2, 0, 0.05)
        plank_arc.inputs['Start Handle'].default_value = (-span/4, 0, arc_lift + 0.05)
        plank_arc.inputs['End Handle'].default_value   = ( span/4, 0, arc_lift + 0.05)
        plank_arc.inputs['End'].default_value          = ( span/2, 0, 0.05)

        presample = tree.nodes.new('GeometryNodeResampleCurve'); presample.location = (base_x+200, 300); color_node(presample, "house")
        try: presample.mode = 'COUNT'
        except Exception: pass
        presample.inputs['Count'].default_value = n_planks
        tree.links.new(plank_arc.outputs['Curve'], presample.inputs['Curve'])

        pc2p = tree.nodes.new('GeometryNodeCurveToPoints'); pc2p.location = (base_x+380, 300); color_node(pc2p, "house")
        try: pc2p.mode = 'EVALUATED'
        except Exception: pass
        tree.links.new(presample.outputs['Curve'], pc2p.inputs['Curve'])

        plank = tree.nodes.new('GeometryNodeMeshCube'); plank.location = (base_x, 500); color_node(plank, "house")
        plank.inputs['Size'].default_value = (span / max(1, n_planks) * 0.85, width * 1.05, 0.045)

        inst = tree.nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (base_x+600, 400)
        tree.links.new(pc2p.outputs['Points'], inst.inputs['Points'])
        tree.links.new(plank.outputs['Mesh'], inst.inputs['Instance'])
        try:
            tree.links.new(pc2p.outputs['Rotation'], inst.inputs['Rotation'])
        except Exception:
            pass
        realize = tree.nodes.new('GeometryNodeRealizeInstances'); realize.location = (base_x+820, 400)
        tree.links.new(inst.outputs['Instances'], realize.inputs['Geometry'])
        parts.append(realize.outputs['Geometry'])

        # Optional side railings
        if PROPS.zen_bridge_railings:
            for y_off in (-width/2 + 0.04, width/2 - 0.04):
                # railing arc parallel to deck arc, offset in Y and up
                rail_arc = tree.nodes.new('GeometryNodeCurvePrimitiveBezierSegment'); rail_arc.location = (base_x, 800)
                rail_arc.inputs['Resolution'].default_value = 32
                rail_arc.inputs['Start'].default_value        = (-span/2, y_off, 0.5)
                rail_arc.inputs['Start Handle'].default_value = (-span/4, y_off, arc_lift + 0.5)
                rail_arc.inputs['End Handle'].default_value   = ( span/4, y_off, arc_lift + 0.5)
                rail_arc.inputs['End'].default_value          = ( span/2, y_off, 0.5)

                rprof = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); rprof.location = (base_x, 900)
                rprof.mode = 'RADIUS'
                rprof.inputs['Resolution'].default_value = 8
                rprof.inputs['Radius'].default_value = 0.03

                rs = tree.nodes.new('GeometryNodeCurveToMesh'); rs.location = (base_x+300, 800)
                tree.links.new(rail_arc.outputs['Curve'], rs.inputs['Curve'])
                tree.links.new(rprof.outputs['Curve'], rs.inputs['Profile Curve'])
                parts.append(rs.outputs['Mesh'])

                # Vertical balusters from the deck up to the rail, spaced along the arc
                n_balu = max(4, n_planks // 2)
                deck_arc = tree.nodes.new('GeometryNodeCurvePrimitiveBezierSegment'); deck_arc.location = (base_x, 1100)
                deck_arc.inputs['Resolution'].default_value = 32
                deck_arc.inputs['Start'].default_value        = (-span/2, y_off, 0.05)
                deck_arc.inputs['Start Handle'].default_value = (-span/4, y_off, arc_lift + 0.05)
                deck_arc.inputs['End Handle'].default_value   = ( span/4, y_off, arc_lift + 0.05)
                deck_arc.inputs['End'].default_value          = ( span/2, y_off, 0.05)
                brs = tree.nodes.new('GeometryNodeResampleCurve'); brs.location = (base_x+200, 1100)
                try: brs.mode = 'COUNT'
                except Exception: pass
                brs.inputs['Count'].default_value = n_balu
                tree.links.new(deck_arc.outputs['Curve'], brs.inputs['Curve'])
                bp = tree.nodes.new('GeometryNodeCurveToPoints'); bp.location = (base_x+380, 1100)
                try: bp.mode = 'EVALUATED'
                except Exception: pass
                tree.links.new(brs.outputs['Curve'], bp.inputs['Curve'])
                balu = tree.nodes.new('GeometryNodeMeshCylinder'); balu.location = (base_x, 1300); color_node(balu, "house")
                balu.inputs['Vertices'].default_value = 6
                balu.inputs['Radius'].default_value = 0.025
                balu.inputs['Depth'].default_value = 0.45
                bt = tree.nodes.new('GeometryNodeTransform'); bt.location = (base_x+200, 1300)
                bt.inputs['Translation'].default_value = (0, 0, 0.225)
                tree.links.new(balu.outputs['Mesh'], bt.inputs['Geometry'])
                binst = tree.nodes.new('GeometryNodeInstanceOnPoints'); binst.location = (base_x+600, 1100)
                tree.links.new(bp.outputs['Points'], binst.inputs['Points'])
                tree.links.new(bt.outputs['Geometry'], binst.inputs['Instance'])
                brz = tree.nodes.new('GeometryNodeRealizeInstances'); brz.location = (base_x+820, 1100)
                tree.links.new(binst.outputs['Instances'], brz.inputs['Geometry'])
                parts.append(brz.outputs['Geometry'])

                # Giboshi (擬宝珠) finials on railing ends
                if show_giboshi:
                    for ex in (-span / 2, span / 2):
                        gb = tree.nodes.new('GeometryNodeMeshUVSphere'); gb.location = (base_x, 1500)
                        gb.inputs['Radius'].default_value = 0.055
                        gbt = tree.nodes.new('GeometryNodeTransform'); gbt.location = (base_x+200, 1500)
                        gbt.inputs['Translation'].default_value = (ex, y_off, arc_lift * 0.85 + 0.55)
                        gbt.inputs['Scale'].default_value = (1.0, 1.0, 1.35)
                        tree.links.new(gb.outputs['Mesh'], gbt.inputs['Geometry'])
                        color_node(gbt, "ornament")
                        parts.append(gbt.outputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+1000, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_zen_bridge")
    return tree, gin, gout

register_builder(
    "MEL_zen_bridge", build_zen_bridge_group,
    "Zen Bridge", "Zen builder (absorbed from monolith build_zen_bridge).",
    category="zen_kit")


def build_zen_stone_garden_group(group_name="MEL_zen_stone_garden"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        elif t == 'EnumProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    def _impl():
        """Karesansui (枯山水) - samon (砂紋) ripples + ishigumi stone groups."""
        size = PROPS.stone_garden_size
        n_stones = PROPS.stone_garden_stones
        n_ripples = PROPS.stone_garden_ripples
        parts = []

        # Sand base
        base = tree.nodes.new('GeometryNodeMeshCube'); base.location = (base_x, 0); color_node(base, "house")
        base.inputs['Size'].default_value = (size, size, 0.06)
        bt = tree.nodes.new('GeometryNodeTransform'); bt.location = (base_x+200, 0)
        bt.inputs['Translation'].default_value = (0, 0, 0.03)
        tree.links.new(base.outputs['Mesh'], bt.inputs['Geometry'])
        parts.append(bt.outputs['Geometry'])

        # Tsukubai (蹲踞) - stone washbasin at roji edge
        if getattr(PROPS, 'stone_garden_tsukubai', False):
            bx = size * 0.38
            by = -size * 0.32
            basin = tree.nodes.new('GeometryNodeMeshCylinder'); basin.location = (base_x, -200); color_node(basin, "house")
            basin.inputs['Vertices'].default_value = 16
            basin.inputs['Radius'].default_value = size * 0.09
            basin.inputs['Depth'].default_value = size * 0.07
            bt2 = tree.nodes.new('GeometryNodeTransform'); bt2.location = (base_x+200, -200)
            bt2.inputs['Translation'].default_value = (bx, by, size * 0.035)
            tree.links.new(basin.outputs['Mesh'], bt2.inputs['Geometry'])
            parts.append(bt2.outputs['Geometry'])
            rim = tree.nodes.new('GeometryNodeMeshTorus'); rim.location = (base_x, -350); color_node(rim, "house")
            rim.inputs['Major Radius'].default_value = size * 0.095
            rim.inputs['Minor Radius'].default_value = size * 0.018
            rim.inputs['Major Segments'].default_value = 24
            rim.inputs['Minor Segments'].default_value = 6
            rt = tree.nodes.new('GeometryNodeTransform'); rt.location = (base_x+200, -350)
            rt.inputs['Translation'].default_value = (bx, by, size * 0.07)
            rt.inputs['Scale'].default_value = (1.0, 1.0, 0.35)
            tree.links.new(rim.outputs['Mesh'], rt.inputs['Geometry'])
            parts.append(rt.outputs['Geometry'])

        # Concentric ripple rings - built as torus-like tubes
        for i in range(n_ripples):
            r = (i + 1) / max(1, n_ripples) * (size * 0.45)
            ring = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); ring.location = (base_x, 200 + i * 80); color_node(ring, "ornament")
            ring.mode = 'RADIUS'
            ring.inputs['Resolution'].default_value = 48
            ring.inputs['Radius'].default_value = r
            rt = tree.nodes.new('GeometryNodeTransform'); rt.location = (base_x+200, 200 + i * 80)
            rt.inputs['Translation'].default_value = (0, 0, 0.07)
            rt.inputs['Rotation'].default_value = (0, 0, 0)
            tree.links.new(ring.outputs['Curve'], rt.inputs['Geometry'])

            prof = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); prof.location = (base_x+400, 200 + i * 80)
            prof.mode = 'RADIUS'
            prof.inputs['Resolution'].default_value = 6
            prof.inputs['Radius'].default_value = 0.015

            s = tree.nodes.new('GeometryNodeCurveToMesh'); s.location = (base_x+600, 200 + i * 80)
            tree.links.new(rt.outputs['Geometry'], s.inputs['Curve'])
            tree.links.new(prof.outputs['Curve'], s.inputs['Profile Curve'])
            parts.append(s.outputs['Mesh'])

        # Stones (icospheres at varied positions)
        import random
        rng = random.Random(getattr(PROPS, 'sv_seed', 42))

        placed_count = 0
        # Sanzon-ishigumi (三尊石組) - Buddha triad: chūshu + waki/soe stones
        if PROPS.stone_garden_sansonseki:
            # chūshu (中主) master, waki-ishi (脇石) attendant, soe-ishi (添石) companion
            ctr_x = rng.uniform(-size * 0.15, size * 0.15)
            ctr_y = rng.uniform(-size * 0.15, size * 0.15)
            triad = [
                # (offset_x, offset_y, radius, scale_xyz)
                (0.0,            0.0,              size * 0.10, (1.0, 0.9, 1.5)),    # master - tall vertical
                (size * 0.20,    size * 0.10,      size * 0.07, (1.2, 0.8, 0.6)),    # attendant - flat low
                (-size * 0.12,   size * 0.18,      size * 0.05, (1.0, 0.9, 0.8)),    # companion - medium
            ]
            for j, (dx, dy, r, sc) in enumerate(triad):
                stone = tree.nodes.new('GeometryNodeMeshIcoSphere'); stone.location = (base_x, 1500 + placed_count * 100); color_node(stone, "house")
                stone.inputs['Subdivisions'].default_value = 2
                stone.inputs['Radius'].default_value = r
                st = tree.nodes.new('GeometryNodeTransform'); st.location = (base_x+200, 1500 + placed_count * 100)
                st.inputs['Translation'].default_value = (ctr_x + dx, ctr_y + dy, 0.06 + r * sc[2] * 0.5)
                st.inputs['Scale'].default_value = sc
                st.inputs['Rotation'].default_value = (0, 0, rng.uniform(0, math.tau))
                tree.links.new(stone.outputs['Mesh'], st.inputs['Geometry'])
                parts.append(st.outputs['Geometry'])
                placed_count += 1

        # Additional scattered stones
        remaining = max(0, n_stones - placed_count)
        for i in range(remaining):
            # Place avoiding the triad area
            for _attempt in range(8):
                x = rng.uniform(-size * 0.4, size * 0.4)
                y = rng.uniform(-size * 0.4, size * 0.4)
                if PROPS.stone_garden_sansonseki:
                    if math.hypot(x - ctr_x, y - ctr_y) > size * 0.3: break
                else: break
            stone_r = rng.uniform(size * 0.04, size * 0.10)
            stone = tree.nodes.new('GeometryNodeMeshIcoSphere'); stone.location = (base_x, 1500 + placed_count * 100); color_node(stone, "house")
            stone.inputs['Subdivisions'].default_value = 2
            stone.inputs['Radius'].default_value = stone_r
            st = tree.nodes.new('GeometryNodeTransform'); st.location = (base_x+200, 1500 + placed_count * 100)
            st.inputs['Translation'].default_value = (x, y, 0.06 + stone_r * 0.6)
            st.inputs['Scale'].default_value = (1.0, rng.uniform(0.7, 1.0), rng.uniform(0.5, 0.9))
            st.inputs['Rotation'].default_value = (0, 0, rng.uniform(0, math.tau))
            tree.links.new(stone.outputs['Mesh'], st.inputs['Geometry'])
            parts.append(st.outputs['Geometry'])
            placed_count += 1

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+1000, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    # ----------------------------------------------------------------------
    # ADVANCED WALL BUILDERS (multi-pane, arched, bay)
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_zen_stone_garden")
    return tree, gin, gout

register_builder(
    "MEL_zen_stone_garden", build_zen_stone_garden_group,
    "Zen Stone Garden", "Zen builder (absorbed from monolith build_zen_stone_garden).",
    category="zen_kit")


# 7 builders registered
