# Quantum Gameplay Experiment Proto — UE Request Contract

**Date:** 2026-08-06
**Status:** Draft implementation slice

## Request schema

```json
{
  "job_type": "rank_layouts",
  "seed": 12345,
  "backend": "classical-baseline",
  "candidates": [
    {"id": "A", "difficulty": 0.7, "spacing": 0.4},
    {"id": "B", "difficulty": 0.8, "spacing": 0.6}
  ]
}
```

`backend` is optional; the server defaults to `classical-baseline`. The
response `backend` field reports what actually ran — a provider failure
never fails the request, it degrades to `classical-baseline`.

## Draw providers (2026-08-09)

All providers share the same scoring function and this contract; they differ
only in HOW the winner is drawn from the candidate weights. Every provider
except `classical-baseline` draws with probability proportional to score.

| backend | What it is | Honest notes |
|---------|-----------|--------------|
| `classical-baseline` | argmax | Deterministic best pick; always available |
| `qsharp-simulator` | Honest 2-candidate amplitude measurement via `qsharp_layout_ranker.qs` | Single Y-rotation + one measurement; the collapse IS the pick. 2 candidates only; N>2 falls back |
| `qiskit-aer` | Amplitude-encode all candidates, sample once on Aer | Needs `qiskit-aer` (optional dep); degrades if absent |
| `chaos` | Seeded logistic-map chaotic weighted draw | Reproducible for a seed — chaotic, not hardware entropy |
| `swarm` | Seeded ant-colony emergent pick | 32 agents walk weighted by score^2, plurality wins |
| `pbit` | Probabilistic bit: thermal softmax over scores, OS-entropy sample | No seed; hardware-fluctuation flavor without the quantum |
| `entropy` | Weighted sample straight from OS hardware entropy | Genuinely unreproducible — no seed by construction |
| `cellular` | Conway's Game of Life: each candidate owns a grid band, 64 generations, most survivors wins | Deterministic per seed; the emergence is the draw |
| `commit-reveal` | Fair draw + SHA-256 commitment/nonce | Verify: `sha256(winner_id + ":" + nonce) == commitment` |
| `oracle` | Local Ollama LLM chooses | No API key; `http://127.0.0.1:11434/api/generate`, model `qwen2.5-coder:7b` (env: `OLLAMA_MODEL`, `OLLAMA_URL`, `OLLAMA_TIMEOUT_S`). Reply must be JSON with a valid `winner_id` or it degrades |

`commit-reveal` adds two additive fields to the response (`commitment`,
`nonce`); every other provider keeps the exact response shape. Analog/optical
hardware is not represented — it cannot run without real photonic hardware,
and a Python simulation would just be a lie wearing a lab coat.

## Response schema

```json
{
  "job_id": "qjob_001",
  "status": "completed",
  "winner_id": "B",
  "score": 0.91,
  "backend": "qsharp-simulator"
}
```

## Implementation order

1. Keep the Python baseline working.
2. Replace the scoring core with a Q#-driven backend.
3. Preserve the JSON contract so UE does not change twice.
4. Add a tiny Blueprint/C++ caller after the service is stable.

## Rhythm gameplay use

For Cadence Strike or similar rhythm skills, use the quantum result to choose the authored note pattern, lane density, accent placement, or BPM band before the session starts.

Keep hit detection, timing windows, combo tracking, and result grading in the normal UE rhythm path.
