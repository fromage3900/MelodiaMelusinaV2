"""Create montages step by step using individual MCP actions."""
import json, urllib.request

def mcp_call(method, params):
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": method, "arguments": params}}
    req = urllib.request.Request('http://127.0.0.1:9316/mcp', data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
    # Handle case where text is empty or just whitespace
    if text.strip() and text.strip() != "{}":
        try:
            return json.loads(text)
        except:
            return {"raw": text[:200]}
    return {"empty": True}

# Get schema for create_montage  
print("=== create_montage schema ===")
r = mcp_call("describe_query", {"action": "action_schema",
    "params": {"target_namespace": "animation", "target_action": "create_montage"}})
print(json.dumps(r, indent=2)[:500])

# Create montage for BasicAttack
print("\n=== Creating AM_Mocap_BasicAttack ===")
r = mcp_call("animation_query", {"action": "create_montage", "params": {
    "asset_path": "/Game/Melodia/Characters/Melusina/Animations/AM_Mocap_BasicAttack.AM_Mocap_BasicAttack",
    "skeleton_path": "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton.SK_Melusina_Skeleton",
}})
print(json.dumps(r, indent=2)[:500])

# Add a slot
print("\n=== Adding DefaultSlot ===")
r = mcp_call("animation_query", {"action": "add_montage_slot", "params": {
    "asset_path": "/Game/Melodia/Characters/Melusina/Animations/AM_Mocap_BasicAttack.AM_Mocap_BasicAttack",
    "slot_name": "DefaultSlot",
}})
print(json.dumps(r, indent=2)[:500])

# Add anim segment
print("\n=== Adding anim segment ===")
r = mcp_call("animation_query", {"action": "add_montage_anim_segment", "params": {
    "asset_path": "/Game/Melodia/Characters/Melusina/Animations/AM_Mocap_BasicAttack.AM_Mocap_BasicAttack",
    "slot_name": "DefaultSlot",
    "anim_path": "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_MercyStab.A_Mocap_MercyStab",
    "start_time": 0.0,
}})
print(json.dumps(r, indent=2)[:500])

# Add section
print("\n=== Adding section ===")
r = mcp_call("animation_query", {"action": "add_montage_section", "params": {
    "asset_path": "/Game/Melodia/Characters/Melusina/Animations/AM_Mocap_BasicAttack.AM_Mocap_BasicAttack",
    "section_name": "Default",
    "start_time": 0.0,
}})
print(json.dumps(r, indent=2)[:500])

# Verify
print("\n=== Verify ===")
r = mcp_call("animation_query", {"action": "get_montage_info", "params": {
    "asset_path": "/Game/Melodia/Characters/Melusina/Animations/AM_Mocap_BasicAttack.AM_Mocap_BasicAttack"}})
print(json.dumps(r, indent=2)[:600])
