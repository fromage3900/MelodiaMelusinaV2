import unreal
import os

# Atomic Sea Above level save: defensively clear ReadOnly on the umap + external
# actors, then save level + all dirty packages in one editor-side call. This
# avoids the Git-plugin race that crashes saves (RO re-mark between clear and save).

UMAP = r'C:\EnvironmentPortfolio\BS_GodFile\Content\EnvSandbox\Monoliths\SeaAbove\Prototype\LV_SeaAbove_Prototype.umap'
EXT_DIR = r'C:\EnvironmentPortfolio\BS_GodFile\Content\__ExternalActors__\EnvSandbox\Monoliths\SeaAbove\Prototype\LV_SeaAbove_Prototype'
EXT_OBJ = r'C:\EnvironmentPortfolio\BS_GodFile\Content\__ExternalObjects__\EnvSandbox\Monoliths\SeaAbove\Prototype\LV_SeaAbove_Prototype'

# 1. Clear read-only on the umap + all external actor/object files for this level
cleared = 0
for path in [UMAP]:
    try:
        os.chmod(path, 0o666)
        cleared += 1
    except Exception as e:
        unreal.log_warning('CHMOD_FAIL %s :: %s' % (path, e))

for root in [EXT_DIR, EXT_OBJ]:
    if not os.path.isdir(root):
        continue
    for dirpath, _, files in os.walk(root):
        for f in files:
            fp = os.path.join(dirpath, f)
            try:
                os.chmod(fp, 0o666)
                cleared += 1
            except Exception:
                pass

unreal.log_warning('LEVEL_SAVE_ATOMIC cleared=%d' % cleared)

# 2. Save the level package
level_ok = unreal.EditorAssetLibrary.save_asset('/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype')
unreal.log_warning('LEVEL_SAVE_ATOMIC level_save=%s' % level_ok)

# 3. Save all dirty packages (external actors from spawn/delete)
saved = unreal.EditorAssetLibrary.save_directory('/Game/__ExternalActors__/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype', only_if_is_dirty=True, recursive=True)
unreal.log_warning('LEVEL_SAVE_ATOMIC ext_actors=%s' % saved)
saved2 = unreal.EditorAssetLibrary.save_directory('/Game/__ExternalObjects__/EnvSandbox/Monoliths/SeaAbove/Prototype/LV_SeaAbove_Prototype', only_if_is_dirty=True, recursive=True)
unreal.log_warning('LEVEL_SAVE_ATOMIC ext_objects=%s' % saved2)
unreal.log_warning('LEVEL_SAVE_ATOMIC DONE')