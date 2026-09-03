"""Find the actual paths of the material instances"""
import json
import urllib.request

MCP_URL = "http://127.0.0.1:9316/mcp"
SAKURA = "/Game/EnvSandbox/VFX/Systems/Sakura"

def call_tool(name, args, timeout=15):
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
               "params": {"name": name, "arguments": args}}
    req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def get_text(result):
    return result.get("result", {}).get("content", [{}])[0].get("text", "")

# Search for materials by name
materials = ["MI_Niagara_Sparkle", "MI_Niagara_Petal", "MI_Niagara_Mote", "MI_Niagara_Pond", "MI_Niagara_Gust"]

for m in materials:
    # Try list_systems with search (this searches Niagara systems, not materials)
    # Let's try use the material_query instead
    r = call_tool("material_query", {"action": "discover", "params": {}})
    # That gave us the action list earlier. Let me try get_all_expressions or something material-specific
    # Actually let's use search_by_material on niagra_query to find references
    pass

# Let's directly check asset existence by trying to load with different paths
# The original report said they exist. Let's try the path without the asset suffix
path = "/Game/EnvSandbox/VFX/Materials"
MATS = path

# Try set_renderer_material without .AssetName suffix
def niagara(action, params):
    r = call_tool("niagara_query", {"action": action, "params": params})
    text = get_text(r)
    print(f"  {action}: {text[:300]}")
    return text

print("=== Try paths WITHOUT suffix ===")
path_ds = f"{SAKURA}/NS_SakuraDreamSparkle"

# Use raw MCP call to see full response
payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
           "params": {"name": "niagara_query", "arguments": {
               "action": "set_renderer_material",
               "params": {
                   "asset_path": f"{path_ds}",
                   "emitter": "DreamMotes",
                   "renderer_index": 0,
                   "material": f"{MATS}/MI_Niagara_Sparkle",
               }}}}
req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=15) as resp:
    raw = json.loads(resp.read().decode())
print(f"Without suffix: {json.dumps(raw)[:300]}")

# Try with MI_Niagara_Sparkle.MI_Niagara_Sparkle using a different path
payload = {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
           "params": {"name": "niagara_query", "arguments": {
               "action": "set_renderer_material",
               "params": {
                   "asset_path": f"{path_ds}",
                   "emitter": "DreamMotes",
                   "renderer_index": 0,
                   "material": f"{MATS}/MI_Niagara_Sparkle/MI_Niagara_Sparkle",
               }}}}
req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=15) as resp:
    raw2 = json.loads(resp.read().decode())
print(f"With / separator: {json.dumps(raw2)[:300]}")

# Try with the same format as existing materials (path.AssetName)
payload = {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
           "params": {"name": "niagara_query", "arguments": {
               "action": "set_renderer_material",
               "params": {
                   "asset_path": f"{path_ds}",
                   "emitter": "DreamMotes",
                   "renderer_index": 1,
                   "material": f"{MATS}/M_Niagara_SakuraSprite.M_Niagara_SakuraSprite",
               }}}}
req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=15) as resp:
    raw3 = json.loads(resp.read().decode())
print(f"Re-set existing mat (wrong ri): {json.dumps(raw3)[:300]}")

# Try with renderer_index 0 and existing mat
payload = {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
           "params": {"name": "niagara_query", "arguments": {
               "action": "set_renderer_material",
               "params": {
                   "asset_path": f"{path_ds}",
                   "emitter": "DreamMotes",
                   "renderer_index": 0,
                   "material": f"{MATS}/M_Niagara_SakuraSprite.M_Niagara_SakuraSprite",
               }}}}
req = urllib.request.Request(MCP_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=15) as resp:
    raw4 = json.loads(resp.read().decode())
print(f"Re-set existing mat (right ri): {json.dumps(raw4)[:300]}")
