"""Check create_state_machine schema + save ABP + build phase 4."""
import json, urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"
ABP = "/Game/Melodia/Characters/Melusina/ABP_Melusina.ABP_Melusina"

def mcp_rpc(method, arguments):
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": method, "arguments": arguments}}
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(MCP_URL, data=data,
                                 headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_text(r):
    if "error" in r:
        return f"ERROR: {r['error'].get('message','')}"
    content = r.get("result", {}).get("content", [])
    if content:
        return content[0].get("text", str(content[0]))
    return str(r)

# 1. Check create_state_machine schema
r = mcp_rpc("describe_query", {"action": "action_schema", "params": {
    "target_namespace": "animation", "target_action": "create_state_machine"}})
print("=== create_state_machine schema ===")
print(get_text(r)[:1000])

# 2. Save the ABP using path string
r2 = mcp_rpc("editor_query", {"action": "run_python", "params": {
    "command": "unreal.EditorAssetLibrary.save_asset('/Game/Melodia/Characters/Melusina/ABP_Melusina.ABP_Melusina')",
    "mode": "execute_statement"}})
print("\n=== Save ABP ===")
print(get_text(r2)[:500])
