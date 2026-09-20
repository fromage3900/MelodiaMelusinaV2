import unreal, json
EAL=unreal.EditorAssetLibrary; MEL=unreal.MaterialEditingLibrary
p='/Game/EnvSandbox/Materials/Instances/Environment/MI_ProcFoliage_NikkiDream'
mi=EAL.load_asset(p)
parent=mi.get_editor_property('parent') if mi else None
sc=[str(n) for n in MEL.get_scalar_parameter_names(mi)] if mi else []
print('PROC', json.dumps({
 'parent': parent.get_path_name() if parent else None,
 'DreamSaturation': 'DreamSaturation' in sc,
 'SharedBend': 'SharedBend' in sc,
 'Cloth_WindStrength': 'Cloth_WindStrength' in sc,
 'nikki': [s for s in sc if 'Dream' in s or 'Pastel' in s][:20],
}))
# List MF assets with Nikki/Dream in name
ar=unreal.AssetRegistryHelpers.get_asset_registry()
mfs=[]
for a in (ar.get_assets_by_path('/Game/EnvSandbox/Materials', True) or []):
  if str(a.asset_class_path.asset_name)!='MaterialFunction': continue
  n=str(a.asset_name)
  if any(k in n.lower() for k in ('nikki','dream','pastel','toon','wind','foliage')):
    mfs.append(str(a.package_name))
print('MFS', json.dumps(mfs[:40]))
