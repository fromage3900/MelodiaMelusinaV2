#!/usr/bin/env python3
"""Read-only owner gate for IntegrationMap mutations.

This tool only calls Monolith read actions. It reports the three required
Melody Slime DataTables and refuses map mutation when unrelated dirty packages
or modal evidence is present. It never opens, edits, saves, or deletes an asset.

Usage:
    python Tools/melodia_live_mutation_preflight.py
    python Tools/melodia_live_mutation_preflight.py --json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
TARGET_MAP = "/Game/MelodiaIntegration/Maps/MelodiaIntegrationMap"
DATATABLES = {
    "DT_MelodySlime_Enemies": "/Game/Melodia/DataStuctures/DT_MelodySlime_Enemies",
    "DT_MelodySlime_Skills": "/Game/Melodia/DataStuctures/DT_MelodySlime_Skills",
    "DT_MelodySlime_RoomMods": "/Game/Melodia/DataStuctures/DT_MelodySlime_RoomMods",
}


def _json_response(raw: Any) -> tuple[dict, str | None]:
    if isinstance(raw, dict):
        return raw, None
    if not isinstance(raw, str):
        return {}, "non_text_response"
    if raw.startswith("ERROR:"):
        return {}, raw
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        return {}, f"invalid_json_response_{exc}"
    return (value, None) if isinstance(value, dict) else ({}, "response_must_be_object")


def _dirty_packages(payload: dict) -> list[dict]:
    values = payload.get("dirty_packages", [])
    return [item for item in values if isinstance(item, dict)]


def _modal_evidence(payload: dict) -> list[str]:
    evidence: list[str] = []

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, str) and (
            "MODAL_OPEN" in value or "modal" in value.casefold()
        ):
            evidence.append(value)

    visit(payload)
    return evidence


def _asset_exists(state: dict) -> bool:
    """Accept the live indexer's known presence field variants."""
    for key in ("exists", "on_disk", "exists_on_disk", "asset_exists", "found"):
        if key in state:
            return bool(state[key])
    nested = state.get("asset_state")
    if isinstance(nested, dict):
        return _asset_exists(nested)
    return str(state.get("status", "")).casefold() in {"present", "loaded", "found"}


def evaluate_readiness(
    dirty_payload: dict,
    log_payload: dict,
    datatable_states: dict[str, dict],
    *,
    target_map: str = TARGET_MAP,
) -> dict[str, Any]:
    """Pure readiness decision used by the live wrapper and regression tests."""
    dirty = _dirty_packages(dirty_payload)
    unrelated_dirty = [
        item for item in dirty
        if str(item.get("package", "")) != target_map
    ]
    dirty_maps = [
        item for item in dirty
        if bool(item.get("is_map")) and str(item.get("package", "")) != target_map
    ]
    modal_evidence = _modal_evidence(log_payload)
    datatables: dict[str, dict[str, Any]] = {}
    for name, state in datatable_states.items():
        exists = _asset_exists(state)
        datatables[name] = {
            "asset_path": DATATABLES.get(name, name),
            "exists": exists,
            "status": "present" if exists else "absent",
            "details": state,
        }

    blockers: list[str] = []
    if unrelated_dirty:
        blockers.append("unrelated_dirty_packages_present")
    if dirty_maps:
        blockers.append("another_dirty_map_present")
    if modal_evidence:
        blockers.append("modal_evidence_present")
    absent = [name for name, state in datatables.items() if not state["exists"]]
    if absent:
        blockers.append("required_datatables_absent")
    return {
        "read_only": True,
        "target_map": target_map,
        "dirty_packages": dirty,
        "unrelated_dirty_packages": unrelated_dirty,
        "modal_evidence": modal_evidence,
        "datatables": datatables,
        "absent_datatables": absent,
        "blockers": blockers,
        "ready_for_map_mutation": not blockers,
        "mutations_issued": False,
    }


def _call_json(monolith: Callable[..., Any], method: str, args: dict) -> tuple[dict, str | None]:
    return _json_response(monolith(method, args))


def build_report(monolith: Callable[..., Any] | None = None) -> dict[str, Any]:
    if monolith is None:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from mcp_client import monolith as live_monolith

        monolith = live_monolith

    status, status_error = _call_json(monolith, "monolith_status", {})
    dirty, dirty_error = _call_json(
        monolith,
        "editor_query",
        {"action": "list_dirty_packages", "params": {"include_maps": True, "include_content": True}},
    )
    logs, logs_error = _call_json(
        monolith,
        "editor_query",
        {"action": "get_recent_logs", "params": {"count": 30}},
    )
    datatable_states: dict[str, dict] = {}
    datatable_errors: dict[str, str] = {}
    for name, asset_path in DATATABLES.items():
        state, error = _call_json(
            monolith,
            "project_query",
            {"action": "get_saved_asset_state", "params": {"asset_path": asset_path}},
        )
        datatable_states[name] = state
        if error:
            datatable_errors[name] = error

    report = evaluate_readiness(dirty, logs, datatable_states)
    report.update(
        {
            "schema_version": "1.0",
            "kind": "melodia_live_mutation_preflight",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "monolith_status": status,
            "query_errors": {
                key: value
                for key, value in {
                    "monolith_status": status_error,
                    "dirty_packages": dirty_error,
                    "modal_logs": logs_error,
                }.items()
                if value
            },
            "datatable_query_errors": datatable_errors,
        }
    )
    if status_error or dirty_error or logs_error or datatable_errors:
        report["blockers"].append("readiness_query_failed")
        report["ready_for_map_mutation"] = False
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    args = parser.parse_args(argv)
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Melodia live map-mutation preflight (read-only)")
        print(f"  ready for map mutation: {report['ready_for_map_mutation']}")
        print(f"  absent DataTables: {', '.join(report['absent_datatables']) or 'none'}")
        print(f"  modal evidence: {len(report['modal_evidence'])}")
        if report["blockers"]:
            print("  blockers:")
            for blocker in report["blockers"]:
                print(f"    - {blocker}")
    return 0 if report["ready_for_map_mutation"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
