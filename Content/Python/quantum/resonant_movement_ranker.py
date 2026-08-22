"""Async-safe movement selection for the Resonant World composer.

This is deliberately narrower than a procedural generator.  It scores a
small set of authored world movements, records the classical baseline, and
optionally performs one honest two-candidate Q# measurement.  The returned
trace is intended to be persisted with the world seed before Unreal applies
the movement, so a quantum draw never makes a saved world unreplayable.

No Q# installation means a truthful classical fallback.  There is no
quantum-themed pseudo-random implementation here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


RANKER_VERSION = "resonant_movement_ranker_v1"
OBJECTIVE_WEIGHTS = {
    "outfit_synergy": 0.30,
    "asset_coverage": 0.25,
    "traversal_safety": 0.20,
    "visual_contrast": 0.15,
    "motif_continuity": 0.10,
}


_QK = None
try:
    import qsharp as _QK  # type: ignore
except Exception:
    try:
        import qdk as _QK  # type: ignore
    except Exception:
        _QK = None

_QSHARP_AVAILABLE = False
_QSHARP_EXPR = "QuantumGameplay.WorldComposer.PickMovement"
_QS_FILE = Path(__file__).with_name("qsharp_world_movement_ranker.qs")
if _QK is not None and _QS_FILE.exists():
    try:
        _QK.init(target_profile=_QK.TargetProfile.Base)
        _QK.eval(_QS_FILE.read_text(encoding="utf-8"))
        _QSHARP_AVAILABLE = True
    except Exception:
        _QSHARP_AVAILABLE = False


@dataclass(frozen=True)
class MovementCandidate:
    id: str
    movement_id: str
    features: dict[str, float]

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "movement_id": self.movement_id, "features": dict(self.features)}


def _bounded(value: Any) -> float:
    return max(0.0, min(1.0, float(value)))


def score_candidate(candidate: MovementCandidate) -> float:
    return round(
        sum(weight * _bounded(candidate.features.get(name, 0.0)) for name, weight in OBJECTIVE_WEIGHTS.items()),
        6,
    )


def _classical_winner(candidates: list[MovementCandidate]) -> tuple[MovementCandidate, float, list[dict[str, Any]]]:
    scored = [(score_candidate(candidate), candidate) for candidate in candidates]
    scored.sort(key=lambda item: (-item[0], item[1].id))
    rows = [
        {"id": candidate.id, "movement_id": candidate.movement_id, "score": score, "features": dict(candidate.features)}
        for score, candidate in scored
    ]
    return scored[0][1], scored[0][0], rows


def _qsharp_pick(score_a: float, score_b: float) -> int | None:
    if not _QSHARP_AVAILABLE:
        return None
    try:
        expression = f"{_QSHARP_EXPR}({score_a}, {score_b})"
        result = _QK.run(expression, 1)[0]
    except Exception:
        return None
    return 0 if str(result).lower().startswith("zero") else 1


def rank_movements(
    seed: int,
    candidates: Iterable[MovementCandidate | Mapping[str, Any]],
    backend: str = "classical-baseline",
) -> dict[str, Any]:
    parsed = [
        item if isinstance(item, MovementCandidate) else MovementCandidate(
            id=str(item["id"]),
            movement_id=str(item.get("movement_id", item["id"])),
            features={key: _bounded(value) for key, value in dict(item.get("features", {})).items()},
        )
        for item in candidates
    ]
    if not parsed:
        raise ValueError("at least one movement candidate is required")
    baseline, baseline_score, baseline_rows = _classical_winner(parsed)

    winner = baseline
    winner_score = baseline_score
    actual_backend = "classical-baseline"
    if backend == "qsharp-simulator" and len(parsed) == 2:
        scores = [score_candidate(candidate) for candidate in parsed]
        winner_index = _qsharp_pick(scores[0], scores[1])
        if winner_index is not None:
            winner = parsed[winner_index]
            winner_score = scores[winner_index]
            actual_backend = "qsharp-simulator"
    elif backend not in {"classical-baseline", "qsharp-simulator"}:
        raise ValueError("backend must be classical-baseline or qsharp-simulator")

    trace_id = hashlib.sha256(
        json.dumps(
            {
                "seed": int(seed),
                "backend_requested": backend,
                "candidate_ids": [candidate.id for candidate in parsed],
                "ranker_version": RANKER_VERSION,
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()[:16]
    return {
        "job_id": f"world-composer_{int(seed):010d}",
        "status": "completed",
        "ranker_version": RANKER_VERSION,
        "winner_id": winner.id,
        "winner_movement_id": winner.movement_id,
        "winner_score": winner_score,
        "backend_requested": backend,
        "backend": actual_backend,
        "qsharp_available": _QSHARP_AVAILABLE,
        "classical_baseline_winner_id": baseline.id,
        "classical_baseline_score": baseline_score,
        "candidate_scores": baseline_rows,
        "trace_id": trace_id,
        "replay_contract": {
            "persist_result_before_world_apply": True,
            "seed_is_not_a_substitute_for_persisted_quantum_draw": actual_backend == "qsharp-simulator",
            "unreal_application_boundary": "async movement result -> authored PCG binding",
        },
    }


def candidates_from_atlas(atlas: Mapping[str, Any], movement_ids: Iterable[str] | None = None) -> list[MovementCandidate]:
    requested = set(movement_ids or atlas.get("world_movements", {}))
    candidates: list[MovementCandidate] = []
    for movement_id, record in sorted(atlas.get("world_movements", {}).items()):
        if movement_id not in requested:
            continue
        counts = record.get("asset_counts", {})
        objectives = set(record.get("quantum_objective", []))
        features = {
            "outfit_synergy": 1.0 if counts.get("outfit_and_archetype", 0) > 0 else 0.0,
            "asset_coverage": min(1.0, (sum(counts.values()) / 80.0)),
            "traversal_safety": 0.85 if "safe_traversal" in objectives or "traversal_safety" in objectives else 0.70,
            "visual_contrast": 0.85 if "visual_novelty" in objectives else 0.72,
            "motif_continuity": 0.90 if "motif_continuity" in objectives else 0.68,
        }
        candidates.append(MovementCandidate(movement_id, movement_id, features))
    return candidates


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--atlas", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=3900)
    parser.add_argument("--backend", choices=("classical-baseline", "qsharp-simulator"), default="classical-baseline")
    parser.add_argument("--candidate", action="append", dest="candidates", help="movement id; repeat to compare two movements")
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    atlas = json.loads(args.atlas.read_text(encoding="utf-8"))
    candidates = candidates_from_atlas(atlas, args.candidates)
    result = rank_movements(args.seed, candidates, args.backend)
    encoded = json.dumps(result, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    else:
        print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
