"""Bounded P0 injected-movement/contact capture; runtime only, gameplay camera."""
import unreal,json,pathlib,math,time,importlib.util
OUT=pathlib.Path(unreal.Paths.project_saved_dir()).resolve()/'Audit/MelusinaLegSkirt_20261023'
w=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world();assert w
assert '/Melodia/Levels/Opening/' in w.get_path_name() and 'L_MelusinaHouse_P0' in w.get_path_name(), 'Owner requires P0-only runtime testing'
fluid_spec=importlib.util.spec_from_file_location('mel_p0_water_hair_audit',pathlib.Path(unreal.Paths.project_content_dir())/'Python/audit_melusina_water_hair.py')
fluid_audit=importlib.util.module_from_spec(fluid_spec);fluid_spec.loader.exec_module(fluid_audit)
p=unreal.GameplayStatics.get_player_pawn(w,0);assert p.get_class().get_name()=='BP_MelusinaJRPGCharacter_C'
body=next(c for c in p.get_components_by_class(unreal.SkeletalMeshComponent) if c.get_name()=='CharacterMesh0')
movement=p.get_component_by_class(unreal.CharacterMovementComponent)
wc=p.get_component_by_class(unreal.load_class(None,'/Script/MelodiaWardrobe.MelodiaWardrobeComponent'))
candidate=globals().get('MEL_PROBE_ANIM_ASSET','/Game/Staging/AnimationDoctor/LegSkirt_20261023/ABP_LegSkirt_Locomotion_Candidate')
tag=globals().get('MEL_LOCOMOTION_TAG','injected_locomotion_contact')
body.set_anim_instance_class(unreal.load_class(None,candidate+'.'+candidate.rsplit('/',1)[-1]+'_C'))
wc.equip_garment(unreal.MelodiaWardrobeSlot.BOOTS,unreal.load_asset('/Game/Staging/AnimationDoctor/LegSkirt_20261023/SK_Melusina_V2_Boots_WeightClean_Candidate'))
pc=unreal.GameplayStatics.get_player_controller(w,0)
visibility={c.get_name():c.is_visible() for c in p.get_components_by_class(unreal.SkeletalMeshComponent)}
cv=['a.AnimNode.FootPlacement.Enable','a.AnimNode.LegIK.Enable','a.AnimNode.KawaiiPhysics.Enable']
saved={x:unreal.SystemLibrary.get_console_variable_int_value(x) for x in cv}
for x in cv:unreal.SystemLibrary.execute_console_command(w,x+' 1')
unreal.SystemLibrary.execute_console_command(w,cv[-1]+' '+str(int(globals().get('MEL_KAWAII_ENABLED',1))))
ring={b['name']:b for b in json.loads((OUT/'waist_ring_reference.json').read_text())['bones'] if b['name']!='c_kilt_master_x'}
assert all(b['parent_name']=='c_kilt_master_x' for b in ring.values())
phases=[('idle',1.5),('walk',3.),('turn',2.),('stop',2.)]
st={'phase':0,'phase_started':None,'started':time.monotonic(),'samples':[],'skin':[],'screens':[],
    'errors':[],'finished':False,'last_sample':-1.,'last_skin':-1.,'input_proof':'injected ACharacter.AddMovementInput, not physical input',
    'max_walk_speed':movement.get_editor_property('max_walk_speed'),'requested_speed':220.,'candidate_anim':candidate,
    'kawaii_enabled':int(globals().get('MEL_KAWAII_ENABLED',1)),
    'world':w.get_path_name(),'camera_proof':'Existing gameplay view; full equipped outfit retained',
    'contact_reference':'World collision traces beneath sampled skinned boot minima, not diagnostic Z=0',
    'owner_boundary':'Run only after exclusive P0 editor testing is available; material pass currently retains control'}
def vec(v):return [v.x,v.y,v.z]
def finish(error=None):
 if st['finished']:return
 if error:st['errors'].append(str(error))
 unreal.unregister_slate_post_tick_callback(st['handle']);st['handle']=None
 movement.stop_movement_immediately()
 for x,v in saved.items():unreal.SystemLibrary.execute_console_command(w,x+' '+str(v))
 for c in p.get_components_by_class(unreal.SkeletalMeshComponent):
  if c.get_name() in visibility:c.set_visibility(visibility[c.get_name()],False)
 pc.set_view_target_with_blend(p,0)
 st['finished']=True
 (OUT/(tag+'.json')).write_text(json.dumps(st,indent=2));print('MEL_LOCOMOTION_FINISHED',len(st['samples']),len(st['skin']),st['errors'])
def tick(dt):
 try:
  if time.monotonic()-st['started']>60:return finish('wall timeout')
  now=unreal.GameplayStatics.get_time_seconds(w)
  if st['phase_started'] is None:st['phase_started']=now
  name,duration=phases[st['phase']];elapsed=now-st['phase_started']
  if name in ['walk','turn']:
   angle=0 if name=='walk' else min(1,elapsed/duration)*math.pi*.5
   p.add_movement_input(unreal.Vector(math.cos(angle),math.sin(angle),0),min(1,220/st['max_walk_speed']),False)
  at=p.get_actor_location()
  if now-st['last_sample']>=.10:
   st['last_sample']=now;bones={}
   for n in ['root_x','c_traj']+[x+'_'+s for s in ['l','r'] for x in ['thigh_stretch','leg_stretch','foot']]:
    bones[n]=vec(body.get_socket_transform(n,unreal.RelativeTransformSpace.RTS_COMPONENT).translation)
   knees={}
   for s in ['l','r']:
    h,k,f=[bones[x+'_'+s] for x in ['thigh_stretch','leg_stretch','foot']];a=[x-y for x,y in zip(h,k)];b=[x-y for x,y in zip(f,k)]
    knees[s]=math.degrees(math.acos(max(-1,min(1,sum(x*y for x,y in zip(a,b))/math.sqrt(sum(x*x for x in a)*sum(x*x for x in b))))))
   boot=wc.get_slot_component(unreal.MelodiaWardrobeSlot.BOOTS)
   master=body.get_socket_transform('c_kilt_master_x',unreal.RelativeTransformSpace.RTS_COMPONENT)
   waist={};root_rotations={};lower_chains={}
   for n,ref in ring.items():
    actual=unreal.MathLibrary.make_relative_transform(body.get_socket_transform(n,unreal.RelativeTransformSpace.RTS_COMPONENT),master).translation
    waist[n]=math.dist(vec(actual),[ref['local']['location'][a] for a in ['x','y','z']])
    rt=unreal.MathLibrary.make_relative_transform(body.get_socket_transform(n,unreal.RelativeTransformSpace.RTS_COMPONENT),master)
    q=rt.rotation;root_rotations[n]=[q.x,q.y,q.z,q.w]
    chain,_joint,side=n.rsplit('_',2);tip=chain+'_04_'+side
    lower_chains[tip]=vec(unreal.MathLibrary.make_relative_transform(body.get_socket_transform(tip,unreal.RelativeTransformSpace.RTS_COMPONENT),body.get_socket_transform(n,unreal.RelativeTransformSpace.RTS_COMPONENT)).translation)
   st['samples'].append({'t':now,'phase':name,'elapsed':elapsed,'location':vec(at),'velocity':vec(p.get_velocity()),'speed':p.get_velocity().length(),
    'knees':knees,'bones_cs':bones,'waist_ring_deviation_cm':waist,'waist_root_rotations_xyzw':root_rotations,'lower_chain_tips_in_first_root_cm':lower_chains,'anim':body.get_anim_instance().get_class().get_path_name(),'boots':boot.get_skinned_asset().get_path_name()})
  if now-st['last_skin']>=.5:
   st['last_skin']=now;boot=wc.get_slot_component(unreal.MelodiaWardrobeSlot.BOOTS)
   opt=unreal.GeometryScriptCopyMeshFromComponentOptions();opt.set_editor_property('requested_lod',unreal.GeometryScriptMeshReadLOD(lod_type=unreal.GeometryScriptLODType.RENDER_DATA,lod_index=0))
   dm,xf,result=unreal.GeometryScript_SceneUtils.copy_mesh_from_component(boot,unreal.DynamicMesh(),opt,True);assert result==unreal.GeometryScriptOutcomePins.SUCCESS
   _,vl,valid=unreal.GeometryScript_MeshQueries.get_all_vertex_positions(dm,False);vs=unreal.GeometryScript_List.convert_vector_list_to_array(vl)
   foot_pos={side:body.get_socket_transform('foot_'+side,unreal.RelativeTransformSpace.RTS_WORLD).translation for side in ['l','r']}
   groups={side:[] for side in foot_pos}
   for v in vs:
    side=min(foot_pos,key=lambda s:(v-foot_pos[s]).length_squared());groups[side].append(v)
   contacts={}
   for side,verts in groups.items():
    if not verts:continue
    low=min(verts,key=lambda v:v.z)
    hit=unreal.SystemLibrary.line_trace_single(w,low+unreal.Vector(0,0,45),low-unreal.Vector(0,0,200),unreal.TraceTypeQuery.TRACE_TYPE_QUERY1,False,[p],unreal.DrawDebugTrace.NONE,True)
    contacts[side]={'lowest_world':vec(low),'vertex_partition':'nearest current ankle; not verified source vertex identity','hit':hit is not None}
    if hit:
     hit_data=hit.to_dict();impact=hit_data['impact_point'];normal=hit_data['impact_normal']
     contacts[side].update({'collision_point':vec(impact),'normal':vec(normal),'vertical_clearance_cm':low.z-impact.z})
   st['skin'].append({'t':now,'phase':name,'speed':p.get_velocity().length(),'minimum_world_z':min(v.z for v in vs),'vertices':len(vs),'contacts':contacts,
     'fluid_observation':fluid_audit.sample_p0_fluid(read_pixels=bool(globals().get('MEL_CAPTURE_FLUID_PIXELS',False)))})
  if elapsed>=duration:
   fn=OUT/(tag+'_move_'+name+'.png');unreal.SystemLibrary.execute_console_command(w,'HighResShot 1280x900 filename="'+fn.as_posix()+'"');st['screens'].append(fn.as_posix())
   st['phase']+=1;st['phase_started']=now
   if st['phase']==len(phases):finish()
 except Exception as exc:finish(exc)
st['handle']=unreal.register_slate_post_tick_callback(tick);unreal._mel_locomotion_probe=st
print('MEL_LOCOMOTION_STARTED')
