"""MEL wall builders — absorbed from the monolith (P2 family 7b).

15 wall/ceiling builders. Params-as-values port. Regenerable.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, add_string_param,
    register_builder,
)


_HIGGSAS_LIB_PATH = (
    r"G:\programs\BlenderPlugins"
    r"\Higgsas_Geometry_Nodes_Toolset_v1.3 vfxMed"
    r"\Higgsas Geo Nodes Blender 5.0"
    r"\Blender 5.0 Higgsas Geo Node Groups v13.blend"
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


def _wall_baseboard_and_cornice(tree, props, length, base_x):
    """Helper: thin baseboard at floor + crown cornice at ceiling. Returns list of geometry sockets."""
    parts = []
    H = props.wall_height
    T = props.wall_thickness
    if props.wall_with_baseboard:
        bb = tree.nodes.new('GeometryNodeMeshCube'); bb.location = (base_x, 200); color_node(bb, "wall")
        bb.inputs['Size'].default_value = (length, T * 1.2, 0.12)
        bb_t = tree.nodes.new('GeometryNodeTransform'); bb_t.location = (base_x+200, 200)
        bb_t.inputs['Translation'].default_value = (0, 0, 0.06)
        tree.links.new(bb.outputs['Mesh'], bb_t.inputs['Geometry'])
        parts.append(bb_t.outputs['Geometry'])
    if props.wall_with_cornice:
        cv = tree.nodes.new('GeometryNodeMeshCube'); cv.location = (base_x, 400); color_node(cv, "wall")
        cv.inputs['Size'].default_value = (length, T * 1.4, 0.18)
        cv_t = tree.nodes.new('GeometryNodeTransform'); cv_t.location = (base_x+200, 400)
        cv_t.inputs['Translation'].default_value = (0, 0, H - 0.09)
        tree.links.new(cv.outputs['Mesh'], cv_t.inputs['Geometry'])
        parts.append(cv_t.outputs['Geometry'])
    return parts


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


# ==============================================================================
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


def _higgsas_available():
    """Return True if the Higgsas library is accessible OR groups already loaded."""
    # Fast path: any Higgsas NT* group already in the file
    for ng in bpy.data.node_groups:
        if ng.name.startswith('NT') and len(ng.name) > 4:
            return True
    # Check the library file on disk
    import os
    return os.path.exists(_HIGGSAS_LIB_PATH)


def _impl_build_pillar(tree, PROPS, base_x=-1400):
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



BUILDER_PARAM_DEFAULTS = {
    "wall_with_baseboard": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "brick_wall_height": {"type": "FloatProperty", "default": 3.0, "min": 0.5, "max": 20.0},
    "brick_wall_width": {"type": "FloatProperty", "default": 4.0, "min": 0.5, "max": 30.0},
    "crenel_merlon_count": {"type": "IntProperty", "default": 10, "min": 2, "max": 60},
    "higgsas_surface_style": {"type": "EnumProperty", "default": 'BRICK', "min": None, "max": None},
    "pillar_capital_layers": {"type": "IntProperty", "default": 2, "min": 1, "max": 5},
    "pillar_capital_size": {"type": "FloatProperty", "default": 0.65, "min": 0.1, "max": 2.0},
    "pillar_flute_depth": {"type": "FloatProperty", "default": 0.025, "min": 0.0, "max": 0.2},
    "pillar_flutes": {"type": "IntProperty", "default": 16, "min": 0, "max": 48},
    "pillar_height": {"type": "FloatProperty", "default": 4.0, "min": 1.0, "max": 15.0},
    "pillar_radius": {"type": "FloatProperty", "default": 0.4, "min": 0.05, "max": 2.0},
    "retaining_batter": {"type": "FloatProperty", "default": 0.08, "min": 0.0, "max": 0.3},
    "retaining_steps": {"type": "IntProperty", "default": 3, "min": 1, "max": 6},
    "unit_size": {"type": "FloatProperty", "default": 2.0, "min": 0.5, "max": 10.0},
    "wall_arched_radius": {"type": "FloatProperty", "default": 0.6, "min": 0.2, "max": 3.0},
    "wall_bay_depth": {"type": "FloatProperty", "default": 0.6, "min": 0.2, "max": 2.0},
    "wall_bay_sides": {"type": "IntProperty", "default": 2, "min": 1, "max": 4},
    "wall_door_height": {"type": "FloatProperty", "default": 2.2, "min": 1.5, "max": 5.0},
    "wall_door_width": {"type": "FloatProperty", "default": 1.2, "min": 0.5, "max": 3.0},
    "wall_frame_width": {"type": "FloatProperty", "default": 0.0, "min": None, "max": None},
    "wall_height": {"type": "FloatProperty", "default": 3.0, "min": 1.0, "max": 10.0},
    "wall_segments": {"type": "IntProperty", "default": 1, "min": 1, "max": 10},
    "wall_thickness": {"type": "FloatProperty", "default": 0.25, "min": 0.05, "max": 2.0},
    "wall_window_grid_x": {"type": "IntProperty", "default": 3, "min": 1, "max": 10},
    "wall_window_grid_y": {"type": "IntProperty", "default": 2, "min": 1, "max": 8},
    "wall_window_height": {"type": "FloatProperty", "default": 1.4, "min": 0.4, "max": 4.0},
    "wall_window_mullion": {"type": "FloatProperty", "default": 0.04, "min": 0.01, "max": 0.2},
    "wall_window_sill": {"type": "FloatProperty", "default": 0.9, "min": 0.0, "max": 3.0},
    "wall_window_width": {"type": "FloatProperty", "default": 1.0, "min": 0.3, "max": 3.0},
    "wall_with_cornice": {"type": "BoolProperty", "default": True, "min": None, "max": None},
}

import types as _types

def _make_props():
    kv = {k: (v["default"] if v["default"] is not None else 0.0)
         for k, v in BUILDER_PARAM_DEFAULTS.items()}
    return _types.SimpleNamespace(**kv)

def _build_colonnade_fallback(tree, PROPS, base_x=-1400):
    """Simple cylinder colonnade - used when the Higgsas path fails."""
    n_cols  = max(2, getattr(PROPS, 'gb_cols_x', 6))
    spacing = getattr(PROPS, 'gb_spacing',    3.0)
    R       = getattr(PROPS, 'pillar_radius', 0.3)
    H       = getattr(PROPS, 'pillar_height', 4.0)
    pieces  = []
    for ci in range(n_cols):
        cx = (ci - (n_cols - 1) * 0.5) * spacing
        cyl = _safe_node(tree, 'GeometryNodeMeshCylinder', (base_x, ci * 200))
        if cyl:
            try:
                cyl.inputs['Vertices'].default_value = 12
                cyl.inputs['Radius'].default_value   = R
                cyl.inputs['Depth'].default_value    = H
            except Exception: pass
            color_node(cyl, "pillar")
            pieces.append(_move(tree, cyl.outputs['Mesh'], (base_x + 200, ci * 200),
                                translation=(cx, 0, H * 0.5), label="pillar"))
    return _join_all(tree, pieces, (base_x + 800, 0))


def _build_higgsas_colonnade_inner(tree, PROPS, base_x=-1400):
    import math as _m
    n_cols   = max(2, getattr(PROPS, 'gb_cols_x', 6))
    spacing  = getattr(PROPS, 'gb_spacing',    3.0)
    R        = getattr(PROPS, 'pillar_radius', 0.3)
    H        = getattr(PROPS, 'pillar_height', 4.0)
    mode     = getattr(PROPS, 'higgsas_array_mode', 'LINEAR')  # LINEAR or RADIAL
    parts    = []

    # ── Single column template ─────────────────────────────────────────
    # Try NTRounded Cube for a more detailed Doric-like profile
    col_body = _higg_node(tree, 'NTRounded Cube', (base_x - 400, 0))
    col_geom = None
    if col_body is not None:
        _higg_input(col_body, 'Size',       (R * 2, R * 2, H))
        _higg_input(col_body, 'Resoliution', 6)
        _higg_input(col_body, 'Radius',     R * 0.12)
        try:
            col_geom = col_body.outputs['Mesh']
        except Exception:
            col_geom = None
    if col_geom is None:
        # Fallback cylinder
        cyl = _safe_node(tree, 'GeometryNodeMeshCylinder', (base_x - 400, 0))
        if cyl:
            try:
                cyl.inputs['Vertices'].default_value = 16
                cyl.inputs['Radius'].default_value   = R
                cyl.inputs['Depth'].default_value    = H
            except Exception: pass
            color_node(cyl, "pillar")
        col_geom = cyl.outputs['Mesh'] if cyl else None

    # Move column so base sits at z=0
    if col_geom is not None:
        shift = _safe_node(tree, 'GeometryNodeTransform', (base_x - 200, 0))
        if shift:
            try: shift.inputs['Translation'].default_value = (0, 0, H * 0.5)
            except Exception: pass
            _link(tree, col_geom, shift.inputs['Geometry'])
            col_geom = shift.outputs['Geometry']
            color_node(shift, "pillar")

    if col_geom is None:
        return None

    # ── Array the column ────────────────────────────────────────────────
    if mode == 'RADIAL':
        arr_node = _higg_node(tree, 'NTCircular Array', (base_x + 200, 0))
        if arr_node is not None:
            _higg_input(arr_node, 'Count',  n_cols)
            _higg_input(arr_node, 'Radius', spacing * n_cols / _m.tau)
            try:
                _link(tree, col_geom, arr_node.inputs['Geometry'])
                real = _safe_node(tree, 'GeometryNodeRealizeInstances', (base_x + 500, 0))
                if real:
                    _link(tree, arr_node.outputs['Instances'], real.inputs['Geometry'])
                    color_node(real, "pillar")
                    parts.append(real.outputs['Geometry'])
            except Exception:
                parts.append(col_geom)
        else:
            # Fallback radial: manual rotation loop
            for i in range(n_cols):
                ang = i * _m.tau / n_cols
                rx  = _m.cos(ang) * spacing * n_cols / _m.tau
                ry  = _m.sin(ang) * spacing * n_cols / _m.tau
                t = _safe_node(tree, 'GeometryNodeTransform', (base_x + 200 + i*120, 0))
                if t:
                    try: t.inputs['Translation'].default_value = (rx, ry, 0)
                    except Exception: pass
                    _link(tree, col_geom, t.inputs['Geometry'])
                    parts.append(t.outputs['Geometry'])
    else:  # LINEAR
        arr_node = _higg_node(tree, 'NTArray', (base_x + 200, 0))
        if arr_node is not None:
            _higg_input(arr_node, 'X Count', n_cols)
            try:
                _link(tree, col_geom, arr_node.inputs['Geometry'])
                arr_geom = arr_node.outputs['Geometry']
                # NTArray outputs instances - realize
                real = _safe_node(tree, 'GeometryNodeRealizeInstances', (base_x + 500, 0))
                if real:
                    _link(tree, arr_geom, real.inputs['Geometry'])
                    color_node(real, "pillar")
                    parts.append(real.outputs['Geometry'])
                else:
                    parts.append(arr_geom)
            except Exception:
                parts.append(col_geom)
        else:
            # Native linear fallback: MeshLine + InstanceOnPoints
            pt_line = _safe_node(tree, 'GeometryNodeMeshLine', (base_x + 200, 0))
            if pt_line:
                try:
                    pt_line.mode = 'END_POINTS'
                    pt_line.inputs['Count'].default_value          = n_cols
                    pt_line.inputs['Start Location'].default_value = (0, 0, 0)
                    pt_line.inputs['Offset'].default_value = (spacing * (n_cols - 1), 0, 0)
                except Exception: pass
                iop = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (base_x + 450, 0))
                if iop:
                    _link(tree, pt_line.outputs['Mesh'], iop.inputs['Points'])
                    _link(tree, col_geom, iop.inputs['Instance'])
                    real = _safe_node(tree, 'GeometryNodeRealizeInstances', (base_x + 700, 0))
                    if real:
                        _link(tree, iop.outputs['Instances'], real.inputs['Geometry'])
                        color_node(real, "pillar")
                        parts.append(real.outputs['Geometry'])

    # ── Entablature beam across the top ──────────────────────────────
    total_span = spacing * (n_cols - 1) + R * 4
    entab = _cube(tree, (base_x, -400), total_span, R * 2.5, R * 1.2, "pillar")
    entab_t = _move(tree, entab, (base_x + 200, -400), translation=(total_span * 0.5 - R * 2, 0, H + R * 0.6), label="pillar")
    if entab_t: parts.append(entab_t)

    return _join_all(tree, parts, (base_x + 1000, 0))


# ==============================================================================
# *  ADVANCED ARCHWAY / BRIDGE / FENCE GENERATORS  (v2.50)
#   Multi-style parametric pieces - all built from curve sweeps + fill-extrude.
#   Styles selectable via PROPS.archway_style / bridge_style / fence_style.
# ==============================================================================


def build_wall_straight_group(group_name="MEL_wall_straight"):
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
        """Standard wall segment - width = wall_segments × unit_size, height = wall_height."""
        L = PROPS.wall_segments * PROPS.unit_size
        H = PROPS.wall_height
        T = PROPS.wall_thickness

        # Main wall slab
        slab = tree.nodes.new('GeometryNodeMeshCube'); slab.location = (base_x, 0); color_node(slab, "wall")
        slab.inputs['Size'].default_value = (L, T, H)
        slab_t = tree.nodes.new('GeometryNodeTransform'); slab_t.location = (base_x+200, 0)
        slab_t.inputs['Translation'].default_value = (0, 0, H/2)
        tree.links.new(slab.outputs['Mesh'], slab_t.inputs['Geometry'])

        parts = [slab_t.outputs['Geometry']]
        parts.extend(_wall_baseboard_and_cornice(tree, PROPS, L, base_x))

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+800, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_wall_straight")
    return tree, gin, gout

register_builder(
    "MEL_wall_straight", build_wall_straight_group,
    "Wall Straight", "Wall builder (absorbed from monolith build_wall_straight).",
    category="structures")


def build_wall_corner_group(group_name="MEL_wall_corner"):
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
        """L-shaped corner wall - two slabs meeting at 90deg."""
        L = PROPS.unit_size
        H = PROPS.wall_height
        T = PROPS.wall_thickness
        parts = []

        # Wall A: along +X
        a = tree.nodes.new('GeometryNodeMeshCube'); a.location = (base_x, 0); color_node(a, "wall")
        a.inputs['Size'].default_value = (L, T, H)
        a_t = tree.nodes.new('GeometryNodeTransform'); a_t.location = (base_x+200, 0)
        a_t.inputs['Translation'].default_value = (L/2, 0, H/2)
        tree.links.new(a.outputs['Mesh'], a_t.inputs['Geometry'])
        parts.append(a_t.outputs['Geometry'])

        # Wall B: along +Y
        b = tree.nodes.new('GeometryNodeMeshCube'); b.location = (base_x, 300); color_node(b, "wall")
        b.inputs['Size'].default_value = (T, L, H)
        b_t = tree.nodes.new('GeometryNodeTransform'); b_t.location = (base_x+200, 300)
        b_t.inputs['Translation'].default_value = (0, L/2, H/2)
        tree.links.new(b.outputs['Mesh'], b_t.inputs['Geometry'])
        parts.append(b_t.outputs['Geometry'])

        # Corner column where they meet (decorative)
        if PROPS.wall_with_cornice:
            cp = tree.nodes.new('GeometryNodeMeshCube'); cp.location = (base_x, 600); color_node(cp, "wall")
            cp.inputs['Size'].default_value = (T * 1.5, T * 1.5, H)
            cp_t = tree.nodes.new('GeometryNodeTransform'); cp_t.location = (base_x+200, 600)
            cp_t.inputs['Translation'].default_value = (0, 0, H/2)
            tree.links.new(cp.outputs['Mesh'], cp_t.inputs['Geometry'])
            parts.append(cp_t.outputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+800, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_wall_corner")
    return tree, gin, gout

register_builder(
    "MEL_wall_corner", build_wall_corner_group,
    "Wall Corner", "Wall builder (absorbed from monolith build_wall_corner).",
    category="structures")


def build_wall_with_door_group(group_name="MEL_wall_with_door"):
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
        """Wall with a door-shaped opening - built as 4 segments (left, top header, right, [no bottom])."""
        L = PROPS.wall_segments * PROPS.unit_size
        H = PROPS.wall_height
        T = PROPS.wall_thickness
        DW = min(PROPS.wall_door_width, L * 0.7)
        DH = min(PROPS.wall_door_height, H * 0.85)

        # Left jamb wall: from -L/2 to -DW/2
        side_w = (L - DW) / 2
        parts = []
        for x_off in (-(L - side_w)/2, +(L - side_w)/2):
            slab = tree.nodes.new('GeometryNodeMeshCube'); slab.location = (base_x, len(parts) * 200); color_node(slab, "wall")
            slab.inputs['Size'].default_value = (side_w, T, H)
            s_t = tree.nodes.new('GeometryNodeTransform'); s_t.location = (base_x+200, len(parts) * 200)
            s_t.inputs['Translation'].default_value = (x_off, 0, H/2)
            tree.links.new(slab.outputs['Mesh'], s_t.inputs['Geometry'])
            parts.append(s_t.outputs['Geometry'])

        # Header above the door
        header_h = H - DH
        header = tree.nodes.new('GeometryNodeMeshCube'); header.location = (base_x, 600); color_node(header, "wall")
        header.inputs['Size'].default_value = (DW, T, header_h)
        h_t = tree.nodes.new('GeometryNodeTransform'); h_t.location = (base_x+200, 600)
        h_t.inputs['Translation'].default_value = (0, 0, DH + header_h/2)
        tree.links.new(header.outputs['Mesh'], h_t.inputs['Geometry'])
        parts.append(h_t.outputs['Geometry'])

        parts.extend(_wall_baseboard_and_cornice(tree, PROPS, L, base_x))

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+800, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_wall_with_door")
    return tree, gin, gout

register_builder(
    "MEL_wall_with_door", build_wall_with_door_group,
    "Wall With Door", "Wall builder (absorbed from monolith build_wall_with_door).",
    category="structures")


def build_wall_with_window_group(group_name="MEL_wall_with_window"):
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
        """Wall with rectangular window opening (5 segments: L, R, top, bottom-sill, [no center])."""
        L = PROPS.wall_segments * PROPS.unit_size
        H = PROPS.wall_height
        T = PROPS.wall_thickness
        WW = min(PROPS.wall_window_width, L * 0.6)
        WH = min(PROPS.wall_window_height, H * 0.6)
        sill = PROPS.wall_window_sill
        parts = []

        side_w = (L - WW) / 2
        for x_off in (-(L - side_w)/2, +(L - side_w)/2):
            slab = tree.nodes.new('GeometryNodeMeshCube'); slab.location = (base_x, len(parts) * 200); color_node(slab, "wall")
            slab.inputs['Size'].default_value = (side_w, T, H)
            s_t = tree.nodes.new('GeometryNodeTransform'); s_t.location = (base_x+200, len(parts) * 200)
            s_t.inputs['Translation'].default_value = (x_off, 0, H/2)
            tree.links.new(slab.outputs['Mesh'], s_t.inputs['Geometry'])
            parts.append(s_t.outputs['Geometry'])

        # Sill (below window)
        sill_h = sill
        if sill_h > 0.01:
            sill_block = tree.nodes.new('GeometryNodeMeshCube'); sill_block.location = (base_x, 500); color_node(sill_block, "wall")
            sill_block.inputs['Size'].default_value = (WW, T, sill_h)
            sb_t = tree.nodes.new('GeometryNodeTransform'); sb_t.location = (base_x+200, 500)
            sb_t.inputs['Translation'].default_value = (0, 0, sill_h/2)
            tree.links.new(sill_block.outputs['Mesh'], sb_t.inputs['Geometry'])
            parts.append(sb_t.outputs['Geometry'])

        # Header (above window)
        header_h = H - sill - WH
        if header_h > 0.01:
            head = tree.nodes.new('GeometryNodeMeshCube'); head.location = (base_x, 700); color_node(head, "wall")
            head.inputs['Size'].default_value = (WW, T, header_h)
            head_t = tree.nodes.new('GeometryNodeTransform'); head_t.location = (base_x+200, 700)
            head_t.inputs['Translation'].default_value = (0, 0, sill + WH + header_h/2)
            tree.links.new(head.outputs['Mesh'], head_t.inputs['Geometry'])
            parts.append(head_t.outputs['Geometry'])

        parts.extend(_wall_baseboard_and_cornice(tree, PROPS, L, base_x))

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+800, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_wall_with_window")
    return tree, gin, gout

register_builder(
    "MEL_wall_with_window", build_wall_with_window_group,
    "Wall With Window", "Wall builder (absorbed from monolith build_wall_with_window).",
    category="structures")


def build_wall_multi_window_group(group_name="MEL_wall_multi_window"):
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
        """Wall with grid of mullioned windows - adjustable rows × cols."""
        L = PROPS.wall_segments * PROPS.unit_size
        H = PROPS.wall_height
        T = PROPS.wall_thickness
        nx = PROPS.wall_window_grid_x
        ny = PROPS.wall_window_grid_y
        mull = PROPS.wall_window_mullion
        parts = []

        # Compute window opening area (with margin from frame)
        margin = max(PROPS.wall_frame_width if hasattr(PROPS, 'wall_frame_width') else 0.2, 0.3)
        win_total_W = L - margin * 2
        win_total_H = H - margin * 2

        # Compute single pane size
        pane_W = (win_total_W - mull * (nx - 1)) / nx
        pane_H = (win_total_H - mull * (ny - 1)) / ny

        # Wall pieces: jambs + sill + header + horizontal/vertical mullions
        # Left & right jambs
        for x_off in (-(L - margin)/2, +(L - margin)/2):
            slab = tree.nodes.new('GeometryNodeMeshCube'); slab.location = (base_x, len(parts) * 100); color_node(slab, "wall")
            slab.inputs['Size'].default_value = (margin, T, H)
            s_t = tree.nodes.new('GeometryNodeTransform'); s_t.location = (base_x+200, len(parts) * 100)
            s_t.inputs['Translation'].default_value = (x_off, 0, H/2)
            tree.links.new(slab.outputs['Mesh'], s_t.inputs['Geometry'])
            parts.append(s_t.outputs['Geometry'])

        # Sill (below window grid)
        sill = tree.nodes.new('GeometryNodeMeshCube'); sill.location = (base_x, 500); color_node(sill, "wall")
        sill.inputs['Size'].default_value = (L - margin * 2, T, margin)
        sill_t = tree.nodes.new('GeometryNodeTransform'); sill_t.location = (base_x+200, 500)
        sill_t.inputs['Translation'].default_value = (0, 0, margin/2)
        tree.links.new(sill.outputs['Mesh'], sill_t.inputs['Geometry'])
        parts.append(sill_t.outputs['Geometry'])

        # Header (above window grid)
        head = tree.nodes.new('GeometryNodeMeshCube'); head.location = (base_x, 700); color_node(head, "wall")
        head.inputs['Size'].default_value = (L - margin * 2, T, margin)
        head_t = tree.nodes.new('GeometryNodeTransform'); head_t.location = (base_x+200, 700)
        head_t.inputs['Translation'].default_value = (0, 0, H - margin/2)
        tree.links.new(head.outputs['Mesh'], head_t.inputs['Geometry'])
        parts.append(head_t.outputs['Geometry'])

        # Vertical mullions
        for i in range(1, nx):
            x = -win_total_W/2 + i * (pane_W + mull) - mull/2
            m_node = tree.nodes.new('GeometryNodeMeshCube'); m_node.location = (base_x, 900 + i * 80); color_node(m_node, "wall")
            m_node.inputs['Size'].default_value = (mull, T * 1.1, win_total_H)
            m_t = tree.nodes.new('GeometryNodeTransform'); m_t.location = (base_x+200, 900 + i * 80)
            m_t.inputs['Translation'].default_value = (x, 0, H/2)
            tree.links.new(m_node.outputs['Mesh'], m_t.inputs['Geometry'])
            parts.append(m_t.outputs['Geometry'])

        # Horizontal mullions
        for j in range(1, ny):
            z = margin + j * (pane_H + mull) - mull/2
            m_node = tree.nodes.new('GeometryNodeMeshCube'); m_node.location = (base_x, 1400 + j * 80); color_node(m_node, "wall")
            m_node.inputs['Size'].default_value = (win_total_W, T * 1.1, mull)
            m_t = tree.nodes.new('GeometryNodeTransform'); m_t.location = (base_x+200, 1400 + j * 80)
            m_t.inputs['Translation'].default_value = (0, 0, z)
            tree.links.new(m_node.outputs['Mesh'], m_t.inputs['Geometry'])
            parts.append(m_t.outputs['Geometry'])

        # Optional glass plane (recessed)
        glass = tree.nodes.new('GeometryNodeMeshCube'); glass.location = (base_x, 1800); color_node(glass, "ornament")
        glass.inputs['Size'].default_value = (win_total_W, mull * 0.5, win_total_H)
        g_t = tree.nodes.new('GeometryNodeTransform'); g_t.location = (base_x+200, 1800)
        g_t.inputs['Translation'].default_value = (0, T * 0.3, H/2)
        tree.links.new(glass.outputs['Mesh'], g_t.inputs['Geometry'])
        parts.append(g_t.outputs['Geometry'])

        # Baseboard/cornice
        parts.extend(_wall_baseboard_and_cornice(tree, PROPS, L, base_x + 2500))

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+2800, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_wall_multi_window")
    return tree, gin, gout

register_builder(
    "MEL_wall_multi_window", build_wall_multi_window_group,
    "Wall Multi Window", "Wall builder (absorbed from monolith build_wall_multi_window).",
    category="structures")


def build_wall_arched_window_group(group_name="MEL_wall_arched_window"):
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
        """Wall with an arched-top window - round arch above rectangular opening."""
        L = PROPS.wall_segments * PROPS.unit_size
        H = PROPS.wall_height
        T = PROPS.wall_thickness
        WW = min(PROPS.wall_window_width, L * 0.6)
        WH = min(PROPS.wall_window_height, H * 0.55)
        arch_R = PROPS.wall_arched_radius
        sill = PROPS.wall_window_sill
        parts = []

        side_w = (L - WW) / 2
        # Side jambs
        for x_off in (-(L - side_w)/2, +(L - side_w)/2):
            slab = tree.nodes.new('GeometryNodeMeshCube'); slab.location = (base_x, len(parts) * 100); color_node(slab, "wall")
            slab.inputs['Size'].default_value = (side_w, T, H)
            s_t = tree.nodes.new('GeometryNodeTransform'); s_t.location = (base_x+200, len(parts) * 100)
            s_t.inputs['Translation'].default_value = (x_off, 0, H/2)
            tree.links.new(slab.outputs['Mesh'], s_t.inputs['Geometry'])
            parts.append(s_t.outputs['Geometry'])

        # Sill block
        sill_block = tree.nodes.new('GeometryNodeMeshCube'); sill_block.location = (base_x, 500); color_node(sill_block, "wall")
        sill_block.inputs['Size'].default_value = (WW, T, sill)
        sb_t = tree.nodes.new('GeometryNodeTransform'); sb_t.location = (base_x+200, 500)
        sb_t.inputs['Translation'].default_value = (0, 0, sill/2)
        tree.links.new(sill_block.outputs['Mesh'], sb_t.inputs['Geometry'])
        parts.append(sb_t.outputs['Geometry'])

        # Arched top - half circle filling the top portion
        arc = tree.nodes.new('GeometryNodeCurveArc'); arc.location = (base_x, 800); color_node(arc, "wall")
        arc.mode = 'RADIUS'
        arc.inputs['Resolution'].default_value = 24
        arc.inputs['Radius'].default_value = arch_R
        arc.inputs['Sweep Angle'].default_value = math.radians(180)

        arc_t = tree.nodes.new('GeometryNodeTransform'); arc_t.location = (base_x+200, 800)
        arc_t.inputs['Translation'].default_value = (0, 0, sill + WH)
        arc_t.inputs['Rotation'].default_value = (math.radians(90), 0, 0)
        tree.links.new(arc.outputs['Curve'], arc_t.inputs['Geometry'])

        # Sweep with profile to make arched frame
        prof = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); prof.location = (base_x, 1000)
        prof.mode = 'RADIUS'
        prof.inputs['Resolution'].default_value = 8
        prof.inputs['Radius'].default_value = T * 0.5

        arc_sweep = tree.nodes.new('GeometryNodeCurveToMesh'); arc_sweep.location = (base_x+400, 800)
        tree.links.new(arc_t.outputs['Geometry'], arc_sweep.inputs['Curve'])
        tree.links.new(prof.outputs['Curve'], arc_sweep.inputs['Profile Curve'])
        arc_sweep.inputs['Fill Caps'].default_value = True
        parts.append(arc_sweep.outputs['Mesh'])

        # Wall above the arch
        top_h = H - sill - WH - arch_R
        if top_h > 0.02:
            top = tree.nodes.new('GeometryNodeMeshCube'); top.location = (base_x, 1200); color_node(top, "wall")
            top.inputs['Size'].default_value = (WW, T, top_h)
            top_t = tree.nodes.new('GeometryNodeTransform'); top_t.location = (base_x+200, 1200)
            top_t.inputs['Translation'].default_value = (0, 0, sill + WH + arch_R + top_h/2)
            tree.links.new(top.outputs['Mesh'], top_t.inputs['Geometry'])
            parts.append(top_t.outputs['Geometry'])

        parts.extend(_wall_baseboard_and_cornice(tree, PROPS, L, base_x + 1500))

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+1800, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_wall_arched_window")
    return tree, gin, gout

register_builder(
    "MEL_wall_arched_window", build_wall_arched_window_group,
    "Wall Arched Window", "Wall builder (absorbed from monolith build_wall_arched_window).",
    category="structures")


def build_wall_bay_window_group(group_name="MEL_wall_bay_window"):
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
        """Wall with projecting bay window - trapezoidal projection forward from main wall."""
        L = PROPS.wall_segments * PROPS.unit_size
        H = PROPS.wall_height
        T = PROPS.wall_thickness
        bay_W = min(PROPS.wall_window_width, L * 0.6)
        bay_D = PROPS.wall_bay_depth
        sides = PROPS.wall_bay_sides
        sill = PROPS.wall_window_sill
        bay_H = min(PROPS.wall_window_height, H * 0.7)
        parts = []

        # Side walls flanking the bay opening
        side_w = (L - bay_W) / 2
        for x_off in (-(L - side_w)/2, +(L - side_w)/2):
            slab = tree.nodes.new('GeometryNodeMeshCube'); slab.location = (base_x, len(parts) * 100); color_node(slab, "wall")
            slab.inputs['Size'].default_value = (side_w, T, H)
            s_t = tree.nodes.new('GeometryNodeTransform'); s_t.location = (base_x+200, len(parts) * 100)
            s_t.inputs['Translation'].default_value = (x_off, 0, H/2)
            tree.links.new(slab.outputs['Mesh'], s_t.inputs['Geometry'])
            parts.append(s_t.outputs['Geometry'])

        # Bay projection - a 5-sided box that sticks forward
        # Front face (parallel to wall, offset bay_D forward)
        front_W = bay_W * (1.0 - 0.2 * sides / 3)
        front = tree.nodes.new('GeometryNodeMeshCube'); front.location = (base_x, 500); color_node(front, "wall")
        front.inputs['Size'].default_value = (front_W, T, bay_H)
        f_t = tree.nodes.new('GeometryNodeTransform'); f_t.location = (base_x+200, 500)
        f_t.inputs['Translation'].default_value = (0, bay_D, sill + bay_H/2)
        tree.links.new(front.outputs['Mesh'], f_t.inputs['Geometry'])
        parts.append(f_t.outputs['Geometry'])

        # Angled side panels (trapezoidal)
        panel_len = math.sqrt(bay_D**2 + ((bay_W - front_W)/2)**2)
        for side_sign in (-1, 1):
            panel = tree.nodes.new('GeometryNodeMeshCube'); panel.location = (base_x, 700); color_node(panel, "wall")
            panel.inputs['Size'].default_value = (panel_len, T, bay_H)
            p_t = tree.nodes.new('GeometryNodeTransform'); p_t.location = (base_x+200, 700)
            # Position at midpoint between corner and front edge
            mid_x = side_sign * (bay_W/2 + front_W/2) / 2
            mid_y = bay_D / 2
            p_t.inputs['Translation'].default_value = (mid_x, mid_y, sill + bay_H/2)
            # Rotate to align with the angled wall
            angle = math.atan2(bay_D, (bay_W - front_W) / 2)
            p_t.inputs['Rotation'].default_value = (0, 0, side_sign * (math.pi/2 - angle))
            tree.links.new(panel.outputs['Mesh'], p_t.inputs['Geometry'])
            parts.append(p_t.outputs['Geometry'])

        # Bay floor & ceiling (caps at bottom and top of bay opening)
        for cap_z, cap_h in [(sill, 0.08), (sill + bay_H, 0.08)]:
            cap = tree.nodes.new('GeometryNodeMeshCube'); cap.location = (base_x, 900 + int(cap_z * 100)); color_node(cap, "wall")
            cap.inputs['Size'].default_value = (bay_W, bay_D * 1.05, cap_h)
            c_t = tree.nodes.new('GeometryNodeTransform'); c_t.location = (base_x+200, 900 + int(cap_z * 100))
            c_t.inputs['Translation'].default_value = (0, bay_D * 0.55, cap_z + cap_h/2)
            tree.links.new(cap.outputs['Mesh'], c_t.inputs['Geometry'])
            parts.append(c_t.outputs['Geometry'])

        # Wall above bay
        top_h = H - (sill + bay_H + 0.1)
        if top_h > 0.05:
            top = tree.nodes.new('GeometryNodeMeshCube'); top.location = (base_x, 1300); color_node(top, "wall")
            top.inputs['Size'].default_value = (bay_W, T, top_h)
            top_t = tree.nodes.new('GeometryNodeTransform'); top_t.location = (base_x+200, 1300)
            top_t.inputs['Translation'].default_value = (0, 0, sill + bay_H + 0.05 + top_h/2)
            tree.links.new(top.outputs['Mesh'], top_t.inputs['Geometry'])
            parts.append(top_t.outputs['Geometry'])

        parts.extend(_wall_baseboard_and_cornice(tree, PROPS, L, base_x + 1600))

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+1900, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    # ----------------------------------------------------------------------
    # UNIVERSAL POST-PASS - make ANY type respond to musical params
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_wall_bay_window")
    return tree, gin, gout

register_builder(
    "MEL_wall_bay_window", build_wall_bay_window_group,
    "Wall Bay Window", "Wall builder (absorbed from monolith build_wall_bay_window).",
    category="structures")


def build_wall_t_join_group(group_name="MEL_wall_t_join"):
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
        """T-intersection wall module: spine wall + perpendicular spur + junction column."""
        L = getattr(PROPS, 'wall_segments', 3) * getattr(PROPS, 'unit_size', 1.0)
        H = getattr(PROPS, 'wall_height', 3.0)
        T = getattr(PROPS, 'wall_thickness', 0.35)
        bh= min(0.12, H * 0.06)
        pieces = []

        # Spine (X-axis, full length)
        pieces.append(_move(tree, _cube(tree, (base_x, 200), L * 2, T, H, "wall"),
                            (base_x + 200, 200), translation=(0, 0, H / 2), label="wall"))
        # Spur (Y-axis, half length, joins at origin)
        pieces.append(_move(tree, _cube(tree, (base_x, -100), T, L, H, "wall"),
                            (base_x + 200, -100), translation=(0, L / 2, H / 2), label="wall"))
        # Junction column
        cs = T * 1.35
        pieces.append(_move(tree, _cube(tree, (base_x, -400), cs, cs, H, "wall"),
                            (base_x + 200, -400), translation=(0, 0, H / 2), label="wall"))
        # Baseboards
        pieces.append(_move(tree, _cube(tree, (base_x, -700), L * 2 + 0.04, T + 0.06, bh, "wall"),
                            (base_x + 200, -700), translation=(0, 0, bh / 2), label="wall"))
        pieces.append(_move(tree, _cube(tree, (base_x, -1000), T + 0.04, L + 0.04, bh, "wall"),
                            (base_x + 200, -1000), translation=(0, L / 2, bh / 2), label="wall"))

        return _join_all(tree, pieces, (base_x + 1000, 0))


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_wall_t_join")
    return tree, gin, gout

register_builder(
    "MEL_wall_t_join", build_wall_t_join_group,
    "Wall T Join", "Wall builder (absorbed from monolith build_wall_t_join).",
    category="structures")


def build_wall_arrow_slits_group(group_name="MEL_wall_arrow_slits"):
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
        """Castle wall section with N cross-shaped arrow slits + battlements."""
        W       = max(3.0, getattr(PROPS, 'wall_segments', 3) * getattr(PROPS, 'unit_size', 1.0) * 1.2)
        H       = getattr(PROPS, 'wall_height', 4.0)
        T       = getattr(PROPS, 'wall_thickness', 0.5)
        n_slits = max(1, getattr(PROPS, 'crenel_merlon_count', 3))
        mw      = W / (n_slits * 2 + 1)
        pieces  = []

        # Main wall
        pieces.append(_move(tree, _cube(tree, (base_x, 200), W, T, H, "tower"),
                            (base_x + 200, 200), translation=(0, 0, H / 2), label="tower"))
        # Battlements (merlons)
        for i in range(n_slits + 1):
            mx = -W / 2 + mw / 2 + i * mw * 2
            pieces.append(_move(tree, _cube(tree, (base_x, -200 - i * 60), mw * 0.9, T, H * 0.18, "tower"),
                                (base_x + 200, -200 - i * 60),
                                translation=(mx, 0, H + H * 0.09), label="tower"))
        # Arrow slit markers (cross-shaped: vertical + horizontal bar)
        slit_h = H * 0.35;  slit_z = H * 0.52
        for i in range(n_slits):
            sx = -W / 2 + W * (i + 1) / (n_slits + 1)
            # Vertical slit
            pieces.append(_move(tree, _cube(tree, (base_x, -800 - i * 80), 0.06, T * 0.55, slit_h, "ornament"),
                                (base_x + 200, -800 - i * 80),
                                translation=(sx, 0, slit_z), label="ornament"))
            # Horizontal cross bar
            pieces.append(_move(tree, _cube(tree, (base_x, -1000 - i * 80), slit_h * 0.18, T * 0.55, 0.09, "ornament"),
                                (base_x + 200, -1000 - i * 80),
                                translation=(sx, 0, slit_z + slit_h * 0.25), label="ornament"))
        # Base plinth
        pieces.append(_move(tree, _cube(tree, (base_x, -1800), W + 0.12, T + 0.1, H * 0.08, "tower"),
                            (base_x + 200, -1800), translation=(0, 0, H * 0.04), label="tower"))

        return _finalize_building(tree, pieces, (base_x + 1200, 0))


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_wall_arrow_slits")
    return tree, gin, gout

register_builder(
    "MEL_wall_arrow_slits", build_wall_arrow_slits_group,
    "Wall Arrow Slits", "Wall builder (absorbed from monolith build_wall_arrow_slits).",
    category="structures")


def build_retaining_wall_group(group_name="MEL_retaining_wall"):
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
        """Battered stone retaining wall with stepped terraces and coping.
        Steps down from raised terrain to grade - UE5 landscape seam piece."""
        W       = max(4.0, getattr(PROPS, 'wall_segments', 3) * getattr(PROPS, 'unit_size', 1.0) * 1.5)
        n_steps = getattr(PROPS, 'retaining_steps', 3)
        batter  = getattr(PROPS, 'retaining_batter', 0.08)
        T_base  = getattr(PROPS, 'wall_thickness', 0.6)
        step_h  = 1.0
        pieces  = []

        for si in range(n_steps):
            top_h  = (n_steps - si) * step_h
            step_T = T_base + batter * top_h
            step_y = si * (T_base + 0.15)
            # Wall tier
            pieces.append(_move(tree, _cube(tree, (base_x, 200 - si * 120), W, step_T, top_h, "tower"),
                                (base_x + 200, 200 - si * 120),
                                translation=(0, -step_y, top_h / 2), label="tower"))
            # Coping row
            pieces.append(_move(tree, _cube(tree, (base_x, -200 - si * 120), W + 0.06, step_T + 0.1, 0.18, "wall"),
                                (base_x + 200, -200 - si * 120),
                                translation=(0, -step_y, top_h + 0.09), label="wall"))

        # Base footing
        foot_d = T_base * (1 + batter * n_steps * step_h) + 0.2
        pieces.append(_move(tree, _cube(tree, (base_x, -1200), W + 0.2, foot_d, 0.35, "tower"),
                            (base_x + 200, -1200), translation=(0, 0, -0.175), label="tower"))

        return _finalize_building(tree, pieces, (base_x + 1200, 0))


    # ==============================================================================
    # *  ENVIRONMENT PROPS  (v2.51)
    # ==============================================================================

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_retaining_wall")
    return tree, gin, gout

register_builder(
    "MEL_retaining_wall", build_retaining_wall_group,
    "Retaining Wall", "Wall builder (absorbed from monolith build_retaining_wall).",
    category="structures")


def build_half_timber_wall_group(group_name="MEL_half_timber_wall"):
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
        """Tudor half-timber wall: plaster infill + horizontal rails + vertical studs
        + X-brace diagonals in each bay on both floor levels."""
        import math
        W    = getattr(PROPS, 'wall_segments', 2) * getattr(PROPS, 'unit_size', 1.0) * 1.5
        H    = getattr(PROPS, 'wall_height', 3.0)
        T    = getattr(PROPS, 'wall_thickness', 0.3)
        bt   = 0.07   # beam/timber thickness
        n_bays = max(2, int(W / 1.2))
        sw   = W / n_bays   # stud spacing
        pieces = []

        # Infill panel
        pieces.append(_move(tree, _cube(tree, (base_x, 200), W, T, H, "wall"),
                            (base_x + 200, 200), translation=(0, 0, H / 2), label="wall"))
        # Horizontal rails (top / mid / bottom)
        for frac in [0.0, 0.5, 1.0]:
            pieces.append(_move(tree, _cube(tree, (base_x, -200 + int(frac * 100)),
                                            W + 0.06, T + 0.04, bt, "ornament"),
                                (base_x + 200, -200 + int(frac * 100)),
                                translation=(0, 0, frac * H), label="ornament"))
        # Vertical studs
        for si in range(n_bays + 1):
            sx = -W / 2 + si * sw
            pieces.append(_move(tree, _cube(tree, (base_x, -800 - si * 60), bt, T + 0.04, H, "ornament"),
                                (base_x + 200, -800 - si * 60),
                                translation=(sx, 0, H / 2), label="ornament"))
        # X-brace diagonals in each bay × 2 floor rows
        for row in range(2):
            bz = row * H / 2
            for bi in range(n_bays):
                x0  = -W / 2 + bi * sw
                x1  = x0 + sw
                dl  = math.sqrt(sw ** 2 + (H / 2) ** 2)
                ang = math.atan2(H / 2, sw)
                for sd, sign in [(-1, ang), (1, -ang)]:
                    pieces.append(_move(tree,
                                        _cube(tree, (base_x, -2000 - row*400 - bi*80 + sd*40),
                                              dl, T + 0.04, bt, "ornament"),
                                        (base_x + 200, -2000 - row*400 - bi*80 + sd*40),
                                        translation=((x0 + x1) / 2, 0, bz + H / 4),
                                        rotation=(0, sign, 0), label="ornament"))

        return _finalize_building(tree, pieces, (base_x + 1200, 0))


    # ==============================================================================
    # *  HIGGSAS-POWERED BUILDERS  (v2.52)
    #   Builders that showcase specific Higgsas node groups.
    #   Each builder falls back gracefully when Higgsas is not loaded.
    # ==============================================================================

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_half_timber_wall")
    return tree, gin, gout

register_builder(
    "MEL_half_timber_wall", build_half_timber_wall_group,
    "Half Timber Wall", "Wall builder (absorbed from monolith build_half_timber_wall).",
    category="structures")


def build_higgsas_surface_wall_group(group_name="MEL_higgsas_surface_wall"):
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
        """Higgsas Surface Wall: a tall wall whose face is overlaid with one of four
        Higgsas procedural patterns, selectable via `higgsas_surface_style`.
          BRICK  -> NTBricks Grid (staggered courses, custom mortar)
          HEX    -> NTHexagon Grid (hexagonal tiles, great for dungeon floors)
          VORONOI-> NTDistance to Edge Voronoi (natural stone cell pattern)
          CAIRO  -> NTCairo Tile Grid (Islamic decorative tiling)
        The wall body is a solidified flat grid. UV mapping via NTTriplanar.
        Falls back to a plain brick wall when Higgsas is not available."""
        W  = getattr(PROPS, 'brick_wall_width',  4.0)
        H  = getattr(PROPS, 'brick_wall_height', 3.0)
        T  = getattr(PROPS, 'wall_thickness',    0.3)
        style = getattr(PROPS, 'higgsas_surface_style', 'BRICK')
        parts = []

        # ── Base wall slab (flat grid to drive patterns) ──────────────────
        grid = _safe_node(tree, 'GeometryNodeMeshGrid', (base_x, 0))
        if grid:
            try:
                grid.inputs['Size X'].default_value = W
                grid.inputs['Size Y'].default_value = H
                grid.inputs['Vertices X'].default_value = max(4, int(W * 4))
                grid.inputs['Vertices Y'].default_value = max(4, int(H * 4))
            except Exception: pass
            color_node(grid, "brick")
            base_geom = grid.outputs['Mesh']
        else:
            return None

        # ── Surface pattern overlay via Higgsas ──────────────────────────
        node_name_map = {
            'BRICK':   'NTBricks Grid',
            'HEX':     'NTHexagon Grid',
            'VORONOI': 'NTDistance to Edge Voronoi',
            'CAIRO':   'NTCairo Tile Grid',
            'TRIANGLE':'NTTriangle Grid',
        }
        nt_name = node_name_map.get(style, 'NTBricks Grid')
        pat_node = _higg_node(tree, nt_name, (base_x + 400, 0))
        if pat_node is not None:
            # Configure common inputs
            if style == 'BRICK':
                _higg_input(pat_node, 'X Grid Size', W)
                _higg_input(pat_node, 'Y Grid Size', H)
            elif style in ('HEX', 'TRIANGLE'):
                _higg_input(pat_node, 'Size', W)
                _higg_input(pat_node, 'Hex X', max(2, int(W / 0.5)))
                _higg_input(pat_node, 'Hex Y', max(2, int(H / 0.5)))
            elif style == 'VORONOI':
                _higg_input(pat_node, 'Smoothness', 0.05)
            elif style == 'CAIRO':
                _higg_input(pat_node, 'Size', min(W, H) * 0.3)
                _higg_input(pat_node, 'Tile X', max(2, int(W / 0.3)))
                _higg_input(pat_node, 'Tile Y', max(2, int(H / 0.3)))
            # Pattern geometry as surface overlay
            pat_geom = pat_node.outputs[0]
            # Solidify pattern for depth
            solid = _higg_node(tree, 'NTSolidify', (base_x + 800, 0))
            if solid is not None:
                _higg_input(solid, 'Thickness',      T)
                _higg_input(solid, 'Even Thickness', True)
                try:
                    _link(tree, pat_geom, solid.inputs['Mesh'])
                    pat_geom = solid.outputs['Mesh']
                except Exception: pass
            # Add UV mapping for game export
            uv_node = _higg_node(tree, 'NTTriplanar UV Mapping', (base_x + 1200, 0))
            if uv_node is not None:
                try:
                    _link(tree, pat_geom, uv_node.inputs['Mesh'])
                    pat_geom = uv_node.outputs['Mesh']
                except Exception: pass
            parts.append(pat_geom)
        else:
            # Fallback: solidified plain grid wall
            ext = _safe_node(tree, 'GeometryNodeExtrudeMesh', (base_x + 400, 0))
            if ext:
                ext.mode = 'FACES'
                try: ext.inputs['Offset Scale'].default_value = T
                except Exception: pass
                _link(tree, base_geom, ext.inputs['Mesh'])
                color_node(ext, "brick")
                parts.append(ext.outputs['Mesh'])
            else:
                parts.append(base_geom)

        # ── Orient: rotate XY grid to stand up as a wall (XZ plane) ─────
        rot = _safe_node(tree, 'GeometryNodeTransform', (base_x + 1600, 0))
        if rot and parts:
            try:
                rot.inputs['Rotation'].default_value    = (math.radians(90), 0, 0)
                rot.inputs['Translation'].default_value = (0, 0, H * 0.5)
            except Exception: pass
            _link(tree, parts[0], rot.inputs['Geometry'])
            color_node(rot, "brick")
            return rot.outputs['Geometry']
        return parts[0] if parts else None


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_higgsas_surface_wall")
    return tree, gin, gout

register_builder(
    "MEL_higgsas_surface_wall", build_higgsas_surface_wall_group,
    "Higgsas Surface Wall", "Wall builder (absorbed from monolith build_higgsas_surface_wall).",
    category="structures")


def build_higgsas_colonnade_group(group_name="MEL_higgsas_colonnade"):
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
        """Higgsas Colonnade: a row of columns with Higgsas NTRounded Cube profile
        and NTArray instancing. Falls back to plain cylinder columns gracefully.
        In-game use: temple forecourt, palace arcade, Venetian loggia."""
        try:
            return _build_higgsas_colonnade_inner(tree, PROPS, base_x)
        except Exception:
            # Emergency fallback: simple cylinder row
            return _build_colonnade_fallback(tree, PROPS, base_x)


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_higgsas_colonnade")
    return tree, gin, gout

register_builder(
    "MEL_higgsas_colonnade", build_higgsas_colonnade_group,
    "Higgsas Colonnade", "Wall builder (absorbed from monolith build_higgsas_colonnade).",
    category="structures")


def build_ceiling_tile_group(group_name="MEL_ceiling_tile"):
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
        """Ceiling tile - matches floor unit. Optional decorative coffer pattern."""
        L = PROPS.unit_size
        parts = []

        slab = tree.nodes.new('GeometryNodeMeshCube'); slab.location = (base_x, 0); color_node(slab, "ceiling")
        slab.inputs['Size'].default_value = (L, L, 0.1)
        parts.append(slab.outputs['Mesh'])

        # Coffer (decorative inset square)
        coffer = tree.nodes.new('GeometryNodeMeshCube'); coffer.location = (base_x, 200); color_node(coffer, "ceiling")
        coffer.inputs['Size'].default_value = (L * 0.7, L * 0.7, 0.04)
        c_t = tree.nodes.new('GeometryNodeTransform'); c_t.location = (base_x+200, 200)
        c_t.inputs['Translation'].default_value = (0, 0, -0.07)
        tree.links.new(coffer.outputs['Mesh'], c_t.inputs['Geometry'])
        parts.append(c_t.outputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+500, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_ceiling_tile")
    return tree, gin, gout

register_builder(
    "MEL_ceiling_tile", build_ceiling_tile_group,
    "Ceiling Tile", "Wall builder (absorbed from monolith build_ceiling_tile).",
    category="structures")


def build_corner_pillar_group(group_name="MEL_corner_pillar"):
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
        """Decorative corner column - base + fluted shaft + capital. Snaps to wall corners."""
        H = PROPS.wall_height
        R = PROPS.wall_thickness * 1.2
        parts = []

        # Square base
        base = tree.nodes.new('GeometryNodeMeshCube'); base.location = (base_x, 0); color_node(base, "wall")
        base.inputs['Size'].default_value = (R * 1.6, R * 1.6, 0.18)
        b_t = tree.nodes.new('GeometryNodeTransform'); b_t.location = (base_x+200, 0)
        b_t.inputs['Translation'].default_value = (0, 0, 0.09)
        tree.links.new(base.outputs['Mesh'], b_t.inputs['Geometry'])
        parts.append(b_t.outputs['Geometry'])

        # Fluted shaft (use saved pillar logic)
        saved = (PROPS.pillar_radius, PROPS.pillar_height, PROPS.pillar_flutes,
                 PROPS.pillar_capital_size, PROPS.pillar_capital_layers)
        PROPS.pillar_radius = R
        PROPS.pillar_height = H - 0.4
        PROPS.pillar_flutes = 12
        PROPS.pillar_capital_size = R * 1.6
        PROPS.pillar_capital_layers = 2
        shaft = _impl_build_pillar(tree, PROPS, base_x=base_x+500)
        PROPS.pillar_radius, PROPS.pillar_height, PROPS.pillar_flutes, PROPS.pillar_capital_size, PROPS.pillar_capital_layers = saved

        sh_t = tree.nodes.new('GeometryNodeTransform'); sh_t.location = (base_x+2200, 0); color_node(sh_t, "wall")
        sh_t.inputs['Translation'].default_value = (0, 0, H/2)
        tree.links.new(shaft, sh_t.inputs['Geometry'])
        parts.append(sh_t.outputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+2500, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    # ----------------------------------------------------------------------
    # CASCADING BEAMS (Erindale-inspired) - N parallel beams with per-step offsets
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_corner_pillar")
    return tree, gin, gout

register_builder(
    "MEL_corner_pillar", build_corner_pillar_group,
    "Corner Pillar", "Wall builder (absorbed from monolith build_corner_pillar).",
    category="structures")


# 15 builders registered
