# Blender Kawaii Geometry Nodes Addon
# Tools/BlenderAddons/blender_kawaii_gn/

bl_info = {
    "name": "Kawaii GN",
    "author": "fromage3900",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Kawaii GN",
    "description": "Procedural kawaii/chibi assets via Geometry Nodes",
    "category": "Kawaii GN",
}

import importlib
import sys

from . import core
from . import ui

# Reload on addon refresh
importlib.reload(core)
if hasattr(core, 'gn_framework'):
    importlib.reload(core.gn_framework)
if hasattr(core, 'node_builder'):
    importlib.reload(core.node_builder)
if hasattr(core, 'material_generator'):
    importlib.reload(core.material_generator)
if hasattr(core, 'operators'):
    importlib.reload(core.operators)

from . import generators
importlib.reload(generators)


def register():
    if hasattr(core, 'operators'):
        core.operators.register()
    if hasattr(ui, 'panel_main'):
        ui.panel_main.register()


def unregister():
    if hasattr(ui, 'panel_main'):
        ui.panel_main.unregister()
    if hasattr(core, 'operators'):
        core.operators.unregister()
