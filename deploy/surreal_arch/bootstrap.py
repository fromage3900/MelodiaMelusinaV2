"""Bootstrap + addon preferences for Surreal Architecture overhaul package."""
from __future__ import annotations

import bpy

from . import capabilities
from .capabilities import _DEFAULT_HIGGSAS

_PATCHED_MONOLITH = None


class MelodiaStudioAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = "melodia_studio"
    bl_label = "Melodia Studio"

    higgsas_library_path: bpy.props.StringProperty(
        name="Higgsas Library (.blend)",
        subtype="FILE_PATH",
        default=_DEFAULT_HIGGSAS,
        description="Path to Higgsas Geo Node Groups library blend file",
    )
    synthia_addon_path: bpy.props.StringProperty(
        name="Synthia Addon Path",
        subtype="DIR_PATH",
        default="",
        description="Optional folder hint for Synthia math-viz addon (install separately)",
    )

    def draw(self, context):
        layout = self.layout
        layout.label(text="Optional Dependencies")
        layout.prop(self, "higgsas_library_path")
        layout.prop(self, "synthia_addon_path")
        col = layout.column(align=True)
        for name in ("beavel", "synthia", "higgsas", "sverchok"):
            col.label(text=capabilities.status_line(name))


def _migrate_old_preferences():
    """One-time migration from legacy surreal_architecture_gen to melodia_studio.

    Runs during register_preferences(). Copies saved paths so returning users
    do not lose Higgsas/Synthia preferences after the module ID rename.
    """
    try:
        old = bpy.context.preferences.addons.get("surreal_architecture_gen")
        if not old:
            return
        new = bpy.context.preferences.addons.get("melodia_studio")
        if not new:
            return
        prefs = new.preferences
        old_prefs = old.preferences
        if not getattr(old_prefs, "higgsas_migrated", False):
            if not prefs.higgsas_library_path and getattr(old_prefs, "higgsas_library_path", ""):
                prefs.higgsas_library_path = old_prefs.higgsas_library_path
            if not prefs.synthia_addon_path and getattr(old_prefs, "synthia_addon_path", ""):
                prefs.synthia_addon_path = old_prefs.synthia_addon_path
            prefs.higgsas_migrated = True
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
        print(f"[Surreal Architecture] repatch failed: {exc}")
        return False


def register_preferences():
    try:
        bpy.utils.register_class(MelodiaStudioAddonPreferences)
    except RuntimeError:
        pass
    _migrate_old_preferences()


def unregister_preferences():
    try:
        bpy.utils.unregister_class(MelodiaStudioAddonPreferences)
    except RuntimeError:
        pass
