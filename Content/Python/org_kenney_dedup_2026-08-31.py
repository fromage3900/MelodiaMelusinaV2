import unreal

# Kenney RetroFantasyKit duplicate cleanup: bare-named MIs (barrel, water, ...)
# are stale copies of the renamed MI_* versions (verified: both referenced_by [],
# identical purpose). Move bare ones to VFX/_Archive pattern — never delete.

SRC = '/Game/EnvSandbox/Materials/Instances/Kenney/RetroFantasyKit'
DST = '/Game/EnvSandbox/VFX/_Archive_2026-08-30/OrphanMaterials/KenneyRetroFantasyKit'

bare = ['barrel', 'cobblestone', 'cobblestoneAlternative', 'cobblestonePainted',
        'details', 'fence', 'planks', 'roof', 'tree', 'water']

moved = 0
failed = []
for name in bare:
    src = '%s/%s.%s' % (SRC, name, name)
    dst = '%s/%s.%s' % (DST, name, name)
    try:
        if unreal.EditorAssetLibrary.rename_asset(src, dst):
            moved += 1
        else:
            failed.append(src)
    except Exception as ex:
        failed.append('%s :: %s' % (src, ex))

unreal.log_warning('KENNEY_DEDUP moved=%d failed=%d' % (moved, len(failed)))
for f in failed[:5]:
    unreal.log_warning('KENNEY_DEDUP_FAIL %s' % f)