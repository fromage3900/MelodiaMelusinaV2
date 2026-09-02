#!/usr/bin/env python3
"""
Comprehensive MI creation and application script.
Creates Copernicus MIs for ALL texture variants and applies to cathedral pieces.

Run inside UE Editor Python console:
    exec(open(r"C:/EnvironmentPortfolio/BS_GodFile/Content/Python/_mi_complete_pipeline.py", encoding="utf-8").read())
"""
import unreal
import os
import json

# ============================================================
# Configuration
# ============================================================
MI_DIR = "/Game/EnvSandbox/Materials/Instances/Copernicus"
MASTER_PATH = "/Game/EnvSandbox/Materials/Masters/M_Master_Toon_Universal"
TEXTURE_DIR = r"C:\EnvironmentPortfolio\BS_GodFile\Saved\Audit\copernicus_cymatic"

# Channel mapping for Copernicus textures
CHANNEL_MAP = {
    "BaseColor": "Albedo",
    "Normal": "NormalMap",
    "ORM": "ORM",
    "Height": "HeightMap",
    "Roughness": "RoughnessMap",
    "Metallic": "MetallicMap",
    "Emissive": "EmissiveMap",
    "Iridescence": "Iridescence",
    "Opacity": "Opacity",
}

# ============================================================
# Step 1: Create Material Parameter Collection for Cymatics
# ============================================================
def create_cymatic_mpc():
    """Create MPC_Cymatics_Driver if it doesn't exist."""
    mpc_path = "/Game/Melodia/Cymatics/MPC_Cymatics_Driver"
    if unreal.EditorAssetLibrary.does_asset_exist(mpc_path):
        print(f"[MPC] Already exists: {mpc_path}")
        return unreal.EditorAssetLibrary.load_asset(mpc_path)
    
    # Create MPC
    factory = unreal.MaterialParameterCollectionFactoryNew()
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    
    mpc = asset_tools.create_asset(
        "MPC_Cymatics_Driver",
        "/Game/Melodia/Cymatics",
        unreal.MaterialParameterCollection,
        factory
    )
    
    if mpc:
        print(f"[MPC] Created: {mpc_path}")
        # Add scalar parameters
        # Note: Can't add params via Python, must use C++ or manual setup
        # For now, just create the empty MPC
        unreal.EditorAssetLibrary.save_loaded_asset(mpc)
        return mpc
    else:
        print(f"[MPC] ERROR: Failed to create")
        return None

# ============================================================
# Step 2: Create MI_Copernicus_CymaticReactive
# ============================================================
def create_cymatic_reactive_mi():
    """Create the audio-reactive MI."""
    mi_path = f"{MI_DIR}/MI_Copernicus_CymaticReactive"
    
    if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
        print(f"[Cymatic] Already exists: {mi_path}")
        return unreal.EditorAssetLibrary.load_asset(mi_path)
    
    # Create MI
    factory = unreal.MaterialInstanceConstantFactoryNew()
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    
    mi = asset_tools.create_asset(
        "MI_Copernicus_CymaticReactive",
        MI_DIR,
        unreal.MaterialInstanceConstant,
        factory
    )
    
    if mi:
        print(f"[Cymatic] Created: {mi_path}")
        # Set parent
        master = unreal.EditorAssetLibrary.load_asset(MASTER_PATH)
        if master:
            mi.set_editor_property("parent", master)
            print(f"[Cymatic] Parent set: {MASTER_PATH}")
        
        # Set scalar params (these will be animated via Blueprint later)
        for name, value in [("IridescenceIntensity", 1.0), ("EmissiveScale", 0.5)]:
            try:
                unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, name, value)
                print(f"[Cymatic] Set {name} = {value}")
            except Exception as e:
                print(f"[Cymatic] WARNING: {e}")
        
        unreal.EditorAssetLibrary.save_loaded_asset(mi)
        return mi
    else:
        print(f"[Cymatic] ERROR: Failed to create")
        return None

# ============================================================
# Step 3: Create MIs for ALL Copernicus variants
# ============================================================
def create_all_copernicus_mis():
    """Create an MI for each Copernicus texture variant."""
    master = unreal.EditorAssetLibrary.load_asset(MASTER_PATH)
    if not master:
        print("[ERROR] Master material not found")
        return []
    
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    created = []
    
    # Get all variant directories
    variants = []
    for item in os.listdir(TEXTURE_DIR):
        item_path = os.path.join(TEXTURE_DIR, item)
        if os.path.isdir(item_path):
            variants.append(item)
    
    print(f"\n[Expand] Found {len(variants)} Copernicus variants")
    
    for variant in sorted(variants):
        mi_name = f"MI_Copernicus_{variant}"
        mi_path = f"{MI_DIR}/{mi_name}"
        
        # Skip if already exists
        if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
            print(f"  [SKIP] {mi_name} exists")
            created.append(variant)
            continue
        
        # Get textures for this variant
        variant_path = os.path.join(TEXTURE_DIR, variant)
        textures = {}
        for f in os.listdir(variant_path):
            if f.endswith('.png'):
                for channel, param in CHANNEL_MAP.items():
                    if channel in f:
                        textures[param] = os.path.join(variant_path, f)
        
        if not textures:
            print(f"  [SKIP] {variant}: no textures")
            continue
        
        # Create MI
        factory = unreal.MaterialInstanceConstantFactoryNew()
        mi = asset_tools.create_asset(mi_name, MI_DIR, unreal.MaterialInstanceConstant, factory)
        
        if not mi:
            print(f"  [FAIL] {variant}")
            continue
        
        # Set parent
        mi.set_editor_property("parent", master)
        
        # Import and assign textures
        for param_name, texture_path in textures.items():
            try:
                # Import texture
                dest_path = f"/Game/EnvSandbox/Textures/Copernicus/{variant}"
                if not unreal.EditorAssetLibrary.does_directory_exist(dest_path):
                    unreal.EditorAssetLibrary.make_directory(dest_path)
                
                filename = os.path.basename(texture_path)
                dest_texture = f"{dest_path}/{filename}"
                
                if not unreal.EditorAssetLibrary.does_asset_exist(dest_texture):
                    unreal.EditorAssetLibrary.import_asset(texture_path, dest_path)
                
                # Load and assign
                tex = unreal.EditorAssetLibrary.load_asset(dest_texture)
                if tex:
                    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                        mi, param_name, tex
                    )
            except Exception as e:
                print(f"    [WARN] {param_name}: {e}")
        
        # Save
        unreal.EditorAssetLibrary.save_loaded_asset(mi)
        created.append(variant)
        print(f"  [OK] {variant} ({len(textures)} textures)")
    
    return created

# ============================================================
# Step 4: Apply MIs to cathedral pieces
# ============================================================
def apply_mis_to_cathedral():
    """Apply Copernicus MIs to all cathedral StaticMeshActors."""
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    sma = [a for a in actors if type(a).__name__ == "StaticMeshActor"]
    
    # Get available MIs
    mis = unreal.EditorAssetLibrary.list_assets(MI_DIR)
    mis = [m for m in mis if "MI_Copernicus_" in m]
    
    if not mis:
        print("[ERROR] No MIs found")
        return 0
    
    print(f"\n[Apply] {len(sma)} SMAs, {len(mis)} MIs")
    
    applied = 0
    for i, actor in enumerate(sma):
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if not comp:
            continue
        
        # Pick MI based on actor label
        label = actor.get_actor_label()
        
        # Determine MI type from label
        mi = None
        if "Arch" in label or "Column" in label:
            mi = next((m for m in mis if "CavernWeave" in m or "ChoirStone" in m), None)
        elif "Bench" in label or "Chair" in label or "Table" in label or "Stool" in label:
            mi = next((m for m in mis if "PearlWeave" in m or "SingingSilk" in m), None)
        elif "Tree" in label or "Shrub" in label or "Ivy" in label:
            mi = next((m for m in mis if "FrostBloom" in m or "FrozenFracture" in m), None)
        elif "Window" in label or "Portal" in label or "Rose" in label:
            mi = next((m for m in mis if "CrystalCathedral" in m or "FractalCathedral" in m), None)
        elif "Altar" in label or "Stall" in label:
            mi = next((m for m in mis if "GildedCoral" in m or "MoltenCore" in m), None)
        else:
            mi = mis[i % len(mis)]
        
        if mi:
            try:
                mi_obj = unreal.EditorAssetLibrary.load_asset(mi)
                if mi_obj:
                    comp.set_editor_property("override_materials", [mi_obj])
                    applied += 1
            except Exception as e:
                pass
    
    return applied

# ============================================================
# Main
# ============================================================
def main():
    print("=" * 70)
    print("COPERNICUS MI COMPLETE PIPELINE")
    print("=" * 70)
    
    # Step 1: Cymatic MPC
    print("\n--- Step 1: Cymatic MPC ---")
    create_cymatic_mpc()
    
    # Step 2: Cymatic Reactive MI
    print("\n--- Step 2: Cymatic Reactive MI ---")
    create_cymatic_reactive_mi()
    
    # Step 3: Expand MI Library
    print("\n--- Step 3: Expand MI Library ---")
    created = create_all_copernicus_mis()
    print(f"\nTotal MIs created/verified: {len(created)}")
    
    # Step 4: Apply to Cathedral
    print("\n--- Step 4: Apply to Cathedral ---")
    applied = apply_mis_to_cathedral()
    print(f"\nPieces updated: {applied}")
    
    # Save level
    unreal.EditorLevelLibrary.save_current_level()
    print("\n[COMPLETE] Level saved.")
    
    return len(created), applied

if __name__ == "__main__":
    main()
