# Resonance Loom - N-panel (View3D > Sidebar > Melodia).
# Copyright (c) 2026 fromage3900 / Melodia Project - MIT

from __future__ import annotations

import json

import bpy


class LOOM_PT_panel(bpy.types.Panel):
    bl_label = "Resonance Loom"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Melodia"

    def draw(self, context):
        loom = context.scene.loom
        col = self.layout.column(align=True)
        col.label(text="Author garments that listen to the battle beat.", icon="MOD_PARTICLES")

        col.label(text="1. Beat", icon="PLAY")
        col.prop(loom, "midi_path", text="")
        col.operator("melodia_loom.import_beatgrid", icon="SEQUENCE")
        if loom.beatgrid_loaded:
            row = col.row(align=True)
            row.label(text=f"{loom.bpm:.0f} BPM | density {loom.pattern_density:.2f}")
            try:
                hits = json.loads(loom.lane_hits_json)
                col.label(text="Hits  " + "  ".join(f"{k}:{v}" for k, v in hits.items()))
            except (ValueError, TypeError):
                pass

        col.separator()
        col.label(text="2. Paint", icon="VPAINT_HLT")
        col.operator("melodia_loom.ensure_paint_groups", icon="NEW")
        col.prop(loom, "bake_scale")

        col.separator()
        col.label(text="3. Bake", icon="KEY_HLT")
        col.prop(loom, "lane_strategy", text="Lanes")
        col.operator("melodia_loom.bake_rhythm_keys", icon="KEYINGSET")
        col.operator("melodia_loom.bake_secondary_action", icon="NLA")

        col.separator()
        col.label(text="4. Ship", icon="CHECKMARK")
        col.prop(loom, "cosmetic_id", text="ID")
        col.prop(loom, "skill_id", text="Skill")
        col.operator("melodia_loom.validate_garment", icon="FILE_TICK")
        col.prop(loom, "output_dir", text="Dir")
        col.operator("melodia_loom.export_garment", icon="EXPORT")

        col.separator()
        box = col.box()
        box.label(text="Flourish only - never a gate.", icon="INFO")
        box.label(text="Decision 016: expressive rhythm.")


def register() -> None:
    bpy.utils.register_class(LOOM_PT_panel)


def unregister() -> None:
    bpy.utils.unregister_class(LOOM_PT_panel)
