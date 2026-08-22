Quantum UE integration helpers

Files
- `ue_apply_result.py`: Editor helper that requests ranking from the local quantum service and persists results to `Saved/QuantumResults/<job_id>.json`.

Usage (Unreal Editor Python)

1. Start the local quantum service (FastAPI) if not running:

```powershell
# from BS_GodFile/Content/Python/quantum
python -m service   # or `uvicorn service:app --host 127.0.0.1 --port 8008`
```

2. In the UE Editor's Python console:

```python
from BS_GodFile.Content.Python.quantum import ue_apply_result as q
payload = {"job_type":"rank_layouts","seed":123,"candidates":[{"id":"A","difficulty":0.5},{"id":"B","difficulty":0.6}]}
q.fetch_and_persist("http://127.0.0.1:8008/rank_layouts", payload)
# or poll a saved job
res = q.read_saved_result('qjob_123')
```

3. Blueprint/Editor stub: read `Saved/QuantumResults/<job_id>.json` and apply `winner_id` into the note highway builder. Ensure this is non-blocking on the game thread.

Notes
- This module works inside UE's embedded Python or standalone; when run inside UE it logs via `unreal.log`.
- The saved JSON contract follows `QUANTUM_GAMEPLAY_EXPERIMENT_PROTO_2026-08-06.md`.

## Resonant World provenance boundary

`resonant_movement_ranker.py` is the source-of-truth selector used by the
offline Resonant World constellation. Version 2 records the classical
objective score, candidate asset provenance, amplitude probabilities for each
two-candidate measurement, the selected backend, and a trace fingerprint that
includes the candidate evidence. This makes a changed atlas produce a changed
replay identity instead of silently reusing an old draw.

The world composer intentionally submits exactly two authored movements to the
Q# kernel. The ranker also supports an experimental N>2 pairwise tournament by
composing that same two-candidate operation in a fixed order; if Q# is missing
or any measurement fails, the complete result reports `classical-baseline`.
Neither path chooses individual voxels, grades input, drives traversal, or
grants rewards.

For the formal contract and research rationale, see
`Docs/RESONANT_WORLD_QUANTUM_PROVENANCE_2026-08-22.md`.
