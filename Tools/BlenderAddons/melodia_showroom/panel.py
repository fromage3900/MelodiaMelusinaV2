# Panel for Melodia Showroom
# Copyright (c) 2026 fromage3900 / Melodia Project
# License: MIT

try:
    import bpy
    from bpy.types import Panel
except Exception:
    bpy = None
    Panel = object


class SHOWROOM_PT_panel(bpy.types.Panel):
    bl_label = "Melodia Showroom"
    bl_idname = "SHOWROOM_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Melodia Showroom"

    def draw(self, context):
        layout = self.layout
        props = context.scene.melodia_showroom

        box = layout.box()
        box.label(text="Pipeline", icon='SEQ_PREVIEW')
        box.prop(props, "preset", text="")
        box.prop(props, "midi_file", text="MIDI Override")

        box = layout.box()
        box.label(text="Render", icon='RENDER_STILL')
        box.prop(props, "resolution_percent")
        box.prop(props, "samples")
        box.prop(props, "transparent")

        row = layout.row()
        row.scale_y = 1.5
        row.operator("melodia_showroom.run_pipeline", icon='PLAY')

        if props.last_report:
            layout.separator()
            box = layout.box()
            for line in str(props.last_report).splitlines():
                box.label(text=line)


classes = (SHOWROOM_PT_panel,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
