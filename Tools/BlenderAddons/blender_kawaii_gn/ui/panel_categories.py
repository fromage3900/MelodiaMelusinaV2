"""Category UI panels."""
import bpy
from ..core.gn_framework import list_generators_by_category

CATEGORIES = [
    'architecture', 'props', 'furniture', 'plushies', 'decorations',
    'effects', 'greybox', 'characters', 'food', 'nature',
]

PANEL_CLASSES = []


def _make_category_panel(category):
    class_name = f"MELKAWAIIGN_PT_{category}"
    cat_display = category.title()

    def draw(self, context):
        layout = self.layout
        gens = list_generators_by_category(category)
        if not gens:
            layout.label(text="No generators yet", icon='INFO')
            return
        header = layout.row(align=True)
        header.label(text="Generators", icon='GEOMETRY_NODES')
        badge = header.row()
        badge.alignment = 'RIGHT'
        badge.label(text=str(len(gens)), icon='LINENUMBERS_ON')
        for gen_id, gen_cls in gens.items():
            box = layout.box()
            box.label(text=gen_cls.generator_name, icon='GEOMETRY_NODES')
            box.label(text=gen_cls.description)
            op = box.operator(
                'melkawaii_gn.generate',
                text=f"Generate {gen_cls.generator_name}",
                icon='PLAY',
            )
            op.generator_id = gen_id

    panel_cls = type(
        class_name,
        (bpy.types.Panel,),
        {
            'bl_label': cat_display,
            'bl_idname': class_name,
            'bl_space_type': 'VIEW_3D',
            'bl_region_type': 'UI',
            'bl_category': "Melodia Kawaii GN",
            'bl_parent_id': "MELKAWAIIGN_PT_main",
            'draw': draw,
        },
    )
    return panel_cls


for _cat in CATEGORIES:
    _cls = _make_category_panel(_cat)
    PANEL_CLASSES.append(_cls)
    globals()[_cls.__name__] = _cls


def register():
    for cls in PANEL_CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(PANEL_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
