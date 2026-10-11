import unreal, json
MEL=unreal.MaterialEditingLibrary; EAL=unreal.EditorAssetLibrary
D='/Game/KitBash_EnchantedVehicles/'
U=unreal.load_asset('/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal'); UA=unreal.load_asset('/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_Alpha')
MAPS={'basecolor':'Albedo','normal':'NormalMap','metallic':'MetallicMap','roughness':'RoughnessMap','height':'HeightMap','emissive':'EmissiveMap','opacity':'OpacityMap'}
ar=unreal.AssetRegistryHelpers.get_asset_registry()
names=[str(a.asset_name) for a in ar.get_assets_by_path(D.rstrip('/'),recursive=False) if str(a.asset_class_path.asset_name)=='MaterialInstanceConstant']
tex={str(a.asset_name) for a in ar.get_assets_by_path(D.rstrip('/'),recursive=False) if str(a.asset_class_path.asset_name)=='Texture2D'}
res={'ok':0,'alpha':0,'no_basecolor':[],'fail':[]}
for n in sorted(names):
    try:
        stem=n[2:]  # KB3D_ECV_<Stem>
        has={k for k in list(MAPS)+['refraction'] if f'{stem}_{k}' in tex}
        alpha=('opacity' in has) or ('refraction' in has)
        mi=unreal.load_asset(D+n)
        mi.set_editor_property('parent', UA if alpha else U)
        for k,param in MAPS.items():
            if k in has and not (param=='OpacityMap' and not alpha):
                MEL.set_material_instance_texture_parameter_value(mi,param,unreal.load_asset(f'{D}{stem}_{k}'))
        for sp,v in (('TextureWeight',1.0),('LayerA_TextureWeight',1.0)):
            MEL.set_material_instance_scalar_parameter_value(mi,sp,v)
        MEL.update_material_instance(mi); EAL.save_asset(D+n,only_if_is_dirty=False)
        res['ok']+=1; res['alpha']+=int(alpha)
        if 'basecolor' not in has: res['no_basecolor'].append(n)
    except Exception as e:
        res['fail'].append((n,str(e)[:80]))
print(json.dumps(res))
