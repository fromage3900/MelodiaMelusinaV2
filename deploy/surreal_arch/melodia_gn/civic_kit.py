"""MEL civic/village builders — absorbed from the monolith (P2 family 4).

19 generator builders. Params-as-values port (PROPS namespace from monolith
bpy.props defaults). Regenerable.
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



def _finalize_building(tree, pieces, loc=(0, 0), label="output"):
    """Heavier weld for monolithic buildings - fuses touching tops/finials
    to their bodies (weld=0.3). Use as the last step of a building builder."""
    return _join_all(tree, pieces, loc=loc, label=label, weld=0.3)




BUILDER_PARAM_DEFAULTS = {
    "base_radius": {"type": "FloatProperty", "default": 1.2, "min": 0.1, "max": 10.0},
    "bridge_arches": {"type": "IntProperty", "default": 3, "min": 1, "max": 12},
    "bridge_height": {"type": "FloatProperty", "default": 2.0, "min": 0.5, "max": 10.0},
    "bridge_length": {"type": "FloatProperty", "default": 8.0, "min": 2.0, "max": 40.0},
    "bridge_walkway": {"type": "BoolProperty", "default": True, "min": None, "max": None},
    "building_floors": {"type": "IntProperty", "default": 3, "min": 1, "max": 12},
    "fountain_tiers": {"type": "IntProperty", "default": 3, "min": 1, "max": 6},
    "height": {"type": "FloatProperty", "default": 5.0, "min": 0.5, "max": 30.0},
    "recursion_depth": {"type": "IntProperty", "default": 3, "min": 1, "max": 6},
    "stair_step_count": {"type": "IntProperty", "default": 12, "min": 2, "max": 80},
}


def build_stone_bridge_group(group_name="MEL_stone_bridge"):
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
        """Multi-arch stone bridge with railings."""
        n = max(1, getattr(PROPS, 'bridge_arches', 3))
        span = max(2.0, getattr(PROPS, 'bridge_length', 6.0)) * 1.2
        height = max(1.0, getattr(PROPS, 'bridge_height', 2.0))
        width = max(1.0, getattr(PROPS, 'bridge_walkway', 1.6))
        arch_w = span / n
        pieces = []
        # Deck slab
        deck = _node(tree, 'GeometryNodeMeshCube', (base_x, 200))
        deck.inputs['Size'].default_value = (width, span, 0.25)
        pieces.append(_move(tree, deck.outputs['Mesh'], (base_x + 200, 200),
                            translation=(0, 0, height + 0.13), label="house"))
        color_node(deck, "house")
        # Arches (bezier per arch) + piers
        prof = _cv_circle(tree, (base_x, -3000), width * 0.42, 16)
        for i in range(n):
            y_center = -span / 2 + arch_w * (i + 0.5)
            # Arch curve = quadratic bezier
            ab = _safe_node(tree, 'GeometryNodeCurveQuadraticBezier',
                            (base_x, -200 - i * 200))
            if ab:
                try:
                    ab.inputs['Resolution'].default_value = 24
                    ab.inputs['Start'].default_value  = (0, y_center - arch_w / 2, 0)
                    ab.inputs['Middle'].default_value = (0, y_center, height * 1.1)
                    ab.inputs['End'].default_value    = (0, y_center + arch_w / 2, 0)
                except Exception:
                    pass
                sw = _safe_node(tree, 'GeometryNodeCurveToMesh',
                                (base_x + 220, -200 - i * 200))
                if sw and prof:
                    _link(tree, ab.outputs['Curve'], sw.inputs['Curve'])
                    _link(tree, prof.outputs['Curve'], sw.inputs['Profile Curve'])
                    color_node(sw, "tower")
                    pieces.append(sw.outputs['Mesh'])
            # Pier between arches (rectangular pillar dropping down from deck)
            if i < n - 1:
                pier = _node(tree, 'GeometryNodeMeshCube',
                             (base_x, -1500 - i * 100))
                pier.inputs['Size'].default_value = (width * 0.7, arch_w * 0.18, height * 1.05)
                pieces.append(_move(tree, pier.outputs['Mesh'],
                                    (base_x + 220, -1500 - i * 100),
                                    translation=(0, y_center + arch_w / 2,
                                                 height * 0.525), label="tower"))
                color_node(pier, "tower")
        # Railings (curve-swept)
        rail_prof = _cv_circle(tree, (base_x, -3300), 0.07, 8)
        for sx in (-1, 1):
            rail = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine',
                              (base_x, -2400 - (sx + 1) * 100))
            if rail:
                try:
                    rail.inputs['Start'].default_value = (sx * width / 2, -span / 2,
                                                           height + 0.35)
                    rail.inputs['End'].default_value   = (sx * width / 2,  span / 2,
                                                           height + 0.35)
                except Exception:
                    pass
                sw = _safe_node(tree, 'GeometryNodeCurveToMesh',
                                (base_x + 220, -2400 - (sx + 1) * 100))
                if sw and rail_prof:
                    _link(tree, rail.outputs['Curve'], sw.inputs['Curve'])
                    _link(tree, rail_prof.outputs['Curve'], sw.inputs['Profile Curve'])
                    color_node(sw, "ornament")
                    pieces.append(sw.outputs['Mesh'])
        return _finalize_building(tree, pieces, (base_x + 1400, 0))


    # ─── WINDMILL ───────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_stone_bridge")
    return tree, gin, gout

register_builder(
    "MEL_stone_bridge", build_stone_bridge_group,
    "Stone Bridge", "Civic builder (absorbed from monolith build_stone_bridge).",
    category="civic")


def build_windmill_group(group_name="MEL_windmill"):
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
        """Tower windmill: cylindrical body + cap + 4 rotating blades."""
        r = max(0.7, getattr(PROPS, 'base_radius', 1.0)) * 1.0
        h = max(3.5, getattr(PROPS, 'height', 5.0)) * 1.6
        pieces = []
        # Tower (tapered top via 2 stacked cylinders)
        body_c1 = _cv_circle(tree, (base_x, 200), r, 16)
        body1 = _fill_extrude(tree, body_c1.outputs['Curve'] if body_c1 else None,
                              (base_x + 200, 200), (base_x + 400, 200),
                              h * 0.65, "tower")
        pieces.append(body1)
        body_c2 = _cv_circle(tree, (base_x, -200), r * 0.78, 16)
        body2 = _fill_extrude(tree, body_c2.outputs['Curve'] if body_c2 else None,
                              (base_x + 200, -200), (base_x + 400, -200),
                              h * 0.35, "tower")
        pieces.append(_move(tree, body2, (base_x + 600, -200),
                            translation=(0, 0, h * 0.65), label="tower"))
        # Cap (smaller dome)
        cap = _safe_node(tree, 'GeometryNodeMeshUVSphere', (base_x, -600))
        if cap:
            cap.inputs['Radius'].default_value = r * 0.85
            cap.inputs['Segments'].default_value = 16
            cap.inputs['Rings'].default_value    = 12
            pieces.append(_move(tree, cap.outputs['Mesh'], (base_x + 200, -600),
                                translation=(0, 0, h), scale=(1, 1, 0.6),
                                label="house"))
            color_node(cap, "house")
        # 4 blades: sweep beams radially
        blade_len = r * 3.0
        blade_w = r * 0.6
        import math
        for i in range(4):
            ang = (i / 4) * math.tau
            blade = _node(tree, 'GeometryNodeMeshCube', (base_x, -1200 - i * 100))
            blade.inputs['Size'].default_value = (blade_w, 0.06, blade_len)
            # Position outward from cap front; rotated around Y for sail tilt
            bx = math.sin(ang) * (blade_len / 2 + r * 0.2)
            bz = math.cos(ang) * (blade_len / 2 + r * 0.2) + h
            pieces.append(_move(tree, blade.outputs['Mesh'],
                                (base_x + 220, -1200 - i * 100),
                                translation=(bx, -r * 0.95, bz),
                                rotation=(0, ang, 0), label="ornament"))
            color_node(blade, "ornament")
        # Tiny door at base
        door = _node(tree, 'GeometryNodeMeshCube', (base_x, -2000))
        door.inputs['Size'].default_value = (0.5, 0.05, 1.0)
        pieces.append(_move(tree, door.outputs['Mesh'], (base_x + 200, -2000),
                            translation=(0, -r, 0.5), label="ornament"))
        color_node(door, "ornament")
        return _finalize_building(tree, pieces, (base_x + 1200, 0))


    # ─── CHAPEL ─────────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_windmill")
    return tree, gin, gout

register_builder(
    "MEL_windmill", build_windmill_group,
    "Windmill", "Civic builder (absorbed from monolith build_windmill).",
    category="civic")


def build_chapel_group(group_name="MEL_chapel"):
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
        """Small chapel: nave + apse + single bell tower at front."""
        W = max(2.0, getattr(PROPS, 'base_radius', 1.0) * 2.4)
        L = W * 2.0
        H = max(2.5, getattr(PROPS, 'height', 4.0)) * 1.0
        pieces = []
        # Nave body
        nave = _node(tree, 'GeometryNodeMeshCube', (base_x, 200))
        nave.inputs['Size'].default_value = (W, L, H)
        pieces.append(_move(tree, nave.outputs['Mesh'], (base_x + 200, 200),
                            translation=(0, 0, H / 2), label="tower"))
        color_node(nave, "tower")
        # Gabled roof - two slanted slabs
        import math
        pitch = math.atan2(H * 0.5, W * 0.5)
        for sx in (-1, 1):
            slab = _node(tree, 'GeometryNodeMeshCube', (base_x, -200 + (sx + 1) * 100))
            slab.inputs['Size'].default_value = (W * 0.55 / math.cos(pitch), L + 0.3, 0.1)
            # Tilt around Y so X-axis rises
            pieces.append(_move(tree, slab.outputs['Mesh'],
                                (base_x + 220, -200 + (sx + 1) * 100),
                                translation=(sx * W * 0.25, 0, H + H * 0.25),
                                rotation=(0, sx * -pitch, 0), label="house"))
            color_node(slab, "house")
        # Apse (semi-cylindrical end via extruded half-circle)
        apse_c = _cv_circle(tree, (base_x, -800), W * 0.4, 16)
        apse = _fill_extrude(tree, apse_c.outputs['Curve'] if apse_c else None,
                             (base_x + 200, -800), (base_x + 400, -800),
                             H * 0.95, "tower")
        pieces.append(_move(tree, apse, (base_x + 600, -800),
                            translation=(0, L / 2 + 0.05, 0),
                            scale=(1, 0.6, 1), label="tower"))
        # Bell tower at front
        tower_r = W * 0.22
        tower_h = H * 1.8
        tc = _cv_circle(tree, (base_x, -1400), tower_r, 16)
        tm = _fill_extrude(tree, tc.outputs['Curve'] if tc else None,
                           (base_x + 200, -1400), (base_x + 400, -1400),
                           tower_h, "tower")
        pieces.append(_move(tree, tm, (base_x + 600, -1400),
                            translation=(0, -L / 2 - tower_r * 0.5, 0),
                            label="tower"))
        # Tower roof (cone)
        tcap = _safe_node(tree, 'GeometryNodeMeshCone', (base_x, -1800))
        if tcap:
            tcap.inputs['Radius Bottom'].default_value = tower_r * 1.1
            tcap.inputs['Radius Top'].default_value = 0
            tcap.inputs['Depth'].default_value = tower_r * 2.4
            tcap.inputs['Vertices'].default_value = 32  # bumped from 16 in v2.31 for smoother shading
            pieces.append(_move(tree, tcap.outputs['Mesh'], (base_x + 200, -1800),
                                translation=(0, -L / 2 - tower_r * 0.5,
                                              tower_h + tower_r * 1.2),
                                label="house"))
            color_node(tcap, "house")
        # Arched front door
        door_arch = _safe_node(tree, 'GeometryNodeCurveQuadraticBezier',
                               (base_x, -2300))
        if door_arch:
            try:
                door_arch.inputs['Resolution'].default_value = 24
                door_arch.inputs['Start'].default_value  = (-0.4, 0, 0)
                door_arch.inputs['Middle'].default_value = (0, 0, 1.4)
                door_arch.inputs['End'].default_value    = (0.4, 0, 0)
            except Exception:
                pass
            prof = _cv_circle(tree, (base_x, -2500), 0.06, 8)
            sw = _safe_node(tree, 'GeometryNodeCurveToMesh',
                            (base_x + 250, -2300))
            if sw and prof:
                _link(tree, door_arch.outputs['Curve'], sw.inputs['Curve'])
                _link(tree, prof.outputs['Curve'], sw.inputs['Profile Curve'])
                color_node(sw, "ornament")
                pieces.append(_move(tree, sw.outputs['Mesh'], (base_x + 500, -2300),
                                    translation=(0, -L / 2 - 0.05, 0),
                                    label="ornament"))
        return _finalize_building(tree, pieces, (base_x + 1300, 0))


    # ─── VILLAGE WELL ───────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_chapel")
    return tree, gin, gout

register_builder(
    "MEL_chapel", build_chapel_group,
    "Chapel", "Civic builder (absorbed from monolith build_chapel).",
    category="civic")


def build_village_well_group(group_name="MEL_village_well"):
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
        """Stone village well: cylindrical wall + crossbar with bucket + roof."""
        r = max(0.4, getattr(PROPS, 'base_radius', 1.0)) * 0.7
        pieces = []
        # Well ring (subdivided torus or extruded circle annulus)
        ring_outer = _cv_circle(tree, (base_x, 200), r * 1.15, 24)
        ring_inner = _cv_circle(tree, (base_x, 0), r * 0.85, 24)
        # Easier: an extruded thick ring built by 2 set positions
        # Use a fill-extrude of outer circle, subtract conceptually - for now,
        # build as a single extruded annulus via Mesh Boolean: skip, use torus
        well = _safe_node(tree, 'GeometryNodeMeshTorus', (base_x, 200))
        if well:
            try:
                well.inputs['Major Radius'].default_value = r
                well.inputs['Minor Radius'].default_value = r * 0.18
                well.inputs['Major Segments'].default_value = 24
                well.inputs['Minor Segments'].default_value = 6
            except Exception:
                pass
            pieces.append(_move(tree, well.outputs['Mesh'], (base_x + 200, 200),
                                translation=(0, 0, r * 0.4),
                                scale=(1, 1, 1.4), label="tower"))
            color_node(well, "tower")
        # 2 vertical posts + horizontal crossbar
        for sx in (-1, 1):
            post = _node(tree, 'GeometryNodeMeshCylinder', (base_x, -300 - (sx + 1) * 100))
            post.inputs['Radius'].default_value = 0.06
            post.inputs['Depth'].default_value  = r * 2.5
            post.inputs['Vertices'].default_value = 12
            pieces.append(_move(tree, post.outputs['Mesh'],
                                (base_x + 220, -300 - (sx + 1) * 100),
                                translation=(sx * r * 1.2, 0, r * 1.85),
                                label="ornament"))
            color_node(post, "ornament")
        crossbar = _node(tree, 'GeometryNodeMeshCylinder', (base_x, -800))
        crossbar.inputs['Radius'].default_value = 0.06
        crossbar.inputs['Depth'].default_value = r * 2.6
        crossbar.inputs['Vertices'].default_value = 12
        pieces.append(_move(tree, crossbar.outputs['Mesh'], (base_x + 200, -800),
                            translation=(0, 0, r * 3.0),
                            rotation=(0, 1.5708, 0), label="ornament"))
        color_node(crossbar, "ornament")
        # Bucket (small cylinder hanging from rope)
        bucket = _node(tree, 'GeometryNodeMeshCylinder', (base_x, -1200))
        bucket.inputs['Radius'].default_value = r * 0.22
        bucket.inputs['Depth'].default_value = r * 0.35
        bucket.inputs['Vertices'].default_value = 12
        pieces.append(_move(tree, bucket.outputs['Mesh'], (base_x + 200, -1200),
                            translation=(0, 0, r * 1.5),
                            label="ornament"))
        color_node(bucket, "ornament")
        # Pitched roof on posts (2 slanted slabs)
        import math
        for sx in (-1, 1):
            slab = _node(tree, 'GeometryNodeMeshCube', (base_x, -1700 + (sx + 1) * 80))
            slab.inputs['Size'].default_value = (r * 1.0, r * 2.8, 0.05)
            pitch = math.atan2(r * 0.6, r * 0.5)
            pieces.append(_move(tree, slab.outputs['Mesh'],
                                (base_x + 220, -1700 + (sx + 1) * 80),
                                translation=(sx * r * 0.3, 0, r * 3.5),
                                rotation=(0, sx * -pitch, 0), label="house"))
            color_node(slab, "house")
        return _finalize_building(tree, pieces, (base_x + 1100, 0))


    # ─── MARKET STALL ───────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_village_well")
    return tree, gin, gout

register_builder(
    "MEL_village_well", build_village_well_group,
    "Village Well", "Civic builder (absorbed from monolith build_village_well).",
    category="civic")


def build_market_stall_group(group_name="MEL_market_stall"):
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
        """Merchant stall with awning + counter + hanging sign."""
        W = max(1.0, getattr(PROPS, 'base_radius', 1.0) * 1.6)
        D = W * 0.6
        H = max(2.0, getattr(PROPS, 'height', 3.0)) * 0.9
        pieces = []
        # Counter - extruded rectangle
        counter = _node(tree, 'GeometryNodeMeshCube', (base_x, 200))
        counter.inputs['Size'].default_value = (W, D, H * 0.4)
        pieces.append(_move(tree, counter.outputs['Mesh'], (base_x + 200, 200),
                            translation=(0, 0, H * 0.2), label="tower"))
        color_node(counter, "tower")
        # 4 corner posts
        for sx in (-1, 1):
            for sy in (-1, 1):
                post = _node(tree, 'GeometryNodeMeshCylinder',
                             (base_x, -300 - (sx + 1) * 80 - (sy + 1) * 40))
                post.inputs['Radius'].default_value = 0.05
                post.inputs['Depth'].default_value = H
                post.inputs['Vertices'].default_value = 8
                pieces.append(_move(tree, post.outputs['Mesh'],
                                    (base_x + 220, -300 - (sx + 1) * 80 - (sy + 1) * 40),
                                    translation=(sx * W / 2, sy * D / 2, H / 2),
                                    label="ornament"))
                color_node(post, "ornament")
        # Awning (single slanted slab)
        import math
        pitch = 0.25
        awning = _node(tree, 'GeometryNodeMeshCube', (base_x, -1200))
        awning.inputs['Size'].default_value = (W * 1.2, D * 1.3, 0.06)
        pieces.append(_move(tree, awning.outputs['Mesh'], (base_x + 200, -1200),
                            translation=(0, 0, H + 0.05),
                            rotation=(pitch, 0, 0), label="house"))
        color_node(awning, "house")
        # Hanging sign (thin board on a rope)
        sign = _node(tree, 'GeometryNodeMeshCube', (base_x, -1700))
        sign.inputs['Size'].default_value = (W * 0.4, 0.04, 0.25)
        pieces.append(_move(tree, sign.outputs['Mesh'], (base_x + 200, -1700),
                            translation=(0, -D / 2 - 0.05, H * 0.85),
                            label="ornament"))
        color_node(sign, "ornament")
        # Rope to sign (thin cylinder)
        rope = _node(tree, 'GeometryNodeMeshCylinder', (base_x, -2100))
        rope.inputs['Radius'].default_value = 0.012
        rope.inputs['Depth'].default_value = 0.15
        rope.inputs['Vertices'].default_value = 6
        pieces.append(_move(tree, rope.outputs['Mesh'], (base_x + 200, -2100),
                            translation=(0, -D / 2 - 0.05, H * 0.97),
                            label="ornament"))
        color_node(rope, "ornament")
        return _finalize_building(tree, pieces, (base_x + 1100, 0))


    # ─── OBELISK ────────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_market_stall")
    return tree, gin, gout

register_builder(
    "MEL_market_stall", build_market_stall_group,
    "Market Stall", "Civic builder (absorbed from monolith build_market_stall).",
    category="civic")


def build_obelisk_group(group_name="MEL_obelisk"):
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
        """Tall narrow obelisk: 4-sided tapered shaft + pyramidion top + plinth."""
        base = max(0.5, getattr(PROPS, 'base_radius', 1.0)) * 0.7
        h = max(3.0, getattr(PROPS, 'height', 5.0)) * 2.0
        top = base * 0.45
        pieces = []
        # Plinth (square block at base)
        plinth = _node(tree, 'GeometryNodeMeshCube', (base_x, 200))
        plinth.inputs['Size'].default_value = (base * 1.8, base * 1.8, base * 0.8)
        pieces.append(_move(tree, plinth.outputs['Mesh'], (base_x + 200, 200),
                            translation=(0, 0, base * 0.4), label="house"))
        color_node(plinth, "house")
        # Shaft - tapered: 8 verts at base + 8 at top, joined as a frustum
        # Build via 2 stacked rectangles using bmesh-equivalent: easiest is
        # a cube transformed with Set Position via Spline Parameter on a line,
        # but simplest is two Mesh Cubes scaled + a custom connecting via
        # GeometryNodeFillCurve on a profile that varies. We'll approximate by
        # extruding a square curve with `Taper Curve`.
        sq = _cv_circle(tree, (base_x, -400), base, 4)   # 4-vert "circle" = square
        if sq:
            # Set rotation 45deg so square edges are axis-aligned
            sq_rot = _move(tree, sq.outputs['Curve'], (base_x + 200, -400),
                           rotation=(0, 0, 0.7854), label="tower")
            # Fill the square
            sf = _safe_node(tree, 'GeometryNodeFillCurve', (base_x + 400, -400))
            if sf:
                try:
                    sf.mode = 'NGONS'
                except Exception:
                    pass
                _link(tree, sq_rot, sf.inputs['Curve'])
                # Extrude upward
                sx = _safe_node(tree, 'GeometryNodeExtrudeMesh',
                                (base_x + 600, -400))
                if sx:
                    sx.mode = 'FACES'
                    sx.inputs['Offset Scale'].default_value = h
                    _link(tree, sf.outputs['Mesh'], sx.inputs['Mesh'])
                    # Now scale TOP face only - approximate taper by scaling
                    # whole mesh with a Z-dependent factor via Set Position
                    pos = _node(tree, 'GeometryNodeInputPosition',
                                (base_x + 600, -700))
                    sep = _node(tree, 'ShaderNodeSeparateXYZ',
                                (base_x + 800, -700))
                    _link(tree, pos.outputs['Position'], sep.inputs['Vector'])
                    # taper = lerp(1.0, top/base, z/h)
                    norm_z = _node(tree, 'ShaderNodeMath', (base_x + 1000, -700))
                    norm_z.operation = 'DIVIDE'
                    _link(tree, sep.outputs['Z'], norm_z.inputs[0])
                    norm_z.inputs[1].default_value = h
                    taper = _node(tree, 'ShaderNodeMath', (base_x + 1200, -700))
                    taper.operation = 'MULTIPLY_ADD'
                    _link(tree, norm_z.outputs['Value'], taper.inputs[0])
                    taper.inputs[1].default_value = (top / base) - 1.0
                    taper.inputs[2].default_value = 1.0
                    # Scale X,Y by taper
                    scl_x = _node(tree, 'ShaderNodeMath', (base_x + 1400, -700))
                    scl_x.operation = 'MULTIPLY'
                    _link(tree, sep.outputs['X'], scl_x.inputs[0])
                    _link(tree, taper.outputs['Value'], scl_x.inputs[1])
                    scl_y = _node(tree, 'ShaderNodeMath', (base_x + 1400, -900))
                    scl_y.operation = 'MULTIPLY'
                    _link(tree, sep.outputs['Y'], scl_y.inputs[0])
                    _link(tree, taper.outputs['Value'], scl_y.inputs[1])
                    # Subtract original X/Y to get offset
                    ox = _node(tree, 'ShaderNodeMath', (base_x + 1600, -700))
                    ox.operation = 'SUBTRACT'
                    _link(tree, scl_x.outputs['Value'], ox.inputs[0])
                    _link(tree, sep.outputs['X'], ox.inputs[1])
                    oy = _node(tree, 'ShaderNodeMath', (base_x + 1600, -900))
                    oy.operation = 'SUBTRACT'
                    _link(tree, scl_y.outputs['Value'], oy.inputs[0])
                    _link(tree, sep.outputs['Y'], oy.inputs[1])
                    ovec = _node(tree, 'ShaderNodeCombineXYZ',
                                 (base_x + 1800, -800))
                    _link(tree, ox.outputs['Value'], ovec.inputs['X'])
                    _link(tree, oy.outputs['Value'], ovec.inputs['Y'])
                    sp = _safe_node(tree, 'GeometryNodeSetPosition',
                                    (base_x + 2000, -400))
                    if sp:
                        _link(tree, sx.outputs['Mesh'], sp.inputs['Geometry'])
                        _link(tree, ovec.outputs['Vector'], sp.inputs['Offset'])
                        pieces.append(_move(tree, sp.outputs['Geometry'],
                                            (base_x + 2200, -400),
                                            translation=(0, 0, base * 0.8),
                                            label="tower"))
        # Pyramidion (cone at top)
        pyr = _safe_node(tree, 'GeometryNodeMeshCone', (base_x, -2200))
        if pyr:
            pyr.inputs['Radius Bottom'].default_value = top * 1.05
            pyr.inputs['Radius Top'].default_value = 0
            pyr.inputs['Depth'].default_value = top * 2.4
            pyr.inputs['Vertices'].default_value = 24
            pieces.append(_move(tree, pyr.outputs['Mesh'], (base_x + 200, -2200),
                                translation=(0, 0, base * 0.8 + h + top * 1.2),
                                rotation=(0, 0, 0.7854), label="house"))
            color_node(pyr, "house")
        return _finalize_building(tree, pieces, (base_x + 2500, 0))


    # ======================================================================
    # * TOWN / CIVIC / ASIAN PIECE LIBRARY (v2.24) - Layer 1 additions
    # ======================================================================
    # All use the vector Size socket on MeshCube (Blender 5.1 API).
    # Geometry composed from curve-fill-extrude and curve sweeps where possible.

    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_obelisk")
    return tree, gin, gout

register_builder(
    "MEL_obelisk", build_obelisk_group,
    "Obelisk", "Civic builder (absorbed from monolith build_obelisk).",
    category="civic")


def build_town_house_group(group_name="MEL_town_house"):
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
        """Multi-story Tudor town house - stone base, jettied upper floor, gable roof."""
        W = max(2.0, getattr(PROPS, 'base_radius', 1.0) * 2.4)
        D = W * 0.7
        floor_h = max(1.5, getattr(PROPS, 'height', 4.0) * 0.45)
        floors = max(2, getattr(PROPS, 'building_floors', 3))
        pieces = []
        # Floor stack with jetty (upper floors overhang by +5%)
        for fi in range(floors):
            ww = W * (1.0 + fi * 0.06)   # progressively wider above (jetty)
            dd = D * (1.0 + fi * 0.06)
            zb = fi * floor_h
            pieces.append(_move(tree,
                                 _cube(tree, (base_x, 200 - fi * 200), ww, dd, floor_h,
                                       "house"),
                                 (base_x + 200, 200 - fi * 200),
                                 translation=(0, 0, zb + floor_h / 2), label="house"))
        # Half-timber X-braces on ground+upper walls (front-facing)
        import math
        for fi in range(floors):
            zb = fi * floor_h
            ww = W * (1.0 + fi * 0.06)
            # Two diagonal beams crossing in an X
            for sd in (-1, 1):
                beam = _cube(tree, (base_x, -800 - fi * 200 - (sd + 1) * 60),
                              ww * 0.95, 0.04, 0.08, "ornament")
                tilt = math.atan2(floor_h, ww)
                pieces.append(_move(tree, beam, (base_x + 220, -800 - fi * 200 - (sd + 1) * 60),
                                     translation=(0, -dd / 2 - 0.025, zb + floor_h / 2),
                                     rotation=(sd * tilt, 0, 0), label="ornament"))
        # Steep gable roof - 2 slabs
        roof_h = floor_h * 0.9
        pitch = math.atan2(roof_h, W * 0.55)
        for sx in (-1, 1):
            slab = _cube(tree, (base_x, -2000 + (sx + 1) * 100),
                          W * 0.6 / math.cos(pitch), D + 0.3, 0.1, "house")
            pieces.append(_move(tree, slab, (base_x + 220, -2000 + (sx + 1) * 100),
                                 translation=(sx * W * 0.27, 0, floors * floor_h + roof_h * 0.5),
                                 rotation=(0, sx * -pitch, 0), label="house"))
        # Brick chimney
        chim = _cube(tree, (base_x, -2400), 0.35, 0.25, floor_h * 0.8, "brick")
        pieces.append(_move(tree, chim, (base_x + 200, -2400),
                             translation=(W * 0.3, 0, floors * floor_h + roof_h * 0.6),
                             label="brick"))
        return _finalize_building(tree, pieces, (base_x + 1200, 0))


    # ─── TAVERN ─────────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_town_house")
    return tree, gin, gout

register_builder(
    "MEL_town_house", build_town_house_group,
    "Town House", "Civic builder (absorbed from monolith build_town_house).",
    category="civic")


def build_tavern_group(group_name="MEL_tavern"):
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
        """Tavern: 2-story half-timber + hanging sign + chimney."""
        W = max(2.5, getattr(PROPS, 'base_radius', 1.0) * 3.0)
        D = W * 0.75
        H = max(2.5, getattr(PROPS, 'height', 4.0))
        pieces = []
        # Ground floor (stone)
        pieces.append(_move(tree, _cube(tree, (base_x, 200), W, D, H, "tower"),
                             (base_x + 200, 200),
                             translation=(0, 0, H / 2), label="tower"))
        # Upper floor (timber, slightly jettied)
        pieces.append(_move(tree, _cube(tree, (base_x, -100), W * 1.06, D * 1.06, H * 0.85, "house"),
                             (base_x + 200, -100),
                             translation=(0, 0, H + H * 0.425), label="house"))
        # Gable roof
        import math
        roof_h = H * 0.8
        pitch = math.atan2(roof_h, W * 0.55)
        for sx in (-1, 1):
            slab = _cube(tree, (base_x, -500 + (sx + 1) * 80),
                          W * 0.65 / math.cos(pitch), D * 1.15, 0.12, "house")
            pieces.append(_move(tree, slab, (base_x + 220, -500 + (sx + 1) * 80),
                                 translation=(sx * W * 0.3, 0, H * 1.85 + roof_h * 0.5),
                                 rotation=(0, sx * -pitch, 0), label="house"))
        # Hanging sign on a bracket
        bracket = _node(tree, 'GeometryNodeMeshCylinder', (base_x, -1000))
        bracket.inputs['Radius'].default_value = 0.04
        bracket.inputs['Depth'].default_value = 0.5
        bracket.inputs['Vertices'].default_value = 8
        pieces.append(_move(tree, bracket.outputs['Mesh'], (base_x + 200, -1000),
                             translation=(W / 2 + 0.2, 0, H * 1.6),
                             rotation=(0, 1.5708, 0), label="ornament"))
        color_node(bracket, "ornament")
        pieces.append(_move(tree, _cube(tree, (base_x, -1300), 0.06, 0.45, 0.55, "ornament"),
                             (base_x + 200, -1300),
                             translation=(W / 2 + 0.45, 0, H * 1.3), label="ornament"))
        # Chimney
        pieces.append(_move(tree, _cube(tree, (base_x, -1700), 0.4, 0.3, H * 1.4, "brick"),
                             (base_x + 200, -1700),
                             translation=(-W * 0.35, 0, H * 1.6), label="brick"))
        # Front door
        door_arch = _safe_node(tree, 'GeometryNodeCurveQuadraticBezier', (base_x, -2100))
        if door_arch:
            try:
                door_arch.inputs['Resolution'].default_value = 24
                door_arch.inputs['Start'].default_value  = (-0.5, 0, 0)
                door_arch.inputs['Middle'].default_value = (0, 0, 1.6)
                door_arch.inputs['End'].default_value    = (0.5, 0, 0)
            except Exception:
                pass
            prof = _cv_circle(tree, (base_x, -2300), 0.06, 8)
            sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 250, -2100))
            if sw and prof:
                _link(tree, door_arch.outputs['Curve'], sw.inputs['Curve'])
                _link(tree, prof.outputs['Curve'], sw.inputs['Profile Curve'])
                color_node(sw, "ornament")
                pieces.append(_move(tree, sw.outputs['Mesh'], (base_x + 500, -2100),
                                     translation=(0, -D / 2 - 0.05, 0), label="ornament"))
        return _finalize_building(tree, pieces, (base_x + 1200, 0))


    # ─── BLACKSMITH ────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_tavern")
    return tree, gin, gout

register_builder(
    "MEL_tavern", build_tavern_group,
    "Tavern", "Civic builder (absorbed from monolith build_tavern).",
    category="civic")


def build_blacksmith_group(group_name="MEL_blacksmith"):
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
        """Forge with open front, large brick chimney, anvil silhouette inside."""
        W = max(2.0, getattr(PROPS, 'base_radius', 1.0) * 2.6)
        D = W * 0.85
        H = max(2.0, getattr(PROPS, 'height', 3.5))
        pieces = []
        # Three walls (open front)
        pieces.append(_move(tree, _cube(tree, (base_x, 200), 0.3, D, H, "tower"),
                             (base_x + 200, 200), translation=(-W / 2, 0, H / 2), label="tower"))
        pieces.append(_move(tree, _cube(tree, (base_x, 0), 0.3, D, H, "tower"),
                             (base_x + 200, 0), translation=(W / 2, 0, H / 2), label="tower"))
        pieces.append(_move(tree, _cube(tree, (base_x, -200), W, 0.3, H, "tower"),
                             (base_x + 200, -200), translation=(0, D / 2, H / 2), label="tower"))
        # Sloped roof slab (single pitch over the open front)
        import math
        pitch = math.atan2(H * 0.4, D)
        pieces.append(_move(tree, _cube(tree, (base_x, -500),
                                          W + 0.3, D / math.cos(pitch), 0.1, "house"),
                             (base_x + 200, -500),
                             translation=(0, 0, H + 0.15),
                             rotation=(pitch, 0, 0), label="house"))
        # Massive chimney rising through roof
        pieces.append(_move(tree, _cube(tree, (base_x, -900), 0.7, 0.7, H * 1.7, "brick"),
                             (base_x + 200, -900),
                             translation=(W * 0.25, D * 0.25, H * 1.0), label="brick"))
        # Anvil inside (subdivided icosphere flattened + cube base)
        pieces.append(_move(tree, _cube(tree, (base_x, -1300), 0.5, 0.3, 0.4, "tower"),
                             (base_x + 200, -1300),
                             translation=(-W * 0.1, -D * 0.1, 0.2), label="tower"))
        pieces.append(_move(tree, _cube(tree, (base_x, -1500), 0.8, 0.18, 0.15, "ornament"),
                             (base_x + 200, -1500),
                             translation=(-W * 0.1, -D * 0.1, 0.5), label="ornament"))
        return _finalize_building(tree, pieces, (base_x + 1100, 0))


    # ─── STABLE ─────────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_blacksmith")
    return tree, gin, gout

register_builder(
    "MEL_blacksmith", build_blacksmith_group,
    "Blacksmith", "Civic builder (absorbed from monolith build_blacksmith).",
    category="civic")


def build_stable_group(group_name="MEL_stable"):
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
        """Long low building with N stall doors along the front."""
        n_stalls = max(3, getattr(PROPS, 'recursion_depth', 4))
        stall_w = 1.5
        W = stall_w * n_stalls
        D = max(2.0, getattr(PROPS, 'base_radius', 1.0) * 2.0)
        H = max(1.8, getattr(PROPS, 'height', 3.0))
        pieces = []
        # Body
        pieces.append(_move(tree, _cube(tree, (base_x, 200), W, D, H, "tower"),
                             (base_x + 200, 200), translation=(0, 0, H / 2), label="tower"))
        # Gable roof - single ridge
        import math
        roof_h = H * 0.5
        pitch = math.atan2(roof_h, D * 0.5)
        for sy in (-1, 1):
            slab = _cube(tree, (base_x, -300 + (sy + 1) * 100),
                          W + 0.2, D * 0.6 / math.cos(pitch), 0.1, "house")
            pieces.append(_move(tree, slab, (base_x + 220, -300 + (sy + 1) * 100),
                                 translation=(0, sy * D * 0.25, H + roof_h * 0.5),
                                 rotation=(sy * -pitch, 0, 0), label="house"))
        # Stall doors (top half open via 2 cubes per door)
        for i in range(n_stalls):
            x = -W / 2 + stall_w * (i + 0.5)
            # Lower half-door
            pieces.append(_move(tree, _cube(tree, (base_x, -1000 - i * 80),
                                              stall_w * 0.85, 0.04, H * 0.45, "ornament"),
                                 (base_x + 220, -1000 - i * 80),
                                 translation=(x, -D / 2 - 0.02, H * 0.225), label="ornament"))
            # Frame around opening
            pieces.append(_move(tree, _cube(tree, (base_x, -1200 - i * 80),
                                              stall_w * 0.95, 0.06, 0.08, "tower"),
                                 (base_x + 220, -1200 - i * 80),
                                 translation=(x, -D / 2 - 0.03, H * 0.95), label="tower"))
        return _finalize_building(tree, pieces, (base_x + 1200, 0))


    # ─── BELL TOWER (Campanile) ─────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_stable")
    return tree, gin, gout

register_builder(
    "MEL_stable", build_stable_group,
    "Stable", "Civic builder (absorbed from monolith build_stable).",
    category="civic")


def build_bell_tower_group(group_name="MEL_bell_tower"):
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
        """Tall square stone bell tower with louvres + pyramidal cap."""
        side = max(1.5, getattr(PROPS, 'base_radius', 1.0) * 1.8)
        H = max(6.0, getattr(PROPS, 'height', 5.0) * 2.0)
        pieces = []
        # Shaft
        pieces.append(_move(tree, _cube(tree, (base_x, 200), side, side, H, "tower"),
                             (base_x + 200, 200), translation=(0, 0, H / 2), label="tower"))
        # Belfry - wider band near top
        belfry_h = H * 0.18
        pieces.append(_move(tree, _cube(tree, (base_x, -200),
                                          side * 1.15, side * 1.15, belfry_h, "house"),
                             (base_x + 200, -200),
                             translation=(0, 0, H - belfry_h / 2), label="house"))
        # 4 louvred arches (one per face) - curve quad bezier + circular profile
        import math
        for face in range(4):
            ang = face * math.pi / 2
            ab = _safe_node(tree, 'GeometryNodeCurveQuadraticBezier',
                            (base_x, -600 - face * 100))
            if ab is None: continue
            try:
                ab.inputs['Resolution'].default_value = 16
                ab.inputs['Start'].default_value  = (-side * 0.32, 0, 0)
                ab.inputs['Middle'].default_value = (0, 0, side * 0.45)
                ab.inputs['End'].default_value    = (side * 0.32, 0, 0)
            except Exception:
                pass
            prof = _cv_circle(tree, (base_x, -800 - face * 100), 0.06, 8)
            sw = _safe_node(tree, 'GeometryNodeCurveToMesh',
                            (base_x + 220, -600 - face * 100))
            if sw and prof:
                _link(tree, ab.outputs['Curve'], sw.inputs['Curve'])
                _link(tree, prof.outputs['Curve'], sw.inputs['Profile Curve'])
                color_node(sw, "ornament")
                pieces.append(_move(tree, sw.outputs['Mesh'], (base_x + 500, -600 - face * 100),
                                     translation=(math.cos(ang) * (side * 0.58 + 0.05),
                                                  math.sin(ang) * (side * 0.58 + 0.05),
                                                  H - belfry_h * 0.5),
                                     rotation=(0, 0, ang + 1.5708),
                                     label="ornament"))
        # Pyramidal cap (4-vertex cone)
        cap = _safe_node(tree, 'GeometryNodeMeshCone', (base_x, -1800))
        if cap:
            cap.inputs['Radius Bottom'].default_value = side * 0.85
            cap.inputs['Radius Top'].default_value = 0
            cap.inputs['Depth'].default_value = side * 1.6
            cap.inputs['Vertices'].default_value = 4
            pieces.append(_move(tree, cap.outputs['Mesh'], (base_x + 200, -1800),
                                 translation=(0, 0, H + side * 0.8),
                                 rotation=(0, 0, 0.7854), label="house"))
            color_node(cap, "house")
        # Small cross/finial on top
        pieces.append(_move(tree, _cube(tree, (base_x, -2200), 0.08, 0.08, 0.45, "ornament"),
                             (base_x + 200, -2200),
                             translation=(0, 0, H + side * 1.85), label="ornament"))
        pieces.append(_move(tree, _cube(tree, (base_x, -2400), 0.32, 0.08, 0.08, "ornament"),
                             (base_x + 200, -2400),
                             translation=(0, 0, H + side * 1.8), label="ornament"))
        return _finalize_building(tree, pieces, (base_x + 1200, 0))


    # ─── MONASTERY CLOISTER ─────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_bell_tower")
    return tree, gin, gout

register_builder(
    "MEL_bell_tower", build_bell_tower_group,
    "Bell Tower", "Civic builder (absorbed from monolith build_bell_tower).",
    category="civic")


def build_monastery_group(group_name="MEL_monastery"):
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
        """Square cloister: 4 walls forming a courtyard, each with a colonnade."""
        side = max(3.5, getattr(PROPS, 'base_radius', 1.0) * 5.0)
        cor_w = side * 0.18   # corridor width
        H = max(2.5, getattr(PROPS, 'height', 4.0))
        pieces = []
        # 4 covered colonnade walls
        for face in range(4):
            import math
            ang = face * math.pi / 2
            # Outer wall
            pieces.append(_move(tree, _cube(tree, (base_x, 200 - face * 200),
                                              side, 0.3, H, "tower"),
                                 (base_x + 200, 200 - face * 200),
                                 translation=(math.cos(ang + math.pi / 2) * (side / 2),
                                              math.sin(ang + math.pi / 2) * (side / 2), H / 2),
                                 rotation=(0, 0, ang), label="tower"))
            # Inner colonnade - 6 columns per side
            n_cols = 6
            for c in range(n_cols):
                t = -side / 2 + (c + 0.5) * (side / n_cols)
                col = _node(tree, 'GeometryNodeMeshCylinder',
                            (base_x, -800 - face * 200 - c * 60))
                col.inputs['Radius'].default_value = 0.12
                col.inputs['Depth'].default_value = H * 0.85
                col.inputs['Vertices'].default_value = 12
                pieces.append(_move(tree, col.outputs['Mesh'],
                                     (base_x + 220, -800 - face * 200 - c * 60),
                                     translation=(math.cos(ang + math.pi / 2) * (side / 2 - cor_w)
                                                  + math.cos(ang) * t,
                                                  math.sin(ang + math.pi / 2) * (side / 2 - cor_w)
                                                  + math.sin(ang) * t,
                                                  H * 0.425), label="tower"))
                color_node(col, "tower")
            # Slanted corridor roof
            roof_slab = _cube(tree, (base_x, -1900 - face * 200),
                               side, cor_w * 1.2, 0.1, "house")
            pieces.append(_move(tree, roof_slab, (base_x + 220, -1900 - face * 200),
                                 translation=(math.cos(ang + math.pi / 2) * (side / 2 - cor_w / 2),
                                              math.sin(ang + math.pi / 2) * (side / 2 - cor_w / 2),
                                              H + 0.05),
                                 rotation=(0, 0, ang), label="house"))
        # Open courtyard floor - walk plane top at Z=0 (v2.60.1)
        court = max(1.0, side - cor_w * 2.2)
        floor_t = 0.25
        pieces.append(_move(tree, _cube(tree, (base_x, -3000), court, court, floor_t, "level"),
                             (base_x + 200, -3000), translation=(0, 0, -floor_t * 0.5), label="level"))
        return _finalize_building(tree, pieces, (base_x + 1400, 0))


    # ─── WATERMILL ──────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_monastery")
    return tree, gin, gout

register_builder(
    "MEL_monastery", build_monastery_group,
    "Monastery", "Civic builder (absorbed from monolith build_monastery).",
    category="civic")


def build_watermill_group(group_name="MEL_watermill"):
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
        """Mill house with large waterwheel on one side."""
        W = max(2.0, getattr(PROPS, 'base_radius', 1.0) * 2.4)
        D = W * 0.85
        H = max(2.5, getattr(PROPS, 'height', 4.0))
        pieces = []
        # Body
        pieces.append(_move(tree, _cube(tree, (base_x, 200), W, D, H, "tower"),
                             (base_x + 200, 200), translation=(0, 0, H / 2), label="tower"))
        # Pitched roof (two slabs)
        import math
        pitch = math.atan2(H * 0.5, W * 0.55)
        for sx in (-1, 1):
            slab = _cube(tree, (base_x, -200 + (sx + 1) * 80),
                          W * 0.6 / math.cos(pitch), D + 0.2, 0.1, "house")
            pieces.append(_move(tree, slab, (base_x + 220, -200 + (sx + 1) * 80),
                                 translation=(sx * W * 0.27, 0, H + H * 0.25),
                                 rotation=(0, sx * -pitch, 0), label="house"))
        # Waterwheel on +X face
        wheel_r = H * 0.55
        wheel_d = 0.35
        wheel = _safe_node(tree, 'GeometryNodeMeshTorus', (base_x, -800))
        if wheel:
            try:
                wheel.inputs['Major Radius'].default_value = wheel_r
                wheel.inputs['Minor Radius'].default_value = 0.06
                wheel.inputs['Major Segments'].default_value = 32
                wheel.inputs['Minor Segments'].default_value = 6
            except Exception:
                pass
            # Two parallel rings = the wheel's outer rims
            for sd in (-1, 1):
                pieces.append(_move(tree, wheel.outputs['Mesh'], (base_x + 200, -800 - sd * 100),
                                     translation=(W / 2 + 0.3, sd * wheel_d / 2, wheel_r * 0.9),
                                     rotation=(0, 1.5708, 0), label="ornament"))
            color_node(wheel, "ornament")
        # Wheel paddles (8 radial boxes)
        for i in range(8):
            ang = (i / 8) * math.tau
            paddle = _cube(tree, (base_x, -1200 - i * 60),
                            0.1, wheel_d, wheel_r * 0.4, "ornament")
            pieces.append(_move(tree, paddle, (base_x + 220, -1200 - i * 60),
                                 translation=(W / 2 + 0.3, 0,
                                              wheel_r * 0.9 + math.sin(ang) * wheel_r * 0.78),
                                 rotation=(0, ang, 0), label="ornament"))
        # Central axle
        axle = _node(tree, 'GeometryNodeMeshCylinder', (base_x, -2000))
        axle.inputs['Radius'].default_value = 0.06
        axle.inputs['Depth'].default_value = wheel_d + 0.4
        axle.inputs['Vertices'].default_value = 12
        pieces.append(_move(tree, axle.outputs['Mesh'], (base_x + 200, -2000),
                             translation=(W / 2 + 0.3, 0, wheel_r * 0.9),
                             rotation=(1.5708, 0, 0), label="ornament"))
        color_node(axle, "ornament")
        return _finalize_building(tree, pieces, (base_x + 1300, 0))


    # ─── LIGHTHOUSE ─────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_watermill")
    return tree, gin, gout

register_builder(
    "MEL_watermill", build_watermill_group,
    "Watermill", "Civic builder (absorbed from monolith build_watermill).",
    category="civic")


def build_lighthouse_group(group_name="MEL_lighthouse"):
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
        """Tall tapered maritime tower: stone shaft + gallery + lantern room + spire."""
        r_base = max(0.8, getattr(PROPS, 'base_radius', 1.0) * 1.0)
        r_top = r_base * 0.55
        H = max(8.0, getattr(PROPS, 'height', 5.0) * 3.0)
        pieces = []
        # Tapered shaft via stacked cylinders (5 sections)
        n_sec = 5
        sec_h = H / n_sec
        for i in range(n_sec):
            z = i * sec_h
            r = r_base + (r_top - r_base) * (i / max(1, n_sec - 1))
            body_c = _cv_circle(tree, (base_x, 200 - i * 200), r, 24)
            body = _fill_extrude(tree, body_c.outputs['Curve'] if body_c else None,
                                  (base_x + 200, 200 - i * 200),
                                  (base_x + 400, 200 - i * 200), sec_h, "tower")
            pieces.append(_move(tree, body, (base_x + 600, 200 - i * 200),
                                 translation=(0, 0, z), label="tower"))
        # Gallery (toroidal ring) just below lantern
        gallery = _safe_node(tree, 'GeometryNodeMeshTorus', (base_x, -1300))
        if gallery:
            try:
                gallery.inputs['Major Radius'].default_value = r_top * 1.4
                gallery.inputs['Minor Radius'].default_value = r_top * 0.12
                gallery.inputs['Major Segments'].default_value = 32
                gallery.inputs['Minor Segments'].default_value = 6
            except Exception:
                pass
            pieces.append(_move(tree, gallery.outputs['Mesh'], (base_x + 200, -1300),
                                 translation=(0, 0, H), label="ornament"))
            color_node(gallery, "ornament")
        # Lantern room (glassy cylinder)
        lantern_c = _cv_circle(tree, (base_x, -1700), r_top * 0.95, 16)
        lantern = _fill_extrude(tree, lantern_c.outputs['Curve'] if lantern_c else None,
                                 (base_x + 200, -1700), (base_x + 400, -1700),
                                 sec_h * 0.8, "house")
        pieces.append(_move(tree, lantern, (base_x + 600, -1700),
                             translation=(0, 0, H + 0.15), label="house"))
        # Conical roof
        roof = _safe_node(tree, 'GeometryNodeMeshCone', (base_x, -2100))
        if roof:
            roof.inputs['Radius Bottom'].default_value = r_top * 1.1
            roof.inputs['Radius Top'].default_value = 0
            roof.inputs['Depth'].default_value = r_top * 2.0
            roof.inputs['Vertices'].default_value = 16
            pieces.append(_move(tree, roof.outputs['Mesh'], (base_x + 200, -2100),
                                 translation=(0, 0, H + sec_h * 0.8 + r_top), label="house"))
            color_node(roof, "house")
        # Spire/finial
        pieces.append(_move(tree, _cube(tree, (base_x, -2500), 0.1, 0.1, r_top * 1.5, "ornament"),
                             (base_x + 200, -2500),
                             translation=(0, 0, H + sec_h * 0.8 + r_top * 2.5), label="ornament"))
        return _finalize_building(tree, pieces, (base_x + 1300, 0))


    # ─── CN MOON GATE ───────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_lighthouse")
    return tree, gin, gout

register_builder(
    "MEL_lighthouse", build_lighthouse_group,
    "Lighthouse", "Civic builder (absorbed from monolith build_lighthouse).",
    category="civic")


def build_public_fountain_group(group_name="MEL_public_fountain"):
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
        """Plaza fountain: large round basin + central tiered cup + finial spout."""
        R = max(1.0, getattr(PROPS, 'base_radius', 1.0) * 1.6)
        tiers = max(2, getattr(PROPS, 'fountain_tiers', 3))
        pieces = []
        # Outer basin (extruded circle ring - approximate with torus + disc)
        outer = _cv_circle(tree, (base_x, 200), R, 48)
        outer_m = _fill_extrude(tree, outer.outputs['Curve'] if outer else None,
                                  (base_x + 200, 200), (base_x + 400, 200), 0.3, "tower")
        pieces.append(_move(tree, outer_m, (base_x + 600, 200),
                             translation=(0, 0, 0), label="tower"))
        # Basin rim torus
        rim = _safe_node(tree, 'GeometryNodeMeshTorus', (base_x, -200))
        if rim:
            try:
                rim.inputs['Major Radius'].default_value = R
                rim.inputs['Minor Radius'].default_value = 0.08
                rim.inputs['Major Segments'].default_value = 48
                rim.inputs['Minor Segments'].default_value = 8
            except Exception:
                pass
            pieces.append(_move(tree, rim.outputs['Mesh'], (base_x + 200, -200),
                                 translation=(0, 0, 0.32), label="ornament"))
            color_node(rim, "ornament")
        # Central tiered cups (stacked toruses with decreasing radius)
        cz = 0.5
        for t in range(tiers):
            cup_r = R * (0.5 - t * 0.12)
            if cup_r <= 0.1: break
            cup_c = _cv_circle(tree, (base_x, -500 - t * 200), cup_r, 32)
            cup_m = _fill_extrude(tree, cup_c.outputs['Curve'] if cup_c else None,
                                    (base_x + 200, -500 - t * 200),
                                    (base_x + 400, -500 - t * 200), 0.18, "tower")
            pieces.append(_move(tree, cup_m, (base_x + 600, -500 - t * 200),
                                 translation=(0, 0, cz), label="tower"))
            cz += 0.5
        # Central column under top cup
        col = _node(tree, 'GeometryNodeMeshCylinder', (base_x, -1300))
        col.inputs['Radius'].default_value = 0.12
        col.inputs['Depth'].default_value = cz + 0.5
        col.inputs['Vertices'].default_value = 16
        pieces.append(_move(tree, col.outputs['Mesh'], (base_x + 200, -1300),
                             translation=(0, 0, (cz + 0.5) / 2 + 0.25), label="tower"))
        color_node(col, "tower")
        # Finial spout
        fin = _safe_node(tree, 'GeometryNodeMeshIcoSphere', (base_x, -1700))
        if fin:
            fin.inputs['Radius'].default_value = 0.15
            fin.inputs['Subdivisions'].default_value = 3
            pieces.append(_move(tree, fin.outputs['Mesh'], (base_x + 200, -1700),
                                 translation=(0, 0, cz + 0.6), label="ornament"))
            color_node(fin, "ornament")
        return _join_all(tree, pieces, (base_x + 1300, 0))


    # ======================================================================
    # * ASIAN + * CIVIC + * LANDSCAPE + * DECOR (v2.25) - Layer 1 additions
    # ======================================================================

    # ─── CN TING PAVILION (hexagonal garden pavilion) ───────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_public_fountain")
    return tree, gin, gout

register_builder(
    "MEL_public_fountain", build_public_fountain_group,
    "Public Fountain", "Civic builder (absorbed from monolith build_public_fountain).",
    category="civic")


def build_town_hall_group(group_name="MEL_town_hall"):
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
        """Civic building with central clock tower."""
        W = max(4.0, getattr(PROPS, 'base_radius', 1.0) * 4.5)
        D = W * 0.7
        H = max(3.5, getattr(PROPS, 'height', 4.0))
        pieces = []
        # Main hall
        pieces.append(_move(tree, _cube(tree, (base_x, 200), W, D, H, "tower"),
                             (base_x + 200, 200), translation=(0, 0, H / 2), label="tower"))
        # Pitched roof
        import math
        roof_h = H * 0.45
        pitch = math.atan2(roof_h, D * 0.5)
        for sy in (-1, 1):
            slab = _cube(tree, (base_x, -300 + (sy + 1) * 80),
                          W + 0.2, D * 0.6 / math.cos(pitch), 0.12, "house")
            pieces.append(_move(tree, slab, (base_x + 220, -300 + (sy + 1) * 80),
                                 translation=(0, sy * D * 0.25, H + roof_h * 0.5),
                                 rotation=(sy * -pitch, 0, 0), label="house"))
        # Central clock tower
        tower_w = W * 0.18
        tower_h = H * 1.5
        pieces.append(_move(tree, _cube(tree, (base_x, -1000), tower_w, tower_w, tower_h, "tower"),
                             (base_x + 200, -1000),
                             translation=(0, 0, H + tower_h * 0.5), label="tower"))
        # Clock face (cylinder on front)
        clock = _node(tree, 'GeometryNodeMeshCylinder', (base_x, -1400))
        clock.inputs['Radius'].default_value = tower_w * 0.4
        clock.inputs['Depth'].default_value = 0.06
        clock.inputs['Vertices'].default_value = 24
        pieces.append(_move(tree, clock.outputs['Mesh'], (base_x + 200, -1400),
                             translation=(0, -tower_w / 2 - 0.04, H + tower_h * 0.7),
                             rotation=(1.5708, 0, 0), label="ornament"))
        color_node(clock, "ornament")
        # Tower roof (pyramid)
        cap = _safe_node(tree, 'GeometryNodeMeshCone', (base_x, -1700))
        if cap:
            cap.inputs['Radius Bottom'].default_value = tower_w * 0.8
            cap.inputs['Radius Top'].default_value = 0
            cap.inputs['Depth'].default_value = tower_w * 1.4
            cap.inputs['Vertices'].default_value = 24
            pieces.append(_move(tree, cap.outputs['Mesh'], (base_x + 200, -1700),
                                 translation=(0, 0, H + tower_h + tower_w * 0.7),
                                 rotation=(0, 0, 0.7854), label="house"))
            color_node(cap, "house")
        # Columned portico at front (4 columns)
        for i in range(4):
            x = -W * 0.35 + i * (W * 0.7 / 3)
            col = _node(tree, 'GeometryNodeMeshCylinder', (base_x, -2000 - i * 60))
            col.inputs['Radius'].default_value = 0.18
            col.inputs['Depth'].default_value = H * 0.85
            col.inputs['Vertices'].default_value = 14
            pieces.append(_move(tree, col.outputs['Mesh'], (base_x + 220, -2000 - i * 60),
                                 translation=(x, -D / 2 - 0.45, H * 0.425), label="tower"))
            color_node(col, "tower")
        # Portico roof
        pieces.append(_move(tree, _cube(tree, (base_x, -2500), W * 0.85, 0.7, 0.12, "house"),
                             (base_x + 200, -2500),
                             translation=(0, -D / 2 - 0.45, H * 0.92), label="house"))
        return _finalize_building(tree, pieces, (base_x + 1300, 0))


    # ─── GUILD HALL ─────────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_town_hall")
    return tree, gin, gout

register_builder(
    "MEL_town_hall", build_town_hall_group,
    "Town Hall", "Civic builder (absorbed from monolith build_town_hall).",
    category="civic")


def build_guild_hall_group(group_name="MEL_guild_hall"):
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
        """Imposing meeting hall with portico, large arched door, banner."""
        W = max(3.5, getattr(PROPS, 'base_radius', 1.0) * 4.0)
        D = W * 0.8
        H = max(3.0, getattr(PROPS, 'height', 4.5))
        pieces = []
        # Body
        pieces.append(_move(tree, _cube(tree, (base_x, 200), W, D, H, "tower"),
                             (base_x + 200, 200), translation=(0, 0, H / 2), label="tower"))
        # Decorative cornice band
        pieces.append(_move(tree, _cube(tree, (base_x, -100), W + 0.3, D + 0.3, 0.2, "ornament"),
                             (base_x + 200, -100),
                             translation=(0, 0, H * 0.92), label="ornament"))
        # Flat roof slab
        pieces.append(_move(tree, _cube(tree, (base_x, -400), W + 0.4, D + 0.4, 0.15, "house"),
                             (base_x + 200, -400),
                             translation=(0, 0, H + 0.075), label="house"))
        # Large arched front door (curve-sweep)
        door = _safe_node(tree, 'GeometryNodeCurveQuadraticBezier', (base_x, -700))
        if door:
            try:
                door.inputs['Resolution'].default_value = 28
                door.inputs['Start'].default_value = (-W * 0.18, 0, 0)
                door.inputs['Middle'].default_value = (0, 0, H * 0.65)
                door.inputs['End'].default_value = (W * 0.18, 0, 0)
            except Exception:
                pass
            prof = _cv_circle(tree, (base_x, -900), 0.09, 8)
            sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 250, -700))
            if sw and prof:
                _link(tree, door.outputs['Curve'], sw.inputs['Curve'])
                _link(tree, prof.outputs['Curve'], sw.inputs['Profile Curve'])
                color_node(sw, "ornament")
                pieces.append(_move(tree, sw.outputs['Mesh'], (base_x + 500, -700),
                                     translation=(0, -D / 2 - 0.05, 0), label="ornament"))
        # Twin columns flanking door
        for sx in (-1, 1):
            col = _node(tree, 'GeometryNodeMeshCylinder', (base_x, -1200 + sx * 100))
            col.inputs['Radius'].default_value = 0.22
            col.inputs['Depth'].default_value = H * 0.75
            col.inputs['Vertices'].default_value = 16
            pieces.append(_move(tree, col.outputs['Mesh'], (base_x + 220, -1200 + sx * 100),
                                 translation=(sx * W * 0.27, -D / 2 - 0.15, H * 0.375),
                                 label="tower"))
            color_node(col, "tower")
        # Banner above door
        pieces.append(_move(tree, _cube(tree, (base_x, -1700), W * 0.55, 0.04, 0.6, "ornament"),
                             (base_x + 200, -1700),
                             translation=(0, -D / 2 - 0.2, H * 0.4), label="ornament"))
        return _finalize_building(tree, pieces, (base_x + 1200, 0))


    # ─── CRYPT ENTRANCE ─────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_guild_hall")
    return tree, gin, gout

register_builder(
    "MEL_guild_hall", build_guild_hall_group,
    "Guild Hall", "Civic builder (absorbed from monolith build_guild_hall).",
    category="civic")


def build_crypt_entrance_group(group_name="MEL_crypt_entrance"):
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
        """Sunken stairs descending to an arched doorway in stonework."""
        W = max(1.6, getattr(PROPS, 'base_radius', 1.0) * 2.0)
        n_steps = max(5, getattr(PROPS, 'stair_step_count', 6))
        step_h = 0.2
        pieces = []
        # Stone surround / arch frame
        pieces.append(_move(tree, _cube(tree, (base_x, 200), W + 0.6, 0.4, 2.0, "tower"),
                             (base_x + 200, 200),
                             translation=(0, n_steps * 0.5 + 0.6, 1.0), label="tower"))
        # Descending steps
        for i in range(n_steps):
            step = _cube(tree, (base_x, -200 - i * 60), W, 0.5, step_h, "tower")
            pieces.append(_move(tree, step, (base_x + 220, -200 - i * 60),
                                 translation=(0, i * 0.5, -i * step_h - step_h * 0.5),
                                 label="tower"))
        # Side walls flanking stairs
        for sx in (-1, 1):
            wall = _cube(tree, (base_x, -1500 - (sx + 1) * 80),
                          0.3, n_steps * 0.5 + 0.5, n_steps * step_h + 0.5, "tower")
            pieces.append(_move(tree, wall, (base_x + 220, -1500 - (sx + 1) * 80),
                                 translation=(sx * (W / 2 + 0.15), n_steps * 0.25,
                                              -n_steps * step_h * 0.5 + 0.25),
                                 label="tower"))
        # Arched doorway at bottom
        door = _safe_node(tree, 'GeometryNodeCurveQuadraticBezier', (base_x, -1900))
        if door:
            try:
                door.inputs['Resolution'].default_value = 24
                door.inputs['Start'].default_value = (-W * 0.3, 0, 0)
                door.inputs['Middle'].default_value = (0, 0, 1.4)
                door.inputs['End'].default_value = (W * 0.3, 0, 0)
            except Exception:
                pass
            prof = _cv_circle(tree, (base_x, -2100), 0.08, 8)
            sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 250, -1900))
            if sw and prof:
                _link(tree, door.outputs['Curve'], sw.inputs['Curve'])
                _link(tree, prof.outputs['Curve'], sw.inputs['Profile Curve'])
                color_node(sw, "ornament")
                pieces.append(_move(tree, sw.outputs['Mesh'], (base_x + 500, -1900),
                                     translation=(0, n_steps * 0.5 + 0.45,
                                                  -n_steps * step_h), label="ornament"))
        return _finalize_building(tree, pieces, (base_x + 1200, 0))


    # ─── WAYSIDE SHRINE ─────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_crypt_entrance")
    return tree, gin, gout

register_builder(
    "MEL_crypt_entrance", build_crypt_entrance_group,
    "Crypt Entrance", "Civic builder (absorbed from monolith build_crypt_entrance).",
    category="civic")


def build_wayside_shrine_group(group_name="MEL_wayside_shrine"):
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
        """Small roadside shrine: plinth + niche + peaked roof + cross/finial."""
        W = max(0.6, getattr(PROPS, 'base_radius', 1.0) * 0.7)
        H = max(1.2, getattr(PROPS, 'height', 2.0))
        pieces = []
        # Plinth base
        pieces.append(_move(tree, _cube(tree, (base_x, 200), W * 1.6, W * 1.4, 0.4, "house"),
                             (base_x + 200, 200), translation=(0, 0, 0.2), label="house"))
        # Tall narrow shrine body
        pieces.append(_move(tree, _cube(tree, (base_x, -100), W, W * 0.7, H, "tower"),
                             (base_x + 200, -100), translation=(0, 0, 0.4 + H / 2), label="tower"))
        # Niche cutout (smaller recessed box on front - visual depth)
        pieces.append(_move(tree, _cube(tree, (base_x, -400), W * 0.7, 0.1, H * 0.55, "ornament"),
                             (base_x + 200, -400),
                             translation=(0, -W * 0.4, 0.4 + H * 0.5), label="ornament"))
        # Peaked roof (two slabs)
        import math
        pitch = math.atan2(H * 0.3, W * 0.55)
        for sx in (-1, 1):
            slab = _cube(tree, (base_x, -700 + (sx + 1) * 60),
                          W * 0.65 / math.cos(pitch), W * 0.8, 0.06, "house")
            pieces.append(_move(tree, slab, (base_x + 220, -700 + (sx + 1) * 60),
                                 translation=(sx * W * 0.27, 0, 0.4 + H + H * 0.15),
                                 rotation=(0, sx * -pitch, 0), label="house"))
        # Cross on top
        pieces.append(_move(tree, _cube(tree, (base_x, -1100), 0.05, 0.05, 0.3, "ornament"),
                             (base_x + 200, -1100),
                             translation=(0, 0, 0.4 + H + H * 0.4), label="ornament"))
        pieces.append(_move(tree, _cube(tree, (base_x, -1300), 0.22, 0.05, 0.05, "ornament"),
                             (base_x + 200, -1300),
                             translation=(0, 0, 0.4 + H + H * 0.5), label="ornament"))
        return _finalize_building(tree, pieces, (base_x + 1100, 0))


    # ─── STYLIZED TREE ──────────────────────────────────────────────────
    geom = _impl()
    if geom is not None:
        _link(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_wayside_shrine")
    return tree, gin, gout

register_builder(
    "MEL_wayside_shrine", build_wayside_shrine_group,
    "Wayside Shrine", "Civic builder (absorbed from monolith build_wayside_shrine).",
    category="civic")


# 19 builders registered
