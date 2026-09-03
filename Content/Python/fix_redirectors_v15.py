import unreal

# Check if TopLevelAssetPath exists in the API
try:
    tl = unreal.TopLevelAssetPath('/Script/CoreUObject.ObjectRedirector')
    unreal.log('TopLevelAssetPath exists: {}'.format(str(tl)))
except AttributeError as e:
    unreal.log('No TopLevelAssetPath: {}'.format(str(e)))

# Alternative: try setting as string after construction
ar_filter = unreal.ARFilter()
try:
    # Try TopLevelAssetPath
    tl_path = unreal.TopLevelAssetPath('/Script/CoreUObject.ObjectRedirector')
    ar_filter.set_editor_property('class_paths', [tl_path])
    unreal.log('Set class_paths via TopLevelAssetPath OK')
except Exception as e:
    unreal.log('TopLevelAssetPath failed: {}'.format(str(e)))

# Try another approach: use SoftClassPath
try:
    ar_filter2 = unreal.ARFilter()
    scp = unreal.SoftClassPath('/Script/CoreUObject.ObjectRedirector')
    ar_filter2.set_editor_property('class_paths', [scp])
    unreal.log('Set class_paths via SoftClassPath OK')
except Exception as e:
    unreal.log('SoftClassPath failed: {}'.format(str(e)))

# Try approach #3: set by full object path
try:
    ar_filter3 = unreal.ARFilter()
    from unreal import ArrayClassPaths
    unreal.log('Type of class_paths on ARFilter: {}'.format(type(ar_filter.property_class.ClassPaths)))
except:
    unreal.log('Cannot inspect type')

unreal.log('DONE')
