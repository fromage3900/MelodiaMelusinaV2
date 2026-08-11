import bpy
bpy.ops.mesh.primitive_cube_add()
obj = bpy.context.active_object
print("start", [m.name for m in obj.modifiers])
for poly in obj.data.polygons:
    poly.use_smooth = True
obj.data.update()
print("after poly smooth", [m.name for m in obj.modifiers])
# bevel like addon
bv = obj.modifiers.new(name="SurrealArch_Bevel", type='BEVEL')
bv.harden_normals = True
print("after bevel", [m.name for m in obj.modifiers])
