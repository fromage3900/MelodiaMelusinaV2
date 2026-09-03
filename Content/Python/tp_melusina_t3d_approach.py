import unreal

# For the TP_Melusina toon profile, the most reliable approach is to use T3D injection
# Let me construct the full T3D text with the warm-violet ramp and import it

# First, let's check if we can import T3D text via the editor
tp_path = "/Game/EnvSandbox/Materials/ToonProfiles/TP_Melusina.TP_Melusina"
tp = unreal.EditorAssetLibrary.load_asset(tp_path)
settings = tp.get_editor_property("Settings")

# Set the scalar properties which we know work
settings.set_editor_property("DiffuseIndirectScale", 0.3)
settings.set_editor_property("SpecularIndirectScale", 0.3)
settings.set_editor_property("ShadowExtinctionCoefficient", 0.3)

# For the ramp curves, we'll use the import_text method on the curve object
# The curve's export_text format shows the structure
# Let me try to set the curve via import_text with our custom values

dr = settings.get_editor_property("DiffuseRamp")

# The export_text format for the curve:
# (ColorCurves[0]=(Keys=((),(Time=0.250000),(Time=0.260000,Value=0.250000),(Time=0.500000,Value=0.250000),(Time=0.510000,Value=0.500000),(Time=0.750000,Value=0.500000),(Time=0.760000,Value=0.750000),(Time=0.990000,Value=0.750000),(Time=1.000000,Value=1.000000)),DefaultValue=340282346638528859811704183484516925440.000000,PreInfinityExtrap=RCCE_Constant,PostInfinityExtrap=RCCE_Constant),ColorCurves[1]=...

# Let me construct the warm-violet ramp T3D text and try to import it
# For the warm-violet ramp #352D40:
# Shadow (NdotL=0.0): LinearColor(0.0340, 0.0227, 0.0476, 1.0)
# Mid (NdotL=0.3): LinearColor(1.0, 1.0, 1.0, 1.0) 
# Lit (NdotL=1.0): LinearColor(1.08, 1.04, 0.98, 1.0)

# We need to create keys that create a 3-stop ramp:
# Time 0.0: shadow color (violet)
# Time 0.3: mid color (white)
# Time 1.0: warm bias

# The curve uses step functions with sharp transitions
# Current keys at 0.25, 0.26, 0.5, 0.51, 0.75, 0.76, 0.99, 1.0 create 4 steps
# For 3 steps: 0.0-0.3 (shadow), 0.3-1.0 (mid to warm)

# Let me try to set the curve via import_text with modified keys
# For R channel (ColorCurves[0]): shadow=0.0340, mid=1.0, warm=1.08
# For G channel (ColorCurves[1]): shadow=0.0227, mid=1.0, warm=1.04
# For B channel (ColorCurves[2]): shadow=0.0476, mid=1.0, warm=0.98
# A channel (ColorCurves[3]): all 1.0

# Construct the import text for the DiffuseRamp
# This is complex - let me try a simpler approach: use the Monolith MCP to run a Python script
# that sets the curve keys using the correct internal API

print("Script prepared - use the Monolith MCP run_python to set curve keys via internal API")
print("See create_tp_melusina_final.py for the complete script")