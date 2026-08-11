import bpy
bpy.ops.mesh.primitive_cube_add()
obj = bpy.context.active_object
for attr in ("use_auto_smooth", "auto_smooth_angle"):
    print("mesh", attr, hasattr(obj.data, attr))
    print("obj", attr, hasattr(obj, attr))
try:
    obj.use_auto_smooth = True
    print("set obj.use_auto_smooth OK", [m.name for m in obj.modifiers])
except Exception as e:
    print("obj.use_auto_smooth", e)
