"""Check schemas and fix montage blend + explore ABP setup options."""
import json, urllib.request

def mcp_call(ns, action, params):
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": f"{ns}_query", "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request('http://127.0.0.1:9316/mcp', data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
    if text.strip() and text.strip() != "{}":
        try:
            return json.loads(text)
        except:
            return {"raw": text[:300]}
    return {"empty": True}

# Check schemas for key ABP animation actions
for action_name in ["set_montage_blend", "add_state_to_machine", "add_slot_node", "add_blend_by_int", "add_anim_graph_node", "connect_anim_graph_pins"]:
    r = mcp_call("describe", "action_schema", {"target_namespace": "animation", "target_action": action_name})
    print(f"=== {action_name} ===")
    print(json.dumps(r, indent=2)[:600])
    print()
