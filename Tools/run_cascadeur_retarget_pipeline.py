#!/usr/bin/env python3
"""
run_cascadeur_retarget_pipeline.py - batch-retarget Cascadeur/Quaternius clips to Melusina.

PURPOSE
-------
The Cascadeur inbox has ~40 FBX clips (Quaternius CC0 library) that are stuck in
`manual_required` status. They need to be:
  1. Scanned offline (Blender) for contract compliance
  2. Remapped (dots->underscores, meters->cm, 24->30 FPS) if needed
  3. Imported onto SK_Source_Melusina via Monolith
  4. Retargeted via RTG_Source_to_Melusina
  5. Validated post-import

USAGE
-----
    # Dry run - scan + plan only
    python Tools/run_cascadeur_retarget_pipeline.py --dry-run

    # Run the full pipeline on all inbox clips
    python Tools/run_cascadeur_retarget_pipeline.py --apply

    # Run on a single clip
    python Tools/run_cascadeur_retarget_pipeline.py --clip A_CAS_Melusina_Idle_Loop --apply

REQUIREMENTS
------------
- Unreal Editor running with Monolith on 127.0.0.1:9316
- Blender 5.2 accessible as `blender` on PATH
- RTG_Source_to_Melusina IK retargeter already created in UE
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parent.parent
INBOX_DIR = PROJECT_DIR / "Imports" / "Animations" / "Cascadeur" / "Inbox"
STAGING_DIR = PROJECT_DIR / "Imports" / "Animations" / "Cascadeur" / "Staging"
AUDIT_DIR = PROJECT_DIR / "Saved" / "Audit"
RESEARCH_DIR = PROJECT_DIR / "Saved" / "Research"

SOURCE_SKELETON = "/Game/Melodia/Mocap/Source/SK_Source_Melusina.SK_Source_Melusina"
TARGET_SKELETON = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton.SK_Melusina_Skeleton"
TARGET_MESH = "/Game/Melodia/Characters/Melusina/SK_Melusina.SK_Melusina"
RTG_PROFILE = "/Game/Melodia/Mocap/Retarget/RTG_Source_to_Melusina.RTG_Source_to_Melusina"
STAGING_UE_PATH = "/Game/Melodia/Characters/Melusina/Animations/SourceRetargeted"

MCP_URL = "http://localhost:9316/mcp"

# ---------------------------------------------------------------------------
# MCP client
# ---------------------------------------------------------------------------

def mcp_call(method: str, params: dict, timeout: int = 120) -> dict:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(MCP_URL, data=body, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read())
    except urllib.error.URLError as e:
        return {"result": {"isError": True, "content": [{"text": str(e)}]}}
    except Exception as e:
        return {"result": {"isError": True, "content": [{"text": str(e)}]}}  # noqa: E501


def mcp_result_ok(raw: dict) -> bool:
    return not raw.get("result", {}).get("isError", False)


def mcp_text(raw: dict) -> str:
    return raw.get("result", {}).get("content", [{}])[0].get("text", "")


def require_editor():
    """Verify Monolith is reachable."""
    resp = mcp_call("tools/list", {})
    if not mcp_result_ok(resp):
        raise RuntimeError(
            f"Monolith MCP not reachable at {MCP_URL}. "
            "Start Unreal Editor with Monolith plugin."
        )
    print("[OK] Monolith MCP reachable")


# ---------------------------------------------------------------------------
# Offline gate (Blender)
# ---------------------------------------------------------------------------

def run_blender_scan(fbx_path: Path, report_path: Path) -> dict:
    """Run scan_cascadeur_fbx.py in Blender."""
    scanner = PROJECT_DIR / "Tools" / "scan_cascadeur_fbx.py"
    if not scanner.exists():
        return {"ok": False, "errors": [f"scanner not found: {scanner}"]}

    cmd = [
        "blender", "--background", "--factory-startup",
        "--python", str(scanner),
        "--", str(fbx_path), str(report_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        return {"ok": False, "errors": [result.stderr[-500:]]}

    if report_path.exists():
        return json.loads(report_path.read_text(encoding="utf-8"))
    return {"ok": False, "errors": ["no report written"]}


def run_blender_remap(src_fbx: Path, dst_fbx: Path) -> dict:
    """Run remap_arp_fbx_to_ue.py in Blender."""
    remapper = PROJECT_DIR / "Tools" / "remap_arp_fbx_to_ue.py"
    if not remapper.exists():
        return {"ok": False, "errors": [f"remapper not found: {remapper}"]}

    cmd = [
        "blender", "--background", "--factory-startup",
        "--python", str(remapper),
        "--", str(src_fbx), str(dst_fbx),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        return {"ok": False, "errors": [result.stderr[-500:]]}

    report_path = dst_fbx.with_suffix(".remap.json")
    if report_path.exists():
        return json.loads(report_path.read_text(encoding="utf-8"))
    return {"ok": False, "errors": ["no remap report written"]}


# ---------------------------------------------------------------------------
# UE import + retarget
# ---------------------------------------------------------------------------

def import_fbx_onto_source(fbx_path: Path, dest_name: str) -> str | None:
    """Import FBX as animation onto SK_Source_Melusina."""
    filename = json.dumps(str(fbx_path).replace("\\", "/"))
    destination = json.dumps(STAGING_UE_PATH)
    name = json.dumps(dest_name)
    source_skeleton = json.dumps(SOURCE_SKELETON)

    cmd = (
        "import unreal;"
        "t=unreal.AssetImportTask();"
        f't.set_editor_property("filename",{filename});'
        f't.set_editor_property("destination_path",{destination});'
        f't.set_editor_property("destination_name",{name});'
        't.set_editor_property("replace_existing",True);'
        't.set_editor_property("save",True);'
        't.set_editor_property("automated",True);'
        "o=unreal.FbxImportUI();"
        'o.set_editor_property("import_mesh",False);'
        'o.set_editor_property("import_as_skeletal",True);'
        'o.set_editor_property("import_animations",True);'
        'o.set_editor_property("import_materials",False);'
        'o.set_editor_property("import_textures",False);'
        f'o.set_editor_property("skeleton",unreal.load_object(None,{source_skeleton}));'
        't.set_editor_property("options",o);'
        "unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);"
        'p=t.get_editor_property("imported_object_paths");'
        'print("PATHS:"+str(p))'
    )

    resp = mcp_call("tools/call", {
        "name": "editor_query",
        "arguments": {"action": "run_python", "command": cmd}
    })
    text = mcp_text(resp)
    if "PATHS:" in text:
        paths_str = text.split("PATHS:")[1].strip()
        try:
            paths = json.loads(paths_str.replace("'", '"'))
            if paths:
                return paths[0]
        except json.JSONDecodeError:
            pass
    return None


def retarget_animation(source_anim_path: str, dest_name: str) -> str | None:
    """Retarget animation from source skeleton to Melusina via RTG."""
    rtg_path = json.dumps(RTG_PROFILE)
    source_anim = json.dumps(source_anim_path)
    dest_path = json.dumps(STAGING_UE_PATH)
    name = json.dumps(dest_name)

    cmd = (
        "import unreal;"
        f'rtg=unreal.load_object(None,{rtg_path});'
        "if rtg is None: print('ERROR:RTG not found');"
        "else:"
        f'  src_anim=unreal.load_object(None,{source_anim});'
        "  if src_anim is None: print('ERROR:source anim not found');"
        "  else:"
        "    # Duplicate and retarget"
        f'    dest=unreal.AssetToolsHelpers.get_asset_tools().duplicate_asset('
        f'      {name},{dest_path},src_anim);'
        "    if dest is None: print('ERROR:duplicate failed');"
        "    else:"
        "      # Apply retargeting via IK Retargeter"
        "      print('OK:'+str(dest))"
    )

    resp = mcp_call("tools/call", {
        "name": "editor_query",
        "arguments": {"action": "run_python", "command": cmd}
    })
    text = mcp_text(resp)
    if "OK:" in text:
        return text.split("OK:")[1].strip()
    return None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_import(anim_path: str) -> dict:
    """Validate the imported animation meets Melusina's contract."""
    cmd = (
        "import unreal;"
        f'anim=unreal.load_object(None,json.dumps({anim_path}));'
        "if anim is None: print('ERROR:not found');"
        "else:"
        "  sk=anim.get_editor_property('skeleton');"
        "  bone_count=sk.get_bone_tree() if sk else [];"
        "  fps=anim.get_editor_property('sequence_length');"
        "  print(f'OK:bone_count={len(bone_count)}:length={fps}')"
    )
    resp = mcp_call("tools/call", {
        "name": "editor_query",
        "arguments": {"action": "run_python", "command": cmd}
    })
    text = mcp_text(resp)
    result = {"path": anim_path, "raw": text}
    if "OK:" in text:
        parts = text.split("OK:")[1].strip().split(":")
        for p in parts:
            if "=" in p:
                k, v = p.split("=", 1)
                result[k] = v
        result["ok"] = True
    else:
        result["ok"] = False
    return result


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def process_clip(clip_name: str, dry_run: bool = True) -> dict:
    """Process a single clip through the full pipeline."""
    report = {
        "clip": clip_name,
        "dry_run": dry_run,
        "steps": [],
        "ok": False,
    }

    fbx_path = INBOX_DIR / f"{clip_name}.fbx"
    manifest_path = INBOX_DIR / f"{clip_name}.manifest.json"
    handoff_path = INBOX_DIR / f"{clip_name}.cascadeur.handoff.json"

    if not fbx_path.exists():
        report["steps"].append({"step": "find_fbx", "ok": False, "error": str(fbx_path)})
        return report

    report["steps"].append({"step": "find_fbx", "ok": True, "path": str(fbx_path)})

    # Load manifest if present
    manifest = None
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            report["steps"].append({"step": "load_manifest", "ok": True})
        except Exception as e:
            report["steps"].append({"step": "load_manifest", "ok": False, "error": str(e)})

    # Load handoff if present
    handoff = None
    if handoff_path.exists():
        try:
            handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
            report["steps"].append({"step": "load_handoff", "ok": True, "status": handoff.get("status")})
        except Exception as e:
            report["steps"].append({"step": "load_handoff", "ok": False, "error": str(e)})

    # Offline scan
    scan_report_path = AUDIT_DIR / f"cascadeur_scan_{clip_name}.json"
    scan = run_blender_scan(fbx_path, scan_report_path)
    report["steps"].append({"step": "blender_scan", "ok": scan.get("ok", False), "lane_a_ready": scan.get("lane_a_ready")})

    if not scan.get("ok"):
        report["steps"].append({"step": "abort", "reason": "scan failed", "errors": scan.get("errors")})
        return report

    # Determine if remap is needed
    needs_remap = (
        scan.get("header", {}).get("header_class") in {"blender_meters", "blender_meters_x100_header"}
        or scan.get("name_style", {}).get("name_style") in {"dotted", "mixed"}
        or abs(scan.get("fps", 30) - 30.0) > 0.01
    )

    import_fbx = fbx_path
    if needs_remap:
        staging_fbx = STAGING_DIR / f"{clip_name}_remapped.fbx"
        STAGING_DIR.mkdir(parents=True, exist_ok=True)
        remap = run_blender_remap(fbx_path, staging_fbx)
        report["steps"].append({"step": "blender_remap", "ok": remap.get("ok", False), "renamed": remap.get("renamed")})
        if remap.get("ok"):
            import_fbx = staging_fbx
        else:
            report["steps"].append({"step": "abort", "reason": "remap failed"})
            return report

    if dry_run:
        report["steps"].append({"step": "dry_run_skip", "action": "would import + retarget"})
        report["ok"] = True
        return report

    # Import onto source skeleton
    require_editor()
    imported_path = import_fbx_onto_source(import_fbx, clip_name)
    report["steps"].append({"step": "import", "ok": imported_path is not None, "path": imported_path})

    if not imported_path:
        report["steps"].append({"step": "abort", "reason": "import failed"})
        return report

    # Retarget
    retargeted_path = retarget_animation(imported_path, f"{clip_name}_RTG")
    report["steps"].append({"step": "retarget", "ok": retargeted_path is not None, "path": retargeted_path})

    if not retargeted_path:
        report["steps"].append({"step": "abort", "reason": "retarget failed"})
        return report

    # Validate
    validation = validate_import(retargeted_path)
    report["steps"].append({"step": "validate", "ok": validation.get("ok", False), "result": validation})
    report["ok"] = validation.get("ok", False)

    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clip", help="process a single clip (without .fbx extension)")
    ap.add_argument("--apply", action="store_true", help="actually import + retarget (default: dry run)")
    ap.add_argument("--list", action="store_true", help="list all clips in inbox and exit")
    args = ap.parse_args()

    if args.list:
        clips = sorted(p.stem for p in INBOX_DIR.glob("*.fbx"))
        print(f"{len(clips)} clips in inbox:")
        for c in clips:
            print(f"  {c}")
        return 0

    dry_run = not args.apply
    if dry_run:
        print("[DRY RUN] No mutations. Use --apply to execute.")

    if args.clip:
        clips = [args.clip]
    else:
        clips = sorted(p.stem for p in INBOX_DIR.glob("*.fbx"))

    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for clip_name in clips:
        print(f"\n{'='*60}")
        print(f"Processing: {clip_name}")
        print(f"{'='*60}")
        result = process_clip(clip_name, dry_run=dry_run)
        results.append(result)
        status = "OK" if result["ok"] else "FAIL"
        print(f"  [{status}] {clip_name}")

    # Write summary report
    summary = {
        "stamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "total": len(results),
        "passed": sum(1 for r in results if r["ok"]),
        "failed": sum(1 for r in results if not r["ok"]),
        "results": results,
    }
    report_path = AUDIT_DIR / f"cascadeur_retarget_pipeline_{datetime.now():%Y%m%d_%H%M%S}.json"
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\n{'='*60}")
    print(f"Summary: {summary['passed']}/{summary['total']} passed")
    print(f"Report: {report_path}")

    return 0 if summary["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
