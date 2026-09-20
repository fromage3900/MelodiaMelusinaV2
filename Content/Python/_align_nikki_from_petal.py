"""Align Nikki defaults on hybrid SpeedTree MIs from real Dream templates.

Discovery: MI_RainbowPetal_Wind_* parents MelodiaPlant_Wind but exposes no Dream*.
Dream* lives on MI_RainbowPetal_* (Universal). Copy those scalars onto hybrid bands.
"""
import unreal, json
from pathlib import Path
from datetime import datetime, timezone

EAL=unreal.EditorAssetLibrary; MEL=unreal.MaterialEditingLibrary
NIKKI_KEYS = [
    'PastelLift','DreamSaturation','DreamContrast','DreamShadowLift','DreamHighlightSoft',
    'DreamIntensity','DreamWarmth','DreamComposition','DreamThreshold','DreamCompositeBlend',
    'RimPower','RimWidth','ShadowDreamStrength','NikkiHeroGradeStrength',
    'SparkleIntensity','SparkleScale','SparkleThreshold','DreamRimStrength','DreamBloomStrength',
]
BANDS = ['B0_Red','B1_Orange','B2_Gold','B3_Green','B4_Blue','B5_Indigo','B6_Violet']

def parent_of(path):
    mi=EAL.load_asset(path)
    if not mi: return None
    p=mi.get_editor_property('parent')
    return p.get_path_name() if p else None

def scalars(path, keys):
    mi=EAL.load_asset(path)
    if not mi: return {}
    names=set(str(n) for n in MEL.get_scalar_parameter_names(mi))
    out={}
    for k in keys:
        if k not in names: continue
        try: out[k]=float(MEL.get_material_instance_scalar_parameter_value(mi, k))
        except: pass
    return out

discovery=[]
for lab in BANDS:
    pw=f'/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowPetal_Wind_{lab}'
    pt=f'/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowPetal_{lab}'
    st=f'/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_{lab}'
    discovery.append({
        'band': lab,
        'petal_wind_parent': parent_of(pw),
        'petal_wind_dream_n': len(scalars(pw, NIKKI_KEYS)),
        'petal_parent': parent_of(pt),
        'petal_dream_n': len(scalars(pt, NIKKI_KEYS)),
        'speedtree_parent': parent_of(st),
        'speedtree_dream_n': len(scalars(st, NIKKI_KEYS)),
        'speedtree_has_SharedBend': 'SharedBend' in set(str(n) for n in MEL.get_scalar_parameter_names(EAL.load_asset(st) or []) ) if EAL.does_asset_exist(st) else False,
    })

applied=[]
for lab in BANDS:
    src_path=f'/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowPetal_{lab}'
    dst_path=f'/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_{lab}'
    src=scalars(src_path, NIKKI_KEYS)
    # mild foliage-safe defaults if source empty
    if not src:
        src={'PastelLift':0.28,'DreamSaturation':0.22,'DreamContrast':-0.06,'DreamShadowLift':0.10,'DreamIntensity':0.55}
    dst=EAL.load_asset(dst_path)
    if not dst:
        applied.append({'band':lab,'ok':False}); continue
    wrote={}
    names=set(str(n) for n in MEL.get_scalar_parameter_names(dst))
    for k,v in src.items():
        if k not in names: continue
        try:
            MEL.set_material_instance_scalar_parameter_value(dst, k, float(v))
            wrote[k]=float(v)
        except Exception as e:
            wrote[k]=f'ERR:{e}'
    # keep wind response
    try: MEL.set_material_instance_scalar_parameter_value(dst,'MelodiaWindResponse',0.5)
    except: pass
    EAL.save_asset(dst_path)
    applied.append({'band':lab,'ok':True,'wrote_n':len([1 for v in wrote.values() if not str(v).startswith('ERR')]),'sample':{k:wrote[k] for k in list(wrote)[:8]}})

report={'generated_at':datetime.now(timezone.utc).isoformat(),'discovery':discovery,'applied':applied,
        'note':'Petal_Wind has MelodiaPlant_Wind parent but 0 Dream* params; Dream* copied from MI_RainbowPetal_* (Universal) onto hybrid SpeedTree MIs.'}
out=Path(unreal.Paths.project_dir())/'Saved'/'Audit'/'nikki_defaults_from_petal_2026-09-20.json'
out.write_text(json.dumps(report, indent=2), encoding='utf-8')
print('ALIGN', json.dumps({'discovery_b0':discovery[0],'applied_ok':sum(1 for a in applied if a.get('ok')),'wrote_sample':applied[0], 'report':str(out)}, default=str))
