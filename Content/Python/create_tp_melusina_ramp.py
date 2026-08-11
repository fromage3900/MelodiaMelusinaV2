import unreal

# Load the TP_Melusina profile
tp_path = "/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina.TP_Melusina"
tp = unreal.EditorAssetLibrary.load_asset(tp_path)
if not tp:
    print("FAILED: Could not load TP_Melusina")
    quit()

print(f"Loaded: {tp.get_path_name()}")

# Set scalar properties
tp.set_editor_property("DiffuseIndirectScale", 0.3)
tp.set_editor_property("SpecularIndirectScale", 0.3)
tp.set_editor_property("ShadowExtinctionCoefficient", 0.3)

# Warm violet ramp #352D40 in linear color space
# sRGB 53, 45, 64 -> linear
shadow_color = unreal.LinearColor(0.0340, 0.0227, 0.0476, 1.0)  # #352D40 linear
mid_color = unreal.LinearColor(1.0, 1.0, 1.0, 1.0)  # base color
# Warm bias for lit: slightly warm
warm_bias = unreal.LinearColor(1.08, 1.04, 0.98, 1.0)

# Set Diffuse Ramp (3 keys: 0.0, 0.3, 1.0)
dr = tp.get_editor_property("DiffuseRamp")
dr.empty()
dr.add_key(0.0, shadow_color)   # shadow
dr.add_key(0.3, mid_color)      # mid
dr.add_key(1.0, warm_bias)      # lit warm bias

# Specular Ramp: 1 narrow key at 0.9
sr = tp.get_editor_property("SpecularRamp")
sr.empty()
sr.add_key(0.9, unreal.LinearColor(1.0, 1.0, 1.0, 1.0))

# Shadow Hatching - try to find T_HatchPattern
hatch_path = "/Game/EnvSandbox/Materials/ToonProfiles/T_HatchPattern"
hatch = unreal.EditorAssetLibrary.load_asset(hatch_path)
if hatch:
    tp.set_editor_property("ShadowHatchingPattern", hatch)
    tp.set_editor_property("ShadowingExtinction", 0.3)
    print(f"Set hatching pattern: {hatch_path}")
else:
    print(f"Hatching pattern not found at {hatch_path} - skipping")

# Save
unreal.EditorAssetLibrary.save_asset("/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina")
print("SUCCESS: TP_Melusina configured and saved")