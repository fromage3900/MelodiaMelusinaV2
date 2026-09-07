import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
t = bpy.data.node_groups.new("QT", "GeometryNodeTree")
s = t.interface.new_socket(name="Roof Width", socket_type="NodeSocketFloat", in_out='INPUT')
s.default_value = 8.0
t.interface.new_socket(name="Geometry", socket_type="NodeSocketGeometry", in_out='OUTPUT')
gin = t.nodes.new("NodeGroupInput"); gout = t.nodes.new("NodeGroupOutput")
o = bpy.data.objects.new("O", bpy.data.meshes.new("M"))
bpy.context.scene.collection.objects.link(o)
md = o.modifiers.new("GN", type='NODES')
md.node_group = t
print("identifier:", s.identifier)
for probe in ["Socket_0", "Input_1", "Roof Width"]:
    try:
        setattr(md, probe, 9.0)
        print(probe, "SETATTR OK ->", getattr(md, probe, None))
    except Exception as e:
        print(probe, "SETATTR FAIL:", str(e)[:90])
print("node_group inputs:", [ (k, type(v).__name__) for k,v in md.node_group.inputs.items()] if hasattr(md.node_group,'inputs') else "n/a")
