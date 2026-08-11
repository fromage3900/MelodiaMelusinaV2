"""Shell launcher for storybook PP rebuild (no unreal import)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
SCRIPT = PROJECT_ROOT / "Content/Python/setup_storybook_outline_rebuild.py"
LOG = PROJECT_ROOT / "Saved" / "Logs" / "storybook_rebuild.log"


def main() -> int:
    if not UE_CMD.exists():
        print(f"ERROR: {UE_CMD}")
        return 1
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={SCRIPT.as_posix()}",
        "-stdout",
        "-unattended",
        "-nosplash",
        f"-log={LOG}",
    ]
    print(f"Storybook rebuild -> {LOG}")
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
