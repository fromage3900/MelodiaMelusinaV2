import unreal

# Second pass: prefix any remaining KB3D_ATL_* textures under Atlantis (first scan
# capped at 200 paths; 251 KB3D textures exist, ~78 still unpinned).
ROOT = '/Game/EnvSandbox/Textures/Atlantis'

ar = unreal.AssetRegistryHelpers.get_asset_registry()
assets = ar.get_assets_by_path(ROOT, recursive=True)
unreal.log_warning('TEX_PASS2 begin scanned=%d' % len(assets))

renamed = 0
failed = []
for a in assets:
    name = str(a.asset_name)
    cls = str(a.asset_class_path)
    if 'Texture2D' not in cls:
        continue
    if name.startswith('T_'):
        continue
    pkg = str(a.package_name)
    new_pkg = pkg.rsplit('/', 1)[0] + '/T_' + name
    try:
        if unreal.EditorAssetLibrary.rename_asset(pkg, new_pkg):
            renamed += 1
        else:
            failed.append(pkg)
    except Exception as ex:
        failed.append('%s :: %s' % (pkg, ex))

unreal.log_warning('TEX_PASS2 renamed=%d failed=%d' % (renamed, len(failed)))
for f in failed[:10]:
    unreal.log_warning('TEX_PASS2_FAIL %s' % f)

saved = unreal.EditorAssetLibrary.save_directory(ROOT, only_if_is_dirty=True, recursive=True)
unreal.log_warning('TEX_PASS2 save_directory=%s' % saved)