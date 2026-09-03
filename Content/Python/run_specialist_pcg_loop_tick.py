"""Specialist PCG loop — audit, fix, organize, greybox validate.

  python Content/Python/run_specialist_pcg_loop_tick.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE = PROJECT_ROOT / "Saved" / "Audit" / "specialist_pcg_loop_state.json"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "specialist_pcg_loop.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

TASKS = (
    "audit_portfolio",
    "organize_library",
    "universal_build",
    "greybox_validate_template",
    "fix_dead_dryrun",
    "sakura_wrapper",
    "docs_note",
)


def _load_tick() -> int:
    if STATE.exists():
        try:
            return int(json.loads(STATE.read_text(encoding="utf-8")).get("tick_index", 0))
        except Exception:
            pass
    return 0


def _save_tick(tick: int, task: str, summary: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps({
        "tick_index": tick,
        "last_task": task,
        "last_run": datetime.now(timezone.utc).isoformat(),
        "summary": summary,
    }, indent=2), encoding="utf-8")


def _run_in_ue() -> int:
    import unreal

    tick = _load_tick()
    task = TASKS[tick % len(TASKS)]
    unreal.log(f"=== SPECIALIST PCG LOOP tick={tick} task={task} ===")
    payload: dict = {"timestamp": datetime.now(timezone.utc).isoformat(), "tick_index": tick, "task": task}

    if task == "audit_portfolio":
        import audit_pcg_portfolio as ap
        payload["audit"] = ap._audit_in_ue()
    elif task == "organize_library":
        import organize_pcg_library as org
        payload["organize"] = org.organize()
    elif task == "universal_build":
        import setup_pcg_universal as uni
        payload["build"] = uni.build_all(force=False)
    elif task == "greybox_validate_template":
        import setup_pcg_template as tpl
        payload["template"] = tpl.build(preset="minimal", generate=True)
    elif task == "fix_dead_dryrun":
        import fix_pcg_dead_systems as fix
        payload["fix"] = fix.fix(apply=False)
    elif task == "sakura_wrapper":
        import setup_pcg_sakura as sak
        payload["sakura"] = sak.build_all(rebuild=False, spawn=False)
    else:
        payload["note"] = "See Docs/PCG_PORTFOLIO_PLAN.md"

    payload["summary"] = {"task": task, "ok": True}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _save_tick(tick + 1, task, payload["summary"])
    unreal.log(f"[SpecialistPCGLoop] task={task} -> {REPORT}")
    return 0


def main() -> int:
    try:
        import unreal  # noqa: F401
        return _run_in_ue()
    except ImportError:
        if not UE_CMD.exists():
            return 1
        os.environ.setdefault("BS_PCG_FORCE", "0")
        cmd = [
            str(UE_CMD), str(UPROJECT),
            f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/run_specialist_pcg_loop_tick.py').as_posix()}",
            "-stdout", "-unattended", "-nullrhi", "-DisablePlugins=Monolith",
        ]
        return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
