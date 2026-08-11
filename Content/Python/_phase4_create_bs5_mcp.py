"""Check if blendspace exists and try to duplicate from another blendspace."""
import json, urllib.request

script = r"""
import unreal
import json

result = {}

# Check what's in the BlendSpaces directory
asst = unreal.EditorAssetLibrary
assets = asst.list_assets("/Game/Melodia/Characters/Melusina/BlendSpaces", False, False)
result["blendspace_assets"] = assets

# Check create_asset more carefully with error handling
try:
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    dir_path = "/Game/Melodia/Characters/Melusina/BlendSpaces"
    factory = unreal.BlendSpaceFactory1D()
    
    # The issue might be that the package path already has an object
    # Try with a unique name
    bs = asset_tools.create_asset("BS_Locomotion_v2", dir_path, None, factory)
    result["create_v2"] = str(bs) if bs else "None"
except Exception as e:
    result["create_v2_err"] = str(e)[:200]

# Try duplicate approach - find any blendspace in the project
try:
    all_assets = asst.list_assets("/Game", True, True)
    bs_assets = [a for a in all_assets if "BlendSpace" in a.split("/")[-1] and a.endswith(".BlendSpace1D")]
    result["found_bs"] = bs_assets[:10]
except Exception as e:
    result["found_bs_err"] = str(e)[:200]

print(json.dumps(result))
"""

with open(r'G:\EnvironmentPortfolio\BS_GodFile\Content\Python\_phase4_create_bs5.py', 'w') as f:
    f.write(script)

req = urllib.request.Request(
    'http://127.0.0.1:9316/mcp',
    data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "editor_query",
                                "arguments": {"action": "run_python",
                                              "params": {"command": "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/_phase4_create_bs5.py",
                                                         "mode": "execute_file"}}}}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
print(text[:3000])
