import unreal

# Check if TP_Melusina profile exists
eal = unreal.EditorAssetLibrary
exists = eal.does_asset_exist("/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina.TP_Melusina")
print(f"TP_Melusina exists: {exists}")

# List existing toon profiles
toon_profiles = unreal.EditorAssetLibrary.list_assets("/Game/EnvSandbox/Materials/ToonProfiles", recursive=True, include_folder=False)
print(f"Existing toon profiles: {toon_profiles}")