"""Check skeletons of available animations for blendspace."""
import json, urllib.request

script = r"""
import unreal

anims_to_check = [
    "/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonIdle.A_ThirdPersonIdle",
    "/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonWalk.A_ThirdPersonWalk",
    "/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonRun.A_ThirdPersonRun",
    "/Game/Melodia/Characters/Melusina/Animations/A_ThirdPersonDash.A_ThirdPersonDash",
    "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_RunCycle_Sprint.A_Mocap_RunCycle_Sprint",
    "/Game/Melodia/Characters/Melusina/Animations/Mocap/A_Mocap_FairyWand.A_Mocap_FairyWand",
]

for path in anims_to_check:
    anim = unreal.load_asset(path)
    if anim:
        skel = anim.get_editor_property("skeleton")
        skel_name = skel.get_name() if skel else "None"
        anim_class = anim.get_class().get_name()
        num_frames = 0
        try:
            num_frames = anim.get_editor_property("num_frames")
        except:
            pass
        unreal.log(f"{path.split('/')[-1].split('.')[0]:30s} skel={skel_name:30s} frames={num_frames} class={anim_class}")
    else:
        unreal.log(f"{path.split('/')[-1].split('.')[0]:30s} NOT FOUND")
"""

with open(r'G:\EnvironmentPortfolio\BS_GodFile\Content\Python\_phase4_check_skeletons.py', 'w') as f:
    f.write(script)

req = urllib.request.Request(
    'http://127.0.0.1:9316/mcp',
    data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "editor_query",
                                "arguments": {"action": "run_python",
                                              "params": {"command": "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/_phase4_check_skeletons.py",
                                                         "mode": "execute_file"}}}}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
parsed = json.loads(text)
if parsed.get("output"):
    for o in parsed["output"]:
        print(o.get("output",""))
