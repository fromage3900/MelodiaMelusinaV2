# Choral Sheep - Blender companion tools for the Choral Sheep character
# Tools/BlenderAddons/choral_sheep/
#
# This addon provides a Blender panel for the Choral Sheep shape-key library.
# Other tools (shine, bake_prep, export, preview) are standalone scripts
# meant to be run via exec() or blender --python.

bl_info = {
    "name": "Choral Sheep",
    "author": "fromage3900",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Choral Sheep",
    "description": "Choral Sheep companion tools - shape keys, materials, bake prep",
    "category": "Choral Sheep",
}

from . import sheep_shapekeys


def register():
    sheep_shapekeys.register()


def unregister():
    sheep_shapekeys.unregister()
