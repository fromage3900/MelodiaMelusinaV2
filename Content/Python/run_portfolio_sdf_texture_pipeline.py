"""Full SDF port + texture integration + phase-A fixup.

Shell:
  python Content/Python/run_portfolio_sdf_texture_pipeline.py

Editor Output Log:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/run_portfolio_sdf_texture_pipeline.py"
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON = PROJECT_ROOT / "Content" / "Python"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
LOG = PROJECT_ROOT / "Saved" / "Logs" / "portfolio_sdf_texture_pipeline.log"


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _run_py(script: str, *extra: str) -> int:
    cmd = [sys.executable, str(PYTHON / script), *extra]
    print(f">>> {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


def _run_ue(script: str, log_name: str) -> int:
    if not UE_CMD.exists():
        print(f"ERROR: {UE_CMD}")
        return 1
    log = PROJECT_ROOT / "Saved" / "Logs" / log_name
    log.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={(PYTHON / script).as_posix()}",
        "-stdout",
        "-unattended",
        "-nosplash",
        f"-log={log}",
    ]
    print(f">>> UE {script} -> {log}")
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


def _run_in_ue() -> int:
    import unreal

    import integrate_compositing_textures as integrate
    import run_phase_a_fixup as phase_a
    import audit_dead_material_nodes as dead

    unreal.log("=== PORTFOLIO SDF + TEXTURE PIPELINE (editor) ===")
    rc = integrate._run_in_ue()
    if rc:
        unreal.log_warning(f"[Pipeline] integrate returned {rc}")
    phase_a._run_in_ue()
    dead.main()
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    return 0


def main() -> int:
    if _in_ue():
        return _run_in_ue()

    steps = [
        ("port_sdf_expansion.py", []),
        ("restore_portfolio_textures.py", []),
        ("portfolio_texture_catalog.py", []),
        ("patch_portfolio_texture_paths.py", []),
    ]
    for script, args in steps:
        if _run_py(script, *args) != 0:
            print(f"WARNING: {script} non-zero exit")

    rc_integrate = _run_ue("integrate_compositing_textures.py", "compositing_integration.log")
    rc_phase = _run_ue("run_phase_a_fixup.py", "phase_a_fixup.log")
    _run_ue("audit_dead_material_nodes.py", "dead_material_nodes.log")
    _run_py("audit_sdf_project.py")
    _run_py("audit_material_library.py")

    print(f"Pipeline done integrate={rc_integrate} phase_a={rc_phase}")
    return 0 if rc_integrate == 0 and rc_phase == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
