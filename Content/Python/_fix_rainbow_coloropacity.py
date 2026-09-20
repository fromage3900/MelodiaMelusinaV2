
import unreal, json
from pathlib import Path
from datetime import datetime, timezone
MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary

BANDS = ['B0_Red','B1_Orange','B2_Gold','B3_Green','B4_Blue','B5_Indigo','B6_Violet']
PREFIX = '/Game/EnvSandbox/Materials/Instances/Flora/Rainbow/MI_RainbowSpeedTree_'
GHOST_ALBEDO = '/Game/EnvSandbox/Textures/SurrealFlora/T_Surreal_GhostLotus_Albedo'
GHOST_NORMAL = '/Game/EnvSandbox/Textures/SurrealFlora/T_Surreal_GhostLotus_Normal'
GHOST_EMISSIVE = '/Game/EnvSandbox/Textures/SurrealFlora/T_Surreal_GhostLotus_Emissive'
FLOWER_COLOR = '/Game/EnvSandbox/Library/FoliageCards/GenericFlower1_Color_png_Tex'
# Prefer GhostLotus on ColorOpacity (surreal lookdev intent); fall back to flower card
albedo = EAL.load_asset(GHOST_ALBEDO) or EAL.load_asset(FLOWER_COLOR)
normal = EAL.load_asset(GHOST_NORMAL)
emissive = EAL.load_asset(GHOST_EMISSIVE)

changed = []
for label in BANDS:
    path = PREFIX + label
    mi = EAL.load_asset(path)
    if not mi:
        continue
    # Clear dead SpeedTree-unrelated overrides that do nothing on Melodia plant parent
    for dead in ('Albedo', 'EmissiveMap', 'Normal', 'BaseColor', 'Diffuse'):
        try:
            MEL.set_material_instance_texture_parameter_value(mi, dead, None)
        except Exception:
            pass
        try:
            # disable override if API supports
            MEL.set_material_instance_parameter_override(mi, dead, False)
        except Exception:
            pass
    if albedo:
        MEL.set_material_instance_texture_parameter_value(mi, 'ColorOpacity', albedo)
    if normal:
        MEL.set_material_instance_texture_parameter_value(mi, 'NormalRoughness', normal)
    if emissive:
        try:
            MEL.set_material_instance_texture_parameter_value(mi, 'Subsurface', emissive)
        except Exception:
            pass
    # Slightly lift response read in harsh sun without breaking recipe ceiling
    MEL.set_material_instance_scalar_parameter_value(mi, 'MelodiaWindResponse', 0.5)
    MEL.update_material_instance(mi)
    EAL.save_asset(path)
    tex = {}
    for e in (mi.get_editor_property('texture_parameter_values') or []):
        n = str(e.get_editor_property('parameter_info').get_editor_property('name'))
        t = e.get_editor_property('parameter_value')
        tex[n] = t.get_path_name() if t else None
    changed.append({'path': path, 'textures': tex})

# Soften UDS contrast a bit for lookdev (sun was harsh at 8)
svc = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
uds = next((a for a in svc.get_all_level_actors() if a.get_actor_label() == 'Ultra_Dynamic_Sky2'), None)
uds_after = {}
if uds:
    uds.set_editor_property('Sun Light Intensity', 6.5)
    uds.set_editor_property('Overall Intensity', 1.2)
    uds.set_editor_property('Cloud Coverage', 1.5)
    for p in ('Time of Day', 'Sun Light Intensity', 'Overall Intensity', 'Cloud Coverage'):
        uds_after[p] = uds.get_editor_property(p)

# Recapture key shots
import sys
sys.path.insert(0, r'C:/EnvironmentPortfolio/BS_GodFile/Content/Python')
import world_compiler_ue as wc
from pathlib import Path as P
b = wc._load_bundle(P(r'C:/EnvironmentPortfolio/BS_GodFile/Saved/WorldCompiler/morning_rainbow_bloom_3900'))
wc.step_lookdev_cameras(b)
cap = wc.step_lookdev_capture(b)
# restore walk/fx
for a in svc.get_all_level_actors():
    label = a.get_actor_label() or ''
    if label.startswith('WC_EscherWalk_') or label in ('FX_Morning_Mist', 'FX_Morning_Bed_PollenSparkle'):
        a.set_is_temporarily_hidden_in_editor(False)
        a.set_actor_hidden_in_game(False)
    if label in ('HoudiniEngine_RainbowBloom_3900', 'Houdini_RainbowBloom_3900'):
        a.set_is_temporarily_hidden_in_editor(True)
        a.set_actor_hidden_in_game(True)
unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()

report = {
  'generated_at': datetime.now(timezone.utc).isoformat(),
  'texture_fix': changed,
  'uds': uds_after,
  'shots': cap.get('shots'),
}
out = Path(unreal.Paths.project_dir()) / 'Saved' / 'Audit' / 'rainbow_lookdev_texture_fix_2026-09-20.json'
out.write_text(json.dumps(report, indent=2), encoding='utf-8')
print('FIXED', json.dumps({'bands': len(changed), 'sample_tex': changed[0]['textures'] if changed else None, 'uds': uds_after, 'shots': [(s['name'], s['bytes']) for s in (cap.get('shots') or [])]}, default=str))
