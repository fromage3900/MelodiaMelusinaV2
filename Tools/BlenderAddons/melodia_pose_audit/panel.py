# Panel for Melodia Pose Audit
# Copyright (c) 2026 fromage3900 / Melodia Project
# License: MIT

import bpy
from bpy.types import Panel


class MELODIA_PT_pose_audit(Panel):
    bl_label = "Melodia Pose Audit"
    bl_idname = "MELODIA_PT_pose_audit"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Pose Audit"

    def draw(self, context):
        layout = self.layout
        props = context.scene.melodia_pose_audit

        layout.prop(props, "target_armature")
        layout.prop(props, "warn_on_missing_bone")
        layout.prop(props, "warn_on_pin")
        layout.prop(props, "tolerance")

        row = layout.row()
        row.scale_y = 1.5
        row.operator("melodia.pose_audit", icon="VIEWZOOM")

        layout.separator()
        layout.label(text="Last Report:")
        box = layout.box()
        for line in str(props.last_report).splitlines():
            box.label(text=line)


classes = (MELODIA_PT_pose_audit,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
