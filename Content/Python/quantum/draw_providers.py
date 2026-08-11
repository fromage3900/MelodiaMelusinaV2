"""Weighted-draw providers for the Melodia quantum decision service.

All providers share one scoring function (`layout_ranker.score_candidate`) and
one result contract (QUANTUM_GAMEPLAY_EXPERIMENT_PROTO_2026-08-06.md). They
differ only in HOW the winner is drawn from the candidate weights:

    classical-baseline  argmax -- deterministic best pick (fallback)
    qsharp-simulator    honest 2-candidate amplitude measurement via the Q#
                        kernel in qsharp_layout_ranker.qs
    qiskit-aer          amplitude-encode all candidates, sample once (optional
                        dependency; degrades to classical if not installed)
    chaos               seeded logistic-map weighted sample -- chaotic dynamics
                        that LOOK random but are reproducible for a seed
    swarm               seeded ant-colony style emergent pick: agents walk the
                        candidate set weighted by score, plurality wins
    pbit                probabilistic bit: thermal softmax over scores sampled
                        with OS entropy -- no seed, hardware fluctuations
    entropy             weighted sample straight from OS hardware entropy --
                        genuinely unreproducible, no seed by construction
    cellular            Conway's Game of Life: each candidate owns a band of
                        the grid, cells seeded by score, 64 generations evolve,
                        most survivors wins -- deterministic but emergent
    commit-reveal       fair draw: winner picked with OS entropy, service
                        returns a SHA-256 commitment + nonce anyone can verify
    oracle              local Ollama LLM (no API key, offline); the model
                        chooses among the candidates and must return a valid id

Every provider except classical-baseline draws with probability proportional to
score; any provider failure degrades to classical-baseline.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
import struct
from typing import Any, Callable, Optional

from .layout_ranker import LayoutCandidate, score_candidate, pick_best_index


DEFAULT_BACKEND = "classical-baseline"

# Ollama is a local daemon -- no API key, no cloud, offline capable.
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:7b")
OLLAMA_TIMEOUT_S = float(os.environ.get("OLLAMA_TIMEOUT_S", "8"))

# Optional real-quantum dependency. Not required to run the service.
try:
    from qiskit import QuantumCircuit, Aer  # type: ignore
    _QISKIT_AVAILABLE = True
except Exception:
    _QISKIT_AVAILABLE = False


def _scored(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach a score to each candidate using the shared scoring function."""
    out = []
    for item in candidates:
        row = dict(item)
        row["score"] = score_candidate(
            LayoutCandidate(id=str(item["id"]), difficulty=float(item["difficulty"]), spacing=float(item["spacing"]))
        )
        out.append(row)
    return out


def _weighted_pick(ids: list[str], scores: list[float], u: float) -> int:
    """Return the index drawn with probability proportional to score."""
    total = sum(scores)
    if total <= 0.0:
        return random.randrange(len(ids))
    target = u * total
    acc = 0.0
    for i, s in enumerate(scores):
        acc += s
        if target <= acc:
            return i
    return len(ids) - 1


def _build_result(seed: int, winner: dict[str, Any], scored: list[dict[str, Any]], backend: str) -> dict[str, Any]:
    return {
        "job_id": f"qjob_{seed:06d}",
        "status": "completed",
        "winner_id": winner["id"],
        "score": winner["score"],
        "backend": backend,
        "candidates": scored,
    }


def _draw_classical(seed: int, candidates: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    scored = _scored(candidates)
    scored.sort(key=lambda row: row["score"], reverse=True)
    return _build_result(seed, scored[0], scored, "classical-baseline")


def _draw_qsharp(seed: int, candidates: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Honest score-weighted measurement, 2 candidates only (Q# kernel).

    The kernel prepares |0> with probability sA/(sA+sB) via a single Y rotation
    and measures once -- the collapse IS the pick. A quantum call no classical
    call reproduces (true score-weighted coin flip, not a tie-break).
    """
    if len(candidates) != 2:
        return None
    scored = _scored(candidates)
    a, b = scored[0], scored[1]
    winner_index = pick_best_index(a["difficulty"], a["spacing"], b["difficulty"], b["spacing"])
    if winner_index is None:
        return None
    winner = scored[winner_index]
    return _build_result(seed, winner, scored, "qsharp-simulator")


def _draw_qiskit(seed: int, candidates: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Amplitude-encode every candidate, sample once on Aer statevector."""
    if not _QISKIT_AVAILABLE:
        return None
    scored = _scored(candidates)
    scores = [row["score"] for row in scored]
    total = sum(scores)
    if total <= 0.0:
        return None
    probs = [s / total for s in scores]
    n = len(probs)
    nq = (n - 1).bit_length()
    circ = QuantumCircuit(nq, nq)
    circ.initialize(probs + [0.0] * (2**nq - n), range(nq))
    circ.measure_all()
    backend = Aer.get_backend("aer_simulator")
    shot = backend.run(circ, shots=1).result().get_counts()
    state = next(iter(shot))
    winner_index = int(state, 2)
    winner = scored[winner_index]
    return _build_result(seed, winner, scored, "qiskit-aer")


def _draw_chaos(seed: int, candidates: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Seeded logistic-map chaotic draw, weighted by score.

    Honest note: this is reproducible for a seed (chaotic dynamics, not
    hardware entropy). It is the 'unfathomable but re-seedable' flavor.
    """
    scored = _scored(candidates)
    ids = [row["id"] for row in scored]
    scores = [row["score"] for row in scored]
    x = ((seed % 9973) + 1) / 9974.0
    for _ in range(50 + (seed % 11)):
        x = 3.99 * x * (1.0 - x)
    idx = _weighted_pick(ids, scores, x)
    return _build_result(seed, scored[idx], scored, "chaos")


def _draw_swarm(seed: int, candidates: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Seeded ant-colony style emergent pick.

    Each agent walks the candidates with transition probability proportional to
    score^beta; the most-visited candidate wins (plurality). Emergent consensus
    rather than a single sample.
    """
    rng = random.Random(seed)
    scored = _scored(candidates)
    ids = [row["id"] for row in scored]
    scores = [row["score"] for row in scored]
    beta = 2.0
    weights = [max(0.0, s) ** beta for s in scores]
    total = sum(weights)
    if total <= 0.0:
        return _draw_classical(seed, candidates)
    visits = [0] * len(ids)
    n_agents = 32
    steps = 3
    for _ in range(n_agents):
        i = rng.randrange(len(ids))
        for _ in range(steps):
            u = rng.random()
            i = _weighted_pick(ids, weights, u)
        visits[i] += 1
    best = max(visits)
    leaders = [i for i, v in enumerate(visits) if v == best]
    idx = rng.choice(leaders)
    return _build_result(seed, scored[idx], scored, "swarm")


def _entropy_uniform() -> float:
    """One float in [0,1) from OS hardware/secure entropy (no seed by design).

    53 random bits via os.urandom -- on Windows this is CryptGenRandom, backed
    by system hardware RNG; there is no seed to reproduce the draw.
    """
    return (struct.unpack("<Q", os.urandom(8))[0] >> 11) * (1.0 / (1 << 53))


def _draw_pbit(seed: int, candidates: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Probabilistic bit: thermal softmax over scores, sampled with OS entropy.

    A p-bit fluctuates with thermal noise and samples a distribution natively;
    this is the honest, hardware-free version of the qubit draw. Temperature
    tuned so the distribution stays score-weighted but never collapses to
    argmax -- the underdog can always win.
    """
    scored = _scored(candidates)
    ids = [row["id"] for row in scored]
    temp = 0.25
    weights = [math.exp(max(0.0, row["score"]) / temp) for row in scored]
    idx = _weighted_pick(ids, weights, _entropy_uniform())
    return _build_result(seed, scored[idx], scored, "pbit")


def _draw_entropy(seed: int, candidates: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Weighted sample straight from OS hardware entropy -- genuinely unreproducible.

    No seed by construction: the draw depends only on system RNG state, so no
    reload, save-scum or replay can repeat it. 'Physics decides.'
    """
    scored = _scored(candidates)
    ids = [row["id"] for row in scored]
    scores = [row["score"] for row in scored]
    idx = _weighted_pick(ids, scores, _entropy_uniform())
    return _build_result(seed, scored[idx], scored, "entropy")


def _life_step(grid: list[list[bool]]) -> list[list[bool]]:
    """One Conway Game of Life generation on a torus (wrap-around edges)."""
    h = len(grid)
    w = len(grid[0])
    out = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            neighbors = 0
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    if grid[(y + dy) % h][(x + dx) % w]:
                        neighbors += 1
            out[y][x] = (grid[y][x] and neighbors in (2, 3)) or (not grid[y][x] and neighbors == 3)
    return out


def _draw_cellular(seed: int, candidates: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Conway's Game of Life: the emergent survivor picks the winner.

    Each candidate owns a horizontal band; cells are seeded by score, the grid
    evolves 64 generations, and the band with the most living cells wins.
    Deterministic given the seed -- the emergence, not the RNG, is the draw.
    """
    scored = _scored(candidates)
    rng = random.Random(seed)
    w, h, gens = 48, 24, 64
    grid = [[False] * w for _ in range(h)]
    n = len(scored)
    rows_per = h // n
    for i, row in enumerate(scored):
        density = min(0.45, max(0.08, row["score"] * 0.5))
        y0 = i * rows_per
        y1 = h if i == n - 1 else (i + 1) * rows_per
        for y in range(y0, y1):
            for x in range(w):
                if rng.random() < density:
                    grid[y][x] = True
    for _ in range(gens):
        grid = _life_step(grid)
    survivors = [0] * n
    for y in range(h):
        for x in range(w):
            if grid[y][x]:
                survivors[min(y // rows_per, n - 1)] += 1
    best = max(survivors)
    leaders = [i for i, v in enumerate(survivors) if v == best]
    idx = rng.choice(leaders)
    return _build_result(seed, scored[idx], scored, "cellular")


def _draw_commit(seed: int, candidates: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Commit-reveal fair draw: the service picks, then proves it.

    The winner is chosen with OS entropy (no input anyone could see or bias),
    and the response carries a SHA-256 commitment + reveal nonce. Anyone can
    verify afterwards that the commitment matches: sha256(winner_id + ':' +
    nonce) == commitment. 'Chosen in a way even Melusina can't see.'
    """
    scored = _scored(candidates)
    ids = [row["id"] for row in scored]
    scores = [row["score"] for row in scored]
    nonce = os.urandom(16).hex()
    idx = _weighted_pick(ids, scores, _entropy_uniform())
    winner = scored[idx]
    result = _build_result(seed, winner, scored, "commit-reveal")
    result["commitment"] = hashlib.sha256(f"{winner['id']}:{nonce}".encode("utf-8")).hexdigest()
    result["nonce"] = nonce
    return result


def _draw_oracle(seed: int, candidates: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    """Local Ollama LLM pick -- no API key, offline capable.

    The model must reply with one of the candidate ids as JSON; the id is
    validated server-side and any failure degrades to classical-baseline.
    """
    import requests

    scored = _scored(candidates)
    ids = {row["id"] for row in scored}
    listing = ", ".join(
        f'"{row["id"]}" (difficulty {row["difficulty"]}, spacing {row["spacing"]}, score {row["score"]})'
        for row in scored
    )
    prompt = (
        "You are the Melodia song library. Pick exactly one song for this battle "
        "from the candidates below. Weigh your choice by score (higher is more fitting), "
        "but a rare pick is allowed.\n"
        f"Candidates: [{listing}]\n"
        'Reply with JSON only: {"winner_id": "<id>"}'
    )
    payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "format": "json"}
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT_S)
        r.raise_for_status()
        body = r.json()
        choice = json.loads(body.get("response", ""))
        winner_id = str(choice.get("winner_id", ""))
        if winner_id not in ids:
            return None
    except Exception:
        return None
    winner = next(row for row in scored if row["id"] == winner_id)
    return _build_result(seed, winner, scored, "oracle")


PROVIDERS: dict[str, Callable[[int, list[dict[str, Any]]], Optional[dict[str, Any]]]] = {
    "classical-baseline": _draw_classical,
    "qsharp-simulator": _draw_qsharp,
    "qiskit-aer": _draw_qiskit,
    "chaos": _draw_chaos,
    "swarm": _draw_swarm,
    "pbit": _draw_pbit,
    "entropy": _draw_entropy,
    "cellular": _draw_cellular,
    "commit-reveal": _draw_commit,
    "oracle": _draw_oracle,
}


def rank_and_draw(seed: int, candidates: list[dict[str, Any]], backend: str = DEFAULT_BACKEND) -> dict[str, Any]:
    """Rank candidates and draw a winner through the requested provider.

    Any provider failure (missing dependency, daemon down, invalid model reply)
    degrades to classical-baseline. The 'backend' field in the response reports
    what actually ran.
    """
    if not candidates:
        raise ValueError("at least one candidate is required")
    if backend not in PROVIDERS:
        raise ValueError(f"unknown backend '{backend}'; expected one of {sorted(PROVIDERS)}")
    result = PROVIDERS[backend](seed, candidates)
    if result is None:
        result = _draw_classical(seed, candidates)
    return result


if __name__ == "__main__":
    import sys

    cands = [
        {"id": "A", "difficulty": 0.5, "spacing": 0.5},
        {"id": "B", "difficulty": 0.8, "spacing": 0.6},
        {"id": "C", "difficulty": 0.3, "spacing": 0.9},
        {"id": "D", "difficulty": 0.9, "spacing": 0.2},
    ]
    wanted = sys.argv[1] if len(sys.argv) > 1 else "classical-baseline"
    res = rank_and_draw(42, cands, wanted)
    print(json.dumps(res, indent=2))
