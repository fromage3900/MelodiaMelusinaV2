"""MEL building generators — absorbed from the monolith (P2 family 8).

modular/curved/radial/auto buildings + raycast facade. Wall cross-calls
served by module-level impls. Params-as-values port. Regenerable.
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


def _impl_build_wall_straight(tree, PROPS, base_x=-1400):
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


def _impl_build_wall_with_door(tree, PROPS, base_x=-1400):
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


def _impl_build_wall_with_window(tree, PROPS, base_x=-1400):
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


def _impl_build_dome(tree, PROPS, base_x=-1400):
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



BUILDER_PARAM_DEFAULTS = {
    "wall_with_cornice": {"type": "FloatProperty", "default": 0.0, "min": 0.0, "max": 10.0},
    "wall_with_baseboard": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "base_radius": {"type": "FloatProperty", "default": 1.2, "min": 0.1, "max": 10.0},
    "bld_balconies": {"type": "BoolProperty", "default": False, "min": None, "max": None},
    "bld_depth_b": {"type": "FloatProperty", "default": 8.0, "min": 3.0, "max": 40.0},
    "bld_floor_count_b": {"type": "IntProperty", "default": 8, "min": 1, "max": 80},
    "bld_floor_height_b": {"type": "FloatProperty", "default": 3.2, "min": 2.0, "max": 6.0},
    "bld_ground_retail": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "bld_rooftop": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "bld_setbacks": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "bld_style": {"type": "EnumProperty", "default": 'COMMERCIAL', "min": None, "max": None},
    "bld_width": {"type": "FloatProperty", "default": 10.0, "min": 3.0, "max": 60.0},
    "bld_win_cols": {"type": "IntProperty", "default": 4, "min": 1, "max": 24},
    "bld_win_h": {"type": "FloatProperty", "default": 1.4, "min": 0.3, "max": 3.0},
    "bld_win_rows": {"type": "IntProperty", "default": 1, "min": 0, "max": 4},
    "bld_win_w": {"type": "FloatProperty", "default": 0.7, "min": 0.1, "max": 2.0},
    "complexity_level": {"type": "IntProperty", "default": 3, "min": 1, "max": 5},
    "curved_arc_deg": {"type": "FloatProperty", "default": 90.0, "min": 15.0, "max": 270.0},
    "curved_arches_per_unit": {"type": "IntProperty", "default": 1, "min": 1, "max": 4},
    "curved_floors": {"type": "IntProperty", "default": 2, "min": 1, "max": 6},
    "curved_radius": {"type": "FloatProperty", "default": 8.0, "min": 2.0, "max": 40.0},
    "dome_radius": {"type": "FloatProperty", "default": 1.5, "min": 0.3, "max": 10.0},
    "dome_rib_count": {"type": "IntProperty", "default": 8, "min": 0, "max": 32},
    "dome_rings": {"type": "IntProperty", "default": 16, "min": 4, "max": 48},
    "dome_segments": {"type": "IntProperty", "default": 32, "min": 8, "max": 96},
    "dome_spire": {"type": "FloatProperty", "default": 0.8, "min": 0.0, "max": 5.0},
    "gothic_thickness": {"type": "FloatProperty", "default": 0.12, "min": 0.02, "max": 1.0},
    "height": {"type": "FloatProperty", "default": 5.0, "min": 0.5, "max": 30.0},
    "house_floors": {"type": "IntProperty", "default": 2, "min": 1, "max": 6},
    "house_units_x": {"type": "IntProperty", "default": 2, "min": 1, "max": 8},
    "house_units_y": {"type": "IntProperty", "default": 2, "min": 1, "max": 8},
    "house_with_chimney": {"type": "BoolProperty", "default": False, "min": None, "max": None},
    "house_with_door": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "house_with_roof": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "house_with_windows": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "ogee_finial": {"type": "FloatProperty", "default": 0.4, "min": 0.0, "max": 2.0},
    "ogee_height": {"type": "FloatProperty", "default": 3.0, "min": 1.0, "max": 12.0},
    "ogee_shoulder": {"type": "FloatProperty", "default": 0.7, "min": 0.1, "max": 2.0},
    "ogee_swell": {"type": "FloatProperty", "default": 0.4, "min": 0.0, "max": 1.5},
    "ogee_width": {"type": "FloatProperty", "default": 2.0, "min": 0.5, "max": 8.0},
    "radial_building_arches": {"type": "IntProperty", "default": 8, "min": 4, "max": 32},
    "radial_building_dome": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "radial_building_floors": {"type": "IntProperty", "default": 2, "min": 1, "max": 6},
    "radial_building_radius": {"type": "FloatProperty", "default": 4.0, "min": 1.0, "max": 20.0},
    "recursion_depth": {"type": "IntProperty", "default": 3, "min": 1, "max": 6},
    "scifi_effect": {"type": "EnumProperty", "default": 'GREEBLE', "min": None, "max": None},
    "seed": {"type": "IntProperty", "default": 42, "min": 0, "max": 9999},
    "unit_size": {"type": "FloatProperty", "default": 2.0, "min": 0.5, "max": 10.0},
    "wall_door_height": {"type": "FloatProperty", "default": 2.2, "min": 1.5, "max": 5.0},
    "wall_door_width": {"type": "FloatProperty", "default": 1.2, "min": 0.5, "max": 3.0},
    "wall_height": {"type": "FloatProperty", "default": 3.0, "min": 1.0, "max": 10.0},
    "wall_segments": {"type": "IntProperty", "default": 1, "min": 1, "max": 10},
    "wall_thickness": {"type": "FloatProperty", "default": 0.25, "min": 0.05, "max": 2.0},
    "wall_window_height": {"type": "FloatProperty", "default": 1.4, "min": 0.4, "max": 4.0},
    "wall_window_sill": {"type": "FloatProperty", "default": 0.9, "min": 0.0, "max": 3.0},
    "wall_window_width": {"type": "FloatProperty", "default": 1.0, "min": 0.3, "max": 3.0},
}

import types as _types

def _make_props():
    kv = {k: (v["default"] if v["default"] is not None else 0.0)
         for k, v in BUILDER_PARAM_DEFAULTS.items()}
    return _types.SimpleNamespace(**kv)

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



def build_modular_house_group(group_name="MEL_modular_house"):
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
        """Composite house - uses unit_size grid. 4 walls (front has door, sides have windows), pitched roof, optional chimney."""
        U = PROPS.unit_size
        Wx = PROPS.house_units_x * U
        Wy = PROPS.house_units_y * U
        H_per_floor = PROPS.wall_height
        floors = PROPS.house_floors
        total_h = floors * H_per_floor
        parts = []

        # Save and override wall properties for each face
        saved = (PROPS.wall_segments, PROPS.wall_door_width, PROPS.wall_door_height,
                 PROPS.wall_window_width, PROPS.wall_window_height, PROPS.wall_height)

        for floor in range(floors):
            z_floor = floor * H_per_floor

            # FRONT (-Y face) - has door if floor 0
            PROPS.wall_segments = PROPS.house_units_x
            PROPS.wall_height = H_per_floor
            if floor == 0 and PROPS.house_with_door:
                front_geom = _impl_build_wall_with_door(tree, PROPS, base_x=base_x + (1500 if floor == 0 else 0))
            else:
                front_geom = _impl_build_wall_straight(tree, PROPS, base_x=base_x + 3000 + floor * 1500)
            ft = tree.nodes.new('GeometryNodeTransform'); ft.location = (base_x+5000, floor * 200); color_node(ft, "house")
            ft.inputs['Translation'].default_value = (0, -Wy/2, z_floor)
            tree.links.new(front_geom, ft.inputs['Geometry'])
            parts.append(ft.outputs['Geometry'])

            # BACK (+Y face) - plain
            back_geom = _impl_build_wall_straight(tree, PROPS, base_x=base_x + 6000 + floor * 1500)
            bt = tree.nodes.new('GeometryNodeTransform'); bt.location = (base_x+8000, floor * 200); color_node(bt, "house")
            bt.inputs['Translation'].default_value = (0, Wy/2, z_floor)
            bt.inputs['Rotation'].default_value = (0, 0, math.radians(180))
            tree.links.new(back_geom, bt.inputs['Geometry'])
            parts.append(bt.outputs['Geometry'])

            # LEFT (-X face) - windows on upper floors
            PROPS.wall_segments = PROPS.house_units_y
            if floor > 0 and PROPS.house_with_windows:
                left_geom = _impl_build_wall_with_window(tree, PROPS, base_x=base_x + 9000 + floor * 1500)
            else:
                left_geom = _impl_build_wall_straight(tree, PROPS, base_x=base_x + 11000 + floor * 1500)
            lt = tree.nodes.new('GeometryNodeTransform'); lt.location = (base_x+13000, floor * 200); color_node(lt, "house")
            lt.inputs['Translation'].default_value = (-Wx/2, 0, z_floor)
            lt.inputs['Rotation'].default_value = (0, 0, math.radians(90))
            tree.links.new(left_geom, lt.inputs['Geometry'])
            parts.append(lt.outputs['Geometry'])

            # RIGHT (+X face) - windows on upper floors
            if floor > 0 and PROPS.house_with_windows:
                right_geom = _impl_build_wall_with_window(tree, PROPS, base_x=base_x + 14000 + floor * 1500)
            else:
                right_geom = _impl_build_wall_straight(tree, PROPS, base_x=base_x + 16000 + floor * 1500)
            rt = tree.nodes.new('GeometryNodeTransform'); rt.location = (base_x+18000, floor * 200); color_node(rt, "house")
            rt.inputs['Translation'].default_value = (Wx/2, 0, z_floor)
            rt.inputs['Rotation'].default_value = (0, 0, math.radians(-90))
            tree.links.new(right_geom, rt.inputs['Geometry'])
            parts.append(rt.outputs['Geometry'])

        # Restore wall PROPS
        (PROPS.wall_segments, PROPS.wall_door_width, PROPS.wall_door_height,
         PROPS.wall_window_width, PROPS.wall_window_height, PROPS.wall_height) = saved

        # Roof
        if PROPS.house_with_roof:
            # Pitched roof - two angled cubes meeting at a ridge
            roof_pitch = math.radians(35)
            roof_h = (Wy / 2) * math.tan(roof_pitch)
            slope_len = (Wy / 2) / math.cos(roof_pitch)
            for sign in (-1, 1):
                slab = tree.nodes.new('GeometryNodeMeshCube'); slab.location = (base_x+19000, 200 + sign * 100); color_node(slab, "house")
                slab.inputs['Size'].default_value = (Wx, slope_len, 0.15)
                st = tree.nodes.new('GeometryNodeTransform'); st.location = (base_x+19500, 200 + sign * 100)
                st.inputs['Translation'].default_value = (0, sign * Wy/4, total_h + roof_h/2)
                # NEGATIVE pitch so eaves drop OUTWARD from ridge (apex on top).
                # Previously this was `sign * roof_pitch` which inverted the roof.
                st.inputs['Rotation'].default_value = (sign * -roof_pitch, 0, 0)
                tree.links.new(slab.outputs['Mesh'], st.inputs['Geometry'])
                parts.append(st.outputs['Geometry'])

        # Chimney
        if PROPS.house_with_chimney:
            ch = tree.nodes.new('GeometryNodeMeshCube'); ch.location = (base_x+19000, 600); color_node(ch, "house")
            ch.inputs['Size'].default_value = (0.6, 0.6, 1.5)
            ch_t = tree.nodes.new('GeometryNodeTransform'); ch_t.location = (base_x+19500, 600)
            ch_t.inputs['Translation'].default_value = (Wx/3, Wy/4, total_h + 1.0)
            tree.links.new(ch.outputs['Mesh'], ch_t.inputs['Geometry'])
            parts.append(ch_t.outputs['Geometry'])

        # Floor slab at base
        floor_slab = tree.nodes.new('GeometryNodeMeshCube'); floor_slab.location = (base_x+19000, -200); color_node(floor_slab, "house")
        floor_slab.inputs['Size'].default_value = (Wx, Wy, 0.15)
        fs_t = tree.nodes.new('GeometryNodeTransform'); fs_t.location = (base_x+19500, -200)
        fs_t.inputs['Translation'].default_value = (0, 0, -0.075)
        tree.links.new(floor_slab.outputs['Mesh'], fs_t.inputs['Geometry'])
        parts.append(fs_t.outputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+20000, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    # ----------------------------------------------------------------------
    # CURVED BUILDING - palazzo facade following an arc
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_modular_house")
    return tree, gin, gout

register_builder(
    "MEL_modular_house", build_modular_house_group,
    "Modular House", "Building generator (absorbed from monolith build_modular_house).",
    category="structures")


def build_curved_building_group(group_name="MEL_curved_building"):
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
        """Palazzo facade bent along an arc - instances arches around the curve."""
        R = PROPS.curved_radius
        sweep = math.radians(PROPS.curved_arc_deg)
        floors = PROPS.curved_floors
        arches_per_unit = PROPS.curved_arches_per_unit
        floor_h = PROPS.wall_height

        # Total arches = arches_per_unit × ceil(arc_length / unit_size)
        arc_length = R * sweep
        total_arches = max(1, int(arc_length / PROPS.unit_size * arches_per_unit))
        parts = []

        # Build arc curve
        arc = tree.nodes.new('GeometryNodeCurveArc'); arc.location = (base_x, 0); color_node(arc, "level")
        arc.mode = 'RADIUS'
        arc.inputs['Resolution'].default_value = total_arches
        arc.inputs['Radius'].default_value = R
        arc.inputs['Start Angle'].default_value = -sweep / 2
        arc.inputs['Sweep Angle'].default_value = sweep

        # Sample arc points (one per arch position)
        samp = tree.nodes.new('GeometryNodeResampleCurve'); samp.location = (base_x+200, 0); color_node(samp, "level")
        samp.inputs['Mode'].default_value = 'Count'
        samp.inputs['Count'].default_value = total_arches
        tree.links.new(arc.outputs['Curve'], samp.inputs['Curve'])

        c2p = tree.nodes.new('GeometryNodeCurveToPoints'); c2p.location = (base_x+450, 0); color_node(c2p, "level")
        c2p.mode = 'EVALUATED'
        tree.links.new(samp.outputs['Curve'], c2p.inputs['Curve'])

        # Per-floor: build an ogee arch piece, instance along the arc
        saved = (PROPS.ogee_width, PROPS.ogee_height, PROPS.ogee_finial)
        for floor in range(floors):
            # Size arch to fit one segment
            arch_w = (arc_length / total_arches) * 0.85
            PROPS.ogee_width  = arch_w
            PROPS.ogee_height = floor_h * 0.85
            PROPS.ogee_finial = 0.0
            arch_geom = _impl_build_ogee_arch(tree, PROPS, base_x=base_x + 1500 + floor * 4500)

            # Position the arch at z = floor * floor_h, tangent to the arc
            inst = tree.nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (base_x+5000, floor * 300); color_node(inst, "level")
            tree.links.new(c2p.outputs['Points'], inst.inputs['Points'])
            tree.links.new(arch_geom, inst.inputs['Instance'])
            tree.links.new(c2p.outputs['Rotation'], inst.inputs['Rotation'])

            ti = tree.nodes.new('GeometryNodeTranslateInstances'); ti.location = (base_x+5300, floor * 300)
            ti.inputs['Translation'].default_value = (0, 0, floor * floor_h)
            tree.links.new(inst.outputs['Instances'], ti.inputs['Instances'])

            rl = tree.nodes.new('GeometryNodeRealizeInstances'); rl.location = (base_x+5600, floor * 300)
            tree.links.new(ti.outputs['Instances'], rl.inputs['Geometry'])
            parts.append(rl.outputs['Geometry'])
        PROPS.ogee_width, PROPS.ogee_height, PROPS.ogee_finial = saved

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+6000, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    # ----------------------------------------------------------------------
    # RADIAL BUILDING - round palazzo (arches around a center axis)
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_curved_building")
    return tree, gin, gout

register_builder(
    "MEL_curved_building", build_curved_building_group,
    "Curved Building", "Building generator (absorbed from monolith build_curved_building).",
    category="structures")


def build_radial_building_group(group_name="MEL_radial_building"):
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
        """Round palazzo - N arches arrayed around a circle of given radius, optional crowning dome."""
        R = PROPS.radial_building_radius
        floors = PROPS.radial_building_floors
        n = PROPS.radial_building_arches
        floor_h = PROPS.wall_height
        parts = []

        # Sample points on a circle
        circ = tree.nodes.new('GeometryNodeCurvePrimitiveCircle'); circ.location = (base_x, 0); color_node(circ, "level")
        circ.mode = 'RADIUS'
        circ.inputs['Resolution'].default_value = n
        circ.inputs['Radius'].default_value = R

        c2p = tree.nodes.new('GeometryNodeCurveToPoints'); c2p.location = (base_x+250, 0); color_node(c2p, "level")
        c2p.mode = 'EVALUATED'
        tree.links.new(circ.outputs['Curve'], c2p.inputs['Curve'])

        saved = (PROPS.ogee_width, PROPS.ogee_height, PROPS.ogee_finial)
        arch_w = (math.tau * R / n) * 0.85
        for floor in range(floors):
            PROPS.ogee_width = arch_w
            PROPS.ogee_height = floor_h * 0.85
            PROPS.ogee_finial = 0.0
            arch_geom = _impl_build_ogee_arch(tree, PROPS, base_x=base_x + 1500 + floor * 4500)

            inst = tree.nodes.new('GeometryNodeInstanceOnPoints'); inst.location = (base_x+5000, floor * 300); color_node(inst, "level")
            tree.links.new(c2p.outputs['Points'], inst.inputs['Points'])
            tree.links.new(arch_geom, inst.inputs['Instance'])
            tree.links.new(c2p.outputs['Rotation'], inst.inputs['Rotation'])

            ti = tree.nodes.new('GeometryNodeTranslateInstances'); ti.location = (base_x+5300, floor * 300)
            ti.inputs['Translation'].default_value = (0, 0, floor * floor_h)
            tree.links.new(inst.outputs['Instances'], ti.inputs['Instances'])

            rl = tree.nodes.new('GeometryNodeRealizeInstances'); rl.location = (base_x+5600, floor * 300)
            tree.links.new(ti.outputs['Instances'], rl.inputs['Geometry'])
            parts.append(rl.outputs['Geometry'])
        PROPS.ogee_width, PROPS.ogee_height, PROPS.ogee_finial = saved

        # Crowning dome on top
        if PROPS.radial_building_dome:
            saved_d = (PROPS.dome_radius, PROPS.dome_spire)
            PROPS.dome_radius = R + 0.2
            PROPS.dome_spire = 0.5
            dome_geom = _impl_build_dome(tree, PROPS, base_x=base_x + 8000)
            PROPS.dome_radius, PROPS.dome_spire = saved_d
            dt = tree.nodes.new('GeometryNodeTransform'); dt.location = (base_x+11000, 600); color_node(dt, "level")
            dt.inputs['Translation'].default_value = (0, 0, floors * floor_h)
            tree.links.new(dome_geom, dt.inputs['Geometry'])
            parts.append(dt.outputs['Geometry'])

        join = tree.nodes.new('GeometryNodeJoinGeometry'); join.location = (base_x+12000, 0); color_node(join, "output")
        for p in parts: tree.links.new(p, join.inputs['Geometry'])
        return join.outputs['Geometry']


    # ----------------------------------------------------------------------
    # TOPOLOGY CLEANUP - game-engine friendly final pass
    # Adds: Merge by Distance + Recalc Normals + Smooth-by-Angle (Blender 5.0+ approach)
    # ----------------------------------------------------------------------

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_radial_building")
    return tree, gin, gout

register_builder(
    "MEL_radial_building", build_radial_building_group,
    "Radial Building", "Building generator (absorbed from monolith build_radial_building).",
    category="structures")


def build_auto_building_group(group_name="MEL_auto_building"):
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
        Full parametric building with floors, window grid, rooftop,
        balconies, and style-specific facade details.
        """
        x = -200
        W  = PROPS.bld_width
        D  = PROPS.bld_depth_b
        Fh = PROPS.bld_floor_height_b
        Fc = PROPS.bld_floor_count_b
        H  = Fh * Fc
        style = PROPS.bld_style
        wc = PROPS.bld_win_cols
        wr = max(1, PROPS.bld_win_rows)
        ww = PROPS.bld_win_w
        wh = PROPS.bld_win_h

        pieces_b = []

        def box(loc, sx, sy, sz, lbl="tower"):
            b = _node(tree, 'GeometryNodeMeshCube', (x+loc[0], loc[1]))
            b.inputs['Size'].default_value = (sx, sy, sz)
            t = _node(tree, 'GeometryNodeTransform', (x+loc[0]+250, loc[1]))
            t.inputs['Translation'].default_value = (0, 0, sz * 0.5)
            _link(tree, b.outputs['Mesh'], t.inputs['Geometry'])
            color_node(b, lbl); color_node(t, lbl)
            pieces_b.append(t.outputs['Geometry'])
            return t

        def window_array(base_z, floor_h, floor_idx, lbl="ornament"):
            """Array a single window shape across the facade for one floor."""
            win = _node(tree, 'GeometryNodeMeshCube',
                        (x+1000, -400 - floor_idx * 200))
            win.inputs['Size'].default_value = (ww * 0.9, D * 0.06, wh)
            color_node(win, "ornament")

            line_w = _node(tree, 'GeometryNodeMeshLine',
                           (x+1000, -600 - floor_idx * 200))
            line_w.mode = 'OFFSET'
            line_w.inputs['Count'].default_value = wc
            spacing = W / max(1, wc)
            line_w.inputs['Offset'].default_value = (spacing, 0, 0)
            line_w.inputs['Start Location'].default_value = (
                -W * 0.5 + spacing * 0.5, D * 0.5 + 0.01,
                base_z + floor_h * 0.5 + Fh * 0.05)

            inst_w = _safe_node(tree, 'GeometryNodeInstanceOnPoints',
                                 (x+1300, -500 - floor_idx * 200))
            if inst_w:
                _link(tree, line_w.outputs['Mesh'], inst_w.inputs['Points'])
                _link(tree, win.outputs['Mesh'],    inst_w.inputs['Instance'])
            real_w = _safe_node(tree, 'GeometryNodeRealizeInstances',
                                 (x+1550, -500 - floor_idx * 200))
            if real_w and inst_w:
                _link(tree, inst_w.outputs['Instances'], real_w.inputs['Geometry'])
                pieces_b.append(real_w.outputs['Geometry'])

        # ── Main body ──────────────────────────────────────────────────────
        if style == 'SKYSCRAPER' and PROPS.bld_setbacks and Fc > 10:
            # Stacked setback volumes
            thirds = Fc // 3
            for seg, (fc_seg, shrink) in enumerate(
                    [(thirds, 1.0), (thirds, 0.78), (Fc - 2*thirds, 0.58)]):
                z_bot = seg * thirds * Fh
                w2 = W * shrink; d2 = D * shrink
                b2 = _node(tree, 'GeometryNodeMeshCube', (x, seg * 400))
                b2.inputs['Size'].default_value = (w2, d2, fc_seg * Fh)
                t2 = _node(tree, 'GeometryNodeTransform', (x+250, seg * 400))
                t2.inputs['Translation'].default_value = (0, 0, z_bot + fc_seg * Fh * 0.5)
                _link(tree, b2.outputs['Mesh'], t2.inputs['Geometry'])
                color_node(b2, "tower"); color_node(t2, "tower")
                pieces_b.append(t2.outputs['Geometry'])
        elif style == 'CYBERPUNK':
            # Irregular stacked volumes
            import random as _rnd
            _rnd.seed(PROPS.seed)
            z_cur = 0.0
            for seg in range(min(8, Fc // 2 + 1)):
                fc_seg = max(1, int(Fc * _rnd.uniform(0.1, 0.35)))
                if z_cur >= H: break
                w2 = W * _rnd.uniform(0.5, 1.1)
                d2 = D * _rnd.uniform(0.5, 1.1)
                off_x = _rnd.uniform(-W * 0.15, W * 0.15)
                off_y = _rnd.uniform(-D * 0.15, D * 0.15)
                h_seg = min(fc_seg * Fh, H - z_cur)
                b2 = _node(tree, 'GeometryNodeMeshCube', (x, seg * 500))
                b2.inputs['Size'].default_value = (w2, d2, h_seg)
                t2 = _node(tree, 'GeometryNodeTransform', (x+250, seg * 500))
                t2.inputs['Translation'].default_value = (off_x, off_y, z_cur + h_seg * 0.5)
                _link(tree, b2.outputs['Mesh'], t2.inputs['Geometry'])
                color_node(b2, "tower"); color_node(t2, "tower")
                pieces_b.append(t2.outputs['Geometry'])
                z_cur += h_seg
        else:
            # Simple box
            b_main = _node(tree, 'GeometryNodeMeshCube', (x, 0))
            b_main.inputs['Size'].default_value = (W, D, H)
            t_main = _node(tree, 'GeometryNodeTransform', (x+250, 0))
            t_main.inputs['Translation'].default_value = (0, 0, H * 0.5)
            _link(tree, b_main.outputs['Mesh'], t_main.inputs['Geometry'])
            color_node(b_main, "tower"); color_node(t_main, "tower")
            pieces_b.append(t_main.outputs['Geometry'])

        # ── Window grid ────────────────────────────────────────────────────
        win_start = 1 if PROPS.bld_ground_retail else 0
        for fi in range(win_start, Fc):
            floor_z = fi * Fh
            for row_i in range(wr):
                row_z = floor_z + Fh * 0.15 + row_i * (Fh * 0.7 / max(1, wr))
                window_array(row_z, Fh * 0.7 / max(1, wr), fi * wr + row_i)

        # ── Ground floor retail windows (taller) ──────────────────────────
        if PROPS.bld_ground_retail and style in ('COMMERCIAL', 'CYBERPUNK', 'BRUTALIST'):
            retail_win = _node(tree, 'GeometryNodeMeshCube', (x+1000, -1800))
            retail_win.inputs['Size'].default_value = (W * 0.85 / max(1, wc) * 0.9, D * 0.06, Fh * 0.65)
            retail_line = _node(tree, 'GeometryNodeMeshLine', (x+1000, -2000))
            retail_line.mode = 'OFFSET'
            retail_line.inputs['Count'].default_value = wc
            retail_line.inputs['Offset'].default_value = (W / max(1, wc), 0, 0)
            retail_line.inputs['Start Location'].default_value = (
                -W * 0.5 + W / max(1, wc) * 0.5, D * 0.5 + 0.01, Fh * 0.35)
            ri_inst = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (x+1300, -1900))
            if ri_inst:
                _link(tree, retail_line.outputs['Mesh'], ri_inst.inputs['Points'])
                _link(tree, retail_win.outputs['Mesh'],  ri_inst.inputs['Instance'])
            ri_real = _safe_node(tree, 'GeometryNodeRealizeInstances', (x+1550, -1900))
            if ri_real and ri_inst:
                _link(tree, ri_inst.outputs['Instances'], ri_real.inputs['Geometry'])
                pieces_b.append(ri_real.outputs['Geometry'])

        # ── Balconies ─────────────────────────────────────────────────────
        if PROPS.bld_balconies and Fc > 2:
            bal = _node(tree, 'GeometryNodeMeshCube', (x+1700, -400))
            bal.inputs['Size'].default_value = (W * 0.9, 0.9, 0.12)
            bal_line = _node(tree, 'GeometryNodeMeshLine', (x+1700, -650))
            bal_line.mode = 'OFFSET'
            step = max(1, Fc // 4)
            bal_count = max(1, Fc // step)
            bal_line.inputs['Count'].default_value = bal_count
            bal_line.inputs['Offset'].default_value = (0, 0, Fh * step)
            bal_line.inputs['Start Location'].default_value = (0, D * 0.5 + 0.45, Fh * step * 0.5)
            bi_inst = _safe_node(tree, 'GeometryNodeInstanceOnPoints', (x+2000, -500))
            if bi_inst:
                _link(tree, bal_line.outputs['Mesh'], bi_inst.inputs['Points'])
                _link(tree, bal.outputs['Mesh'],      bi_inst.inputs['Instance'])
            bi_real = _safe_node(tree, 'GeometryNodeRealizeInstances', (x+2250, -500))
            if bi_real and bi_inst:
                _link(tree, bi_inst.outputs['Instances'], bi_real.inputs['Geometry'])
                pieces_b.append(bi_real.outputs['Geometry'])

        # ── Cornices: thin protruding string course at each floor boundary ──
        # Skip for SKYSCRAPER + CYBERPUNK (those don't have classical cornices)
        if style not in ('SKYSCRAPER', 'CYBERPUNK', 'SCIFI_STATION'):
            for fi in range(1, Fc):
                corn = _node(tree, 'GeometryNodeMeshCube', (x+1800, -1100 - fi * 80))
                corn.inputs['Size'].default_value = (W + 0.18, D + 0.18, 0.08)
                corn_t = _node(tree, 'GeometryNodeTransform', (x+2050, -1100 - fi * 80))
                corn_t.inputs['Translation'].default_value = (0, 0, fi * Fh)
                _link(tree, corn.outputs['Mesh'], corn_t.inputs['Geometry'])
                color_node(corn, "ornament"); color_node(corn_t, "ornament")
                pieces_b.append(corn_t.outputs['Geometry'])

        # ── Rooftop ───────────────────────────────────────────────────────
        if PROPS.bld_rooftop:
            if style == 'SKYSCRAPER':
                # Spire
                spr = _node(tree, 'GeometryNodeMeshCone', (x+2200, 400))
                spr.inputs['Vertices'].default_value = 16  # bumped from 8 in v2.31
                spr.inputs['Radius Top'].default_value    = 0.0
                spr.inputs['Radius Bottom'].default_value = W * 0.06
                spr.inputs['Depth'].default_value         = H * 0.08
                spr_t = _node(tree, 'GeometryNodeTransform', (x+2450, 400))
                spr_t.inputs['Translation'].default_value = (0, 0, H + H * 0.04)
                _link(tree, spr.outputs['Mesh'], spr_t.inputs['Geometry'])
                pieces_b.append(spr_t.outputs['Geometry'])
            elif style in ('CYBERPUNK', 'SCIFI_STATION'):
                # AC units + water tower
                for ri2, (ox, oy) in enumerate([(W*0.25, D*0.2), (-W*0.2, -D*0.25), (0, D*0.3)]):
                    ac = _node(tree, 'GeometryNodeMeshCube', (x+2200, 400 + ri2*200))
                    ac.inputs['Size'].default_value = (W * 0.2, D * 0.2, Fh * 0.5)
                    ac_t = _node(tree, 'GeometryNodeTransform', (x+2450, 400 + ri2*200))
                    ac_t.inputs['Translation'].default_value = (ox, oy, H + Fh * 0.25)
                    _link(tree, ac.outputs['Mesh'], ac_t.inputs['Geometry'])
                    pieces_b.append(ac_t.outputs['Geometry'])
            elif style in ('RESIDENTIAL', 'COMMERCIAL', 'GOTHIC_MANOR'):
                # === Proper hipped roof - 4 triangular slopes meeting at a ridge ===
                import math as _m
                rise = Fh * 0.85   # roof apex height
                overhang = 0.4
                # Pitches: two long trapezoidal slopes (front/back) + two triangular (sides)
                # Approximate by 4 transformed cube slabs each rotated outward
                slab_thick = 0.08
                # Long sides (front/back) tilt around the X axis
                for sign in (-1, 1):
                    pitch = _m.atan2(rise, D * 0.5 + overhang)
                    slab_w = W + overhang * 2.0
                    slab_h = _m.hypot(D * 0.5 + overhang, rise)
                    slab = _node(tree, 'GeometryNodeMeshCube', (x+2200, 800 + (sign + 1) * 250))
                    slab.inputs['Size'].default_value = (slab_w, slab_h, slab_thick)
                    slab_t = _node(tree, 'GeometryNodeTransform',
                                   (x+2450, 800 + (sign + 1) * 250))
                    # tilt around X so its Y axis rises up toward the apex
                    slab_t.inputs['Rotation'].default_value = (sign * -pitch, 0, 0)
                    # position: center of the slab is half its length from the eave,
                    # rotated up by pitch
                    cy_slab = sign * (D * 0.5 - (slab_h * 0.5 - overhang) * _m.cos(pitch))
                    cz_slab = H + (slab_h * 0.5 - overhang) * _m.sin(pitch) + slab_thick * 0.5
                    # Simpler/safer: align the bottom edge to the eave line
                    cy_slab = sign * ((D * 0.5 + overhang) - slab_h * 0.5 * _m.cos(pitch))
                    cz_slab = H + slab_h * 0.5 * _m.sin(pitch)
                    slab_t.inputs['Translation'].default_value = (0, cy_slab, cz_slab)
                    _link(tree, slab.outputs['Mesh'], slab_t.inputs['Geometry'])
                    color_node(slab, "house"); color_node(slab_t, "house")
                    pieces_b.append(slab_t.outputs['Geometry'])
                # Gable ends (front/back triangles) - extruded 3-vertex curve
                for sy in (-1, 1):
                    tri_c = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle',
                                        (x+2200, 1500 + (sy + 1) * 100))
                    if tri_c is None: continue
                    tri_c.inputs['Resolution'].default_value = 3
                    tri_c.inputs['Radius'].default_value = rise
                    tri_tr = _node(tree, 'GeometryNodeTransform',
                                    (x+2450, 1500 + (sy + 1) * 100))
                    tri_tr.inputs['Scale'].default_value = (W * 0.5 / max(0.001, rise), 1.0, 1.0)
                    tri_tr.inputs['Rotation'].default_value = (1.5708, 0, 0)
                    tri_tr.inputs['Translation'].default_value = (0, sy * D * 0.5, H + rise * 0.5)
                    _link(tree, tri_c.outputs['Curve'], tri_tr.inputs['Geometry'])
                    gfill = _safe_node(tree, 'GeometryNodeFillCurve',
                                        (x+2700, 1500 + (sy + 1) * 100))
                    if gfill is None: continue
                    try: gfill.mode = 'NGONS'
                    except Exception: pass
                    _link(tree, tri_tr.outputs['Geometry'], gfill.inputs['Curve'])
                    ge = _safe_node(tree, 'GeometryNodeExtrudeMesh',
                                    (x+2950, 1500 + (sy + 1) * 100))
                    if ge:
                        ge.mode = 'FACES'
                        ge.inputs['Offset Scale'].default_value = slab_thick
                        _link(tree, gfill.outputs['Mesh'], ge.inputs['Mesh'])
                        color_node(ge, "house")
                        pieces_b.append(ge.outputs['Mesh'])
            else:
                # Parapet wall around roof (BRUTALIST / WAREHOUSE)
                for side, (ox, oy, rx, ry) in enumerate([
                        (0, D*0.5 + 0.15, W, 0.3),
                        (0, -D*0.5 - 0.15, W, 0.3),
                        (W*0.5 + 0.15, 0, 0.3, D),
                        (-W*0.5 - 0.15, 0, 0.3, D)]):
                    par = _node(tree, 'GeometryNodeMeshCube', (x+2200+side*300, 400))
                    par.inputs['Size'].default_value = (rx, ry, 0.8)
                    par_t = _node(tree, 'GeometryNodeTransform', (x+2450+side*300, 400))
                    par_t.inputs['Translation'].default_value = (ox, oy, H + 0.4)
                    _link(tree, par.outputs['Mesh'], par_t.inputs['Geometry'])
                    pieces_b.append(par_t.outputs['Geometry'])

        # ── Join all (with welding so pieces fuse properly) ────────────────
        return _finalize_building(tree, pieces_b, (x+3200, 0))


    # ======================================================================
    # OPERATORS - Sci-Fi Effect
    # ======================================================================

    class SURREAL_ARCH_OT_scifi_apply(bpy.types.Operator):
        """Apply the selected Sci-Fi effect non-destructively to the active object."""
        bl_idname = "surreal_arch.scifi_apply"
        bl_label  = "* Apply Sci-Fi Effect"
        bl_options = {'REGISTER', 'UNDO'}

        def execute(self, context):
            obj = context.active_object
            if not obj or obj.type != 'MESH':
                self.report({'WARNING'}, "Select a mesh object first.")
                return {'CANCELLED'}
            apply_scifi_effect_gn(obj, obj.surreal_arch_props)
            self.report({'INFO'}, f"Applied {obj.surreal_arch_props.scifi_effect} effect.")
            return {'FINISHED'}


    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_auto_building")
    return tree, gin, gout

register_builder(
    "MEL_auto_building", build_auto_building_group,
    "Auto Building", "Building generator (absorbed from monolith build_auto_building).",
    category="structures")


def build_raycast_facade_group(group_name="MEL_raycast_facade"):
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
        Curtain-wall facade: distribute points on a grid, cast rays outward
        along normals to find the facade surface, instance glass panels at
        hit positions aligned to hit normals.
        """
        x = -200
        in_node = tree.nodes.get("Group Input") or tree.nodes.new('NodeGroupInput')
        in_node.location = (-600, 0)

        # Base curved surface - use cylinder as facade backing
        cyl = _node(tree, 'GeometryNodeMeshCylinder', (x, 200))
        cyl.inputs['Vertices'].default_value    = max(6, PROPS.complexity_level * 6)
        cyl.inputs['Radius'].default_value      = PROPS.base_radius
        cyl.inputs['Depth'].default_value       = PROPS.height
        color_node(cyl, "tower")

        # Grid of sample points
        grid = _node(tree, 'GeometryNodeMeshGrid', (x, -200))
        grid.inputs['Size X'].default_value   = PROPS.base_radius * 2.2
        grid.inputs['Size Y'].default_value   = PROPS.height
        grid.inputs['Vertices X'].default_value = max(3, PROPS.recursion_depth * 2)
        grid.inputs['Vertices Y'].default_value = max(3, PROPS.recursion_depth * 3)
        color_node(grid, "input")

        # Distribute points on the grid
        pts = _node(tree, 'GeometryNodeDistributePointsOnFaces', (x+300, -200))
        pts.distribute_method = 'POISSON'
        pts.inputs['Distance Min'].default_value  = 0.4
        pts.inputs['Density Max'].default_value   = PROPS.complexity_level * 0.8
        pts.inputs['Seed'].default_value          = PROPS.seed
        _link(tree, grid.outputs['Mesh'], pts.inputs['Mesh'])
        color_node(pts, "input")

        # Point position + outward ray direction (along +X / radial)
        pos_node = _node(tree, 'GeometryNodeInputPosition', (x+300, -500))
        nrm_node = _node(tree, 'GeometryNodeInputNormal',   (x+300, -650))

        # Raycast from each point toward the cylinder
        raycast = _node(tree, 'GeometryNodeRaycast', (x+700, -200))
        raycast.data_type      = 'FLOAT_VECTOR'
        # `.mapping` was renamed in newer Blender - set defensively
        try: raycast.mapping = 'INTERPOLATED'
        except (AttributeError, TypeError): pass
        raycast.inputs['Ray Length'].default_value = PROPS.base_radius * 3.0
        _link(tree, cyl.outputs['Mesh'],         raycast.inputs['Target Geometry'])
        _link(tree, pos_node.outputs['Position'],raycast.inputs['Source Position'])
        _link(tree, nrm_node.outputs['Normal'],  raycast.inputs['Ray Direction'])
        color_node(raycast, "deform")

        # Set point positions to hit locations
        set_pos = _node(tree, 'GeometryNodeSetPosition', (x+1100, -200))
        _link(tree, pts.outputs['Points'],             set_pos.inputs['Geometry'])
        _link(tree, raycast.outputs['Hit Position'],   set_pos.inputs['Position'])
        color_node(set_pos, "deform")

        # Instance glass panel on each point aligned to hit normal
        panel_src = _node(tree, 'GeometryNodeMeshCube', (x+900, 300))
        panel_src.inputs['Size'].default_value = (0.6 * (1.0 / max(1, PROPS.recursion_depth)), 0.02, 0.8 * (1.0 / max(1, PROPS.recursion_depth)))
        color_node(panel_src, "ornament")

        inst = _node(tree, 'GeometryNodeInstanceOnPoints', (x+1400, -200))
        _link(tree, set_pos.outputs['Geometry'],        inst.inputs['Points'])
        _link(tree, panel_src.outputs['Mesh'],          inst.inputs['Instance'])
        _link(tree, raycast.outputs['Hit Normal'],      inst.inputs['Rotation'])
        color_node(inst, "ornament")

        realize = _node(tree, 'GeometryNodeRealizeInstances', (x+1700, -200))
        _link(tree, inst.outputs['Instances'], realize.inputs['Geometry'])

        # Join facade surface + panels
        join = _node(tree, 'GeometryNodeJoinGeometry', (x+2000, 0))
        _link(tree, cyl.outputs['Mesh'],    join.inputs['Geometry'])
        _link(tree, realize.outputs['Geometry'], join.inputs['Geometry'])
        color_node(join, "output")

        return join.outputs['Geometry']


    # ──────────────────────────────────────────────────────────────────────
    # ADVANCED BUILDER: VOLUME CLOUD PALACE
    # Converts a subdivided mesh to volume, then back - producing puffy
    # volumetric-style architecture. Uses Mesh->Volume->Mesh pipeline.
    # ──────────────────────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_raycast_facade")
    return tree, gin, gout

register_builder(
    "MEL_raycast_facade", build_raycast_facade_group,
    "Raycast Facade", "Building generator (absorbed from monolith build_raycast_facade).",
    category="structures")


# 5 builders registered
