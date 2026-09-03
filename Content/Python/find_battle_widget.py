import unreal

ar = unreal.AssetRegistryHelpers.get_asset_registry()

# Find all battle UI blueprints
assets = ar.get_assets_by_path("/Game/TurnBasedJRPGTemplate/Blueprints/UI", recursive=True) or []
print("=== Battle UI Blueprints ===")
for a in assets:
    if "Battle" in str(a.package_name) or "Command" in str(a.package_name):
        print(f"{a.package_name} | {a.asset_class_path.asset_name}")

# Also check the _ThirdParty copy
assets2 = ar.get_assets_by_path("/Game/_ThirdParty/TurnBasedJRPGTemplate/Blueprints/UI", recursive=True) or []
print("\n=== _ThirdParty Battle UI Blueprints ===")
for a in assets2:
    if "Battle" in str(a.package_name) or "Command" in str(a.package_name):
        print(f"{a.package_name} | {a.asset_class_path.asset_name}")

# Find what's referenced in Dreamstate or ZenForest
for map_path in ["/Game/MelodiaIntegration/Maps/L_Melodia_Dreamstate", "/Game/ZenForestTest"]:
    data = ar.get_asset_by_object_path(unreal.SoftObjectPath(map_path))
    if data.is_valid():
        print(f"\n=== Map: {map_path} ===")
        deps = []
        ar.get_referencers(data, deps, [unreal.AssetRegistryDependencyOptions(
            include_soft_package_references=True,
            include_hard_package_references=True
        )])
        for d in deps:
            if "Battle" in str(d.package_name) or "UI" in str(d.package_name):
                print(f"  ref: {d.package_name}")
    else:
        print(f"\n=== Map not found: {map_path} ===")