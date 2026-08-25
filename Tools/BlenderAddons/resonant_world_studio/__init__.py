"""Resonant World Studio - MIDI to walkable level, in one click.

Folder-based addon so it can be junction-linked from the repo and survive a
Blender reinstall (see BLENDER_ADDON_MANIFEST).

What it does that the older panels did not:
  * imports the proven voxel parser by path instead of a bare import that
    could never resolve
  * builds terrain with a material that actually samples the baked AuraColor
  * frames camera and lights from real mesh bounds
  * reports MEASURED walkability in the panel -- footprint, aspect, walkable
    edge fraction, largest connected region -- so the UI states facts rather
    than claims
"""

bl_info = {
    "name": "Resonant World Studio",
    "author": "fromage3900",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Resonant World",
    "description": "Turn a MIDI file into a walkable, dressed, lit level and "
                   "report measured traversability.",
    "category": "Melodia",
}

import importlib

from . import bridge
from . import build
from . import ops
from . import panel

for _mod in (bridge, build, ops, panel):
    importlib.reload(_mod)


def register():
    ops.register()
    panel.register()


def unregister():
    panel.unregister()
    ops.unregister()
