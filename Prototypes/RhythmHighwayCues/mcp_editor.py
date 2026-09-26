"""Tiny Monolith MCP client for one-off editor calls (live compile, log search).

Usage:
    uv run --no-sync python Prototypes/RhythmHighwayCues/mcp_editor.py live_compile
    uv run --no-sync python Prototypes/RhythmHighwayCues/mcp_editor.py call <tool> <json-args>
"""
from __future__ import annotations

import json
import sys
import urllib.request

MCP = "http://127.0.0.1:9316/mcp"


def call(tool: str, args: dict, timeout: int = 300) -> dict:
    body = json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": args}}
    ).encode()
    req = urllib.request.Request(MCP, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = json.loads(r.read().decode())
    result = data.get("result", {})
    content = result.get("content") or [{}]
    text = content[0].get("text", "")
    try:
        return json.loads(text) if text else {}
    except Exception:
        return {"raw": text}


def main() -> int:
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return 2
    if argv[0] == "live_compile":
        out = call("editor_query", {"action": "live_compile"})
        print("live_compile:", json.dumps(out)[:900])
        return 0
    if argv[0] == "call":
        tool = argv[1]
        args = json.loads(argv[2]) if len(argv) > 2 else {}
        print(json.dumps(call(tool, args))[:4000])
        return 0
    print("unknown command", argv[0])
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
