"""Execute the Sakura Dream Niagara plan end-to-end (editor or headless).

Output Log (editor open, UnrealMCP/Monolith optional):
  py Content/Python/run_sakura_niagara_plan.py
  py Content/Python/run_sakura_niagara_plan.py --rebuild
  py Content/Python/run_sakura_niagara_plan.py --skip-master

Headless:
  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript="G:/EnvironmentPortfolio/BS_GodFile/Content/Python/run_sakura_niagara_plan.py"
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = PROJECT_ROOT / "Saved" / "Audit" / "sakura_niagara_plan.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _step(name: str, fn) -> dict:
    import unreal

    unreal.log(f"[SakuraPlan] >>> {name}")
    entry = {"step": name, "ok": False, "error": None}
    try:
        fn()
        entry["ok"] = True
        unreal.log(f"[SakuraPlan] ok: {name}")
    except Exception as exc:
        entry["error"] = str(exc)
        unreal.log_error(f"[SakuraPlan] FAILED {name}: {exc}")
    return entry


def run_plan(*, rebuild: bool = False, skip_master: bool = False, showcase: bool = False) -> dict:
    import unreal

    import material_lib as lib

    started = datetime.now(timezone.utc).isoformat()
    steps: list[dict] = []

    master = f"{lib.MASTER_DIR}/M_Master_Toon_Universal.M_Master_Toon_Universal"
    if not skip_master and not unreal.EditorAssetLibrary.does_asset_exist(master):
        steps.append(
            _step(
                "rebuild universal master",
                lambda: __import__("setup_master_universal").build(),
            )
        )
    else:
        steps.append({"step": "rebuild universal master", "ok": True, "skipped": True})

    steps.append(_step("sakura material instances", lambda: __import__("setup_sakura_instances").build()))
    steps.append(
        _step(
            "sakura alpha import",
            lambda: __import__("portfolio_alpha_paths").ensure_alpha_imports(),
        )
    )
    steps.append(_step("L_SakuraPath greybox", lambda: __import__("setup_sakura_scene").build()))
    steps.append(
        _step(
            "niagara ambient library (seeds)",
            lambda: __import__("setup_niagara_library").build_all(showcase=False, prefer_mcp=True),
        )
    )

    def do_sakura_kit():
        mod = __import__("setup_sakura_niagara")
        mod.build_all(rebuild=rebuild, spawn=True, skip_prereq=True)
        if showcase and hasattr(mod, "build_sakura_showcase_level"):
            mod.build_sakura_showcase_level()

    steps.append(_step("sakura dream niagara kit", do_sakura_kit))
    steps.append(
        _step(
            "validate sakura vfx",
            lambda: __import__("validate_sakura_niagara").run_validation(),
        )
    )
    steps.append(
        _step(
            "audit sakura petal niagara",
            lambda: __import__("audit_sakura_petal_niagara").run_audit(),
        )
    )

    report = {
        "timestamp": started,
        "rebuild": rebuild,
        "steps": steps,
        "all_ok": all(s.get("ok") for s in steps),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"[SakuraPlan] report -> {REPORT_PATH}")
    return report


def main() -> int:
    rebuild = "--rebuild" in sys.argv
    skip_master = "--skip-master" in sys.argv
    showcase = "--showcase" in sys.argv

    if _in_ue():
        report = run_plan(rebuild=rebuild, skip_master=skip_master, showcase=showcase)
        return 0 if report.get("all_ok") else 1

    if not UE_CMD.exists():
        print(f"ERROR: {UE_CMD} not found")
        return 1
    script = (PROJECT_ROOT / "Content/Python/run_sakura_niagara_plan.py").as_posix()
    args = [str(UE_CMD), str(UPROJECT), f"-ExecutePythonScript={script}", "-stdout", "-unattended", "-nosplash"]
    if rebuild:
        args[-1] += " --rebuild"
    if skip_master:
        args[-1] += " --skip-master"
    if showcase:
        args[-1] += " --showcase"
    return subprocess.run(args, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
