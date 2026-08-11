"""Final attempt - import with import_as_skeletal=True, import_mesh=False"""
import json, urllib.request

script = r"""
import unreal
import json

result = {}

task = unreal.AssetImportTask()
task.set_editor_property("filename", r"G:\EnvironmentPortfolio\BS_GodFile\Imports\Mocap\RunCycle.fbx")
task.set_editor_property("destination_path", "/Game/Melodia/Mocap/Source/Anims")
task.set_editor_property("destination_name", "A_Src_RunCycle_TEST")
task.set_editor_property("replace_existing", True)
task.set_editor_property("save", True)
task.set_editor_property("automated", True)

opts = unreal.FbxImportUI()

# Set skeleton
skel = unreal.load_asset("/Game/Melodia/Mocap/Source/SK_MocapSource_Skeleton.SK_MocapSource_Skeleton")
try:
    opts.set_editor_property("skeleton", skel)
    result["skeleton_set"] = True
except Exception as e:
    result["skeleton_set"] = str(e)[:100]

opts.set_editor_property("import_as_skeletal", True)
opts.set_editor_property("import_mesh", False)
opts.set_editor_property("import_animations", True)
opts.set_editor_property("import_textures", False)
opts.set_editor_property("import_materials", False)

task.set_editor_property("options", opts)

tools = unreal.AssetToolsHelpers.get_asset_tools()
tools.import_asset_tasks([task])

imported = task.get_editor_property("imported_object_paths")
result["imported"] = [str(i) for i in imported]
result["imported_count"] = len(imported)

# Check what got created
assets = unreal.EditorAssetLibrary.list_assets("/Game/Melodia/Mocap/Source/Anims", False, False)
result["anims_in_dir"] = len(assets)
test_assets = [a for a in assets if "RunCycle_TEST" in a]
result["test_assets"] = test_assets

print(json.dumps(result))
"""

with open(r'G:\EnvironmentPortfolio\BS_GodFile\Content\Python\_phase4_try_import8.py', 'w') as f:
    f.write(script)

req = urllib.request.Request(
    'http://127.0.0.1:9316/mcp',
    data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "editor_query",
                                "arguments": {"action": "run_python",
                                              "params": {"command": "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/_phase4_try_import8.py",
                                                         "mode": "execute_file"}}}}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
print(text[:3000])
