
import unreal, json
EAL=unreal.EditorAssetLibrary; MEL=unreal.MaterialEditingLibrary

def parent_of(path):
    mi=EAL.load_asset(path)
    if not mi: return None
    try: p=mi.get_editor_property('parent')
    except: p=None
    return p.get_path_name() if p else None

rows=[]
for p in [
 '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_B0_Red',
 '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowPetal_B0_Red',
 '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowPetal_Wind_B0_Red',
 '/Game/EnvSandbox/Materials/Masters/M_MelodiaPlant_Wind',
 '/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal',
 '/Game/EnvSandbox/Materials/Masters/M_ToonFoliage',
]:
  if not EAL.does_asset_exist(p):
    rows.append({'path':p,'missing':True}); continue
  mi=EAL.load_asset(p)
  sc=[str(n) for n in MEL.get_scalar_parameter_names(mi)]
  rows.append({
    'path': p.split('/')[-1],
    'parent': parent_of(p),
    'DreamSaturation': 'DreamSaturation' in sc,
    'SharedBend': 'SharedBend' in sc,
    'MelodiaWindResponse': 'MelodiaWindResponse' in sc,
    'nikki_n': sum(1 for s in sc if any(k in s for k in ('Dream','Pastel','Nikki'))),
    'wind_n': sum(1 for s in sc if any(k in s for k in ('Wind','Shared','Branch','Ripple'))),
  })
print('ROWS '+json.dumps(rows))
print('API set_material_instance_parent='+str(hasattr(MEL,'set_material_instance_parent')))
