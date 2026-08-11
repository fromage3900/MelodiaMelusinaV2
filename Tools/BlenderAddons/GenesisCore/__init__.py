# type: ignore
bl_info = {
    "name": "GenesisCore",
    "author": "幻之境开发小组-会飞的键盘侠(KarryCharon)、只剩一瓶辣椒酱",
    "version": (0, 0, 1),
    "blender": (4, 0, 0),
    "location": "3DView > UI > GenesisCore",
    "category": "AI",
}

import bpy

reg_modules = [
    "src",
]

reg, unreg = bpy.utils.register_submodule_factory(__package__, reg_modules)


def register():
    reg()


def unregister():
    unreg()
