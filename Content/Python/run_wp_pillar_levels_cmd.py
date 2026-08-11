"""Headless entrypoint for setup_wp_pillar_levels.py (all 4 pillars).

  py Content/Python/run_wp_pillar_levels_cmd.py
  py Content/Python/run_wp_pillar_levels_cmd.py --pillar SakuraDream
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON = PROJECT_ROOT / "Content" / "Python"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
LOG = PROJECT_ROOT / "Saved" / "Logs" / "wp_pillar_levels_cmd.log"


def main() -> int:
    if not UE_CMD.exists():
        print(f"Missing: {UE_CMD}")
        return 1

    editor_probe = subprocess.run(
        [
            "powershell",
            "-Command",
            "$p=Get-Process UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue; if ($p) { $p | Select-Object Id,ProcessName; exit 2 }",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if editor_probe.returncode != 0:
        print("Refusing WP commandlet launch while an Unreal editor process is active.")
        if editor_probe.stdout:
            print(editor_probe.stdout.strip())
        return 2

    extra = sys.argv[1:]
    if "--pillar" not in extra and "--all" not in extra:
        extra = ["--all", *extra]
    script = (PYTHON / "setup_wp_pillar_levels.py").as_posix()
    # UE only forwards args embedded in -ExecutePythonScript, not trailing CLI tokens.
    script_with_args = script if not extra else f"{script} {' '.join(extra)}"
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
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
