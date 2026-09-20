import unreal, json
EAL = unreal.EditorAssetLibrary
cands = [
 '/Game/Actor_BP/BP_InstanceOnSpline',
 '/Game/EnvSandbox/PCG/Universal/BP_InstanceOnSpline',
 '/Game/Actor_BP/BP_InstanceOnSpline_Old',
 '/Game/Melodia/Actor_BP/BP_InstanceOnSpline_Old',
]
out=[]
for p in cands:
    ex = EAL.does_asset_exist(p)
    info={'path':p,'exists':ex}
    if ex:
        try:
            a=EAL.find_asset_data(p)
            info['class']=str(a.asset_class_path) if hasattr(a,'asset_class_path') else str(getattr(a,'asset_class',None))
        except Exception as e:
            info['err']=str(e)
    out.append(info)
print('BPS', json.dumps(out, default=str))
