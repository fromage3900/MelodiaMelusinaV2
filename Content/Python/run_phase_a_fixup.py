"""Phase A fixup: MeshBlend rewire, texture rewire, toon convert + finish, audits.

Run from shell:
  python Content/Python/run_phase_a_fixup.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON_DIR = PROJECT_ROOT / "Content" / "Python"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
LOG_DIR = PROJECT_ROOT / "Saved" / "Logs"


def _in_unreal() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _run_in_ue() -> int:
    import rewire_portfolio_texture_refs as tex

    tex.main()

    import setup_master_universal as universal
    universal.build()

    import convert_masters_to_substrate_toon as conv

    sys.argv = ["convert", "--batch", "all", "--fix-params", "--assign-profiles"]
    conv.main()

    sys.argv = ["convert", "--batch", "all", "--finish", "--assign-profiles"]
    conv.main()

    import ensure_portfolio_instances as ensure

    ensure.main()

    import unreal

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    return 0


def main() -> int:
    if _in_unreal():
        return _run_in_ue()

    if not UE_CMD.exists():
        print(f"ERROR: {UE_CMD} not found")
        return 1

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    for script in (
        "patch_portfolio_texture_paths.py",
    ):
        subprocess.run([sys.executable, str(PYTHON_DIR / script)], cwd=str(PROJECT_ROOT), check=False)

    log_path = LOG_DIR / "phase_a_fixup.log"
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={(PYTHON_DIR / 'run_phase_a_fixup.py').as_posix()}",
        "-stdout",
        "-unattended",
        "-nosplash",
        f"-log={log_path}",
    ]
    print(f"Phase A fixup -> {log_path}")
    proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT))

    for script in ("audit_material_library.py", "audit_material_parameters.py"):
        subprocess.run([sys.executable, str(PYTHON_DIR / script)], cwd=str(PROJECT_ROOT), check=False)

    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
