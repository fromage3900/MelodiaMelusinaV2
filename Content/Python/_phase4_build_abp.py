"""Build ABP_Melusina: variables, state machine, slot node, wiring."""
import json, urllib.request, sys, time

MCP_URL = "http://127.0.0.1:9316/mcp"
ABP = "/Game/Melodia/Characters/Melusina/ABP_Melusina.ABP_Melusina"
SKEL = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton.SK_Melusina_Skeleton"
BS = "/Game/Melodia/Characters/Melusina/BlendSpaces/BS_Locomotion.BS_Locomotion"

MOCAP = "/Game/Melodia/Characters/Melusina/Animations/Mocap"
IDLE = f"{MOCAP}/A_Mocap_Idle.A_Mocap_Idle"

def mcp_rpc(method, arguments):
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": method, "arguments": arguments}}
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(MCP_URL, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_text(r):
    if "error" in r:
        return f"ERROR: {r['error'].get('message','')}"
    content = r.get("result", {}).get("content", [])
    if content:
        return content[0].get("text", str(content[0]))
    return str(r)

def anim_call(action, params):
    return mcp_rpc("animation_query", {"action": action, "params": params})

def bp_call(action, params):
    return mcp_rpc("blueprint_query", {"action": action, "params": params})

def editor_code(code, mode="execute_statement"):
    return mcp_rpc("editor_query", {"action": "run_python", "params": {"command": code, "mode": mode}})

# Check add_variable schema
r = mcp_rpc("describe_query", {"action": "action_schema", "params": {
    "target_namespace": "blueprint", "target_action": "add_variable"}})
print("=== add_variable schema ===")
print(get_text(r)[:1200])
print()

# Check add_property_access_node schema
r = mcp_rpc("describe_query", {"action": "action_schema", "params": {
    "target_namespace": "blueprint", "target_action": "add_property_access_node"}})
print("=== add_property_access_node schema ===")
print(get_text(r)[:1200])
print()

# Step 1: Add Speed variable to ABP
print("=== Adding Speed variable ===")
r = bp_call("add_variable", {
    "asset_path": ABP,
    "name": "Speed",
    "type": "float",
    "default_value": "0.0",
    "category": "Locomotion",
})
print(get_text(r)[:500])

# Step 2: Verify variable exists
r = bp_call("get_variables", {"asset_path": ABP})
print(get_text(r)[:800])
