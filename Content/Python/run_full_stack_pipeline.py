"""Full-stack material library pipeline Ã¢â‚¬â€ all plan phases in one UE run.

Run from shell (patches filesystem first, then UE):
  python Content/Python/run_full_stack_pipeline.py

Run inside UE only:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/run_full_stack_pipeline.py"
"""
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


def _run_unreal_pipeline() -> int:
    import unreal

    unreal.log("=== Full-stack material pipeline ===")
    time.sleep(8)

    try:
        import rewire_portfolio_texture_refs as tex
        tex.main()
    except Exception as exc:
        unreal.log_warning(f"[Pipeline] Texture rewire: {exc}")

    sys.argv = [
        "run_toon_conversion.py",
        "--batch", "all",
        "--fix-params",
        "--assign-profiles",
    ]
    from convert_masters_to_substrate_toon import main as convert_main
    convert_main()

    sys.argv = [
        "run_toon_conversion.py",
        "--batch", "all",
        "--finish",
        "--assign-profiles",
    ]
    convert_main()

    # Phase B: Material functions
    import setup_material_functions as mf
    mf.main()

    # Refresh impressionist (Phase 2 ink params on existing master)
    import setup_impressionist_materials as imp
    imp.build_all()

    # Phase C: Unified toon master + env instances
    import setup_master_toon as master_toon
    master_toon.build_all()

    # Phase D: SDF maturation + cathedral batch
    import setup_sdf_maturation as sdf_mat
    sdf_mat.build_all()

    # Phase E: Audio MPC + post-process outline
    import setup_audio_outline as audio_pp
    audio_pp.build_all()

    # Ensure all masters have instances
    import ensure_portfolio_instances as ensure
    ensure.main()

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log("=== Full-stack pipeline complete ===")
    return 0


def main() -> int:
    if _in_unreal():
        return _run_unreal_pipeline()

    print("=== BS_GodFile full-stack material pipeline ===")

    restore = PYTHON_DIR / "restore_portfolio_masters.py"
    textures = PYTHON_DIR / "restore_portfolio_textures.py"
    subprocess.run([sys.executable, str(restore)], cwd=str(PROJECT_ROOT), check=False)
    subprocess.run([sys.executable, str(textures)], cwd=str(PROJECT_ROOT), check=False)
    subprocess.run([sys.executable, str(PYTHON_DIR / "patch_portfolio_texture_paths.py")], cwd=str(PROJECT_ROOT), check=False)

    if not UE_CMD.exists():
        print(f"ERROR: UnrealEditor-Cmd not found: {UE_CMD}")
        return 1

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "full_stack_pipeline.log"
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={(PYTHON_DIR / 'run_full_stack_pipeline.py').as_posix()}",
        "-stdout",
        "-unattended",
        "-nosplash",
        f"-log={log_path}",
    ]
    print(f"Running UE pipeline -> {log_path}")
    proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    print(f"UE exit code: {proc.returncode}")

    for audit_script in ("audit_material_library.py", "audit_material_parameters.py"):
        subprocess.run(
            [sys.executable, str(PYTHON_DIR / audit_script)],
            cwd=str(PROJECT_ROOT),
            check=False,
        )

    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
