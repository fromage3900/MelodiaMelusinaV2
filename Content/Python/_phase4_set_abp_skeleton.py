"""Phase 4.3: Set ABP skeleton + build state machine + slot nodes."""
import json, urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"

def mcp_rpc(method, arguments):
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": method, "arguments": arguments}}
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(MCP_URL, data=data,
                                 headers={"Content-Type": "application/json"},
                                 method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))

def anim_call(action, params):
    return mcp_rpc("animation_query", {"action": action, "params": params})

def editor_run_python(code):
    return mcp_rpc("editor_query", {"action": "run_python", "params": {"command": code, "mode": "execute_statement"}})

def get_text(r):
    """Extract text from MCP JSON-RPC response."""
    if "error" in r:
        return f"ERROR[{r['error'].get('code','?')}]: {r['error'].get('message','')}"
    content = r.get("result", {}).get("content", [])
    if content:
        return content[0].get("text", str(content[0]))
    return str(r)

ABP = "/Game/Melodia/Characters/Melusina/ABP_Melusina.ABP_Melusina"
SKEL = "/Game/Melodia/Characters/Melusina/SK_Melusina_Skeleton.SK_Melusina_Skeleton"

# Step 1: Set target skeleton on ABP via Python (no direct MCP action)
print("=== Setting ABP skeleton ===")
r = editor_run_python(f"""
import unreal
abp = unreal.load_asset(r"{ABP}")
skel = unreal.load_asset(r"{SKEL}")
abp.set_editor_property("target_skeleton", skel)
unreal.EditorAssetLibrary.save_asset(r"{ABP}")
print(f"Target skeleton set to: {{abp.get_editor_property('target_skeleton').get_name()}}")
""")
print(get_text(r))

# Verify
print("\n=== Verify ===")
r = anim_call("get_abp_info", {"asset_path": ABP})
print(get_text(r)[:600])
