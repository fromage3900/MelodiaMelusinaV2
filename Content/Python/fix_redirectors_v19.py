import unreal

unreal.log('START')

# Test 1: Can we list assets at all?
try:
    assets = unreal.EditorAssetLibrary.list_assets('/Game/Characters', recursive=False, include_folder=False)
    unreal.log('Chars: {}'.format(len(assets)))
except Exception as ex:
    unreal.log('Chars FAIL: {}'.format(str(ex)))

# Test 2: Check a single asset class
try:
    test = '/Game/Characters/Melusina/BP_Melusina.BP_Melusina'
    ad = unreal.EditorAssetLibrary.find_asset_data(test)
    unreal.log('Class: {}'.format(str(ad.asset_class)))
    unreal.log('ClassPath: {}'.format(str(ad.asset_class_path)))
    unreal.log('ObjPath: {}'.format(str(ad.object_path)))
except Exception as ex:
    unreal.log('Find FAIL: {}'.format(str(ex)))

unreal.log('END')
