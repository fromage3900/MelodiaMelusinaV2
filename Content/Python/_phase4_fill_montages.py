"""Get schema for create_montage_from_sections and add anim segments to montages."""
import json, urllib.request

def mcp_tool(ns, action, params):
    body = {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": f"{ns}_query", "arguments": {"action": action, "params": params}}
    }
    req = urllib.request.Request('http://127.0.0.1:9316/mcp', data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
    return json.loads(text)

# Get schema
print("=== create_montage_from_sections schema ===")
r = mcp_tool("describe", "action_schema", {"target_namespace": "animation", "target_action": "create_montage_from_sections"})
print(json.dumps(r, indent=2)[:2000])

# Now create montages properly using individual actions
# 1. create_montage (base)
# 2. add_montage_slot
# 3. add_montage_anim_segment
# 4. add_montage_section

montages = [
    ("AM_Mocap_BasicAttack", "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_MercyStab.A_Mocap_MercyStab"),
    ("AM_Mocap_Skill", "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_FairyWand.A_Mocap_FairyWand"),
    ("AM_Mocap_Victory", "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_Twirl_001.A_Mocap_Twirl_001"),
    ("AM_Mocap_JumpEnd", "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_GracefulLanding.A_Mocap_GracefulLanding"),
]

for name, anim_path in montages:
    montage_path = f"/Game/Melodia/Characters/Melusina/Animations/{name}.{name}"
    print(f"\n=== Filling {name} ===")
    
    # Check if montage exists (was created by previous script)
    r = mcp_tool("animation", "get_montage_info", {"asset_path": montage_path})
    print(f"Montage info: sections={r.get('section_count')}, slots={r.get('slot_count')}")
    
    # If no anim segments, add one
    if r.get("section_count", 0) > 0:
        # Add animation to DefaultSlot
        r2 = mcp_tool("animation", "add_montage_anim_segment", {
            "asset_path": montage_path,
            "slot_name": "DefaultSlot",
            "anim_path": anim_path,
            "start_time": 0.0,
        })
        print(f"  add_segment: {json.dumps(r2)[:200]}")
    
    # Set blend in/out
    r3 = mcp_tool("animation", "set_montage_blend", {
        "asset_path": montage_path,
        "blend_in": 0.1,
        "blend_out": 0.2,
    })
    print(f"  set_blend: {json.dumps(r3)[:200]}")

print("\n=== Getting ABP_Melusina info for Phase 4.3 ===")
r4 = mcp_tool("animation", "get_abp_info", {"asset_path": "/Game/Melodia/Characters/Melusina/ABP_Melusina.ABP_Melusina"})
print(json.dumps(r4, indent=2)[:3000])
