# -*- coding: utf-8 -*-
"""Send a Python snippet to the already-open Unreal Editor via Monolith.

Does not spawn UnrealEditor. Usage:
  python Tools/ue_run_python.py --file snippet.py
  python Tools/ue_run_python.py --exec "print('ok')"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from mcp_client import monolith  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path)
    parser.add_argument("--exec", dest="code")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    if args.file:
        code = args.file.read_text(encoding="utf-8")
    elif args.code:
        code = args.code
    else:
        parser.error("need --file or --exec")
        return 2
    raw = monolith(
        "editor_query",
        {"action": "run_python", "params": {"command": code}},
        timeout=args.timeout,
    )
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(raw)
    if isinstance(raw, str) and raw.startswith("ERROR:"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
