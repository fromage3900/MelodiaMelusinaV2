"""List available animation actions and fix montage blends."""
import json, urllib.request

def mcp_call(ns, action, params):
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": f"{ns}_query", "arguments": {"action": action, "params": params}}}
    req = urllib.request.Request("http://127.0.0.1:9316/mcp", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
    if text.strip() and text.strip() != "{}":
        try:
            return json.loads(text)
        except:
            return {"raw": text[:500]}
    return {"empty": True}

# Try to list actions
for possible in ["list_actions", "get_actions", "get_all_schemas", "available_actions"]:
    r = mcp_call("describe", possible, {"target_namespace": "animation"})
    val = r.get("raw", json.dumps(r)[:300])
    print(f"{possible}: {val}")

# Fix montage blends using correct param names
print("\n=== Fixing montage blends ===")
for name in ["AM_Mocap_BasicAttack", "AM_Mocap_Skill", "AM_Mocap_Victory", "AM_Mocap_JumpEnd"]:
    path = f"/Game/Melodia/Characters/Melusina/Animations/{name}.{name}"
    r = mcp_call("animation", "set_montage_blend", {
        "asset_path": path,
        "blend_in_time": 0.1,
        "blend_out_time": 0.2,
    })
    print(f"  {name}: blend = {r.get('blend_in_time','?')} / {r.get('blend_out_time','?')}")

# Check ABP more carefully - look for existing state machines
print("\n=== ABP_Melusina state machines ===")
r = mcp_call("animation", "get_state_machines", {
    "asset_path": "/Game/Melodia/Characters/Melusina/ABP_Melusina.ABP_Melusina"})
print(json.dumps(r, indent=2)[:1000])

# Check if we can set skeleton on ABP
print("\n=== Set ABP skeleton? ===")
r = mcp_call("describe", "action_schema", {
    "target_namespace": "animation", "target_action": "set_abp_skeleton"})
print(json.dumps(r, indent=2)[:500])
