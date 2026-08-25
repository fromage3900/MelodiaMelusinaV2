# Melodia Aura - procedural magic/energy effect generator for Blender
# Copyright (c) 2026 fromage3900 / Melodia Project
# License: MIT

bl_info = {
    "name": "Melodia Aura",
    "author": "fromage3900",
    "version": (1, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Melodia",
    "description": "Procedural spell auras (unified Melodia), energy ribbons, and glow effects for JRPG battles",
    "category": "Melodia",
}

from . import operators, panel


def register():
    operators.register()
    panel.register()


def unregister():
    panel.unregister()
    operators.unregister()
