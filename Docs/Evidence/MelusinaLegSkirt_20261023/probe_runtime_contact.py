"""Same-tick body, leg and equipped-footwear probe; no asset mutation."""
import unreal, json, pathlib, math

def probe_melusina_contact(tag):
    w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    p=unreal.GameplayStatics.get_player_pawn(w,0)
    body=next(c for c in p.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name()=='CharacterMesh0')
    r={'tag':tag,'pawn':p.get_path_name(),'anim':body.get_anim_instance().get_class().get_path_name(),'bones':{},'knees':{},'skin':[],'speed':p.get_velocity().length()}
    for n in ['root','c_traj','root_x','head_x','c_kilt_master_x']+[n+'_'+s for s in ['l','r'] for n in ['thigh_stretch','leg_stretch','foot','toes_01','c_foot_ik']]:
        t=body.get_socket_transform(n,unreal.RelativeTransformSpace.RTS_COMPONENT)
        r['bones'][n]=[t.translation.x,t.translation.y,t.translation.z]
    for s in ['l','r']:
        h,k,f=[r['bones'][n+'_'+s] for n in ['thigh_stretch','leg_stretch','foot']]
        a=[x-y for x,y in zip(h,k)];d=[x-y for x,y in zip(f,k)]
        r['knees'][s]=math.degrees(math.acos(max(-1,min(1,sum(x*y for x,y in zip(a,d))/math.sqrt(sum(x*x for x in a)*sum(x*x for x in d))))))
    for c in p.get_components_by_class(unreal.SkeletalMeshComponent):
        if c!=body and 'Boots' not in c.get_name():continue
        opt=unreal.GeometryScriptCopyMeshFromComponentOptions()
        opt.set_editor_property('requested_lod',unreal.GeometryScriptMeshReadLOD(lod_type=unreal.GeometryScriptLODType.RENDER_DATA,lod_index=0))
        dm,xf,result=unreal.GeometryScript_SceneUtils.copy_mesh_from_component(c,unreal.DynamicMesh(),opt,True)
        assert result==unreal.GeometryScriptOutcomePins.SUCCESS
        _,vl,g=unreal.GeometryScript_MeshQueries.get_all_vertex_positions(dm,False)
        vs=unreal.GeometryScript_List.convert_vector_list_to_array(vl)
        feet={s:body.get_socket_transform('foot_'+s,unreal.RelativeTransformSpace.RTS_WORLD).translation for s in ['l','r']}
        groups={s:[] for s in ['l','r']}
        for v in vs:
            s=min(feet,key=lambda s:(v.x-feet[s].x)**2+(v.y-feet[s].y)**2)
            groups[s].append(v.z)
        r['skin'].append({'component':c.get_name(),'mesh':c.get_skinned_asset().get_path_name(),'vertices':len(vs),'min_world_z':min(v.z for v in vs),'per_foot_lowest_world_z':{s:min(z) for s,z in groups.items() if z}})
    out=pathlib.Path(unreal.Paths.project_saved_dir()).resolve()/'Audit/MelusinaLegSkirt_20261023'
    (out/(tag+'.json')).write_text(json.dumps(r,indent=2))
    print(json.dumps(r))
    return r

probe_melusina_contact(globals().get('MEL_PROBE_TAG','contact_probe'))
