"""Try factory-based FBX animation import."""
import json, urllib.request

script = r"""
import unreal
import json

result = {}
fbx_path = r"G:\EnvironmentPortfolio\BS_GodFile\Imports\Mocap\RunCycle.fbx"

# Approach: Use FbxFactory to import animation sequence
try:
    # Create FBX factory
    factory = unreal.FbxFactory()
    # Configure for animation import
    anim_import_data = unreal.FbxAnimSequenceImportData()
    
    # Try to set animation length
    anim_import_data.set_editor_property("animation_length", unreal.FbxTimeSpan.INFINITE)
    
    fbx_import_ui = unreal.FbxImportUI()
    fbx_import_ui.set_editor_property("import_mesh", False)
    fbx_import_ui.set_editor_property("import_animations", True)
    fbx_import_ui.set_editor_property("import_as_skeletal", False)
    
    # Set the import data on the factory
    factory.set_editor_property("import_ui", fbx_import_ui)
    
    result["factory_ok"] = True
except Exception as e:
    result["factory_err"] = str(e)[:200]

# Approach 2: Use AssetTools.import_asset_tasks with UNSET options
# This means let UE decide based on FBX content
try:
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", fbx_path)
    task.set_editor_property("destination_path", "/Game/Melodia/Mocap/Source/Anims")
    task.set_editor_property("destination_name", "A_Src_RunCycle_v2")
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("automated", True)
    
    # Don't set options - let UE auto-detect
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    tools.import_asset_tasks([task])
    
    imported = task.get_editor_property("imported_object_paths")
    result["auto_import"] = [str(i) for i in imported]
except Exception as e:
    result["auto_import_err"] = str(e)[:200]

# Check what was created
assets = unreal.EditorAssetLibrary.list_assets("/Game/Melodia/Mocap/Source/Anims", False, False)
result["new_assets"] = [a for a in assets if "RunCycle" in a]

# Also check if any new assets were created in the Source root
all_source = unreal.EditorAssetLibrary.list_assets("/Game/Melodia/Mocap/Source", True, False)
result["all_source"] = [a for a in all_source if "RunCycle" in a]

print(json.dumps(result))
"""

with open(r'G:\EnvironmentPortfolio\BS_GodFile\Content\Python\_phase4_try_import9.py', 'w') as f:
    f.write(script)

req = urllib.request.Request(
    'http://127.0.0.1:9316/mcp',
    data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "editor_query",
                                "arguments": {"action": "run_python",
                                              "params": {"command": "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/_phase4_try_import9.py",
                                                         "mode": "execute_file"}}}}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
print(text[:3000])
