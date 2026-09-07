"""MEL East Asian builders — absorbed from the monolith (P2 family 3).

9 generator builders. Params-as-values port: PROPS namespace built from
monolith bpy.props defaults at build time (rebuild-on-change semantics).
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




BUILDER_PARAM_DEFAULTS = {
    "base_radius": {"type": "FloatProperty", "default": 1.2, "min": 0.1, "max": 10.0},
    "height": {"type": "FloatProperty", "default": 5.0, "min": 0.5, "max": 30.0},
    "pagoda_base_radius": {"type": "FloatProperty", "default": 1.2, "min": 0.3, "max": 8.0},
    "pagoda_roof_overhang": {"type": "FloatProperty", "default": 0.45, "min": 0.1, "max": 1.5},
    "pagoda_taper": {"type": "FloatProperty", "default": 0.85, "min": 0.5, "max": 0.99},
    "pagoda_tier_height": {"type": "FloatProperty", "default": 1.0, "min": 0.4, "max": 3.0},
    "pagoda_tiers": {"type": "IntProperty", "default": 3, "min": 2, "max": 7},
    "recursion_depth": {"type": "IntProperty", "default": 3, "min": 1, "max": 6},
    "teahouse_depth": {"type": "FloatProperty", "default": 3.0, "min": 1.5, "max": 8.0},
    "teahouse_height": {"type": "FloatProperty", "default": 2.5, "min": 1.5, "max": 6.0},
    "teahouse_pitch_factor": {"type": "FloatProperty", "default": 0.6, "min": 0.2, "max": 1.5},
    "teahouse_width": {"type": "FloatProperty", "default": 3.0, "min": 1.5, "max": 8.0},
}


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



def build_cn_dougong_group(group_name="MEL_cn_dougong"):
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
        """Chinese dougong (斗拱) bracket cluster: cap-block (dou) + radial
        bracket arms (gong) stacked in tiers. Uses extruded filled curves so
        the geometry is real beams, not cones."""
        pieces = []
        base_x = -1200
        cap_size = max(0.25, getattr(PROPS, 'base_radius', 1.0) * 0.55)
        tiers = max(1, min(4, getattr(PROPS, 'recursion_depth', 2)))
        arm_len = cap_size * 3.2
        arm_thk = cap_size * 0.32
        arm_h   = cap_size * 0.42
        cur_z = 0.0
        import math
        for tier in range(tiers):
            # Cap block (dou): square prism via curve->fill->extrude
            rect = _node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x, 200 + tier * 250))
            rect.inputs['Resolution'].default_value = 4
            rect.inputs['Radius'].default_value = cap_size
            rrot = _node(tree, 'GeometryNodeTransform', (base_x + 200, 200 + tier * 250))
            rrot.inputs['Rotation'].default_value = (0, 0, 0.7854)  # 45deg -> square
            _link(tree, rect.outputs['Curve'], rrot.inputs['Geometry'])
            fill = _safe_node(tree, 'GeometryNodeFillCurve', (base_x + 400, 200 + tier * 250))
            if fill:
                try: fill.mode = 'NGONS'
                except Exception: pass
                _link(tree, rrot.outputs['Geometry'], fill.inputs['Curve'])
            ext = _safe_node(tree, 'GeometryNodeExtrudeMesh', (base_x + 600, 200 + tier * 250))
            if ext and fill:
                ext.mode = 'FACES'
                ext.inputs['Offset Scale'].default_value = cap_size * 0.65
                _link(tree, fill.outputs['Mesh'], ext.inputs['Mesh'])
            tr_dou = _node(tree, 'GeometryNodeTransform', (base_x + 800, 200 + tier * 250))
            tr_dou.inputs['Translation'].default_value = (0, 0, cur_z)
            if ext: _link(tree, ext.outputs['Mesh'], tr_dou.inputs['Geometry'])
            color_node(rect, "ornament"); color_node(rrot, "ornament"); color_node(tr_dou, "ornament")
            if ext: color_node(ext, "ornament")
            pieces.append(tr_dou.outputs['Geometry'])
            cur_z += cap_size * 0.7
            # 4 (or 8 alternating) bracket arms radiating outward
            # v2.49: arms are CurvePrimitiveLine sweeps with rectangular profile
            # (ogee/round cross-section) instead of MeshCubes - real AAA bracket beams
            n_arms = 4 if (tier % 2 == 0) else 8
            arm_rect_prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveQuadrilateral',
                                       (base_x - 300, -200 - tier * 300))
            if arm_rect_prof:
                try:
                    arm_rect_prof.mode = 'RECTANGLE'
                    arm_rect_prof.inputs['Width'].default_value  = arm_h   # cross-section height
                    arm_rect_prof.inputs['Height'].default_value = arm_thk  # cross-section depth
                except Exception:
                    arm_rect_prof = None
            color_node(arm_rect_prof, "tower") if arm_rect_prof else None

            for a in range(n_arms):
                ang = (a / n_arms) * math.tau
                cos_a = math.cos(ang)
                sin_a = math.sin(ang)
                # Arm extends from center (cap_size*0.6) to arm_len/2 radius
                x0 = cos_a * cap_size * 0.6
                y0 = sin_a * cap_size * 0.6
                x1 = cos_a * (arm_len * 0.5)
                y1 = sin_a * (arm_len * 0.5)
                z_arm = cur_z + arm_h * 0.5

                arm_line = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine',
                                      (base_x, -200 - tier * 300 - a * 80))
                if arm_line:
                    try:
                        arm_line.inputs['Start'].default_value = (x0, y0, z_arm)
                        arm_line.inputs['End'].default_value   = (x1, y1, z_arm)
                    except Exception: pass
                    color_node(arm_line, "tower")
                    if arm_rect_prof:
                        arm_sw = _safe_node(tree, 'GeometryNodeCurveToMesh',
                                            (base_x + 250, -200 - tier * 300 - a * 80))
                        if arm_sw:
                            _link(tree, arm_line.outputs['Curve'], arm_sw.inputs['Curve'])
                            _link(tree, arm_rect_prof.outputs['Curve'], arm_sw.inputs['Profile Curve'])
                            try: arm_sw.inputs['Fill Caps'].default_value = True
                            except Exception: pass
                            color_node(arm_sw, "tower")
                            pieces.append(arm_sw.outputs['Mesh'])

                # Small corbel block at arm tip (dou at end of gong)
                tip_cap = _safe_node(tree, 'GeometryNodeMeshCube',
                                     (base_x, -350 - tier * 300 - a * 80))
                if tip_cap:
                    tip_size = arm_thk * 1.8
                    try: tip_cap.inputs['Size'].default_value = (tip_size, tip_size, arm_h * 0.6)
                    except Exception: pass
                    tip_tr = _safe_node(tree, 'GeometryNodeTransform',
                                        (base_x + 200, -350 - tier * 300 - a * 80))
                    if tip_tr:
                        try:
                            tip_tr.inputs['Translation'].default_value = (x1 * 0.9, y1 * 0.9,
                                                                           z_arm + arm_h * 0.6)
                        except Exception: pass
                        _link(tree, tip_cap.outputs['Mesh'], tip_tr.inputs['Geometry'])
                        color_node(tip_cap, "ornament"); color_node(tip_tr, "ornament")
                        pieces.append(tip_tr.outputs['Geometry'])
            cur_z += arm_h * 1.05
        # Final top cap (slightly smaller)
        top_cap = _node(tree, 'GeometryNodeMeshCube', (base_x, 1500))
        top_size = cap_size * 1.3
        top_cap.inputs['Size'].default_value = (top_size, top_size, cap_size * 0.35)
        ttr = _node(tree, 'GeometryNodeTransform', (base_x + 250, 1500))
        ttr.inputs['Translation'].default_value = (0, 0, cur_z + cap_size * 0.18)
        _link(tree, top_cap.outputs['Mesh'], ttr.inputs['Geometry'])
        color_node(top_cap, "ornament"); color_node(ttr, "ornament")
        pieces.append(ttr.outputs['Geometry'])
        # Join everything
        join = _node(tree, 'GeometryNodeJoinGeometry', (base_x + 1100, 0))
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_cn_dougong")
    return tree, gin, gout

register_builder(
    "MEL_cn_dougong", build_cn_dougong_group,
    "Cn Dougong", "East Asian builder (absorbed from monolith build_cn_dougong).",
    category="asian")


def build_cn_tiered_pagoda_group(group_name="MEL_cn_tiered_pagoda"):
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
        """Chinese tiered pagoda: octagonal-plan body stacked N tiers, each tier
        wearing a heavily-flared eave built from a bezier-swept circle. Finial
        spire at the top."""
        pieces = []
        base_x = -1000
        tiers = max(2, min(9, getattr(PROPS, 'pagoda_tiers', 5)))
        base_r = max(0.8, getattr(PROPS, 'pagoda_base_radius', 3.0))
        tier_h = max(0.8, getattr(PROPS, 'pagoda_tier_height', 2.0))
        overhang = max(0.4, getattr(PROPS, 'pagoda_roof_overhang', 0.8))
        taper = max(0.5, min(0.95, getattr(PROPS, 'pagoda_taper', 0.78)))
        cur_z = 0.0
        cur_r = base_r
        for tier in range(tiers):
            # Octagonal column (body of this tier) - curve->fill->extrude
            oct_c = _node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x, 200 + tier * 220))
            oct_c.inputs['Resolution'].default_value = 8
            oct_c.inputs['Radius'].default_value = cur_r
            oct_fill = _safe_node(tree, 'GeometryNodeFillCurve', (base_x + 200, 200 + tier * 220))
            if oct_fill:
                try: oct_fill.mode = 'NGONS'
                except Exception: pass
                _link(tree, oct_c.outputs['Curve'], oct_fill.inputs['Curve'])
            oct_ext = _safe_node(tree, 'GeometryNodeExtrudeMesh', (base_x + 400, 200 + tier * 220))
            if oct_ext and oct_fill:
                oct_ext.mode = 'FACES'
                oct_ext.inputs['Offset Scale'].default_value = tier_h
                _link(tree, oct_fill.outputs['Mesh'], oct_ext.inputs['Mesh'])
            body_tr = _node(tree, 'GeometryNodeTransform', (base_x + 600, 200 + tier * 220))
            body_tr.inputs['Translation'].default_value = (0, 0, cur_z)
            if oct_ext: _link(tree, oct_ext.outputs['Mesh'], body_tr.inputs['Geometry'])
            color_node(oct_c, "tower"); color_node(body_tr, "tower")
            if oct_ext: color_node(oct_ext, "tower")
            pieces.append(body_tr.outputs['Geometry'])
            # Flared eave: bezier arch swept around - approximate with a torus
            # rotated horizontally + scaled. Use a torus knot mesh for richness.
            eave_r = cur_r + overhang
            eave = _safe_node(tree, 'GeometryNodeMeshTorus', (base_x, -250 - tier * 220))
            if eave:
                try:
                    eave.inputs['Major Radius'].default_value = eave_r
                    eave.inputs['Minor Radius'].default_value = overhang * 0.35
                    eave.inputs['Major Segments'].default_value = 48
                    eave.inputs['Minor Segments'].default_value = 8
                except Exception:
                    pass
                etr = _node(tree, 'GeometryNodeTransform', (base_x + 250, -250 - tier * 220))
                etr.inputs['Translation'].default_value = (0, 0, cur_z + tier_h)
                etr.inputs['Scale'].default_value = (1.0, 1.0, 0.35)  # squash -> flat-flared
                _link(tree, eave.outputs['Mesh'], etr.inputs['Geometry'])
                color_node(eave, "ornament"); color_node(etr, "ornament")
                pieces.append(etr.outputs['Geometry'])
            # Lid disc on top (octagonal again, thinner)
            lid_c = _node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x, 1300 - tier * 100))
            lid_c.inputs['Resolution'].default_value = 8
            lid_c.inputs['Radius'].default_value = eave_r * 0.95
            lid_fill = _safe_node(tree, 'GeometryNodeFillCurve', (base_x + 200, 1300 - tier * 100))
            if lid_fill:
                try: lid_fill.mode = 'NGONS'
                except Exception: pass
                _link(tree, lid_c.outputs['Curve'], lid_fill.inputs['Curve'])
            lid_ext = _safe_node(tree, 'GeometryNodeExtrudeMesh', (base_x + 400, 1300 - tier * 100))
            if lid_ext and lid_fill:
                lid_ext.mode = 'FACES'
                lid_ext.inputs['Offset Scale'].default_value = overhang * 0.18
                _link(tree, lid_fill.outputs['Mesh'], lid_ext.inputs['Mesh'])
            lid_tr = _node(tree, 'GeometryNodeTransform', (base_x + 600, 1300 - tier * 100))
            lid_tr.inputs['Translation'].default_value = (0, 0, cur_z + tier_h)
            if lid_ext: _link(tree, lid_ext.outputs['Mesh'], lid_tr.inputs['Geometry'])
            color_node(lid_c, "ornament"); color_node(lid_tr, "ornament")
            pieces.append(lid_tr.outputs['Geometry'])
            cur_z += tier_h + overhang * 0.18
            cur_r *= taper
        # Finial spire: tall thin curve-swept cone-equivalent
        spire = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (base_x, -1500))
        if spire:
            try:
                spire.inputs['Start'].default_value = (0, 0, cur_z)
                spire.inputs['End'].default_value   = (0, 0, cur_z + tier_h * 1.4)
            except Exception:
                pass
            prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x, -1700))
            if prof:
                try:
                    prof.inputs['Radius'].default_value = base_r * 0.08
                    prof.inputs['Resolution'].default_value = 12
                except Exception:
                    pass
                sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 250, -1500))
                if sw:
                    _link(tree, spire.outputs['Curve'], sw.inputs['Curve'])
                    _link(tree, prof.outputs['Curve'], sw.inputs['Profile Curve'])
                    color_node(sw, "ornament")
                    pieces.append(sw.outputs['Mesh'])
            # Add 3 rings as finial bells
            for k in range(3):
                ring = _safe_node(tree, 'GeometryNodeMeshTorus', (base_x, -1900 - k * 150))
                if ring is None: continue
                try:
                    ring.inputs['Major Radius'].default_value = base_r * (0.18 - k * 0.04)
                    ring.inputs['Minor Radius'].default_value = base_r * 0.025
                    ring.inputs['Major Segments'].default_value = 24
                    ring.inputs['Minor Segments'].default_value = 6
                except Exception:
                    continue
                rtr = _node(tree, 'GeometryNodeTransform', (base_x + 250, -1900 - k * 150))
                rtr.inputs['Translation'].default_value = (0, 0, cur_z + 0.3 + k * 0.4)
                _link(tree, ring.outputs['Mesh'], rtr.inputs['Geometry'])
                color_node(ring, "ornament"); color_node(rtr, "ornament")
                pieces.append(rtr.outputs['Geometry'])
        join = _node(tree, 'GeometryNodeJoinGeometry', (base_x + 1100, 0))
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_cn_tiered_pagoda")
    return tree, gin, gout

register_builder(
    "MEL_cn_tiered_pagoda", build_cn_tiered_pagoda_group,
    "Cn Tiered Pagoda", "East Asian builder (absorbed from monolith build_cn_tiered_pagoda).",
    category="asian")


def build_kr_hanok_group(group_name="MEL_kr_hanok"):
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
        """Korean hanok (한옥): elevated stone platform, wooden column grid,
        plastered walls, low-pitched gable roof with curved-up corners.
        Reuses teahouse_width/depth/height/pitch_factor properties."""
        pieces = []
        base_x = -1100
        W = max(2.0, getattr(PROPS, 'teahouse_width', 6.0))
        D = max(2.0, getattr(PROPS, 'teahouse_depth', 4.5))
        H = max(1.5, getattr(PROPS, 'teahouse_height', 3.0))
        pitch = max(0.25, getattr(PROPS, 'teahouse_pitch_factor', 0.4))  # lower than Japanese
        # === Elevated stone platform (ondol base) ===
        plat = _node(tree, 'GeometryNodeMeshCube', (base_x, 200))
        plat.inputs['Size'].default_value = (W * 1.15, D * 1.15, 0.45)
        ptr = _node(tree, 'GeometryNodeTransform', (base_x + 200, 200))
        ptr.inputs['Translation'].default_value = (0, 0, 0.225)
        _link(tree, plat.outputs['Mesh'], ptr.inputs['Geometry'])
        color_node(plat, "input"); color_node(ptr, "input")
        pieces.append(ptr.outputs['Geometry'])
        # === Body: column-and-wall - 4 corner columns + plastered wall fills ===
        col_r = 0.12
        col_h = H
        import math
        corners = [(-W/2, -D/2), (W/2, -D/2), (-W/2, D/2), (W/2, D/2)]
        for i, (cx, cy) in enumerate(corners):
            col = _node(tree, 'GeometryNodeMeshCylinder', (base_x, -200 - i * 100))
            col.inputs['Radius'].default_value = col_r
            col.inputs['Depth'].default_value  = col_h
            col.inputs['Vertices'].default_value = 12
            ctr = _node(tree, 'GeometryNodeTransform', (base_x + 200, -200 - i * 100))
            ctr.inputs['Translation'].default_value = (cx, cy, 0.45 + col_h * 0.5)
            _link(tree, col.outputs['Mesh'], ctr.inputs['Geometry'])
            color_node(col, "tower"); color_node(ctr, "tower")
            pieces.append(ctr.outputs['Geometry'])
        # Plastered wall slabs - thin boxes between corners (front/back/sides)
        wall_thk = 0.08
        for orient, (sx, sy, tx, ty) in enumerate([
            (W - col_r * 4, wall_thk, 0, -D/2),  # front (will be split for door)
            (W - col_r * 4, wall_thk, 0,  D/2),  # back
            (wall_thk, D - col_r * 4, -W/2, 0),  # left
            (wall_thk, D - col_r * 4,  W/2, 0),  # right
        ]):
            wall = _node(tree, 'GeometryNodeMeshCube', (base_x, -800 - orient * 150))
            wall.inputs['Size'].default_value = (sx, sy, col_h * 0.9)
            wtr = _node(tree, 'GeometryNodeTransform', (base_x + 200, -800 - orient * 150))
            wtr.inputs['Translation'].default_value = (tx, ty, 0.45 + col_h * 0.45)
            _link(tree, wall.outputs['Mesh'], wtr.inputs['Geometry'])
            color_node(wall, "input"); color_node(wtr, "input")
            pieces.append(wtr.outputs['Geometry'])
        # === Low-pitched gable roof - two slanted slabs meeting at ridge ===
        roof_z_base = 0.45 + col_h
        ridge_h = pitch * (D * 0.5)   # low pitch
        # Build roof from a bezier ridge curve swept with a wide profile
        # Simpler: two rectangular slabs tilted to meet at ridge
        overhang = 0.55  # extended eaves Korean-style, mid between China & Japan
        slab_l = W + overhang * 2.0          # ridge length (X)
        half_y = D / 2 + overhang            # eave reach (Y)
        # Curved gable roof from a deformed grid - ridge along X, concave slopes
        # in Y, with the four corners sweeping up (cheoma curve).
        gres = 28
        rgrid = _node(tree, 'GeometryNodeMeshGrid', (base_x, -1600))
        rgrid.inputs['Size X'].default_value = slab_l
        rgrid.inputs['Size Y'].default_value = half_y * 2.0
        rgrid.inputs['Vertices X'].default_value = gres
        rgrid.inputs['Vertices Y'].default_value = gres
        color_node(rgrid, "ornament")
        rpos = _node(tree, 'GeometryNodeInputPosition', (base_x, -1380))
        rsep = tree.nodes.new('ShaderNodeSeparateXYZ'); rsep.location = (base_x+180, -1380)
        _link(tree, rpos.outputs['Position'], rsep.inputs['Vector'])
        # n = |y| / half_y   (0 at ridge, 1 at eave)
        ny = tree.nodes.new('ShaderNodeMath'); ny.location = (base_x+360, -1320); ny.operation = 'ABSOLUTE'
        _link(tree, rsep.outputs['Y'], ny.inputs[0])
        nn = tree.nodes.new('ShaderNodeMath'); nn.location = (base_x+540, -1320); nn.operation = 'DIVIDE'
        nn.inputs[1].default_value = max(0.001, half_y)
        _link(tree, ny.outputs[0], nn.inputs[0])
        n1 = tree.nodes.new('ShaderNodeMath'); n1.location = (base_x+720, -1320); n1.operation = 'SUBTRACT'
        n1.inputs[0].default_value = 1.0
        _link(tree, nn.outputs[0], n1.inputs[1])           # 1 - n
        np = tree.nodes.new('ShaderNodeMath'); np.location = (base_x+900, -1320); np.operation = 'POWER'
        np.inputs[1].default_value = 1.7                   # concave sag
        _link(tree, n1.outputs[0], np.inputs[0])
        nz = tree.nodes.new('ShaderNodeMath'); nz.location = (base_x+1080, -1320); nz.operation = 'MULTIPLY'
        nz.inputs[1].default_value = ridge_h
        _link(tree, np.outputs[0], nz.inputs[0])
        # Corner upturn: lift where both |x| (near gable end) and |y| (near eave) are large
        cx = tree.nodes.new('ShaderNodeMath'); cx.location = (base_x+360, -1500); cx.operation = 'ABSOLUTE'
        _link(tree, rsep.outputs['X'], cx.inputs[0])
        cxn = tree.nodes.new('ShaderNodeMath'); cxn.location = (base_x+540, -1500); cxn.operation = 'DIVIDE'
        cxn.inputs[1].default_value = max(0.001, slab_l * 0.5)
        _link(tree, cx.outputs[0], cxn.inputs[0])
        cxp = tree.nodes.new('ShaderNodeMath'); cxp.location = (base_x+720, -1500); cxp.operation = 'POWER'
        cxp.inputs[1].default_value = 5.0
        _link(tree, cxn.outputs[0], cxp.inputs[0])
        cyp = tree.nodes.new('ShaderNodeMath'); cyp.location = (base_x+720, -1620); cyp.operation = 'POWER'
        cyp.inputs[1].default_value = 4.0
        _link(tree, nn.outputs[0], cyp.inputs[0])
        cmul = tree.nodes.new('ShaderNodeMath'); cmul.location = (base_x+900, -1560); cmul.operation = 'MULTIPLY'
        _link(tree, cxp.outputs[0], cmul.inputs[0]); _link(tree, cyp.outputs[0], cmul.inputs[1])
        camp = tree.nodes.new('ShaderNodeMath'); camp.location = (base_x+1080, -1560); camp.operation = 'MULTIPLY'
        camp.inputs[1].default_value = ridge_h * 0.55
        _link(tree, cmul.outputs[0], camp.inputs[0])
        rzsum = tree.nodes.new('ShaderNodeMath'); rzsum.location = (base_x+1280, -1400); rzsum.operation = 'ADD'
        _link(tree, nz.outputs[0], rzsum.inputs[0]); _link(tree, camp.outputs[0], rzsum.inputs[1])
        rzvec = tree.nodes.new('ShaderNodeCombineXYZ'); rzvec.location = (base_x+1460, -1400)
        _link(tree, rzsum.outputs[0], rzvec.inputs['Z'])
        rsetp = _node(tree, 'GeometryNodeSetPosition', (base_x+1640, -1600))
        _link(tree, rgrid.outputs['Mesh'], rsetp.inputs['Geometry'])
        _link(tree, rzvec.outputs['Vector'], rsetp.inputs['Offset'])
        rext = _safe_node(tree, 'GeometryNodeExtrudeMesh', (base_x+1840, -1600))
        if rext:
            rext.mode = 'FACES'
            try: rext.inputs['Offset Scale'].default_value = -0.1
            except Exception: pass
            _link(tree, rsetp.outputs['Geometry'], rext.inputs['Mesh'])
            roof_geo_out = rext.outputs['Mesh']
        else:
            roof_geo_out = rsetp.outputs['Geometry']
        rtr = _node(tree, 'GeometryNodeTransform', (base_x+2040, -1600))
        rtr.inputs['Translation'].default_value = (0, 0, roof_z_base)
        _link(tree, roof_geo_out, rtr.inputs['Geometry'])
        color_node(rsetp, "ornament"); color_node(rtr, "ornament")
        pieces.append(rtr.outputs['Geometry'])
        # Gable end triangles (front/back) - extruded filled triangle curves
        for sign_y in (-1, 1):
            tri = _node(tree, 'GeometryNodeCurvePrimitiveLine', (base_x, -2200 + (sign_y + 1) * 80))
            # Use a 3-resolution curve circle = triangle, then extrude
            tri_c = _node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x, -2200 + (sign_y + 1) * 80))
            tri_c.inputs['Resolution'].default_value = 3
            tri_c.inputs['Radius'].default_value = ridge_h
            ttr_c = _node(tree, 'GeometryNodeTransform', (base_x + 200, -2200 + (sign_y + 1) * 80))
            ttr_c.inputs['Scale'].default_value = (W * 0.5 / max(0.001, ridge_h), 1.0, 1.0)
            ttr_c.inputs['Rotation'].default_value = (1.5708, 0, 0)
            ttr_c.inputs['Translation'].default_value = (0, sign_y * D * 0.5, roof_z_base + ridge_h * 0.5)
            _link(tree, tri_c.outputs['Curve'], ttr_c.inputs['Geometry'])
            gfill = _safe_node(tree, 'GeometryNodeFillCurve', (base_x + 400, -2200 + (sign_y + 1) * 80))
            if gfill:
                try: gfill.mode = 'NGONS'
                except Exception: pass
                _link(tree, ttr_c.outputs['Geometry'], gfill.inputs['Curve'])
                gext = _safe_node(tree, 'GeometryNodeExtrudeMesh', (base_x + 600, -2200 + (sign_y + 1) * 80))
                if gext:
                    gext.mode = 'FACES'
                    gext.inputs['Offset Scale'].default_value = 0.08
                    _link(tree, gfill.outputs['Mesh'], gext.inputs['Mesh'])
                    color_node(gext, "input")
                    pieces.append(gext.outputs['Mesh'])
            color_node(tri_c, "input"); color_node(ttr_c, "input")
        join = _node(tree, 'GeometryNodeJoinGeometry', (base_x + 1100, 0))
        for p in pieces:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        return join.outputs['Geometry']


    # ======================================================================
    # * CASTLE / CITY PIECE LIBRARY (v2.23) - Layer 1 additions
    # Composable architectural pieces designed to feed the procedural city /
    # castle system. Geometry is built from curve-fill-extrude or curve sweeps
    # so every silhouette is real beveled mesh, not cones.
    # ======================================================================

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_kr_hanok")
    return tree, gin, gout

register_builder(
    "MEL_kr_hanok", build_kr_hanok_group,
    "Kr Hanok", "East Asian builder (absorbed from monolith build_kr_hanok).",
    category="asian")


def build_cn_moon_gate_group(group_name="MEL_cn_moon_gate"):
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
        """Circular Chinese garden doorway set in a wall."""
        r = max(1.0, getattr(PROPS, 'base_radius', 1.0) * 1.8)
        W = r * 3.6
        H = r * 2.8
        T = 0.3
        pieces = []
        # Wall slab
        pieces.append(_move(tree, _cube(tree, (base_x, 200), W, T, H, "tower"),
                             (base_x + 200, 200), translation=(0, 0, H / 2), label="tower"))
        # The circle "frame" - torus rotated to face camera
        frame = _safe_node(tree, 'GeometryNodeMeshTorus', (base_x, -400))
        if frame:
            try:
                frame.inputs['Major Radius'].default_value = r
                frame.inputs['Minor Radius'].default_value = T * 0.65
                frame.inputs['Major Segments'].default_value = 48
                frame.inputs['Minor Segments'].default_value = 8
            except Exception:
                pass
            pieces.append(_move(tree, frame.outputs['Mesh'], (base_x + 200, -400),
                                 translation=(0, 0, H * 0.4),
                                 rotation=(1.5708, 0, 0), label="ornament"))
            color_node(frame, "ornament")
        # Coping stones along top of wall (ornament strip)
        pieces.append(_move(tree, _cube(tree, (base_x, -1000), W + 0.4, T + 0.2, 0.18, "ornament"),
                             (base_x + 200, -1000),
                             translation=(0, 0, H + 0.09), label="ornament"))
        # Base plinth
        pieces.append(_move(tree, _cube(tree, (base_x, -1300), W + 0.3, T + 0.3, 0.25, "house"),
                             (base_x + 200, -1300),
                             translation=(0, 0, 0.125), label="house"))
        return _join_all(tree, pieces, (base_x + 1100, 0))


    # ─── CN PAILOU ──────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_cn_moon_gate")
    return tree, gin, gout

register_builder(
    "MEL_cn_moon_gate", build_cn_moon_gate_group,
    "Cn Moon Gate", "East Asian builder (absorbed from monolith build_cn_moon_gate).",
    category="asian")


def build_cn_pailou_group(group_name="MEL_cn_pailou"):
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
        """Chinese memorial archway: 4 pillars + 3 stacked decorative roofs."""
        W = max(3.5, getattr(PROPS, 'base_radius', 1.0) * 4.0)
        H = max(4.0, getattr(PROPS, 'height', 5.0) * 1.4)
        pillar_w = 0.4
        pillar_pitch = W / 3
        pieces = []
        # 4 vertical pillars
        for i in range(4):
            x = -W / 2 + i * pillar_pitch
            pieces.append(_move(tree,
                                 _cube(tree, (base_x, 200 - i * 100), pillar_w, pillar_w, H, "tower"),
                                 (base_x + 200, 200 - i * 100),
                                 translation=(x, 0, H / 2), label="tower"))
        # 3 stacked curved roofs (decreasing width going up) - real swept eaves
        roof_z = H + 0.1
        for tier in range(3):
            rw = W * (1.0 - tier * 0.15)
            rd = 1.4 - tier * 0.12
            ridge_h = 0.45 + tier * 0.05
            roof_geo = _curved_roof(tree, (base_x, -500 - tier * 700),
                                    size_x=rw, size_y=rd, ridge_h=ridge_h,
                                    base_z=roof_z, pitch=1.5, hip=False,
                                    eave_flip=0.5, thickness=-0.09, label="ornament")
            pieces.append(roof_geo)
            roof_z += ridge_h + 0.25
        # Central plaque (inscribed panel)
        pieces.append(_move(tree, _cube(tree, (base_x, -1400), W * 0.55, 0.1, H * 0.18, "ornament"),
                             (base_x + 200, -1400),
                             translation=(0, 0, H * 1.05), label="ornament"))
        return _join_all(tree, pieces, (base_x + 1300, 0))


    # ─── STREET LAMP ────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_cn_pailou")
    return tree, gin, gout

register_builder(
    "MEL_cn_pailou", build_cn_pailou_group,
    "Cn Pailou", "East Asian builder (absorbed from monolith build_cn_pailou).",
    category="asian")


def build_cn_ting_pavilion_group(group_name="MEL_cn_ting_pavilion"):
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
        """Chinese garden pavilion (亭): hexagonal stone base + 6 columns +
        upturned hex roof + finial."""
        import math
        R = max(1.2, getattr(PROPS, 'base_radius', 1.0) * 1.6)
        H = max(2.5, getattr(PROPS, 'height', 3.5))
        pieces = []
        # Hex base platform
        hex_c = _cv_circle(tree, (base_x, 200), R * 1.1, 6)
        base_m = _fill_extrude(tree, hex_c.outputs['Curve'] if hex_c else None,
                                (base_x + 200, 200), (base_x + 400, 200), 0.25, "tower")
        pieces.append(_move(tree, base_m, (base_x + 600, 200), translation=(0, 0, 0.12),
                             label="tower"))
        # 6 columns at hex vertices
        for i in range(6):
            ang = (i / 6) * math.tau
            col = _node(tree, 'GeometryNodeMeshCylinder', (base_x, -200 - i * 80))
            col.inputs['Radius'].default_value = 0.1
            col.inputs['Depth'].default_value = H
            col.inputs['Vertices'].default_value = 12
            pieces.append(_move(tree, col.outputs['Mesh'], (base_x + 220, -200 - i * 80),
                                 translation=(math.cos(ang) * R, math.sin(ang) * R, H / 2 + 0.25),
                                 label="tower"))
            color_node(col, "tower")
        # ---- Upturned hexagonal roof (curved corner ridge beams) ----------
        roof_base_z = H + 0.25
        eave_R = R * 1.4
        roof_rise = R * 0.85
        apex_z = roof_base_z + roof_rise
        # Thin flared hex eave disc
        eave_c = _cv_circle(tree, (base_x, -900), eave_R, 6)
        eave_m = _fill_extrude(tree, eave_c.outputs['Curve'] if eave_c else None,
                                (base_x + 200, -900), (base_x + 400, -900), 0.1, "house")
        pieces.append(_move(tree, eave_m, (base_x + 600, -900),
                             translation=(0, 0, roof_base_z), label="house"))
        # Mid hex tier (raised, narrower) -> stepped concave silhouette
        mid_c = _cv_circle(tree, (base_x, -1150), eave_R * 0.62, 6)
        mid_m = _fill_extrude(tree, mid_c.outputs['Curve'] if mid_c else None,
                               (base_x + 200, -1150), (base_x + 400, -1150), 0.1, "house")
        pieces.append(_move(tree, mid_m, (base_x + 600, -1150),
                             translation=(0, 0, roof_base_z + roof_rise * 0.5), label="house"))
        # Apex cap hex
        cap_c = _cv_circle(tree, (base_x, -1400), eave_R * 0.22, 6)
        cap_m = _fill_extrude(tree, cap_c.outputs['Curve'] if cap_c else None,
                               (base_x + 200, -1400), (base_x + 400, -1400), 0.12, "ornament")
        pieces.append(_move(tree, cap_m, (base_x + 600, -1400),
                             translation=(0, 0, apex_z - 0.06), label="ornament"))
        # 6 upturned hip ridge beams from apex to each hex corner
        ridge_prof = _make_circle_profile(tree, 0.055, 6, (base_x, -1650), PROPS)
        for i in range(6):
            ang = (i / 6.0) * math.tau + math.radians(30)  # align to hex corners
            ex, ey = math.cos(ang) * eave_R, math.sin(ang) * eave_R
            rb = tree.nodes.new('GeometryNodeCurvePrimitiveBezierSegment'); rb.location = (base_x, -1900 - i * 90)
            rb.inputs['Start'].default_value = (0, 0, apex_z)
            rb.inputs['End'].default_value = (ex, ey, roof_base_z + roof_rise * 0.12)
            rb.inputs['Start Handle'].default_value = (ex * 0.3, ey * 0.3, apex_z)
            rb.inputs['End Handle'].default_value = (ex * 0.8, ey * 0.8, roof_base_z + roof_rise * 0.55)
            rsw = tree.nodes.new('GeometryNodeCurveToMesh'); rsw.location = (base_x + 250, -1900 - i * 90); color_node(rsw, "ornament")
            tree.links.new(rb.outputs['Curve'], rsw.inputs['Curve'])
            if ridge_prof is not None:
                tree.links.new(ridge_prof.outputs['Curve'], rsw.inputs['Profile Curve'])
            rsw.inputs['Fill Caps'].default_value = True
            pieces.append(rsw.outputs['Mesh'])
        # Finial sphere on top
        fin = _safe_node(tree, 'GeometryNodeMeshIcoSphere', (base_x, -2500))
        if fin:
            fin.inputs['Radius'].default_value = 0.2
            fin.inputs['Subdivisions'].default_value = 3
            pieces.append(_move(tree, fin.outputs['Mesh'], (base_x + 200, -2500),
                                 translation=(0, 0, apex_z + 0.18), label="ornament"))
            color_node(fin, "ornament")
        return _join_all(tree, pieces, (base_x + 1300, 0))


    # ─── JP KURA STOREHOUSE ─────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_cn_ting_pavilion")
    return tree, gin, gout

register_builder(
    "MEL_cn_ting_pavilion", build_cn_ting_pavilion_group,
    "Cn Ting Pavilion", "East Asian builder (absorbed from monolith build_cn_ting_pavilion).",
    category="asian")


def build_jp_kura_storehouse_group(group_name="MEL_jp_kura_storehouse"):
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
        """Whitewashed kura: thick rectangular box, small high windows, heavy door,
        grey-tile hipped roof."""
        W = max(2.5, getattr(PROPS, 'base_radius', 1.0) * 2.8)
        D = W * 0.9
        H = max(3.0, getattr(PROPS, 'height', 4.0))
        pieces = []
        # Thick body
        pieces.append(_move(tree, _cube(tree, (base_x, 200), W, D, H, "tower"),
                             (base_x + 200, 200), translation=(0, 0, H / 2), label="tower"))
        # Heavy reinforced door (recessed dark cube on front face)
        pieces.append(_move(tree, _cube(tree, (base_x, -100), W * 0.35, 0.15, H * 0.6, "ornament"),
                             (base_x + 200, -100),
                             translation=(0, -D / 2 - 0.08, H * 0.3), label="ornament"))
        # Door frame
        pieces.append(_move(tree, _cube(tree, (base_x, -400), W * 0.42, 0.08, H * 0.7, "tower"),
                             (base_x + 200, -400),
                             translation=(0, -D / 2 - 0.04, H * 0.35), label="tower"))
        # Two small high windows on each side
        import math
        for sx in (-1, 1):
            for w_off in (-W * 0.18, W * 0.18):
                win = _cube(tree, (base_x, -800 - (sx + 1) * 50 - int(w_off * 10)),
                             0.04, W * 0.15, H * 0.1, "ornament")
                pieces.append(_move(tree, win,
                                     (base_x + 220, -800 - (sx + 1) * 50 - int(w_off * 10)),
                                     translation=(sx * W / 2 + sx * 0.02, w_off, H * 0.75),
                                     label="ornament"))
        # Real hipped tile roof (slight Japanese curve) via curved-roof helper
        roof_geo = _curved_roof(tree, (base_x, -1500),
                                size_x=W * 1.2, size_y=D * 1.2, ridge_h=H * 0.5,
                                base_z=H, pitch=1.3, hip=True, eave_flip=0.1,
                                thickness=-0.12, label="house")
        pieces.append(roof_geo)
        # Ridge cap beam along the top
        pieces.append(_move(tree, _cube(tree, (base_x, -1700), W * 0.5, 0.14, 0.14, "ornament"),
                             (base_x + 200, -1700),
                             translation=(0, 0, H + H * 0.5 + H * 0.05), label="ornament"))
        return _join_all(tree, pieces, (base_x + 1200, 0))


    # ─── KR JANGSEUNG (Korean totem) ────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_jp_kura_storehouse")
    return tree, gin, gout

register_builder(
    "MEL_jp_kura_storehouse", build_jp_kura_storehouse_group,
    "Jp Kura Storehouse", "East Asian builder (absorbed from monolith build_jp_kura_storehouse).",
    category="asian")


def build_kr_jangseung_group(group_name="MEL_kr_jangseung"):
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
        """Wooden guardian pole: tall log + carved-face block on top + hat."""
        H = max(2.5, getattr(PROPS, 'height', 4.0) * 1.0)
        r = 0.18
        pieces = []
        # Buried plinth at bottom
        pieces.append(_move(tree, _cube(tree, (base_x, 200), r * 3, r * 3, 0.15, "house"),
                             (base_x + 200, 200), translation=(0, 0, 0.075), label="house"))
        # Tall log shaft
        log = _node(tree, 'GeometryNodeMeshCylinder', (base_x, -100))
        log.inputs['Radius'].default_value = r
        log.inputs['Depth'].default_value = H * 0.7
        log.inputs['Vertices'].default_value = 12
        pieces.append(_move(tree, log.outputs['Mesh'], (base_x + 200, -100),
                             translation=(0, 0, H * 0.35 + 0.15), label="tower"))
        color_node(log, "tower")
        # Carved-face block (oversized head)
        pieces.append(_move(tree, _cube(tree, (base_x, -500), r * 2.4, r * 2, r * 2.8, "ornament"),
                             (base_x + 200, -500),
                             translation=(0, 0, H * 0.85 + 0.15), label="ornament"))
        # Eyebrow-ridge bar across face
        pieces.append(_move(tree, _cube(tree, (base_x, -800), r * 2.5, 0.04, 0.07, "ornament"),
                             (base_x + 200, -800),
                             translation=(0, -r * 1.05, H * 0.92 + 0.15), label="ornament"))
        # Conical hat
        hat = _safe_node(tree, 'GeometryNodeMeshCone', (base_x, -1100))
        if hat:
            hat.inputs['Radius Bottom'].default_value = r * 1.8
            hat.inputs['Radius Top'].default_value = 0
            hat.inputs['Depth'].default_value = r * 2.2
            hat.inputs['Vertices'].default_value = 24
            pieces.append(_move(tree, hat.outputs['Mesh'], (base_x + 200, -1100),
                                 translation=(0, 0, H * 1.05 + 0.15), label="house"))
            color_node(hat, "house")
        return _finalize_building(tree, pieces, (base_x + 1100, 0))


    # ─── KR HONGSALMUN (Red arrow gate) ─────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_kr_jangseung")
    return tree, gin, gout

register_builder(
    "MEL_kr_jangseung", build_kr_jangseung_group,
    "Kr Jangseung", "East Asian builder (absorbed from monolith build_kr_jangseung).",
    category="asian")


def build_kr_hong_sal_mun_group(group_name="MEL_kr_hong_sal_mun"):
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
        """Hongsalmun: 2 red posts + horizontal beam + arrowhead pole at top."""
        H = max(3.5, getattr(PROPS, 'height', 5.0))
        W = max(2.0, getattr(PROPS, 'base_radius', 1.0) * 2.4)
        pieces = []
        # 2 vertical posts
        for sx in (-1, 1):
            post = _node(tree, 'GeometryNodeMeshCylinder', (base_x, 200 + (sx + 1) * 100))
            post.inputs['Radius'].default_value = 0.15
            post.inputs['Depth'].default_value = H
            post.inputs['Vertices'].default_value = 12
            pieces.append(_move(tree, post.outputs['Mesh'],
                                 (base_x + 220, 200 + (sx + 1) * 100),
                                 translation=(sx * W / 2, 0, H / 2), label="tower"))
            color_node(post, "tower")
        # Horizontal beam connecting them at top
        beam = _node(tree, 'GeometryNodeMeshCylinder', (base_x, -400))
        beam.inputs['Radius'].default_value = 0.1
        beam.inputs['Depth'].default_value = W + 0.4
        beam.inputs['Vertices'].default_value = 10
        pieces.append(_move(tree, beam.outputs['Mesh'], (base_x + 200, -400),
                             translation=(0, 0, H * 0.85),
                             rotation=(0, 1.5708, 0), label="tower"))
        color_node(beam, "tower")
        # Central round emblem (cylinder face-on between posts)
        emblem = _node(tree, 'GeometryNodeMeshCylinder', (base_x, -700))
        emblem.inputs['Radius'].default_value = 0.3
        emblem.inputs['Depth'].default_value = 0.06
        emblem.inputs['Vertices'].default_value = 16
        pieces.append(_move(tree, emblem.outputs['Mesh'], (base_x + 200, -700),
                             translation=(0, -0.18, H * 0.85),
                             rotation=(1.5708, 0, 0), label="ornament"))
        color_node(emblem, "ornament")
        # Top "arrowhead" pole rising above the beam (3 thin verticals)
        for i, off in enumerate((-0.4, 0.0, 0.4)):
            arrow = _node(tree, 'GeometryNodeMeshCylinder', (base_x, -1000 - i * 100))
            arrow.inputs['Radius'].default_value = 0.04
            arrow.inputs['Depth'].default_value = 0.8
            arrow.inputs['Vertices'].default_value = 8
            pieces.append(_move(tree, arrow.outputs['Mesh'], (base_x + 220, -1000 - i * 100),
                                 translation=(off, 0, H * 0.85 + 0.4),
                                 label="ornament"))
            color_node(arrow, "ornament")
        return _join_all(tree, pieces, (base_x + 1100, 0))


    # ─── TOWN HALL ──────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_kr_hong_sal_mun")
    return tree, gin, gout

register_builder(
    "MEL_kr_hong_sal_mun", build_kr_hong_sal_mun_group,
    "Kr Hong Sal Mun", "East Asian builder (absorbed from monolith build_kr_hong_sal_mun).",
    category="asian")


# 9 builders registered
