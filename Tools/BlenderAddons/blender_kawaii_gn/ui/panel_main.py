"""
Main UI Panel for Kawaii Geometry Nodes Addon
==============================================
Provides parameterized UI for all GeoNodes generators.
"""

import bpy
from ..core.gn_framework import get_generator, list_generators_by_category


class KawaiiGNSceneProps(bpy.types.PropertyGroup):
    """Scene properties for Kawaii GN."""
    selected_generator: bpy.props.StringProperty(
        name="Selected Generator",
        default="",
    )
    pastel_theme: bpy.props.EnumProperty(
        name="Pastel Theme",
        items=[
            ('pastel_pink', 'Pastel Pink', 'Soft pink palette'),
            ('pastel_blue', 'Pastel Blue', 'Gentle blue'),
            ('pastel_lavender', 'Lavender', 'Purple tones'),
            ('pastel_mint', 'Mint', 'Green mint'),
            ('pastel_peach', 'Peach', 'Warm peach'),
            ('pastel_yellow', 'Yellow', 'Sunny yellow'),
            ('rainbow', 'Rainbow', 'Multi-color'),
        ],
        default='pastel_pink',
    )
    cuteness_level: bpy.props.FloatProperty(
        name="Cuteness Level",
        default=0.7,
        min=0.0,
        max=1.0,
        description="Drives Roundness on generators that expose it (plushies, food, architecture, etc.)",
    )
    export_lod: bpy.props.BoolProperty(
        name="Generate LOD Mesh",
        default=False,
        description="Also export basename_LOD1.fbx (ratio) and basename_LOD2.fbx (ratio² faces vs LOD0) for UE5",
    )
    export_lod_ratio: bpy.props.FloatProperty(
        name="LOD Ratio",
        default=0.35,
        min=0.05,
        max=1.0,
        subtype='FACTOR',
        description="Decimate ratio per step; LOD2 applies ratio twice on the export mesh",
    )
    plushie_fabric_style: bpy.props.EnumProperty(
        name="Plushie Material",
        items=[
            ('pastel', 'Pastel', 'Standard pastel shader'),
            ('plushie_fabric', 'Plushie Fabric', 'Fuzzy plushie fabric shader'),
        ],
        default='plushie_fabric',
    )


class MELKAWAIIGN_PT_main(bpy.types.Panel):
    """Main panel."""
    bl_label = "* Kawaii Geometry Nodes (v2.0.40) *"
    bl_idname = "MELKAWAIIGN_PT_main"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Melodia Kawaii GN"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = scene.kawaii_gn_props
        
        # Header
        box = layout.box()
        box.label(text="WORLD'S MOST COMPREHENSIVE", icon='COLOR')
        box.label(text="KAWAII GEOMETRY NODES ADDON", icon='GEOMETRY_NODES')
        
        # Settings
        box = layout.box()
        box.label(text="Global Settings", icon='SETTINGS')
        box.prop(props, 'cuteness_level', text="Cuteness")
        box.label(text="Cuteness -> Roundness on supported GNs", icon='INFO')
        box.label(text="Cupcake/Donut: Roundness scales icing + base", icon='BLANK1')
        box.label(text="Donut: Roundness also lifts icing Z (CombineXYZ)", icon='BLANK1')
        box.prop(props, 'pastel_theme', text="Theme")
        box.prop(props, 'plushie_fabric_style', text="Plushie Mat")

        export_row = layout.row(align=True)
        export_row.scale_y = 1.2
        export_row.operator("melkawaii_gn.export_ue5", text="Export to UE5", icon='EXPORT')
        lod = layout.box()
        lod.label(text="UE5 Export", icon='EXPORT')
        lod.prop(props, 'export_lod', text="LOD Decimate")
        if props.export_lod:
            lod.label(text="FBX: basename, basename_LOD1, basename_LOD2", icon='INFO')
            lod.label(text="LOD1 ≈ ratio faces; LOD2 ≈ ratio² vs LOD0", icon='BLANK1')
        lod.prop(props, 'export_lod_ratio', text="LOD Ratio")
        
        # Categories
        categories = [
            ("Architecture", 'MOD_WIREFRAME'),
            ("Props", 'MESH_CUBE'),
            ("Furniture", 'OUTLINER_OB_MESH'),
            ("Plushies", 'HEART'),
            ("Decorations", 'GEOMETRY_NODES'),
            ("Effects", 'PARTICLES'),
            ("Greybox", 'MODIFIER'),
            ("Characters", 'OUTLINER_OB_ARMATURE'),
            ("Food", 'NODE_TEXTURE'),
            ("Nature", 'STRANDS'),
        ]
        
        box = layout.box()
        box.label(text="Categories", icon='MENU_PANEL')
        box.label(text="Pick a category to open its generator list", icon='INFO')
        for cat_name, icon in categories:
            box.operator(f"melkawaii_gn.show_{cat_name.lower()}", text=cat_name, icon=icon)


def register():
    bpy.utils.register_class(KawaiiGNSceneProps)
    bpy.utils.register_class(MELKAWAIIGN_PT_main)
    bpy.types.Scene.kawaii_gn_props = bpy.props.PointerProperty(type=KawaiiGNSceneProps)
    print("[Kawaii GN v2.0.40] Main panel - Blender 5.1 GN I/O + node API compatibility")


def unregister():
    del bpy.types.Scene.kawaii_gn_props
    bpy.utils.unregister_class(MELKAWAIIGN_PT_main)
    bpy.utils.unregister_class(KawaiiGNSceneProps)
