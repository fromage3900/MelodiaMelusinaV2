"""Try AutomatedAssetImportData approach."""
import json, urllib.request

script = r"""import unreal, json
result = {}

try:
    # Use AutomatedAssetImportData
    import_data = unreal.AutomatedAssetImportData()
    import_data.set_editor_property("filenames", [r"G:\EnvironmentPortfolio\BS_GodFile\Imports\Mocap\RunCycle.fbx"])
    import_data.set_editor_property("destination_path", "/Game/Melodia/Mocap/Source/Anims")
    import_data.set_editor_property("replace_existing", True)
    import_data.set_editor_property("skip_read_only", False)
    
    # Set the import options for the group
    opts = unreal.FbxImportUI()
    skel = unreal.load_asset("/Game/Melodia/Mocap/Source/SK_MocapSource_Skeleton.SK_MocapSource_Skeleton")
    opts.set_editor_property("skeleton", skel)
    opts.set_editor_property("import_mesh", False)
    opts.set_editor_property("import_animations", True)
    opts.set_editor_property("import_as_skeletal", False)
    opts.set_editor_property("import_textures", False)
    opts.set_editor_property("import_materials", False)
    
    import_data.set_editor_property("factory", opts.DefaultSkeletalMeshFactory)
    
    result["import_data_ok"] = True
except Exception as e:
    result["error_setup"] = str(e)[:300]

# Try simpler: just use AssetImportTask again but with more verbose logging
try:
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", r"G:\EnvironmentPortfolio\BS_GodFile\Imports\Mocap\RunCycle.fbx")
    task.set_editor_property("destination_path", "/Game/Melodia/Mocap/Source/Anims")
    task.set_editor_property("destination_name", "A_Src_RunCycle")
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("automated", True)
    
    opts = unreal.FbxImportUI()
    skel = unreal.load_asset("/Game/Melodia/Mocap/Source/SK_MocapSource_Skeleton.SK_MocapSource_Skeleton")
    opts.set_editor_property("skeleton", skel)
    opts.set_editor_property("import_mesh", False)
    opts.set_editor_property("import_animations", True)
    opts.set_editor_property("import_as_skeletal", True)
    opts.set_editor_property("import_textures", False)
    opts.set_editor_property("import_materials", False)
    
    task.set_editor_property("options", opts)
    
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    tools.import_asset_tasks([task])
    
    result["task_imported"] = task.get_editor_property("imported_object_paths")
    result["task_error"] = task.get_editor_property("error")
    # Check what got created
    assets = unreal.EditorAssetLibrary.list_assets("/Game/Melodia/Mocap/Source/Anims", False, False)
    runcycle_assets = [a for a in assets if "RunCycle" in a and "Sprint" not in a]
    result["new_runcycle"] = runcycle_assets
except Exception as e:
    result["task_error_exc"] = str(e)[:300]

print(json.dumps(result))
"""

with open(r'G:\EnvironmentPortfolio\BS_GodFile\Content\Python\_phase4_try_import3.py', 'w') as f:
    f.write(script)

req = urllib.request.Request(
    'http://127.0.0.1:9316/mcp',
    data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "editor_query",
                                "arguments": {"action": "run_python",
                                              "params": {"command": "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/_phase4_try_import3.py",
                                                         "mode": "execute_file"}}}}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
print(text[:3000])
