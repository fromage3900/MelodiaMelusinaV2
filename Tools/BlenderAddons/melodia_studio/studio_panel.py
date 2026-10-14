"""Melodia Studio panel - registration facade.

QOL pass (2026-08-24, C-authority):
 - Unified N-panel category "Melodia" so all Melodia tools sit together
 - Search/filter for MIDI, preview line (notes + beatgrid), last-run stats
 - Cleanup of stale Terrain objects on re-generate
 - dress_terrain receives midi_path so the placement plan uses real terrain
 - Management subpanel: health, folders, reload, docs
 - Icon fallback via addon_utils, offline-safe (no bpy on import)
 - Cached MIDI discovery (avoids rescanning every draw)

Monolith split (2026-10-04): the implementation now lives in
  - midi_picker.py    discovery cache, _selected_midi, preview line
  - terrain_build.py  mesh / aura material / dressing instancing
  - properties.py     AddonPreferences + StudioProps + enum helpers
  - operators.py      the 11 STUDIO_OT_* classes
  - panel.py          STUDIO_PT_panel + STUDIO_PT_management

This module keeps the historic public surface:
  studio_panel.register() / .unregister()   (called by __init__.py)
  studio_panel._selected_midi               (reused by tandem_bridge)
All bl_idnames and the registration order are unchanged.
"""

try:
    import bpy  # type: ignore
except Exception:
    bpy = None  # type: ignore

from . import midi_picker
from . import properties
from . import operators
from . import panel

# Re-exported for tandem_bridge (historical access path studio_panel._selected_midi)
from .midi_picker import _selected_midi  # noqa: F401

if bpy is not None:
    classes = [
        properties.MelodiaStudioPreferences,
        properties.StudioProps,
        *operators.OPERATOR_CLASSES,
        *panel.PANEL_CLASSES,
    ]

else:
    classes = []  # type: ignore


def _warn(msg: str) -> None:
    if bpy is not None:
        try:
            bpy.log.warn(f"[Melodia Studio] {msg}")
            return
        except Exception:
            pass
    print(f"[Melodia Studio] {msg}")


def register():
    if bpy is None:
        return
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except Exception as exc:
            _warn(f"register_class failed for {getattr(cls, '__name__', cls)}: {exc!r}")
    try:
        bpy.types.Scene.melodia_studio = bpy.props.PointerProperty(type=properties.StudioProps)  # type: ignore[attr-defined]
    except Exception as exc:
        _warn(f"Scene.melodia_studio pointer registration failed: {exc!r}")


def unregister():
    if bpy is None:
        return
    if hasattr(bpy.types.Scene, "melodia_studio"):
        try:
            del bpy.types.Scene.melodia_studio  # type: ignore[attr-defined]
        except Exception:
            pass
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception as exc:
            _warn(f"unregister_class failed for {getattr(cls, '__name__', cls)}: {exc!r}")
