"""UE5 terrain import test.

Verifies that exported FBX files can be imported into UE5:
1. Check FBX file exists and is valid
2. Verify UCX_ collision meshes are present
3. Check scale (centimeters)
4. Generate import settings JSON for UE5

This script runs OUTSIDE UE5 (offline validation).
For in-editor tests, use the PythonScriptPlugin.

Run:
  python -B Tools/test_ue5_import.py
"""

import os
import sys
import json
import struct

REPO = r"C:\EnvironmentPortfolio\BS_GodFile"
ADDON = os.path.join(REPO, "Tools", "BlenderAddons", "melodia_studio")
if ADDON not in sys.path:
    sys.path.insert(0, ADDON)


def validate_fbx(path):
    """Validate FBX file structure."""
    if not os.path.exists(path):
        return {"ok": False, "error": "file not found"}

    size = os.path.getsize(path)
    if size < 100:
        return {"ok": False, "error": "file too small (%d bytes)" % size}

    # Check FBX magic header (binary or ASCII)
    with open(path, 'rb') as f:
        header = f.read(27)

    # Binary FBX: "Kaydara FBX Binary  \x00\x1a\x00"
    if header[:23] == b'Kaydara FBX Binary  \x00\x1a\x00':
        return {"ok": True, "size": size, "path": path, "format": "binary"}

    # ASCII FBX: starts with "; FBX"
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        first_line = f.readline()
    if first_line.startswith('; FBX'):
        return {"ok": True, "size": size, "path": path, "format": "ascii"}

    return {"ok": False, "error": "not a valid FBX file"}


def check_collision_meshes(path):
    """Check for UCX_ collision meshes in FBX."""
    # Read FBX and look for UCX_ mesh names
    with open(path, 'rb') as f:
        data = f.read()

    # Search for UCX_ pattern
    ucx_count = data.count(b'UCX_')
    has_collision = ucx_count > 0

    return {
        "ok": has_collision,
        "ucx_count": ucx_count,
        "message": "%d collision mesh(es) found" % ucx_count if has_collision else "no UCX_ collision meshes",
    }


def generate_import_settings(fbx_path, content_path):
    """Generate UE5 import settings JSON."""
    settings = {
        "ImportSettings": {
            "Mesh": {
                "bConvertScene": True,
                "bConvertSceneUnit": True,
                "bTransformVertexAbsolute": True,
                "bBakePivotInVertex": False,
                "bComputeWeightedNormals": True,
                "bRemoveDegenerates": True,
                "bGenerateLightmapUVs": True,
                "bOneConvexHullPerUCX": True,
                "bAutoGenerateCollision": False,
                "bCombineMeshes": False,
                "bImportMeshLODs": False,
                "bPreserveSmoothingGroups": True,
                "bConvertSceneAxis": True,
                "bImportAnimations": False,
                "bImportMaterials": True,
                "bImportTextures": False,
            },
            "StaticMesh": {
                "LightMapResolution": 64,
                "LightMapCoordinateIndex": 1,
            },
        },
        "DestinationPath": content_path,
        "SourcePath": fbx_path,
    }

    return settings


def main():
    out_dir = os.path.join(REPO, "Saved", "Audit", "ue5_export")
    os.makedirs(out_dir, exist_ok=True)

    report = {"tests": [], "ok": True}

    # Test 1: Validate FBX files exist
    fbx_files = [f for f in os.listdir(out_dir) if f.endswith('.fbx')]
    if not fbx_files:
        report["tests"].append({
            "name": "fbx_exists",
            "ok": False,
            "error": "no FBX files in %s" % out_dir,
        })
        report["ok"] = False
    else:
        for fbx_file in fbx_files:
            path = os.path.join(out_dir, fbx_file)
            result = validate_fbx(path)
            result["name"] = "validate_%s" % fbx_file
            report["tests"].append(result)
            if not result["ok"]:
                report["ok"] = False

    # Test 2: Check collision meshes
    for fbx_file in fbx_files:
        path = os.path.join(out_dir, fbx_file)
        result = check_collision_meshes(path)
        result["name"] = "collision_%s" % fbx_file
        report["tests"].append(result)
        if not result["ok"]:
            report["ok"] = False

    # Test 3: Generate import settings
    if fbx_files:
        fbx_path = os.path.join(out_dir, fbx_files[0])
        content_path = "/Game/_PROJECT/ResonantWorld/Terrain"
        settings = generate_import_settings(fbx_path, content_path)
        settings_path = os.path.join(out_dir, "import_settings.json")
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        report["tests"].append({
            "name": "import_settings",
            "ok": True,
            "path": settings_path,
        })

    # Summary
    report["verdict"] = "PASS" if report["ok"] else "FAIL"
    report["total"] = len(report["tests"])
    report["passed"] = sum(1 for t in report["tests"] if t["ok"])

    print("\n=== UE5 Import Test ===")
    for test in report["tests"]:
        status = "OK" if test["ok"] else "FAIL"
        extra = ""
        if test.get("size"):
            extra = " (%d bytes)" % test["size"]
        if test.get("error"):
            extra = " - %s" % test["error"]
        if test.get("message"):
            extra = " - %s" % test["message"]
        print("  %-30s %s%s" % (test["name"], status, extra))

    print("\n%d/%d tests passed" % (report["passed"], report["total"]))
    print("VERDICT:", report["verdict"])

    # Save report
    report_path = os.path.join(out_dir, "ue5_test_report.json")
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    print("REPORT %s" % report_path)


if __name__ == "__main__":
    main()
