#!/usr/bin/env python3
"""Offline readiness inventory for the Melodia gameplay Blueprint kit.

This tool deliberately does not infer live Blueprint readiness from a .uasset file.
It reports the distinction between:

* a planned canonical path that is absent;
* an asset present on disk but missing live graph/fixture proof; and
* a contract-only fixture that has passed the offline schema gate.

The editor/Monolith is intentionally not contacted. Use the live BP sweep and
fixture evidence to promote L2-L4 after a usable editor session returns.

Usage:
    python Tools/melodia_bp_readiness.py
    python Tools/melodia_bp_readiness.py --json
    python Tools/melodia_bp_readiness.py --strict   # expected to fail until live proof exists
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "specs" / "blueprints" / "melodia_gameplay_bp_kit.v1.json"
KAWAII_PROBE = "/Game/MelodiaIntegration/Tests/BP_KawaiiPhysicsPlacementProbe"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def game_asset_path_to_file(asset_path: str) -> Path:
    if not asset_path.startswith("/Game/"):
        raise ValueError(f"unsupported asset path: {asset_path}")
    relative = asset_path.removeprefix("/Game/").replace("/", "\\")
    return ROOT / "Content" / f"{relative}.uasset"


def fixture_state(relative_path: str | None) -> dict[str, Any] | None:
    if not relative_path:
        return None
    path = ROOT / relative_path
    result: dict[str, Any] = {"path": relative_path, "exists": path.is_file()}
    if not path.is_file():
        result["state"] = "missing_contract"
        return result
    try:
        fixture = load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result["state"] = "invalid_contract"
        result["error"] = str(exc)
        return result
    result["kind"] = fixture.get("kind")
    result["status"] = fixture.get("status")
    result["readiness_level"] = fixture.get("readiness_level")
    result["state"] = (
        "L1_contract_spec_only"
        if fixture.get("kind") == "melodia_content_fixture"
        and fixture.get("status") == "contract_spec_only"
        and fixture.get("readiness_level") == "L1"
        else "contract_needs_review"
    )
    return result


def build_report() -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH)
    templates: list[dict[str, Any]] = []
    for template in registry.get("templates", []):
        planned = str(template["planned_blueprint"])
        asset_file = game_asset_path_to_file(planned)
        on_disk = asset_file.is_file()
        fixture = fixture_state(template.get("fixture_spec"))
        templates.append(
            {
                "id": template.get("id"),
                "planned_blueprint": planned,
                "asset_file": str(asset_file.relative_to(ROOT)).replace("\\", "/"),
                "asset_on_disk": on_disk,
                "readiness": "L0_inventory_only_live_pending" if on_disk else "planned_L0_missing_asset",
                "materialization": template.get("materialization", {}),
                "fixture": fixture,
                "live_evidence_required": [
                    "parent_cdo_interfaces_components_graphs",
                    "compile_result",
                    "fixture_map_reachability",
                    "failure_and_reset_or_idempotency",
                    "fresh_evidence_envelope",
                ],
            }
        )

    existing_assets: list[dict[str, Any]] = []
    for path in registry.get("existing_integration_assets_to_audit", []):
        asset_file = game_asset_path_to_file(str(path))
        existing_assets.append(
            {
                "asset_path": path,
                "asset_on_disk": asset_file.is_file(),
                "asset_file": str(asset_file.relative_to(ROOT)).replace("\\", "/"),
            }
        )

    kawaii_file = game_asset_path_to_file(KAWAII_PROBE)
    on_disk_count = sum(1 for item in templates if item["asset_on_disk"])
    return {
        "schema_version": "1.0",
        "kind": "melodia_blueprint_readiness_report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "registry": str(REGISTRY_PATH.relative_to(ROOT)).replace("\\", "/"),
        "live_evidence_available": False,
        "live_evidence_note": "Offline inventory only; editor/Monolith was not contacted.",
        "templates": templates,
        "existing_integration_assets": existing_assets,
        "kawaii_probe": {
            "asset_path": KAWAII_PROBE,
            "asset_on_disk": kawaii_file.is_file(),
            "asset_file": str(kawaii_file.relative_to(ROOT)).replace("\\", "/"),
            "readiness": "L0_inventory_only_live_pending" if kawaii_file.is_file() else "planned_L0_missing_asset",
        },
        "summary": {
            "planned_templates": len(templates),
            "template_assets_on_disk": on_disk_count,
            "template_assets_missing": len(templates) - on_disk_count,
            "contract_only_fixtures": sum(
                1 for item in templates
                if isinstance(item.get("fixture"), dict)
                and item["fixture"].get("state") == "L1_contract_spec_only"
            ),
            "promoted_l2_or_higher": 0,
        },
        "promotion_rule": registry.get("promotion_rule"),
    }


def print_text(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print("Melodia Blueprint readiness (offline inventory)")
    print(f"  templates: {summary['planned_templates']}")
    print(f"  canonical template assets on disk: {summary['template_assets_on_disk']}")
    print(f"  contract-only fixtures: {summary['contract_only_fixtures']}")
    print("  live evidence available: false")
    print()
    for item in report["templates"]:
        fixture = item.get("fixture") or {}
        fixture_label = fixture.get("state", "none")
        materialization = item.get("materialization") or {}
        print(
            f"  {item['id']:<16} {item['readiness']:<34} "
            f"model={materialization.get('artifact_model', 'unspecified')} "
            f"fixture={fixture_label}"
        )
    kawaii = report["kawaii_probe"]
    print(f"\n  kawaii_probe       {kawaii['readiness']} (on_disk={kawaii['asset_on_disk']})")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit the machine-readable report")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return non-zero unless every template is live-promoted (not expected offline)",
    )
    args = parser.parse_args(argv)
    try:
        report = build_report()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"readiness inventory failed: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)

    if args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
