#!/usr/bin/env python3
"""
Create MI_Copernicus_CymaticReactive material instance.

Creates a new material instance with audio-reactive scalar parameters that
read from MPC_Melodia_Palette for animation.

Run inside UE Editor Python (Monolith run_python):
    exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/_mi_cymatic_reactive_create.py", encoding="utf-8").read())
"""
import unreal

MI_PATH = "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_CymaticReactive"
MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
MPC_PATH = "/Game/Melodia/_PROJECT/04_Materials/MPC_Melodia_Palette"

# Audio-reactive scalar parameters
AUDIO_REACTIVE_PARAMS = {
    "CymaticAmplitude": 1.0,
    "BeatPulse": 0.0,
    "BassIntensity": 0.5,
    "CymaticModeN": 3.0,
    "CymaticModeM": 2.0,
}


def create_cymatic_reactive_mi():
    """Create MI_Copernicus_CymaticReactive with audio-reactive parameters."""
    # Check if already exists
    if unreal.EditorAssetLibrary.does_asset_exist(MI_PATH):
        mi = unreal.EditorAssetLibrary.load_asset(MI_PATH)
        print(f"[cymatic] MI already exists: {MI_PATH}")
        return mi

    # Load master material
    master = unreal.EditorAssetLibrary.load_asset(MASTER_PATH)
    if not master:
        print(f"[cymatic] ERROR: Master material not found: {MASTER_PATH}")
        return None

    # Create the material instance
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    mi_name = "MI_Copernicus_CymaticReactive"
    mi_dir = "/Game/EnvSandbox/Materials/Instances/Copernicus"

    # Ensure directory exists
    if not unreal.EditorAssetLibrary.does_directory_exist(mi_dir):
        unreal.EditorAssetLibrary.make_directory(mi_dir)

    mi = asset_tools.create_asset(mi_name, mi_dir, unreal.MaterialInstanceConstant,
                                   unreal.MaterialInstanceConstantFactoryNew())
    if not mi:
        print(f"[cymatic] ERROR: Failed to create MI")
        return None

    # Set parent
    try:
        mi.set_editor_property("parent", master)
        print(f"[cymatic] Set parent: {MASTER_PATH}")
    except Exception as e:
        print(f"[cymatic] WARNING: Failed to set parent: {e}")

    # Set audio-reactive scalar parameters
    for param_name, param_value in AUDIO_REACTIVE_PARAMS.items():
        try:
            unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
                mi, param_name, param_value
            )
            print(f"[cymatic] Set scalar {param_name} = {param_value}")
        except Exception as e:
            print(f"[cymatic] WARNING: Failed to set {param_name}: {e}")

    # Save the asset
    try:
        unreal.EditorAssetLibrary.save_loaded_asset(mi)
        print(f"[cymatic] Saved: {MI_PATH}")
    except Exception as e:
        print(f"[cymatic] WARNING: Failed to save: {e}")

    return mi


def main():
    print("=" * 60)
    print("Creating MI_Copernicus_CymaticReactive")
    print("=" * 60)

    mi = create_cymatic_reactive_mi()
    if mi:
        print(f"\n[SUCCESS] MI created at: {MI_PATH}")
        print(f"Parameters set:")
        for k, v in AUDIO_REACTIVE_PARAMS.items():
            print(f"  {k} = {v}")
    else:
        print("\n[FAILED] MI creation failed")

    return mi


if __name__ == "__main__":
    main()