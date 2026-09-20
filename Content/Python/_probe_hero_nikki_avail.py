import unreal, json
EAL=unreal.EditorAssetLibrary; MEL=unreal.MaterialEditingLibrary
mi=EAL.load_asset('/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_B0_Red')
sc=[str(n) for n in MEL.get_scalar_parameter_names(mi)]
sw=[]
try: sw=[str(n) for n in MEL.get_static_switch_parameter_names(mi)]
except: pass
hero=[s for s in sc if any(k in s for k in ('Nikki','Dream','Pastel','Rim','Sparkle','Hero','Glow','Bloom'))]
print('HERO_AVAIL', json.dumps({'scalars':hero,'switches':[s for s in sw if 'Nikki' in s or 'Dream' in s or 'Sparkle' in s or 'Hero' in s]}))
