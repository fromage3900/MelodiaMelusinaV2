# Properties / operator state for Melodia Pose Audit
# Copyright (c) 2026 fromage3900 / Melodia Project
# License: MIT

import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, StringProperty


class MELODIA_POSE_AUDIT_Props(bpy.types.PropertyGroup):
    target_armature: bpy.props.PointerProperty(
        name="Armature",
        type=bpy.types.Object,
        description="Armature to audit",
        poll=lambda self, obj: obj.type == "ARMATURE",
    )
    max_frames: IntProperty(
        name="Max Frames",
        default=24,
        min=1,
        max=120,
        description="Cap baked frames when testing IK/pose locks",
    )
    tolerance: FloatProperty(
        name="Tolerance",
        default=0.0001,
        min=1e-6,
        max=0.1,
        description="Numeric comparison epsilon",
    )
    warn_on_pin: BoolProperty(
        name="Warn on Pinned Constraints",
        default=True,
        description="Flag constraints that pin control to bind",
    )
    warn_on_missing_bone: BoolProperty(
        name="Warn on Missing Spine/Neck",
        default=True,
        description="Warn when common Melodia rig bones are missing",
    )
    last_report: StringProperty(
        name="Last Report",
        default="No audit yet",
    )


classes = (MELODIA_POSE_AUDIT_Props,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.melodia_pose_audit = bpy.props.PointerProperty(type=MELODIA_POSE_AUDIT_Props)


def unregister():
    del bpy.types.Scene.melodia_pose_audit
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
