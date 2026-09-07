"""MEL Castle builders — absorbed from the monolith (P2 family 3).

6 generator builders. Params-as-values port: each builder reads its
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
    "build_watchtower": "watchtower",
    "build_gatehouse": "gatehouse",
    "build_keep": "keep",
    "build_curtain_wall": "curtain_wall",
    "build_barbican": "barbican",
    "build_drawbridge": "drawbridge",
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
    "base_radius": {"type": "FloatProperty", "default": 1.2, "min": 0.1, "max": 10.0},
    "bridge_height": {"type": "FloatProperty", "default": 2.0, "min": 0.5, "max": 10.0},
    "bridge_length": {"type": "FloatProperty", "default": 8.0, "min": 2.0, "max": 40.0},
    "height": {"type": "FloatProperty", "default": 5.0, "min": 0.5, "max": 30.0},
    "rail_length": {"type": "FloatProperty", "default": 6.0, "min": 1.0, "max": 30.0},
    "sv_complexity": {"type": "FloatProperty", "default": 1.0, "min": 0.3, "max": 4.0},
    "wall_thickness": {"type": "FloatProperty", "default": 0.25, "min": 0.05, "max": 2.0},
}


def build_watchtower_group(group_name="MEL_watchtower"):
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
        """Cylindrical watchtower with battlements + conical roof."""
        r = max(0.6, getattr(PROPS, 'base_radius', 1.0)) * 0.9
        h = max(3.0, getattr(PROPS, 'height', 5.0)) * 1.4
        pieces = []
        # Shaft (octagonal extruded curve)
        shaft_c = _cv_circle(tree, (base_x, 200), r, 16)
        shaft = _fill_extrude(tree, shaft_c.outputs['Curve'] if shaft_c else None,
                              (base_x + 200, 200), (base_x + 400, 200), h, "tower")
        pieces.append(shaft)
        # Machicolation ring (slightly wider torus at top of shaft)
        mach = _safe_node(tree, 'GeometryNodeMeshTorus', (base_x, -200))
        if mach:
            try:
                mach.inputs['Major Radius'].default_value = r * 1.15
                mach.inputs['Minor Radius'].default_value = r * 0.18
                mach.inputs['Major Segments'].default_value = 24
                mach.inputs['Minor Segments'].default_value = 6
            except Exception:
                pass
            color_node(mach, "ornament")
            pieces.append(_move(tree, mach.outputs['Mesh'], (base_x + 200, -200),
                                translation=(0, 0, h - r * 0.18), label="ornament"))
        # Battlements above machicolation - narrow ring of merlons
        n_merlons = 12
        import math
        for i in range(n_merlons):
            m = _node(tree, 'GeometryNodeMeshCube', (base_x, -600 - i * 60))
            m.inputs['Size'].default_value = (r * 0.35, r * 0.2, r * 0.7)
            ang = (i / n_merlons) * math.tau
            t = _move(tree, m.outputs['Mesh'], (base_x + 220, -600 - i * 60),
                      translation=(math.cos(ang) * r * 1.15,
                                   math.sin(ang) * r * 1.15,
                                   h + r * 0.2),
                      rotation=(0, 0, ang),
                      label="ornament")
            color_node(m, "ornament")
            pieces.append(t)
        # Conical roof: curve line + circular profile, swept
        roof_line = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (base_x, -1500))
        if roof_line:
            try:
                roof_line.inputs['Start'].default_value = (0, 0, h + r * 0.6)
                roof_line.inputs['End'].default_value   = (0, 0, h + r * 0.6 + r * 1.5)
            except Exception:
                pass
            # Tapered cone via resampled line with custom radius
            roof_c = _cv_circle(tree, (base_x, -1700), r * 1.05, 16)
            c2m = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 200, -1500))
            if c2m and roof_c:
                _link(tree, roof_line.outputs['Curve'], c2m.inputs['Curve'])
                _link(tree, roof_c.outputs['Curve'], c2m.inputs['Profile Curve'])
                # Use a small set of resampled radii via Set Curve Radius
                # Quick hack: just put a smaller circle at the apex via 2nd object
                color_node(c2m, "house")
                pieces.append(c2m.outputs['Mesh'])
        # Slit windows (3 vertical narrow openings just under the machicolation)
        for i in range(3):
            ang = (i / 3) * math.tau + 0.3
            slit = _node(tree, 'GeometryNodeMeshCube', (base_x, -2200 - i * 80))
            slit.inputs['Size'].default_value = (0.06, 0.3, 0.6)
            # NB: these are inset markers; could be subtracted via boolean
            t = _move(tree, slit.outputs['Mesh'], (base_x + 220, -2200 - i * 80),
                      translation=(math.cos(ang) * r * 1.02,
                                   math.sin(ang) * r * 1.02,
                                   h * 0.6),
                      rotation=(0, 0, ang + 1.5708),
                      label="ornament")
            color_node(slit, "ornament")
            pieces.append(t)
        return _finalize_building(tree, pieces, (base_x + 1100, 0))


    # ─── GATEHOUSE ──────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_watchtower")
    return tree, gin, gout

register_builder(
    "MEL_watchtower", build_watchtower_group,
    "Watchtower", "Castle builder (absorbed from monolith build_watchtower).",
    category="castle")


def build_gatehouse_group(group_name="MEL_gatehouse"):
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
        """Twin towers flanking an arched gateway with a portcullis grid."""
        r = max(0.6, getattr(PROPS, 'base_radius', 1.0)) * 0.8
        h = max(3.5, getattr(PROPS, 'height', 5.0)) * 1.4
        gate_w = r * 2.6
        gate_h = h * 0.65
        pieces = []
        # Two flanking cylindrical towers (use build_watchtower-style shafts)
        for sx in (-1, 1):
            shaft_c = _cv_circle(tree, (base_x, 200 + sx * 250), r, 16)
            shaft = _fill_extrude(tree, shaft_c.outputs['Curve'] if shaft_c else None,
                                  (base_x + 200, 200 + sx * 250),
                                  (base_x + 400, 200 + sx * 250), h, "tower")
            pieces.append(_move(tree, shaft,
                                (base_x + 600, 200 + sx * 250),
                                translation=(sx * (gate_w / 2 + r), 0, 0), label="tower"))
            # Conical cap
            cap = _safe_node(tree, 'GeometryNodeMeshCone', (base_x + 800, 200 + sx * 250))
            if cap:
                cap.inputs['Radius Bottom'].default_value = r * 1.1
                cap.inputs['Radius Top'].default_value = 0
                cap.inputs['Depth'].default_value = r * 1.6
                cap.inputs['Vertices'].default_value = 32  # bumped from 16 in v2.31 for smoother shading
                pieces.append(_move(tree, cap.outputs['Mesh'],
                                    (base_x + 1000, 200 + sx * 250),
                                    translation=(sx * (gate_w / 2 + r), 0, h + r * 0.8),
                                    label="house"))
                color_node(cap, "house")
        # Connecting wall block between towers (with arched gate cut)
        wall = _node(tree, 'GeometryNodeMeshCube', (base_x, -300))
        wall.inputs['Size'].default_value = (gate_w, r * 0.6, h * 0.85)
        pieces.append(_move(tree, wall.outputs['Mesh'], (base_x + 200, -300),
                            translation=(0, 0, h * 0.425), label="tower"))
        color_node(wall, "tower")
        # Portcullis grid (vertical + horizontal bars)
        bars_v = 5; bars_h = 3
        for i in range(bars_v):
            b = _node(tree, 'GeometryNodeMeshCube', (base_x, -700 - i * 70))
            b.inputs['Size'].default_value = (0.06, 0.08, gate_h * 0.9)
            x = -gate_w * 0.4 + i * (gate_w * 0.8 / max(1, bars_v - 1))
            pieces.append(_move(tree, b.outputs['Mesh'], (base_x + 220, -700 - i * 70),
                                translation=(x, r * 0.3, gate_h * 0.5), label="ornament"))
            color_node(b, "ornament")
        for j in range(bars_h):
            b = _node(tree, 'GeometryNodeMeshCube', (base_x, -1200 - j * 70))
            b.inputs['Size'].default_value = (gate_w * 0.85, 0.08, 0.06)
            z = gate_h * (0.15 + j * 0.35)
            pieces.append(_move(tree, b.outputs['Mesh'], (base_x + 220, -1200 - j * 70),
                                translation=(0, r * 0.3, z), label="ornament"))
            color_node(b, "ornament")
        # Battlement cap atop the connecting wall
        crenel = _crenel_top(tree, gate_w, r * 0.6, r * 0.4, 7, 0.5,
                             loc=(base_x, -2000), label="ornament")
        pieces.append(_move(tree, crenel, (base_x + 700, -2000),
                            translation=(0, 0, h * 0.85), label="ornament"))
        return _finalize_building(tree, pieces, (base_x + 1400, 0))


    # ─── KEEP / DONJON ──────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_gatehouse")
    return tree, gin, gout

register_builder(
    "MEL_gatehouse", build_gatehouse_group,
    "Gatehouse", "Castle builder (absorbed from monolith build_gatehouse).",
    category="castle")


def build_keep_group(group_name="MEL_keep"):
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
        """Rectangular keep - body + 4 corner turrets + battlements."""
        W = max(2.5, getattr(PROPS, 'base_radius', 1.0) * 3.5)
        H = max(5.0, getattr(PROPS, 'height', 5.0)) * 1.6
        D = W * 0.85
        pieces = []
        # Main body
        body = _node(tree, 'GeometryNodeMeshCube', (base_x, 200))
        body.inputs['Size'].default_value = (W, D, H)
        pieces.append(_move(tree, body.outputs['Mesh'], (base_x + 200, 200),
                            translation=(0, 0, H / 2), label="tower"))
        color_node(body, "tower")
        # Battlement cap on top
        crenel_x = _crenel_top(tree, W, D, H * 0.07, 11, 0.5,
                                loc=(base_x, -400), label="ornament")
        pieces.append(_move(tree, crenel_x, (base_x + 700, -400),
                            translation=(0, 0, H + H * 0.035), label="ornament"))
        # 4 corner turrets - small extruded octagons
        import math
        turret_r = W * 0.13
        turret_h = H * 1.15
        for sx in (-1, 1):
            for sy in (-1, 1):
                tc = _cv_circle(tree, (base_x, -900 - (sx + 1) * 100 - (sy + 1) * 50),
                                turret_r, 12)
                tm = _fill_extrude(tree,
                                   tc.outputs['Curve'] if tc else None,
                                   (base_x + 200, -900 - (sx + 1) * 100 - (sy + 1) * 50),
                                   (base_x + 400, -900 - (sx + 1) * 100 - (sy + 1) * 50),
                                   turret_h, "tower")
                pieces.append(_move(tree, tm,
                                    (base_x + 600, -900 - (sx + 1) * 100 - (sy + 1) * 50),
                                    translation=(sx * W / 2, sy * D / 2, 0), label="tower"))
                # Conical cap
                cap = _safe_node(tree, 'GeometryNodeMeshCone',
                                 (base_x + 800, -900 - (sx + 1) * 100 - (sy + 1) * 50))
                if cap:
                    cap.inputs['Radius Bottom'].default_value = turret_r * 1.1
                    cap.inputs['Radius Top'].default_value = 0
                    cap.inputs['Depth'].default_value = turret_r * 2.0
                    cap.inputs['Vertices'].default_value = 32  # bumped from 16 in v2.31 for smoother shading
                    pieces.append(_move(tree, cap.outputs['Mesh'],
                                        (base_x + 1000, -900 - (sx + 1) * 100 - (sy + 1) * 50),
                                        translation=(sx * W / 2, sy * D / 2, turret_h + turret_r),
                                        label="house"))
                    color_node(cap, "house")
        # Single arched front door (extruded curve)
        door_arch = _safe_node(tree, 'GeometryNodeCurveQuadraticBezier', (base_x, -2200))
        if door_arch:
            try:
                door_arch.inputs['Resolution'].default_value = 24
                door_arch.inputs['Start'].default_value  = (-0.6, 0, 0)
                door_arch.inputs['Middle'].default_value = (0, 0, 1.6)
                door_arch.inputs['End'].default_value    = (0.6, 0, 0)
            except Exception:
                pass
            # Thin profile circle for arch frame
            prof = _cv_circle(tree, (base_x, -2400), 0.08, 8)
            sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 250, -2200))
            if sw and prof:
                _link(tree, door_arch.outputs['Curve'], sw.inputs['Curve'])
                _link(tree, prof.outputs['Curve'], sw.inputs['Profile Curve'])
                color_node(sw, "ornament")
                pieces.append(_move(tree, sw.outputs['Mesh'], (base_x + 500, -2200),
                                    translation=(0, -D / 2 - 0.05, 0), label="ornament"))
        return _finalize_building(tree, pieces, (base_x + 1400, 0))


    # ─── CURTAIN WALL ───────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_keep")
    return tree, gin, gout

register_builder(
    "MEL_keep", build_keep_group,
    "Keep", "Castle builder (absorbed from monolith build_keep).",
    category="castle")


def build_curtain_wall_group(group_name="MEL_curtain_wall"):
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
        """Crenellated curtain wall section with battlement walkway."""
        L = max(3.0, getattr(PROPS, 'rail_length', 4.0)) * 1.8
        H = max(2.0, getattr(PROPS, 'height', 4.0)) * 1.0
        T = max(0.4, getattr(PROPS, 'wall_thickness', 0.5))
        pieces = []
        # Main wall slab
        wall = _node(tree, 'GeometryNodeMeshCube', (base_x, 200))
        wall.inputs['Size'].default_value = (L, T, H)
        pieces.append(_move(tree, wall.outputs['Mesh'], (base_x + 200, 200),
                            translation=(0, 0, H / 2), label="tower"))
        color_node(wall, "tower")
        # Battlement cap (merlons)
        n_m = max(5, int(L / 0.8))
        crenel = _crenel_top(tree, L, T * 1.05, H * 0.18, n_m, 0.5,
                             loc=(base_x, -300), label="ornament")
        pieces.append(_move(tree, crenel, (base_x + 700, -300),
                            translation=(0, 0, H + H * 0.09), label="ornament"))
        # Walkway shelf on the inside of the wall (Y-)
        walk = _node(tree, 'GeometryNodeMeshCube', (base_x, -1000))
        walk.inputs['Size'].default_value = (L, T * 0.9, 0.1)
        pieces.append(_move(tree, walk.outputs['Mesh'], (base_x + 200, -1000),
                            translation=(0, -T * 0.55, H - 0.05), label="house"))
        color_node(walk, "house")
        return _finalize_building(tree, pieces, (base_x + 1100, 0))


    # ─── BARBICAN ───────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_curtain_wall")
    return tree, gin, gout

register_builder(
    "MEL_curtain_wall", build_curtain_wall_group,
    "Curtain Wall", "Castle builder (absorbed from monolith build_curtain_wall).",
    category="castle")


def build_barbican_group(group_name="MEL_barbican"):
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
        """Outer fortified gatehouse: 2 small flanking towers + connecting wall
        with passageway, ahead of where a main gatehouse would sit."""
        r = max(0.5, getattr(PROPS, 'base_radius', 1.0)) * 0.7
        h = max(2.5, getattr(PROPS, 'height', 4.0)) * 1.1
        gap = r * 2.2
        pieces = []
        for sx in (-1, 1):
            c = _cv_circle(tree, (base_x, 200 + sx * 200), r, 12)
            sh = _fill_extrude(tree, c.outputs['Curve'] if c else None,
                               (base_x + 200, 200 + sx * 200),
                               (base_x + 400, 200 + sx * 200), h, "tower")
            pieces.append(_move(tree, sh, (base_x + 600, 200 + sx * 200),
                                translation=(sx * (gap / 2 + r), 0, 0), label="tower"))
            # Crenel ring on top
            for i in range(8):
                import math
                ang = (i / 8) * math.tau
                m = _node(tree, 'GeometryNodeMeshCube', (base_x, -500 - sx * 200 - i * 40))
                m.inputs['Size'].default_value = (r * 0.3, r * 0.18, r * 0.5)
                pieces.append(_move(tree, m.outputs['Mesh'],
                                    (base_x + 220, -500 - sx * 200 - i * 40),
                                    translation=(sx * (gap / 2 + r) + math.cos(ang) * r * 1.05,
                                                 math.sin(ang) * r * 1.05, h + r * 0.15),
                                    rotation=(0, 0, ang), label="ornament"))
                color_node(m, "ornament")
        # Connecting wall arch
        wall = _node(tree, 'GeometryNodeMeshCube', (base_x, -1800))
        wall.inputs['Size'].default_value = (gap, r * 0.55, h * 0.4)
        pieces.append(_move(tree, wall.outputs['Mesh'], (base_x + 200, -1800),
                            translation=(0, 0, h * 0.8), label="tower"))
        color_node(wall, "tower")
        return _finalize_building(tree, pieces, (base_x + 1200, 0))


    # ─── DRAWBRIDGE ─────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_barbican")
    return tree, gin, gout

register_builder(
    "MEL_barbican", build_barbican_group,
    "Barbican", "Castle builder (absorbed from monolith build_barbican).",
    category="castle")


def build_drawbridge_group(group_name="MEL_drawbridge"):
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
        """Hinged drawbridge: deck + side rails + chains to upper hinge."""
        L = max(1.5, getattr(PROPS, 'bridge_length', 4.0)) * 0.6
        W = max(1.0, getattr(PROPS, 'bridge_height', 2.0)) * 0.8
        pieces = []
        # Deck - tilted at user-control angle (use sv_complexity as tilt 0..1)
        tilt = min(1.0, getattr(PROPS, 'sv_complexity', 0.5)) * 1.2  # rad
        deck = _node(tree, 'GeometryNodeMeshCube', (base_x, 200))
        deck.inputs['Size'].default_value = (W, L, 0.12)
        import math
        pieces.append(_move(tree, deck.outputs['Mesh'], (base_x + 200, 200),
                            translation=(0, math.cos(tilt) * L / 2,
                                         math.sin(tilt) * L / 2 + 0.06),
                            rotation=(tilt, 0, 0), label="house"))
        color_node(deck, "house")
        # 6 plank ridges across the deck for detail
        for i in range(7):
            p = _node(tree, 'GeometryNodeMeshCube', (base_x, -200 - i * 60))
            p.inputs['Size'].default_value = (W * 0.95, 0.04, 0.04)
            t = -L / 2 + i * (L / 6)
            pieces.append(_move(tree, p.outputs['Mesh'], (base_x + 220, -200 - i * 60),
                                translation=(0,
                                             math.cos(tilt) * (L / 2 + t),
                                             math.sin(tilt) * (L / 2 + t) + 0.13),
                                rotation=(tilt, 0, 0), label="ornament"))
            color_node(p, "ornament")
        # Two side rails
        for sx in (-1, 1):
            rail = _node(tree, 'GeometryNodeMeshCube', (base_x, -800 - (sx + 1) * 50))
            rail.inputs['Size'].default_value = (0.06, L, 0.25)
            pieces.append(_move(tree, rail.outputs['Mesh'],
                                (base_x + 220, -800 - (sx + 1) * 50),
                                translation=(sx * W / 2,
                                             math.cos(tilt) * L / 2,
                                             math.sin(tilt) * L / 2 + 0.18),
                                rotation=(tilt, 0, 0), label="ornament"))
            color_node(rail, "ornament")
        # Chains (2 thin tubes from hinge to upper edge of deck)
        chain_prof = _cv_circle(tree, (base_x, -1500), 0.025, 8)
        for sx in (-1, 1):
            line = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine',
                              (base_x, -1300 - (sx + 1) * 80))
            if line:
                try:
                    line.inputs['Start'].default_value = (sx * W / 2, 0, 0.1)
                    line.inputs['End'].default_value   = (sx * W / 2,
                                                           math.cos(tilt) * L,
                                                           math.sin(tilt) * L + 0.2)
                except Exception:
                    pass
                sw = _safe_node(tree, 'GeometryNodeCurveToMesh',
                                (base_x + 220, -1300 - (sx + 1) * 80))
                if sw and chain_prof:
                    _link(tree, line.outputs['Curve'], sw.inputs['Curve'])
                    _link(tree, chain_prof.outputs['Curve'], sw.inputs['Profile Curve'])
                    color_node(sw, "ornament")
                    pieces.append(sw.outputs['Mesh'])
        return _finalize_building(tree, pieces, (base_x + 1200, 0))


    # ─── STONE BRIDGE ───────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_drawbridge")
    return tree, gin, gout

register_builder(
    "MEL_drawbridge", build_drawbridge_group,
    "Drawbridge", "Castle builder (absorbed from monolith build_drawbridge).",
    category="castle")


# 6 builders registered
