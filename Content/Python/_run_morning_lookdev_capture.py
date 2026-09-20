
import unreal, json, sys
from pathlib import Path
sys.path.insert(0, r'C:/EnvironmentPortfolio/BS_GodFile/Content/Python')
import world_compiler_ue as wc

bundle = Path(r'C:/EnvironmentPortfolio/BS_GodFile/Saved/WorldCompiler/morning_rainbow_bloom_3900')
b = wc._load_bundle(bundle)

# gentle source-lane wind for lookdev
try:
    mpc = unreal.EditorAssetLibrary.load_asset('/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette')
    if mpc:
        unreal.MaterialEditingLibrary.set_material_parameter_collection_scalar(mpc, 'WindStrength', 0.35)
        unreal.MaterialEditingLibrary.set_material_parameter_collection_scalar(mpc, 'WindDirX', 1.0)
        unreal.MaterialEditingLibrary.set_material_parameter_collection_scalar(mpc, 'WindDirY', 0.15)
        print('WIND_MPC_OK')
except Exception as e:
    print('WIND_MPC_ERR', e)

cam = wc.step_lookdev_cameras(b)
print('CAMERAS', json.dumps(cam, default=str)[:2000])
cap = wc.step_lookdev_capture(b)
print('CAPTURE', json.dumps(cap, default=str)[:3000])

try:
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
    print('LEVEL_SAVED')
except Exception as e:
    try:
        unreal.EditorLevelLibrary.save_current_level()
        print('LEVEL_SAVED_ELL')
    except Exception as e2:
        print('SAVE_FAIL', e, e2)
