import unreal

print("--- NPC Interaction Diagnosis v2 ---")
ar = unreal.AssetRegistryHelpers.get_asset_registry()
eal = unreal.EditorAssetLibrary

# 1. Find all interaction-related assets
print("\n--- Interaction Components & Blueprints ---")
for prefix, label in [
    ("/Game/MelodiaIntegration", "MelodiaIntegration"),
    ("/Game/TurnBasedJRPGTemplate", "JRPG Template"),
]:
    for a in (ar.get_assets_by_path(prefix, recursive=True) or []):
        name = str(a.package_name)
        if "Interaction" in name or "NPC" in name or "PlayerController" in name or "smoke" in name.lower():
            print(f"  [{label}] {name} ({a.asset_class_path.asset_name})")

# 2. Input mapping contexts
print("\n--- Input Mapping Contexts ---")
for prefix in ["/Game/Melodia", "/Game/MelodiaIntegration"]:
    for a in (ar.get_assets_by_path(prefix, recursive=True) or []):
        name = str(a.package_name)
        cls = str(a.asset_class_path.asset_name)
        if "Input" in name or "IMC" in name or cls == "InputMappingContext":
            print(f"  {name} ({cls})")

# 3. Check Blueprint classes that derive from PlayerController
print("\n--- PlayerController Children ---")
for prefix in ["/Game/Melodia", "/Game/MelodiaIntegration", "/Game/TurnBasedJRPGTemplate", "/Game/Experiments"]:
    for a in (ar.get_assets_by_path(prefix, recursive=True) or []):
        name = str(a.package_name)
        cls = str(a.asset_class_path.asset_name)
        if "PlayerController" in name or "MelodiaSmoke" in name:
            print(f"  {name} ({cls})")

# 4. Check Config for input
print("\n--- Config: DefaultInput.ini interaction settings ---")
try:
    config_class = unreal.find_class("InputSettings")
    if config_class:
        print("  InputSettings class found")
except:
    print("  No InputSettings accessible")

# 5. Check MelodiaJRPGGameMode for default pawn/controller
print("\n--- GameMode Default Classes ---")
for gm_path in [
    "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode",
    "/Game/TurnBasedJRPGTemplate/Blueprints/BP_JRPGPlayerController"
]:
    obj = eal.load_asset(gm_path)
    if obj:
        cls = obj.get_class()
        print(f"  {gm_path}: LOADED ({cls.get_name()})")
        # Try to get default pawn class and other game mode properties
        for prop in ["DefaultPawnClass", "PlayerControllerClass", "HUDClass"]:
            try:
                val = obj.get_editor_property(prop)
                if val:
                    print(f"    {prop}: {val.get_name() if hasattr(val, 'get_name') else val}")
                else:
                    print(f"    {prop}: None")
            except:
                print(f"    {prop}: NOT ACCESSIBLE")
    else:
        print(f"  {gm_path}: NOT FOUND")

# 6. Check if the player pawn in ZenForest has interaction component
print("\n--- Character Pawns ---")
for prefix in ["/Game/MelodiaIntegration", "/Game/Experiments"]:
    for a in (ar.get_assets_by_path(prefix, recursive=True) or []):
        name = str(a.package_name)
        cls = str(a.asset_class_path.asset_name)
        if "Character" in name or "Pawn" in name or "Smoke" in name:
            print(f"  {name} ({cls})")

print("\nDONE")