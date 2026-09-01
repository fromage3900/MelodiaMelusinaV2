import unreal
import json

# ============================================================
# Create BP_CymaticsMIDDriver using the documented C++ API
# ============================================================

# Based on subagent findings:
# - SampleCymaticAmplitude(float U, float V) -> float
# - GetCymaticMode(int32& OutN, int32& OutM) -> void
# - GetBeatPulse() -> float
# - GetBassIntensity() -> float
# All BlueprintPure - callable from Python

print("=== Creating BP_CymaticsMIDDriver ===")

# Create the Blueprint
bp_path = "/Game/Melodia/Cymatics/BP_CymaticsMIDDriver"
existing = unreal.EditorAssetLibrary.load_asset(bp_path)
if existing:
    print("BP already exists, skipping creation")
else:
    # Create Blueprint factory
    factory = unresolved.AssetTask()
    factory.set_editor_property("asset_name", "BP_CymaticsMIDDriver")
    factory.set_editor_property("package_path", "/Game/Melodia/Cymatics")
    factory.set_editor_property("asset_class", unreal.ActorBlueprint)
    
    # Use AssetTools to create
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    bp = asset_tools.create_asset(
        "BP_CymaticsMIDDriver",
        "/Game/Melodia/Cymatics",
        None,
        None
    )
    
    if bp:
        print(f"Created: {bp.get_name()}")
    else:
        print("[FAIL] Could not create BP")

print("\n=== Creating MI_Copernicus_CymaticReactive ===")

# Create MI that reads from MPC_Melodia_Palette
mi_path = "/Game/EnvSandbox/Materials/Instances/Copernicus/MI_Copernicus_CymaticReactive"
existing_mi = unreal.EditorAssetLibrary.load_asset(mi_path)
if existing_mi:
    print("MI already exists")
else:
    # Create a Material Instance from M_Master_Toon_Universal
    master = unreal.EditorAssetLibrary.load_asset("/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal.M_Master_Toon_Universal")
    if master:
        factory = unreal.MaterialInstanceConstantFactoryNew()
        factory.set_editor_property("parent", master)
        mi = asset_tools.create_asset(
            "MI_Copernicus_CymaticReactive",
            "/Game/EnvSandbox/Materials/Instances/Copernicus",
            master,
            factory
        )
        if mi:
            print(f"Created: {mi.get_name()}")
        else:
            print("[FAIL] Could not create MI")

print("\n=== DONE ===")
