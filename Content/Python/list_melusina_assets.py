import unreal
registry = unreal.AssetRegistryHelpers.get_asset_registry()
assets = registry.get_assets_by_path('/Game', recursive=True)
found = []
for asset in assets:
    name = asset.asset_name
    if 'Melusina' in name and name.endswith('BP_Melusina'):
        found.append(asset.object_path)
if found:
    for obj in found:
        unreal.log('Duplicate BP_Melusina found: {}'.format(obj))
else:
    unreal.log('No BP_Melusina assets found.')
