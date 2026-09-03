# Panel for Melodia Showroom
# Copyright (c) 2026 fromage3900 / Melodia Project
# License: MIT

try:
    import bpy
    from bpy.types import Panel
    import os, sys
    from pathlib import Path
    try:
        _AR = Path(__file__).resolve().parent.parent
        if str(_AR) not in sys.path:
            sys.path.insert(0, str(_AR))
        from melodia_studio import addon_utils as _au
    except Exception:
        _au = None
except Exception:
    bpy = None
    Panel = object
    _au = None


class SHOWROOM_PT_panel(bpy.types.Panel):
    bl_label = "Melodia Showroom"
    bl_idname = "SHOWROOM_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Melodia"

    def draw(self, context):
        layout = self.layout
        if _au is not None:
            try:
                _au.draw_melodia_header(layout, "Showroom", "Showroom  -  Terrain -> Dress -> Render", icon_key="stage")
            except Exception:
                layout.label(text="*  MELODIA  -  SHOWROOM")
        else:
            layout.label(text="*  MELODIA  -  SHOWROOM")
        props = context.scene.melodia_showroom

        box = layout.box()
        row = box.row()
        row.label(text="P I P E L I N E", icon='SEQ_PREVIEW')
        box.prop(props, "preset", text="")
        box.prop(props, "midi_file", text="MIDI Override")
        box.label(text="Dressing uses real walkable field", icon='CHECKMARK')

        box2 = layout.box()
        box2.label(text="R E N D E R", icon='RENDER_STILL')
        box2.prop(props, "resolution_percent")
        box2.prop(props, "samples")
        box2.prop(props, "transparent")
        if _au is not None:
            try:
                _au.draw_gold_rule(box2)
            except Exception:
                pass

        row = layout.row()
        row.scale_y = 1.5
        if _au is not None:
            try:
                row.operator("melodia_showroom.run_pipeline", text="Run Showroom", **_au.icon_kwargs("generate", 'PLAY'))
            except Exception:
                row.operator("melodia_showroom.run_pipeline", icon='PLAY')
        else:
            row.operator("melodia_showroom.run_pipeline", icon='PLAY')

        if props.last_report:
            layout.separator()
            box = layout.box()
            box.label(text="L A S T   R U N", icon='CHECKMARK')
            for line in str(props.last_report).split(" | "):
                box.label(text=line)


classes = (SHOWROOM_PT_panel,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
