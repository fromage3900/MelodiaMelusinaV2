"""Q# shim for experiments.

This shim imitates a Q# ranker by applying a deterministic pseudo-quantum
heuristic so experiments can run without QDK installed.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List


def _pseudo_quantum_score(features: Dict[str, Any]) -> float:
    # Combine features into a non-linear score to simulate ``quantum`` behavior
    x = float(features.get("x", 0.0))
    y = float(features.get("y", 0.0))
    # Use a non-linear function with periodic component
    return round((math.sin(x * 12.34) * 0.5 + 0.5) * 0.6 + (y ** 2) * 0.4, 4)


def rank_layouts(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not candidates:
        raise ValueError("no candidates")
    scored = []
    for c in candidates:
        features = c.get("features", {})
        s = _pseudo_quantum_score(features)
        scored.append((s, c))
    scored.sort(key=lambda t: t[0], reverse=True)
    winner = scored[0][1]
    return {"winner_id": winner.get("id"), "score": float(scored[0][0])}
