#!/usr/bin/env python3
"""Run every offline contract suite with an explicit coverage floor.

The repository intentionally contains script-style assertion suites as well as a
small number of unittest/pytest-shaped files.  Calling ``pytest Tools`` is not a
valid gate here: most script suites collect zero tests, and this checkout may not
have pytest installed at all.  This runner invokes each suite as a process and
requires a suite-specific success marker, so a green process with zero observed
assertion output fails closed.

No editor, Unreal, network, AWS, or Monolith access is used.

Usage:
    python Tools/run_contract_tests.py
    python Tools/run_contract_tests.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Pattern


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Suite:
    path: str
    success_pattern: Pattern[str]


SUITES = (
    Suite("Tools/test_echo_contract.py", re.compile(r"===\s+(\d+)/(\d+) passed ===")),
    Suite("Tools/test_t3d_safe_wire.py", re.compile(r"===\s+(\d+)/(\d+) passed ===")),
    Suite("Tools/test_t3d_request_contract.py", re.compile(r"validated T3D request schema")),
    Suite("Tools/test_melodia_content_fixtures.py", re.compile(r"validated \d+ Melodia fixture specs")),
    Suite("Tools/test_melodia_bp_readiness.py", re.compile(r"validated Blueprint readiness inventory")),
    Suite("Tools/test_melodia_bp_materialization_preflight.py", re.compile(r"validated materialization preflight")),
    Suite("Tools/test_melodia_skill_bridge_contract.py", re.compile(r"validated skill bridge contract")),
    Suite("Tools/test_melodia_native_adapter_contract.py", re.compile(r"validated native adapter contract surfaces")),
    Suite("Tools/test_melodia_bp_registry_contract.py", re.compile(r"validated BP registry/fixture parity")),
    Suite("Tools/test_melodia_blessing_burden_contract.py", re.compile(r"validated Blessing/Burden contract")),
    Suite("Tools/test_melodia_wardrobe_transaction_contract.py", re.compile(r"validated Melodia wardrobe transaction contract")),
    Suite("Tools/test_melusina_skin_topology_contract.py", re.compile(r"validated Melusina skin topology contract")),
    Suite("Tools/test_validate_source_control_ownership.py", re.compile(r"source-control ownership validator contract \(4 assertions\)")),
    Suite("Tools/test_art_gates_authority.py", re.compile(r"Ran\s+4 tests.*\bOK\b", re.S)),
    Suite("Tools/test_artdrop_archive.py", re.compile(r"Ran\s+3 tests.*\bOK\b", re.S)),
    Suite("Tools/test_melodia_package_launch_contract.py", re.compile(r"validated Melusina package-launch montage contract")),
    Suite("Tools/test_mcp_policy.py", re.compile(r"mcp-policy-tests:\s+\d+/\d+ passed")),
    Suite("Tools/test_mcp_registration.py", re.compile(r"validated checked-in MCP registration policy")),
    Suite("Tools/test_evidence_envelope.py", re.compile(r"Ran\s+\d+ tests.*\bOK\b", re.S)),
    Suite("Tools/test_ollama_health.py", re.compile(r"Ran\s+\d+ tests.*\bOK\b", re.S)),
    Suite("Tools/test_ui_style_audit.py", re.compile(r"===\s+(\d+)/(\d+) passed ===")),
    Suite("Tools/test_melusina_anim_unit_guard.py", re.compile(r'"ok"\s*:\s*true')),
    Suite("Docs/T3D_Baseline/test_canonical.py", re.compile(r"===\s+(\d+)/(\d+) passed ===")),
)

# This is intentionally independent of len(SUITES): removing a suite must make
# the gate fail instead of lowering its own coverage floor.
MINIMUM_SUITE_COUNT = 23


def run_suite(suite: Suite) -> dict[str, object]:
    path = ROOT / suite.path
    result: dict[str, object] = {"path": suite.path, "exists": path.is_file()}
    if not path.is_file():
        result.update({"status": "fail", "reason": "suite file missing"})
        return result

    completed = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    marker_match = suite.success_pattern.search(output)
    marker_ok = marker_match is not None
    if marker_ok and marker_match and len(marker_match.groups()) >= 2:
        try:
            observed, total = (int(marker_match.group(1)), int(marker_match.group(2)))
            marker_ok = observed > 0 and observed == total
        except (TypeError, ValueError):
            marker_ok = False
    status = "pass" if completed.returncode == 0 and marker_ok else "fail"
    result.update(
        {
            "status": status,
            "returncode": completed.returncode,
            "success_marker_observed": marker_ok,
            "output_tail": output[-1200:],
        }
    )
    if completed.returncode != 0:
        result["reason"] = "suite returned non-zero"
    elif not marker_ok:
        result["reason"] = "suite returned zero without its assertion-bearing success marker"
    return result


def build_report() -> dict[str, object]:
    results = [run_suite(suite) for suite in SUITES]
    passed = sum(item.get("status") == "pass" for item in results)
    return {
        "schema_version": "1.0",
        "kind": "melodia_offline_contract_test_report",
        "runner": "Tools/run_contract_tests.py",
        "editor_contacted": False,
        "pytest_required": False,
        "suite_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "coverage_floor": MINIMUM_SUITE_COUNT,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable report")
    parser.add_argument("--ci", action="store_true", help="CI mode; same checks, concise output")
    args = parser.parse_args(argv)
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for item in report["results"]:
            print(f"{'PASS' if item['status'] == 'pass' else 'FAIL'}  {item['path']}")
            if item["status"] != "pass" and not args.ci:
                print(item.get("output_tail", ""))
        print(
            f"contract suites: {report['passed']}/{report['suite_count']} passed; "
            f"coverage floor={report['coverage_floor']}"
        )
    return 0 if (
        report["failed"] == 0
        and report["passed"] == len(SUITES)
        and len(SUITES) >= report["coverage_floor"]
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
