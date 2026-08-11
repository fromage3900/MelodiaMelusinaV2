"""Orchestrate full material library finish pipeline for BS_GodFile.

Order:
  1. patch_portfolio_uasset_paths (filesystem, no editor)
  2. run_toon_conversion (Substrate Toon + fix-params + profiles)
  3. setup_impressionist_materials (refresh impressionist family)
  4. ensure_portfolio_instances (missing MI_* per master)
  5. audit_material_library (filesystem report)

Run:
  python Content/Python/run_material_finish_pipeline.py

Or headless UE only (skip step 1 if already patched):
  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript="G:/EnvironmentPortfolio/BS_GodFile/Content/Python/run_material_finish_pipeline.py"
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


def _run_python_patch() -> int:
    patch = PYTHON_DIR / "patch_portfolio_uasset_paths.py"
    print(f"[Pipeline] Step 1: {patch.name}")
    proc = subprocess.run([sys.executable, str(patch)], cwd=str(PROJECT_ROOT))
    return proc.returncode


def _run_audit() -> int:
    audit = PYTHON_DIR / "audit_material_library.py"
    print(f"[Pipeline] Step 5: {audit.name}")
    proc = subprocess.run([sys.executable, str(audit)], cwd=str(PROJECT_ROOT))
    return proc.returncode


def _run_ue_script(script_name: str, log_name: str) -> int:
    script = PYTHON_DIR / script_name
    if not UE_CMD.exists():
        print(f"[Pipeline] ERROR: UnrealEditor-Cmd not found: {UE_CMD}")
        return 1
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / log_name
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={script.as_posix()}",
        "-stdout",
        "-unattended",
        "-nosplash",
        f"-log={log_path}",
    ]
    print(f"[Pipeline] Running {script_name} -> {log_path}")
    proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    print(f"[Pipeline] {script_name} exit={proc.returncode}")
    return proc.returncode


def _run_unreal_pipeline() -> int:
    import unreal

    unreal.log("=== Material finish pipeline (in-editor) ===")
    time.sleep(5)


    # Toon conversion: all masters + fix params + profiles + finish incomplete
    import sys as _sys

    _sys.argv = [
        "run_toon_conversion.py",
        "--batch",
        "all",
        "--fix-params",
        "--assign-profiles",
        "--finish",
    ]
    from convert_masters_to_substrate_toon import main as convert_main

    rc = convert_main()
    if rc != 0:
        unreal.log_warning(f"[Pipeline] Toon conversion returned {rc}")

    import setup_impressionist_materials as imp

    imp.build_all()

    import ensure_portfolio_instances as ensure

    rc2 = ensure.main()
    if rc2 != 0:
        unreal.log_warning(f"[Pipeline] ensure_portfolio_instances returned {rc2}")

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log("=== Material finish pipeline complete ===")
    return 0


def main() -> int:
    if _in_unreal():
        return _run_unreal_pipeline()

    print("=== BS_GodFile material finish pipeline ===")
    rc = _run_python_patch()
    if rc != 0:
        print(f"[Pipeline] patch failed with {rc}")
        return rc

    rc = _run_ue_script("run_material_finish_pipeline.py", "material_finish_pipeline.log")
    if rc != 0:
        print(f"[Pipeline] UE pipeline failed with {rc} (check log)")

    _run_audit()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
