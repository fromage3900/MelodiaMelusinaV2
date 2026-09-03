# consolidate_env_materials.py
# Run from UE editor console: py Content/Python/consolidate_env_materials.py
"""
Environment Mesh Material Consolidation

Usage:
    # Dry run first:
    import consolidate_env_materials; consolidate_env_materials.dry_run()
    
    # Apply:
    import consolidate_env_materials; consolidate_env_materials.apply()
    
    # Consolidate specific mesh type:
    import consolidate_env_materials; consolidate_env_materials.dry_run(filter='wall')
"""

import unreal
import os
from collections import defaultdict
from datetime import datetime

ENV_MESH_DIR = "C:/EnvironmentPortfolio/BS_GodFile/Content/EnvSandbox/Meshes/Environment"
ENV_MESH_GAME = "/Game/EnvSandbox/Meshes/Environment"

# Safe deletions (junk files, no references possible)
JUNK_FILES = {'__ignore_.uasset', '_defaultMat.uasset'}


def find_mesh_folders():
    """Find all mesh folders that contain .uasset files."""
    folders = []
    for item in os.listdir(ENV_MESH_DIR):
        item_path = os.path.join(ENV_MESH_DIR, item)
        if os.path.isdir(item_path):
            # Check if it has .uasset files
            has_uasset = any(f.endswith('.uasset') for f in os.listdir(item_path))
            if has_uasset:
                folders.append(item)
    return sorted(folders)


def get_local_materials(mesh_folder):
    """Get all mesh-local material files in a mesh folder."""
    materials = []
    mesh_path = os.path.join(ENV_MESH_DIR, mesh_folder)
    for f in os.listdir(mesh_path):
        if f.endswith('.uasset'):
            full = os.path.join(mesh_path, f)
            size = os.path.getsize(full)
            materials.append({
                'filename': f,
                'full_path': full,
                'size': size,
                'is_junk': f in JUNK_FILES,
                'is_colormap': f == 'colormap.uasset',
            })
    
    # Also check Materials/ subfolder
    sub_mat_path = os.path.join(mesh_path, 'Materials')
    if os.path.exists(sub_mat_path):
        for f in os.listdir(sub_mat_path):
            if f.endswith('.uasset'):
                full = os.path.join(sub_mat_path, f)
                size = os.path.getsize(full)
                materials.append({
                    'filename': f,
                    'full_path': full,
                    'size': size,
                    'is_junk': f in JUNK_FILES,
                    'is_colormap': f == 'colormap.uasset',
                })
    
    return materials


def delete_material_files(mesh_folder, materials):
    """Delete material files from a mesh folder."""
    deleted = []
    errors = []
    for mat in materials:
        try:
            os.remove(mat['full_path'])
            deleted.append(mat['full_path'])
            # Also delete .uexp and .ubulk
            for ext in ['.uexp', '.ubulk']:
                sidecar = mat['full_path'].replace('.uasset', ext)
                if os.path.exists(sidecar):
                    os.remove(sidecar)
        except Exception as e:
            errors.append((mat['full_path'], str(e)))
    return deleted, errors


def run(dry_run=True, filter_str=None):
    """
    Main consolidation.
    
    Args:
        dry_run: If True, only report what would happen
        filter_str: If set, only process mesh folders containing this string
    """
    unreal.log("=" * 60)
    unreal.log(f"ENV MESH MATERIAL CONSOLIDATION {'(DRY RUN)' if dry_run else '(APPLYING)'}")
    unreal.log(f"Time: {datetime.now().isoformat()}")
    unreal.log("=" * 60)
    
    mesh_folders = find_mesh_folders()
    if filter_str:
        mesh_folders = [f for f in mesh_folders if filter_str.lower() in f.lower()]
    
    unreal.log(f"Processing {len(mesh_folders)} mesh folders")
    
    stats = {
        'folders_processed': 0,
        'junk_deleted': 0,
        'colormaps_found': 0,
        'colormaps_deleted': 0,
        'mesh_mats_found': 0,
        'mesh_mats_deleted': 0,
        'errors': 0,
        'total_size_freed': 0,
    }
    
    for folder in mesh_folders:
        materials = get_local_materials(folder)
        if not materials:
            continue
        
        stats['folders_processed'] += 1
        
        for mat in materials:
            try:
                if mat['is_junk']:
                    if dry_run:
                        unreal.log(f"  [JUNK] {folder}/{mat['filename']} ({mat['size']/1024:.0f}KB)")
                    else:
                        os.remove(mat['full_path'])
                        stats['junk_deleted'] += 1
                        stats['total_size_freed'] += mat['size']
                        
                elif mat['is_colormap']:
                    stats['colormaps_found'] += 1
                    if dry_run:
                        unreal.log(f"  [COLORMAP] {folder}/{mat['filename']} ({mat['size']/1024:.0f}KB)")
                    else:
                        # NOTE: Deleting colormaps requires reassigning mesh material slot first
                        # For now, just report
                        unreal.log_warning(f"  [COLORMAP] {folder}/{mat['filename']} - requires material slot reassignment")
                        
                else:
                    stats['mesh_mats_found'] += 1
                    if dry_run:
                        unreal.log(f"  [MESH-MAT] {folder}/{mat['filename']} ({mat['size']/1024:.0f}KB)")
                    else:
                        # NOTE: Same issue - need to reassign mesh slot
                        unreal.log_warning(f"  [MESH-MAT] {folder}/{mat['filename']} - requires material slot reassignment")
                        
            except Exception as e:
                unreal.log_warning(f"  ERROR: {folder}/{mat['filename']}: {e}")
                stats['errors'] += 1
    
    # Summary
    unreal.log("=" * 60)
    unreal.log("SUMMARY")
    unreal.log(f"  Folders processed: {stats['folders_processed']}")
    unreal.log(f"  Junk files {'would be ' if dry_run else ''}deleted: {stats['junk_deleted']}")
    unreal.log(f"  Colormaps found: {stats['colormaps_found']}")
    unreal.log(f"  Mesh-specific mats found: {stats['mesh_mats_found']}")
    unreal.log(f"  Size freed: {stats['total_size_freed']/1024/1024:.1f}MB")
    unreal.log(f"  Errors: {stats['errors']}")
    unreal.log("=" * 60)
    
    if dry_run:
        unreal.log("\nTo apply changes, run: consolidate_env_materials.run(dry_run=False)")
    
    return stats


# Convenience functions
def dry_run(filter=None):
    return run(dry_run=True, filter_str=filter)

def apply(filter=None):
    return run(dry_run=False, filter_str=filter)


if __name__ == "__main__":
    import sys
    dry = "--apply" not in sys.argv
    filt = None
    for arg in sys.argv:
        if arg.startswith("--filter="):
            filt = arg.split("=", 1)[1]
    run(dry_run=dry, filter_str=filt)
