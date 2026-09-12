"""Stage the eyewear hero builder in the running Blender session.

Connects to the running blender_mcp at 127.0.0.1:9876 and:
1. Creates a new blend or clears the current one
2. Creates an empty host object
3. Applies MEL_eyewear_hero as a Geometry Nodes modifier
4. Rotates it -90° X to stand up
5. Frames the viewport"""
import socket
import json
import sys
import time

MCP_HOST = "127.0.0.1"
MCP_PORT = 9876

def mcp_call(tool, params=None):
    """Send a JSON-RPC call to the Blender MCP."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(30)
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
    
    # Read response
    data = b""
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        data += chunk
        if b"\n" in data:
            break
    sock.close()
    
    response = json.loads(data.decode().strip())
    return response.get("result", {}).get("content", [{}])[0].get("text", "")

# Check connection
print("=== Connecting to Blender MCP...")
result = mcp_call("scene_info")
print("Scene:", result[:200])

# Create new file
print("\n=== Creating new blend file...")
result = mcp_call("new_blender_file")
print("New file:", result[:200])

# Create empty host
print("\n=== Creating host empty...")
result = mcp_call("add_object", {"type": "EMPTY", "name": "Eyewear_Hero_Host"})
print("Host:", result[:200])

# Add geometry nodes modifier
print("\n=== Adding Geometry Nodes modifier...")
result = mcp_call("add_modifier", {
    "object": "Eyewear_Hero_Host",
    "type": "NODES",
    "node_group": "MEL_eyewear_hero"
})
print("Modifier:", result[:200])

# Rotate to stand up
print("\n=== Rotating to stand up...")
result = mcp_call("transform_object", {
    "object": "Eyewear_Hero_Host",
    "rotation": [-90, 0, 0]
})
print("Transform:", result[:200])

# Frame selected
print("\n=== Framing viewport...")
result = mcp_call("frame_selected")
print("Frame:", result[:200])

# Get scene info to confirm
print("\n=== Final scene state ===")
result = mcp_call("scene_info")
print(result[:500])

print("\nDONE")
