import unreal

print("=== Finding active BattleUI widget in Dreamstate ===")
ar = unreal.AssetRegistryHelpers.get_asset_registry()

# Check which BP_BattleUI the GameMode or BP_InteractionBattle references
for path in [
    "/Game/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI",
    "/Game/_ThirdParty/TurnBasedJRPGTemplate/Blueprints/UI/BP_BattleUI"
]:
    data = ar.get_asset_by_object_path(unreal.SoftObjectPath(path))
    if data.is_valid():
        refs = []
        ar.get_referencers(data, refs, [unreal.AssetRegistryDependencyOptions(
            include_soft_package_references=True,
            include_hard_package_references=True
        )])
        print(f"\n{path}:")
        for r in refs:
            if "Melodia" in str(r.package_name) or "GameMode" in str(r.package_name) or "Battle" in str(r.package_name):
                print(f"  -> referenced by: {r.package_name}")

# Now find Skybound Refrain and check its current state
print("\n=== Skybound Refrain status ===")
skill = unreal.EditorAssetLibrary.load_asset("/Game/MelodiaIntegration/Party/Skills/BP_SirSkyboundRefrain")
if skill:
    print(f"BP_SirSkyboundRefrain loaded: {skill.get_class().get_name()}")
    # Check parent chain
    for_name = skill.get_class().get_name()
    print(f"  Class: {for_name}")
else:
    print("BP_SirSkyboundRefrain NOT FOUND")

# Check Resonance buff
print("\n=== Resonance buff status ===")
resonance = unreal.EditorAssetLibrary.load_asset("/Game/MelodiaIntegration/Party/Skills/Buffs/BP_Resonance")
if resonance:
    print(f"BP_Resonance loaded: {resonance.get_class().get_name()}")
else:
    print("BP_Resonance NOT FOUND")

# Check Petal Cadence
print("\n=== Petal Cadence status ===")
pc = unreal.EditorAssetLibrary.load_asset("/Game/Experiments/MelodiaJRPG/Skills/BP_MelusinaPetalCadence")
if pc:
    print(f"BP_MelusinaPetalCadence loaded: {pc.get_class().get_name()}")
else:
    print("BP_MelusinaPetalCadence NOT FOUND")