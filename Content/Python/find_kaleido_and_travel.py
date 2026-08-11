import unreal

print("=== FIND KALEIDO NAVE + TRAVEL CHAIN ===\n")

ar = unreal.AssetRegistryHelpers.get_asset_registry()
eal = unreal.EditorAssetLibrary

# 1. Find Kaleido Nave
print("--- Finding L_KaleidoNave ---")
for a in (ar.get_assets_by_path("/Game", recursive=True) or []):
    name = str(a.package_name)
    cls = str(a.asset_class_path.asset_name)
    if "kaleido" in name.lower() or "Kaleido" in name:
        print(f"  {name} ({cls})")

# 2. Find all world/level assets
print("\n--- All Level Maps ---")
for prefix in ["/Game/Melodia/Levels", "/Game/EnvSandbox/Environments", "/Game/ZenForestTest"]:
    for a in (ar.get_assets_by_path(prefix, recursive=True) or []):
        cls = str(a.asset_class_path.asset_name)
        if cls == "World":
            print(f"  {a.package_name} (World)")

# 3. Check Morning to Dreamstate travel
print("\n--- Morning → Dreamstate Travel ---")
# Find any blueprint that references both maps
morning_bp_path = "/Game/MelodiaIntegration/Blueprints/Opening/BP_MelodiaSirMelodiousMorningIntro"
bp = eal.load_asset(morning_bp_path)
if bp:
    print(f"  BP_MelodiaSirMelodiousMorningIntro: LOADED ({bp.get_class().get_name()})")
    # Check if it has a 'TravelToMap' or 'OpenLevel' function reference
    for prop_name in dir(bp):
        if 'travel' in prop_name.lower() or 'map' in prop_name.lower() or 'level' in prop_name.lower():
            print(f"    Property: {prop_name}")
else:
    print(f"  BP_MelodiaSirMelodiousMorningIntro: NOT FOUND")

# 4. Check DefaultGame.ini for MapsToCook
print("\n--- MapsToCook Config ---")
maps_to_cook = [
    "/Game/Melodia/Levels/Menu/L_MelodiaMainMenu",
    "/Game/Melodia/Levels/Opening/L_MelusinaMorning", 
    "/Game/Melodia/Levels/Opening/L_Melodia_Dreamstate",
    "/Game/ZenForestTest",
]
for m in maps_to_cook:
    exists = eal.does_asset_exist(m)
    print(f"  {m}: {'EXISTS' if exists else 'MISSING'}")

# 5. Check Quill narrative for travel references
print("\n--- Quill Narrative Travel ---")
morning_qsc = eal.load_asset("/Game/MelodiaIntegration/Narrative/MelodiaMorningIntro")
if morning_qsc:
    print(f"  MelodiaMorningIntro: LOADED")
    # Try to read statements
    try:
        statements = morning_qsc.get_editor_property("Statements")
        if statements:
            for i, s in enumerate(statements):
                txt = str(s)
                if 'travel' in txt.lower() or 'dream' in txt.lower() or 'kaleido' in txt.lower():
                    print(f"    Statement {i}: {txt[:120]}")
    except Exception as e:
        print(f"    Could not read statements: {e}")
else:
    print(f"  MelodiaMorningIntro: NOT FOUND")

print("\nDONE")