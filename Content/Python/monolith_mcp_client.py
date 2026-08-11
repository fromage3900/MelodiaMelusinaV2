"""HTTP JSON-RPC client for Monolith MCP (editor must be open, default port 9316).

Monolith exposes MCP at http://localhost:9316/mcp — same backend as monolith_proxy.exe.
Use from in-editor Python when UnrealMCP socket (55557) is unavailable.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

MONOLITH_URL = "http://127.0.0.1:9316/mcp"
_RPC_ID = 0


def _next_id() -> int:
    global _RPC_ID
    _RPC_ID += 1
    return _RPC_ID


def post(method: str, params: dict | None = None, *, url: str = MONOLITH_URL, timeout: float = 120.0) -> dict:
    payload = {"jsonrpc": "2.0", "id": _next_id(), "method": method, "params": params or {}}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
    return json.loads(body)


def ping(*, timeout: float = 5.0) -> bool:
    try:
        resp = post("ping", {}, timeout=timeout)
        return "error" not in resp
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return False


def call_tool(name: str, arguments: dict, *, timeout: float = 120.0) -> dict:
    resp = post(
        "tools/call",
        {"name": name, "arguments": arguments},
        timeout=timeout,
    )
    if "error" in resp:
        raise RuntimeError(resp["error"])
    return resp.get("result", resp)


def niagara_query(action: str, **kwargs: Any) -> dict:
    args = {"action": action, **kwargs}
    result = call_tool("niagara_query", args)
    if isinstance(result, dict) and "content" in result:
        for block in result.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "text":
                try:
                    return json.loads(block["text"])
                except (json.JSONDecodeError, KeyError, TypeError):
                    return {"text": block.get("text", "")}
    return result if isinstance(result, dict) else {"result": result}


def editor_query(action: str, **kwargs: Any) -> dict:
    args = {"action": action, **kwargs}
    return call_tool("editor_query", args)


def discover_niagara_actions() -> list[str]:
    try:
        result = call_tool("monolith_discover", {"namespace": "niagara"})
        if isinstance(result, dict):
            actions = result.get("actions") or result.get("tools") or []
            return [str(a) for a in actions]
    except Exception:
        pass
    return []
