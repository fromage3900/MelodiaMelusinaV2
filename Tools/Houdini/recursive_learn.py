#!/usr/bin/env python3
"""
Recursive Learning Controller — analyzes overnight results, proposes next mutations.

Reads: Saved/Audit/overnight/generation_NNN/ results
Writes: next generation task proposals to queue

Run after each generation completes:
  python Tools/Houdini/recursive_learn.py --gen 1
"""
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

OVERNIGHT_DIR = Path("Saved/Audit/overnight")
QUEUE_FILE = OVERNIGHT_DIR / "queue.jsonl"
STATE_FILE = OVERNIGHT_DIR / "state.json"

MODES = ["A_flat", "B_worley12", "C_worley25", "D_pop_worley12"]
PCS = list(range(12))

MUTATION_SPACE = {
    "worley": [-0.02, 0.0, +0.02],
    "sat": [-0.03, 0.0, +0.03],
    "glow": [-0.02, 0.0, +0.02],
    "fibers": [0.0],
    "hue_shift": [-1.0, 0.0, +1.0],
}

PARAM_BOUNDS = {
    "worley": (0.0, 0.30),
    "sat": (0.35, 0.55),
    "glow": (0.04, 0.18),
    "fibers": (0.0, 1.0),
    "hue_shift": (-5.0, 5.0),
}

def _clamp_params(params):
    for k, (lo, hi) in PARAM_BOUNDS.items():
        if k in params:
            params[k] = max(lo, min(hi, params[k]))
    return params

def _load_gen_results(gen):
    """Load all task results from queue for a generation."""
    if not QUEUE_FILE.is_file():
        return []
    tasks = []
    for line in QUEUE_FILE.read_text(encoding="utf-8").splitlines():
        try:
            t = json.loads(line)
            if t.get("gen") == gen and t.get("status") == "done" and "result" in t:
                tasks.append(t)
        except Exception:
            pass
    return tasks

def _analyze(gen):
    tasks = _load_gen_results(gen)
    if not tasks:
        print(f"[learn] No completed tasks for gen {gen}")
        return None
    # Group by mode
    mode_groups = defaultdict(list)
    for t in tasks:
        mode_groups[t["mode"]].append(t)
    analysis = {}
    for mode, m_tasks in mode_groups.items():
        # Average scores across PCs
        scores_sum = defaultdict(float)
        for t in m_tasks:
            for k, v in t["result"]["scores"].items():
                scores_sum[k] += v
        n = len(m_tasks)
        avg_scores = {k: v/n for k, v in scores_sum.items()}
        avg_total = sum(avg_scores.values()) / len(avg_scores)
        # Best individual task
        best_task = max(m_tasks, key=lambda t: sum(t["result"]["scores"].values()))
        analysis[mode] = {
            "n_tasks": n,
            "avg_scores": avg_scores,
            "avg_total": avg_total,
            "best_params": best_task["result"]["params"],
            "best_scores": best_task["result"]["scores"],
            "promoted": all(v >= 8.5 for v in avg_scores.values()),
        }
    return analysis

def _propose_mutations(analysis, gen):
    """Propose next gen tasks based on analysis."""
    proposals = []
    task_counter = 0
    # Get max existing task ID
    max_id = 0
    if QUEUE_FILE.is_file():
        for line in QUEUE_FILE.read_text(encoding="utf-8").splitlines():
            try:
                t = json.loads(line)
                if "_" in t.get("id", ""):
                    parts = t["id"].split("_")
                    if len(parts) > 1 and parts[1].startswith("W"):
                        num = int(parts[1][1:])
                        max_id = max(max_id, num)
            except Exception:
                pass

    for mode, a in analysis.items():
        if a["promoted"]:
            # Lock params, just stability jitter
            print(f"[learn] {mode} PROMOTED (avg={a['avg_total']:.2f}) — stability jitter only")
            for pc in PCS:
                for _ in range(1):  # 1 variant per PC for stability
                    task_counter += 1; max_id += 1
                    jitter = {}
                    for k, choices in {
                        "worley": [-0.005, 0, 0.005],
                        "sat": [-0.01, 0, 0.01],
                        "glow": [-0.005, 0, 0.005],
                    }.items():
                        if k in a["best_params"]:
                            jitter[k] = random.choice(choices)
                    proposals.append({
                        "id": f"G{gen+1:03d}_W{max_id+task_counter:03d}",
                        "type": "wool_evolve",
                        "stage": "stabilize",
                        "gen": gen + 1,
                        "mode": mode,
                        "pc": pc,
                        "params": a["best_params"].copy(),
                        "mutation": jitter,
                        "deps": [],
                        "status": "pending",
                        "created": datetime.now().isoformat(),
                    })
        else:
            # Gradient-ish proposals based on score deficits
            print(f"[learn] {mode} avg={a['avg_total']:.2f} — proposing mutations")
            for pc in PCS:
                # Find this PC's scores
                pc_task = next((t for t in m_tasks if t["pc"] == pc), None)
                if not pc_task:
                    continue
                sc = pc_task["result"]["scores"]
                # Propose 2 mutations per PC
                for proposal_i in range(2):
                    task_counter += 1; max_id += 1
                    mutation = {}
                    # Heuristic gradient
                    if sc["wool_reading"] < 7.5:
                        mutation["worley"] = random.choice([+0.02, +0.03])
                    if sc["glow_subtlety"] < 7.5:
                        mutation["glow"] = random.choice([-0.02, -0.01])
                    if sc["nissi_softness"] < 7.5:
                        mutation["sat"] = random.choice([-0.03, -0.02])
                    if sc["emission_balance"] < 7.5:
                        mutation["hue_shift"] = random.choice([-1.5, +1.5])
                    if sc["uv_stability"] < 8:
                        mutation["fibers"] = 0.1  # slight fiber for UV hide
                    # Exploration noise
                    for k, choices in MUTATION_SPACE.items():
                        if k not in mutation and k in a["best_params"]:
                            mutation[k] = random.choice(choices)
                    if not mutation:
                        mutation["worley"] = random.choice([-0.01, 0, +0.01])
                    proposals.append({
                        "id": f"G{gen+1:03d}_W{max_id+task_counter:03d}",
                        "type": "wool_evolve",
                        "stage": "mutate",
                        "gen": gen + 1,
                        "mode": mode,
                        "pc": pc,
                        "params": a["best_params"].copy(),
                        "mutation": mutation,
                        "deps": [],
                        "status": "pending",
                        "created": datetime.now().isoformat(),
                    })
    return proposals

def _write_proposals(proposals):
    """Append proposals to queue."""
    with QUEUE_FILE.open("a", encoding="utf-8") as f:
        for p in proposals:
            f.write(json.dumps(p) + "\n")
    print(f"[learn] wrote {len(proposals)} proposals to queue for next gen")

def main():
    import argparse
    from datetime import datetime
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", type=int, required=True, help="generation to analyze (results from this gen)")
    args = ap.parse_args()
    analysis = _analyze(args.gen)
    if not analysis:
        sys.exit(1)
    print(f"\n=== RECURSIVE LEARN — Gen {args.gen} Analysis ===")
    for mode, a in analysis.items():
        print(f"  {mode}: avg={a['avg_total']:.2f} wool={a['avg_scores']['wool_reading']:.1f} glow={a['avg_scores']['glow_subtlety']:.1f} nissi={a['avg_scores']['nissi_softness']:.1f} {'🏆 PROMOTED' if a['promoted'] else ''}")
    proposals = _propose_mutations(analysis, args.gen)
    _write_proposals(proposals)
    print(f"\nNext gen {args.gen+1} queued. Run: python Tools/Houdini/overnight_orchestrator.py --resume")

if __name__ == "__main__":
    from datetime import datetime
    main()