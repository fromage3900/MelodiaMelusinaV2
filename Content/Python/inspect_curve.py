import unreal

# Load the TP_Melusina profile
tp_path = "/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina.TP_Melusina"
tp = unreal.EditorAssetLibrary.load_asset(tp_path)
if not tp:
    print("FAILED: Could not load TP_Melusina")
    quit()

print(f"Loaded: {tp.get_path_name()}")

settings = tp.get_editor_property("Settings")

# Set scalar properties on Settings
settings.set_editor_property("DiffuseIndirectScale", 0.3)
settings.set_editor_property("SpecularIndirectScale", 0.3)
settings.set_editor_property("ShadowExtinctionCoefficient", 0.3)

# Check what methods are available on the curve
dr = settings.get_editor_property("DiffuseRamp")
print(f"DiffuseRamp type: {type(dr)}")
print(f"DiffuseRamp dir: {[m for m in dir(dr) if not m.startswith('_')]}")

# Try to find the correct method to add keys
# Maybe it's update_or_add_key or set_key
for attr in dir(dr):
    if 'key' in attr.lower() or 'add' in attr.lower():
        print(f"  Found: {attr}")

# Save current state
unreal.EditorAssetLibrary.save_asset("/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina")
print("Done inspecting")