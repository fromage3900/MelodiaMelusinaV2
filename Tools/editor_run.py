#!/usr/bin/env python3
"""editor_run.py - run a Content/Python editor script through the live Monolith editor.

Pipeline driver: waits for the editor MCP endpoint, then calls
`editor_query` action `run_python` (execute_file mode, unattended).

Usage:
    python Tools/editor_run.py <relative-or-absolute script path> [-- arg1 arg2 ...]

Example:
    python Tools/editor_run.py Content/Python/sweep_pbr_state.py
    python Tools/editor_run.py Content/Python/fix_pbr_routing.py -- --apply
"""
import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Tools"))
import mcp_client  # noqa: E402

MONOLITH_URL = os.environ.get("MONOLITH_URL", "http://127.0.0.1:9316/mcp")
WAIT_SECONDS = int(os.environ.get("EDITOR_WAIT", "1800"))


def wait_for_editor(timeout: int) -> bool:
    host = "127.0.0.1"
    port = 9316
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=3):
                return True
        except OSError:
            time.sleep(10)
    return False


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: editor_run.py <script.py> [-- args...]")
        return 2
    script = sys.argv[1]
    args = []
    if "--" in sys.argv:
        args = sys.argv[sys.argv.index("--") + 1:]
    if not os.path.isabs(script):
        script = str(ROOT / script)
    if not Path(script).exists():
        print(f"ERROR: script not found: {script}")
        return 2
    command = script + (" " + " ".join(args) if args else "")
    print(f"waiting for editor MCP at {MONOLITH_URL} ...", flush=True)
    if not wait_for_editor(WAIT_SECONDS):
        print("ERROR: editor MCP endpoint never came up")
        return 1
    print(f"calling editor_query run_python: {command}", flush=True)
    resp = mcp_client.monolith(
        "editor_query",
        {"action": "run_python", "command": command, "mode": "execute_file", "unattended": True},
        timeout=3600,
    )
    if resp.startswith("ERROR"):
        print(resp)
        return 1
    print(resp, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
