import unreal

# Try importing with default options (no options at all)
task = unreal.AssetImportTask()
task.set_editor_property("filename", r"G:\EnvironmentPortfolio\BS_GodFile\Imports\Mocap\RunCycle.fbx")
task.set_editor_property("destination_path", "/Game/Melodia/Mocap/Source/Anims")
task.set_editor_property("destination_name", "A_Src_RunCycle2")
task.set_editor_property("replace_existing", True)
task.set_editor_property("save", True)
task.set_editor_property("automated", True)

tools = unreal.AssetToolsHelpers.get_asset_tools()
tools.import_asset_tasks([task])

imported = task.get_editor_property("imported_object_paths")
unreal.log("=== DEFAULT IMPORT RESULT ===")
unreal.log(f"Imported count: {len(imported)}")
for i in imported:
    unreal.log(f"  - {i}")
unreal.log("================================")

# Check what's in the directory
assets = unreal.EditorAssetLibrary.list_assets("/Game/Melodia/Mocap/Source/Anims", False, False)
unreal.log(f"Total anims in Anims dir: {len(assets)}")
for a in assets:
    if "RunCycle" in a:
        unreal.log(f"  RunCycle asset: {a}")

# Also list what's in the Source dir root
root_assets = unreal.EditorAssetLibrary.list_assets("/Game/Melodia/Mocap/Source", False, False)
unreal.log("Source root assets:")
for a in root_assets:
    unreal.log(f"  {a}")
