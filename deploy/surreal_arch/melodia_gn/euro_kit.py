"""MEL euro-classical builders — absorbed from the monolith (P2 family 6).

11 self-contained builders (gothic arch, venetian bridge, baroque vault/
facade/niche/balustrade, bifora, cusped arch, ogee arch, trefoil, buttress).
The 4 greybox-dependent euro pieces (portal/bay/arcade_bay/apse) ride the
greybox+shell-ladder batch — NOT here. Params-as-values port. Regenerable.
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
def _gb_bool_diff(tree, base_geom, cutters, x, y=0):
    """Boolean DIFFERENCE: base_geom minus the list of cutter sockets.
    Falls back to returning base_geom if the boolean node is unavailable."""
    cutters = [c for c in cutters if c is not None]
    if base_geom is None or not cutters:
        return base_geom
    boolean = _safe_node(tree, 'GeometryNodeMeshBoolean', (x, y))
    if boolean is None:
        return base_geom
    try:
        boolean.operation = 'DIFFERENCE'
    except Exception:
        pass
    # In 5.1, DIFFERENCE has 'Mesh 1' (single) + 'Mesh 2' (multi)
    linked = False
    try:
        _link(tree, base_geom, boolean.inputs['Mesh 1'])
        for c in cutters:
            _link(tree, c, boolean.inputs['Mesh 2'])
        linked = True
    except Exception:
        linked = False
    if not linked:
        # Fallback: some builds expose a single 'Mesh' multi-input
        try:
            _link(tree, base_geom, boolean.inputs['Mesh'])
            for c in cutters:
                _link(tree, c, boolean.inputs['Mesh'])
        except Exception:
            return base_geom
    color_node(boolean, "level")
    try:
        return boolean.outputs['Mesh']
    except Exception:
        return base_geom



def _gb_box(tree, size, loc_xyz, x, y, label="level"):
    """Helper: a MeshCube of `size`=(sx,sy,sz) translated to `loc_xyz`.
    Returns the translated geometry socket."""
    cube = _safe_node(tree, 'GeometryNodeMeshCube', (x, y))
    if cube is None:
        return None
    try:
        cube.inputs['Size'].default_value = size
    except Exception:
        pass
    color_node(cube, label)
    tr = _safe_node(tree, 'GeometryNodeTransform', (x + 200, y))
    if tr is None:
        return cube.outputs['Mesh']
    try:
        tr.inputs['Translation'].default_value = loc_xyz
    except Exception:
        pass
    _link(tree, cube.outputs['Mesh'], tr.inputs['Geometry'])
    color_node(tr, label)
    return tr.outputs['Geometry']


def _gb_join(tree, parts, x, y=0, label="output"):
    """Join a list of geometry sockets. Returns a single socket (or None)."""
    parts = [p for p in parts if p is not None]
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0]
    join = _safe_node(tree, 'GeometryNodeJoinGeometry', (x, y))
    if join is None:
        return parts[0]
    for p in parts:
        _link(tree, p, join.inputs['Geometry'])
    color_node(join, label)
    return join.outputs['Geometry']


def _gb_opening_cutter_depth(t, mult=4.0):
    """Deep cutter through wall thickness - prevents boolean clipping in UE blockout."""
    return t * mult



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


def _baroque_barrel_vault(tree, span, depth, rise, base_x=-1400):
    """Barrel vault: semicircular CurveArc swept along depth (CurveToMesh)."""
    import math as _m
    res = max(16, int(span * 4))
    arc = _safe_node(tree, 'GeometryNodeCurveArc', (base_x, 0))
    if arc:
        try:
            arc.mode = 'RADIUS'
            arc.inputs['Radius'].default_value = span * 0.5
            arc.inputs['Start Angle'].default_value = 0.0
            arc.inputs['Sweep Angle'].default_value = _m.pi
            arc.inputs['Resolution'].default_value = res
        except Exception:
            pass
        arc_rot = _safe_node(tree, 'GeometryNodeTransform', (base_x + 200, 0))
        if arc_rot:
            try:
                arc_rot.inputs['Rotation'].default_value = (_m.radians(90), 0, 0)
                arc_rot.inputs['Translation'].default_value = (0, 0, rise * 0.5)
            except Exception:
                pass
            _link(tree, arc.outputs['Curve'], arc_rot.inputs['Geometry'])
            shell_t = max(span, depth) * 0.035
            prof = _rect_profile(tree, (base_x + 100, 0), depth * 0.98, shell_t, 'vault')
            c2m = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 400, 0))
            if c2m and prof:
                _link(tree, arc_rot.outputs['Geometry'], c2m.inputs['Curve'])
                _link(tree, prof, c2m.inputs['Profile Curve'])
                try:
                    c2m.inputs['Fill Caps'].default_value = True
                except Exception:
                    pass
                color_node(c2m, 'vault')
                z_scale = rise / max(span * 0.5, 0.01)
                if abs(z_scale - 1.0) > 0.02:
                    sc = _safe_node(tree, 'GeometryNodeScale', (base_x + 600, 0))
                    if sc:
                        try:
                            sc.inputs['Scale'].default_value = (1.0, 1.0, z_scale)
                        except Exception:
                            pass
                        _link(tree, c2m.outputs['Mesh'], sc.inputs['Geometry'])
                        color_node(sc, 'vault')
                        return sc.outputs['Geometry']
                return c2m.outputs['Mesh']
    cube = _node(tree, 'GeometryNodeMeshCube', (base_x, 0))
    try:
        cube.inputs['Size'].default_value = (span * 0.95, depth * 0.95, rise * 0.65)
    except Exception:
        cube.inputs['Size X'].default_value = span * 0.95
        cube.inputs['Size Y'].default_value = depth * 0.95
        cube.inputs['Size Z'].default_value = rise * 0.65
    color_node(cube, 'vault')
    tr = _node(tree, 'GeometryNodeTransform', (base_x + 200, 0))
    tr.inputs['Translation'].default_value = (0, 0, rise * 0.35)
    _link(tree, cube.outputs['Mesh'], tr.inputs['Geometry'])
    color_node(tr, 'vault')
    return tr.outputs['Geometry']


def _baroque_groin_vault(tree, span, depth, rise, base_x=-1400):
    sph = _node(tree, 'GeometryNodeMeshUVSphere', (base_x, 0))
    sph.inputs['Radius'].default_value = span * 0.4
    sph.inputs['Segments'].default_value = 16
    sph.inputs['Rings'].default_value = 12
    color_node(sph, 'vault')
    sc = _node(tree, 'GeometryNodeScale', (base_x + 200, 0))
    sc.inputs['Scale'].default_value = (span * 0.6, depth * 0.6, rise * 0.45)
    _link(tree, sph.outputs['Mesh'], sc.inputs['Geometry'])
    tr = _node(tree, 'GeometryNodeTransform', (base_x + 400, 0))
    tr.inputs['Translation'].default_value = (0, 0, rise * 0.5)
    _link(tree, sc.outputs['Geometry'], tr.inputs['Geometry'])
    return tr.outputs['Geometry']


def _baroque_pilaster_geom(tree, width, height, base_x=-1400, y=0):
    base_h = height * 0.08
    cap_h = height * 0.12
    shaft_h = height - base_h - cap_h
    parts = []
    for label, h, z, sx in (
        ('base', base_h, base_h * 0.5, width * 1.1),
        ('shaft', shaft_h, base_h + shaft_h * 0.5, width * 0.85),
        ('cap', cap_h, height - cap_h * 0.5, width * 1.2),
    ):
        c = _node(tree, 'GeometryNodeMeshCube', (base_x, y))
        try:
            c.inputs['Size'].default_value = (sx, width * 0.35, h)
        except Exception:
            c.inputs['Size X'].default_value = sx
            c.inputs['Size Y'].default_value = width * 0.35
            c.inputs['Size Z'].default_value = h
        color_node(c, 'pilaster')
        tr = _node(tree, 'GeometryNodeTransform', (base_x + 100, y))
        tr.inputs['Translation'].default_value = (0, 0, z)
        _link(tree, c.outputs['Mesh'], tr.inputs['Geometry'])
        parts.append(tr.outputs['Geometry'])
    return _gb_join(tree, parts, base_x + 200, y) if parts else None


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



BUILDER_PARAM_DEFAULTS = {
    "baroque_balustrade_length": {"type": "FloatProperty", "default": 4.0, "min": 0.5, "max": 20.0},
    "baroque_balustrade_posts": {"type": "IntProperty", "default": 9, "min": 3, "max": 30},
    "baroque_facade_bays": {"type": "IntProperty", "default": 5, "min": 1, "max": 15},
    "baroque_facade_height": {"type": "FloatProperty", "default": 12.0, "min": 2.0, "max": 40.0},
    "baroque_niche_depth": {"type": "FloatProperty", "default": 0.4, "min": 0.1, "max": 2.0},
    "baroque_niche_height": {"type": "FloatProperty", "default": 2.0, "min": 0.5, "max": 6.0},
    "baroque_niche_width": {"type": "FloatProperty", "default": 1.2, "min": 0.3, "max": 4.0},
    "baroque_ornament_density": {"type": "FloatProperty", "default": 0.5, "min": 0.0, "max": 1.0},
    "baroque_rib_count": {"type": "IntProperty", "default": 8, "min": 4, "max": 24},
    "baroque_vault_depth": {"type": "FloatProperty", "default": 8.0, "min": 1.0, "max": 40.0},
    "baroque_vault_rise": {"type": "FloatProperty", "default": 3.0, "min": 0.5, "max": 15.0},
    "baroque_vault_span": {"type": "FloatProperty", "default": 6.0, "min": 1.0, "max": 30.0},
    "baroque_vault_style": {"type": "EnumProperty", "default": 'BARREL', "min": None, "max": None},
    "bifora_height": {"type": "FloatProperty", "default": 4.0, "min": 1.5, "max": 15.0},
    "bifora_lights": {"type": "IntProperty", "default": 2, "min": 2, "max": 6},
    "bifora_quatrefoil": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "bifora_use_ogee": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "bifora_width": {"type": "FloatProperty", "default": 2.4, "min": 0.8, "max": 10.0},
    "bridge_arch_style": {"type": "EnumProperty", "default": 'OGEE', "min": None, "max": None},
    "bridge_arches": {"type": "IntProperty", "default": 3, "min": 1, "max": 12},
    "bridge_height": {"type": "FloatProperty", "default": 2.0, "min": 0.5, "max": 10.0},
    "bridge_length": {"type": "FloatProperty", "default": 8.0, "min": 2.0, "max": 40.0},
    "bridge_railings": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "bridge_walkway": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "buttress_arch_bow": {"type": "FloatProperty", "default": 1.5, "min": 0.0, "max": 5.0},
    "buttress_finial_size": {"type": "FloatProperty", "default": 0.6, "min": 0.0, "max": 2.0},
    "buttress_height": {"type": "FloatProperty", "default": 4.0, "min": 0.5, "max": 15.0},
    "buttress_rib_count": {"type": "IntProperty", "default": 9, "min": 0, "max": 30},
    "buttress_span": {"type": "FloatProperty", "default": 3.0, "min": 0.5, "max": 15.0},
    "cusped_height": {"type": "FloatProperty", "default": 3.0, "min": 1.0, "max": 10.0},
    "cusped_lobe_depth": {"type": "FloatProperty", "default": 0.12, "min": 0.0, "max": 0.5},
    "cusped_lobes": {"type": "IntProperty", "default": 5, "min": 3, "max": 11},
    "cusped_width": {"type": "FloatProperty", "default": 2.0, "min": 0.5, "max": 8.0},
    "gothic_radius": {"type": "FloatProperty", "default": 1.5, "min": 0.6, "max": 10.0},
    "gothic_thickness": {"type": "FloatProperty", "default": 0.12, "min": 0.02, "max": 1.0},
    "gothic_width": {"type": "FloatProperty", "default": 2.0, "min": 0.5, "max": 10.0},
    "harmonic_layers": {"type": "IntProperty", "default": 2, "min": 1, "max": 5},
    "musical_freq_a": {"type": "FloatProperty", "default": 0.6, "min": 0.05, "max": 5.0},
    "musical_freq_b": {"type": "FloatProperty", "default": 1.2, "min": 0.05, "max": 5.0},
    "ogee_finial": {"type": "FloatProperty", "default": 0.4, "min": 0.0, "max": 2.0},
    "ogee_height": {"type": "FloatProperty", "default": 3.0, "min": 1.0, "max": 12.0},
    "ogee_shoulder": {"type": "FloatProperty", "default": 0.7, "min": 0.1, "max": 2.0},
    "ogee_swell": {"type": "FloatProperty", "default": 0.4, "min": 0.0, "max": 1.5},
    "ogee_width": {"type": "FloatProperty", "default": 2.0, "min": 0.5, "max": 8.0},
    "ornament_density": {"type": "FloatProperty", "default": 0.5, "min": 0.0, "max": 1.0},
    "trefoil_lobes": {"type": "IntProperty", "default": 3, "min": 2, "max": 8},
    "trefoil_outer": {"type": "FloatProperty", "default": 1.0, "min": 0.3, "max": 5.0},
    "trefoil_radius": {"type": "FloatProperty", "default": 0.4, "min": 0.1, "max": 3.0},
}


def _impl_build_gothic_arch(tree, PROPS, base_x=-1400):
    """Pointed Gothic arch: two intersecting circle arcs."""
    W = PROPS.gothic_width
    R = max(W / 2 + 0.001, PROPS.gothic_radius)  # must be ≥ half-width
    half_W = W / 2

    # peak angle from horizontal at arc center
    peak_angle = math.acos(min(1.0, max(-1.0, (R - half_W) / R)))

    # Right-side arc - center at (-half_W + R, 0)
    right_arc = tree.nodes.new('GeometryNodeCurveArc'); right_arc.location = (base_x, 200); color_node(right_arc, "gothic")
    right_arc.mode = 'RADIUS'
    right_arc.inputs['Resolution'].default_value = 32
    right_arc.inputs['Radius'].default_value = R
    right_arc.inputs['Start Angle'].default_value = math.pi - peak_angle
    right_arc.inputs['Sweep Angle'].default_value = peak_angle

    right_t = tree.nodes.new('GeometryNodeTransform'); right_t.location = (base_x+300, 200)
    right_t.inputs['Translation'].default_value = (-half_W + R, 0, 0)
    right_t.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
    tree.links.new(right_arc.outputs['Curve'], right_t.inputs['Geometry'])

    # Left-side arc
    left_arc = tree.nodes.new('GeometryNodeCurveArc'); left_arc.location = (base_x, -200); color_node(left_arc, "gothic")
    left_arc.mode = 'RADIUS'
    left_arc.inputs['Resolution'].default_value = 32
    left_arc.inputs['Radius'].default_value = R
    left_arc.inputs['Start Angle'].default_value = 0
    left_arc.inputs['Sweep Angle'].default_value = peak_angle

    left_t = tree.nodes.new('GeometryNodeTransform'); left_t.location = (base_x+300, -200)
    left_t.inputs['Translation'].default_value = (half_W - R, 0, 0)
    left_t.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
    tree.links.new(left_arc.outputs['Curve'], left_t.inputs['Geometry'])

    # Profile
    profile = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); profile.location = (base_x, -500); color_node(profile, "gothic")
    profile.mode = 'RADIUS'
    profile.inputs['Resolution'].default_value = 8
    profile.inputs['Radius'].default_value = PROPS.gothic_thickness

    right_sweep = tree.nodes.new('GeometryNodeCurveToMesh'); right_sweep.location = (base_x+600, 200)
    tree.links.new(right_t.outputs['Geometry'], right_sweep.inputs['Curve'])
    tree.links.new(profile.outputs['Curve'], right_sweep.inputs['Profile Curve'])
    right_sweep.inputs['Fill Caps'].default_value = True

    left_sweep = tree.nodes.new('GeometryNodeCurveToMesh'); left_sweep.location = (base_x+600, -200)
    tree.links.new(left_t.outputs['Geometry'], left_sweep.inputs['Curve'])
    tree.links.new(profile.outputs['Curve'], left_sweep.inputs['Profile Curve'])
    left_sweep.inputs['Fill Caps'].default_value = True

    join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+900, 0); color_node(join, "output")
    tree.links.new(right_sweep.outputs['Mesh'], join.inputs['Geometry'])
    tree.links.new(left_sweep.outputs['Mesh'], join.inputs['Geometry'])
    return join.outputs['Geometry']


# ----------------------------------------------------------------------
# BUILDER: TREFOIL / QUATREFOIL / CINQUEFOIL
# ----------------------------------------------------------------------


def build_gothic_arch_group(group_name="MEL_gothic_arch"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    geom = _impl_build_gothic_arch(tree, PROPS, base_x)
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_gothic_arch")
    return tree, gin, gout

register_builder(
    "MEL_gothic_arch", build_gothic_arch_group,
    "Gothic Arch", "Euro-classical builder (absorbed from monolith build_gothic_arch).",
    category="euro")

def build_venetian_bridge_group(group_name="MEL_venetian_bridge"):
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
        """Multi-arch bridge over a span. Pier walls + ogee/gothic arches + walkway + railings."""
        L = PROPS.bridge_length
        H = PROPS.bridge_height
        n = max(1, PROPS.bridge_arches)
        style = PROPS.bridge_arch_style

        parts = []
        pier_W = L * 0.05
        arch_W = (L - pier_W * (n + 1)) / n

        # Build a single arch sized for one bay
        saved_ogee = (PROPS.ogee_width, PROPS.ogee_height, PROPS.ogee_swell, PROPS.ogee_finial)
        saved_goth = (PROPS.gothic_width, PROPS.gothic_radius)
        saved_cusp = (PROPS.cusped_width, PROPS.cusped_height)

        if style == 'OGEE':
            PROPS.ogee_width  = arch_W
            PROPS.ogee_height = H
            PROPS.ogee_swell  = 0.2
            PROPS.ogee_finial = 0.0
            arch_geom = _impl_build_ogee_arch(tree, PROPS, base_x=base_x)
        elif style == 'CUSPED':
            PROPS.cusped_width  = arch_W
            PROPS.cusped_height = H
            arch_geom = _impl_build_cusped_arch(tree, PROPS, base_x=base_x)
        else:
            PROPS.gothic_width  = arch_W
            PROPS.gothic_radius = arch_W * 0.7
            arch_geom = _impl_build_gothic_arch(tree, PROPS, base_x=base_x)

        # Restore
        PROPS.ogee_width, PROPS.ogee_height, PROPS.ogee_swell, PROPS.ogee_finial = saved_ogee
        PROPS.gothic_width, PROPS.gothic_radius = saved_goth
        PROPS.cusped_width, PROPS.cusped_height = saved_cusp

        # Instance arches across the span
        arch_line = tree.nodes.new('GeometryNodeMeshLine'); arch_line.location = (base_x+3000, 0); color_node(arch_line, "bridge")
        arch_line.mode = 'OFFSET'
        arch_line.inputs['Count'].default_value = n
        arch_x_start = -L/2 + pier_W + arch_W/2
        arch_line.inputs['Start Location'].default_value = (arch_x_start, 0, 0)
        arch_line.inputs['Offset'].default_value = (arch_W + pier_W, 0, 0)

        inst = tree.nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (base_x+3300, 0)
        tree.links.new(arch_line.outputs['Mesh'], inst.inputs['Points'])
        tree.links.new(arch_geom, inst.inputs['Instance'])

        realize = tree.nodes.new('GeometryNodeRealizeInstances'); realize.location = (base_x+3600, 0)
        tree.links.new(inst.outputs['Instances'], realize.inputs['Geometry'])
        parts.append(realize.outputs['Geometry'])

        # === Pier walls - FULL HEIGHT (z=0 -> z=H) so the walkway sits directly on top ===
        pier_depth_y = 1.0  # match walkway depth so piers and deck align in Y
        pier_line = tree.nodes.new('GeometryNodeMeshLine'); pier_line.location = (base_x+3000, 400); color_node(pier_line, "bridge")
        pier_line.mode = 'OFFSET'
        pier_line.inputs['Count'].default_value = n + 1
        pier_line.inputs['Start Location'].default_value = (-L/2 + pier_W/2, 0, 0)
        pier_line.inputs['Offset'].default_value = (arch_W + pier_W, 0, 0)

        pier = tree.nodes.new('GeometryNodeMeshCube'); pier.location = (base_x+3000, 700); color_node(pier, "bridge")
        pier.inputs['Size'].default_value = (pier_W, pier_depth_y, H)  # FULL HEIGHT (was H*0.9)

        pier_inst = tree.nodes.new('GeometryNodeInstanceOnPoints'); pier_inst.location = (base_x+3300, 400)
        tree.links.new(pier_line.outputs['Mesh'], pier_inst.inputs['Points'])
        tree.links.new(pier.outputs['Mesh'], pier_inst.inputs['Instance'])

        pier_t = tree.nodes.new('GeometryNodeTranslateInstances'); pier_t.location = (base_x+3600, 400)
        pier_t.inputs['Translation'].default_value = (0, 0, H / 2)  # centered at H/2 -> top at H
        tree.links.new(pier_inst.outputs['Instances'], pier_t.inputs['Instances'])

        pier_real = tree.nodes.new('GeometryNodeRealizeInstances'); pier_real.location = (base_x+3900, 400)
        tree.links.new(pier_t.outputs['Instances'], pier_real.inputs['Geometry'])
        parts.append(pier_real.outputs['Geometry'])

        # Spandrel walls - fill space between arch tops and walkway bottom (Venetian-style fillets)
        spandrel_h = 0.06  # thin band right under the walkway
        spandrel_line = tree.nodes.new('GeometryNodeMeshLine'); spandrel_line.location = (base_x+3000, 1700); color_node(spandrel_line, "bridge")
        spandrel_line.mode = 'OFFSET'
        spandrel_line.inputs['Count'].default_value = n
        spandrel_line.inputs['Start Location'].default_value = (-L/2 + pier_W + arch_W/2, 0, H - spandrel_h/2)
        spandrel_line.inputs['Offset'].default_value = (arch_W + pier_W, 0, 0)

        span_block = tree.nodes.new('GeometryNodeMeshCube'); span_block.location = (base_x+3000, 1900); color_node(span_block, "bridge")
        span_block.inputs['Size'].default_value = (arch_W * 0.5, pier_depth_y, spandrel_h)  # only fills part above arch peak

        span_inst = tree.nodes.new('GeometryNodeInstanceOnPoints'); span_inst.location = (base_x+3300, 1700)
        tree.links.new(spandrel_line.outputs['Mesh'], span_inst.inputs['Points'])
        tree.links.new(span_block.outputs['Mesh'], span_inst.inputs['Instance'])

        span_real = tree.nodes.new('GeometryNodeRealizeInstances'); span_real.location = (base_x+3600, 1700)
        tree.links.new(span_inst.outputs['Instances'], span_real.inputs['Geometry'])
        parts.append(span_real.outputs['Geometry'])

        # === Walkway - sits directly on top of piers, snap-aligned ===
        deck_thick = 0.18
        if PROPS.bridge_walkway:
            walkway = tree.nodes.new('GeometryNodeMeshCube'); walkway.location = (base_x+3000, 1000); color_node(walkway, "bridge")
            walkway.inputs['Size'].default_value = (L, pier_depth_y * 1.05, deck_thick)  # tiny eave overhang
            walk_t = tree.nodes.new('GeometryNodeTransform'); walk_t.location = (base_x+3300, 1000)
            walk_t.inputs['Translation'].default_value = (0, 0, H + deck_thick/2)  # bottom at H, top at H+thick
            tree.links.new(walkway.outputs['Mesh'], walk_t.inputs['Geometry'])
            parts.append(walk_t.outputs['Geometry'])

        # === Side railings - sit on TOP of walkway, with tiny inset ===
        if PROPS.bridge_railings:
            rail_top = H + deck_thick  # top of walkway
            rail_height = 0.5
            rail_y_inset = 0.03
            for y_off in (-pier_depth_y/2 + rail_y_inset, pier_depth_y/2 - rail_y_inset):
                rail = tree.nodes.new('GeometryNodeMeshCube'); rail.location = (base_x+3000, 1300); color_node(rail, "bridge")
                rail.inputs['Size'].default_value = (L, 0.06, rail_height)
                r_t = tree.nodes.new('GeometryNodeTransform'); r_t.location = (base_x+3300, 1300 + (100 if y_off > 0 else 0))
                r_t.inputs['Translation'].default_value = (0, y_off, rail_top + rail_height/2)
                tree.links.new(rail.outputs['Mesh'], r_t.inputs['Geometry'])
                parts.append(r_t.outputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+4200, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    # ----------------------------------------------------------------------
    # BUILDER: ESCHER PATH (curving impossible loop walkway)
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_venetian_bridge")
    return tree, gin, gout

register_builder(
    "MEL_venetian_bridge", build_venetian_bridge_group,
    "Venetian Bridge", "Euro-classical builder (absorbed from monolith build_venetian_bridge).",
    category="euro")


def build_baroque_vault_group(group_name="MEL_baroque_vault"):
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
        span = getattr(PROPS, 'baroque_vault_span', 6.0)
        depth = getattr(PROPS, 'baroque_vault_depth', 8.0)
        rise = getattr(PROPS, 'baroque_vault_rise', 3.0)
        style = getattr(PROPS, 'baroque_vault_style', 'BARREL')
        ribs = getattr(PROPS, 'baroque_rib_count', 8)
        if style == 'GROIN':
            return _baroque_groin_vault(tree, span, depth, rise, base_x)
        if style == 'RIBBED':
            return _baroque_ribbed_vault(tree, span, depth, rise, ribs, base_x)
        return _baroque_barrel_vault(tree, span, depth, rise, base_x)


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_baroque_vault")
    return tree, gin, gout

register_builder(
    "MEL_baroque_vault", build_baroque_vault_group,
    "Baroque Vault", "Euro-classical builder (absorbed from monolith build_baroque_vault).",
    category="euro")


def build_baroque_facade_group(group_name="MEL_baroque_facade"):
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
        """Baroque facade: pilaster bays + entablature + boolean window rhythm."""
        bays = max(1, getattr(PROPS, 'baroque_facade_bays', 5))
        H = getattr(PROPS, 'baroque_facade_height', 12.0)
        density = getattr(PROPS, 'baroque_ornament_density', 0.5)
        W = bays * 2.4
        t = 0.35
        parts = []
        bay_w = W / bays
        wall = _gb_box(tree, (W, t, H), (0, 0, H * 0.5), base_x, 0)
        cutters = []
        cutter_depth = _gb_opening_cutter_depth(t)
        win_w = bay_w * (0.5 + density * 0.08)
        rows = (
            (H * 0.12, H * 0.22),
            (H * 0.52, H * 0.34),
        )
        if density > 0.35:
            rows = rows + ((H * 0.78, H * 0.14),)
        for i in range(bays):
            wx = -W * 0.5 + (i + 0.5) * bay_w
            for sill_z, win_h in rows:
                wz = sill_z + win_h * 0.5
                c = _gb_box(tree, (win_w, cutter_depth, win_h), (wx, 0, wz), base_x + 200, i * 80, "door")
                if c:
                    cutters.append(c)
        if wall and cutters:
            wall = _gb_bool_diff(tree, wall, cutters, base_x + 400, 0)
        if wall:
            parts.append(wall)
        for i in range(bays + 1):
            x = -W * 0.5 + i * bay_w
            pil = _baroque_pilaster_geom(tree, 0.35, H * 0.92, base_x + 600, i * 50)
            if pil:
                tr = _node(tree, 'GeometryNodeTransform', (base_x + 800, i * 50))
                tr.inputs['Translation'].default_value = (x, t * 0.6, 0)
                _link(tree, pil, tr.inputs['Geometry'])
                parts.append(tr.outputs['Geometry'])
        ent = _gb_box(tree, (W * 1.02, t * 0.8, H * 0.08), (0, t * 0.5, H * 0.96), base_x, 300, 'cornice')
        if ent:
            parts.append(ent)
        ped = _gb_box(tree, (W * 0.92, t * 0.5, H * 0.06), (0, t * 0.55, H * 0.88), base_x, 500, 'cornice')
        if ped and density > 0.25:
            parts.append(ped)
        return _gb_join(tree, parts, base_x + 1000, 0)


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_baroque_facade")
    return tree, gin, gout

register_builder(
    "MEL_baroque_facade", build_baroque_facade_group,
    "Baroque Facade", "Euro-classical builder (absorbed from monolith build_baroque_facade).",
    category="euro")


def build_baroque_niche_group(group_name="MEL_baroque_niche"):
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
        nw = getattr(PROPS, 'baroque_niche_width', 1.2)
        nd = getattr(PROPS, 'baroque_niche_depth', 0.4)
        nh = getattr(PROPS, 'baroque_niche_height', 2.0)
        parts = []
        frame = _gb_box(tree, (nw + 0.2, 0.25, nh + 0.2), (0, 0.12, nh * 0.5), base_x, 0)
        recess = _gb_box(tree, (nw, nd, nh), (0, nd * 0.5, nh * 0.5), base_x, 200)
        if frame:
            parts.append(frame)
        if recess:
            parts.append(recess)
        ped = _gb_box(tree, (nw + 0.4, 0.15, 0.25), (0, 0.08, nh + 0.15), base_x, 400, 'cornice')
        if ped:
            parts.append(ped)
        return _gb_join(tree, parts, base_x + 600, 0)


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_baroque_niche")
    return tree, gin, gout

register_builder(
    "MEL_baroque_niche", build_baroque_niche_group,
    "Baroque Niche", "Euro-classical builder (absorbed from monolith build_baroque_niche).",
    category="euro")


def build_baroque_balustrade_group(group_name="MEL_baroque_balustrade"):
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
        length = getattr(PROPS, 'baroque_balustrade_length', 4.0)
        posts = max(3, getattr(PROPS, 'baroque_balustrade_posts', 9))
        parts = []
        rail = _gb_box(tree, (length, 0.12, 0.1), (0, 0, 1.0), base_x, 0)
        base = _gb_box(tree, (length, 0.15, 0.12), (0, 0, 0.55), base_x, 100)
        if rail:
            parts.append(rail)
        if base:
            parts.append(base)
        for i in range(posts):
            x = -length * 0.5 + (i / max(1, posts - 1)) * length
            bal = _gb_box(tree, (0.1, 0.1, 0.35), (x, 0, 0.75), base_x + 300, i * 30)
            if bal:
                parts.append(bal)
        return _gb_join(tree, parts, base_x + 500, 0)


    # ======================================================================
    # Chinese & Korean traditional architecture builders
    # Distinct from the Japanese ZEN_* builders - derived from the Xie & Wang
    # (2023) modular system for Chinese carpentry and Hanok references.
    # ======================================================================

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_baroque_balustrade")
    return tree, gin, gout

register_builder(
    "MEL_baroque_balustrade", build_baroque_balustrade_group,
    "Baroque Balustrade", "Euro-classical builder (absorbed from monolith build_baroque_balustrade).",
    category="euro")


def build_bifora_group(group_name="MEL_bifora"):
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
        """Venetian bifora: 2+ pointed (or ogee) arches with central colonnettes + quatrefoil oculus."""
        n_lights = PROPS.bifora_lights
        W_total = PROPS.bifora_width
        H = PROPS.bifora_height
        light_W = W_total / n_lights
        half_lw = light_W / 2

        parts = []

        # Profile
        profile = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); profile.location = (base_x, -700); color_node(profile, "venetian")
        profile.mode = 'RADIUS'
        profile.inputs['Resolution'].default_value = 8
        profile.inputs['Radius'].default_value = PROPS.gothic_thickness

        # For each light, build an ogee or pointed arch on a vertical pair of side bars
        for i in range(n_lights):
            cx = -W_total / 2 + light_W * (i + 0.5)  # center X of this light

            if PROPS.bifora_use_ogee:
                # Build ogee curves directly with offset
                rb = tree.nodes.new('GeometryNodeCurvePrimitiveBezierSegment'); rb.location = (base_x + i * 200, 200 + i * 30)
                rb.inputs['Resolution'].default_value = 24
                rb.inputs['Start'].default_value         = (cx + half_lw, 0, 0)
                rb.inputs['Start Handle'].default_value  = (cx + half_lw + 0.2, H * 0.4, 0)
                rb.inputs['End Handle'].default_value    = (cx + half_lw * 0.3, H - 0.2, 0)
                rb.inputs['End'].default_value           = (cx, H * 0.85, 0)

                lb = tree.nodes.new('GeometryNodeCurvePrimitiveBezierSegment'); lb.location = (base_x + i * 200, -200 - i * 30)
                lb.inputs['Resolution'].default_value = 24
                lb.inputs['Start'].default_value         = (cx - half_lw, 0, 0)
                lb.inputs['Start Handle'].default_value  = (cx - half_lw - 0.2, H * 0.4, 0)
                lb.inputs['End Handle'].default_value    = (cx - half_lw * 0.3, H - 0.2, 0)
                lb.inputs['End'].default_value           = (cx, H * 0.85, 0)

                rt = tree.nodes.new('GeometryNodeTransform'); rt.location = (base_x + i * 200 + 200, 200 + i * 30)
                rt.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
                tree.links.new(rb.outputs['Curve'], rt.inputs['Geometry'])

                lt = tree.nodes.new('GeometryNodeTransform'); lt.location = (base_x + i * 200 + 200, -200 - i * 30)
                lt.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
                tree.links.new(lb.outputs['Curve'], lt.inputs['Geometry'])

                for c_socket, y_off in [(rt.outputs['Geometry'], 100 + i * 50),
                                         (lt.outputs['Geometry'], -100 - i * 50)]:
                    sw = tree.nodes.new('GeometryNodeCurveToMesh'); sw.location = (base_x + 800, y_off)
                    tree.links.new(c_socket, sw.inputs['Curve'])
                    tree.links.new(profile.outputs['Curve'], sw.inputs['Profile Curve'])
                    sw.inputs['Fill Caps'].default_value = True
                    parts.append(sw.outputs['Mesh'])
            else:
                # Plain pointed Gothic arches
                R = light_W * 0.7
                peak_angle = math.acos(min(1.0, max(-1.0, (R - half_lw) / R)))

                ra = tree.nodes.new('GeometryNodeCurveArc'); ra.location = (base_x + i * 200, 200 + i * 30); color_node(ra, "venetian")
                ra.mode = 'RADIUS'
                ra.inputs['Resolution'].default_value = 24
                ra.inputs['Radius'].default_value = R
                ra.inputs['Start Angle'].default_value = math.pi - peak_angle
                ra.inputs['Sweep Angle'].default_value = peak_angle

                rt = tree.nodes.new('GeometryNodeTransform'); rt.location = (base_x + i * 200 + 200, 200 + i * 30)
                rt.inputs['Translation'].default_value = (cx - half_lw + R, 0, H * 0.5)
                rt.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
                tree.links.new(ra.outputs['Curve'], rt.inputs['Geometry'])

                la = tree.nodes.new('GeometryNodeCurveArc'); la.location = (base_x + i * 200, -200 - i * 30); color_node(la, "venetian")
                la.mode = 'RADIUS'
                la.inputs['Resolution'].default_value = 24
                la.inputs['Radius'].default_value = R
                la.inputs['Start Angle'].default_value = 0
                la.inputs['Sweep Angle'].default_value = peak_angle

                lt = tree.nodes.new('GeometryNodeTransform'); lt.location = (base_x + i * 200 + 200, -200 - i * 30)
                lt.inputs['Translation'].default_value = (cx + half_lw - R, 0, H * 0.5)
                lt.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
                tree.links.new(la.outputs['Curve'], lt.inputs['Geometry'])

                for c_socket, y_off in [(rt.outputs['Geometry'], 100 + i * 50),
                                         (lt.outputs['Geometry'], -100 - i * 50)]:
                    sw = tree.nodes.new('GeometryNodeCurveToMesh'); sw.location = (base_x + 800, y_off)
                    tree.links.new(c_socket, sw.inputs['Curve'])
                    tree.links.new(profile.outputs['Curve'], sw.inputs['Profile Curve'])
                    sw.inputs['Fill Caps'].default_value = True
                    parts.append(sw.outputs['Mesh'])

            # Vertical bars on each side of this light (sill + jambs)
            # Right jamb
            rj = tree.nodes.new('GeometryNodeMeshCube'); rj.location = (base_x + i * 200, 600); color_node(rj, "venetian")
            rj.inputs['Size'].default_value = (PROPS.gothic_thickness * 1.5, PROPS.gothic_thickness * 1.5, H * 0.5)
            rjt = tree.nodes.new('GeometryNodeTransform'); rjt.location = (base_x + i * 200 + 300, 600)
            rjt.inputs['Translation'].default_value = (cx + half_lw, 0, H * 0.25)
            tree.links.new(rj.outputs['Mesh'], rjt.inputs['Geometry'])
            parts.append(rjt.outputs['Geometry'])

        # Central colonnette(s) between lights
        for i in range(n_lights - 1):
            col_x = -W_total / 2 + light_W * (i + 1)
            col = tree.nodes.new('GeometryNodeMeshCylinder'); col.location = (base_x + i * 200, 1000); color_node(col, "venetian")
            col.inputs['Vertices'].default_value = 16
            col.inputs['Radius'].default_value = PROPS.gothic_thickness * 1.8
            col.inputs['Depth'].default_value = H * 0.85
            ct = tree.nodes.new('GeometryNodeTransform'); ct.location = (base_x + i * 200 + 300, 1000)
            ct.inputs['Translation'].default_value = (col_x, 0, H * 0.42)
            tree.links.new(col.outputs['Mesh'], ct.inputs['Geometry'])
            parts.append(ct.outputs['Geometry'])

            # Capital on top of colonnette
            cap = tree.nodes.new('GeometryNodeMeshCone'); cap.location = (base_x + i * 200, 1300); color_node(cap, "venetian")
            cap.inputs['Vertices'].default_value = 32  # bumped from 16 in v2.31 for smoother shading  # bumped from 12 in v2.31
            cap.inputs['Radius Top'].default_value = PROPS.gothic_thickness * 3
            cap.inputs['Radius Bottom'].default_value = PROPS.gothic_thickness * 2
            cap.inputs['Depth'].default_value = H * 0.05
            capt = tree.nodes.new('GeometryNodeTransform'); capt.location = (base_x + i * 200 + 300, 1300)
            capt.inputs['Translation'].default_value = (col_x, 0, H * 0.85 + H * 0.025)
            tree.links.new(cap.outputs['Mesh'], capt.inputs['Geometry'])
            parts.append(capt.outputs['Geometry'])

        # Quatrefoil oculus above (if enabled)
        if PROPS.bifora_quatrefoil:
            quat = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); quat.location = (base_x, 1600); color_node(quat, "tracery")
            quat.mode = 'RADIUS'
            quat.inputs['Resolution'].default_value = 32
            quat.inputs['Radius'].default_value = light_W * 0.25

            quat_rot = tree.nodes.new('GeometryNodeTransform'); quat_rot.location = (base_x + 300, 1600)
            quat_rot.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
            quat_rot.inputs['Translation'].default_value = (0, 0, H * 0.92)
            tree.links.new(quat.outputs['Curve'], quat_rot.inputs['Geometry'])

            quat_sw = tree.nodes.new('GeometryNodeCurveToMesh'); quat_sw.location = (base_x + 600, 1600)
            tree.links.new(quat_rot.outputs['Geometry'], quat_sw.inputs['Curve'])
            tree.links.new(profile.outputs['Curve'], quat_sw.inputs['Profile Curve'])
            parts.append(quat_sw.outputs['Mesh'])

            # 4 small lobes inside the quatrefoil
            for ang_deg in (0, 90, 180, 270):
                lobe = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); lobe.location = (base_x, 1900); color_node(lobe, "tracery")
                lobe.mode = 'RADIUS'
                lobe.inputs['Resolution'].default_value = 20
                lobe.inputs['Radius'].default_value = light_W * 0.10

                ang = math.radians(ang_deg)
                lt = tree.nodes.new('GeometryNodeTransform'); lt.location = (base_x + 300, 1900)
                lt.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
                lt.inputs['Translation'].default_value = (light_W * 0.13 * math.cos(ang), 0, H * 0.92 + light_W * 0.13 * math.sin(ang))
                tree.links.new(lobe.outputs['Curve'], lt.inputs['Geometry'])

                ls = tree.nodes.new('GeometryNodeCurveToMesh'); ls.location = (base_x + 600, 1900)
                tree.links.new(lt.outputs['Geometry'], ls.inputs['Curve'])
                tree.links.new(profile.outputs['Curve'], ls.inputs['Profile Curve'])
                parts.append(ls.outputs['Mesh'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x + 1200, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_bifora")
    return tree, gin, gout

register_builder(
    "MEL_bifora", build_bifora_group,
    "Bifora", "Euro-classical builder (absorbed from monolith build_bifora).",
    category="euro")


def _impl_build_cusped_arch(tree, PROPS, base_x=-1400):
    """Pointed arch with multi-lobed (foiled) inner edge - Venetian Gothic detail."""
    W = PROPS.cusped_width
    H = PROPS.cusped_height
    n_cusps = PROPS.cusped_lobes
    cusp_d = PROPS.cusped_lobe_depth
    half_W = W / 2

    # Outer arch - same as Gothic arch
    R = max(half_W + 0.001, half_W * 1.4)
    peak_angle = math.acos(min(1.0, max(-1.0, (R - half_W) / R)))

    parts = []

    profile = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); profile.location = (base_x, -700); color_node(profile, "venetian")
    profile.mode = 'RADIUS'
    profile.inputs['Resolution'].default_value = 8
    profile.inputs['Radius'].default_value = PROPS.gothic_thickness

    # Outer right arc
    ra = tree.nodes.new('GeometryNodeCurveArc'); ra.location = (base_x, 200); color_node(ra, "venetian")
    ra.mode = 'RADIUS'
    ra.inputs['Resolution'].default_value = 32
    ra.inputs['Radius'].default_value = R
    ra.inputs['Start Angle'].default_value = math.pi - peak_angle
    ra.inputs['Sweep Angle'].default_value = peak_angle
    rat = tree.nodes.new('GeometryNodeTransform'); rat.location = (base_x + 300, 200)
    rat.inputs['Translation'].default_value = (-half_W + R, 0, 0)
    rat.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
    tree.links.new(ra.outputs['Curve'], rat.inputs['Geometry'])
    rsw = tree.nodes.new('GeometryNodeCurveToMesh'); rsw.location = (base_x + 600, 200)
    tree.links.new(rat.outputs['Geometry'], rsw.inputs['Curve'])
    tree.links.new(profile.outputs['Curve'], rsw.inputs['Profile Curve'])
    parts.append(rsw.outputs['Mesh'])

    # Outer left arc
    la = tree.nodes.new('GeometryNodeCurveArc'); la.location = (base_x, -200); color_node(la, "venetian")
    la.mode = 'RADIUS'
    la.inputs['Resolution'].default_value = 32
    la.inputs['Radius'].default_value = R
    la.inputs['Start Angle'].default_value = 0
    la.inputs['Sweep Angle'].default_value = peak_angle
    lat = tree.nodes.new('GeometryNodeTransform'); lat.location = (base_x + 300, -200)
    lat.inputs['Translation'].default_value = (half_W - R, 0, 0)
    lat.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
    tree.links.new(la.outputs['Curve'], lat.inputs['Geometry'])
    lsw = tree.nodes.new('GeometryNodeCurveToMesh'); lsw.location = (base_x + 600, -200)
    tree.links.new(lat.outputs['Geometry'], lsw.inputs['Curve'])
    tree.links.new(profile.outputs['Curve'], lsw.inputs['Profile Curve'])
    parts.append(lsw.outputs['Mesh'])

    # Inner cusps: small circles arrayed along the inside of the arch
    # Arc length parameterization: place lobes evenly on a sample of the outer arc
    # We sample n_cusps points on the right arc and mirror
    # Use a half-arc that goes all the way around for sampling
    full_arc = tree.nodes.new('GeometryNodeCurveArc'); full_arc.location = (base_x, 700); color_node(full_arc, "tracery")
    full_arc.mode = 'RADIUS'
    full_arc.inputs['Resolution'].default_value = 64
    full_arc.inputs['Radius'].default_value = R - cusp_d
    full_arc.inputs['Start Angle'].default_value = -peak_angle
    full_arc.inputs['Sweep Angle'].default_value = 2 * peak_angle

    fa_t = tree.nodes.new('GeometryNodeTransform'); fa_t.location = (base_x + 300, 700)
    fa_t.inputs['Translation'].default_value = (0, 0, 0)
    fa_t.inputs['Rotation'].default_value = (math.radians(90), 0, math.radians(90))
    # We need to position so the arc spans the full width.
    # Actually simpler: build inner curve by sampling the right arc & mirroring.
    tree.links.new(full_arc.outputs['Curve'], fa_t.inputs['Geometry'])

    sample = tree.nodes.new('GeometryNodeResampleCurve'); sample.location = (base_x + 600, 700); color_node(sample, "tracery")
    sample.inputs['Mode'].default_value = 'Count'
    sample.inputs['Count'].default_value = n_cusps
    tree.links.new(fa_t.outputs['Geometry'], sample.inputs['Curve'])

    c2p = tree.nodes.new('GeometryNodeCurveToPoints'); c2p.location = (base_x + 800, 700)
    c2p.mode = 'EVALUATED'
    tree.links.new(sample.outputs['Curve'], c2p.inputs['Curve'])

    # Lobe sphere
    lobe = tree.nodes.new('GeometryNodeMeshUVSphere'); lobe.location = (base_x, 1000); color_node(lobe, "tracery")
    lobe.inputs['Radius'].default_value = max(0.08, cusp_d * 0.8)
    lobe.inputs['Segments'].default_value = 16
    lobe.inputs['Rings'].default_value = 12

    inst = tree.nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (base_x + 1100, 700)
    tree.links.new(c2p.outputs['Points'], inst.inputs['Points'])
    tree.links.new(lobe.outputs['Mesh'], inst.inputs['Instance'])

    realize = tree.nodes.new('GeometryNodeRealizeInstances'); realize.location = (base_x + 1400, 700)
    tree.links.new(inst.outputs['Instances'], realize.inputs['Geometry'])
    parts.append(realize.outputs['Geometry'])

    join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x + 1700, 0); color_node(join, "output")
    for p in parts: tree.links.new(p, join.inputs['Geometry'])
    return join.outputs['Geometry']



def build_cusped_arch_group(group_name="MEL_cusped_arch"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    geom = _impl_build_cusped_arch(tree, PROPS, base_x)
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_cusped_arch")
    return tree, gin, gout

register_builder(
    "MEL_cusped_arch", build_cusped_arch_group,
    "Cusped Arch", "Euro-classical builder (absorbed from monolith build_cusped_arch).",
    category="euro")
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



def build_ogee_arch_group(group_name="MEL_ogee_arch"):
    tree, gin, gout = new_geometry_tree(group_name)
    for nm, spec in BUILDER_PARAM_DEFAULTS.items():
        t = spec['type']
        if t == 'IntProperty':
            add_int_param(tree, nm.replace('_', ' ').title(), int(spec['default'] or 0), int(spec['min'] or 0), int(spec['max'] or 100))
        elif t == 'BoolProperty':
            add_bool_param(tree, nm.replace('_', ' ').title(), bool(spec['default']))
        elif t == 'StringProperty':
            add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
        else:
            try:
                add_float_param(tree, nm.replace('_', ' ').title(), float(spec['default'] or 0.0), float(spec['min'] or 0.0), float(spec['max'] or 10.0))
            except (TypeError, ValueError):
                add_string_param(tree, nm.replace('_', ' ').title(), str(spec['default'] or ''))
    import types as _types
    PROPS = _types.SimpleNamespace(**{k: v['default'] for k, v in BUILDER_PARAM_DEFAULTS.items()})
    base_x = -1400
    geom = _impl_build_ogee_arch(tree, PROPS, base_x)
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_ogee_arch")
    return tree, gin, gout

register_builder(
    "MEL_ogee_arch", build_ogee_arch_group,
    "Ogee Arch", "Euro-classical builder (absorbed from monolith build_ogee_arch).",
    category="euro")

def build_trefoil_group(group_name="MEL_trefoil"):
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
        """N-lobed Gothic ornament: N circles arranged radially around a center."""
        n_lobes = PROPS.trefoil_lobes
        R_lobe = PROPS.trefoil_radius
        R_outer = PROPS.trefoil_outer

        # Each lobe: a swept circle
        lobe_curve = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); lobe_curve.location = (base_x, 0); color_node(lobe_curve, "gothic")
        lobe_curve.mode = 'RADIUS'
        lobe_curve.inputs['Resolution'].default_value = 32
        lobe_curve.inputs['Radius'].default_value = R_lobe

        lobe_t = tree.nodes.new('GeometryNodeTransform'); lobe_t.location = (base_x+200, 0)
        lobe_t.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
        tree.links.new(lobe_curve.outputs['Curve'], lobe_t.inputs['Geometry'])

        profile = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); profile.location = (base_x, -300); color_node(profile, "gothic")
        profile.mode = 'RADIUS'
        profile.inputs['Resolution'].default_value = 6
        profile.inputs['Radius'].default_value = PROPS.gothic_thickness

        lobe_sweep = tree.nodes.new('GeometryNodeCurveToMesh'); lobe_sweep.location = (base_x+500, 0)
        tree.links.new(lobe_t.outputs['Geometry'], lobe_sweep.inputs['Curve'])
        tree.links.new(profile.outputs['Curve'], lobe_sweep.inputs['Profile Curve'])

        # Place lobes on circle of points
        points_circle = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); points_circle.location = (base_x, 300); color_node(points_circle, "gothic")
        points_circle.mode = 'RADIUS'
        points_circle.inputs['Resolution'].default_value = n_lobes
        points_circle.inputs['Radius'].default_value = R_outer

        pc_t = tree.nodes.new('GeometryNodeTransform'); pc_t.location = (base_x+300, 300)
        pc_t.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
        tree.links.new(points_circle.outputs['Curve'], pc_t.inputs['Geometry'])

        c2p = tree.nodes.new('GeometryNodeCurveToPoints'); c2p.location = (base_x+600, 300)
        c2p.mode = 'EVALUATED'
        tree.links.new(pc_t.outputs['Geometry'], c2p.inputs['Curve'])

        inst = tree.nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (base_x+900, 0)
        tree.links.new(c2p.outputs['Points'], inst.inputs['Points'])
        tree.links.new(lobe_sweep.outputs['Mesh'], inst.inputs['Instance'])

        realize = tree.nodes.new('GeometryNodeRealizeInstances'); realize.location = (base_x+1200, 0)
        tree.links.new(inst.outputs['Instances'], realize.inputs['Geometry'])

        # Outer ring
        outer = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); outer.location = (base_x, -600); color_node(outer, "gothic")
        outer.mode = 'RADIUS'
        outer.inputs['Resolution'].default_value = 64
        outer.inputs['Radius'].default_value = R_outer + R_lobe

        outer_t = tree.nodes.new('GeometryNodeTransform'); outer_t.location = (base_x+300, -600)
        outer_t.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
        tree.links.new(outer.outputs['Curve'], outer_t.inputs['Geometry'])

        outer_sweep = tree.nodes.new('GeometryNodeCurveToMesh'); outer_sweep.location = (base_x+600, -600)
        tree.links.new(outer_t.outputs['Geometry'], outer_sweep.inputs['Curve'])
        tree.links.new(profile.outputs['Curve'], outer_sweep.inputs['Profile Curve'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+1500, 0); color_node(join, "output")
        tree.links.new(realize.outputs['Geometry'], join.inputs['Geometry'])
        tree.links.new(outer_sweep.outputs['Mesh'], join.inputs['Geometry'])
        return join.outputs['Geometry']


    # ----------------------------------------------------------------------
    # BUILDER: ROSE WINDOW
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_trefoil")
    return tree, gin, gout

register_builder(
    "MEL_trefoil", build_trefoil_group,
    "Trefoil", "Euro-classical builder (absorbed from monolith build_trefoil).",
    category="euro")


def build_buttress_group(group_name="MEL_buttress"):
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
        span = PROPS.buttress_span
        height = PROPS.buttress_height
        bow = PROPS.buttress_arch_bow

        # Curve from base to wall
        line = tree.nodes.new('GeometryNodeCurvePrimitiveLine'); line.location = (base_x, 200); color_node(line, "buttress")
        line.mode = 'POINTS'
        line.inputs['Start'].default_value = (0, 0, 0)
        line.inputs['End'].default_value = (span, 0, height)

        # Resample
        sample = tree.nodes.new('GeometryNodeResampleCurve'); sample.location = (base_x+300, 200); color_node(sample, "buttress")
        sample.inputs['Mode'].default_value = 'Count'
        sample.inputs['Count'].default_value = 32
        tree.links.new(line.outputs['Curve'], sample.inputs['Curve'])

        # Arch bow: Set Position with sin(π*t)
        param = tree.nodes.new('GeometryNodeSplineParameter'); param.location = (base_x+300, -200)
        mul_pi = tree.nodes.new('ShaderNodeMath'); mul_pi.location = (base_x+500, -200); mul_pi.operation = 'MULTIPLY'
        mul_pi.inputs[1].default_value = math.pi
        tree.links.new(param.outputs['Factor'], mul_pi.inputs[0])
        sine = tree.nodes.new('ShaderNodeMath'); sine.location = (base_x+700, -200); sine.operation = 'SINE'
        tree.links.new(mul_pi.outputs['Value'], sine.inputs[0])
        bow_h = tree.nodes.new('ShaderNodeMath'); bow_h.location = (base_x+900, -200); bow_h.operation = 'MULTIPLY'
        bow_h.inputs[1].default_value = bow
        tree.links.new(sine.outputs['Value'], bow_h.inputs[0])

        ovec = tree.nodes.new('ShaderNodeCombineXYZ'); ovec.location = (base_x+1100, -200)
        ovec.inputs['X'].default_value = 0; ovec.inputs['Y'].default_value = 0
        tree.links.new(bow_h.outputs['Value'], ovec.inputs['Z'])

        set_arch = tree.nodes.new('GeometryNodeSetPosition'); set_arch.location = (base_x+600, 200); color_node(set_arch, "deform")
        tree.links.new(sample.outputs['Curve'], set_arch.inputs['Geometry'])
        tree.links.new(ovec.outputs['Vector'], set_arch.inputs['Offset'])

        # Profile
        profile = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); profile.location = (base_x, -500); color_node(profile, "buttress")
        profile.mode = 'RADIUS'
        profile.inputs['Resolution'].default_value = 6
        profile.inputs['Radius'].default_value = 0.15

        sweep = tree.nodes.new('GeometryNodeCurveToMesh'); sweep.location = (base_x+1300, 0); color_node(sweep, "buttress")
        tree.links.new(set_arch.outputs['Geometry'], sweep.inputs['Curve'])
        tree.links.new(profile.outputs['Curve'], sweep.inputs['Profile Curve'])
        sweep.inputs['Fill Caps'].default_value = True

        geom = sweep.outputs['Mesh']

        # Decorative bands
        if PROPS.buttress_rib_count > 0:
            sample2 = tree.nodes.new('GeometryNodeResampleCurve'); sample2.location = (base_x+1300, 500); color_node(sample2, "ornament")
            sample2.inputs['Mode'].default_value = 'Count'
            sample2.inputs['Count'].default_value = PROPS.buttress_rib_count
            tree.links.new(set_arch.outputs['Geometry'], sample2.inputs['Curve'])

            c2p = tree.nodes.new('GeometryNodeCurveToPoints'); c2p.location = (base_x+1500, 500)
            c2p.mode = 'EVALUATED'
            tree.links.new(sample2.outputs['Curve'], c2p.inputs['Curve'])

            band = tree.nodes.new('GeometryNodeMeshCylinder'); band.location = (base_x+1500, 700); color_node(band, "ornament")
            band.inputs['Vertices'].default_value = 12
            band.inputs['Radius'].default_value = 0.22
            band.inputs['Depth'].default_value = 0.08

            inst = tree.nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (base_x+1800, 500)
            tree.links.new(c2p.outputs['Points'], inst.inputs['Points'])
            tree.links.new(band.outputs['Mesh'], inst.inputs['Instance'])
            tree.links.new(c2p.outputs['Rotation'], inst.inputs['Rotation'])

            # Musical scale modulation per band
            idx = tree.nodes.new('GeometryNodeInputIndex'); idx.location = (base_x+1500, 900)
            h = make_harmonic_value(tree, idx.outputs['Index'],
                                     PROPS.musical_freq_a, PROPS.musical_freq_b,
                                     PROPS.harmonic_layers, base_x+1700, 900)
            mr = tree.nodes.new('ShaderNodeMapRange'); mr.location = (base_x+2500, 900)
            mr.inputs['From Min'].default_value = -2; mr.inputs['From Max'].default_value = 2
            mr.inputs['To Min'].default_value = 1.0 - PROPS.ornament_density * 0.5
            mr.inputs['To Max'].default_value = 1.0 + PROPS.ornament_density * 0.5
            tree.links.new(h, mr.inputs['Value'])
            sv = tree.nodes.new('ShaderNodeCombineXYZ'); sv.location = (base_x+2700, 900)
            tree.links.new(mr.outputs['Result'], sv.inputs['X'])
            tree.links.new(mr.outputs['Result'], sv.inputs['Y'])
            sv.inputs['Z'].default_value = 1.0

            scale_b = tree.nodes.new('GeometryNodeScaleInstances'); scale_b.location = (base_x+2900, 500)
            tree.links.new(inst.outputs['Instances'], scale_b.inputs['Instances'])
            tree.links.new(sv.outputs['Vector'], scale_b.inputs['Scale'])

            realize = tree.nodes.new('GeometryNodeRealizeInstances'); realize.location = (base_x+3100, 500)
            tree.links.new(scale_b.outputs['Instances'], realize.inputs['Geometry'])

            join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+3400, 0); color_node(join, "output")
            tree.links.new(geom, join.inputs['Geometry'])
            tree.links.new(realize.outputs['Geometry'], join.inputs['Geometry'])
            geom = join.outputs['Geometry']

        # Finial at top of buttress
        if PROPS.buttress_finial_size > 0.01:
            finial = tree.nodes.new('GeometryNodeMeshCone'); finial.location = (base_x+1300, 900); color_node(finial, "ornament")
            finial.inputs['Vertices'].default_value = 16  # bumped from 12 in v2.31
            finial.inputs['Radius Top'].default_value = 0
            finial.inputs['Radius Bottom'].default_value = PROPS.buttress_finial_size * 0.4
            finial.inputs['Depth'].default_value = PROPS.buttress_finial_size

            ftrans = tree.nodes.new('GeometryNodeTransform'); ftrans.location = (base_x+1600, 900)
            ftrans.inputs['Translation'].default_value = (span, 0, height + PROPS.buttress_finial_size/2)
            tree.links.new(finial.outputs['Mesh'], ftrans.inputs['Geometry'])

            join2 = tree.nodes.new('GeometryNodeJoinGeometry'); join2.location = (base_x+3700, 0); color_node(join2, "output")
            tree.links.new(geom, join2.inputs['Geometry'])
            tree.links.new(ftrans.outputs['Geometry'], join2.inputs['Geometry'])
            geom = join2.outputs['Geometry']

        return geom


    # ----------------------------------------------------------------------
    # BUILDER: BUILDING (composite)
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_buttress")
    return tree, gin, gout

register_builder(
    "MEL_buttress", build_buttress_group,
    "Buttress", "Euro-classical builder (absorbed from monolith build_buttress).",
    category="euro")


# 11 builders registered
