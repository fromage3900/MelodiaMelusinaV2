import unreal

# ============================================================
# TP_Melusina Material Parameter Collection Creation Script
# Run in Unreal Editor: -ExecutePythonScript=C:/EnvironmentPortfolio/BS_GodFile/Content/Python/create_tp_melusina_mpc.py
# ============================================================

def create_tp_melusina_mpc():
    """Create TP_Melusina Material Parameter Collection with DiffuseRamp and SpecularRamp curves."""
    
    asset_path = "/Game/Melodia/Characters/Melusina/MPC_TP_Melusina"
    asset_name = "MPC_TP_Melusina"
    
    # Check if already exists
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        print(f"Asset already exists: {asset_path}")
        mpc = unreal.EditorAssetLibrary.load_asset(asset_path)
    else:
        # Create new Material Parameter Collection
        mpc_factory = unreal.MaterialParameterCollectionFactoryNew()
        mpc = unreal.EditorAssetLibrary.create_asset(asset_path, asset_name, unreal.MaterialParameterCollection, mpc_factory)
        print(f"Created new MPC: {asset_path}")
    
    if not mpc:
        print("Failed to create/load MPC")
        return
    
    # Get the parameter editor subsystem to modify parameters
    param_editor = unreal.MaterialParameterCollectionEditorSubsystem()
    
    # Define DiffuseRamp curve keys: (0.0=#352D40, 0.3=white, 1.0=warm)
    # Convert hex colors to linear RGB
    # #352D40 = RGB(53, 45, 64) -> sRGB to linear
    # white = RGB(255, 255, 255)
    # warm = RGB(255, 180, 100) approx
    
    def srgb_to_linear(c):
        c = c / 255.0
        if c <= 0.04045:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4
    
    color_0_0 = unreal.LinearColor(
        srgb_to_linear(53), srgb_to_linear(45), srgb_to_linear(64), 1.0
    )
    color_0_3 = unreal.LinearColor(1.0, 1.0, 1.0, 1.0)  # white
    color_1_0 = unreal.LinearColor(
        srgb_to_linear(255), srgb_to_linear(180), srgb_to_linear(100), 1.0
    )
    
    # Define SpecularRamp curve key: (0.9) - assuming single key at 0.9 = white/high specular
    # We'll create a scalar curve for specular intensity
    
    # Add/Update DiffuseRamp Vector Parameter (Color Ramp)
    diffuse_param_name = "DiffuseRamp"
    try:
        # Try to add vector parameter for color ramp
        param_editor.add_vector_parameter(mpc, diffuse_param_name)
        print(f"Added vector parameter: {diffuse_param_name}")
    except:
        print(f"Parameter {diffuse_param_name} may already exist")
    
    # Set the default value for DiffuseRamp (we'll use the first key color as default)
    param_editor.set_vector_parameter_default(mpc, diffuse_param_name, color_0_0)
    
    # Add/Update SpecularRamp Scalar Parameter
    specular_param_name = "SpecularRamp"
    try:
        param_editor.add_scalar_parameter(mpc, specular_param_name)
        print(f"Added scalar parameter: {specular_param_name}")
    except:
        print(f"Parameter {specular_param_name} may already exist")
    
    # Set default specular value at 0.9
    param_editor.set_scalar_parameter_default(mpc, specular_param_name, 0.9)
    
    # Save the asset
    unreal.EditorAssetLibrary.save_asset(asset_path)
    print(f"Saved MPC: {asset_path}")
    
    # Note: For full curve editing (multiple keys), you'd need to use the Curve Editor UI
    # or create a CurveAsset and reference it. MPC parameters are single values.
    # For gradient/ramps, typically you'd use a Texture (Gradient Texture) or CurveAsset.
    
    print("\n=== TP_Melusina MPC Created ===")
    print(f"Asset: {asset_path}")
    print(f"DiffuseRamp: Vector param (default=#352D40)")
    print(f"SpecularRamp: Scalar param (default=0.9)")
    print("\nNOTE: For multi-key ramps (0.0, 0.3, 1.0), create a Gradient Texture or CurveAsset")
    print("and reference it from your materials instead of using MPC vector params directly.")

if __name__ == "__main__":
    create_tp_melusina_mpc()