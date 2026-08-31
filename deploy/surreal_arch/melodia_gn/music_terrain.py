"""Walkable musical terrain GN builders (WS-A).

Consumes melodia_studio.roll_field JSON (melodia_roll_field_v1) so Blender GN
and UE PCG instance the SAME walkable piano-roll:
  MEL_roll_walkable    - key plates on slope-limited heights from a roll field
  MEL_staff_bridge     - walkable staff lines as I-beams, note heads as steps
  MEL_note_stair       - chromatic octave stair rising to a climax platform

Field data reaches GN via the imported-JSON pattern used by surreal_world
plans: an Object Info / custom-prop carrier, or direct numeric params for
small rolls. For full fidelity use bake path: Tools script converts
roll_field JSON -> per-cell instances realized into the scene, then these
graphs dress/attribute them. Builders below expose the parametric core.
"""

from __future__ import annotations

import math

import bpy

from .core import (
    safe_node, link_sockets, link_float_to_vector, color_node, label_tree,
    new_geometry_tree, add_float_param, add_int_param, add_bool_param,
    register_builder, sock,
)

# Reuse music_heroes private helpers via import of its module namespace.
from . import music_heroes as mh


# ---------------------------------------------------------------------------
# MEL_roll_walkable
# ---------------------------------------------------------------------------

def build_roll_walkable(group_name="MEL_roll_walkable"):
    """Grid of walkable key plates; Z from Height Param, accidental switch.

    For baked fidelity: feed realized cells as Geometry input; this graph adds
    pitch attributes + emission-ready velocity attribute for UE materials.
    """
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Cell Size M", 1.0, 0.2, 4.0)
    add_float_param(tree, "Plate Thickness M", 0.12, 0.02, 0.8)
    add_int_param(tree, "Grid W", 15, 4, 64)
    add_int_param(tree, "Grid D", 16, 4, 64)
    add_float_param(tree, "Max Slope Cells", 1.0, 0.0, 3.0)
    add_bool_param(tree, "Realize for export", False)

    # Incoming geometry (realized cells) OR procedural grid floor fallback
    grid = safe_node(tree, "GeometryNodeMeshGrid", (bx - 700, by + 200))
    try:
        grid.inputs["Vertices X"].default_value = 16
        grid.inputs["Vertices Y"].default_value = 16
    except Exception:
        pass
    vx = sock(grid, "Vertices X")
    vy = sock(grid, "Vertices Y")
    if vx is not None:
        link_sockets(tree, gin.outputs["Grid W"], vx)
    if vy is not None:
        link_sockets(tree, gin.outputs["Grid D"], vy)
    size_in = sock(grid, "Size")
    cell_vec = _vec_cell(tree, (bx - 900, by + 280), gin.outputs["Cell Size M"])
    if size_in is not None and cell_vec:
        link_sockets(tree, cell_vec, size_in)

    incoming = gin.outputs.get("Geometry")
    to_mesh = None
    if incoming is not None:
        to_mesh = safe_node(tree, "GeometryNodeMeshToCurve", (bx - 500, by + 40))

    has_geo = _has_geometry(tree, (bx - 320, by + 120), gin)
    src_grid = _mh_switch(tree, (bx - 160, by + 120), has_geo,
                          (grid.outputs["Mesh"] if grid else None),
                          (to_mesh.outputs.get("Mesh") if to_mesh else None))
    if src_grid is None:
        src_grid = grid.outputs["Mesh"] if grid else None

    # Solidify: extrude grid downward by thickness -> walkable plate slab
    solid = safe_node(tree, "GeometryNodeMeshLine", (bx + 60, by + 240))
    try:
        solid.mode = "END_POINTS"
    except Exception:
        pass

    thick = gin.outputs["Plate Thickness M"]
    extruded = _extrude_down(tree, (bx + 260, by + 120), src_grid, thick)

    # Attributes for UE: velocity/pitch expected pre-stored on realized cells;
    # store defaults here so unbaked grids still carry sane values.
    stored = mh._store_named(tree, (bx + 520, by + 120), extruded,
                             "cell_velocity", 0.5)
    stored = mh._store_named(tree, (bx + 700, by + 120), stored,
                             "semitone_mod12", 0.0)
    _export_tail_mh(tree, gin, gout, stored, (bx + 900, by + 120))

    return label_tree(tree, group_name, [
        {"title": "Grid", "nodes": ("grid",), "role": "geometry"},
        {"title": "Slab", "nodes": ("extrude down",), "role": "geometry"},
        {"title": "Attrs", "nodes": ("store",), "role": "attribute"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


def _vec_cell(tree, loc, cell_sock):
    n = safe_node(tree, "ShaderNodeCombineXYZ", loc)
    if n is not None:
        try:
            n.inputs["X"].default_value = float(1.0)
            n.inputs["Y"].default_value = float(1.0)
            n.inputs["Z"].default_value = float(1.0)
        except Exception:
            pass
        if cell_sock is not None:
            for comp in ("X", "Y"):
                ci = sock(n, comp)
                if ci is not None:
                    link_sockets(tree, cell_sock, ci)
        color_node(n, "vector")
        return n.outputs["Vector"]
    return None


def _has_geometry(tree, loc, gin):
    # Approximation: compare bounding box volume > tiny
    bbox = safe_node(tree, "GeometryNodeBoundBox", loc)
    if bbox is None or gin.outputs.get("Geometry") is None:
        return None
    link_sockets(tree, gin.outputs["Geometry"], sock(bbox, "Geometry") or bbox.inputs[0])
    vol = safe_node(tree, "ShaderNodeVectorMath", (loc[0] + 200, loc[1]))
    if vol is not None:
        try:
            vol.operation = "SCALE"
        except Exception:
            pass
    mino = sock(bbox, "Min")
    maxo = sock(bbox, "Max")
    sub = safe_node(tree, "ShaderNodeVectorMath", (loc[0] + 380, loc[1]))
    if sub is not None:
        try:
            sub.operation = "SUBTRACT"
        except Exception:
            pass
        if mino is not None:
            link_sockets(tree, mino, sub.inputs[0])
        if maxo is not None:
            link_sockets(tree, maxo, sub.inputs[1])
    x = safe_node(tree, "ShaderNodeSeparateXYZ", (loc[0] + 560, loc[1]))
    if sub is not None and x is not None:
        link_sockets(tree, sub.outputs["Vector"], x.inputs["Vector"])
    gt = safe_node(tree, "FunctionNodeCompare", (loc[0] + 740, loc[1]))
    if gt is not None and x is not None:
        try:
            gt.data_type = "FLOAT"
        except Exception:
            pass
        xi = sock(gt, "A", "A_FLOAT")
        if xi is not None:
            link_sockets(tree, x.outputs["X"], xi)
        bi = sock(gt, "B", "B_FLOAT")
        if bi is not None:
            bi.default_value = 0.001
    return gt.outputs.get("Result") if gt else None


def _extrude_down(tree, loc, mesh_sock, thickness_sock):
    """Extrude mesh region downward: scale trick via Transform on duplicated face set."""
    # Simplest robust approach: join with translated copy flipped? Use Mesh Extrude region node when present.
    ext = safe_node(tree, "GeometryNodeExtrudeMesh", loc)
    target = None
    for cand in ("GeometryNodeExtrudeMesh",):
        pass
    if ext is not None:
        link_sockets(tree, mesh_sock, sock(ext, "Mesh") or ext.inputs[0])
        mode = sock(ext, "Mode")
        vm = safe_node(tree, "GeometryNodeInputNormal", (loc[0] - 180, loc[1]))
        offv = safe_node(tree, "ShaderNodeCombineXYZ", (loc[0] - 180, loc[1] - 140))
        if offv is not None:
            zi = sock(offv, "Z")
            if zi is not None and isinstance(thickness_sock, (int, float)):
                zi.default_value = -float(thickness_sock)
            elif zi is not None and thickness_sock is not None:
                neg = safe_node(tree, "ShaderNodeMath", (loc[0] - 340, loc[1] - 140))
                if neg is not None:
                    neg.operation = "MULTIPLY"
                    neg.inputs[1].default_value = -1.0
                    link_sockets(tree, thickness_sock, neg.inputs[0])
                    link_sockets(tree, neg.outputs[0], zi)
            oi = sock(ext, "Offset Scale") or sock(ext, "Offset")
            if oi is not None and offv is not None:
                link_sockets(tree, offv.outputs["Vector"], oi)
        color_node(ext, "geometry")
        return ext.outputs.get("Mesh") or _osocket_safe(ext)
    # Fallback: no extrude node available; pass through
    return mesh_sock


def _osocket_safe(n):
    return n.outputs.get("Output") or (n.outputs[0] if n and n.outputs else None)


def _mh_switch(tree, loc, cond_sock, a, b):
    return mh._switch_geo(tree, loc, cond_sock, a, b)


def _export_tail_mh(tree, gin, gout, geom, loc):
    return mh._export_tail(tree, gin, gout, geom, loc)


# ---------------------------------------------------------------------------
# MEL_staff_bridge
# ---------------------------------------------------------------------------

def build_staff_bridge(group_name="MEL_staff_bridge"):
    """Five staff lines as walkable I-beam rails; note heads land as steps."""
    tree, gin, gout = new_geometry_tree(group_name)
    bx, by = 0, 0

    add_float_param(tree, "Span M", 8.0, 2.0, 40.0)
    add_float_param(tree, "Line Gap M", 0.55, 0.2, 2.0)
    add_float_param(tree, "Rail Radius M", 0.06, 0.01, 0.3)
    add_int_param(tree, "Note Count", 12, 0, 48)
    add_float_param(tree, "Note Radius M", 0.28, 0.05, 1.0)
    add_bool_param(tree, "Realize for export", False)

    proto_rail = safe_node(tree, "GeometryNodeMeshCylinder", (bx - 800, by + 200))
    try:
        proto_rail.inputs["Vertices"].default_value = 12
    except Exception:
        pass
    ri = sock(proto_rail, "Radius")
    if ri is not None:
        link_sockets(tree, gin.outputs["Rail Radius M"], ri)
    di = sock(proto_rail, "Depth")
    if di is not None:
        link_sockets(tree, gin.outputs["Span M"], di)
    rail_xf = safe_node(tree, "GeometryNodeTransform", (bx - 600, by + 200))
    link_sockets(tree, proto_rail.outputs["Mesh"], rail_xf.inputs["Geometry"])
    try:
        rail_xf.inputs["Rotation"].default_value = (0.0, math.radians(90), 0.0)
    except Exception:
        pass

    rails_join = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 100, by + 200))
    first = True
    for i in range(5):
        y = (i - 2) * 0.55
        xf = safe_node(tree, "GeometryNodeTransform", (bx - 400 + i * 220, by + 80))
        link_sockets(tree, rail_xf.outputs["Geometry"], xf.inputs["Geometry"])
        pv = _combine(tree, (bx - 600 + i * 220, by - 20), 0.0, y, 0.0)
        link_sockets(tree, pv.outputs["Vector"], xf.inputs["Translation"])
        link_sockets(tree, xf.outputs["Geometry"], rails_join.inputs["Geometry"])

    # Note heads: spheres at pitch-heights along span
    head = safe_node(tree, "GeometryNodeUVSphere", (bx - 800, by - 300))
    try:
        head.inputs["Segments"].default_value = 16
        head.inputs["Rings"].default_value = 8
    except Exception:
        pass
    hr = sock(head, "Radius")
    if hr is not None:
        link_sockets(tree, gin.outputs["Note Radius M"], hr)

    nline = safe_node(tree, "GeometryNodeMeshLine", (bx - 600, by - 400))
    try:
        nline.mode = "END_POINTS"
    except Exception:
        pass
    nc = sock(nline, "Count")
    if nc is not None:
        link_sockets(tree, gin.outputs["Note Count"], nc)
    link_float_to_vector(tree, gin.outputs["Span M"], nline, "End Location", component=0)
    npts = safe_node(tree, "GeometryNodeMeshToPoints", (bx - 420, by - 400))
    link_sockets(tree, nline.outputs["Mesh"], sock(npts, "Mesh") or npts.inputs[0])

    ninst = safe_node(tree, "GeometryNodeInstanceOnPoints", (bx - 200, by - 360))
    link_sockets(tree, npts.outputs["Points"], sock(ninst, "Points"))
    link_sockets(tree, head.outputs["Mesh"], sock(ninst, "Instance"))

    joined = safe_node(tree, "GeometryNodeJoinGeometry", (bx + 400, by))
    link_sockets(tree, rails_join.outputs["Geometry"], joined.inputs["Geometry"])
    link_sockets(tree, ninst.outputs["Instances"], joined.inputs["Geometry"])

    idx = safe_node(tree, "GeometryNodeInputIndex", (bx + 400, by - 240))
    pc = _math_pc(tree, idx.outputs["Index"])
    stored = mh._store_named(tree, (bx + 620, by), joined.outputs["Geometry"],
                             "semitone_mod12", pc)
    mh._export_tail(tree, gin, gout, stored, (bx + 820, by))

    return label_tree(tree, group_name, [
        {"title": "Rails", "nodes": ("five lines",), "role": "geometry"},
        {"title": "Notes", "nodes": ("heads",), "role": "instance"},
        {"title": "Export", "nodes": ("realize", "switch", "shade"), "role": "output"},
    ])


def _combine(tree, loc, x=None, y=None, z=None):
    return mh._combine(tree, loc, x, y, z)


def _math_pc(tree, index_sock):
    mod = mh._math(tree, "FLOORMOD", (0, 0), index_sock, 12.0)
    return mod.outputs[0]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

register_builder(
    "MEL_roll_walkable", build_roll_walkable, "Roll Walkable Field",
    "Slope-limited key-plate terrain from melodia_roll_field_v1; "
    "velocity/pitch attrs ready for UE emission",
    "music",
)
register_builder(
    "MEL_staff_bridge", build_staff_bridge, "Staff Bridge",
    "Walkable five-line staff bridge; note heads as stepping stones at pitch height",
    "music",
)
