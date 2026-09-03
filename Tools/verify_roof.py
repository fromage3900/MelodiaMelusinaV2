import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath="Saved/MelusinasHouse/House_RoofRibbon.blend")
dg = bpy.context.evaluated_depsgraph_get()
for name in ["Roof_Main","Roof_Wing","Roof_Porch"]:
    o = bpy.data.objects.get(name)
    ev = o.evaluated_get(dg)
    me = ev.data
    xs=[v.co.x for v in me.vertices]; ys=[v.co.y for v in me.vertices]; zs=[v.co.z for v in me.vertices]
    print(f"{name}: verts={len(me.vertices)} faces={len(me.polygons)} x:[{min(xs):.2f},{max(xs):.2f}] y:[{min(ys):.2f},{max(ys):.2f}] z:[{min(zs):.2f},{max(zs):.2f}]")
