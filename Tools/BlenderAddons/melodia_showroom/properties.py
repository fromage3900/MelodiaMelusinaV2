# Properties for Melodia Showroom
# Copyright (c) 2026 fromage3900 / Melodia Project
# License: MIT

try:
    import bpy
    from bpy.props import BoolProperty, EnumProperty, IntProperty, StringProperty
except Exception:
    bpy = None
    BoolProperty = EnumProperty = IntProperty = StringProperty = object


if bpy is not None:
    SHOWROOM_PRESETS = [
        ("verdant_default", "Verdant Default", "Resonant Default terrain + Verdant dressing"),
        ("cathedral_wide_crystalline", "Cathedral Wide Crystalline", "Cathedral Wide terrain + Crystalline dressing"),
        ("toccata_spires_toccata", "Toccata Spires Toccata", "Toccata Spires terrain + Toccata Surface dressing"),
        ("waltz_garden_waltz", "Waltz Garden Waltz", "Waltz Corridors terrain + Waltz Garden dressing"),
        ("ballad_plaza_ballad", "Ballad Plaza Ballad", "Ballad Broadstage terrain + Ballad Plaza dressing"),
        ("fugue_maze_fugue", "Fugue Maze Fugue", "Fugue Labyrinth terrain + Fugue Maze dressing"),
        ("nocturne_reflection_nocturne", "Nocturne Reflection Nocturne", "Nocturne Ribbon terrain + Nocturne Reflection dressing"),
        ("lullaby_cave_lullaby", "Lullaby Cave Lullaby", "Lullaby Undergrowth terrain + Lullaby Cave dressing"),
    ]

    class SHOWROOM_Props(bpy.types.PropertyGroup):
        preset: EnumProperty(
            name="Showroom Preset",
            description="Terrain + dressing combo",
            items=SHOWROOM_PRESETS,
            default="verdant_default",
        )
        midi_file: StringProperty(
            name="MIDI Override",
            description="Override MIDI file path",
            subtype='FILE_PATH',
            default="",
        )
        samples: IntProperty(
            name="Samples",
            default=64,
            min=1,
            max=4096,
            description="Render samples",
        )
        resolution_percent: IntProperty(
            name="Resolution %",
            default=100,
            min=10,
            max=200,
            description="Resolution percent",
        )
        transparent: BoolProperty(
            name="Transparent",
            default=False,
        )
        last_report: StringProperty(
            name="Last Report",
            default="No pipeline run yet",
        )

    classes = (SHOWROOM_Props,)
else:
    SHOWROOM_PRESETS = []
    SHOWROOM_Props = None
    classes = ()


def register():
    if bpy is None:
        return
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.melodia_showroom = bpy.props.PointerProperty(type=SHOWROOM_Props)


def unregister():
    if bpy is None or not hasattr(bpy.types.Scene, "melodia_showroom"):
        return
    del bpy.types.Scene.melodia_showroom
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
