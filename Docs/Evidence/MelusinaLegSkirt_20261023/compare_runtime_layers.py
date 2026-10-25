"""Reversible same-pawn leg/cloth comparison. No asset writes or bindings."""
import unreal, json, math, pathlib, time

def start_leg_skirt_comparison():
    out = pathlib.Path(unreal.Paths.project_saved_dir()) / 'Audit/MelusinaLegSkirt_20261023'
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world()
    assert w, 'PIE absent'
    p = unreal.GameplayStatics.get_player_pawn(w, 0)
    assert p and p.get_class().get_name() == 'BP_MelusinaJRPGCharacter_C'
    comps = list(p.get_components_by_class(unreal.SkeletalMeshComponent))
    body = next(c for c in comps if c.get_name() == 'CharacterMesh0')
    boom = next(c for c in p.get_components_by_class(unreal.SpringArmComponent) if c.get_name() == 'SpringArm')
    movement = p.get_component_by_class(unreal.CharacterMovementComponent)
    cv = ['a.AnimNode.FootPlacement.Enable', 'a.AnimNode.LegIK.Enable', 'a.AnimNode.KawaiiPhysics.Enable']
    saved_cv = {x: unreal.SystemLibrary.get_console_variable_int_value(x) for x in cv}
    saved_vis = {c.get_name(): c.is_visible() for c in comps}
    static_only=bool(globals().get('MEL_USE_STATIC_CAMERAS_ONLY',False))
    saved_camera = {} if static_only else {k: boom.get_editor_property(k) for k in ['relative_rotation','use_pawn_control_rotation','do_collision_test','target_arm_length','socket_offset','target_offset']}
    widgets = []
    for x, _ in widgets: x.set_visibility(unreal.SlateVisibility.HIDDEN)
    if not static_only:
        boom.set_editor_property('use_pawn_control_rotation', False)
        boom.set_editor_property('do_collision_test', False)
        boom.set_editor_property('target_arm_length', 230.0)
        boom.set_editor_property('socket_offset', unreal.Vector(0,0,0))
        boom.set_editor_property('target_offset', unreal.Vector(0,0,-20))
    phases = [
        ('all_on_outfit', (1,1,1), True),
        ('all_on_body', (1,1,1), False),
        ('legik_off_body', (1,0,1), False),
        ('foot_legik_off_body', (0,0,1), False),
        ('all_solvers_off_body', (0,0,0), False),
        ('kawaii_off_outfit', (1,1,0), True),
    ]
    prefix=str(globals().get('MEL_COMPARE_PREFIX',''))
    if globals().get('MEL_CAPTURE_ONLY',False): phases=phases[:2]
    if globals().get('MEL_CAPTURE_OUTFIT_ONLY',False): phases=phases[:1]
    bones = ['root','root_x','spine_01_x','head_x','c_kilt_master_x'] + [b+'_'+s for s in ['l','r'] for b in ['thigh_stretch','leg_stretch','foot','toes_01','c_foot_ik']]
    state = {'samples': [], 'errors': [], 'phase': 0, 'view': 0, 'stage': 'begin', 'started_wall': time.monotonic(), 'saved_cvars': saved_cv, 'finished': False}
    def finish(error=None):
        if state['finished']: return
        if error: state['errors'].append(str(error))
        unreal.unregister_slate_post_tick_callback(state['handle'])
        state['handle'] = None
        for x,v in saved_cv.items(): unreal.SystemLibrary.execute_console_command(w, x+' '+str(v))
        for c in p.get_components_by_class(unreal.SkeletalMeshComponent):
            if c.get_name() in saved_vis: c.set_visibility(saved_vis[c.get_name()],False)
        for k,v in saved_camera.items(): boom.set_editor_property(k,v)
        for x,v in widgets: x.set_visibility(v)
        movement.stop_movement_immediately()
        state['finished'] = True
        (out/(prefix+'runtime_layer_comparison.json')).write_text(json.dumps(state,indent=2))
        print('MELUSINA_LEG_COMPARISON_FINISHED', len(state['samples']), state['errors'])
    def point(b):
        t=body.get_socket_transform(b,unreal.RelativeTransformSpace.RTS_COMPONENT)
        return [t.translation.x,t.translation.y,t.translation.z]
    def sample():
        pos={b:point(b) for b in bones}
        derived={}
        for s in ['l','r']:
            h,k,f=[pos[b+'_'+s] for b in ['thigh_stretch','leg_stretch','foot']]
            a=[x-y for x,y in zip(h,k)]; b=[x-y for x,y in zip(f,k)]
            den=math.sqrt(sum(v*v for v in a)*sum(v*v for v in b))
            derived[s]={'thigh_length':math.dist(h,k),'calf_length':math.dist(k,f),'knee_angle':math.degrees(math.acos(max(-1,min(1,sum(x*y for x,y in zip(a,b))/den)))),'hip_foot_distance':math.dist(h,f)}
        return {'bones_cs':pos,'derived':derived,'actor':str(p.get_actor_location()),'velocity':str(p.get_velocity()),'cvars':{x:unreal.SystemLibrary.get_console_variable_int_value(x) for x in cv}}
    def tick(dt):
        try:
            if time.monotonic()-state['started_wall']>110: return finish('comparison timeout')
            name,values,dressed=phases[state['phase']]
            now=unreal.GameplayStatics.get_time_seconds(w)
            if state['stage']=='begin':
                for x,v in zip(cv,values): unreal.SystemLibrary.execute_console_command(w,x+' '+str(v))
                current_comps=list(p.get_components_by_class(unreal.SkeletalMeshComponent))
                for c in current_comps:
                    c.set_visibility(saved_vis.get(c.get_name(),True) if dressed else c==body,False)
                # Hair, weapon and wings obscure body/skirt inspection even with the outfit present.
                for c in list(p.get_components_by_class(unreal.SkeletalMeshComponent)):
                    if c.get_name() in ['WaterHairMesh','HatMesh','MelusinaWings','WaveHarpInstrumentPresentation']: c.set_visibility(False,False)
                if not static_only:
                    boom.set_editor_property('relative_rotation',unreal.Rotator(pitch=-5,yaw=180 if state['view']==0 else 90,roll=0))
                label='DiagnosticFrontCamera' if state['view']==0 else 'DiagnosticSideCamera'
                cam=next((a for a in unreal.GameplayStatics.get_all_actors_of_class(w,unreal.CameraActor) if a.get_actor_label()==label),None)
                if cam: unreal.GameplayStatics.get_player_controller(w,0).set_view_target_with_blend(cam,0)
                state['phase_start']=now;state['stage']='settle';return
            if state['stage']=='settle':
                if now-state['phase_start']<1.0:return
                row=sample();row.update({'case':name,'view':'front' if state['view']==0 else 'side'})
                fn=str(out/(prefix+name+'_'+row['view']+'.png')).replace('\\','/')
                row['image']=fn;state['samples'].append(row)
                unreal.SystemLibrary.execute_console_command(w,'HighResShot 1280x900 filename="'+fn+'"')
                state['pending']=fn;state['stage']='capture';return
            if state['stage']=='capture':
                if not pathlib.Path(state['pending']).exists():return
                if state['view']==0:state['view']=1;state['stage']='begin';return
                state['view']=0;state['phase']+=1;state['stage']='begin'
                if state['phase']==len(phases):finish()
        except Exception as e: finish(e)
    state['handle']=unreal.register_slate_post_tick_callback(tick)
    unreal._mel_legskirt_comparison=state
    print('MELUSINA_LEG_COMPARISON_STARTED')

start_leg_skirt_comparison()
