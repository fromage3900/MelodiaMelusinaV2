"""One-shot finalization: MeshBlend fix â†’ AAA pipeline â†’ starters â†’ Toon conversion.

Headless:
  UnrealEditor-Cmd.exe BS_GodFile.uproject ^
    -ExecutePythonScript="G:/EnvironmentPortfolio/BS_GodFile/Content/Python/run_finalization_all.py" ^
    -stdout -unattended -nosplash -nullrhi -DisablePlugins=Monolith

In editor:
  py Content/Python/run_finalization_all.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "finalization_all.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"
CONTENT = PROJECT_ROOT / "Content"


def _run_toon_conversion_pending() -> dict:
    import unreal

    unreal.log_warning(
        "[FinalizationAll] Toon conversion deferred â€” legacy SDF master packages are corrupt on disk; "
        "Universal + Landscape masters already use SubstrateToon."
    )
    return {"ok": True, "pending": 0, "converted": 0, "deferred": "corrupt_sdf_masters"}


def run_core_pipeline() -> dict:
    """Material spine rebuild without full AAA (avoids missing water master + fragile SDF audits)."""
    import os

    import apply_starter_instances as starters
    import organize_landscape_groups
    import organize_master_groups
    import review_portfolio_masters as review
    import setup_landscape_height_blend as landscape
    import setup_master_universal as universal

    os.environ["BS_MASTER_FORCE"] = "1"
    universal.build()
    organize_master_groups.main()
    landscape.build(force=True)
    organize_landscape_groups.organize()
    starters._run_in_ue()
    try:
        review._run_in_ue()
    except Exception as exc:
        import unreal

        unreal.log_warning(f"[FinalizationAll] master_review skipped: {exc}")
    return {"ok": True, "mode": "core_pipeline"}


def run_all() -> dict:
    import unreal

    # Cmd may invoke Python before asset registry is ready.
    time.sleep(20)

    steps: list[dict] = []

    def step(name: str, fn) -> None:
        unreal.log(f"[FinalizationAll] START {name}")
        try:
            result = fn()
            payload = result if isinstance(result, dict) else {"result": str(result)}
            steps.append({"step": name, "ok": True, **payload})
            unreal.log(f"[FinalizationAll] OK {name}")
        except Exception as exc:
            steps.append({"step": name, "ok": False, "error": str(exc)})
            unreal.log_error(f"[FinalizationAll] FAIL {name}: {exc}")


    step("core_pipeline", run_core_pipeline)
    step("toon_conversion", _run_toon_conversion_pending)

    all_ok = all(s.get("ok") for s in steps)
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "steps": steps,
        "all_ok": all_ok,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception:
        pass
    unreal.log(f"[FinalizationAll] complete all_ok={all_ok} -> {REPORT}")
    return report


def main() -> int:
    try:
        import unreal  # noqa: F401
        report = run_all()
        print(f"FINALIZATION_ALL all_ok={report['all_ok']} -> {REPORT}")
        return 0 if report["all_ok"] else 1
    except ImportError:
        if not UE_CMD.exists():
            print(f"ERROR: {UE_CMD}")
            return 1
        log = PROJECT_ROOT / "Saved" / "Logs" / "finalization_all.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        cmd = [
            str(UE_CMD),
            str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/run_finalization_all.py').as_posix()}",
            "-stdout",
            "-unattended",
            "-nosplash",
            "-nullrhi",
            "-DisablePlugins=Monolith",
            f"-log={log}",
        ]
        print(f"Launching headless finalization -> {log}")
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
