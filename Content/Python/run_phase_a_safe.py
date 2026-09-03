"""Phase A without universal rebuild — safe for headless after SDF port.

  python Content/Python/run_phase_a_safe.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON = PROJECT_ROOT / "Content" / "Python"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _run_in_ue() -> int:
    import convert_masters_to_substrate_toon as conv
    import ensure_portfolio_instances as ensure
    import unreal

    unreal.log("=== PHASE A SAFE (convert only, no rewire/inventory) ===")

    sys.argv = ["convert", "--batch", "1", "--fix-params", "--assign-profiles"]
    conv.main()

    sys.argv = ["convert", "--batch", "2", "--fix-params"]
    conv.main()

    sys.argv = ["convert", "--batch", "3", "--fix-params"]
    conv.main()

    sys.argv = ["convert", "--batch", "4", "--fix-params"]
    conv.main()

    ensure.main()
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    return 0


def main() -> int:
    if _in_ue():
        return _run_in_ue()

    for script in ("repair_crash_assets.py",):
        subprocess.run([sys.executable, str(PYTHON / script)], cwd=str(PROJECT_ROOT), check=False)

    log = PROJECT_ROOT / "Saved" / "Logs" / "phase_a_safe.log"
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={(PYTHON / 'run_phase_a_safe.py').as_posix()}",
        "-stdout",
        "-unattended",
        "-nosplash",
        f"-log={log}",
    ]
    print(f"Phase A safe -> {log}")
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
