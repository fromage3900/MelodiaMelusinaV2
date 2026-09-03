# GenesisCore — MCP Client Addon for Blender
# Tools/BlenderAddons/GenesisCore/

bl_info = {
    "name": "GenesisCore",
    "author": "fromage3900",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > GenesisCore",
    "description": "MCP client for AI providers (Claude, DeepSeek, Ollama, OpenAI, etc.)",
    "category": "GenesisCore",
}

import importlib

from . import src

importlib.reload(src)


def register():
    if hasattr(src, 'ui'):
        src.ui.register()
    if hasattr(src, 'preference'):
        src.preference.register()
    if hasattr(src, 'operator'):
        src.operator.register()


def unregister():
    if hasattr(src, 'operator'):
        src.operator.unregister()
    if hasattr(src, 'preference'):
        src.preference.unregister()
    if hasattr(src, 'ui'):
        src.ui.unregister()
