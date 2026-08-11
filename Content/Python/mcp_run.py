"""Run an in-editor Python snippet via Monolith MCP (port 9316).

Avoids shell quoting: the code lives in a .py file, read here, sent verbatim
through monolith_mcp_client.call_tool -> editor_query run_python.
Usage: python mcp_run.py path/to/snippet.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from monolith_mcp_client import ping, call_tool


def main() -> int:
    if not ping():
        print("MONOLITH_UNREACHABLE")
        return 2
    snippet_path = Path(sys.argv[1])
    code = snippet_path.read_text(encoding="utf-8")
    result = call_tool("editor_query", {"action": "run_python", "command": code})
    text = result.get("text", "")
    print(str(result)[:50000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())