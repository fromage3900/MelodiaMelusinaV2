"""Viewport snap overlay draw handler."""

from __future__ import annotations

import bpy
import gpu
from gpu_extras.batch import batch_for_shader

_handler = None
_colors = {
    "WALL": (1.0, 0.45, 0.1, 0.9),
    "DOOR": (0.2, 0.5, 1.0, 0.9),
    "FLOOR": (0.2, 0.85, 0.3, 0.9),
    "CORNER": (1.0, 0.85, 0.1, 0.9),
    "TRACERY": (0.75, 0.6, 1.0, 0.9),
    "BUTTRESS": (0.6, 0.6, 0.65, 0.9),
    "BAY": (0.9, 0.7, 0.5, 0.9),
}


def _draw_snap_overlay():
    import json
    from mathutils import Vector
    ctx = bpy.context
    region = ctx.region
    rv3d = ctx.region_data
    if not region or not rv3d:
        return
    shader = gpu.shader.from_builtin("UNIFORM_COLOR")
    for obj in ctx.selected_objects:
        raw = obj.get("surreal_snap_points")
        if not raw:
            continue
        try:
            pts = json.loads(raw) if isinstance(raw, str) else list(raw)
        except (TypeError, ValueError):
            continue
        for pt in pts:
            wp = obj.matrix_world @ Vector(pt["position"])
            wd = (obj.matrix_world.to_3x3() @ Vector(pt["direction"])).normalized()
            col = _colors.get(pt.get("type", "WALL"), (1, 1, 1, 0.8))
            end = wp + wd * 0.35
            coords = [tuple(wp), tuple(end)]
            batch = batch_for_shader(shader, "LINES", {"pos": coords})
            shader.bind()
            shader.uniform_float("color", col)
            batch.draw(shader)


def enable_overlay():
    global _handler
    if _handler is None:
        _handler = bpy.types.SpaceView3D.draw_handler_add(
            _draw_snap_overlay, (), "WINDOW", "POST_VIEW"
        )


def disable_overlay():
    global _handler
    if _handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_handler, "WINDOW")
        _handler = None
