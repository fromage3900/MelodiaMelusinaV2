import unreal, json
from pathlib import Path
EAL=unreal.EditorAssetLibrary; MEL=unreal.MaterialEditingLibrary
BANDS=['B0_Red','B1_Orange','B2_Gold','B3_Green','B4_Blue','B5_Indigo','B6_Violet']
# Foliage-safe Nikki grade (Universal petal MIs had zeros on Dream*)
NIKKI={
  'PastelLift':0.32,'DreamSaturation':0.26,'DreamContrast':-0.05,
  'DreamShadowLift':0.12,'DreamIntensity':0.62,'DreamWarmth':0.08,
  'ShadowDreamStrength':0.28,'RimPower':4.5,'RimWidth':0.22,
  'SparkleIntensity':0.12,'SparkleScale':180.0,'SparkleThreshold':0.55,
}
out=[]
for lab in BANDS:
  path=f'/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_{lab}'
  mi=EAL.load_asset(path)
  if not mi: continue
  names=set(str(n) for n in MEL.get_scalar_parameter_names(mi))
  wrote={}
  for k,v in NIKKI.items():
    if k not in names: continue
    MEL.set_material_instance_scalar_parameter_value(mi,k,float(v)); wrote[k]=v
  MEL.set_material_instance_scalar_parameter_value(mi,'MelodiaWindResponse',0.5)
  EAL.save_asset(path)
  out.append({'band':lab,'wrote':wrote})
print('RESTORE', json.dumps({'bands':len(out),'b0':out[0] if out else None}))
