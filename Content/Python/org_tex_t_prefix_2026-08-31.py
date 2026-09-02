import unreal
import json
import os

# Vendor texture T_ prefix batch — 200 textures under /Game/EnvSandbox/Textures
# missing the T_ prefix (Brick01_*, KB3D_ATL_*, crystal*, skybox-*, etc).
# Engine-native rename_asset (reference fixup + redirectors), unattended save.

PATH_FILE = r'C:\Users\froma\AppData\Local\Temp\opencode\atl_texture_paths.json'
with open(PATH_FILE, encoding='utf-8-sig') as fh:
    paths = json.load(fh)

unreal.log_warning('TEX_RENAME begin paths=%d' % len(paths))
renamed = 0
failed = []
for pkg in paths:
    name = pkg.rsplit('/', 1)[-1]
    if name.startswith('T_'):
        continue
    new_pkg = pkg.rsplit('/', 1)[0] + '/T_' + name
    try:
        if unreal.EditorAssetLibrary.rename_asset(pkg, new_pkg):
            renamed += 1
        else:
            failed.append(pkg)
    except Exception as ex:
        failed.append('%s :: %s' % (pkg, ex))

unreal.log_warning('TEX_RENAME renamed=%d failed=%d' % (renamed, len(failed)))
for f in failed[:15]:
    unreal.log_warning('TEX_FAIL %s' % f)

saved = unreal.EditorAssetLibrary.save_directory('/Game/EnvSandbox/Textures', only_if_is_dirty=True, recursive=True)
unreal.log_warning('TEX_RENAME save_directory=%s' % saved)