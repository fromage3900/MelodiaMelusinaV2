import unreal

# Specific known redirector paths to check
paths = [
    '/Game/Characters/Melusina/SK_Melusina',
    '/Game/Characters/Melusina/BP_Melusina',
    '/Game/Library/Migrated/MagiciansLibrary',
    '/Game/Melodia/Characters/Melusina/SK_Melusina',
]

asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

for path in paths:
    asset_data = asset_registry.get_asset_by_object_path(path)
    if asset_data:
        print('{} -> class={}, is_redirector={}'.format(path, asset_data.asset_class_path, asset_data.is_redirector()))
    else:
        print('{} -> NOT FOUND'.format(path))

# Also check if the old MigrationRedirector packages exist
print('---')
print('Checking redirector packages...')
ar_filter = unreal.ARFilter()
ar_filter.package_paths = ['/Game/Characters', '/Game/Library']
redirectors = asset_registry.get_assets(ar_filter)
for r in redirectors:
    if r.is_redirector():
        print('REDIRECTOR: {} -> {}'.format(r.package_name, r.asset_class_path))

print('DONE')
