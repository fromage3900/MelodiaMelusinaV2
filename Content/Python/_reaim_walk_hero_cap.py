
import unreal, math, json
from pathlib import Path
from datetime import datetime, timezone

def label(a):
    try: return a.get_actor_label() or ''
    except: return ''

def look_at(from_v, to_v):
    d = unreal.Vector(to_v.x-from_v.x, to_v.y-from_v.y, to_v.z-from_v.z)
    yaw = math.degrees(math.atan2(d.y, d.x))
    horiz = math.sqrt(d.x*d.x + d.y*d.y) or 1.0
    pitch = math.degrees(math.atan2(d.z, horiz))
    return unreal.Rotator(-pitch, yaw, 0.0)

svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
field = next((a for a in svc.get_all_level_actors() if label(a)=='WC_morning_rainbow_bloom_Field'), None)
fl = field.get_actor_location() if field else unreal.Vector(-2300,1440,66)
# aim at upper third of field for meadow read
look = unreal.Vector(fl.x, fl.y, fl.z + 120)
fixed = []
for name in ('WC_Lookdev_walk_deck_meadow','WC_Lookdev_walk_deck_approach'):
    a = next((x for x in svc.get_all_level_actors() if label(x)==name), None)
    if not a: continue
    loc = a.get_actor_location()
    rot = look_at(loc, look)
    a.set_actor_location_and_rotation(loc, rot, False, False)
    fixed.append({'label': name, 'loc':[loc.x,loc.y,loc.z], 'yaw': rot.yaw, 'pitch': rot.pitch})

# capture midmorning walk only
uds = next((a for a in svc.get_all_level_actors() if label(a)=='Ultra_Dynamic_Sky2'), None)
if uds:
    uds.set_editor_property('Animate Time of Day', False)
    uds.set_editor_property('Time of Day', 1100.0)
    uds.set_editor_property('Cloud Coverage', 1.8)
    uds.set_editor_property('Sun Light Intensity', 5.5)
    uds.set_editor_property('Overall Intensity', 1.25)

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
out_dir = Path(unreal.Paths.project_dir())/'Saved'/'Portfolio'/'Hero'/'MelusinaMorning'
rt = unreal.RenderingLibrary.create_render_target2d(world, 1920, 1080, unreal.TextureRenderTargetFormat.RTF_RGBA8, unreal.LinearColor(0,0,0,1), False)
cap = svc.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(0,0,0))
shots=[]
try:
    comp = cap.get_editor_property('capture_component2d')
    comp.set_editor_property('texture_target', rt)
    comp.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    for name in ('WC_Lookdev_walk_deck_meadow','WC_Lookdev_walk_deck_approach'):
        a = next((x for x in svc.get_all_level_actors() if label(x)==name), None)
        if not a: continue
        loc=a.get_actor_location(); rot=a.get_actor_rotation()
        cap.set_actor_location_and_rotation(loc, rot, False, False)
        cam=a.get_component_by_class(unreal.CameraComponent)
        fov=60.0
        if cam:
            try: fov=float(cam.get_editor_property('field_of_view'))
            except: pass
        comp.set_editor_property('fov_angle', fov)
        for _ in range(4):
            comp.capture_scene()
        short=name.replace('WC_Lookdev_','')
        fn=out_dir/('hero_midmorning_%s_reaim_2026-09-20.png'%short)
        opts=unreal.ImageWriteOptions()
        opts.set_editor_property('format', unreal.DesiredImageFormat.PNG)
        opts.set_editor_property('overwrite_file', True)
        opts.set_editor_property('async_', False)
        unreal.ImageWriteBlueprintLibrary.export_to_disk(rt, str(fn).replace('\\','/'), opts)
        shots.append({'name':short,'file':str(fn),'bytes':fn.stat().st_size if fn.exists() else 0})
finally:
    cap.destroy_actor()
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print('REAIM', json.dumps({'fixed':fixed,'shots':shots}))
