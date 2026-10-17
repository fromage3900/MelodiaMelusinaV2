"""Host driver for the P0 hybrid loop PIE proof. Does not launch the editor.

Walks with movement input (no teleport), then lock, three swings, phrase, four lanes, exit.
Screenshots land in Saved/Audit/P0HybridLoop_20261017/.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

PROJECT = Path(r"C:/EnvironmentPortfolio/BS_GodFile")
TOOLS = PROJECT / "Tools"
OUT = PROJECT / "Saved" / "Audit" / "P0HybridLoop_20261017"
LEVEL = "/Game/EnvSandbox/Environments/WP/L_WP_CosmicOrrery"
sys.path.insert(0, str(TOOLS))
from mcp_client import monolith_call  # noqa: E402


def editor(action, params=None, timeout=180):
    return monolith_call("editor_query", {"action": action, "params": params or {}}, timeout=timeout)


def run_op(op, shot="", pause=0.35):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "command.json").write_text(json.dumps({"op": op, "shot": shot}), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(TOOLS / "mcp_run_python.py"), "--file", str(TOOLS / "p0_hybrid_loop_payload.py"),
         "--name", "p0_" + op, "--timeout", "90"],
        cwd=str(PROJECT), capture_output=True, text=True)
    text = (proc.stdout or "") + (proc.stderr or "")
    print(text, flush=True)
    time.sleep(pause)
    return text


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("[p0] load", LEVEL, flush=True)
    print(editor("load_level", {"path": LEVEL}, timeout=240), flush=True)
    time.sleep(2)
    print("[p0] start_pie", flush=True)
    print(editor("start_pie", {}), flush=True)
    deadline = time.time() + 90
    world = None
    while time.time() < deadline:
        text = run_op("status", pause=2.0)
        if "world=NONE" not in text and "pawn=" in text and "pawn=NONE" not in text:
            world = text
            break
    if not world:
        print("[p0] PIE pawn did not appear", flush=True)
        return 2
    run_op("shot", "01_possessed", pause=0.6)
    for i in range(50):
        text = run_op("step", "02_walk_%02d" % i if i in (0, 24, 49) else "", pause=0.15)
        if "dist=" in text:
            try:
                dist = float(text.split("dist=")[1].split()[0])
            except ValueError:
                dist = 99999
            if 0 < dist < 320:
                break
    run_op("shot", "03_in_range", pause=0.4)
    run_op("lock", "04_lock", pause=1.2)
    for n in range(1, 4):
        run_op("swing", "05_swing_%d" % n, pause=1.3)
    run_op("shot", "06_after_swings", pause=0.4)
    run_op("phrase", "07_sequence", pause=0.8)
    run_op("lanes", "08_lanes", pause=0.8)
    run_op("exit", "09_exit", pause=0.8)
    for i in range(8):
        run_op("step", "10_walkaway" if i == 7 else "", pause=0.15)
    print(editor("search_logs", {"pattern": "MELODIA_WAVEHARP_SCYTHE_SWING|MELODIA_HYBRID_RESONANCE|MELODIA_WAVEHARP_LOCK_STEP", "limit": 40}), flush=True)
    print("[p0] frames in", OUT, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
