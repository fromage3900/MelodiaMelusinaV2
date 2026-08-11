
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
