
import unreal, json
MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
paths = [
  '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowPetal_B0_Red',
  '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_B0_Red',
  '/Game/Melodia/_PROJECT/04_Materials/Plants/M_MelodiaPlant_Wind',
  '/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal',
]
out = {}
for p in paths:
  a = EAL.load_asset(p)
  if not a:
    out[p] = None; continue
  try:
    names = [str(n) for n in MEL.get_scalar_parameter_names(a)]
  except Exception as e:
    names = ['err:'+str(e)]
  nikki = [n for n in names if any(h in n for h in ('Dream','Pastel','Nikki','FlowerShadow','MossConcavity','ShadowDream','MelodiaWind'))]
  mf = []
  # master only: list function calls roughly via expressions if material
  out[p] = {'available_nikki_or_melodia': sorted(nikki)[:40], 'scalar_count': len(names)}
print('AVAIL', json.dumps(out))
