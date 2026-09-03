"""Quantum gameplay experiment service helpers.

This module provides a small, UE-friendly contract for ranking layout or
encounter candidates and is intentionally split so it can be wired to a real
Q# backend later.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
import os


# Q# loader (qdk interpreter). The installed 'qsharp' package is the qdk
# interpreter -- the legacy 0.17 API (compile(src) then import) is gone. The
# 'qsharp' shim re-exports the high-level eval/run API; plain 'qdk' does not,
# so prefer 'qsharp' first. Everything stays optional so the baseline works
# when QDK isn't installed.
_QK = None
try:
    import qsharp as _QK  # type: ignore
except Exception:
    try:
        import qdk as _QK  # type: ignore
    except Exception:
        _QK = None

_QSHARP_AVAILABLE = False
_QSHARP_EXPR = "QuantumGameplay.Experiment.PickBestCandidate"
_QS_FILE = os.path.join(os.path.dirname(__file__), "qsharp_layout_ranker.qs")
if _QK is not None and os.path.exists(_QS_FILE):
    try:
        _QK.init(target_profile=_QK.TargetProfile.Base)
        with open(_QS_FILE, "r", encoding="utf-8") as _f:
            _QK.eval(_f.read())
        _QSHARP_AVAILABLE = True
    except Exception:
        _QSHARP_AVAILABLE = False


def pick_best_index(difficulty_a: float, spacing_a: float, difficulty_b: float, spacing_b: float) -> int | None:
    """Run the honest score-weighted Q# kernel once; return 0 or 1, or None on failure.

    The kernel amplitude-encodes P(|0>) = sA/(sA+sB) and the single
    measurement IS the pick.
    """
    if not _QSHARP_AVAILABLE:
        return None
    try:
        expr = f"{_QSHARP_EXPR}({difficulty_a}, {spacing_a}, {difficulty_b}, {spacing_b})"
        res = _QK.run(expr, 1)[0]
    except Exception:
        return None
    return 0 if str(res).lower().startswith("zero") else 1


@dataclass(frozen=True)
class LayoutCandidate:
    id: str
    difficulty: float
    spacing: float


@dataclass(frozen=True)
class LayoutRankResult:
    job_id: str
    status: str
    winner_id: str
    score: float
    backend: str
    candidates: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def score_candidate(candidate: LayoutCandidate) -> float:
    """Classical fallback scoring for the first vertical slice.

    This is a baseline so the workflow can be tested before the Q# backend is
    fully wired. The score favors balanced difficulty and spacing.
    """
    balance = 1.0 - abs(candidate.difficulty - 0.75)
    spacing = 1.0 - abs(candidate.spacing - 0.55)
    return round(max(0.0, (balance * 0.6) + (spacing * 0.4)), 4)


def rank_layouts(seed: int, candidates: list[dict[str, Any]]) -> LayoutRankResult:
    parsed = [LayoutCandidate(id=str(item["id"]), difficulty=float(item["difficulty"]), spacing=float(item["spacing"])) for item in candidates]
    if not parsed:
        raise ValueError("at least one candidate is required")
    # If Q# is available and we have exactly two candidates, use the Q# kernel to pick.
    if _QSHARP_AVAILABLE and len(parsed) == 2:
        try:
            winner_index = pick_best_index(parsed[0].difficulty, parsed[0].spacing, parsed[1].difficulty, parsed[1].spacing)
            if winner_index is None:
                raise RuntimeError("Q# kernel failed")
            winner = parsed[winner_index]
            # compute scores for reporting
            scored = [(score_candidate(candidate), candidate) for candidate in parsed]
            scored.sort(key=lambda pair: pair[0], reverse=True)
            best_score = next((s for s, c in scored if c.id == winner.id), scored[0][0])
            backend = "qsharp-simulator"
        except Exception:
            # fallback to classical baseline on any Q# error
            scored = [(score_candidate(candidate), candidate) for candidate in parsed]
            scored.sort(key=lambda pair: pair[0], reverse=True)
            best_score, winner = scored[0]
            backend = "classical-baseline"
    else:
        scored = [(score_candidate(candidate), candidate) for candidate in parsed]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        best_score, winner = scored[0]
        backend = "classical-baseline"

    return LayoutRankResult(
        job_id=f"qjob_{seed:06d}",
        status="completed",
        winner_id=winner.id,
        score=best_score,
        backend=backend,
        candidates=[{"id": candidate.id, "difficulty": candidate.difficulty, "spacing": candidate.spacing, "score": score} for score, candidate in scored],
    )
