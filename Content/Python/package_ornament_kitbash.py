#!/usr/bin/env python3
"""
package_ornament_kitbash.py - Dry-run validation script for SKU #1 Musical Ornament Kitbash

This script performs disk-only validation checks for the Gumroad/FAB marketplace release.
Run without arguments for dry-check mode.

Usage:
    python package_ornament_kitbash.py --dry-check
    python package_ornament_kitbash.py --validate-fbx
    python package_ornament_kitbash.py --check-manifest
"""

import os
import json
from pathlib import Path
from datetime import datetime

# Project paths
PROJECT_ROOT = Path("G:/EnvironmentPortfolio/BS_GodFile")
KITBASH_EXPORT_DIR = PROJECT_ROOT / "KitbashExport" / "MusicalOrnamentalMeshes"
PRODUCT_FBX_DIR = PROJECT_ROOT / "Products" / "MusicalOrnamentKitbash" / "FBX"
PRODUCT_MANIFEST = PROJECT_ROOT / "Products" / "MusicalOrnamentKitbash" / "product_manifest.json"
ORNAMENT_KITBASH_DIR = PROJECT_ROOT / "Products" / "OrnamentKitbash" / "releases"

# Expected meshes from product manifest
EXPECTED_MESHES = [
    "SM_Orn_TrebleClef",
    "SM_Orn_NoteHead",
    "SM_Orn_NoteBeam",
    "SM_Orn_SheetMusicRail",
    "SM_Orn_MusicalCorner",
    "SM_Orn_MusicalDivider",
    "SM_Orn_PearlJewel",
    "SM_Orn_MelodyToken_01",
    "SM_Orn_MelodyToken_02",
    "SM_Orn_MelodyToken_03",
]


def check_fbx_ssot():
    """Verify FBX files exist at both source and staging locations."""
    print("=" * 60)
    print("FBX SSOT (Single Source of Truth) Verification")
    print("=" * 60)
    
    results = {
        "kitbash_export": {"exists": KITBASH_EXPORT_DIR.exists(), "files": []},
        "product_staging": {"exists": PRODUCT_FBX_DIR.exists(), "files": []},
        "status": "PASS"
    }
    
    # Check KitbashExport
    if results["kitbash_export"]["exists"]:
        fbx_files = list(KITBASH_EXPORT_DIR.glob("*.fbx"))
        results["kitbash_export"]["count"] = len(fbx_files)
        for f in sorted(fbx_files):
            results["kitbash_export"]["files"].append(f.name)
            print(f"  [FOUND] {f.name}")
    else:
        results["status"] = "FAIL"
        print(f"  [MISSING] KitbashExport directory")
    
    # Check Product FBX
    if results["product_staging"]["exists"]:
        fbx_files = list(PRODUCT_FBX_DIR.glob("*.fbx"))
        results["product_staging"]["count"] = len(fbx_files)
        for f in sorted(fbx_files):
            results["product_staging"]["files"].append(f.name)
            print(f"  [FOUND] {f.name}")
    else:
        results["status"] = "FAIL"
        print(f"  [MISSING] Product FBX directory")
    
    # Verify expected meshes
    print("\n  Expected Mesh Verification:")
    missing_meshes = []
    for mesh in EXPECTED_MESHES:
        fbx_path = KITBASH_EXPORT_DIR / f"{mesh}.fbx"
        if fbx_path.exists():
            print(f"    [OK] {mesh}.fbx")
        else:
            print(f"    [MISSING] {mesh}.fbx - NOT FOUND")
            missing_meshes.append(mesh)
            results["status"] = "FAIL"
    
    results["missing_meshes"] = missing_meshes
    print(f"\n  Status: {results['status']}")
    return results


def check_manifest():
    """Validate product manifest structure."""
    print("\n" + "=" * 60)
    print("Product Manifest Validation")
    print("=" * 60)
    
    if not PRODUCT_MANIFEST.exists():
        print(f"  [MISSING] Manifest file not found")
        return {"status": "FAIL", "error": "Manifest not found"}
    
    with open(PRODUCT_MANIFEST, 'r') as f:
        manifest = json.load(f)
    
    issues = []
    
    # Check required fields
    required_fields = ["product_id", "name", "mesh_count", "meshes", "ue_paths"]
    for field in required_fields:
        if field in manifest:
            print(f"  [OK] {field}: {manifest.get(field, 'N/A')}")
        else:
            print(f"  [MISSING] {field}: NOT FOUND")
            issues.append(f"Missing field: {field}")
    
    # Verify mesh count matches
    manifest_count = len(manifest.get("meshes", []))
    expected_count = len(EXPECTED_MESHES)
    if manifest_count == expected_count:
        print(f"  [OK] Mesh count matches: {manifest_count}")
    else:
        print(f"  [MISSING] Mesh count mismatch: {manifest_count} vs expected {expected_count}")
        issues.append(f"Mesh count mismatch: {manifest_count}")
    
    status = "PASS" if not issues else "FAIL"
    print(f"\n  Status: {status}")
    return {"status": status, "issues": issues}


def check_validation_reports():
    """Check validation report and quarantine status."""
    print("\n" + "=" * 60)
    print("Validation Report Status Check")
    print("=" * 60)
    
    reports = {
        "release_validation": PROJECT_ROOT / "Docs" / "RELEASE_VALIDATION_REPORT.md",
        "quarantine": PROJECT_ROOT / "Docs" / "DUPE_ROOT_QUARANTINE_2026-07.md"
    }
    
    results = {"status": "PASS", "unchanged": []}
    
    for name, path in reports.items():
        if path.exists():
            stat = path.stat()
            mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d")
            print(f"  [{name}] Last modified: {mod_time}")
            # Check if unchanged since prior audit (both dated 2026-07-17)
            if "2026-07" in mod_time:
                results["unchanged"].append(name)
        else:
            print(f"  [{name}] NOT FOUND")
            results["status"] = "WARN"
    
    print(f"\n  Status: {results['status']}")
    print(f"  Reports unchanged: {', '.join(results['unchanged']) if results['unchanged'] else 'None'}")
    return results


def check_screenshot_readiness():
    """Check screenshot shot-list compliance."""
    print("\n" + "=" * 60)
    print("Screenshot Shot-List Checklist (6 Items)")
    print("=" * 60)
    
    results = {"shots_verified": [], "shots_missing": []}
    
    # Check if SDF masters exist for each shot
    sdf_dir = PROJECT_ROOT / "Content" / "_PROJECT" / "04_Materials" / "SDF"
    
    shot_patterns = {
        "Mandelbulb": ["M_SDF_Mandelbulb_Master", "M_SDF_MandelbulbSlice"],
        "Penrose Staircase": ["M_SDF_Penrose_Staircase"],
        "Gothic Rose Window": ["M_SDF_RoseWindow", "M_SDF_GothicRoseWindow"],
        "Julia Set": ["M_SDF_JuliaSet_Quaternion"],
        "Klein Bottle": ["M_SDF_Klein_Bottle"],
        "Menger Sponge": ["M_SDF_MengerSponge"]
    }
    
    for shot, patterns in shot_patterns.items():
        found = any((sdf_dir / f"{p}.uasset").exists() for p in patterns)
        if found:
            results["shots_verified"].append(shot)
            print(f"  [OK] {shot}")
        else:
            results["shots_missing"].append(shot)
            print(f"  [MISSING] {shot} - MATERIAL NOT FOUND")
    
    results["status"] = "PASS" if not results["shots_missing"] else "PARTIAL"
    print(f"\n  Status: {results['status']}")
    return results


def main():
    """Run all dry-check validations."""
    print("SKU #1 Musical Ornament Kitbash - Dry Check Validation")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    all_results = {
        "fbx_ssot": check_fbx_ssot(),
        "manifest": check_manifest(),
        "validation_reports": check_validation_reports(),
        "screenshot_readiness": check_screenshot_readiness()
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    all_pass = all(r.get("status") in ["PASS", "WARN"] for r in all_results.values())
    print(f"\n  Overall Status: {'PASS' if all_pass else 'FAIL'}")
    print(f"\n  FBX SSOT: {all_results['fbx_ssot']['status']}")
    print(f"  Manifest: {all_results['manifest']['status']}")
    print(f"  Reports Unchanged: {len(all_results['validation_reports']['unchanged'])} (as expected)")
    print(f"  Screenshots Ready: {len(all_results['screenshot_readiness']['shots_verified'])}/6")
    
    return 0 if all_pass else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())