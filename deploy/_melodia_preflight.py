"""One-writer preflight for headless gate runs (freeze rule: one writer).

Why this exists
---------------
On 2026-09-18 the full builder gate crashed mid-run (gate D) while three Blender
processes were live (two interactive sessions + the gate). It passed when run
with fewer contenders. A gate result is only trustworthy when nothing else is
mutating Blender state at the same time -- and the meltdown class the freeze doc
warns about ("five crash reports in one hour, assets changing mid-edit") is the
same hazard one level up.

This script does NOT launch Blender. It answers one question: is it safe to start
a gate right now? Call it immediately before a `blender --background --python`
gate.

Usage
-----
    python deploy/_melodia_preflight.py            # refuse if ANY blender.exe runs
    python deploy/_melodia_preflight.py --allow-interactive   # allow idle interactive, refuse a second gate
    python deploy/_melodia_preflight.py --allow-any           # report only (never refuse)
    python deploy/_melodia_preflight.py --json                # machine-readable

Exit codes
----------
    0  clear to run a gate
    3  blocked (contending Blender process(es) present)
    2  could not determine process state (treat as unsafe)
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys

GATE_MARKER = "--background"


def _via_powershell() -> list[str] | None:
    """Return blender.exe command lines via PowerShell CIM, or None if unavailable."""
    ps = shutil.which("powershell") or shutil.which("pwsh")
    if ps is None:
        return None
    cmd = [
        ps, "-NoProfile", "-NonInteractive", "-Command",
        "Get-CimInstance Win32_Process -Filter \"Name='blender.exe'\" | "
        "ForEach-Object { $_.CommandLine }",
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
    except Exception:
        return None
    if out.returncode != 0:
        return None
    lines = [ln.strip() for ln in (out.stdout or "").splitlines() if ln.strip()]
    return lines


def _via_tasklist() -> list[str] | None:
    """Count-only fallback (no command line). Empty string == interactive/unknown."""
    if shutil.which("tasklist") is None:
        return None
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq blender.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=25,
        )
    except Exception:
        return None
    if out.returncode != 0:
        return None
    count = sum(1 for ln in (out.stdout or "").splitlines() if ln.strip().startswith('"'))
    return [""] * count


def blender_processes() -> list[dict] | None:
    """[{'cmd': str, 'gate': bool}] for each blender.exe, or None if undeterminable."""
    lines = _via_powershell()
    if lines is None:
        lines = _via_tasklist()
    if lines is None:
        return None
    return [{"cmd": ln, "gate": GATE_MARKER in ln} for ln in lines]


def main() -> int:
    ap = argparse.ArgumentParser(description="One-writer preflight for Blender gate runs")
    ap.add_argument("--allow-interactive", action="store_true",
                    help="Allow idle interactive Blender session(s); still refuse a 2nd gate.")
    ap.add_argument("--allow-any", action="store_true",
                    help="Report only; never refuse (use only when you know why).")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    procs = blender_processes()
    if procs is None:
        print("PREFLIGHT: could not determine blender.exe state (assuming UNSAFE).", file=sys.stderr)
        return 2

    gates = [p for p in procs if p["gate"]]
    interactive = [p for p in procs if not p["gate"]]
    total = len(procs)

    if args.json:
        print(json.dumps({"total": total, "gates": gates, "interactive": interactive}, indent=2))

    blocked = False
    reason = ""
    if total == 0:
        reason = "no other blender.exe running"
    elif args.allow_any:
        reason = f"{total} blender.exe running (--allow-any)"
    elif gates:
        blocked = True
        reason = f"{len(gates)} gate (--background) process(es) already running"
    elif interactive and not args.allow_interactive:
        blocked = True
        reason = f"{len(interactive)} interactive blender.exe running (close it, or pass --allow-interactive)"
    else:
        reason = f"{len(interactive)} interactive blender.exe (allowed by --allow-interactive)"

    if blocked:
        print(f"PREFLIGHT: BLOCKED - {reason}", file=sys.stderr)
        for p in procs:
            print(f"  {'[gate]' if p['gate'] else '[interactive]'} {p['cmd'][:120]}", file=sys.stderr)
        print("A gate run here risks the crash/mis-compare class. Close the session(s) and retry.",
              file=sys.stderr)
        return 3

    print(f"PREFLIGHT: OK - {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
