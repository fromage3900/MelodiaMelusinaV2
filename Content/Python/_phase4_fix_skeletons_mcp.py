"""Fix A_ThirdPerson skeleton references + add to blendspace."""
import json, urllib.request

script = r"""
import unreal
import json

result = {}
skel = unreal.load_asset("/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton.SK_Melusina_Skeleton")

# Fix skeleton on A_ThirdPerson anims
anims_to_fix = [
    "/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonIdle.A_ThirdPersonIdle",
    "/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonWalk.A_ThirdPersonWalk",
    "/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonRun.A_ThirdPersonRun",
    "/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonDash.A_ThirdPersonDash",
    "/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonJump_End.A_ThirdPersonJump_End",
]

for path in anims_to_fix:
    anim = unreal.load_asset(path)
    if anim:
        try:
            anim.set_editor_property("skeleton", skel)
            unreal.EditorAssetLibrary.save_loaded_asset(anim)
            result[path.split("/")[-1].split(".")[0]] = "fixed"
        except Exception as e:
            result[path.split("/")[-1].split(".")[0]] = str(e)[:80]
    else:
        result[path.split("/")[-1].split(".")[0]] = "not found"

print(json.dumps(result))
"""

with open(r'G:\EnvironmentPortfolio\BS_GodFile\Content\Python\_phase4_fix_skeletons.py', 'w') as f:
    f.write(script)

req = urllib.request.Request(
    'http://127.0.0.1:9316/mcp',
    data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "editor_query",
                                "arguments": {"action": "run_python",
                                              "params": {"command": "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/_phase4_fix_skeletons.py",
                                                         "mode": "execute_file"}}}}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
print(text[:2000])
