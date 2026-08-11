"""Phase 0.1: Create ENV_SakuraVFX EffectType"""
import json, urllib.request, sys

MCP = "http://127.0.0.1:9316/mcp"

def call_tool(name, args, timeout=15):
    payload = {"jsonrpc":"2.0","id":1,"method":"tools/call",
               "params":{"name":name,"arguments":args}}
    req = urllib.request.Request(MCP,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def gt(r):
    return r.get("result",{}).get("content",[{}])[0].get("text","")

def ok(r):
    return not r.get("result",{}).get("isError",False)

# Create the effect type
r = call_tool("niagara_query", {"action":"create_effect_type","params":{
    "save_path": "/Game/EnvSandbox/VFX/EffectTypes/ENV_SakuraVFX.ENV_SakuraVFX"
}})
print(f"create_effect_type: {gt(r)[:200]}")
print(f"  OK: {ok(r)}")

if ok(r):
    # Set scalability settings with distance cull
    # The params might be different - let me check the action
    r = call_tool("niagara_query", {"action":"set_scalability_settings","params":{
        "asset_path": "/Game/EnvSandbox/VFX/EffectTypes/ENV_SakuraVFX.ENV_SakuraVFX",
    }})
    print(f"set_scalability_settings: {gt(r)[:200]}")

# Save
r = call_tool("niagara_query", {"action":"save_system","params":{
    "asset_path": "/Game/EnvSandbox/VFX/EffectTypes/ENV_SakuraVFX.ENV_SakuraVFX"
}})
print(f"save: {gt(r)[:100]}")
