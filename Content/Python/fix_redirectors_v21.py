import unreal
import sys

L = unreal.log_warning

L('=== FIX REDIRECTORS START ===')

editor_asset_lib = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

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
        L('SKIP {} (not found)'.format(root))
        continue
    assets = editor_asset_lib.list_assets(root, recursive=True, include_folder=False)
    L('Scan {} -> {} assets'.format(root, len(assets)))
    for p in assets:
        try:
            ad = editor_asset_lib.find_asset_data(p)
            cls = str(ad.asset_class_path)
            if 'ObjectRedirector' in cls:
                all_redirectors.append(p)
                L('  REDIR: {}'.format(p))
        except:
            pass

L('Redirectors found: {}'.format(len(all_redirectors)))
for r in all_redirectors:
    L('  {}'.format(r))

if all_redirectors:
    L('Attempting fix_up_redirectors...')
    try:
        asset_tools.fix_up_redirectors(all_redirectors)
        L('Fix succeeded!')
    except Exception as ex:
        L('Fix failed: {}'.format(str(ex)))
        L('Deleting redirectors directly...')
        for r in all_redirectors:
            try:
                editor_asset_lib.delete_asset(r)
                L('  Deleted {}'.format(r))
            except Exception as ex2:
                L('  Failed {}: {}'.format(r, str(ex2)))
else:
    L('No redirectors to fix.')

L('=== FIX REDIRECTORS DONE ===')
