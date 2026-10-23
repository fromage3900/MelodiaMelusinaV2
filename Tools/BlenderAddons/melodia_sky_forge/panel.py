# Melodia Sky Forge - N-panel (View3D > Sidebar > Melodia).
# Copyright (c) 2026 fromage3900 / Melodia Project - MIT

from __future__ import annotations

import bpy


class MELSKY_PT_panel(bpy.types.Panel):
    bl_label = "Sky Forge"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Melodia"

    def draw(self, context):
        sky = context.scene.melodia_sky
        col = self.layout.column(align=True)
        col.label(text="Musical procedural skies (FADE-style).", icon="RENDER_STILL")

        col.label(text="1. Theme", icon="NORMALS_FACE")
        col.prop(sky, "theme_id", text="")
        row = col.row(align=True)
        row.operator("melodia_sky.reload_library", icon="FILE_REFRESH")
        row.operator("melodia_sky.apply_theme", icon="CHECKMARK")

        col.separator()
        col.label(text="2. Bake", icon="RENDER_ANIMATION")
        col.prop(sky, "output_dir", text="Dir")
        row = col.row(align=True)
        row.prop(sky, "bake_samples", text="Smp")
        row.prop(sky, "bake_frames", text="Frms")
        col.operator("melodia_sky.bake_equirect", icon="EXPORT")

        col.separator()
        box = col.box()
        box.label(text="EXR + sidecar JSON -> TD / UE.", icon="INFO")
        box.label(text="Presentation only; no gameplay truth.")


def register() -> None:
    bpy.utils.register_class(MELSKY_PT_panel)


def unregister() -> None:
    bpy.utils.unregister_class(MELSKY_PT_panel)
