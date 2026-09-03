import unreal, sys, re
L = unreal.log_warning

ar = unreal.AssetRegistryHelpers.get_asset_registry()
ar.wait_for_completion()
all_assets = ar.get_all_assets()

# Index EnvSandbox + Melodia materials
env_mats = [a for a in all_assets 
    if ('Material' in str(a.asset_class_path) or 'MaterialInstanceConstant' in str(a.asset_class_path))
    and (str(a.package_path).startswith('/Game/EnvSandbox/Materials') or str(a.package_path).startswith('/Game/Melodia'))
    and 'MaterialFunction' not in str(a.asset_class_path)
    and 'MaterialLayer' not in str(a.asset_class_path)]

L('Available materials: {}'.format(len(env_mats)))

mat_lookup = {}
for a in env_mats:
    name = str(a.asset_name).lower()
    path = str(a.package_name)
    if name not in mat_lookup:
        mat_lookup[name] = []
    mat_lookup[name].append(path)

def find_material(slot_name):
    sn = slot_name.lower()
    # Try exact
    if sn in mat_lookup:
        return mat_lookup[sn][0]
    # Try variants
    variants = set()
    variants.add(sn)
    if sn.startswith('m_'):
        variants.add(sn[2:])
        variants.add('mi_' + sn[2:])
    elif sn.startswith('mi_'):
        variants.add(sn[3:])
        variants.add('m_' + sn[3:])
    base = re.sub(r'_\d+$', '', sn)
    if base != sn:
        variants.add(base)
        if base.startswith('m_'):
            variants.add(base[2:])
        elif base.startswith('mi_'):
            variants.add(base[3:])
    for v in variants:
        if v in mat_lookup:
            return mat_lookup[v][0]
    # Try fuzzy: look for slot_name as substring of material name
    for name, paths in mat_lookup.items():
        if sn in name or (len(sn) > 5 and name in sn):
            return paths[0]
    return None

# Get all project static meshes
sm = [a for a in all_assets 
    if 'StaticMesh' in str(a.asset_class_path) and 'StaticMeshActor' not in str(a.asset_class_path)
    and str(a.package_path).startswith('/Game')
    and not '__ExternalActors__' in str(a.package_path)
    and not '__ExternalObjects__' in str(a.package_path)]

L('Static meshes: {}'.format(len(sm)))

fixed = 0
unfixable = 0
for ad in sm:
    try:
        m = ad.get_asset()
        slots = m.get_editor_property('static_materials')
        chg = False
        for s in slots:
            mi = s.get_editor_property('material_interface')
            if mi is None:
                sn = str(s.material_slot_name)
                found = find_material(sn)
                if found:
                    a = unreal.EditorAssetLibrary.load_asset(found)
                    if a:
                        s.set_editor_property('material_interface', a)
                        L('FIXED {} slot {} -> {}'.format(ad.asset_name, sn, found))
                        fixed += 1
                        chg = True
                    else:
                        L('FAIL {} slot {} (load failed)'.format(ad.asset_name, sn))
                        unfixable += 1
                else:
                    L('MISS {} slot {}'.format(ad.asset_name, sn))
                    unfixable += 1
        if chg:
            unreal.EditorAssetLibrary.save_asset(str(ad.package_name), only_if_is_dirty=True)
    except Exception as e:
        L('ERROR {}: {}'.format(ad.asset_name, str(e)))

L('RESULT: fixed={}, missing={}'.format(fixed, unfixable))
