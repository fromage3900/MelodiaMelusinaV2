import unreal, json
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
