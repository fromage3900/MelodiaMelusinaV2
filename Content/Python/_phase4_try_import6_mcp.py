"""Try default import and log results."""
import json, urllib.request

script = r"""import unreal

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
"""

with open(r'G:\EnvironmentPortfolio\BS_GodFile\Content\Python\_phase4_try_import6.py', 'w') as f:
    f.write(script)

req = urllib.request.Request(
    'http://127.0.0.1:9316/mcp',
    data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "editor_query",
                                "arguments": {"action": "run_python",
                                              "params": {"command": "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/_phase4_try_import6.py",
                                                         "mode": "execute_file"}}}}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
# Just print the raw response to see what happened
print("Editor response received.")
# The output is in the MCP response - show any output messages
content = resp.get("result", {}).get("content", [{}])
for c in content:
    if c.get("type") == "text":
        txt = c.get("text", "")
        # Check for error
        if "error" in txt.lower() and "false" in txt:
            print(txt[:1000])
