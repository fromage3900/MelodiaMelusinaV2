import bpy
bpy.ops.mesh.primitive_cube_add()
obj = bpy.context.active_object
for i in range(3):
    try:
        r = bpy.ops.object.shade_smooth(use_auto_smooth=True)
        print("shade_smooth use_auto_smooth", i, r, [m.name for m in obj.modifiers])
    except Exception as e:
        print("err", e)
