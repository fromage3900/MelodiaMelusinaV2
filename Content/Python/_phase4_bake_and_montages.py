"""Bake blendspace + create battle montages."""
import json, urllib.request

def mcp_tool(ns, action, params):
    body = {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": f"{ns}_query", "arguments": {"action": action, "params": params}}
    }
    req = urllib.request.Request('http://127.0.0.1:9316/mcp', data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
    return json.loads(text)

def mcp_dict(ns, action, params):
    return mcp_tool(ns, action, params)

# Step 1: Bake blendspace
print("=== Baking blendspace ===")
r = mcp_tool("animation", "bake_blend_space", {"asset_path": "/Game/Melodia/Characters/Melusina/BlendSpaces/BS_Locomotion.BS_Locomotion"})
print(json.dumps(r, indent=2)[:500])

# Step 2: Get blendspace info to see samples
print("\n=== Blendspace info ===")
r = mcp_tool("animation", "get_blend_space_info", {"asset_path": "/Game/Melodia/Characters/Melusina/BlendSpaces/BS_Locomotion.BS_Locomotion"})
print(json.dumps(r, indent=2)[:1000])

# Step 3: Create battle montages
# Using create_montage_from_sections (all-in-one)
# Basic Attack: A_Mocap_MercyStab
print("\n=== Creating AM_Mocap_BasicAttack ===")
r = mcp_tool("animation", "create_montage_from_sections", {
    "asset_path": "/Game/Melodia/Characters/Melusina/Animations/AM_Mocap_BasicAttack",
    "skeleton_path": "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton.SK_Melusina_Skeleton",
    "slot_name": "DefaultSlot",
    "segments": [
        {"anim_path": "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_MercyStab.A_Mocap_MercyStab", "start_time": 0.0}
    ],
    "sections": [
        {"name": "Default", "start_time": 0.0}
    ],
    "blend_in": 0.1,
    "blend_out": 0.2,
})
print(json.dumps(r, indent=2)[:500])

# Skill: A_Mocap_FairyWand
print("\n=== Creating AM_Mocap_Skill ===")
r = mcp_tool("animation", "create_montage_from_sections", {
    "asset_path": "/Game/Melodia/Characters/Melusina/Animations/AM_Mocap_Skill",
    "skeleton_path": "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton.SK_Melusina_Skeleton",
    "slot_name": "DefaultSlot",
    "segments": [
        {"anim_path": "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_FairyWand.A_Mocap_FairyWand", "start_time": 0.0}
    ],
    "sections": [
        {"name": "Default", "start_time": 0.0}
    ],
    "blend_in": 0.1,
    "blend_out": 0.3,
})
print(json.dumps(r, indent=2)[:500])

# Victory: A_Mocap_Twirl_001 (since Twirl wasn't retargeted)
print("\n=== Creating AM_Mocap_Victory ===")
r = mcp_tool("animation", "create_montage_from_sections", {
    "asset_path": "/Game/Melodia/Characters/Melusina/Animations/AM_Mocap_Victory",
    "skeleton_path": "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton.SK_Melusina_Skeleton",
    "slot_name": "DefaultSlot",
    "segments": [
        {"anim_path": "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_Twirl_001.A_Mocap_Twirl_001", "start_time": 0.0}
    ],
    "sections": [
        {"name": "Default", "start_time": 0.0}
    ],
    "blend_in": 0.1,
    "blend_out": 0.3,
})
print(json.dumps(r, indent=2)[:500])

# Jump End: A_Mocap_GracefulLanding
print("\n=== Creating AM_Mocap_JumpEnd ===")
r = mcp_tool("animation", "create_montage_from_sections", {
    "asset_path": "/Game/Melodia/Characters/Melusina/Animations/AM_Mocap_JumpEnd",
    "skeleton_path": "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton.SK_Melusina_Skeleton",
    "slot_name": "DefaultSlot",
    "segments": [
        {"anim_path": "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_GracefulLanding.A_Mocap_GracefulLanding", "start_time": 0.0}
    ],
    "sections": [
        {"name": "Default", "start_time": 0.0}
    ],
    "blend_in": 0.1,
    "blend_out": 0.2,
})
print(json.dumps(r, indent=2)[:500])
