"""Audit instance appliers health."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

REPORT = Path(__file__).resolve().parents[2] / "Saved" / "Audit" / "instance_appliers.json"
INSTANCE_APPLIERS = "/Game/EnvSandbox/InstanceAppliers"

def main() -> dict:
    try:
        unreal.AssetRegistryHelpers.get_asset_registry().search_all_assets(True)
    except Exception:
        pass
    
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "instance_appliers_exists": unreal.EditorAssetLibrary.does_directory_exist(INSTANCE_APPLIERS),
        "params": {},
        "all_ok": False,
    }
    
    if report["instance_appliers_exists"]:
        instance_applier_files = unreal.EditorAssetLibrary.list_assets(INSTANCE_APPLIERS, recursive=True)
        
        for file in instance_applier_files:
            asset = unreal.load_asset(file)
            
            if not isinstance(asset, unreal.InstanceType):
                continue
                
            report["params"][file] = {
                "class": str(type(asset)),
                "has_valid_references": asset.has_valid_references(),
                "is_loaded": unreal.is_asset_registered(file),
            }
            
    report["all_ok"] = (
        report["instance_appliers_exists"]
        and all(report.get("params", {}).values())
    )
    
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    
    return report

if __name__ == "__main__":
    main()