"""Get add_blendspace_sample schema and add all samples."""
import json, urllib.request

def mcp_tool(ns, action, params):
    body = {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": f"{ns}_query", "arguments": {"action": action, "params": params}}
    }
    req = urllib.request.Request(
        'http://127.0.0.1:9316/mcp',
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    return json.loads(urllib.request.urlopen(req, timeout=60).read())

# Get schema for add_blendspace_sample
print("=== Schema for add_blendspace_sample ===")
r = mcp_tool("describe", "action_schema", {"target_namespace": "animation", "target_action": "add_blendspace_sample"})
print(json.dumps(r, indent=2)[:2000])

# Now add samples
samples = [
    ("/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonIdle.A_ThirdPersonIdle", 0.0),
    ("/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonWalk.A_ThirdPersonWalk", 200.0),
    ("/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonRun.A_ThirdPersonRun", 400.0),
    ("/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_RunCycle_Sprint.A_Mocap_RunCycle_Sprint", 600.0),
]

for anim_path, speed in samples:
    print(f"\nAdding {anim_path.split('/')[-1]} @ {speed}")
    r = mcp_tool("animation", "add_blendspace_sample", {
        "asset_path": "/Game/Melodia/Characters/Melusina/BlendSpaces/BS_Locomotion.BS_Locomotion",
        "anim_path": anim_path,
        "x": speed,
        "y": 0.0,
    })
    print(r.get("result", {}).get("content", [{}])[0].get("text", ""))
