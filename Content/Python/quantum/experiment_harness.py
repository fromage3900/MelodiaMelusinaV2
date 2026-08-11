"""
Experiment harness to compare classical `layout_ranker.rank_layouts` vs a Q# path.

Usage:
    python experiment_harness.py --trials 50 --out results.csv --summary results.json

This script attempts to import `layout_ranker.rank_layouts` for the classical
baseline. For the Q# path it calls a local stub `qsharp_ranker.rank_layouts`
if available — otherwise `use_qsharp=True` will raise an informative error.

Results are written to CSV with fields: trial, winner_id, score, backend, latency_ms
and a small JSON summary with mean latencies and win-rate differences.
"""
from __future__ import annotations

import argparse
import csv
import json
import logging
import random
import statistics
import time
import inspect
from typing import Any, Dict, List, Tuple

logger = logging.getLogger("experiment_harness")
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


def load_classical_ranker():
    try:
        from layout_ranker import rank_layouts

        return rank_layouts
    except Exception:
        logger.exception("Could not import `layout_ranker.rank_layouts`. Ensure it's on PYTHONPATH.")
        raise


def load_qsharp_ranker():
    try:
        # Attempt to import a qsharp shim module if present
        from qsharp_ranker import rank_layouts as q_rank

        return q_rank
    except Exception:
        logger.exception("Q# ranker not available (qsharp_ranker.rank_layouts). Install or provide a shim.)")
        raise


def run_trial(seed: int, candidates: List[Dict[str, Any]], use_qsharp: bool = False) -> Tuple[str, float, str, float]:
    """Run a single trial. Returns (winner_id, score, backend, latency_ms).

    `candidates` is a list of dicts that the ranker understands.
    """
    random.seed(seed)
    start = time.perf_counter()

    if use_qsharp:
        ranker = load_qsharp_ranker()
        backend = "qsharp"
    else:
        ranker = load_classical_ranker()
        backend = "classical"

    # Call the ranker; support either signature: (seed, candidates) or (candidates,)
    try:
        sig = inspect.signature(ranker)
        if len(sig.parameters) >= 2:
            res = ranker(seed, candidates)
        else:
            res = ranker(candidates)
    except Exception:
        logger.exception("Ranker failed for backend=%s", backend)
        raise

    latency_ms = (time.perf_counter() - start) * 1000.0

    if isinstance(res, tuple) and len(res) >= 2:
        winner_id, score = res[0], float(res[1])
    elif isinstance(res, dict):
        winner_id = res.get("winner_id") or res.get("winner") or ""
        score = float(res.get("score", 0.0))
    else:
        # Try to infer
        winner_id = str(res)
        score = 0.0

    return winner_id, score, backend, latency_ms


def generate_candidates(n: int = 5, seed: int = None) -> List[Dict[str, Any]]:
    if seed is not None:
        random.seed(seed)
    out = []
    for i in range(n):
        x = random.random()
        y = random.random()
        # Map x/y to difficulty/spacing ranges expected by layout_ranker
        difficulty = 0.2 + x * 0.8  # range [0.2, 1.0]
        spacing = 0.1 + y * 0.9     # range [0.1, 1.0]
        out.append({
            "id": f"cand_{i}",
            "difficulty": difficulty,
            "spacing": spacing,
            "features": {"x": x, "y": y},
        })
    return out


def run_experiments(num_trials: int, out_csv: str, summary_json: str, candidates_per_trial: int = 5):
    rows = []
    classical_latencies = []
    qsharp_latencies = []
    classical_wins = 0
    qsharp_wins = 0

    for t in range(num_trials):
        seed = 1000 + t
        candidates = generate_candidates(candidates_per_trial, seed=seed)

        # classical
        try:
            winner_c, score_c, _, lat_c = run_trial(seed, candidates, use_qsharp=False)
        except Exception:
            logger.exception("Classical trial %d failed", t)
            continue

        # qsharp
        try:
            winner_q, score_q, _, lat_q = run_trial(seed, candidates, use_qsharp=True)
        except Exception:
            logger.exception("Q# trial %d failed; marking as failed", t)
            continue

        classical_latencies.append(lat_c)
        qsharp_latencies.append(lat_q)

        # Decide winners by score (higher better)
        if score_c >= score_q:
            classical_wins += 1
        else:
            qsharp_wins += 1

        rows.append({
            "trial": t,
            "classical_winner": winner_c,
            "classical_score": score_c,
            "classical_latency_ms": lat_c,
            "qsharp_winner": winner_q,
            "qsharp_score": score_q,
            "qsharp_latency_ms": lat_q,
        })

    # Write CSV
    fieldnames = [
        "trial",
        "classical_winner",
        "classical_score",
        "classical_latency_ms",
        "qsharp_winner",
        "qsharp_score",
        "qsharp_latency_ms",
    ]
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    summary = {
        "num_trials": num_trials,
        "classical_mean_latency_ms": statistics.mean(classical_latencies) if classical_latencies else None,
        "qsharp_mean_latency_ms": statistics.mean(qsharp_latencies) if qsharp_latencies else None,
        "classical_win_rate": classical_wins / (classical_wins + qsharp_wins) if (classical_wins + qsharp_wins) else None,
        "qsharp_win_rate": qsharp_wins / (classical_wins + qsharp_wins) if (classical_wins + qsharp_wins) else None,
        "classical_wins": classical_wins,
        "qsharp_wins": qsharp_wins,
    }

    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info("Wrote results to %s and summary to %s", out_csv, summary_json)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--trials", type=int, default=50)
    p.add_argument("--out", type=str, default="results.csv")
    p.add_argument("--summary", type=str, default="summary.json")
    p.add_argument("--candidates", type=int, default=5)
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    try:
        run_experiments(args.trials, args.out, args.summary, candidates_per_trial=args.candidates)
    except Exception:
        logger.exception("Experiment run failed.")
