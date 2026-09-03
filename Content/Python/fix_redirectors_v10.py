import unreal

# In UE 5.8, try using filter constructor
ar_filter = unreal.ARFilter(
    class_names=['ObjectRedirector']
)

asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
redirectors = asset_registry.get_assets(ar_filter)

print('Redirectors: {}'.format(len(redirectors)))

for r in redirectors:
    soft_path = r.to_soft_object_path()
    print('  {} -> redirects_to={}'.format(str(soft_path), str(r.redirector_dest)))

print('DONE')
