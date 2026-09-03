#!/usr/bin/env python3
"""Fail-closed validator for normalized wardrobe T3D requests.

This is the adapter boundary for LiveLink, TouchDesigner, and OSC. It validates
the tracked mutation schema and wardrobe operation manifest without contacting
Unreal or mutating assets.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]
REQUEST_SCHEMA = PROJECT / "specs" / "schemas" / "t3d_mutation_request.v1.json"
PIPELINE_MANIFEST = PROJECT / "specs" / "wardrobe" / "wardrobe_t3d_pipeline_manifest.v1.json"


def validate(request: dict) -> list[str]:
    errors: list[str] = []
    if request.get("schema") != "melodia.t3d_mutation_request.v1":
        errors.append("schema_mismatch")
    if not isinstance(request.get("request_id"), str) or not request["request_id"].strip():
        errors.append("request_id_required")
    asset = request.get("asset_path")
    if not isinstance(asset, str) or not asset.startswith("/Game/"):
        errors.append("asset_path_must_start_with_/Game/")
    fingerprint = request.get("expected_before_fingerprint")
    if not isinstance(fingerprint, str) or len(fingerprint) < 8:
        errors.append("expected_before_fingerprint_required")
    operations = request.get("operations")
    if not isinstance(operations, list) or not operations:
        errors.append("operations_required")
        operations = []
    try:
        pipeline = json.loads(PIPELINE_MANIFEST.read_text(encoding="utf-8"))
        allowed = set(pipeline.get("operations", []))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"pipeline_manifest_unavailable_{exc}")
        allowed = set()
    for operation in operations:
        if operation not in allowed:
            errors.append(f"operation_not_in_manifest_{operation}")
        if operation == "wire_wardrobe_battle_gate" and request.get("enable_battle") is not True:
            errors.append("battle_gate_requires_explicit_enable_battle")
    verification = request.get("verification")
    if not isinstance(verification, dict) or verification.get("compile_zero_errors") is not True:
        errors.append("compile_zero_errors_verification_required")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path)
    args = parser.parse_args()
    try:
        request = json.loads(args.request.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "errors": [f"request_read_failed_{exc}"]}, indent=2))
        return 1
    errors = validate(request)
    print(json.dumps({"ok": not errors, "request": str(args.request), "errors": errors}, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
