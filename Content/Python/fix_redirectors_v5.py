import unreal

ar_filter = unreal.ARFilter()
ar_filter.class_names = ['ObjectRedirector']

asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
redirectors = asset_registry.get_assets(ar_filter)

print('Found {} redirectors'.format(len(redirectors)))

if redirectors:
    packages_to_fix = []
    for asset_data in redirectors:
        packages_to_fix.append(asset_data.package_name)
    unreal.EditorAssetLibrary.fix_up_redirector(packages_to_fix)
    print('Fixed {} redirector packages'.format(len(packages_to_fix)))
else:
    print('No redirectors to fix')
print('DONE')
