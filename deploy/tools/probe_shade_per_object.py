import bpy
for i in range(5):
    bpy.ops.mesh.primitive_cube_add(location=(i*3,0,0))
    obj = bpy.context.active_object
    obj.name = f"Cube_{i}"
    bpy.ops.object.shade_auto_smooth()
total = sum(1 for o in bpy.data.objects if any(m.name == "Smooth by Angle" for m in o.modifiers))
print("objects with smooth mod:", total, "of", len(bpy.data.objects))
