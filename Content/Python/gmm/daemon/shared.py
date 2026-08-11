"""Shared utilities for GMM subpackage daemons."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[4]
STAGING_ROOT = PROJECT_ROOT / "_staging" / "gmm_daemon"
STATE_DIR = PROJECT_ROOT / "Saved" / "Loop"
PYTHON_DIR = str(PROJECT_ROOT / "Content" / "Python")
PY = Path(sys.executable)


def state_path(daemon_name: str) -> Path:
    return STATE_DIR / f"gmm_{daemon_name}_daemon.json"


def load_state(daemon_name: str) -> dict:
    path = state_path(daemon_name)
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "daemon": daemon_name,
        "tick": 0,
        "completed": [],
        "failed": [],
        "log": [],
    }


def save_state(daemon_name: str, state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_path(daemon_name).write_text(json.dumps(state, indent=2), encoding="utf-8")


def stage_output(
    daemon_name: str,
    tick: int,
    rel_path: str,
    content: str,
    task: dict,
) -> Path:
    tick_dir = STAGING_ROOT / daemon_name / f"tick_{tick:04d}"
    tick_dir.mkdir(parents=True, exist_ok=True)
    safe_name = rel_path.replace("/", "_").replace("\\", "_")
    target = tick_dir / safe_name
    target.write_text(content, encoding="utf-8")
    meta = {
        "daemon": daemon_name,
        "tick": tick,
        "task_id": task.get("id"),
        "desc": task.get("desc"),
        "target_file": rel_path,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    (tick_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return target


def run_smoke(modules: list[str], extra_fn: Optional[Callable[[], dict]] = None) -> dict:
    """Run unittest modules and optional extra smoke callable."""
    start = time.time()
    env = {**os.environ, "PYTHONPATH": PYTHON_DIR}
    if modules:
        cmd = [str(PY), "-m", "unittest"] + modules
        proc = subprocess.run(
            cmd, capture_output=True, text=True, env=env, cwd=PYTHON_DIR, timeout=90,
        )
        combined = proc.stdout + proc.stderr
        result_line = next((l for l in combined.split("\n") if l.startswith("Ran ")), "")
        ok = proc.returncode == 0 and "FAILED" not in combined
        returncode = proc.returncode
    else:
        combined = ""
        result_line = "no unittest modules"
        ok = True
        returncode = 0
    elapsed = time.time() - start
    out: dict[str, Any] = {
        "ok": ok,
        "returncode": returncode,
        "result": result_line,
        "elapsed": round(elapsed, 2),
    }
    if extra_fn:
        try:
            out["extra"] = extra_fn()
            if out["extra"].get("ok") is False:
                ok = False
                out["ok"] = False
        except Exception as exc:
            out["extra"] = {"ok": False, "error": str(exc)}
            out["ok"] = False
    return out


def pick_next_task(tasks: list[dict], completed: set[str], failed: set[str], tick: int) -> tuple[dict, bool]:
    """Return (task, cycling). cycling=True when re-running completed queue."""
    for t in tasks:
        if t["id"] not in completed and t["id"] not in failed:
            return t, False
    return tasks[(tick - 1) % len(tasks)], True


def run_tick(
    daemon_name: str,
    tasks: list[dict],
    generators: dict[str, Callable[[], Any]],
    smoke_modules: list[str],
    smoke_extra: Optional[Callable[[], dict]] = None,
    label: Optional[str] = None,
) -> int:
    """Execute one daemon tick: smoke tests, generate, stage, save state."""
    tag = label or f"GMM {daemon_name}"
    state = load_state(daemon_name)
    state["tick"] = state.get("tick", 0) + 1
    tick = state["tick"]
    completed = set(state.get("completed", []))
    generated = set(state.get("generated", state.get("completed", [])))
    failed = set(state.get("failed", []))
    now = datetime.now(timezone.utc)

    print(f"[{tag}] Tick {tick} — {now.strftime('%Y-%m-%d %H:%M UTC')}")

    print("  Running smoke...", end=" ")
    test_result = run_smoke(smoke_modules, smoke_extra)
    log_entry: dict[str, Any] = {"tick": tick, "timestamp": now.isoformat(), "test": test_result}

    if not test_result["ok"]:
        print(f"FAILED ({test_result.get('result', 'error')})")
        log = state.get("log", [])
        log.append(log_entry)
        state["log"] = log[-100:]
        state["last_test"] = test_result
        save_state(daemon_name, state)
        return 1

    print(f"OK ({test_result.get('result', 'ok')})")

    task, cycling = pick_next_task(tasks, completed, failed, tick)
    if cycling:
        log_entry["note"] = "All tasks completed once — cycling"

    gen_fn = generators.get(task["id"])
    if gen_fn:
        try:
            content = gen_fn()
            if isinstance(content, (list, dict)):
                content = json.dumps(content, indent=2)
            path = stage_output(daemon_name, tick, task["file"], str(content), task)
            print(f"  Generated: {task['desc']} -> {path}")
            completed.add(task["id"])
            generated.add(task["id"])
            failed.discard(task["id"])
            log_entry["task"] = task["id"]
            log_entry["status"] = "generated"
            log_entry["lifecycle"] = "generated_not_applied"
            log_entry["path"] = str(path)
        except Exception as exc:
            print(f"  FAILED: {task['desc']}: {exc}")
            failed.add(task["id"])
            log_entry["task"] = task["id"]
            log_entry["status"] = "error"
            log_entry["error"] = str(exc)
    else:
        print(f"  Skipped: {task['desc']} (no generator)")
        log_entry["task"] = task["id"]
        log_entry["status"] = "skipped"

    state["completed"] = sorted(completed)  # legacy name: means generated successfully
    state["generated"] = sorted(generated)
    state["failed"] = sorted(failed)
    state["last_batch"] = task["id"]
    state["last_test"] = test_result
    state["updated_at"] = now.isoformat()
    log = state.get("log", [])
    log.append(log_entry)
    state["log"] = log[-100:]
    save_state(daemon_name, state)

    print(f"  Progress: {len(completed)}/{len(tasks)} tasks completed")
    print(f"[{tag}] Tick {tick} done")
    return 0
