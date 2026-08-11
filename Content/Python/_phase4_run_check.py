"""Run property check via MCP execute_file."""
import json, urllib.request

req = urllib.request.Request(
    'http://127.0.0.1:9316/mcp',
    data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "editor_query",
                                "arguments": {"action": "run_python",
                                              "params": {"command": "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/_phase4_check_props.py",
                                                         "mode": "execute_file"}}}}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
parsed = json.loads(text)
print("skeleton settable:", parsed.get("skeleton_settable"))
print("error:", parsed.get("skeleton_error"))
print("anim_seq props:", parsed.get("anim_seq_props"))
