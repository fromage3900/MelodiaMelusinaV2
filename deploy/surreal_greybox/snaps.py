"""Snap point load/save helpers — extracted greybox assembly utilities."""

from __future__ import annotations

import json

_M = None


def bind(monolith):
    global _M
    _M = monolith


def load_snap_points(obj):
    raw = obj.get("surreal_snap_points")
    if not raw:
        return []
    try:
        return json.loads(raw) if isinstance(raw, str) else list(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []


def snap_world_point(obj, pt):
    from mathutils import Vector
    return obj.matrix_world @ Vector(pt["position"])


def snap_world_dir(obj, pt):
    from mathutils import Vector
    d = Vector(pt["direction"])
    return (obj.matrix_world.to_3x3() @ d).normalized()


def attach_to_monolith(monolith):
    bind(monolith)
    monolith._gb_load_snap_points = load_snap_points
    monolith._gb_snap_world_point = snap_world_point
    monolith._gb_snap_world_dir = snap_world_dir
