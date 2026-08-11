"""
Setup Material Parameter Collection MPC_HarmonicGravity for Substrate Toon Shaders
"""

import unreal

def setup_mpc_harmonic_gravity():
    mpc_package = "/Game/EnvSandbox/Materials"
    mpc_name = "MPC_HarmonicGravity"
    mpc_path = f"{mpc_package}/{mpc_name}"

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

    mpc = unreal.load_asset(mpc_path)
    if not mpc:
        factory = unreal.MaterialParameterCollectionFactoryNew()
        mpc = asset_tools.create_asset(mpc_name, mpc_package, unreal.MaterialParameterCollection, factory)
        print(f"Created MPC: {mpc_path}")
    else:
        print(f"Loaded existing MPC: {mpc_path}")

    # Configure Scalar Parameters
    scalars = [
        ("BassPulseIntensity", 0.0),
        ("HarmonicRippleFreq", 1.0),
        ("HarmonicRippleAmp", 0.0),
        ("ToonOutlineDistortion", 0.0),
        ("BeatOnsetFlash", 0.0)
    ]

    for name, default_val in scalars:
        unreal.MaterialEditingLibrary.set_material_parameter_collection_scalar_variable(mpc, name, default_val)

    # Configure Vector Parameters
    vectors = [
        ("HarmonicGlowColor", unreal.LinearColor(0.2, 0.6, 1.0, 1.0)),
        ("GravityVector4D", unreal.LinearColor(0.0, 0.0, 1.0, 0.0))
    ]

    for name, default_color in vectors:
        unreal.MaterialEditingLibrary.set_material_parameter_collection_vector_variable(mpc, name, default_color)

    unreal.EditorAssetLibrary.save_asset(mpc_path)
    print("Successfully configured MPC_HarmonicGravity!")

if __name__ == "__main__":
    setup_mpc_harmonic_gravity()
