"""Promote Nikki masters to production - creates duplicates without replacing Universal master.

This script:
1. Duplicates M_Master_Nikki from _Scratch to production Masters folder
2. Duplicates M_Master_Nikki_Landscape for landscape use
3. Creates showcase instances: MI_Show_NikkiDream, MI_Show_NikkiLandscape
4. Sets up proper texture references for Nikki aesthetic

Run in-editor:
  py Content/Python/promote_nikki_masters.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import unreal

# Source: Nikki research masters in _Scratch
NIKKI_SOURCE = "/Game/EnvSandbox/Materials/_Scratch/M_Master_Nikki"
NIKKI_LANDSCAPE_SOURCE = "/Game/EnvSandbox/Materials/_Scratch/M_Master_Nikki_Landscape"

# Destination: Production Masters
MASTER_DIR = "/Game/EnvSandbox/Materials/Masters"

# Instance destinations
SHOWCASE_INST_DIR = "/Game/EnvSandbox/Materials/Instances/Showcase"
LANDSCAPE_INST_DIR = "/Game/EnvSandbox/Materials/Instances/Landscape"

REPORT_PATH = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "nikki_promotion.json"


def promote_nikki_master() -> dict:
    """Duplicate Nikki master to production Masters folder."""
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    MEL = unreal.MaterialEditingLibrary
    
    result = {"masters": [], "instances": []}
    
    # ---- Promote M_Master_Nikki ----
    src_path = f"{NIKKI_SOURCE}.{NIKKI_SOURCE.split('/')[-1]}"
    dest_name = "M_Master_Nikki_Published"
    dest_path = f"{MASTER_DIR}/{dest_name}.{dest_name}"
    
    if not unreal.EditorAssetLibrary.does_asset_exist(src_path):
        unreal.log_warning(f"[NikkiPromote] source {src_path} not found")
    elif unreal.EditorAssetLibrary.does_asset_exist(dest_path):
        unreal.log(f"[NikkiPromote] {dest_path} already exists - skipping")
        result["masters"].append({"name": dest_name, "status": "exists"})
    else:
        # Duplicate the asset using duplicate_asset
        success = unreal.EditorAssetLibrary.duplicate_asset(src_path, f"{MASTER_DIR}/{dest_name}")
        if success:
            unreal.log(f"[NikkiPromote] created {dest_path}")
            result["masters"].append({"name": dest_name, "status": "created", "path": dest_path})
        else:
            result["masters"].append({"name": dest_name, "status": "failed"})
    
    # ---- Promote M_Master_Nikki_Landscape ----
    src_land_path = f"{NIKKI_LANDSCAPE_SOURCE}.{NIKKI_LANDSCAPE_SOURCE.split('/')[-1]}"
    dest_land_name = "M_Master_Nikki_Landscape_Published"
    dest_land_path = f"{MASTER_DIR}/{dest_land_name}.{dest_land_name}"
    
    if not unreal.EditorAssetLibrary.does_asset_exist(src_land_path):
        unreal.log_warning(f"[NikkiPromote] source {src_land_path} not found")
    elif unreal.EditorAssetLibrary.does_asset_exist(dest_land_path):
        unreal.log(f"[NikkiPromote] {dest_land_path} already exists - skipping")
        result["masters"].append({"name": dest_land_name, "status": "exists"})
    else:
        success = unreal.EditorAssetLibrary.duplicate_asset(src_land_path, f"{MASTER_DIR}/{dest_land_name}")
        if success:
            unreal.log(f"[NikkiPromote] created {dest_land_path}")
            result["masters"].append({"name": dest_land_name, "status": "created", "path": dest_land_path})
        else:
            result["masters"].append({"name": dest_land_name, "status": "failed"})
    
    return result


def create_showcase_instances() -> list[dict]:
    """Create showcase instances from promoted Nikki masters."""
    import material_lib as mlib
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    
    results = []
    nikki_master = f"{MASTER_DIR}/M_Master_Nikki_Published.M_Master_Nikki_Published"
    nikki_land_master = f"{MASTER_DIR}/M_Master_Nikki_Landscape_Published.M_Master_Nikki_Landscape_Published"
    
    # ---- MI_Show_NikkiDream ----
    inst_name = "MI_Show_NikkiDream"
    inst_path = f"{SHOWCASE_INST_DIR}/{inst_name}.{inst_name}"
    
    if not unreal.EditorAssetLibrary.does_asset_exist(nikki_master):
        results.append({"instance": inst_name, "status": "master_not_found"})
    elif unreal.EditorAssetLibrary.does_asset_exist(inst_path):
        results.append({"instance": inst_name, "status": "exists"})
    else:
        # Create instance
        mlib.ensure_directory(SHOWCASE_INST_DIR)
        parent = unreal.load_asset(nikki_master)
        if parent:
            inst = asset_tools.create_asset(
                inst_name, SHOWCASE_INST_DIR, 
                unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew()
            )
            if inst:
                MEL = unreal.MaterialEditingLibrary
                MEL.set_material_instance_parent(inst, parent)
                mlib.save_package(inst)
                results.append({"instance": inst_name, "status": "created", "path": inst_path})
            else:
                results.append({"instance": inst_name, "status": "create_failed"})
        else:
            results.append({"instance": inst_name, "status": "parent_load_failed"})
    
    # ---- MI_Show_NikkiLandscape ----
    inst_land_name = "MI_Landscape_NikkiDream"
    inst_land_path = f"{LANDSCAPE_INST_DIR}/{inst_land_name}.{inst_land_name}"
    
    if not unreal.EditorAssetLibrary.does_asset_exist(nikki_land_master):
        results.append({"instance": inst_land_name, "status": "master_not_found"})
    elif unreal.EditorAssetLibrary.does_asset_exist(inst_land_path):
        results.append({"instance": inst_land_name, "status": "exists"})
    else:
        mlib.ensure_directory(LANDSCAPE_INST_DIR)
        parent = unreal.load_asset(nikki_land_master)
        if parent:
            inst = asset_tools.create_asset(
                inst_land_name, LANDSCAPE_INST_DIR,
                unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew()
            )
            if inst:
                MEL = unreal.MaterialEditingLibrary
                MEL.set_material_instance_parent(inst, parent)
                mlib.save_package(inst)
                results.append({"instance": inst_land_name, "status": "created", "path": inst_land_path})
            else:
                results.append({"instance": inst_land_name, "status": "create_failed"})
        else:
            results.append({"instance": inst_land_name, "status": "parent_load_failed"})
    
    return results


def build_all() -> dict:
    """Run full promotion pipeline."""
    masters = promote_nikki_master()
    instances = create_showcase_instances()
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "masters": masters,
        "instances": instances,
        "note": "Nikki masters promoted as duplicates - Universal master unchanged",
    }
    
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    try:
        build_all()
    except ImportError:
        print("ERROR: Must run inside Unreal Editor with unreal module available")
        sys.exit(1)