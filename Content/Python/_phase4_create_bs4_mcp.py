"""Try create_asset with explicit class and factory methods."""
import json, urllib.request

script = r"""
import unreal
import json

result = {}

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
dir_path = "/Game/Melodia/Characters/Melusina/BlendSpaces"

# Check create_asset signature
try:
    import inspect
    sig = str(inspect.signature(asset_tools.create_asset))
    result["create_asset_sig"] = sig
except:
    result["create_asset_sig"] = "inspect failed"

# Try with explicit BlendSpace1D class
try:
    bs_class = unreal.load_class(None, "/Script/Engine.BlendSpace1D")
    factory = unreal.BlendSpaceFactory1D()
    bs = asset_tools.create_asset("BS_Locomotion", dir_path, bs_class, factory)
    result["with_explicit_class"] = bs is not None
except Exception as e:
    result["with_explicit_class_err"] = str(e)[:200]

# Try using the factory directly
try:
    factory = unreal.BlendSpaceFactory1D()
    # Some UE factory classes need to be configured with an asset type
    result["factory_methods"] = [m for m in dir(factory) if m.startswith("factory")]
except Exception as e:
    result["factory_methods_err"] = str(e)[:100]

# Try using import_object instead
try:
    # Check if there's a way to create via import
    result["import_methods"] = [m for m in dir(unreal.AssetToolsHelpers.get_asset_tools()) if "import" in m.lower()]
except Exception as e:
    pass

# Try direct package creation
try:
    pkg = unreal.load_package("/Game/Melodia/Characters/Melusina/BlendSpaces/BS_Locomotion")
    result["load_pkg"] = str(pkg) if pkg else "None"
except:
    result["load_pkg"] = "ERR"

print(json.dumps(result))
"""

with open(r'G:\EnvironmentPortfolio\BS_GodFile\Content\Python\_phase4_create_bs4.py', 'w') as f:
    f.write(script)

req = urllib.request.Request(
    'http://127.0.0.1:9316/mcp',
    data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "editor_query",
                                "arguments": {"action": "run_python",
                                              "params": {"command": "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/_phase4_create_bs4.py",
                                                         "mode": "execute_file"}}}}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
print(text[:3000])
