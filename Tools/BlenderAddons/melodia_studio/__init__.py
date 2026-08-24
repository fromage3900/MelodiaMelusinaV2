# Melodia Studio — Blender Integration Panel
# Tools/BlenderAddons/melodia_studio/

bl_info = {
    "name": "Melodia Studio",
    "author": "fromage3900",
    "version": (1, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Melodia Studio",
    "description": "MIDI-driven Resonant World generation for Melodia",
    "category": "Melodia",
}

import importlib

from . import midi_bridge
from . import studio_panel

# Reload on addon refresh so edits land without restarting Blender.
importlib.reload(midi_bridge)
importlib.reload(studio_panel)


def register():
    studio_panel.register()


def unregister():
    studio_panel.unregister()
