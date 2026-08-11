"""Try Monolith native protocol for blendspace creation."""
import json, urllib.request

# Try native Monolith protocol: POST with namespace/action/params
body = {
    "jsonrpc": "2.0",
    "id": 1,
    "namespace": "animation",
    "action": "create_blend_space_1d",
    "params": {
        "path": "/Game/Melodia/Characters/Melusina/BlendSpaces/BS_Locomotion",
        "skeleton": "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton.SK_Melusina_Skeleton",
        "axis_name": "Speed",
        "axis_min": 0.0,
        "axis_max": 600.0,
    }
}

req = urllib.request.Request(
    'http://127.0.0.1:9316',  # NOTE: no /mcp path - GMM client uses root
    data=json.dumps(body).encode(),
    headers={"Content-Type": "application/json"},
)
try:
    resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
    print("Monolith native response:")
    print(json.dumps(resp, indent=2)[:2000])
except Exception as e:
    print(f"Error: {e}")
