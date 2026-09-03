"""Unified audit/report system — every GMM action writes structured JSON reports.

Reports land in Saved/Audit/gmm_*.json with standard envelope fields:
    timestamp, action, status, data, errors, warnings
"""
from __future__ import annotations

import dataclasses
import datetime
import json
import os
import pathlib
import traceback
from typing import Any

_PROJECT_ROOT: pathlib.Path | None = None


def _project_root() -> pathlib.Path:
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        _PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[3]
    return _PROJECT_ROOT


def audit_dir() -> pathlib.Path:
    """Return Saved/Audit/ directory (created if missing)."""
    d = _project_root() / "Saved" / "Audit"
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_audit(name: str, data: dict) -> str:
    """Write a JSON audit report to Saved/Audit/{name}.

    Args:
        name: Filename (e.g. "gmm_melusina_rig.json")
        data: Serializable dict.

    Returns:
        Absolute path to the written file.
    """
    path = audit_dir() / name
    with open(str(path), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    return str(path.resolve())


@dataclasses.dataclass
class GmmAudit:
    """Builder for structured audit reports.

    Usage:
        audit = GmmAudit(action="melusina.rig_assess")
        audit.ok(bone_count=72, material_slots=6)
        audit.save("gmm_melusina_rig.json")
    """
    action: str
    timestamp: str = dataclasses.field(default_factory=lambda: str(datetime.datetime.now()))
    status: str = "pending"
    data: dict = dataclasses.field(default_factory=dict)
    warnings: list[str] = dataclasses.field(default_factory=list)
    errors: list[str] = dataclasses.field(default_factory=list)

    def ok(self, **fields) -> GmmAudit:
        self.status = "ok"
        self.data.update(fields)
        return self

    def warn(self, message: str) -> GmmAudit:
        self.warnings.append(message)
        return self

    def fail(self, error: str) -> GmmAudit:
        self.status = "error"
        self.errors.append(error)
        return self

    def fail_from_exception(self, exc: Exception) -> GmmAudit:
        self.status = "error"
        self.errors.append(f"{exc}")
        self.data["traceback"] = traceback.format_exc()
        return self

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "timestamp": self.timestamp,
            "status": self.status,
            "data": self.data,
            "warnings": self.warnings,
            "errors": self.errors,
        }

    def save(self, name: str | None = None) -> str:
        if name is None:
            safe = self.action.replace(".", "_").replace("/", "_")
            name = f"gmm_{safe}.json"
        return write_audit(name, self.to_dict())

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)
