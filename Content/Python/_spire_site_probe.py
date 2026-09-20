import unreal, json
EAL = unreal.EditorAssetLibrary
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

def lab(a):
    try: return a.get_actor_label() or ''
    except: return ''

lake=None
for a in svc.get_all_level_actors():
    L=lab(a); C=a.get_class().get_name()
    if L=='Morning_SheepDell_Lake' or 'OceanologyLake' in C:
        t=a.get_actor_transform()
        try:
            o,e=a.get_actor_bounds(False,False)
            ext=[e.x,e.y,e.z]
        except Exception:
            ext=None
        lake={'label':L,'class':C,'loc':[t.translation.x,t.translation.y,t.translation.z],'scale':[t.scale3d.x,t.scale3d.y,t.scale3d.z],'extent':ext}

# SDF MI paths
mis=[]
for p in [
 '/Game/EnvSandbox/Materials/Instances/SDFArchitecture/MI_SDF_CrystallineSpire',
 '/Game/EnvSandbox/Materials/Instances/SDFArchitecture/MI_SDF_Musical',
 '/Game/EnvSandbox/Materials/Instances/SDFArchitecture/MI_SDF_CrystallineSpire',
]:
    pass
# list architecture folder
root='/Game/EnvSandbox/Materials/Instances/SDFArchitecture'
found=[]
if EAL.does_directory_exist(root):
    for p in EAL.list_assets(root, False, False) or []:
        if 'Cosmic' in p or 'Portal' in p or 'Musical' in p or 'Spire' in p or 'Cathedral' in p:
            found.append(p)

gb='/Game/EnvSandbox/Greybox_Kit/SM_Greybox_Cube_1m'
print('SITE', json.dumps({'lake':lake,'sdf_hits':found,'greybox':EAL.does_asset_exist(gb),'ios':EAL.does_asset_exist('/Game/Actor_BP/BP_InstanceOnSpline')}, default=str))
