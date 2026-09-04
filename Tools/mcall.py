"""One-shot Monolith MCP call helper.

Usage: python Tools/mcall.py <tool> <key=value> [key=value ...]

Resolves the active checkout from this file; no workstation-specific repository
path is allowed here.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

TOOLS_ROOT = Path(__file__).resolve().parent
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

from mcp_client import monolith  # noqa: E402


def parse_value(raw: str):
    """Best-effort typed parse: json: prefix, then int/float/bool/null, else string."""
    if raw.startswith("json:"):
        return json.loads(raw[5:])
    if raw == "true":
        return True
    if raw == "false":
        return False
    if raw == "null":
        return None
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if re.fullmatch(r"-?\d+\.\d+", raw):
        return float(raw)
    return raw


def main():
    if len(sys.argv) < 2:
        print("usage: mcall.py <tool> [key=value ...]")
        sys.exit(2)

    tool = sys.argv[1]
    args = {}
    for pair in sys.argv[2:]:
        if "=" not in pair:
            print(f"WARN: ignoring non key=value arg: {pair}")
            continue
        key, _, val = pair.partition("=")
        args[key] = parse_value(val)

    result = monolith(tool, args)
    if isinstance(result, str):
        print(result)
    else:
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
