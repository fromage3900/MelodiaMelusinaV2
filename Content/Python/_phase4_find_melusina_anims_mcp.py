"""Find ANY anim with valid skel for blendspace idle/low-end."""
import json, urllib.request

script = r"""
import unreal
import json

result = {}
dirs = [
    "/Game/Melodia/Characters/Melusina/Animations",
    "/Game/Melodia/Characters/Melusina/Animations/Mocap",
]
melusina_skel = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton.SK_Melusina_Skeleton"

for d in dirs:
    assets = unreal.EditorAssetLibrary.list_assets(d, False, False)
    for ap in assets:
        obj = unreal.load_asset(ap)
        if obj and obj.get_class().get_name() == "AnimSequence":
            skel = obj.get_editor_property("skeleton")
            if skel and skel.get_path_name() == melusina_skel:
                name = ap.split("/")[-1].split(".")[0]
                result[name] = 1

print(json.dumps(list(result.keys())))
"""

with open(r'G:\EnvironmentPortfolio\BS_GodFile\Content\Python\_phase4_find_melusina_anims.py', 'w') as f:
    f.write(script)

req = urllib.request.Request(
    'http://127.0.0.1:9316/mcp',
    data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                     "params": {"name": "editor_query",
                                "arguments": {"action": "run_python",
                                              "params": {"command": "G:/EnvironmentPortfolio/BS_GodFile/Content/Python/_phase4_find_melusina_anims.py",
                                                         "mode": "execute_file"}}}}).encode(),
    headers={"Content-Type": "application/json"},
)
resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
print(text[:3000])
