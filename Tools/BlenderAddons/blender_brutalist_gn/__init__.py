"""
Melodia Brutalist Geometry Nodes — Blender Python Addon
========================================================
Procedural Brutalist architecture generators using Geometry Nodes.

Features:
  - Monolithic concrete forms
  - Modular repetitive facades
  - Raw structural elements
  - Tower blocks and monuments
  - Balconies and pilotis
  - Housing estates and civic centers
  
All generators are fully non-destructive with live parameter adjustment!
"""

bl_info = {
    "name": "Melodia Brutalist Geometry Nodes",
    "author": "Melodia Studio",
    "version": (2, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Melodia Brutalist GN",
    "description": "Procedural Brutalist architecture using Geometry Nodes",
    "category": "Geometry Nodes",
}

import bpy
import importlib
import sys

ADDON_NAME = "melobrutalist"
OPERATOR_PREFIX = "melobrutalist_gn"
BL_CATEGORY = "Melodia Brutalist GN"

_SUBMODULES = [
    # Core
    "core.gn_framework",
    "core.operators",
    # Generators
    "generators.walls",
    "generators.structures",
    "generators.details",
    "generators.complexes",
    # UI
    "ui.panel_main",
    # Utilities
    "utils.export",
]


def register():
    """Register all addon classes."""
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
            print(f"[Brutalist GN] Warning: Could not load {name}: {e}")
    
    print("[Brutalist GN] ✓ Registered - Procedural Brutalist Architecture!")


def unregister():
    """Unregister all addon classes."""
    package = __package__
    for name in reversed(_SUBMODULES):
        full = f"{package}.{name}"
        if full in sys.modules:
            try:
                mod = sys.modules[full]
                if hasattr(mod, "unregister"):
                    mod.unregister()
            except Exception as e:
                print(f"[Brutalist GN] Warning: Could not unload {name}: {e}")
