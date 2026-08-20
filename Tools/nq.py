"""nq.py — thin CLI wrapper for Monolith query namespaces.

Usage:
    python Tools/nq.py niagara get_system_summary params.json
    python Tools/nq.py blueprint get_cdo_properties params.json
    python Tools/nq.py editor capture_scene_preview params.json

Pass a JSON file path (not inline JSON) to avoid shell quoting issues.
Prints the raw text payload (JSON) from the MCP tool call.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from mcp_client import monolith  # noqa: E402

if __name__ == "__main__":
    ns = sys.argv[1] if len(sys.argv) > 1 else "niagara"
    action = sys.argv[2] if len(sys.argv) > 2 else ""
    arg = sys.argv[3] if len(sys.argv) > 3 else "{}"
    try:
        if arg.startswith("@"):
            with open(arg[1:], "r", encoding="utf-8") as f:
                params = json.load(f)
        else:
            params = json.loads(arg)
    except (json.JSONDecodeError, OSError):
        params = {}
    print(monolith(f"{ns}_query", {"action": action, "params": params}))
