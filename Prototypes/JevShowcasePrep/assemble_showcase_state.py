"""Assemble showcase-prep state from receipts and machine signals. Read-only.

Never writes assets, maps, receipts, or the gate ledger. Missing receipts
and failed reads stay None — this module does not invent zeros.
"""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from jev_showcase_prep import LEVELS, ShowcaseState

_GOD = Path(__file__).resolve().parents[2]
_AUDIT_DIR = _GOD / "Saved" / "Audit" / "showcase_prep_2026-09-21"

_COUNT_FIELDS = (
    "mi_bad_parent_count",
    "engine_default_count",
    "missing_texture_count",
)
_AGE_FIELD = "last_audit_age_h"
_PROOF_FIELD = "render_proof_exists"
_GLOBAL_INTS = ("niagara_default_material_count", "validate_errors")
_GLOBAL_BOOLS = (
    "flipbook_authority_ok",
    "kawaii_tune_ok",
    "hair_tick_flags_ok",
    "blend_verified",
    "shp_bone_match",
)


def _as_int(value: Any) -> Optional[int]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return int(value)


def _as_float(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _as_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    return None


def _repo_root() -> Optional[Path]:
    for candidate in (_GOD, *_GOD.parents):
        if (candidate / ".git").exists():
            return candidate
    return None


def _git_dirty() -> Optional[int]:
    root = _repo_root()
    if root is None:
        return None
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(root),
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return len([line for line in proc.stdout.splitlines() if line.strip()])


def _port_open(port: int = 9316) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=3):
            return True
    except OSError:
        return False


def _disk_gb_free_c() -> Optional[float]:
    try:
        usage = shutil.disk_usage("C:/")
    except OSError:
        return None
    return round(usage.free / 1e9, 1)


def _age_hours(path: Path) -> Optional[float]:
    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except OSError:
        return None
    delta = datetime.now(timezone.utc) - mtime
    return round(delta.total_seconds() / 3600.0, 2)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None


def _blank_acc() -> dict[str, Any]:
    return {
        "mi_bad_parent_count": {},
        "engine_default_count": {},
        "missing_texture_count": {},
        "last_audit_age_h": {},
        "render_proof_exists": {},
        "niagara_default_material_count": None,
        "flipbook_authority_ok": None,
        "validate_errors": None,
        "kawaii_tune_ok": None,
        "hair_tick_flags_ok": None,
        "blend_verified": None,
        "shp_bone_match": None,
        "open_defect": None,
    }


def _assign_count(bucket: dict[str, int], level: str, value: Any) -> None:
    if level not in LEVELS:
        return
    parsed = _as_int(value)
    if parsed is not None:
        bucket[level] = parsed


def _assign_proof(bucket: dict[str, bool], level: str, value: Any) -> None:
    if level not in LEVELS:
        return
    parsed = _as_bool(value)
    if parsed is not None:
        bucket[level] = parsed


def _assign_age(bucket: dict[str, float], level: str, value: Any) -> None:
    if level not in LEVELS:
        return
    parsed = _as_float(value)
    if parsed is not None:
        bucket[level] = parsed


def _take_maps(payload: dict[str, Any], acc: dict[str, Any]) -> None:
    for key in _COUNT_FIELDS:
        raw = payload.get(key)
        if isinstance(raw, dict):
            for path, value in raw.items():
                _assign_count(acc[key], str(path), value)
    ages = payload.get(_AGE_FIELD)
    if isinstance(ages, dict):
        for path, value in ages.items():
            _assign_age(acc[_AGE_FIELD], str(path), value)
    proofs = payload.get(_PROOF_FIELD)
    if isinstance(proofs, dict):
        for path, value in proofs.items():
            _assign_proof(acc[_PROOF_FIELD], str(path), value)


def _take_level_record(level: str, rec: dict[str, Any], acc: dict[str, Any], file_age: Optional[float]) -> None:
    if level not in LEVELS:
        return
    for key in _COUNT_FIELDS:
        if key in rec and not isinstance(rec[key], dict):
            _assign_count(acc[key], level, rec[key])
    if _PROOF_FIELD in rec and not isinstance(rec[_PROOF_FIELD], dict):
        _assign_proof(acc[_PROOF_FIELD], level, rec[_PROOF_FIELD])
    if _AGE_FIELD in rec and not isinstance(rec[_AGE_FIELD], dict):
        _assign_age(acc[_AGE_FIELD], level, rec[_AGE_FIELD])
    elif file_age is not None and level not in acc[_AGE_FIELD]:
        acc[_AGE_FIELD][level] = file_age
    _take_globals(rec, acc)


def _named_from(payload: dict[str, Any]) -> Optional[str]:
    for key in ("open_defect", "defect", "defect_name"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    defects = payload.get("open_defects")
    if isinstance(defects, list):
        for item in defects:
            if isinstance(item, str) and item.strip():
                return item.strip()
            if isinstance(item, dict):
                for sub in ("name", "defect", "open_defect"):
                    named = item.get(sub)
                    if isinstance(named, str) and named.strip():
                        return named.strip()
    return None


def _take_globals(payload: dict[str, Any], acc: dict[str, Any]) -> None:
    for key in _GLOBAL_INTS:
        if key in payload and not isinstance(payload[key], dict):
            parsed = _as_int(payload[key])
            if parsed is not None:
                acc[key] = parsed
    for key in _GLOBAL_BOOLS:
        if key in payload and not isinstance(payload[key], dict):
            parsed = _as_bool(payload[key])
            if parsed is not None:
                acc[key] = parsed
    named = _named_from(payload)
    if named:
        acc["open_defect"] = named


def _iter_level_pairs(payload: Any):
    if isinstance(payload, list):
        for item in payload:
            yield from _iter_level_pairs(item)
        return
    if not isinstance(payload, dict):
        return
    levels = payload.get("levels")
    if isinstance(levels, dict):
        for path, rec in levels.items():
            if isinstance(rec, dict):
                yield str(path), rec
    elif isinstance(levels, list):
        for rec in levels:
            if isinstance(rec, dict):
                path = rec.get("level") or rec.get("level_path") or rec.get("map")
                if isinstance(path, str):
                    yield path, rec
    path = payload.get("level") or payload.get("level_path") or payload.get("map")
    if isinstance(path, str):
        yield path, payload


def _ingest_payload(payload: Any, acc: dict[str, Any], file_age: Optional[float]) -> None:
    if isinstance(payload, list):
        for item in payload:
            _ingest_payload(item, acc, file_age)
        return
    if not isinstance(payload, dict):
        return
    before = {key: set(acc[key]) for key in _COUNT_FIELDS}
    before_proof = set(acc[_PROOF_FIELD])
    _take_maps(payload, acc)
    _take_globals(payload, acc)
    for level, rec in _iter_level_pairs(payload):
        _take_level_record(level, rec, acc, file_age)
    if file_age is None:
        return
    fresh = set()
    for key in _COUNT_FIELDS:
        fresh.update(set(acc[key]) - before[key])
    fresh.update(set(acc[_PROOF_FIELD]) - before_proof)
    for level in fresh:
        acc[_AGE_FIELD].setdefault(level, file_age)


def _read_receipts() -> dict[str, Any]:
    acc = _blank_acc()
    if not _AUDIT_DIR.is_dir():
        return acc
    files = sorted(path for path in _AUDIT_DIR.glob("*.json") if path.is_file())
    for path in files:
        payload = _load_json(path)
        if payload is None:
            continue
        _ingest_payload(payload, acc, _age_hours(path))
    return acc


def _or_none_dict(bucket: dict) -> Optional[dict]:
    return bucket or None


def assemble(time_budget_min: float = 60.0) -> ShowcaseState:
    """Read receipts, git dirt, C: free space, and the editor port. No writes."""
    acc = _read_receipts()
    return ShowcaseState(
        mi_bad_parent_count=_or_none_dict(acc["mi_bad_parent_count"]),
        engine_default_count=_or_none_dict(acc["engine_default_count"]),
        missing_texture_count=_or_none_dict(acc["missing_texture_count"]),
        last_audit_age_h=_or_none_dict(acc["last_audit_age_h"]),
        render_proof_exists=_or_none_dict(acc["render_proof_exists"]),
        niagara_default_material_count=acc["niagara_default_material_count"],
        flipbook_authority_ok=acc["flipbook_authority_ok"],
        validate_errors=acc["validate_errors"],
        kawaii_tune_ok=acc["kawaii_tune_ok"],
        hair_tick_flags_ok=acc["hair_tick_flags_ok"],
        blend_verified=acc["blend_verified"],
        shp_bone_match=acc["shp_bone_match"],
        open_defect=acc["open_defect"],
        editor_up=_port_open(),
        dirty_count=_git_dirty(),
        disk_gb_free_c=_disk_gb_free_c(),
        time_budget_min=time_budget_min,
        provenance="live-read",
    )


if __name__ == "__main__":
    import sys

    from jev_showcase_prep import hud, triage

    budget = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
    state = assemble(time_budget_min=budget)
    print(state)
    print(hud(triage(state, live_enabled=True)))
