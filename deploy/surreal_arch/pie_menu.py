"""Surreal Architecture radial pie menu — quick trim / UV / export workflow."""

from __future__ import annotations

import bpy


def _has_surreal_mesh(context):
    obj = context.active_object
    return bool(obj and obj.type == "MESH" and hasattr(obj, "surreal_arch_props"))


class SURREAL_ARCH_MT_pie_main(bpy.types.Menu):
    bl_label = "Surreal Architecture"
    bl_idname = "SURREAL_ARCH_MT_pie_main"

    def draw(self, context):
        layout = self.layout
        pie = layout.menu_pie()
        has_props = _has_surreal_mesh(context)

        pie.operator("surreal_arch.generate", text="Generate", icon="SHADERFX")

        if has_props:
            pie.operator("surreal_arch.trim_preset_zen_stone", text="Zen Stone Trim", icon="MOD_BOOLEAN")
        else:
            pie.label(text="Select Surreal mesh", icon="ERROR")

        if has_props:
            pie.operator("surreal_arch.uv_create_edit_proxy", text="UV Edit Proxy", icon="UV")
        else:
            pie.label(text="—", icon="BLANK1")

        if has_props:
            pie.operator("surreal_arch.uv_commit_from_proxy", text="Commit UV (Bake)", icon="UV_DATA")
        else:
            pie.label(text="—", icon="BLANK1")

        pie.operator("surreal_arch.bake_trim_attributes", text="Bake Trim", icon="GROUP_VCOL")
        pie.operator("surreal_arch.export_ue5", text="Export UE5", icon="EXPORT")

        if has_props:
            pie.operator("surreal_arch.spawn_graph_zen_sakura_walk", text="Sakura Walk Chain", icon="OUTLINER_OB_GROUP_INSTANCE")
        else:
            pie.operator("surreal_arch.snap_to_selected", text="Snap", icon="SNAP_VERTEX")

        pie.operator("surreal_arch.plan_spawn_zen_sakura", text="Zen Sakura Plan", icon="WORLD")
        pie.operator("surreal_arch.toggle_snap_overlay", text="Snap Overlay", icon="HIDE_OFF")


class SURREAL_ARCH_OT_pie_menu(bpy.types.Operator):
    bl_idname = "surreal_arch.pie_menu"
    bl_label = "Surreal Architecture Pie"
    bl_options = {"REGISTER"}

    def execute(self, context):
        bpy.ops.wm.call_menu_pie(name=SURREAL_ARCH_MT_pie_main.bl_idname)
        return {"FINISHED"}


def register_pie_menu():
    return SURREAL_ARCH_MT_pie_main, SURREAL_ARCH_OT_pie_menu
