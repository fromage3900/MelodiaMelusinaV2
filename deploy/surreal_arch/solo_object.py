"""Solo Object local-view operator for Melodia Studio."""

from __future__ import annotations

import bpy


def _active_view3d_context(context):
    """Return the active VIEW_3D override parts needed by view3d.localview."""
    area = getattr(context, "area", None)
    if area is None or area.type != "VIEW_3D":
        return None
    region = next((r for r in area.regions if r.type == "WINDOW"), None)
    space = getattr(context, "space_data", None)
    if space is None or space.type != "VIEW_3D":
        space = next((s for s in area.spaces if s.type == "VIEW_3D"), None)
    if region is None or space is None:
        return None
    return area, region, space


def _is_local_view(space) -> bool:
    local_view = getattr(space, "local_view", None)
    if isinstance(local_view, bool):
        return local_view
    return local_view is not None


class SURREAL_ARCH_OT_solo_object(bpy.types.Operator):
    bl_idname = "surreal_arch.solo_object"
    bl_label = "Solo Object"
    bl_description = (
        "Isolate selected objects in local view. Distinct from Stage Solo Melusina."
    )
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return _active_view3d_context(context) is not None and bool(
            getattr(context, "selected_objects", None)
        )

    def execute(self, context):
        view_ctx = _active_view3d_context(context)
        if view_ctx is None:
            self.report({"ERROR"}, "Solo Object needs an active 3D View")
            return {"CANCELLED"}

        selected = list(context.selected_objects or [])
        if not selected:
            self.report({"WARNING"}, "Select at least one object to use Solo Object")
            return {"CANCELLED"}

        area, region, space = view_ctx
        was_local = _is_local_view(space)
        with context.temp_override(area=area, region=region, space_data=space):
            bpy.ops.view3d.localview(frame_selected=True)

        if was_local:
            self.report({"INFO"}, "Solo Object off")
        else:
            self.report({"INFO"}, f"Solo Object on ({len(selected)} selected)")
        return {"FINISHED"}


SOLO_OBJECT_CLASSES = (SURREAL_ARCH_OT_solo_object,)

