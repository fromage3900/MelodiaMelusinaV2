import unreal

# Use ClassPaths (SoftObjectPath) not deprecated class_names
redirector_cls = unreal.SoftObjectPath('/Script/CoreUObject.ObjectRedirector')
ar_filter = unreal.ARFilter(class_paths=[redirector_cls])

asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

unreal.log('Searching for redirectors...')
redirectors = asset_registry.get_assets(ar_filter)
unreal.log('Redirectors found: {}'.format(len(redirectors)))

for r in redirectors:
    pkg = r.package_name
    unreal.log('  {}'.format(pkg))
    # Try to delete the redirector
    try:
        unreal.EditorAssetLibrary.delete_asset(str(pkg))
        unreal.log('  Deleted: {}'.format(pkg))
    except Exception as e:
        unreal.log('  Failed: {}'.format(str(e)))

unreal.log('DONE')
