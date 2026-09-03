import unreal

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

# Test 1: Foundation state diagnostic
try:
    unreal.MelodiaPresentationDiagnosticsLibrary.log_gameplay_foundation_state(world)
    print("FOUNDATION_STATE: logged to OutputLog - UHT rebuild SUCCESS")
except AttributeError:
    print("FOUNDATION_STATE: NOT AVAILABLE - UHT not refreshed yet")
except Exception as e:
    print(f"FOUNDATION_STATE: error - {e}")

# Test 2: Verify MapsToCook
import os
ini_path = "C:/EnvironmentPortfolio/BS_GodFile/Config/DefaultGame.ini"
with open(ini_path, "r") as f:
    content = f.read()
    if "L_KaleidoNave" in content:
        print("MapsToCook: KaleidoNave FOUND in DefaultGame.ini")
    else:
        print("MapsToCook: KaleidoNave NOT in DefaultGame.ini - NEEDS FIX")
    if "L_Melodia_Dreamstate" in content:
        print("MapsToCook: Dreamstate STILL PRESENT - may need cleanup")

# Test 3: Asset existence
eal = unreal.EditorAssetLibrary
checks = {
    "BP_MelusinaPetalCadence": "/Game/Experiments/MelodiaJRPG/Skills/BP_MelusinaPetalCadence",
    "BP_SirSkyboundRefrain": "/Game/MelodiaIntegration/Party/Skills/BP_SirSkyboundRefrain",
    "BP_Resonance": "/Game/MelodiaIntegration/Party/Skills/Buffs/BP_Resonance",
    "MIDI_128BPM": "/Game/MelodiaIntegration/MIDI/128BPMarpeggiomelody",
    "WBP_MainMenu": "/Game/Melodia/UI/WBP_MainMenu",
    "WBP_Settings": "/Game/Melodia/UI/WBP_Settings",
    "WBP_Battle_Rhythm": "/Game/Melodia/UI/WBP_Battle_Rhythm",
    "L_KaleidoNave": "/Game/EnvSandbox/Environments/L_KaleidoNave",
    "L_MelusinaMorning": "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
    "ZenForestTest": "/Game/ZenForestTest",
}
print("\nAsset Verification:")
for label, path in checks.items():
    exists = eal.does_asset_exist(path)
    print(f"  {label}: {'OK' if exists else 'MISSING'}")

print("\nDONE - Rebuild verification complete")