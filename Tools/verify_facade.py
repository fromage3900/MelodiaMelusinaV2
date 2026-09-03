import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.open_mainfile(filepath="Saved/MelusinasHouse/House_Facade_v4.blend")
obj = bpy.data.objects.get("MH_FacadeWall")
dg = bpy.context.evaluated_depsgraph_get()
ev = obj.evaluated_get(dg)
me = ev.data
print(f"verts={len(me.vertices)} faces={len(me.polygons)}")
xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
print(f"x:[{min(xs):.2f},{max(xs):.2f}] y:[{min(ys):.2f},{max(ys):.2f}] z:[{min(zs):.2f},{max(zs):.2f}]")
# check wave: modules are boxes (verts live at corner heights), so compare
# full-height mean y per x-bin; boolean holes remove faces, never whole bins
cy = [v.co.y for v in me.vertices if abs(v.co.x)<0.6]
sy = [v.co.y for v in me.vertices if 4.0<abs(v.co.x)<5.0]
print(f"center_y~{sum(cy)/len(cy):.3f} shoulder_y~{sum(sy)/len(sy):.3f}" if cy and sy else "wave-check-n/a")
