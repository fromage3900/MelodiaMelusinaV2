import unreal

# Atlantis KB3D pattern rename — BldgLgPalace_A_KB3D_ATL_BldgLgPalace_A_* -> SM_ATL_Palace_*
# Engine-native path: unreal.EditorAssetLibrary.rename_asset (IAssetTools rename with
# reference fixup + redirector creation). No class loading, package operations only.

OLD = "BldgLgPalace_A_KB3D_ATL_BldgLgPalace_A_"
NEW = "SM_ATL_Palace_"
ROOT = "/Game/EnvSandbox/Meshes/Atlantis"

ar = unreal.AssetRegistryHelpers.get_asset_registry()
assets = ar.get_assets_by_path(ROOT, recursive=True)
unreal.log_warning("ATL_RENAME begin scanned=%d" % len(assets))

renamed = 0
failed = []
skipped = 0
for a in assets:
    name = str(a.asset_name)
    if not name.startswith(OLD):
        skipped += 1
        continue
    pkg = str(a.package_name)
    new_pkg = pkg.replace(OLD, NEW, 1)
    try:
        if unreal.EditorAssetLibrary.rename_asset(pkg, new_pkg):
            renamed += 1
        else:
            failed.append(pkg)
    except Exception as ex:
        failed.append("%s :: %s" % (pkg, ex))

unreal.log_warning("ATL_RENAME renamed=%d failed=%d skipped=%d" % (renamed, len(failed), skipped))
for f in failed[:15]:
    unreal.log_warning("ATL_FAIL %s" % f)

# Unattended save of the touched directory (redirectors + renamed assets).
saved = unreal.EditorAssetLibrary.save_directory(ROOT, only_if_is_dirty=True, recursive=True)
unreal.log_warning("ATL_RENAME save_directory returned=%s" % saved)
