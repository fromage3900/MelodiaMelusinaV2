"""Greybox primitive GN helpers — extracted from monolith for maintainability."""

from __future__ import annotations

_M = None


def bind(monolith):
    """Bind monolith node helpers (_safe_node, _link, color_node)."""
    global _M
    _M = monolith


def _require():
    if _M is None:
        raise RuntimeError("surreal_greybox.primitives not bound — call bind(monolith) at register")


def gb_box(tree, size, loc_xyz, x, y, label="level"):
    _require()
    cube = _M._safe_node(tree, "GeometryNodeMeshCube", (x, y))
    if cube is None:
        return None
    try:
        cube.inputs["Size"].default_value = size
    except Exception:
        pass
    _M.color_node(cube, label)
    tr = _M._safe_node(tree, "GeometryNodeTransform", (x + 200, y))
    if tr is None:
        return cube.outputs["Mesh"]
    try:
        tr.inputs["Translation"].default_value = loc_xyz
    except Exception:
        pass
    _M._link(tree, cube.outputs["Mesh"], tr.inputs["Geometry"])
    _M.color_node(tr, label)
    return tr.outputs["Geometry"]


def gb_box_node(tree, size, loc_xyz, rot_xyz, x, y, label="level"):
    _require()
    cube = _M._safe_node(tree, "GeometryNodeMeshCube", (x, y))
    if cube is None:
        return None
    try:
        cube.inputs["Size"].default_value = size
    except Exception:
        pass
    _M.color_node(cube, label)
    tr = _M._safe_node(tree, "GeometryNodeTransform", (x + 200, y))
    if tr is None:
        return cube.outputs["Mesh"]
    try:
        tr.inputs["Translation"].default_value = loc_xyz
        tr.inputs["Rotation"].default_value = rot_xyz
    except Exception:
        pass
    _M._link(tree, cube.outputs["Mesh"], tr.inputs["Geometry"])
    _M.color_node(tr, label)
    return tr.outputs["Geometry"]


def gb_join(tree, parts, x, y=0, label="output"):
    _require()
    parts = [p for p in parts if p is not None]
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0]
    join = _M._safe_node(tree, "GeometryNodeJoinGeometry", (x, y))
    if join is None:
        return parts[0]
    for p in parts:
        _M._link(tree, p, join.inputs["Geometry"])
    _M.color_node(join, label)
    return join.outputs["Geometry"]


def gb_bool_diff(tree, base_geom, cutters, x, y=0):
    _require()
    cutters = [c for c in cutters if c is not None]
    if base_geom is None or not cutters:
        return base_geom
    boolean = _M._safe_node(tree, "GeometryNodeMeshBoolean", (x, y))
    if boolean is None:
        return base_geom
    try:
        boolean.operation = "DIFFERENCE"
    except Exception:
        pass
    linked = False
    try:
        _M._link(tree, base_geom, boolean.inputs["Mesh 1"])
        for c in cutters:
            _M._link(tree, c, boolean.inputs["Mesh 2"])
        linked = True
    except Exception:
        linked = False
    if not linked:
        try:
            _M._link(tree, base_geom, boolean.inputs["Mesh"])
            for c in cutters:
                _M._link(tree, c, boolean.inputs["Mesh"])
        except Exception:
            return base_geom
    _M.color_node(boolean, "level")
    try:
        return boolean.outputs["Mesh"]
    except Exception:
        return base_geom


def gb_trim_mode(props):
    return getattr(props, "gb_trim_mode", "RECESS")


def gb_trim_depth(props, wall_t):
    return max(0.005, getattr(props, "gb_trim_recess", 0.04))


def attach_to_monolith(monolith):
    """Replace monolith _gb_* primitives with package implementations."""
    bind(monolith)
    monolith._gb_box = gb_box
    monolith._gb_box_node = gb_box_node
    monolith._gb_join = gb_join
    monolith._gb_bool_diff = gb_bool_diff
    monolith._gb_trim_mode = gb_trim_mode
    monolith._gb_trim_depth = gb_trim_depth
