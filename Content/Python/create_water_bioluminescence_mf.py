import unreal

# ============================================================
# MF_WaterBioluminescence_v7 Material Function Creation Script
# Run in Unreal Editor: -ExecutePythonScript=C:/EnvironmentPortfolio/BS_GodFile/Content/Python/create_water_bioluminescence_mf.py
# ============================================================

def create_water_bioluminescence_mf():
    """Create MF_WaterBioluminescence_v7 Material Function with CharacterWorldPosition param and proximity multipliers"""
    
    mf_path = "/Game/Melodia/Materials/Functions/MF_WaterBioluminescence_v7"
    mf_name = "MF_WaterBioluminescence_v7"
    
    # Check if exists
    if unreal.EditorAssetLibrary.does_asset_exist(mf_path):
        print(f"Material Function already exists: {mf_path}")
        mf = unreal.EditorAssetLibrary.load_asset(mf_path)
    else:
        mf_factory = unreal.MaterialFunctionFactoryNew()
        mf = unreal.EditorAssetLibrary.create_asset(mf_path, mf_name, unreal.MaterialFunction, mf_factory)
        print(f"Created new Material Function: {mf_path}")
    
    if not mf:
        print("Failed to create/load Material Function")
        return
    
    # Get the material editing library
    mat_edit_lib = unreal.MaterialEditingLibrary()
    
    # Clear existing nodes (optional - comment out to preserve existing)
    # nodes = mat_edit_lib.get_all_material_function_expressions(mf)
    # for node in nodes:
    #     mat_edit_lib.destroy_material_function_expression(node)
    
    # Create input: CharacterWorldPosition (Vector3)
    char_pos_input = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionFunctionInput, -400, -100)
    char_pos_input.input_name = "CharacterWorldPosition"
    char_pos_input.input_type = unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3
    char_pos_input.use_preview_value_as_default = True
    char_pos_input.preview_value = unreal.Vector(0, 0, 0)
    char_pos_input.description = "World position of the character/player for proximity calculations"
    print("Created CharacterWorldPosition input")
    
    # Create input: ProximityRadius (Scalar) - distance at which effect is max
    prox_radius_input = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionFunctionInput, -400, 50)
    prox_radius_input.input_name = "ProximityRadius"
    prox_radius_input.input_type = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR
    prox_radius_input.use_preview_value_as_default = True
    prox_radius_input.preview_value = 500.0
    prox_radius_input.description = "Radius within which proximity effect is calculated"
    print("Created ProximityRadius input")
    
    # Create input: ProximityFalloff (Scalar) - falloff exponent
    prox_falloff_input = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionFunctionInput, -400, 150)
    prox_falloff_input.input_name = "ProximityFalloff"
    prox_falloff_input.input_type = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR
    prox_falloff_input.use_preview_value_as_default = True
    prox_falloff_input.preview_value = 2.0
    prox_falloff_input.description = "Falloff exponent for proximity (1=linear, 2=quadratic, etc.)"
    print("Created ProximityFalloff input")
    
    # WorldPosition node (for current pixel/fragment world position)
    world_pos = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionWorldPosition, -200, -100)
    print("Created WorldPosition node")
    
    # Distance calculation: distance(CharacterWorldPosition, WorldPosition)
    distance = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionDistance, 0, -100)
    mat_edit_lib.connect_material_expressions(char_pos_input, "", distance, "A")
    mat_edit_lib.connect_material_expressions(world_pos, "", distance, "B")
    print("Created Distance calculation")
    
    # Normalized distance: distance / ProximityRadius
    div = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionDivide, 200, -100)
    mat_edit_lib.connect_material_expressions(distance, "", div, "A")
    mat_edit_lib.connect_material_expressions(prox_radius_input, "", div, "B")
    print("Created Normalized Distance")
    
    # Proximity factor: 1 - saturate(normalized_distance ^ ProximityFalloff)
    # First: pow(normalized_distance, ProximityFalloff)
    pow_node = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionPower, 400, -100)
    mat_edit_lib.connect_material_expressions(div, "", pow_node, "Base")
    mat_edit_lib.connect_material_expressions(prox_falloff_input, "", pow_node, "Exponent")
    print("Created Pow for falloff")
    
    # Saturate
    saturate = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionSaturate, 600, -100)
    mat_edit_lib.connect_material_expressions(pow_node, "", saturate, "")
    print("Created Saturate")
    
    # 1 - saturate = proximity factor (1 at center, 0 at radius)
    one_minus = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionOneMinus, 800, -100)
    mat_edit_lib.connect_material_expressions(saturate, "", one_minus, "")
    print("Created 1 - saturate (ProximityFactor)")
    
    # === OUTPUTS ===
    
    # Output 1: ProximityFactor (Scalar) - for general use
    prox_factor_output = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionFunctionOutput, 1000, -200)
    prox_factor_output.output_name = "ProximityFactor"
    prox_factor_output.description = "Proximity factor (1.0 at character, 0.0 at radius)"
    mat_edit_lib.connect_material_expressions(one_minus, "", prox_factor_output, "")
    print("Created ProximityFactor output")
    
    # Now create the bioluminescence logic using ProximityFactor
    # SparkleDensity *= ProximityFactor
    # DeepGlowColor.a *= ProximityFactor
    # FoamIntensity *= ProximityFactor
    
    # Input: BaseSparkleDensity
    sparkle_density_input = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionFunctionInput, -400, 250)
    sparkle_density_input.input_name = "BaseSparkleDensity"
    sparkle_density_input.input_type = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR
    sparkle_density_input.use_preview_value_as_default = True
    sparkle_density_input.preview_value = 1.0
    print("Created BaseSparkleDensity input")
    
    # Input: BaseDeepGlowColor (Vector3 for RGB, Alpha handled separately)
    deep_glow_input = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionFunctionInput, -400, 350)
    deep_glow_input.input_name = "BaseDeepGlowColor"
    deep_glow_input.input_type = unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3
    deep_glow_input.use_preview_value_as_default = True
    deep_glow_input.preview_value = unreal.Vector(0.0, 0.5, 1.0)
    print("Created BaseDeepGlowColor input")
    
    # Input: BaseDeepGlowAlpha
    deep_glow_alpha_input = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionFunctionInput, -400, 450)
    deep_glow_alpha_input.input_name = "BaseDeepGlowAlpha"
    deep_glow_alpha_input.input_type = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR
    deep_glow_alpha_input.use_preview_value_as_default = True
    deep_glow_alpha_input.preview_value = 1.0
    print("Created BaseDeepGlowAlpha input")
    
    # Input: BaseFoamIntensity
    foam_intensity_input = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionFunctionInput, -400, 550)
    foam_intensity_input.input_name = "BaseFoamIntensity"
    foam_intensity_input.input_type = unreal.FunctionInputType.FUNCTION_INPUT_SCALAR
    foam_intensity_input.use_preview_value_as_default = True
    foam_intensity_input.preview_value = 1.0
    print("Created BaseFoamIntensity input")
    
    # Multiply SparkleDensity * ProximityFactor
    sparkle_mult = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionMultiply, 1000, 250)
    mat_edit_lib.connect_material_expressions(sparkle_density_input, "", sparkle_mult, "A")
    mat_edit_lib.connect_material_expressions(one_minus, "", sparkle_mult, "B")
    print("Created SparkleDensity * ProximityFactor")
    
    # Output: SparkleDensity
    sparkle_output = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionFunctionOutput, 1200, 250)
    sparkle_output.output_name = "SparkleDensity"
    sparkle_output.description = "Sparkle density modulated by proximity"
    mat_edit_lib.connect_material_expressions(sparkle_mult, "", sparkle_output, "")
    print("Created SparkleDensity output")
    
    # Multiply DeepGlowColor.a * ProximityFactor
    # DeepGlowColor is Vector3, we need to append alpha
    # First multiply alpha
    glow_alpha_mult = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionMultiply, 1000, 450)
    mat_edit_lib.connect_material_expressions(deep_glow_alpha_input, "", glow_alpha_mult, "A")
    mat_edit_lib.connect_material_expressions(one_minus, "", glow_alpha_mult, "B")
    print("Created DeepGlowAlpha * ProximityFactor")
    
    # Output: DeepGlowColor (Vector4 with modulated alpha)
    # We'll output Vector3 for RGB and Scalar for Alpha separately
    deep_glow_rgb_output = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionFunctionOutput, 1200, 350)
    deep_glow_rgb_output.output_name = "DeepGlowColorRGB"
    deep_glow_rgb_output.description = "Deep glow color RGB (unmodulated)"
    mat_edit_lib.connect_material_expressions(deep_glow_input, "", deep_glow_rgb_output, "")
    print("Created DeepGlowColorRGB output")
    
    deep_glow_alpha_output = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionFunctionOutput, 1200, 450)
    deep_glow_alpha_output.output_name = "DeepGlowAlpha"
    deep_glow_alpha_output.description = "Deep glow alpha modulated by proximity"
    mat_edit_lib.connect_material_expressions(glow_alpha_mult, "", deep_glow_alpha_output, "")
    print("Created DeepGlowAlpha output")
    
    # Multiply FoamIntensity * ProximityFactor
    foam_mult = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionMultiply, 1000, 550)
    mat_edit_lib.connect_material_expressions(foam_intensity_input, "", foam_mult, "A")
    mat_edit_lib.connect_material_expressions(one_minus, "", foam_mult, "B")
    print("Created FoamIntensity * ProximityFactor")
    
    # Output: FoamIntensity
    foam_output = mat_edit_lib.create_material_expression(mf, unreal.MaterialExpressionFunctionOutput, 1200, 550)
    foam_output.output_name = "FoamIntensity"
    foam_output.description = "Foam intensity modulated by proximity"
    mat_edit_lib.connect_material_expressions(foam_mult, "", foam_output, "")
    print("Created FoamIntensity output")
    
    # Save
    unreal.EditorAssetLibrary.save_asset(mf_path)
    print(f"\nSaved Material Function: {mf_path}")
    
    print("\n=== MF_WaterBioluminescence_v7 Created ===")
    print(f"Asset: {mf_path}")
    print("\nInputs:")
    print("  - CharacterWorldPosition (Vector3)")
    print("  - ProximityRadius (Scalar, default 500)")
    print("  - ProximityFalloff (Scalar, default 2.0)")
    print("  - BaseSparkleDensity (Scalar)")
    print("  - BaseDeepGlowColor (Vector3)")
    print("  - BaseDeepGlowAlpha (Scalar)")
    print("  - BaseFoamIntensity (Scalar)")
    print("\nOutputs:")
    print("  - ProximityFactor (Scalar)")
    print("  - SparkleDensity (Scalar) = BaseSparkleDensity * ProximityFactor")
    print("  - DeepGlowColorRGB (Vector3)")
    print("  - DeepGlowAlpha (Scalar) = BaseDeepGlowAlpha * ProximityFactor")
    print("  - FoamIntensity (Scalar) = BaseFoamIntensity * ProximityFactor")

if __name__ == "__main__":
    create_water_bioluminescence_mf()