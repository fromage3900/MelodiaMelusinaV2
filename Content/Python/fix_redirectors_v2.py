import unreal

# Use AssetRegistry to find all redirectors
asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
redirectors = asset_registry.get_assets_by_class('ObjectRedirector')
print('Found {} redirectors'.format(len(redirectors)))

if redirectors:
    # Get package paths
    packages = []
    for asset in redirectors:
        packages.append(asset.package_name)
    
    # Fix up using the library function that exists
    fixed = unreal.EditorAssetLibrary.fix_up_redirector(packages)
    if fixed:
        print('Successfully fixed up redirectors')
    else:
        # Try individual fixup
        for asset in redirectors:
            obj_path = asset.object_path
            print('Processing: ' + str(obj_path))
            # Load the redirector and fix
            obj = unreal.load_asset(str(obj_path))
            if obj and obj.get_class().get_name() == 'ObjectRedirector':
                unreal.EditorAssetLibrary.consolidate_assets(obj, None)

print('DONE')
