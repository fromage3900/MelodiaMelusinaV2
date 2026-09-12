#!/usr/bin/env python3
"""
Import Resonant World chunks into Blender.
Creates one mesh object per block type with proper materials.
Run from Blender's Python console or as a script.
"""

import bpy
import os
import glob

def_import_dir = None  # will be auto-detected

def get_chunks_dir():
    """Find the chunks directory relative to this script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    chunks_dir = os.path.join(script_dir, 'chunks')
    if os.path.isdir(chunks_dir):
        return chunks_dir
    return None


def create_material(name, color):
    """Create a simple Principled BSDF material."""
    mat = bpy.data.materials.new(name=f"RW_{name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs['Base Color'].default_value = (*color, 1.0)
        bsdf.inputs['Roughness'].default_value = 0.7
        if name == 'crystal':
            bsdf.inputs['Roughness'].default_value = 0.2
            bsdf.inputs['Metallic'].default_value = 0.3
        elif name == 'gold':
            bsdf.inputs['Metallic'].default_value = 0.8
            bsdf.inputs['Roughness'].default_value = 0.3
    return mat


def import_chunks():
    chunks_dir = get_chunks_dir()
    if not chunks_dir:
        print("Chunks directory not found. Run midi_voxel_v2.py first.")
        return

    obj_files = sorted(glob.glob(os.path.join(chunks_dir, "chunk_*.obj")))
    if not obj_files:
        print("No chunk files found.")
        return

    print(f"Found {len(obj_files)} chunks")

    # Create materials
    block_colors = {
        'stone': (0.45, 0.42, 0.40),
        'wood': (0.55, 0.35, 0.20),
        'crystal': (0.30, 0.65, 0.95),
        'gold': (0.95, 0.78, 0.20),
    }

    # Import all chunks into one collection
    collection = bpy.data.collections.new("ResonantWorld")
    bpy.context.scene.collection.children.link(collection)

    imported = 0
    for obj_path in obj_files:
        chunk_name = os.path.splitext(os.path.basename(obj_path))[0]

        # Import OBJ
        bpy.ops.import_scene.obj(filepath=obj_path, use_split_objects=False)
        obj = bpy.context.selected_objects[0] if bpy.context.selected_objects else None

        if obj:
            obj.name = chunk_name
            # Move to our collection
            for col in obj.users_collection:
                col.objects.unlink(obj)
            collection.objects.link(obj)
            imported += 1

    print(f"Imported {imported} chunks into 'ResonantWorld' collection")

    # Frame all
    bpy.ops.object.select_all(action='DESELECT')
    for obj in collection.objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = collection.objects[0] if collection.objects else None


def clear_world():
    """Remove existing ResonantWorld collection."""
    collection = bpy.data.collections.get("ResonantWorld")
    if collection:
        for obj in list(collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(collection)
        print("Cleared ResonantWorld")


# Run
if __name__ == '__main__':
    import_chunks()
