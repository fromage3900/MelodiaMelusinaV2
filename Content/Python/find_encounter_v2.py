import unreal
L = unreal.log_warning

# Find encounter/trigger BPs by searching specific directories
dirs_to_search = [
    '/Game/Melodia/Enemies',
    '/Game/Melodia/Blueprints/Battle',
    '/Game/Melodia/Blueprints/Volumes',
    '/Game/Melodia/_PROJECT/Blueprints',
    '/Game/Melodia/Roguelike/Blueprints',
]

for d in dirs_to_search:
    if unreal.EditorAssetLibrary.does_directory_exist(d):
        assets = unreal.EditorAssetLibrary.list_assets(d, recursive=True, include_folder=False)
        for a in assets:
            L('Asset in {}: {}'.format(d, a))
    else:
        L('SKIP {} (not found)'.format(d))

L('DONE')
