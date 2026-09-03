"""Execute MATERIAL_WORK_PLAN.md do-next steps (editor or headless shell).

  python Content/Python/run_material_work_plan.py
  python Content/Python/run_material_work_plan.py --skip-rebuild
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON = PROJECT_ROOT / "Content" / "Python"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
LOG = PROJECT_ROOT / "Saved" / "Logs" / "material_work_plan.log"


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _run_in_ue(skip_rebuild: bool) -> int:
    import unreal

    unreal.log("=== MATERIAL WORK PLAN ===")
    steps_ok = 0
    steps_total = 0

    def step(label: str, fn) -> None:
        nonlocal steps_ok, steps_total
        steps_total += 1
        unreal.log(f"[WorkPlan] >>> {label}")
        try:
            fn()
            steps_ok += 1
            unreal.log(f"[WorkPlan] ok: {label}")
        except Exception as exc:
            unreal.log_error(f"[WorkPlan] FAILED {label}: {exc}")

    if not skip_rebuild:
        def rebuild():
            import run_force_universal
            run_force_universal  # noqa: F401 — executes build via import side effect

        step("rebuild universal master", rebuild)
    else:
        unreal.log("[WorkPlan] skipping rebuild (--skip-rebuild)")

    step("reparent unified instances", lambda: __import__("reparent_unified_instances").main())
    step("sakura instances", lambda: __import__("setup_sakura_instances").build())
    step("refresh universal instances", lambda: __import__("setup_universal_instances").build_instances())
    step("organize instance folders", lambda: __import__("organize_universal_instances").main())
    step("portfolio palette MPC", lambda: __import__("setup_portfolio_mpc").main())
    step("trimsheet instances", lambda: __import__("setup_trimsheet_instances").build())

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"=== WORK PLAN COMPLETE ({steps_ok}/{steps_total} steps) ===")
    return 0 if steps_ok == steps_total else 1


def main() -> int:
    skip_rebuild = "--skip-rebuild" in sys.argv
    if _in_ue():
        return _run_in_ue(skip_rebuild)

    if not UE_CMD.exists():
        print(f"ERROR: {UE_CMD}")
        return 1

    LOG.parent.mkdir(parents=True, exist_ok=True)
    args = f"{(PYTHON / 'run_material_work_plan.py').as_posix()}"
    if skip_rebuild:
        args += " --skip-rebuild"
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={args}",
        "-stdout",
        "-unattended",
        "-nosplash",
        f"-log={LOG}",
    ]
    print(f"Work plan -> {LOG}")
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
