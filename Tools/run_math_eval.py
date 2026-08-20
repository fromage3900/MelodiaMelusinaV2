#!/usr/bin/env python3
"""Deterministic MATH harness eval: score MCP tools, not an LLM.

    python Tools/run_math_eval.py
    python Tools/run_math_eval.py --json

Writes Saved/Audit/math_run_<stamp>.json and updates
generated/melodia/status/math_evidence latest pointer when the sibling
EnvironmentPortfolio tree exists.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "specs" / "mcp" / "math_tasks.v1.json"
AUDIT = ROOT / "Saved" / "Audit"


def _check(result: dict[str, Any], task: dict[str, Any]) -> tuple[bool, str]:
    for key, expected in (task.get("expect") or {}).items():
        got = result.get(key)
        if got != expected:
            return False, f"{key}: got {got!r} want {expected!r}"
    for key in task.get("expect_keys") or []:
        if key not in result:
            return False, f"missing key {key}"
    for key, n in (task.get("expect_min_len") or {}).items():
        val = result.get(key)
        if not isinstance(val, list) or len(val) < n:
            return False, f"{key} len {0 if not isinstance(val, list) else len(val)} < {n}"
    for key, n in (task.get("expect_len") or {}).items():
        val = result.get(key)
        if not isinstance(val, list) or len(val) != n:
            return False, f"{key} len {0 if not isinstance(val, list) else len(val)} != {n}"
    for parent, nested_keys in (task.get("expect_nested_keys") or {}).items():
        parent_val = result.get(parent)
        if not isinstance(parent_val, dict):
            return False, f"{parent} is not an object"
        for nk in nested_keys:
            if nk not in parent_val:
                return False, f"missing nested key {parent}.{nk}"
    return True, "ok"


def _monolith_live() -> bool:
    try:
        import deploy.melodia_mcp_server as server

        return bool(getattr(server, "_monolith_is_live", lambda: False)())
    except Exception:
        return False


def run_eval() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT))
    spec = json.loads(TASKS.read_text(encoding="utf-8"))
    import deploy.melodia_mcp_server as server

    editor_live = _monolith_live()
    rows = []
    passed = 0
    held = 0
    for task in spec["tasks"]:
        if task.get("editor_required") and not editor_live:
            held += 1
            rows.append({
                "id": task["id"],
                "tool": task["tool"],
                "pass": False,
                "status": "hold",
                "detail": "editor_required — Monolith unreachable on :9316",
            })
            continue

        fn = getattr(server, task["tool"], None)
        if fn is None:
            rows.append({"id": task["id"], "tool": task["tool"], "pass": False, "detail": "tool missing"})
            continue
        try:
            result = fn(**(task.get("args") or {}))
        except TypeError:
            result = fn() if not task.get("args") else fn(**task["args"])
        except Exception as exc:
            rows.append({"id": task["id"], "tool": task["tool"], "pass": False, "detail": str(exc)})
            continue
        if not isinstance(result, dict):
            rows.append({"id": task["id"], "tool": task["tool"], "pass": False, "detail": "non-dict result"})
            continue
        ok, detail = _check(result, task)
        if ok:
            passed += 1
        rows.append({
            "id": task["id"],
            "tool": task["tool"],
            "pass": ok,
            "status": "pass" if ok else "fail",
            "detail": detail,
        })

    total = len(spec["tasks"])
    scored = total - held
    tca = round(100.0 * passed / scored, 1) if scored else 0.0
    report = {
        "schema": "melodia.math_run.v1",
        "kind": "harness_self_eval",
        "model": "none",
        "note": "Scores the MCP tool surface with golden expects. Not an LLM leaderboard.",
        "captured_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "editor_contacted": editor_live,
        "tasks_spec": str(TASKS.relative_to(ROOT)).replace("\\", "/"),
        "passed": passed,
        "total": total,
        "failed": scored - passed,
        "held": held,
        "tca_pct": tca,
        "tasks": rows,
    }
    return report


def write_report(report: dict[str, Any]) -> Path:
    AUDIT.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d")
    path = AUDIT / f"math_run_{stamp}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    latest = AUDIT / "math_run_latest.json"
    latest.write_text(json.dumps(report, indent=2), encoding="utf-8")
    sibling = Path(r"C:\EnvironmentPortfolio\generated\melodia\status")
    if sibling.is_dir():
        (sibling / "math_run_latest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    report = run_eval()
    path = write_report(report)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        held_note = f"  held={report['held']}" if report.get("held") else ""
        print(
            f"MATH harness eval: {report['passed']}/{report['total']}  "
            f"TCA={report['tca_pct']}%{held_note}  ({path.name})"
        )
        for row in report["tasks"]:
            if row.get("status") == "hold":
                print(f"  HOLD  {row['id']}  {row['detail']}")
                continue
            mark = "PASS" if row["pass"] else "FAIL"
            extra = "" if row["pass"] else f"  {row['detail']}"
            print(f"  {mark}  {row['id']}{extra}")
    return 0 if report["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
