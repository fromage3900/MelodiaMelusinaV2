import unreal, json
from pathlib import Path

def label(a):
    try: return a.get_actor_label() or ''
    except: return ''

svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
uds = next((a for a in svc.get_all_level_actors() if label(a)=='Ultra_Dynamic_Sky2'), None)
if uds:
    uds.set_editor_property('Animate Time of Day', False)
    uds.set_editor_property('Time of Day', 1100.0)
    uds.set_editor_property('Cloud Coverage', 1.8)
    uds.set_editor_property('Sun Light Intensity', 5.5)
    uds.set_editor_property('Overall Intensity', 1.25)

names = ['WC_Lookdev_walk_deck_approach','WC_Lookdev_walk_deck_meadow','WC_Lookdev_website_oblique']
cams = [a for a in svc.get_all_level_actors() if label(a) in names]
out_dir = Path(unreal.Paths.project_dir())/'Saved'/'Portfolio'/'Hero'/'MelusinaMorning'
rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8, unreal.LinearColor(0,0,0,1), False)
cap = svc.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(0,0,0))
shots=[]
try:
    comp = cap.get_editor_property('capture_component2d')
    comp.set_editor_property('texture_target', rt)
    comp.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    for a in cams:
        cap.set_actor_location_and_rotation(a.get_actor_location(), a.get_actor_rotation(), False, False)
        cam = a.get_component_by_class(unreal.CameraComponent)
        fov = 60.0
        if cam:
            try: fov=float(cam.get_editor_property('field_of_view'))
            except: pass
        comp.set_editor_property('fov_angle', fov)
        for _ in range(4):
            comp.capture_scene()
        short = label(a).replace('WC_Lookdev_','')
        fn = out_dir / ('hero_midmorning_%s_p1b_2026-09-20.png' % short)
        opts = unreal.ImageWriteOptions()
        opts.set_editor_property('format', unreal.DesiredImageFormat.PNG)
        opts.set_editor_property('overwrite_file', True)
        opts.set_editor_property('async_', False)
        unreal.ImageWriteBlueprintLibrary.export_to_disk(rt, str(fn).replace('\\','/'), opts)
        shots.append({'name': short, 'bytes': fn.stat().st_size if fn.exists() else 0, 'file': str(fn)})
finally:
    cap.destroy_actor()
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print('P1BCAP', json.dumps(shots))
