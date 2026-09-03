"""Probe what creates Smooth by Angle modifiers in Blender 5.1."""
import math
import bpy

bpy.ops.mesh.primitive_cube_add()
obj = bpy.context.active_object

def mod_names():
    return [(m.name, m.type) for m in obj.modifiers]

print("mods start:", mod_names())
print("has use_auto_smooth:", hasattr(obj.data, "use_auto_smooth"))

try:
    obj.data.use_auto_smooth = True
    obj.data.auto_smooth_angle = math.radians(30)
    print("set use_auto_smooth OK")
except Exception as e:
    print("use_auto_smooth failed:", e)

print("mods after use_auto_smooth:", mod_names())

for p in obj.data.polygons:
    p.use_smooth = True
obj.data.update()
print("mods after poly smooth:", mod_names())

# Simulate generate path: add bevel like apply_edge_bevel_modifier
try:
    obj.data.use_auto_smooth = True
    obj.data.auto_smooth_angle = math.radians(35)
except Exception:
    pass
print("mods after second use_auto_smooth:", mod_names())
