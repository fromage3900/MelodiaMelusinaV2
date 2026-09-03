# Operators for Melodia Pose Audit
# Copyright (c) 2026 fromage3900 / Melodia Project
# License: MIT

import bpy
from bpy.types import Operator
import traceback


COMMON_MELODIA_BONES = [
    "pelvis",
    "spine_01",
    "spine_02",
    "spine_03",
    "neck_01",
    "neck_02",
    "head",
]


class MELODIA_OT_pose_audit(Operator):
    bl_idname = "melodia.pose_audit"
    bl_label = "Audit Rig"
    bl_options = {"REGISTER"}

    def execute(self, context):
        props = context.scene.melodia_pose_audit
        arm = props.target_armature

        if arm is None:
            self.report({"WARNING"}, "Select an armature first.")
            props.last_report = "No armature selected."
            return {"CANCELLED"}

        if arm.type != "ARMATURE":
            self.report({"WARNING"}, "Selected object is not an armature.")
            props.last_report = "Selected object is not an armature."
            return {"CANCELLED"}

        try:
            report = _audit(context, props, arm)
        except Exception:
            self.report({"ERROR"}, "Audit failed; see system console.")
            print(traceback.format_exc())
            props.last_report = "Audit failed. Check system console."
            return {"CANCELLED"}

        text = "\n".join(report)
        props.last_report = f"{len(report)} findings"

        block_name = "Pose Audit"
        if block_name in bpy.data.texts:
            text_block = bpy.data.texts[block_name]
            text_block.clear()
        else:
            text_block = bpy.data.texts.new(block_name)
        text_block.from_string(text)

        self.report({"INFO"}, f"Pose audit complete: {len(report)} findings")
        return {"FINISHED"}


def _audit(context, props, arm):
    findings = []
    bones = [b.name for b in arm.data.bones]
    bone_set = set(bones)
    pose = arm.pose

    findings.append(f"Armature: {arm.name}")
    findings.append(f"Bones: {len(bones)}")

    if props.warn_on_missing_bone:
        missing = [name for name in COMMON_MELODIA_BONES if name not in bone_set]
        if missing:
            findings.append(f"MISSING_BONE: {', '.join(missing)}")

    constraints_by_bone = 0
    for pb in pose.bones:
        for c in pb.constraints:
            constraints_by_bone += 1
            if props.warn_on_pin and _looks_like_pin(c):
                findings.append(
                    f"PIN_CONSTRAINT: {pb.name} -> {c.name} ({c.type})"
                )

    findings.append(f"Constraints scanned: {constraints_by_bone}")
    return findings


def _looks_like_pin(constraint):
    text = " ".join(
        filter(
            None,
            [
                getattr(constraint, "subtarget", ""),
                getattr(constraint, "target", "").get("name", ""),
                getattr(constraint, "pole_target", "").get("name", ""),
            ],
        )
    ).lower()

    pinned = (
        constraint.type in {"COPY_LOCATION", "COPY_ROTATION", "COPY_TRANSFORMS", "IK"}
        or "root" in text
        or "bind" in text
        or "pelvis" in text
    )

    if not pinned:
        return False

    if constraint.type == "IK" and getattr(constraint, "chain_count", 0) > 1:
        return False

    return True


classes = (MELODIA_OT_pose_audit,)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
