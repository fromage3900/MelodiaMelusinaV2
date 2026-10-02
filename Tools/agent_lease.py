#!/usr/bin/env python3
"""Single-writer editor lease for Melodia agent orchestration.

H1 contract:
- one active holder may mutate an editor surface at a time;
- acquisition fails closed while any deploy/*_LOOP_STOP marker exists;
- acquisition fails closed while the current editor log reports MODAL_OPEN
  without a later MODAL_CLOSED marker;
- expired leases may be replaced;
- writes are atomic (temp file + os.replace).

The lease is coordination state, not evidence and not authority to mutate Git/P4.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
LEASE_PATH = PROJECT_ROOT / "Saved" / "Agents" / "editor.lease"
DEFAULT_TTL_MINUTES = 30


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _read_tail(path: Path, limit: int = 200_000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    with path.open("rb") as fh:
        try:
            fh.seek(-limit, os.SEEK_END)
        except OSError:
            fh.seek(0)
        return fh.read().decode("utf-8", errors="replace")


def blocking_stop_files(project_root: Path = PROJECT_ROOT) -> list[str]:
    deploy = project_root / "deploy"
    if not deploy.exists():
        return []
    return sorted(
        str(p.relative_to(project_root)).replace("\\", "/")
        for p in deploy.glob("*_LOOP_STOP")
        if p.is_file()
    )


def modal_is_open(project_root: Path = PROJECT_ROOT) -> bool:
    log = project_root / "Saved" / "Logs" / "BS_GodFile.log"
    tail = _read_tail(log)
    if not tail:
        return False
    opened = tail.rfind("MODAL_OPEN")
    closed = tail.rfind("MODAL_CLOSED")
    return opened >= 0 and opened > closed


def read_lease(
    lease_path: Path = LEASE_PATH,
    *,
    now: datetime | None = None,
) -> dict[str, Any] | None:
    if not lease_path.exists():
        return None
    try:
        data = json.loads(lease_path.read_text(encoding="utf-8"))
        expires = _parse_iso(str(data["expires_at"]))
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return {
            "schema": "melodia.editor_lease/v1",
            "status": "invalid",
            "path": str(lease_path),
        }
    now = now or _utcnow()
    result = dict(data)
    result["status"] = "expired" if expires <= now else "active"
    return result


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    finally:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass


def acquire_lease(
    holder: str,
    session: str,
    surface: str,
    *,
    ttl_minutes: int = DEFAULT_TTL_MINUTES,
    project_root: Path = PROJECT_ROOT,
    lease_path: Path = LEASE_PATH,
    now: datetime | None = None,
) -> dict[str, Any]:
    holder = holder.strip()
    session = session.strip()
    surface = surface.strip()
    if not holder or not session or not surface:
        return {"ok": False, "reason": "holder, session and surface are required"}
    if ttl_minutes < 1:
        return {"ok": False, "reason": "ttl_minutes must be >= 1"}

    stops = blocking_stop_files(project_root)
    if stops:
        return {"ok": False, "reason": "loop stop marker present", "stop_files": stops}
    if modal_is_open(project_root):
        return {"ok": False, "reason": "MODAL_OPEN is active in Saved/Logs/BS_GodFile.log"}

    now = now or _utcnow()
    current = read_lease(lease_path, now=now)
    if current and current.get("status") == "invalid":
        return {"ok": False, "reason": "lease file is invalid; owner inspection required"}
    if current and current.get("status") == "active":
        same_owner = (
            current.get("holder") == holder
            and current.get("session") == session
            and current.get("surface") == surface
        )
        if not same_owner:
            return {
                "ok": False,
                "reason": "editor lease already held",
                "lease": current,
            }

    payload = {
        "schema": "melodia.editor_lease/v1",
        "holder": holder,
        "session": session,
        "surface": surface,
        "acquired_at": _iso(now),
        "expires_at": _iso(now + timedelta(minutes=ttl_minutes)),
    }
    _atomic_write_json(lease_path, payload)
    return {"ok": True, "lease": {**payload, "status": "active"}}


def release_lease(
    holder: str,
    *,
    session: str | None = None,
    lease_path: Path = LEASE_PATH,
    now: datetime | None = None,
) -> dict[str, Any]:
    current = read_lease(lease_path, now=now)
    if current is None:
        return {"ok": True, "released": False, "reason": "no lease exists"}
    if current.get("status") == "invalid":
        return {"ok": False, "reason": "lease file is invalid; owner inspection required"}
    if current.get("status") == "active":
        if current.get("holder") != holder:
            return {"ok": False, "reason": "holder mismatch", "lease": current}
        if session is not None and current.get("session") != session:
            return {"ok": False, "reason": "session mismatch", "lease": current}
    try:
        lease_path.unlink()
    except FileNotFoundError:
        pass
    return {"ok": True, "released": True}


def _print(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_acquire = sub.add_parser("acquire")
    p_acquire.add_argument("--holder", required=True)
    p_acquire.add_argument("--session", required=True)
    p_acquire.add_argument("--surface", required=True)
    p_acquire.add_argument("--ttl-minutes", type=int, default=DEFAULT_TTL_MINUTES)

    p_release = sub.add_parser("release")
    p_release.add_argument("--holder", required=True)
    p_release.add_argument("--session")

    sub.add_parser("status")

    args = ap.parse_args()
    if args.cmd == "acquire":
        result = acquire_lease(
            args.holder,
            args.session,
            args.surface,
            ttl_minutes=args.ttl_minutes,
        )
        _print(result)
        return 0 if result.get("ok") else 2
    if args.cmd == "release":
        result = release_lease(args.holder, session=args.session)
        _print(result)
        return 0 if result.get("ok") else 2

    current = read_lease()
    _print({
        "ok": True,
        "lease": current,
        "stop_files": blocking_stop_files(),
        "modal_open": modal_is_open(),
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
