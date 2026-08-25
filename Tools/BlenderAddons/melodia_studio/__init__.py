# Melodia Studio - Blender Integration Panel
# Tools/BlenderAddons/melodia_studio/

bl_info = {
    "name": "Melodia Studio",
    "author": "fromage3900",
    "version": (1, 3, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Melodia Studio",
    "description": "MIDI-driven Resonant World generation - walkable default, Gaea surfaced, musical GN presets, bespoke Melodia chrome (C: authority)",
    "category": "Melodia Studio",
}

import importlib
import sys

from . import midi_bridge
from . import studio_panel

# Optional helpers - may be absent offline
try:
    from . import addon_utils  # type: ignore
except Exception:
    addon_utils = None  # type: ignore

try:
    from . import walkable_world  # type: ignore
except Exception:
    walkable_world = None  # type: ignore

try:
    from . import terrain_dressing  # type: ignore
except Exception:
    terrain_dressing = None  # type: ignore

# Reload on addon refresh so edits land without restarting Blender.
importlib.reload(midi_bridge)
importlib.reload(studio_panel)
if addon_utils is not None:
    try:
        importlib.reload(addon_utils)
    except Exception:
        pass
if walkable_world is not None:
    try:
        importlib.reload(walkable_world)
    except Exception:
        pass
if terrain_dressing is not None:
    try:
        importlib.reload(terrain_dressing)
    except Exception:
        pass


def register():
    studio_panel.register()


def unregister():
    studio_panel.unregister()
    if addon_utils is not None:
        try:
            addon_utils.unload_icons()
        except Exception:
            pass
