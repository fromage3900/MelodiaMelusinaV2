#!/usr/bin/env python3
"""emit_math_evidence.py — derive melodia.math.evidence.v1 from run artifacts.

This is the single source of truth for the published evidence JSON. It NEVER
hand-edits numbers: every field is derived from a run artifact on disk.

    python Tools/emit_math_evidence.py

Derives:
  - mcp_tests      : live run of Tools/test_melodia_mcp.py (parsed from stdout)
  - contract_tests : live run of Tools/run_contract_tests.py --json
  - math eval      : Saved/Audit/math_run_latest.json (tool-surface eval)
  - model runs     : Saved/Audit/math_run_models_latest.json (per-model rows)
  - runtime gates  : Saved/gate_ledger.json (latest row per gate id) — a FAIL
                     row that the ledger has since superseded with PASS can
                     never be re-published, and vice versa
  - server         : tool list + policy from deploy/melodia_mcp_server.py and
                     specs/mcp_tool_policy.v1.json

Writes:
  - BS_GodFile/Saved/Audit/math_evidence_<date>.json
  - generated/melodia/status/math_evidence_<date>.json        (workspace root)
  - generated/melodia/status/math_evidence_latest.json
  - my-site-clean/generated/melodia/status/math_evidence_<date>.json
  - my-site-clean/public/melodia/status/math_evidence_<date>.json
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "Saved" / "Audit"
LEDGER = ROOT / "Saved" / "gate_ledger.json"
TOOLS = ROOT / "Tools"
WORKSPACE = Path(r"C:\EnvironmentPortfolio")
STATUS = WORKSPACE / "generated" / "melodia" / "status"
SITE = WORKSPACE / "my-site-clean"

COMPLETION_GATES = {
    "runtime": "Victory/Defeat/Fled/unavailable; each resumes/aborts Quill once",
    "save_load": "Canonical BP_JRPGSaveGame slot across a full process restart",
    "repeat_consume": "melodia:stat: idempotent per IntentId",
    "package_launch": "UE 5.8 packaged Gauntlet passed outside editor",
}
BATTLE_GATES = {
    "battle_encounter": "Encounter triggers via BP_InteractionBattle in MelodiaIntegrationMap",
    "battle_integration_map": "Same PIE session; UI created, battle flows",
}


def _run_py(script: str, args: list[str], timeout: int = 300) -> tuple[int, str]:
    try:
        r = subprocess.run(
            [sys.executable, str(TOOLS / script), *args],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            timeout=timeout,
        )
        return r.returncode, (r.stdout + r.stderr)
    except Exception as exc:  # timeout, OSError
        return 1, str(exc)


def _parse_mcp_tests() -> dict[str, Any]:
    rc, out = _run_py("test_melodia_mcp.py", [])
    m = re.search(r"(\d+)/(\d+)\s+passed", out)
    if not m:
        return {
            "passed": 0,
            "total": 0,
            "failed": 0,
            "runner": "Tools/test_melodia_mcp.py",
            "derived": True,
            "parse_failed": True,
            "exit": rc,
        }
    passed, total = int(m.group(1)), int(m.group(2))
    return {
        "passed": passed,
        "total": total,
        "failed": total - passed,
        "runner": "Tools/test_melodia_mcp.py",
        "derived": True,
        "exit": rc,
    }


def _parse_contract_tests() -> dict[str, Any]:
    rc, out = _run_py("run_contract_tests.py", ["--json"], timeout=600)
    try:
        report = json.loads(out[out.index("{"):])
    except (ValueError, IndexError):
        return {
            "passed": 0,
            "total": 0,
            "coverage_floor": 0,
            "runner": "Tools/run_contract_tests.py",
            "derived": True,
            "parse_failed": True,
            "exit": rc,
        }
    return {
        "passed": report.get("passed", 0),
        "total": report.get("suite_count", report.get("total", 0)),
        "coverage_floor": report.get("coverage_floor", 0),
        "editor_contacted": report.get("editor_contacted", False),
        "runner": "Tools/run_contract_tests.py",
        "derived": True,
        "stamp": datetime.now().strftime("%Y-%m-%dT%H:%M"),
    }


def _latest_gate(rows: list[dict], gate_id: str) -> dict[str, Any] | None:
    matches = [r for r in rows if r.get("id") == gate_id]
    if not matches:
        return None
    matches.sort(key=lambda r: (r.get("date") or "", r.get("time") or ""))
    return matches[-1]


def _runtime_gates(rows: list[dict]) -> dict[str, Any]:
    completion = []
    for gid, what in COMPLETION_GATES.items():
        rec = _latest_gate(rows, gid)
        completion.append({
            "gate": gid,
            "state": (rec.get("status") or "open").upper() if rec else "OPEN",
            "date": rec.get("date", "") if rec else "",
            "note": (rec.get("note") or "")[:200] if rec else what,
        })
    battle = []
    for gid, what in BATTLE_GATES.items():
        rec = _latest_gate(rows, gid)
        battle.append({
            "gate": gid,
            "state": (rec.get("status") or "open").upper() if rec else "OPEN",
            "date": rec.get("date", "") if rec else "",
            "note": (rec.get("note") or "")[:200] if rec else what,
        })
    return {
        "source": "Saved/gate_ledger.json (latest row per gate id; derived, not hand-edited)",
        "completion": completion,
        "battle": battle,
        "historical_fail_rows_are_not_standing": True,
    }


def _model_runs() -> dict[str, Any]:
    latest = AUDIT / "math_run_models_latest.json"
    if not latest.is_file():
        return {"runs": [], "note": "no math_run_models_latest.json on disk"}
    try:
        bundle = json.loads(latest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"runs": [], "note": "math_run_models_latest.json unparseable"}
    runs = []
    for r in bundle.get("runs") or []:
        if not isinstance(r, dict) or r.get("kind") != "model_via_hermes_harness":
            continue
        runs.append({
            "model": r.get("model"),
            "backend": r.get("backend"),
            "captured_at": r.get("captured_at"),
            "passed": r.get("passed"),
            "total": r.get("total"),
            "held": r.get("held"),
            "tca_pct": r.get("tca_pct"),
            "arg_pct": r.get("arg_pct"),
            "exec_pct": r.get("exec_pct"),
            "ter_ratio": r.get("ter_ratio"),
            "ter_meets_target": r.get("ter_meets_target"),
        })
    return {"runs": runs, "updated_at": bundle.get("updated_at")}


def _math_eval() -> dict[str, Any]:
    latest = AUDIT / "math_run_latest.json"
    if not latest.is_file():
        return {"note": "no math_run_latest.json on disk"}
    try:
        r = json.loads(latest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"note": "math_run_latest.json unparseable"}
    return {
        "captured_at": r.get("captured_at"),
        "editor_contacted": r.get("editor_contacted"),
        "passed": r.get("passed"),
        "total": r.get("total"),
        "held": r.get("held"),
        "tca_pct": r.get("tca_pct"),
        "tasks_spec": r.get("tasks_spec"),
    }


def _server_surface() -> dict[str, Any]:
    try:
        sys.path.insert(0, str(ROOT))
        import deploy.melodia_mcp_server as server

        tools = [str(t.get("name")) for t in getattr(server, "TOOLS", []) if t.get("name")]
    except Exception:
        tools = []
    policy = ROOT / "specs" / "mcp_tool_policy.v1.json"
    default_decision = "deny"
    if policy.is_file():
        try:
            default_decision = json.loads(policy.read_text(encoding="utf-8")).get("default_decision", "deny")
        except json.JSONDecodeError:
            pass
    return {
        "entrypoint": "deploy/melodia_mcp_server.py",
        "tool_count": len(tools),
        "tools": tools,
        "policy": {
            "default_decision": default_decision,
            "file": "specs/mcp_tool_policy.v1.json",
        },
    }


def _build() -> dict[str, Any]:
    rows = []
    if LEDGER.is_file():
        try:
            rows = json.loads(LEDGER.read_text(encoding="utf-8")).get("gates") or []
        except json.JSONDecodeError:
            rows = []
    mcp = _parse_mcp_tests()
    contract = _parse_contract_tests()
    evidence = {
        "schema": "melodia.math.evidence.v1",
        "captured_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "derived_from": [
            "Saved/gate_ledger.json",
            "Saved/Audit/math_run_latest.json",
            "Saved/Audit/math_run_models_latest.json",
            "Tools/test_melodia_mcp.py (live)",
            "Tools/run_contract_tests.py --json (live)",
        ],
        "command": "python Tools/emit_math_evidence.py",
        "mcp_tests": mcp,
        "contract_tests": contract,
        "math_eval": _math_eval(),
        "model_runs": _model_runs(),
        "server": _server_surface(),
        "runtime_gates_documented": _runtime_gates(rows),
        "not_claimed": [
            "No public 100-task LLM eval log (no TCA/PAR/SCR/RCF/TER run JSON).",
            "No certified Hermes 3 / LongCat scorecard on disk.",
            "A model lane is PASS only when its run JSON exists; tag presence is installation, not evidence.",
        ],
    }
    return evidence


def _write_all(evidence: dict[str, Any]) -> list[Path]:
    stamp = datetime.now().strftime("%Y-%m-%d")
    name = f"math_evidence_{stamp}.json"
    text = json.dumps(evidence, indent=2)
    targets = [
        AUDIT / name,
        STATUS / name,
        STATUS / "math_evidence_latest.json",
        SITE / "generated" / "melodia" / "status" / name,
        SITE / "public" / "melodia" / "status" / name,
    ]
    written = []
    for t in targets:
        try:
            t.parent.mkdir(parents=True, exist_ok=True)
            t.write_text(text, encoding="utf-8")
            written.append(t)
        except OSError as exc:
            print(f"  ! {t}: {exc}")
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print the evidence JSON to stdout")
    args = parser.parse_args(argv)
    evidence = _build()
    written = _write_all(evidence)
    if args.json:
        print(json.dumps(evidence, indent=2))
    else:
        m = evidence["mcp_tests"]
        c = evidence["contract_tests"]
        e = evidence["math_eval"]
        print(
            f"evidence {evidence['captured_at']}: "
            f"MCP {m.get('passed')}/{m.get('total')}  contract {c.get('passed')}/{c.get('total')}  "
            f"math {e.get('passed')}/{e.get('total')}"
        )
        for p in written:
            print(f"  -> {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())