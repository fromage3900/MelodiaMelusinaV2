#!/usr/bin/env python3
"""Validate Cascadeur sidecar manifests before Unreal import.

This tool does not parse or modify FBX files. Unreal performs the authoritative
post-import skeleton check. The validator catches naming, path, timing, and
contract mistakes before a file reaches the editor.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_INBOX = PROJECT_DIR / "Imports" / "Animations" / "Cascadeur" / "Inbox"
DEFAULT_REPORT = PROJECT_DIR / "Saved" / "Audit" / "cascadeur_manifest_report.json"
TARGET_SKELETON = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton"
ROOT_MOTION_VALUES = {"in_place", "root_motion", "explicit_review_required"}
CONTEXT_VALUES = {"exploration", "battle", "vn", "cinematic"}
IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_]{0,63}\Z")


def _validate(path: Path, expected_skeleton: str) -> dict[str, Any]:
    result: dict[str, Any] = {"path": str(path), "ok": False, "errors": [], "warnings": []}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        result["errors"].append(str(exc))
        return result

    if not isinstance(value, dict):
        result["errors"].append("manifest root must be a JSON object")
        return result

    if value.get("schema_version") != 1:
        result["errors"].append("schema_version must be 1")

    clip_id = value.get("clip_id")
    if not isinstance(clip_id, str) or not IDENTIFIER.fullmatch(clip_id):
        result["errors"].append("clip_id must be an ASCII identifier of 1-64 characters")

    context = value.get("context")
    if context not in CONTEXT_VALUES:
        result["errors"].append(f"context must be one of {sorted(CONTEXT_VALUES)}")

    skeleton = value.get("expected_skeleton")
    if skeleton != expected_skeleton:
        result["errors"].append(f"expected_skeleton must equal {expected_skeleton}")

    fps = value.get("fps")
    if not isinstance(fps, (int, float)) or isinstance(fps, bool) or fps <= 0:
        result["errors"].append("fps must be a positive number")

    root_motion = value.get("root_motion", "in_place")
    if root_motion not in ROOT_MOTION_VALUES:
        result["errors"].append(f"root_motion must be one of {sorted(ROOT_MOTION_VALUES)}")

    consumer = value.get("consumer")
    if not isinstance(consumer, str) or not consumer:
        result["errors"].append("consumer must be a non-empty string")

    start = value.get("start_frame")
    end = value.get("end_frame")
    if not isinstance(start, int) or not isinstance(end, int) or end < start:
        result["errors"].append("start_frame and end_frame must be integers with end >= start")

    loop = value.get("loop")
    if not isinstance(loop, bool):
        result["errors"].append("loop must be boolean")

    notify = value.get("notify_contract", {})
    if not isinstance(notify, dict):
        result["errors"].append("notify_contract must be an object")
    else:
        count = notify.get("count", 0)
        if not isinstance(count, int) or count < 0:
            result["errors"].append("notify_contract.count must be a non-negative integer")
        if context == "battle" and count != 0:
            result["warnings"].append("Gameplay notifies are added to the UE montage, not the FBX")

    if value.get("fps") != 30:
        result["warnings"].append("New authored clips should normally use the 30 fps project contract")
    if root_motion == "root_motion" and context in {"exploration", "battle"}:
        result["errors"].append("Exploration and battle clips must remain in_place")

    result["ok"] = not result["errors"]
    return result


def _collect_manifests(args: argparse.Namespace) -> tuple[list[Path], list[str]]:
    paths: list[Path] = []
    errors: list[str] = []
    if args.manifest:
        paths.extend(Path(path).resolve() for path in args.manifest)
    if args.inbox:
        inbox = Path(args.inbox).resolve()
        if not inbox.is_dir():
            errors.append(f"Inbox does not exist: {inbox}")
            return paths, errors
        fbxs = sorted(path for path in inbox.iterdir() if path.suffix.lower() == ".fbx")
        for fbx in fbxs:
            sidecar = fbx.with_suffix(".json")
            if not sidecar.is_file():
                message = f"Missing sidecar for {fbx.name}: {sidecar.name}"
                if args.require_sidecar:
                    errors.append(message)
                else:
                    print(f"WARNING: {message}", file=sys.stderr)
                continue
            paths.append(sidecar)
    return sorted(set(paths)), errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", action="append", help="Manifest JSON file; repeatable")
    parser.add_argument("--inbox", default=str(DEFAULT_INBOX), help="Cascadeur FBX inbox to scan")
    parser.add_argument("--expected-skeleton", default=TARGET_SKELETON)
    parser.add_argument("--require-sidecar", action="store_true")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Output JSON report path")
    args = parser.parse_args(argv)

    paths, collection_errors = _collect_manifests(args)
    files = [_validate(path, args.expected_skeleton) for path in paths if path.is_file()]
    for path in paths:
        if not path.is_file():
            files.append({"path": str(path), "ok": False, "errors": ["file not found"], "warnings": []})

    errors = collection_errors + [error for item in files for error in item.get("errors", [])]
    report = {
        "schema_version": 1,
        "expected_skeleton": args.expected_skeleton,
        "ok": not errors and bool(files),
        "files": files,
        "errors": errors,
        "warnings": [warning for item in files for warning in item.get("warnings", [])],
    }

    report_path = Path(args.report).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    for item in files:
        status = "OK" if item.get("ok") else "FAIL"
        print(f"{status}: {item['path']}")
        for error in item.get("errors", []):
            print(f"  ERROR: {error}")
        for warning in item.get("warnings", []):
            print(f"  WARNING: {warning}")
    for error in collection_errors:
        print(f"ERROR: {error}")
    print(f"Report: {report_path}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
