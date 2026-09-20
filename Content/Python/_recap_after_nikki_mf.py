import unreal, json, math
from pathlib import Path

def label(a):
    try: return a.get_actor_label() or ''
    except: return ''

def look_at(from_v, to_v):
    dx, dy, dz = to_v.x-from_v.x, to_v.y-from_v.y, to_v.z-from_v.z
    yaw = math.degrees(math.atan2(dy, dx))
    horiz = math.sqrt(dx*dx+dy*dy) or 1.0
    pitch = math.degrees(math.atan2(dz, horiz))
    return unreal.Rotator(pitch=pitch, yaw=yaw, roll=0.0)

svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
field = next((a for a in svc.get_all_level_actors() if label(a)=='WC_morning_rainbow_bloom_Field'), None)
fl = field.get_actor_location() if field else unreal.Vector(-2300,1440,66)
look = unreal.Vector(fl.x, fl.y, fl.z+90)

uds = next((a for a in svc.get_all_level_actors() if label(a)=='Ultra_Dynamic_Sky2'), None)
if uds:
    uds.set_editor_property('Animate Time of Day', False)
    uds.set_editor_property('Time of Day', 1130.0)
    uds.set_editor_property('Cloud Coverage', 2.1)
    uds.set_editor_property('Sun Light Intensity', 4.6)
    uds.set_editor_property('Overall Intensity', 1.15)

# beauty visibility
for a in svc.get_all_level_actors():
    lab = label(a)
    if lab.startswith('SM_PM3D_Sphere3D') or lab.startswith('SM_Greybox_') or lab.startswith('Houdini') or lab in ('FX_Morning_Mist','FX_BowStage_PondMist'):
        a.set_is_temporarily_hidden_in_editor(True); a.set_actor_hidden_in_game(True)
    if lab.startswith(('WC_Lookdev_','WC_EscherWalk_','WC_NS_Morning_','WC_PortfolioDress_')) or lab in ('WC_morning_rainbow_bloom_Field','WC_MorningFlowerField_WindSource'):
        a.set_is_temporarily_hidden_in_editor(False); a.set_actor_hidden_in_game(False)

# re-aim locked cams
deck = next((a for a in svc.get_all_level_actors() if label(a)=='WC_EscherWalk_spur_westbank_00'), None)
walk = next((a for a in svc.get_all_level_actors() if label(a)=='WC_Lookdev_walk_deck_meadow'), None)
if walk and deck:
    d = deck.get_actor_location()
    loc = unreal.Vector(d.x, d.y, d.z+170.0)
    walk.set_actor_location(loc, False, False)
    walk.set_actor_rotation(look_at(loc, look), False)
    cam = walk.get_component_by_class(unreal.CameraComponent)
    if cam: cam.set_editor_property('field_of_view', 58.0)

for name, fov, zoff in (('WC_Lookdev_website_oblique',62.0,60.0),('WC_Lookdev_website_south',55.0,140.0)):
    a = next((x for x in svc.get_all_level_actors() if label(x)==name), None)
    if not a: continue
    loc = a.get_actor_location()
    a.set_actor_rotation(look_at(loc, unreal.Vector(fl.x,fl.y,fl.z+zoff)), False)
    cam = a.get_component_by_class(unreal.CameraComponent)
    if cam: cam.set_editor_property('field_of_view', fov)

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
        cap.set_actor_location_and_rotation(a.get_actor_location(), a.get_actor_rotation(), False, False)
        cam = a.get_component_by_class(unreal.CameraComponent)
        fov=60.0
        if cam:
            try: fov=float(cam.get_editor_property('field_of_view'))
            except: pass
        comp.set_editor_property('fov_angle', fov)
        try:
            pps=comp.get_editor_property('post_process_settings')
            pps.set_editor_property('override_auto_exposure_bias', True)
            pps.set_editor_property('auto_exposure_bias', 1.05)
            comp.set_editor_property('post_process_settings', pps)
            comp.set_editor_property('post_process_blend_weight', 1.0)
        except: pass
        for _ in range(5):
            comp.capture_scene()
        short=name.replace('WC_Lookdev_','')
        fn=out_dir/('corner_%s_nikkimf_2026-09-20.png'%short)
        opts=unreal.ImageWriteOptions()
        opts.set_editor_property('format', unreal.DesiredImageFormat.PNG)
        opts.set_editor_property('overwrite_file', True)
        opts.set_editor_property('async_', False)
        unreal.ImageWriteBlueprintLibrary.export_to_disk(rt, str(fn).replace('\\','/'), opts)
        shots.append({'name':short,'bytes':fn.stat().st_size if fn.exists() else 0,'file':str(fn)})
finally:
    cap.destroy_actor()

unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print('RECAP_MF', json.dumps({'shots':shots}))
