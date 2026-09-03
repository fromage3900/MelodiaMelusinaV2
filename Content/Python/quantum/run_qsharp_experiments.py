"""Run the honest Q# kernel via layout_ranker and record two-candidate trials.

Writes `qsharp_results.csv` and `qsharp_summary.json` in the repo root.

Uses `layout_ranker.pick_best_index` / `rank_layouts` as the single Q# entry
point (qdk interpreter). Run from the workspace root:
    python BS_GodFile/Content/Python/quantum/run_qsharp_experiments.py
"""
from __future__ import annotations

import collections
import csv
import json
import random
import statistics
import time
from typing import Any, Dict, List

from BS_GodFile.Content.Python.quantum import layout_ranker

NUM_TRIALS = 100
OUT_CSV = "qsharp_results.csv"
OUT_SUM = "qsharp_summary.json"


def generate_two_candidates(seed: int) -> List[Dict[str, Any]]:
    random.seed(seed)
    c0 = {"id": "A", "difficulty": 0.2 + random.random() * 0.8, "spacing": 0.1 + random.random() * 0.9}
    c1 = {"id": "B", "difficulty": 0.2 + random.random() * 0.8, "spacing": 0.1 + random.random() * 0.9}
    return [c0, c1]


def main() -> None:
    print("Q# available:", layout_ranker._QSHARP_AVAILABLE)
    if not layout_ranker._QSHARP_AVAILABLE:
        print("Q# kernel not loaded; every trial will report classical-baseline.")

    # Direct kernel sanity check: the measurement must be genuinely
    # score-weighted, not deterministic. A(0.5,0.5) scores 0.83, B(0.8,0.6)
    # scores 0.95, so P(A) ~ 0.466 -- expect a visible mix, not all-B.
    sanity_wins = collections.Counter()
    for _ in range(40):
        idx = layout_ranker.pick_best_index(0.5, 0.5, 0.8, 0.6)
        sanity_wins["A" if idx == 0 else "B"] += 1
    print("kernel sanity (40 shots, A=0.83 vs B=0.95):", dict(sanity_wins))

    rows: List[Dict[str, Any]] = []
    latencies: List[float] = []
    wins = {"A": 0, "B": 0}
    backends = collections.Counter()

    for t in range(NUM_TRIALS):
        seed = 2000 + t
        candidates = generate_two_candidates(seed)
        start = time.perf_counter()
        try:
            res = layout_ranker.rank_layouts(seed, candidates)
        except Exception as e:
            print(f"Trial {t} rank_layouts failed:", type(e).__name__, e)
            continue
        lat = (time.perf_counter() - start) * 1000.0
        latencies.append(lat)

        winner = res.winner_id
        backend = res.backend
        score = res.score
        backends[backend] += 1

        rows.append({"trial": t, "winner": winner, "score": score, "backend": backend, "latency_ms": lat})
        if winner in wins:
            wins[winner] += 1

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["trial", "winner", "score", "backend", "latency_ms"])
        w.writeheader()
        for r in rows:
            w.writerow(r)

    summary = {
        "num_trials": NUM_TRIALS,
        "kernel_sanity_40_shots": dict(sanity_wins),
        "mean_latency_ms": statistics.mean(latencies) if latencies else None,
        "backends": dict(backends),
        "wins": wins,
    }
    with open(OUT_SUM, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Wrote {OUT_CSV} and {OUT_SUM}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
