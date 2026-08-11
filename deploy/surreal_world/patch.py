"""Patch monolith Layer 2 world pipeline to surreal_world package."""

from __future__ import annotations

import bpy

from surreal_world import compose, export, library, plans


def patch_world(monolith):
    """Replace library/compose implementations; extend operators."""
    monolith._SURREAL_LIBRARY_SPEC = library.SURREAL_LIBRARY_SPEC
    monolith._SURREAL_COMPOSE_STYLES = compose.COMPOSE_STYLES
    monolith._surreal_library_collection = library.library_collection

    def _bake(arch_type, params, target_coll, force=False):
        return library.bake_library_piece(monolith, arch_type, params, target_coll, force)

    monolith._bake_library_piece = _bake

    def _compose(ctx, plan_obj, style_key="WESTERN_CASTLE", detail_scale=1.0, compose_mode="COLLECTION"):
        return compose.compose_world(monolith, ctx, plan_obj, style_key, detail_scale, compose_mode)

    monolith._compose_world = _compose

    monolith._spawn_castle_plan = plans.spawn_castle_plan
    monolith._spawn_zen_roji_plan = plans.spawn_zen_roji_plan
    monolith._spawn_zen_temple_plan = plans.spawn_zen_temple_plan

    _patch_library_init(monolith)
    _patch_compose_world(monolith)
    _patch_recompose(monolith)


def _patch_library_init(monolith):
    def execute(self, context):
        stats = library.init_library(monolith, force_refresh=self.force_refresh)
        self.report(
            {"INFO"},
            f"Library: {stats['baked']} baked, {stats['skipped']} kept, {stats['failed']} failed",
        )
        try:
            bpy.ops.object.select_all(action="DESELECT")
        except Exception:
            pass
        return {"FINISHED"}

    monolith.SURREAL_ARCH_OT_library_init.execute = execute


def _patch_compose_world(monolith):
    op_cls = monolith.SURREAL_ARCH_OT_compose_world

    def execute(self, context):
        obj = context.active_object
        if obj is None or obj.type != "MESH":
            self.report({"WARNING"}, "Select a plan mesh first")
            return {"CANCELLED"}
        if library.library_collection(create=False) is None:
            self.report({"INFO"}, "Library not found — auto-initializing…")
            library.init_library(monolith, force_refresh=False)
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            context.view_layer.objects.active = obj
        compose_mode = getattr(self, "compose_mode", "COLLECTION")
        result, message = compose.compose_world(
            monolith, context, obj, self.style, self.detail_scale, compose_mode,
        )
        if result is None:
            self.report({"WARNING"}, message)
            return {"CANCELLED"}
        self.report({"INFO"}, message)
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "style")
        if hasattr(self, "compose_mode"):
            layout.prop(self, "compose_mode")
        layout.prop(self, "detail_scale")
        obj = context.active_object
        if obj:
            layout.label(text=f"Plan: {obj.name}", icon="OUTLINER_OB_MESH")

    op_cls.execute = execute
    op_cls.draw = draw


def _patch_recompose(monolith):
    def execute(self, context):
        obj = context.active_object
        if obj is None:
            self.report({"WARNING"}, "Select a composed world or its source plan")
            return {"CANCELLED"}
        result, message = compose.recompose_world(monolith, context, obj)
        if result is None:
            self.report({"WARNING"}, message)
            return {"CANCELLED"}
        self.report({"INFO"}, message)
        return {"FINISHED"}

    monolith.SURREAL_ARCH_OT_recompose.execute = execute


def register_world_operators(monolith):
    """Extra operators for zen plan + UE export."""

    class SURREAL_ARCH_OT_plan_spawn_zen_roji(bpy.types.Operator):
        bl_idname = "surreal_arch.plan_spawn_zen_roji"
        bl_label = "Zen Roji Plan"
        bl_options = {"REGISTER", "UNDO"}

        path_len: bpy.props.FloatProperty(name="Path Length", default=16.0, min=6.0, max=60.0)
        courtyard_w: bpy.props.FloatProperty(name="Courtyard Width", default=8.0, min=4.0, max=30.0)

        def execute(self, context):
            cursor = context.scene.cursor.location
            obj = plans.spawn_zen_roji_plan(
                location=tuple(cursor),
                path_len=self.path_len,
                courtyard_w=self.courtyard_w,
            )
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            context.view_layer.objects.active = obj
            self.report({"INFO"}, f"Zen roji plan: {obj.name}")
            return {"FINISHED"}

    class SURREAL_ARCH_OT_plan_spawn_zen_temple(bpy.types.Operator):
        bl_idname = "surreal_arch.plan_spawn_zen_temple"
        bl_label = "Zen Temple Plan"
        bl_options = {"REGISTER", "UNDO"}

        path_len: bpy.props.FloatProperty(name="Path Length", default=20.0, min=8.0, max=80.0)
        courtyard_w: bpy.props.FloatProperty(name="Courtyard Width", default=12.0, min=6.0, max=40.0)
        engawa_w: bpy.props.FloatProperty(name="Engawa Wing", default=6.0, min=3.0, max=20.0)

        def execute(self, context):
            cursor = context.scene.cursor.location
            obj = plans.spawn_zen_temple_plan(
                location=tuple(cursor),
                path_len=self.path_len,
                courtyard_w=self.courtyard_w,
                engawa_w=self.engawa_w,
            )
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            context.view_layer.objects.active = obj
            self.report({"INFO"}, f"Zen temple plan: {obj.name}")
            return {"FINISHED"}

    class SURREAL_ARCH_OT_export_world_ue(bpy.types.Operator):
        bl_idname = "surreal_arch.export_world_ue"
        bl_label = "Export World to UE"
        bl_options = {"REGISTER"}

        filepath: bpy.props.StringProperty(subtype="FILE_PATH")
        export_fbx: bpy.props.BoolProperty(name="Export Role FBX", default=False)

        def execute(self, context):
            obj = context.active_object
            if obj is None:
                self.report({"WARNING"}, "Select a composed world root or plan")
                return {"CANCELLED"}
            root = export.find_world_root(obj)
            if root is None:
                self.report({"WARNING"}, "No COLLECTION world root found")
                return {"CANCELLED"}
            path = self.filepath or bpy.path.abspath(f"//{root.name}.world.json")
            written = export.write_world_manifest(obj, path, monolith=monolith)
            fbx_paths = []
            if self.export_fbx:
                fbx_paths = export.export_role_fbx_batches(context, root)
            self.report(
                {"INFO"},
                f"Wrote {written} ({len(fbx_paths)} FBX batches)" if fbx_paths else f"Wrote {written}",
            )
            return {"FINISHED"}

        def invoke(self, context, event):
            context.window_manager.fileselect_add(self)
            return {"RUNNING_MODAL"}

    def _compose_panel_draw_orig(self, context):
        pass

    orig_draw = getattr(monolith.SURREAL_ARCH_PT_compose, "draw", None)

    def compose_panel_draw(self, context):
        if orig_draw:
            orig_draw(self, context)
        layout = self.layout
        box = layout.box()
        box.label(text="Zen + UE Export", icon="WORLD")
        box.operator("surreal_arch.plan_spawn_zen_roji", text="Zen Roji Plan", icon="MESH_GRID")
        box.operator("surreal_arch.plan_spawn_zen_temple", text="Zen Temple Plan", icon="HOME")
        box.operator("surreal_arch.export_world_ue", text="Export World to UE", icon="EXPORT")

    if orig_draw and not getattr(monolith.SURREAL_ARCH_PT_compose, "_world_patched", False):
        monolith.SURREAL_ARCH_PT_compose.draw = compose_panel_draw
        monolith.SURREAL_ARCH_PT_compose._world_patched = True

    return [SURREAL_ARCH_OT_plan_spawn_zen_roji, SURREAL_ARCH_OT_plan_spawn_zen_temple, SURREAL_ARCH_OT_export_world_ue]
