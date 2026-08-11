"""Try multiple FBX import approaches and report results."""
import json, urllib.request

def mcp_file(path):
    with open(path, 'r') as f:
        return f.read()

script = """import unreal, json
result = {"approaches": []}

# Approach 1: Use AssetTools.import_assets with automatic detection
try:
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    fbx_path = r"G:\\EnvironmentPortfolio\\BS_GodFile\\Imports\\Mocap\\RunCycle.fbx"
    dest = "/Game/Melodia/Mocap/Source/Anims"
    imported = tools.import_assets([fbx_path], dest)
    result["approach1"] = {"ok": True, "count": len(imported) if imported else 0, "imported": [str(i) for i in (imported or [])]}
except Exception as e:
    result["approach1"] = {"ok": False, "error": str(e)[:200]}

# Check what got created
assets = unreal.EditorAssetLibrary.list_assets("/Game/Melodia/Mocap/Source/Anims", False, False)
runcycle_assets = [a for a in assets if "RunCycle" in a]
result["runcycle_assets"] = runcycle_assets

print(json.dumps(result))
"""

with open(r'G:\EnvironmentPortfolio\BS_GodFile\Content\Python\_phase4_try_import.py', 'w') as f:
    f.write(script)

req = urllib.request.Request(
    'http://127.0.0.1:9316/mcp',
    data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "editor_query",
                                "arguments": {"action": "run_python",
                                              "params": {"command": "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/_phase4_try_import.py",
                                                         "mode": "execute_file"}}}}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
parsed = json.loads(text)
print("Approach 1:", json.dumps(parsed.get("approach1", {}), indent=2))
print("RunCycle assets:", json.dumps(parsed.get("runcycle_assets", []), indent=2))
