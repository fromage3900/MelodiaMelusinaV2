
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
