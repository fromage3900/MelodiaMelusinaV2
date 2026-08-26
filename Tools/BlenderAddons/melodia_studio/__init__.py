# Melodia Studio - Blender Integration Panel
# Tools/BlenderAddons/melodia_studio/

bl_info = {
    "name": "Melodia Studio",
    "author": "fromage3900",
    "version": (1, 4, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Melodia Studio",
    "description": "MIDI-driven Resonant World generation - walkable default + instanced dressing + Tandem City (field-wins snap to Surreal GN, no monolith edits) (C: authority)",
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

try:
    from . import gaea_panel  # type: ignore
except Exception:
    gaea_panel = None  # type: ignore

try:
    from . import tandem_bridge  # type: ignore
except Exception:
    tandem_bridge = None  # type: ignore

try:
    from . import melodia_chrome  # type: ignore
except Exception:
    melodia_chrome = None  # type: ignore

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
if gaea_panel is not None:
    try:
        importlib.reload(gaea_panel)
    except Exception:
        pass
if tandem_bridge is not None:
    try:
        importlib.reload(tandem_bridge)
    except Exception:
        pass
if melodia_chrome is not None:
    try:
        importlib.reload(melodia_chrome)
    except Exception:
        pass


def register():
    if melodia_chrome is not None:
        try:
            melodia_chrome.register()
        except Exception:
            pass
    studio_panel.register()
    if gaea_panel is not None:
        try:
            gaea_panel.register()
        except Exception:
            pass
    if tandem_bridge is not None:
        try:
            tandem_bridge.register()
        except Exception:
            pass


def unregister():
    if tandem_bridge is not None:
        try:
            tandem_bridge.unregister()
        except Exception:
            pass
    if gaea_panel is not None:
        try:
            gaea_panel.unregister()
        except Exception:
            pass
    studio_panel.unregister()
    if melodia_chrome is not None:
        try:
            melodia_chrome.unregister()
        except Exception:
            pass
    if addon_utils is not None:
        try:
            addon_utils.unload_icons()
        except Exception:
            pass
