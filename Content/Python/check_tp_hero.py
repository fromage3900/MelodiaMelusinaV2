import unreal

# Check TP_Hero profile details
eal = unreal.EditorAssetLibrary
profile = eal.load_asset("/Game/EnvSandbox/Materials/ToonProfiles/TP_Hero.TP_Hero")
if profile:
    print(f"TP_Hero found: {profile.get_name()}")
    # Try to get ramp keys
    try:
        diffuse_keys = profile.get_editor_property("DiffuseRampKeys")
        print(f"Diffuse ramp keys: {diffuse_keys}")
    except:
        print("Could not get DiffuseRampKeys")
    try:
        specular_keys = profile.get_editor_property("SpecularRampKeys")
        print(f"Specular ramp keys: {specular_keys}")
    except:
        print("Could not get SpecularRampKeys")
    try:
        indirect_diffuse = profile.get_editor_property("IndirectDiffuseIntensity")
        print(f"IndirectDiffuseIntensity: {indirect_diffuse}")
    except:
        print("Could not get IndirectDiffuseIntensity")
    try:
        indirect_specular = profile.get_editor_property("IndirectSpecularIntensity")
        print(f"IndirectSpecularIntensity: {indirect_specular}")
    except:
        print("Could not get IndirectSpecularIntensity")
else:
    print("TP_Hero not found")