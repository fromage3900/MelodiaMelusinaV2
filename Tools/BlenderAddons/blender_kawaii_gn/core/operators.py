"""Kawaii GN operators - generate objects, category popups, and UE5 FBX export."""
import os

import bpy
from .gn_framework import get_generator, list_generators_by_category
from .material_generator import KawaiiMaterialGenerator
from .gn_framework import apply_scene_cuteness_to_object

_CATEGORY_OPS = []


class MELKAWAIIGN_OT_generate(bpy.types.Operator):
    bl_idname = "melkawaii_gn.generate"
    bl_label = "Generate Kawaii GN"
    bl_options = {'REGISTER', 'UNDO'}

    generator_id: bpy.props.StringProperty(name="Generator ID")

    def execute(self, context):
        gen_cls = get_generator(self.generator_id)
        if gen_cls is None:
            self.report({'ERROR'}, f"Unknown generator: {self.generator_id}")
            return {'CANCELLED'}
        obj = gen_cls.create_object()
        if obj:
            context.view_layer.objects.active = obj
            obj.select_set(True)
            props = getattr(context.scene, 'kawaii_gn_props', None)
            cuteness = props.cuteness_level if props else 0.7
            apply_scene_cuteness_to_object(obj, cuteness)
            palette = props.pastel_theme if props else 'pastel_pink'
            if gen_cls.category == 'plushies':
                fabric_style = props.plushie_fabric_style if props else 'plushie_fabric'
                if fabric_style == 'plushie_fabric':
                    mat = KawaiiMaterialGenerator.create_plushie_fabric(
                        name=f"Kawaii_{gen_cls.generator_name}",
                        palette=palette,
                        fuzziness=0.5 + cuteness * 0.4,
                    )
                else:
                    mat = KawaiiMaterialGenerator.create_pastel_material(
                        name=f"Kawaii_{gen_cls.generator_name}",
                        palette=palette,
                        subsurface=0.45,
                    )
            else:
                mat = KawaiiMaterialGenerator.create_pastel_material(
                    name=f"Kawaii_{gen_cls.generator_name}",
                    palette=palette,
                    subsurface=0.45,
                )
            if obj.data.materials:
                obj.data.materials[0] = mat
            else:
                obj.data.materials.append(mat)
        self.report({'INFO'}, f"Created {obj.name}")
        return {'FINISHED'}


class MELKAWAIIGN_OT_export_ue5(bpy.types.Operator):
    """Apply modifiers on active mesh then export FBX with UE5-friendly axis settings."""
    bl_idname = "melkawaii_gn.export_ue5"
    bl_label = "Export to UE5"
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    apply_modifiers: bpy.props.BoolProperty(
        name="Apply Modifiers",
        default=True,
        description="Bake Geometry Nodes to mesh before export",
    )

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        export_obj = obj

        if self.apply_modifiers:
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            bpy.ops.object.duplicate(linked=False)
            export_obj = context.active_object
            export_obj.name = obj.name + "_UE5"
            for mod in list(export_obj.modifiers):
                try:
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                except RuntimeError:
                    export_obj.modifiers.remove(mod)

        bpy.ops.object.select_all(action='DESELECT')
        export_obj.select_set(True)
        context.view_layer.objects.active = export_obj

        fbx_kwargs = dict(
            use_selection=True,
            global_scale=1.0,
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_NONE',
            axis_forward='-Y',
            axis_up='Z',
            mesh_smooth_type='FACE',
        )

        gn_props = getattr(context.scene, 'kawaii_gn_props', None)
        export_lod = gn_props and gn_props.export_lod

        try:
            bpy.ops.export_scene.fbx(filepath=self.filepath, **fbx_kwargs)
        except Exception as exc:
            self.report({'ERROR'}, f"FBX export failed: {exc}")
            return {'CANCELLED'}

        if export_lod:
            base, ext = os.path.splitext(self.filepath)
            lod_ratio = gn_props.export_lod_ratio

            dec1 = export_obj.modifiers.new(name="Kawaii_LOD1", type='DECIMATE')
            dec1.ratio = lod_ratio
            try:
                bpy.ops.object.modifier_apply(modifier=dec1.name)
            except RuntimeError:
                export_obj.modifiers.remove(dec1)

            lod1_path = f"{base}_LOD1{ext}"
            try:
                bpy.ops.export_scene.fbx(filepath=lod1_path, **fbx_kwargs)
            except Exception as exc:
                self.report({'ERROR'}, f"LOD1 FBX export failed: {exc}")
                return {'CANCELLED'}

            dec2 = export_obj.modifiers.new(name="Kawaii_LOD2", type='DECIMATE')
            dec2.ratio = lod_ratio
            try:
                bpy.ops.object.modifier_apply(modifier=dec2.name)
            except RuntimeError:
                export_obj.modifiers.remove(dec2)

            lod2_path = f"{base}_LOD2{ext}"
            try:
                bpy.ops.export_scene.fbx(filepath=lod2_path, **fbx_kwargs)
            except Exception as exc:
                self.report({'ERROR'}, f"LOD2 FBX export failed: {exc}")
                return {'CANCELLED'}

            self.report(
                {'INFO'},
                f"Exported LOD0 -> {self.filepath}, LOD1 -> {lod1_path}, LOD2 -> {lod2_path}",
            )
        else:
            self.report({'INFO'}, f"Exported {export_obj.name} -> {self.filepath}")
        return {'FINISHED'}

    def invoke(self, context, event):
        obj = context.active_object
        self.filepath = (obj.name if obj else "kawaii_gn") + ".fbx"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def _make_show_category_op(category: str):
    """Factory: popup listing generators for a main-panel category button."""
    cat_display = category.title()
    op_id = f"melkawaii_gn.show_{category}"

    class MELKAWAIIGN_OT_show_category(bpy.types.Operator):
        bl_idname = op_id
        bl_label = cat_display
        bl_options = {'REGISTER'}

        def invoke(self, context, event):
            gens = list_generators_by_category(category)
            if not gens:
                self.report({'INFO'}, f"No {cat_display} generators registered yet")
                return {'CANCELLED'}
            context.scene.kawaii_gn_props.selected_generator = category
            return context.window_manager.invoke_popup(self, width=300)

        def draw(self, context):
            layout = self.layout
            gens = list_generators_by_category(category)
            layout.label(text=f"{cat_display} Generators", icon='GEOMETRY_NODES')
            for gen_id, gen_cls in gens.items():
                box = layout.box()
                box.label(text=gen_cls.generator_name)
                if gen_cls.description:
                    box.label(text=gen_cls.description, icon='BLANK1')
                op = box.operator(
                    "melkawaii_gn.generate",
                    text=f"Generate {gen_cls.generator_name}",
                    icon='PLAY',
                )
                op.generator_id = gen_id

        def execute(self, context):
            return {'FINISHED'}

    MELKAWAIIGN_OT_show_category.__name__ = f"MELKAWAIIGN_OT_show_{category}"
    return MELKAWAIIGN_OT_show_category


_SHOW_CATEGORIES = (
    'architecture', 'props', 'furniture', 'plushies', 'decorations',
    'effects', 'greybox', 'characters', 'food', 'nature',
)

for _cat in _SHOW_CATEGORIES:
    _CATEGORY_OPS.append(_make_show_category_op(_cat))

_CLASSES = (MELKAWAIIGN_OT_generate, MELKAWAIIGN_OT_export_ue5, *_CATEGORY_OPS)


def register():
    for cls in _CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(_CLASSES):
        bpy.utils.unregister_class(cls)
