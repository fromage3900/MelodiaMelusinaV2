# Melodia Showroom - integrated terrain -> dress -> frame -> render
# Copyright (c) 2026 fromage3900 / Melodia Project
# License: MIT

bl_info = {
    "name": "Melodia Showroom",
    "author": "fromage3900",
    "version": (1, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Melodia",
    "description": "Integrated terrain -> dress -> frame -> render (C: authority, reuses Melodia Studio bridge)",
    "category": "Melodia",
}

try:
    from . import operators, panel, properties
except Exception:
    operators = panel = properties = None


def register():
    if operators is None:
        return
    properties.register()
    operators.register()
    panel.register()


def unregister():
    if panel is None:
        return
    panel.unregister()
    operators.unregister()
    properties.unregister()
