import unreal, json
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary

paths = {
  'speedtree_b0': '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_B0_Red',
  'petal_b0': '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowPetal_B0_Red',
  'plant_wind': '/Game/EnvSandbox/Materials/Masters/M_MelodiaPlant_Wind',
}
# search common masters
candidates = [
  '/Game/EnvSandbox/Materials/Masters/M_MelodiaPlant_Wind',
  '/Game/EnvSandbox/Materials/Masters/M_MelodiaPlant_Universal',
  '/Game/EnvSandbox/Materials/Masters/M_Melodia_UniversalToon',
  '/Game/EnvSandbox/Materials/Masters/M_UniversalToon',
  '/Game/EnvSandbox/Materials/Masters/M_NikkiToon',
  '/Game/EnvSandbox/Materials/Masters/M_MelodiaToon',
  '/Game/Melodia/Materials/M_UniversalToon',
  '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowPetal_B0_Red',
]
out = {'exists': {}, 'parents': {}, 'nikki_speed': [], 'nikki_petal': [], 'st_params_sample': {}, 'petal_params_sample': {}}
for p in candidates:
    out['exists'][p] = EAL.does_asset_exist(p)

def dump_mi(path, key_n, key_s):
    mi = EAL.load_asset(path)
    if not mi:
        return
    try:
        parent = MEL.get_material_instance_parent(mi) if hasattr(MEL, 'get_material_instance_parent') else mi.get_editor_property('parent')
        out['parents'][path] = parent.get_path_name() if parent else None
    except Exception as e:
        out['parents'][path] = str(e)
    try:
        scalars = [str(n) for n in MEL.get_scalar_parameter_names(mi)]
    except Exception:
        scalars = []
    try:
        vectors = [str(n) for n in MEL.get_vector_parameter_names(mi)]
    except Exception:
        vectors = []
    try:
        switches = [str(n) for n in MEL.get_static_switch_parameter_names(mi)]
    except Exception:
        switches = []
    nikki = [s for s in scalars if any(k in s for k in ('Dream','Pastel','Nikki','ShadowDream','MossConcavity','FlowerShadow'))]
    wind = [s for s in scalars if 'Wind' in s or 'Shared' in s or 'Branch' in s or 'Ripple' in s]
    out[key_n] = nikki
    out[key_s] = {
        'scalar_count': len(scalars),
        'vector_count': len(vectors),
        'switch_count': len(switches),
        'nikki': nikki,
        'wind_like': wind[:40],
        'vectors_sample': vectors[:30],
        'switches_sample': switches[:30],
    }

dump_mi(paths['speedtree_b0'], 'nikki_speed', 'st_params_sample')
dump_mi(paths['petal_b0'], 'nikki_petal', 'petal_params_sample')

# asset registry search for Universal / Toon masters
ar = unreal.AssetRegistryHelpers.get_asset_registry()
hits = []
for root in ('/Game/EnvSandbox/Materials', '/Game/Melodia', '/Game/EnvSandbox'):
    try:
        assets = ar.get_assets_by_path(root, True) or []
    except Exception:
        assets = []
    for a in assets:
        name = str(a.asset_name)
        cls = str(a.asset_class_path.asset_name)
        if cls not in ('Material', 'MaterialInstanceConstant'):
            continue
        low = name.lower()
        if any(k in low for k in ('universal', 'toon', 'nikki', 'melodiaplant', 'rainbowpetal', 'rainbowspeed')):
            hits.append({'name': name, 'class': cls, 'path': str(a.package_name)})
            if len(hits) >= 60:
                break
    if len(hits) >= 60:
        break
out['registry_hits'] = hits
print('MATDISCOVER', json.dumps(out)[:12000])
