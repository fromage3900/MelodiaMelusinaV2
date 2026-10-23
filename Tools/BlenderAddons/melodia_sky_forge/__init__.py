# Melodia Sky Forge - musical procedural skies for Melodia.
# Copyright (c) 2026 fromage3900 / Melodia Project - MIT
#
# Blender 4.0+ addon. bl_info minimum follows the sibling addons so the same
# folder loads on every workstation Blender in this project.
#
# One theme = one musical identity (mode/root/bpm, same vocabulary as
# world_recipe.v1) + stylized sky look (banded gradient, sun, clouds, stars,
# aurora). Bake = equirect EXR + flat sidecar JSON for TouchDesigner/UE.
# Register is idempotent-safe: bpy imports happen inside register() so
# `python -m unittest` on sky_core never needs bpy.

bl_info = {
    "name": "Melodia Sky Forge",
    "author": "fromage3900",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Melodia > Sky Forge",
    "description": (
        "Author stylized procedural skies keyed to Melodia musical themes: "
        "banded FADE-style gradients, sun, clouds, stars, aurora. Bake "
        "equirect EXR + sidecar JSON for TouchDesigner and UE import."
    ),
    "doc_url": "specs/sky_themes/melodia_sky_themes.v1.json",
    "category": "Melodia",
}


def register():
    from . import properties, operators, panel

    properties.register()
    operators.register()
    panel.register()


def unregister():
    from . import properties, operators, panel

    panel.unregister()
    operators.unregister()
    properties.unregister()
