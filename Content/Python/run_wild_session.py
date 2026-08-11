"""Wild build session â€” rebuild universal master, PP stack, template showcase, audits.

Shell:
  python Content/Python/run_wild_session.py

Editor:
  py "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/run_wild_session.py"
"""
from __future__ import annotations

import subprocess
import sys
import time
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PYTHON = PROJECT_ROOT / "Content" / "Python"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
LOG = PROJECT_ROOT / "Saved" / "Logs" / "wild_session.log"


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _step(label: str, fn) -> bool:
    import unreal

    unreal.log(f"[Wild] >>> {label}")
    try:
        fn()
        unreal.log(f"[Wild] ok: {label}")
        return True
    except Exception as exc:
        unreal.log_error(f"[Wild] FAILED {label}: {exc}")
        unreal.log_error(traceback.format_exc())
        return False


def _run_ue_pipeline() -> int:
    import unreal

    unreal.log("=== WILD SESSION START ===")
    time.sleep(2)

    ok = 0
    total = 0

    def run(label, fn):
        nonlocal ok, total
        total += 1
        if _step(label, fn):
            ok += 1

    run("material functions (missing only)", lambda: __import__("setup_material_functions").build_all(force=False))

    def refresh_universal():
        sys.argv = ["setup_master_universal.py"]
        __import__("setup_master_universal").build()

    run("universal master (skip if exists)", refresh_universal)
    run("universal instances", lambda: __import__("setup_universal_instances").build_instances())
    run("audio + outline PP", lambda: __import__("setup_audio_outline").build_all())
    run("storybook vines PP", lambda: __import__("setup_storybook_outline").build_all(force=True))
    run("template showcase", lambda: __import__("setup_template_showcase").build_all())

    if "--convert" in sys.argv:
        def convert_masters():
            sys.argv = ["convert", "--batch", "all", "--fix-params", "--assign-profiles"]
            __import__("convert_masters_to_substrate_toon").main()

        run("substrate convert", convert_masters)
        run("portfolio texture rewire", lambda: __import__("rewire_portfolio_texture_refs").main())
        run("ensure portfolio instances", lambda: __import__("ensure_portfolio_instances").main())

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"=== WILD SESSION COMPLETE ({ok}/{total} steps) ===")
    return 0 if ok == total else 1


def main() -> int:
    if _in_ue():
        return _run_ue_pipeline()

    if not UE_CMD.exists():
        print(f"ERROR: {UE_CMD}")
        return 1

    LOG.parent.mkdir(parents=True, exist_ok=True)

    for mod_name in ("patch_portfolio_texture_paths",):
        try:
            report = __import__(mod_name).main()
            print(f"[Wild] pre-UE {mod_name}: ok")
        except PermissionError as exc:
            print(f"[Wild] pre-UE {mod_name}: skipped (file locked â€” use editor rewire): {exc}")
        except Exception as exc:
            print(f"[Wild] pre-UE {mod_name}: {exc}")

    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={(PYTHON / 'run_wild_session.py').as_posix()}",
        "-stdout",
        "-unattended",
        "-nosplash",
        f"-log={LOG}",
    ]
    print(f"Wild session -> {LOG}")
    proc = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    for audit in ("audit_material_library.py", "audit_material_parameters.py"):
        subprocess.run([sys.executable, str(PYTHON / audit)], cwd=str(PROJECT_ROOT), check=False)
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
