import unreal

# Try direct approach - find redirector references by scanning the asset registry
asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

# Use a different approach: scan all assets for references to known stale paths
stale_prefixes = ['/Game/Characters/Melusina/', '/Game/MagicianLabatory/']

# Find actual redirector assets
all_assets = asset_registry.get_all_assets()

redirector_count = 0
for asset in all_assets:
    try:
        cls = asset.asset_class_path
        if 'ObjectRedirector' in str(cls):
            print('Redirector: {} ({})'.format(asset.package_name, cls))
            redirector_count += 1
    except:
        pass

print('Total redirectors: {}'.format(redirector_count))
print('DONE')
