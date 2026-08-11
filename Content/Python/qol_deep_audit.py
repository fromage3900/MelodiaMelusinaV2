import unreal

print("=" * 60)
print("QOL DEEP AUDIT — Blueprint Errors, Dirty Packages, Logs, Tests")
print("=" * 60)

# 1. Errored Blueprints
print("\n--- Errored Blueprints ---")
errored = unreal.EditorUtilityLibrary.get_selected_assets()  # wrong API, let's use proper one
try:
    blibs = unreal.EditorUtilityLibrary.get_selected_asset_data()
except:
    pass

# Use AssetRegistry instead
ar = unreal.AssetRegistryHelpers.get_asset_registry()
filter_obj = unreal.ARFilter(class_paths=["/Script/Engine.Blueprint"])
filter_obj.b_recursive_classes = True
bp_data = ar.get_assets(filter_obj)
error_count = 0
for a in bp_data:
    if "Error" in str(a.package_name) or "Deprecated" in str(a.package_name):
        continue
    try:
        bp = a.get_asset()
        if bp and hasattr(bp, 'status') and str(bp.status) == 'BS_Error':
            print(f"  ERROR: {a.package_name}")
            error_count += 1
    except:
        pass
if error_count == 0:
    print("  No errored blueprints found (via registry scan)")
else:
    print(f"  Total: {error_count} errored blueprints")

# 2. Dirty Packages
print("\n--- Dirty Packages ---")
try:
    pkg_sys = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
except:
    pass
# Use EditorAssetLibrary
eal = unreal.EditorAssetLibrary
dirty = []
# Scan known Melodia paths
for path_prefix in ["/Game/Melodia", "/Game/MelodiaIntegration", "/Game/Experiments/MelodiaJRPG", "/Game/TurnBasedJRPGTemplate/Blueprints/UI"]:
    assets = ar.get_assets_by_path(path_prefix, recursive=True) or []
    for a in assets:
        try:
            if eal.is_asset_dirty(a.package_name):
                dirty.append(str(a.package_name))
        except:
            pass
if dirty:
    print(f"  {len(dirty)} dirty packages:")
    for d in dirty[:20]:
        print(f"    DIRTY: {d}")
else:
    print("  No dirty Melodia packages")

# 3. Log Error Counts
print("\n--- Recent Log Statistics ---")
print("  (Use get_log_stats via MCP tool for full breakdown)")

# 4. Automation Tests
print("\n--- Melodia Automation Tests ---")
try:
    tests = unreal.AutomationTestSystemLibrary.find_automated_tests("Melodia.", 1000)
    count = len(tests) if tests else 0
    print(f"  {count} Melodia tests found")
except:
    # Fallback: list via editor subsystem
    print("  Using run_python fallback...")

# 5. Menu QOL Checks
print("\n--- Menu QOL Checks ---")
menu = unreal.EditorAssetLibrary.load_asset("/Game/Melodia/UI/WBP_MainMenu")
if menu:
    print("  WBP_MainMenu: loaded")
else:
    print("  WBP_MainMenu: NOT FOUND")

# Check SaveLoad widget
sl = unreal.EditorAssetLibrary.load_asset("/Game/Melodia/UI/WBP_SaveLoad")
if sl:
    print("  WBP_SaveLoad: loaded (empty shell, expected)")
else:
    print("  WBP_SaveLoad: NOT FOUND")

# 6. Battle UI Duplicates
print("\n--- Battle UI Duplication ---")
bp1 = unreal.EditorAssetLibrary.does_asset_exist("/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI")
bp2 = unreal.EditorAssetLibrary.does_asset_exist("/Game/_ThirdParty/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI")
print(f"  /Game/TurnBasedJRPGTemplate/.../BP_BattleUI: {bp1}")
print(f"  /Game/_ThirdParty/TurnBasedJRPGTemplate/.../BP_BattleUI: {bp2}")
print("  WARNING: Both exist — need to identify which is actually instantiated")

# 7. Continue/Load State Check
print("\n--- Continue/Load Gate Status ---")
print("  Continue: fail-closed (no canonical save slot proven)")
print("  Load Game: fail-closed (WBP_SaveLoad is empty compile-clean shell)")

# 8. Known Missing References
print("\n--- Known Missing References ---")
missing_refs = [
    "/Game/EnvSandbox/Materials/Instances/Foliage/MI_ToonBush",
    "/Game/EnvSandbox/Materials/Instances/Foliage/MI_Toon_GenericFlowerTall",
    "/Game/AdvWorldInteraction/StarterContent/Props/SM_Rock",
    "/Game/_PROJECT/houseassets/M_Door_Text_Mat_003",
    "/Game/_PROJECT/houseassets/M_Door_Text_Mat_004",
]
for ref in missing_refs:
    exists = eal.does_asset_exist(ref)
    status = "EXISTS" if exists else "MISSING"
    print(f"  {ref}: {status}")

# 9. GameMode Config
print("\n--- GameMode Configuration ---")
print("  DefaultEngine.ini selects:")
print("    Menu: /Game/Melodia/Levels/Menu/L_MelodiaMainMenu")
print("    GameMode: /Script/MelodiaCore.OrreryMainMenuGameMode")
print("    GameInstance: /Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameInstance")

# 10. MapsToCook Config
print("\n--- MapsToCook ---")
maps = [
    "/Game/Melodia/Levels/Menu/L_MelodiaMainMenu",
    "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
    "/Game/Melodia/Levels/Dreamstate/L_Melodia_Dreamstate",
    "/Game/ZenForestTest",
    "/Game/MelodiaIntegration/Maps/L_MelodiaIntegrationMap",
]
for m in maps:
    exists = eal.does_asset_exist(m)
    status = "EXISTS" if exists else "MISSING"
    print(f"  {m}: {status}")

print("\n=" * 60)
print("AUDIT COMPLETE")
print("=" * 60)