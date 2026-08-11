import unreal
L = unreal.log_warning

# Scan ALL of /Game for ObjectRedirector assets
L('=== FULL REDIRECTOR SCAN ===')
assets = unreal.EditorAssetLibrary.list_assets('/Game', recursive=True, include_folder=False)
L('Total assets: {}'.format(len(assets)))

redirectors = []
for p in assets:
    try:
        ad = unreal.EditorAssetLibrary.find_asset_data(p)
        if str(ad.asset_class_path).find('ObjectRedirector') >= 0:
            redirectors.append(p)
    except:
        pass

L('Redirectors found: {}'.format(len(redirectors)))
for r in redirectors:
    L('  REDIR: {}'.format(r))

if redirectors:
    L('FIXING...')
    at = unreal.AssetToolsHelpers.get_asset_tools()
    try:
        at.fix_up_redirectors(redirectors)
        L('FIX_OK')
    except Exception as ex:
        L('FIX_FAILED: {}'.format(str(ex)))

# Also check the old paths
L('=== CHECK STALE PATHS ===')
for old_path in ['/Game/Characters/Melusina', '/Game/MagicianLabatory']:
    if unreal.EditorAssetLibrary.does_directory_exist(old_path):
        old_assets = unreal.EditorAssetLibrary.list_assets(old_path, recursive=True, include_folder=False)
        L('OLD PATH {}: {} assets'.format(old_path, len(old_assets)))
        for a in old_assets[:5]:
            L('  OLD: {}'.format(a))
    else:
        L('OLD PATH {}: NOT FOUND'.format(old_path))

L('DONE')
