import unreal

# Try different approach - scan asset registry directly
asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

# Try getting all assets and find redirectors
all_assets = asset_registry.get_all_assets()
count = 0
for a in all_assets:
    cls_name = a.asset_class
    if cls_name == 'ObjectRedirector':
        count += 1
        pkg = a.package_name
        print(str(pkg))

print('Total redirectors: {}'.format(count))
print('DONE')
