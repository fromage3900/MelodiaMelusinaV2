import unreal

# Get redirectors
ar_filter = unreal.ARFilter()
ar_filter.class_names = ['ObjectRedirector']
asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
redirectors = asset_registry.get_assets(ar_filter)

count = len(redirectors)
print('Found {} redirectors'.format(count))

# Process each redirector by renaming the redirector to the target
fixed = 0
for r in redirectors:
    pkg_name = r.package_name
    obj_path = r.object_path
    try:
        # Load the redirector
        obj = unreal.load_asset(str(obj_path))
        if obj:
            # Get the destination it points to
            dest = unreal.AssetRegistryHelpers.get_asset_registry().get_asset_by_object_path(str(obj.fix_up()))
            if dest:
                unreal.EditorAssetLibrary.delete_asset(str(obj_path))
                print('Fixed: {} -> {}'.format(str(pkg_name), str(dest.package_name)))
                fixed += 1
    except Exception as e:
        pass

print('Fixed {} redirectors'.format(fixed))
print('DONE')
