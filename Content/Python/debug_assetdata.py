import unreal, sys
L = unreal.log_warning

ar = unreal.AssetRegistryHelpers.get_asset_registry()
ar.wait_for_completion()
all_assets = ar.get_all_assets()

# Debug: check AssetData properties
a = all_assets[0]
L('AssetData type: {}'.format(type(a)))
L('dir: {}'.format([x for x in dir(a) if not x.startswith('_')]))

# Check what the asset class looks like
L('asset_class_path: {}'.format(str(a.asset_class_path)))
L('asset_name: {}'.format(str(a.asset_name)))
L('package_name: {}'.format(str(a.package_name)))
L('package_path: {}'.format(str(a.package_path)))

# Check envelope methods
L('DONE')
