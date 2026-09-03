import unreal
import inspect

# Check what redirect-related methods exist on EditorAssetLibrary
methods = [m for m in dir(unreal.EditorAssetLibrary) if 'redirect' in m.lower() or 'director' in m.lower()]
print('Redirect methods on EditorAssetLibrary:')
for m in methods:
    print('  ' + m)

# Also check on EditorLevelLibrary
methods2 = [m for m in dir(unreal.EditorLevelLibrary) if 'redirect' in m.lower() or 'director' in m.lower()]
print('On EditorLevelLibrary:')
for m in methods2:
    print('  ' + m)

# Check for any function with fix_up or fixup
methods3 = [m for m in dir(unreal.EditorAssetLibrary) if 'fix' in m.lower()]
print('Fix methods:')
for m in methods3:
    print('  ' + m)

# Also check what redirector count is
ar_filter = unreal.ARFilter()
ar_filter.class_names = ['ObjectRedirector']
asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
redirectors = asset_registry.get_assets(ar_filter)
print('Found {} redirectors'.format(len(redirectors)))
if redirectors:
    for r in redirectors[:5]:
        print('  ' + str(r.package_name))

print('DONE')
