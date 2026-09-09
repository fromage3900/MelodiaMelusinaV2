import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath="Saved/MelusinasHouse/House_ShinglePatch.blend")
obj = bpy.data.objects.get("MH_ShinglePatch")
dg = bpy.context.evaluated_depsgraph_get()
ev = obj.evaluated_get(dg)
me = ev.data
print(f"verts={len(me.vertices)} faces={len(me.polygons)}")
xs=[v.co.x for v in me.vertices]; ys=[v.co.y for v in me.vertices]; zs=[v.co.z for v in me.vertices]
print(f"x:[{min(xs):.2f},{max(xs):.2f}] y:[{min(ys):.2f},{max(ys):.2f}] z:[{min(zs):.2f},{max(zs):.2f}]")
