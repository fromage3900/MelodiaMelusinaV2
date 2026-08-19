"""CLI wrapper around the Cascadeur MCP bridge for headless scripting.

Usage (run with C:/Python314/python.exe):
    cascadeur_rpc.py scene
    cascadeur_rpc.py import <path.fbx> [import_model|import_animation|import_scene|add_model]
    cascadeur_rpc.py exec "<python code>"
    cascadeur_rpc.py export <path.fbx> [method]

Each call round-trips through the running Cascadeur instance via
cascadeur.exe --run-script commands.externals.csc_mcp_exec.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from deploy.cascadeur_mcp_server import execute_cascadeur_code, export_fbx, get_scene_info, import_fbx  # noqa: E402


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "scene":
        print(get_scene_info())
    elif cmd == "import":
        if len(rest) < 1:
            print("usage: cascadeur_rpc.py import <path.fbx> [method]")
            return 2
        print(import_fbx(rest[0], rest[1] if len(rest) > 1 else "import_model"))
    elif cmd == "export":
        if len(rest) < 1:
            print("usage: cascadeur_rpc.py export <path.fbx> [method]")
            return 2
        print(export_fbx(rest[0], rest[1] if len(rest) > 1 else "export_all_objects"))
    elif cmd == "exec":
        if len(rest) < 1:
            print("usage: cascadeur_rpc.py exec <python code>")
            return 2
        print(execute_cascadeur_code(rest[0]))
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
