import unreal

# Fix up all redirectors in the project
asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
ar_filter = unreal.ARFilter()
ar_filter.class_names = ['ObjectRedirector']
redirectors = asset_registry.get_assets(ar_filter)

print('Found {} redirectors'.format(len(redirectors)))

if redirectors:
    # Collect all packages with redirectors
    package_paths = []
    for asset_data in redirectors:
        package_paths.append(asset_data.package_name)
    
    # Fix up redirectors
    result = unreal.EditorAssetLibrary.fix_up_redirectors(package_paths)
    print('Fix up completed: {} packages processed'.format(len(package_paths)))
else:
    print('No redirectors found')

print('DONE')
