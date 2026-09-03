"""Brutalist GN Export Utilities."""
import bpy
import os


def export_to_fbx(obj, filepath):
    """Export object to FBX for UE5."""
    bpy.ops.export_scene.fbx(
        filepath=filepath,
        use_selection=True,
        axis_forward='-Z',
        axis_up='Y',
        mesh_smooth_type='FACE',
    )


def register(): pass
def unregister(): pass
