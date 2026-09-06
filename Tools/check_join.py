import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
t = bpy.data.node_groups.new("Q", "GeometryNodeTree")
for bid in ["GeometryNodeJoinGeometry","GeometryNodeMeshBoolean","GeometryNodeMeshCube","GeometryNodeTransform","GeometryNodeMeshBevel"]:
    n = t.nodes.new(bid)
    print(bid, "IN:", [i.name for i in n.inputs], "OUT:", [o.name for o in n.outputs])
