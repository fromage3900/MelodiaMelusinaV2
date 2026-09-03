import unreal, sys
L = unreal.log_warning

PATH_MAP = [
    ('/Game/Characters/Melusina/', '/Game/Melodia/Characters/Melusina/'),
    ('/Game/MagicianLabatory/', '/Game/Library/Migrated/MagiciansLibrary/'),
]

def try_find(path_str, asset_name):
    path_str = path_str.split('.')[0]
    for old, new in PATH_MAP:
        if old in path_str:
            alt = path_str.replace(old, new)
            if unreal.EditorAssetLibrary.does_asset_exist(alt):
                return alt
    for _, new in PATH_MAP:
        d = new.rstrip('/')
        for name in [asset_name, asset_name + '_INST']:
            c = d + '/' + name
            if unreal.EditorAssetLibrary.does_asset_exist(c):
                return c
    return None

ar = unreal.AssetRegistryHelpers.get_asset_registry()
ar.wait_for_completion()
all_assets = ar.get_all_assets()

game_paths = ['/Game/Melodia/', '/Game/Library/', '/Game/EnvSandbox/']
sm_assets = [a for a in all_assets 
    if 'StaticMesh' in str(a.asset_class_path) and 'StaticMeshActor' not in str(a.asset_class_path)
    and any(str(a.package_path).startswith(p) for p in game_paths)]
L('Game StaticMesh assets: {}'.format(len(sm_assets)))

fixed = 0
for ad in sm_assets:
    try:
        m = ad.get_asset()
        slots = m.get_editor_property('static_materials')
        chg = False
        for s in slots:
            mi = s.get_editor_property('material_interface')
            if mi is None:
                sn = str(s.material_slot_name)
                r = try_find(sn, str(ad.asset_name))
                if r:
                    a = unreal.EditorAssetLibrary.load_asset(r)
                    if a:
                        s.set_editor_property('material_interface', a)
                        L('FIXED {} slot {} -> {}'.format(ad.asset_name, sn, r))
                        fixed += 1
                        chg = True
                    else:
                        L('BROKEN {} slot {} (load fail)'.format(ad.asset_name, sn))
                else:
                    L('BROKEN {} slot {} (no match)'.format(ad.asset_name, sn))
        if chg:
            unreal.EditorAssetLibrary.save_asset(ad.object_path.to_deprecated_string(), only_if_is_dirty=True)
    except Exception as e:
        L('ERROR {}: {}'.format(ad.asset_name, str(e)))

L('DONE fixed={} checked={}'.format(fixed, len(sm_assets)))
