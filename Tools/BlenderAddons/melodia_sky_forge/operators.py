# Melodia Sky Forge - operators.
# Copyright (c) 2026 fromage3900 / Melodia Project - MIT

from __future__ import annotations

from pathlib import Path

import bpy


class MELSKY_OT_apply_theme(bpy.types.Operator):
    """Apply the selected sky theme to the scene world"""

    bl_idname = "melodia_sky.apply_theme"
    bl_label = "Apply Theme"

    def execute(self, context):
        from . import sky_builder, sky_core

        sky = context.scene.melodia_sky
        try:
            lib = sky_core.load_library()
            theme = sky_core.get_theme(lib, sky.theme_id)
            sky_builder.apply_theme(theme, dome_radius=sky.dome_radius)
        except (OSError, ValueError, RuntimeError, KeyError) as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        self.report({'INFO'}, f"Applied sky theme {sky.theme_id}")
        return {'FINISHED'}


class MELSKY_OT_reload_library(bpy.types.Operator):
    """Reload the sky theme library from disk"""

    bl_idname = "melodia_sky.reload_library"
    bl_label = "Reload Library"

    def execute(self, context):
        from . import sky_core

        try:
            lib = sky_core.load_library()
        except (OSError, ValueError) as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}
        self.report({'INFO'}, f"{len(lib['themes'])} sky themes loaded")
        return {'FINISHED'}


class MELSKY_OT_bake_equirect(bpy.types.Operator):
    """Bake the current sky world to an equirect EXR + TD sidecar JSON"""

    bl_idname = "melodia_sky.bake_equirect"
    bl_label = "Bake Equirect"

    def execute(self, context):
        from . import export, sky_core

        sky = context.scene.melodia_sky
        out_dir = bpy.path.abspath(sky.output_dir)
        theme = None
        try:
            lib = sky_core.load_library()
            theme = sky_core.get_theme(lib, sky.theme_id)
        except (OSError, ValueError, KeyError):
            pass  # bake still runs on the live world; sidecar is skipped
        report = export.bake_equirect(
            Path(out_dir), theme=theme, samples=sky.bake_samples,
            frames=sky.bake_frames,
        )
        if not report.get("ok"):
            self.report({'ERROR'}, report.get("error", "bake failed"))
            return {'CANCELLED'}
        self.report({'INFO'}, f"Baked {report.get('exr')}")
        return {'FINISHED'}


_CLASSES = (MELSKY_OT_apply_theme, MELSKY_OT_reload_library, MELSKY_OT_bake_equirect)


def register() -> None:
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
