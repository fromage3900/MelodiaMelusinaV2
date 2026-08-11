import bpy

reg_modules = [
    "server",
    "tools",
]

reg, unreg = bpy.utils.register_submodule_factory(__package__, reg_modules)


# Registration functions
def register():
    reg()


def unregister():
    unreg()
