"""Editor helper: fetch quantum rank result and persist for UE to consume.

Intended to be run inside the Unreal editor Python environment (or standalone).
It writes a small JSON file under Saved/QuantumResults/<job_id>.json which a
Blueprint or editor script can read and apply to the rhythm builder.

Usage (editor Python):
    import quantum.ue_apply_result as q
    q.fetch_and_persist('http://127.0.0.1:8008/rank_layouts', payload)

Where `payload` matches the proto in QUANTUM_GAMEPLAY_EXPERIMENT_PROTO_2026-08-06.md.
"""
from __future__ import annotations

import json
import os
from typing import Any

try:
    import unreal  # type: ignore
except Exception:
    unreal = None

import requests


def _saved_dir() -> str:
    base = None
    if unreal is not None:
        try:
            base = unreal.SystemLibrary.get_project_directory()
        except Exception:
            base = None
    if not base:
        base = os.getcwd()
    out = os.path.join(base, "Saved", "QuantumResults")
    os.makedirs(out, exist_ok=True)
    return out


def fetch_and_persist(service_url: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Fetch from the prototype service and persist result to Saved/QuantumResults.

    Returns the parsed JSON response.
    """
    r = requests.post(service_url, json=payload, timeout=10)
    r.raise_for_status()
    data = r.json()
    job_id = data.get("job_id") or f"qjob_{payload.get('seed', 0)}"
    saved_path = os.path.join(_saved_dir(), f"{job_id}.json")
    with open(saved_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    if unreal is not None:
        unreal.log(f"[Quantum] Saved result to {saved_path}")
    else:
        print(f"[Quantum] Saved result to {saved_path}")
    return data


def read_saved_result(job_id: str) -> dict[str, Any] | None:
    """Read a previously saved result from Saved/QuantumResults.

    Returns parsed JSON or None if not found.
    """
    path = os.path.join(_saved_dir(), f"{job_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    # quick local smoke test
    payload = {
        "job_type": "rank_layouts",
        "seed": 1,
        "candidates": [
            {"id": "A", "difficulty": 0.7, "spacing": 0.4},
            {"id": "B", "difficulty": 0.8, "spacing": 0.6},
        ],
    }
    print(fetch_and_persist("http://127.0.0.1:8008/rank_layouts", payload))
