#!/usr/bin/env python3
"""Offline-first preflight for the Melodia gameplay Blueprint kit.

This command answers a narrow question before an editor session is available:
is each planned template sufficiently specified to enter a *live* authoring
session, and what still has to be proven there?

It never creates, edits, saves, or infers a ``.uasset``/``.umap``.  The default
mode is fully offline.  ``--live-readonly`` may be used after Monolith returns;
it performs only ``monolith_status`` and ``blueprint_query:list_graphs`` reads
for paths that already exist on disk.  No mutation action is issued.

Usage:
    python Tools/melodia_bp_materialization_preflight.py
    python Tools/melodia_bp_materialization_preflight.py --json
    python Tools/melodia_bp_materialization_preflight.py --live-readonly
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "specs" / "blueprints" / "melodia_gameplay_bp_kit.v1.json"
SOURCE_ROOTS = (ROOT / "Source", ROOT / "Plugins")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def asset_path_to_file(asset_path: str) -> Path:
    if not asset_path.startswith("/Game/"):
        raise ValueError(f"unsupported planned asset path: {asset_path}")
    relative = asset_path.removeprefix("/Game/").replace("/", "\\")
    return ROOT / "Content" / f"{relative}.uasset"


def native_class_name(native_parent: str | None) -> str | None:
    if not native_parent or native_parent.startswith("/Script/Engine."):
        return None
    # Registry values may carry an explanatory suffix in parentheses.
    value = native_parent.split("(", 1)[0].strip()
    return value.rsplit(".", 1)[-1] or None


def source_matches(class_name: str | None) -> list[str]:
    if not class_name:
        return []
    matches: list[str] = []
    pattern = re.compile(rf"\b{re.escape(class_name)}\b")
    for source_root in SOURCE_ROOTS:
        if not source_root.is_dir():
            continue
        for path in sorted(source_root.rglob("*")):
            if path.suffix not in {".h", ".cpp"}:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if pattern.search(text):
                matches.append(str(path.relative_to(ROOT)).replace("\\", "/"))
    return matches


def fixture_check(relative_path: str | None) -> dict[str, Any] | None:
    if not relative_path:
        return None
    path = ROOT / relative_path
    result: dict[str, Any] = {
        "path": relative_path,
        "exists": path.is_file(),
        "state": "missing_contract",
    }
    if not path.is_file():
        return result
    try:
        fixture = load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        result.update({"state": "invalid_contract", "error": str(exc)})
        return result
    result.update(
        {
            "kind": fixture.get("kind"),
            "status": fixture.get("status"),
            "readiness_level": fixture.get("readiness_level"),
        }
    )
    if (
        fixture.get("kind") == "melodia_content_fixture"
        and fixture.get("status") == "contract_spec_only"
        and fixture.get("readiness_level") == "L1"
    ):
        result["state"] = "L1_contract_spec_only"
    else:
        result["state"] = "contract_needs_review"
    return result


def template_preflight(template: dict[str, Any]) -> dict[str, Any]:
    planned = str(template.get("planned_blueprint", ""))
    materialization = template.get("materialization")
    if not isinstance(materialization, dict):
        materialization = {}
    asset_file = asset_path_to_file(planned)
    native_parent = materialization.get("native_parent")
    class_name = native_class_name(native_parent)
    source_files = source_matches(class_name)
    adapter_contract = materialization.get("adapter_contract")
    adapter_contract_path = ROOT / str(adapter_contract) if adapter_contract else None
    required_config_allowlist = materialization.get("required_config_allowlist")
    if not isinstance(required_config_allowlist, dict):
        required_config_allowlist = {}
    required_config_allowlist_source = materialization.get("required_config_allowlist_source")
    required_config_allowlist_source_path = (
        ROOT / str(required_config_allowlist_source)
        if required_config_allowlist_source
        else None
    )
    fixture = fixture_check(template.get("fixture_spec"))
    blockers = materialization.get("materialization_blockers")
    if not isinstance(blockers, list):
        blockers = []

    checks = {
        "planned_path_valid": planned.startswith("/Game/"),
        "artifact_model_declared": bool(materialization.get("artifact_model")),
        "status_declared": bool(materialization.get("status")),
        "blockers_declared": bool(blockers),
        "native_parent_declared_when_needed": bool(
            native_parent or materialization.get("presentation_parent")
        ),
        "native_parent_source_found": not bool(class_name) or bool(source_files),
        "adapter_contract_valid_when_declared": adapter_contract is None
        or (adapter_contract_path is not None and adapter_contract_path.is_file()),
        "required_config_allowlist_source_valid": required_config_allowlist_source is None
        or (
            required_config_allowlist_source_path is not None
            and required_config_allowlist_source_path.is_file()
        ),
        "fixture_contract_valid_when_present": fixture is None
        or fixture.get("state") == "L1_contract_spec_only",
        "planned_asset_absent_or_requires_live_readback": not asset_file.is_file(),
    }
    # A documented live-graph/fixture blocker is expected at this stage.  A
    # status explicitly saying that a native adapter or definition bridge is
    # still missing is a true offline stop: materializing the BP would encode
    # an authority that has not been designed yet.
    status = str(materialization.get("status", ""))
    design_blocked = (
        "native_adapter_needed" in status
        or "definition_bridge" in status
        or "cooldown_authority" in status
    )
    # Once an approved live transaction has materialized the planned asset,
    # the offline authoring preflight is no longer the right state label.  Do
    # not call an existing asset an unexplained collision forever: it is now a
    # materialized candidate that still needs independent live readback,
    # compile/export, fixture, and evidence checks.  Keep the absence check in
    # ``checks`` so a future mutation pass can still see the boundary.
    contract_ready = all(
        value
        for key, value in checks.items()
        if key != "planned_asset_absent_or_requires_live_readback"
    )
    offline_ready = contract_ready and not design_blocked and not asset_file.is_file()
    materialized_pending = contract_ready and not design_blocked and asset_file.is_file()
    preflight_status = (
        "blocked"
        if design_blocked or not contract_ready
        else "materialized_requires_live_readback"
        if materialized_pending
        else "ready_for_live_materialization"
    )
    return {
        "id": template.get("id"),
        "planned_blueprint": planned,
        "asset_file": str(asset_file.relative_to(ROOT)).replace("\\", "/"),
        "asset_on_disk": asset_file.is_file(),
        "artifact_model": materialization.get("artifact_model"),
        "status": materialization.get("status"),
        "native_parent": native_parent,
        "native_parent_class": class_name,
        "native_parent_source_files": source_files,
        "adapter_contract": adapter_contract,
        "required_config_allowlist": required_config_allowlist,
        "required_config_allowlist_source": required_config_allowlist_source,
        "fixture": fixture,
        "declared_blockers": blockers,
        "design_blocked": design_blocked,
        "checks": checks,
        "offline_preflight": preflight_status,
        "live_proof_still_required": [
            "read parent/CDO/interfaces/components or definition shape",
            "materialize through one readback-verified editor transaction",
            "compile and export graph or asset reflection",
            "exercise the fixture route and deterministic reset/idempotency",
            "write a fresh evidence envelope before promotion",
        ],
    }


def ordered_live_plan(registry: dict[str, Any], templates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_id = {str(item.get("id")): item for item in templates}
    planned: list[dict[str, Any]] = []
    order = registry.get("template_materialization_order") or [str(item.get("id")) for item in templates]
    for index, template_id in enumerate(order, 1):
        if template_id in by_id:
            planned.append(
                {
                    "step": index,
                    "template": template_id,
                    "planned_blueprint": by_id[template_id]["planned_blueprint"],
                    "precondition": "fresh live fingerprint + independent readback",
                    "postcondition": "compile/export/fixture evidence; no authority duplication",
                }
            )
    # Keep a deterministic content order for any newly added template that has
    # not yet been inserted into the explicit materialization order.
    for template in templates:
        template_id = str(template.get("id"))
        if template_id not in {item["template"] for item in planned}:
            planned.append(
                {
                    "step": len(planned) + 1,
                    "template": template_id,
                    "planned_blueprint": template["planned_blueprint"],
                    "precondition": "fresh live fingerprint + independent readback",
                    "postcondition": "compile/export/fixture evidence; no authority duplication",
                }
            )
    return planned


def live_readonly(paths: list[str]) -> dict[str, Any]:
    """Read Monolith only when explicitly requested and never issue a mutation."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from mcp_client import monolith  # pylint: disable=import-outside-toplevel

    raw_status = monolith("monolith_status", {}, timeout=5)
    result: dict[str, Any] = {
        "requested": True,
        "status": "reachable" if not str(raw_status).startswith("ERROR:") else "unreachable",
        "monolith_status": raw_status,
        "graphs": [],
        "mutations_issued": False,
    }
    if result["status"] == "unreachable":
        return result
    for asset_path in paths:
        raw = monolith(
            "blueprint_query",
            {"action": "list_graphs", "asset_path": asset_path},
            timeout=30,
        )
        if isinstance(raw, str) and raw.startswith("ERROR:"):
            result["graphs"].append({"asset_path": asset_path, "error": raw})
            continue
        try:
            payload = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            payload = {"raw": raw}
        result["graphs"].append({"asset_path": asset_path, "readback": payload})
    return result


def build_report(include_live: bool = False) -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH)
    templates = [template_preflight(item) for item in registry.get("templates", [])]
    report: dict[str, Any] = {
        "schema_version": "1.0",
        "kind": "melodia_blueprint_materialization_preflight",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "registry": str(REGISTRY_PATH.relative_to(ROOT)).replace("\\", "/"),
        "offline_only": not include_live,
        "no_assets_created": True,
        "templates": templates,
        "live_plan": ordered_live_plan(registry, templates),
        "summary": {
            "templates": len(templates),
            "offline_ready": sum(item["offline_preflight"] == "ready_for_live_materialization" for item in templates),
            "blocked": sum(item["offline_preflight"] == "blocked" for item in templates),
            "materialized_requires_live_readback": sum(
                item["offline_preflight"] == "materialized_requires_live_readback"
                for item in templates
            ),
            "planned_asset_collisions": sum(item["asset_on_disk"] for item in templates),
            "native_parents_with_source": sum(
                bool(item["native_parent_class"]) and bool(item["native_parent_source_files"])
                for item in templates
            ),
        },
    }
    if include_live:
        report["live_readonly"] = live_readonly(
            [item["planned_blueprint"] for item in templates if item["asset_on_disk"]]
        )
    else:
        report["live_readonly"] = {
            "requested": False,
            "status": "not_contacted",
            "mutations_issued": False,
        }
    return report


def print_text(report: dict[str, Any]) -> None:
    summary = report["summary"]
    print("Melodia BP materialization preflight (read-only)")
    print(f"  templates: {summary['templates']}")
    print(f"  offline-ready for live authoring: {summary['offline_ready']}")
    print(f"  blocked by missing contract/source detail: {summary['blocked']}")
    print(f"  existing planned assets requiring readback: {summary['planned_asset_collisions']}")
    print(f"  live read-only probe: {report['live_readonly']['status']}")
    print("  assets created by this command: false")
    print()
    for item in report["templates"]:
        fixture = (item.get("fixture") or {}).get("state", "none")
        print(
            f"  {item['id']:<16} {item['offline_preflight']:<32} "
            f"model={item.get('artifact_model') or 'unspecified'} fixture={fixture}"
        )
    print("\n  Live order:")
    for item in report["live_plan"]:
        print(f"    {item['step']}. {item['template']} -> {item['planned_blueprint']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    parser.add_argument(
        "--live-readonly",
        action="store_true",
        help="after Monolith returns, perform status/list_graphs reads only",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="return non-zero if the offline contract is not ready for live authoring",
    )
    args = parser.parse_args(argv)
    try:
        report = build_report(include_live=args.live_readonly)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"materialization preflight failed: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    if args.strict and report["summary"]["blocked"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
