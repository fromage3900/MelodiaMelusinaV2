# Melodia Pose Audit — character rig cleanliness checker
# Copyright (c) 2026 fromage3900 / Melodia Project
# License: MIT

bl_info = {
    "name": "Melodia Pose Audit",
    "author": "fromage3900",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Pose Audit",
    "description": "Audit Melodia-style character rigs for pose-sheet blockers",
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
