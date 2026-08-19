#!/usr/bin/env python3
"""Offline preflight for the IntegrationMap puzzle -> water -> quest seam.

The existing spatial-puzzle driver is an editor mutation tool.  This preflight
is intentionally separate and dependency-free: it checks the source/spec
contract, reports the live-editor assertions that are still pending, and never
contacts Monolith or issues a Blueprint mutation.

Usage:
    python Tools/melodia_wiring_preflight.py
    python Tools/melodia_wiring_preflight.py --json
    python Tools/melodia_wiring_preflight.py --strict  # expected to fail offline
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "specs" / "blueprints" / "melodia_puzzle_water_quest_wiring.v1.json"
ALLOWLIST_PATH = ROOT / "specs" / "progression" / "melodia_integration_allowlist_seed.v1.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def source_check(contract: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for item in contract.get("source_contracts", []):
        relpath = str(item["path"])
        path = ROOT / relpath
        text = path.read_text(encoding="utf-8", errors="ignore") if path.is_file() else ""
        missing = [marker for marker in item.get("required_markers", []) if marker not in text]
        forbidden_present = [
            marker for marker in item.get("forbidden_markers", []) if marker in text
        ]
        checks.append(
            {
                "path": relpath,
                "exists": path.is_file(),
                "missing_required_markers": missing,
                "forbidden_markers_present": forbidden_present,
                "status": (
                    "pass"
                    if path.is_file() and not missing and not forbidden_present
                    else "fail"
                ),
            }
        )
    return checks


def allowlist_check(contract: dict[str, Any]) -> dict[str, Any]:
    allowlist = load_json(ALLOWLIST_PATH)
    flags = set(allowlist.get("sets", {}).get("NarrativeFlagIds", []))
    quests = set(allowlist.get("sets", {}).get("QuestIds", []))
    expected_flag = "first_resonance_solved"
    expected_quest = "quest.first_dream"
    return {
        "path": relative(ALLOWLIST_PATH),
        "flag": expected_flag,
        "flag_present": expected_flag in flags,
        "quest": expected_quest,
        "quest_present": expected_quest in quests,
        "status": (
            "pass"
            if expected_flag in flags and expected_quest in quests
            else "fail"
        ),
    }


def audit_check(contract: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for item in contract.get("current_audit_inputs", []):
        path = ROOT / str(item["path"])
        results.append(
            {
                "path": str(item["path"]),
                "exists": path.is_file(),
                "status": "available_snapshot" if path.is_file() else "missing_snapshot",
                "claim_limit": item.get("must_not_be_promoted_to")
                or item.get("claim_limit"),
            }
        )
    return results


def build_report() -> dict[str, Any]:
    contract = load_json(CONTRACT_PATH)
    driver_path = ROOT / str(contract["driver"])
    driver_text = driver_path.read_text(encoding="utf-8", errors="ignore") if driver_path.is_file() else ""
    chain = contract.get("chain", [])
    chain_ids = [str(item.get("id")) for item in chain]
    source_checks = source_check(contract)
    allowlist = allowlist_check(contract)
    audits = audit_check(contract)

    static_preconditions = [
        {
            "id": "contract_shape",
            "status": (
                "pass"
                if contract.get("kind") == "melodia_puzzle_water_quest_wiring_contract"
                and chain_ids == [
                    "puzzle_event",
                    "water_route",
                    "narrative_flag",
                    "quest_objective",
                    "save_readback",
                ]
                else "fail"
            ),
        },
        {
            "id": "source_authority_markers",
            "status": (
                "pass"
                if source_checks and all(item["status"] == "pass" for item in source_checks)
                else "fail"
            ),
        },
        {
            "id": "allowlist_seed",
            "status": allowlist["status"],
        },
        {
            "id": "driver_has_no_direct_travel",
            "status": (
                "pass"
                if driver_path.is_file() and "OpenLevel" not in driver_text
                else "fail"
            ),
        },
        {
            "id": "audit_snapshots_are_labeled",
            "status": (
                "pass"
                if audits and all(item["claim_limit"] for item in audits)
                else "fail"
            ),
        },
    ]

    live_preconditions = [
        {
            "id": "monolith_reachable",
            "status": "pending",
            "reason": "This offline command never contacts the editor; live Monolith status is required.",
        },
        {
            "id": "stable_graph_fingerprint",
            "status": "pending",
            "reason": "Requires two identical fingerprints on an untouched graph and a saved rollback export.",
        },
        {
            "id": "pin_defaults_and_binding_readback",
            "status": "pending",
            "reason": "PuzzleId, route id, flag id, quest id, and delegate binding require live graph readback.",
        },
        {
            "id": "compile_save_mtime_reexport",
            "status": "pending",
            "reason": "Requires compile, save, disk mtime, and independent post-save graph export.",
        },
        {
            "id": "map_placement_and_pie",
            "status": "pending",
            "reason": "Requires the disposable map, one-player authority readback, save/reload, and PIE.",
        },
    ]

    return {
        "schema_version": "1.0",
        "kind": "melodia_wiring_preflight_report",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "offline_only": True,
        "mutations_issued": False,
        "contract": relative(CONTRACT_PATH),
        "driver": str(contract["driver"]),
        "source_checks": source_checks,
        "allowlist_check": allowlist,
        "audit_checks": audits,
        "static_preconditions": static_preconditions,
        "live_preconditions": live_preconditions,
        "ready_for_live_mutation": False,
        "live_evidence_available": False,
        "claim_boundary": "Source/spec checks do not prove Blueprint wiring, map placement, compile/save persistence, or PIE.",
    }


def print_text(report: dict[str, Any]) -> None:
    print("Melodia puzzle -> water -> quest wiring preflight (offline)")
    print(f"  static checks: {sum(item['status'] == 'pass' for item in report['static_preconditions'])}/"
          f"{len(report['static_preconditions'])} pass")
    print("  live evidence available: false")
    print("  mutations issued: false")
    print("  ready for live mutation: false")
    print()
    for item in report["static_preconditions"]:
        print(f"  [{item['status'].upper():7}] {item['id']}")
    print("\n  live gates:")
    for item in report["live_preconditions"]:
        print(f"  [{item['status'].upper():7}] {item['id']} — {item['reason']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return non-zero while any live precondition is pending",
    )
    args = parser.parse_args(argv)
    try:
        report = build_report()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"wiring preflight failed: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 1 if args.strict and not report["ready_for_live_mutation"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
