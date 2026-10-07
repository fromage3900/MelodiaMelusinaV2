# Melodia Studio - Blender Integration Panel
# Tools/BlenderAddons/melodia_studio/

bl_info = {
    "name": "Melodia Studio — MIDI World",
    "author": "fromage3900",
    "version": (1, 5, 1),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Melodia Studio",
    "description": "MIDI-driven Resonant World generation - walkable default + instanced dressing + Tandem City (field-wins snap to Surreal GN, no monolith edits) (C: authority) — D7 divisor threaded + AddonPreferences",
    "category": "Melodia Studio",
}

import importlib

try:
    import bpy
except ImportError:  # offline / unit-test context
    bpy = None


def _warn(msg: str) -> None:
    # Surface failures instead of silently dropping optional modules.
    if bpy is not None:
        try:
            bpy.log.warn(f"[Melodia Studio] {msg}")
            return
        except Exception:
            pass
    print(f"[Melodia Studio] {msg}")


from . import midi_bridge
from . import studio_panel

_OPTIONAL_MODULES: dict[str, object] = {}
for _name in (
    "addon_utils",
    "walkable_world",
    "terrain_dressing",
    "gaea_panel",
    "tandem_bridge",
    "melodia_chrome",
):
    try:
        _OPTIONAL_MODULES[_name] = importlib.import_module(f".{_name}", __name__)
    except Exception as exc:
        _warn(f"optional module '{_name}' unavailable: {exc!r}")

addon_utils = _OPTIONAL_MODULES.get("addon_utils")  # type: ignore
walkable_world = _OPTIONAL_MODULES.get("walkable_world")  # type: ignore
terrain_dressing = _OPTIONAL_MODULES.get("terrain_dressing")  # type: ignore
gaea_panel = _OPTIONAL_MODULES.get("gaea_panel")  # type: ignore
tandem_bridge = _OPTIONAL_MODULES.get("tandem_bridge")  # type: ignore
melodia_chrome = _OPTIONAL_MODULES.get("melodia_chrome")  # type: ignore


def _reload(mod, name: str) -> None:
    # Reload on addon refresh so edits land without restarting Blender.
    try:
        importlib.reload(mod)
    except Exception as exc:
        _warn(f"reload of '{name}' failed: {exc!r}")


# studio_panel split (2026-10-04): reload the split submodules first so the
# facade rebinds to the reloaded classes.
for _name in ("midi_picker", "terrain_build", "properties", "operators", "panel"):
    try:
        _reload(importlib.import_module(f".{_name}", __name__), _name)
    except Exception as exc:
        _warn(f"studio split module '{_name}' unavailable: {exc!r}")

_reload(midi_bridge, "midi_bridge")
_reload(studio_panel, "studio_panel")
for _name, _mod in _OPTIONAL_MODULES.items():
    _reload(_mod, _name)


def _call_optional(name: str, func: str) -> None:
    mod = _OPTIONAL_MODULES.get(name)
    if mod is None:
        return
    try:
        getattr(mod, func)()
    except Exception as exc:
        _warn(f"{func}() failed in '{name}': {exc!r}")


def register():
    _call_optional("melodia_chrome", "register")
    studio_panel.register()
    _call_optional("gaea_panel", "register")
    _call_optional("tandem_bridge", "register")


def unregister():
    _call_optional("tandem_bridge", "unregister")
    _call_optional("gaea_panel", "unregister")
    studio_panel.unregister()
    _call_optional("melodia_chrome", "unregister")
    _call_optional("addon_utils", "unload_icons")
