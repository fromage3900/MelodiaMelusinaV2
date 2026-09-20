
import unreal, json, sys
from pathlib import Path
sys.path.insert(0, r'C:/EnvironmentPortfolio/BS_GodFile/Content/Python')
import world_compiler_ue as wc
b = wc._load_bundle(Path(r'C:/EnvironmentPortfolio/BS_GodFile/Saved/WorldCompiler/morning_rainbow_bloom_3900'))
wc.step_lookdev_cameras(b)
cap = wc.step_lookdev_capture(b)
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for a in svc.get_all_level_actors():
    lab = a.get_actor_label() or ''
    if lab.startswith('WC_EscherWalk_') or lab.startswith('WC_Lookdev_') or lab == 'WC_morning_rainbow_bloom_Field':
        a.set_is_temporarily_hidden_in_editor(False); a.set_actor_hidden_in_game(False)
    if lab in ('FX_Morning_Mist','FX_Morning_Bed_PollenSparkle','WC_NS_Morning_pollen_fx_pollen_0_0','WC_NS_Morning_petal_fx_petal_0_0','WC_NS_Morning_mist_fx_mist_x_0','WC_NS_Morning_windfront_fx_windfront_x_0','FX_Morning_WaterGlint','FX_Morning_DustShafts_Threshold'):
        a.set_is_temporarily_hidden_in_editor(False); a.set_actor_hidden_in_game(False)
    if lab in ('HoudiniEngine_RainbowBloom_3900','Houdini_RainbowBloom_3900'):
        a.set_is_temporarily_hidden_in_editor(True); a.set_actor_hidden_in_game(True)
# keep beauty hides for spheres/greybox
for a in svc.get_all_level_actors():
    lab = a.get_actor_label() or ''
    if lab.startswith('SM_PM3D_Sphere3D') or lab.startswith('SM_Greybox_'):
        a.set_is_temporarily_hidden_in_editor(True); a.set_actor_hidden_in_game(True)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
print('RECAP', json.dumps([(s['name'], s['bytes']) for s in cap.get('shots') or []], default=str))
