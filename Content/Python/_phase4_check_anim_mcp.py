"""Check existing A_Src animation properties to understand import approach."""
import json, urllib.request

def mcp_run(cmd):
    req = urllib.request.Request(
        'http://127.0.0.1:9316/mcp',
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                         "params": {"name": "editor_query",
                                    "arguments": {"action": "run_python",
                                                  "params": {"command": cmd,
                                                             "mode": "execute_file"}}}}).encode(),
        headers={"Content-Type": "application/json"},
    )
    resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
    text = resp.get("result", {}).get("content", [{}])[0].get("text", "{}")
    return json.loads(text)

# Write the script to check
script = r"""
import unreal, json
# Check an existing source animation to understand the skeleton
anim = unreal.load_asset('/Game/Melodia/Mocap/Source/Anims/A_Src_Dodge.A_Src_Dodge')
result = {}
if anim:
    result['path'] = '/Game/Melodia/Mocap/Source/Anims/A_Src_Dodge'
    result['class'] = anim.get_class().get_name()
    try:
        skel = anim.get_editor_property('skeleton')
        result['skeleton'] = skel.get_path_name() if skel else None
    except:
        result['skeleton_error'] = 'no skeleton prop'
    try:
        rate = anim.get_editor_property('rate_scale')
        result['rate_scale'] = rate
    except:
        pass
    # Check bone names
    try:
        bones = anim.get_editor_property('bone_names')
        result['bone_count'] = len(bones) if bones else 0
        if bones:
            result['first_bones'] = bones[:5]
    except:
        result['bones_error'] = 'no bone_names'
else:
    result['error'] = 'Cannot load animation'

print(json.dumps(result))
"""

with open(r'G:\EnvironmentPortfolio\BS_GodFile\Content\Python\_phase4_check_anim.py', 'w') as f:
    f.write(script)

r = mcp_run(r'G:/EnvironmentPortfolio/BS_GodFile/Content/Python/_phase4_check_anim.py')
out = "\n".join(o.get("output","") for o in r.get("output",[]))
print(out)
