#!/usr/bin/env python3
"""Read-only owner gate for the Melodia rebuild and live-authoring handoff.

This command never terminates a process, starts Unreal, contacts Monolith, or
mutates project files. It distinguishes a compile-safe boundary (no editor or
command-line editor process) from a live-read-only boundary (exactly one editor
and a listening Monolith endpoint). Modal/import activity in the newest editor
log is reported as a warning rather than silently treated as clean evidence.

Usage:
    python Tools/melodia_rebuild_preflight.py
    python Tools/melodia_rebuild_preflight.py --json
    python Tools/melodia_rebuild_preflight.py --strict-compile
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "Saved" / "Logs"
PROCESS_NAMES = ("UnrealEditor", "UnrealEditor-Cmd", "monolith_proxy")
ACTIVE_LOG_MARKERS = (
    "LogMonolith: Warning: MODAL_OPEN",
    "LogInterchangeEngine: Display: Interchange start",
    "LogSavePackage: Moving",
)


def powershell_json(script: str) -> list[dict[str, Any]]:
    completed = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout).strip() or "PowerShell query failed")
    value = json.loads(completed.stdout or "[]")
    if isinstance(value, dict):
        return [value]
    if not isinstance(value, list):
        raise RuntimeError("PowerShell query returned a non-array")
    return value


def process_snapshot() -> list[dict[str, Any]]:
    names = ",".join(f"'{name}.exe'" for name in PROCESS_NAMES)
    script = (
        f"$items = Get-Process -Name {','.join(name for name in PROCESS_NAMES)} "
        "-ErrorAction SilentlyContinue | "
        "Select-Object Id,ProcessName,StartTime,Responding; "
        "$items | ConvertTo-Json -Compress"
    )
    # Keep the explicit names string above for documentation and avoid relying
    # on wildcard process enumeration; PowerShell accepts comma-separated names.
    del names
    return powershell_json(script)


def port_snapshot() -> list[dict[str, Any]]:
    script = (
        "if (Get-Command Get-NetTCPConnection -ErrorAction SilentlyContinue) { "
        "$rows = @(Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 9316 "
        "-State Listen -ErrorAction SilentlyContinue | "
        "Select-Object LocalAddress,LocalPort,State,OwningProcess) "
        "} else { "
        "$rows = @(netstat -ano -p TCP | Select-String "
        "-Pattern '\\s127\\.0\\.0\\.1:9316\\s+.*LISTENING\\s+\\d+$' | "
        "ForEach-Object { "
        "$match = [regex]::Match($_.ToString(), "
        "'\\s(?<local>127\\.0\\.0\\.1:9316)\\s+(?<remote>\\S+)\\s+LISTENING\\s+(?<pid>\\d+)$'); "
        "if ($match.Success) { [pscustomobject]@{ LocalAddress='127.0.0.1'; "
        "LocalPort=9316; State='Listen'; OwningProcess=[int]$match.Groups['pid'].Value } } "
        "} ) "
        "} $rows | ConvertTo-Json -Compress"
    )
    return powershell_json(script)


def newest_log_snapshot() -> dict[str, Any]:
    logs = sorted(LOG_DIR.glob("*.log"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not logs:
        return {"path": None, "recent_markers": [], "last_write_time": None}
    path = logs[0]
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-300:]
    except OSError as exc:
        return {"path": str(path), "recent_markers": [], "read_error": str(exc)}
    markers = sorted({marker for line in lines for marker in ACTIVE_LOG_MARKERS if marker in line})
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "last_write_time": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
        "recent_markers": markers,
        "recent_pie": any("PIE:" in line or "LogPlayLevel: PlayLevel" in line for line in lines),
    }


def build_report() -> dict[str, Any]:
    try:
        processes = process_snapshot()
        port = port_snapshot()
        query_error = None
    except (OSError, RuntimeError, json.JSONDecodeError) as exc:
        processes = []
        port = []
        query_error = str(exc)

    counts = {name: 0 for name in PROCESS_NAMES}
    for process in processes:
        name = str(process.get("ProcessName", ""))
        if name in counts:
            counts[name] += 1

    blockers: list[str] = []
    if query_error:
        blockers.append(f"process/port query failed: {query_error}")
    if counts["UnrealEditor"]:
        blockers.append(f"{counts['UnrealEditor']} UnrealEditor process(es) still own the checkout")
    if counts["UnrealEditor-Cmd"]:
        blockers.append(f"{counts['UnrealEditor-Cmd']} UnrealEditor-Cmd process(es) still run")
    if not port:
        blockers.append("Monolith 127.0.0.1:9316 is not listening")

    log = newest_log_snapshot()
    report = {
        "schema_version": "1.0",
        "kind": "melodia_rebuild_preflight",
        "read_only": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "process_counts": counts,
        "processes": processes,
        "monolith_listeners": port,
        "newest_log": log,
        "blockers": blockers,
        "safe_to_compile": not query_error and counts["UnrealEditor"] == 0 and counts["UnrealEditor-Cmd"] == 0,
        "safe_for_live_readonly": not query_error and counts["UnrealEditor"] == 1 and bool(port),
        "mutations_issued": False,
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    parser.add_argument(
        "--strict-compile",
        action="store_true",
        help="return non-zero unless the checkout is compile-safe",
    )
    args = parser.parse_args(argv)
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("Melodia rebuild preflight (read-only)")
        print(f"  UnrealEditor: {report['process_counts']['UnrealEditor']}")
        print(f"  UnrealEditor-Cmd: {report['process_counts']['UnrealEditor-Cmd']}")
        print(f"  monolith_proxy: {report['process_counts']['monolith_proxy']}")
        print(f"  Monolith 9316 listening: {bool(report['monolith_listeners'])}")
        print(f"  safe to compile: {report['safe_to_compile']}")
        print(f"  safe for live read-only: {report['safe_for_live_readonly']}")
        print(f"  mutations issued: {report['mutations_issued']}")
        if report["blockers"]:
            print("  blockers:")
            for blocker in report["blockers"]:
                print(f"    - {blocker}")
        log = report["newest_log"]
        if log.get("recent_markers"):
            print(f"  newest-log activity markers: {', '.join(log['recent_markers'])}")
    return 0 if (not args.strict_compile or report["safe_to_compile"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
