"""One specialist terrain loop tick — landscape Nikki, water shore, audits.

Editor:
  py Content/Python/run_specialist_terrain_loop_tick.py

Headless (close editor first):
  python Content/Python/run_specialist_terrain_loop_tick.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE = PROJECT_ROOT / "Saved" / "Audit" / "specialist_terrain_loop_state.json"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "specialist_terrain_loop.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

TASKS = (
    "audit_landscape",
    "organize_landscape_groups",
    "instance_tune_sakura_garden",
    "instance_tune_pond_bank",
    "water_shore_expand",
    "scene_validate",
    "docs_note",
)


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _load_tick() -> int:
    if STATE.exists():
        try:
            return int(json.loads(STATE.read_text(encoding="utf-8")).get("tick_index", 0))
        except Exception:
            pass
    return 0


def _save_tick(tick: int, task: str, summary: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(
        json.dumps(
            {
                "tick_index": tick,
                "last_task": task,
                "last_run": datetime.now(timezone.utc).isoformat(),
                "summary": summary,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _run_in_ue() -> int:
    import unreal
    import material_lib as lib

    tick = _load_tick()
    task = TASKS[tick % len(TASKS)]
    unreal.log(f"=== SPECIALIST TERRAIN LOOP tick={tick} task={task} ===")
    report: dict = {"timestamp": datetime.now(timezone.utc).isoformat(), "tick_index": tick, "task": task}

    if task == "audit_landscape":
        import audit_landscape as audit_mod
        report["audit"] = audit_mod._audit_in_ue()
    elif task == "organize_landscape_groups":
        import organize_landscape_groups as org
        org.organize()
        report["note"] = "landscape groups refreshed"
    elif task == "instance_tune_sakura_garden":
        mi_path = "/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_SakuraGarden"
        if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
            mi = unreal.load_asset(f"{mi_path}.MI_Landscape_SakuraGarden")
            lib.set_instance_scalar(mi, "SparkleIntensity", 0.38)
            lib.set_instance_scalar(mi, "PastelLift", 0.24)
            lib.save_package(mi)
            report["tuned"] = mi_path
    elif task == "instance_tune_pond_bank":
        mi_path = "/Game/EnvSandbox/Materials/Instances/Landscape/MI_Landscape_PondBank"
        if unreal.EditorAssetLibrary.does_asset_exist(mi_path):
            mi = unreal.load_asset(f"{mi_path}.MI_Landscape_PondBank")
            lib.set_instance_scalar(mi, "Wetness", 0.58)
            lib.set_instance_scalar(mi, "ShoreWetnessBoost", 0.42)
            lib.save_package(mi)
            report["tuned"] = mi_path
    elif task == "water_shore_expand":
        import expand_grand_water as water_exp
        report["water"] = water_exp.expand()
    elif task == "scene_validate":
        import setup_sakura_scene as scene
        os.environ["BS_SAKURA_VALIDATE"] = "1"
        scene.build()
        audit_path = PROJECT_ROOT / "Saved" / "Audit" / "sakura_scene.json"
        if audit_path.exists():
            report["sakura_scene"] = json.loads(audit_path.read_text(encoding="utf-8"))
    else:
        report["note"] = "Docs: see MATERIAL_SPECIALISTS_PLAN.md Nikki-on-landscape section"

    report["summary"] = {"task": task, "ok": True}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    _save_tick(tick + 1, task, report["summary"])
    unreal.log(f"[SpecialistTerrainLoop] task={task} -> {REPORT}")
    return 0


def main() -> int:
    if _in_ue():
        return _run_in_ue()
    if not UE_CMD.exists():
        print(f"ERROR: {UE_CMD}")
        return 1
    os.environ.setdefault("BS_MASTER_FORCE", "1")
    log = PROJECT_ROOT / "Saved" / "Logs" / "specialist_terrain_loop.log"
    cmd = [
        str(UE_CMD), str(UPROJECT),
        f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/run_specialist_terrain_loop_tick.py').as_posix()}",
        "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
        f"-log={log}",
    ]
    print(f"Specialist terrain loop tick -> {log}")
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
