"""Close the editor, rebuild the editor target, relaunch, wait for Monolith.

Why: the last code edits (cue log lines, the two-way grade pairing) went in through
Live Coding, which patches the running process only. The built DLL has to carry them
before the source can be called verified -- "a file existing is not a file compiling".

Usage: uv run --no-sync python Prototypes/RhythmHighwayCues/editor_rebuild.py
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

MCP = "http://127.0.0.1:9316/mcp"
ROOT = Path(r"C:\EnvironmentPortfolio\BS_GodFile")
DLL = ROOT / "Binaries" / "Win64" / "UnrealEditor-BS_GodFile.dll"
CORE_DLL = ROOT / "Binaries" / "Win64" / "UnrealEditor-MelodiaCore.dll"
BUILD = r"C:\Program Files\Epic Games\UE_5.8\Engine\Build\BatchFiles\Build.bat"
EDITOR = r"C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
PROJECT = r"C:\EnvironmentPortfolio\BS_GodFile\BS_GodFile.uproject"


def call(tool: str, args: dict, timeout: int = 120) -> dict:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": tool, "arguments": args}}).encode()
    req = urllib.request.Request(MCP, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode())
    content = data.get("result", {}).get("content") or [{}]
    text = content[0].get("text", "")
    try:
        return json.loads(text) if text else {}
    except Exception:
        return {"raw": text}


def dll_writable(path: Path) -> bool:
    try:
        with open(path, "r+b"):
            return True
    except OSError:
        return False


def editor_alive() -> bool:
    out = subprocess.run(["tasklist", "/FO", "CSV", "/NH"], capture_output=True, text=True).stdout
    return "UnrealEditor.exe" in out


def main() -> int:
    print("[rebuild] asking the editor to quit (QUIT_EDITOR)")
    try:
        call("editor_query", {"action": "run_console_command", "command": "QUIT_EDITOR"})
    except Exception as exc:
        print("[rebuild] console quit failed:", exc)

    for _ in range(60):
        if not editor_alive() and dll_writable(DLL):
            break
        time.sleep(3)
    else:
        print("[rebuild] editor still up or DLL locked; aborting before the build")
        return 1
    print("[rebuild] editor down, DLL writable")

    print("[rebuild] building BS_GodFileEditor Win64 Development")
    proc = subprocess.run(
        [BUILD, "BS_GodFileEditor", "Win64", "Development", f"-project={PROJECT}", "-waitmutex"],
        capture_output=True, text=True, cwd=str(ROOT))
    tail = "\n".join([ln for ln in (proc.stdout or "").splitlines() if ln.strip()][-12:])
    print(tail)
    print("[rebuild] build exit code:", proc.returncode)
    if proc.returncode != 0:
        print("[rebuild] BUILD FAILED -- not relaunching")
        return 1

    print("[rebuild] core dll:", CORE_DLL.stat().st_mtime, "| editor dll:", DLL.stat().st_mtime)
    print("[rebuild] relaunching the editor")
    subprocess.Popen([EDITOR, PROJECT], close_fds=True)
    for _ in range(80):
        try:
            with urllib.request.urlopen(MCP, timeout=3):
                pass
        except Exception:
            time.sleep(3)
            continue
        break
    print("[rebuild] monolith reachable again")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
