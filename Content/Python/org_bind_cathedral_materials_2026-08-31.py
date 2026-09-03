import unreal

# Bind jelly MIs to the 107 cathedral meshes (import left WorldGridMaterial).
# Body parts (tiers/halo/spire/cilia/drapes/arches/cascades) -> MI_Jelly_Bell
# Arms (13) -> MI_Jelly_Arms

MESH_ROOT = '/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Meshes'
BELL_MI = '/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Materials/MI_Jelly_Bell.MI_Jelly_Bell'
ARMS_MI = '/Game/EnvSandbox/Monoliths/SeaAbove/Prototype/Reef/Materials/MI_Jelly_Arms.MI_Jelly_Arms'

ar = unreal.AssetRegistryHelpers.get_asset_registry()
assets = ar.get_assets_by_path(MESH_ROOT, recursive=False)
unreal.log_warning('CATH_BIND begin scanned=%d' % len(assets))

bell_mat = unreal.load_asset(BELL_MI)
arms_mat = unreal.load_asset(ARMS_MI)
ok = 0
failed = []
for a in assets:
    name = str(a.asset_name)
    if not name.startswith('JELLY_Cathedral'):
        continue
    cls = str(a.asset_class_path)
    if 'StaticMesh' not in cls:
        continue
    mesh = a.get_asset()
    if mesh is None:
        failed.append('%s: not loadable' % name)
        continue
    mat = arms_mat if '_Arms_' in name else bell_mat
    try:
        mesh.set_material(0, mat)
        ok += 1
    except Exception as ex:
        failed.append('%s :: %s' % (name, ex))

unreal.log_warning('CATH_BIND ok=%d failed=%d' % (ok, len(failed)))
for f in failed[:10]:
    unreal.log_warning('CATH_BIND_FAIL %s' % f)

saved = unreal.EditorAssetLibrary.save_directory(MESH_ROOT, only_if_is_dirty=True, recursive=True)
unreal.log_warning('CATH_BIND save=%s' % saved)