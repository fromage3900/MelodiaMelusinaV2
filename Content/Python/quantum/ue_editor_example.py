"""Unreal Editor example: request quantum ranking and apply result to a Blueprint actor.

Usage inside UE Editor Python:

from BS_GodFile.Content.Python.quantum import ue_editor_example as qx

# Start a request and watch in background; look for an actor named 'QuantumReceiver'
payload = {"job_type":"rank_layouts","seed":42,"candidates":[{"id":"A","difficulty":0.5},{"id":"B","difficulty":0.6}]}
qx.start_request_and_watch("http://127.0.0.1:8008/rank_layouts", payload,
                           target_actor_name="QuantumReceiver",
                           function_name="ApplyQuantumResult")

Requirements for Blueprint actor:
- An actor named `QuantumReceiver` placed in the level, or adjust `target_actor_name`.
- The actor must implement a Blueprint-callable function `ApplyQuantumResult(FString winnerId, FName jobId)`
  (or the function name configured via `function_name`).

The watcher runs in a background thread and does not block the editor.
"""
from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Optional

try:
    import unreal  # type: ignore
except Exception:
    unreal = None

from .ue_apply_result import fetch_and_persist, read_saved_result


def _find_actor_by_name(name: str):
    if unreal is None:
        return None
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for a in actors:
        try:
            if a.get_name() == name or a.get_actor_label() == name:
                return a
        except Exception:
            continue
    return None


def _call_actor_function(actor, function_name: str, *args):
    try:
        fn = getattr(actor, function_name)
    except Exception:
        try:
            # Blueprint callable functions are sometimes exposed with exact name
            return None
        except Exception:
            return None
    try:
        return fn(*args)
    except Exception as e:
        if unreal is not None:
            unreal.log_warning(f"[Quantum] Failed calling {function_name} on {actor.get_name()}: {e}")
        else:
            print(f"[Quantum] Failed calling {function_name} on actor: {e}")
        return None


def _watch_job_and_apply(job_id: str, target_actor_name: Optional[str], function_name: str, poll_interval: float):
    if unreal is not None:
        unreal.log(f"[Quantum] Watching for job {job_id}")
    else:
        print(f"[Quantum] Watching for job {job_id}")
    while True:
        res = read_saved_result(job_id)
        if res:
            winner = res.get("winner_id") or res.get("winner") or res.get("selected")
            if target_actor_name and unreal is not None:
                actor = _find_actor_by_name(target_actor_name)
                if actor is not None:
                    _call_actor_function(actor, function_name, winner, job_id)
                    unreal.log(f"[Quantum] Applied job {job_id} winner {winner} to {actor.get_name()}")
                else:
                    unreal.log_warning(f"[Quantum] Target actor '{target_actor_name}' not found to apply result")
            else:
                # no actor configured; just log
                if unreal is not None:
                    unreal.log(f"[Quantum] Job {job_id} result: {winner}")
                else:
                    print(f"[Quantum] Job {job_id} result: {winner}")
            break
        time.sleep(poll_interval)


def start_request_and_watch(service_url: str, payload: dict[str, Any], target_actor_name: Optional[str] = None,
                            function_name: str = "ApplyQuantumResult", poll_interval: float = 0.5) -> str:
    """Post the payload to the service, persist the result, and spawn a background watcher.

    Returns the job_id used for the result file.
    """
    data = fetch_and_persist(service_url, payload)
    job_id = data.get("job_id") or f"qjob_{payload.get('seed', 0)}"
    t = threading.Thread(target=_watch_job_and_apply, args=(job_id, target_actor_name, function_name, poll_interval), daemon=True)
    t.start()
    return job_id


def register_editor_utility():
    """Helper to register the Editor menu from Python inside the Editor.

    In the UE Python console run::

        from BS_GodFile.Content.Python.quantum.ue_editor_widget import register
        register()

    Or call this function which provides the same convenience.
    """
    try:
        from BS_GodFile.Content.Python.quantum.ue_editor_widget import register
        register()
        return True
    except Exception:
        logger.exception("Failed to register Editor Utility; ensure Unreal Python API is available.")
        return False


if __name__ == "__main__":
    # Basic smoke test when run standalone (will use cwd Saved path)
    payload = {"job_type": "rank_layouts", "seed": 99, "candidates": [{"id": "A", "difficulty": 0.1}, {"id": "B", "difficulty": 0.9}]}
    print("Starting request and watcher (standalone). Ensure service is running on 127.0.0.1:8008")
    jid = start_request_and_watch("http://127.0.0.1:8008/rank_layouts", payload, target_actor_name=None)
    print("Started job", jid)
