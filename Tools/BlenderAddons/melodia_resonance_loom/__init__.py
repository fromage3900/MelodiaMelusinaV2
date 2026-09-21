# Resonance Loom - author garments that listen to the battle beat.
# Copyright (c) 2026 fromage3900 / Melodia Project - MIT
#
# Blender 5.x addon. bl_info minimum follows the sibling addons (4.0) so the
# same folder loads on every workstation Blender in this project.
#
# Register is idempotent-safe for module reloads: bpy imports happen in the
# submodule files so `python -m unittest` on loom_core never needs bpy.

bl_info = {
    "name": "Resonance Loom",
    "author": "fromage3900",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Melodia > Resonance Loom",
    "description": (
        "Tailor garments to the project beatgrid: parse the battle MIDI, "
        "paint rhythm weights, bake Tier-A flourish shape keys, validate "
        "against the wardrobe contract, export FBX + rhythm sidecar."
    ),
    "doc_url": "Tools/BlenderAddons/melodia_resonance_loom/docs/RESONANCE_LOOM.md",
    "category": "Melodia",
}


def register():
    # Import here so loading this module outside Blender (tests) never touches bpy.
    from . import properties, operators, panel

    properties.register()
    operators.register()
    panel.register()


def unregister():
    from . import properties, operators, panel

    panel.unregister()
    operators.unregister()
    properties.unregister()
