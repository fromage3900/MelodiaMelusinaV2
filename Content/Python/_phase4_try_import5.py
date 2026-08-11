import unreal, json

def to_json_safe(obj):
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    try:
        return [to_json_safe(x) for x in obj]
    except:
        pass
    try:
        return str(obj)
    except:
        return repr(obj)

result = {}

# Use completely default options - let UE auto-detect
task = unreal.AssetImportTask()
task.set_editor_property("filename", r"G:\EnvironmentPortfolio\BS_GodFile\Imports\Mocap\RunCycle.fbx")
task.set_editor_property("destination_path", "/Game/Melodia/Mocap/Source/Anims")
task.set_editor_property("destination_name", "A_Src_RunCycle")
task.set_editor_property("replace_existing", True)
task.set_editor_property("save", True)
task.set_editor_property("automated", True)

# Try with completely default options (let UE decide)
tools = unreal.AssetToolsHelpers.get_asset_tools()
tools.import_asset_tasks([task])

imported = task.get_editor_property("imported_object_paths")
result["imported_without_options"] = to_json_safe(imported)

# Also try importing into the root Source dir to see what happens
task2 = unreal.AssetImportTask()
task2.set_editor_property("filename", r"G:\EnvironmentPortfolio\BS_GodFile\Imports\Mocap\RunCycle.fbx")
task2.set_editor_property("destination_path", "/Game/Melodia/Mocap/Source")
task2.set_editor_property("destination_name", "A_Src_RunCycle_Test")
task2.set_editor_property("replace_existing", True)
task2.set_editor_property("save", True)
task2.set_editor_property("automated", True)

tools.import_asset_tasks([task2])
imported2 = task2.get_editor_property("imported_object_paths")
result["imported_root"] = to_json_safe(imported2)

# List ALL assets in Source dir (recursive)
all_assets = unreal.EditorAssetLibrary.list_assets("/Game/Melodia/Mocap/Source", True, False)
result["all_source_assets"] = all_assets

print(json.dumps(result))
