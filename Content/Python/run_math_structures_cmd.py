"""Headless entrypoint for generate_math_structures.py.

  py Content/Python/run_math_structures_cmd.py
  py Content/Python/run_math_structures_cmd.py --run 1
  py Content/Python/run_math_structures_cmd.py --structure TorusKnot_2_3
  py Content/Python/run_math_structures_cmd.py --dry
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON = PROJECT_ROOT / "Content" / "Python"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
LOG = PROJECT_ROOT / "Saved" / "Logs" / "math_structures_cmd.log"


def main() -> int:
    extra = sys.argv[1:]
    if "--dry" in extra:
        import generate_math_structures as gms
        return gms.main(extra)

    if not UE_CMD.exists():
        print(f"Missing: {UE_CMD}")
        print("Falling back to dry-run audit (no mesh bake).")
        import generate_math_structures as gms
        return gms.main(["--dry", "--run", "1", *extra])

    probe = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "$p=Get-Process UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue; if ($p) { $p | Select-Object Id,ProcessName; exit 2 }",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        print("Refusing math-structure commandlet launch while an Unreal editor process is active.")
        if probe.stdout:
            print(probe.stdout.strip())
        return 2

    if "--run" not in extra and "--structure" not in extra and "--all" not in extra:
        extra = ["--run", "1", *extra]
    script = (PYTHON / "generate_math_structures.py").as_posix()
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
