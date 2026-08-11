"""Small FastAPI wrapper exposing the rank_layouts contract.

Run with:
    uvicorn quantum.service:app --reload --port 8008

Backends: classical-baseline (default), qsharp-simulator, qiskit-aer,
chaos, swarm, pbit, entropy, cellular, commit-reveal, oracle (local
Ollama -- no API key). The response 'backend' field reports what actually
ran; any provider failure degrades to classical-baseline.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

from .draw_providers import PROVIDERS, DEFAULT_BACKEND, rank_and_draw

app = FastAPI(title="Melodia Quantum Prototype")


class CandidateModel(BaseModel):
    id: str
    difficulty: float
    spacing: float


class RankRequest(BaseModel):
    job_type: str
    seed: int
    candidates: List[CandidateModel]
    backend: str = DEFAULT_BACKEND


@app.post("/rank_layouts")
async def rank_layouts_endpoint(req: RankRequest):
    if req.job_type != "rank_layouts":
        raise HTTPException(status_code=400, detail="unsupported job_type")
    if req.backend not in PROVIDERS:
        raise HTTPException(status_code=400, detail=f"unknown backend; expected one of {sorted(PROVIDERS)}")
    try:
        return rank_and_draw(req.seed, [c.dict() for c in req.candidates], req.backend)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
