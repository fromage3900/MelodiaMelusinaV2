import sys, os
for _m in [m for m in list(sys.modules) if m == 'surreal_arch' or m.startswith('surreal_arch.')]:
    del sys.modules[_m]
sys.path.insert(0, os.path.join(os.getcwd(), "deploy"))
from surreal_arch.melodia_gn.core import GROUP_BUILDERS
print("registry ids:", len(GROUP_BUILDERS))
for rid in ["MEL_allee_ribbon","MEL_ribbon_curve","MEL_lissajous_ribbon","MEL_closed_ribbon"]:
    assert rid in GROUP_BUILDERS, f"MISSING {rid}"
    t = GROUP_BUILDERS[rid](rid)
    print(f"{rid}: nodes={len(t.nodes)}")
import bpy
sc = bpy.context.scene
col = bpy.data.collections.new("T"); sc.collection.children.link(col)
m = bpy.data.meshes.new("Allee"); o = bpy.data.objects.new("Allee", m)
col.objects.link(o)
md = o.modifiers.new("GN", type='NODES')
md.node_group = bpy.data.node_groups["MEL_allee_ribbon"]
dg = bpy.context.evaluated_depsgraph_get()
ev = o.evaluated_get(dg); me = ev.data
xs=[v.co.x for v in me.vertices]; ys=[v.co.y for v in me.vertices]; zs=[v.co.z for v in me.vertices]
print(f"ALLEE: verts={len(me.vertices)} x:[{min(xs):.2f},{max(xs):.2f}] y:[{min(ys):.2f},{max(ys):.2f}] z:[{min(zs):.3f},{max(zs):.3f}]")
