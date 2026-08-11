"""UV / trimsheet operators registered by integration."""

from __future__ import annotations

import bpy

from . import uv_workflow


def _poll_surreal_mesh(cls, context):
    obj = context.active_object
    return obj and obj.type == "MESH" and hasattr(obj, "surreal_arch_props")


class SURREAL_ARCH_OT_uv_create_edit_proxy(bpy.types.Operator):
    bl_idname = "surreal_arch.uv_create_edit_proxy"
    bl_label = "Create UV Edit Proxy"
    bl_description = (
        "Duplicate evaluated geometry for MioUV / UVPackmaster / manual unwrap "
        "without applying modifiers on the source"
    )
    bl_options = {"REGISTER", "UNDO"}

    poll = classmethod(_poll_surreal_mesh)

    def execute(self, context):
        source = context.active_object
        proxy, msg = uv_workflow.create_uv_edit_proxy(context, source)
        if proxy is None:
            self.report({"ERROR"}, msg)
            return {"CANCELLED"}
        bpy.ops.object.select_all(action="DESELECT")
        proxy.select_set(True)
        context.view_layer.objects.active = proxy
        self.report({"INFO"}, msg)
        return {"FINISHED"}


class SURREAL_ARCH_OT_uv_commit_from_proxy(bpy.types.Operator):
    bl_idname = "surreal_arch.uv_commit_from_proxy"
    bl_label = "Commit UV from Proxy"
    bl_description = (
        "Copy UV from proxy onto source; bakes mesh when topology differs (removes GN modifier)"
    )
    bl_options = {"REGISTER", "UNDO"}

    poll = classmethod(_poll_surreal_mesh)

    def execute(self, context):
        source = context.active_object
        proxy = uv_workflow.find_proxy_for_source(source)
        if proxy is None:
            proxy = context.active_object
            source = uv_workflow.find_source_for_proxy(proxy)
        if source is None or proxy is None:
            self.report({"WARNING"}, "No UV proxy linked — create one first")
            return {"CANCELLED"}
        ok, msg = uv_workflow.commit_uv_from_proxy(context, source, proxy)
        if not ok:
            self.report({"ERROR"}, msg)
            return {"CANCELLED"}
        bpy.ops.object.select_all(action="DESELECT")
        source.select_set(True)
        context.view_layer.objects.active = source
        self.report({"INFO"}, msg)
        return {"FINISHED"}


class SURREAL_ARCH_OT_uv_remove_proxy(bpy.types.Operator):
    bl_idname = "surreal_arch.uv_remove_proxy"
    bl_label = "Remove UV Edit Proxy"
    bl_options = {"REGISTER", "UNDO"}

    poll = classmethod(_poll_surreal_mesh)

    def execute(self, context):
        uv_workflow.remove_uv_proxy(context, context.active_object)
        self.report({"INFO"}, "UV proxy removed")
        return {"FINISHED"}


class SURREAL_ARCH_OT_trim_preset_architectural(bpy.types.Operator):
    bl_idname = "surreal_arch.trim_preset_architectural"
    bl_label = "Architectural Trim + UV"
    bl_options = {"REGISTER", "UNDO"}

    poll = classmethod(_poll_surreal_mesh)

    def execute(self, context):
        props = context.active_object.surreal_arch_props
        uv_workflow.apply_trim_preset(props, "ARCHITECTURAL")
        return bpy.ops.surreal_arch.generate()


class SURREAL_ARCH_OT_trim_preset_modular(bpy.types.Operator):
    bl_idname = "surreal_arch.trim_preset_modular"
    bl_label = "Modular Tile Trim"
    bl_options = {"REGISTER", "UNDO"}

    poll = classmethod(_poll_surreal_mesh)

    def execute(self, context):
        props = context.active_object.surreal_arch_props
        uv_workflow.apply_trim_preset(props, "MODULAR_TILE")
        return bpy.ops.surreal_arch.generate()


class SURREAL_ARCH_OT_trim_preset_scifi(bpy.types.Operator):
    bl_idname = "surreal_arch.trim_preset_scifi"
    bl_label = "Sci-Fi Panel Trim"
    bl_options = {"REGISTER", "UNDO"}

    poll = classmethod(_poll_surreal_mesh)

    def execute(self, context):
        props = context.active_object.surreal_arch_props
        uv_workflow.apply_trim_preset(props, "SCI_FI_PANEL")
        return bpy.ops.surreal_arch.generate()


class SURREAL_ARCH_OT_trim_preset_zen_wood(bpy.types.Operator):
    bl_idname = "surreal_arch.trim_preset_zen_wood"
    bl_label = "Zen Wood Trim + UV"
    bl_options = {"REGISTER", "UNDO"}

    poll = classmethod(_poll_surreal_mesh)

    def execute(self, context):
        props = context.active_object.surreal_arch_props
        uv_workflow.apply_trim_preset(props, "ZEN_WOOD")
        return bpy.ops.surreal_arch.generate()


class SURREAL_ARCH_OT_trim_preset_zen_stone(bpy.types.Operator):
    bl_idname = "surreal_arch.trim_preset_zen_stone"
    bl_label = "Zen Stone Trim + UV"
    bl_options = {"REGISTER", "UNDO"}

    poll = classmethod(_poll_surreal_mesh)

    def execute(self, context):
        props = context.active_object.surreal_arch_props
        uv_workflow.apply_trim_preset(props, "ZEN_STONE")
        return bpy.ops.surreal_arch.generate()


class SURREAL_ARCH_OT_open_uv_editor(bpy.types.Operator):
    bl_idname = "surreal_arch.open_uv_editor"
    bl_label = "Open UV Editor"
    bl_options = {"REGISTER"}

    def execute(self, context):
        for window in context.window_manager.windows:
            screen = window.screen
            for area in screen.areas:
                if area.type == "IMAGE_EDITOR":
                    area.ui_type = "UV"
                    with context.temp_override(window=window, screen=screen, area=area):
                        pass
                    self.report({"INFO"}, "UV Editor ready")
                    return {"FINISHED"}
        self.report({"INFO"}, "Add an Image Editor area and set mode to UV")
        return {"FINISHED"}


def _invoke_addon_op(module_name, keywords=()):
    """Best-effort invoke of a third-party UV addon operator by name substring."""
    mod = getattr(bpy.ops, module_name, None)
    if mod is None:
        return None
    for attr in sorted(dir(mod)):
        if attr.startswith("_"):
            continue
        low = attr.lower()
        if not any(k in low for k in keywords):
            continue
        try:
            op = getattr(mod, attr)
            op.get_rna_type()
            op()
            return f"{module_name}.{attr}"
        except Exception:
            continue
    return None


class SURREAL_ARCH_OT_uv_invoke_miouv(bpy.types.Operator):
    bl_idname = "surreal_arch.uv_invoke_miouv"
    bl_label = "MioUV Pack (proxy)"
    bl_description = "Create UV edit proxy if needed, then invoke MioUV pack operator"
    bl_options = {"REGISTER", "UNDO"}

    poll = classmethod(_poll_surreal_mesh)

    def execute(self, context):
        from .capabilities import is_available

        if not is_available("miouv"):
            self.report({"ERROR"}, "MioUV addon not detected")
            return {"CANCELLED"}
        source = context.active_object
        proxy = uv_workflow.find_proxy_for_source(source)
        if proxy is None:
            proxy, msg = uv_workflow.create_uv_edit_proxy(context, source)
            if proxy is None:
                self.report({"ERROR"}, msg)
                return {"CANCELLED"}
            bpy.ops.object.select_all(action="DESELECT")
            proxy.select_set(True)
            context.view_layer.objects.active = proxy
        invoked = _invoke_addon_op("miouv", ("pack", "unwrap", "island"))
        if not invoked:
            self.report({"WARNING"}, "MioUV installed but no pack operator found — use UV Editor manually")
            return {"CANCELLED"}
        self.report({"INFO"}, f"Invoked {invoked}")
        return {"FINISHED"}


class SURREAL_ARCH_OT_uv_invoke_uvpackmaster(bpy.types.Operator):
    bl_idname = "surreal_arch.uv_invoke_uvpackmaster"
    bl_label = "UVPackmaster Pack (proxy)"
    bl_description = "Create UV edit proxy if needed, then invoke UVPackmaster pack"
    bl_options = {"REGISTER", "UNDO"}

    poll = classmethod(_poll_surreal_mesh)

    def execute(self, context):
        from .capabilities import is_available

        if not is_available("uvpackmaster"):
            self.report({"ERROR"}, "UVPackmaster addon not detected")
            return {"CANCELLED"}
        source = context.active_object
        proxy = uv_workflow.find_proxy_for_source(source)
        if proxy is None:
            proxy, msg = uv_workflow.create_uv_edit_proxy(context, source)
            if proxy is None:
                self.report({"ERROR"}, msg)
                return {"CANCELLED"}
            bpy.ops.object.select_all(action="DESELECT")
            proxy.select_set(True)
            context.view_layer.objects.active = proxy
        for mod_name in ("uvpackmaster3", "uvpackmaster2"):
            invoked = _invoke_addon_op(mod_name, ("pack",))
            if invoked:
                self.report({"INFO"}, f"Invoked {invoked}")
                return {"FINISHED"}
        self.report({"WARNING"}, "UVPackmaster installed but pack operator not found")
        return {"CANCELLED"}


UV_OPERATOR_CLASSES = (
    SURREAL_ARCH_OT_uv_create_edit_proxy,
    SURREAL_ARCH_OT_uv_commit_from_proxy,
    SURREAL_ARCH_OT_uv_remove_proxy,
    SURREAL_ARCH_OT_uv_invoke_miouv,
    SURREAL_ARCH_OT_uv_invoke_uvpackmaster,
    SURREAL_ARCH_OT_trim_preset_architectural,
    SURREAL_ARCH_OT_trim_preset_modular,
    SURREAL_ARCH_OT_trim_preset_scifi,
    SURREAL_ARCH_OT_trim_preset_zen_wood,
    SURREAL_ARCH_OT_trim_preset_zen_stone,
    SURREAL_ARCH_OT_open_uv_editor,
)
