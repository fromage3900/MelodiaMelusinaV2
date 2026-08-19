"""Stats overlay — small viewport HUD with live scene counters.

P2 from DEEPSEEK_HANDOFF_TOGGLEABLES: the original stats_overlay.py had
register/unregister but was never wired into register_overhaul. This version
owns its own draw handler + toggle operator and is registered by integration.
"""

from __future__ import annotations

import bpy
import blf

_handler = None

_FONT_ID = 0
_LINE_H = 18
_START_X = 14
_START_Y = 60


def _draw_stats_overlay():
    ctx = bpy.context
    region = ctx.region
    if not region:
        return
    scene = ctx.scene
    wm = ctx.window_manager

    stats = []
    stats.append(f"Scene: {scene.name}")
    stats.append(f"Frame: {scene.frame_current}/{scene.frame_end}")
    stats.append(f"Objects: {len(bpy.data.objects)}")
    stats.append(f"Meshes: {len(bpy.data.meshes)}")
    stats.append(f"Collections: {len(bpy.data.collections)}")
    stats.append(f"Materials: {len(bpy.data.materials)}")
    stats.append(f"Lights: {len(bpy.data.lights)}")
    stats.append(f"Cameras: {len(bpy.data.cameras)}")
    stats.append(f"Selected: {len(ctx.selected_objects)}")
    active = getattr(ctx, "active_object", None)
    stats.append(f"Active: {active.name if active else '—'}")

    blf.size(_FONT_ID, 12)
    x, y = _START_X, region.height - _START_Y
    for line in stats:
        blf.position(_FONT_ID, x, y, 0)
        blf.draw(_FONT_ID, line)
        y -= _LINE_H


def enable_overlay():
    global _handler
    if _handler is None:
        _handler = bpy.types.SpaceView3D.draw_handler_add(
            _draw_stats_overlay, (), "WINDOW", "POST_PIXEL"
        )


def disable_overlay():
    global _handler
    if _handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_handler, "WINDOW")
        _handler = None


def is_active() -> bool:
    return _handler is not None


class SURREAL_ARCH_OT_stats_overlay_toggle(bpy.types.Operator):
    bl_idname = "surreal_arch.stats_overlay_toggle"
    bl_label = "Toggle Stats Overlay"
    bl_description = "Show/hide the live scene stats HUD in the 3D Viewport"
    bl_options = {"REGISTER"}

    def execute(self, context):
        if is_active():
            disable_overlay()
            self.report({"INFO"}, "Stats overlay OFF")
        else:
            enable_overlay()
            self.report({"INFO"}, "Stats overlay ON")
        return {"FINISHED"}


STATS_OVERLAY_CLASSES = (SURREAL_ARCH_OT_stats_overlay_toggle,)


def register_stats_overlay():
    return list(STATS_OVERLAY_CLASSES)


def unregister_stats_overlay():
    disable_overlay()