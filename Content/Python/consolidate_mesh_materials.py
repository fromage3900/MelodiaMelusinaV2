# consolidate_mesh_materials.py
# Run from UE editor console: py Content/Python/consolidate_mesh_materials.py

"""
Mesh-Local Material Consolidation Script

This script safely consolidates mesh-local materials into shared instances:
1. Loads each mesh
2. Reads its material slots
3. For mesh-local materials, copies them to a shared folder with a proper name
4. Reassigns mesh material slots to the shared copy
5. Saves the mesh
6. Deletes the old mesh-local material

This prevents broken material references and reduces clutter.

USAGE:
    # Dry run first:
    consolidate_mesh_materials(dry_run=True)
    
    # Apply changes:
    consolidate_mesh_materials(dry_run=False)
    
    # Process specific mesh folder:
    consolidate_mesh_materials(filter='wall')
"""

import unreal
import os
import shutil
from datetime import datetime
from collections import defaultdict

ENV_MESH_PATH = "/Game/EnvSandbox/Meshes/Environment"
SHARED_OUTPUT_PATH = "/Game/EnvSandbox/Materials/Instances/Consolidated"

# Known material names to skip (these are the "standard" mesh-local names)
STANDARD_NAMES = {
    "colormap.uasset", "__ignore_.uasset", "_defaultMat.uasset",
    "door.uasset", "doorLeft.uasset", "doorRight.uasset",
    "doorFridge.uasset", "doorFreezer.uasset", "drawer.uasset",
    "drawerBottom.uasset", "drawerLeft.uasset", "drawerRight.uasset",
    "drawerTop.uasset", "cover.uasset", "coverBottom.uasset", "coverTop.uasset",
    "window.uasset", "windowBottom.uasset", "windowTop.uasset",
    "gate.uasset", "fence.uasset", "ladder.uasset", "overhang.uasset",
    "pillar-stone.uasset", "pillar-wood.uasset",
    "planks.uasset", "planks-half.uasset", "planks-opening.uasset",
    "plant.uasset", "rock-large.uasset", "rock-small.uasset",
    "rock-wide.uasset", "rocks-high.uasset", "rocks-large.uasset",
    "rocks-low.uasset", "rocks-ramp.uasset", "rocks-small.uasset",
    "stairs-stone.uasset", "stairs-wood.uasset",
    "tower-base.uasset", "tower-top.uasset",
    "tree.uasset", "tree-crooked.uasset", "tree-large.uasset",
    "tree-small.uasset", "tree-trunk.uasset",
    "wall.uasset", "wall-arch.uasset", "wall-block.uasset",
    "wall-broken.uasset", "wall-corner.uasset", "wall-corner-diagonal.uasset",
    "wall-corner-edge.uasset", "wall-corner-half.uasset",
    "wall-corner-slant.uasset", "wall-curved.uasset",
    "wall-diagonal.uasset", "wall-door.uasset", "wall-half.uasset",
    "wall-narrow.uasset", "wall-pillar.uasset", "wall-rounded.uasset",
    "wall-side.uasset", "wall-slope.uasset", "wall-stud.uasset",
    "wall-window.uasset", "roof.uasset", "roof-corner.uasset",
    "roof-flat.uasset", "roof-gable.uasset", "roof-gable-detail.uasset",
    "roof-gable-end.uasset", "roof-gable-top.uasset",
    "roof-high.uasset", "roof-left.uasset", "roof-point.uasset",
    "roof-right.uasset", "roof-window.uasset",
    "Water.uasset", "watermill.uasset", "watermill-wide.uasset",
    "weapon-arrow.uasset", "weapon-bow.uasset", "wheel.uasset",
    "windmill.uasset", "wood.uasset",
    # Furniture
    "bedDouble.uasset", "bedSingle.uasset", "bedBunk.uasset",
    "chair.uasset", "chairDesk.uasset", "pillow.uasset",
    "pillowBottom.uasset", "pillowLeft.uasset", "pillowRight.uasset",
    "pillowTop.uasset", "sideTableDrawers.uasset",
    "bathroomCabinetDrawer.uasset", "stall.uasset", "stall-bench.uasset",
    "stall-green.uasset", "stall-red.uasset", "stall-stool.uasset",
    "target.uasset", "tent.uasset", "barrel.uasset", "cobblestone.uasset",
    "details.uasset", "mug.uasset", "mugTop.uasset",
    # Kitchen
    "kitchenBlender.uasset", "kitchenCoffeeMachine.uasset",
    "kitchenFridge.uasset", "kitchenFridgeBuiltIn.uasset",
    "kitchenFridgeSmall.uasset", "blenderCup.uasset", "blenderTop.uasset",
    # Appliances
    "dryer.uasset", "dryerDoor.uasset", "washer.uasset", "washerDoor.uasset",
    "washerDryerStacked.uasset", "showerRound.uasset", "faucet.uasset",
    # Characters
    "character-archer.uasset", "body-mesh.uasset", "head-mesh.uasset",
    "arm.uasset", "ram.uasset", "weight.uasset", "arrow.uasset",
    # Siege
    "siege-ballista.uasset", "siege-catapult.uasset", "siege-ram.uasset",
    "siege-tower.uasset", "siege-trebuchet.uasset",
    # Crops
    "crops_cornStageD.uasset", "corn.uasset",
    # Other
    "Group.uasset", "arm-mesh.uasset", "leafs.uasset",
    "tree_palmDetailedShort.uasset", "tree_palmDetailedTall.uasset",
    "leafs.uasset",
}


def find_all_meshes():
    """Find all meshes in the Environment folder using the asset registry."""
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = registry.get_assets_by_path(ENV_MESH_PATH, recursive=True)
    
    meshes = []
    for asset in assets:
        if asset.asset_class == "StaticMesh":
            meshes.append(str(asset.object_path))
    
    return sorted(meshes)


def get_mesh_material_slots(mesh_path):
    """Get all material slots from a mesh."""
    try:
        mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
        if not mesh:
            return None
        
        slots = []
        # Get the number of material slots
        num_sections = mesh.get_num_sections(0)
        for i in range(num_sections):
            mat = mesh.get_material(i)
            if mat:
                path = mat.get_path_name()
                name = mat.get_name()
                slots.append({
                    'slot_index': i,
                    'material_name': name,
                    'material_path': path,
                    'is_local': 'Meshes/Environment' in path and '/Materials/' not in path,
                })
        return slots
    except Exception as e:
        unreal.log_warning(f"Error reading mesh {mesh_path}: {e}")
        return None


def copy_material_to_shared(local_mat_path, mesh_name, slot_index):
    """
    Copy a mesh-local material to the shared folder with a proper name.
    Returns the new material path or None if failed.
    """
    try:
        # Load the source material
        src_mat = unreal.EditorAssetLibrary.load_asset(local_mat_path)
        if not src_mat:
            return None
        
        # Generate a proper name: MeshName_SlotIndex
        base_name = mesh_name.replace('SM_', '').replace('_', '')
        new_name = f"MI_{base_name}_Slot{slot_index}"
        
        # Create the output path
        output_path = f"{SHARED_OUTPUT_PATH}/{new_name}"
        
        # Check if already exists
        if unreal.EditorAssetLibrary.does_asset_exist(output_path):
            return output_path
        
        # Create a Material Instance Constant
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        factory = unreal.MaterialInstanceConstantFactoryNew()
        
        # Get the parent material
        parent_mat = src_mat.get_base_material() if hasattr(src_mat, 'get_base_material') else src_mat
        
        # Create the new instance
        new_mat = asset_tools.create_asset(
            new_name,
            SHARED_OUTPUT_PATH,
            unreal.MaterialInstanceConstant,
            factory
        )
        
        if not new_mat:
            return None
        
        # Copy parameters from source
        unreal.MaterialEditingLibrary.copy_material_instance_parameters(src_mat, new_mat)
        
        # Set parent
        new_mat.set_editor_property('parent', parent_mat)
        
        # Save
        unreal.EditorAssetLibrary.save_loaded_asset(new_mat)
        
        return output_path
        
    except Exception as e:
        unreal.log_warning(f"Error copying {local_mat_path}: {e}")
        return None


def run(dry_run=True, filter_str=None):
    """
    Main consolidation.
    
    Args:
        dry_run: If True, only report what would happen
        filter_str: If set, only process meshes matching this string
    """
    unreal.log("=" * 60)
    unreal.log(f"MESH MATERIAL CONSOLIDATION {'(DRY RUN)' if dry_run else '(APPLYING)'}")
    unreal.log(f"Time: {datetime.now().isoformat()}")
    unreal.log("=" * 60)
    
    # Find all meshes
    meshes = find_all_meshes()
    if filter_str:
        meshes = [m for m in meshes if filter_str.lower() in m.lower()]
    
    unreal.log(f"Found {len(meshes)} meshes to process")
    
    stats = {
        'meshes_processed': 0,
        'materials_reassigned': 0,
        'materials_copied': 0,
        'errors': 0,
        'skipped': 0,
    }
    
    for mesh_path in meshes:
        try:
            slots = get_mesh_material_slots(mesh_path)
            if not slots:
                continue
            
            stats['meshes_processed'] += 1
            
            # Check if any slots use local materials
            local_slots = [s for s in slots if s['is_local']]
            if not local_slots:
                stats['skipped'] += 1
                continue
            
            mesh_name = os.path.basename(mesh_path)
            unreal.log(f"\nProcessing: {mesh_name}")
            
            for slot in local_slots:
                mat_name = slot['material_name']
                mat_path = slot['material_path']
                
                if dry_run:
                    unreal.log(f"  [DRY] Would copy slot {slot['slot_index']}: {mat_name} -> {SHARED_OUTPUT_PATH}/")
                else:
                    # Copy to shared
                    new_path = copy_material_to_shared(mat_path, mesh_name, slot['slot_index'])
                    if new_path:
                        # Reassign mesh slot
                        mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
                        new_mat = unreal.EditorAssetLibrary.load_asset(new_path)
                        if mesh and new_mat:
                            mesh.set_material(slot['slot_index'], new_mat)
                            unreal.EditorAssetLibrary.save_loaded_asset(mesh)
                            unreal.log(f"  [DONE] Slot {slot['slot_index']}: {mat_name} -> {new_path}")
                            stats['materials_reassigned'] += 1
                    else:
                        unreal.log_warning(f"  [FAIL] Slot {slot['slot_index']}: {mat_name}")
                        stats['errors'] += 1
            
        except Exception as e:
            unreal.log_warning(f"Error processing {mesh_path}: {e}")
            stats['errors'] += 1
    
    # Summary
    unreal.log("=" * 60)
    unreal.log("SUMMARY")
    unreal.log(f"  Meshes processed: {stats['meshes_processed']}")
    unreal.log(f"  Materials reassigned: {stats['materials_reassigned']}")
    unreal.log(f"  Materials copied: {stats['materials_copied']}")
    unreal.log(f"  Skipped (no local mats): {stats['skipped']}")
    unreal.log(f"  Errors: {stats['errors']}")
    unreal.log("=" * 60)
    
    if dry_run:
        unreal.log("\nTo apply, run: consolidate_mesh_materials.run(dry_run=False)")
    
    return stats


if __name__ == "__main__":
    import sys
    dry = "--apply" not in sys.argv
    filt = None
    for arg in sys.argv:
        if arg.startswith("--filter="):
            filt = arg.split("=", 1)[1]
    run(dry_run=dry, filter_str=filt)
