"""Rebuild fixed masters + run toon conversion on Melodia copies."""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON_DIR = PROJECT_ROOT / "Content" / "Python"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


def _in_unreal() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _run() -> int:
    import unreal

    time.sleep(5)
    import setup_master_toon as mt
    mt.build_all()
    import setup_sdf_maturation as sdf
    sdf.build_all()


    sys.argv = ["run_toon_conversion.py", "--batch", "all", "--fix-params", "--assign-profiles"]
    from convert_masters_to_substrate_toon import main as convert_main
    convert_main()

    import ensure_portfolio_instances as ensure
    ensure.main()

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    return 0


def main() -> int:
    if _in_unreal():
        return _run()
    subprocess.run([sys.executable, str(PYTHON_DIR / "restore_portfolio_textures.py")], cwd=str(PROJECT_ROOT))
    subprocess.run([sys.executable, str(PYTHON_DIR / "restore_portfolio_masters.py")], cwd=str(PROJECT_ROOT))
    cmd = [
        str(UE_CMD), str(UPROJECT),
        f"-ExecutePythonScript={(PYTHON_DIR / 'run_convert_only_pipeline.py').as_posix()}",
        "-stdout", "-unattended", "-nosplash",
    ]
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
