
import unreal, json, sys
from pathlib import Path
sys.path.insert(0, r'C:/EnvironmentPortfolio/BS_GodFile/Content/Python')
import world_compiler_ue as wc

svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
uds = next((a for a in svc.get_all_level_actors() if a.get_actor_label() == 'Ultra_Dynamic_Sky2'), None)
before = {}
after = {}
if uds:
    for prop in ('Time of Day', 'Cloud Coverage', 'Overall Intensity', 'Sun Light Intensity', 'Animate Time of Day', 'Night Brightness'):
        try:
            before[prop] = uds.get_editor_property(prop)
        except Exception as e:
            before[prop] = str(e)
    # Mid-morning lookdev: 10:30 clock (1030 on 0..2400), clearer sky, brighter sun
    try:
        uds.set_editor_property('Animate Time of Day', False)
        uds.set_editor_property('Time of Day', 1030.0)
        uds.set_editor_property('Cloud Coverage', 1.2)
        uds.set_editor_property('Overall Intensity', 1.15)
        uds.set_editor_property('Sun Light Intensity', 8.0)
    except Exception as e:
        print('SET_ERR', e)
    for prop in before:
        try:
            after[prop] = uds.get_editor_property(prop)
        except Exception as e:
            after[prop] = str(e)
print('UDS', json.dumps({'before': before, 'after': after}, default=str))

# Soft translucency read on flower bands: slight MelodiaWindResponse stay 0.5; bump SharedFlexibility a touch already set
# Re-run lookdev capture only (cameras already placed)
bundle = Path(r'C:/EnvironmentPortfolio/BS_GodFile/Saved/WorldCompiler/morning_rainbow_bloom_3900')
b = wc._load_bundle(bundle)
# ensure cameras exist
wc.step_lookdev_cameras(b)
cap = wc.step_lookdev_capture(b)
print('CAPTURE', json.dumps(cap.get('shots'), default=str)[:2000])

# Restore walk + FX after beauty hide; keep Houdini hidden
restored = 0
for a in svc.get_all_level_actors():
    label = a.get_actor_label() or ''
    if label.startswith('WC_EscherWalk_') or label in ('FX_Morning_Mist', 'FX_Morning_Bed_PollenSparkle'):
        a.set_is_temporarily_hidden_in_editor(False)
        a.set_actor_hidden_in_game(False)
        restored += 1
    if label in ('HoudiniEngine_RainbowBloom_3900', 'Houdini_RainbowBloom_3900'):
        a.set_is_temporarily_hidden_in_editor(True)
        a.set_actor_hidden_in_game(True)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print('RESTORED', restored, 'SAVED')
