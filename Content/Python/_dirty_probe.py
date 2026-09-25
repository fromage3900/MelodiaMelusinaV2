# Read-only probe: what packages are dirty (unsaved) in the open editor. Prints only.
import unreal

try:
    dp = unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    print('DP dirty_content:', [p.get_name() for p in dp])
except Exception as e:
    print('DP dirty_content ERR', e)

try:
    dm = unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    print('DP dirty_maps:', [p.get_name() for p in dm])
except Exception as e:
    print('DP dirty_maps ERR', e)

print('DP done')