import unreal

editor_asset_lib = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

# Target specific directories known to have redirector issues
targets = [
    '/Game/Characters',
    '/Game/MagicianLabatory',
    '/Game/Melodia',
    '/Game/EnvSandbox',
    '/Game/Blueprints',
    '/Game/Library',
]

all_redirectors = []
for root in targets:
    assets = editor_asset_lib.list_assets(root, recursive=True, include_folder=False)
    for p in assets:
        try:
            ad = editor_asset_lib.find_asset_data(p)
            cls_path = str(ad.asset_class_path)
            if 'ObjectRedirector' in cls_path:
                all_redirectors.append(p)
                unreal.log('REDIR: {}'.format(p))
        except:
            pass

unreal.log('TOTAL: {}'.format(len(all_redirectors)))

if all_redirectors:
    unreal.log('FIXING...')
    try:
        asset_tools.fix_up_redirectors(all_redirectors)
        unreal.log('FIX_OK')
    except Exception as ex:
        unreal.log('FIX_FAILED: {}'.format(str(ex)))
        for r in all_redirectors:
            try:
                editor_asset_lib.delete_asset(r)
                unreal.log('DEL: {}'.format(r))
            except Exception as ex2:
                unreal.log('DELFAIL: {}'.format(str(ex2)))

unreal.log('DONE')
