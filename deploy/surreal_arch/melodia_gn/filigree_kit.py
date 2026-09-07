"""MEL filigree builders — absorbed from the monolith (P2 family 9b).
Full dependency closure. Regenerable."""
from __future__ import annotations
import math
import bpy
from .core import (
    safe_node, link_sockets, color_node, label_tree, new_geometry_tree,
    add_float_param, add_int_param, add_bool_param, add_string_param,
    register_builder,
)

COLORS = {
    "input":     (0.55, 0.65, 0.85),
    "tower":     (0.85, 0.75, 0.85),
    "organic":   (0.76, 0.92, 0.78),
    "noise":     (0.95, 0.85, 0.70),
    "deform":    (1.00, 0.95, 0.75),
    "optimize":  (0.75, 0.90, 0.95),
    "output":    (0.85, 0.75, 0.95),
    "railing":   (0.90, 0.80, 0.95),
    "stair":     (0.80, 0.95, 0.85),
    "arch":      (0.95, 0.80, 0.80),
    "buttress":  (0.92, 0.88, 0.78),
    "ornament":  (0.95, 0.92, 0.78),
    "penrose":   (0.85, 0.85, 1.00),    # impossible stairs
    "pillar":    (0.95, 0.92, 0.85),    # classical column
    "dome":      (0.80, 0.92, 0.95),    # spherical roof
    "crenel":    (0.90, 0.88, 0.85),    # castle battlements
    "fractal":   (0.95, 0.85, 0.95),    # recursive structures
    "bevel":     (0.92, 0.95, 0.92),    # soft-bevel pass
    "music":     (0.95, 0.80, 0.92),    # musical notation
    "gothic":    (0.85, 0.80, 0.95),    # Gothic architectural elements
    "tracery":   (0.92, 0.92, 1.00),    # Gothic tracery / tracing
    "venetian":  (0.95, 0.85, 0.78),    # Venetian Gothic (warm sandstone)
    "ogee":      (0.92, 0.78, 0.85),    # Venetian ogee curves
    "palazzo":   (0.88, 0.82, 0.95),    # Palazzo composite
    "entropiombo":(0.85,0.95, 0.85),    # Inward-lean deformation
    "brick":     (0.95, 0.78, 0.72),    # Brick masonry
    "bridge":    (0.85, 0.92, 0.95),    # Venetian bridge
    "path":      (0.92, 0.85, 0.95),    # Escher walkway
    "universal": (1.00, 0.92, 0.85),    # Universal modulation pass
    "synthia":   (0.85, 0.92, 0.78),    # Synthia math viz integration
    "modular":   (0.92, 0.95, 0.85),    # Modular building pieces
    "window":    (0.85, 0.92, 0.95),    # Window opening
    "door":      (0.95, 0.85, 0.78),    # Door
    "fountain":  (0.78, 0.92, 0.95),    # Fountain
    "tile":      (0.95, 0.92, 0.85),    # Floor tile
    "roof":      (0.95, 0.78, 0.78),    # Roof tiles
    "lantern":   (1.00, 0.92, 0.65),    # Lamppost
    "spline":    (0.78, 0.92, 0.95),    # Spline instancing
    "radial":    (0.95, 0.85, 0.85),    # Radial array
    "tessellation":(0.85, 0.95, 0.78),  # Escher tessellation
    "hyperbolic": (0.92, 0.78, 0.95),   # Hyperbolic disk
    "genshin":   (1.00, 0.85, 0.92),    # Genshin Impact stylization
    "sheet_music":(0.95, 0.95, 0.85),   # Sheet music railing
    "level":      (0.85, 0.95, 0.85),   # Level design / greybox
    "wall":       (0.90, 0.85, 0.80),   # Wall pieces
    "ceiling":    (0.78, 0.82, 0.92),   # Ceiling
    "house":      (0.95, 0.85, 0.92),   # Modular house composite
    "beams":      (0.85, 0.92, 0.95),   # Cascading beams (Erindale)
    "cleanup":    (0.92, 0.92, 0.92),   # Topology cleanup pass
    "fence":      (0.88, 0.92, 0.80),   # Fence / barrier generators
}


# Forward-declared base for all sub-panels (referenced by panels defined
# both before and after the original definition site further down).
class _SubPanelBase:
    """Mixin for all sub-panels (sets parent and properties context)."""
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "modifier"
    bl_parent_id   = "SURREAL_ARCH_PT_panel"
    bl_options     = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'


class _EffectsSubPanelBase:
    """Nested under Effects & Atmosphere - optional overlay panels."""
    bl_space_type  = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context     = "modifier"
    bl_parent_id   = "SURREAL_ARCH_PT_effects"
    bl_options     = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'


# Synthia preset list (curated subset with the most surreal/architectural shapes)

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



def build_filigree_core(tree, props, base_x=-1400, rail_mode=False):
    thick = max(0.005, getattr(props, 'filigree_thickness', 0.02))
    if rail_mode:
        span_w = max(0.5, getattr(props, 'rail_length', 2.5))
        span_h = max(0.3, getattr(props, 'rail_height', 1.0) * 0.85)
    else:
        span_w = max(0.4, getattr(props, 'filigree_width', 1.6))
        span_h = max(0.4, getattr(props, 'filigree_height', 2.0))
    prof = _filigree_profile(tree, thick, base_x, -400)
    parts = []
    if getattr(props, 'filigree_include_frame', True):
        parts.extend(_filigree_frame_edges(tree, span_w, span_h, prof, base_x))
    parts.extend(_build_filigree_interior(tree, props, span_w, span_h, prof, base_x))
    return _join_all(tree, parts, (base_x + 1200, 0), label="ornament", weld=0.0)



def build_filigree_panel(tree, props, base_x=-1400):
    return build_filigree_core(tree, props, base_x=base_x, rail_mode=False)



def build_filigree_rail_inset(tree, props, base_x=-1400):
    return build_filigree_core(tree, props, base_x=base_x, rail_mode=True)



def _filigree_profile(tree, radius, base_x, y_off, label="ornament"):
    prof = _safe_node(tree, 'GeometryNodeCurvePrimitiveCircle', (base_x, y_off))
    if prof:
        try:
            prof.inputs['Resolution'].default_value = 8
            prof.inputs['Radius'].default_value = radius
        except Exception:
            pass
        color_node(prof, label)
    return prof



def _filigree_frame_edges(tree, span_w, span_h, prof, base_x):
    margin = max(0.04, min(span_w, span_h) * 0.06)
    hw, hh = span_w / 2 - margin, span_h / 2 - margin
    edges = (
        ((-hw, -hh, 0), (hw, -hh, 0)),
        ((hw, -hh, 0), (hw, hh, 0)),
        ((hw, hh, 0), (-hw, hh, 0)),
        ((-hw, hh, 0), (-hw, -hh, 0)),
    )
    parts = []
    for i, (a, b) in enumerate(edges):
        seg = _filigree_sweep_line(tree, a, b, prof, base_x, 800 + i * 40)
        if seg:
            parts.append(seg)
    return parts



def _build_filigree_interior(tree, props, span_w, span_h, prof, base_x):
    style = getattr(props, 'filigree_style', 'ARTNOUVEAU_VINE')
    density = max(0.1, min(1.0, getattr(props, 'filigree_density', 0.5)))
    symmetry = getattr(props, 'filigree_symmetry', 'MIRROR')
    parts = []
    n_curves = max(2, int(3 + density * 8))

    if style == 'ARTNOUVEAU_VINE':
        for i in range(n_curves):
            cy = -span_h * 0.35 + (span_h * 0.7) * (i / max(1, n_curves - 1))
            parts.extend(_filigree_scurve(
                tree, prof, 0, cy, span_w, span_h, base_x, 100 + i * 70, flip=(i % 2 == 1)))
            if symmetry == 'MIRROR':
                for side in (-1, 1):
                    ox = side * span_w * 0.22
                    parts.extend(_filigree_scurve(
                        tree, prof, ox, cy, span_w * 0.55, span_h,
                        base_x, 500 + i * 70 + side * 20, flip=(i % 2 == 0)))
    elif style == 'GOTHIC_IRON':
        n_spokes = max(4, int(4 + density * 8))
        for i in range(n_spokes):
            ang = math.pi * 2 * i / n_spokes
            r0 = min(span_w, span_h) * 0.08
            r1 = min(span_w, span_h) * 0.42
            a = (math.cos(ang) * r0, math.sin(ang) * r0, 0.02)
            b = (math.cos(ang) * r1, math.sin(ang) * r1, 0.02)
            seg = _filigree_sweep_line(tree, a, b, prof, base_x, 200 + i * 25)
            if seg:
                parts.append(seg)
        ring_r = min(span_w, span_h) * 0.32
        n_ring = 20
        for i in range(n_ring):
            a1 = math.pi * 2 * i / n_ring
            a2 = math.pi * 2 * (i + 1) / n_ring
            p0 = (math.cos(a1) * ring_r, math.sin(a1) * ring_r, 0.02)
            p1 = (math.cos(a2) * ring_r, math.sin(a2) * ring_r, 0.02)
            seg = _filigree_sweep_line(tree, p0, p1, prof, base_x, 900 + i * 12)
            if seg:
                parts.append(seg)
        if symmetry == 'RADIAL' and n_spokes >= 6:
            inner_r = ring_r * 0.55
            for i in range(0, n_spokes, 2):
                ang = math.pi * 2 * i / n_spokes
                p0 = (math.cos(ang) * inner_r, math.sin(ang) * inner_r, 0.02)
                p1 = (math.cos(ang + math.pi) * inner_r, math.sin(ang + math.pi) * inner_r, 0.02)
                seg = _filigree_sweep_line(tree, p0, p1, prof, base_x, 1400 + i * 15)
                if seg:
                    parts.append(seg)
    else:
        rows = max(2, int(2 + density * 5))
        cols = max(2, int(2 + density * 5))
        cell_w = span_w * 0.8 / max(1, cols - 1) if cols > 1 else span_w * 0.4
        cell_h = span_h * 0.8 / max(1, rows - 1) if rows > 1 else span_h * 0.4
        for r in range(rows):
            for c in range(cols):
                if (r + c) % 2:
                    continue
                cx = -span_w * 0.4 + cell_w * c
                cy = -span_h * 0.4 + cell_h * r
                d = min(cell_w, cell_h) * 0.35
                for da in (0, math.pi / 2):
                    p0 = (cx + math.cos(da) * d, cy + math.sin(da) * d, 0.02)
                    p1 = (cx + math.cos(da + math.pi / 2) * d, cy + math.sin(da + math.pi / 2) * d, 0.02)
                    seg = _filigree_sweep_line(tree, p0, p1, prof, base_x, 300 + r * 50 + c * 10)
                    if seg:
                        parts.append(seg)
        if symmetry == 'MIRROR':
            for r in range(rows):
                cy = -span_h * 0.4 + cell_h * r
                seg = _filigree_sweep_line(
                    tree, (0, cy - cell_h * 0.2, 0.02), (0, cy + cell_h * 0.2, 0.02),
                    prof, base_x, 1800 + r * 30)
                if seg:
                    parts.append(seg)
    return parts



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



def color_node(node, key):
    if key in COLORS:
        node.use_custom_color = True
        node.color = COLORS[key]


# ----------------------------------------------------------------------
# REUSABLE BUILDER HELPERS
# ----------------------------------------------------------------------


def _filigree_sweep_line(tree, p0, p1, prof, base_x, y_off, label="ornament"):
    line = _safe_node(tree, 'GeometryNodeCurvePrimitiveLine', (base_x, y_off))
    if not line or prof is None:
        return None
    try:
        line.inputs['Start'].default_value = tuple(p0)
        line.inputs['End'].default_value = tuple(p1)
    except Exception:
        return None
    sw = _safe_node(tree, 'GeometryNodeCurveToMesh', (base_x + 220, y_off))
    if not sw:
        return None
    _link(tree, line.outputs['Curve'], sw.inputs['Curve'])
    _link(tree, prof.outputs['Curve'], sw.inputs['Profile Curve'])
    try:
        sw.inputs['Fill Caps'].default_value = True
    except Exception:
        pass
    color_node(sw, label)
    return sw.outputs['Mesh']



def _filigree_scurve(tree, prof, cx, cy, span_w, span_h, base_x, y_off, flip=False):
    parts = []
    n = 12
    sign = 1.0 if not flip else -1.0
    pts = []
    for i in range(n + 1):
        t = i / n
        x = cx - span_w * 0.45 + t * span_w * 0.9
        y = cy + sign * span_h * 0.32 * math.sin(t * math.pi)
        pts.append((x, y, 0.02))
    for i in range(len(pts) - 1):
        seg = _filigree_sweep_line(tree, pts[i], pts[i + 1], prof, base_x, y_off - i * 4)
        if seg:
            parts.append(seg)
    return parts




# ---- registered groups (params-as-values) ----
import types as _types

_FILIGREE_PARAMS = {
    "filigree_density": 0.8, "filigree_style": 0, "filigree_ornament_density": 0.5,
}

def _make_props(**extra):
    kv = dict(_FILIGREE_PARAMS)
    kv.update(extra or {})
    return _types.SimpleNamespace(**kv)


def build_filigree_core_group(group_name="MEL_filigree_core"):
    tree, gin, gout = new_geometry_tree(group_name)
    PROPS = _make_props()
    geom = build_filigree_core(tree, PROPS)
    if geom is not None:
        link_sockets(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_filigree_core")
    return tree, gin, gout
register_builder("MEL_filigree_core", build_filigree_core_group,
    "Filigree Core", "Filigree builder (absorbed from monolith).", category="filigree")


def build_filigree_panel_group(group_name="MEL_filigree_panel"):
    tree, gin, gout = new_geometry_tree(group_name)
    PROPS = _make_props()
    geom = build_filigree_panel(tree, PROPS)
    if geom is not None:
        link_sockets(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_filigree_panel")
    return tree, gin, gout
register_builder("MEL_filigree_panel", build_filigree_panel_group,
    "Filigree Panel", "Filigree builder (absorbed from monolith).", category="filigree")


def build_filigree_rail_inset_group(group_name="MEL_filigree_rail_inset"):
    tree, gin, gout = new_geometry_tree(group_name)
    PROPS = _make_props()
    geom = build_filigree_rail_inset(tree, PROPS)
    if geom is not None:
        link_sockets(tree, geom, gout.inputs["Geometry"])
    label_tree(tree, "MEL_filigree_rail_inset")
    return tree, gin, gout
register_builder("MEL_filigree_rail_inset", build_filigree_rail_inset_group,
    "Filigree Rail Inset", "Filigree builder (absorbed from monolith).", category="filigree")
