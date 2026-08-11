"""Portfolio Materials AAA — one workstream per 15m loop tick.

Editor:
  py Content/Python/run_material_aaa_loop_tick.py

Headless:
  python Content/Python/run_material_aaa_loop_tick.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE = PROJECT_ROOT / "Saved" / "Audit" / "material_aaa_loop_state.json"
REPORT = PROJECT_ROOT / "Saved" / "Audit" / "material_aaa_loop.json"
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = PROJECT_ROOT / "BS_GodFile.uproject"

TASKS = (
    "baseline_audit",
    "cc0_textures",
    "universal_rebuild",
    "zen_masks",
    "trimsheet_layers",
    "starters_sakura",
    "landscape_aaa",
    "grand_water_aaa",
    "sync_instances",
    "final_audit",
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

    tick = _load_tick()
    task = TASKS[tick % len(TASKS)]
    unreal.log(f"=== MATERIAL AAA LOOP tick={tick} task={task} ===")
    payload: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tick_index": tick,
        "task": task,
    }
    ok = True

    try:
        if task == "baseline_audit":
            os.environ["BS_AAA_READ_ONLY"] = "1"
            import review_portfolio_masters as rpm
            import audit_zen_trimsheet as zt

            rpm._run_in_ue()
            master_report = PROJECT_ROOT / "Saved" / "Audit" / "master_review.json"
            if master_report.exists():
                payload["master_review"] = json.loads(master_report.read_text(encoding="utf-8"))
            payload["zen_trimsheet"] = zt._audit_in_ue()
            ok = payload["zen_trimsheet"].get("all_ok", False)
        elif task == "cc0_textures":
            import portfolio_landscape_textures as lt

            lt.main()
            payload["landscape_textures"] = lt.LANDSCAPE_LAYER_TEXTURES
            ok = True
        elif task == "universal_rebuild":
            os.environ["BS_MASTER_FORCE"] = "1"
            import setup_master_universal as uni
            import organize_master_groups as org

            uni.build()
            org.main()
            payload["note"] = "universal rebuilt"
            ok = True
        elif task == "zen_masks":
            import apply_zen_instances as zen

            ok = zen._run_in_ue() == 0
            audit_path = PROJECT_ROOT / "Saved" / "Audit" / "zen_instances.json"
            if audit_path.exists():
                payload["zen"] = json.loads(audit_path.read_text(encoding="utf-8"))
        elif task == "trimsheet_layers":
            import setup_trimsheet_instances as trim
            import audit_zen_trimsheet as zt

            trim.build()
            audit_path = PROJECT_ROOT / "Saved" / "Audit" / "trimsheet_instances.json"
            if audit_path.exists():
                payload["trimsheet"] = json.loads(audit_path.read_text(encoding="utf-8"))
            payload["audit"] = zt._audit_in_ue()
            ok = payload["audit"].get("all_ok", False)
        elif task == "starters_sakura":
            import apply_starter_instances as starters
            import setup_sakura_instances as sakura

            starters.build_starter_instances()
            sakura.build()
            payload["note"] = "starters + sakura refreshed"
            ok = True
        elif task == "landscape_aaa":
            os.environ["BS_MASTER_FORCE"] = "1"
            import setup_landscape_height_blend as lhb
            import organize_landscape_groups as org

            lhb.build(force=True)
            org.organize()
            payload["note"] = "landscape height blend rebuilt"
            ok = True
        elif task == "grand_water_aaa":
            import expand_grand_water as exp
            import setup_master_water as water

            payload["expand"] = exp.expand() if hasattr(exp, "expand") else {}
            water.build()
            payload["note"] = "grand water expanded"
            ok = True
        elif task == "sync_instances":
            import sync_all_material_instances as sync

            payload["sync"] = sync.run_sync()
            ok = payload["sync"].get("all_ok", True)
        elif task == "final_audit":
            import audit_zen_trimsheet as zt
            import audit_landscape_aaa as la
            import audit_grand_water_aaa as wa
            import review_portfolio_masters as rpm

            rpm._run_in_ue()
            payload["zen_trimsheet"] = zt._audit_in_ue()
            payload["landscape_aaa"] = la._audit_in_ue()
            payload["grand_water_aaa"] = wa._audit_in_ue()
            master_report = PROJECT_ROOT / "Saved" / "Audit" / "master_review.json"
            master_ok = False
            if master_report.exists():
                mr = json.loads(master_report.read_text(encoding="utf-8"))
                payload["master_review"] = mr
                summary = mr.get("summary") or mr
                master_ok = summary.get("clean", False) or (
                    summary.get("banned_texture_count", summary.get("banned_texture_slots", 1)) == 0
                    and summary.get("unwired_texture_count", summary.get("unwired_texture_slots", 1)) == 0
                )
            merged = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "zen_trimsheet_all_ok": payload["zen_trimsheet"].get("all_ok"),
                "landscape_aaa_all_ok": payload["landscape_aaa"].get("all_ok"),
                "grand_water_aaa_all_ok": payload["grand_water_aaa"].get("all_ok"),
                "master_review_ok": master_ok,
                "all_ok": bool(
                    payload["zen_trimsheet"].get("all_ok")
                    and payload["landscape_aaa"].get("all_ok")
                    and payload["grand_water_aaa"].get("all_ok")
                    and master_ok
                ),
            }
            out = PROJECT_ROOT / "Saved" / "Audit" / "portfolio_materials_aaa.json"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(merged, indent=2), encoding="utf-8")
            payload["portfolio_materials_aaa"] = merged
            ok = merged["all_ok"]
        else:
            payload["note"] = "unknown task"
    except Exception as exc:
        ok = False
        payload["error"] = str(exc)
        unreal.log_error(f"[MaterialAAALoop] {task} failed: {exc}")

    payload["summary"] = {"task": task, "ok": ok}
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _save_tick(tick + 1, task, payload["summary"])
    unreal.log(f"[MaterialAAALoop] task={task} ok={ok} -> {REPORT}")
    try:
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    except Exception:
        pass
    return 0 if ok else 1


def main() -> int:
    if _in_ue():
        return _run_in_ue()
    if not UE_CMD.exists():
        print(f"ERROR: {UE_CMD}")
        return 1
    os.environ.setdefault("BS_MASTER_FORCE", "1")
    log = PROJECT_ROOT / "Saved" / "Logs" / "material_aaa_loop.log"
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={(PROJECT_ROOT / 'Content/Python/run_material_aaa_loop_tick.py').as_posix()}",
        "-stdout",
        "-unattended",
        "-nullrhi",
        "-DisablePlugins=Monolith",
        f"-log={log}",
    ]
    print(f"Material AAA loop tick -> {log}")
    return subprocess.run(cmd, cwd=str(PROJECT_ROOT)).returncode


if __name__ == "__main__":
    raise SystemExit(main())
