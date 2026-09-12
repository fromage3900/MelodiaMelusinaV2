"""Drive the running Blender MCP — proper protocol from live-session-bridge reference.

Protocol: newline-free JSON over TCP 127.0.0.1:9876
Commands: execute_code, ping, get_scene_info, get_object_info, get_viewport_screenshot

RULES:
- Back up before mutating (save_as_mainfile with copy=True)
- execute_code captures stdout, DISCARDS on exception — wrap in try/except
- A render blocks the main thread
- Do not replace the live addon while Blender runs
"""
import socket
import json
import sys
import os
import time

MCP_HOST = "127.0.0.1"
MCP_PORT = 9876
MCP_TIMEOUT = 60

def mcp_call(command_type, params=None):
    """Send a JSON command to the Blender MCP and return (status, result)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(MCP_TIMEOUT)
    sock.connect((MCP_HOST, MCP_PORT))
    
    msg = {"type": command_type}
    if params:
        msg["params"] = params
    
    # Newline-free JSON
    raw = json.dumps(msg)
    sock.sendall(raw.encode())
    
    # Read response
    data = b""
    while True:
        chunk = sock.recv(8192)
        if not chunk:
            break
        data += chunk
        try:
            decoded = data.decode()
            response = json.loads(decoded)
            sock.close()
            return response.get("status", "error"), response.get("result", {})
        except json.JSONDecodeError:
            continue
    sock.close()
    return "error", {}

def execute(code):
    """Run Python code in Blender, return (success, output)."""
    try:
        status, result = mcp_call("execute_code", {"code": code})
        if status == "success":
            return True, result.get("stdout", "")
        else:
            # On exception, stdout is discarded — result has the error
            return False, result.get("error", str(result))
    except Exception as e:
        return False, str(e)

def scene_info():
    """Get scene info."""
    status, result = mcp_call("get_scene_info")
    return status == "success", result

def ping():
    """Check connection."""
    status, result = mcp_call("ping")
    return status == "success"

# Step 0: Ping
print("=== Step 0: Ping Blender MCP ===")
if ping():
    print("  MCP connection: OK")
else:
    print("  MCP connection: FAILED")
    sys.exit(1)

# Step 1: Backup
print("\n=== Step 1: Backup current file ===")
ok, out = execute("""
bpy.ops.wm.save_as_mainfile(
    filepath=r'P:/MelodiaMelusinaV2-Laptop/Saved/Accessories/_backup_pre_stage.blend',
    copy=True
)
print('Backup saved')
""")
print(f"  Backup: {'OK' if out else 'FAILED'} — {out[:100]}")

# Step 2: Scene info
print("\n=== Step 2: Scene info ===")
ok, info = scene_info()
if ok:
    print(f"  Scene: {info.get('scene_name', '?')}")
    print(f"  Objects: {len(info.get('objects', []))}")
    print(f"  Cameras: {len([o for o in info.get('objects', []) if o.get('type') == 'CAMERA'])}")

# Step 3: Verify eyewear builders load
print("\n=== Step 3: Verify eyewear builders ===")
ok, out = execute("""
import sys
sys.path.insert(0, r'P:/MelodiaMelusinaV2-Laptop/deploy')
from surreal_arch.melodia_gn.core import GROUP_BUILDERS
eyewear = [k for k in GROUP_BUILDERS if 'eyewear' in k]
print('eyewear builders:', eyewear)
print('count:', len(eyewear))
""")
print(f"  Result: {out[:200]}")

# Step 4: Stage the silhouette grid
print("\n=== Step 4: Stage silhouette grid ===")
ok, out = execute("""
import sys
sys.path.insert(0, r'P:/MelodiaMelusinaV2-Laptop/deploy')
from surreal_arch.melodia_gn.core import GROUP_BUILDERS
import bpy

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Lighting
for name, energy, loc in [('Key', 600, (2.6, -2.4, 3.4)), ('Rim', 300, (-2.4, 1.6, 2.8)), ('Fill', 200, (0.4, 2.8, 2.2))]:
    bpy.ops.object.light_add(type='AREA', location=loc)
    light = bpy.context.active_object
    light.name = name
    light.data.energy = energy
    light.data.size = 1.5

# Camera
bpy.ops.object.camera_add(location=(0, -6, 1.4))
cam = bpy.context.active_object
cam.name = 'Cam_Compare'
cam.data.lens = 50
cam.data.clip_start = 0.001
bpy.context.scene.camera = cam

# Grid of 6 silhouettes
SILHOUETTES = [(0, 'Rect'), (1, 'Panto'), (2, 'CatEye'), (3, 'Aviator'), (4, 'Browline'), (5, 'Round')]
spacing = 0.30
x_start = -((len(SILHOUETTES) - 1) * spacing) / 2

for i, (idx, label) in enumerate(SILHOUETTES):
    x = x_start + i * spacing
    bpy.ops.object.mesh_cube_add(size=0.001, location=(x, 0, 0))
    host = bpy.context.active_object
    host.name = f'Eyewear_{label}'
    mod = host.modifiers.new('GN', 'NODES')
    mod.node_group = GROUP_BUILDERS['MEL_eyewear_hero']()
    # Set silhouette
    for it in mod.node_group.interface.items_tree:
        if getattr(it, 'name', None) == 'Silhouette' and getattr(it, 'in_out', None) == 'INPUT':
            it.default_value = idx
    host.rotation_euler = (-1.5707963267948966, 0, 0)
    print(f'  [{i+1}/6] {label} (idx={idx}) at x={x:.2f}')

print('Grid staged:', len(SILHOUETTES), 'pairs')
""")
print(f"  Result: {out[:500]}")

# Step 5: Save
print("\n=== Step 5: Save blend ===")
ok, out = execute("""
bpy.ops.wm.save_as_mainfile(filepath=r'P:/MelodiaMelusinaV2-Laptop/Saved/Accessories/Silhouette_Grid_Live_v1.blend')
print('Saved')
""")
print(f"  Save: {'OK' if out else 'FAILED'} — {out[:100]}")

print("\nDONE")
