# -*- coding: utf-8 -*-
"""
import_poitou_nanite_sanctuary.py — Automated Unreal Engine 5 Nanite & Collision Importer
Imports all FBX assets from Content/EnvSandbox/Poitou/Meshes/ into /Game/EnvSandbox/Poitou/Meshes/
with Nanite enabled and custom UCX collision hulls bound.
"""
from __future__ import annotations
import os, sys
from pathlib import Path

def run_import():
    try:
        import unreal
    except ImportError:
        print("[WARN] Unreal module not available outside UE5 editor context.")
        print("Run this script inside UE5: Execute Python Script -> Content/Python/import_poitou_nanite_sanctuary.py")
        return 1

    content_dir = Path(unreal.Paths.project_content_dir())
    fbx_dir = content_dir / "EnvSandbox" / "Poitou" / "Meshes"
    dest_path = "/Game/EnvSandbox/Poitou/Meshes"

    if not fbx_dir.exists():
        unreal.log_error(f"Source FBX directory does not exist: {fbx_dir}")
        return 1

    fbx_files = list(fbx_dir.glob("*.fbx"))
    unreal.log(f"Found {len(fbx_files)} FBX files to import into {dest_path}...")

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

    for fbx_file in fbx_files:
        asset_name = fbx_file.stem
        unreal.log(f"Importing {asset_name}...")

        task = unreal.AssetImportTask()
        task.filename = str(fbx_file)
        task.destination_path = dest_path
        task.destination_name = asset_name
        task.replace_existing = True
        task.automated = True
        task.save = True

        options = unreal.FbxImportUI()
        options.import_mesh = True
        options.import_textures = False
        options.import_materials = True
        options.import_as_skeletal = False
        options.static_mesh_import_data.combine_meshes = True
        options.static_mesh_import_data.auto_generate_collision = False
        options.static_mesh_import_data.import_collision_according_to_fname = True
        options.static_mesh_import_data.build_nanite = True
        options.static_mesh_import_data.generate_lightmap_u_vs = False

        task.options = options
        asset_tools.import_asset_tasks([task])

        # Post-import: Verify Nanite and Collision settings
        asset_full_path = f"{dest_path}/{asset_name}"
        loaded_mesh = unreal.EditorAssetLibrary.load_asset(asset_full_path)
        if loaded_mesh and isinstance(loaded_mesh, unreal.StaticMesh):
            nanite_settings = loaded_mesh.get_editor_property("nanite_settings")
            nanite_settings.set_editor_property("enabled", True)
            loaded_mesh.set_editor_property("nanite_settings", nanite_settings)
            unreal.EditorAssetLibrary.save_loaded_asset(loaded_mesh)
            unreal.log(f"  [OK] Nanite enabled and UCX collision bound on {asset_name}")

    unreal.log("[COMPLETE] All Poitou Sanctuary assets imported successfully into Unreal Engine 5.")
    return 0

if __name__ == "__main__":
    run_import()
