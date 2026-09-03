import unreal

unreal.log('=== FIX REDIRECTORS START ===')

editor_asset_lib = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

# Targeted directories most likely to have redirectors
targets = [
    '/Game/EnvSandbox/Materials',
    '/Game/Characters',
    '/Game/MagicianLabatory',
    '/Game/Library',
    '/Game/Blueprints',
]

all_redirectors = []
for root in targets:
    if not editor_asset_lib.does_directory_exist(root):
        unreal.log('SKIP {} (not found)'.format(root))
        continue
    assets = editor_asset_lib.list_assets(root, recursive=True, include_folder=False)
    for p in assets:
        try:
            ad = editor_asset_lib.find_asset_data(p)
            if str(ad.asset_class) == 'ObjectRedirector':
                all_redirectors.append(p)
        except:
            pass

unreal.log('Redirectors found: {}'.format(len(all_redirectors)))
for r in all_redirectors:
    unreal.log('  {}'.format(r))

if all_redirectors:
    unreal.log('Attempting fix_up_redirectors...')
    try:
        asset_tools.fix_up_redirectors(all_redirectors)
        unreal.log('Fix succeeded!')
    except Exception as ex:
        unreal.log('Fix failed: {}'.format(str(ex)))
        unreal.log('Deleting redirectors directly...')
        for r in all_redirectors:
            try:
                editor_asset_lib.delete_asset(r)
                unreal.log('  Deleted {}'.format(r))
            except Exception as ex2:
                unreal.log('  Failed {}: {}'.format(r, str(ex2)))
else:
    unreal.log('No redirectors to fix.')

unreal.log('=== FIX REDIRECTORS DONE ===')
