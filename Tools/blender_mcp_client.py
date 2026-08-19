# -*- coding: utf-8 -*-
"""Client for the in-session BlenderMCP addon (TCP 127.0.0.1:9876).

Protocol: send {"type": "<cmd>", "params": {...}}; the addon replies on the same
connection and keeps it open, so we read until a complete JSON response plus an
idle gap (or connection close).

Usage:
  python Tools/blender_mcp_client.py get_scene_info
  python Tools/blender_mcp_client.py execute_code "bpy.data.objects.keys()[:5]"
  python Tools/blender_mcp_client.py execute_code --file path/to/code.py
  python Tools/blender_mcp_client.py get_viewport_screenshot <filepath>
"""
from __future__ import annotations

import json
import socket
import sys
import time

HOST = "127.0.0.1"
PORT = 9876
IDLE = 1.5
MAX_WAIT = 1200.0


def call(cmd_type: str, params: dict | None = None) -> dict:
    payload = json.dumps({"type": cmd_type, "params": params or {}})
    s = socket.create_connection((HOST, PORT), timeout=5)
    s.settimeout(1.0)
    s.sendall(payload.encode("utf-8"))
    buf = b""
    last_data = time.time()
    deadline = time.time() + MAX_WAIT
    while time.time() < deadline:
        try:
            chunk = s.recv(65536)
            if chunk:
                buf += chunk
                last_data = time.time()
            else:
                break
        except socket.timeout:
            if buf and (time.time() - last_data) > IDLE:
                break
        except OSError:
            break
    s.close()
    if not buf:
        return {"status": "error", "message": "empty response"}
    try:
        return json.loads(buf.decode("utf-8", "replace"))
    except Exception:
        return {"status": "error", "message": "unparseable response", "raw": buf.decode("utf-8", "replace")[:2000]}


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print("usage: blender_mcp_client.py <cmd> [code|--file path|filepath]")
        sys.exit(1)
    cmd = args[0]
    if cmd == "execute_code":
        if len(args) >= 3 and args[1] == "--file":
            code = open(args[2], "r", encoding="utf-8").read()
        elif len(args) >= 2:
            code = args[1]
        else:
            print("execute_code needs a code string or --file path")
            sys.exit(1)
        print(json.dumps(call("execute_code", {"code": code}), indent=2))
    elif cmd == "get_object_info":
        print(json.dumps(call("get_object_info", {"name": args[1] if len(args) > 1 else ""}), indent=2))
    elif cmd == "get_viewport_screenshot":
        print(json.dumps(call("get_viewport_screenshot", {"filepath": args[1]} if len(args) > 1 else {}), indent=2))
    else:
        print(json.dumps(call(cmd), indent=2))
