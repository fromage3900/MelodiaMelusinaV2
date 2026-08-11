#!/usr/bin/env python3
"""
mcp_client.py — the single MCP client for Tools/* pipeline scripts.

Wraps the Monolith JSON-RPC endpoint used by the T3D wiring pipeline
(bp_regression_checker.py, t3d_blueprint_injector.py, continuous_loop.py,
live_dashboard.py, metrics_dashboard.py, loop_monitor.py, ...).

Call convention (same envelope as deploy/call_mcp.py):

    {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
     "params": {"name": <tool>, "arguments": <args>}}

- monolith(method, args) calls an MCP tool (e.g. "blueprint_query") and returns
  the parsed text payload of the first content item, or "ERROR:<reason>" when
  the server is unreachable / returns no content. Callers may feed the text to
  json.loads() for structured results.
- discover(namespace) lists the tools available for a namespace (e.g.
  "blueprint" -> blueprint_query). The server documents a monolith_discover
  convention; when the server does not implement it, tools/list enumeration
  filtered by namespace is used instead.
"""
import json
import urllib.error
import urllib.request

MONOLITH_URL = "http://127.0.0.1:9316/mcp"


def _call_envelope(method, params=None, timeout=30):
    """POST a raw JSON-RPC method and return the parsed envelope dict."""
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {},
    }
    req = urllib.request.Request(
        MONOLITH_URL,
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        return {"error": str(e)}


def monolith(method, args=None, timeout=30):
    """Call an MCP tool via tools/call and return its parsed text content.

    Returns the text of the first content item, or "ERROR:<reason>" when the
    server cannot be reached or returns no content.
    """
    envelope = _call_envelope("tools/call", {"name": method, "arguments": args or {}}, timeout=timeout)
    if "error" in envelope:
        return f"ERROR:{envelope['error']}"
    content = envelope.get("result", {}).get("content") or []
    if not content:
        return "ERROR:empty content"
    return content[0].get("text", "")


def discover(namespace, timeout=30):
    """List MCP tools for a namespace (e.g. "blueprint" -> blueprint_query).

    Tries the server-documented monolith_discover convention first; falls back
    to tools/list enumeration filtered by namespace. Returns a list of tool
    dicts ({"name", "description", ...}) or None when the server is unreachable.
    """
    envelope = _call_envelope("monolith_discover", {"namespace": namespace}, timeout=timeout)
    if "error" not in envelope:
        content = envelope.get("result", {}).get("content") or []
        if content:
            text = content[0].get("text", "")
            try:
                parsed = json.loads(text) if text else None
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, dict) and isinstance(parsed.get("tools"), list):
                return parsed["tools"]

    envelope = _call_envelope("tools/list", {}, timeout=timeout)
    if "error" in envelope:
        return None
    tools = envelope.get("result", {}).get("tools", [])
    return [t for t in tools if namespace in t.get("name", "")]


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: mcp_client.py <method> [json_args]")
        print("       mcp_client.py discover <namespace>")
        sys.exit(1)
    if sys.argv[1] == "discover":
        tools = discover(sys.argv[2] if len(sys.argv) > 2 else "")
        print(json.dumps(tools, indent=2) if tools is not None else "ERROR:discover failed")
    else:
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
        print(monolith(sys.argv[1], args))
