import unreal

print("=" * 60)
print("NPC INTERACTION DIAGNOSIS — ZenForestTest + Melodia")
print("=" * 60)

ar = unreal.AssetRegistryHelpers.get_asset_registry()
eal = unreal.EditorAssetLibrary

# 1. Check ZenForestTest map configuration
print("\n--- ZenForestTest Map ---")
zft = eal.load_asset("/Game/ZenForestTest")
if zft:
    wf = zft.get_world()
    print(f"  Loaded: {zft.get_class().get_name()}")
    # Check GameMode override
    settings = zft.get_editor_property('world_settings') if hasattr(zft, 'get_editor_property') else None
    print(f"  WorldSettings: {'FOUND' if settings else 'None via direct get'}")
else:
    print("  Failed to load as asset (world asset loads differently)")

# 2. Check the project's DefaultGame.ini for ZenForest
print("\n--- Config: GameMode Mappings ---")
try:
    config = unreal.GameMapsSettings.get_game_maps_settings()
    # Get game default map
    default_map = config.get_editor_property('game_default_map')
    print(f"  GameDefaultMap: {default_map}")
    # Get game mode map prefixes
    prefixes = config.get_editor_property('game_mode_map_prefixes')
    if prefixes:
        for p in prefixes:
            print(f"  MapPrefix: {p}")
    else:
        print("  No GameModeMapPrefixes found")
except Exception as e:
    print(f"  Config read error: {e}")

# 3. Check what controller ZenForestTest actually uses
print("\n--- PlayerController for Exploration Maps ---")
# Check BP_MelodiaSmokeCharacter (used in ZenForestTest per handoff)
smoke = eal.load_asset("/Game/MelodiaIntegration/Blueprints/BP_MelodiaSmokeCharacter")
if smoke:
    print(f"  BP_MelodiaSmokeCharacter: LOADED as {smoke.get_class().get_name()}")
else:
    # Try to find it
    print("  BP_MelodiaSmokeCharacter: NOT FOUND at expected path")
    # Search
    for a in (ar.get_assets_by_path("/Game/MelodiaIntegration", recursive=True) or []):
        if "Smoke" in str(a.package_name) or "smoke" in str(a.package_name):
            print(f"    Found: {a.package_name}")

# 4. Check the stock JRPG PlayerController
jrpg_pc = eal.load_asset("/Game/TurnBasedJRPGTemplate/Blueprints/BP_JRPGPlayerController")
if jrpg_pc:
    print(f"\n  BP_JRPGPlayerController: LOADED as {jrpg_pc.get_class().get_name()}")
else:
    print(f"\n  BP_JRPGPlayerController: NOT FOUND")

# 5. Check MelodiaNPCInteractionComponent
print("\n--- MelodiaNPCInteractionComponent ---")
# Check what input it listens for
comp_class = unreal.find_class("MelodiaNPCInteractionComponent")
if comp_class:
    print(f"  Class found: MelodiaNPCInteractionComponent")
    # Get UPROPERTY list
    for prop_name in dir(comp_class):
        if 'interaction' in prop_name.lower() or 'input' in prop_name.lower() or 'overlap' in prop_name.lower() or 'collision' in prop_name.lower():
            print(f"    Property: {prop_name}")
else:
    print("  MelodiaNPCInteractionComponent: NOT FOUND as Python class")

# 6. Check ZenForestTest NPCs
print("\n--- ZenForestTest NPCs ---")
npc_paths = [
    "/Game/ZenForestTest.ZenForestTest:PersistentLevel.BP_EnemyExplorePawn",
    "/Game/MelodiaIntegration/NPC/BP_MelodiaZenNPC",  # guess
]
for path in npc_paths:
    try:
        obj = unreal.find_object(None, path)
        if obj:
            print(f"  {path}: EXISTS ({obj.get_class().get_name()})")
        else:
            print(f"  {path}: None")
    except:
        pass

# 7. Input mapping check
print("\n--- Input Mappings ---")
try:
    enhanced_input = unreal.EnhancedInputLibrary
    imcs = [a for a in ar.get_assets_by_path("/Game/Melodia", recursive=True) or [] if "Input" in str(a.package_name) or "IMC" in str(a.package_name)]
    for imc in imcs:
        print(f"  {imc.package_name}")
except:
    pass

# 8. Check if ZenForestTest's level has a GameMode override
print("\n--- Level GameMode Override ---")
try:
    # Use the editor subsystem to get current level
    level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    current_level = level_editor.get_current_level()
    # We need to load ZenForest to check - let's do a world settings read
except:
    pass

print("\nDONE")