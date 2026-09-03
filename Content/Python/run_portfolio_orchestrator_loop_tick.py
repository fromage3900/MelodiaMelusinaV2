"""Portfolio environment orchestrator — one workstream per 10m loop tick.

Rotates: PCG anti-cluster → Sakura petal VFX → UDS/toon → storybook PP → UE water.

Editor:
  py Content/Python/run_portfolio_orchestrator_loop_tick.py

Headless (close editor first):
  python Content/Python/run_portfolio_orchestrator_loop_tick.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE = PROJECT_ROOT / "Saved" / "Audit" / "portfolio_orchestrator_loop_state.json"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "portfolio_orchestrator_loop.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

TASKS = (
    "pcg_anti_cluster",
    "sakura_petal_vfx",
    "uds_toon_lighting",
    "storybook_outline",
    "ue_water_simulation",
)

AUDIT_BY_TASK = {
    "pcg_anti_cluster": PROJECT_ROOT / "Saved" / "Audit" / "pcg_clustering_audit.json",
    "sakura_petal_vfx": PROJECT_ROOT / "Saved" / "Audit" / "sakura_petal_niagara.json",
    "uds_toon_lighting": PROJECT_ROOT / "Saved" / "Audit" / "uds_toon_integration.json",
    "storybook_outline": PROJECT_ROOT / "Saved" / "Audit" / "storybook_outline_audit.json",
    "ue_water_simulation": PROJECT_ROOT / "Saved" / "Audit" / "ue_water_sim_audit.json",
}


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


def _read_audit(task: str) -> dict | None:
    path = AUDIT_BY_TASK.get(task)
    if path and path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return None


def _run_in_ue() -> int:
    import unreal

    tick = _load_tick()
    task = TASKS[tick % len(TASKS)]
    unreal.log(f"=== PORTFOLIO ORCHESTRATOR tick={tick} task={task} ===")
    payload: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tick_index": tick,
        "task": task,
        "previous_audit": _read_audit(task),
    }
    ok = True

    try:
        if task == "pcg_anti_cluster":
            import audit_pcg_clustering as cluster_audit
            import setup_pcg_greybox as grey

            payload["audit_before"] = cluster_audit.run_audit()
            payload["greybox"] = grey.apply_greybox_pcg(
                "/Game/EnvSandbox/Environments/Sakura/L_SakuraPath",
                preset="showcase",
                generate=True,
            )
            payload["audit_after"] = cluster_audit.run_audit()
            ok = bool(payload["audit_after"].get("passed", False))
        elif task == "sakura_petal_vfx":
            import audit_sakura_petal_niagara as petal_audit
            import run_sakura_niagara_plan as niagara_plan

            payload["plan"] = niagara_plan.run_plan(rebuild=False, skip_master=True, showcase=False)
            payload["audit"] = petal_audit.run_audit()
            ok = payload["audit"].get("critical_count", 1) == 0
        elif task == "uds_toon_lighting":
            import setup_time_of_day_mpc as uds

            sys.argv = [a for a in sys.argv if a != "--apply"] + ["--apply"]
            uds.main()
            payload["audit"] = json.loads(
                (PROJECT_ROOT / "Saved" / "Audit" / "uds_toon_integration.json").read_text(encoding="utf-8")
            )
            ok = bool(payload["audit"].get("passed", False))
        elif task == "storybook_outline":
            import audit_storybook_outline as pp_audit
            import setup_audio_outline as audio_pp
            import setup_storybook_outline as story_pp

            audio_pp.build_all(force=True)
            story_pp.build_all(force=True)
            import portfolio_scene_integration as scene

            les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
            eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
            for lvl in (
                "/Game/EnvSandbox/Environments/Sakura/L_SakuraPath",
                "/Game/EnvSandbox/_Template/L_Template",
            ):
                leaf = lvl.rsplit("/", 1)[-1]
                if unreal.EditorAssetLibrary.does_asset_exist(f"{lvl}.{leaf}"):
                    les.load_level(lvl)
                    scene.apply_post_process_stack(scene.find_or_spawn_ppv(eas))
                    les.save_current_level()
            payload["audit"] = pp_audit.run_audit()
            ok = bool(payload["audit"].get("passed", False))
        elif task == "ue_water_simulation":
            import setup_ue_water_simulation as water_sim

            payload["water"] = water_sim.build_all()
            audit_path = PROJECT_ROOT / "Saved" / "Audit" / "ue_water_sim_audit.json"
            if audit_path.exists():
                payload["audit"] = json.loads(audit_path.read_text(encoding="utf-8"))
                ok = bool(payload["audit"].get("passed", False))
        else:
            payload["note"] = "See Docs/PORTFOLIO_ORCHESTRATOR_PLAN.md"
    except Exception as exc:
        ok = False
        payload["error"] = str(exc)
        unreal.log_error(f"[PortfolioOrchestrator] {task} failed: {exc}")

    payload["summary"] = {"task": task, "ok": ok}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _save_tick(tick + 1, task, payload["summary"])
    unreal.log(f"[PortfolioOrchestrator] task={task} ok={ok} -> {REPORT}")
    return 0 if ok else 1


def main() -> int:
    if _in_ue():
        return _run_in_ue()
    if not UE_CMD.exists():
        print(f"ERROR: {UE_CMD}")
        return 1
    log = PROJECT_ROOT / "Saved" / "Logs" / "portfolio_orchestrator_loop.log"
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/run_portfolio_orchestrator_loop_tick.py').as_posix()}",
        "-stdout",
        "-unattended",
        "-nullrhi",
        "-DisablePlugins=Monolith",
        f"-log={log}",
    ]
    print(f"Portfolio orchestrator tick -> {log}")
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
