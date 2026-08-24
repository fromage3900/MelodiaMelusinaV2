"""Bootstrap + addon preferences for Melodia Studio."""
from __future__ import annotations

import bpy

from . import capabilities
from .capabilities import _DEFAULT_HIGGSAS

_PATCHED_MONOLITH = None

_HIGGSAS_PATH = bpy.props.StringProperty(
    name="Higgsas Library (.blend)",
    subtype="FILE_PATH",
    default=_DEFAULT_HIGGSAS,
    description="Path to Higgsas Geo Node Groups library blend file",
)
_SYNTHIA_PATH = bpy.props.StringProperty(
    name="Synthia Addon Path",
    subtype="DIR_PATH",
    default="",
    description="Optional folder hint for Synthia math-viz addon (install separately)",
)
_HIGGSAS_MIGRATED = bpy.props.BoolProperty(
    name="Higgsas prefs migrated",
    default=False,
    options={"HIDDEN"},
)
_SHOW_LEGACY = bpy.props.BoolProperty(
    name="Show legacy Modifier panel",
    description=(
        "Show the old Surreal Architecture drawer on the Modifier properties tab. "
        "Off by default — use N → Melodia Studio."
    ),
    default=False,
)


def _draw_studio_prefs(layout, prefs):
    layout.label(text="Melodia Studio")
    layout.prop(prefs, "show_legacy_modifier_panel")
    layout.separator()
    layout.label(text="Optional Dependencies")
    layout.prop(prefs, "higgsas_library_path")
    layout.prop(prefs, "synthia_addon_path")
    col = layout.column(align=True)
    for name in ("beavel", "synthia", "higgsas", "sverchok"):
        col.label(text=capabilities.status_line(name))


class MelodiaStudioAddonPreferences(bpy.types.AddonPreferences):
    """Preferences for the enabled module (surreal_architecture_gen.py)."""

    bl_idname = "surreal_architecture_gen"
    bl_label = "Melodia Studio"

    higgsas_library_path: _HIGGSAS_PATH
    synthia_addon_path: _SYNTHIA_PATH
    higgsas_migrated: _HIGGSAS_MIGRATED
    show_legacy_modifier_panel: _SHOW_LEGACY

    def draw(self, context):
        _draw_studio_prefs(self.layout, self)


class MelodiaStudioPrefsProductId(bpy.types.AddonPreferences):
    """Product-id alias so B1 migration (melodia_studio) still resolves."""

    bl_idname = "melodia_studio"
    bl_label = "Melodia Studio"

    higgsas_library_path: _HIGGSAS_PATH
    synthia_addon_path: _SYNTHIA_PATH
    higgsas_migrated: _HIGGSAS_MIGRATED
    show_legacy_modifier_panel: _SHOW_LEGACY

    def draw(self, context):
        _draw_studio_prefs(self.layout, self)


def _migrate_old_preferences():
    """Copy Higgsas/Synthia paths onto whichever prefs class is live."""
    try:
        addons = bpy.context.preferences.addons
        src = addons.get("surreal_architecture_gen") or addons.get("melodia_studio")
        dst = addons.get("melodia_studio") or addons.get("surreal_architecture_gen")
        if not src or not dst:
            return
        src_prefs = src.preferences
        dst_prefs = dst.preferences
        if getattr(dst_prefs, "higgsas_migrated", False):
            return
        if not dst_prefs.higgsas_library_path and getattr(src_prefs, "higgsas_library_path", ""):
            dst_prefs.higgsas_library_path = src_prefs.higgsas_library_path
        if not dst_prefs.synthia_addon_path and getattr(src_prefs, "synthia_addon_path", ""):
            dst_prefs.synthia_addon_path = src_prefs.synthia_addon_path
        dst_prefs.higgsas_migrated = True
    except Exception:
        pass


def repatch(monolith) -> bool:
    """Idempotent re-apply integration patches after importlib.reload."""
    from .integration import patch_monolith
    try:
        patch_monolith(monolith)
        global _PATCHED_MONOLITH
        _PATCHED_MONOLITH = monolith
        return True
    except Exception as exc:
        print(f"[Melodia Studio] repatch failed: {exc}")
        return False


_PREF_CLASSES = (
    MelodiaStudioAddonPreferences,
    MelodiaStudioPrefsProductId,
)


def register_preferences():
    for cls in _PREF_CLASSES:
        try:
            bpy.utils.register_class(cls)
        except (RuntimeError, ValueError):
            pass
    _migrate_old_preferences()


def unregister_preferences():
    for cls in reversed(_PREF_CLASSES):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
