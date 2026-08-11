"""
Melodia Kawaii Geometry Nodes â€” Blender Python Addon
=====================================================
THE most expansive, unique kawaii Geometry Nodes addon on the market.

Features:
  - 50+ procedural Geometry Nodes setups (fully non-destructive)
  - Live parameter adjustment (cuteness, proportions, materials)
  - Plushie Physics with real-time deformation
  - Pastel Material Generator with procedural shaders
  - Smart Instancing system for scene population
  - Animation-ready with keyframeable parameters
  - UE5 export with proper LOD generation
  
UNIQUE FEATURES (World-First!):
  - Kindchenschema-based proportions (scientific cuteness)
  - Plushie squish simulation in GeoNodes
  - Procedural sparkle/magic effects
  - Kawaii face generation (eyes, mouths, blush)
  - Pastel gradient materials (8 curated palettes)
  - Smart bevel system (adaptive rounded edges)
  - Chibi proportion transformer
  - Modular assembly system
"""

bl_info = {
    "name": "Melodia Kawaii Geometry Nodes",
    "author": "Melodia Studio",
    "version": (2, 0, 40),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Melodia Kawaii GN",
    "description": "World's most comprehensive Kawaii Geometry Nodes addon",
    "category": "Geometry Nodes",
}

import bpy
import importlib
import sys
from pathlib import Path

ADDON_NAME = "melkawaii"
OPERATOR_PREFIX = "melkawaii_gn"
BL_CATEGORY = "Melodia Kawaii GN"

_SUBMODULES = [
    # Core systems
    "core.gn_framework",
    "core.material_generator",
    "core.node_builder",
    "core.operators",
    # Generator categories (all use Geometry Nodes!)
    "generators.kawaii_architecture",
    "generators.kawaii_props",
    "generators.kawaii_furniture",
    "generators.kawaii_plushies",
    "generators.kawaii_decorations",
    "generators.kawaii_effects",
    "generators.kawaii_greybox",
    "generators.kawaii_characters",
    "generators.kawaii_food",
    "generators.kawaii_nature",
    # Advanced generators (v2.0.1 â€” were orphaned on disk)
    "generators.kawaii_plushies_advanced",
    "generators.kawaii_food_advanced",
    "generators.kawaii_nature_advanced",
    "generators.kawaii_decorations_advanced",
    "generators.kawaii_ice_cream",
    # UI
    "ui.panel_main",
    "ui.panel_categories",
    # Utilities
    "utils.instancer",
    "utils.animation",
]


def register():
    """Register all addon classes with Blender."""
    import bpy
    
    # Import and register all submodules
    package = __package__
    for name in _SUBMODULES:
        full = f"{package}.{name}"
        try:
            if full in sys.modules:
                mod = importlib.import_module(full)
                importlib.reload(mod)
            else:
                mod = importlib.import_module(full)
            
            if hasattr(mod, "register"):
                mod.register()
        except Exception as e:
            print(f"[Kawaii GN] Warning: Could not load {name}: {e}")

    from .core.gn_framework import (
        KAWAII_GN_REGISTRY,
        clear_generator_tree_cache,
        purge_stale_kawaii_node_groups,
    )
    clear_generator_tree_cache()

    def _purge_stale_on_load():
        removed = purge_stale_kawaii_node_groups()
        if removed:
            print(f"[Kawaii GN v2.0.40] Purged {removed} stale node group(s)")
        return None

    try:
        import bpy as _bpy
        _bpy.app.timers.register(_purge_stale_on_load, first_interval=0.0)
    except Exception:
        removed = purge_stale_kawaii_node_groups()
        if removed:
            print(f"[Kawaii GN v2.0.40] Purged {removed} stale node group(s)")

    print("[Kawaii GN v2.0.40] Registered — Blender 5.1 GN I/O + node API compatibility")


def unregister():
    """Unregister all addon classes from Blender."""
    package = __package__
    for name in reversed(_SUBMODULES):
        full = f"{package}.{name}"
        if full in sys.modules:
            try:
                mod = sys.modules[full]
                if hasattr(mod, "unregister"):
                    mod.unregister()
            except Exception as e:
                print(f"[Kawaii GN] Warning: Could not unload {name}: {e}")
