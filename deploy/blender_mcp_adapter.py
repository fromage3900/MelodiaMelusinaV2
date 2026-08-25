"""Blender MCP stdio adapter - wraps TCP socket addon (port 9878) as standard MCP server for opencode."""
from __future__ import annotations

import json
import socket
import sys
import time

BLENDER_MCP_HOST = "127.0.0.1"
BLENDER_MCP_PORT = 9878
CMD_TIMEOUT = 15

TOOLS = [
    {
        "name": "blender_scene_info",
        "description": "Get current scene info (objects, materials count, first 10 objects)",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "blender_object_info",
        "description": "Get detailed info about a named object",
        "inputSchema": {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Object name"}},
            "required": ["name"],
        },
    },
    {
        "name": "blender_execute_code",
        "description": "Execute arbitrary Blender Python code",
        "inputSchema": {
            "type": "object",
            "properties": {"code": {"type": "string", "description": "Python code to execute in Blender"}},
            "required": ["code"],
        },
    },
    {
        "name": "blender_viewport_screenshot",
        "description": "Capture a viewport screenshot to a file",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Save path (optional, defaults to temp file)"},
            },
            "required": [],
        },
    },
    {
        "name": "blender_shared_context",
        "description": "Get shared context state (variables, object/material handles, history)",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "blender_create_handle",
        "description": "Create a handle referencing an object for future operations",
        "inputSchema": {
            "type": "object",
            "properties": {
                "handle": {"type": "string", "description": "Handle name"},
                "object_name": {"type": "string", "description": "Existing object name in scene"},
            },
            "required": ["handle", "object_name"],
        },
    },
]


def _send_cmd(cmd_type: str, params: dict | None = None) -> dict:
    payload = json.dumps({"type": cmd_type, "params": params or {}})
    try:
        s = socket.create_connection((BLENDER_MCP_HOST, BLENDER_MCP_PORT), timeout=5)
        s.settimeout(CMD_TIMEOUT)
        s.sendall(payload.encode("utf-8"))
        time.sleep(2.5)
        resp = b""
        while True:
            try:
                chunk = s.recv(4096)
                if not chunk:
                    break
                resp += chunk
            except socket.timeout:
                break
        s.close()
        if not resp:
            return {"status": "error", "message": "empty response from Blender MCP"}
        return json.loads(resp.decode("utf-8"))
    except Exception as e:
        return {"status": "error", "message": str(e)}


def _exec_code(code: str) -> dict:
    return _send_cmd("execute_code", {"code": code})


def _handle_tool(name: str, args: dict) -> dict:
    if name == "blender_scene_info":
        return _send_cmd("get_scene_info")
    if name == "blender_object_info":
        return _send_cmd("get_object_info", {"name": args["name"]})
    if name == "blender_execute_code":
        return _exec_code(args["code"])
    if name == "blender_viewport_screenshot":
        return _send_cmd("get_viewport_screenshot", args)
    if name == "blender_shared_context":
        return _send_cmd("get_shared_context")
    if name == "blender_create_handle":
        return _send_cmd("create_object_handle", {"handle": args["handle"], "object_name": args["object_name"]})
    return {"status": "error", "message": f"Unknown tool: {name}"}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        rid = msg.get("id")
        method = msg.get("method", "")
        params = msg.get("params", {})

        if method == "initialize":
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0", "id": rid,
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "blender-mcp-adapter", "version": "2.0.0"},
                }
            }) + "\n")
            sys.stdout.flush()
        elif method == "tools/list":
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0", "id": rid,
                "result": {"tools": TOOLS}
            }) + "\n")
            sys.stdout.flush()
        elif method == "tools/call":
            result = _handle_tool(params.get("name", ""), params.get("arguments", {}))
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0", "id": rid,
                "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
            }) + "\n")
            sys.stdout.flush()
        elif method == "notifications/initialized":
            pass
        else:
            sys.stdout.write(json.dumps({
                "jsonrpc": "2.0", "id": rid,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()