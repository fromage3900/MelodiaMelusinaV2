# Melodia Stage — one-click character turntable & studio staging
# Copyright (c) 2026 fromage3900 / Melodia Project
# License: MIT

bl_info = {
    "name": "Melodia Stage",
    "author": "fromage3900",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Melodia Stage",
    "description": "One-click turntable + studio lighting for character portfolio shots",
    "category": "Melodia",
}

from . import operators, panel, properties


def register():
    properties.register()
    operators.register()
    panel.register()


def unregister():
    panel.unregister()
    operators.unregister()
    properties.unregister()
