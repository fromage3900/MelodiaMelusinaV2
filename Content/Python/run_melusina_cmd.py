"""Standalone entrypoint for Melusina rig assessment + setup.

Usage (from a terminal, NOT inside UE):
  py Content/Python/run_melusina_cmd.py
  py Content/Python/run_melusina_cmd.py --verify-only
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON = PROJECT_ROOT / "Content" / "Python"
UE_CMD = Path(
    r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
)
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
LOG = PROJECT_ROOT / "Saved" / "Logs" / "melusina_cmd.log"


def main() -> int:
    if not UE_CMD.exists():
        print(f"ERROR: UnrealEditor-Cmd.exe not found at {UE_CMD}")
        return 1
    if not UPROJECT.exists():
        print(f"ERROR: Project not found at {UPROJECT}")
        return 1

    # --dry-run flag just prints what would run
    dry_run = "--dry-run" in sys.argv

    # Determine which script to run
    extra_args = [a for a in sys.argv[1:] if not a.startswith("--")]
    script_name = "run_melusina_all.py"
    if "--verify-only" in sys.argv:
        script_name = "assess_melusina_rig.py"
    elif "--setup-only" in sys.argv:
        script_name = "setup_melusina_exploration.py"
    elif "--bridge-only" in sys.argv:
        script_name = "bridge_melusina_to_mpc.py"
    elif "--verify-all" in sys.argv:
        script_name = "verify_rhythm_battle_system.py"

    script = script_name  # relative to Content/Python/
    script_with_args = script if not extra_args else f"{script} {' '.join(extra_args)}"

    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={script_with_args}",
        "-stdout",
        "-unattended",
        "-nosplash",
        f"-log={LOG}",
    ]

    print(">>>", " ".join(cmd))
    if dry_run:
        return 0

    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))

    if result.returncode != 0:
        print(f"ERROR: UE exited with code {result.returncode}")
    else:
        print(f"OK. Audit reports: {PROJECT_ROOT}/Saved/Audit/melusina_*.json")
        print(f"Log: {LOG}")

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
