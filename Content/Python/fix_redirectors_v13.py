import unreal

# Use unreal.log for proper log output
ar_filter = unreal.ARFilter()
ar_filter.set_editor_property('class_names', ['ObjectRedirector'])

asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()

# Try setting via set_editor_properties
ar_filter2 = unreal.ARFilter()
unreal.log('Created ARFilter')

all_assets = asset_registry.get_all_assets()
unreal.log('Total assets: {}'.format(len(all_assets)))

redirectors = []
for a in all_assets:
    cls_name = str(a.asset_class_path)
    if 'ObjectRedirector' in cls_name:
        redirectors.append(a)
        unreal.log('  Redirector: {}'.format(a.package_name))

unreal.log('Redirectors found: {}'.format(len(redirectors)))
unreal.log('DONE')
