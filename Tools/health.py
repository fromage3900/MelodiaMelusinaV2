#!/usr/bin/env python3
"""
health.py - single entry point for the Melodia project health command.

Prints a one-screen pass/hold/fail summary to stdout and regenerates
Saved/project_health.html (and Saved/Audit/project_health_claims.json) so the
dashboard and the terminal agree.

This is the command a contributor runs to verify the project, and the command
the CI workflow runs on push/PR.

Usage:
    python Tools/health.py                 # summary + dashboard
    python Tools/health.py --json          # also write claims JSON
    python Tools/health.py --open          # open the dashboard in a browser
    python Tools/health.py --watch         # regenerate every 10s

The offline slice (contract parse, policy parse, baseline existence, doc links,
UTF-8 hygiene) runs without the editor. Editor-backed claims (completion gates)
are HOLD when Monolith is not reachable on 9316.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DASHBOARD = HERE / "project_health_dashboard.py"


def main() -> int:
    parser = argparse.ArgumentParser(description="Melodia project health - one command")
    parser.add_argument("--json", action="store_true", help="also write Saved/Audit/project_health_claims.json")
    parser.add_argument("--open", action="store_true", help="open the dashboard in a browser after writing")
    parser.add_argument("--watch", action="store_true", help="regenerate every 10s")
    args = parser.parse_args()

    if not DASHBOARD.exists():
        print(f"[FAIL] {DASHBOARD} missing")
        return 1

    extra = []
    if args.json:
        extra.append("--json")
    if args.open:
        extra.append("--open")
    if args.watch:
        extra.append("--watch")
    rc = subprocess.call([sys.executable, str(DASHBOARD), *extra], cwd=HERE.parent)
    return rc


if __name__ == "__main__":
    sys.exit(main())
