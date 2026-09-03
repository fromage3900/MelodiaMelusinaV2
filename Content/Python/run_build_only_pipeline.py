"""Build-only pipeline: new MFs, masters, instances — skips Melodia master conversion."""
from __future__ import annotations

import subprocess
import sys
import time
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


def _run_build() -> int:
    import unreal

    unreal.log("=== Build-only material pipeline ===")
    time.sleep(5)

    import setup_material_functions as mf
    mf.main()

    import setup_impressionist_materials as imp
    imp.build_all()

    import setup_master_toon as master_toon
    master_toon.build_all()

    import setup_sdf_maturation as sdf_mat
    sdf_mat.build_all()

    import setup_audio_outline as audio_pp
    audio_pp.build_all()

    import ensure_portfolio_instances as ensure
    ensure.main()

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log("=== Build-only pipeline complete ===")
    return 0


def main() -> int:
    if _in_unreal():
        return _run_build()

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "build_only_pipeline.log"
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={(PYTHON_DIR / 'run_build_only_pipeline.py').as_posix()}",
        "-stdout",
        "-unattended",
        "-nosplash",
        f"-log={log_path}",
    ]
    print(f"Running build-only UE pipeline -> {log_path}")
    proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
