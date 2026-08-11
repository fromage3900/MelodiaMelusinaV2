"""Complete all 4 montages + set blend + verify."""
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
            return {"raw": text[:200]}
    return {"empty": True}

montages = [
    ("AM_Mocap_BasicAttack", "A_Mocap_MercyStab"),
    ("AM_Mocap_Skill", "A_Mocap_FairyWand"),
    ("AM_Mocap_Victory", "A_Mocap_Twirl_001"),
    ("AM_Mocap_JumpEnd", "A_Mocap_GracefulLanding"),
]

for name, anim_base in montages:
    montage_path = f"/Game/Melodia/Characters/Melusina/Animations/{name}.{name}"
    anim_path = f"/Game/Melodia/Characters/Melusina/Animations/Mocap/{anim_base}.{anim_base}"
    
    # Get montage info to see current state
    info = mcp_call("animation", "get_montage_info", {"asset_path": montage_path})
    
    # The montage exists but may have 0 sections. If section exists, set blend
    # If no anim segment, add one
    has_segments = info.get("slots") and len(info.get("slots", [])) > 0
    has_sections = info.get("sections") and len(info.get("sections", [])) > 0
    
    if not has_segments:
        # Add anim segment - try without slot_name
        r = mcp_call("animation", "add_montage_anim_segment", {
            "asset_path": montage_path,
            "anim_path": anim_path,
            "start_time": 0.0,
        })
        print(f"{name}: added segment = {r.get('segment_index', '?')}")
    
    if has_sections:
        # Set blend
        r = mcp_call("animation", "set_montage_blend", {
            "asset_path": montage_path,
            "blend_in": 0.1,
            "blend_out": 0.2,
        })
        print(f"{name}: blend set = {r}")
    
    # Final check
    final = mcp_call("animation", "get_montage_info", {"asset_path": montage_path})
    sections = len(final.get("sections", []))
    slots = len(final.get("slots", []))
    duration = final.get("duration", 0)
    print(f"{name}: sections={sections}, slots={slots}, duration={duration}s")
    print()

# Now get ABP_Melusina structure
print("=== ABP_Melusina structure ===")
r = mcp_call("animation", "get_abp_info", {"asset_path": "/Game/Melodia/Characters/Melusina/ABP_Melusina.ABP_Melusina"})
print(json.dumps(r, indent=2)[:4000])
