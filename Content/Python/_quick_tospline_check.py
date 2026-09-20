import unreal, json
from pathlib import Path
EAL = unreal.EditorAssetLibrary
paths = [
 '/Game/Actor_BP/BP_InstanceOnSpline',
 '/Game/Actor_BP/BP_InstanceOnSpline_02',
 '/Game/Actor_BP/BP_InstanceOnSpline_Old',
 '/Game/Melodia/Actor_BP/BP_InstanceOnSpline_Old',
]
exists = {p: EAL.does_asset_exist(p) for p in paths}
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = []
lake = []
for a in svc.get_all_level_actors():
    L = a.get_actor_label() or ''
    C = a.get_class().get_name()
    k = (L+' '+C).lower()
    if 'instanceonspline' in k.replace('_','') or 'instance_on_spline' in k or C.startswith('BP_InstanceOnSpline'):
        actors.append({'label':L,'class':C})
    if any(x in k for x in ('sheepdell','oceanologylake','infiniteocean','oceanologymanager')):
        t=a.get_actor_transform()
        lake.append({'label':L,'class':C,'scale':[t.scale3d.x,t.scale3d.y,t.scale3d.z]})
    if any(x in k for x in ('road','escherwalk','path_')) and 'spline' in k:
        actors.append({'label':L,'class':C,'tag':'roadish'})
print('QUICK', json.dumps({'exists':exists,'instance_actors':actors[:40],'lake':lake}, default=str))
