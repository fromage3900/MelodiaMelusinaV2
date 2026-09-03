"""Extended version: query Universal Master param names by reading its expressions,
then set params on instances directly without relying on get_parameter_names()."""

import unreal

UNIVERSAL = '/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal'

CLASSIC_ROOTS = [
    '/Game/_PROJECT/04_Materials/SDF',
    '/Game/_PROJECT/04_Materials/baroque',
    '/Game/_PROJECT/04_Materials/Cathedral',
]

# --- Read Universal Master's param names from its expressions ---
_um_scalar_names = []
_um_vector_names = []
_um_texture_names = []

def _read_um_params():
    global _um_scalar_names, _um_vector_names, _um_texture_names
    mat = (unreal.EditorAssetLibrary.load_asset(UNIVERSAL)
           if unreal.EditorAssetLibrary.does_asset_exist(UNIVERSAL) else None)
    if not mat:
        unreal.log('[UM] FAILED to load M_Master_Toon_Universal')
        return
    s, v, t = [], [], []
    for e in unreal.MaterialEditingLibrary.get_material_expressions(mat):
        tn = type(e).__name__
        try:
            if 'Texture' in tn and 'Parameter' in tn:
                pn = e.get_editor_property('parameter_name')
                if pn: t.append(pn)
            elif 'ScalarParameter' in tn:
                pn = e.get_editor_property('parameter_name')
                if pn: s.append(pn)
            elif 'VectorParameter' in tn:
                pn = e.get_editor_property('parameter_name')
                if pn: v.append(pn)
        except Exception:
            pass
    _um_scalar_names = s
    _um_vector_names = v
    _um_texture_names = t
    unreal.log(f'[UM] param count: scalar={len(s)} vector={len(v)} texture={len(t)}')
    # Log all names for debugging
    unreal.log(f'[UM] scalar names: {s}')
    unreal.log(f'[UM] vector names (first 20): {v[:20]}')
    unreal.log(f'[UM] texture names (first 20): {t[:20]}')

def load(path):
    p = path.split('.')[0]
    return (unreal.EditorAssetLibrary.load_asset(p)
            if unreal.EditorAssetLibrary.does_asset_exist(p)
            else None)

def find_masters(root):
    out = []
    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    ar.scan_paths_synchronous([root], force_rescan=True)
    for ad in ar.get_assets_by_path(root, recursive=True):
        pkg = ad.package_name
        n = ad.asset_name
        cls = str(ad.asset_class_path)
        if 'Material' in cls and str(n).startswith('M_'):
            out.append(f'{pkg}.{n}')
    return out

def get_params(mat):
    tex, sc, vec = {}, {}, {}
    for e in unreal.MaterialEditingLibrary.get_material_expressions(mat):
        tn = type(e).__name__
        try:
            if 'Texture' in tn and 'Parameter' in tn:
                pn = e.get_editor_property('parameter_name')
                t = e.get_editor_property('texture')
                if pn and t:
                    tex[pn] = t.get_path_name()
            elif 'ScalarParameter' in tn:
                pn = e.get_editor_property('parameter_name')
                if pn is not None:
                    sc[pn] = e.get_editor_property('default_value')
            elif 'VectorParameter' in tn:
                pn = e.get_editor_property('parameter_name')
                if pn is not None:
                    vec[pn] = e.get_editor_property('default_value')
        except Exception:
            pass
    return tex, sc, vec

def tex_aliases(n):
    m = {'Diffuse': ['BaseColorMap', 'Diffuse'], 'BaseColor': ['BaseColorMap', 'BaseColor'],
         'Albedo': ['BaseColorMap'], 'Normal': ['NormalMap', 'Normal'],
         'BumpMap': ['NormalMap'], 'Roughness': ['RoughnessMap', 'Roughness'],
         'Specular': ['SpecularMap', 'Specular'], 'Metallic': ['MetallicMap', 'Metallic'],
         'AO': ['AOMap', 'AO'], 'AmbientOcclusion': ['AOMap'],
         'Opacity': ['OpacityMap', 'Opacity'], 'Mask': ['OpacityMap'],
         'Emissive': ['EmissiveMap', 'Emissive'], 'HeightMap': ['DisplacementMap'],
         'Displacement': ['DisplacementMap']}
    return m.get(n, [])

def sc_aliases(n):
    m = {'Tiling': ['UVTiling', 'Tiling'], 'Tile': ['UVTiling'],
         'Metallic': ['MetallicAmount', 'Metallic'],
         'Roughness': ['RoughnessAmount', 'Roughness'],
         'Specular': ['SpecularAmount', 'Specular'],
         'AO': ['AOScale', 'AO'], 'AOScale': ['AOScale'],
         'EmissiveIntensity': ['EmissiveIntensity'],
         'Opacity': ['OpacityAmount', 'Opacity']}
    return m.get(n, [])

def vec_aliases(n):
    m = {'BaseTint': ['BaseTint'], 'Tint': ['BaseTint'],
         'ColorTint': ['BaseTint'], 'BaseColor': ['BaseTint'],
         'DiffuseTint': ['BaseTint'], 'AlbedoTint': ['BaseTint'],
         'EmissiveColor': ['EmissiveColor'], 'EmissiveTint': ['EmissiveColor'],
         'SpecularColor': ['SpecularColor'], 'SpecularTint': ['SpecularColor']}
    return m.get(n, [])

def to_lc(v):
    if isinstance(v, unreal.LinearColor): return v
    if isinstance(v, (list, tuple)):
        return unreal.LinearColor(v[0], v[1], v[2], v[3] if len(v) > 3 else 1.0)
    if isinstance(v, unreal.Color):
        return unreal.LinearColor(v.r/255.0, v.g/255.0, v.b/255.0, v.a/255.0)
    return unreal.LinearColor(0.7, 0.7, 0.7, 1.0)

def convert(src_path):
    p = src_path.split('.')[0]
    folder = p.rsplit('/', 1)[0]
    stem = p.rsplit('/', 1)[-1]
    iname = stem.replace('M_', 'MI_', 1)
    ipath = f'{folder}/{iname}.{iname}'

    if unreal.EditorAssetLibrary.does_asset_exist(ipath):
        unreal.log(f'[MI] EXISTS {ipath}')
        return {'stem': stem, 'status': 'exists'}

    mat = load(p)
    if not mat or isinstance(mat, unreal.MaterialInstanceConstant):
        return {'stem': stem, 'status': 'skip'}

    tex, sc, vec = get_params(mat)

    parent = load(UNIVERSAL)
    if not parent:
        return {'stem': stem, 'status': 'no_parent'}

    inst = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        iname, folder, unreal.MaterialInstanceConstant,
        unreal.MaterialInstanceConstantFactoryNew()
    )
    if not inst:
        return {'stem': stem, 'status': 'create_failed'}

    unreal.MaterialEditingLibrary.set_material_instance_parent(inst, parent)

    # First save to ensure parent chain resolves
    unreal.EditorAssetLibrary.save_loaded_asset(inst, only_if_is_dirty=False)

    # Reload to get fresh reference
    inst = load(f'{folder}/{iname}')

    tok, sok, vok = 0, 0, 0

    # Textures
    for src_n, tex_p in tex.items():
        ta = load(tex_p)
        if not ta: continue
        # Try the original name and aliases against known UM texture param names
        for dst in [src_n] + tex_aliases(src_n):
            if dst in _um_texture_names:
                try:
                    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(inst, dst, ta)
                    tok += 1
                    unreal.log(f'[MI]   tex: {src_n} -> {dst}')
                    break
                except Exception as e:
                    unreal.log(f'[MI]   tex fail {dst}: {e}')

    # Scalars
    for src_n, val in sc.items():
        for dst in [src_n] + sc_aliases(src_n):
            if dst in _um_scalar_names:
                try:
                    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst, dst, val)
                    sok += 1
                    unreal.log(f'[MI]   sc: {src_n} -> {dst} = {val}')
                    break
                except Exception as e:
                    unreal.log(f'[MI]   sc fail {dst}: {e}')

    # Vectors
    for src_n, val in vec.items():
        lc = to_lc(val)
        for dst_ in [src_n] + vec_aliases(src_n):
            if dst_ in _um_vector_names:
                try:
                    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(inst, dst_, lc)
                    vok += 1
                    unreal.log(f'[MI]   vec: {src_n} -> {dst_}')
                    break
                except Exception as e:
                    unreal.log(f'[MI]   vec fail {dst_}: {e}')

    unreal.EditorAssetLibrary.save_loaded_asset(inst, only_if_is_dirty=False)
    unreal.log(f'[MI] CREATED {ipath} (t={tok}/{len(tex)} s={sok}/{len(sc)} v={vok}/{len(vec)})')
    return {'stem': stem, 'status': 'created', 'tex': tok, 'sc': sok, 'vec': vok}

def main():
    _read_um_params()
    unreal.log('=== Convert M_ -> MI_ (Universal Toon) ===')
    results = []

    ml_root = None
    for c in ['/Game/Library/Migrated/MagiciansLibrary',
              '/Library/Migrated/MagiciansLibrary',
              '/Game/Content/Library/Migrated/MagiciansLibrary']:
        if unreal.EditorAssetLibrary.does_directory_exist(c):
            ml_root = c; break

    if ml_root:
        unreal.log(f'[MI] MagiciansLibrary @ {ml_root}')
        for mp in find_masters(ml_root):
            results.append(convert(mp))

    for root in CLASSIC_ROOTS:
        if not unreal.EditorAssetLibrary.does_directory_exist(root):
            unreal.log(f'[MI] Skipping {root} (not found)')
            continue
        tag = root.rsplit('/', 1)[-1]
        unreal.log(f'[MI] Classic [{tag}]')
        for mp in find_masters(root):
            results.append(convert(mp))

    created = sum(1 for r in results if r['status'] == 'created')
    existed = sum(1 for r in results if r['status'] == 'exists')
    skipped = sum(1 for r in results if r['status'] == 'skip')
    failed = sum(1 for r in results if r['status'] not in ('created', 'exists', 'skip'))

    unreal.log('=== SUMMARY ===')
    unreal.log(f'  Created: {created}')
    unreal.log(f'  Already existed: {existed}')
    unreal.log(f'  Skipped (not master): {skipped}')
    unreal.log(f'  Failed: {failed}')

    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception:
        pass
    unreal.log('=== DONE ===')

if __name__ == '__main__':
    main()
