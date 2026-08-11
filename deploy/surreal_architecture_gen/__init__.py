"""Melodia Studio — Surreal Architecture Generator for Blender 5.1."""
from __future__ import annotations

import sys
import os
from pathlib import Path

from ._version import BLENDER_MIN, BLENDER_TESTED, BLENDER_VERSION
from .compat import check_blender_version

check_blender_version()

import bpy

from . import core, integration, ui, mcp_bridge

__version__ = BLENDER_VERSION

bl_info = {
    "name": "Melodia Studio — Surreal Architecture",
    "author": "Melodia Team",
    "description": "Procedural surreal architecture with style genomes, greybox kits, and Nikki material vocabulary.",
    "version": BLENDER_VERSION,
    "blender": BLENDER_MIN,
    "location": "Properties > Modifiers",
    "category": "Geometry Nodes",
}

_m = None

def _get_monolith():
    global _m
    if _m is None:
        _m = core.monolith
    return _m

def register():
    monolith = core.monolith
    integration.register_overhaul(monolith)
    ui.register_ui()
    mcp_bridge.register_tools()

def unregister():
    ui.unregister_ui()
    integration.unregister_overhaul()
    mcp_bridge.unregister_tools()

if __name__ == "__main__":
    register()