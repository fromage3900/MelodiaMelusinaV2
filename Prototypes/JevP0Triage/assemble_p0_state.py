"""Assemble live P0 state from repo signals. Read-only. Never writes."""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
from datetime import datetime, timezone

from jev_p0_triage import P0State


def _echo_gates() -> float | None:
    try:
        out = subprocess.run(
            ["python", "-B", "Tools/echo_run.py", "status"],
            capture_output=True, text=True, timeout=60,
        ).stdout
    except Exception:
        return None
    oldest = None
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] == "[PASS]":
            try:
                dt = datetime.strptime(parts[2], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                age = (datetime.now(timezone.utc) - dt).days
                oldest = age if oldest is None else max(oldest, age)
            except ValueError:
                continue
    return float(oldest) if oldest is not None else None


def _git_dirty() -> int | None:
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, timeout=60,
        ).stdout
        return len([l for l in out.splitlines() if l.strip()])
    except Exception:
        return None


def _port_open(port: int = 9316) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=3):
            return True
    except OSError:
        return False


def assemble(time_budget_min: float = 60.0, failures: str = "none") -> P0State:
    disk = shutil.disk_usage("C:/")
    return P0State(
        gate_staleness_days=_echo_gates(),
        dirty_count=_git_dirty(),
        disk_gb_free_c=round(disk.free / 1e9, 1),
        editor_up=_port_open(),  # port up implies the editor/Monolith lane
        port_9316_open=_port_open(),
        last_failures=failures,
        time_budget_min=time_budget_min,
        provenance="live-read",
    )


if __name__ == "__main__":
    import sys

    from jev_p0_triage import hud, triage

    budget = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
    fails = sys.argv[2] if len(sys.argv) > 2 else "none"
    state = assemble(time_budget_min=budget, failures=fails)
    print(state)
    print(hud(triage(state, live_enabled=True)))
