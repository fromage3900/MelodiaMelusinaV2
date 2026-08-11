import unreal

# Use SoftObjectPath filter approach
ar_filter = unreal.ARFilter(
    class_names=['ObjectRedirector'],
    recursive_paths=True
)

asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
redirectors = asset_registry.get_assets(ar_filter)

print('Redirectors found: {}'.format(len(redirectors)))

success = 0
for r in redirectors:
    pkg_name = str(r.package_name)
    try:
        # Load the redirector package
        obj = unreal.load_asset(pkg_name)
        if obj and obj.get_class().get_name() == 'ObjectRedirector':
            # Delete it - references auto-fix
            unreal.EditorAssetLibrary.delete_asset(pkg_name)
            print('  Fixed: {}'.format(pkg_name))
            success += 1
    except Exception as e:
        pass

print('Fixed {} redirectors'.format(success))
print('DONE')
