"""Re-create montages with correct schema params."""
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

# Delete empty montages first
for name in ["AM_Mocap_BasicAttack", "AM_Mocap_Skill", "AM_Mocap_Victory", "AM_Mocap_JumpEnd"]:
    path = f"/Game/Melodia/Characters/Melusina/Animations/{name}"
    r = mcp_tool("editor", "delete_assets", {"asset_paths": [path], "restrict_to_allowed_prefixes": True})
    print(f"Deleted {name}: {json.dumps(r)[:100]}")

# Re-create with correct params
montage_defs = [
    ("AM_Mocap_BasicAttack", "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_MercyStab.A_Mocap_MercyStab"),
    ("AM_Mocap_Skill", "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_FairyWand.A_Mocap_FairyWand"),
    ("AM_Mocap_Victory", "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_Twirl_001.A_Mocap_Twirl_001"),
    ("AM_Mocap_JumpEnd", "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_GracefulLanding.A_Mocap_GracefulLanding"),
]

for name, anim_path in montage_defs:
    montage_path = f"/Game/Melodia/Characters/Melusina/Animations/{name}.{name}"
    print(f"\n=== Creating {name} ===")
    r = mcp_tool("animation", "create_montage_from_sections", {
        "asset_path": montage_path,
        "skeleton_path": "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton.SK_Melusina_Skeleton",
        "slot_name": "DefaultSlot",
        "sections": [
            {"name": "Default", "anim_path": anim_path, "start_time": 0.0}
        ],
        "blend": {"blend_in_time": 0.1, "blend_out_time": 0.2},
    })
    print(json.dumps(r, indent=2)[:500])
    
    # Verify
    r2 = mcp_tool("animation", "get_montage_info", {"asset_path": montage_path})
    print(f"  sections={r2.get('section_count')}, slots={r2.get('slot_count')}, anims={r2.get('anim_count')}")
