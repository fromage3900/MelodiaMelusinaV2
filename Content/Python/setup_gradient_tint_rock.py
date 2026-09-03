"""Implement Gradient Tint Rock (Genshin-style altitude coloring) on landscape master.
Uses existing MF_ColorRamp3 + MF_LandscapeDistanceBands."""
import unreal
MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary

LANDSCAPE_MASTER = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Landscape_HeightBlend"
COLOR_RAMP3 = "/Game/EnvSandbox/Materials/Functions/MF_ColorRamp3"
DISTANCE_BANDS = "/Game/EnvSandbox/Materials/Functions/MF_LandscapeDistanceBands"

mat = unreal.load_asset(LANDSCAPE_MASTER)
if not mat:
    raise RuntimeError(f"Missing landscape master at {LANDSCAPE_MASTER}")

# Check that MF_ColorRamp3 exists
if not EAL.does_asset_exist(COLOR_RAMP3):
    raise RuntimeError(f"MF_ColorRamp3 not found at {COLOR_RAMP3}")

print("=== Gradient Tint Rock Implementation ===")

# Check existing parameters to avoid duplicates
existing_params = set()
for expr in MEL.get_material_expressions(mat) or []:
    try:
        existing_params.add(str(expr.get_editor_property("parameter_name")))
    except:
        pass

# Add gradient tint rock parameters
new_params = []
y_pos = 4200  # Below existing params in the graph

# Low color (tan/earth at base)
if "GTR_LowColor" not in existing_params:
    low_color = MEL.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -1400, y_pos)
    low_color.set_editor_property("parameter_name", "GTR_LowColor")
    low_color.set_editor_property("default_value", unreal.LinearColor(0.55, 0.42, 0.30, 1.0))
    low_color.set_editor_property("group", "Gradient Tint Rock")
    new_params.append("GTR_LowColor")
    y_pos += 60

# Mid color (green for vegetation band)
if "GTR_MidColor" not in existing_params:
    mid_color = MEL.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -1400, y_pos)
    mid_color.set_editor_property("parameter_name", "GTR_MidColor")
    mid_color.set_editor_property("default_value", unreal.LinearColor(0.45, 0.55, 0.35, 1.0))
    mid_color.set_editor_property("group", "Gradient Tint Rock")
    new_params.append("GTR_MidColor")
    y_pos += 60

# High color (cyan/dark at peaks)
if "GTR_HighColor" not in existing_params:
    high_color = MEL.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -1400, y_pos)
    high_color.set_editor_property("parameter_name", "GTR_HighColor")
    high_color.set_editor_property("default_value", unreal.LinearColor(0.50, 0.55, 0.60, 1.0))
    high_color.set_editor_property("group", "Gradient Tint Rock")
    new_params.append("GTR_HighColor")
    y_pos += 60

# Altitude bands (low→mid, mid→high transitions)
if "GTR_LowAltitude" not in existing_params:
    low_alt = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -1400, y_pos)
    low_alt.set_editor_property("parameter_name", "GTR_LowAltitude")
    low_alt.set_editor_property("default_value", 50.0)
    low_alt.set_editor_property("slider_min", 0.0)
    low_alt.set_editor_property("slider_max", 500.0)
    low_alt.set_editor_property("group", "Gradient Tint Rock")
    new_params.append("GTR_LowAltitude")
    y_pos += 60

if "GTR_HighAltitude" not in existing_params:
    high_alt = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -1400, y_pos)
    high_alt.set_editor_property("parameter_name", "GTR_HighAltitude")
    high_alt.set_editor_property("default_value", 300.0)
    high_alt.set_editor_property("slider_min", 0.0)
    high_alt.set_editor_property("slider_max", 1000.0)
    high_alt.set_editor_property("group", "Gradient Tint Rock")
    new_params.append("GTR_HighAltitude")
    y_pos += 60

if "GTR_Strength" not in existing_params:
    strength = MEL.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -1400, y_pos)
    strength.set_editor_property("parameter_name", "GTR_Strength")
    strength.set_editor_property("default_value", 0.0)
    strength.set_editor_property("slider_min", 0.0)
    strength.set_editor_property("slider_max", 1.0)
    strength.set_editor_property("group", "Gradient Tint Rock")
    new_params.append("GTR_Strength")
    y_pos += 60

print(f"  Created {len(new_params)} new parameters: {new_params}")
print(f"  Note: Manual wiring of MF_ColorRamp3 and blending into rock_color required in-editor")
print(f"  MF_ColorRamp3 path: {COLOR_RAMP3}")
print(f"  Wire: WorldPosition.Z -> normalize by LowAltitude/HighAltitude -> MF_ColorRamp3 alpha -> lerp(rock_color, gradient, GTR_Strength)")

# Save
EAL.save_asset(LANDSCAPE_MASTER)
print("[OK] Landscape master saved with GTR parameters")
