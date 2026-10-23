# Melodia Sky Forge - scene properties.
# Copyright (c) 2026 fromage3900 / Melodia Project - MIT

from __future__ import annotations

import bpy


def _theme_enum_items(self, context):
    from . import sky_core

    try:
        lib = sky_core.load_library()
    except (OSError, ValueError, RuntimeError):
        return [("none", "Library unavailable", "")]
    items = [
        (t["theme_id"], t.get("label", t["theme_id"]), t["musical"]["mode_id"])
        for t in lib["themes"]
    ]
    return items or [("none", "No themes", "")]


class MELSKY_Properties(bpy.types.PropertyGroup):
    theme_id: bpy.props.EnumProperty(  # type: ignore[valid-type]
        name="Theme",
        description="Sky theme from specs/sky_themes/melodia_sky_themes.v1.json",
        items=_theme_enum_items,
    )
    output_dir: bpy.props.StringProperty(  # type: ignore[valid-type]
        name="Output Dir",
        description="Where equirect bakes and sidecars are written (staging only)",
        subtype='DIR_PATH',
        default="//sky_forge_out/",
    )
    dome_radius: bpy.props.FloatProperty(  # type: ignore[valid-type]
        name="Dome Radius",
        description="Radius (m) of the MEL_SkyForge_Dome sky carrier; make it larger than the scene",
        default=1000.0, min=10.0, soft_max=100000.0,
    )
    bake_samples: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="Samples",
        description="Cycles samples for the equirect bake",
        default=16, min=1, max=256,
    )
    bake_frames: bpy.props.IntProperty(  # type: ignore[valid-type]
        name="Frames (bar loop)",
        description="Bake ONE 4/4 bar as N frames (frame 0 = static sky; clouds drift, aurora pulses on the beat). Requires a theme with sky.motion values > 0",
        default=1, min=1, max=32,
    )


def register() -> None:
    bpy.utils.register_class(MELSKY_Properties)
    bpy.types.Scene.melodia_sky = bpy.props.PointerProperty(type=MELSKY_Properties)


def unregister() -> None:
    del bpy.types.Scene.melodia_sky
    bpy.utils.unregister_class(MELSKY_Properties)
