import unreal

print("--- Dirty Melodia Packages ---")
eal = unreal.EditorAssetLibrary
ar = unreal.AssetRegistryHelpers.get_asset_registry()
dirty = []
for prefix in ["/Game/Melodia", "/Game/MelodiaIntegration", "/Game/Experiments/MelodiaJRPG", "/Game/ZenForestTest"]:
    assets = ar.get_assets_by_path(prefix, recursive=True) or []
    for a in assets:
        try:
            if eal.is_asset_dirty(str(a.package_name)):
                dirty.append(str(a.package_name))
        except:
            pass
if dirty:
    for d in dirty[:30]:
        print("  DIRTY:", d)
    print(f"  Total dirty: {len(dirty)}")
else:
    print("  No dirty Melodia packages")

print("\n--- Missing Asset References ---")
refs = {
    "MI_ToonBush": "/Game/EnvSandbox/Materials/Instances/Foliage/MI_ToonBush",
    "MI_Toon_GenericFlowerTall": "/Game/EnvSandbox/Materials/Instances/Foliage/MI_Toon_GenericFlowerTall",
    "SM_Rock": "/Game/AdvWorldInteraction/StarterContent/Props/SM_Rock",
    "M_Door_Text_Mat_003": "/Game/_PROJECT/houseassets/M_Door_Text_Mat_003",
    "M_Door_Text_Mat_004": "/Game/_PROJECT/houseassets/M_Door_Text_Mat_004",
}
for name, path in refs.items():
    exists = eal.does_asset_exist(path)
    print(f"  {name}: {'EXISTS' if exists else 'MISSING'}")

print("\n--- Maps Status ---")
maps = [
    "/Game/Melodia/Levels/Menu/L_MelodiaMainMenu",
    "/Game/Melodia/Levels/Opening/L_MelusinaMorning",
    "/Game/Melodia/Levels/Dreamstate/L_Melodia_Dreamstate",
    "/Game/ZenForestTest",
]
for m in maps:
    print(f"  {m}: {'EXISTS' if eal.does_asset_exist(m) else 'MISSING'}")

print("\n--- Battle UI Duplicates ---")
for bp_path in ["/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI", "/Game/_ThirdParty/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI"]:
    print(f"  {bp_path}: {'EXISTS' if eal.does_asset_exist(bp_path) else 'MISSING'}")

print("\n--- Menu Widget Status ---")
for w in ["/Game/Melodia/UI/WBP_MainMenu", "/Game/Melodia/UI/WBP_SaveLoad"]:
    asset = eal.load_asset(w)
    print(f"  {w}: {'LOADED' if asset else 'MISSING'}")

print("\nDONE")