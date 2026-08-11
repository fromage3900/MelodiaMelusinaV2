"""Phase 4.1: Create BS_Locomotion blendspace with available animations."""
import json, urllib.request

script = r"""
import unreal
import json

result = {"steps": [], "errors": []}

SKEL_PATH = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton.SK_Melusina_Skeleton"
BS_PATH = "/Game/Melodia/Characters/Melusina/BlendSpaces/BS_Locomotion"
ANIMS = {
    "/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonIdle.A_ThirdPersonIdle": 0.0,
    "/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonWalk.A_ThirdPersonWalk": 200.0,
    "/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonRun.A_ThirdPersonRun": 400.0,
    "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_RunCycle_Sprint.A_Mocap_RunCycle_Sprint": 600.0,
}

# Step 1: Check if blendspace already exists
if unreal.EditorAssetLibrary.does_asset_exist(BS_PATH):
    result["steps"].append("BlendSpace already exists, skipping creation")
    print(json.dumps(result))

# Step 2: Create blend space 1D
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
factory = unreal.BlendSpaceFactory1D()
package_path = "/Game/Melodia/Characters/Melusina/BlendSpaces"

blend_space = asset_tools.create_asset("BS_Locomotion", package_path, None, factory)
if not blend_space:
    result["errors"].append("Failed to create blend space asset")
    print(json.dumps(result))

result["steps"].append("Created BS_Locomotion blend space")

# Step 3: Load skeleton
skel = unreal.load_asset(SKEL_PATH)
if not skel:
    result["errors"].append("Could not load skeleton")
    print(json.dumps(result))

blend_space.modify()
blend_space.set_editor_property("skeleton", skel)
result["steps"].append("Set skeleton")

# Step 4: Set blend parameter (Speed axis)
param = unreal.BlendParameter()
param.set_editor_property("name", "Speed")
param.set_editor_property("min", 0.0)
param.set_editor_property("max", 600.0)
param.set_editor_property("grid_num", 4)
blend_space.set_editor_property("blend_parameters", [param])
result["steps"].append("Set blend parameter Speed (0-600)")

# Step 5: Add animation samples
samples_added = 0
for anim_path, speed in ANIMS.items():
    anim = unreal.EditorAssetLibrary.load_asset(anim_path)
    if not anim:
        result["errors"].append(f"Animation not found: {anim_path}")
        continue
    try:
        blend_space.add_sample(anim, speed)
        samples_added += 1
        result["steps"].append(f"Added {anim_path.split('/')[-1].split('.')[0]} @ {speed}")
    except Exception as e:
        # Try alternative approach
        try:
            mappings = blend_space.get_editor_property("animation_sequences") or []
            existing = list(mappings)
            from unreal import BlendMappedAnimation
            mapping = BlendMappedAnimation()
            mapping.set_editor_property("animation", anim)
            mapping.set_editor_property("sample_value", speed)
            existing.append(mapping)
            blend_space.set_editor_property("animation_sequences", existing)
            samples_added += 1
            result["steps"].append(f"Added {anim_path.split('/')[-1].split('.')[0]} @ {speed} (via property)")
        except Exception as e2:
            result["errors"].append(f"Failed to add {anim_path}: {str(e2)[:80]}")

# Step 6: Save
unreal.EditorAssetLibrary.save_asset(blend_space.get_path_name())
result["steps"].append(f"Saved. Samples added: {samples_added}/{len(ANIMS)}")
result["ok"] = samples_added > 0

print(json.dumps(result))
"""

with open(r'G:\EnvironmentPortfolio\BS_GodFile\Content\Python\_phase4_create_blendspace.py', 'w') as f:
    f.write(script)

req = urllib.request.Request(
    'http://127.0.0.1:9316/mcp',
    data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "editor_query",
                                "arguments": {"action": "run_python",
                                              "params": {"command": "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/_phase4_create_blendspace.py",
                                                         "mode": "execute_file"}}}}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=60).read())
text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
print(text[:3000])
