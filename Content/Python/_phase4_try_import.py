import unreal, json
result = {"approaches": []}

# Approach 1: Use AssetTools.import_assets with automatic detection
try:
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    fbx_path = r"G:\EnvironmentPortfolio\BS_GodFile\Imports\Mocap\RunCycle.fbx"
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
