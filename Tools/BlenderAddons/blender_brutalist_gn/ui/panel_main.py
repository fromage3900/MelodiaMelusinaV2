"""Brutalist GN Main UI Panel."""
import bpy
from ..core.gn_framework import BRUTALIST_GN_REGISTRY, list_generators_by_category


class BRUTALIST_GN_PT_main(bpy.types.Panel):
    """Main panel for Brutalist Geometry Nodes."""
    bl_label = "Brutalist Architecture GN"
    bl_idname = "BRUTALIST_GN_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Melodia Brutalist GN"
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="Procedural Brutalist Architecture", icon='MOD_BUILD')
        layout.separator()
        
        # Category buttons
        categories = {
            "walls": {"label": "Walls", "icon": 'MOD_SOLIDIFY'},
            "structures": {"label": "Structures", "icon': 'OUTLINER_OB_MESH'},
            "details": {"label": "Details", "icon": 'NODETREE'},
            "complexes": {"label": "Complexes", "icon": 'GROUP'},
        }
        
        for cat_id, cat_info in categories.items():
            box = layout.box()
            box.label(text=cat_info["label"], icon=cat_info["icon"])
            
            generators = list_generators_by_category(cat_id)
            for gen_id, gen_class in generators.items():
                box.operator(
                    f"melobrutalist_gn.create_{gen_id}",
                    text=gen_class.generator_name
                )


def register():
    bpy.utils.register_class(BRUTALIST_GN_PT_main)


def unregister():
    bpy.utils.unregister_class(BRUTALIST_GN_PT_main)
