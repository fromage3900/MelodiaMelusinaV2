"""Run set_abp_skeleton_temp.py via editor.run_python (execute_file mode)."""
import json, urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"

def mcp_rpc(method, arguments):
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": method, "arguments": arguments}}
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(MCP_URL, data=data,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_text(r):
    if "error" in r:
        return f"ERROR: {r['error'].get('message','')}"
    content = r.get("result", {}).get("content", [])
    if content:
        return content[0].get("text", str(content[0]))
    return str(r)

# Set skeleton via execute_file
body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "editor_query", "arguments": {
            "action": "run_python",
            "params": {
                "command": "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/_set_abp_skeleton_temp.py",
                "mode": "execute_file"
            }
        }}}
data = json.dumps(body).encode("utf-8")
req = urllib.request.Request(MCP_URL, data=data,
                             headers={"Content-Type": "application/json"},
                             method="POST")
with urllib.request.urlopen(req, timeout=60) as resp:
    r = json.loads(resp.read().decode("utf-8"))
print("=== Set skeleton ===")
print(get_text(r))

# Verify
body2 = {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
         "params": {"name": "animation_query", "arguments": {
             "action": "get_abp_info",
             "params": {"asset_path": "/Game/Melodia/Characters/Melusina/ABP_Melusina.ABP_Melusina"}
         }}}
data2 = json.dumps(body2).encode("utf-8")
req2 = urllib.request.Request(MCP_URL, data=data2,
                              headers={"Content-Type": "application/json"},
                              method="POST")
with urllib.request.urlopen(req2, timeout=60) as resp:
    r2 = json.loads(resp.read().decode("utf-8"))
print("\n=== Verify ===")
print(get_text(r2)[:800])
