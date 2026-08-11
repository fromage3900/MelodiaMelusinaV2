
import unreal
import json

result = {}

asst = unreal.EditorAssetLibrary
dir_path = "/Game/Melodia/Characters/Melusina/BlendSpaces"
if not asst.does_directory_exist(dir_path):
    asst.make_directory(dir_path)

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
factory = unreal.BlendSpaceFactory1D()

# Try with explicit class
try:
    bs = asset_tools.create_asset("BS_Locomotion", dir_path, None, factory)
    result["with_none_class"] = bs is not None
except Exception as e:
    result["with_none_class_err"] = str(e)[:200]

# Try BlendSpaceFactoryNew instead
try:
    factory2 = unreal.BlendSpaceFactoryNew()
    bs2 = asset_tools.create_asset("BS_Locomotion", dir_path, None, factory2)
    result["with_factory_new"] = bs2 is not None
except Exception as e:
    result["with_factory_new_err"] = str(e)[:200]

# Check factory properties
try:
    result["factory_supported"] = str(factory.get_editor_property("supported_class"))
except:
    result["factory_supported"] = "ERR"

try:
    result["factory_format"] = str(factory.get_editor_property("format"))
except:
    result["factory_format"] = "ERR"

# Try importing from a different approach - duplicate existing
existing_bs = None
try:
    # Check if there's any existing blendspace we can duplicate
    all_assets = asst.list_assets("/Game/Melodia", True, False)
    bs_assets = [a for a in all_assets if "BlendSpace" in a.split("/")[-1]]
    result["existing_bs"] = bs_assets[:5]
except Exception as e:
    result["existing_bs_err"] = str(e)[:200]

# Check what factories are suported
try:
    # Maybe BlendSpaceFactory1D needs a skeleton set first?
    factory.set_editor_property("skeleton", unreal.load_asset("/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton.SK_Melusina_Skeleton"))
    bs3 = asset_tools.create_asset("BS_Locomotion2", dir_path, None, factory)
    result["with_preset_skel"] = bs3 is not None
except Exception as e:
    result["with_preset_skel_err"] = str(e)[:200]

print(json.dumps(result))
