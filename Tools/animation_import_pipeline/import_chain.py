"""
Additive retarget pipeline: public source -> validated -> retargeted -> staged.

Usage:
    python Tools/animation_import_pipeline/import_chain.py <fbx_path> [--manifest <path>] [--dry-run]

Runs pre-flight, imports FBX onto source skeleton, batch-retargets to
Melusina skeleton, validates post-import contract. All assets land in
staging paths -- never touches the working rig.

Requires:
    1. Monolith MCP running on localhost:9316
    2. IK Source/Retargeter pair already created (see pipeline README)
    3. FBX + .manifest.json pair
"""

import json
import os
import sys
import subprocess
import urllib.request
import urllib.error

from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
if str(PIPELINE_DIR) not in sys.path:
    sys.path.insert(0, str(PIPELINE_DIR))
from manifest_v2 import (  # noqa: E402
    CANONICAL_SKELETON_PATH,
    RETARGET_PROFILE,
    TARGET_MESH_PATH,
    TARGET_SKELETON_PATH,
    load_as_v2,
    validate_v2,
)

MCP_URL = "http://localhost:9316/mcp"
SOURCE_SKELETON_PATH = "/Game/Melodia/Mocap/Source/SK_Source_Melusina.SK_Source_Melusina"
TARGET_MESH = TARGET_MESH_PATH + ".SK_Melusina"
RTG_SOURCE_TO_MELUSINA = "/Game/Melodia/Characters/Melusina/RTG_Source_to_Melusina.RTG_Source_to_Melusina"
STAGING_DEST = "/Game/Melodia/Characters/Melusina/Animations/SourceRetargeted"


def mcp_call(method: str, params: dict) -> dict:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(MCP_URL, data=body, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        return json.loads(resp.read())
    except urllib.error.URLError as e:
        return {"result": {"isError": True, "content": [{"text": str(e)}]}}


def mcp_result_ok(raw: dict) -> bool:
    return not raw.get("result", {}).get("isError", False)


def mcp_text(raw: dict) -> str:
    return raw.get("result", {}).get("content", [{}])[0].get("text", "")


def validate(fbx_path: str, manifest_path: str) -> bool:
    validator = os.path.join(os.path.dirname(__file__), "validate_source.py")
    result = subprocess.run(
        [sys.executable, validator, fbx_path, manifest_path],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        return False
    return True


def import_fbx_as_anim(fbx_path: str, dest_name: str) -> str | None:
    """Import FBX as animation onto the source skeleton in staging path."""
    # Keep the import path explicit.  Unreal otherwise infers a skeleton from
    # the FBX, which is precisely how foreign/UAL1 clips used to bypass the
    # canonical source-rig lane.
    filename = json.dumps(os.path.abspath(fbx_path).replace("\\", "/"))
    destination = json.dumps(STAGING_DEST)
    name = json.dumps(dest_name)
    source_skeleton = json.dumps(SOURCE_SKELETON_PATH)
    resp = mcp_call("tools/call", {
        "name": "editor_query",
        "arguments": {
            "action": "run_python",
            "command": (
                "import unreal;"
                "t=unreal.AssetImportTask();"
                't.set_editor_property("filename",' + filename + ');'
                't.set_editor_property("destination_path",' + destination + ');'
                't.set_editor_property("destination_name",' + name + ');'
                "t.set_editor_property(\"replace_existing\",True);"
                "t.set_editor_property(\"save\",True);"
                "t.set_editor_property(\"automated\",True);"
                "o=unreal.FbxImportUI();"
                "o.set_editor_property(\"import_mesh\",False);"
                "o.set_editor_property(\"import_as_skeletal\",True);"
                "o.set_editor_property(\"import_animations\",True);"
                "o.set_editor_property(\"import_materials\",False);"
                "o.set_editor_property(\"import_textures\",False);"
                'o.set_editor_property("skeleton",unreal.load_object(None,' + source_skeleton + '));'
                "t.set_editor_property(\"options\",o);"
                "unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);"
                'p=t.get_editor_property("imported_object_paths");'
                'print("PATHS:"+str(p))'
            )
        }
    })
    text = mcp_text(resp)
    if "PATHS:" in text:
        paths_str = text.split("PATHS:")[1].strip()
        try:
            paths = json.loads(paths_str.replace("'", "\""))
            if paths:
                print(f"  Imported: {paths[0]}")
                return paths[0]
        except json.JSONDecodeError:
            pass
    print(f"  Import returned no assets for {dest_name}")
    return None


def retarget(source_asset: str, retargeter_path: str) -> str | None:
    """Batch retarget from source skeleton to Melusina skeleton."""
    resp = mcp_call("tools/call", {
        "name": "animation_query",
        "arguments": {
            "action": "batch_retarget_animations",
            "retargeter_path": retargeter_path,
            "source_anims": [source_asset],
            "target_mesh": TARGET_MESH,
            "output_folder": STAGING_DEST
        }
    })
    if not mcp_result_ok(resp):
        print(f"  Retarget failed: {mcp_text(resp)}")
        return None
    result = json.loads(mcp_text(resp))
    created = result.get("created_assets", [])
    if created:
        print(f"  Retargeted: {created[0]}")
        return created[0]
    print(f"  Retarget created no assets (maybe already exists)")
    return None


def set_looping(asset_path: str, should_loop: bool) -> bool:
    """Set looping flag on a retargeted animation sequence."""
    resp = mcp_call("tools/call", {
        "name": "editor_query",
        "arguments": {
            "action": "run_python",
            "command": (
                "import unreal;"
                'seq=unreal.load_asset("' + asset_path + '");'
                "seq.set_editor_property(\"is_looping\"," + ("True" if should_loop else "False") + ");"
                "unreal.EditorAssetLibrary.save_loaded_asset(seq);"
                'print("Loops:"+str(seq.get_editor_property("is_looping")))'
            )
        }
    })
    return mcp_result_ok(resp)


def verify(asset_path: str) -> bool:
    """Post-import: confirm retargeted animation has SK_Melusina_Skeleton."""
    resp = mcp_call("tools/call", {
        "name": "animation_query",
        "arguments": {
            "action": "get_sequence_info",
            "asset_path": asset_path
        }
    })
    if not mcp_result_ok(resp):
        print(f"  Verify FAILED: asset not found")
        return False
    data = json.loads(mcp_text(resp))
    skel = data.get("skeleton", "")
    if "SK_Melusina_Skeleton" not in skel:
        print(f"  Verify FAILED: skeleton is {skel}")
        return False
    print(f"  Verified: skeleton = {skel.split('.')[0]}")
    print(f"  Duration: {data.get('duration')}s, FPS: {data.get('sample_rate')}")
    return True


QUATERNIUS_PREFIX = "A_CAS_Melusina_"


def _pick_retargeter(clip_name: str) -> str:
    return RTG_SOURCE_TO_MELUSINA


def main():
    if len(sys.argv) < 2:
        print("Usage: python import_chain.py <fbx_path> [--manifest <path>] [--dry-run]")
        sys.exit(1)

    fbx_path = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    manifest_path = None
    for i, arg in enumerate(sys.argv):
        if arg == "--manifest" and i + 1 < len(sys.argv):
            manifest_path = sys.argv[i + 1]
    if not manifest_path:
        manifest_path = fbx_path.replace(".fbx", ".manifest.json")

    try:
        manifest, schema_errors, was_legacy = load_as_v2(Path(manifest_path), Path(fbx_path))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: manifest could not be read: {exc}")
        sys.exit(1)
    manifest_errors = list(schema_errors)
    if was_legacy:
        manifest_errors.append("legacy sidecar is catalogue-only; create a v2 source-rig manifest")
    else:
        manifest_errors.extend(validate_v2(manifest))
    if not was_legacy and manifest.get("status") != "canonical":
        manifest_errors.append(
            f"manifest status {manifest.get('status')!r} is not importable; only canonical source-rig clips may enter the UE chain"
        )
    if manifest_errors:
        print("FAIL: manifest rejected:")
        for error in manifest_errors:
            print(f"  - {error}")
        sys.exit(1)

    if manifest.get("canonical_skeleton") != CANONICAL_SKELETON_PATH:
        print("FAIL: manifest does not declare the canonical source skeleton")
        sys.exit(1)
    if manifest.get("retarget_profile") != RETARGET_PROFILE:
        print("FAIL: manifest does not declare RTG_Source_to_Melusina")
        sys.exit(1)

    clip_name = os.path.splitext(os.path.basename(fbx_path))[0]
    retargeter = _pick_retargeter(clip_name)
    is_looping = manifest.get("loop", False)

    print(f"=== Additive Import Chain ===")
    print(f"  Clip: {clip_name}")
    print(f"  FBX: {fbx_path}")
    print(f"  Manifest: {manifest_path}")
    print(f"  Retargeter: {retargeter.split('.')[0]}")
    print(f"  Looping: {is_looping}")

    if dry_run:
        print("  DRY RUN -- stopping before import")
        sys.exit(0)

    if not validate(fbx_path, manifest_path):
        print("FAIL: Validation rejected.")
        sys.exit(1)

    imported = import_fbx_as_anim(fbx_path, clip_name)
    if not imported:
        print("FAIL: Import step failed.")
        sys.exit(1)

    retargeted = retarget(imported, retargeter)
    if not retargeted:
        print("FAIL: Retarget step failed.")
        sys.exit(1)

    set_looping(retargeted, is_looping)

    if not verify(retargeted):
        print("FAIL: Verification step failed.")
        sys.exit(1)

    print(f"PASS: {clip_name} imported, retargeted, loop={is_looping}, verified.")
    print(f"  Asset: {retargeted}")
    print(f"  Next: wire into ABP/blendspace via t3d_anim_injector.py")
    sys.exit(0)


if __name__ == "__main__":
    main()
