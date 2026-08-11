"""Try create_blend_space_1d via tools/call on animation_query."""
import json, urllib.request

body = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "animation_query",
        "arguments": {
            "action": "create_blend_space_1d",
            "params": {
                "asset_path": "/Game/Melodia/Characters/Melusina/BlendSpaces/BS_Locomotion",
                "skeleton_path": "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton.SK_Melusina_Skeleton",
                "axis_name": "Speed",
                "axis_min": 0.0,
                "axis_max": 600.0,
            }
        }
    }
}

req = urllib.request.Request(
    'http://127.0.0.1:9316/mcp',
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"},
)
try:
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    print(json.dumps(resp, indent=2)[:2000])
except Exception as e:
    print(f"Error: {e}")
