#!/usr/bin/env python3
"""
mcp_client.py - the single MCP client for Tools/* pipeline scripts.

Wraps the Monolith JSON-RPC endpoint used by the T3D wiring pipeline
(bp_regression_checker.py, t3d_blueprint_injector.py, continuous_loop.py,
live_dashboard.py, metrics_dashboard.py, loop_monitor.py, ...).

Call convention (same envelope as deploy/call_mcp.py):

    {"jsonrpc": "2.0", "id": <unique>, "method": "tools/call",
     "params": {"name": <tool>, "arguments": <args>}}

- monolith(method, args) calls an MCP tool (e.g. "blueprint_query") and returns
  the parsed text payload, joining every text content item (not just the
  first), or "ERROR:<reason>" when the server is unreachable, returns no
  content, or reports result.isError. Callers may feed the text to
  json.loads() for structured results.
- discover(namespace) lists the tools available for a namespace (e.g.
  "blueprint" -> blueprint_query). The server documents a monolith_discover
  convention; when the server does not implement it, tools/list enumeration
  filtered by namespace is used instead.

MONOLITH_URL honours the environment variable of the same name so a caller
(or CI) can point this at a non-default Monolith instance. It is resolved
once at import time, matching every other Tools/ script that reads it.
"""
import itertools
import json
import os
import urllib.error
import urllib.request

MONOLITH_URL = os.environ.get("MONOLITH_URL", "http://127.0.0.1:9316/mcp")

_id_counter = itertools.count(1)


def _next_id():
    return next(_id_counter)


def _call_envelope(method, params=None, timeout=30):
    """POST a raw JSON-RPC method and return the parsed envelope dict."""
    body = {
        "jsonrpc": "2.0",
        "id": _next_id(),
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

    Returns the text of every content item joined with newlines, or
    "ERROR:<reason>" when the server cannot be reached, returns no content,
    or reports result.isError (the MCP-level error signal, distinct from the
    JSON-RPC transport-level "error" key already handled above).
    """
    envelope = _call_envelope("tools/call", {"name": method, "arguments": args or {}}, timeout=timeout)
    if "error" in envelope:
        return f"ERROR:{envelope['error']}"
    result = envelope.get("result", {})
    content = result.get("content") or []
    if not content:
        return "ERROR:empty content"
    texts = [item.get("text", "") for item in content if isinstance(item, dict)]
    joined = "\n".join(t for t in texts if t)
    if result.get("isError"):
        return f"ERROR:{joined or 'MCP tool reported isError'}"
    return joined


def discover(namespace, timeout=30):
    """List MCP tools for a namespace (e.g. "blueprint" -> blueprint_query).

    Tries the server-documented monolith_discover convention first; falls
    back to tools/list enumeration filtered by namespace. Returns a list of
    tool dicts ({"name", "description", ...}) or None when the server is
    unreachable.
    """
    envelope = _call_envelope("monolith_discover", {"namespace": namespace}, timeout=timeout)
    if "error" not in envelope:
        result = envelope.get("result", {})
        content = result.get("content") or []
        if content and not result.get("isError"):
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


def selftest(timeout=5):
    """Read-only reachability check. Never mutates project state.

    Calls monolith_status, which Monolith answers without touching any
    asset. Returns (ok: bool, detail: str).
    """
    result = monolith("monolith_status", {}, timeout=timeout)
    if isinstance(result, str) and result.startswith("ERROR:"):
        return False, result
    return True, result


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: mcp_client.py <method> [json_args]")
        print("       mcp_client.py discover <namespace>")
        print("       mcp_client.py --selftest")
        sys.exit(1)
    if sys.argv[1] == "--selftest":
        ok, detail = selftest()
        print(f"MONOLITH_URL: {MONOLITH_URL}")
        print(f"reachable: {ok}")
        print(detail)
        sys.exit(0 if ok else 1)
    elif sys.argv[1] == "discover":
        tools = discover(sys.argv[2] if len(sys.argv) > 2 else "")
        print(json.dumps(tools, indent=2) if tools is not None else "ERROR:discover failed")
    else:
        args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
        print(monolith(sys.argv[1], args))
