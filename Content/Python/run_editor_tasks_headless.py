"""Headless editor tasks â€” editor closed, no Monolith required.

  python Content/Python/run_editor_tasks_headless.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON = PROJECT_ROOT / "Content" / "Python"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


def _py(script: str) -> int:
    print(f">>> python {script}")
    return subprocess.run([sys.executable, str(PYTHON / script)], cwd=str(PROJECT_ROOT)).returncode


def _ue(script: str, log: str) -> int:
    log_path = PROJECT_ROOT / "Saved" / "Logs" / log
    log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={(PYTHON / script).as_posix()}",
        "-stdout",
        "-unattended",
        "-nosplash",
        f"-log={log_path}",
    ]
    print(f">>> UE {script}")
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


def main() -> int:
    # Refuse rather than terminate an editor that may belong to another lane.
    probe = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "$p=Get-Process UnrealEditor,UnrealEditor-Cmd -ErrorAction SilentlyContinue; if ($p) { $p | Select-Object Id,ProcessName; exit 2 }"],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        print("Refusing headless editor tasks while an Unreal editor process is active.")
        if probe.stdout:
            print(probe.stdout.strip())
        return 2

    disk = [
        "port_sdf_expansion.py",
        "restore_portfolio_textures.py",
        "portfolio_texture_catalog.py",
        "patch_portfolio_texture_paths.py",
    ]
    for s in disk:
        _py(s)

    rc = 0
    for script, log in (
        ("integrate_instances_light.py", "integrate_instances_light.log"),
        ("run_phase_a_safe.py", "phase_a_safe.log"),
        ("audit_dead_material_nodes.py", "dead_material_nodes.log"),
    ):
        if _ue(script, log) != 0:
            rc = 1

    _py("audit_sdf_project.py")
    _py("audit_material_library.py")
    print(f"Headless tasks done rc={rc}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
