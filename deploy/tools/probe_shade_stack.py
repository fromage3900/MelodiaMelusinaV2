import bpy
bpy.ops.mesh.primitive_cube_add()
obj = bpy.context.active_object
for i in range(5):
    bpy.ops.object.shade_auto_smooth()
    print(i+1, [m.name for m in obj.modifiers])
