"""Try EditorAssetLibrary.create_asset and list all create methods."""
import json, urllib.request

script = r"""
import unreal
import json

result = {}

# Check EditorAssetLibrary.create_asset
try:
    asst = unreal.EditorAssetLibrary
    # Create a test blendspace
    bs = asst.create_asset("BS_Locomotion_v3", "/Game/Melodia/Characters/Melusina/BlendSpaces", None, None)
    result["editorlib_create"] = str(bs) if bs else "None"
except Exception as e:
    result["editorlib_create_err"] = str(e)[:200]

# Check all create methods on EditorAssetLibrary
result["editorlib_methods"] = [m for m in dir(unreal.EditorAssetLibrary) if "create" in m.lower() or "import" in m.lower()]

# Check AssetTools.create_asset more carefully
try:
    at = unreal.AssetToolsHelpers.get_asset_tools()
    # Try creating a simple data asset first (should always work)
    factory_t = unreal.DataAssetFactory()
    da = at.create_asset("DA_Test", "/Game/Melodia/Characters/Melusina/BlendSpaces", None, factory_t)
    result["data_asset_test"] = str(da) if da else "None"
    
    # Clean up test
    if da:
        unreal.EditorAssetLibrary.delete_asset("/Game/Melodia/Characters/Melusina/BlendSpaces/DA_Test.DA_Test")
        result["cleaned"] = True
except Exception as e:
    result["data_asset_test_err"] = str(e)[:200]

print(json.dumps(result))
"""

with open(r'G:\EnvironmentPortfolio\BS_GodFile\Content\Python\_phase4_create_bs6.py', 'w') as f:
    f.write(script)

req = urllib.request.Request(
    'http://127.0.0.1:9316/mcp',
    data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "editor_query",
                                "arguments": {"action": "run_python",
                                              "params": {"command": "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/_phase4_create_bs6.py",
                                                         "mode": "execute_file"}}}}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
print(text[:3000])
