"""Verify Blender 5.2 MCP adapter via MCP protocol (raw JSON-RPC stdio).

Usage:
  python deploy/_mcp_verify_blender_5_2.py
"""
import json
import os
import subprocess
import sys

DEPLOY = os.path.dirname(os.path.abspath(__file__))
ADAPTER = os.path.join(DEPLOY, "blender_5.2_mcp.py")


def _mcp_call(requests: list[dict], timeout: int = 120) -> list[dict]:
    """Send JSON-RPC requests to the MCP adapter via stdio and return responses."""
    input_data = "\n".join(json.dumps(r) for r in requests)
    proc = subprocess.run(
        [sys.executable, ADAPTER],
        input=input_data,
        capture_output=True, text=True, timeout=timeout,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    responses = []
    for line in proc.stdout.strip().split("\n"):
        line = line.strip()
        if line:
            responses.append(json.loads(line))
    return responses


def _call_tool(name: str, args: dict = None, timeout: int = 120) -> dict:
    init = {"jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                       "clientInfo": {"name": "verify", "version": "1.0"}}}
    notif = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
    tool_call = {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                 "params": {"name": name, "arguments": args or {}}}
    responses = _mcp_call([init, notif, tool_call], timeout=timeout)
    for r in responses:
        content = r.get("result", {}).get("content", [])
        if content:
            return json.loads(content[0]["text"])
    return {"status": "error", "message": "no tool result"}


TESTS = []


def test(name: str):
    def wrapper(fn):
        TESTS.append((name, fn))
        return fn
    return wrapper


@test("get_scene_info")
def test_scene_info():
    r = _call_tool("get_scene_info", timeout=30)
    assert r.get("status") == "ok", f"FAIL: {r}"
    obj_count = r.get("result", {}).get("object_count", 0)
    print(f"  PASS: {obj_count} objects, {r['result']['materials_count']} materials")


@test("list_genomes")
def test_list_genomes():
    r = _call_tool("list_genomes", timeout=120)
    assert r.get("status") == "ok", f"FAIL: {r}"
    res = r.get("result", {})
    print(f"  PASS: {res.get('total', 0)} styles, {len(res.get('groups', []))} groups: {res.get('groups', [])}")


@test("create_mesh")
def test_create_mesh():
    r = _call_tool("create_mesh", {"name": "VerifyCube", "mesh_type": "CUBE"}, timeout=30)
    assert r.get("status") == "ok", f"FAIL: {r}"
    print(f"  PASS: created {r['result']['name']}")


@test("list_materials")
def test_list_materials():
    r = _call_tool("list_materials", timeout=30)
    assert r.get("status") == "ok", f"FAIL: {r}"
    print(f"  PASS: {r['result']['count']} materials")


def run_all():
    print(f"=== Blender 5.2 MCP Verify (MCP protocol) ===")
    print(f"Adapter: {ADAPTER}")
    passed = 0
    failed = 0
    for name, fn in TESTS:
        print(f"  {name}...", end=" ")
        try:
            fn()
            passed += 1
        except Exception as e:
            print(f"FAIL: {e}")
            failed += 1
    print(f"\n=== {passed}/{passed + failed} passed ===")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
