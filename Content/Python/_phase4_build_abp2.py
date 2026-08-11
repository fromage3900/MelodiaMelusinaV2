"""Build ABP_Melusina: state machine, states, slot, and wiring."""
import json, urllib.request, time

MCP_URL = "http://127.0.0.1:9316/mcp"
ABP = "/Game/Melodia/Characters/Melusina/ABP_Melusina.ABP_Melusina"
BS = "/Game/Melodia/Characters/Melusina/BlendSpaces/BS_Locomotion.BS_Locomotion"
IDLE = "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_Idle.A_Mocap_Idle"

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

def action_text(action, params):
    return get_text(anim_call(action, params))

# Step 1: Create state machine
print("=== Creating Locomotion state machine ===")
r = anim_call("create_state_machine", {
    "asset_path": ABP,
    "state_machine_name": "Locomotion",
    "position_x": 200,
    "position_y": 300,
})
print(get_text(r)[:500])

# Step 2: Verify state machines
print("\n=== State machines ===")
r = anim_call("get_state_machines", {"asset_path": ABP})
print(get_text(r)[:500])

# Step 3: Add states
for st_name, pos_y in [("Idle", 100), ("Walk", 0), ("Run", -100)]:
    r = anim_call("add_state_to_machine", {
        "asset_path": ABP,
        "machine_name": "Locomotion",
        "state_name": st_name,
        "position_y": pos_y,
    })
    print(f"  {st_name}: {get_text(r)[:200]}")

# Step 4: Set state animations
print("\n=== Setting Idle state animation ===")
r = anim_call("set_state_animation", {
    "asset_path": ABP,
    "machine_name": "Locomotion",
    "state_name": "Idle",
    "anim_asset_path": IDLE,
    "loop": True,
})
print(get_text(r)[:400])

print("\n=== Setting Walk state animation (BlendSpace) ===")
r = anim_call("set_state_animation", {
    "asset_path": ABP,
    "machine_name": "Locomotion",
    "state_name": "Walk",
    "anim_asset_path": BS,
    "loop": True,
})
print(get_text(r)[:400])

print("\n=== Setting Run state animation (BlendSpace) ===")
r = anim_call("set_state_animation", {
    "asset_path": ABP,
    "machine_name": "Locomotion",
    "state_name": "Run",
    "anim_asset_path": BS,
    "loop": True,
})
print(get_text(r)[:400])

# Step 5: Check state info  
print("\n=== State info ===")
for st in ["Idle", "Walk", "Run"]:
    r = anim_call("get_state_info", {
        "asset_path": ABP,
        "machine_name": "Locomotion",
        "state_name": st,
    })
    text = get_text(r)[:600]
    print(f"  {st}: {text}")

# Step 6: Add DefaultSlot node in AnimGraph
print("\n=== Adding DefaultSlot node ===")
r = anim_call("add_slot_node", {
    "asset_path": ABP,
    "slot_name": "DefaultSlot",
})
print(get_text(r)[:400])

# Step 7: Set output pose source to use the slot node
# First, need to find the slot node name
print("\n=== Getting graph nodes ===")
r = anim_call("get_nodes", {"asset_path": ABP, "graph_name": "AnimGraph"})
print(get_text(r)[:1000])
