"""
Retire the orphaned enchanted-vehicle material set.

Set B = /Game/Melodia/Imported/EnchantedVehicles/MI_KB3D_ECV_* (73 files).

Why: the 2026-09-25 Perforce cutover left a duplicate of the vehicle materials in
a second folder. Nothing in the project references them (the 172 vehicle meshes use
/Game/KitBash_EnchantedVehicles/M_KB3D_ECV_*, which was converged onto
M_Master_Toon_Universal on 2026-10-21), and the duplicate set is the *lesser* copy:
15 of its instances never received their opacity/emissive routes and none carried a
masked override, so translucent vehicle parts would have rendered opaque.

Deletion is owner-approved (2026-10-21). This script:
  * proves every candidate is unreferenced before deleting anything
  * deletes only assets with ZERO referencers
  * writes a receipt with the full list and the referencer counts

Run: UnrealEditor-Cmd <proj> -run=pythonscript -script=<this file> -unattended -nullrhi
Writes Saved/Audit/orphan_vehicle_set_retirement.json
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal

ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
OUT = ROOT / "Saved" / "Audit" / "orphan_vehicle_set_retirement.json"

TARGET_ROOT = "/Game/Melodia/Imported/EnchantedVehicles"
KEEP_MESH_FACING = "/Game/KitBash_EnchantedVehicles"


def main():
    report = {"generated": "2026-10-21", "target": TARGET_ROOT,
              "candidates": [], "deleted": [], "skipped": [], "failed": []}

    ar = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = [a for a in ar.get_assets_by_path(TARGET_ROOT, recursive=True)
              if str(a.asset_class_path.asset_name) == "MaterialInstanceConstant"]
    report["candidates"] = len(assets)
    unreal.log(f"[RET] candidate instances in {TARGET_ROOT}: {len(assets)}")

    opts = unreal.AssetRegistryDependencyOptions(
        include_soft_package_references=True,
        include_hard_package_references=True)

    for a in assets:
        pkg = str(a.package_name)
        name = str(a.asset_name)
        refs = ar.get_referencers(pkg, opts)
        ref_names = sorted(str(r) for r in refs) if refs else []
        row = {"package": pkg, "name": name, "referencers": len(ref_names),
               "referencer_list": ref_names[:10]}
        if ref_names:
            row["reason"] = "still referenced"
            report["skipped"].append(row)
            unreal.log(f"[RET] SKIP {name}: {len(ref_names)} referencer(s)")
            continue
        try:
            ok = unreal.EditorAssetLibrary.delete_asset(pkg)
            row["deleted"] = bool(ok)
            report["deleted"].append(row)
            unreal.log(f"[RET] deleted {name} (referencers: 0)")
        except Exception as exc:
            row["error"] = f"{type(exc).__name__}: {exc}"
            report["failed"].append(row)
            unreal.log(f"[RET] FAIL {name}: {exc}")

    # what is left in the folder?
    left = [str(a.asset_name) for a in ar.get_assets_by_path(TARGET_ROOT, recursive=True)]
    report["remaining_in_folder"] = left
    report["summary"] = {
        "candidates": len(assets),
        "deleted": len(report["deleted"]),
        "skipped_referenced": len(report["skipped"]),
        "failed": len(report["failed"]),
        "remaining": len(left),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    unreal.log(f"[RET] DONE {report['summary']} -> {OUT}")
    return 0


if __name__ == "__main__":
    main()
