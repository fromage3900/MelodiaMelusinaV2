"""
Animation import pre-flight validator.

Usage:
    python Tools/animation_import_pipeline/validate_source.py <fbx_path> [<manifest_path>]

Validates an FBX against its sidecar manifest before any UE import.
Returns exit code 0 = pass, 1 = fail with reasons.
"""

import json
import os
import sys
import subprocess
import tempfile
import shutil

REQUIRED_FPS = 30
REQUIRED_SKELETON_PREFIX = "SK_Source_Melusina"
MIN_BONE_COUNT = 400
MAX_BONE_COUNT = 500


def validate_manifest_schema(manifest: dict) -> list[str]:
    if manifest.get("schema_version") == 2:
        pipeline_dir = os.path.dirname(__file__)
        if pipeline_dir not in sys.path:
            sys.path.insert(0, pipeline_dir)
        from manifest_v2 import validate_v2
        return validate_v2(manifest)
    errors = []
    required = ["schema_version", "clip_id", "context", "expected_skeleton",
                 "fps", "root_motion", "loop", "start_frame", "end_frame", "consumer"]
    for key in required:
        if key not in manifest:
            errors.append(f"Missing required field: {key}")
    if manifest.get("fps") != REQUIRED_FPS:
        errors.append(f"FPS must be {REQUIRED_FPS}, got {manifest.get('fps')}")
    if manifest.get("root_motion") not in ("in_place", "root"):
        errors.append(f"root_motion must be 'in_place' or 'root', got {manifest.get('root_motion')}")
    if manifest.get("start_frame", 0) > manifest.get("end_frame", 0):
        errors.append(f"start_frame ({manifest.get('start_frame')}) > end_frame ({manifest.get('end_frame')})")
    return errors


def validate_fbx_with_blender(fbx_path: str) -> list[str]:
    """Run scan_cascadeur_fbx.py on the FBX if Blender is available."""
    errors = []
    blender = os.environ.get("BLENDER_EXE") or shutil.which("blender")
    if not blender:
        known_windows = os.path.join(
            os.environ.get("PROGRAMFILES", r"C:\Program Files"),
            "Blender Foundation", "Blender 5.2", "blender.exe"
        )
        blender = known_windows if os.path.isfile(known_windows) else "blender"
    scanner = os.path.join(os.path.dirname(__file__), "..", "scan_cascadeur_fbx.py")
    scanner = os.path.normpath(scanner)

    if not os.path.exists(scanner):
        errors.append(f"Scanner not found at {scanner} - install Blender + scan_cascadeur_fbx.py")
        return errors

    report_path = os.path.join(
        tempfile.gettempdir(),
        f"mual_fbx_preflight_{abs(hash(os.path.abspath(fbx_path)))}.json",
    )
    try:
        completed = subprocess.run(
            [blender, "--background", "--python", scanner, "--", fbx_path, report_path],
            capture_output=True, text=True, timeout=120
        )
        if completed.returncode != 0:
            errors.append(
                "Blender scan failed: "
                + (completed.stderr.strip() or completed.stdout.strip() or f"exit {completed.returncode}")
            )
        elif os.path.exists(report_path):
            with open(report_path) as f:
                report = json.load(f)
            if not report.get("has_armature", bool(report.get("armatures"))):
                errors.append("FBX has no armature")
            if report.get("fps") != REQUIRED_FPS:
                errors.append(f"FBX FPS is {report.get('fps')}, expected {REQUIRED_FPS}")
            missing = report.get("missing_bones", report.get("missing_required_bones", []))
            if missing:
                errors.append(f"Missing required bones: {missing[:10]}...")
        else:
            errors.append("Blender scan produced no report")
    except FileNotFoundError:
        errors.append("Blender not found - set BLENDER_EXE env var or install Blender")
    except subprocess.TimeoutExpired:
        errors.append("Blender scan timed out (120s)")
    return errors


def validate_metadata(fbx_path: str, manifest: dict) -> list[str]:
    errors = []
    file_size = os.path.getsize(fbx_path)
    if file_size < 1000:
        errors.append(f"FBX too small: {file_size} bytes")
    start = manifest.get("frame_start", manifest.get("start_frame", 0))
    end = manifest.get("frame_end", manifest.get("end_frame", 0))
    if end - start < 2:
        errors.append(f"Animation range too short: {start}-{end}")
    return errors


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_source.py <fbx_path> [<manifest_path>]")
        sys.exit(1)

    fbx_path = sys.argv[1]
    manifest_path = sys.argv[2] if len(sys.argv) > 2 else fbx_path.replace(".fbx", ".manifest.json")

    if not os.path.exists(fbx_path):
        print(f"FAIL: FBX not found: {fbx_path}")
        sys.exit(1)

    if not os.path.exists(manifest_path):
        print(f"FAIL: Manifest not found: {manifest_path}")
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    all_errors = []
    all_errors += validate_manifest_schema(manifest)
    all_errors += validate_metadata(fbx_path, manifest)
    all_errors += validate_fbx_with_blender(fbx_path)

    if all_errors:
        print(f"FAIL: {len(all_errors)} pre-flight error(s):")
        for e in all_errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("PASS: All pre-flight checks passed")
        print(f"  Clip: {manifest.get('clip_id', 'unknown')}")
        print(f"  FPS: {manifest.get('fps')}")
        print(f"  Root motion: {manifest.get('root_motion')}")
        start = manifest.get("frame_start", manifest.get("start_frame"))
        end = manifest.get("frame_end", manifest.get("end_frame"))
        print(f"  Frames: {start}-{end}")
        print(f"  Context: {manifest.get('context')}")
        sys.exit(0)


if __name__ == "__main__":
    main()
