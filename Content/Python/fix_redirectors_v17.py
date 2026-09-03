import unreal

asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
editor_asset_lib = unreal.EditorAssetLibrary

# Use /Game as root for list_assets
all_assets = editor_asset_lib.list_assets('/Game', recursive=True, include_folder=False)
unreal.log('Total assets scanned: {}'.format(len(all_assets)))

redirectors = []
for p in all_assets:
    try:
        ad = editor_asset_lib.find_asset_data(p)
        cls_name = str(ad.asset_class)
        if cls_name == 'ObjectRedirector':
            redirectors.append(p)
    except:
        pass

unreal.log('Redirectors found: {}'.format(len(redirectors)))
for r in redirectors:
    unreal.log('  {}'.format(r))

if redirectors:
    unreal.log('Attempting fix_up_redirectors...')
    try:
        asset_tools.fix_up_redirectors(redirectors)
        unreal.log('fix_up_redirectors succeeded!')
    except Exception as ex:
        unreal.log('fix_up_redirectors failed: {}'.format(str(ex)))
        unreal.log('Plan B: deleting redirectors...')
        for r in redirectors:
            try:
                editor_asset_lib.delete_asset(r)
                unreal.log('  Deleted {}'.format(r))
            except Exception as ex2:
                unreal.log('  Failed {}: {}'.format(r, str(ex2)))

unreal.log('DONE')
