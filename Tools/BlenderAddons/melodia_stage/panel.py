import bpy
import os, sys
from pathlib import Path

try:
    _ADDONS_ROOT = Path(__file__).resolve().parent.parent
    if str(_ADDONS_ROOT) not in sys.path:
        sys.path.insert(0, str(_ADDONS_ROOT))
    from melodia_studio import addon_utils as _au
except Exception:
    _au = None


class STAGE_PT_panel(bpy.types.Panel):
    """Melodia Stage - turntable, bespoke chrome"""
    bl_label = "Melodia Stage"
    bl_idname = "STAGE_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Melodia"

    def draw(self, context):
        layout = self.layout
        if _au is not None:
            try:
                _au.draw_melodia_header(layout, "Stage", "Turntable  -  Portfolio Lighting", icon_key="stage")
            except Exception:
                layout.label(text="*  MELODIA  -  STAGE")
        else:
            layout.label(text="*  MELODIA  -  STAGE")

        has_stage = any(obj.name.startswith("MelodiaStage_") for obj in bpy.data.objects)
        box = layout.box()
        if has_stage:
            box.label(text="R I G   A C T I V E", icon='CHECKMARK')
        else:
            box.label(text="N O   R I G", icon='INFO')
        if _au is not None:
            try:
                _au.draw_gold_rule(box)
            except Exception:
                pass

        box2 = layout.box()
        box2.label(text="C A P T U R E", icon='CAMERA_DATA')
        col = box2.column(align=True)
        col.scale_y = 1.4
        if _au is not None:
            try:
                col.operator("melodia_stage.stage_selected", text="Stage Selected", **_au.icon_kwargs("stage", 'CAMERA_DATA'))
            except Exception:
                col.operator("melodia_stage.stage_selected", text="Stage Selected", icon='CAMERA_DATA')
        else:
            col.operator("melodia_stage.stage_selected", text="Stage Selected", icon='CAMERA_DATA')
        col.separator()
        col.operator("melodia_stage.animate_spin", text="Animate Spin", icon='ANIM')
        col.operator("melodia_stage.render_animation", text="Render Spin", icon='RENDER_ANIMATION')

        row = layout.row()
        row.scale_y = 1.05
        row.operator("melodia_stage.clear_stage", text="Clear Stage", icon='TRASH')


def register():
    bpy.utils.register_class(STAGE_PT_panel)


def unregister():
    bpy.utils.unregister_class(STAGE_PT_panel)
