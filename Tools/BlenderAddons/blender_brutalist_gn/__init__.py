# Blender Brutalist Geometry Nodes Addon
# Tools/BlenderAddons/blender_brutalist_gn/

bl_info = {
    "name": "Brutalist GN",
    "author": "fromage3900",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Brutalist GN",
    "description": "Procedural monolithic concrete architecture via Geometry Nodes",
    "category": "Brutalist GN",
}

import importlib

from . import core
from . import ui
from . import generators
from . import utils

importlib.reload(core)
importlib.reload(ui)
importlib.reload(generators)
importlib.reload(utils)


def register():
    if hasattr(core, 'operators'):
        core.operators.register()


def unregister():
    if hasattr(core, 'operators'):
        core.operators.unregister()
