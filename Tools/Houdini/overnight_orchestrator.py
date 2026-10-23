#!/usr/bin/env python3
"""
Overnight Orchestrator — runs the recursive wool evolution + Melusina weight lab loop.

Architecture:
- Queue: Saved/Audit/overnight/queue.jsonl (one JSON per task)
- Evidence: Saved/Audit/overnight/generation_NNN/
- Log: Saved/Audit/overnight/OVERNIGHT_LOG.md
- State: Saved/Audit/overnight/state.json (current gen, best params)

Modes: A_flat, B_worley12, C_worley25, D_pop_worley12

Usage:
  python Tools/Houdini/overnight_orchestrator.py --max-gens 8 --modes A,B,C,D --start
  python Tools/Houdini/overnight_orchestrator.py --status
  python Tools/Houdini/overnight_orchestrator.py --resume
"""
import argparse
import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

OVERNIGHT_DIR = Path("Saved/Audit/overnight")
QUEUE_FILE = OVERNIGHT_DIR / "queue.jsonl"
STATE_FILE = OVERNIGHT_DIR / "state.json"
LOG_FILE = OVERNIGHT_DIR / "OVERNIGHT_LOG.md"

MODES = ["A_flat", "B_worley12", "C_worley25", "D_pop_worley12"]
PCS = list(range(12))
LABELS = ["C","Cs","D","Ds","E","F","Fs","G","Gs","A","As","B"]

MUTATION_SPACE = {
    "worley": [-0.02, 0.0, +0.02],
    "sat": [-0.03, 0.0, +0.03],
    "glow": [-0.02, 0.0, +0.02],
    "fibers": [0.0],  # fixed 0 for now
    "hue_shift": [-1.0, 0.0, +1.0],  # degrees
}

def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _ensure_dirs():
    OVERNIGHT_DIR.mkdir(parents=True, exist_ok=True)
    for g in range(100):
        (OVERNIGHT_DIR / f"generation_{g:03d}" / "renders").mkdir(parents=True, exist_ok=True)

def _load_state():
    if STATE_FILE.is_file():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {
        "current_gen": 0,
        "best": {m: {"params": None, "avg_score": 0.0} for m in MODES},
        "history": [],
    }

def _save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")

def _append_log(line):
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"{_now()}  {line}\n")

def _write_queue(tasks):
    """Write tasks to queue.jsonl (append)."""
    with QUEUE_FILE.open("a", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps(t) + "\n")

def _read_queue():
    if not QUEUE_FILE.is_file():
        return []
    tasks = []
    for line in QUEUE_FILE.read_text(encoding="utf-8").splitlines():
        try:
            tasks.append(json.loads(line))
        except Exception:
            pass
    return tasks

def _clear_queue():
    if QUEUE_FILE.is_file():
        QUEUE_FILE.unlink()

def _init_queue(max_gens, modes):
    """Initialize queue with first generation tasks."""
    _clear_queue()
    tasks = []
    task_id = 0
    # Generation 0: just score the 4 base modes (no mutation)
    for mode in modes:
        for pc in PCS:
            task_id += 1
            tasks.append({
                "id": f"G000_W{task_id:03d}",
                "type": "wool_evolve",
                "stage": "score_base",
                "gen": 0,
                "mode": mode,
                "pc": pc,
                "params": {
                    "worley": 0.0 if mode=="A_flat" else 0.12,
                    "sat": 0.38 if mode!="D_pop_worley12" else 0.52,
                    "glow": 0.09,
                    "fibers": 0.0,
                    "hue_shift": 0.0,
                },
                "mutation": {},
                "deps": [],
                "status": "pending",
                "created": _now(),
            })
    _write_queue(tasks)
    print(f"[orch] initialized {len(tasks)} base scoring tasks (gen 0)")

def _run_task(task):
    """Execute a single task via mutate_wool.py subprocess."""
    cmd = [
        sys.executable,
        "Tools/Houdini/mutate_wool.py",
        "--mode", task["mode"],
        "--pc", str(task["pc"]),
        "--params", json.dumps(task["params"]),
        "--mutation", json.dumps(task.get("mutation", {})),
        "--size", "512",
        "--gen", str(task["gen"]),
        "--out-root", "Saved/Audit/overnight",
    ]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path.cwd())
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    if proc.returncode != 0:
        return {"ok": False, "error": proc.stderr[-500:], "stdout": proc.stdout[-500:]}
    try:
        result = json.loads(proc.stdout.strip().splitlines()[-1])
        return {"ok": True, "result": result}
    except Exception as e:
        return {"ok": False, "error": f"parse failed: {e}", "stdout": proc.stdout[-500:]}

def _run_generation(gen, modes):
    """Run all tasks for a generation, return results."""
    tasks = _read_queue()
    gen_tasks = [t for t in tasks if t.get("gen") == gen and t.get("status") == "pending"]
    if not gen_tasks:
        return []
    print(f"[orch] gen {gen}: {len(gen_tasks)} tasks")
    results = []
    for i, task in enumerate(gen_tasks):
        # mark running
        task["status"] = "running"
        task["started"] = _now()
        _update_queue(tasks)
        _append_log(f"  [{task['id']}] START {task['mode']} PC{task['pc']:02d} {task.get('stage','')}")

        run_result = _run_task(task)
        task["status"] = "done" if run_result["ok"] else "failed"
        task["finished"] = _now()
        if run_result["ok"]:
            res = run_result["result"]
            task["result"] = res
            _append_log(f"  [{task['id']}] OK scores={res['scores']} promoted={res['promoted']}")
            results.append({"task": task, "result": res})
        else:
            _append_log(f"  [{task['id']}] FAILED: {run_result['error']}")
        _update_queue(tasks)
        # small delay to not hammer disk
        time.sleep(0.1)
    return results

def _update_queue(tasks):
    with QUEUE_FILE.open("w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps(t) + "\n")

def _aggregate_and_propose(gen, results, modes):
    """Aggregate scores per mode, propose next gen mutations."""
    if not results:
        return []
    # Group by mode
    from collections import defaultdict
    mode_results = defaultdict(list)
    for r in results:
        mode_results[r["task"]["mode"]].append(r)
    next_tasks = []
    task_id = 0
    # Find current max task id
    all_tasks = _read_queue()
    max_id = max([int(t["id"].split("_")[1][1:]) for t in all_tasks if "_" in t["id"]], default=0)

    for mode in modes:
        mres = mode_results.get(mode, [])
        if not mres:
            continue
        # Average scores across PCs
        avg_scores = {}
        for k in mres[0]["result"]["scores"].keys():
            avg_scores[k] = sum(r["result"]["scores"][k] for r in mres) / len(mres)
        avg_total = sum(avg_scores.values()) / len(avg_scores)

        # Get current best params (from last result's params)
        best_task = max(mres, key=lambda r: sum(r["result"]["scores"].values()))
        best_params = best_task["result"]["params"]

        print(f"[orch] gen {gen} {mode}: avg={avg_total:.2f} | wool={avg_scores['wool_reading']:.1f} glow={avg_scores['glow_subtlety']:.1f} nissi={avg_scores['nissi_softness']:.1f}")

        # If promoted (heuristic >=8.5 all), keep params, just add tiny jitter for next gen
        promoted = all(v >= 8.5 for v in avg_scores.values())
        if promoted:
            _append_log(f"    PROMOTED {mode} — params locked, jitter only")
            # Just jitter for stability
            for pc in PCS:
                task_id += 1; max_id += 1
                jitter = {k: random.choice([-0.005, 0, 0.005]) for k in MUTATION_SPACE if k in best_params}
                next_tasks.append({
                    "id": f"G{gen+1:03d}_W{max_id:03d}",
                    "type": "wool_evolve",
                    "stage": "mutate",
                    "gen": gen + 1,
                    "mode": mode,
                    "pc": pc,
                    "params": best_params.copy(),
                    "mutation": jitter,
                    "deps": [],
                    "status": "pending",
                    "created": _now(),
                })
        else:
            # Propose mutations: for each PC, try 2-3 param changes
            # Use gradient-ish: if wool low, increase worley; if glow high, decrease glow; etc.
            for pc in PCS:
                # Propose 2 mutations per PC
                for _ in range(2):
                    task_id += 1; max_id += 1
                    mutation = {}
                    # Heuristic: adjust toward targets
                    mres_pc = [r for r in mres if r["task"]["pc"] == pc]
                    if mres_pc:
                        sc = mres_pc[0]["result"]["scores"]
                        if sc["wool_reading"] < 7:
                            mutation["worley"] = random.choice([+0.02, +0.04])
                        if sc["glow_subtlety"] < 7:
                            mutation["glow"] = random.choice([-0.02, -0.03])
                        if sc["nissi_softness"] < 7:
                            mutation["sat"] = random.choice([-0.03, -0.06])
                        if sc["emission_balance"] < 7:
                            mutation["hue_shift"] = random.choice([-2.0, +2.0])
                    # Always add some exploration noise
                    for k, choices in MUTATION_SPACE.items():
                        if k not in mutation and k in best_params:
                            mutation[k] = random.choice(choices)
                    # Ensure at least one mutation
                    if not mutation:
                        mutation["worley"] = random.choice([-0.02, 0, +0.02])
                    next_tasks.append({
                        "id": f"G{gen+1:03d}_W{max_id:03d}",
                        "type": "wool_evolve",
                        "stage": "mutate",
                        "gen": gen + 1,
                        "mode": mode,
                        "pc": pc,
                        "params": best_params.copy(),
                        "mutation": mutation,
                        "deps": [],
                        "status": "pending",
                        "created": _now(),
                    })
    return next_tasks

def _run_melusina_weight_lab():
    """Build and run weight lab HIP for sheep test."""
    print("[orch] Building Melusina weight lab (sheep test)...")
    # Build HIP
    build_cmd = [
        sys.executable, "Tools/Houdini/build_melusina_weight_lab.py",
        "--out", "Tools/Houdini/melusina_weight_lab.hipnc",
        "--test-sheep"
    ]
    proc = subprocess.run(build_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    if proc.returncode != 0:
        _append_log(f"  WLAB BUILD FAILED: {proc.stderr[-300:]}")
        return False
    _append_log("  WLAB HIP built (stub, needs hython)")
    # If hython available, cook
    hython = Path(os.environ.get("HOUDINI_HYTHON_EXE", r"C:\Program Files\Side Effects Software\Houdini 20.5\bin\hython.exe"))
    if hython.is_file():
        cook_cmd = [str(hython), "Tools/Houdini/build_melusina_weight_lab.py", "--out", "Tools/Houdini/melusina_weight_lab.hipnc", "--test-sheep"]
        proc = subprocess.run(cook_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
        if proc.returncode == 0:
            _append_log("  WLAB cooked via hython — check Saved/Audit/melusina_weight_lab/")
        else:
            _append_log(f"  WLAB hython cook failed: {proc.stderr[-300:]}")
    return True

def cmd_start(args):
    _ensure_dirs()
    state = _load_state()
    if args.max_gens:
        state["max_gens"] = args.max_gens
    if args.modes:
        state["modes"] = [m.strip() for m in args.modes.split(",")]
    _save_state(state)

    modes = state.get("modes", MODES)
    max_gens = state.get("max_gens", 8)

    # Initialize queue
    _init_queue(max_gens, modes)

    # Run Melusina weight lab first
    _run_melusina_weight_lab()

    # Run generations
    for gen in range(max_gens):
        state["current_gen"] = gen
        _save_state(state)
        _append_log(f"=== GENERATION {gen} START ===")
        _run_generation(gen, modes)
        results = []  # would collect from _run_generation in real impl
        # For now, just simulate one gen to test
        if gen == 0:
            print(f"[orch] Gen 0 complete. Queue has {len(_read_queue())} tasks.")
            break  # demo only runs gen 0

    _append_log(f"=== OVERNIGHT RUN COMPLETE (demo) ===")

def cmd_status(args):
    state = _load_state()
    tasks = _read_queue()
    print(f"Current Gen: {state.get('current_gen', 0)}")
    print(f"Max Gens: {state.get('max_gens', 8)}")
    print(f"Modes: {state.get('modes', MODES)}")
    print(f"Queue: {len(tasks)} tasks")
    statuses = {}
    for t in tasks:
        s = t.get("status", "unknown")
        statuses[s] = statuses.get(s, 0) + 1
    for s, c in sorted(statuses.items()):
        print(f"  {s}: {c}")
    if LOG_FILE.is_file():
        lines = LOG_FILE.read_text(encoding="utf-8").splitlines()
        print(f"Log: {len(lines)} lines (last 5):")
        for l in lines[-5:]:
            print(f"  {l}")

def cmd_resume(args):
    state = _load_state()
    max_gens = state.get("max_gens", 8)
    modes = state.get("modes", MODES)
    for gen in range(state.get("current_gen", 0), max_gens):
        state["current_gen"] = gen
        _save_state(state)
        _append_log(f"=== GENERATION {gen} RESUME ===")
        _run_generation(gen, modes)

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("start")
    sp.add_argument("--max-gens", type=int, default=8)
    sp.add_argument("--modes", default="A_flat,B_worley12,C_worley25,D_pop_worley12")
    sp.set_defaults(func=cmd_start)
    sp = sub.add_parser("status")
    sp.set_defaults(func=cmd_status)
    sp = sub.add_parser("resume")
    sp.set_defaults(func=cmd_resume)
    args = ap.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()