import unreal, json
EAL = unreal.EditorAssetLibrary
MEL = unreal.MaterialEditingLibrary

def parent_of(path):
    mi = EAL.load_asset(path)
    if not mi: return None
    try:
        p = MEL.get_parent(mi) if hasattr(MEL,'get_parent') else None
    except Exception:
        p = None
    if p is None:
        try:
            p = mi.get_editor_property('parent')
        except Exception:
            p = None
    return p.get_path_name() if p else None

def param_sets(path):
    mi = EAL.load_asset(path)
    if not mi: return {}
    sc = [str(n) for n in MEL.get_scalar_parameter_names(mi)]
    sw = []
    try: sw = [str(n) for n in MEL.get_static_switch_parameter_names(mi)]
    except: pass
    nikki = [s for s in sc if any(k in s for k in ('Dream','Pastel','Nikki','Rim','Sparkle','ShadowDream'))]
    wind = [s for s in sc if any(k in s for k in ('Wind','Shared','Branch','Ripple','MelodiaWind'))]
    return {
        'parent': parent_of(path),
        'nikki_n': len(nikki), 'nikki': nikki[:25],
        'wind_n': len(wind), 'wind': wind[:25],
        'has_SharedBend': 'SharedBend' in sc,
        'has_DreamSaturation': 'DreamSaturation' in sc,
        'has_MelodiaWindResponse': 'MelodiaWindResponse' in sc,
    }

assets = [
  '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_B0_Red',
  '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowPetal_B0_Red',
  '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowPetal_Wind_B0_Red',
  '/Game/EnvSandbox/Materials/Masters/M_MelodiaPlant_Wind',
  '/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal',
  '/Game/EnvSandbox/Materials/Masters/M_ToonFoliage',
  '/Game/EnvSandbox/Materials/Masters/M_Master_Nikki',
  '/Game/EnvSandbox/Materials/Instances/Environment/MI_ProcFoliage_NikkiDream',
  '/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal_Inst',
  '/Game/EnvSandbox/Materials/Instances/MI_Master_Toon_Universal_Inst',
]
out = {p: param_sets(p) for p in assets if EAL.does_asset_exist(p)}

# Can we set parent? Check API
out['api'] = {
  'set_material_instance_parent': hasattr(MEL, 'set_material_instance_parent'),
  'set_parent': hasattr(MEL, 'set_parent'),
}

# Read current SpeedTree scalar snapshot for restore
st = EAL.load_asset('/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_B0_Red')
snap = {}
if st:
    for name in ('SharedBend','SharedOscillation','SharedSpeed','SharedTurbulence','SharedFlexibility',
                 'Branch1Bend','Branch1Oscillation','Branch1Speed','RipplePlanar','RippleDirectional','RippleSpeed',
                 'MelodiaWindResponse','MelodiaWindSpatialScale','MelodiaWindTravelSpeed','MelodiaWindHueSeed'):
        try:
            snap[name] = MEL.get_material_instance_scalar_parameter_value(st, name)
        except Exception as e:
            snap[name] = str(e)[:60]
    try:
        snap['MelodiaWindRevealTint'] = str(MEL.get_material_instance_vector_parameter_value(st, 'MelodiaWindRevealTint'))
    except Exception as e:
        snap['MelodiaWindRevealTint'] = str(e)[:60]
out['speedtree_b0_snap'] = snap

# Petal wind nikki defaults
pw = EAL.load_asset('/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowPetal_Wind_B0_Red')
pn = {}
if pw:
    for name in ('DreamSaturation','DreamContrast','PastelLift','DreamIntensity','RimPower','RimWidth','bNikkiHero'):
        try:
            if name.startswith('b'):
                # static switch
                pn[name] = 'switch'
            else:
                pn[name] = MEL.get_material_instance_scalar_parameter_value(pw, name)
        except Exception as e:
            pn[name] = str(e)[:80]
out['petal_wind_nikki'] = pn
print('CMP', json.dumps(out, default=str)[:14000])
