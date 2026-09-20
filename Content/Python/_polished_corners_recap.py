import unreal, json, math
from pathlib import Path

EAL=unreal.EditorAssetLibrary; MEL=unreal.MaterialEditingLibrary

def label(a):
    try: return a.get_actor_label() or ''
    except: return ''

def look_at(from_v, to_v):
    dx = to_v.x - from_v.x
    dy = to_v.y - from_v.y
    dz = to_v.z - from_v.z
    yaw = math.degrees(math.atan2(dy, dx))
    horiz = math.sqrt(dx*dx + dy*dy) or 1.0
    pitch = math.degrees(math.atan2(dz, horiz))
    # keyword args — positional Rotator order is unreliable across UE Python builds
    return unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
field = next((a for a in svc.get_all_level_actors() if label(a)=='WC_morning_rainbow_bloom_Field'), None)
fl = field.get_actor_location() if field else unreal.Vector(-2300,1440,66)
look = unreal.Vector(fl.x, fl.y, fl.z + 90)

# Soft UDS for stills
uds = next((a for a in svc.get_all_level_actors() if label(a)=='Ultra_Dynamic_Sky2'), None)
if uds:
    uds.set_editor_property('Animate Time of Day', False)
    uds.set_editor_property('Time of Day', 1130.0)
    uds.set_editor_property('Cloud Coverage', 2.1)
    uds.set_editor_property('Sun Light Intensity', 4.6)
    uds.set_editor_property('Overall Intensity', 1.15)

# Fix walk cam
deck = next((a for a in svc.get_all_level_actors() if label(a)=='WC_EscherWalk_spur_westbank_00'), None)
walk = next((a for a in svc.get_all_level_actors() if label(a)=='WC_Lookdev_walk_deck_meadow'), None)
fixed=[]
if walk and deck:
    dloc = deck.get_actor_location()
    cam_loc = unreal.Vector(dloc.x, dloc.y, dloc.z + 170.0)
    rot = look_at(cam_loc, look)
    walk.set_actor_location(cam_loc, False, False)
    walk.set_actor_rotation(rot, False)
    r2 = walk.get_actor_rotation()
    cam = walk.get_component_by_class(unreal.CameraComponent)
    if cam: cam.set_editor_property('field_of_view', 58.0)
    fixed.append({'label':'walk_deck_meadow','yaw':r2.yaw,'pitch':r2.pitch,'loc':[cam_loc.x,cam_loc.y,cam_loc.z]})

# Fix oblique/south — keep location, aim at field
for name, fov, zoff in (
    ('WC_Lookdev_website_oblique', 62.0, 60.0),
    ('WC_Lookdev_website_south', 55.0, 140.0),
):
    a = next((x for x in svc.get_all_level_actors() if label(x)==name), None)
    if not a: continue
    loc = a.get_actor_location()
    target = unreal.Vector(fl.x, fl.y, fl.z + zoff)
    rot = look_at(loc, target)
    a.set_actor_rotation(rot, False)
    r2 = a.get_actor_rotation()
    cam = a.get_component_by_class(unreal.CameraComponent)
    if cam: cam.set_editor_property('field_of_view', fov)
    fixed.append({'label':name,'yaw':r2.yaw,'pitch':r2.pitch,'loc':[loc.x,loc.y,loc.z]})

# Capture with softer exposure
out_dir = Path(unreal.Paths.project_dir())/'Saved'/'Portfolio'/'Hero'/'MelusinaMorning'/'PolishedCorners'
out_dir.mkdir(parents=True, exist_ok=True)
rt = unreal.RenderingLibrary.create_render_target2d(world,1920,1080,unreal.TextureRenderTargetFormat.RTF_RGBA8,unreal.LinearColor(0,0,0,1),False)
cap = svc.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(0,0,0))
shots=[]
try:
    comp = cap.get_editor_property('capture_component2d')
    comp.set_editor_property('texture_target', rt)
    comp.set_editor_property('capture_source', unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    for name in ('WC_Lookdev_website_oblique','WC_Lookdev_website_south','WC_Lookdev_walk_deck_meadow'):
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
        try:
            pps=comp.get_editor_property('post_process_settings')
            pps.set_editor_property('override_auto_exposure_bias', True)
            pps.set_editor_property('auto_exposure_bias', 1.1)
            comp.set_editor_property('post_process_settings', pps)
            comp.set_editor_property('post_process_blend_weight', 1.0)
        except: pass
        for _ in range(5):
            comp.capture_scene()
        short=name.replace('WC_Lookdev_','')
        fn=out_dir/('corner_%s_hero_2026-09-20.png'%short)
        opts=unreal.ImageWriteOptions()
        opts.set_editor_property('format', unreal.DesiredImageFormat.PNG)
        opts.set_editor_property('overwrite_file', True)
        opts.set_editor_property('async_', False)
        unreal.ImageWriteBlueprintLibrary.export_to_disk(rt, str(fn).replace('\\','/'), opts)
        shots.append({'name':short,'bytes':fn.stat().st_size if fn.exists() else 0,'yaw':rot.yaw,'pitch':rot.pitch})
finally:
    cap.destroy_actor()

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print('CORNERS2', json.dumps({'fixed':fixed,'shots':shots}, default=str))
