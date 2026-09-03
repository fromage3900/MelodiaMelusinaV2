import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath="Saved/MelusinasHouse/House_ShinglePatch.blend")
obj = bpy.data.objects.get("MH_ShinglePatch")
dg = bpy.context.evaluated_depsgraph_get()
ev = obj.evaluated_get(dg)
n=0; zs=[]
for inst in dg.object_instances:
    if inst.parent and inst.parent.original == obj:
        n+=1
        zs.append(inst.matrix_world.translation.z)
print(f"instances={n} expect=63")
if zs:
    print(f"z:[{min(zs):.3f},{max(zs):.3f}]")
