"""Check remaining ABP action schemas + build the state machine."""
import json, urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"

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

for action in ["add_state_to_machine", "set_state_animation", "add_slot_node", "set_output_pose_source", "add_anim_graph_node", "connect_anim_graph_pins"]:
    r = mcp_rpc("describe_query", {"action": "action_schema", "params": {
        "target_namespace": "animation", "target_action": action}})
    print(f"=== {action} ===")
    print(get_text(r)[:800])
    print()
