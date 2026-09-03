import unreal

print("Sir Skybound Refrain:", unreal.EditorAssetLibrary.load_asset("/Game/MelodiaIntegration/Party/Skills/BP_SirSkyboundRefrain") is not None)
print("BP_Resonance:", unreal.EditorAssetLibrary.load_asset("/Game/MelodiaIntegration/Party/Skills/Buffs/BP_Resonance") is not None)
print("Melusina Petal Cadence:", unreal.EditorAssetLibrary.load_asset("/Game/Experiments/MelodiaJRPG/Skills/BP_MelusinaPetalCadence") is not None)

# Check what BP_BattleUI the stock GameMode references
for gm_path in ["/Game/TurnBasedJRPGTemplate/Blueprints/BP_JRPGPlayerController", "/Game/MelodiaIntegration/Blueprints/BP_MelodiaJRPGGameMode"]:
    gm = unreal.EditorAssetLibrary.load_asset(gm_path)
    if gm:
        print(f"\n{gm_path}: loaded as {gm.get_class().get_name()}")
        # Try to find BattleUI reference via property
        props = gm.get_class()
        for prop_name in dir(props):
            if 'battle' in str(prop_name).lower() or 'ui' in str(prop_name).lower():
                print(f"  prop: {prop_name}")
    else:
        print(f"\n{gm_path}: NOT FOUND")

print("\n=== DONE ===")