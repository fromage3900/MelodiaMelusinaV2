"""MEL core architectural forms — absorbed from the monolith (P2 family 7a).

14 builders. Cross-calls to ogee_arch served by module-level impl.
Params-as-values port. Regenerable.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, add_string_param,
    register_builder,
)

def _higg_load(name):
    """Lazily append one Higgsas node group from the library. Returns the
    NodeGroup or None if unavailable. Idempotent - skips if already loaded."""
    ng = bpy.data.node_groups.get(name)
    if ng is not None:
        return ng
    import os
    if not os.path.exists(_HIGGSAS_LIB_PATH):
        return None
    try:
        with bpy.data.libraries.load(_HIGGSAS_LIB_PATH, link=False) as (src, dst):
            if name in src.node_groups:
                dst.node_groups = [name]
            else:
                return None
    except Exception:
        return None
    return bpy.data.node_groups.get(name)


_HIGGSAS_LIB_PATH = (
    r"G:\programs\BlenderPlugins"
    r"\Higgsas_Geometry_Nodes_Toolset_v1.3 vfxMed"
    r"\Higgsas Geo Nodes Blender 5.0"
    r"\Blender 5.0 Higgsas Geo Node Groups v13.blend"
)

def _higgsas_available():
    """Return True if the Higgsas library is accessible OR groups already loaded."""
    # Fast path: any Higgsas NT* group already in the file
    for ng in bpy.data.node_groups:
        if ng.name.startswith('NT') and len(ng.name) > 4:
            return True
    # Check the library file on disk
    import os
    return os.path.exists(_HIGGSAS_LIB_PATH)



def _higg_load(name):
    """Lazily append one Higgsas node group from the library. Returns the
    NodeGroup or None if unavailable. Idempotent - skips if already loaded."""
    ng = bpy.data.node_groups.get(name)
    if ng is not None:
        return ng
    import os
    if not os.path.exists(_HIGGSAS_LIB_PATH):
        return None
    try:
        with bpy.data.libraries.load(_HIGGSAS_LIB_PATH, link=False) as (src, dst):
            if name in src.node_groups:
                dst.node_groups = [name]
            else:
                return None
    except Exception:
        return None
    return bpy.data.node_groups.get(name)



def _higg_node(tree, name, loc, fallback_type=None):
    """Add a GeometryNodeGroup node for the named Higgsas group.
    If unavailable, creates `fallback_type` (e.g. 'GeometryNodeMeshCube') instead.
    Returns the node or None. All failure paths fall back gracefully."""
    ng = _higg_load(name)
    if ng is None:
        if fallback_type:
            return _safe_node(tree, fallback_type, loc)
        return None
    try:
        node = tree.nodes.new('GeometryNodeGroup')
        node.node_tree = ng
        node.location = loc
        color_node(node, 'ornament')
        return node
    except Exception:
        # Group loaded but node creation failed (version mismatch, corrupt group, etc.)
        if fallback_type:
            return _safe_node(tree, fallback_type, loc)
        return None



def _higg_input(node, name, value):
    """Safely set a named input on a Higgsas node group. Skips on error."""
    if node is None:
        return
    try:
        node.inputs[name].default_value = value
    except Exception:
        pass



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


def _make_circle_profile(tree, radius, resolution=8, loc=(-400, -600), props=None):
    """Build the user-selected sweep profile and return a stub object whose
    `.outputs['Curve']` is the profile curve socket.

    Backwards-compatible wrapper: callers that pass no `props` get a circle.
    With `props`, picks from `props.aest_profile`."""
    kind = getattr(props, 'aest_profile', 'CIRCLE') if props else 'CIRCLE'

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


def make_harmonic_value(tree, index_socket, freq_a, freq_b, layers, x, y):
    """
    Compose layered sine waves driven by point index -> musical/harmonic factor.
    Returns a Math output socket (value in roughly [-2..2]).
    """
    # Layer 1
    m1 = tree.nodes.new('ShaderNodeMath'); m1.location = (x, y); m1.operation = 'MULTIPLY'
    m1.inputs[1].default_value = freq_a
    tree.links.new(index_socket, m1.inputs[0])
    s1 = tree.nodes.new('ShaderNodeMath'); s1.location = (x+200, y); s1.operation = 'SINE'
    tree.links.new(m1.outputs['Value'], s1.inputs[0])
    color_node(s1, "ornament")

    if layers <= 1:
        return s1.outputs['Value']

    # Layer 2
    m2 = tree.nodes.new('ShaderNodeMath'); m2.location = (x, y-200); m2.operation = 'MULTIPLY'
    m2.inputs[1].default_value = freq_b
    tree.links.new(index_socket, m2.inputs[0])
    s2 = tree.nodes.new('ShaderNodeMath'); s2.location = (x+200, y-200); s2.operation = 'SINE'
    tree.links.new(m2.outputs['Value'], s2.inputs[0])
    color_node(s2, "ornament")

    add = tree.nodes.new('ShaderNodeMath'); add.location = (x+400, y-100); add.operation = 'ADD'
    tree.links.new(s1.outputs['Value'], add.inputs[0])
    tree.links.new(s2.outputs['Value'], add.inputs[1])

    if layers <= 2:
        return add.outputs['Value']

    # Layer 3 (octave-up of A)
    m3 = tree.nodes.new('ShaderNodeMath'); m3.location = (x, y-400); m3.operation = 'MULTIPLY'
    m3.inputs[1].default_value = freq_a * 2.0
    tree.links.new(index_socket, m3.inputs[0])
    s3 = tree.nodes.new('ShaderNodeMath'); s3.location = (x+200, y-400); s3.operation = 'SINE'
    tree.links.new(m3.outputs['Value'], s3.inputs[0])
    color_node(s3, "ornament")
    add2 = tree.nodes.new('ShaderNodeMath'); add2.location = (x+400, y-300); add2.operation = 'ADD'
    tree.links.new(add.outputs['Value'], add2.inputs[0])
    tree.links.new(s3.outputs['Value'], add2.inputs[1])
    final = add2

    # Optional layers 4 & 5
    for i, fmul in enumerate([3.0, 5.0][:layers-3], start=4):
        mn = tree.nodes.new('ShaderNodeMath'); mn.location = (x, y-200*i-200); mn.operation = 'MULTIPLY'
        mn.inputs[1].default_value = freq_b * fmul / 3.0
        tree.links.new(index_socket, mn.inputs[0])
        sn = tree.nodes.new('ShaderNodeMath'); sn.location = (x+200, y-200*i-200); sn.operation = 'SINE'
        tree.links.new(mn.outputs['Value'], sn.inputs[0])
        addn = tree.nodes.new('ShaderNodeMath'); addn.location = (x+400, y-200*i-100); addn.operation = 'ADD'
        tree.links.new(final.outputs['Value'], addn.inputs[0])
        tree.links.new(sn.outputs['Value'], addn.inputs[1])
        final = addn

    return final.outputs['Value']


# ----------------------------------------------------------------------
# BUILDERS - TOWER / ORGANIC / HYBRID (existing)
# ----------------------------------------------------------------------

def _higg_node(tree, name, loc, fallback_type=None):
    """Add a GeometryNodeGroup node for the named Higgsas group.
    If unavailable, creates `fallback_type` (e.g. 'GeometryNodeMeshCube') instead.
    Returns the node or None. All failure paths fall back gracefully."""
    ng = _higg_load(name)
    if ng is None:
        if fallback_type:
            return _safe_node(tree, fallback_type, loc)
        return None
    try:
        node = tree.nodes.new('GeometryNodeGroup')
        node.node_tree = ng
        node.location = loc
        color_node(node, 'ornament')
        return node
    except Exception:
        # Group loaded but node creation failed (version mismatch, corrupt group, etc.)
        if fallback_type:
            return _safe_node(tree, fallback_type, loc)
        return None

def _ogee_curve_pair(tree, half_W, height, swell, shoulder, base_x=0, base_y=0):
    """
    Build the two Bezier curves of an ogee arch (right + left).
    Returns (right_curve_socket, left_curve_socket).
    Curves are in the XZ plane (rotated from default XY).
    """
    rb = tree.nodes.new('GeometryNodeCurvePrimitiveBezierSegment')
    rb.location = (base_x, base_y + 200); color_node(rb, "ogee")
    rb.inputs['Resolution'].default_value = 32
    rb.inputs['Start'].default_value         = (half_W, 0, 0)
    rb.inputs['Start Handle'].default_value  = (half_W + swell, shoulder, 0)
    rb.inputs['End Handle'].default_value    = (half_W * 0.3, height - 0.3, 0)
    rb.inputs['End'].default_value           = (0, height, 0)

    lb = tree.nodes.new('GeometryNodeCurvePrimitiveBezierSegment')
    lb.location = (base_x, base_y - 200); color_node(lb, "ogee")
    lb.inputs['Resolution'].default_value = 32
    lb.inputs['Start'].default_value         = (-half_W, 0, 0)
    lb.inputs['Start Handle'].default_value  = (-half_W - swell, shoulder, 0)
    lb.inputs['End Handle'].default_value    = (-half_W * 0.3, height - 0.3, 0)
    lb.inputs['End'].default_value           = (0, height, 0)

    rt = tree.nodes.new('GeometryNodeTransform'); rt.location = (base_x + 300, base_y + 200)
    rt.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
    tree.links.new(rb.outputs['Curve'], rt.inputs['Geometry'])

    lt = tree.nodes.new('GeometryNodeTransform'); lt.location = (base_x + 300, base_y - 200)
    lt.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
    tree.links.new(lb.outputs['Curve'], lt.inputs['Geometry'])

    return rt.outputs['Geometry'], lt.outputs['Geometry']



def _impl_build_ogee_arch(tree, PROPS, base_x=-1400):
    """Iconic Venetian Gothic ogee arch with S-curve sides + finial pinnacle."""
    half_W = PROPS.ogee_width / 2
    H = PROPS.ogee_height
    rc, lc = _ogee_curve_pair(tree, half_W, H, PROPS.ogee_swell, PROPS.ogee_shoulder,
                               base_x=base_x, base_y=0)

    profile = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); profile.location = (base_x, -500); color_node(profile, "ogee")
    profile.mode = 'RADIUS'
    profile.inputs['Resolution'].default_value = 8
    profile.inputs['Radius'].default_value = PROPS.gothic_thickness

    rsw = tree.nodes.new('GeometryNodeCurveToMesh'); rsw.location = (base_x+700, 200); color_node(rsw, "ogee")
    tree.links.new(rc, rsw.inputs['Curve'])
    tree.links.new(profile.outputs['Curve'], rsw.inputs['Profile Curve'])
    rsw.inputs['Fill Caps'].default_value = True

    lsw = tree.nodes.new('GeometryNodeCurveToMesh'); lsw.location = (base_x+700, -200); color_node(lsw, "ogee")
    tree.links.new(lc, lsw.inputs['Curve'])
    tree.links.new(profile.outputs['Curve'], lsw.inputs['Profile Curve'])
    lsw.inputs['Fill Caps'].default_value = True

    parts = [rsw.outputs['Mesh'], lsw.outputs['Mesh']]

    # Finial pinnacle at apex
    if PROPS.ogee_finial > 0.01:
        finial = tree.nodes.new('GeometryNodeMeshCone'); finial.location = (base_x, 600); color_node(finial, "ornament")
        finial.inputs['Vertices'].default_value = 16  # bumped from 8 in v2.31
        finial.inputs['Radius Top'].default_value = 0.0
        finial.inputs['Radius Bottom'].default_value = PROPS.ogee_finial * 0.3
        finial.inputs['Depth'].default_value = PROPS.ogee_finial

        ft = tree.nodes.new('GeometryNodeTransform'); ft.location = (base_x+300, 600)
        ft.inputs['Translation'].default_value = (0, 0, H + PROPS.ogee_finial / 2)
        tree.links.new(finial.outputs['Mesh'], ft.inputs['Geometry'])
        parts.append(ft.outputs['Geometry'])

    join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+1000, 0); color_node(join, "output")
    for p in parts: tree.links.new(p, join.inputs['Geometry'])
    return join.outputs['Geometry']




NOTE_PATTERNS = {
    'WHOLE':    1.0,
    'HALF':     2.0,
    'QUARTER':  4.0,
    'EIGHTH':   8.0,
    'SIXTEENTH':16.0,
    'TRIPLET':  3.0,
    'DOTTED':   1.5,
}

BUILDER_PARAM_DEFAULTS = {
    "aest_profile": {"type": "EnumProperty", "default": 'CIRCLE', "min": None, "max": None},
    "arch_radius": {"type": "FloatProperty", "default": 1.5, "min": 0.3, "max": 10.0},
    "arch_rib_count": {"type": "IntProperty", "default": 7, "min": 0, "max": 24},
    "arch_rib_radius": {"type": "FloatProperty", "default": 0.28, "min": 0.05, "max": 1.0},
    "arch_sweep_deg": {"type": "FloatProperty", "default": 180.0, "min": 30.0, "max": 360.0},
    "arch_thickness": {"type": "FloatProperty", "default": 0.18, "min": 0.02, "max": 1.0},
    "balcony_baluster_count": {"type": "IntProperty", "default": 10, "min": 2, "max": 40},
    "balcony_depth": {"type": "FloatProperty", "default": 0.8, "min": 0.2, "max": 3.0},
    "balcony_thickness": {"type": "FloatProperty", "default": 0.12, "min": 0.05, "max": 0.5},
    "balcony_width": {"type": "FloatProperty", "default": 2.5, "min": 0.5, "max": 10.0},
    "brick_depth": {"type": "FloatProperty", "default": 0.15, "min": 0.05, "max": 1.0},
    "brick_mortar_gap": {"type": "FloatProperty", "default": 0.04, "min": 0.0, "max": 0.3},
    "brick_size_x": {"type": "FloatProperty", "default": 0.4, "min": 0.05, "max": 2.0},
    "brick_size_z": {"type": "FloatProperty", "default": 0.2, "min": 0.05, "max": 2.0},
    "brick_wall_height": {"type": "FloatProperty", "default": 3.0, "min": 0.5, "max": 20.0},
    "brick_wall_width": {"type": "FloatProperty", "default": 4.0, "min": 0.5, "max": 30.0},
    "cornice_depth": {"type": "FloatProperty", "default": 0.25, "min": 0.05, "max": 1.0},
    "cornice_height": {"type": "FloatProperty", "default": 0.3, "min": 0.05, "max": 1.5},
    "cornice_layers": {"type": "IntProperty", "default": 3, "min": 1, "max": 6},
    "cornice_length": {"type": "FloatProperty", "default": 4.0, "min": 0.5, "max": 20.0},
    "crenel_gap_ratio": {"type": "FloatProperty", "default": 0.5, "min": 0.05, "max": 0.9},
    "crenel_height": {"type": "FloatProperty", "default": 2.5, "min": 0.5, "max": 10.0},
    "crenel_length": {"type": "FloatProperty", "default": 8.0, "min": 1.0, "max": 30.0},
    "crenel_merlon_count": {"type": "IntProperty", "default": 10, "min": 2, "max": 60},
    "crenel_merlon_height": {"type": "FloatProperty", "default": 0.6, "min": 0.1, "max": 3.0},
    "crenel_thickness": {"type": "FloatProperty", "default": 0.6, "min": 0.1, "max": 3.0},
    "dome_radius": {"type": "FloatProperty", "default": 1.5, "min": 0.3, "max": 10.0},
    "dome_rib_count": {"type": "IntProperty", "default": 8, "min": 0, "max": 32},
    "dome_rings": {"type": "IntProperty", "default": 16, "min": 4, "max": 48},
    "dome_segments": {"type": "IntProperty", "default": 32, "min": 8, "max": 96},
    "dome_spire": {"type": "FloatProperty", "default": 0.8, "min": 0.0, "max": 5.0},
    "door_arch_top": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "door_frame_width": {"type": "FloatProperty", "default": 0.12, "min": 0.02, "max": 0.5},
    "door_height": {"type": "FloatProperty", "default": 2.4, "min": 1.5, "max": 5.0},
    "door_step_count": {"type": "IntProperty", "default": 2, "min": 0, "max": 8},
    "door_width": {"type": "FloatProperty", "default": 1.2, "min": 0.4, "max": 4.0},
    "fountain_height": {"type": "FloatProperty", "default": 2.5, "min": 0.5, "max": 8.0},
    "fountain_radius": {"type": "FloatProperty", "default": 1.5, "min": 0.3, "max": 8.0},
    "fountain_tier_scale": {"type": "FloatProperty", "default": 0.65, "min": 0.3, "max": 0.9},
    "fountain_tiers": {"type": "IntProperty", "default": 3, "min": 1, "max": 6},
    "gothic_thickness": {"type": "FloatProperty", "default": 0.12, "min": 0.02, "max": 1.0},
    "harmonic_layers": {"type": "IntProperty", "default": 2, "min": 1, "max": 5},
    "lantern_glass_size": {"type": "FloatProperty", "default": 0.35, "min": 0.1, "max": 1.5},
    "lantern_height": {"type": "FloatProperty", "default": 3.0, "min": 1.0, "max": 8.0},
    "lantern_post_radius": {"type": "FloatProperty", "default": 0.06, "min": 0.02, "max": 0.3},
    "musical_freq_a": {"type": "FloatProperty", "default": 0.6, "min": 0.05, "max": 5.0},
    "musical_freq_b": {"type": "FloatProperty", "default": 1.2, "min": 0.05, "max": 5.0},
    "note_pattern": {"type": "EnumProperty", "default": 'QUARTER', "min": None, "max": None},
    "ogee_finial": {"type": "FloatProperty", "default": 0.4, "min": 0.0, "max": 2.0},
    "ogee_height": {"type": "FloatProperty", "default": 3.0, "min": 1.0, "max": 12.0},
    "ogee_shoulder": {"type": "FloatProperty", "default": 0.7, "min": 0.1, "max": 2.0},
    "ogee_swell": {"type": "FloatProperty", "default": 0.4, "min": 0.0, "max": 1.5},
    "ogee_width": {"type": "FloatProperty", "default": 2.0, "min": 0.5, "max": 8.0},
    "ornament_density": {"type": "FloatProperty", "default": 0.5, "min": 0.0, "max": 1.0},
    "pillar_capital_layers": {"type": "IntProperty", "default": 2, "min": 1, "max": 5},
    "pillar_capital_size": {"type": "FloatProperty", "default": 0.65, "min": 0.1, "max": 2.0},
    "pillar_flute_depth": {"type": "FloatProperty", "default": 0.025, "min": 0.0, "max": 0.2},
    "pillar_flutes": {"type": "IntProperty", "default": 16, "min": 0, "max": 48},
    "pillar_height": {"type": "FloatProperty", "default": 4.0, "min": 1.0, "max": 15.0},
    "pillar_radius": {"type": "FloatProperty", "default": 0.4, "min": 0.05, "max": 2.0},
    "rail_baluster_count": {"type": "IntProperty", "default": 24, "min": 4, "max": 200},
    "rail_baluster_radius": {"type": "FloatProperty", "default": 0.06, "min": 0.01, "max": 0.5},
    "rail_height": {"type": "FloatProperty", "default": 1.0, "min": 0.2, "max": 5.0},
    "rail_length": {"type": "FloatProperty", "default": 6.0, "min": 1.0, "max": 30.0},
    "rail_top_size": {"type": "FloatProperty", "default": 0.1, "min": 0.02, "max": 0.5},
    "railing_height": {"type": "FloatProperty", "default": None, "min": 0.1, "max": 20.0},
    "railing_length": {"type": "FloatProperty", "default": None, "min": 0.1, "max": 50.0},
    "stair_rise": {"type": "FloatProperty", "default": 0.25, "min": 0.05, "max": 1.0},
    "stair_run": {"type": "FloatProperty", "default": 0.40, "min": 0.1, "max": 2.0},
    "stair_spiral_deg": {"type": "FloatProperty", "default": 0.0, "min": -90.0, "max": 90.0},
    "stair_step_count": {"type": "IntProperty", "default": 12, "min": 2, "max": 80},
    "stair_width": {"type": "FloatProperty", "default": 1.6, "min": 0.5, "max": 8.0},
    "stair_with_rails": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "tempo_factor": {"type": "FloatProperty", "default": 1.0, "min": 0.1, "max": 4.0},
    "tile_grid_count": {"type": "IntProperty", "default": 6, "min": 1, "max": 30},
    "tile_pattern": {"type": "EnumProperty", "default": 'GRID', "min": None, "max": None},
    "tile_size": {"type": "FloatProperty", "default": 0.5, "min": 0.1, "max": 3.0},
    "tile_thickness": {"type": "FloatProperty", "default": 0.05, "min": 0.01, "max": 0.3},
    "window_arch_top": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "window_frame_width": {"type": "FloatProperty", "default": 0.08, "min": 0.01, "max": 0.5},
    "window_height": {"type": "FloatProperty", "default": 1.1, "min": 0.2, "max": 4.0},
    "window_sill_depth": {"type": "FloatProperty", "default": 0.15, "min": 0.0, "max": 0.5},
    "window_width": {"type": "FloatProperty", "default": 0.7, "min": 0.1, "max": 4.0},
}

import types as _types

def _make_props(extra=None):
    kv = {k: (v["default"] if v["default"] is not None else 0.0)
         for k, v in BUILDER_PARAM_DEFAULTS.items()}
    if extra:
        kv.update(extra)
    return _types.SimpleNamespace(**kv)

def _impl_build_railing(tree, PROPS, x_offset=0, y_offset=0, length=None, height=None):
    """AAA railing - curve-swept balusters + proper horizontal rails aligned to piece.

    v2.49 overhaul:
    * Balusters are vertical CurvePrimitiveLine segments swept with a decorative
      profile (round / ogee / fluted) - no more MeshCube / MeshCylinder instances.
    * Top and bottom rails are horizontal CurvePrimitiveLine segments swept with
      a slightly larger matching profile - seamless cap geometry, no floating cubes.
    * Balusters start at z=0 (piece floor), top rail sits at z=H - zero Z-gap.
    * Harmonic height modulation kept for musical whimsy.
    """
    L  = length if length is not None else PROPS.rail_length
    H  = height if height is not None else PROPS.rail_height
    br = getattr(PROPS, 'rail_baluster_radius', 0.04)
    ts = getattr(PROPS, 'rail_top_size',        0.07)
    n  = max(2, getattr(PROPS, 'rail_baluster_count', 8))
    bx = -1400 + x_offset
    spacing = L / max(1, n - 1)
    parts   = []

    # ── Shared baluster profile (picked from PROPS.aest_profile) ──────────
    bal_prof = _make_circle_profile(tree, br, resolution=10,
                                    loc=(bx - 300, -300), props=PROPS)
    if bal_prof is None:
        # Fallback: plain circle
        bal_prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (bx - 300, -300))
        if bal_prof:
            try:
                bal_prof.inputs['Resolution'].default_value = 10
                bal_prof.inputs['Radius'].default_value     = br
            except Exception:
                pass

    # ── Rail profile (slightly larger, always round for clean cap) ────────
    rail_prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (bx - 300, -600))
    if rail_prof:
        try:
            rail_prof.inputs['Resolution'].default_value = 10
            rail_prof.inputs['Radius'].default_value     = ts * 0.55
        except Exception:
            pass
    color_node(rail_prof, "railing") if rail_prof else None

    # ── Individual swept balusters ─────────────────────────────────────────
    # Use InstanceOnPoints so baluster count is a real parameter.
    # Each baluster: vertical CurvePrimitiveLine from (x, 0, 0) to (x, 0, H),
    # assembled as a single instance and placed along a point line.
    bal_line = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (bx, 0))
    if bal_line:
        try:
            bal_line.inputs['Start'].default_value = (0, 0, 0)
            bal_line.inputs['End'].default_value   = (0, 0, H)
        except Exception:
            pass
        color_node(bal_line, "railing")

    if bal_line and bal_prof:
        bal_sweep = _safe_node(tree, 'GeometryNodeCurveToMesh', (bx + 250, 0))
        if bal_sweep:
            _link(tree, bal_line.outputs['Curve'], bal_sweep.inputs['Curve'])
            _link(tree, bal_prof.outputs['Curve'], bal_sweep.inputs['Profile Curve'])
            try: bal_sweep.inputs['Fill Caps'].default_value = True
            except Exception: pass
            color_node(bal_sweep, "railing")
            bal_geom_out = bal_sweep.outputs['Mesh']
        else:
            bal_geom_out = None
    else:
        bal_geom_out = None

    # Point distribution along the railing length
    pt_line = _safe_node(tree, 'GeometryNodeMeshLine', (bx, 400))
    if pt_line:
        try:
            pt_line.mode = 'END_POINTS'
            pt_line.inputs['Count'].default_value          = n
            pt_line.inputs['Start Location'].default_value = (-L / 2, 0, 0)
            pt_line.inputs['Offset'].default_value         = (L, 0, 0)
        except Exception:
            pass
        color_node(pt_line, "railing")

    if pt_line and bal_geom_out is not None:
        iop = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (bx + 500, 300))
        if iop:
            _link(tree, pt_line.outputs['Mesh'], iop.inputs['Points'])
            _link(tree, bal_geom_out, iop.inputs['Instance'])
            color_node(iop, "railing")

            # Musical height modulation - scale Z per baluster
            idx = _safe_node(tree, 'GeometryNodeInputIndex', (bx, -300))
            if idx:
                try:
                    harmonic = make_harmonic_value(
                        tree, idx.outputs['Index'],
                        PROPS.musical_freq_a, PROPS.musical_freq_b,
                        PROPS.harmonic_layers, bx + 200, -300)
                    mpr = _safe_node(tree, 'ShaderNodeMapRange', (bx + 900, -300))
                    if mpr:
                        try:
                            mpr.inputs['From Min'].default_value = -2.0
                            mpr.inputs['From Max'].default_value  =  2.0
                            mpr.inputs['To Min'].default_value    =  1.0 - PROPS.ornament_density * 0.35
                            mpr.inputs['To Max'].default_value    =  1.0 + PROPS.ornament_density * 0.35
                        except Exception: pass
                        _link(tree, harmonic, mpr.inputs['Value'])
                        svec = _safe_node(tree, 'ShaderNodeCombineXYZ', (bx + 1100, -300))
                        if svec:
                            try:
                                svec.inputs['X'].default_value = 1.0
                                svec.inputs['Y'].default_value = 1.0
                            except Exception: pass
                            _link(tree, mpr.outputs['Result'], svec.inputs['Z'])
                            si = _safe_node(tree, 'GeometryNodeScaleInstances', (bx + 1300, 300))
                            if si:
                                _link(tree, iop.outputs['Instances'], si.inputs['Instances'])
                                _link(tree, svec.outputs['Vector'],   si.inputs['Scale'])
                                iop_out = si.outputs['Instances']
                            else:
                                iop_out = iop.outputs['Instances']
                        else:
                            iop_out = iop.outputs['Instances']
                except Exception:
                    iop_out = iop.outputs['Instances']
            else:
                iop_out = iop.outputs['Instances']

            rea = _safe_node(tree, 'GeometryNodeRealizeInstances', (bx + 1600, 300))
            if rea:
                _link(tree, iop_out, rea.inputs['Geometry'])
                parts.append(rea.outputs['Geometry'])

    # ── Top rail - horizontal sweep ────────────────────────────────────────
    top_curve = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (bx, 700))
    if top_curve:
        try:
            top_curve.inputs['Start'].default_value = (-L / 2, 0, H)
            top_curve.inputs['End'].default_value   = ( L / 2, 0, H)
        except Exception:
            pass
        color_node(top_curve, "railing")
        if rail_prof:
            top_sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (bx + 250, 700))
            if top_sw:
                _link(tree, top_curve.outputs['Curve'], top_sw.inputs['Curve'])
                _link(tree, rail_prof.outputs['Curve'], top_sw.inputs['Profile Curve'])
                try: top_sw.inputs['Fill Caps'].default_value = True
                except Exception: pass
                color_node(top_sw, "railing")
                parts.append(top_sw.outputs['Mesh'])

    # ── Bottom rail - horizontal sweep ────────────────────────────────────
    bot_curve = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (bx, 900))
    if bot_curve:
        try:
            bot_curve.inputs['Start'].default_value = (-L / 2, 0, ts * 0.5)
            bot_curve.inputs['End'].default_value   = ( L / 2, 0, ts * 0.5)
        except Exception:
            pass
        color_node(bot_curve, "railing")
        if rail_prof:
            bot_sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (bx + 250, 900))
            if bot_sw:
                _link(tree, bot_curve.outputs['Curve'], bot_sw.inputs['Curve'])
                _link(tree, rail_prof.outputs['Curve'], bot_sw.inputs['Profile Curve'])
                try: bot_sw.inputs['Fill Caps'].default_value = True
                except Exception: pass
                color_node(bot_sw, "railing")
                parts.append(bot_sw.outputs['Mesh'])

    # ── Mid rail (optional decorative) at 40% height ──────────────────────
    if n > 4:
        mid_curve = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (bx, 1100))
        if mid_curve:
            try:
                mid_curve.inputs['Start'].default_value = (-L / 2, 0, H * 0.4)
                mid_curve.inputs['End'].default_value   = ( L / 2, 0, H * 0.4)
            except Exception:
                pass
            color_node(mid_curve, "railing")
            if rail_prof:
                mid_sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (bx + 250, 1100))
                if mid_sw:
                    _link(tree, mid_curve.outputs['Curve'], mid_sw.inputs['Curve'])
                    _link(tree, rail_prof.outputs['Curve'], mid_sw.inputs['Profile Curve'])
                    try: mid_sw.inputs['Fill Caps'].default_value = True
                    except Exception: pass
                    color_node(mid_sw, "railing")
                    parts.append(mid_sw.outputs['Mesh'])

    # ── Join all parts ─────────────────────────────────────────────────────
    if not parts:
        return None
    join = _safe_node(tree, 'GeometryNodeJoinGeometry', (bx + 2000, 0))
    if join is None:
        return parts[0] if parts else None
    for p in parts:
        _link(tree, p, join.inputs['Geometry'])
    color_node(join, "output")
    geom = join.outputs['Geometry']

    # Optional Z offset for alignment to parent piece surface
    if y_offset != 0:
        off_t = _safe_node(tree, 'GeometryNodeTransform', (bx + 2200, 0))
        if off_t:
            try: off_t.inputs['Translation'].default_value = (0, 0, y_offset)
            except Exception: pass
            _link(tree, geom, off_t.inputs['Geometry'])
            geom = off_t.outputs['Geometry']

    return geom



def build_railing_group(group_name="MEL_railing"):
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
    x_offset = 0
    y_offset = 0
    length = PROPS.railing_length if getattr(PROPS, 'railing_length', 0.0) else None
    height = PROPS.railing_height if getattr(PROPS, 'railing_height', 0.0) else None
    def _impl():
        """AAA railing - curve-swept balusters + proper horizontal rails aligned to piece.

        v2.49 overhaul:
        * Balusters are vertical CurvePrimitiveLine segments swept with a decorative
          profile (round / ogee / fluted) - no more MeshCube / MeshCylinder instances.
        * Top and bottom rails are horizontal CurvePrimitiveLine segments swept with
          a slightly larger matching profile - seamless cap geometry, no floating cubes.
        * Balusters start at z=0 (piece floor), top rail sits at z=H - zero Z-gap.
        * Harmonic height modulation kept for musical whimsy.
        """
        L  = length if length is not None else PROPS.rail_length
        H  = height if height is not None else PROPS.rail_height
        br = getattr(PROPS, 'rail_baluster_radius', 0.04)
        ts = getattr(PROPS, 'rail_top_size',        0.07)
        n  = max(2, getattr(PROPS, 'rail_baluster_count', 8))
        bx = -1400 + x_offset
        spacing = L / max(1, n - 1)
        parts   = []

        # ── Shared baluster profile (picked from PROPS.aest_profile) ──────────
        bal_prof = _make_circle_profile(tree, br, resolution=10,
                                        loc=(bx - 300, -300), props=PROPS)
        if bal_prof is None:
            # Fallback: plain circle
            bal_prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (bx - 300, -300))
            if bal_prof:
                try:
                    bal_prof.inputs['Resolution'].default_value = 10
                    bal_prof.inputs['Radius'].default_value     = br
                except Exception:
                    pass

        # ── Rail profile (slightly larger, always round for clean cap) ────────
        rail_prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (bx - 300, -600))
        if rail_prof:
            try:
                rail_prof.inputs['Resolution'].default_value = 10
                rail_prof.inputs['Radius'].default_value     = ts * 0.55
            except Exception:
                pass
        color_node(rail_prof, "railing") if rail_prof else None

        # ── Individual swept balusters ─────────────────────────────────────────
        # Use InstanceOnPoints so baluster count is a real parameter.
        # Each baluster: vertical CurvePrimitiveLine from (x, 0, 0) to (x, 0, H),
        # assembled as a single instance and placed along a point line.
        bal_line = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (bx, 0))
        if bal_line:
            try:
                bal_line.inputs['Start'].default_value = (0, 0, 0)
                bal_line.inputs['End'].default_value   = (0, 0, H)
            except Exception:
                pass
            color_node(bal_line, "railing")

        if bal_line and bal_prof:
            bal_sweep = _safe_node(tree, 'GeometryNodeCurveToMesh', (bx + 250, 0))
            if bal_sweep:
                _link(tree, bal_line.outputs['Curve'], bal_sweep.inputs['Curve'])
                _link(tree, bal_prof.outputs['Curve'], bal_sweep.inputs['Profile Curve'])
                try: bal_sweep.inputs['Fill Caps'].default_value = True
                except Exception: pass
                color_node(bal_sweep, "railing")
                bal_geom_out = bal_sweep.outputs['Mesh']
            else:
                bal_geom_out = None
        else:
            bal_geom_out = None

        # Point distribution along the railing length
        pt_line = _safe_node(tree, 'GeometryNodeMeshLine', (bx, 400))
        if pt_line:
            try:
                pt_line.mode = 'END_POINTS'
                pt_line.inputs['Count'].default_value          = n
                pt_line.inputs['Start Location'].default_value = (-L / 2, 0, 0)
                pt_line.inputs['Offset'].default_value         = (L, 0, 0)
            except Exception:
                pass
            color_node(pt_line, "railing")

        if pt_line and bal_geom_out is not None:
            iop = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (bx + 500, 300))
            if iop:
                _link(tree, pt_line.outputs['Mesh'], iop.inputs['Points'])
                _link(tree, bal_geom_out, iop.inputs['Instance'])
                color_node(iop, "railing")

                # Musical height modulation - scale Z per baluster
                idx = _safe_node(tree, 'GeometryNodeInputIndex', (bx, -300))
                if idx:
                    try:
                        harmonic = make_harmonic_value(
                            tree, idx.outputs['Index'],
                            PROPS.musical_freq_a, PROPS.musical_freq_b,
                            PROPS.harmonic_layers, bx + 200, -300)
                        mpr = _safe_node(tree, 'ShaderNodeMapRange', (bx + 900, -300))
                        if mpr:
                            try:
                                mpr.inputs['From Min'].default_value = -2.0
                                mpr.inputs['From Max'].default_value  =  2.0
                                mpr.inputs['To Min'].default_value    =  1.0 - PROPS.ornament_density * 0.35
                                mpr.inputs['To Max'].default_value    =  1.0 + PROPS.ornament_density * 0.35
                            except Exception: pass
                            _link(tree, harmonic, mpr.inputs['Value'])
                            svec = _safe_node(tree, 'ShaderNodeCombineXYZ', (bx + 1100, -300))
                            if svec:
                                try:
                                    svec.inputs['X'].default_value = 1.0
                                    svec.inputs['Y'].default_value = 1.0
                                except Exception: pass
                                _link(tree, mpr.outputs['Result'], svec.inputs['Z'])
                                si = _safe_node(tree, 'GeometryNodeScaleInstances', (bx + 1300, 300))
                                if si:
                                    _link(tree, iop.outputs['Instances'], si.inputs['Instances'])
                                    _link(tree, svec.outputs['Vector'],   si.inputs['Scale'])
                                    iop_out = si.outputs['Instances']
                                else:
                                    iop_out = iop.outputs['Instances']
                            else:
                                iop_out = iop.outputs['Instances']
                    except Exception:
                        iop_out = iop.outputs['Instances']
                else:
                    iop_out = iop.outputs['Instances']

                rea = _safe_node(tree, 'GeometryNodeRealizeInstances', (bx + 1600, 300))
                if rea:
                    _link(tree, iop_out, rea.inputs['Geometry'])
                    parts.append(rea.outputs['Geometry'])

        # ── Top rail - horizontal sweep ────────────────────────────────────────
        top_curve = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (bx, 700))
        if top_curve:
            try:
                top_curve.inputs['Start'].default_value = (-L / 2, 0, H)
                top_curve.inputs['End'].default_value   = ( L / 2, 0, H)
            except Exception:
                pass
            color_node(top_curve, "railing")
            if rail_prof:
                top_sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (bx + 250, 700))
                if top_sw:
                    _link(tree, top_curve.outputs['Curve'], top_sw.inputs['Curve'])
                    _link(tree, rail_prof.outputs['Curve'], top_sw.inputs['Profile Curve'])
                    try: top_sw.inputs['Fill Caps'].default_value = True
                    except Exception: pass
                    color_node(top_sw, "railing")
                    parts.append(top_sw.outputs['Mesh'])

        # ── Bottom rail - horizontal sweep ────────────────────────────────────
        bot_curve = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (bx, 900))
        if bot_curve:
            try:
                bot_curve.inputs['Start'].default_value = (-L / 2, 0, ts * 0.5)
                bot_curve.inputs['End'].default_value   = ( L / 2, 0, ts * 0.5)
            except Exception:
                pass
            color_node(bot_curve, "railing")
            if rail_prof:
                bot_sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (bx + 250, 900))
                if bot_sw:
                    _link(tree, bot_curve.outputs['Curve'], bot_sw.inputs['Curve'])
                    _link(tree, rail_prof.outputs['Curve'], bot_sw.inputs['Profile Curve'])
                    try: bot_sw.inputs['Fill Caps'].default_value = True
                    except Exception: pass
                    color_node(bot_sw, "railing")
                    parts.append(bot_sw.outputs['Mesh'])

        # ── Mid rail (optional decorative) at 40% height ──────────────────────
        if n > 4:
            mid_curve = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (bx, 1100))
            if mid_curve:
                try:
                    mid_curve.inputs['Start'].default_value = (-L / 2, 0, H * 0.4)
                    mid_curve.inputs['End'].default_value   = ( L / 2, 0, H * 0.4)
                except Exception:
                    pass
                color_node(mid_curve, "railing")
                if rail_prof:
                    mid_sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (bx + 250, 1100))
                    if mid_sw:
                        _link(tree, mid_curve.outputs['Curve'], mid_sw.inputs['Curve'])
                        _link(tree, rail_prof.outputs['Curve'], mid_sw.inputs['Profile Curve'])
                        try: mid_sw.inputs['Fill Caps'].default_value = True
                        except Exception: pass
                        color_node(mid_sw, "railing")
                        parts.append(mid_sw.outputs['Mesh'])

        # ── Join all parts ─────────────────────────────────────────────────────
        if not parts:
            return None
        join = _safe_node(tree, 'GeometryNodeJoinGeometry', (bx + 2000, 0))
        if join is None:
            return parts[0] if parts else None
        for p in parts:
            _link(tree, p, join.inputs['Geometry'])
        color_node(join, "output")
        geom = join.outputs['Geometry']

        # Optional Z offset for alignment to parent piece surface
        if y_offset != 0:
            off_t = _safe_node(tree, 'GeometryNodeTransform', (bx + 2200, 0))
            if off_t:
                try: off_t.inputs['Translation'].default_value = (0, 0, y_offset)
                except Exception: pass
                _link(tree, geom, off_t.inputs['Geometry'])
                geom = off_t.outputs['Geometry']

        return geom


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_railing")
    return tree, gin, gout

register_builder(
    "MEL_railing", build_railing_group,
    "Railing", "Core form builder (absorbed from monolith build_railing).",
    category="structures")


def build_staircase_group(group_name="MEL_staircase"):
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
        rise  = PROPS.stair_rise
        run_  = PROPS.stair_run
        width = PROPS.stair_width
        spiral= math.radians(PROPS.stair_spiral_deg)
        count = max(2, PROPS.stair_step_count)

        # Step path line
        line = tree.nodes.new('GeometryNodeMeshLine'); line.location = (base_x, 200); color_node(line, "stair")
        line.mode = 'OFFSET'
        line.inputs['Count'].default_value = count
        line.inputs['Start Location'].default_value = (0, 0, 0)
        line.inputs['Offset'].default_value = (run_, 0, rise)

        # Step block
        step = tree.nodes.new('GeometryNodeMeshCube'); step.location = (base_x, -200); color_node(step, "stair")
        step.inputs['Size'].default_value = (run_, width, rise * 0.9)

        inst = tree.nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (base_x+300, 0)
        tree.links.new(line.outputs['Mesh'], inst.inputs['Points'])
        tree.links.new(step.outputs['Mesh'], inst.inputs['Instance'])

        # Spiral rotation
        idx = tree.nodes.new('GeometryNodeInputIndex'); idx.location = (base_x, -500)
        rot_mul = tree.nodes.new('ShaderNodeMath'); rot_mul.location = (base_x+200, -500); rot_mul.operation = 'MULTIPLY'
        rot_mul.inputs[1].default_value = spiral
        tree.links.new(idx.outputs['Index'], rot_mul.inputs[0])
        rvec = tree.nodes.new('ShaderNodeCombineXYZ'); rvec.location = (base_x+400, -500)
        rvec.inputs['X'].default_value = 0; rvec.inputs['Y'].default_value = 0
        tree.links.new(rot_mul.outputs['Value'], rvec.inputs['Z'])
        rot_inst = tree.nodes.new('GeometryNodeRotateInstances'); rot_inst.location = (base_x+600, 0)
        tree.links.new(inst.outputs['Instances'], rot_inst.inputs['Instances'])
        tree.links.new(rvec.outputs['Vector'], rot_inst.inputs['Rotation'])

        realize = tree.nodes.new('GeometryNodeRealizeInstances'); realize.location = (base_x+900, 0)
        tree.links.new(rot_inst.outputs['Instances'], realize.inputs['Geometry'])

        geom = realize.outputs['Geometry']

        # Optional side balusters (whimsical)
        if PROPS.stair_with_rails:
            baluster_line = tree.nodes.new('GeometryNodeMeshLine'); baluster_line.location = (base_x, 600)
            baluster_line.mode = 'OFFSET'
            baluster_line.inputs['Count'].default_value = count
            baluster_line.inputs['Start Location'].default_value = (0, width/2, rise*0.5)
            baluster_line.inputs['Offset'].default_value = (run_, 0, rise)
            color_node(baluster_line, "ornament")

            bal = tree.nodes.new('GeometryNodeMeshCylinder'); bal.location = (base_x, 800)
            bal.inputs['Vertices'].default_value = 6
            bal.inputs['Radius'].default_value = 0.04
            bal.inputs['Depth'].default_value = 0.5
            color_node(bal, "ornament")

            inst_b = tree.nodes.new('GeometryNodeInstanceOnPoints'); inst_b.location = (base_x+300, 700)
            tree.links.new(baluster_line.outputs['Mesh'], inst_b.inputs['Points'])
            tree.links.new(bal.outputs['Mesh'], inst_b.inputs['Instance'])

            # Musical height modulation
            idx2 = tree.nodes.new('GeometryNodeInputIndex'); idx2.location = (base_x, 1000)
            h_val = make_harmonic_value(tree, idx2.outputs['Index'],
                                         PROPS.musical_freq_a, PROPS.musical_freq_b,
                                         PROPS.harmonic_layers, base_x+200, 1000)
            map_h = tree.nodes.new('ShaderNodeMapRange'); map_h.location = (base_x+1000, 1000)
            map_h.inputs['From Min'].default_value = -2; map_h.inputs['From Max'].default_value = 2
            map_h.inputs['To Min'].default_value = 1.0 - PROPS.ornament_density * 0.5
            map_h.inputs['To Max'].default_value = 1.0 + PROPS.ornament_density * 0.5
            tree.links.new(h_val, map_h.inputs['Value'])

            sv = tree.nodes.new('ShaderNodeCombineXYZ'); sv.location = (base_x+1200, 1000)
            sv.inputs['X'].default_value = 1; sv.inputs['Y'].default_value = 1
            tree.links.new(map_h.outputs['Result'], sv.inputs['Z'])

            scale_b = tree.nodes.new('GeometryNodeScaleInstances'); scale_b.location = (base_x+1400, 700)
            tree.links.new(inst_b.outputs['Instances'], scale_b.inputs['Instances'])
            tree.links.new(sv.outputs['Vector'], scale_b.inputs['Scale'])

            realize_b = tree.nodes.new('GeometryNodeRealizeInstances'); realize_b.location = (base_x+1600, 700)
            tree.links.new(scale_b.outputs['Instances'], realize_b.inputs['Geometry'])

            # Mirror on the other side too
            mirror_trans = tree.nodes.new('GeometryNodeTransform'); mirror_trans.location = (base_x+1800, 900)
            mirror_trans.inputs['Translation'].default_value = (0, -width, 0)
            tree.links.new(realize_b.outputs['Geometry'], mirror_trans.inputs['Geometry'])

            # Join sides
            join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+2100, 300); color_node(join, "output")
            tree.links.new(geom, join.inputs['Geometry'])
            tree.links.new(realize_b.outputs['Geometry'], join.inputs['Geometry'])
            tree.links.new(mirror_trans.outputs['Geometry'], join.inputs['Geometry'])
            geom = join.outputs['Geometry']

        return geom


    # ----------------------------------------------------------------------
    # BUILDER: ARCH
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_staircase")
    return tree, gin, gout

register_builder(
    "MEL_staircase", build_staircase_group,
    "Staircase", "Core form builder (absorbed from monolith build_staircase).",
    category="structures")


def build_arch_group(group_name="MEL_arch"):
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
        R = PROPS.arch_radius
        sweep = math.radians(PROPS.arch_sweep_deg)

        # Base arc
        curve = tree.nodes.new('GeometryNodeCurveArc'); curve.location = (base_x, 200); color_node(curve, "arch")
        curve.mode = 'RADIUS'
        curve.inputs['Resolution'].default_value = 32
        curve.inputs['Radius'].default_value = R
        curve.inputs['Sweep Angle'].default_value = sweep

        # Profile
        profile = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); profile.location = (base_x, -200); color_node(profile, "arch")
        profile.mode = 'RADIUS'
        profile.inputs['Resolution'].default_value = 8
        profile.inputs['Radius'].default_value = PROPS.arch_thickness

        # Sweep
        sweep_node = tree.nodes.new('GeometryNodeCurveToMesh'); sweep_node.location = (base_x+300, 0); color_node(sweep_node, "arch")
        tree.links.new(curve.outputs['Curve'], sweep_node.inputs['Curve'])
        tree.links.new(profile.outputs['Curve'], sweep_node.inputs['Profile Curve'])
        sweep_node.inputs['Fill Caps'].default_value = True

        # Musical wave deformation on sweep
        idx = tree.nodes.new('GeometryNodeInputIndex'); idx.location = (base_x, -500)
        harmonic = make_harmonic_value(tree, idx.outputs['Index'],
                                        PROPS.musical_freq_a, PROPS.musical_freq_b,
                                        PROPS.harmonic_layers, base_x+200, -500)
        sc = tree.nodes.new('ShaderNodeMath'); sc.location = (base_x+1000, -500); sc.operation = 'MULTIPLY'
        sc.inputs[1].default_value = PROPS.ornament_density * 0.1
        tree.links.new(harmonic, sc.inputs[0])

        ovec = tree.nodes.new('ShaderNodeCombineXYZ'); ovec.location = (base_x+1200, -500)
        ovec.inputs['X'].default_value = 0; ovec.inputs['Y'].default_value = 0
        tree.links.new(sc.outputs['Value'], ovec.inputs['Z'])

        set_pos = tree.nodes.new('GeometryNodeSetPosition'); set_pos.location = (base_x+1400, 0); color_node(set_pos, "deform")
        tree.links.new(sweep_node.outputs['Mesh'], set_pos.inputs['Geometry'])
        tree.links.new(ovec.outputs['Vector'], set_pos.inputs['Offset'])

        geom = set_pos.outputs['Geometry']

        # Ribs
        if PROPS.arch_rib_count > 0:
            sample = tree.nodes.new('GeometryNodeResampleCurve'); sample.location = (base_x+300, 500); color_node(sample, "ornament")
            sample.inputs['Mode'].default_value = 'Count'
            sample.inputs['Count'].default_value = PROPS.arch_rib_count
            tree.links.new(curve.outputs['Curve'], sample.inputs['Curve'])

            c2p = tree.nodes.new('GeometryNodeCurveToPoints'); c2p.location = (base_x+500, 500)
            c2p.mode = 'EVALUATED'
            tree.links.new(sample.outputs['Curve'], c2p.inputs['Curve'])

            rib = tree.nodes.new('GeometryNodeMeshCylinder'); rib.location = (base_x+500, 700); color_node(rib, "ornament")
            rib.inputs['Vertices'].default_value = 12
            rib.inputs['Radius'].default_value = PROPS.arch_rib_radius
            rib.inputs['Depth'].default_value = max(0.05, PROPS.arch_thickness * 0.6)

            inst = tree.nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (base_x+800, 500)
            tree.links.new(c2p.outputs['Points'], inst.inputs['Points'])
            tree.links.new(rib.outputs['Mesh'], inst.inputs['Instance'])
            tree.links.new(c2p.outputs['Rotation'], inst.inputs['Rotation'])

            # Musical scale modulation
            idx2 = tree.nodes.new('GeometryNodeInputIndex'); idx2.location = (base_x+500, 1000)
            h2 = make_harmonic_value(tree, idx2.outputs['Index'],
                                      PROPS.musical_freq_a, PROPS.musical_freq_b,
                                      PROPS.harmonic_layers, base_x+700, 1000)
            sm = tree.nodes.new('ShaderNodeMapRange'); sm.location = (base_x+1500, 1000)
            sm.inputs['From Min'].default_value = -2; sm.inputs['From Max'].default_value = 2
            sm.inputs['To Min'].default_value = 1.0 - PROPS.ornament_density * 0.4
            sm.inputs['To Max'].default_value = 1.0 + PROPS.ornament_density * 0.4
            tree.links.new(h2, sm.inputs['Value'])
            sv = tree.nodes.new('ShaderNodeCombineXYZ'); sv.location = (base_x+1700, 1000)
            tree.links.new(sm.outputs['Result'], sv.inputs['X'])
            tree.links.new(sm.outputs['Result'], sv.inputs['Y'])
            tree.links.new(sm.outputs['Result'], sv.inputs['Z'])

            scale_inst = tree.nodes.new('GeometryNodeScaleInstances'); scale_inst.location = (base_x+1900, 500)
            tree.links.new(inst.outputs['Instances'], scale_inst.inputs['Instances'])
            tree.links.new(sv.outputs['Vector'], scale_inst.inputs['Scale'])

            realize = tree.nodes.new('GeometryNodeRealizeInstances'); realize.location = (base_x+2100, 500)
            tree.links.new(scale_inst.outputs['Instances'], realize.inputs['Geometry'])

            join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+2400, 0); color_node(join, "output")
            tree.links.new(geom, join.inputs['Geometry'])
            tree.links.new(realize.outputs['Geometry'], join.inputs['Geometry'])
            geom = join.outputs['Geometry']

        return geom


    # ----------------------------------------------------------------------
    # BUILDER: BUTTRESS
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_arch")
    return tree, gin, gout

register_builder(
    "MEL_arch", build_arch_group,
    "Arch", "Core form builder (absorbed from monolith build_arch).",
    category="structures")


def build_pillar_group(group_name="MEL_pillar"):
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
        """Classical fluted pillar with capital + base.
        v2.52: When Higgsas is available, uses NTSpin to lathe a custom profile
        (wider at base, entasis bulge at 1/3) -> NTTaper for classical entasis.
        Falls back to cylinder + cosine-flute deform when Higgsas is absent."""
        R = PROPS.pillar_radius
        H = PROPS.pillar_height
        n_flutes = PROPS.pillar_flutes

        # ── Higgsas path: NTSpin profile + NTTaper entasis ─────────────────
        higg_spin = _higg_node(tree, 'NTSpin', (base_x, 0))
        if higg_spin is not None:
            # Build a half-profile curve (quarter of a circle for the shaft cross-section)
            # Use a CurveArc for the shaft silhouette, then spin 360deg
            profile_arc = _safe_node(tree, 'GeometryNodeCurveArc', (base_x - 300, 0))
            if profile_arc:
                try:
                    profile_arc.mode = 'RADIUS'
                    profile_arc.inputs['Radius'].default_value      = R
                    profile_arc.inputs['Start Angle'].default_value = 0
                    profile_arc.inputs['Sweep Angle'].default_value = math.pi / 2
                    profile_arc.inputs['Resolution'].default_value  = 8
                except Exception: pass
                fill = _safe_node(tree, 'GeometryNodeFillCurve', (base_x - 100, 0))
                if fill:
                    _link(tree, profile_arc.outputs['Curve'], fill.inputs['Curve'])
                    _higg_input(higg_spin, 'Angle', math.tau)   # full 360deg
                    _higg_input(higg_spin, 'Steps', max(16, n_flutes * 2))
                    try:
                        _link(tree, fill.outputs['Mesh'], higg_spin.inputs['Mesh'])
                    except Exception: pass
            # Apply Higgsas NTTaper for entasis (slight bulge at mid-height)
            higg_taper = _higg_node(tree, 'NTTaper', (base_x + 400, 0))
            geom_out = higg_spin.outputs.get('Mesh') or higg_spin.outputs[0]
            if higg_taper is not None:
                _higg_input(higg_taper, 'Upper Factor', 0.90)
                _higg_input(higg_taper, 'Lower Factor', 1.08)
                try:
                    _link(tree, geom_out, higg_taper.inputs['Geometry'])
                    geom_out = higg_taper.outputs['Geometry']
                except Exception: pass
            # Extrude to height
            ext_t = _safe_node(tree, 'GeometryNodeTransform', (base_x + 700, 0))
            if ext_t:
                try: ext_t.inputs['Scale'].default_value = (1, 1, H)
                except Exception: pass
                _link(tree, geom_out, ext_t.inputs['Geometry'])
                geom_out = ext_t.outputs['Geometry']
            color_node(higg_spin, 'pillar')
            # Still add native capital + base on top
            # Fall through to capital code below with geom = geom_out
            geom = geom_out
            # Skip the cylinder+flute section - jump straight to capital
            # (done via goto-equivalent: just don't define shaft; set n_flutes=0 for capital section)
            shaft = None
            n_flutes_orig = n_flutes
            n_flutes = 0   # suppress flute deform (already handled by NTSpin)
            # Rerun capital section inline
            cap = tree.nodes.new('GeometryNodeMeshCone'); cap.location = (base_x+300, 700); color_node(cap, "pillar")
            cap.inputs['Vertices'].default_value     = max(16, n_flutes_orig * 2)
            cap.inputs['Radius Top'].default_value   = PROPS.pillar_capital_size
            cap.inputs['Radius Bottom'].default_value= R + 0.05
            cap.inputs['Depth'].default_value        = 0.4
            cap_t = tree.nodes.new('GeometryNodeTransform'); cap_t.location = (base_x+600, 700)
            cap_t.inputs['Translation'].default_value = (0, 0, H/2 + 0.2)
            tree.links.new(cap.outputs['Mesh'], cap_t.inputs['Geometry'])
            parts = [geom, cap_t.outputs['Geometry']]
            for layer in range(PROPS.pillar_capital_layers):
                ring = tree.nodes.new('GeometryNodeMeshCylinder'); ring.location = (base_x+600, 700 + layer*200); color_node(ring, "ornament")
                ring.inputs['Vertices'].default_value = 16
                ring.inputs['Radius'].default_value  = PROPS.pillar_capital_size * (1.0 - layer*0.08)
                ring.inputs['Depth'].default_value   = 0.06
                ring_t = tree.nodes.new('GeometryNodeTransform'); ring_t.location = (base_x+900, 700 + layer*200)
                ring_t.inputs['Translation'].default_value = (0, 0, H/2 + 0.4 + layer*0.1)
                tree.links.new(ring.outputs['Mesh'], ring_t.inputs['Geometry'])
                parts.append(ring_t.outputs['Geometry'])
            base_cone = tree.nodes.new('GeometryNodeMeshCone'); base_cone.location = (base_x+300, -1000); color_node(base_cone, "pillar")
            base_cone.inputs['Vertices'].default_value    = max(16, n_flutes_orig * 2)
            base_cone.inputs['Radius Top'].default_value  = R + 0.05
            base_cone.inputs['Radius Bottom'].default_value = PROPS.pillar_capital_size
            base_cone.inputs['Depth'].default_value       = 0.4
            base_t = tree.nodes.new('GeometryNodeTransform'); base_t.location = (base_x+600, -1000)
            base_t.inputs['Translation'].default_value = (0, 0, -H/2 - 0.2)
            tree.links.new(base_cone.outputs['Mesh'], base_t.inputs['Geometry'])
            parts.append(base_t.outputs['Geometry'])
            join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+1700, 0); color_node(join, "output")
            for p in parts: tree.links.new(p, join.inputs['Geometry'])
            return join.outputs['Geometry']

        # ── Native fallback: cylinder + cosine-flute deform ────────────────
        shaft = tree.nodes.new('GeometryNodeMeshCylinder'); shaft.location = (base_x, 0); color_node(shaft, "pillar")
        shaft.inputs['Vertices'].default_value = max(16, n_flutes * 2)
        shaft.inputs['Side Segments'].default_value = 8
        shaft.inputs['Radius'].default_value = R
        shaft.inputs['Depth'].default_value = H

        geom = shaft.outputs['Mesh']

        # Flutes via radial cosine on radius
        if n_flutes > 0 and PROPS.pillar_flute_depth > 0.001:
            pos = tree.nodes.new('GeometryNodeInputPosition'); pos.location = (base_x, -400); color_node(pos, "input")
            sep = tree.nodes.new('ShaderNodeSeparateXYZ'); sep.location = (base_x+200, -400)
            tree.links.new(pos.outputs['Position'], sep.inputs['Vector'])

            atan2 = tree.nodes.new('ShaderNodeMath'); atan2.location = (base_x+400, -400); atan2.operation = 'ARCTAN2'
            tree.links.new(sep.outputs['Y'], atan2.inputs[0])
            tree.links.new(sep.outputs['X'], atan2.inputs[1])

            flute_freq = tree.nodes.new('ShaderNodeMath'); flute_freq.location = (base_x+600, -400); flute_freq.operation = 'MULTIPLY'
            flute_freq.inputs[1].default_value = float(n_flutes)
            tree.links.new(atan2.outputs['Value'], flute_freq.inputs[0])

            flute_cos = tree.nodes.new('ShaderNodeMath'); flute_cos.location = (base_x+800, -400); flute_cos.operation = 'COSINE'
            tree.links.new(flute_freq.outputs['Value'], flute_cos.inputs[0])
            color_node(flute_cos, "ornament")

            flute_amp = tree.nodes.new('ShaderNodeMath'); flute_amp.location = (base_x+1000, -400); flute_amp.operation = 'MULTIPLY'
            flute_amp.inputs[1].default_value = PROPS.pillar_flute_depth
            tree.links.new(flute_cos.outputs['Value'], flute_amp.inputs[0])

            rad_vec = tree.nodes.new('ShaderNodeCombineXYZ'); rad_vec.location = (base_x+800, -200)
            tree.links.new(sep.outputs['X'], rad_vec.inputs['X'])
            tree.links.new(sep.outputs['Y'], rad_vec.inputs['Y'])
            rad_vec.inputs['Z'].default_value = 0

            norm = tree.nodes.new('ShaderNodeVectorMath'); norm.location = (base_x+1000, -200); norm.operation = 'NORMALIZE'
            tree.links.new(rad_vec.outputs['Vector'], norm.inputs[0])

            flute_offset = tree.nodes.new('ShaderNodeVectorMath'); flute_offset.location = (base_x+1200, -300); flute_offset.operation = 'SCALE'
            tree.links.new(norm.outputs['Vector'], flute_offset.inputs[0])
            tree.links.new(flute_amp.outputs['Value'], flute_offset.inputs['Scale'])

            set_flute = tree.nodes.new('GeometryNodeSetPosition'); set_flute.location = (base_x+1400, 0); color_node(set_flute, "deform")
            tree.links.new(geom, set_flute.inputs['Geometry'])
            tree.links.new(flute_offset.outputs[0], set_flute.inputs['Offset'])
            geom = set_flute.outputs['Geometry']

        # Capital - tapered cone
        cap = tree.nodes.new('GeometryNodeMeshCone'); cap.location = (base_x, 700); color_node(cap, "pillar")
        cap.inputs['Vertices'].default_value = max(16, n_flutes * 2)
        cap.inputs['Radius Top'].default_value    = PROPS.pillar_capital_size
        cap.inputs['Radius Bottom'].default_value = R + 0.05
        cap.inputs['Depth'].default_value         = 0.4

        cap_t = tree.nodes.new('GeometryNodeTransform'); cap_t.location = (base_x+300, 700); color_node(cap_t, "pillar")
        cap_t.inputs['Translation'].default_value = (0, 0, H/2 + 0.2)
        tree.links.new(cap.outputs['Mesh'], cap_t.inputs['Geometry'])

        # Capital decorative rings
        parts = [geom, cap_t.outputs['Geometry']]
        for layer in range(PROPS.pillar_capital_layers):
            ring = tree.nodes.new('GeometryNodeMeshCylinder'); ring.location = (base_x+600, 700 + layer * 200); color_node(ring, "ornament")
            ring.inputs['Vertices'].default_value = 16
            ring.inputs['Radius'].default_value = PROPS.pillar_capital_size * (1.0 - layer * 0.08)
            ring.inputs['Depth'].default_value = 0.06

            ring_t = tree.nodes.new('GeometryNodeTransform'); ring_t.location = (base_x+900, 700 + layer * 200)
            ring_t.inputs['Translation'].default_value = (0, 0, H/2 + 0.4 + layer * 0.1)
            tree.links.new(ring.outputs['Mesh'], ring_t.inputs['Geometry'])
            parts.append(ring_t.outputs['Geometry'])

        # Base (mirror of capital)
        base = tree.nodes.new('GeometryNodeMeshCone'); base.location = (base_x, -1000); color_node(base, "pillar")
        base.inputs['Vertices'].default_value = max(16, n_flutes * 2)
        base.inputs['Radius Top'].default_value    = R + 0.05
        base.inputs['Radius Bottom'].default_value = PROPS.pillar_capital_size
        base.inputs['Depth'].default_value         = 0.4

        base_t = tree.nodes.new('GeometryNodeTransform'); base_t.location = (base_x+300, -1000); color_node(base_t, "pillar")
        base_t.inputs['Translation'].default_value = (0, 0, -H/2 - 0.2)
        tree.links.new(base.outputs['Mesh'], base_t.inputs['Geometry'])
        parts.append(base_t.outputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+1700, 0); color_node(join, "output")
        for p in parts:
            tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    # ----------------------------------------------------------------------
    # BUILDER: DOME
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_pillar")
    return tree, gin, gout

register_builder(
    "MEL_pillar", build_pillar_group,
    "Pillar", "Core form builder (absorbed from monolith build_pillar).",
    category="structures")


def build_dome_group(group_name="MEL_dome"):
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
        """Hemispherical dome with longitudinal ribs and optional spire."""
        R = PROPS.dome_radius

        # Top half of UV sphere via boolean cut
        sphere = tree.nodes.new('GeometryNodeMeshUVSphere'); sphere.location = (base_x, 0); color_node(sphere, "dome")
        sphere.inputs['Segments'].default_value = PROPS.dome_segments
        sphere.inputs['Rings'].default_value    = PROPS.dome_rings
        sphere.inputs['Radius'].default_value   = R

        cutter = tree.nodes.new('GeometryNodeMeshCube'); cutter.location = (base_x, -300); color_node(cutter, "dome")
        cutter.inputs['Size'].default_value = (R * 4, R * 4, R * 4)
        cut_t = tree.nodes.new('GeometryNodeTransform'); cut_t.location = (base_x+300, -300)
        cut_t.inputs['Translation'].default_value = (0, 0, -R * 2)
        tree.links.new(cutter.outputs['Mesh'], cut_t.inputs['Geometry'])

        bool_n = tree.nodes.new('GeometryNodeMeshBoolean'); bool_n.location = (base_x+600, 0); color_node(bool_n, "dome")
        bool_n.operation = 'DIFFERENCE'
        tree.links.new(sphere.outputs['Mesh'], bool_n.inputs[0])
        tree.links.new(cut_t.outputs['Geometry'], bool_n.inputs[1])

        parts = [bool_n.outputs[0]]

        # Ribs
        if PROPS.dome_rib_count > 0:
            # Rib profile
            rib_profile = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); rib_profile.location = (base_x, 600); color_node(rib_profile, "ornament")
            rib_profile.mode = 'RADIUS'
            rib_profile.inputs['Resolution'].default_value = 6
            rib_profile.inputs['Radius'].default_value = 0.04

            # Single arc that spans dome
            arc = tree.nodes.new('GeometryNodeCurveArc'); arc.location = (base_x, 900); color_node(arc, "dome")
            arc.mode = 'RADIUS'
            arc.inputs['Resolution'].default_value = 32
            arc.inputs['Radius'].default_value = R
            arc.inputs['Sweep Angle'].default_value = math.radians(180)

            arc_orient = tree.nodes.new('GeometryNodeTransform'); arc_orient.location = (base_x+300, 900)
            arc_orient.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
            tree.links.new(arc.outputs['Curve'], arc_orient.inputs['Geometry'])

            rib_sweep = tree.nodes.new('GeometryNodeCurveToMesh'); rib_sweep.location = (base_x+600, 800); color_node(rib_sweep, "ornament")
            tree.links.new(arc_orient.outputs['Geometry'], rib_sweep.inputs['Curve'])
            tree.links.new(rib_profile.outputs['Curve'], rib_sweep.inputs['Profile Curve'])
            rib_sweep.inputs['Fill Caps'].default_value = True

            # Instance ribs around dome
            n_ribs = PROPS.dome_rib_count
            circle = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); circle.location = (base_x+900, 600)
            circle.mode = 'RADIUS'
            circle.inputs['Resolution'].default_value = n_ribs
            circle.inputs['Radius'].default_value = 0.01

            c2p = tree.nodes.new('GeometryNodeCurveToPoints'); c2p.location = (base_x+1100, 600)
            c2p.mode = 'EVALUATED'
            tree.links.new(circle.outputs['Curve'], c2p.inputs['Curve'])

            inst = tree.nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (base_x+1300, 600)
            tree.links.new(c2p.outputs['Points'], inst.inputs['Points'])
            tree.links.new(rib_sweep.outputs['Mesh'], inst.inputs['Instance'])

            idx = tree.nodes.new('GeometryNodeInputIndex'); idx.location = (base_x+1100, 900)
            rmul = tree.nodes.new('ShaderNodeMath'); rmul.location = (base_x+1300, 900); rmul.operation = 'MULTIPLY'
            rmul.inputs[1].default_value = math.tau / n_ribs
            tree.links.new(idx.outputs['Index'], rmul.inputs[0])

            rvec = tree.nodes.new('ShaderNodeCombineXYZ'); rvec.location = (base_x+1500, 900)
            rvec.inputs['X'].default_value = 0; rvec.inputs['Y'].default_value = 0
            tree.links.new(rmul.outputs['Value'], rvec.inputs['Z'])

            rot_inst = tree.nodes.new('GeometryNodeRotateInstances'); rot_inst.location = (base_x+1700, 600)
            tree.links.new(inst.outputs['Instances'], rot_inst.inputs['Instances'])
            tree.links.new(rvec.outputs['Vector'], rot_inst.inputs['Rotation'])

            realize = tree.nodes.new('GeometryNodeRealizeInstances'); realize.location = (base_x+1900, 600)
            tree.links.new(rot_inst.outputs['Instances'], realize.inputs['Geometry'])

            parts.append(realize.outputs['Geometry'])

        # Spire
        if PROPS.dome_spire > 0.01:
            spire = tree.nodes.new('GeometryNodeMeshCone'); spire.location = (base_x, 1300); color_node(spire, "ornament")
            spire.inputs['Vertices'].default_value = 16  # bumped from 12 in v2.31
            spire.inputs['Radius Top'].default_value = 0.0
            spire.inputs['Radius Bottom'].default_value = PROPS.dome_spire * 0.2
            spire.inputs['Depth'].default_value = PROPS.dome_spire

            spire_t = tree.nodes.new('GeometryNodeTransform'); spire_t.location = (base_x+300, 1300)
            spire_t.inputs['Translation'].default_value = (0, 0, R + PROPS.dome_spire / 2)
            tree.links.new(spire.outputs['Mesh'], spire_t.inputs['Geometry'])
            parts.append(spire_t.outputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+2200, 0); color_node(join, "output")
        for p in parts:
            tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    # ----------------------------------------------------------------------
    # BUILDER: CRENELLATION (Castle Battlements)
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_dome")
    return tree, gin, gout

register_builder(
    "MEL_dome", build_dome_group,
    "Dome", "Core form builder (absorbed from monolith build_dome).",
    category="structures")


def build_crenellation_group(group_name="MEL_crenellation"):
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
        """Castle wall with merlons (alternating high/low tops)."""
        L = PROPS.crenel_length
        H = PROPS.crenel_height
        T = PROPS.crenel_thickness
        n_merlons = max(2, PROPS.crenel_merlon_count)
        merlon_h = PROPS.crenel_merlon_height
        gap = PROPS.crenel_gap_ratio

        # Wall body
        wall = tree.nodes.new('GeometryNodeMeshCube'); wall.location = (base_x, 0); color_node(wall, "crenel")
        wall.inputs['Size'].default_value = (L, T, H)

        # Merlon block dimensions
        merlon_period = L / n_merlons
        merlon_width = merlon_period * (1.0 - gap)

        # Line of points for merlons
        line = tree.nodes.new('GeometryNodeMeshLine'); line.location = (base_x, 400); color_node(line, "crenel")
        line.mode = 'OFFSET'
        line.inputs['Count'].default_value = n_merlons
        line.inputs['Start Location'].default_value = (-L/2 + merlon_period/2, 0, H/2 + merlon_h/2)
        line.inputs['Offset'].default_value = (merlon_period, 0, 0)

        # Merlon block
        merlon = tree.nodes.new('GeometryNodeMeshCube'); merlon.location = (base_x, 700); color_node(merlon, "crenel")
        merlon.inputs['Size'].default_value = (merlon_width, T, merlon_h)

        inst = tree.nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (base_x+300, 500)
        tree.links.new(line.outputs['Mesh'], inst.inputs['Points'])
        tree.links.new(merlon.outputs['Mesh'], inst.inputs['Instance'])

        # Whimsical: musical height variation per merlon
        idx = tree.nodes.new('GeometryNodeInputIndex'); idx.location = (base_x, 900)
        h_val = make_harmonic_value(tree, idx.outputs['Index'],
                                     PROPS.musical_freq_a * NOTE_PATTERNS.get(PROPS.note_pattern, 4.0) * PROPS.tempo_factor / 4.0,
                                     PROPS.musical_freq_b * NOTE_PATTERNS.get(PROPS.note_pattern, 4.0) * PROPS.tempo_factor / 4.0,
                                     PROPS.harmonic_layers, base_x+200, 900)
        mr = tree.nodes.new('ShaderNodeMapRange'); mr.location = (base_x+1000, 900)
        mr.inputs['From Min'].default_value = -2; mr.inputs['From Max'].default_value = 2
        mr.inputs['To Min'].default_value = 1.0 - PROPS.ornament_density * 0.5
        mr.inputs['To Max'].default_value = 1.0 + PROPS.ornament_density * 0.5
        tree.links.new(h_val, mr.inputs['Value'])

        sv = tree.nodes.new('ShaderNodeCombineXYZ'); sv.location = (base_x+1200, 900); color_node(sv, "ornament")
        sv.inputs['X'].default_value = 1; sv.inputs['Y'].default_value = 1
        tree.links.new(mr.outputs['Result'], sv.inputs['Z'])

        scale_m = tree.nodes.new('GeometryNodeScaleInstances'); scale_m.location = (base_x+1400, 500)
        tree.links.new(inst.outputs['Instances'], scale_m.inputs['Instances'])
        tree.links.new(sv.outputs['Vector'], scale_m.inputs['Scale'])

        realize = tree.nodes.new('GeometryNodeRealizeInstances'); realize.location = (base_x+1600, 500)
        tree.links.new(scale_m.outputs['Instances'], realize.inputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+1900, 0); color_node(join, "output")
        tree.links.new(wall.outputs['Mesh'], join.inputs['Geometry'])
        tree.links.new(realize.outputs['Geometry'], join.inputs['Geometry'])

        return join.outputs['Geometry']


    # ----------------------------------------------------------------------
    # BUILDER: FRACTAL TOWER (recursive self-similar)
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_crenellation")
    return tree, gin, gout

register_builder(
    "MEL_crenellation", build_crenellation_group,
    "Crenellation", "Core form builder (absorbed from monolith build_crenellation).",
    category="structures")


def build_window_group(group_name="MEL_window"):
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
        """Window opening: rectangular frame with optional ogee top + sill."""
        W = PROPS.window_width
        H = PROPS.window_height
        fw = PROPS.window_frame_width
        parts = []

        # Two vertical jambs
        for x_off in (-W/2, W/2):
            jamb = tree.nodes.new('GeometryNodeMeshCube'); jamb.location = (base_x, 0); color_node(jamb, "window")
            jamb.inputs['Size'].default_value = (fw, fw, H)
            jt = tree.nodes.new('GeometryNodeTransform'); jt.location = (base_x+200, 0)
            jt.inputs['Translation'].default_value = (x_off, 0, H/2)
            tree.links.new(jamb.outputs['Mesh'], jt.inputs['Geometry'])
            parts.append(jt.outputs['Geometry'])

        # Bottom sill (extends past the jambs slightly)
        sill = tree.nodes.new('GeometryNodeMeshCube'); sill.location = (base_x, 300); color_node(sill, "window")
        sill.inputs['Size'].default_value = (W + fw*2 + 0.05, fw + PROPS.window_sill_depth, fw)
        st = tree.nodes.new('GeometryNodeTransform'); st.location = (base_x+200, 300)
        st.inputs['Translation'].default_value = (0, PROPS.window_sill_depth/2, fw/2)
        tree.links.new(sill.outputs['Mesh'], st.inputs['Geometry'])
        parts.append(st.outputs['Geometry'])

        # Top - either flat header or ogee arch
        if PROPS.window_arch_top:
            # Reuse build_ogee_arch with this window's dimensions
            saved = (PROPS.ogee_width, PROPS.ogee_height, PROPS.ogee_swell, PROPS.ogee_finial)
            PROPS.ogee_width = W
            PROPS.ogee_height = H * 0.4
            PROPS.ogee_swell = 0.15
            PROPS.ogee_finial = 0.0
            arch_geom = _impl_build_ogee_arch(tree, PROPS, base_x=base_x+1500)
            PROPS.ogee_width, PROPS.ogee_height, PROPS.ogee_swell, PROPS.ogee_finial = saved

            at = tree.nodes.new('GeometryNodeTransform'); at.location = (base_x+3000, 600)
            at.inputs['Translation'].default_value = (0, 0, H)
            tree.links.new(arch_geom, at.inputs['Geometry'])
            parts.append(at.outputs['Geometry'])
        else:
            head = tree.nodes.new('GeometryNodeMeshCube'); head.location = (base_x, 600); color_node(head, "window")
            head.inputs['Size'].default_value = (W + fw*2, fw, fw)
            ht = tree.nodes.new('GeometryNodeTransform'); ht.location = (base_x+200, 600)
            ht.inputs['Translation'].default_value = (0, 0, H + fw/2)
            tree.links.new(head.outputs['Mesh'], ht.inputs['Geometry'])
            parts.append(ht.outputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+3500, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_window")
    return tree, gin, gout

register_builder(
    "MEL_window", build_window_group,
    "Window", "Core form builder (absorbed from monolith build_window).",
    category="structures")


def build_door_group(group_name="MEL_door"):
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
        """Door opening with frame + optional steps below + optional ogee arch."""
        W = PROPS.door_width
        H = PROPS.door_height
        fw = PROPS.door_frame_width
        parts = []

        # Two jambs
        for x_off in (-W/2, W/2):
            jamb = tree.nodes.new('GeometryNodeMeshCube'); jamb.location = (base_x, 0); color_node(jamb, "door")
            jamb.inputs['Size'].default_value = (fw, fw*1.5, H)
            jt = tree.nodes.new('GeometryNodeTransform'); jt.location = (base_x+200, 0)
            jt.inputs['Translation'].default_value = (x_off, 0, H/2)
            tree.links.new(jamb.outputs['Mesh'], jt.inputs['Geometry'])
            parts.append(jt.outputs['Geometry'])

        # Header / arch top
        if PROPS.door_arch_top:
            saved = (PROPS.ogee_width, PROPS.ogee_height, PROPS.ogee_swell, PROPS.ogee_finial)
            PROPS.ogee_width = W
            PROPS.ogee_height = H * 0.45
            PROPS.ogee_swell = 0.2
            PROPS.ogee_finial = 0.0
            arch_geom = _impl_build_ogee_arch(tree, PROPS, base_x=base_x+1500)
            PROPS.ogee_width, PROPS.ogee_height, PROPS.ogee_swell, PROPS.ogee_finial = saved
            at = tree.nodes.new('GeometryNodeTransform'); at.location = (base_x+3000, 600)
            at.inputs['Translation'].default_value = (0, 0, H)
            tree.links.new(arch_geom, at.inputs['Geometry'])
            parts.append(at.outputs['Geometry'])
        else:
            lintel = tree.nodes.new('GeometryNodeMeshCube'); lintel.location = (base_x, 600); color_node(lintel, "door")
            lintel.inputs['Size'].default_value = (W + fw*2, fw*1.5, fw*1.2)
            lt = tree.nodes.new('GeometryNodeTransform'); lt.location = (base_x+200, 600)
            lt.inputs['Translation'].default_value = (0, 0, H + fw*0.6)
            tree.links.new(lintel.outputs['Mesh'], lt.inputs['Geometry'])
            parts.append(lt.outputs['Geometry'])

        # Steps below
        if PROPS.door_step_count > 0:
            for i in range(PROPS.door_step_count):
                step = tree.nodes.new('GeometryNodeMeshCube'); step.location = (base_x, -200 - i*100); color_node(step, "door")
                sw = W + fw*2 + (PROPS.door_step_count - i) * 0.12
                sd = fw*1.5 + (PROPS.door_step_count - i) * 0.12
                step.inputs['Size'].default_value = (sw, sd, 0.12)
                stt = tree.nodes.new('GeometryNodeTransform'); stt.location = (base_x+200, -200 - i*100)
                stt.inputs['Translation'].default_value = (0, 0, -0.06 - i*0.12)
                tree.links.new(step.outputs['Mesh'], stt.inputs['Geometry'])
                parts.append(stt.outputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+3500, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_door")
    return tree, gin, gout

register_builder(
    "MEL_door", build_door_group,
    "Door", "Core form builder (absorbed from monolith build_door).",
    category="structures")


def build_balcony_group(group_name="MEL_balcony"):
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
        """Small balcony platform with a railing on three sides."""
        W = PROPS.balcony_width
        D = PROPS.balcony_depth
        T = PROPS.balcony_thickness
        parts = []

        # Slab
        slab = tree.nodes.new('GeometryNodeMeshCube'); slab.location = (base_x, 0); color_node(slab, "modular")
        slab.inputs['Size'].default_value = (W, D, T)
        parts.append(slab.outputs['Mesh'])

        # Front railing (along +X face - actually use Y direction: front = +Y/2)
        saved = (PROPS.rail_length, PROPS.rail_baluster_count, PROPS.rail_height)
        PROPS.rail_length = W
        PROPS.rail_baluster_count = PROPS.balcony_baluster_count
        PROPS.rail_height = 0.9
        rail_front = _impl_build_railing(tree, PROPS, x_offset=2500)
        PROPS.rail_length, PROPS.rail_baluster_count, PROPS.rail_height = saved

        # Position front railing at +Y edge of slab
        rt = tree.nodes.new('GeometryNodeTransform'); rt.location = (base_x+5000, 200); color_node(rt, "modular")
        rt.inputs['Translation'].default_value = (0, D/2 - 0.03, T/2)
        tree.links.new(rail_front, rt.inputs['Geometry'])
        parts.append(rt.outputs['Geometry'])

        # Side railings (two, perpendicular)
        for x_off, dir_sign in ((-W/2 + 0.03, 1), (W/2 - 0.03, -1)):
            saved = (PROPS.rail_length, PROPS.rail_baluster_count)
            PROPS.rail_length = D - 0.05
            PROPS.rail_baluster_count = max(3, PROPS.balcony_baluster_count // 3)
            side_rail = _impl_build_railing(tree, PROPS, x_offset=2500 + (x_off + W/2) * 100)
            PROPS.rail_length, PROPS.rail_baluster_count = saved

            srt = tree.nodes.new('GeometryNodeTransform'); srt.location = (base_x+5000, 500); color_node(srt, "modular")
            srt.inputs['Translation'].default_value = (x_off, 0, T/2)
            srt.inputs['Rotation'].default_value = (0, 0, math.radians(90))
            tree.links.new(side_rail, srt.inputs['Geometry'])
            parts.append(srt.outputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+5500, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_balcony")
    return tree, gin, gout

register_builder(
    "MEL_balcony", build_balcony_group,
    "Balcony", "Core form builder (absorbed from monolith build_balcony).",
    category="structures")


def build_cornice_group(group_name="MEL_cornice"):
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
        """Layered horizontal molding - multiple bands of decreasing depth."""
        L = PROPS.cornice_length
        H = PROPS.cornice_height
        D = PROPS.cornice_depth
        layers = PROPS.cornice_layers
        parts = []

        band_h = H / max(1, layers)
        for i in range(layers):
            scale = 1.0 - (i * 0.12)
            b = tree.nodes.new('GeometryNodeMeshCube'); b.location = (base_x, i * 200); color_node(b, "modular")
            b.inputs['Size'].default_value = (L * scale, D * scale, band_h)
            bt = tree.nodes.new('GeometryNodeTransform'); bt.location = (base_x+200, i * 200)
            bt.inputs['Translation'].default_value = (0, 0, band_h * (i + 0.5))
            tree.links.new(b.outputs['Mesh'], bt.inputs['Geometry'])
            parts.append(bt.outputs['Geometry'])

        # Crown molding on top - rounded edge cylinder
        crown = tree.nodes.new('GeometryNodeMeshCylinder'); crown.location = (base_x, layers * 200); color_node(crown, "modular")
        crown.inputs['Vertices'].default_value = 16
        crown.inputs['Radius'].default_value = D * 0.4
        crown.inputs['Depth'].default_value = L
        ct = tree.nodes.new('GeometryNodeTransform'); ct.location = (base_x+200, layers * 200)
        ct.inputs['Translation'].default_value = (0, 0, H)
        ct.inputs['Rotation'].default_value = (0, math.radians(90), 0)
        tree.links.new(crown.outputs['Mesh'], ct.inputs['Geometry'])
        parts.append(ct.outputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+500, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_cornice")
    return tree, gin, gout

register_builder(
    "MEL_cornice", build_cornice_group,
    "Cornice", "Core form builder (absorbed from monolith build_cornice).",
    category="structures")


def build_fountain_group(group_name="MEL_fountain"):
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
        """Tiered fountain: stacked bowls with central column."""
        R = PROPS.fountain_radius
        tiers = PROPS.fountain_tiers
        tier_scale = PROPS.fountain_tier_scale
        H = PROPS.fountain_height
        parts = []

        tier_h = H / (tiers + 1)
        cur_r = R
        cur_z = 0
        for i in range(tiers):
            # Bowl: cylinder with smaller cylinder hollowed (use cone with high top radius)
            bowl = tree.nodes.new('GeometryNodeMeshCylinder'); bowl.location = (base_x, i * 200); color_node(bowl, "fountain")
            bowl.inputs['Vertices'].default_value = 32
            bowl.inputs['Radius'].default_value = cur_r
            bowl.inputs['Depth'].default_value = tier_h * 0.4
            bt = tree.nodes.new('GeometryNodeTransform'); bt.location = (base_x+200, i * 200)
            bt.inputs['Translation'].default_value = (0, 0, cur_z + tier_h * 0.2)
            tree.links.new(bowl.outputs['Mesh'], bt.inputs['Geometry'])
            parts.append(bt.outputs['Geometry'])

            # Inner bowl rim (smaller cylinder on top)
            rim = tree.nodes.new('GeometryNodeMeshCylinder'); rim.location = (base_x, i * 200 + 100); color_node(rim, "fountain")
            rim.inputs['Vertices'].default_value = 32
            rim.inputs['Radius'].default_value = cur_r * 0.92
            rim.inputs['Depth'].default_value = tier_h * 0.05
            rt = tree.nodes.new('GeometryNodeTransform'); rt.location = (base_x+200, i * 200 + 100)
            rt.inputs['Translation'].default_value = (0, 0, cur_z + tier_h * 0.42)
            tree.links.new(rim.outputs['Mesh'], rt.inputs['Geometry'])
            parts.append(rt.outputs['Geometry'])

            # Central column between this tier and next
            col = tree.nodes.new('GeometryNodeMeshCylinder'); col.location = (base_x, i * 200 + 200); color_node(col, "fountain")
            col.inputs['Vertices'].default_value = 16
            col.inputs['Radius'].default_value = cur_r * 0.18
            col.inputs['Depth'].default_value = tier_h * 0.6
            cot = tree.nodes.new('GeometryNodeTransform'); cot.location = (base_x+200, i * 200 + 200)
            cot.inputs['Translation'].default_value = (0, 0, cur_z + tier_h * 0.7)
            tree.links.new(col.outputs['Mesh'], cot.inputs['Geometry'])
            parts.append(cot.outputs['Geometry'])

            cur_r *= tier_scale
            cur_z += tier_h

        # Tip finial sphere
        tip = tree.nodes.new('GeometryNodeMeshUVSphere'); tip.location = (base_x, tiers * 200); color_node(tip, "fountain")
        tip.inputs['Radius'].default_value = cur_r * 0.5
        tip.inputs['Segments'].default_value = 16
        tip.inputs['Rings'].default_value = 12
        tt = tree.nodes.new('GeometryNodeTransform'); tt.location = (base_x+200, tiers * 200)
        tt.inputs['Translation'].default_value = (0, 0, cur_z + cur_r * 0.5)
        tree.links.new(tip.outputs['Mesh'], tt.inputs['Geometry'])
        parts.append(tt.outputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+500, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_fountain")
    return tree, gin, gout

register_builder(
    "MEL_fountain", build_fountain_group,
    "Fountain", "Core form builder (absorbed from monolith build_fountain).",
    category="structures")


def build_floor_tile_group(group_name="MEL_floor_tile"):
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
        """Decorative floor tile - single, grid, checkerboard, or randomized."""
        s = PROPS.tile_size
        t = PROPS.tile_thickness
        pat = PROPS.tile_pattern
        n = max(1, PROPS.tile_grid_count)

        if pat == 'SOLID':
            tile = tree.nodes.new('GeometryNodeMeshCube'); tile.location = (base_x, 0); color_node(tile, "tile")
            tile.inputs['Size'].default_value = (s, s, t)
            return tile.outputs['Mesh']

        # Grid of points
        grid = tree.nodes.new('GeometryNodeMeshGrid'); grid.location = (base_x, 0); color_node(grid, "tile")
        grid.inputs['Size X'].default_value = s * n
        grid.inputs['Size Y'].default_value = s * n
        grid.inputs['Vertices X'].default_value = n
        grid.inputs['Vertices Y'].default_value = n

        tile_proto = tree.nodes.new('GeometryNodeMeshCube'); tile_proto.location = (base_x, 300); color_node(tile_proto, "tile")
        tile_proto.inputs['Size'].default_value = (s * 0.95, s * 0.95, t)

        inst = tree.nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (base_x+300, 0)
        tree.links.new(grid.outputs['Mesh'], inst.inputs['Points'])
        tree.links.new(tile_proto.outputs['Mesh'], inst.inputs['Instance'])

        if pat == 'CHECKER':
            # Vary Z by index parity
            idx = tree.nodes.new('GeometryNodeInputIndex'); idx.location = (base_x, 600)
            mod_n = tree.nodes.new('ShaderNodeMath'); mod_n.location = (base_x+200, 600); mod_n.operation = 'MODULO'
            mod_n.inputs[1].default_value = 2.0
            tree.links.new(idx.outputs['Index'], mod_n.inputs[0])
            z_off = tree.nodes.new('ShaderNodeMath'); z_off.location = (base_x+400, 600); z_off.operation = 'MULTIPLY'
            z_off.inputs[1].default_value = t
            tree.links.new(mod_n.outputs[0], z_off.inputs[0])
            ovec = tree.nodes.new('ShaderNodeCombineXYZ'); ovec.location = (base_x+600, 600)
            ovec.inputs['X'].default_value = 0; ovec.inputs['Y'].default_value = 0
            tree.links.new(z_off.outputs[0], ovec.inputs['Z'])
            ti = tree.nodes.new('GeometryNodeTranslateInstances'); ti.location = (base_x+800, 0)
            tree.links.new(inst.outputs['Instances'], ti.inputs['Instances'])
            tree.links.new(ovec.outputs['Vector'], ti.inputs['Translation'])
            out_inst = ti.outputs['Instances']
        elif pat == 'VENETIAN':
            # Random Z rotation per tile
            idx = tree.nodes.new('GeometryNodeInputIndex'); idx.location = (base_x, 600)
            rmul = tree.nodes.new('ShaderNodeMath'); rmul.location = (base_x+200, 600); rmul.operation = 'MULTIPLY'
            rmul.inputs[1].default_value = 0.78  # ~45deg per index, irrational ratio
            tree.links.new(idx.outputs['Index'], rmul.inputs[0])
            rvec = tree.nodes.new('ShaderNodeCombineXYZ'); rvec.location = (base_x+400, 600)
            rvec.inputs['X'].default_value = 0; rvec.inputs['Y'].default_value = 0
            tree.links.new(rmul.outputs[0], rvec.inputs['Z'])
            ri = tree.nodes.new('GeometryNodeRotateInstances'); ri.location = (base_x+800, 0)
            tree.links.new(inst.outputs['Instances'], ri.inputs['Instances'])
            tree.links.new(rvec.outputs['Vector'], ri.inputs['Rotation'])
            out_inst = ri.outputs['Instances']
        else:  # GRID
            out_inst = inst.outputs['Instances']

        realize = tree.nodes.new('GeometryNodeRealizeInstances'); realize.location = (base_x+1100, 0)
        tree.links.new(out_inst, realize.inputs['Geometry'])
        return realize.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_floor_tile")
    return tree, gin, gout

register_builder(
    "MEL_floor_tile", build_floor_tile_group,
    "Floor Tile", "Core form builder (absorbed from monolith build_floor_tile).",
    category="structures")


def build_lantern_post_group(group_name="MEL_lantern_post"):
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
        """Venetian lamppost: tall thin post + capital + glass enclosure + finial."""
        H = PROPS.lantern_height
        pr = PROPS.lantern_post_radius
        gs = PROPS.lantern_glass_size
        parts = []

        # Post
        post = tree.nodes.new('GeometryNodeMeshCylinder'); post.location = (base_x, 0); color_node(post, "lantern")
        post.inputs['Vertices'].default_value = 12
        post.inputs['Radius'].default_value = pr
        post.inputs['Depth'].default_value = H * 0.85
        pt = tree.nodes.new('GeometryNodeTransform'); pt.location = (base_x+200, 0)
        pt.inputs['Translation'].default_value = (0, 0, H * 0.425)
        tree.links.new(post.outputs['Mesh'], pt.inputs['Geometry'])
        parts.append(pt.outputs['Geometry'])

        # Base - wider cylinder
        base = tree.nodes.new('GeometryNodeMeshCylinder'); base.location = (base_x, -200); color_node(base, "lantern")
        base.inputs['Vertices'].default_value = 12
        base.inputs['Radius'].default_value = pr * 4
        base.inputs['Depth'].default_value = pr * 4
        bt = tree.nodes.new('GeometryNodeTransform'); bt.location = (base_x+200, -200)
        bt.inputs['Translation'].default_value = (0, 0, pr * 2)
        tree.links.new(base.outputs['Mesh'], bt.inputs['Geometry'])
        parts.append(bt.outputs['Geometry'])

        # Capital under the lamp
        cap = tree.nodes.new('GeometryNodeMeshCone'); cap.location = (base_x, 200); color_node(cap, "lantern")
        cap.inputs['Vertices'].default_value = 32  # bumped from 16 in v2.31 for smoother shading
        cap.inputs['Radius Top'].default_value = gs * 0.6
        cap.inputs['Radius Bottom'].default_value = pr * 1.5
        cap.inputs['Depth'].default_value = gs * 0.5
        capt = tree.nodes.new('GeometryNodeTransform'); capt.location = (base_x+200, 200)
        capt.inputs['Translation'].default_value = (0, 0, H * 0.85 + gs * 0.25)
        tree.links.new(cap.outputs['Mesh'], capt.inputs['Geometry'])
        parts.append(capt.outputs['Geometry'])

        # Glass cube
        glass = tree.nodes.new('GeometryNodeMeshCube'); glass.location = (base_x, 400); color_node(glass, "lantern")
        glass.inputs['Size'].default_value = (gs, gs, gs)
        gt = tree.nodes.new('GeometryNodeTransform'); gt.location = (base_x+200, 400)
        gt.inputs['Translation'].default_value = (0, 0, H * 0.85 + gs * 0.5 + gs * 0.5)
        tree.links.new(glass.outputs['Mesh'], gt.inputs['Geometry'])
        parts.append(gt.outputs['Geometry'])

        # Finial cap on top
        fin = tree.nodes.new('GeometryNodeMeshCone'); fin.location = (base_x, 600); color_node(fin, "lantern")
        fin.inputs['Vertices'].default_value = 16  # bumped from 12 in v2.31
        fin.inputs['Radius Top'].default_value = 0.0
        fin.inputs['Radius Bottom'].default_value = gs * 0.4
        fin.inputs['Depth'].default_value = gs * 0.6
        ft = tree.nodes.new('GeometryNodeTransform'); ft.location = (base_x+200, 600)
        ft.inputs['Translation'].default_value = (0, 0, H * 0.85 + gs + gs * 0.8)
        tree.links.new(fin.outputs['Mesh'], ft.inputs['Geometry'])
        parts.append(ft.outputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+500, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    # ----------------------------------------------------------------------
    # REUSABLE INSTANCE-PIECE PROTOTYPES
    # Returns a small, generic mesh suitable for instancing on a curve / radial array.
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_lantern_post")
    return tree, gin, gout

register_builder(
    "MEL_lantern_post", build_lantern_post_group,
    "Lantern Post", "Core form builder (absorbed from monolith build_lantern_post).",
    category="structures")


def build_brick_wall_group(group_name="MEL_brick_wall"):
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
        """Staggered brick masonry wall.
        v2.52: Uses Higgsas NTBricks Grid + NTSolidify when available for a
        proper parametric brick surface with accurate mortar gaps and UV.
        Falls back to the native GN stagger-grid approach when Higgsas is absent."""
        W      = PROPS.brick_wall_width
        H      = PROPS.brick_wall_height
        bw     = PROPS.brick_size_x
        bh_    = PROPS.brick_size_z
        bd     = PROPS.brick_depth
        mortar = PROPS.brick_mortar_gap

        # ── Higgsas path: NTBricks Grid -> NTSolidify -> orient ─────────────
        higg_bricks = _higg_node(tree, 'NTBricks Grid', (base_x, 0))
        if higg_bricks is not None:
            _higg_input(higg_bricks, 'X Grid Size',        W)
            _higg_input(higg_bricks, 'Y Grid Size',        H)
            _higg_input(higg_bricks, 'Absolute Grid Size', False)
            # NTBricks Grid outputs a flat (XY) grid - solidify for depth
            higg_solid = _higg_node(tree, 'NTSolidify', (base_x + 400, 0))
            geom_out = higg_bricks.outputs[0]
            if higg_solid is not None:
                _higg_input(higg_solid, 'Even Thickness', True)
                _higg_input(higg_solid, 'Thickness',      bd)
                _link(tree, higg_bricks.outputs[0], higg_solid.inputs['Mesh'])
                geom_out = higg_solid.outputs['Mesh']
            # Rotate to stand up (XZ plane) + shift up so base is at z=0
            rot = _safe_node(tree, 'GeometryNodeTransform', (base_x + 800, 0))
            if rot:
                try:
                    rot.inputs['Rotation'].default_value    = (math.radians(90), 0, 0)
                    rot.inputs['Translation'].default_value = (0, 0, H * 0.5)
                except Exception: pass
                _link(tree, geom_out, rot.inputs['Geometry'])
                color_node(rot, "brick")
                return rot.outputs['Geometry']
            return geom_out

        # ── Native fallback: stagger-grid (original approach) ─────────────
        cols = max(2, int(W / (bw + mortar)))
        rows = max(2, int(H / (bh_ + mortar)))

        grid = tree.nodes.new('GeometryNodeMeshGrid'); grid.location = (base_x, 0); color_node(grid, "brick")
        grid.inputs['Size X'].default_value = W
        grid.inputs['Size Y'].default_value = H
        grid.inputs['Vertices X'].default_value = cols
        grid.inputs['Vertices Y'].default_value = rows

        pos = tree.nodes.new('GeometryNodeInputPosition'); pos.location = (base_x, -300); color_node(pos, "input")
        sep = tree.nodes.new('ShaderNodeSeparateXYZ'); sep.location = (base_x+200, -300)
        tree.links.new(pos.outputs['Position'], sep.inputs['Vector'])

        norm_y = tree.nodes.new('ShaderNodeMath'); norm_y.location = (base_x+400, -300); norm_y.operation = 'DIVIDE'
        norm_y.inputs[1].default_value = bh_ + mortar
        tree.links.new(sep.outputs['Y'], norm_y.inputs[0])
        floor_y = tree.nodes.new('ShaderNodeMath'); floor_y.location = (base_x+600, -300); floor_y.operation = 'FLOOR'
        tree.links.new(norm_y.outputs['Value'], floor_y.inputs[0])
        mod2 = tree.nodes.new('ShaderNodeMath'); mod2.location = (base_x+800, -300); mod2.operation = 'MODULO'
        mod2.inputs[1].default_value = 2.0
        tree.links.new(floor_y.outputs['Value'], mod2.inputs[0])
        stagger = tree.nodes.new('ShaderNodeMath'); stagger.location = (base_x+1000, -300); stagger.operation = 'MULTIPLY'
        stagger.inputs[1].default_value = (bw + mortar) / 2
        tree.links.new(mod2.outputs['Value'], stagger.inputs[0])
        ovec = tree.nodes.new('ShaderNodeCombineXYZ'); ovec.location = (base_x+1200, -300); color_node(ovec, "brick")
        tree.links.new(stagger.outputs['Value'], ovec.inputs['X'])
        ovec.inputs['Y'].default_value = 0; ovec.inputs['Z'].default_value = 0

        set_pos = tree.nodes.new('GeometryNodeSetPosition'); set_pos.location = (base_x+1400, 0); color_node(set_pos, "deform")
        tree.links.new(grid.outputs['Mesh'], set_pos.inputs['Geometry'])
        tree.links.new(ovec.outputs['Vector'], set_pos.inputs['Offset'])

        brick = tree.nodes.new('GeometryNodeMeshCube'); brick.location = (base_x, 400); color_node(brick, "brick")
        brick.inputs['Size'].default_value = (bw, bd, bh_)
        inst = tree.nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (base_x+1700, 0)
        tree.links.new(set_pos.outputs['Geometry'], inst.inputs['Points'])
        tree.links.new(brick.outputs['Mesh'], inst.inputs['Instance'])
        realize = tree.nodes.new('GeometryNodeRealizeInstances'); realize.location = (base_x+2000, 0)
        tree.links.new(inst.outputs['Instances'], realize.inputs['Geometry'])
        trans = tree.nodes.new('GeometryNodeTransform'); trans.location = (base_x+2300, 0); color_node(trans, "brick")
        trans.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
        tree.links.new(realize.outputs['Geometry'], trans.inputs['Geometry'])
        return trans.outputs['Geometry']


    # ----------------------------------------------------------------------
    # BUILDER: VENETIAN BRIDGE (Rialto-style multi-arch)
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_brick_wall")
    return tree, gin, gout

register_builder(
    "MEL_brick_wall", build_brick_wall_group,
    "Brick Wall", "Core form builder (absorbed from monolith build_brick_wall).",
    category="structures")


# 14 builders registered
