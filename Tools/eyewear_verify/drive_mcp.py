"""Drive the RUNNING Blender MCP session (port 9876) — does NOT spawn a new Blender."""
import socket
import json
import sys

MCP_HOST = "127.0.0.1"
MCP_PORT = 9876

def mcp_call(tool, params=None, timeout=30):
    """Send a JSON-RPC call to the running Blender MCP."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect((MCP_HOST, MCP_PORT))
    
    msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool,
            "arguments": params or {}
        }
    }
    sock.sendall((json.dumps(msg) + "\n").encode())
    
    data = b""
    while True:
        chunk = sock.recv(8192)
        if not chunk:
            break
        data += chunk
        try:
            decoded = data.decode()
            for line in decoded.split("\n"):
                line = line.strip()
                if line:
                    try:
                        response = json.loads(line)
                        sock.close()
                        return response.get("result", {}).get("content", [{}])[0].get("text", str(response))
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
    sock.close()
    return ""

# Step 1: Check if addon is loaded
print("=== Step 1: Check addon availability ===")
result = mcp_call("run_python", {
    "code": "from surreal_arch.melodia_gn.core import GROUP_BUILDERS; print([k for k in GROUP_BUILDERS if 'eyewear' in k])"
})
print(f"Eyewear builders: {result}")

# Step 2: Create mesh host (cube)
print("\n=== Step 2: Create mesh host ===")
result = mcp_call("add_object", {"type": "MESH", "name": "Eyewear_Hero_Host"})
print(f"Mesh host: {result}")

# Step 3: Apply GN modifier
print("\n=== Step 3: Apply GN modifier ===")
result = mcp_call("add_modifier", {
    "object": "Eyewear_Hero_Host",
    "type": "NODES",
    "node_group": "MEL_eyewear_hero"
})
print(f"Modifier: {result}")

# Step 4: Rotate to stand up
print("\n=== Step 4: Rotate to stand up ===")
result = mcp_call("transform_object", {
    "object": "Eyewear_Hero_Host",
    "rotation": [-90, 0, 0]
})
print(f"Transform: {result}")

# Step 5: Frame the view
print("\n=== Step 5: Frame viewport ===")
result = mcp_call("frame_selected")
print(f"Frame: {result}")

# Step 6: Check if it evaluates
print("\n=== Step 6: Evaluate check ===")
result = mcp_call("run_python", {
    "code": """import bpy
host = bpy.data.objects.get('Eyewear_Hero_Host')
if host:
    dg = bpy.context.evaluated_depsgraph_get()
    ev = host.evaluated_get(dg)
    me = bpy.data.meshes.new('__probe')
    ev.to_mesh(me)
    print(f'verts: {len(me.vertices)}, faces: {len(me.polygons)}')
    bpy.data.meshes.remove(me)
else:
    print('host not found')"""
})
print(f"Eval: {result}")

print("\nDONE")
