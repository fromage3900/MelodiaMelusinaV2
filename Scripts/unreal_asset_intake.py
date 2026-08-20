import unreal
import os

# Define source and destination paths
source_imports_dir = r"C:\EnvironmentPortfolio\BS_GodFile\Imports"
dest_audio_path = "/Game/Audio"
dest_env_path = "/Game/EnvSandbox/Meshes/Environment"

def import_assets():
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    
    # 1. Import Audio
    unreal.log("Scanning for audio files...")
    audio_dir = os.path.join(source_imports_dir, "Audio")
    audio_files = []
    if os.path.exists(audio_dir):
        for root, _, files in os.walk(audio_dir):
            for file in files:
                if file.lower().endswith((".wav", ".ogg")):
                    audio_files.append(os.path.join(root, file))
    
    if audio_files:
        audio_task = unreal.AssetImportTask()
        audio_task.set_editor_property('automated', True)
        audio_task.set_editor_property('destination_path', dest_audio_path)
        audio_task.set_editor_property('filenames', audio_files)
        audio_task.set_editor_property('replace_existing', True)
        audio_task.set_editor_property('save', False)
        asset_tools.import_asset_tasks([audio_task])
        unreal.log(f"Imported {len(audio_files)} Audio Files.")

    # 2. Import Meshes (FBX/glTF/OBJ) without generating materials
    unreal.log("Scanning for mesh files...")
    mesh_dir = os.path.join(source_imports_dir, "Environment")
    mesh_files = []
    if os.path.exists(mesh_dir):
        for root, _, files in os.walk(mesh_dir):
            for file in files:
                if file.lower().endswith((".fbx", ".obj", ".gltf", ".glb")):
                    mesh_files.append(os.path.join(root, file))
                    
    if mesh_files:
        fbx_options = unreal.FbxImportUI()
        fbx_options.set_editor_property('import_materials', False)
        fbx_options.set_editor_property('import_textures', False)
        
        mesh_task = unreal.AssetImportTask()
        mesh_task.set_editor_property('automated', True)
        mesh_task.set_editor_property('destination_path', dest_env_path)
        mesh_task.set_editor_property('filenames', mesh_files)
        mesh_task.set_editor_property('replace_existing', True)
        mesh_task.set_editor_property('save', False)
        mesh_task.options = fbx_options
        
        asset_tools.import_asset_tasks([mesh_task])
        unreal.log(f"Imported {len(mesh_files)} Mesh Files with material generation disabled.")

    unreal.log("Bulk Import Complete. Next step: Generate and Assign Material Instances.")

import_assets()
