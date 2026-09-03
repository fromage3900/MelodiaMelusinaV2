import unreal

# ============================================================
# SK_Melusina Material Slots Inspection Script
# Run in Unreal Editor: -ExecutePythonScript=C:/EnvironmentPortfolio/BS_GodFile/Content/Python/inspect_sk_melusina_slots.py
# ============================================================

def inspect_sk_melusina_material_slots():
    """Inspect SK_Melusina material slots, especially 24, 26, 28"""
    
    # Paths to check (both projects)
    sk_paths = [
        "/Game/Melodia/Characters/Melusina/SK_Melusina",  # BS_GodFile
        "/Game/Melodia/Characters/Melusina/SK_Melusina",  # CompatibilityLabs (same path)
    ]
    
    for sk_path in sk_paths:
        print(f"\n{'='*60}")
        print(f"Inspecting: {sk_path}")
        print(f"{'='*60}")
        
        if not unreal.EditorAssetLibrary.does_asset_exist(sk_path):
            print(f"  NOT FOUND: {sk_path}")
            continue
        
        sk_mesh = unreal.EditorAssetLibrary.load_asset(sk_path)
        if not sk_mesh or not isinstance(sk_mesh, unreal.SkeletalMesh):
            print(f"  Failed to load or not a SkeletalMesh")
            continue
        
        # Get material slots
        materials = sk_mesh.get_materials()
        print(f"  Total material slots: {len(materials)}")
        
        for i, mat_slot in enumerate(materials):
            mat_name = mat_slot.get_name() if mat_slot else "None"
            slot_name = mat_slot.slot_name if mat_slot else "None"
            print(f"  Slot [{i}]: Name='{slot_name}', Material='{mat_name}'")
            
            # Highlight slots 24, 26, 28
            if i in [24, 26, 28]:
                print(f"    *** TARGET SLOT {i} ***")
                if mat_slot and mat_slot.material_interface:
                    mi = mat_slot.material_interface
                    print(f"      Material: {mi.get_name()}")
                    print(f"      Class: {mi.get_class().get_name()}")
                    if isinstance(mi, unreal.MaterialInstance):
                        parent = mi.get_parent()
                        if parent:
                            print(f"      Parent: {parent.get_name()}")
        
        # Also check for any materials with "SkeletonFixSpike" in name
        print(f"\n  Searching for '_SkeletonFixSpike' materials...")
        for i, mat_slot in enumerate(materials):
            if mat_slot and mat_slot.material_interface:
                mat_name = mat_slot.material_interface.get_name()
                if "SkeletonFixSpike" in mat_name or "SkeletonFix" in mat_name or "Spike" in mat_name:
                    print(f"    Slot [{i}]: {mat_name} <- CONTAINS 'SkeletonFixSpike'")
        
        # List all material instances used
        print(f"\n  All Material Instances used:")
        mi_set = set()
        for mat_slot in materials:
            if mat_slot and mat_slot.material_interface:
                mi = mat_slot.material_interface
                if isinstance(mi, unreal.MaterialInstance):
                    mi_set.add(mi.get_name())
        for mi_name in sorted(mi_set):
            print(f"    - {mi_name}")

def find_clean_mi_instances():
    """Find clean MI instances for Melusina materials"""
    print(f"\n{'='*60}")
    print(f"Searching for clean MI_Melusina_* instances...")
    print(f"{'='*60}")
    
    # Search in Melusina Materials folder
    search_paths = [
        "/Game/Melodia/Characters/Melusina/Materials",
    ]
    
    for search_path in search_paths:
        assets = unreal.EditorAssetLibrary.list_assets(search_path, recursive=True, include_folder=False)
        for asset_path in assets:
            if asset_path.endswith(".uasset"):
                asset = unreal.EditorAssetLibrary.load_asset(asset_path)
                if asset and isinstance(asset, unreal.MaterialInstance):
                    name = asset.get_name()
                    if name.startswith("MI_Melusina_") and "SkeletonFix" not in name and "Spike" not in name:
                        parent = asset.get_parent()
                        parent_name = parent.get_name() if parent else "None"
                        print(f"  {name} (Parent: {parent_name})")

def suggest_slot_reassignments():
    """Suggest clean MI instances for slots 24, 26, 28"""
    print(f"\n{'='*60}")
    print(f"SUGGESTED REASSIGNMENTS FOR SLOTS 24, 26, 28")
    print(f"{'='*60}")
    print("Based on typical Melusina material setup:")
    print("  Slot 24: Likely body/skin material -> MI_Melusina_Material_024 or similar")
    print("  Slot 26: Likely clothing/accessory -> MI_Melusina_SKIRT_003 or MI_Melusina_SHAWL_001")
    print("  Slot 28: Likely hair/outline -> MI_Melusina_Outline_004/005 or MI_Melusina_Halftone_*")
    print("\nAction: In Skeletal Mesh Editor -> Materials tab, reassign these slots")

if __name__ == "__main__":
    inspect_sk_melusina_material_slots()
    find_clean_mi_instances()
    suggest_slot_reassignments()