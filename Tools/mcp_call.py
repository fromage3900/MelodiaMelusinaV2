"""Minimal MCP caller for Monolith at 127.0.0.1:9316.

Usage:
  python Tools/mcp_call.py run_python <command_file>
  python Tools/mcp_call.py <tool> <action> <params_json_file>
"""

from mcp_client import post_envelope
import json
import sys

URL = "http://127.0.0.1:9316/mcp"


def call(name, arguments):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": name, "arguments": arguments}}).encode()
    return post_envelope(body, timeout=600, raise_on_error=True)


def main():
    if sys.argv[1] == "run_python":
        cmd = open(sys.argv[2], encoding="utf-8").read()
        r = call("editor_query", {"action": "run_python", "params": {"command": cmd}})
    else:
        tool, action, path = sys.argv[1], sys.argv[2], sys.argv[3]
        params = json.load(open(path, encoding="utf-8"))
        r = call(tool, {"action": action, "params": params})
    if "result" in r:
        print(r["result"]["content"][0]["text"])
    else:
        print(json.dumps(r, indent=1))


if __name__ == "__main__":
    main()
