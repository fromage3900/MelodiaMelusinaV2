import bpy


class STAGE_PT_panel(bpy.types.Panel):
    """Melodia Stage panel in the 3D View sidebar"""
    bl_label = "Melodia Stage"
    bl_idname = "STAGE_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Melodia Stage"

    def draw(self, context):
        layout = self.layout

        # Status indicator
        has_stage = any(
            obj.name.startswith("MelodiaStage_")
            for obj in bpy.data.objects
        )

        if has_stage:
            layout.label(text="Rig Active", icon='CHECKMARK')
        else:
            layout.label(text="No Rig", icon='INFO')

        layout.separator()

        # Main actions
        col = layout.column(align=True)
        col.scale_y = 1.5

        col.operator(
            "melodia_stage.stage_selected",
            text="Stage Selected",
            icon='CAMERA_DATA'
        )

        col.separator()

        col.operator(
            "melodia_stage.animate_spin",
            text="Animate Spin",
            icon='ANIM'
        )

        col.operator(
            "melodia_stage.render_animation",
            text="Render Spin",
            icon='RENDER_ANIMATION'
        )

        layout.separator()

        # Utility row
        row = layout.row()
        row.operator(
            "melodia_stage.clear_stage",
            text="Clear Stage",
            icon='TRASH'
        )


def register():
    bpy.utils.register_class(STAGE_PT_panel)


def unregister():
    bpy.utils.unregister_class(STAGE_PT_panel)
