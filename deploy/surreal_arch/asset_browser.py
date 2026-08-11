"""Asset Browser publishing helpers.

Creates a .blend file containing generated greybox kit objects marked as assets.
"""

from __future__ import annotations

import os

import bpy


def _default_asset_blend_path():
    # Put it next to the addon .py by default, so it can be referenced as a linked library.
    addon_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(addon_dir, "SurrealArch_GreyboxAssets.blend")


def _iter_greybox_type_ids(monolith):
    from .catalog import search_index
    seen = set()
    for ent in search_index(monolith):
        at = ent.get("id", "")
        if not isinstance(at, str):
            continue
        if at.startswith("GB_WOODS_"):
            continue
        if not (at.startswith("GREYBOX_") or at.startswith("GB_")):
            continue
        if at in seen:
            continue
        seen.add(at)
        yield at


class SURREAL_ARCH_OT_publish_greybox_assets(bpy.types.Operator):
    bl_idname = "surreal_arch.publish_greybox_assets"
    bl_label = "Publish Greybox Assets (.blend)"
    bl_options = {"REGISTER"}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH", default="")
    limit: bpy.props.IntProperty(name="Limit", default=60, min=1, max=400)

    def execute(self, context):
        import surreal_architecture_gen as monolith

        target = self.filepath.strip() if self.filepath else ""
        if not target:
            target = _default_asset_blend_path()
        target = bpy.path.abspath(target)
        os.makedirs(os.path.dirname(target), exist_ok=True)

        # Build assets in an isolated scene so the user's current file is untouched.
        src_scene = context.scene
        scene = bpy.data.scenes.new("SurrealArch_AssetPublish")
        context.window.scene = scene

        created = []
        try:
            # A dedicated collection keeps Asset Browser tidy.
            col = bpy.data.collections.new("SurrealArch Greybox")
            scene.collection.children.link(col)

            for i, at in enumerate(_iter_greybox_type_ids(monolith)):
                if i >= int(self.limit):
                    break
                mesh = bpy.data.meshes.new(f"SA_{at}")
                obj = bpy.data.objects.new(f"SA_{at}", mesh)
                col.objects.link(obj)
                context.view_layer.objects.active = obj
                obj.select_set(True)
                try:
                    props = obj.surreal_arch_props
                except Exception:
                    continue
                props.arch_type = at
                try:
                    bpy.ops.surreal_arch.generate()
                except Exception:
                    continue
                try:
                    obj.asset_mark()
                    obj.asset_data.description = f"Surreal Architecture — {at}"
                except Exception:
                    pass
                created.append(obj)

            # Save to a library .blend.
            try:
                bpy.ops.wm.save_as_mainfile(filepath=target, copy=True)
            except TypeError:
                bpy.ops.wm.save_as_mainfile(filepath=target)

        finally:
            # Restore the user's scene.
            context.window.scene = src_scene
            try:
                bpy.data.scenes.remove(scene)
            except Exception:
                pass

        self.report({"INFO"}, f"Wrote {len(created)} assets: {target}")
        return {"FINISHED"}

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = _default_asset_blend_path()
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


def register_asset_ops(monolith):
    return [SURREAL_ARCH_OT_publish_greybox_assets]

