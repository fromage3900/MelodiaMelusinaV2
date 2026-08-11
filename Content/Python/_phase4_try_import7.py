import unreal

# Use the source skeletal mesh (which knows its skeleton)
src_mesh = unreal.load_asset("/Game/Melodia/Mocap/Source/SK_MocapSource.SK_MocapSource")
if not src_mesh:
    unreal.log_error("Source mesh not found!")
else:
    # Approach: use FbxImportUI with skeletal_mesh set
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", r"G:\EnvironmentPortfolio\BS_GodFile\Imports\Mocap\RunCycle.fbx")
    task.set_editor_property("destination_path", "/Game/Melodia/Mocap/Source/Anims")
    task.set_editor_property("destination_name", "A_Src_RunCycle3")
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("automated", True)
    
    opts = unreal.FbxImportUI()
    opts.set_editor_property("skeletal_mesh", src_mesh)
    opts.set_editor_property("import_mesh", False)
    opts.set_editor_property("import_animations", True)
    opts.set_editor_property("import_as_skeletal", True)
    opts.set_editor_property("import_textures", False)
    opts.set_editor_property("import_materials", False)
    
    task.set_editor_property("options", opts)
    
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    tools.import_asset_tasks([task])
    
    imported = task.get_editor_property("imported_object_paths")
    unreal.log(f"Imported: {[str(i) for i in imported]}")

# Check result
assets = unreal.EditorAssetLibrary.list_assets("/Game/Melodia/Mocap/Source/Anims", False, False)
runcycle_assets = [a for a in assets if "RunCycle3" in a]
unreal.log(f"RunCycle3 assets: {runcycle_assets}")
