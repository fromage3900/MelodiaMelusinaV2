"""Try creating blendspace with directory creation first."""
import json, urllib.request

script = r"""
import unreal
import json

result = {"steps": [], "errors": []}

# Step 1: Ensure directory exists
asst = unreal.EditorAssetLibrary
dir_path = "/Game/Melodia/Characters/Melusina/BlendSpaces"
if not asst.does_directory_exist(dir_path):
    asst.make_directory(dir_path)
    result["steps"].append(f"Created directory {dir_path}")

# Step 2: Check available factory classes
factory_classes = [c for c in dir(unreal) if 'BlendSpace' in c and 'Factory' in c]
result["available_factories"] = factory_classes

# Step 3: Try creating with a different factory name
try:
    factory = unreal.BlendSpaceFactory1D()
    result["factory_created"] = str(type(factory).__name__)
except Exception as e:
    result["factory_error"] = str(e)[:200]

# Step 4: Try create_asset with specific factory
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
try:
    bs = asset_tools.create_asset("BS_Locomotion", dir_path, None, factory)
    result["bs_created"] = bs is not None
    if bs:
        result["bs_class"] = bs.get_class().get_name()
except Exception as e:
    result["create_error"] = str(e)[:200]

# Step 5: Alternative - try with AssetSubsystem
try:
    asset_subsystem = unreal.get_engine_subsystem(unreal.AssetEditorSubsystem)
    result["asset_subsystem"] = asset_subsystem is not None
except Exception as e:
    result["subsystem_error"] = str(e)[:200]

print(json.dumps(result))
"""

with open(r'G:\EnvironmentPortfolio\BS_GodFile\Content\Python\_phase4_create_bs2.py', 'w') as f:
    f.write(script)

req = urllib.request.Request(
    'http://127.0.0.1:9316/mcp',
    data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "editor_query",
                                "arguments": {"action": "run_python",
                                              "params": {"command": "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/_phase4_create_bs2.py",
                                                         "mode": "execute_file"}}}}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
print(text[:3000])
