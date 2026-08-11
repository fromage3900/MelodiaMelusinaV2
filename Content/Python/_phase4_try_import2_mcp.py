"""Try import_assets_automated with proper FBX import."""
import json, urllib.request

script = r"""import unreal, json
result = {}

# Approach: import_assets_automated 
try:
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    fbx_path = r"G:\EnvironmentPortfolio\BS_GodFile\Imports\Mocap\RunCycle.fbx"
    dest = "/Game/Melodia/Mocap/Source/Anims"
    
    # import_assets_automated takes (Filenames, DestinationPath) and returns list of UObjects
    imported = tools.import_assets_automated([fbx_path], dest)
    result["approach_auto"] = {
        "ok": True, 
        "count": len(imported) if imported else 0,
        "types": [i.get_class().get_name() for i in (imported or [])],
        "paths": [i.get_path_name() for i in (imported or [])]
    }
except Exception as e:
    result["approach_auto"] = {"ok": False, "error": str(e)[:300]}

# Check what got created
assets = unreal.EditorAssetLibrary.list_assets("/Game/Melodia/Mocap/Source/Anims", False, False)
runcycle_assets = [a for a in assets if "RunCycle" in a]
result["runcycle_assets"] = runcycle_assets

print(json.dumps(result))
"""

with open(r'G:\EnvironmentPortfolio\BS_GodFile\Content\Python\_phase4_try_import2.py', 'w') as f:
    f.write(script)

req = urllib.request.Request(
    'http://127.0.0.1:9316/mcp',
    data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "editor_query",
                                "arguments": {"action": "run_python",
                                              "params": {"command": "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/_phase4_try_import2.py",
                                                         "mode": "execute_file"}}}}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=120).read())
text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
parsed = json.loads(text)
print(json.dumps(parsed, indent=2))
