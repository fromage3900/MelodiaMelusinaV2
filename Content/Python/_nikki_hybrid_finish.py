"""Finish placement snap + verify hybrid convert after Transform fix."""
import unreal, json
from pathlib import Path
from datetime import datetime, timezone

EAL=unreal.EditorAssetLibrary; MEL=unreal.MaterialEditingLibrary
HYBRID='/Game/EnvSandbox/Materials/Masters/M_MelodiaPlant_Wind_NikkiToon'
BAND_PREFIX='/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_'
BANDS=['B0_Red','B1_Orange','B2_Gold','B3_Green','B4_Blue','B5_Indigo','B6_Violet']

def label(a):
    try: return a.get_actor_label() or ''
    except: return ''

# Verify hybrid + bands
verify={'hybrid_exists': EAL.does_asset_exist(HYBRID), 'bands':[]}
if verify['hybrid_exists']:
    m=EAL.load_asset(HYBRID)
    sc=[str(n) for n in MEL.get_scalar_parameter_names(m)]
    verify['hybrid']={'PastelLift':'PastelLift' in sc,'DreamSaturation':'DreamSaturation' in sc,
                      'SharedBend':'SharedBend' in sc,'MelodiaWindResponse':'MelodiaWindResponse' in sc}
for lab in BANDS:
    path=BAND_PREFIX+lab
    mi=EAL.load_asset(path)
    if not mi:
        verify['bands'].append({'label':lab,'ok':False}); continue
    p=mi.get_editor_property('parent')
    sc=[str(n) for n in MEL.get_scalar_parameter_names(mi)]
    verify['bands'].append({
        'label':lab,
        'parent': p.get_path_name() if p else None,
        'PastelLift':'PastelLift' in sc,
        'SharedBend':'SharedBend' in sc,
        'DreamSaturation': 'DreamSaturation' in sc,
    })

svc=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world=unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
field=next((a for a in svc.get_all_level_actors() if label(a)=='WC_morning_rainbow_bloom_Field'), None)

removed=0; snapped=0
if field:
    for comp in list(field.get_components_by_class(unreal.InstancedStaticMeshComponent) or []):
        mesh=comp.get_editor_property('static_mesh')
        if not mesh or 'GenericFlower' not in mesh.get_name():
            continue
        n=int(comp.get_instance_count())
        kill=[]
        for i in range(n):
            try: xf=comp.get_instance_transform(i, True)
            except: continue
            t=xf.translation
            hit=unreal.SystemLibrary.line_trace_single(
                world, unreal.Vector(t.x,t.y,t.z+500), unreal.Vector(t.x,t.y,t.z-3000),
                unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
                unreal.DrawDebugTrace.NONE, True,
                unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0)
            tup=hit.to_tuple() if hit else None
            if not tup or not tup[0]:
                kill.append(i); continue
            lab=tup[9].get_actor_label() if tup[9] else ''
            if not lab.startswith('BrushifyIsland_') or float(tup[5].z)<0.65:
                kill.append(i); continue
            # copy transform, only change translation Z via translation setter
            try:
                new_xf = unreal.Transform()
                new_xf.translation = unreal.Vector(t.x, t.y, float(tup[4].z))
                new_xf.rotation = xf.rotation
                new_xf.scale3d = xf.scale3d
                # Prefer update with world space; if rotation is quat, use set_instance_transform differently
                ok=comp.update_instance_transform(i, new_xf, True, True, True)
                if not ok:
                    # fallback: remove+readd
                    pass
                snapped+=1
            except Exception as e:
                # fallback using EditorStaticMeshLibrary? just leave
                try:
                    xf2=comp.get_instance_transform(i, True)
                    loc=unreal.Vector(t.x,t.y,float(tup[4].z))
                    rot=xf2.rotation.rotator() if hasattr(xf2.rotation,'rotator') else unreal.Rotator(0,0,0)
                    scale=xf2.scale3d
                    nt=unreal.Transform(loc, rot, scale)
                    comp.update_instance_transform(i, nt, True, True, True)
                    snapped+=1
                except Exception:
                    pass
        for i in sorted(kill, reverse=True):
            try:
                comp.remove_instance(i); removed+=1
            except: pass
        try: comp.mark_render_state_dirty()
        except: pass

# dress
destroyed=[]; fixed=[]
for a in list(svc.get_all_level_actors()):
    lab=label(a)
    if not lab.startswith('WC_PortfolioDress_'): continue
    loc=a.get_actor_location()
    hit=unreal.SystemLibrary.line_trace_single(
        world, unreal.Vector(loc.x,loc.y,loc.z+2000), unreal.Vector(loc.x,loc.y,loc.z-4000),
        unreal.TraceTypeQuery.ECC_VISIBILITY, False, [],
        unreal.DrawDebugTrace.NONE, True,
        unreal.LinearColor.RED, unreal.LinearColor.GREEN, 0.0)
    tup=hit.to_tuple() if hit else None
    if not tup or not tup[0]:
        svc.destroy_actor(a); destroyed.append(lab); continue
    glab=tup[9].get_actor_label() if tup[9] else ''
    if not (glab.startswith('Brushify') or glab.startswith('WC_EscherWalk_')):
        svc.destroy_actor(a); destroyed.append(lab); continue
    a.set_actor_location(unreal.Vector(tup[4].x,tup[4].y,tup[4].z), False, False)
    try:
        s=a.get_actor_scale3d(); sc=max(0.55,min(1.45,(s.x+s.y+s.z)/3.0))
        a.set_actor_scale3d(unreal.Vector(sc,sc,sc))
    except: pass
    fixed.append(lab)

# capture
uds=next((a for a in svc.get_all_level_actors() if label(a)=='Ultra_Dynamic_Sky2'), None)
if uds:
    uds.set_editor_property('Animate Time of Day', False)
    uds.set_editor_property('Time of Day', 1100.0)
    uds.set_editor_property('Cloud Coverage', 1.8)
    uds.set_editor_property('Sun Light Intensity', 5.5)
    uds.set_editor_property('Overall Intensity', 1.25)

out_dir=Path(unreal.Paths.project_dir())/'Saved'/'Portfolio'/'Hero'/'MelusinaMorning'
rt=unreal.RenderingLibrary.create_render_target2d(world,1920,1080,unreal.TextureRenderTargetFormat.RTF_RGBA8,unreal.LinearColor(0,0,0,1),False)
cap=svc.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(0,0,0))
shots=[]
try:
    comp=cap.get_editor_property('capture_component2d')
    comp.set_editor_property('texture_target', rt)
    comp.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    for name in ['WC_Lookdev_walk_deck_meadow','WC_Lookdev_walk_deck_approach','WC_Lookdev_website_oblique','WC_Lookdev_website_south']:
        a=next((x for x in svc.get_all_level_actors() if label(x)==name), None)
        if not a: continue
        cap.set_actor_location_and_rotation(a.get_actor_location(), a.get_actor_rotation(), False, False)
        cam=a.get_component_by_class(unreal.CameraComponent)
        fov=60.0
        if cam:
            try: fov=float(cam.get_editor_property('field_of_view'))
            except: pass
        comp.set_editor_property('fov_angle', fov)
        for _ in range(4):
            comp.capture_scene()
        short=name.replace('WC_Lookdev_','')
        fn=out_dir/('hero_midmorning_%s_nikki_2026-09-20.png'%short)
        opts=unreal.ImageWriteOptions()
        opts.set_editor_property('format', unreal.DesiredImageFormat.PNG)
        opts.set_editor_property('overwrite_file', True)
        opts.set_editor_property('async_', False)
        unreal.ImageWriteBlueprintLibrary.export_to_disk(rt, str(fn).replace('\\','/'), opts)
        shots.append({'name':short,'bytes':fn.stat().st_size if fn.exists() else 0})
finally:
    cap.destroy_actor()

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
report={'verify':verify,'place':{'removed':removed,'snapped':snapped},
        'dress':{'fixed':len(fixed),'destroyed':destroyed},'shots':shots}
out=Path(unreal.Paths.project_dir())/'Saved'/'Audit'/'nikki_hybrid_finish_2026-09-20.json'
out.write_text(json.dumps(report, indent=2), encoding='utf-8')
print('FINISH', json.dumps({'verify':verify,'removed':removed,'snapped':snapped,'dress_fixed':len(fixed),'dress_destroyed':len(destroyed),'shots':shots}, default=str))
