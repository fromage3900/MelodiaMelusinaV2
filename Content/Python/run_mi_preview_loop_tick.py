"""Resume-friendly MI loop capture — N dirty MIs per run, one UE launch per MI.

Editor:
  py Content/Python/run_mi_preview_loop_tick.py
  py Content/Python/run_mi_preview_loop_tick.py --proof
  py Content/Python/run_mi_preview_loop_tick.py --batch-size 3

Headless:
  python Content/Python/run_mi_preview_loop_tick.py --batch-size 1
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import mi_preview_dirty as dirty_mod
import mi_preview_manifest as manifest_mod
import mi_preview_pipeline_status as status_mod
import mi_preview_studio as studio

REPORT = studio.PROJECT_ROOT / "Saved" / "Audit" / "mi_preview_loop_tick.json"
STATE = studio.LOOP_STATE_JSON
UE_CMD = Path(r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe")
UPROJECT = studio.PROJECT_ROOT / "BS_GodFile.uproject"
TICK_SCRIPT = studio.PROJECT_ROOT / "Content/Python/run_mi_preview_loop_tick.py"
MRQ_SCRIPT = studio.PROJECT_ROOT / "Content/Python/run_mi_preview_mrq.py"


def _in_ue() -> bool:
    try:
        import unreal  # noqa: F401
        return True
    except ImportError:
        return False


def _parse_int_flag(name: str, default: int) -> int:
    for index, arg in enumerate(sys.argv):
        if arg == name and index + 1 < len(sys.argv):
            try:
                return max(1, int(sys.argv[index + 1]))
            except ValueError:
                pass
    return default


def _parse_only() -> str | None:
    if "--proof" in sys.argv:
        return dirty_mod.PROOF_MI
    for index, arg in enumerate(sys.argv):
        if arg == "--only" and index + 1 < len(sys.argv):
            return sys.argv[index + 1]
    return None


def _load_state() -> dict[str, Any]:
    if STATE.is_file():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"runs": 0, "last_ids": []}


def _save_state(state: dict[str, Any]) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _manifest_stale() -> bool:
    if not studio.MANIFEST_JSON.is_file():
        return True
    age = datetime.now(timezone.utc).timestamp() - studio.MANIFEST_JSON.stat().st_mtime
    return age > 3600


def _ensure_manifest() -> None:
    if _manifest_stale():
        manifest_mod.write_manifest()
    dirty_mod.write_dirty_report()


def _capture_one_in_ue(mi_id: str) -> dict[str, Any]:
    import run_mi_preview_mrq as mrq

    manifest = manifest_mod.load_manifest()
    entries = manifest_mod.filter_entries(manifest, only=mi_id)
    if not entries:
        return {"ok": False, "id": mi_id, "error": "not_in_manifest"}
    entry = entries[0]
    result = mrq.run_batch(only=mi_id, prepare=True)
    ok = bool(result.get("ok"))
    frames = dirty_mod._png_frame_count(mi_id)
    if ok and frames >= studio.LOOP_FRAMES:
        dirty_mod.mark_captured(entry, ok=True)
    else:
        err = result.get("error") or f"frames={frames}"
        dirty_mod.mark_captured(entry, ok=False, error=str(err))
    return {"ok": ok, "id": mi_id, "frames": frames, "result": result}


def _run_tick_in_ue() -> int:
    import unreal

    batch_size = _parse_int_flag("--batch-size", 3)
    force_all = "--force-all" in sys.argv
    only = _parse_only()
    _ensure_manifest()

    if only:
        queue = dirty_mod.build_dirty_queue(proof_only="--proof" in sys.argv, only=only)
    else:
        queue = dirty_mod.build_dirty_queue(force_all=force_all)[:batch_size]

    unreal.log(f"[MILoopTick] batch={len(queue)} ids={[e['id'] for e in queue]}")
    results: list[dict] = []
    for entry in queue:
        res = _capture_one_in_ue(entry["id"])
        results.append(res)

    ok = all(r.get("ok") for r in results) if results else False
    state = _load_state()
    state["runs"] = int(state.get("runs", 0)) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    state["last_ids"] = [r.get("id") for r in results]
    state["last_ok"] = ok
    _save_state(state)

    payload = {
        "ok": ok,
        "count": len(results),
        "results": results,
        "next_dirty": [e["id"] for e in dirty_mod.build_dirty_queue()[:10]],
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_mod.write_status(
        captured=[r["id"] for r in results if r.get("ok")],
        capture_failures=[r for r in results if not r.get("ok")],
        next_dirty_ids=payload["next_dirty"],
    )
    return 0 if ok or not results else 1


def _launch_ue_for_mi(mi_id: str) -> int:
    log = studio.PROJECT_ROOT / "Saved" / "Logs" / f"mi_loop_{mi_id}.log"
    cmd = [
        str(UE_CMD),
        str(UPROJECT),
        f"-ExecutePythonScript={MRQ_SCRIPT.as_posix()}",
        "--",
        "--only",
        mi_id,
        "json",
        "-stdout",
        "-unattended",
        "-nosplash",
        f"-log={log}",
    ]
    return subprocess.run(cmd, cwd=str(studio.PROJECT_ROOT)).returncode


def run_tick_headless() -> dict[str, Any]:
    batch_size = _parse_int_flag("--batch-size", 3)
    force_all = "--force-all" in sys.argv
    dry_run = "--dry-run" in sys.argv
    only = _parse_only()
    _ensure_manifest()

    if only:
        queue = dirty_mod.build_dirty_queue(proof_only="--proof" in sys.argv, only=only)
    else:
        queue = dirty_mod.build_dirty_queue(force_all=force_all)[:batch_size]

    plan = {
        "ok": True,
        "dry_run": dry_run,
        "planned": [{"id": e["id"], "reason": e.get("dirty_reason")} for e in queue],
    }
    if dry_run:
        return plan

    if not UE_CMD.exists():
        return {"ok": False, "error": f"ue_cmd_missing:{UE_CMD}"}

    results: list[dict] = []
    for entry in queue:
        mi_id = entry["id"]
        code = _launch_ue_for_mi(mi_id)
        frames = dirty_mod._png_frame_count(mi_id)
        ok = code == 0 and frames >= studio.LOOP_FRAMES
        if ok:
            dirty_mod.mark_captured(entry, ok=True)
        else:
            dirty_mod.mark_captured(entry, ok=False, error=f"exit={code} frames={frames}")
        results.append({"ok": ok, "id": mi_id, "exit_code": code, "frames": frames})

    ok = all(r.get("ok") for r in results) if results else True
    state = _load_state()
    state["runs"] = int(state.get("runs", 0)) + 1
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    state["last_ids"] = [r.get("id") for r in results]
    _save_state(state)

    payload = {
        "ok": ok,
        "count": len(results),
        "results": results,
        "next_dirty": [e["id"] for e in dirty_mod.build_dirty_queue()[:10]],
    }
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    status_mod.write_status(
        captured=[r["id"] for r in results if r.get("ok")],
        capture_failures=[r for r in results if not r.get("ok")],
        next_dirty_ids=payload["next_dirty"],
    )
    return payload


def main() -> int:
    if _in_ue():
        return _run_tick_in_ue()
    result = run_tick_headless()
    if "json" in sys.argv:
        print(json.dumps(result, indent=2))
    else:
        print(result)
    return 0 if result.get("ok", False) else 1


if __name__ == "__main__":
    raise SystemExit(main())
