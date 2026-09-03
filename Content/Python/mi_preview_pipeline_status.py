"""Pipeline status writer for low-fatigue MI loop publish flow."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import mi_preview_dirty as dirty_mod
import mi_preview_studio as studio

STATUS_PATH = studio.PIPELINE_STATUS_JSON


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_status() -> dict[str, Any]:
    if not STATUS_PATH.is_file():
        return {}
    try:
        return json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_status(**fields: Any) -> dict[str, Any]:
    status = _read_status()
    status.update(fields)
    status["last_run"] = _now_iso()
    if "next_dirty_ids" not in status:
        try:
            queue = dirty_mod.build_dirty_queue()
            status["next_dirty_ids"] = [e["id"] for e in queue[:10]]
        except Exception:
            status["next_dirty_ids"] = []
    status["wix_republish_required"] = True
    STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATUS_PATH.write_text(json.dumps(status, indent=2), encoding="utf-8")
    return status


def append_failure(message: str) -> None:
    status = _read_status()
    failures = list(status.get("failures") or [])
    failures.append({"at": _now_iso(), "message": message})
    status["failures"] = failures[-20:]
    write_status(**status)
