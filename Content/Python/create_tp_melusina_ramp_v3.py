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

# Warm violet ramp #352D40 in linear color space
shadow_color = unreal.LinearColor(0.0340, 0.0227, 0.0476, 1.0)
mid_color = unreal.LinearColor(1.0, 1.0, 1.0, 1.0)
warm_bias = unreal.LinearColor(1.08, 1.04, 0.98, 1.0)

# Set Diffuse Ramp - clear existing keys and add new ones
dr = settings.get_editor_property("DiffuseRamp")
# Clear by creating new curve
new_dr = unreal.RuntimeCurveLinearColor()
new_dr.add_key(0.0, unreal.LinearColor(0.0340, 0.0227, 0.0476, 1.0))
new_dr.add_key(0.3, unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
new_dr.add_key(1.0, unreal.LinearColor(1.08, 1.04, 0.98, 1.0))
settings.set_editor_property("DiffuseRamp", new_dr)

# Specular Ramp: 1 narrow key at 0.9
sr = unreal.RuntimeCurveLinearColor()
sr.add_key(0.9, unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
settings.set_editor_property("SpecularRamp", sr)

# Shadow Hatching
hatch_path = "/Game/EnvSandbox/Materials/ToonProfiles/T_HatchPattern"
hatch = unreal.EditorAssetLibrary.load_asset(hatch_path)
if hatch:
    settings.set_editor_property("ShadowHatchingPattern", hatch)
    settings.set_editor_property("ShadowExtinctionCoefficient", 0.3)
    print(f"Set hatching pattern: {hatch_path}")
else:
    print(f"Hatching pattern not found at {hatch_path} - skipping")

tp.set_editor_property("Settings", settings)

# Save
unreal.EditorAssetLibrary.save_asset("/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina")
print("SUCCESS: TP_Melusina configured and saved")