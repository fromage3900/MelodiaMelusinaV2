"""Optional third-party dependency detection for Surreal Architecture."""
from __future__ import annotations

import os

import bpy

# Repo root = two levels up from deploy/surreal_arch/capabilities.py
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_HIGGSAS_LIB_NAME = "Blender 5.0 Higgsas Geo Node Groups v13.blend"

_LEGACY_HIGGSAS = (
    r"G:\programs\BlenderPlugins"
    r"\Higgsas_Geometry_Nodes_Toolset_v1.3 vfxMed"
    r"\Higgsas Geo Nodes Blender 5.0"
    "\\" + _HIGGSAS_LIB_NAME
)


def _higgsas_candidates() -> list:
    """Ordered library locations; first existing wins. See RawArt/BlenderLibraries/README.md."""
    downloads = os.path.join(
        os.path.expanduser("~"), "Downloads",
        "Higgsas_Geometry_Nodes_Toolset_v1.3",
        "Higgsas Geo Nodes Blender 5.0", _HIGGSAS_LIB_NAME)
    return [
        os.path.join(_REPO_ROOT, "RawArt", "BlenderLibraries",
                     "Higgsas", _HIGGSAS_LIB_NAME),
        _LEGACY_HIGGSAS,
        downloads,
    ]


# Legacy module-level name kept for bootstrap.py prefs default. The resolver
# (higgsas_library_path) is the authority; this is only the prefs fallback shown
# in Edit > Preferences before the user sets an override.
_DEFAULT_HIGGSAS = (
    os.path.join(_REPO_ROOT, "RawArt", "BlenderLibraries",
                 "Higgsas", _HIGGSAS_LIB_NAME)
)


def _prefs():
    try:
        return bpy.context.preferences.addons["surreal_architecture_gen"].preferences
    except Exception:
        return None


def higgsas_library_path() -> str:
    prefs = _prefs()
    override = getattr(prefs, "higgsas_library_path", "") if prefs else ""
    if override and os.path.exists(override):
        return override
    for cand in _higgsas_candidates():
        if os.path.exists(cand):
            return cand
    # Nothing found: report the canonical repo-relative expectation.
    return os.path.join(_REPO_ROOT, "RawArt", "BlenderLibraries",
                        "Higgsas", _HIGGSAS_LIB_NAME)


def synthia_addon_hint() -> str:
    prefs = _prefs()
    if prefs and getattr(prefs, "synthia_addon_path", ""):
        return prefs.synthia_addon_path
    return ""


def is_available(name: str) -> bool:
    name = name.lower()
    if name == "beavel":
        return hasattr(bpy.ops.mesh, "beavel_operator")
    if name == "synthia":
        if not hasattr(bpy.ops.synthia, "spawn_preset"):
            return False
        try:
            bpy.ops.synthia.spawn_preset.get_rna_type()
            return True
        except Exception:
            return False
    if name == "higgsas":
        if os.path.exists(higgsas_library_path()):
            return True
        for ng in bpy.data.node_groups:
            if ng.name.startswith("NT") and len(ng.name) > 4:
                return True
        return False
    if name == "sverchok":
        try:
            t = bpy.data.node_groups.new(name="__sv_cap_probe__", type="SverchCustomTreeType")
            bpy.data.node_groups.remove(t)
            return True
        except Exception:
            return False
    if name == "miouv":
        if hasattr(bpy.ops, "miouv"):
            return True
        for addon_name in bpy.context.preferences.addons.keys():
            if "miouv" in addon_name.lower():
                return True
        return False
    if name == "uvpackmaster":
        for mod_name in ("uvpackmaster3", "uvpackmaster2", "uvpackmaster"):
            if hasattr(bpy.ops, mod_name):
                return True
        for addon_name in bpy.context.preferences.addons.keys():
            if "uvpackmaster" in addon_name.lower():
                return True
        return False
    return False


def status_line(name: str) -> str:
    if is_available(name):
        return f"{name.title()}: installed"
    hint = ""
    if name.lower() == "synthia" and synthia_addon_hint():
        hint = f" (path: {synthia_addon_hint()})"
    elif name.lower() == "higgsas" and not os.path.exists(higgsas_library_path()):
        hint = " (library file missing)"
    return f"{name.title()}: not available{hint}"
